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
Unit tests for _partition module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client, Partition


class PartitionTests(unittest.TestCase):
    """All tests for Partition and PartitionManager classes."""

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

    def tearDown(self):
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)
            self.session.logoff()

    def test_init(self):
        """Test __init__() on PartitionManager instance in CPC."""
        partition_mgr = self.cpc.partitions
        self.assertEqual(partition_mgr.cpc, self.cpc)

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties on PartitionManager
        instance in CPC.
        """
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

            partitions = partition_mgr.list(full_properties=False)

            self.assertEqual(len(partitions), len(result['partitions']))
            for idx, partition in enumerate(partitions):
                self.assertEqual(
                    partition.properties,
                    result['partitions'][idx])
                self.assertEqual(
                    partition.uri,
                    result['partitions'][idx]['object-uri'])
                self.assertFalse(partition.full_properties)
                self.assertEqual(partition.manager, partition_mgr)

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on PartitionManager
        instance in CPC.
        """
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
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1',
                  json=mock_result_part1)
            mock_result_part2 = {
                'status': 'stopped',
                'object-uri': '/api/partitions/fake-lpar-id-2',
                'name': 'PART2',
                'description': 'Test Partition',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-2',
                  json=mock_result_part2)

            partitions = partition_mgr.list(full_properties=True)

            self.assertEqual(len(partitions), len(result['partitions']))
            for idx, partition in enumerate(partitions):
                self.assertEqual(partition.properties['name'],
                                 result['partitions'][idx]['name'])
                self.assertEqual(
                    partition.uri,
                    result['partitions'][idx]['object-uri'])
                self.assertTrue(partition.full_properties)
                self.assertEqual(partition.manager, partition_mgr)

    def test_create(self):
        """
        This tests the 'Create' operation.
        """
        partition_mgr = self.cpc.partitions
        with requests_mock.mock() as m:
            result = {
                'object-uri': '/api/partitions/fake-part-id-1'
            }
            m.post('/api/cpcs/fake-cpc-id-1/partitions', json=result)

            partition = partition_mgr.create(properties={})

            self.assertTrue(isinstance(partition, Partition))
            self.assertEqual(partition.properties, result)
            self.assertEqual(partition.uri, result['object-uri'])

    def test_start(self):
        """
        This tests the 'Start Partition' operation.
        """
        partition_mgr = self.cpc.partitions
        with requests_mock.mock() as m:
            result = {
                'partitions': [
                    {
                        'status': 'stopped',
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

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post(
                "/api/partitions/fake-part-id-1/operations/start",
                json=result)
            status = partition.start(wait_for_completion=False)
            self.assertEqual(status, result)

    def test_stop(self):
        """
        This tests the 'Stop Partition' operation.
        """
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

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post(
                "/api/partitions/fake-part-id-1/operations/stop",
                json=result)
            status = partition.stop(wait_for_completion=False)
            self.assertEqual(status, result)

    def test_delete(self):
        """
        This tests the 'Delete Partition' operation.
        """
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

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            m.delete(
                "/api/partitions/fake-part-id-1",
                json=result)
            status = partition.delete()
            self.assertEqual(status, None)

    def test_update_properties(self):
        """
        This tests the 'Update Partition Properties' operation.
        """
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

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            m.post(
                "/api/partitions/fake-part-id-1",
                json=result)
            status = partition.update_properties(properties={})
            self.assertEqual(status, None)

    def test_dump_partition(self):
        """
        This tests the 'Dump Partition' operation.
        """
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

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                'job-uri': '/api/jobs/fake-job-id-1'
            }
            m.post(
                "/api/partitions/fake-part-id-1/operations/scsi-dump",
                json=result)
            status = partition.dump_partition(
                wait_for_completion=False, parameters={})
            self.assertEqual(status, result)

    def test_psw_restart(self):
        """
        This tests the 'Perform PSW Restart' operation.
        """
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

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                'job-uri': '/api/jobs/fake-job-id-1'
            }
            m.post(
                "/api/partitions/fake-part-id-1/operations/psw-restart",
                json=result)
            status = partition.psw_restart(wait_for_completion=False)
            self.assertEqual(status, result)

    def test_mount_iso_image(self):
        """
        This tests the 'Mount ISO image' operation.
        """
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

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                'job-uri': '/api/jobs/fake-job-id-1'
            }
            m.post(
                "/api/partitions/fake-part-id-1/operations/mount-iso-image",
                json=result)
            status = partition.mount_iso_image(properties={})
            self.assertEqual(status, None)

    def test_unmount_iso_image(self):
        """
        This tests the 'Unmount ISO image' operation.
        """
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

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                'job-uri': '/api/jobs/fake-job-id-1'
            }
            m.post(
                "/api/partitions/fake-part-id-1/operations/unmount-iso-image",
                json=result)
            status = partition.unmount_iso_image()
            self.assertEqual(status, None)

    def test_partition_object(self):
        """
        This tests the `partition_object()` method.
        """
        partition_mgr = self.cpc.partitions
        partition_id = 'fake-partition-id42'

        partition = partition_mgr.partition_object(partition_id)

        partition_uri = "/api/partitions/" + partition_id

        self.assertTrue(isinstance(partition, Partition))
        self.assertEqual(partition.uri, partition_uri)
        self.assertEqual(partition.properties['object-uri'], partition_uri)
        self.assertEqual(partition.properties['object-id'], partition_id)
        self.assertEqual(partition.properties['class'], 'partition')
        self.assertEqual(partition.properties['parent'], self.cpc.uri)


if __name__ == '__main__':
    unittest.main()
