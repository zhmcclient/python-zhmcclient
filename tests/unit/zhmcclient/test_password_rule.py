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
Unit tests for _password_rule module.
"""

from __future__ import absolute_import, print_function

import pytest
import re
import copy

from zhmcclient import Client, HTTPError, NotFound, PasswordRule
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestPasswordRule(object):
    """All tests for the PasswordRule and PasswordRuleManager classes."""

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

    def add_password_rule(self, name, type_):
        faked_password_rule = self.faked_console.password_rules.add({
            'element-id': 'oid-{}'.format(name),
            # element-uri will be automatically set
            'parent': '/api/console',
            'class': 'password-rule',
            'name': name,
            'description': 'Password Rule {}'.format(name),
            'type': type_,
        })
        return faked_password_rule

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

    def test_password_rule_manager_repr(self):
        """Test PasswordRuleManager.__repr__()."""

        password_rule_mgr = self.console.password_rules

        # Execute the code to be tested
        repr_str = repr(password_rule_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=password_rule_mgr.__class__.__name__,
                               id=id(password_rule_mgr)),
                        repr_str)

    def test_password_rule_manager_initial_attrs(self):
        """Test initial attributes of PasswordRuleManager."""

        password_rule_mgr = self.console.password_rules

        # Verify all public properties of the manager object
        assert password_rule_mgr.resource_class == PasswordRule
        assert password_rule_mgr.class_name == 'password-rule'
        assert password_rule_mgr.session is self.session
        assert password_rule_mgr.parent is self.console
        assert password_rule_mgr.console is self.console

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
    def test_password_rule_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test PasswordRuleManager.list()."""

        faked_password_rule1 = self.add_password_rule(
            name='a', type_='user-defined')
        faked_password_rule2 = self.add_password_rule(
            name='b', type_='system-defined')
        faked_password_rules = [faked_password_rule1, faked_password_rule2]
        exp_faked_password_rules = [u for u in faked_password_rules
                                    if u.name in exp_names]
        password_rule_mgr = self.console.password_rules

        # Execute the code to be tested
        password_rules = password_rule_mgr.list(filter_args=filter_args,
                                                **full_properties_kwargs)

        assert_resources(password_rules, exp_faked_password_rules, prop_names)

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
             ['element-uri', 'name', 'description'],
             None),
        ]
    )
    def test_password_rule_manager_create(self, input_props, exp_prop_names,
                                          exp_exc):
        """Test PasswordRuleManager.create()."""

        password_rule_mgr = self.console.password_rules

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                password_rule_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            password_rule = password_rule_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(password_rule, PasswordRule)
            password_rule_name = password_rule.name
            exp_password_rule_name = password_rule.properties['name']
            assert password_rule_name == exp_password_rule_name
            password_rule_uri = password_rule.uri
            exp_password_rule_uri = password_rule.properties['element-uri']
            assert password_rule_uri == exp_password_rule_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in password_rule.properties
                if prop_name in input_props:
                    value = password_rule.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_password_rule_repr(self):
        """Test PasswordRule.__repr__()."""

        faked_password_rule1 = self.add_password_rule(
            name='a', type_='user-defined')
        password_rule1 = self.console.password_rules.find(
            name=faked_password_rule1.name)

        # Execute the code to be tested
        repr_str = repr(password_rule1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=password_rule1.__class__.__name__,
                               id=id(password_rule1)),
                        repr_str)

    @pytest.mark.parametrize(
        "input_props, exp_exc", [
            ({'name': 'a',
              'type': 'user-defined'},
             None),
            ({'name': 'b',
              'type': 'system-defined'},
             None),
        ]
    )
    def test_password_rule_delete(self, input_props, exp_exc):
        """Test PasswordRule.delete()."""

        faked_password_rule = self.add_password_rule(
            name=input_props['name'],
            type_=input_props['type'])

        password_rule_mgr = self.console.password_rules
        password_rule = password_rule_mgr.find(name=faked_password_rule.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                password_rule.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the Password Rule still exists
            password_rule_mgr.find(name=faked_password_rule.name)

        else:

            # Execute the code to be tested.
            password_rule.delete()

            # Check that the Password Rule no longer exists
            with pytest.raises(NotFound) as exc_info:
                password_rule_mgr.find(name=faked_password_rule.name)

    def test_password_rule_delete_create_same_name(self):
        """Test PasswordRule.delete() followed by create() with same name."""

        password_rule_name = 'faked_a'

        # Add the Password Rule to be tested
        self.add_password_rule(name=password_rule_name, type_='user-defined')

        # Input properties for a Password Rule with the same name
        sn_password_rule_props = {
            'name': password_rule_name,
            'description': 'Password Rule with same name',
            'type': 'user-defined',
        }

        password_rule_mgr = self.console.password_rules
        password_rule = password_rule_mgr.find(name=password_rule_name)

        # Execute the deletion code to be tested
        password_rule.delete()

        # Check that the Password Rule no longer exists
        with pytest.raises(NotFound):
            password_rule_mgr.find(name=password_rule_name)

        # Execute the creation code to be tested.
        password_rule_mgr.create(sn_password_rule_props)

        # Check that the Password Rule exists again under that name
        sn_password_rule = password_rule_mgr.find(name=password_rule_name)
        description = sn_password_rule.get_property('description')
        assert description == sn_password_rule_props['description']

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New Password Rule description'},
        ]
    )
    def test_password_rule_update_properties(self, input_props):
        """Test PasswordRule.update_properties()."""

        password_rule_name = 'faked_a'

        # Add the Password Rule to be tested
        self.add_password_rule(name=password_rule_name, type_='user-defined')

        password_rule_mgr = self.console.password_rules
        password_rule = password_rule_mgr.find(name=password_rule_name)

        password_rule.pull_full_properties()
        saved_properties = copy.deepcopy(password_rule.properties)

        # Execute the code to be tested
        password_rule.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in password_rule.properties
            prop_value = password_rule.properties[prop_name]
            assert prop_value == exp_prop_value, \
                "Unexpected value for property {!r}".format(prop_name)

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        password_rule.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in password_rule.properties
            prop_value = password_rule.properties[prop_name]
            assert prop_value == exp_prop_value
