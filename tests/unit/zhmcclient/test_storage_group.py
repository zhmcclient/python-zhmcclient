# Copyright 2018 IBM Corp. All Rights Reserved.
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
Unit tests for _storage_group module.
"""

from __future__ import absolute_import, print_function

import pytest
import re
import copy

from zhmcclient import Client, Cpc, StorageGroup, StorageGroupManager, \
    StorageVolumeManager, VirtualStorageResourceManager, HTTPError, \
    NotFound
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked storage groups:
CPC_OID = 'fake-cpc1-oid'
CPC_URI = '/api/cpcs/%s' % CPC_OID
SG1_OID = 'sg1-oid'
SG1_NAME = 'sg 1'
SG2_OID = 'sg2-oid'
SG2_NAME = 'sg 2'


class TestStorageGroup(object):
    """All tests for the StorageGroup and StorageGroupManager classes."""

    def setup_method(self):
        """
        Set up a faked session, and add a faked CPC in DPM mode without any
        child resources.
        """

        self.session = FakedSession('fake-host', 'fake-hmc', '2.14.1', '1.9')
        self.client = Client(self.session)
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': CPC_OID,
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode, storage mgmt feature enabled)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
            'available-features-list': [
                dict(name='dpm-storage-management', state=True),
            ],
        })
        assert self.faked_cpc.uri == CPC_URI
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')
        self.faked_console = self.session.hmc.consoles.add({
            # object-id is set up automatically
            # object-uri is set up automatically
            # parent will be automatically set
            # class will be automatically set
            'name': 'fake-console-name',
            'description': 'The HMC',
        })
        self.console = self.client.consoles.console

    def add_storage_group1(self):
        """Add storage group 1 (type fcp)."""

        faked_storage_group = self.faked_console.storage_groups.add({
            'object-id': SG1_OID,
            # object-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'cpc-uri': CPC_URI,
            'name': SG1_NAME,
            'description': 'Storage Group #1',
            'type': 'fcp',
            'shared': False,
            'fulfillment-state': 'complete',
            'connectivity': 4,
        })
        return faked_storage_group

    def add_storage_group2(self):
        """Add storage group 2 (type fc)."""

        faked_storage_group = self.faked_console.storage_groups.add({
            'object-id': SG2_OID,
            # object-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'cpc-uri': CPC_URI,
            'name': SG2_NAME,
            'description': 'Storage Group #2',
            'type': 'fc',
            'shared': False,
            'fulfillment-state': 'complete',
            'connectivity': 4,
        })
        return faked_storage_group

    def test_storagegroupmanager_initial_attrs(self):
        """Test initial attributes of StorageGroupManager."""

        storage_group_mgr = self.console.storage_groups

        assert isinstance(storage_group_mgr, StorageGroupManager)

        # Verify all public properties of the manager object
        assert storage_group_mgr.resource_class == StorageGroup
        assert storage_group_mgr.session == self.session
        assert storage_group_mgr.parent == self.console
        assert storage_group_mgr.console == self.console

    # TODO: Test for StorageGroupManager.__repr__()

    testcases_storagegroupmanager_list_full_properties = (
        "full_properties_kwargs, prop_names", [
            (dict(),
             ['object-uri', 'cpc-uri', 'name', 'fulfillment-state', 'type']),
            (dict(full_properties=False),
             ['object-uri', 'cpc-uri', 'name', 'fulfillment-state', 'type']),
            (dict(full_properties=True),
             None),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_storagegroupmanager_list_full_properties
    )
    def test_storagegroupmanager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test StorageGroupManager.list() with full_properties."""

        # Add two faked storage groups
        faked_storage_group1 = self.add_storage_group1()
        faked_storage_group2 = self.add_storage_group2()

        exp_faked_storage_groups = [faked_storage_group1, faked_storage_group2]
        storage_group_mgr = self.console.storage_groups

        # Execute the code to be tested
        storage_groups = storage_group_mgr.list(**full_properties_kwargs)

        assert_resources(storage_groups, exp_faked_storage_groups, prop_names)

    testcases_storagegroupmanager_list_filter_args = (
        "filter_args, exp_names", [
            ({'object-id': SG1_OID},
             [SG1_NAME]),
            ({'object-id': SG2_OID},
             [SG2_NAME]),
            ({'object-id': [SG1_OID, SG2_OID]},
             [SG1_NAME, SG2_NAME]),
            ({'object-id': [SG1_OID, SG1_OID]},
             [SG1_NAME]),
            ({'object-id': SG1_OID + 'foo'},
             []),
            ({'object-id': [SG1_OID, SG2_OID + 'foo']},
             [SG1_NAME]),
            ({'object-id': [SG2_OID + 'foo', SG1_OID]},
             [SG1_NAME]),
            ({'name': SG1_NAME},
             [SG1_NAME]),
            ({'name': SG2_NAME},
             [SG2_NAME]),
            ({'name': [SG1_NAME, SG2_NAME]},
             [SG1_NAME, SG2_NAME]),
            ({'name': SG1_NAME + 'foo'},
             []),
            ({'name': [SG1_NAME, SG2_NAME + 'foo']},
             [SG1_NAME]),
            ({'name': [SG2_NAME + 'foo', SG1_NAME]},
             [SG1_NAME]),
            ({'name': [SG1_NAME, SG1_NAME]},
             [SG1_NAME]),
            ({'name': '.*sg 1'},
             [SG1_NAME]),
            ({'name': 'sg 1.*'},
             [SG1_NAME]),
            ({'name': 'sg .'},
             [SG1_NAME, SG2_NAME]),
            ({'name': '.g 1'},
             [SG1_NAME]),
            ({'name': '.+'},
             [SG1_NAME, SG2_NAME]),
            ({'name': 'sg 1.+'},
             []),
            ({'name': '.+sg 1'},
             []),
            ({'name': SG1_NAME,
              'object-id': SG1_OID},
             [SG1_NAME]),
            ({'name': SG1_NAME,
              'object-id': SG1_OID + 'foo'},
             []),
            ({'name': SG1_NAME + 'foo',
              'object-id': SG1_OID},
             []),
            ({'name': SG1_NAME + 'foo',
              'object-id': SG1_OID + 'foo'},
             []),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_storagegroupmanager_list_filter_args
    )
    def test_storagegroupmanager_list_filter_args(
            self, filter_args, exp_names):
        """Test StorageGroupManager.list() with filter_args."""

        # Add two faked storage_groups
        self.add_storage_group1()
        self.add_storage_group2()

        storage_group_mgr = self.console.storage_groups

        # Execute the code to be tested
        storage_groups = storage_group_mgr.list(filter_args=filter_args)

        assert len(storage_groups) == len(exp_names)
        if exp_names:
            names = [p.properties['name'] for p in storage_groups]
            assert set(names) == set(exp_names)

    testcases_storagegroupmanager_create_no_volumes = (
        "input_props, exp_prop_names, exp_exc", [
            ({},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-sg-x'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-sg-x',
              'cpc-uri': CPC_URI,
              'type': 'fcp'},
             ['object-uri', 'name', 'cpc-uri'],
             None),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_storagegroupmanager_create_no_volumes
    )
    def test_storagegroupmanager_create(
            self, input_props, exp_prop_names, exp_exc):
        """Test StorageGroupManager.create()."""

        # TODO: Add logic and test cases for creating initial storage volumes

        storage_group_mgr = self.console.storage_groups

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                storage_group = storage_group_mgr.create(
                    properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            # Note: the StorageGroup object returned by StorageGroup.create()
            # has the input properties plus 'object-uri'.
            storage_group = storage_group_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(storage_group, StorageGroup)
            storage_group_name = storage_group.name
            exp_storage_group_name = storage_group.properties['name']
            assert storage_group_name == exp_storage_group_name
            storage_group_uri = storage_group.uri
            exp_storage_group_uri = storage_group.properties['object-uri']
            assert storage_group_uri == exp_storage_group_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in storage_group.properties
                if prop_name in input_props:
                    value = storage_group.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_storagegroupmanager_resource_object(self):
        """
        Test StorageGroupManager.resource_object().

        This test exists for historical reasons, and by now is covered by the
        test for BaseManager.resource_object().
        """

        # Add a faked storage_group
        faked_storage_group = self.add_storage_group1()
        storage_group_oid = faked_storage_group.oid

        storage_group_mgr = self.console.storage_groups

        # Execute the code to be tested
        storage_group = storage_group_mgr.resource_object(storage_group_oid)

        storage_group_uri = "/api/storage-groups/" + storage_group_oid

        sv_mgr = storage_group.storage_volumes
        vsr_mgr = storage_group.virtual_storage_resources

        assert isinstance(storage_group, StorageGroup)
        assert isinstance(sv_mgr, StorageVolumeManager)
        assert isinstance(vsr_mgr, VirtualStorageResourceManager)

        sg_cpc = storage_group.cpc
        assert isinstance(sg_cpc, Cpc)
        assert sg_cpc.uri == storage_group.properties['cpc-uri']

        # Note: Properties inherited from BaseResource are tested there,
        # but we test them again:
        assert storage_group.properties['object-uri'] == storage_group_uri
        assert storage_group.properties['object-id'] == storage_group_oid
        assert storage_group.properties['class'] == 'storage-group'
        assert storage_group.properties['parent'] == self.console.uri

    def test_storagegroup_repr(self):
        """Test StorageGroup.__repr__()."""

        # Add a faked storage_group
        faked_storage_group = self.add_storage_group1()

        storage_group_mgr = self.console.storage_groups
        storage_group = storage_group_mgr.find(name=faked_storage_group.name)

        # Execute the code to be tested
        repr_str = repr(storage_group)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=storage_group.__class__.__name__,
                               id=id(storage_group)),
                        repr_str)

    def test_storagegroup_delete_non_associated(self):
        """Test StorageGroup.delete() of non-associated storage group."""

        # Add a faked storage group to be tested and another one
        faked_storage_group = self.add_storage_group1()
        self.add_storage_group2()

        storage_group_mgr = self.console.storage_groups

        storage_group = storage_group_mgr.find(name=faked_storage_group.name)

        # Execute the code to be tested.
        storage_group.delete()

        # Check that the storage group no longer exists
        with pytest.raises(NotFound):
            storage_group_mgr.find(name=faked_storage_group.name)

    def test_storagegroup_delete_create_same_name(self):
        """Test StorageGroup.delete() followed by create() with same name."""

        # Add a faked storage_group to be tested and another one
        faked_storage_group = self.add_storage_group1()
        storage_group_name = faked_storage_group.name
        self.add_storage_group2()

        # Construct the input properties for a third storage_group
        sg3_props = copy.deepcopy(faked_storage_group.properties)
        sg3_props['description'] = 'Third storage_group'

        storage_group_mgr = self.console.storage_groups
        storage_group = storage_group_mgr.find(name=storage_group_name)

        # Execute the deletion code to be tested.
        storage_group.delete()

        # Check that the storage_group no longer exists
        with pytest.raises(NotFound):
            storage_group_mgr.find(name=storage_group_name)

        # Execute the creation code to be tested.
        storage_group_mgr.create(sg3_props)

        # Check that the storage_group exists again under that name
        storage_group3 = storage_group_mgr.find(name=storage_group_name)
        description = storage_group3.get_property('description')
        assert description == 'Third storage_group'

    testcases_storagegroup_update_properties_sgs = (
        "storage_group_name", [
            SG1_NAME,
            SG2_NAME,
        ]
    )

    testcases_storagegroup_update_properties_props = (
        "input_props", [
            {},
            {'description': 'New storage_group description'},
            {'shared': True},
            {'connectivity': 8},
        ]
    )

    @pytest.mark.parametrize(
        *testcases_storagegroup_update_properties_sgs
    )
    @pytest.mark.parametrize(
        *testcases_storagegroup_update_properties_props
    )
    def test_storagegroup_update_properties(
            self, input_props, storage_group_name):
        """Test StorageGroup.update_properties()."""

        # Add faked storage_groups
        self.add_storage_group1()
        self.add_storage_group2()

        storage_group_mgr = self.console.storage_groups
        storage_group = storage_group_mgr.find(name=storage_group_name)

        storage_group.pull_full_properties()
        saved_properties = copy.deepcopy(storage_group.properties)

        # Execute the code to be tested
        storage_group.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in storage_group.properties
            prop_value = storage_group.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        storage_group.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in storage_group.properties
            prop_value = storage_group.properties[prop_name]
            assert prop_value == exp_prop_value

    def test_storagegroup_update_name(self):
        """
        Test StorageGroup.update_properties() with 'name' property.
        """

        # Add a faked storage_group
        faked_storage_group = self.add_storage_group1()
        storage_group_name = faked_storage_group.name

        storage_group_mgr = self.console.storage_groups
        storage_group = storage_group_mgr.find(name=storage_group_name)

        new_storage_group_name = "new-" + storage_group_name

        # Execute the code to be tested
        storage_group.update_properties(
            properties={'name': new_storage_group_name})

        # Verify that the resource is no longer found by its old name, using
        # list() (this does not use the name-to-URI cache).
        storage_groups_list = storage_group_mgr.list(
            filter_args=dict(name=storage_group_name))
        assert len(storage_groups_list) == 0

        # Verify that the resource is no longer found by its old name, using
        # find() (this uses the name-to-URI cache).
        with pytest.raises(NotFound):
            storage_group_mgr.find(name=storage_group_name)

        # Verify that the resource object already reflects the update, even
        # though it has not been refreshed yet.
        assert storage_group.properties['name'] == new_storage_group_name

        # Refresh the resource object and verify that it still reflects the
        # update.
        storage_group.pull_full_properties()
        assert storage_group.properties['name'] == new_storage_group_name

        # Verify that the resource can be found by its new name, using find()
        new_storage_group_find = storage_group_mgr.find(
            name=new_storage_group_name)
        assert new_storage_group_find.properties['name'] == \
            new_storage_group_name

        # Verify that the resource can be found by its new name, using list()
        new_storage_groups_list = storage_group_mgr.list(
            filter_args=dict(name=new_storage_group_name))
        assert len(new_storage_groups_list) == 1
        new_storage_group_list = new_storage_groups_list[0]
        assert new_storage_group_list.properties['name'] == \
            new_storage_group_name

    # TODO: Adjust to invoke a SG method
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
    def xtest_storagegroup_start(self, initial_status, exp_exc):
        """Test StorageGroup.start()."""

        # Add a faked storage_group
        faked_storage_group = self.add_storage_group1()

        # Set the initial status of the faked storage_group
        faked_storage_group.properties['status'] = initial_status

        storage_group_mgr = self.console.storage_groups
        storage_group = storage_group_mgr.find(name=faked_storage_group.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                storage_group.start()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            ret = storage_group.start()

            assert ret == {}

            storage_group.pull_full_properties()
            status = storage_group.get_property('status')
            assert status == 'active'
