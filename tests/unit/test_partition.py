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

        self.cpc_id = 'fake-cpc-id-1'
        self.cpc_name = 'CPC1'

        self.cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/%s' % self.cpc_id,
                        'name': self.cpc_name,
                        'status': '',
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
            m.get('/api/cpcs/%s/partitions' % self.cpc_id, json=result)

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
            m.get('/api/cpcs/%s/partitions' % self.cpc_id, json=result)

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

    def test_create_empty_input(self):
        """
        This tests the 'Create' operation, with no input properties.
        """
        partition_mgr = self.cpc.partitions

        part_id = 'fake-part-id-1'  # created by faked HMC
        part_uri = '/api/partitions/%s' % part_id
        part_name = 'fake-part-name-1'

        with requests_mock.mock() as m:
            input_props = {
            }
            mock_create_result = {
                'object-uri': part_uri
            }
            # this test implements a mocked HMC that creates a default name:
            mock_get_result = {
                'object-uri': part_uri,
                'name': part_name
            }
            m.post('/api/cpcs/%s/partitions' % self.cpc_id,
                   json=mock_create_result)

            partition = partition_mgr.create(properties=input_props)

            props = input_props.copy()
            props.update(mock_create_result)

            self.assertTrue(isinstance(partition, Partition))
            self.assertEqual(partition.properties, props)
            self.assertEqual(partition.uri, part_uri)

            # Check the name property (accessing it will cause a get)
            m.get(part_uri, json=mock_get_result)
            self.assertEqual(partition.name, part_name)

    def test_create_name_input(self):
        """
        This tests the 'Create' operation, with partition name as input
        properties.
        """
        partition_mgr = self.cpc.partitions

        part_id = 'fake-part-id-1'  # created by faked HMC
        part_uri = '/api/partitions/%s' % part_id
        part_name = 'fake-part-name-1'

        with requests_mock.mock() as m:
            input_props = {
                'name': part_name
            }
            mock_create_result = {
                'object-uri': part_uri
            }
            m.post('/api/cpcs/%s/partitions' % self.cpc_id,
                   json=mock_create_result)

            partition = partition_mgr.create(properties=input_props)

            props = input_props.copy()
            props.update(mock_create_result)

            self.assertTrue(isinstance(partition, Partition))
            self.assertEqual(partition.properties, props)
            self.assertEqual(partition.uri, part_uri)

            # Check the name property (accessing it will not cause a get,
            # because the create() method is supposed to also update the
            # properties of the Python resource object, so the property
            # is already available).
            self.assertEqual(partition.name, part_name)

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
            m.get('/api/cpcs/%s/partitions' % self.cpc_id, json=result)

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post("/api/partitions/fake-part-id-1/operations/start",
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
            m.get('/api/cpcs/%s/partitions' % self.cpc_id, json=result)

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                "job-reason-code": 0,
                "job-status-code": 204,
                "status": "complete"
            }
            m.post("/api/partitions/fake-part-id-1/operations/stop",
                   json=result)
            status = partition.stop(wait_for_completion=False)
            self.assertEqual(status, result)

    def test_delete(self):
        """
        This tests the 'Delete Partition' operation.
        """
        partition_mgr = self.cpc.partitions
        with requests_mock.mock() as m:
            initial_partitions = {
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
            m.get('/api/cpcs/%s/partitions' % self.cpc_id,
                  json=initial_partitions)

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            m.delete("/api/partitions/fake-part-id-1", status_code=204)
            partition.delete()

    def test_delete_create_same_name(self):
        """
        This tests a partition deletion followed by a creation of a partition
        with the same name.
        """
        partition_mgr = self.cpc.partitions
        with requests_mock.mock() as m:
            partition1_uri = '/api/partitions/fake-part-id-1#1'
            list_partitions_result = {
                'partitions': [
                    {
                        'status': 'active',
                        'object-uri': partition1_uri,
                        'name': 'PART1',
                        'description': 'PART1 #1'
                    },
                    {
                        'status': 'stopped',
                        'object-uri': '/api/partitions/fake-part-id-2#1',
                        'name': 'PART2',
                        'description': 'PART2 #1'
                    }
                ]
            }
            m.get('/api/cpcs/%s/partitions' % self.cpc_id,
                  json=list_partitions_result)

            # Find the partition.
            partition1 = partition_mgr.find(name='PART1')

            # Delete the partition.
            m.delete(partition1_uri)
            status = partition1.delete()
            self.assertEqual(status, None)

            # Create a new partition with the same name.
            partition1_new_uri = '/api/partitions/fake-part-id-1#2'
            partition1_new_props = {
                'name': 'PART1',
                'description': 'PART1 #2'
            }
            create_partition1_new_result = {
                'object-uri': partition1_new_uri
            }
            m.post('/api/cpcs/%s/partitions' % self.cpc_id,
                   json=create_partition1_new_result)
            partition1_new_created = partition_mgr.create(partition1_new_props)
            self.assertNotEqual(partition1_new_created.uri, partition1_uri)
            self.assertEqual(partition1_new_created.uri, partition1_new_uri)

            # Find the new partition.
            partition1_new_found = partition_mgr.find(name='PART1')
            self.assertEqual(partition1_new_found.uri, partition1_new_uri)

    def test_update_properties_all(self):
        """
        This tests the `update_properties()` method with a number of different
        new properties.
        """

        # Each list item is a separate test.
        # TODO: Use fixtures instead of loop, for better diagnostics
        update_props_tests = [
            {},
            {'name': 'PART1-updated'},
            {'description': 'new description added'},
        ]

        partition_mgr = self.cpc.partitions

        for update_props in update_props_tests:
            with requests_mock.mock() as m:
                list_partitions_result = {
                    'partitions': [
                        {
                            'status': 'active',
                            'object-uri': '/api/partitions/fake-part-id-1',
                            'name': 'PART1'
                        }
                    ]
                }
                m.get('/api/cpcs/%s/partitions' % self.cpc_id,
                      json=list_partitions_result)
                partition = partition_mgr.list(full_properties=False)[0]
                partition_props = partition.properties.copy()

                m.post("/api/partitions/fake-part-id-1", status_code=204)
                partition.update_properties(properties=update_props)

                list_partitions_result['partitions'][0].update(update_props)
                partition_upd = partition_mgr.list(full_properties=False)[0]
                partition_upd_props = partition_upd.properties.copy()

                exp_partition_upd_props = partition_props.copy()
                exp_partition_upd_props.update(update_props)
                self.assertEqual(partition_upd_props, exp_partition_upd_props)

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
            m.get('/api/cpcs/%s/partitions' % self.cpc_id, json=result)

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                'job-uri': '/api/jobs/fake-job-id-1'
            }
            m.post("/api/partitions/fake-part-id-1/operations/scsi-dump",
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
            m.get('/api/cpcs/%s/partitions' % self.cpc_id, json=result)

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                'job-uri': '/api/jobs/fake-job-id-1'
            }
            m.post("/api/partitions/fake-part-id-1/operations/psw-restart",
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
            m.get('/api/cpcs/%s/partitions' % self.cpc_id, json=result)

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                'job-uri': '/api/jobs/fake-job-id-1'
            }
            m.post("/api/partitions/fake-part-id-1/operations/mount-iso-image",
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
            m.get('/api/cpcs/%s/partitions' % self.cpc_id, json=result)

            partitions = partition_mgr.list(full_properties=False)
            partition = partitions[0]
            result = {
                'job-uri': '/api/jobs/fake-job-id-1'
            }
            m.post("/api/partitions/fake-part-id-1/operations/"
                   "unmount-iso-image", json=result)
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
