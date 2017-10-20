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
Unit tests for _user module.
"""

from __future__ import absolute_import, print_function

import pytest
import re
import copy

from zhmcclient import Client, HTTPError, NotFound, User
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestUser(object):
    """All tests for the User and UserManager classes."""

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

    def add_user_role(self, name, type_):
        faked_user_role = self.faked_console.user_roles.add({
            'object-id': 'oid-{}'.format(name),
            # object-uri will be automatically set
            'parent': '/api/console',
            'class': 'user-role',
            'name': name,
            'description': 'User Role {}'.format(name),
            'type': type_,
        })
        return faked_user_role

    def test_user_manager_repr(self):
        """Test UserManager.__repr__()."""

        user_mgr = self.console.users

        # Execute the code to be tested
        repr_str = repr(user_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=user_mgr.__class__.__name__,
                               id=id(user_mgr)),
                        repr_str)

    def test_user_manager_initial_attrs(self):
        """Test initial attributes of UserManager."""

        user_mgr = self.console.users

        # Verify all public properties of the manager object
        assert user_mgr.resource_class == User
        assert user_mgr.class_name == 'user'
        assert user_mgr.session is self.session
        assert user_mgr.parent is self.console
        assert user_mgr.console is self.console

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(full_properties=False),
             ['object-uri']),
            (dict(full_properties=True),
             ['object-uri', 'name']),
            (dict(),  # test default for full_properties (True)
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
    def test_user_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test UserManager.list()."""

        faked_user1 = self.add_user(name='a', type_='standard')
        faked_user2 = self.add_user(name='b', type_='standard')
        faked_users = [faked_user1, faked_user2]
        exp_faked_users = [u for u in faked_users if u.name in exp_names]
        user_mgr = self.console.users

        # Execute the code to be tested
        users = user_mgr.list(filter_args=filter_args,
                              **full_properties_kwargs)

        assert_resources(users, exp_faked_users, prop_names)

    @pytest.mark.parametrize(
        "input_props, exp_prop_names, exp_exc", [
            ({},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-name-x'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-name-x',
              'type': 'standard'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-name-x',
              'type': 'standard',
              'authentication-type': 'local'},
             ['object-uri', 'name', 'type', 'authentication-type'],
             None),
            ({'name': 'fake-name-x',
              'type': 'standard',
              'authentication-type': 'local',
              'description': 'fake description X'},
             ['object-uri', 'name', 'type', 'authentication-type',
              'description'],
             None),
        ]
    )
    def test_user_manager_create(self, input_props, exp_prop_names, exp_exc):
        """Test UserManager.create()."""

        user_mgr = self.console.users

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            user = user_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(user, User)
            user_name = user.name
            exp_user_name = user.properties['name']
            assert user_name == exp_user_name
            user_uri = user.uri
            exp_user_uri = user.properties['object-uri']
            assert user_uri == exp_user_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in user.properties
                if prop_name in input_props:
                    value = user.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_user_repr(self):
        """Test User.__repr__()."""

        faked_user1 = self.add_user(name='a', type_='standard')
        user1 = self.console.users.find(name=faked_user1.name)

        # Execute the code to be tested
        repr_str = repr(user1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=user1.__class__.__name__,
                               id=id(user1)),
                        repr_str)

    @pytest.mark.parametrize(
        "input_name, input_type, exp_exc", [
            ('a', 'standard', None),
            ('b', 'template', None),
            ('c', 'pattern-based',
             HTTPError({'http-status': 400, 'reason': 312})),
            ('d', 'system-defined', None),
        ]
    )
    def test_user_delete(self, input_name, input_type, exp_exc):
        """Test User.delete()."""

        faked_user = self.add_user(name=input_name, type_=input_type)
        user_mgr = self.console.users
        user = user_mgr.find(name=faked_user.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the user still exists
            user_mgr.find(name=faked_user.name)

        else:

            # Execute the code to be tested.
            user.delete()

            # Check that the user no longer exists
            with pytest.raises(NotFound) as exc_info:
                user_mgr.find(name=faked_user.name)

    def test_user_delete_create_same_name(self):
        """Test User.delete() followed by create() with same name."""

        user_name = 'faked_a'

        # Add the user to be tested
        self.add_user(name=user_name, type_='standard')

        # Input properties for a user with the same name
        sn_user_props = {
            'name': user_name,
            'description': 'User with same name',
            'type': 'standard',
            'authentication-type': 'local',
        }

        user_mgr = self.console.users
        user = user_mgr.find(name=user_name)

        # Execute the deletion code to be tested
        user.delete()

        # Check that the user no longer exists
        with pytest.raises(NotFound):
            user_mgr.find(name=user_name)

        # Execute the creation code to be tested.
        user_mgr.create(sn_user_props)

        # Check that the user exists again under that name
        sn_user = user_mgr.find(name=user_name)
        description = sn_user.get_property('description')
        assert description == sn_user_props['description']

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New user description'},
            {'authentication-type': 'ldap',
             'description': 'New user description'},
        ]
    )
    def test_user_update_properties(self, input_props):
        """Test User.update_properties()."""

        # Add the user to be tested
        faked_user = self.add_user(name='a', type_='standard')

        user_mgr = self.console.users
        user = user_mgr.find(name=faked_user.name)

        user.pull_full_properties()
        saved_props = copy.deepcopy(user.properties)

        # Execute the code to be tested
        user.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_props:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_props[prop_name]
            assert prop_name in user.properties
            prop_value = user.properties[prop_name]
            assert prop_value == exp_prop_value, \
                "Unexpected value for property {!r}".format(prop_name)

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        user.pull_full_properties()
        for prop_name in saved_props:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_props[prop_name]
            assert prop_name in user.properties
            prop_value = user.properties[prop_name]
            assert prop_value == exp_prop_value

    @pytest.mark.parametrize(
        "user_name, user_type, exp_exc", [
            ('a', 'standard', None),
            ('b', 'template', None),
            ('c', 'pattern-based',
             HTTPError({'http-status': 400, 'reason': 314})),
            ('d', 'system-defined',
             HTTPError({'http-status': 400, 'reason': 314})),
        ]
    )
    @pytest.mark.parametrize(
        "role_name, role_type", [
            ('ra', 'user-defined'),
            ('rb', 'system-defined'),
        ]
    )
    def test_user_add_user_role(
            self, role_name, role_type, user_name, user_type, exp_exc):
        """Test User.add_user_role()."""

        faked_user = self.add_user(name=user_name, type_=user_type)
        user_mgr = self.console.users
        user = user_mgr.find(name=faked_user.name)

        faked_user_role = self.add_user_role(name=role_name, type_=role_type)
        user_role_mgr = self.console.user_roles
        user_role = user_role_mgr.find(name=faked_user_role.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user.add_user_role(user_role)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the user does not have that user role
            user.pull_full_properties()
            if 'user-roles' in user.properties:
                user_role_uris = user.properties['user-roles']
                user_role_uri = user_role.uri
                assert user_role_uri not in user_role_uris

        else:

            # Execute the code to be tested.
            ret = user.add_user_role(user_role)

            assert ret is None

            # Check that the user has that user role
            user.pull_full_properties()
            assert 'user-roles' in user.properties
            user_role_uris = user.properties['user-roles']
            user_role_uri = user_role.uri
            assert user_role_uri in user_role_uris

    @pytest.mark.parametrize(
        "user_name, user_type, exp_exc", [
            ('a', 'standard', None),
            ('b', 'template', None),
            ('c', 'pattern-based',
             HTTPError({'http-status': 400, 'reason': 314})),
            ('d', 'system-defined',
             HTTPError({'http-status': 400, 'reason': 314})),
        ]
    )
    @pytest.mark.parametrize(
        "role_name, role_type", [
            ('ra', 'user-defined'),
            ('rb', 'system-defined'),
        ]
    )
    def test_user_remove_user_role(
            self, role_name, role_type, user_name, user_type, exp_exc):
        """Test User.remove_user_role()."""

        faked_user = self.add_user(name=user_name, type_=user_type)
        user_mgr = self.console.users
        user = user_mgr.find(name=faked_user.name)

        faked_user_role = self.add_user_role(name=role_name, type_=role_type)
        user_role_mgr = self.console.user_roles
        user_role = user_role_mgr.find(name=faked_user_role.name)

        # Prepare the user with the initial user role
        if 'user-roles' not in faked_user.properties:
            faked_user.properties['user-roles'] = []
        faked_user.properties['user-roles'].append(faked_user_role.uri)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user.remove_user_role(user_role)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the user still has that user role
            user.pull_full_properties()
            if 'user-roles' in user.properties:
                user_role_uris = user.properties['user-roles']
                user_role_uri = user_role.uri
                assert user_role_uri in user_role_uris

        else:

            # Execute the code to be tested.
            ret = user.remove_user_role(user_role)

            assert ret is None

            # Check that the user no longer has that user role
            user.pull_full_properties()
            assert 'user-roles' in user.properties
            user_role_uris = user.properties['user-roles']
            user_role_uri = user_role.uri
            assert user_role_uri not in user_role_uris
