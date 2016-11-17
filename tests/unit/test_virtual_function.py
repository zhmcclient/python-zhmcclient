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
Unit tests for _virtual_function module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client, VirtualFunction


class VirtualFunctionTests(unittest.TestCase):
    """
    All tests for VirtualFunction and VirtualFunctionManager classes.
    """

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
                'virtual-function-uris': [
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-1',
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-2'
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
                'virtual-function-uris': [
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-1',
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-2'
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
        """Test __init__() on VirtualFunctionManager instance in Partition."""
        vf_mgr = self.partition.virtual_functions
        self.assertEqual(vf_mgr.partition, self.partition)

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties on
        VirtualFunctionManager instance in partition.
        """
        vf_mgr = self.partition.virtual_functions
        vfs = vf_mgr.list(full_properties=False)

        self.assertEqual(
            len(vfs),
            len(self.partition.properties['virtual-function-uris']))
        for idx, vf in enumerate(vfs):
            self.assertEqual(
                vf.properties['element-uri'],
                self.partition.properties['virtual-function-uris'][idx])
            self.assertEqual(
                vf.uri,
                self.partition.properties['virtual-function-uris'][idx])
            self.assertFalse(vf.full_properties)
            self.assertEqual(vf.manager, vf_mgr)

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on
        VirtualFunctionManager instance in partition.
        """
        vf_mgr = self.partition.virtual_functions

        with requests_mock.mock() as m:

            mock_result_vf1 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'vf1',
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-1',
                'class': 'virtual-function',
                'element-id': 'fake-vf-id-1',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/virtual-functions/'
                  'fake-vf-id-1',
                  json=mock_result_vf1)
            mock_result_vf2 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'vf2',
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-2',
                'class': 'virtual-function',
                'element-id': 'fake-vf-id-2',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/virtual-functions/'
                  'fake-vf-id-2',
                  json=mock_result_vf2)

            vfs = vf_mgr.list(full_properties=True)

            self.assertEqual(
                len(vfs),
                len(self.partition.properties['virtual-function-uris']))
            for idx, vf in enumerate(vfs):
                self.assertEqual(
                    vf.properties['element-uri'],
                    self.partition.properties['virtual-function-uris'][idx])
                self.assertEqual(
                    vf.uri,
                    self.partition.properties['virtual-function-uris'][idx])
                self.assertTrue(vf.full_properties)
                self.assertEqual(vf.manager, vf_mgr)

    def test_create(self):
        """
        This tests the 'Create Virtual Function' operation.
        """
        vf_mgr = self.partition.virtual_functions
        with requests_mock.mock() as m:
            result = {
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-1'
            }
            m.post('/api/partitions/fake-part-id-1/virtual-functions',
                   json=result)

            vf = vf_mgr.create(properties={})

            self.assertTrue(isinstance(vf, VirtualFunction))
            self.assertEqual(vf.properties, result)
            self.assertEqual(vf.uri, result['element-uri'])

    def test_delete(self):
        """
        This tests the 'Delete Virtual Function' operation.
        """
        vf_mgr = self.partition.virtual_functions
        vfs = vf_mgr.list(full_properties=False)
        vf = vfs[0]
        with requests_mock.mock() as m:
            result = {}
            m.delete(
                '/api/partitions/fake-part-id-1/virtual-functions/'
                'fake-vf-id-1',
                json=result)
            status = vf.delete()
            self.assertEqual(status, None)

    def test_update_properties(self):
        """
        This tests the 'Update Virtual Function Properties' operation.
        """
        vf_mgr = self.partition.virtual_functions
        vfs = vf_mgr.list(full_properties=False)
        vf = vfs[0]
        with requests_mock.mock() as m:
            result = {}
            m.post(
                '/api/partitions/fake-part-id-1/virtual-functions/'
                'fake-vf-id-1',
                json=result)
            status = vf.update_properties(properties={})
            self.assertEqual(status, None)


if __name__ == '__main__':
    unittest.main()
