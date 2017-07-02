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
from .utils import assert_resources


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
        self.cpc = self.client.cpcs.list()[0]

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

    def test_manager_initial_attrs(self):
        """Test initial attributes of AdapterManager."""

        manager = self.cpc.adapters

        # Verify all public properties of the manager object
        assert manager.resource_class == Adapter
        assert manager.session == self.session
        assert manager.parent == self.cpc
        assert manager.cpc == self.cpc

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
    def test_manager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test AdapterManager.list() with full_properties."""

        # Add two adapters
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
    def test_manager_list_filter_args(self, filter_args, exp_names):
        """Test AdapterManager.list() with filter_args."""

        self.add_standard_osa()
        self.add_standard_hipersocket()

        # Execute the code to be tested
        adapters = self.cpc.adapters.list(filter_args=filter_args)

        assert len(adapters) == len(exp_names)
        if exp_names:
            names = [ad.properties['name'] for ad in adapters]
            assert set(names) == set(exp_names)

    def test_manager_create_hipersocket(self):
        """Test AdapterManager.create_hipersocket()."""

        hs_properties = {
            'name': 'hs 3',
            'description': 'Hipersocket #3',
            'port-description': 'Hipersocket #3 Port',
            'maximum-transmission-unit-size': 56,
        }

        # Execute the code to be tested
        adapter = self.cpc.adapters.create_hipersocket(
            properties=hs_properties)

        assert isinstance(adapter, Adapter)
        assert adapter.name == adapter.properties['name']
        assert adapter.uri == adapter.properties['object-uri']

        # We expect the input properties to be in the resource object
        assert adapter.properties['name'] == 'hs 3'
        assert adapter.properties['description'] == 'Hipersocket #3'
        assert adapter.properties['port-description'] == 'Hipersocket #3 Port'
        assert adapter.properties['maximum-transmission-unit-size'] == 56

    def test_resource_repr(self):
        """Test Adapter.__repr__()."""

        adapter = Adapter(self.cpc.adapters, '/adapters/1', 'osa1')

        # Execute the code to be tested
        repr_str = repr(adapter)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=adapter.__class__.__name__,
                               id=id(adapter)),
                        repr_str)

    def test_resource_delete(self):
        """Test Adapter.delete() (for Hipersocket adapter)."""

        self.add_standard_osa()
        self.add_standard_hipersocket()
        hs_adapter = self.cpc.adapters.find(type='hipersockets')

        # Execute the code to be tested
        hs_adapter.delete()

        with pytest.raises(NotFound):
            hs_adapter = self.cpc.adapters.find(type='hipersockets')

        with pytest.raises(NotFound):
            hs_adapter = self.cpc.adapters.find(name='hs 2')

        adapters = self.cpc.adapters.list()
        assert len(adapters) == 1

        with pytest.raises(HTTPError) as exc_info:
            hs_adapter.pull_full_properties()
        exc = exc_info.value
        assert exc.http_status == 404
        assert exc.reason == 1

    def test_resource_update_nothing(self):
        """Test Adapter.update_properties() with no properties."""

        self.add_standard_osa()
        self.add_standard_hipersocket()
        adapters = self.cpc.adapters.list(filter_args={'name': HS2_NAME})
        assert len(adapters) == 1
        adapter = adapters[0]

        saved_properties = copy.deepcopy(adapter.properties)

        # Execute the code to be tested
        adapter.update_properties(properties={})

        # Verify that the properties of the local resource object have not
        # changed
        assert adapter.properties == saved_properties

    def test_resource_update_name(self):
        """
        Test Adapter.update_properties() with 'name' property.
        """

        self.add_standard_osa()
        self.add_standard_hipersocket()
        adapters = self.cpc.adapters.list(filter_args={'name': HS2_NAME})
        assert len(adapters) == 1
        adapter = adapters[0]

        new_name = "new hs2"

        # Execute the code to be tested
        adapter.update_properties(properties={'name': new_name})

        # Verify that the local resource object reflects the update
        assert adapter.properties['name'] == new_name

        # Update the properties of the resource object and verify that the
        # resource object reflects the update
        adapter.pull_full_properties()
        assert adapter.properties['name'] == new_name

        # List the resource by its new name and verify that it was found
        adapters = self.cpc.adapters.list(filter_args={'name': new_name})
        assert len(adapters) == 1
        adapter = adapters[0]
        assert adapter.properties['name'] == new_name

    def test_resource_update_not_fetched(self):
        """
        Test Adapter.update_properties() with no properties with an existing
        property that has not been fetched into the local resource object.
        """

        self.add_standard_osa()
        self.add_standard_hipersocket()
        adapters = self.cpc.adapters.list(filter_args={'name': HS2_NAME})
        assert len(adapters) == 1
        adapter = adapters[0]

        # A property that is not in the result of list():
        update_prop_name = 'description'
        update_prop_value = 'Hipersocket #2.new'

        # Execute the code to be tested
        adapter.update_properties(
            properties={update_prop_name: update_prop_value})

        # Verify that the local resource object reflects the update
        assert adapter.properties[update_prop_name] == update_prop_value

        # Update the properties of the resource object and verify that the
        # resource object reflects the update
        adapter.pull_full_properties()
        assert adapter.properties[update_prop_name] == update_prop_value

    def test_max_crypto_domains(self):
        """Test Adapter.maximum_crypto_domains() on z13 and z13s."""

        faked_cpc = self.faked_cpc
        faked_crypto = self.add_crypto_ce5s(faked_cpc)
        self._one_test_max_crypto_domains(faked_cpc, faked_crypto, 85)

        faked_cpc = self.add_cpc_z13s()
        faked_crypto = self.add_crypto_ce5s(faked_cpc)
        self._one_test_max_crypto_domains(faked_cpc, faked_crypto, 40)

    def _one_test_max_crypto_domains(
            self, faked_cpc, faked_adapter, exp_max_domains):

        cpc = self.client.cpcs.find(name=faked_cpc.name)
        adapter = cpc.adapters.find(name=faked_adapter.name)

        # Exercise code to be tested
        max_domains = adapter.maximum_crypto_domains

        assert max_domains == exp_max_domains
