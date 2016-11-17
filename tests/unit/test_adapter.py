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
Unit tests for _adapter module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client, Adapter


class AdapterTests(unittest.TestCase):
    """All tests for Adapter and AdapterManager classes."""

    def setUp(self):
        self.session = Session('adapter-dpm-host', 'adapter-user',
                               'adapter-pwd')
        self.client = Client(self.session)
        with requests_mock.mock() as m:
            # Because logon is deferred until needed, we perform it
            # explicitly in order to keep mocking in the actual test simple.
            m.post('/api/sessions', json={'api-session': 'adapter-session-id'})
            self.session.logon()

        self.cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/adapter-cpc-id-1',
                        'name': 'CPC',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)

            cpcs = self.cpc_mgr.list()
            self.cpc = cpcs[0]

    def tearDown(self):
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)
            self.session.logoff()

    def test_init(self):
        """Test __init__() on AdapterManager instance in CPC."""
        adapter_mgr = self.cpc.adapters
        self.assertEqual(adapter_mgr.cpc, self.cpc)

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties on AdapterManager
        instance in CPC.
        """
        adapter_mgr = self.cpc.adapters
        with requests_mock.mock() as m:
            result = {
                'adapters': [
                    {
                        'adapter-family': 'ficon',
                        'adapter-id': '18C',
                        'type': 'fcp',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-1',
                        'name': 'FCP Adapter 1'
                    },
                    {
                        'adapter-family': 'osa',
                        'adapter-id': '1C4',
                        'type': 'osd',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-2',
                        'name': 'OSD Adapter 1'
                    }
                ]
            }

            m.get('/api/cpcs/adapter-cpc-id-1/adapters', json=result)

            adapters = adapter_mgr.list(full_properties=False)

            self.assertEqual(len(adapters), len(result['adapters']))
            for idx, adapter in enumerate(adapters):
                self.assertEqual(
                    adapter.properties,
                    result['adapters'][idx])
                self.assertEqual(
                    adapter.uri,
                    result['adapters'][idx]['object-uri'])
                self.assertFalse(adapter.full_properties)
                self.assertEqual(adapter.manager, adapter_mgr)

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on AdapterManager
        instance in CPC.
        """
        adapter_mgr = self.cpc.adapters
        with requests_mock.mock() as m:
            result = {
                'adapters': [
                    {
                        'adapter-family': 'ficon',
                        'adapter-id': '18C',
                        'type': 'fcp',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-1',
                        'name': 'FCP Adapter 1'
                    },
                    {
                        'adapter-family': 'osa',
                        'adapter-id': '1C4',
                        'type': 'osd',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-2',
                        'name': 'OSD Adapter 1'
                    }
                ]
            }

            m.get('/api/cpcs/adapter-cpc-id-1/adapters', json=result)

            mock_result_adapter1 = {
                'adapter-family': 'ficon',
                'adapter-id': '18C',
                'type': 'fcp',
                'status': 'active',
                'object-uri': '/api/adapters/fake-adapter-id-1',
                'name': 'FCP Adapter 1',
                'more_properties': 'bliblablub'
            }
            m.get('/api/adapters/fake-adapter-id-1',
                  json=mock_result_adapter1)
            mock_result_adapter2 = {
                'adapter-family': 'osa',
                'adapter-id': '1C4',
                'type': 'osd',
                'status': 'active',
                'object-uri': '/api/adapters/fake-adapter-id-2',
                'name': 'OSD Adapter 1',
                'description': 'Test Adapter',
                'more_properties': 'bliblablub'
            }
            m.get('/api/adapters/fake-adapter-id-2',
                  json=mock_result_adapter2)

            adapters = adapter_mgr.list(full_properties=True)

            self.assertEqual(len(adapters), len(result['adapters']))
            for idx, adapter in enumerate(adapters):
                self.assertEqual(adapter.properties['name'],
                                 result['adapters'][idx]['name'])
                self.assertEqual(
                    adapter.uri,
                    result['adapters'][idx]['object-uri'])
                self.assertTrue(adapter.full_properties)
                self.assertEqual(adapter.manager, adapter_mgr)

    def test_create_hipersocket(self):
        """
        This tests the 'Create Hipersocket' operation.
        """
        adapter_mgr = self.cpc.adapters
        with requests_mock.mock() as m:
            result = {
                'object-uri': '/api/adapters/fake-adapter-id-1'
            }
            m.post('/api/cpcs/adapter-cpc-id-1/adapters', json=result)

            adapter = adapter_mgr.create_hipersocket(properties={})

            self.assertTrue(isinstance(adapter, Adapter))
            self.assertEqual(adapter.properties, result)
            self.assertEqual(adapter.uri, result['object-uri'])

    def test_delete(self):
        """
        This tests the 'Delete Adapter' operation.
        """
        adapter_mgr = self.cpc.adapters
        with requests_mock.mock() as m:
            result = {
                'adapters': [
                    {
                        'adapter-family': 'ficon',
                        'adapter-id': '18C',
                        'type': 'fcp',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-1',
                        'name': 'FCP Adapter 1'
                    },
                    {
                        'adapter-family': 'osa',
                        'adapter-id': '1C4',
                        'type': 'osd',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-2',
                        'name': 'OSD Adapter 1'
                    }
                ]
            }
            m.get('/api/cpcs/adapter-cpc-id-1/adapters', json=result)

            adapters = adapter_mgr.list(full_properties=False)
            adapter = adapters[0]
            m.delete(
                "/api/adapters/fake-adapter-id-1",
                json=result)
            status = adapter.delete()
            self.assertEqual(status, None)

    def test_update_properties(self):
        """
        This tests the 'Update Adapter Properties' operation.
        """
        adapter_mgr = self.cpc.adapters
        with requests_mock.mock() as m:
            result = {
                'adapters': [
                    {
                        'adapter-family': 'ficon',
                        'adapter-id': '18C',
                        'type': 'fcp',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-1',
                        'name': 'FCP Adapter 1'
                    },
                    {
                        'adapter-family': 'osa',
                        'adapter-id': '1C4',
                        'type': 'osd',
                        'status': 'active',
                        'object-uri': '/api/adapters/fake-adapter-id-2',
                        'name': 'OSD Adapter 1'
                    }
                ]
            }
            m.get('/api/cpcs/adapter-cpc-id-1/adapters', json=result)

            adapters = adapter_mgr.list(full_properties=False)
            adapter = adapters[0]
            m.post(
                "/api/adapters/fake-adapter-id-1",
                json=result)
            status = adapter.update_properties(properties={})
            self.assertEqual(status, None)


if __name__ == '__main__':
    unittest.main()
