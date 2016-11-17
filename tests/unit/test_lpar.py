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
Unit tests for _lpar module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client


class LparTests(unittest.TestCase):
    """All tests for Lpar and LparManager classes."""

    def setUp(self):
        self.session = Session('fake-host', 'fake-user', 'fake-id')
        self.client = Client(self.session)
        with requests_mock.mock() as m:
            # Because logon is deferred until needed, we perform it
            # explicitly in order to keep mocking in the actual test simple.
            m.post('/api/sessions', json={'api-session': 'fake-session-id'})
            self.session.logon()

        self.cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'P0ZHMP02',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)
            cpcs = self.cpc_mgr.list(full_properties=False)
            self.cpc = cpcs[0]

    def tearDown(self):
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)
            self.session.logoff()

    def test_init(self):
        """Test __init__() on LparManager instance in CPC."""
        lpar_mgr = self.cpc.lpars
        self.assertEqual(lpar_mgr.cpc, self.cpc)

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties on LparManager
        instance in CPC.
        """
        lpar_mgr = self.cpc.lpars
        with requests_mock.mock() as m:
            result = {
                'logical-partitions': [
                    {
                        'status': 'not-activated',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-1',
                        'name': 'LPAR1'
                    },
                    {
                        'status': 'operating',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-2',
                        'name': 'LPAR2'
                    }
                ]
            }
            m.get('/api/cpcs/fake-cpc-id-1/logical-partitions', json=result)

            lpars = lpar_mgr.list(full_properties=False)

            self.assertEqual(len(lpars), len(result['logical-partitions']))
            for idx, lpar in enumerate(lpars):
                self.assertEqual(
                    lpar.properties,
                    result['logical-partitions'][idx])
                self.assertEqual(
                    lpar.uri,
                    result['logical-partitions'][idx]['object-uri'])
                self.assertFalse(lpar.full_properties)
                self.assertEqual(lpar.manager, lpar_mgr)

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on LparManager
        instance in CPC.
        """
        lpar_mgr = self.cpc.lpars
        with requests_mock.mock() as m:
            result = {
                'logical-partitions': [
                    {
                        'status': 'not-activated',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-1',
                        'name': 'LPAR1'
                    },
                    {
                        'status': 'operating',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-2',
                        'name': 'LPAR2'
                    }

                ]
            }
            m.get('/api/cpcs/fake-cpc-id-1/logical-partitions', json=result)

            mock_result_lpar1 = {
                'status': 'not-activated',
                'object-uri': '/api/logical-partitions/fake-lpar-id-1',
                'name': 'LPAR1',
                'description': 'LPAR Image',
                'more_properties': 'bliblablub'
            }
            m.get('/api/logical-partitions/fake-lpar-id-1',
                  json=mock_result_lpar1)
            mock_result_lpar2 = {
                'status': 'not-activated',
                'object-uri': '/api/logical-partitions/fake-lpar-id-2',
                'name': 'LPAR2',
                'description': 'LPAR Image',
                'more_properties': 'bliblablub'
            }
            m.get('/api/logical-partitions/fake-lpar-id-2',
                  json=mock_result_lpar2)

            lpars = lpar_mgr.list(full_properties=True)

            self.assertEqual(len(lpars), len(result['logical-partitions']))
            for idx, lpar in enumerate(lpars):
                self.assertEqual(lpar.properties['name'],
                                 result['logical-partitions'][idx]['name'])
                self.assertEqual(
                    lpar.uri,
                    result['logical-partitions'][idx]['object-uri'])
                self.assertTrue(lpar.full_properties)
                self.assertEqual(lpar.manager, lpar_mgr)

    def test_activate(self):
        """
        This tests the 'Activate Logical Partition' operation.
        """
        lpar_mgr = self.cpc.lpars
        with requests_mock.mock() as m:
            result = {
                'logical-partitions': [
                    {
                        'status': 'not-activated',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-1',
                        'name': 'LPAR1'
                    },
                    {
                        'status': 'operating',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-2',
                        'name': 'LPAR2'
                    }
                ]
            }
            m.get('/api/cpcs/fake-cpc-id-1/logical-partitions', json=result)

            lpars = lpar_mgr.list(full_properties=False)
            lpar = lpars[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post(
                "/api/logical-partitions/fake-lpar-id-1/operations/activate",
                json=result)
            status = lpar.activate(wait_for_completion=False)
            self.assertEqual(status, result)

    def test_deactivate(self):
        """
        This tests the 'Deactivate Logical Partition' operation.
        """
        lpar_mgr = self.cpc.lpars
        with requests_mock.mock() as m:
            result = {
                'logical-partitions': [
                    {
                        'status': 'operating',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-1',
                        'name': 'LPAR1'
                    },
                    {
                        'status': 'operating',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-2',
                        'name': 'LPAR2'
                    }
                ]
            }
            m.get('/api/cpcs/fake-cpc-id-1/logical-partitions', json=result)

            lpars = lpar_mgr.list(full_properties=False)
            lpar = lpars[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post(
                "/api/logical-partitions/fake-lpar-id-1/operations/deactivate",
                json=result)
            status = lpar.deactivate(wait_for_completion=False)
            self.assertEqual(status, result)

    def test_load(self):
        """
        This tests the 'Load Logical Partition' operation.
        """
        lpar_mgr = self.cpc.lpars
        with requests_mock.mock() as m:
            result = {
                'logical-partitions': [
                    {
                        'status': 'not-operating',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-1',
                        'name': 'LPAR1'
                    },
                    {
                        'status': 'operating',
                        'object-uri': '/api/logical-partitions/fake-lpar-id-2',
                        'name': 'LPAR2'
                    }
                ]
            }
            m.get('/api/cpcs/fake-cpc-id-1/logical-partitions', json=result)

            lpars = lpar_mgr.list(full_properties=False)
            lpar = lpars[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }

            m.post("/api/logical-partitions/fake-lpar-id-1/operations/load",
                   json=result)
            status = lpar.load(load_address='5162', wait_for_completion=False)
            self.assertEqual(status, result)


if __name__ == '__main__':
    unittest.main()
