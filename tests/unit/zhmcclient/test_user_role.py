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
Unit tests for _user_role module.
"""

from __future__ import absolute_import, print_function

import pytest
import re
import copy
import six

from zhmcclient import Client, HTTPError, NotFound, BaseResource, UserRole
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestUserRole(object):
    """All tests for the UserRole and UserRoleManager classes."""

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

    def test_user_role_manager_repr(self):
        """Test UserRoleManager.__repr__()."""

        user_role_mgr = self.console.user_roles

        # Execute the code to be tested
        repr_str = repr(user_role_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=user_role_mgr.__class__.__name__,
                               id=id(user_role_mgr)),
                        repr_str)

    def test_user_role_manager_initial_attrs(self):
        """Test initial attributes of UserRoleManager."""

        user_role_mgr = self.console.user_roles

        # Verify all public properties of the manager object
        assert user_role_mgr.resource_class == UserRole
        assert user_role_mgr.class_name == 'user-role'
        assert user_role_mgr.session is self.session
        assert user_role_mgr.parent is self.console
        assert user_role_mgr.console is self.console

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
    def test_user_role_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test UserRoleManager.list()."""

        faked_user_role1 = self.add_user_role(name='a', type_='user-defined')
        faked_user_role2 = self.add_user_role(name='b', type_='user-defined')
        faked_user_roles = [faked_user_role1, faked_user_role2]
        exp_faked_user_roles = [u for u in faked_user_roles
                                if u.name in exp_names]
        user_role_mgr = self.console.user_roles

        # Execute the code to be tested
        user_roles = user_role_mgr.list(filter_args=filter_args,
                                        **full_properties_kwargs)

        assert_resources(user_roles, exp_faked_user_roles, prop_names)

    @pytest.mark.parametrize(
        "input_props, exp_prop_names, exp_exc", [
            ({},  # name missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X'},  # name missing
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-name-x',
              'type': 'user-defined'},  # type not allowed
             None,
             HTTPError({'http-status': 400, 'reason': 6})),
            ({'name': 'fake-name-x',
              'type': 'system-defined'},  # type not allowed
             None,
             HTTPError({'http-status': 400, 'reason': 6})),
            ({'name': 'fake-name-x'},
             ['object-uri', 'name'],
             None),
            ({'name': 'fake-name-x',
              'description': 'fake description X'},
             ['object-uri', 'name', 'description'],
             None),
        ]
    )
    def test_user_role_manager_create(self, input_props, exp_prop_names,
                                      exp_exc):
        """Test UserRoleManager.create()."""

        user_role_mgr = self.console.user_roles

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user_role_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            user_role = user_role_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(user_role, UserRole)
            user_role_name = user_role.name
            exp_user_role_name = user_role.properties['name']
            assert user_role_name == exp_user_role_name
            user_role_uri = user_role.uri
            exp_user_role_uri = user_role.properties['object-uri']
            assert user_role_uri == exp_user_role_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in user_role.properties
                if prop_name in input_props:
                    value = user_role.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_user_role_repr(self):
        """Test UserRole.__repr__()."""

        faked_user_role1 = self.add_user_role(name='a', type_='user-defined')
        user_role1 = self.console.user_roles.find(name=faked_user_role1.name)

        # Execute the code to be tested
        repr_str = repr(user_role1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=user_role1.__class__.__name__,
                               id=id(user_role1)),
                        repr_str)

    @pytest.mark.parametrize(
        "input_name, input_type, exp_exc", [
            ('a', 'user-defined', None),
            # ('b', 'system-defined',
            #  HTTPError({'http-status': 400, 'reason': 312})),
            # TODO: Re-enable once rejection for system-defined roles supported
        ]
    )
    def test_user_role_delete(self, input_name, input_type, exp_exc):
        """Test UserRole.delete()."""

        faked_user_role = self.add_user_role(name=input_name, type_=input_type)
        user_role_mgr = self.console.user_roles
        user_role = user_role_mgr.find(name=faked_user_role.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user_role.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the user role still exists
            user_role_mgr.find(name=faked_user_role.name)

        else:

            # Execute the code to be tested.
            user_role.delete()

            # Check that the user role no longer exists
            with pytest.raises(NotFound) as exc_info:
                user_role_mgr.find(name=faked_user_role.name)

    def test_user_role_delete_create_same_name(self):
        """Test UserRole.delete() followed by create() with same name."""

        user_role_name = 'faked_a'

        # Add the user role to be tested
        self.add_user_role(name=user_role_name, type_='user-defined')

        # Input properties for a user role with the same name
        sn_user_role_props = {
            'name': user_role_name,
            'description': 'User Role with same name',
        }

        user_role_mgr = self.console.user_roles
        user_role = user_role_mgr.find(name=user_role_name)

        # Execute the deletion code to be tested
        user_role.delete()

        # Check that the user role no longer exists
        with pytest.raises(NotFound):
            user_role_mgr.find(name=user_role_name)

        # Execute the creation code to be tested.
        user_role_mgr.create(sn_user_role_props)

        # Check that the user role exists again under that name
        sn_user_role = user_role_mgr.find(name=user_role_name)
        description = sn_user_role.get_property('description')
        assert description == sn_user_role_props['description']

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New user role description'},
        ]
    )
    def test_user_role_update_properties(self, input_props):
        """Test UserRole.update_properties()."""

        # Add the user role to be tested
        faked_user_role = self.add_user_role(name='a', type_='user-defined')

        user_role_mgr = self.console.user_roles
        user_role = user_role_mgr.find(name=faked_user_role.name)

        user_role.pull_full_properties()
        saved_properties = copy.deepcopy(user_role.properties)

        # Execute the code to be tested
        user_role.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in user_role.properties
            prop_value = user_role.properties[prop_name]
            assert prop_value == exp_prop_value, \
                "Unexpected value for property {!r}".format(prop_name)

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        user_role.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in user_role.properties
            prop_value = user_role.properties[prop_name]
            assert prop_value == exp_prop_value

    @pytest.mark.parametrize(
        "role_name, role_type, exp_exc", [
            ('ra', 'user-defined', None),
            ('rb', 'system-defined',
             HTTPError({'http-status': 400, 'reason': 314})),
        ]
    )
    @pytest.mark.parametrize(
        "perm_args", [
            {'permitted_object': 'cpc',
             'include_members': True,
             'view_only': False},
        ]
    )
    def test_user_role_add_permission(
            self, perm_args, role_name, role_type, exp_exc):
        """Test UserRole.add_permission()."""

        faked_user_role = self.add_user_role(name=role_name, type_=role_type)
        user_role_mgr = self.console.user_roles
        user_role = user_role_mgr.find(name=faked_user_role.name)

        permitted_object = perm_args['permitted_object']
        if isinstance(permitted_object, BaseResource):
            perm_obj = permitted_object.uri
            perm_type = 'object'
        else:
            assert isinstance(permitted_object, six.string_types)
            perm_obj = permitted_object
            perm_type = 'object-class'
        permission_parms = {
            'permitted-object': perm_obj,
            'permitted-object-type': perm_type,
            'include-members': perm_args['include_members'],
            'view-only-mode': perm_args['view_only'],
        }

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user_role.add_permission(**perm_args)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the user role still does not have that permission
            user_role.pull_full_properties()
            if 'permissions' in user_role.properties:
                permissions = user_role.properties['permissions']
                assert permission_parms not in permissions

        else:

            # Execute the code to be tested.
            ret = user_role.add_permission(**perm_args)

            assert ret is None

            # Check that the user role now has that permission
            user_role.pull_full_properties()
            permissions = user_role.properties['permissions']
            assert permission_parms in permissions

    @pytest.mark.parametrize(
        "role_name, role_type, exp_exc", [
            ('ra', 'user-defined', None),
            ('rb', 'system-defined',
             HTTPError({'http-status': 400, 'reason': 314})),
        ]
    )
    @pytest.mark.parametrize(
        "perm_args", [
            {'permitted_object': 'cpc',
             'include_members': True,
             'view_only': False},
        ]
    )
    def test_user_role_remove_permission(
            self, perm_args, role_name, role_type, exp_exc):
        """Test UserRole.remove_permission()."""

        faked_user_role = self.add_user_role(name=role_name, type_=role_type)
        user_role_mgr = self.console.user_roles
        user_role = user_role_mgr.find(name=faked_user_role.name)

        permitted_object = perm_args['permitted_object']
        if isinstance(permitted_object, BaseResource):
            perm_obj = permitted_object.uri
            perm_type = 'object'
        else:
            assert isinstance(permitted_object, six.string_types)
            perm_obj = permitted_object
            perm_type = 'object-class'
        permission_parms = {
            'permitted-object': perm_obj,
            'permitted-object-type': perm_type,
            'include-members': perm_args['include_members'],
            'view-only-mode': perm_args['view_only'],
        }

        # Prepare the user role with the initial permission
        if 'permissions' not in faked_user_role.properties:
            faked_user_role.properties['permissions'] = []
        faked_user_role.properties['permissions'].append(permission_parms)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                user_role.remove_permission(**perm_args)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the user role still has that permission
            user_role.pull_full_properties()
            permissions = user_role.properties['permissions']
            assert permission_parms in permissions

        else:

            # Execute the code to be tested.
            ret = user_role.remove_permission(**perm_args)

            assert ret is None

            # Check that the user role no longer has that permission
            user_role.pull_full_properties()
            if 'permissions' in user_role.properties:
                permissions = user_role.properties['permissions']
                assert permission_parms not in permissions
