# Copyright 2017 IBM Corp. All Rights Reserved.
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
Unit tests for _user_pattern module.
"""

from __future__ import absolute_import, print_function

import pytest
import re
import copy

from zhmcclient import Client, HTTPError, NotFound, UserPattern
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestUserPattern(object):
    """All tests for the UserPattern and UserPatternManager classes."""

    def setup_method(self):
        """
        Set up a faked session, and add a faked Console without any
        child resources.
        """

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

    def add_user_pattern(self, name, pattern, type_, user_template_uri):
        faked_user_pattern = self.faked_console.user_patterns.add({
            'element-id': 'oid-{}'.format(name),
            # element-uri will be automatically set
            'parent': '/api/console',
            'class': 'user-pattern',
            'name': name,
            'description': 'User Pattern {}'.format(name),
            'pattern': pattern,
            'type': type_,
            'retention-time': 0,
            'user-template-uri': user_template_uri,
        })
        return faked_user_pattern

    def add_user(self, name, type_):
        faked_user = self.faked_console.users.add({
            'object-id': 'oid-{}'.format(name),
            # object-uri will be automatically set
            'parent': '/api/console',
            'class': 'user',
            'name': name,
            'description': 'User {}'.format(name),
            'type': type_,
            'authentication-type': 'local',
        })
        return faked_user

    def test_user_pattern_manager_repr(self):
        """Test UserPatternManager.__repr__()."""

        user_pattern_mgr = self.console.user_patterns

        # Execute the code to be tested
        repr_str = repr(user_pattern_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=user_pattern_mgr.__class__.__name__,
                               id=id(user_pattern_mgr)),
                        repr_str)

    def test_user_pattern_manager_initial_attrs(self):
        """Test initial attributes of UserPatternManager."""

        user_pattern_mgr = self.console.user_patterns

        # Verify all public properties of the manager object
        assert user_pattern_mgr.resource_class == UserPattern
        assert user_pattern_mgr.class_name == 'user-pattern'
        assert user_pattern_mgr.session is self.session
        assert user_pattern_mgr.parent is self.console
        assert user_pattern_mgr.console is self.console

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(full_properties=False),
             ['element-uri']),
            (dict(full_properties=True),
             ['element-uri', 'name']),
            (dict(),  # test default for full_properties (True)
             ['element-uri', 'name']),
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
    def test_user_pattern_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test UserPatternManager.list()."""

        faked_user1 = self.add_user(name='a', type_='standard')
        faked_user2 = self.add_user(name='b', type_='standard')

        faked_user_pattern1 = self.add_user_pattern(
            name='a', pattern='a_*', type_='glob-like',
            user_template_uri=faked_user1.uri)
        faked_user_pattern2 = self.add_user_pattern(
            name='b', pattern='b_.*', type_='regular-expression',
            user_template_uri=faked_user2.uri)
        faked_user_patterns = [faked_user_pattern1, faked_user_pattern2]
        exp_faked_user_patterns = [u for u in faked_user_patterns
                                   if u.name in exp_names]
        user_pattern_mgr = self.console.user_patterns

        # Execute the code to be tested
        user_patterns = user_pattern_mgr.list(filter_args=filter_args,
                                              **full_properties_kwargs)

        assert_resources(user_patterns, exp_faked_user_patterns, prop_names)

    @pytest.mark.parametrize(
        "input_props, exp_prop_names, exp_exc", [
            ({},  # props missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X'},  # props missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X',
              'name': 'a',
              'pattern': 'a*'},  # several missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X',
              'name': 'a',
              'pattern': 'a*'},  # several missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X',
              'name': 'a',
              'pattern': 'a*',
              'type': 'glob-like'},  # props missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X',
              'name': 'a',
              'pattern': 'a*',
              'type': 'glob-like',
              'retention-time': 0},  # props missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X',
              'name': 'a',
              'pattern': 'a*',
              'type': 'glob-like',
              'retention-time': 28,
              'user-template-uri': '/api/users/oid-tpl'},
             ['element-uri', 'name', 'description', 'pattern', 'type',
              'retention-time', 'user-template-uri'],
             None),
        ]
    )
    def test_user_pattern_manager_create(self, input_props, exp_prop_names,
                                         exp_exc):
        """Test UserPatternManager.create()."""

        faked_user_template = self.add_user(name='tpl', type_='template')
        assert faked_user_template.uri == '/api/users/oid-tpl'

        user_pattern_mgr = self.console.user_patterns

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user_pattern_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            user_pattern = user_pattern_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(user_pattern, UserPattern)
            user_pattern_name = user_pattern.name
            exp_user_pattern_name = user_pattern.properties['name']
            assert user_pattern_name == exp_user_pattern_name
            user_pattern_uri = user_pattern.uri
            exp_user_pattern_uri = user_pattern.properties['element-uri']
            assert user_pattern_uri == exp_user_pattern_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in user_pattern.properties
                if prop_name in input_props:
                    value = user_pattern.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_user_pattern_repr(self):
        """Test UserPattern.__repr__()."""

        faked_user1 = self.add_user(name='a', type_='standard')
        faked_user_pattern1 = self.add_user_pattern(
            name='a', pattern='a_*', type_='glob-like',
            user_template_uri=faked_user1.uri)
        user_pattern1 = self.console.user_patterns.find(
            name=faked_user_pattern1.name)

        # Execute the code to be tested
        repr_str = repr(user_pattern1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=user_pattern1.__class__.__name__,
                               id=id(user_pattern1)),
                        repr_str)

    @pytest.mark.parametrize(
        "input_props, exp_exc", [
            ({'name': 'a',
              'description': 'fake description X',
              'pattern': 'a*',
              'type': 'glob-like',
              'retention-time': 28,
              'user-template-uri': '/api/users/oid-tpl'},
             None),
        ]
    )
    def test_user_pattern_delete(self, input_props, exp_exc):
        """Test UserPattern.delete()."""

        faked_user_pattern = self.add_user_pattern(
            name=input_props['name'],
            pattern=input_props['pattern'],
            type_=input_props['type'],
            user_template_uri=input_props['user-template-uri'])

        user_pattern_mgr = self.console.user_patterns
        user_pattern = user_pattern_mgr.find(name=faked_user_pattern.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user_pattern.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the user pattern still exists
            user_pattern_mgr.find(name=faked_user_pattern.name)

        else:

            # Execute the code to be tested.
            user_pattern.delete()

            # Check that the user pattern no longer exists
            with pytest.raises(NotFound) as exc_info:
                user_pattern_mgr.find(name=faked_user_pattern.name)

    def test_user_pattern_delete_create_same_name(self):
        """Test UserPattern.delete() followed by create() with same name."""

        user_pattern_name = 'faked_a'

        faked_user1 = self.add_user(name='a', type_='standard')

        # Add the user pattern to be tested
        self.add_user_pattern(
            name=user_pattern_name, pattern='a_*', type_='glob-like',
            user_template_uri=faked_user1.uri)

        # Input properties for a user pattern with the same name
        sn_user_pattern_props = {
            'name': user_pattern_name,
            'description': 'User Pattern with same name',
            'pattern': 'a*',
            'type': 'glob-like',
            'retention-time': 28,
            'user-template-uri': '/api/users/oid-tpl',
        }

        user_pattern_mgr = self.console.user_patterns
        user_pattern = user_pattern_mgr.find(name=user_pattern_name)

        # Execute the deletion code to be tested
        user_pattern.delete()

        # Check that the user pattern no longer exists
        with pytest.raises(NotFound):
            user_pattern_mgr.find(name=user_pattern_name)

        # Execute the creation code to be tested.
        user_pattern_mgr.create(sn_user_pattern_props)

        # Check that the user pattern exists again under that name
        sn_user_pattern = user_pattern_mgr.find(name=user_pattern_name)
        description = sn_user_pattern.get_property('description')
        assert description == sn_user_pattern_props['description']

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New user pattern description'},
        ]
    )
    def test_user_pattern_update_properties(self, input_props):
        """Test UserPattern.update_properties()."""

        user_pattern_name = 'faked_a'

        faked_user1 = self.add_user(name='a', type_='standard')

        # Add the user pattern to be tested
        self.add_user_pattern(
            name=user_pattern_name, pattern='a_*', type_='glob-like',
            user_template_uri=faked_user1.uri)

        user_pattern_mgr = self.console.user_patterns
        user_pattern = user_pattern_mgr.find(name=user_pattern_name)

        user_pattern.pull_full_properties()
        saved_properties = copy.deepcopy(user_pattern.properties)

        # Execute the code to be tested
        user_pattern.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in user_pattern.properties
            prop_value = user_pattern.properties[prop_name]
            assert prop_value == exp_prop_value, \
                "Unexpected value for property {!r}".format(prop_name)

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        user_pattern.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in user_pattern.properties
            prop_value = user_pattern.properties[prop_name]
            assert prop_value == exp_prop_value
