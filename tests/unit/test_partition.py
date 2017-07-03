# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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

import pytest
import re
import copy
from requests.utils import quote

import requests_mock

from zhmcclient import Client, Partition, HTTPError, NotFound
from zhmcclient_mock import FakedSession
from .utils import assert_resources


# Object IDs and names of our faked partitions:
PART1_OID = 'part1-oid'
PART1_NAME = 'part 1'
PART2_OID = 'part2-oid'
PART2_NAME = 'part 2'


class TestPartition(object):
    """All tests for the Partition and PartitionManager classes."""

    def setup_method(self):
        """
        Set up a faked session, and add a faked CPC in DPM mode without any
        child resources.
        """

        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'fake-cpc1-oid',
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
        })
        self.cpc = self.client.cpcs.list()[0]

    def add_part1(self):
        """Add partition 1."""

        faked_part = self.faked_cpc.partitions.add({
            'object-id': PART1_OID,
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': PART1_NAME,
            'description': 'Partition #1',
            'status': 'active',
            'initial-memory': 1024,
            'maximum-memory': 2048,
        })
        return faked_part

    def add_part2(self):
        """Add partition 2."""

        faked_part = self.faked_cpc.partitions.add({
            'object-id': PART2_OID,
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': PART2_NAME,
            'description': 'Partition #2',
            'status': 'active',
            'initial-memory': 1024,
            'maximum-memory': 2048,
        })
        return faked_part

    def test_manager_initial_attrs(self):
        """Test initial attributes of PartitionManager."""

        manager = self.cpc.partitions

        # Verify all public properties of the manager object
        assert manager.resource_class == Partition
        assert manager.session == self.session
        assert manager.parent == self.cpc
        assert manager.cpc == self.cpc

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(),
             ['object-uri', 'name', 'status']),
            (dict(full_properties=False),
             ['object-uri', 'name', 'status']),
            (dict(full_properties=True),
             None),
        ]
    )
    def test_manager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test PartitionManager.list() with full_properties."""

        # Add two partitions
        faked_part1 = self.add_part1()
        faked_part2 = self.add_part2()

        exp_faked_partitions = [faked_part1, faked_part2]
        partition_mgr = self.cpc.partitions

        # Execute the code to be tested
        partitions = partition_mgr.list(**full_properties_kwargs)

        assert_resources(partitions, exp_faked_partitions, prop_names)

    @pytest.mark.parametrize(
        "filter_args, exp_names", [
            ({'object-id': PART1_OID},
             [PART1_NAME]),
            ({'object-id': PART2_OID},
             [PART2_NAME]),
            ({'object-id': [PART1_OID, PART2_OID]},
             [PART1_NAME, PART2_NAME]),
            ({'object-id': [PART1_OID, PART1_OID]},
             [PART1_NAME]),
            ({'object-id': PART1_OID + 'foo'},
             []),
            ({'object-id': [PART1_OID, PART2_OID + 'foo']},
             [PART1_NAME]),
            ({'object-id': [PART2_OID + 'foo', PART1_OID]},
             [PART1_NAME]),
            ({'name': PART1_NAME},
             [PART1_NAME]),
            ({'name': PART2_NAME},
             [PART2_NAME]),
            ({'name': [PART1_NAME, PART2_NAME]},
             [PART1_NAME, PART2_NAME]),
            ({'name': PART1_NAME + 'foo'},
             []),
            ({'name': [PART1_NAME, PART2_NAME + 'foo']},
             [PART1_NAME]),
            ({'name': [PART2_NAME + 'foo', PART1_NAME]},
             [PART1_NAME]),
            ({'name': [PART1_NAME, PART1_NAME]},
             [PART1_NAME]),
            ({'name': '.*part 1'},
             [PART1_NAME]),
            ({'name': 'part 1.*'},
             [PART1_NAME]),
            ({'name': 'part .'},
             [PART1_NAME, PART2_NAME]),
            ({'name': '.art 1'},
             [PART1_NAME]),
            ({'name': '.+'},
             [PART1_NAME, PART2_NAME]),
            ({'name': 'part 1.+'},
             []),
            ({'name': '.+part 1'},
             []),
            ({'name': PART1_NAME,
              'object-id': PART1_OID},
             [PART1_NAME]),
            ({'name': PART1_NAME,
              'object-id': PART1_OID + 'foo'},
             []),
            ({'name': PART1_NAME + 'foo',
              'object-id': PART1_OID},
             []),
            ({'name': PART1_NAME + 'foo',
              'object-id': PART1_OID + 'foo'},
             []),
        ]
    )
    def test_manager_list_filter_args(self, filter_args, exp_names):
        """Test PartitionManager.list() with filter_args."""

        # Add two partitions
        self.add_part1()
        self.add_part2()

        # Execute the code to be tested
        partitions = self.cpc.partitions.list(filter_args=filter_args)

        assert len(partitions) == len(exp_names)
        if exp_names:
            names = [p.properties['name'] for p in partitions]
            assert set(names) == set(exp_names)

    @pytest.mark.parametrize(
        "input_props, exp_prop_names, exp_exc", [
            ({},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-part-x'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-part-x',
              'initial-memory': 1024},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-part-x',
              'initial-memory': 1024,
              'maximum-memory': 1024},
             ['object-uri', 'name', 'initial-memory', 'maximum-memory'],
             None),
            ({'name': 'fake-part-x',
              'initial-memory': 1024,
              'maximum-memory': 1024,
              'description': 'fake description X'},
             ['object-uri', 'name', 'initial-memory', 'maximum-memory',
              'description'],
             None),
        ]
    )
    def test_manager_create(self, input_props, exp_prop_names, exp_exc):
        """Test PartitionManager.create()."""

        partition_mgr = self.cpc.partitions

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                partition = partition_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            # Note: the Partition object returned by Partition.create() has
            # the input properties plus 'object-uri'.
            partition = partition_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(partition, Partition)
            partition_name = partition.name
            exp_partition_name = partition.properties['name']
            assert partition_name == exp_partition_name
            partition_uri = partition.uri
            exp_partition_uri = partition.properties['object-uri']
            assert partition_uri == exp_partition_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in partition.properties
                if prop_name in input_props:
                    value = partition.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_resource_repr(self):
        """Test Partition.__repr__()."""

        # Add a partition
        self.add_part1()

        partition = self.cpc.partitions.list()[0]

        # Execute the code to be tested
        repr_str = repr(partition)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=partition.__class__.__name__,
                               id=id(partition)),
                        repr_str)

    @pytest.mark.parametrize(
        "initial_status, exp_exc", [
            ('stopped', None),
            ('terminated', HTTPError({'http-status': 409, 'reason': 1})),
            ('starting', HTTPError({'http-status': 409, 'reason': 1})),
            ('active', HTTPError({'http-status': 409, 'reason': 1})),
            ('stopping', HTTPError({'http-status': 409, 'reason': 1})),
            ('degraded', HTTPError({'http-status': 409, 'reason': 1})),
            ('reservation-error',
             HTTPError({'http-status': 409, 'reason': 1})),
            ('paused', HTTPError({'http-status': 409, 'reason': 1})),
        ]
    )
    def test_resource_start(self, initial_status, exp_exc):
        """Test Partition.start()."""

        # Add a faked partition
        faked_part = self.add_part1()

        # Set the initial status of the faked partition
        faked_part.properties['status'] = initial_status

        partition = self.cpc.partitions.list()[0]

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                partition.start(wait_for_completion=True)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            partition.start(wait_for_completion=True)

            partition.pull_full_properties()
            status = partition.get_property('status')
            assert status == 'active'

    @pytest.mark.parametrize(
        "initial_status, exp_exc", [
            ('stopped', HTTPError({'http-status': 409, 'reason': 1})),
            ('terminated', None),
            ('starting', HTTPError({'http-status': 409, 'reason': 1})),
            ('active', None),
            ('stopping', HTTPError({'http-status': 409, 'reason': 1})),
            ('degraded', None),
            ('reservation-error', None),
            ('paused', None),
        ]
    )
    def test_resource_stop(self, initial_status, exp_exc):
        """Test Partition.stop()."""

        # Add a faked partition
        faked_part = self.add_part1()

        # Set the initial status of the faked partition
        faked_part.properties['status'] = initial_status

        partition = self.cpc.partitions.list()[0]

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                partition.stop(wait_for_completion=True)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            partition.stop(wait_for_completion=True)

            partition.pull_full_properties()
            status = partition.get_property('status')
            assert status == 'stopped'

    @pytest.mark.parametrize(
        "initial_status, exp_exc", [
            ('stopped', None),
            ('terminated', HTTPError({'http-status': 409, 'reason': 1})),
            ('starting', HTTPError({'http-status': 409, 'reason': 1})),
            ('active', HTTPError({'http-status': 409, 'reason': 1})),
            ('stopping', HTTPError({'http-status': 409, 'reason': 1})),
            ('degraded', HTTPError({'http-status': 409, 'reason': 1})),
            ('reservation-error',
             HTTPError({'http-status': 409, 'reason': 1})),
            ('paused', HTTPError({'http-status': 409, 'reason': 1})),
        ]
    )
    def test_resource_delete(self, initial_status, exp_exc):
        """Test Partition.delete()."""

        # Add a faked partition to be tested and another one
        faked_part = self.add_part1()
        self.add_part2()

        # Set the initial status of the faked partition
        faked_part.properties['status'] = initial_status

        partition = self.cpc.partitions.find(name=faked_part.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                partition.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the partition still exists
            self.cpc.partitions.find(name=faked_part.name)

        else:

            # Execute the code to be tested.
            partition.delete()

            # Check that the partition no longer exists
            with pytest.raises(NotFound) as exc_info:
                self.cpc.partitions.find(name=faked_part.name)

    def test_resource_delete_create_same_name(self):
        """Test Partition.delete() followed by create() with same name."""

        # Add a faked partition to be tested and another one
        faked_part = self.add_part1()
        part_name = faked_part.name
        self.add_part2()

        # Construct the input properties for a third partition
        part3_props = copy.deepcopy(faked_part.properties)
        part3_props['description'] = 'Third partition'

        # Set the initial status of the faked partition
        faked_part.properties['status'] = 'stopped'  # deletable

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=part_name)

        # Execute the deletion code to be tested.
        partition.delete()

        # Check that the partition no longer exists
        with pytest.raises(NotFound):
            partition_mgr.find(name=part_name)

        # Execute the creation code to be tested.
        partition_mgr.create(part3_props)

        # Check that the partition exists again under that name
        partition3 = partition_mgr.find(name=part_name)
        description = partition3.get_property('description')
        assert description == 'Third partition'

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New partition description'},
            {'initial-memory': 512,
             'description': 'New partition description'},
        ]
    )
    def test_resource_update_properties(self, input_props):
        """Test Partition.update_properties()."""

        # Add a faked partition
        faked_part = self.add_part1()
        part_name = faked_part.name

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=part_name)

        partition.pull_full_properties()
        saved_properties = copy.deepcopy(partition.properties)

        # Execute the code to be tested
        partition.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in partition.properties
            prop_value = partition.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        partition.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in partition.properties
            prop_value = partition.properties[prop_name]
            assert prop_value == exp_prop_value

    def test_resource_update_name(self):
        """
        Test Partition.update_properties() with 'name' property.
        """

        # Add a faked partition
        faked_part = self.add_part1()
        part_name = faked_part.name

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=part_name)

        new_part_name = "new-" + part_name

        # Execute the code to be tested
        partition.update_properties(properties={'name': new_part_name})

        # Verify that the resource is no longer found by its old name, using
        # list() (this does not use the name-to-URI cache).
        partitions_list = partition_mgr.list(filter_args=dict(name=part_name))
        assert len(partitions_list) == 0

        # Verify that the resource is no longer found by its old name, using
        # find() (this uses the name-to-URI cache).
        with pytest.raises(NotFound):
            partition_mgr.find(name=part_name)

        # Verify that the resource object already reflects the update, even
        # though it has not been refreshed yet.
        assert partition.properties['name'] == new_part_name

        # Refresh the resource object and verify that it still reflects the
        # update.
        partition.pull_full_properties()
        assert partition.properties['name'] == new_part_name

        # Verify that the resource can be found by its new name, using find()
        new_partition_find = partition_mgr.find(name=new_part_name)
        assert new_partition_find.properties['name'] == new_part_name

        # Verify that the resource can be found by its new name, using list()
        new_partitions_list = partition_mgr.list(
            filter_args=dict(name=new_part_name))
        assert len(new_partitions_list) == 1
        new_partition_list = new_partitions_list[0]
        assert new_partition_list.properties['name'] == new_part_name

    def xtest_resource_dump_partition(self):
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

    def xtest_resource_psw_restart(self):
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

    def xtest_resource_mount_iso_image(self):
        """
        This tests the 'Mount ISO image' operation.
        """
        partition_mgr = self.cpc.partitions
        with requests_mock.mock() as m:

            image_name = 'faked-image-name'
            ins_file_name = 'faked-ins-file-name'
            image = b'faked-image-data'

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
            qp = '?image-name={}&ins-file-name={}'. \
                format(quote(image_name, safe=''),
                       quote(ins_file_name, safe=''))
            m.post(
                "/api/partitions/fake-part-id-1/operations/mount-iso-image" +
                qp, json=result)
            status = partition.mount_iso_image(
                image=image, image_name=image_name,
                ins_file_name=ins_file_name)
            self.assertEqual(status, None)

    def xtest_resource_unmount_iso_image(self):
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

    def xtest_manager_partition_object(self):
        """
        Test PartitionManager.partition_object().
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
