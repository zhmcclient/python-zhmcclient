# Copyright 2025 IBM Corp. All Rights Reserved.
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
Unit tests for _mfa_server_definition module.
"""

import re
import copy
import logging
import pytest

from zhmcclient import Client, HTTPError, NotFound, MfaServerDefinition
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestMfaServerDefinition:
    """All tests for the MfaServerDefinition and MfaServerDefinitionManager
    classes."""

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

    def add_mfa_srv_def(self, name):
        """
        Add a faked MFAServerDefinition object to the faked Console
        and return it.
        """

        faked_mfa_srv_def = self.faked_console.mfa_server_definitions.add({
            'element-id': f'oid-{name}',
            # element-uri will be automatically set
            'parent': '/api/console',
            'class': 'mfa-server-definition',
            'name': name,
            'description': f'MFA Server Definition {name}',
            'hostname-ipaddr': f'host-{name}',
        })
        return faked_mfa_srv_def

    def test_mfa_srv_def_manager_repr(self):
        """Test MfaServerDefinitionManager.__repr__()."""

        mfa_srv_def_mgr = self.console.mfa_server_definitions

        # Execute the code to be tested
        repr_str = repr(mfa_srv_def_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{mfa_srv_def_mgr.__class__.__name__}\s+at\s+'
            rf'0x{id(mfa_srv_def_mgr):08x}\s+\(\\n.*',
            repr_str)

    def test_mfa_srv_def_manager_initial_attrs(self):
        """Test initial attributes of MfaServerDefinitionManager."""

        mfa_srv_def_mgr = self.console.mfa_server_definitions

        # Verify all public properties of the manager object
        assert mfa_srv_def_mgr.resource_class == MfaServerDefinition
        assert mfa_srv_def_mgr.class_name == 'mfa-server-definition'
        assert mfa_srv_def_mgr.session is self.session
        assert mfa_srv_def_mgr.parent is self.console
        assert mfa_srv_def_mgr.console is self.console

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(full_properties=False),
             ['element-uri', 'name']),
            (dict(full_properties=True),
             ['element-uri', 'name', 'description']),
            ({},  # test default for full_properties (False)
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
            ({'name': 'A'},  # MFA user definitions have case-insensitive names
             ['a']),
        ]
    )
    def test_mfa_srv_def_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test MfaServerDefinitionManager.list()."""

        faked_mfa_srv_def1 = self.add_mfa_srv_def(name='a')
        faked_mfa_srv_def2 = self.add_mfa_srv_def(name='b')
        faked_mfa_srv_defs = [faked_mfa_srv_def1, faked_mfa_srv_def2]
        exp_faked_mfa_srv_defs = [u for u in faked_mfa_srv_defs
                                  if u.name in exp_names]
        mfa_srv_def_mgr = self.console.mfa_server_definitions

        # Execute the code to be tested
        mfa_srv_defs = mfa_srv_def_mgr.list(filter_args=filter_args,
                                            **full_properties_kwargs)

        assert_resources(mfa_srv_defs, exp_faked_mfa_srv_defs, prop_names)

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
              'hostname-ipaddr': '10.11.12.13'},
             ['element-uri', 'name', 'description'],
             None),
            ({'name': 'a',
              'hostname-ipaddr': '10.11.12.13',
              'port': 1234},
             ['element-uri', 'name', 'port'],
             None),
        ]
    )
    def test_mfa_srv_def_manager_create(
            self, caplog, input_props, exp_prop_names, exp_exc):
        """Test MfaServerDefinitionManager.create()."""

        logger_name = "zhmcclient.api"
        caplog.set_level(logging.DEBUG, logger=logger_name)

        mfa_srv_def_mgr = self.console.mfa_server_definitions

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                mfa_srv_def_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            mfa_srv_def = mfa_srv_def_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(mfa_srv_def, MfaServerDefinition)
            mfa_srv_def_name = mfa_srv_def.name
            exp_mfa_srv_def_name = mfa_srv_def.properties['name']
            assert mfa_srv_def_name == exp_mfa_srv_def_name
            mfa_srv_def_uri = mfa_srv_def.uri
            exp_mfa_srv_def_uri = mfa_srv_def.properties['element-uri']
            assert mfa_srv_def_uri == exp_mfa_srv_def_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in mfa_srv_def.properties
                if prop_name in input_props:
                    value = mfa_srv_def.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    def test_mfa_srv_def_repr(self):
        """Test MfaServerDefinition.__repr__()."""

        faked_mfa_srv_def1 = self.add_mfa_srv_def(name='a')
        mfa_srv_def1 = self.console.mfa_server_definitions.find(
            name=faked_mfa_srv_def1.name)

        # Execute the code to be tested
        repr_str = repr(mfa_srv_def1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{mfa_srv_def1.__class__.__name__}\s+at\s+'
            rf'0x{id(mfa_srv_def1):08x}\s+\(\\n.*',
            repr_str)

    @pytest.mark.parametrize(
        "input_props, exp_exc", [
            ({'name': 'a'},
             None),
            ({'name': 'b'},
             None),
        ]
    )
    def test_mfa_srv_def_delete(self, input_props, exp_exc):
        """Test MfaServerDefinition.delete()."""

        faked_mfa_srv_def = self.add_mfa_srv_def(name=input_props['name'])

        mfa_srv_def_mgr = self.console.mfa_server_definitions
        mfa_srv_def = mfa_srv_def_mgr.find(name=faked_mfa_srv_def.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                mfa_srv_def.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the MFA Server Definition still exists
            mfa_srv_def_mgr.find(name=faked_mfa_srv_def.name)

        else:

            # Execute the code to be tested.
            mfa_srv_def.delete()

            # Check that the MFA Server Definition no longer exists
            with pytest.raises(NotFound) as exc_info:
                mfa_srv_def_mgr.find(name=faked_mfa_srv_def.name)

    def test_mfa_delete_create_same(self):
        """Test MfaServerDefinition.delete() followed by create() with same
        name."""

        mfa_srv_def_name = 'faked_a'

        # Add the MFA Server Definition to be tested
        self.add_mfa_srv_def(name=mfa_srv_def_name)

        # Input properties for a MFA Server Definition with the same name
        sn_mfa_srv_def_props = {
            'name': mfa_srv_def_name,
            'description': 'MFA Server Definition with same name',
            'hostname-ipaddr': '10.11.12.13',
        }

        mfa_srv_def_mgr = self.console.mfa_server_definitions
        mfa_srv_def = mfa_srv_def_mgr.find(name=mfa_srv_def_name)

        # Execute the deletion code to be tested
        mfa_srv_def.delete()

        # Check that the MFA Server Definition no longer exists
        with pytest.raises(NotFound):
            mfa_srv_def_mgr.find(name=mfa_srv_def_name)

        # Execute the creation code to be tested.
        mfa_srv_def_mgr.create(sn_mfa_srv_def_props)

        # Check that the MFA Server Definition exists again under that name
        sn_mfa_srv_def = mfa_srv_def_mgr.find(name=mfa_srv_def_name)
        description = sn_mfa_srv_def.get_property('description')
        assert description == sn_mfa_srv_def_props['description']

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New MFA Server Definition description'},
            {'port': 1234},
        ]
    )
    def test_mfa_srv_def_update_properties(self, caplog, input_props):
        """Test MfaServerDefinition.update_properties()."""

        logger_name = "zhmcclient.api"
        caplog.set_level(logging.DEBUG, logger=logger_name)

        mfa_srv_def_name = 'faked_a'

        # Add the MFA Server Definition to be tested
        self.add_mfa_srv_def(name=mfa_srv_def_name)

        mfa_srv_def_mgr = self.console.mfa_server_definitions
        mfa_srv_def = mfa_srv_def_mgr.find(name=mfa_srv_def_name)

        mfa_srv_def.pull_full_properties()
        saved_properties = copy.deepcopy(mfa_srv_def.properties)

        # Execute the code to be tested
        mfa_srv_def.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in mfa_srv_def.properties
            prop_value = mfa_srv_def.properties[prop_name]
            assert prop_value == exp_prop_value, \
                f"Unexpected value for property {prop_name!r}"

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        mfa_srv_def.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in mfa_srv_def.properties
            prop_value = mfa_srv_def.properties[prop_name]
            assert prop_value == exp_prop_value
