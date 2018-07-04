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
Unit tests for _adapter module.
"""

from __future__ import absolute_import, print_function

import pytest
import copy
import re

from zhmcclient import Client, Adapter, NotFound, HTTPError
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked adapters:
OSA1_OID = 'osa1-oid'
OSA1_NAME = 'osa 1'
HS2_OID = 'hs2-oid'
HS2_NAME = 'hs 2'


class TestAdapter(object):
    """All tests for the Adapter and AdapterManager classes."""

    def setup_method(self):
        """
        Set up a faked session, and add a faked CPC in DPM mode without any
        child resources.
        """

        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'fake-cpc1-oid',
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
            'machine-type': '2964',  # z13
        })
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

    def add_standard_osa(self):
        """Add a standard OSA adapter with one port to the faked HMC."""

        # Adapter properties that will be auto-set:
        # - object-uri
        # - adapter-family
        # - network-port-uris (to empty array)
        faked_osa1 = self.faked_cpc.adapters.add({
            'object-id': OSA1_OID,
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': OSA1_NAME,
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
            'physical-channel-status': 'operating',
        })

        # Port properties that will be auto-set:
        # - element-uri
        # Properties in parent adapter that will be auto-set:
        # - network-port-uris
        faked_osa1.ports.add({
            'element-id': 'fake-port11-oid',
            'parent': faked_osa1.uri,
            'class': 'network-port',
            'index': 0,
            'name': 'fake-port11-name',
            'description': 'OSA #1 Port #1',
        })
        return faked_osa1

    def add_standard_hipersocket(self):
        """Add a standard Hipersocket adapter with one port to the faked
        HMC."""

        # Adapter properties that will be auto-set:
        # - object-uri
        # - adapter-family
        # - network-port-uris (to empty array)
        faked_hs2 = self.faked_cpc.adapters.add({
            'object-id': HS2_OID,
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': HS2_NAME,
            'description': 'Hipersocket #2',
            'status': 'active',
            'type': 'hipersockets',
            'adapter-id': '123',
            'detected-card-type': 'hipersockets',
            'port-count': 1,
            'network-port-uris': [],
            'state': 'online',
            'configured-capacity': 32,
            'used-capacity': 0,
            'allowed-capacity': 32,
            'maximum-total-capacity': 32,
            'physical-channel-status': 'operating',
            'maximum-transmission-unit-size': 56,
        })

        # Port properties that will be auto-set:
        # - element-uri
        # Properties in parent adapter that will be auto-set:
        # - network-port-uris
        faked_hs2.ports.add({
            'element-id': 'fake-port21-oid',
            'parent': faked_hs2.uri,
            'class': 'network-port',
            'index': 0,
            'name': 'fake-port21-name',
            'description': 'Hipersocket #2 Port #1',
        })
        return faked_hs2

    def add_crypto_ce5s(self, faked_cpc):
        """Add a Crypto Express 5S adapter to a faked CPC."""

        # Adapter properties that will be auto-set:
        # - object-uri
        # - adapter-family
        faked_adapter = faked_cpc.adapters.add({
            'object-id': 'fake-ce5s-oid',
            'parent': faked_cpc.uri,
            'class': 'adapter',
            'name': 'fake-ce5s-name',
            'description': 'Crypto Express 5S #1',
            'status': 'active',
            'type': 'crypto',
            'adapter-id': '123',
            'detected-card-type': 'crypto-express-5s',
            'card-location': 'vvvv-wwww',
            'state': 'online',
            'physical-channel-status': 'operating',
            'crypto-number': 7,
            'crypto-type': 'ep11-coprocessor',
            'udx-loaded': False,
            'tke-commands-enabled': False,
        })
        return faked_adapter

    def add_ficon_fe6sp(self, faked_cpc):
        """Add a not-configured FICON Express 6S+ adapter to a faked CPC."""

        # Adapter properties that will be auto-set:
        # - object-uri
        # - storage-port-uris
        faked_ficon_adapter = faked_cpc.adapters.add({
            'object-id': 'fake-ficon6s-oid',
            'parent': faked_cpc.uri,
            'class': 'adapter',
            'name': 'fake-ficon6s-name',
            'description': 'FICON Express 6S+ #1',
            'status': 'active',
            'type': 'not-configured',
            'adapter-id': '124',
            'adapter-family': 'ficon',
            'detected-card-type': 'ficon-express-16s-plus',
            'card-location': 'vvvv-wwww',
            'port-count': 1,
            'state': 'online',
            'configured-capacity': 254,
            'used-capacity': 0,
            'allowed-capacity': 254,
            'maximum-total-capacity': 254,
            'channel-path-id': None,
            'physical-channel-status': 'not-defined',
        })

        # Port properties that will be auto-set:
        # - element-uri
        # Properties in parent adapter that will be auto-set:
        # - storage-port-uris
        faked_ficon_adapter.ports.add({
            'element-id': 'fake-port11-oid',
            'parent': faked_ficon_adapter.uri,
            'class': 'storage-port',
            'index': 0,
            'name': 'fake-port11-name',
            'description': 'FICON #1 Port #1',
        })
        return faked_ficon_adapter

    def add_cpc_z13s(self):
        """Add a CPC #2 of type z13s to the faked HMC."""

        # CPC properties that will be auto-set:
        # - object-uri
        faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'fake-cpc-2-oid',
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc-2-name',
            'description': 'CPC z13s #2',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
            'machine-type': '2965',  # z13s
        })
        return faked_cpc

    def test_adaptermanager_initial_attrs(self):
        """Test initial attributes of AdapterManager."""

        adapter_mgr = self.cpc.adapters

        # Verify all public properties of the manager object
        assert adapter_mgr.resource_class == Adapter
        assert adapter_mgr.session == self.session
        assert adapter_mgr.parent == self.cpc
        assert adapter_mgr.cpc == self.cpc

    # TODO: Test for AdapterManager.__repr__()

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(),
             ['object-uri', 'name', 'status']),
            (dict(full_properties=False),
             ['object-uri', 'name', 'status']),
            (dict(full_properties=True),
             None),
        ]
    )
    def test_adaptermanager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test AdapterManager.list() with full_properties."""

        # Add two faked adapters
        faked_osa1 = self.add_standard_osa()
        faked_hs2 = self.add_standard_hipersocket()

        exp_faked_adapters = [faked_osa1, faked_hs2]
        adapter_mgr = self.cpc.adapters

        # Execute the code to be tested
        adapters = adapter_mgr.list(**full_properties_kwargs)

        assert_resources(adapters, exp_faked_adapters, prop_names)

    @pytest.mark.parametrize(
        "filter_args, exp_names", [
            ({'object-id': OSA1_OID},
             [OSA1_NAME]),
            ({'object-id': HS2_OID},
             [HS2_NAME]),
            ({'object-id': [OSA1_OID, HS2_OID]},
             [OSA1_NAME, HS2_NAME]),
            ({'object-id': [OSA1_OID, OSA1_OID]},
             [OSA1_NAME]),
            ({'object-id': OSA1_OID + 'foo'},
             []),
            ({'object-id': [OSA1_OID, HS2_OID + 'foo']},
             [OSA1_NAME]),
            ({'object-id': [HS2_OID + 'foo', OSA1_OID]},
             [OSA1_NAME]),
            ({'name': OSA1_NAME},
             [OSA1_NAME]),
            ({'name': HS2_NAME},
             [HS2_NAME]),
            ({'name': [OSA1_NAME, HS2_NAME]},
             [OSA1_NAME, HS2_NAME]),
            ({'name': OSA1_NAME + 'foo'},
             []),
            ({'name': [OSA1_NAME, HS2_NAME + 'foo']},
             [OSA1_NAME]),
            ({'name': [HS2_NAME + 'foo', OSA1_NAME]},
             [OSA1_NAME]),
            ({'name': [OSA1_NAME, OSA1_NAME]},
             [OSA1_NAME]),
            ({'name': '.*osa 1'},
             [OSA1_NAME]),
            ({'name': 'osa 1.*'},
             [OSA1_NAME]),
            ({'name': 'osa .'},
             [OSA1_NAME]),
            ({'name': '.sa 1'},
             [OSA1_NAME]),
            ({'name': '.+'},
             [OSA1_NAME, HS2_NAME]),
            ({'name': 'osa 1.+'},
             []),
            ({'name': '.+osa 1'},
             []),
            ({'name': OSA1_NAME,
              'object-id': OSA1_OID},
             [OSA1_NAME]),
            ({'name': OSA1_NAME,
              'object-id': OSA1_OID + 'foo'},
             []),
            ({'name': OSA1_NAME + 'foo',
              'object-id': OSA1_OID},
             []),
            ({'name': OSA1_NAME + 'foo',
              'object-id': OSA1_OID + 'foo'},
             []),
        ]
    )
    def test_adaptermanager_list_filter_args(self, filter_args, exp_names):
        """Test AdapterManager.list() with filter_args."""

        # Add two faked adapters
        self.add_standard_osa()
        self.add_standard_hipersocket()

        adapter_mgr = self.cpc.adapters

        # Execute the code to be tested
        adapters = adapter_mgr.list(filter_args=filter_args)

        assert len(adapters) == len(exp_names)
        if exp_names:
            names = [ad.properties['name'] for ad in adapters]
            assert set(names) == set(exp_names)

    def test_adaptermanager_create_hipersocket(self):
        """Test AdapterManager.create_hipersocket()."""

        hs_properties = {
            'name': 'hs 3',
            'description': 'Hipersocket #3',
            'port-description': 'Hipersocket #3 Port',
            'maximum-transmission-unit-size': 56,
        }

        adapter_mgr = self.cpc.adapters

        # Execute the code to be tested
        adapter = adapter_mgr.create_hipersocket(properties=hs_properties)

        assert isinstance(adapter, Adapter)
        assert adapter.name == adapter.properties['name']
        assert adapter.uri == adapter.properties['object-uri']

        # We expect the input properties to be in the resource object
        assert adapter.properties['name'] == 'hs 3'
        assert adapter.properties['description'] == 'Hipersocket #3'
        assert adapter.properties['port-description'] == 'Hipersocket #3 Port'
        assert adapter.properties['maximum-transmission-unit-size'] == 56

    # TODO: Test for initial Adapter attributes (ports, port_uris_prop,
    #       port_uri_segment)

    def test_adapter_repr(self):
        """Test Adapter.__repr__()."""

        # Add a faked adapter
        faked_osa = self.add_standard_osa()

        adapter_mgr = self.cpc.adapters
        adapter = adapter_mgr.find(name=faked_osa.name)

        # Execute the code to be tested
        repr_str = repr(adapter)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=adapter.__class__.__name__,
                               id=id(adapter)),
                        repr_str)

    def test_max_crypto_domains(self):
        """Test Adapter.maximum_crypto_domains on z13 and z13s."""

        faked_cpc = self.faked_cpc
        faked_crypto = self.add_crypto_ce5s(faked_cpc)
        self._one_test_max_crypto_domains(faked_cpc, faked_crypto, 85)

        faked_cpc = self.add_cpc_z13s()
        faked_crypto = self.add_crypto_ce5s(faked_cpc)
        self._one_test_max_crypto_domains(faked_cpc, faked_crypto, 40)

    def _one_test_max_crypto_domains(self, faked_cpc, faked_adapter,
                                     exp_max_domains):

        cpc = self.client.cpcs.find(name=faked_cpc.name)
        adapter = cpc.adapters.find(name=faked_adapter.name)

        # Exercise code to be tested
        max_domains = adapter.maximum_crypto_domains

        assert max_domains == exp_max_domains

    def test_adapter_delete(self):
        """Test Adapter.delete() for Hipersocket adapter."""

        # Add two faked adapters
        self.add_standard_osa()
        faked_hs = self.add_standard_hipersocket()

        adapter_mgr = self.cpc.adapters
        hs_adapter = adapter_mgr.find(name=faked_hs.name)

        # Execute the code to be tested
        hs_adapter.delete()

        with pytest.raises(NotFound):
            hs_adapter = adapter_mgr.find(type='hipersockets')

        with pytest.raises(NotFound):
            hs_adapter = adapter_mgr.find(name=faked_hs.name)

        adapters = adapter_mgr.list()
        assert len(adapters) == 1

        with pytest.raises(HTTPError) as exc_info:
            hs_adapter.pull_full_properties()
        exc = exc_info.value
        assert exc.http_status == 404
        assert exc.reason == 1

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New adapter description'},
            {'channel-path-id': '1A',
             'description': 'New adapter description'},
        ]
    )
    def test_adapter_update_properties(self, input_props):
        """Test Adapter.update_properties()."""

        # Add a faked adapter
        faked_adapter = self.add_standard_osa()

        adapter_mgr = self.cpc.adapters
        adapter = adapter_mgr.find(name=faked_adapter.name)

        adapter.pull_full_properties()
        saved_properties = copy.deepcopy(adapter.properties)

        # Execute the code to be tested
        adapter.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in adapter.properties
            prop_value = adapter.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        adapter.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in adapter.properties
            prop_value = adapter.properties[prop_name]
            assert prop_value == exp_prop_value

    def test_adapter_update_name(self):
        """
        Test Adapter.update_properties() with 'name' property.
        """

        # Add a faked adapter
        faked_adapter = self.add_standard_osa()
        adapter_name = faked_adapter.name

        adapter_mgr = self.cpc.adapters
        adapter = adapter_mgr.find(name=adapter_name)

        new_adapter_name = "new-" + adapter_name

        # Execute the code to be tested
        adapter.update_properties(properties={'name': new_adapter_name})

        # Verify that the resource is no longer found by its old name, using
        # list() (this does not use the name-to-URI cache).
        adapters_list = adapter_mgr.list(filter_args=dict(name=adapter_name))
        assert len(adapters_list) == 0

        # Verify that the resource is no longer found by its old name, using
        # find() (this uses the name-to-URI cache).
        with pytest.raises(NotFound):
            adapter_mgr.find(name=adapter_name)

        # Verify that the resource object already reflects the update, even
        # though it has not been refreshed yet.
        assert adapter.properties['name'] == new_adapter_name

        # Refresh the resource object and verify that it still reflects the
        # update.
        adapter.pull_full_properties()
        assert adapter.properties['name'] == new_adapter_name

        # Verify that the resource can be found by its new name, using find()
        new_adapter_find = adapter_mgr.find(name=new_adapter_name)
        assert new_adapter_find.properties['name'] == new_adapter_name

        # Verify that the resource can be found by its new name, using list()
        new_adapters_list = adapter_mgr.list(
            filter_args=dict(name=new_adapter_name))
        assert len(new_adapters_list) == 1
        new_adapter_list = new_adapters_list[0]
        assert new_adapter_list.properties['name'] == new_adapter_name

    # TODO: Test for Adapter.change_crypto_type()

    @pytest.mark.parametrize(
        "init_type", ['not-configured', 'fc', 'fcp']
    )
    @pytest.mark.parametrize(
        "new_type", ['not-configured', 'fc', 'fcp']
    )
    def test_change_adapter_type_success(self, init_type, new_type):
        """Test Adapter.change_adapter_type() on ficon adapter with success."""

        faked_cpc = self.faked_cpc
        faked_adapter = self.add_ficon_fe6sp(faked_cpc)

        # Set the desired initial adapter type for the test
        faked_adapter.properties['type'] = init_type

        adapter_mgr = self.cpc.adapters
        adapter = adapter_mgr.find(name=faked_adapter.name)

        if new_type == init_type:
            with pytest.raises(HTTPError) as exc_info:

                # Execute the code to be tested
                adapter.change_adapter_type(new_type)

            exc = exc_info.value
            assert exc.http_status == 400
            assert exc.reason == 8
        else:

            # Execute the code to be tested.
            adapter.change_adapter_type(new_type)

            act_type = adapter.get_property('type')
            assert act_type == new_type

    @pytest.mark.parametrize(
        "desc, family, init_type, new_type, exp_exc", [
            (
                "Invalid adapter family: 'osa'",
                'osa', 'osd', None,
                HTTPError({'http-status': 400, 'reason': 18})
            ),
            (
                "Invalid new type value: 'xxx'",
                'ficon', 'fcp', 'xxx',
                HTTPError({'http-status': 400, 'reason': 8})
            ),
        ]
    )
    def test_change_adapter_type_error(
            self, desc, family, init_type, new_type, exp_exc):
        """Test Adapter.change_adapter_type()."""

        faked_cpc = self.faked_cpc
        if family == 'ficon':
            faked_adapter = self.add_ficon_fe6sp(faked_cpc)
        else:
            assert family == 'osa'
            faked_adapter = self.add_standard_osa()

        faked_adapter.properties['type'] == init_type

        adapter_mgr = self.cpc.adapters
        adapter = adapter_mgr.find(name=faked_adapter.name)

        with pytest.raises(exp_exc.__class__) as exc_info:

            # Execute the code to be tested
            adapter.change_adapter_type(new_type)

        exc = exc_info.value
        if isinstance(exp_exc, HTTPError):
            assert exc.http_status == exp_exc.http_status
            assert exc.reason == exp_exc.reason
