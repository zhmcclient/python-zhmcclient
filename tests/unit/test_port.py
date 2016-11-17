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
Unit tests for _port module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client


class PortTests(unittest.TestCase):
    """All tests for Port and PortManager classes."""

    def setUp(self):
        self.session = Session('port-dpm-host', 'port-user',
                               'port-pwd')
        self.client = Client(self.session)
        with requests_mock.mock() as m:
            # Because logon is deferred until needed, we perform it
            # explicitly in order to keep mocking in the actual test simple.
            m.post('/api/sessions', json={'api-session': 'port-session-id'})
            self.session.logon()

        self.cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/port-cpc-id-1',
                        'name': 'CPC',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)

            cpcs = self.cpc_mgr.list()
            self.cpc = cpcs[0]

        adapter_mgr = self.cpc.adapters
        with requests_mock.mock() as m:
            self.result = {
                'adapters': [
                    {
                        'adapter-family': 'ficon',
                        'adapter-id': '18C',
                        'type': 'fcp',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-1',
                        'name': 'FCP Adapter 1',
                        'port-count': 1,
                        'storage-port-uris': [
                            '/api/adapters/fake-adapter-id-1/storage-ports/0'
                        ]
                    },
                    {
                        'adapter-family': 'osa',
                        'adapter-id': '1C4',
                        'type': 'osd',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-2',
                        'name': 'OSD Adapter 1',
                        'port-count': 2,
                        'network-port-uris': [
                            '/api/adapters/fake-adapter-id-2/network-ports/0',
                            '/api/adapters/fake-adapter-id-2/network-ports/1'
                        ]
                    },
                    {
                        'status': 'not-active',
                        'configured-capacity': 3,
                        'description': '',
                        'parent': '/api/cpcs//port-cpc-id-1',
                        'object-id': 'fake-adapter-id-3',
                        'detected-card-type': 'zedc-express',
                        'class': 'adapter',
                        'name': 'zEDC 01CC Z15B-23',
                        'used-capacity': 0,
                        'adapter-id': '1CC',
                        'maximum-total-capacity': 15,
                        'adapter-family': 'accelerator',
                        'allowed-capacity': 15,
                        'state': 'reserved',
                        'object-uri': '/api/adapters/fake-adapter-id-3',
                        'card-location': 'Z15B-LG23',
                        'type': 'zedc'
                    }
                ]
            }

            m.get('/api/cpcs/port-cpc-id-1/adapters', json=self.result)

            adapters = adapter_mgr.list(full_properties=False)
            self.adapters = adapters

    def tearDown(self):
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)
            self.session.logoff()

    def test_init(self):
        """Test __init__() on PortManager instance in Adapter."""
        port_mgr = self.adapters[0].ports
        self.assertEqual(port_mgr.adapter, self.adapters[0])

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties on PortManager
        instance in Adapter.
        """
        adapters = self.adapters
        for idy, adapter in enumerate(adapters):
            port_mgr = adapter.ports
            ports = port_mgr.list(full_properties=False)
            if len(ports) != 0:
                result_adapter = self.result['adapters'][idy]
                if 'storage-port-uris' in result_adapter:
                    storage_uris = result_adapter['storage-port-uris']
                    uris = storage_uris
                else:
                    network_uris = result_adapter['network-port-uris']
                    uris = network_uris
                self.assertEqual(adapter.properties['port-count'], len(uris))
            else:
                uris = []

            self.assertEqual(len(ports), len(uris))
            for idx, port in enumerate(ports):
                self.assertEqual(
                    port.properties['element-uri'],
                    uris[idx])
                self.assertFalse(port.full_properties)
                self.assertEqual(port.manager, port_mgr)

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on PortManager
        instance in Adapter.
        """
        adapters = self.adapters
        adapter = adapters[0]
        with requests_mock.mock() as m:

            mock_result_port1 = {
                'parent': '/api/adapters/fake-adapter-id-1',
                'index': 0,
                'fabric-id': '',
                'description': '',
                'element-uri':
                    '/api/adapters/fake-adapter-id-1/storage-ports/0',
                'element-id': '0',
                'class': 'storage-port',
                'name': 'Port 0'
            }

            m.get('/api/adapters/fake-adapter-id-1/storage-ports/0',
                  json=mock_result_port1)

            port_mgr = adapter.ports
            ports = port_mgr.list(full_properties=True)
            if len(ports) != 0:
                storage_uris = self.result['adapters'][0]['storage-port-uris']
                self.assertEqual(adapter.properties['port-count'],
                                 len(storage_uris))
            else:
                storage_uris = []

            self.assertEqual(len(ports), len(storage_uris))
            for idx, port in enumerate(ports):
                self.assertEqual(
                    port.properties['element-uri'],
                    storage_uris[idx])
                self.assertTrue(port.full_properties)
                self.assertEqual(port.manager, port_mgr)

    def test_update_properties(self):
        """
        This tests the 'Update Port Properties' operation.
        """
        port_mgr = self.adapters[0].ports
        ports = port_mgr.list(full_properties=False)
        port = ports[0]
        with requests_mock.mock() as m:
            result = {}
            m.post(
                '/api/adapters/fake-adapter-id-1/storage-ports/0',
                json=result)
            status = port.update_properties(properties={})
            self.assertEqual(status, None)


if __name__ == '__main__':
    unittest.main()
