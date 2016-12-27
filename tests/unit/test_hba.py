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
Unit tests for _hba module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client, Hba, Adapter, Port


class HbaTests(unittest.TestCase):
    """All tests for Hba and HbaManager classes."""

    def setUp(self):
        self.session = Session('test-dpm-host', 'test-user', 'test-id')
        self.client = Client(self.session)
        with requests_mock.mock() as m:
            # Because logon is deferred until needed, we perform it
            # explicitly in order to keep mocking in the actual test simple.
            m.post('/api/sessions', json={'api-session': 'test-session-id'})
            self.session.logon()

        self.cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'CPC1',
                        'status': '',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)
#            self.cpc = self.cpc_mgr.find(name="CPC1", full_properties=False)
            cpcs = self.cpc_mgr.list()
            self.cpc = cpcs[0]

        partition_mgr = self.cpc.partitions
        with requests_mock.mock() as m:
            result = {
                'partitions': [
                    {
                        'status': 'active',
                        'object-uri': '/api/partitions/fake-part-id-1',
                        'name': 'PART1'
                    },
                    {
                        'status': 'stopped',
                        'object-uri': '/api/partitions/fake-part-id-2',
                        'name': 'PART2'
                    }
                ]
            }

            m.get('/api/cpcs/fake-cpc-id-1/partitions', json=result)

            mock_result_part1 = {
                'status': 'active',
                'object-uri': '/api/partitions/fake-part-id-1',
                'name': 'PART1',
                'description': 'Test Partition',
                'more_properties': 'bliblablub',
                'hba-uris': [
                    '/api/partitions/fake-part-id-1/hbas/fake-hba-id-1',
                    '/api/partitions/fake-part-id-1/hbas/fake-hba-id-2'
                ]
            }
            m.get('/api/partitions/fake-part-id-1',
                  json=mock_result_part1)
            mock_result_part2 = {
                'status': 'stopped',
                'object-uri': '/api/partitions/fake-lpar-id-2',
                'name': 'PART2',
                'description': 'Test Partition',
                'more_properties': 'bliblablub',
                'hba-uris': [
                    '/api/partitions/fake-part-id-2/hbas/fake-hba-id-4',
                    '/api/partitions/fake-part-id-2/hbas/fake-hba-id-6'
                ]
            }
            m.get('/api/partitions/fake-part-id-2',
                  json=mock_result_part2)

            partitions = partition_mgr.list(full_properties=True)
            self.partition = partitions[0]

    def tearDown(self):
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)
            self.session.logoff()

    def test_init(self):
        """Test __init__() on HbaManager instance in Partition."""
        hba_mgr = self.partition.hbas
        self.assertEqual(hba_mgr.partition, self.partition)

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties on
        HbaManager instance in partition.
        """
        hba_mgr = self.partition.hbas
        hbas = hba_mgr.list(full_properties=False)

        self.assertEqual(len(hbas), len(self.partition.properties['hba-uris']))
        for idx, hba in enumerate(hbas):
            self.assertEqual(
                hba.properties['element-uri'],
                self.partition.properties['hba-uris'][idx])
            self.assertEqual(
                hba.uri,
                self.partition.properties['hba-uris'][idx])
            self.assertFalse(hba.full_properties)
            self.assertEqual(hba.manager, hba_mgr)

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on
        HbaManager instance in partition.
        """
        hba_mgr = self.partition.hbas

        with requests_mock.mock() as m:

            mock_result_hba1 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'hba1',
                'element-uri':
                    '/api/partitions/fake-part-id-1/hbas/fake-hba-id-1',
                'class': 'hba',
                'element-id': 'fake-hba-id-1',
                'wwpn': 'AABBCCDDEC000082',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/hbas/fake-hba-id-1',
                  json=mock_result_hba1)
            mock_result_hba2 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'hba2',
                'element-uri':
                    '/api/partitions/fake-part-id-1/hbas/fake-hba-id-2',
                'class': 'hba',
                'element-id': 'fake-hba-id-2',
                'wwpn': 'AABBCCDDEC000083',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/hbas/fake-hba-id-2',
                  json=mock_result_hba2)

            hbas = hba_mgr.list(full_properties=True)

            self.assertEqual(
                len(hbas),
                len(self.partition.properties['hba-uris']))
            for idx, hba in enumerate(hbas):
                self.assertEqual(
                    hba.properties['element-uri'],
                    self.partition.properties['hba-uris'][idx])
                self.assertEqual(
                    hba.uri,
                    self.partition.properties['hba-uris'][idx])
                self.assertTrue(hba.full_properties)
                self.assertEqual(hba.manager, hba_mgr)

    def test_create(self):
        """
        This tests the 'Create HBA' operation.
        """
        hba_mgr = self.partition.hbas
        with requests_mock.mock() as m:
            result = {
                'element-uri':
                    '/api/partitions/fake-part-id-1/hbas/fake-hba-id-1'
            }
            m.post('/api/partitions/fake-part-id-1/hbas', json=result)

            hba = hba_mgr.create(properties={})

            self.assertTrue(isinstance(hba, Hba))
            self.assertEqual(hba.properties, result)
            self.assertEqual(hba.uri, result['element-uri'])

    def test_delete(self):
        """
        This tests the 'Delete HBA' operation.
        """
        hba_mgr = self.partition.hbas
        hbas = hba_mgr.list(full_properties=False)
        hba = hbas[0]
        with requests_mock.mock() as m:
            result = {}
            m.delete(
                '/api/partitions/fake-part-id-1/hbas/fake-hba-id-1',
                json=result)
            status = hba.delete()
            self.assertEqual(status, None)

    def test_update_properties(self):
        """
        This tests the 'Update HBA Properties' operation.
        """
        hba_mgr = self.partition.hbas
        hbas = hba_mgr.list(full_properties=False)
        hba = hbas[0]
        with requests_mock.mock() as m:
            result = {}
            m.post(
                '/api/partitions/fake-part-id-1/hbas/fake-hba-id-1',
                json=result)
            status = hba.update_properties(properties={})
            self.assertEqual(status, None)

    def test_reassign_port(self):
        """
        This tests the 'reassign_port()' method.
        """
        hba_mgr = self.partition.hbas
        hba_uri = '/api/partitions/fake-part-id-1/hbas/fake-hba-id-1'
        hba = Hba(hba_mgr, hba_uri)

        adapter_mgr = self.cpc.adapters
        adapter_uri = '/api/adapters/fake-adapter-id-1'
        adapter = Adapter(adapter_mgr, adapter_uri)

        port_mgr = adapter.ports
        port2_uri = '/api/adapters/fake-adapter-id-2/'\
                    'storage-ports/fake-port-id-2'
        port2 = Port(port_mgr, port2_uri)

        with requests_mock.mock() as m:
            # TODO: Add the request body to the mock call:
            # request_reassign = {
            #     'adapter-port-uri': port2_uri
            # }
            m.post(hba_uri + '/operations/reassign-storage-adapter-port',
                   json={})

            hba.reassign_port(port2)


if __name__ == '__main__':
    unittest.main()
