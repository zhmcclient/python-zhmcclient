# Copyright 2021 IBM Corp. All Rights Reserved.
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
Unit tests for _capacity_group module.
"""


import re
import copy
import pytest

from zhmcclient import Client, CapacityGroup, CapacityGroupManager, \
    HTTPError, NotFound
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked capacity groups:
CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'
CG1_OID = 'cg1-oid'
CG1_NAME = 'cg 1'
CG1_SHORT_NAME = 'CG1'
CG2_OID = 'cg2-oid'
CG2_NAME = 'cg 2'
CG2_SHORT_NAME = 'CG2'


class TestCapacityGroup:
    """All tests for the CapacityGroup and CapacityGroupManager classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Set up a faked session, and add a faked CPC in DPM mode without any
        child resources.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.14.1', '1.9')
        self.client = Client(self.session)
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': CPC_OID,
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

    def add_capacity_group1(self):
        """Add capacity group 1"""

        faked_capacity_group = self.faked_cpc.capacity_groups.add({
            'element-id': CG1_OID,
            # element-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'name': CG1_NAME,
            'short-name': CG1_SHORT_NAME,
            'description': 'Capacity Group #1',
            'capping-enabled': True,
            'absolute-general-purpose-proc-cap': 0.0,
            'absolute-ifl-proc-cap': 100.0,
        })
        return faked_capacity_group

    def add_capacity_group2(self):
        """Add capacity group 2"""

        faked_capacity_group = self.faked_cpc.capacity_groups.add({
            'element-id': CG2_OID,
            # element-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'name': CG2_NAME,
            'short-name': CG2_SHORT_NAME,
            'description': 'Capacity Group #2',
            'capping-enabled': True,
            'absolute-general-purpose-proc-cap': 0.0,
            'absolute-ifl-proc-cap': 100.0,
        })
        return faked_capacity_group

    def add_partition1(self):
        """Add partition 1 (shared processor mode)"""

        faked_partition = self.faked_cpc.partitions.add({
            'object-id': 'fake-part1-oid',
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': 'fake-part1-name',
            'description': 'Partition #1 (shared)',
            'status': 'active',
            'processor-mode': 'shared',
            'initial-memory': 1024,
            'maximum-memory': 2048,
        })
        return faked_partition

    def add_partition2(self):
        """Add partition 2 (dedicated processor mode)"""

        faked_partition = self.faked_cpc.partitions.add({
            'object-id': 'fake-part2-oid',
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': 'fake-part2-name',
            'description': 'Partition #2 (dedicated)',
            'status': 'active',
            'processor-mode': 'dedicated',
            'initial-memory': 1024,
            'maximum-memory': 2048,
        })
        return faked_partition

    def test_cgm_initial_attrs(self):
        """Test initial attributes of CapacityGroupManager."""

        capacity_group_mgr = self.cpc.capacity_groups

        assert isinstance(capacity_group_mgr, CapacityGroupManager)

        # Verify all public properties of the manager object
        assert capacity_group_mgr.resource_class == CapacityGroup
        assert capacity_group_mgr.session == self.session
        assert capacity_group_mgr.parent == self.cpc

    # TODO: Test for CapacityGroupManager.__repr__()

    testcases_cgm_list_full_properties = (
        "full_properties_kwargs, prop_names", [
            ({},
             ['element-uri', 'name']),
            (dict(full_properties=False),
             ['element-uri', 'name']),
            (dict(full_properties=True),
             None),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_cgm_list_full_properties
    )
    def test_cgm_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test CapacityGroupManager.list() with full_properties."""

        # Add two faked capacity groups
        faked_capacity_group1 = self.add_capacity_group1()
        faked_capacity_group2 = self.add_capacity_group2()

        exp_faked_capacity_groups = [faked_capacity_group1,
                                     faked_capacity_group2]
        capacity_group_mgr = self.cpc.capacity_groups

        # Execute the code to be tested
        capacity_groups = capacity_group_mgr.list(**full_properties_kwargs)

        assert_resources(capacity_groups, exp_faked_capacity_groups, prop_names)

    testcases_cgm_list_filter_args = (
        "filter_args, exp_names", [
            ({'element-id': CG1_OID},
             [CG1_NAME]),
            ({'element-id': CG2_OID},
             [CG2_NAME]),
            ({'element-id': [CG1_OID, CG2_OID]},
             [CG1_NAME, CG2_NAME]),
            ({'element-id': [CG1_OID, CG1_OID]},
             [CG1_NAME]),
            ({'element-id': CG1_OID + 'foo'},
             []),
            ({'element-id': [CG1_OID, CG2_OID + 'foo']},
             [CG1_NAME]),
            ({'element-id': [CG2_OID + 'foo', CG1_OID]},
             [CG1_NAME]),
            ({'name': CG1_NAME},
             [CG1_NAME]),
            ({'name': CG2_NAME},
             [CG2_NAME]),
            ({'name': [CG1_NAME, CG2_NAME]},
             [CG1_NAME, CG2_NAME]),
            ({'name': CG1_NAME + 'foo'},
             []),
            ({'name': [CG1_NAME, CG2_NAME + 'foo']},
             [CG1_NAME]),
            ({'name': [CG2_NAME + 'foo', CG1_NAME]},
             [CG1_NAME]),
            ({'name': [CG1_NAME, CG1_NAME]},
             [CG1_NAME]),
            ({'name': '.*cg 1'},
             [CG1_NAME]),
            ({'name': 'cg 1.*'},
             [CG1_NAME]),
            ({'name': 'cg .'},
             [CG1_NAME, CG2_NAME]),
            ({'name': '.g 1'},
             [CG1_NAME]),
            ({'name': '.+'},
             [CG1_NAME, CG2_NAME]),
            ({'name': 'cg 1.+'},
             []),
            ({'name': '.+cg 1'},
             []),
            ({'name': CG1_NAME,
              'element-id': CG1_OID},
             [CG1_NAME]),
            ({'name': CG1_NAME,
              'element-id': CG1_OID + 'foo'},
             []),
            ({'name': CG1_NAME + 'foo',
              'element-id': CG1_OID},
             []),
            ({'name': CG1_NAME + 'foo',
              'element-id': CG1_OID + 'foo'},
             []),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_cgm_list_filter_args
    )
    def test_cgm_list_filter_args(
            self, filter_args, exp_names):
        """Test CapacityGroupManager.list() with filter_args."""

        # Add two faked capacity_groups
        self.add_capacity_group1()
        self.add_capacity_group2()

        capacity_group_mgr = self.cpc.capacity_groups

        # Execute the code to be tested
        capacity_groups = capacity_group_mgr.list(filter_args=filter_args)

        assert len(capacity_groups) == len(exp_names)
        if exp_names:
            names = [p.properties['name'] for p in capacity_groups]
            assert set(names) == set(exp_names)

    testcases_cgm_create = (
        "input_props, exp_prop_names, exp_exc", [
            ({'name': 'fake-cg-x',
              'capping-enabled': True,
              'absolute-ifl-proc-cap': 50.0},
             ['element-uri', 'name', 'capping-enabled',
              'absolute-ifl-proc-cap'],
             None),
        ]
    )

    @pytest.mark.parametrize(
        *testcases_cgm_create
    )
    def test_cgm_create(
            self, input_props, exp_prop_names, exp_exc):
        """Test CapacityGroupManager.create()."""

        capacity_group_mgr = self.cpc.capacity_groups

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                capacity_group = capacity_group_mgr.create(
                    properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            # Note: the CapacityGroup object returned by CapacityGroup.create()
            # has the input properties plus 'element-uri'.
            capacity_group = capacity_group_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(capacity_group, CapacityGroup)
            capacity_group_name = capacity_group.name
            exp_capacity_group_name = capacity_group.properties['name']
            assert capacity_group_name == exp_capacity_group_name
            capacity_group_uri = capacity_group.uri
            exp_capacity_group_uri = capacity_group.properties['element-uri']
            assert capacity_group_uri == exp_capacity_group_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in capacity_group.properties
                if prop_name in input_props:
                    value = capacity_group.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_cg_repr(self):
        """Test CapacityGroup.__repr__()."""

        # Add a faked capacity_group
        faked_capacity_group = self.add_capacity_group1()

        capacity_group_mgr = self.cpc.capacity_groups
        capacity_group = capacity_group_mgr.find(name=faked_capacity_group.name)

        # Execute the code to be tested
        repr_str = repr(capacity_group)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{capacity_group.__class__.__name__}\s+at\s+'
            rf'0x{id(capacity_group):08x}\s+\(\\n.*',
            repr_str)

    def test_cg_delete_empty(self):
        """Test CapacityGroup.delete() of empty capacity group."""

        # Add a faked capacity group to be tested and another one
        faked_capacity_group = self.add_capacity_group1()
        self.add_capacity_group2()

        capacity_group_mgr = self.cpc.capacity_groups

        capacity_group = capacity_group_mgr.find(name=faked_capacity_group.name)

        # Execute the code to be tested.
        capacity_group.delete()

        # Check that the capacity group no longer exists
        with pytest.raises(NotFound):
            capacity_group_mgr.find(name=faked_capacity_group.name)

    def test_cg_delete_non_empty(self):
        """Test CapacityGroup.delete() of non-empty capacity group."""

        # Add a faked capacity group to be tested and another one
        faked_capacity_group = self.add_capacity_group1()
        self.add_capacity_group2()

        # Add a faked partition
        partition1 = self.add_partition1()

        capacity_group_mgr = self.cpc.capacity_groups

        capacity_group = capacity_group_mgr.find(name=faked_capacity_group.name)

        # Add the partition to the capacity group
        capacity_group.add_partition(partition1)

        with pytest.raises(HTTPError):

            # Execute the code to be tested.
            capacity_group.delete()

    def test_cg_delete_create_same(self):
        """Test CapacityGroup.delete() followed by create() with same name."""

        # Add a faked capacity_group to be tested and another one
        faked_capacity_group = self.add_capacity_group1()
        capacity_group_name = faked_capacity_group.name
        self.add_capacity_group2()

        # Construct the input properties for a third capacity_group
        cg3_props = copy.deepcopy(faked_capacity_group.properties)
        cg3_props['description'] = 'Third capacity_group'

        capacity_group_mgr = self.cpc.capacity_groups
        capacity_group = capacity_group_mgr.find(name=capacity_group_name)

        # Execute the deletion code to be tested.
        capacity_group.delete()

        # Check that the capacity_group no longer exists
        with pytest.raises(NotFound):
            capacity_group_mgr.find(name=capacity_group_name)

        # Execute the creation code to be tested.
        capacity_group_mgr.create(cg3_props)

        # Check that the capacity_group exists again under that name
        capacity_group3 = capacity_group_mgr.find(name=capacity_group_name)
        description = capacity_group3.get_property('description')
        assert description == 'Third capacity_group'

    testcases_cg_update_properties_names = (
        "capacity_group_name", [
            CG1_NAME,
            CG2_NAME,
        ]
    )

    testcases_cg_update_properties_props = (
        "input_props", [
            {},
            {'description': 'New capacity_group description'},
            {'shared': True},
            {'connectivity': 8},
        ]
    )

    @pytest.mark.parametrize(
        *testcases_cg_update_properties_names
    )
    @pytest.mark.parametrize(
        *testcases_cg_update_properties_props
    )
    def test_cg_update_properties(
            self, input_props, capacity_group_name):
        """Test CapacityGroup.update_properties()."""

        # Add faked capacity_groups
        self.add_capacity_group1()
        self.add_capacity_group2()

        capacity_group_mgr = self.cpc.capacity_groups
        capacity_group = capacity_group_mgr.find(name=capacity_group_name)

        capacity_group.pull_full_properties()
        saved_properties = copy.deepcopy(capacity_group.properties)

        # Execute the code to be tested
        capacity_group.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in capacity_group.properties
            prop_value = capacity_group.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        capacity_group.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in capacity_group.properties
            prop_value = capacity_group.properties[prop_name]
            assert prop_value == exp_prop_value

    def test_cg_update_name(self):
        """
        Test CapacityGroup.update_properties() with 'name' property.
        """

        # Add a faked capacity_group
        faked_capacity_group = self.add_capacity_group1()
        capacity_group_name = faked_capacity_group.name

        capacity_group_mgr = self.cpc.capacity_groups
        capacity_group = capacity_group_mgr.find(name=capacity_group_name)

        new_capacity_group_name = "new-" + capacity_group_name

        # Execute the code to be tested
        capacity_group.update_properties(
            properties={'name': new_capacity_group_name})

        # Verify that the resource is no longer found by its old name, using
        # list() (this does not use the name-to-URI cache).
        capacity_groups_list = capacity_group_mgr.list(
            filter_args=dict(name=capacity_group_name))
        assert len(capacity_groups_list) == 0

        # Verify that the resource is no longer found by its old name, using
        # find() (this uses the name-to-URI cache).
        with pytest.raises(NotFound):
            capacity_group_mgr.find(name=capacity_group_name)

        # Verify that the resource object already reflects the update, even
        # though it has not been refreshed yet.
        assert capacity_group.properties['name'] == new_capacity_group_name

        # Refresh the resource object and verify that it still reflects the
        # update.
        capacity_group.pull_full_properties()
        assert capacity_group.properties['name'] == new_capacity_group_name

        # Verify that the resource can be found by its new name, using find()
        new_capacity_group_find = capacity_group_mgr.find(
            name=new_capacity_group_name)
        assert new_capacity_group_find.properties['name'] == \
            new_capacity_group_name

        # Verify that the resource can be found by its new name, using list()
        new_capacity_groups_list = capacity_group_mgr.list(
            filter_args=dict(name=new_capacity_group_name))
        assert len(new_capacity_groups_list) == 1
        new_capacity_group_list = new_capacity_groups_list[0]
        assert new_capacity_group_list.properties['name'] == \
            new_capacity_group_name

    def test_cg_add_partition_empty(self):
        """Test CapacityGroup.add_partition() into empty capacity group."""

        # Add faked capacity_groups
        faked_cg1 = self.add_capacity_group1()
        self.add_capacity_group2()

        # Add faked partitions
        faked_part1 = self.add_partition1()

        cg1 = self.cpc.capacity_groups.find(name=faked_cg1.name)
        part1 = self.cpc.partitions.find(name=faked_part1.name)

        # Execute the code to be tested
        cg1.add_partition(part1)

        cg1.pull_full_properties()
        assert cg1.properties['partition-uris'] == [part1.uri]

    def test_cg_add_partition_same(self):
        """Test CapacityGroup.add_partition() into capacity group that
        contains the partition already."""

        # Add faked capacity_groups
        faked_cg1 = self.add_capacity_group1()
        self.add_capacity_group2()

        # Add faked partitions
        faked_part1 = self.add_partition1()

        cg1 = self.cpc.capacity_groups.find(name=faked_cg1.name)
        part1 = self.cpc.partitions.find(name=faked_part1.name)
        cg1.add_partition(part1)

        with pytest.raises(HTTPError) as exc_info:

            # Execute the code to be tested
            cg1.add_partition(part1)

        exc = exc_info.value
        assert exc.http_status == 409
        assert exc.reason == 130

    def test_cg_add_partition_other(self):
        """Test CapacityGroup.add_partition() with partition that is already
        in another capacity group."""

        # Add faked capacity_groups
        faked_cg1 = self.add_capacity_group1()
        faked_cg2 = self.add_capacity_group2()

        # Add faked partitions
        faked_part1 = self.add_partition1()

        cg1 = self.cpc.capacity_groups.find(name=faked_cg1.name)
        cg2 = self.cpc.capacity_groups.find(name=faked_cg2.name)
        part1 = self.cpc.partitions.find(name=faked_part1.name)
        cg2.add_partition(part1)

        with pytest.raises(HTTPError) as exc_info:

            # Execute the code to be tested
            cg1.add_partition(part1)

        exc = exc_info.value
        assert exc.http_status == 409
        assert exc.reason == 120

    def test_cg_add_partition_dedicated(self):
        """Test CapacityGroup.add_partition() with partition that has dedicated
        processor mode."""

        # Add faked capacity_groups
        faked_cg1 = self.add_capacity_group1()
        self.add_capacity_group2()

        # Add faked partitions
        faked_part2 = self.add_partition2()

        cg1 = self.cpc.capacity_groups.find(name=faked_cg1.name)
        part2 = self.cpc.partitions.find(name=faked_part2.name)

        with pytest.raises(HTTPError) as exc_info:

            # Execute the code to be tested
            cg1.add_partition(part2)

        exc = exc_info.value
        assert exc.http_status == 409
        assert exc.reason == 170

    def test_cg_remove_partition_success(self):
        """Test CapacityGroup.remove_partition(), simple success case."""

        # Add faked capacity_groups
        faked_cg1 = self.add_capacity_group1()
        self.add_capacity_group2()

        # Add faked partitions
        faked_part1 = self.add_partition1()

        cg1 = self.cpc.capacity_groups.find(name=faked_cg1.name)
        part1 = self.cpc.partitions.find(name=faked_part1.name)
        cg1.add_partition(part1)

        # Execute the code to be tested
        cg1.remove_partition(part1)

        cg1.pull_full_properties()
        assert cg1.properties['partition-uris'] == []

    def test_cg_remove_partition_empty(self):
        """Test CapacityGroup.remove_partition(), existing partition removal
        from empty capacity group."""

        # Add faked capacity_groups
        faked_cg1 = self.add_capacity_group1()
        self.add_capacity_group2()

        # Add faked partitions
        faked_part1 = self.add_partition1()

        cg1 = self.cpc.capacity_groups.find(name=faked_cg1.name)
        part1 = self.cpc.partitions.find(name=faked_part1.name)

        with pytest.raises(HTTPError) as exc_info:

            # Execute the code to be tested
            cg1.remove_partition(part1)

        exc = exc_info.value
        assert exc.http_status == 409
        assert exc.reason == 140
