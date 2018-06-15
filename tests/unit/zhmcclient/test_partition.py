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

from zhmcclient import Client, Partition, HTTPError, NotFound
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked partitions:
PART1_OID = 'part1-oid'
PART1_NAME = 'part 1'
PART2_OID = 'part2-oid'
PART2_NAME = 'part 2'
PART3_OID = 'part3-oid'
PART3_NAME = 'part 3'


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
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

    def add_partition1(self):
        """Add partition 1 (type linux)."""

        faked_partition = self.faked_cpc.partitions.add({
            'object-id': PART1_OID,
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': PART1_NAME,
            'description': 'Partition #1',
            'status': 'active',
            'type': 'linux',
            'initial-memory': 1024,
            'maximum-memory': 2048,
        })
        return faked_partition

    def add_partition2(self):
        """Add partition 2 (type ssc)."""

        faked_partition = self.faked_cpc.partitions.add({
            'object-id': PART2_OID,
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': PART2_NAME,
            'description': 'Partition #2',
            'status': 'active',
            'type': 'ssc',
            'initial-memory': 1024,
            'maximum-memory': 2048,
        })
        return faked_partition

    def add_partition3(self):
        """Add partition 3 (support for firmware features)."""

        faked_partition = self.faked_cpc.partitions.add({
            'object-id': PART3_OID,
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': PART3_NAME,
            'description': 'Partition #3',
            'status': 'active',
            'type': 'linux',
            'initial-memory': 1024,
            'maximum-memory': 2048,
            'available-features-list': [],
        })
        return faked_partition

    def add_partition(self, part_name):
        """Add a partition (using one of the known names)."""

        if part_name == PART1_NAME:
            faked_partition = self.add_partition1()
        elif part_name == PART2_NAME:
            faked_partition = self.add_partition2()
        elif part_name == PART3_NAME:
            faked_partition = self.add_partition3()
        return faked_partition

    def test_partitionmanager_initial_attrs(self):
        """Test initial attributes of PartitionManager."""

        partition_mgr = self.cpc.partitions

        # Verify all public properties of the manager object
        assert partition_mgr.resource_class == Partition
        assert partition_mgr.session == self.session
        assert partition_mgr.parent == self.cpc
        assert partition_mgr.cpc == self.cpc

    # TODO: Test for PartitionManager.__repr__()

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
    def test_partitionmanager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test PartitionManager.list() with full_properties."""

        # Add two faked partitions
        faked_partition1 = self.add_partition1()
        faked_partition2 = self.add_partition2()

        exp_faked_partitions = [faked_partition1, faked_partition2]
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
    def test_partitionmanager_list_filter_args(self, filter_args, exp_names):
        """Test PartitionManager.list() with filter_args."""

        # Add two faked partitions
        self.add_partition1()
        self.add_partition2()

        partition_mgr = self.cpc.partitions

        # Execute the code to be tested
        partitions = partition_mgr.list(filter_args=filter_args)

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
    def test_partitionmanager_create(self, input_props, exp_prop_names,
                                     exp_exc):
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

    def test_partitionmanager_resource_object(self):
        """
        Test PartitionManager.resource_object().

        This test exists for historical reasons, and by now is covered by the
        test for BaseManager.resource_object().
        """
        partition_mgr = self.cpc.partitions

        partition_oid = 'fake-partition-id42'

        # Execute the code to be tested
        partition = partition_mgr.resource_object(partition_oid)

        partition_uri = "/api/partitions/" + partition_oid

        assert isinstance(partition, Partition)
        assert partition.uri == partition_uri
        assert partition.properties['object-uri'] == partition_uri
        assert partition.properties['object-id'] == partition_oid
        assert partition.properties['class'] == 'partition'
        assert partition.properties['parent'] == self.cpc.uri

    # TODO: Test for initial Partition attributes (nics, hbas,
    #       virtual_functions)

    def test_partition_repr(self):
        """Test Partition.__repr__()."""

        # Add a faked partition
        faked_partition = self.add_partition1()

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=faked_partition.name)

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
    def test_partition_delete(self, initial_status, exp_exc):
        """Test Partition.delete()."""

        # Add a faked partition to be tested and another one
        faked_partition = self.add_partition1()
        self.add_partition2()

        # Set the initial status of the faked partition
        faked_partition.properties['status'] = initial_status

        partition_mgr = self.cpc.partitions

        partition = partition_mgr.find(name=faked_partition.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                partition.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the partition still exists
            partition_mgr.find(name=faked_partition.name)

        else:

            # Execute the code to be tested.
            partition.delete()

            # Check that the partition no longer exists
            with pytest.raises(NotFound) as exc_info:
                partition_mgr.find(name=faked_partition.name)

    def test_partition_delete_create_same_name(self):
        """Test Partition.delete() followed by create() with same name."""

        # Add a faked partition to be tested and another one
        faked_partition = self.add_partition1()
        partition_name = faked_partition.name
        self.add_partition2()

        # Construct the input properties for a third partition
        part3_props = copy.deepcopy(faked_partition.properties)
        part3_props['description'] = 'Third partition'

        # Set the initial status of the faked partition
        faked_partition.properties['status'] = 'stopped'  # deletable

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=partition_name)

        # Execute the deletion code to be tested.
        partition.delete()

        # Check that the partition no longer exists
        with pytest.raises(NotFound):
            partition_mgr.find(name=partition_name)

        # Execute the creation code to be tested.
        partition_mgr.create(part3_props)

        # Check that the partition exists again under that name
        partition3 = partition_mgr.find(name=partition_name)
        description = partition3.get_property('description')
        assert description == 'Third partition'

    @pytest.mark.parametrize(
        "desc, partition_name, available_features, feature_name, "
        "exp_feature_enabled, exp_exc", [
            (
                "No feature support on the CPC",
                PART1_NAME,
                None,
                'fake-feature1', None, ValueError()
            ),
            (
                "Feature not available on the partition (empty feature list)",
                PART3_NAME,
                [],
                'fake-feature1', None, ValueError()
            ),
            (
                "Feature not available on the part (one other feature avail)",
                PART3_NAME,
                [
                    dict(name='fake-feature-foo', state=True),
                ],
                'fake-feature1', None, ValueError()
            ),
            (
                "Feature disabled (the only feature available)",
                PART3_NAME,
                [
                    dict(name='fake-feature1', state=False),
                ],
                'fake-feature1', False, None
            ),
            (
                "Feature enabled (the only feature available)",
                PART3_NAME,
                [
                    dict(name='fake-feature1', state=True),
                ],
                'fake-feature1', True, None
            ),
        ]
    )
    def test_partition_feature_enabled(
            self, desc, partition_name, available_features, feature_name,
            exp_feature_enabled, exp_exc):
        """Test Partition.feature_enabled()."""

        # Add a faked Partition
        faked_partition = self.add_partition(partition_name)

        # Set up the firmware feature list
        if available_features is not None:
            faked_partition.properties['available-features-list'] = \
                available_features

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=partition_name)

        if exp_exc:
            with pytest.raises(exp_exc.__class__):

                # Execute the code to be tested
                partition.feature_enabled(feature_name)

        else:

            # Execute the code to be tested
            act_feature_enabled = partition.feature_enabled(feature_name)

            assert act_feature_enabled == exp_feature_enabled

    @pytest.mark.parametrize(
        "desc, partition_name, available_features, exp_exc", [
            (
                "No feature support on the CPC",
                PART1_NAME,
                None,
                ValueError()
            ),
            (
                "Feature not available on the partition (empty feature list)",
                PART3_NAME,
                [],
                None
            ),
            (
                "Feature not available on the part (one other feature avail)",
                PART3_NAME,
                [
                    dict(name='fake-feature-foo', state=True),
                ],
                None
            ),
            (
                "Feature disabled (the only feature available)",
                PART3_NAME,
                [
                    dict(name='fake-feature1', state=False),
                ],
                None
            ),
            (
                "Feature enabled (the only feature available)",
                PART3_NAME,
                [
                    dict(name='fake-feature1', state=True),
                ],
                None
            ),
        ]
    )
    def test_partition_feature_info(
            self, desc, partition_name, available_features, exp_exc):
        """Test Partition.feature_info()."""

        # Add a faked Partition
        faked_partition = self.add_partition(partition_name)

        # Set up the firmware feature list
        if available_features is not None:
            faked_partition.properties['available-features-list'] = \
                available_features

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=partition_name)

        if exp_exc:
            with pytest.raises(exp_exc.__class__):

                # Execute the code to be tested
                partition.feature_info()

        else:

            # Execute the code to be tested
            act_features = partition.feature_info()

            assert act_features == available_features

    @pytest.mark.parametrize(
        "partition_name", [
            PART1_NAME,
            PART2_NAME,
        ]
    )
    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New partition description'},
            {'initial-memory': 512,
             'description': 'New partition description'},
            {'autogenerate-partition-id': True,
             'partition-id': None},
            {'boot-device': 'none',
             'boot-ftp-host': None,
             'boot-ftp-username': None,
             'boot-ftp-password': None,
             'boot-ftp-insfile': None},
            {'boot-device': 'none',
             'boot-network-device': None},
            {'boot-device': 'none',
             'boot-removable-media': None,
             'boot-removable-media-type': None},
            {'boot-device': 'none',
             'boot-storage-device': None,
             'boot-logical-unit-number': None,
             'boot-world-wide-port-name': None},
            {'boot-device': 'none',
             'boot-iso-image-name': None,
             'boot-iso-insfile': None},
            {'ssc-ipv4-gateway': None,
             'ssc-ipv6-gateway': None,
             'ssc-master-userid': None,
             'ssc-master-pw': None},
        ]
    )
    def test_partition_update_properties(self, input_props, partition_name):
        """Test Partition.update_properties()."""

        # Add faked partitions
        self.add_partition1()
        self.add_partition2()

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=partition_name)

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

    def test_partition_update_name(self):
        """
        Test Partition.update_properties() with 'name' property.
        """

        # Add a faked partition
        faked_partition = self.add_partition1()
        partition_name = faked_partition.name

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=partition_name)

        new_partition_name = "new-" + partition_name

        # Execute the code to be tested
        partition.update_properties(properties={'name': new_partition_name})

        # Verify that the resource is no longer found by its old name, using
        # list() (this does not use the name-to-URI cache).
        partitions_list = partition_mgr.list(
            filter_args=dict(name=partition_name))
        assert len(partitions_list) == 0

        # Verify that the resource is no longer found by its old name, using
        # find() (this uses the name-to-URI cache).
        with pytest.raises(NotFound):
            partition_mgr.find(name=partition_name)

        # Verify that the resource object already reflects the update, even
        # though it has not been refreshed yet.
        assert partition.properties['name'] == new_partition_name

        # Refresh the resource object and verify that it still reflects the
        # update.
        partition.pull_full_properties()
        assert partition.properties['name'] == new_partition_name

        # Verify that the resource can be found by its new name, using find()
        new_partition_find = partition_mgr.find(name=new_partition_name)
        assert new_partition_find.properties['name'] == new_partition_name

        # Verify that the resource can be found by its new name, using list()
        new_partitions_list = partition_mgr.list(
            filter_args=dict(name=new_partition_name))
        assert len(new_partitions_list) == 1
        new_partition_list = new_partitions_list[0]
        assert new_partition_list.properties['name'] == new_partition_name

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
    def test_partition_start(self, initial_status, exp_exc):
        """Test Partition.start()."""

        # Add a faked partition
        faked_partition = self.add_partition1()

        # Set the initial status of the faked partition
        faked_partition.properties['status'] = initial_status

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=faked_partition.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                partition.start()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            ret = partition.start()

            assert ret == {}

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
            ('degraded', HTTPError({'http-status': 409, 'reason': 1})),
            ('reservation-error',
             HTTPError({'http-status': 409, 'reason': 1})),
            ('paused', None),
        ]
    )
    def test_partition_stop(self, initial_status, exp_exc):
        """Test Partition.stop()."""

        # Add a faked partition
        faked_partition = self.add_partition1()

        # Set the initial status of the faked partition
        faked_partition.properties['status'] = initial_status

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=faked_partition.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                partition.stop()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            ret = partition.stop()

            assert ret == {}

            partition.pull_full_properties()
            status = partition.get_property('status')
            assert status == 'stopped'

    # TODO: Re-enable test_partition_dump_partition() once supported in hdlr
    def xtest_partition_dump_partition(self):
        """Test Partition.dump_partition()."""

        # Add a faked partition
        faked_partition = self.add_partition1()

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=faked_partition.name)

        parameters = {
            'dump-load-hba-uri': 'fake-hba-uri',
            'dump-world-wide-port-name': 'fake-wwpn',
            'dump-logical-unit-number': 'fake-lun',
        }

        # Execute the code to be tested.
        ret = partition.dump_partition(parameters=parameters)

        assert ret == {}

    # TODO: Re-enable test_partition_psw_restart() once supported in hdlr
    def xtest_partition_psw_restart(self):
        """Test Partition.psw_restart()."""

        # Add a faked partition
        faked_partition = self.add_partition1()

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=faked_partition.name)

        # Execute the code to be tested.
        ret = partition.psw_restart()

        assert ret == {}

    # TODO: Re-enable test_partition_mount_iso_image() once supported in hdlr
    def xtest_partition_mount_iso_image(self):
        """Test Partition.mount_iso_image()."""

        # Add a faked partition
        faked_partition = self.add_partition1()

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=faked_partition.name)

        image = b'fake-image-data'
        image_name = 'fake-image-name'
        ins_file_name = 'fake-ins-file-name'

        # Execute the code to be tested.
        ret = partition.mount_iso_image(image=image, image_name=image_name,
                                        ins_file_name=ins_file_name)

        assert ret is None

    # TODO: Re-enable test_partition_unmount_iso_image() once supported in hdlr
    def xtest_partition_unmount_iso_image(self):
        """Test Partition.unmount_iso_image()."""

        # Add a faked partition
        faked_partition = self.add_partition1()

        partition_mgr = self.cpc.partitions
        partition = partition_mgr.find(name=faked_partition.name)

        # Execute the code to be tested.
        ret = partition.unmount_iso_image()

        assert ret is None

    # TODO: Test for Partition.send_os_command()

    # TODO: Test for Partition.wait_for_status()

    # TODO: Test for Partition.increase_crypto_config()

    # TODO: Test for Partition.decrease_crypto_config()

    # TODO: Test for Partition.change_crypto_domain_config()
