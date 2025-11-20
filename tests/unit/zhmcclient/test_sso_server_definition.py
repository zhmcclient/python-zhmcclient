# Copyright 2017,2021 IBM Corp. All Rights Reserved.
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
Unit tests for _sso_srv_def module.
"""


import re
import copy
import logging
import pytest

from zhmcclient import Client, HTTPError, NotFound, SSOServerDefinition
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources, assert_blanked_in_message


class TestSSOServerDefinition:
    """All tests for the SSOServerDefinition and SSOServerDefinitionManager
    classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        Set up a faked session, and add a faked Console without any
        child resources.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.17.1', '1.8')
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

    def add_sso_srv_def(self, name):
        """
        Add a faked SSOServerDefinition object to the faked Console
        and return it.
        """

        faked_sso_srv_def = self.faked_console.sso_server_definitions.add({
            'element-id': f'oid-{name}',
            # element-uri will be automatically set
            'parent': '/api/console',
            'class': 'sso-server-definition',
            'name': name,
            'description': f'SSO Server Definition {name}',
            "authentication-page-servers":[
            {
            "hostname-ipaddr":"images1.example.com",
            "port":443
            },
            {
            "hostname-ipaddr":"images2.example.com",
            "port":80
            }
            ],
            "authentication-url":"https://sso1.example.com/auth",
            "client-id":"sso1-123456",
            "element-uri":"/api/console/sso-server-definitions/c6a464c2-a211-11ef-bbc4-fa163e7cf285",
            "issuer-url":"https://sso1.example.com/issuer",
           "jwks-url":"https://sso1.example.com/jwks",
           "logout-sso-session-on-reauthentication-failure":true,
          "logout-url":"https://sso1.example.com/logoff",
          "token-url":"https://sso1.example.com/token",
          "type":"oidc"
        })
        return faked_sso_srv_def

    def test_sso_srv_def_manager_repr(self):
        """Test SSOServerDefinitionManager.__repr__()."""

        sso_srv_def_mgr = self.console.sso_server_definitions

        # Execute the code to be tested
        repr_str = repr(sso_srv_def_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{sso_srv_def_mgr.__class__.__name__}\s+at\s+'
            rf'0x{id(sso_srv_def_mgr):08x}\s+\(\\n.*',
            repr_str)

    def test_sso_srv_def_manager_initial_attrs(self):
        """Test initial attributes of SSOServerDefinitionManager."""

        sso_srv_def_mgr = self.console.sso_server_definitions

        # Verify all public properties of the manager object
        assert sso_srv_def_mgr.resource_class == SSOServerDefinition
        assert sso_srv_def_mgr.class_name == 'sso-server-definition'
        assert sso_srv_def_mgr.session is self.session
        assert sso_srv_def_mgr.parent is self.console
        assert sso_srv_def_mgr.console is self.console

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(full_properties=False),
             ['element-uri', 'name','type']),
            (dict(full_properties=True),
             ['element-uri', 'name', 'type']),
            ({},  # test default for full_properties (False)
             ['element-uri', 'name','type']),
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
            ({'name': 'A'},  # SSO user definitions have case-insensitive names
             ['a']),
        ]
    )
    def test_sso_srv_def_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test SSOServerDefinitionManager.list()."""

        faked_sso_srv_def1 = self.add_sso_srv_def(name='a')
        faked_sso_srv_def2 = self.add_sso_srv_def(name='b')
        faked_sso_srv_defs = [faked_sso_srv_def1, faked_sso_srv_def2]
        exp_faked_sso_srv_defs = [u for u in faked_sso_srv_defs
                                   if u.name in exp_names]
        sso_srv_def_mgr = self.console.sso_server_definitions

        # Execute the code to be tested
        sso_srv_defs = sso_srv_def_mgr.list(filter_args=filter_args,
                                              **full_properties_kwargs)

        assert_resources(sso_srv_defs, exp_faked_sso_srv_defs, prop_names)

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
              'type': 'oidc',
              'client-secret': 'sso1-client-secret',
              "issuer-url":"https://sso1.example.com/issuer",
               'authentication-url' :'https://sso1.example.com/auth',
               'token-url':'https://sso1.example.com/token',
                "jwks-url":"https://sso1.example.com/jwks",
               'logout-url ':'https://sso1.example.com/logout'},
             ['element-uri', 'name', 'description'],
             None),
            ({'description': 'fake description X',
              'name': 'a',
              'type': 'oidc',
              'client-secret': 'sso1-client-secret',
              "issuer-url":"https://sso1.example.com/issuer",
               'authentication-url' :'https://sso1.example.com/auth',
               'token-url':'https://sso1.example.com/token',
                "jwks-url":"https://sso1.example.com/jwks",
               'logout-url ':'https://sso1.example.com/logout'},
             ['element-uri', 'name', 'client-secret'],
             None),
        ]
    )
    def test_sso_srv_def_manager_create(
            self, caplog, input_props, exp_prop_names, exp_exc):
        """Test SSOServerDefinitionManager.create()."""

        logger_name = "zhmcclient.api"
        caplog.set_level(logging.DEBUG, logger=logger_name)

        sso_srv_def_mgr = self.console.sso_server_definitions

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                sso_srv_def_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            sso_srv_def = sso_srv_def_mgr.create(properties=input_props)

            # Get its API call log record
            call_record = caplog.records[-2]

            # Check the resource for consistency within itself
            assert isinstance(sso_srv_def, SSOServerDefinition)
            sso_srv_def_name = sso_srv_def.name
            exp_sso_srv_def_name = sso_srv_def.properties['name']
            assert sso_srv_def_name == exp_sso_srv_def_name
            sso_srv_def_uri = sso_srv_def.uri
            exp_sso_srv_def_uri = sso_srv_def.properties['element-uri']
            assert sso_srv_def_uri == exp_sso_srv_def_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in sso_srv_def.properties
                if prop_name in input_props:
                    value = sso_srv_def.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

            # Verify the API call log record for blanked-out properties.
            assert_blanked_in_message(
                call_record.message, input_props,
                ['client-secret'])

    def test_sso_srv_def_repr(self):
        """Test SSOServerDefinition.__repr__()."""

        faked_sso_srv_def1 = self.add_sso_srv_def(name='a')
        sso_srv_def1 = self.console.sso_server_definitions.find(
            name=faked_sso_srv_def1.name)

        # Execute the code to be tested
        repr_str = repr(sso_srv_def1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{sso_srv_def1.__class__.__name__}\s+at\s+'
            rf'0x{id(sso_srv_def1):08x}\s+\(\\n.*',
            repr_str)

    @pytest.mark.parametrize(
        "input_props, exp_exc", [
            ({'name': 'a'},
             None),
            ({'name': 'b'},
             None),
        ]
    )
    def test_sso_srv_def_delete(self, input_props, exp_exc):
        """Test SSOServerDefinition.delete()."""

        faked_sso_srv_def = self.add_sso_srv_def(name=input_props['name'])

        sso_srv_def_mgr = self.console.sso_server_definitions
        sso_srv_def = sso_srv_def_mgr.find(name=faked_sso_srv_def.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                sso_srv_def.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the SSO Server Definition still exists
            sso_srv_def_mgr.find(name=faked_sso_srv_def.name)

        else:

            # Execute the code to be tested.
            sso_srv_def.delete()

            # Check that the SSO Server Definition no longer exists
            with pytest.raises(NotFound) as exc_info:
                sso_srv_def_mgr.find(name=faked_sso_srv_def.name)

    def test_sso_delete_create_same(self):
        """Test SSOServerDefinition.delete() followed by create() with same
        name."""

        sso_srv_def_name = 'faked_a'

        # Add the SSO Server Definition to be tested
        self.add_sso_srv_def(name=sso_srv_def_name)

        # Input properties for a SSO Server Definition with the same name
        sn_sso_srv_def_props = {
            'name': sso_srv_def_name,
            'description': 'SSO Server Definition with same name',
            'primary-hostname-ipaddr': '10.11.12.13',
            'search-distinguished-name': 'test{0}',
        }

        sso_srv_def_mgr = self.console.sso_server_definitions
        sso_srv_def = sso_srv_def_mgr.find(name=sso_srv_def_name)

        # Execute the deletion code to be tested
        sso_srv_def.delete()

        # Check that the SSO Server Definition no longer exists
        with pytest.raises(NotFound):
            sso_srv_def_mgr.find(name=sso_srv_def_name)

        # Execute the creation code to be tested.
        sso_srv_def_mgr.create(sn_sso_srv_def_props)

        # Check that the SSO Server Definition exists again under that name
        sn_sso_srv_def = sso_srv_def_mgr.find(name=sso_srv_def_name)
        description = sn_sso_srv_def.get_property('description')
        assert description == sn_sso_srv_def_props['description']

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New SSO Server Definition description'},
            {'client-secret': 'bla'},
        ]
    )
    def test_sso_srv_def_update_properties(self, caplog, input_props):
        """Test SSOServerDefinition.update_properties()."""

        logger_name = "zhmcclient.api"
        caplog.set_level(logging.DEBUG, logger=logger_name)

        sso_srv_def_name = 'faked_a'

        # Add the SSO Server Definition to be tested
        self.add_sso_srv_def(name=sso_srv_def_name)

        sso_srv_def_mgr = self.console.sso_server_definitions
        sso_srv_def = sso_srv_def_mgr.find(name=sso_srv_def_name)

        sso_srv_def.pull_full_properties()
        saved_properties = copy.deepcopy(sso_srv_def.properties)

        # Execute the code to be tested
        sso_srv_def.update_properties(properties=input_props)

        # Get its API call log record
        call_record = caplog.records[-2]

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in sso_srv_def.properties
            prop_value = sso_srv_def.properties[prop_name]
            assert prop_value == exp_prop_value, \
                f"Unexpected value for property {prop_name!r}"

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        sso_srv_def.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in sso_srv_def.properties
            prop_value = sso_srv_def.properties[prop_name]
            assert prop_value == exp_prop_value

        # Verify the API call log record for blanked-out properties.
        assert_blanked_in_message(
            call_record.message, input_props,
            ['client-secret'])
