#!/usr/bin/env python
# Copyright 2016 IBM Corp. All Rights Reserved.
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
Unit tests for _adapter module, using the zhmcclient mock support.
"""

from __future__ import absolute_import, print_function

import unittest

from zhmcclient import Client, Adapter, NotFound, HTTPError
from zhmcclient_mock import FakedSession


class AdapterTests(unittest.TestCase):
    """All tests for Adapter and AdapterManager classes."""

    def setUp(self):
        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'faked-cpc1',
            'parent': None,
            'class': 'cpc',
            'name': 'cpc_1',
            'description': 'CPC #1',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
        })
        self.client = Client(self.session)
        self.cpc = self.client.cpcs.list()[0]

    def add_standard_osa(self):
        """Add a standard OSA adapter with one port to the faked HMC."""

        self.osa1_id = 'fake-osa1'
        self.osa1_name = 'osa 1'
        self.osa1_uri = '/api/adapters/' + self.osa1_id

        self.port11_id = 'fake-port11'
        self.port11_name = 'osa 1 port 1'
        self.port11_uri = self.osa1_uri + '/network-ports/' + self.port11_id

        # Adapter properties that will be auto-set:
        # - object-uri
        # - adapter-family
        # - network-port-uris (to empty array)
        faked_osa1 = self.faked_cpc.adapters.add({
            'object-id': self.osa1_id,
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': self.osa1_name,
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
            'element-id': self.port11_id,
            'parent': faked_osa1.uri,
            'class': 'network-port',
            'index': 0,
            'name': self.port11_name,
            'description': 'OSA #1 Port #1',
        })

    def add_standard_hipersocket(self):
        """Add a standard Hipersocket adapter with one port to the faked
        HMC."""

        self.hs2_id = 'fake-hs2'
        self.hs2_name = 'hs 2'
        self.hs2_uri = '/api/adapters/' + self.hs2_id

        self.port21_id = 'fake-port21'
        self.port21_name = 'hs 2 port 1'
        self.port21_uri = self.hs2_uri + '/network-ports/' + self.port21_id

        # Adapter properties that will be auto-set:
        # - object-uri
        # - adapter-family
        # - network-port-uris (to empty array)
        faked_hs2 = self.faked_cpc.adapters.add({
            'object-id': self.hs2_id,
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': self.hs2_name,
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
            'element-id': self.port21_id,
            'parent': faked_hs2.uri,
            'class': 'network-port',
            'index': 0,
            'name': self.port21_name,
            'description': 'Hipersocket #2 Port #1',
        })

    def test_repr(self):
        """Test Adapter.__repr__()."""
        adapter = Adapter(self.cpc.adapters, '/adapters/1', 'osa1')

        repr_str = repr(adapter)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        self.assertRegexpMatches(
            repr_str,
            r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.format(
                classname=adapter.__class__.__name__,
                id=id(adapter)))

    def test_init(self):
        """Test AdapterManager.__init__()."""
        self.add_standard_osa()

        manager = self.cpc.adapters

        # Verify all public properties of the manager object
        self.assertEqual(manager.resource_class, Adapter)
        self.assertEqual(manager.session, self.session)
        self.assertEqual(manager.parent, self.cpc)
        self.assertEqual(manager.cpc, self.cpc)

    def test_list_default(self):
        """Test AdapterManager.list() with default for full_properties."""
        self.add_standard_osa()
        self.add_standard_hipersocket()

        adapters = self.cpc.adapters.list()

        self.assertEqual(len(adapters), 2)

        osa1 = adapters[0]
        self.assertEqual(osa1.uri, self.osa1_uri)
        self.assertEqual(osa1.name, self.osa1_name)
        self.assertEqual(osa1.properties['object-uri'], self.osa1_uri)
        self.assertEqual(osa1.properties['name'], self.osa1_name)
        self.assertEqual(osa1.properties['status'], 'active')

        hs2 = adapters[1]
        self.assertEqual(hs2.uri, self.hs2_uri)
        self.assertEqual(hs2.name, self.hs2_name)
        self.assertEqual(hs2.properties['object-uri'], self.hs2_uri)
        self.assertEqual(hs2.properties['name'], self.hs2_name)
        self.assertEqual(hs2.properties['status'], 'active')

    def test_list_short(self):
        """Test AdapterManager.list() with full_properties=False."""
        self.add_standard_osa()

        adapters = self.cpc.adapters.list(full_properties=False)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.uri, self.osa1_uri)
        self.assertEqual(osa1.name, self.osa1_name)
        self.assertEqual(osa1.properties['object-uri'], self.osa1_uri)
        self.assertEqual(osa1.properties['name'], self.osa1_name)
        self.assertEqual(osa1.properties['status'], 'active')

    def test_list_full(self):
        """Test AdapterManager.list() with full_properties=True."""
        self.add_standard_osa()

        adapters = self.cpc.adapters.list(full_properties=True)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.uri, self.osa1_uri)
        self.assertEqual(osa1.name, self.osa1_name)
        self.assertEqual(osa1.properties['object-uri'], self.osa1_uri)
        self.assertEqual(osa1.properties['object-id'], self.osa1_id)
        self.assertEqual(osa1.properties['parent'], self.cpc.uri)
        self.assertEqual(osa1.properties['class'], 'adapter')
        self.assertEqual(osa1.properties['name'], self.osa1_name)
        self.assertEqual(osa1.properties['description'], 'OSA #1')
        self.assertEqual(osa1.properties['status'], 'active')
        self.assertEqual(osa1.properties['type'], 'osd')
        self.assertEqual(osa1.properties['adapter-id'], '123')
        self.assertEqual(osa1.properties['detected-card-type'],
                         'osa-express-5s-10gb')
        self.assertEqual(osa1.properties['card-location'], '1234-5678-J.01')
        self.assertEqual(osa1.properties['port-count'], 1)
        self.assertEqual(osa1.properties['network-port-uris'],
                         [self.port11_uri])
        self.assertEqual(osa1.properties['state'], 'online')
        self.assertEqual(osa1.properties['configured-capacity'], 80)
        self.assertEqual(osa1.properties['used-capacity'], 0)
        self.assertEqual(osa1.properties['allowed-capacity'], 80)
        self.assertEqual(osa1.properties['maximum-total-capacity'], 80)
        self.assertEqual(osa1.properties['physical-channel-status'],
                         'operating')

    def test_list_filter_name_found1(self):
        """Test AdapterManager.list() with filtering on existing name
        (filtered on faked HMC server), matching on first one."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': self.osa1_name,
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_name_found2(self):
        """Test AdapterManager.list() with filtering on existing name
        (filtered on faked HMC server), matching on second one."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': self.hs2_name,
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        hs2 = adapters[0]
        self.assertEqual(hs2.name, self.hs2_name)

    def test_list_filter_name_notfound(self):
        """Test AdapterManager.list() with filtering on non-existing name
        (filtered on faked HMC server)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': self.osa1_name + 'foo',
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 0)

    def test_list_filter_oid_found(self):
        """Test AdapterManager.list() with filtering on existing object-id
        (filtered on client)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'object-id': self.osa1_id,
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_oid_notfound(self):
        """Test AdapterManager.list() with filtering on non-existing
        object-id (filtered on client)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'object-id': self.osa1_id + 'foo',
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 0)

    def test_list_filter_name_id_found(self):
        """Test AdapterManager.list() with filtering on existing name
        (filtered on faked HMC server) and existing object-id (filtered on
        client)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': self.osa1_name,
            'object-id': self.osa1_id,
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_name_id_notfound1(self):
        """Test AdapterManager.list() with filtering on existing name
        (filtered on faked HMC server) and non-existing object-id (filtered on
        client)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': self.osa1_name,
            'object-id': self.osa1_id + 'foo',
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 0)

    def test_list_filter_name_id_notfound2(self):
        """Test AdapterManager.list() with filtering on non-existing name
        (filtered on faked HMC server) and existing object-id (filtered on
        client)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': self.osa1_name + 'foo',
            'object-id': self.osa1_id,
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 0)

    def test_list_filter_name_id_notfound3(self):
        """Test AdapterManager.list() with filtering on non-existing name
        (filtered on faked HMC server) and non-existing object-id (filtered on
        client)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': self.osa1_name + 'foo',
            'object-id': self.osa1_id + 'foo',
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 0)

    def test_list_filter_name2_found1(self):
        """Test AdapterManager.list() with filtering on two names (first
        existing second non-existing)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': [self.osa1_name, self.hs2_name + 'foo'],
        }

        # import pdb; pdb.set_trace()

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_name2_found2(self):
        """Test AdapterManager.list() with filtering on two names (first
        non-existing second existing)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': [self.hs2_name + 'foo', self.osa1_name],
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_name2_found3(self):
        """Test AdapterManager.list() with filtering on the same existing name
        twice."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': [self.osa1_name, self.osa1_name],
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_name_reg1_found(self):
        """Test AdapterManager.list() with filtering on the an existing name
        with regexp 1"""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': '.*osa 1',
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_name_reg2_found(self):
        """Test AdapterManager.list() with filtering on the an existing name
        with regexp 2"""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': 'osa 1.*',
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_name_reg3_found(self):
        """Test AdapterManager.list() with filtering on the an existing name
        with regexp 2"""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': 'osa .',
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_name_reg4_found(self):
        """Test AdapterManager.list() with filtering on the an existing name
        with regexp 4"""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': '.sa 1',
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 1)
        osa1 = adapters[0]
        self.assertEqual(osa1.name, self.osa1_name)

    def test_list_filter_name_reg5_found(self):
        """Test AdapterManager.list() with filtering on the an existing names
        with regexp 5"""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        filter_args = {
            'name': '.+',
        }

        adapters = self.cpc.adapters.list(filter_args=filter_args)

        self.assertEqual(len(adapters), 2)
        names = [ad.name for ad in adapters]
        self.assertEqual(names, [self.osa1_name, self.hs2_name])

    def test_create_hipersocket(self):
        """Test AdapterManager.create_hipersocket()."""
        hs_properties = {
            'name': 'hs 1',
            'description': 'Hipersocket #1',
            'port-description': 'Hipersocket #1 Port',
            'maximum-transmission-unit-size': 56,
        }

        adapter = self.cpc.adapters.create_hipersocket(
            properties=hs_properties)

        self.assertTrue(isinstance(adapter, Adapter))
        self.assertEqual(adapter.name, adapter.properties['name'])
        self.assertEqual(adapter.uri, adapter.properties['object-uri'])

        # We expect the input properties to be in the resource object
        self.assertEqual(adapter.properties['name'], 'hs 1')
        self.assertEqual(adapter.properties['description'], 'Hipersocket #1')
        self.assertEqual(adapter.properties['port-description'],
                         'Hipersocket #1 Port')
        self.assertEqual(adapter.properties['maximum-transmission-unit-size'],
                         56)

    def test_delete(self):
        """Test Adapter.delete() (for Hipersocket adapter)."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        hs_adapter = self.cpc.adapters.find(type='hipersockets')

        hs_adapter.delete()

        with self.assertRaises(NotFound):
            hs_adapter = self.cpc.adapters.find(type='hipersockets')

        with self.assertRaises(NotFound):
            hs_adapter = self.cpc.adapters.find(name='hs 2')

        adapters = self.cpc.adapters.list()
        self.assertEqual(len(adapters), 1)

        with self.assertRaises(HTTPError) as cm:
            hs_adapter.pull_full_properties()
        self.assertEqual(cm.exception.http_status, 404)
        self.assertEqual(cm.exception.reason, 1)

    def test_update_properties(self):
        """Test Adapter.update_properties()."""
        self.add_standard_osa()
        self.add_standard_hipersocket()
        new_properties = {
            'name': 'hs 2.new',
            'description': 'Hipersocket #2.new',
        }
        adapter = self.cpc.adapters.find(type='hipersockets')

        adapter.update_properties(properties=new_properties)

        self.assertEqual(adapter.name, new_properties['name'])
        self.assertEqual(adapter.properties['name'], new_properties['name'])
        self.assertEqual(adapter.properties['description'],
                         new_properties['description'])


if __name__ == '__main__':
    unittest.main()
