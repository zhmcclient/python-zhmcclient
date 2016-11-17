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
Unit tests for _cpc module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client, LparManager, PartitionManager


class CpcTests(unittest.TestCase):
    """All tests for Cpc and CpcManager classes."""

    def setUp(self):
        self.session = Session('fake-host', 'fake-user', 'fake-id')
        self.client = Client(self.session)  # contains CpcManager object
        with requests_mock.mock() as m:
            # Because logon is deferred until needed, we perform it
            # explicitly in order to keep mocking in the actual test simple.
            m.post('/api/sessions', json={'api-session': 'fake-session-id'})
            self.session.logon()

    def tearDown(self):
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)
            self.session.logoff()

    def test_init(self):
        """Test __init__() on CpcManager instance in client."""
        cpc_mgr = self.client.cpcs
        self.assertEqual(cpc_mgr.parent, None)
        self.assertTrue(cpc_mgr.session is self.session)

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties on CpcManager
        instance in client.
        """
        cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'P0ZHMP02',
                        'status': 'service-required',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-2',
                        'name': 'P0000P30',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)

            cpcs = cpc_mgr.list(full_properties=False)

            self.assertEqual(len(cpcs), len(result['cpcs']))
            for idx, cpc in enumerate(cpcs):
                self.assertEqual(cpc.properties, result['cpcs'][idx])

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on CpcManager
        instance in client.
        """
        cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            mock_result_cpcs = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'P0ZHMP02',
                        'status': 'service-required',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-2',
                        'name': 'P0000P30',
                        'status': 'service-required',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-3',
                        'name': 'P0000OLD',
                        'status': 'enabled',
                    }
                ]
            }
            m.get('/api/cpcs', json=mock_result_cpcs)
            mock_result_cpc1 = {
                'object-uri': '/api/cpcs/fake-cpc-id-1',
                'name': 'P0ZHMP02',
                'status': 'service-required',
                'dpm-enabled': True,
                'bla': 'blub',
            }
            m.get('/api/cpcs/fake-cpc-id-1', json=mock_result_cpc1)
            mock_result_cpc1p = {
                'partitions': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1/'
                                      'partitions/fake-part-id-1',
                        'name': 'PART1',
                        'status': 'active',
                    }
                ]
            }
            m.get('/api/cpcs/fake-cpc-id-1/partitions', json=mock_result_cpc1p)
            mock_result_cpc1l = {
                'http-status': 404,
                'reason': 1,
                'message': 'Invalid resource',
            }
            m.get('/api/cpcs/fake-cpc-id-1/logical-partitions',
                  json=mock_result_cpc1l, status_code=404, reason='Not Found')

            mock_result_cpc2 = {
                'object-uri': '/api/cpcs/fake-cpc-id-2',
                'name': 'P0000P30',
                'status': 'service-required',
                'dpm-enabled': False,
                'bla': 'baz',
            }
            m.get('/api/cpcs/fake-cpc-id-2', json=mock_result_cpc2)
            mock_result_cpc2p = {
                'http-status': 404,
                'reason': 1,
                'message': 'Invalid resource',
            }
            m.get('/api/cpcs/fake-cpc-id-2/partitions',
                  json=mock_result_cpc2p, status_code=404, reason='Not Found')
            mock_result_cpc2l = {
                'logical-partitions': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-2/'
                                      'logical-partitions/fake-lpar-id-1',
                        'name': 'LPAR1',
                        'status': 'active',
                    }
                ]
            }
            m.get('/api/cpcs/fake-cpc-id-2/logical-partitions',
                  json=mock_result_cpc2l)

            mock_result_cpc3 = {
                'object-uri': '/api/cpcs/fake-cpc-id-3',
                'name': 'P0000OLD',
                'status': 'enabled',
                'bla': 'foo',
            }
            m.get('/api/cpcs/fake-cpc-id-3', json=mock_result_cpc3)
            mock_result_cpc3p = {
                'http-status': 404,
                'reason': 1,
                'message': 'Invalid resource',
            }
            m.get('/api/cpcs/fake-cpc-id-3/partitions',
                  json=mock_result_cpc3p, status_code=404, reason='Not Found')
            mock_result_cpc3l = {
                'logical-partitions': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-3/'
                                      'logical-partitions/fake-lpar-id-1',
                        'name': 'LPAR1',
                        'status': 'active',
                    }
                ]
            }
            m.get('/api/cpcs/fake-cpc-id-3/logical-partitions',
                  json=mock_result_cpc3l)

            result = {
                'cpcs': [
                    mock_result_cpc1,
                    mock_result_cpc2,
                    mock_result_cpc3,
                ]
            }
            dpm_enabled_result = [
                True,
                False,
                False,
            ]

            cpcs = cpc_mgr.list(full_properties=True)

            self.assertEqual(len(cpcs), len(result['cpcs']))
            for idx, cpc in enumerate(cpcs):
                self.assertEqual(cpc.properties, result['cpcs'][idx])
                self.assertEqual(cpc.dpm_enabled, dpm_enabled_result[idx])
                if dpm_enabled_result[idx]:
                    self.assertTrue(
                        isinstance(cpc.partitions, PartitionManager))
                else:
                    self.assertTrue(isinstance(cpc.lpars, LparManager))

    def test_start(self):
        """
        This tests the 'Start CPC' operation.
        """
        cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'P0ZHMP02',
                        'status': 'service-required',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-2',
                        'name': 'P0000P30',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)

            cpcs = cpc_mgr.list(full_properties=False)
            cpc = cpcs[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post('/api/cpcs/fake-cpc-id-1/operations/start', json=result)
            status = cpc.start(wait_for_completion=False)
            self.assertEqual(status, result)

    def test_stop(self):
        """
        This tests the 'Stop CPC' operation.
        """
        cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'P0ZHMP02',
                        'status': 'service-required',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-2',
                        'name': 'P0000P30',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)

            cpcs = cpc_mgr.list(full_properties=False)
            cpc = cpcs[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post('/api/cpcs/fake-cpc-id-1/operations/stop', json=result)
            status = cpc.stop(wait_for_completion=False)
            self.assertEqual(status, result)

    def test_import_profiles(self):
        """
        This tests the 'Import Profiles' operation.
        """
        cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'P0ZHMP02',
                        'status': 'service-required',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-2',
                        'name': 'P0000P30',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)

            cpcs = cpc_mgr.list(full_properties=False)
            cpc = cpcs[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post('/api/cpcs/fake-cpc-id-1/operations/import-profiles',
                   json=result)
            status = cpc.import_profiles(1, wait_for_completion=False)
            self.assertEqual(status, result)

    def test_export_profiles(self):
        """
        This tests the 'Export Profiles' operation.
        """
        cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'P0ZHMP02',
                        'status': 'service-required',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-2',
                        'name': 'P0000P30',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)

            cpcs = cpc_mgr.list(full_properties=False)
            cpc = cpcs[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post('/api/cpcs/fake-cpc-id-1/operations/export-profiles',
                   json=result)
            status = cpc.export_profiles(1, wait_for_completion=False)
            self.assertEqual(status, result)

    def test_wwpns_of_partitions(self):
        """
        This tests the 'wwpns_of_partitions()' method.
        """
        cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:

            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'P0ZHMP02',
                        'status': 'service-required',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-2',
                        'name': 'P0000P30',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)

            result = {
                'partitions': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1/'
                                      'partitions/part-id-1',
                        'name': 'part-name-1',
                        'status': 'active',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1/'
                                      'partitions/part-id-2',
                        'name': 'part-name-2',
                        'status': 'active',
                    },
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1/'
                                      'partitions/part-id-3',
                        'name': 'part-name-3',
                        'status': 'active',
                    },
                ]
            }
            m.get('/api/cpcs/fake-cpc-id-1/partitions', json=result)

            # TODO: Add the request body to the mock call:
            # request = {
            #     'partitions': [
            #         '/api/cpcs/fake-cpc-id-1/partitions/part-id-1',
            #         '/api/cpcs/fake-cpc-id-1/partitions/part-id-2',
            #     ]
            # }
            result = {
                'wwpn-list': [
                    'part-name-1,adapter-id-1,devno-1,wwpn-1',
                    'part-name-2,adapter-id-1,devno-2,wwpn-2',
                ]
            }
            m.post('/api/cpcs/fake-cpc-id-1/operations/export-port-names-list',
                   json=result)

            exp_wwpn_list = [
                {
                    'partition-name': 'part-name-1',
                    'adapter-id': 'adapter-id-1',
                    'device-number': 'devno-1',
                    'wwpn': 'wwpn-1'
                },
                {
                    'partition-name': 'part-name-2',
                    'adapter-id': 'adapter-id-1',
                    'device-number': 'devno-2',
                    'wwpn': 'wwpn-2'
                },
            ]

            cpcs = cpc_mgr.list()
            cpc = cpcs[0]
            partitions = cpc.partitions.list()

            wwpn_list = cpc.get_wwpns(partitions[0:2])

            self.assertEqual(wwpn_list, exp_wwpn_list)


if __name__ == '__main__':
    unittest.main()
