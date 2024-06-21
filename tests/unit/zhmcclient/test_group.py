# Copyright 2023 IBM Corp. All Rights Reserved.
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
Unit tests for _group module.
"""


import re
import pytest

from zhmcclient import Client, HTTPError, NotFound, Group
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestGroup:
    """All tests for the Group and GroupManager classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Set up a faked session, and add a faked Console without any
        child resources.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

        self.faked_console = self.session.hmc.consoles.add({
            'object-id': None,
            # object-uri will be automatically set
            'parent': None,
            'class': 'console',
            'name': 'fake-console1',
            'description': 'Console #1',
        })
        self.console = self.client.consoles.find(name=self.faked_console.name)

    def add_group(self, name):
        """
        Add a faked group object to the faked Console and return it.
        """
        faked_group = self.faked_console.groups.add({
            'object-id': f'oid-{name}',
            # object-uri will be automatically set
            'parent': None,
            'class': 'group',
            'name': name,
            'description': f'Group {name}',
        })
        return faked_group

    def test_group_manager_repr(self):
        """Test GroupManager.__repr__()."""

        group_mgr = self.console.groups

        # Execute the code to be tested
        repr_str = repr(group_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{group_mgr.__class__.__name__}\s+at\s+'
            rf'0x{id(group_mgr):08x}\s+\(\\n.*',
            repr_str)

    def test_group_manager_initial_attrs(self):
        """Test initial attributes of GroupManager."""

        group_mgr = self.console.groups

        # Verify all public properties of the manager object
        assert group_mgr.resource_class == Group
        assert group_mgr.class_name == 'group'
        assert group_mgr.session is self.session
        assert group_mgr.parent is self.console
        assert group_mgr.console is self.console

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(full_properties=False),
             ['object-uri', 'name']),
            (dict(full_properties=True),
             ['object-uri', 'name', 'description', 'match-info']),
            ({},  # test default for full_properties (False)
             ['object-uri', 'name']),
        ]
    )
    @pytest.mark.parametrize(
        "filter_args, exp_names", [
            (None,
             ['a', 'b']),
            ({},
             ['a', 'b']),
            ({'name': 'a'},
             ['a']),
        ]
    )
    def test_group_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test GroupManager.list()."""

        faked_group1 = self.add_group(name='a')
        faked_group2 = self.add_group(name='b')
        faked_groups = [faked_group1, faked_group2]
        exp_faked_groups = [g for g in faked_groups if g.name in exp_names]
        group_mgr = self.console.groups

        # Execute the code to be tested
        groups = group_mgr.list(filter_args=filter_args,
                                **full_properties_kwargs)

        assert_resources(groups, exp_faked_groups, prop_names)

    @pytest.mark.parametrize(
        "input_props, exp_prop_names, exp_exc", [
            ({},  # props missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X'},  # props missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X',
              'name': 'a'},
             ['object-uri', 'name', 'description'],
             None),
        ]
    )
    def test_group_manager_create(self, input_props, exp_prop_names, exp_exc):
        """Test GroupManager.create()."""

        group_mgr = self.console.groups

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                group_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            group = group_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(group, Group)
            group_name = group.name
            exp_group_name = group.properties['name']
            assert group_name == exp_group_name
            group_uri = group.uri
            exp_group_uri = group.properties['object-uri']
            assert group_uri == exp_group_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in group.properties
                if prop_name in input_props:
                    value = group.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_group_repr(self):
        """Test Group.__repr__()."""

        faked_group1 = self.add_group(name='a')
        group_mgr = self.console.groups
        group1 = group_mgr.find(name=faked_group1.name)

        # Execute the code to be tested
        repr_str = repr(group1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{group1.__class__.__name__}\s+at\s+'
            rf'0x{id(group1):08x}\s+\(\\n.*',
            repr_str)

    @pytest.mark.parametrize(
        "input_props, exp_exc", [
            ({'name': 'a'},
             None),
            ({'name': 'b'},
             None),
        ]
    )
    def test_group_delete(self, input_props, exp_exc):
        """Test Group.delete()."""

        faked_group = self.add_group(name=input_props['name'])

        group_mgr = self.console.groups
        group = group_mgr.find(name=faked_group.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                group.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the Group still exists
            group_mgr.find(name=faked_group.name)

        else:

            # Execute the code to be tested.
            group.delete()

            # Check that the Group no longer exists
            with pytest.raises(NotFound) as exc_info:
                group_mgr.find(name=faked_group.name)

    def test_group_delete_create_same_name(self):
        """Test Group.delete() followed by create() with same name."""

        group_name = 'faked_a'

        # Add the Group to be tested
        self.add_group(name=group_name)

        # Input properties for a Group with the same name
        sn_group_props = {
            'name': group_name,
            'description': 'Group with same name',
        }

        group_mgr = self.console.groups
        group = group_mgr.find(name=group_name)

        # Execute the deletion code to be tested
        group.delete()

        # Check that the Group no longer exists
        with pytest.raises(NotFound):
            group_mgr.find(name=group_name)

        # Execute the creation code to be tested.
        group_mgr.create(sn_group_props)

        # Check that the Group exists again under that name
        sn_group = group_mgr.find(name=group_name)
        description = sn_group.get_property('description')
        assert description == sn_group_props['description']
