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
Unit tests for _unmanaged_cpc module.
"""

from __future__ import absolute_import, print_function

import pytest
import re

from zhmcclient import Client, UnmanagedCpc
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestUnmanagedCpc(object):
    """All tests for the UnmanagedCpc and UnmanagedCpcManager classes."""

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

    def add_unmanaged_cpc(self, name):
        faked_unmanaged_cpc = self.faked_console.unmanaged_cpcs.add({
            'object-id': 'oid-{}'.format(name),
            # object-uri will be automatically set
            'parent': '/api/console',
            'class': 'cpc',
            'name': name,
            'description': 'Unmanaged CPC {}'.format(name),
        })
        return faked_unmanaged_cpc

    def test_ucpc_manager_repr(self):
        """Test UnmanagedCpcManager.__repr__()."""

        ucpc_mgr = self.console.unmanaged_cpcs

        # Execute the code to be tested
        repr_str = repr(ucpc_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=ucpc_mgr.__class__.__name__,
                               id=id(ucpc_mgr)),
                        repr_str)

    def test_ucpc_manager_initial_attrs(self):
        """Test initial attributes of UnmanagedCpcManager."""

        ucpc_mgr = self.console.unmanaged_cpcs

        # Verify all public properties of the manager object
        assert ucpc_mgr.resource_class == UnmanagedCpc
        assert ucpc_mgr.class_name == 'cpc'
        assert ucpc_mgr.session is self.session
        assert ucpc_mgr.parent is self.console
        assert ucpc_mgr.console is self.console

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
    def test_ucpc_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test UnmanagedCpcManager.list()."""

        faked_ucpc1 = self.add_unmanaged_cpc(name='a')
        faked_ucpc2 = self.add_unmanaged_cpc(name='b')
        faked_ucpcs = [faked_ucpc1, faked_ucpc2]
        exp_faked_ucpcs = [u for u in faked_ucpcs if u.name in exp_names]
        ucpc_mgr = self.console.unmanaged_cpcs

        # Execute the code to be tested
        ucpcs = ucpc_mgr.list(filter_args=filter_args,
                              **full_properties_kwargs)

        assert_resources(ucpcs, exp_faked_ucpcs, prop_names)

    def test_ucpc_repr(self):
        """Test UnmanagedCpc.__repr__()."""

        faked_ucpc1 = self.add_unmanaged_cpc(name='a')
        ucpc1 = self.console.unmanaged_cpcs.find(name=faked_ucpc1.name)

        # Execute the code to be tested
        repr_str = repr(ucpc1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=ucpc1.__class__.__name__,
                               id=id(ucpc1)),
                        repr_str)
