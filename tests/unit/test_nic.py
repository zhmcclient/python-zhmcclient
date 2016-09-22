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
Unit tests for _nic module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client, Nic


class NicTests(unittest.TestCase):
    """All tests for Nic and NicManager classes."""

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
                'nic-uris': [
                    '/api/partitions/fake-part-id-1/nics/fake-nic-id-1',
                    '/api/partitions/fake-part-id-1/nics/fake-nic-id-2'
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
                'nic-uris': [
                    '/api/partitions/fake-part-id-2/nics/fake-nic-id-4',
                    '/api/partitions/fake-part-id-2/nics/fake-nic-id-6'
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
        """Test __init__() on NicManager instance in Partition."""
        nic_mgr = self.partition.nics
        self.assertEqual(nic_mgr.partition, self.partition)

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties on
        NicManager instance in partition.
        """
        nic_mgr = self.partition.nics
        nics = nic_mgr.list(full_properties=False)

        self.assertEqual(len(nics), len(self.partition.properties['nic-uris']))
        for idx, nic in enumerate(nics):
            self.assertEqual(
                nic.properties['element-uri'],
                self.partition.properties['nic-uris'][idx])
            self.assertEqual(
                nic.uri,
                self.partition.properties['nic-uris'][idx])
            self.assertFalse(nic.full_properties)
            self.assertEqual(nic.manager, nic_mgr)

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on
        NicManager instance in partition.
        """
        nic_mgr = self.partition.nics

        with requests_mock.mock() as m:

            mock_result_nic1 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'nic1',
                'element-uri':
                    '/api/partitions/fake-part-id-1/nics/fake-nic-id-1',
                'class': 'nic',
                'element-id': 'fake-nic-id-1',
                'type': 'osd',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/nics/fake-nic-id-1',
                  json=mock_result_nic1)
            mock_result_nic2 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'nic2',
                'element-uri':
                    '/api/partitions/fake-part-id-1/nics/fake-nic-id-2',
                'class': 'nic',
                'element-id': 'fake-nic-id-2',
                'type': 'osd',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/nics/fake-nic-id-2',
                  json=mock_result_nic2)

            nics = nic_mgr.list(full_properties=True)

            self.assertEqual(
                len(nics),
                len(self.partition.properties['nic-uris']))
            for idx, nic in enumerate(nics):
                self.assertEqual(
                    nic.properties['element-uri'],
                    self.partition.properties['nic-uris'][idx])
                self.assertEqual(
                    nic.uri,
                    self.partition.properties['nic-uris'][idx])
                self.assertTrue(nic.full_properties)
                self.assertEqual(nic.manager, nic_mgr)

    def test_create(self):
        """
        This tests the 'Create NIC' operation.
        """
        nic_mgr = self.partition.nics
        with requests_mock.mock() as m:
            result = {
                'element-uri':
                    '/api/partitions/fake-part-id-1/nics/fake-nic-id-1'
            }
            m.post('/api/partitions/fake-part-id-1/nics', json=result)

            nic = nic_mgr.create(properties={})

            self.assertTrue(isinstance(nic, Nic))
            self.assertEqual(nic.properties, result)
            self.assertEqual(nic.uri, result['element-uri'])

    def test_delete(self):
        """
        This tests the 'Delete NIC' operation.
        """
        nic_mgr = self.partition.nics
        nics = nic_mgr.list(full_properties=False)
        nic = nics[0]
        with requests_mock.mock() as m:
            result = {}
            m.delete(
                '/api/partitions/fake-part-id-1/nics/fake-nic-id-1',
                json=result)
            status = nic.delete()
            self.assertEqual(status, None)

    def test_update_properties(self):
        """
        This tests the 'Update NIC Properties' operation.
        """
        nic_mgr = self.partition.nics
        nics = nic_mgr.list(full_properties=False)
        nic = nics[0]
        with requests_mock.mock() as m:
            result = {}
            m.post(
                '/api/partitions/fake-part-id-1/nics/fake-nic-id-1',
                json=result)
            status = nic.update_properties(properties={})
            self.assertEqual(status, None)

    def test_nic_object(self):
        """
        This tests the `nic_object()` method.
        """
        nic_mgr = self.partition.nics
        nic_id = 'fake-nic-id0711'

        nic = nic_mgr.nic_object(nic_id)

        nic_uri = self.partition.uri + "/nics/" + nic_id

        self.assertTrue(isinstance(nic, Nic))
        self.assertEqual(nic.uri, nic_uri)
        self.assertEqual(nic.properties['element-uri'], nic_uri)
        self.assertEqual(nic.properties['element-id'], nic_id)
        self.assertEqual(nic.properties['class'], 'nic')
        self.assertEqual(nic.properties['parent'], self.partition.uri)


if __name__ == '__main__':
    unittest.main()
