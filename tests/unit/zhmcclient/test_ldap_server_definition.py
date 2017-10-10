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
Unit tests for _ldap_srv_def module.
"""

from __future__ import absolute_import, print_function

import pytest
import re
import copy

from zhmcclient import Client, HTTPError, NotFound, LdapServerDefinition
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestLdapServerDefinition(object):
    """All tests for the LdapServerDefinition and LdapServerDefinitionManager
    classes."""

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

    def add_ldap_srv_def(self, name):
        faked_ldap_srv_def = self.faked_console.ldap_server_definitions.add({
            'element-id': 'oid-{}'.format(name),
            # element-uri will be automatically set
            'parent': '/api/console',
            'class': 'ldap-server-definition',
            'name': name,
            'description': 'LDAP Server Definition {}'.format(name),
            'primary-hostname-ipaddr': 'host-{}'.format(name),
        })
        return faked_ldap_srv_def

    def test_ldap_srv_def_manager_repr(self):
        """Test LdapServerDefinitionManager.__repr__()."""

        ldap_srv_def_mgr = self.console.ldap_server_definitions

        # Execute the code to be tested
        repr_str = repr(ldap_srv_def_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=ldap_srv_def_mgr.__class__.__name__,
                               id=id(ldap_srv_def_mgr)),
                        repr_str)

    def test_ldap_srv_def_manager_initial_attrs(self):
        """Test initial attributes of LdapServerDefinitionManager."""

        ldap_srv_def_mgr = self.console.ldap_server_definitions

        # Verify all public properties of the manager object
        assert ldap_srv_def_mgr.resource_class == LdapServerDefinition
        assert ldap_srv_def_mgr.class_name == 'ldap-server-definition'
        assert ldap_srv_def_mgr.session is self.session
        assert ldap_srv_def_mgr.parent is self.console
        assert ldap_srv_def_mgr.console is self.console

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
    def test_ldap_srv_def_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test LdapServerDefinitionManager.list()."""

        faked_ldap_srv_def1 = self.add_ldap_srv_def(name='a')
        faked_ldap_srv_def2 = self.add_ldap_srv_def(name='b')
        faked_ldap_srv_defs = [faked_ldap_srv_def1, faked_ldap_srv_def2]
        exp_faked_ldap_srv_defs = [u for u in faked_ldap_srv_defs
                                   if u.name in exp_names]
        ldap_srv_def_mgr = self.console.ldap_server_definitions

        # Execute the code to be tested
        ldap_srv_defs = ldap_srv_def_mgr.list(filter_args=filter_args,
                                              **full_properties_kwargs)

        assert_resources(ldap_srv_defs, exp_faked_ldap_srv_defs, prop_names)

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
    def test_ldap_srv_def_manager_create(
            self, input_props, exp_prop_names, exp_exc):
        """Test LdapServerDefinitionManager.create()."""

        ldap_srv_def_mgr = self.console.ldap_server_definitions

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                ldap_srv_def_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            ldap_srv_def = ldap_srv_def_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(ldap_srv_def, LdapServerDefinition)
            ldap_srv_def_name = ldap_srv_def.name
            exp_ldap_srv_def_name = ldap_srv_def.properties['name']
            assert ldap_srv_def_name == exp_ldap_srv_def_name
            ldap_srv_def_uri = ldap_srv_def.uri
            exp_ldap_srv_def_uri = ldap_srv_def.properties['element-uri']
            assert ldap_srv_def_uri == exp_ldap_srv_def_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in ldap_srv_def.properties
                if prop_name in input_props:
                    value = ldap_srv_def.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_ldap_srv_def_repr(self):
        """Test LdapServerDefinition.__repr__()."""

        faked_ldap_srv_def1 = self.add_ldap_srv_def(name='a')
        ldap_srv_def1 = self.console.ldap_server_definitions.find(
            name=faked_ldap_srv_def1.name)

        # Execute the code to be tested
        repr_str = repr(ldap_srv_def1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=ldap_srv_def1.__class__.__name__,
                               id=id(ldap_srv_def1)),
                        repr_str)

    @pytest.mark.parametrize(
        "input_props, exp_exc", [
            ({'name': 'a'},
             None),
            ({'name': 'b'},
             None),
        ]
    )
    def test_ldap_srv_def_delete(self, input_props, exp_exc):
        """Test LdapServerDefinition.delete()."""

        faked_ldap_srv_def = self.add_ldap_srv_def(name=input_props['name'])

        ldap_srv_def_mgr = self.console.ldap_server_definitions
        ldap_srv_def = ldap_srv_def_mgr.find(name=faked_ldap_srv_def.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                ldap_srv_def.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the LDAP Server Definition still exists
            ldap_srv_def_mgr.find(name=faked_ldap_srv_def.name)

        else:

            # Execute the code to be tested.
            ldap_srv_def.delete()

            # Check that the LDAP Server Definition no longer exists
            with pytest.raises(NotFound) as exc_info:
                ldap_srv_def_mgr.find(name=faked_ldap_srv_def.name)

    def test_ldap_srv_def_delete_create_same_name(self):
        """Test LdapServerDefinition.delete() followed by create() with same
        name."""

        ldap_srv_def_name = 'faked_a'

        # Add the LDAP Server Definition to be tested
        self.add_ldap_srv_def(name=ldap_srv_def_name)

        # Input properties for a LDAP Server Definition with the same name
        sn_ldap_srv_def_props = {
            'name': ldap_srv_def_name,
            'description': 'LDAP Server Definition with same name',
            'type': 'user-defined',
        }

        ldap_srv_def_mgr = self.console.ldap_server_definitions
        ldap_srv_def = ldap_srv_def_mgr.find(name=ldap_srv_def_name)

        # Execute the deletion code to be tested
        ldap_srv_def.delete()

        # Check that the LDAP Server Definition no longer exists
        with pytest.raises(NotFound):
            ldap_srv_def_mgr.find(name=ldap_srv_def_name)

        # Execute the creation code to be tested.
        ldap_srv_def_mgr.create(sn_ldap_srv_def_props)

        # Check that the LDAP Server Definition exists again under that name
        sn_ldap_srv_def = ldap_srv_def_mgr.find(name=ldap_srv_def_name)
        description = sn_ldap_srv_def.get_property('description')
        assert description == sn_ldap_srv_def_props['description']

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New LDAP Server Definition description'},
        ]
    )
    def test_ldap_srv_def_update_properties(self, input_props):
        """Test LdapServerDefinition.update_properties()."""

        ldap_srv_def_name = 'faked_a'

        # Add the LDAP Server Definition to be tested
        self.add_ldap_srv_def(name=ldap_srv_def_name)

        ldap_srv_def_mgr = self.console.ldap_server_definitions
        ldap_srv_def = ldap_srv_def_mgr.find(name=ldap_srv_def_name)

        ldap_srv_def.pull_full_properties()
        saved_properties = copy.deepcopy(ldap_srv_def.properties)

        # Execute the code to be tested
        ldap_srv_def.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in ldap_srv_def.properties
            prop_value = ldap_srv_def.properties[prop_name]
            assert prop_value == exp_prop_value, \
                "Unexpected value for property {!r}".format(prop_name)

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        ldap_srv_def.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in ldap_srv_def.properties
            prop_value = ldap_srv_def.properties[prop_name]
            assert prop_value == exp_prop_value
