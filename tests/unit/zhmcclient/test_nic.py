# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Unit tests for _nic module.
"""

from __future__ import absolute_import, print_function

import pytest
import re
import copy

from zhmcclient import Client, Nic, HTTPError, NotFound
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked NICs:
NIC1_OID = 'nic 1-oid'
NIC1_NAME = 'nic 1'
NIC2_OID = 'nic 2-oid'
NIC2_NAME = 'nic 2'

# URIs and Object IDs of elements referenced in NIC properties:
VSWITCH11_OID = 'fake-vswitch11-oid'
VSWITCH11_URI = '/api/virtual-switches/{}'.format(VSWITCH11_OID)
ROCE2_OID = 'fake-roce2-oid'
PORT21_OID = 'fake-port21-oid'
PORT21_URI = '/api/adapters/{}/network-ports/{}'.format(ROCE2_OID, PORT21_OID)


class TestNic(object):
    """All tests for Nic and NicManager classes."""

    def setup_method(self):
        """
        Set up a faked session, and add a faked CPC in DPM mode with one
        partition that has no NICs.
        Add one OSA adapter, port and vswitch, for tests with OSA-backed NICs.
        Add one ROSE adapter and port, for tests with ROCE-backed NICs.
        """

        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

        # Add a CPC in DPM mode
        self.faked_cpc = self.session.hmc.cpcs.add({
            'element-id': 'fake-cpc1-oid',
            # element-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
        })
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

        # Add a partition to the CPC
        self.faked_partition = self.faked_cpc.partitions.add({
            'element-id': 'fake-part1-oid',
            # element-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': 'fake-part1-name',
            'description': 'Partition #1',
            'status': 'active',
            'initial-memory': 1024,
            'maximum-memory': 2048,
        })
        self.partition = self.cpc.partitions.find(name='fake-part1-name')

        # Add an OSA adapter, port and vswitch to the CPC
        self.faked_osa1 = self.faked_cpc.adapters.add({
            'object-id': 'osa1-oid',
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': 'osa1',
            'description': 'OSA #1',
            'status': 'active',
            'type': 'osd',
            'adapter-id': '123',
            'detected-card-type': 'osa-express-5s-10gb',
            'card-location': '1234-5678-J.01',
            'port-count': 1,
            'network-port-uris': [],
            'state': 'online',
            'configured-capacity': 80,
            'used-capacity': 0,
            'allowed-capacity': 80,
            'maximum-total-capacity': 80,
            'channel-path-id': '1D',
            'physical-channel-status': 'operating',
        })
        self.faked_port11 = self.faked_osa1.ports.add({
            'element-id': 'fake-port11-oid',
            'parent': self.faked_osa1.uri,
            'class': 'network-port',
            'index': 0,
            'name': 'fake-port11-name',
            'description': 'OSA #1 Port #1',
        })
        self.faked_vswitch11 = self.faked_cpc.virtual_switches.add({
            'object-id': VSWITCH11_OID,
            'parent': self.faked_cpc.uri,
            'class': 'virtual-switch',
            'name': 'fake-vswitch11-name',
            'description': 'Vswitch for OSA #1 Port #1',
            'type': 'osa',
            'backing-adapter-uri': self.faked_osa1.uri,
            'port': self.faked_port11.properties['index'],
            'connected-vnic-uris': [],
        })
        assert VSWITCH11_URI == self.faked_vswitch11.uri

        # Add a ROCE adapter and port to the CPC
        self.faked_roce2 = self.faked_cpc.adapters.add({
            'object-id': ROCE2_OID,
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': 'roce2',
            'description': 'ROCE #2',
            'status': 'active',
            'type': 'roce',
            'adapter-id': '123',
            'detected-card-type': '10gbe-roce-express',
            'card-location': '1234-5678-J.01',
            'port-count': 1,
            'network-port-uris': [],
            'state': 'online',
            'configured-capacity': 80,
            'used-capacity': 0,
            'allowed-capacity': 80,
            'maximum-total-capacity': 80,
            'physical-channel-status': 'operating',
        })
        self.faked_port21 = self.faked_roce2.ports.add({
            'element-id': PORT21_OID,
            'parent': self.faked_roce2.uri,
            'class': 'network-port',
            'index': 1,
            'name': 'fake-port21-name',
            'description': 'ROCE #2 Port #1',
        })
        assert PORT21_URI == self.faked_port21.uri

    def add_nic1(self):
        """Add a faked OSA NIC 1 to the faked partition."""
        faked_nic = self.faked_partition.nics.add({
            'element-id': NIC1_OID,
            # element-uri will be automatically set
            'parent': self.faked_partition.uri,
            'class': 'nic',
            'name': NIC1_NAME,
            'description': 'NIC ' + NIC1_NAME,
            'type': 'osd',
            'virtual-switch-uri': VSWITCH11_URI,
            'device-number': '1111',
            'ssc-management-nic': False,
        })
        return faked_nic

    def add_nic2(self):
        """Add a faked ROCE NIC 2 to the faked partition."""
        faked_nic = self.faked_partition.nics.add({
            'element-id': NIC2_OID,
            # element-uri will be automatically set
            'parent': self.faked_partition.uri,
            'class': 'nic',
            'name': NIC2_NAME,
            'description': 'NIC ' + NIC2_NAME,
            'type': 'roce',
            'network-adapter-port-uri': PORT21_URI,
            'device-number': '1112',
            'ssc-management-nic': False,
        })
        return faked_nic

    def test_nicmanager_initial_attrs(self):
        """Test initial attributes of NicManager."""

        nic_mgr = self.partition.nics

        # Verify all public properties of the manager object
        assert nic_mgr.resource_class == Nic
        assert nic_mgr.session == self.session
        assert nic_mgr.parent == self.partition
        assert nic_mgr.partition == self.partition

    # TODO: Test for NicManager.__repr__()

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(),
             ['element-uri']),
            (dict(full_properties=False),
             ['element-uri']),
            (dict(full_properties=True),
             None),
        ]
    )
    def test_nicmanager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test NicManager.list() with full_properties."""

        # Add two faked NICs
        faked_nic1 = self.add_nic1()
        faked_nic2 = self.add_nic2()

        exp_faked_nics = [faked_nic1, faked_nic2]
        nic_mgr = self.partition.nics

        # Execute the code to be tested
        nics = nic_mgr.list(**full_properties_kwargs)

        assert_resources(nics, exp_faked_nics, prop_names)

    @pytest.mark.parametrize(
        "filter_args, exp_oids", [
            ({'element-id': NIC1_OID},
             [NIC1_OID]),
            ({'element-id': NIC2_OID},
             [NIC2_OID]),
            ({'element-id': [NIC1_OID, NIC2_OID]},
             [NIC1_OID, NIC2_OID]),
            ({'element-id': [NIC1_OID, NIC1_OID]},
             [NIC1_OID]),
            ({'element-id': NIC1_OID + 'foo'},
             []),
            ({'element-id': [NIC1_OID, NIC2_OID + 'foo']},
             [NIC1_OID]),
            ({'element-id': [NIC2_OID + 'foo', NIC1_OID]},
             [NIC1_OID]),
            ({'name': NIC1_NAME},
             [NIC1_OID]),
            ({'name': NIC2_NAME},
             [NIC2_OID]),
            ({'name': [NIC1_NAME, NIC2_NAME]},
             [NIC1_OID, NIC2_OID]),
            ({'name': NIC1_NAME + 'foo'},
             []),
            ({'name': [NIC1_NAME, NIC2_NAME + 'foo']},
             [NIC1_OID]),
            ({'name': [NIC2_NAME + 'foo', NIC1_NAME]},
             [NIC1_OID]),
            ({'name': [NIC1_NAME, NIC1_NAME]},
             [NIC1_OID]),
            ({'name': '.*nic 1'},
             [NIC1_OID]),
            ({'name': 'nic 1.*'},
             [NIC1_OID]),
            ({'name': 'nic .'},
             [NIC1_OID, NIC2_OID]),
            ({'name': '.ic 1'},
             [NIC1_OID]),
            ({'name': '.+'},
             [NIC1_OID, NIC2_OID]),
            ({'name': 'nic 1.+'},
             []),
            ({'name': '.+nic 1'},
             []),
            ({'name': NIC1_NAME,
              'element-id': NIC1_OID},
             [NIC1_OID]),
            ({'name': NIC1_NAME,
              'element-id': NIC1_OID + 'foo'},
             []),
            ({'name': NIC1_NAME + 'foo',
              'element-id': NIC1_OID},
             []),
            ({'name': NIC1_NAME + 'foo',
              'element-id': NIC1_OID + 'foo'},
             []),
        ]
    )
    def test_nicmanager_list_filter_args(self, filter_args, exp_oids):
        """Test NicManager.list() with filter_args."""

        # Add two faked NICs
        self.add_nic1()
        self.add_nic2()

        nic_mgr = self.partition.nics

        # Execute the code to be tested
        nics = nic_mgr.list(filter_args=filter_args)

        assert len(nics) == len(exp_oids)
        if exp_oids:
            oids = [nic.properties['element-id'] for nic in nics]
            assert set(oids) == set(exp_oids)

    @pytest.mark.parametrize(
        "initial_partition_status, exp_status_exc", [
            ('stopped', None),
            ('terminated', None),
            ('starting', HTTPError({'http-status': 409, 'reason': 1})),
            ('active', None),
            ('stopping', HTTPError({'http-status': 409, 'reason': 1})),
            ('degraded', None),
            ('reservation-error', None),
            ('paused', None),
        ]
    )
    @pytest.mark.parametrize(
        "input_props, exp_prop_names, exp_prop_exc", [
            ({},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-nic-x'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'network-adapter-port-uri': PORT21_URI},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'virtual-switch-uri': VSWITCH11_URI},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-nic-x',
              'network-adapter-port-uri': PORT21_URI},
             ['element-uri', 'name', 'network-adapter-port-uri'],
             None),
            ({'name': 'fake-nic-x',
              'virtual-switch-uri': VSWITCH11_URI},
             ['element-uri', 'name', 'virtual-switch-uri'],
             None),
        ]
    )
    def test_nicmanager_create(
            self, input_props, exp_prop_names, exp_prop_exc,
            initial_partition_status, exp_status_exc):
        """Test NicManager.create()."""

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = initial_partition_status

        nic_mgr = self.partition.nics

        if exp_status_exc:
            exp_exc = exp_status_exc
        elif exp_prop_exc:
            exp_exc = exp_prop_exc
        else:
            exp_exc = None

        if exp_exc:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                nic = nic_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            # Note: the Nic object returned by Nic.create() has
            # the input properties plus 'element-uri' plus 'element-id'.
            nic = nic_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(nic, Nic)
            nic_name = nic.name
            exp_nic_name = nic.properties['name']
            assert nic_name == exp_nic_name
            nic_uri = nic.uri
            exp_nic_uri = nic.properties['element-uri']
            assert nic_uri == exp_nic_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in nic.properties
                if prop_name in input_props:
                    value = nic.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_nic_repr(self):
        """Test Nic.__repr__()."""

        # Add a faked nic
        faked_nic = self.add_nic1()

        nic_mgr = self.partition.nics
        nic = nic_mgr.find(name=faked_nic.name)

        # Execute the code to be tested
        repr_str = repr(nic)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=nic.__class__.__name__,
                               id=id(nic)),
                        repr_str)

    @pytest.mark.parametrize(
        "initial_partition_status, exp_exc", [
            ('stopped', None),
            ('terminated', None),
            ('starting', HTTPError({'http-status': 409, 'reason': 1})),
            ('active', None),
            ('stopping', HTTPError({'http-status': 409, 'reason': 1})),
            ('degraded', None),
            ('reservation-error', None),
            ('paused', None),
        ]
    )
    def test_nic_delete(self, initial_partition_status, exp_exc):
        """Test Nic.delete()."""

        # Add a faked NIC to be tested and another one
        faked_nic = self.add_nic1()
        self.add_nic2()

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = initial_partition_status

        nic_mgr = self.partition.nics

        nic = nic_mgr.find(name=faked_nic.name)

        if exp_exc:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                nic.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the NIC still exists
            nic_mgr.find(name=faked_nic.name)

        else:

            # Execute the code to be tested.
            nic.delete()

            # Check that the NIC no longer exists
            with pytest.raises(NotFound) as exc_info:
                nic_mgr.find(name=faked_nic.name)

    def test_nic_delete_create_same_name(self):
        """Test Nic.delete() followed by Nic.create() with same name."""

        # Add a faked NIC to be tested and another one
        faked_nic = self.add_nic1()
        nic_name = faked_nic.name
        self.add_nic2()

        # Construct the input properties for a third NIC with same name
        part3_props = copy.deepcopy(faked_nic.properties)
        part3_props['description'] = 'Third NIC'

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = 'stopped'  # deletable

        nic_mgr = self.partition.nics
        nic = nic_mgr.find(name=nic_name)

        # Execute the deletion code to be tested.
        nic.delete()

        # Check that the NIC no longer exists
        with pytest.raises(NotFound):
            nic_mgr.find(name=nic_name)

        # Execute the creation code to be tested.
        nic_mgr.create(part3_props)

        # Check that the NIC exists again under that name
        nic3 = nic_mgr.find(name=nic_name)
        description = nic3.get_property('description')
        assert description == 'Third NIC'

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New NIC description'},
            {'device-number': 'FEDC',
             'description': 'New NIC description'},
        ]
    )
    def test_nic_update_properties(self, input_props):
        """Test Nic.update_properties()."""

        # Add a faked NIC
        faked_nic = self.add_nic1()

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = 'stopped'  # updatable

        nic_mgr = self.partition.nics
        nic = nic_mgr.find(name=faked_nic.name)

        nic.pull_full_properties()
        saved_properties = copy.deepcopy(nic.properties)

        # Execute the code to be tested
        nic.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in nic.properties
            prop_value = nic.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        nic.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in nic.properties
            prop_value = nic.properties[prop_name]
            assert prop_value == exp_prop_value

    def test_nic_update_name(self):
        """Test Nic.update_properties() with 'name' property."""

        # Add a faked NIC
        faked_nic = self.add_nic1()
        nic_name = faked_nic.name

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = 'stopped'  # updatable

        nic_mgr = self.partition.nics
        nic = nic_mgr.find(name=nic_name)

        new_nic_name = "new-" + nic_name

        # Execute the code to be tested
        nic.update_properties(properties={'name': new_nic_name})

        # Verify that the resource is no longer found by its old name, using
        # list() (this does not use the name-to-URI cache).
        nics_list = nic_mgr.list(
            filter_args=dict(name=nic_name))
        assert len(nics_list) == 0

        # Verify that the resource is no longer found by its old name, using
        # find() (this uses the name-to-URI cache).
        with pytest.raises(NotFound):
            nic_mgr.find(name=nic_name)

        # Verify that the resource object already reflects the update, even
        # though it has not been refreshed yet.
        assert nic.properties['name'] == new_nic_name

        # Refresh the resource object and verify that it still reflects the
        # update.
        nic.pull_full_properties()
        assert nic.properties['name'] == new_nic_name

        # Verify that the resource can be found by its new name, using find()
        new_nic_find = nic_mgr.find(name=new_nic_name)
        assert new_nic_find.properties['name'] == new_nic_name

        # Verify that the resource can be found by its new name, using list()
        new_nics_list = nic_mgr.list(
            filter_args=dict(name=new_nic_name))
        assert len(new_nics_list) == 1
        new_nic_list = new_nics_list[0]
        assert new_nic_list.properties['name'] == new_nic_name

    def test_nicmanager_resource_object(self):
        """
        Test NicManager.resource_object().

        This test exists for historical reasons, and by now is covered by the
        test for BaseManager.resource_object().
        """

        nic_mgr = self.partition.nics
        nic_oid = 'fake-nic-id0711'

        # Execute the code to be tested
        nic = nic_mgr.resource_object(nic_oid)

        nic_uri = self.partition.uri + "/nics/" + nic_oid

        assert isinstance(nic, Nic)
        assert nic.uri == nic_uri
        assert nic.properties['element-uri'] == nic_uri
        assert nic.properties['element-id'] == nic_oid
        assert nic.properties['class'] == 'nic'
        assert nic.properties['parent'] == self.partition.uri
