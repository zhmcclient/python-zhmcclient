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
Unit tests for _hba module.
"""

from __future__ import absolute_import, print_function

import pytest
import re
import copy

from zhmcclient import Client, Hba, HTTPError, NotFound
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked HBAs:
HBA1_OID = 'hba 1-oid'
HBA1_NAME = 'hba 1'
HBA2_OID = 'hba 2-oid'
HBA2_NAME = 'hba 2'

# URIs and Object IDs of elements referenced in HBA properties:
FCP1_OID = 'fake-fcp1-oid'
PORT11_OID = 'fake-port11-oid'
PORT11_URI = '/api/adapters/{}/storage-ports/{}'.format(FCP1_OID, PORT11_OID)


class TestHba(object):
    """All tests for Hba and HbaManager classes."""

    def setup_method(self):
        """
        Set up a faked session, and add a faked CPC in DPM mode with one
        partition that has no HBAs.
        Add one FCP adapter and port.
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

        # Add an FCP adapter and port to the CPC
        self.faked_fcp1 = self.faked_cpc.adapters.add({
            'object-id': FCP1_OID,
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': 'fcp1',
            'description': 'FCP #1',
            'status': 'active',
            'type': 'fcp',
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
        self.faked_port11 = self.faked_fcp1.ports.add({
            'element-id': PORT11_OID,
            'parent': self.faked_fcp1.uri,
            'class': 'storage-port',
            'index': 1,
            'name': 'fake-port11-name',
            'description': 'FCP #1 Port #1',
        })
        assert PORT11_URI == self.faked_port11.uri

    def add_hba1(self):
        """Add a faked HBA 1 to the faked partition."""
        faked_hba = self.faked_partition.hbas.add({
            'element-id': HBA1_OID,
            # element-uri will be automatically set
            'parent': self.faked_partition.uri,
            'class': 'hba',
            'name': HBA1_NAME,
            'description': 'HBA ' + HBA1_NAME,
            'adapter-port-uri': PORT11_URI,
            'wwpn': 'AABBCCDDEEFF0011',
            'device-number': '1111',
        })
        return faked_hba

    def add_hba2(self):
        """Add a faked HBA 2 to the faked partition."""
        faked_hba = self.faked_partition.hbas.add({
            'element-id': HBA2_OID,
            # element-uri will be automatically set
            'parent': self.faked_partition.uri,
            'class': 'hba',
            'name': HBA2_NAME,
            'description': 'HBA ' + HBA2_NAME,
            'adapter-port-uri': PORT11_URI,
            'wwpn': 'AABBCCDDEEFF0012',
            'device-number': '1112',
        })
        return faked_hba

    def test_hbamanager_initial_attrs(self):
        """Test initial attributes of HbaManager."""

        hba_mgr = self.partition.hbas

        # Verify all public properties of the manager object
        assert hba_mgr.resource_class == Hba
        assert hba_mgr.session == self.session
        assert hba_mgr.parent == self.partition
        assert hba_mgr.partition == self.partition

    # TODO: Test for HbaManager.__repr__()

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
    def test_hbamanager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test HbaManager.list() with full_properties."""

        # Add two faked HBAs
        faked_hba1 = self.add_hba1()
        faked_hba2 = self.add_hba2()

        exp_faked_hbas = [faked_hba1, faked_hba2]
        hba_mgr = self.partition.hbas

        # Execute the code to be tested
        hbas = hba_mgr.list(**full_properties_kwargs)

        assert_resources(hbas, exp_faked_hbas, prop_names)

    @pytest.mark.parametrize(
        "filter_args, exp_oids", [
            ({'element-id': HBA1_OID},
             [HBA1_OID]),
            ({'element-id': HBA2_OID},
             [HBA2_OID]),
            ({'element-id': [HBA1_OID, HBA2_OID]},
             [HBA1_OID, HBA2_OID]),
            ({'element-id': [HBA1_OID, HBA1_OID]},
             [HBA1_OID]),
            ({'element-id': HBA1_OID + 'foo'},
             []),
            ({'element-id': [HBA1_OID, HBA2_OID + 'foo']},
             [HBA1_OID]),
            ({'element-id': [HBA2_OID + 'foo', HBA1_OID]},
             [HBA1_OID]),
            ({'name': HBA1_NAME},
             [HBA1_OID]),
            ({'name': HBA2_NAME},
             [HBA2_OID]),
            ({'name': [HBA1_NAME, HBA2_NAME]},
             [HBA1_OID, HBA2_OID]),
            ({'name': HBA1_NAME + 'foo'},
             []),
            ({'name': [HBA1_NAME, HBA2_NAME + 'foo']},
             [HBA1_OID]),
            ({'name': [HBA2_NAME + 'foo', HBA1_NAME]},
             [HBA1_OID]),
            ({'name': [HBA1_NAME, HBA1_NAME]},
             [HBA1_OID]),
            ({'name': '.*hba 1'},
             [HBA1_OID]),
            ({'name': 'hba 1.*'},
             [HBA1_OID]),
            ({'name': 'hba .'},
             [HBA1_OID, HBA2_OID]),
            ({'name': '.ba 1'},
             [HBA1_OID]),
            ({'name': '.+'},
             [HBA1_OID, HBA2_OID]),
            ({'name': 'hba 1.+'},
             []),
            ({'name': '.+hba 1'},
             []),
            ({'name': HBA1_NAME,
              'element-id': HBA1_OID},
             [HBA1_OID]),
            ({'name': HBA1_NAME,
              'element-id': HBA1_OID + 'foo'},
             []),
            ({'name': HBA1_NAME + 'foo',
              'element-id': HBA1_OID},
             []),
            ({'name': HBA1_NAME + 'foo',
              'element-id': HBA1_OID + 'foo'},
             []),
        ]
    )
    def test_hbamanager_list_filter_args(self, filter_args, exp_oids):
        """Test HbaManager.list() with filter_args."""

        # Add two faked HBAs
        self.add_hba1()
        self.add_hba2()

        hba_mgr = self.partition.hbas

        # Execute the code to be tested
        hbas = hba_mgr.list(filter_args=filter_args)

        assert len(hbas) == len(exp_oids)
        if exp_oids:
            oids = [hba.properties['element-id'] for hba in hbas]
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
            ({'name': 'fake-hba-x'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'adapter-port-uri': PORT11_URI},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-hba-x',
              'adapter-port-uri': PORT11_URI},
             ['element-uri', 'name', 'adapter-port-uri'],
             None),
        ]
    )
    def test_hbamanager_create(
            self, input_props, exp_prop_names, exp_prop_exc,
            initial_partition_status, exp_status_exc):
        """Test HbaManager.create()."""

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = initial_partition_status

        hba_mgr = self.partition.hbas

        if exp_status_exc:
            exp_exc = exp_status_exc
        elif exp_prop_exc:
            exp_exc = exp_prop_exc
        else:
            exp_exc = None

        if exp_exc:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                hba = hba_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            # Note: the Hba object returned by Hba.create() has
            # the input properties plus 'element-uri' plus 'element-id'.
            hba = hba_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(hba, Hba)
            hba_name = hba.name
            exp_hba_name = hba.properties['name']
            assert hba_name == exp_hba_name
            hba_uri = hba.uri
            exp_hba_uri = hba.properties['element-uri']
            assert hba_uri == exp_hba_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in hba.properties
                if prop_name in input_props:
                    value = hba.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_hba_repr(self):
        """Test Hba.__repr__()."""

        # Add a faked hba
        faked_hba = self.add_hba1()

        hba_mgr = self.partition.hbas
        hba = hba_mgr.find(name=faked_hba.name)

        # Execute the code to be tested
        repr_str = repr(hba)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=hba.__class__.__name__,
                               id=id(hba)),
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
    def test_hba_delete(self, initial_partition_status, exp_exc):
        """Test Hba.delete()."""

        # Add a faked HBA to be tested and another one
        faked_hba = self.add_hba1()
        self.add_hba2()

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = initial_partition_status

        hba_mgr = self.partition.hbas

        hba = hba_mgr.find(name=faked_hba.name)

        if exp_exc:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                hba.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the HBA still exists
            hba_mgr.find(name=faked_hba.name)

        else:

            # Execute the code to be tested.
            hba.delete()

            # Check that the HBA no longer exists
            with pytest.raises(NotFound) as exc_info:
                hba_mgr.find(name=faked_hba.name)

    def test_hba_delete_create_same_name(self):
        """Test Hba.delete() followed by Hba.create() with same name."""

        # Add a faked HBA to be tested and another one
        faked_hba = self.add_hba1()
        hba_name = faked_hba.name
        self.add_hba2()

        # Construct the input properties for a third HBA with same name
        part3_props = copy.deepcopy(faked_hba.properties)
        part3_props['description'] = 'Third HBA'

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = 'stopped'  # deletable

        hba_mgr = self.partition.hbas
        hba = hba_mgr.find(name=hba_name)

        # Execute the deletion code to be tested.
        hba.delete()

        # Check that the HBA no longer exists
        with pytest.raises(NotFound):
            hba_mgr.find(name=hba_name)

        # Execute the creation code to be tested.
        hba_mgr.create(part3_props)

        # Check that the HBA exists again under that name
        hba3 = hba_mgr.find(name=hba_name)
        description = hba3.get_property('description')
        assert description == 'Third HBA'

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New HBA description'},
            {'device-number': 'FEDC',
             'description': 'New HBA description'},
        ]
    )
    def test_hba_update_properties(self, input_props):
        """Test Hba.update_properties()."""

        # Add a faked HBA
        faked_hba = self.add_hba1()

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = 'stopped'  # updatable

        hba_mgr = self.partition.hbas
        hba = hba_mgr.find(name=faked_hba.name)

        hba.pull_full_properties()
        saved_properties = copy.deepcopy(hba.properties)

        # Execute the code to be tested
        hba.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in hba.properties
            prop_value = hba.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        hba.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in hba.properties
            prop_value = hba.properties[prop_name]
            assert prop_value == exp_prop_value

    def test_hba_update_name(self):
        """Test Hba.update_properties() with 'name' property."""

        # Add a faked HBA
        faked_hba = self.add_hba1()
        hba_name = faked_hba.name

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = 'stopped'  # updatable

        hba_mgr = self.partition.hbas
        hba = hba_mgr.find(name=hba_name)

        new_hba_name = "new-" + hba_name

        # Execute the code to be tested
        hba.update_properties(properties={'name': new_hba_name})

        # Verify that the resource is no longer found by its old name, using
        # list() (this does not use the name-to-URI cache).
        hbas_list = hba_mgr.list(
            filter_args=dict(name=hba_name))
        assert len(hbas_list) == 0

        # Verify that the resource is no longer found by its old name, using
        # find() (this uses the name-to-URI cache).
        with pytest.raises(NotFound):
            hba_mgr.find(name=hba_name)

        # Verify that the resource object already reflects the update, even
        # though it has not been refreshed yet.
        assert hba.properties['name'] == new_hba_name

        # Refresh the resource object and verify that it still reflects the
        # update.
        hba.pull_full_properties()
        assert hba.properties['name'] == new_hba_name

        # Verify that the resource can be found by its new name, using find()
        new_hba_find = hba_mgr.find(name=new_hba_name)
        assert new_hba_find.properties['name'] == new_hba_name

        # Verify that the resource can be found by its new name, using list()
        new_hbas_list = hba_mgr.list(
            filter_args=dict(name=new_hba_name))
        assert len(new_hbas_list) == 1
        new_hba_list = new_hbas_list[0]
        assert new_hba_list.properties['name'] == new_hba_name

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
    def test_hba_reassign_port(self, initial_partition_status, exp_exc):
        """Test Hba.reassign_port()."""

        # Add a faked HBA to be tested.
        # Its port points to a faked URI.
        faked_hba = self.add_hba1()

        # Add a faked FCP with one port that the HBA will be reassigned to
        faked_adapter = self.faked_cpc.adapters.add({
            'object-id': 'fake-fcp1-oid',
            # object-uri is auto-set based upon object-id
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': 'fake-fcp1',
            'description': 'FCP #1',
            'status': 'active',
            'type': 'fcp',
            # adapter-family is auto-set based upon type
            'adapter-id': '123',
            'detected-card-type': 'ficon-express-16s',
            'card-location': '1234-5678-J.01',
            'port-count': 1,
            'storage-port-uris': [],
            'state': 'online',
            'configured-capacity': 80,
            'used-capacity': 0,
            'allowed-capacity': 80,
            'maximum-total-capacity': 80,
            'channel-path-id': '1B',
            'physical-channel-status': 'operating',
        })
        adapter = self.cpc.adapters.find(name='fake-fcp1')
        faked_adapter.ports.add({
            'element-id': 'fake-port1-oid',
            # element-uri is auto-set based upon object-id
            'parent': faked_adapter.uri,
            'class': 'storage-port',
            'name': 'fake-port1',
            'description': 'FCP #1 Port 1',
            'index': 0,
            'fabric-id': None,
        })
        port = adapter.ports.find(name='fake-port1')

        # Set the status of the faked partition
        self.faked_partition.properties['status'] = initial_partition_status

        # The HBA object we will perform the test on
        hba = self.partition.hbas.find(name=faked_hba.name)

        # Save the HBA properties for later comparison
        hba.pull_full_properties()
        saved_properties = copy.deepcopy(hba.properties)

        if exp_exc:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                hba.reassign_port(port)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the port of the HBA is unchanged ...
            prop_name = 'adapter-port-uri'
            # ... in the resource object:
            assert hba.properties[prop_name] == saved_properties[prop_name]
            # ... and again when refreshed from the mock state:
            hba.pull_full_properties()
            assert hba.properties[prop_name] == saved_properties[prop_name]

        else:

            # Execute the code to be tested.
            hba.reassign_port(port)

            # Check that the port of the HBA has been set ...
            # ... in the resource object:
            prop_name = 'adapter-port-uri'
            assert hba.properties[prop_name] == port.uri
            # ... and again when refreshed from the mock state:
            hba.pull_full_properties()
            assert hba.properties[prop_name] == port.uri
