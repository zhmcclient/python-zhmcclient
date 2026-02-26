# Copyright 2026 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for _virtual_tape_resource module.
"""


import re
import copy
import pytest

from zhmcclient import Client, VirtualTapeResource, \
    VirtualTapeResourceManager, NotFound
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked resources:
CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'
PARTITION_OID = 'partition1-oid'
PARTITION_URI = f'/api/partitions/{PARTITION_OID}'
ADAPTER_OID = 'adapter1-oid'
ADAPTER_URI = f'/api/adapters/{ADAPTER_OID}'
ADAPTER_PORT_URI = f'{ADAPTER_URI}/storage-ports/0'
TL_OID = 'tape-library1-oid'
TL_NAME = 'tape-library 1'
TL_URI = f'/api/tape-libraries/{TL_OID}'
TLINK_OID = 'tlink1-oid'
TLINK_NAME = 'tape link 1'
TLINK_URI = f'{TL_URI}/tape-links/{TLINK_OID}'
VTR1_OID = 'vtr1-oid'
VTR1_NAME = 'virtual tape resource 1'
VTR2_OID = 'vtr2-oid'
VTR2_NAME = 'virtual tape resource 2'


class TestVirtualTapeResource:
    """All tests for the VirtualTapeResource and
    VirtualTapeResourceManager classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Set up a faked session, and add a faked CPC in DPM mode with a
        tape library, tape link, and related resources.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.16.0', '4.10')
        self.client = Client(self.session)

        # Add a faked CPC
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': CPC_OID,
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
        })
        assert self.faked_cpc.uri == CPC_URI
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

        # Add a faked partition
        self.faked_partition = self.faked_cpc.partitions.add({
            'object-id': PARTITION_OID,
            # object-uri is set up automatically
            'parent': CPC_URI,
            'class': 'partition',
            'name': 'fake-partition1-name',
            'description': 'Partition #1',
            'status': 'stopped',
        })
        assert self.faked_partition.uri == PARTITION_URI

        # Add a faked adapter
        self.faked_adapter = self.faked_cpc.adapters.add({
            'object-id': ADAPTER_OID,
            # object-uri is set up automatically
            'parent': CPC_URI,
            'class': 'adapter',
            'name': 'fake-adapter1-name',
            'description': 'Adapter #1',
            'type': 'fcp',
            'adapter-family': 'ficon',
            'status': 'active',
        })
        assert self.faked_adapter.uri == ADAPTER_URI

        # Add a faked console
        self.faked_console = self.session.hmc.consoles.add({
            # object-id is set up automatically
            # object-uri is set up automatically
            # parent will be automatically set
            # class will be automatically set
            'name': 'fake-console-name',
            'description': 'The HMC',
        })
        self.console = self.client.consoles.console

        # Add a faked tape library
        self.faked_tape_library = self.faked_console.tape_library.add({
            'object-id': TL_OID,
            # object-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'cpc-uri': CPC_URI,
            'name': TL_NAME,
            'description': 'Tape Library #1',
            'state': 'online',
        })
        assert self.faked_tape_library.uri == TL_URI
        self.tape_library = self.console.tape_library.find(name=TL_NAME)

        # Add a faked tape link
        self.faked_tape_link = self.faked_tape_library.tape_links.add({
            'element-id': TLINK_OID,
            # element-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'name': TLINK_NAME,
            'description': 'Tape Link #1',
            'partition-uri': PARTITION_URI,
        })
        assert self.faked_tape_link.uri == TLINK_URI
        self.tape_link = self.tape_library.tape_links.find(name=TLINK_NAME)

    def add_vtr1(self):
        """Add virtual tape resource 1."""

        faked_vtr = self.faked_tape_link.virtual_tape_resources.add({
            'element-id': VTR1_OID,
            # element-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'name': VTR1_NAME,
            'description': 'Virtual Tape Resource #1',
            'device-number': '0001',
            'adapter-port-uri': ADAPTER_PORT_URI,
            'partition-uri': PARTITION_URI,
        })
        return faked_vtr

    def add_vtr2(self):
        """Add virtual tape resource 2."""

        faked_vtr = self.faked_tape_link.virtual_tape_resources.add({
            'element-id': VTR2_OID,
            # element-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'name': VTR2_NAME,
            'description': 'Virtual Tape Resource #2',
            'device-number': '0002',
            'adapter-port-uri': ADAPTER_PORT_URI,
            'partition-uri': PARTITION_URI,
        })
        return faked_vtr

    def test_vtrm_initial_attrs(self):
        """Test initial attributes of VirtualTapeResourceManager."""

        vtr_mgr = self.tape_link.virtual_tape_resources

        assert isinstance(vtr_mgr, VirtualTapeResourceManager)

        # Verify all public properties of the manager object
        assert vtr_mgr.resource_class == VirtualTapeResource
        assert vtr_mgr.session == self.session
        assert vtr_mgr.parent == self.tape_link
        assert vtr_mgr.tape_link == self.tape_link

    # TODO: Test for VirtualTapeResourceManager.__repr__()

    testcases_vtrm_list_full_properties = (
        "full_properties_kwargs, prop_names", [
            ({},
             ['element-uri', 'name', 'device-number', 'adapter-port-uri',
              'partition-uri']),
            (dict(full_properties=False),
             ['element-uri', 'name', 'device-number', 'adapter-port-uri',
              'partition-uri']),
            (dict(full_properties=True),
             ['element-uri', 'name', 'device-number', 'adapter-port-uri',
              'partition-uri', 'description']),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_vtrm_list_full_properties
    )
    def test_vtrm_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test VirtualTapeResourceManager.list() with full_properties."""

        # Add two faked virtual tape resources
        faked_vtr1 = self.add_vtr1()
        faked_vtr2 = self.add_vtr2()

        exp_faked_vtrs = [faked_vtr1, faked_vtr2]
        vtr_mgr = self.tape_link.virtual_tape_resources

        # Execute the code to be tested
        vtrs = vtr_mgr.list(**full_properties_kwargs)

        assert_resources(vtrs, exp_faked_vtrs, prop_names)

    testcases_vtrm_list_filter_args = (
        "filter_args, exp_names", [
            ({'element-id': VTR1_OID},
             [VTR1_NAME]),
            ({'element-id': VTR2_OID},
             [VTR2_NAME]),
            ({'element-id': [VTR1_OID, VTR2_OID]},
             [VTR1_NAME, VTR2_NAME]),
            ({'element-id': [VTR1_OID, VTR1_OID]},
             [VTR1_NAME]),
            ({'element-id': VTR1_OID + 'foo'},
             []),
            ({'element-id': [VTR1_OID, VTR2_OID + 'foo']},
             [VTR1_NAME]),
            ({'element-id': [VTR2_OID + 'foo', VTR1_OID]},
             [VTR1_NAME]),
            ({'name': VTR1_NAME},
             [VTR1_NAME]),
            ({'name': VTR2_NAME},
             [VTR2_NAME]),
            ({'name': [VTR1_NAME, VTR2_NAME]},
             [VTR1_NAME, VTR2_NAME]),
            ({'name': VTR1_NAME + 'foo'},
             []),
            ({'name': [VTR1_NAME, VTR2_NAME + 'foo']},
             [VTR1_NAME]),
            ({'name': [VTR2_NAME + 'foo', VTR1_NAME]},
             [VTR1_NAME]),
            ({'name': [VTR1_NAME, VTR1_NAME]},
             [VTR1_NAME]),
            ({'name': '.*virtual tape resource 1'},
             [VTR1_NAME]),
            ({'name': 'virtual tape resource 1.*'},
             [VTR1_NAME]),
            ({'name': 'virtual tape resource .'},
             [VTR1_NAME, VTR2_NAME]),
            ({'name': '.irtual tape resource 1'},
             [VTR1_NAME]),
            ({'name': '.+'},
             [VTR1_NAME, VTR2_NAME]),
            ({'name': 'virtual tape resource 1.+'},
             []),
            ({'name': '.+virtual tape resource 1'},
             []),
            ({'name': VTR1_NAME,
              'element-id': VTR1_OID},
             [VTR1_NAME]),
            ({'name': VTR1_NAME,
              'element-id': VTR1_OID + 'foo'},
             []),
            ({'name': VTR1_NAME + 'foo',
              'element-id': VTR1_OID},
             []),
            ({'name': VTR1_NAME + 'foo',
              'element-id': VTR1_OID + 'foo'},
             []),
            ({'device-number': '0001'},
             [VTR1_NAME]),
            ({'device-number': '0002'},
             [VTR2_NAME]),
            ({'adapter-port-uri': ADAPTER_PORT_URI},
             [VTR1_NAME, VTR2_NAME]),
            ({'partition-uri': PARTITION_URI},
             [VTR1_NAME, VTR2_NAME]),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_vtrm_list_filter_args
    )
    def test_vtrm_list_filter_args(
            self, filter_args, exp_names):
        """Test VirtualTapeResourceManager.list() with filter_args."""

        # Add two faked virtual tape resources
        self.add_vtr1()
        self.add_vtr2()

        vtr_mgr = self.tape_link.virtual_tape_resources

        # Execute the code to be tested
        vtrs = vtr_mgr.list(filter_args=filter_args)

        assert len(vtrs) == len(exp_names)
        if exp_names:
            names = [vtr.properties['name'] for vtr in vtrs]
            assert set(names) == set(exp_names)

    def test_vtrm_resource_object(self):
        """
        Test VirtualTapeResourceManager.resource_object().

        This test exists for historical reasons, and by now is covered by the
        test for BaseManager.resource_object().
        """

        # Add a faked virtual tape resource
        faked_vtr = self.add_vtr1()
        vtr_oid = faked_vtr.oid

        vtr_mgr = self.tape_link.virtual_tape_resources

        # Execute the code to be tested
        vtr = vtr_mgr.resource_object(vtr_oid)

        vtr_uri = f"{TLINK_URI}/virtual-tape-resources/{vtr_oid}"

        assert isinstance(vtr, VirtualTapeResource)

        # Note: Properties inherited from BaseResource are tested there,
        # but we test them again:
        assert vtr.properties['element-uri'] == vtr_uri
        assert vtr.properties['element-id'] == vtr_oid
        assert vtr.properties['class'] == 'virtual-tape-resource'
        assert vtr.properties['parent'] == TLINK_URI

    def test_vtr_repr(self):
        """Test VirtualTapeResource.__repr__()."""

        # Add a faked virtual tape resource
        faked_vtr = self.add_vtr1()

        vtr_mgr = self.tape_link.virtual_tape_resources
        vtr = vtr_mgr.find(name=faked_vtr.name)

        # Execute the code to be tested
        repr_str = repr(vtr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{vtr.__class__.__name__}\s+at\s+'
            rf'0x{id(vtr):08x}\s+\(\\n.*',
            repr_str)

    testcases_vtr_update_properties_vtrs = (
        "vtr_name", [
            VTR1_NAME,
            VTR2_NAME,
        ]
    )

    testcases_vtr_update_properties_props = (
        "input_props", [
            {},
            {'description': 'New virtual tape resource description'},
            {'device-number': '0003'},
            {'description': 'Updated description', 'device-number': '0004'},
        ]
    )

    @pytest.mark.parametrize(
        *testcases_vtr_update_properties_vtrs
    )
    @pytest.mark.parametrize(
        *testcases_vtr_update_properties_props
    )
    def test_vtr_update_properties(
            self, input_props, vtr_name):
        """Test VirtualTapeResource.update_properties()."""

        # Add faked virtual tape resources
        self.add_vtr1()
        self.add_vtr2()

        vtr_mgr = self.tape_link.virtual_tape_resources
        vtr = vtr_mgr.find(name=vtr_name)

        vtr.pull_full_properties()
        saved_properties = copy.deepcopy(vtr.properties)

        # Execute the code to be tested
        vtr.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in vtr.properties
            prop_value = vtr.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        vtr.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in vtr.properties
            prop_value = vtr.properties[prop_name]
            assert prop_value == exp_prop_value

    def test_vtr_update_name(self):
        """
        Test VirtualTapeResource.update_properties() with 'name' property.
        """

        # Add a faked virtual tape resource
        faked_vtr = self.add_vtr1()
        vtr_name = faked_vtr.name

        vtr_mgr = self.tape_link.virtual_tape_resources
        vtr = vtr_mgr.find(name=vtr_name)

        new_vtr_name = "new-" + vtr_name

        # Execute the code to be tested
        vtr.update_properties(
            properties={'name': new_vtr_name})

        # Verify that the resource is no longer found by its old name, using
        # list() (this does not use the name-to-URI cache).
        vtrs_list = vtr_mgr.list(
            filter_args=dict(name=vtr_name))
        assert len(vtrs_list) == 0

        # Verify that the resource is no longer found by its old name, using
        # find() (this uses the name-to-URI cache).
        with pytest.raises(NotFound):
            vtr_mgr.find(name=vtr_name)

        # Verify that the resource object already reflects the update, even
        # though it has not been refreshed yet.
        assert vtr.properties['name'] == new_vtr_name

        # Refresh the resource object and verify that it still reflects the
        # update.
        vtr.pull_full_properties()
        assert vtr.properties['name'] == new_vtr_name

        # Verify that the resource can be found by its new name, using find()
        new_vtr_find = vtr_mgr.find(
            name=new_vtr_name)
        assert new_vtr_find.properties['name'] == \
            new_vtr_name

        # Verify that the resource can be found by its new name, using list()
        new_vtrs_list = vtr_mgr.list(
            filter_args=dict(name=new_vtr_name))
        assert len(new_vtrs_list) == 1
        new_vtr_list = new_vtrs_list[0]
        assert new_vtr_list.properties['name'] == \
            new_vtr_name

    def test_vtr_attached_partition_property(self):
        """Test VirtualTapeResource.attached_partition property."""

        # Add a faked virtual tape resource
        faked_vtr = self.add_vtr1()

        vtr_mgr = self.tape_link.virtual_tape_resources
        vtr = vtr_mgr.find(name=faked_vtr.name)

        # Execute the code to be tested
        partition = vtr.attached_partition

        # Verify the result
        assert partition is not None
        assert partition.uri == PARTITION_URI

    def test_vtr_adapter_port_property(self):
        """Test VirtualTapeResource.adapter_port property."""

        # Add a faked virtual tape resource
        faked_vtr = self.add_vtr1()

        vtr_mgr = self.tape_link.virtual_tape_resources
        vtr = vtr_mgr.find(name=faked_vtr.name)

        # Execute the code to be tested
        adapter_port = vtr.adapter_port

        # Verify the result
        assert adapter_port is not None
        assert adapter_port.uri == ADAPTER_PORT_URI

    def test_vtr_update_device_number(self):
        """Test updating device-number property."""

        # Add a faked virtual tape resource
        faked_vtr = self.add_vtr1()

        vtr_mgr = self.tape_link.virtual_tape_resources
        vtr = vtr_mgr.find(name=faked_vtr.name)

        old_device_number = vtr.get_property('device-number')
        new_device_number = '0005'

        # Execute the code to be tested
        vtr.update_properties(properties={'device-number': new_device_number})

        # Verify the update
        assert vtr.get_property('device-number') == new_device_number
        assert vtr.get_property('device-number') != old_device_number

    def test_vtr_multiple_property_updates(self):
        """Test updating multiple properties at once."""

        # Add a faked virtual tape resource
        faked_vtr = self.add_vtr1()

        vtr_mgr = self.tape_link.virtual_tape_resources
        vtr = vtr_mgr.find(name=faked_vtr.name)

        new_props = {
            'name': 'updated-vtr-name',
            'description': 'Updated description',
            'device-number': '0006',
        }

        # Execute the code to be tested
        vtr.update_properties(properties=new_props)

        # Verify all updates
        vtr.pull_full_properties()
        assert vtr.get_property('name') == new_props['name']
        assert vtr.get_property('description') == new_props['description']
        assert vtr.get_property('device-number') == new_props['device-number']

    def test_vtr_list_empty(self):
        """Test listing virtual tape resources when none exist."""

        vtr_mgr = self.tape_link.virtual_tape_resources

        # Execute the code to be tested
        vtrs = vtr_mgr.list()

        # Verify the result
        assert isinstance(vtrs, list)
        assert len(vtrs) == 0

    def test_vtr_find_nonexistent(self):
        """Test finding a non-existent virtual tape resource."""

        vtr_mgr = self.tape_link.virtual_tape_resources

        # Execute the code to be tested and expect NotFound
        with pytest.raises(NotFound):
            vtr_mgr.find(name='nonexistent-vtr')

    def test_vtr_properties_consistency(self):
        """Test that virtual tape resource properties are consistent."""

        # Add a faked virtual tape resource
        faked_vtr = self.add_vtr1()

        vtr_mgr = self.tape_link.virtual_tape_resources
        vtr = vtr_mgr.find(name=faked_vtr.name)

        # Pull full properties to ensure all properties are available
        vtr.pull_full_properties()

        # Verify property consistency
        assert vtr.name == vtr.properties['name']
        assert vtr.uri == vtr.properties['element-uri']
        assert vtr.properties['partition-uri'] == PARTITION_URI
        assert vtr.properties['adapter-port-uri'] == ADAPTER_PORT_URI

    def test_vtr_filter_by_device_number(self):
        """Test filtering virtual tape resources by device number."""

        # Add faked virtual tape resources with different device numbers
        self.add_vtr1()  # device-number: '0001'
        self.add_vtr2()  # device-number: '0002'

        vtr_mgr = self.tape_link.virtual_tape_resources

        # Execute the code to be tested
        vtrs = vtr_mgr.list(filter_args={'device-number': '0001'})

        # Verify the result
        assert len(vtrs) == 1
        assert vtrs[0].get_property('device-number') == '0001'
        assert vtrs[0].name == VTR1_NAME

    def test_vtr_filter_by_partition_uri(self):
        """Test filtering virtual tape resources by partition URI."""

        # Add faked virtual tape resources
        self.add_vtr1()
        self.add_vtr2()

        vtr_mgr = self.tape_link.virtual_tape_resources

        # Execute the code to be tested
        vtrs = vtr_mgr.list(filter_args={'partition-uri': PARTITION_URI})

        # Verify the result
        assert len(vtrs) == 2
        for vtr in vtrs:
            assert vtr.get_property('partition-uri') == PARTITION_URI

    def test_vtr_filter_by_adapter_port_uri(self):
        """Test filtering virtual tape resources by adapter port URI."""

        # Add faked virtual tape resources
        self.add_vtr1()
        self.add_vtr2()

        vtr_mgr = self.tape_link.virtual_tape_resources

        # Execute the code to be tested
        vtrs = vtr_mgr.list(filter_args={'adapter-port-uri': ADAPTER_PORT_URI})

        # Verify the result
        assert len(vtrs) == 2
        for vtr in vtrs:
            assert vtr.get_property('adapter-port-uri') == ADAPTER_PORT_URI
