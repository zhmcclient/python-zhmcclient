# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Unit tests for _console module.
"""

from __future__ import absolute_import, print_function

import pytest
import re

from zhmcclient import Client, Error, Console, UserManager, UserRoleManager, \
    UserPatternManager, PasswordRuleManager, TaskManager, \
    LdapServerDefinitionManager
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestConsole(object):
    """All tests for the Console and ConsoleManager classes."""

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

    def test_consolemanager_initial_attrs(self):
        """Test initial attributes of ConsoleManager."""

        console_mgr = self.client.consoles

        # Verify all public properties of the manager object
        assert console_mgr.resource_class == Console
        assert console_mgr.class_name == 'console'
        assert console_mgr.session == self.session
        assert console_mgr.parent is None
        assert console_mgr.client == self.client

    # TODO: Test for ConsoleManager.__repr__()

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
        "filter_args", [  # will be ignored
            None,
            {},
            {'name': 'foo'},
        ]
    )
    def test_consolemanager_list(
            self, filter_args, full_properties_kwargs, prop_names):
        """Test ConsoleManager.list()."""

        exp_faked_consoles = [self.faked_console]
        console_mgr = self.client.consoles

        # Execute the code to be tested
        consoles = console_mgr.list(
            filter_args=filter_args,
            **full_properties_kwargs)

        assert_resources(consoles, exp_faked_consoles, prop_names)

    def test_console_initial_attrs(self):
        """Test initial attributes of Console."""

        console_mgr = self.client.consoles
        console = console_mgr.find(name=self.faked_console.name)

        # Verify all public properties of the resource object (except those
        # of its BaseResource superclass which are tested at that level).
        assert isinstance(console.users, UserManager)
        assert isinstance(console.user_roles, UserRoleManager)
        assert isinstance(console.user_patterns, UserPatternManager)
        assert isinstance(console.password_rules, PasswordRuleManager)
        assert isinstance(console.tasks, TaskManager)
        assert isinstance(console.ldap_server_definitions,
                          LdapServerDefinitionManager)

    def test_console_repr(self):
        """Test Console.__repr__()."""

        console_mgr = self.client.consoles
        console = console_mgr.find(name=self.faked_console.name)

        # Execute the code to be tested
        repr_str = repr(console)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=console.__class__.__name__,
                               id=id(console)),
                        repr_str)

    @pytest.mark.parametrize(
        "wait", [
            True,
            # False,  # TODO: Re-enable once implemented
        ]
    )
    @pytest.mark.parametrize(
        "force", [
            True,
            False,
        ]
    )
    def test_console_restart(self, force, wait):
        """Test Console.restart()."""

        console_mgr = self.client.consoles
        console = console_mgr.find(name=self.faked_console.name)

        # Note: The force parameter is passed in, but we expect the restart
        # to always succeed. This means we are not testing cases with other
        # HMC users being logged on, that would either cause a non-forced
        # restart to be rejected, or a forced restart to succeed despite them.

        # Execute the code to be tested.
        ret = console.restart(
            force=force,
            wait_for_available=wait,
            operation_timeout=600)

        assert ret is None

        if wait:
            # The HMC is expected to be up again, and therefore a simple
            # operation is expected to succeed:
            try:
                self.client.query_api_version()
            except Error as exc:
                pytest.fail(
                    "Unexpected zhmcclient exception during "
                    "query_api_version() after HMC restart: %s" % exc)
        else:
            # The HMC is expected to still be in the restart process, and
            # therefore a simple operation is expected to fail. This test
            # may end up to be timing dependent.
            try:
                self.client.query_api_version()
            except Error:
                pass
            except Exception as exc:
                pytest.fail(
                    "Unexpected non-zhmcclient exception during "
                    "query_api_version() after HMC restart: %s" % exc)
            else:
                pytest.fail(
                    "Unexpected success of query_api_version() after HMC "
                    "restart.")

    @pytest.mark.parametrize(
        "force", [
            True,
            False,
        ]
    )
    def test_console_shutdown(self, force):
        """Test Console.shutdown()."""

        console_mgr = self.client.consoles
        console = console_mgr.find(name=self.faked_console.name)

        # Note: The force parameter is passed in, but we expect the shutdown
        # to always succeed. This means we are not testing cases with other
        # HMC users being logged on, that would either cause a non-forced
        # shutdown to be rejected, or a forced shutdown to succeed despite
        # them.

        # Execute the code to be tested.
        ret = console.shutdown(force=force)

        assert ret is None

        # The HMC is expected to be offline, and therefore a simple operation
        # is expected to fail.
        try:
            self.client.query_api_version()
        except Error:
            pass
        except Exception as exc:
            pytest.fail(
                "Unexpected non-zhmcclient exception during "
                "query_api_version() after HMC shutdown: %s" % exc)
        else:
            pytest.fail(
                "Unexpected success of query_api_version() after HMC "
                "shutdown.")

    def test_console_audit_log(self):
        """Test Console.get_audit_log()."""

        # TODO: Add begin/end_time once mocked audit log is supported

        console_mgr = self.client.consoles
        console = console_mgr.find(name=self.faked_console.name)

        # Execute the code to be tested.
        log_items = console.get_audit_log()

        assert isinstance(log_items, list)

        # TODO: Verify log items once mocked audit log is supported

    def test_console_security_log(self):
        """Test Console.get_security_log()."""

        # TODO: Add begin/end_time once mocked security log is supported

        console_mgr = self.client.consoles
        console = console_mgr.find(name=self.faked_console.name)

        # Execute the code to be tested.
        log_items = console.get_security_log()

        assert isinstance(log_items, list)

        # TODO: Verify log items once mocked security log is supported

    @pytest.mark.parametrize(
        "name, exp_cpc_names, prop_names", [
            (None,
             ['ucpc_name_1', 'ucpc_name_2'],
             ['object-uri', 'name']),
            ('.*',
             ['ucpc_name_1', 'ucpc_name_2'],
             ['object-uri', 'name']),
            ('ucpc_name_.*',
             ['ucpc_name_1', 'ucpc_name_2'],
             ['object-uri', 'name']),
            ('ucpc_name_1',
             ['ucpc_name_1'],
             ['object-uri', 'name']),
            ('ucpc_name_1.*',
             ['ucpc_name_1'],
             ['object-uri', 'name']),
            ('ucpc_name_1.+',
             [],
             ['object-uri', 'name']),
        ]
    )
    def test_console_list_unmanaged_cpcs(
            self, name, exp_cpc_names, prop_names):
        """Test Console.list_unmanaged_cpcs() and
        UnmanagedCpcManager.list()."""

        console_mgr = self.client.consoles
        console = console_mgr.find(name=self.faked_console.name)

        # Add two unmanaged faked CPCs
        faked_ucpc1 = self.faked_console.unmanaged_cpcs.add({
            'object-id': 'ucpc-oid-1',
            # object-uri is set up automatically
            'name': 'ucpc_name_1',
        })
        faked_ucpc2 = self.faked_console.unmanaged_cpcs.add({
            'object-id': 'ucpc-oid-2',
            # object-uri is set up automatically
            'name': 'ucpc_name_2',
        })
        faked_ucpcs = [faked_ucpc1, faked_ucpc2]

        exp_faked_ucpcs = [cpc for cpc in faked_ucpcs
                           if cpc.name in exp_cpc_names]

        # Execute the code to be tested.
        # This indirectly tests UnmanagedCpcManager.list().
        ucpcs = console.list_unmanaged_cpcs(name)

        assert_resources(ucpcs, exp_faked_ucpcs, prop_names)
