# Copyright 2026 IBM Corp. All Rights Reserved.
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
Unit tests for _tape_library module.
"""


import copy
import logging
import pytest

from zhmcclient import Client, TapeLibrary, HTTPError, NotFound
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources

# Object IDs and names of our faked tape library:
TL1_NAME = 'tl1'
TL2_NAME = 'tl2'
CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'


class TestTapeLibrary:
    """All tests for the TapeLibrary and TapeLibraryManager classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Set up a faked session, and add a faked Console without any
        child resources.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.15.0', '1.8')
        self.client = Client(self.session)
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': CPC_OID,
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode, storage mgmt feature enabled)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
            'available-features-list': [
                dict(name='dpm-storage-management', state=True),
            ],
            'management-world-wide-port-name': None
        })
        assert self.faked_cpc.uri == CPC_URI
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

        self.faked_console = self.session.hmc.consoles.add({
            'object-id': None,
            # object-uri will be automatically set
            'parent': None,
            'class': 'console',
            'name': 'fake-console1',
            'description': 'Console #1',
        })
        self.console = self.client.consoles.find(name=self.faked_console.name)

    @staticmethod
    def add_fcp(faked_cpc):
        """Add a FCP type FICON Express 6S+ adapter to a faked CPC."""

        # Adapter properties that will be auto-set:
        # - object-uri
        # - storage-port-uris
        faked_fcp_adapter = faked_cpc.adapters.add({
            'object-id': 'fake-fcp-oid',
            'parent': faked_cpc.uri,
            'class': 'adapter',
            'name': 'fake-fcp-name',
            'description': 'FCP Adapter',
            'status': 'active',
            'type': 'FCP',
            'adapter-id': '124',
            'adapter-family': 'ficon',
            'detected-card-type': 'ficon-express-16s-plus',
            'card-location': 'vvvv-wwww',
            'port-count': 1,
            'state': 'online',
            'configured-capacity': 254,
            'used-capacity': 0,
            'allowed-capacity': 254,
            'maximum-total-capacity': 254,
            'channel-path-id': None,
            'physical-channel-status': 'not-defined',
        })
        return faked_fcp_adapter

    def add_tape_library(self, name):
        """Add Tape Library1"""

        faked_tape_library = self.faked_console.tape_library.add({
            'object-uri': f'/api/tape-libraries/{name}',
            'parent': self.faked_console.uri,
            'class': 'tape-library',
            'name': name,
            'description': f'tapelibrary {name}',
        })
        return faked_tape_library

    def test_tape_lib_mgr_initial_attrs(self):
        """Test initial attributes of TapeLibraryManager."""

        tape_lib_mgr = self.console.tape_library

        # Verify all public properties of the manager object
        assert tape_lib_mgr.resource_class == TapeLibrary
        assert tape_lib_mgr.class_name == 'tape-library'
        assert tape_lib_mgr.session == self.session
        assert tape_lib_mgr.parent == self.console
        assert tape_lib_mgr.console == self.console

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(full_properties=False),
             ['object-uri', 'name']),
            (dict(full_properties=True),
             ['object-uri', 'name', 'description']),
            ({},  # test default for full_properties (False)
             ['object-uri', 'name']),
        ]
    )
    @pytest.mark.parametrize(
        "filter_args, exp_name", [
            (None, [TL1_NAME, TL2_NAME]),
            ({}, [TL1_NAME, TL2_NAME]),
            ({'name': TL1_NAME}, [TL1_NAME]),
            ({'name': [TL1_NAME, TL2_NAME]}, [TL1_NAME, TL2_NAME]),
        ]
    )
    def test_tape_lib_mgr_list(
            self, filter_args, exp_name, full_properties_kwargs, prop_names):
        """Test TapeLibraryManager.list()."""

        faked_tape_lib1 = self.add_tape_library(name=TL1_NAME)
        faked_tape_lib2 = self.add_tape_library(name=TL2_NAME)
        faked_tape_libs = [faked_tape_lib1, faked_tape_lib2]
        exp_faked_tape_libs = [u for u in faked_tape_libs
                               if u.name in exp_name]
        tape_lib_mgr = self.console.tape_library

        # Execute the code to be tested
        tape_libs = tape_lib_mgr.list(filter_args=filter_args,
                                      **full_properties_kwargs)

        assert_resources(tape_libs, exp_faked_tape_libs, prop_names)

    @pytest.mark.parametrize(
        "input_props,fcp_availability ,exp_exc", [
            ({}, True, None),
            ({}, False, HTTPError({'http-status': 409, 'reason': 487})),
        ]
    )
    def test_tape_lib_manager_request_zoning(
            self, caplog, input_props, fcp_availability, exp_exc):
        """Test TapeLibraryManager.request_zoning()."""

        logger_name = "zhmcclient.api"
        caplog.set_level(logging.DEBUG, logger=logger_name)

        tape_lib_mgr = self.console.tape_library

        if fcp_availability:
            self.add_fcp(self.faked_cpc)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                tape_lib_mgr.request_zoning(input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason
        else:
            tape_lib_mgr.request_zoning(input_props)

    @pytest.mark.parametrize(
        "input_props,management_world_wide_port_name, exp_exc", [
            ({},
             False, HTTPError({'http-status': 409, 'reason': 501})
             ),
            ({}, True, None)
        ]
    )
    def test_tape_lib_manager_discovertl(
            self, caplog, input_props,
            management_world_wide_port_name, exp_exc):
        """Test TapeLibraryManager.discover()."""

        logger_name = "zhmcclient.api"
        caplog.set_level(logging.DEBUG, logger=logger_name)

        tape_lib_mgr = self.console.tape_library

        if management_world_wide_port_name:
            self.faked_cpc.properties['management-world-wide-port-name'] = \
                'a1b2c3d4e5f60002'

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                tape_lib_mgr.discover(input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:
            tape_lib_mgr.discover(input_props)

    @pytest.mark.parametrize(
        "input_props, exp_exc", [
            ({'name': TL1_NAME},
             None),
            ({'name': TL2_NAME},
             None),
        ]
    )
    def test_tape_lib_undefine(self, input_props, exp_exc):
        """Test TapeLibrary.undefine()."""

        faked_tape_lib = self.add_tape_library(name=input_props['name'])

        tape_lib_mgr = self.console.tape_library
        tape_lib = tape_lib_mgr.find(name=faked_tape_lib.name)
        print('Manager before undefine', str(tape_lib_mgr))

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                tape_lib.undefine()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the Tape Library still exists
            tape_lib_mgr.find(name=faked_tape_lib.name)

        else:

            # Execute the code to be tested.
            tape_lib.undefine()

            # Check that the Tape Library no longer exists
            with pytest.raises(NotFound) as exc_info:
                tape_lib_mgr.find(name=tape_lib.name)

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'name': TL1_NAME},
            {'description': 'Test Description for Tape Library'},
        ]
    )
    def test_tape_lib_update_properties(self, caplog, input_props):
        """Test TapeLibrary.update_properties()."""
        logger_name = "zhmcclient.api"
        caplog.set_level(logging.DEBUG, logger=logger_name)

        tape_lib_name = TL2_NAME

        # Add the Tape Library to be tested
        self.add_tape_library(name=tape_lib_name)

        tape_lib_mgr = self.console.tape_library
        tape_lib = tape_lib_mgr.find(name=tape_lib_name)

        tape_lib.pull_full_properties()
        saved_properties = copy.deepcopy(tape_lib.properties)

        # Execute the code to be tested
        tape_lib.update_properties(properties=input_props)
        tape_lib.pull_full_properties()
        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in tape_lib.properties
            prop_value = tape_lib.properties[prop_name]
            assert prop_value == exp_prop_value, \
                f"Unexpected value for property {prop_name!r}"

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        tape_lib.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in tape_lib.properties
            prop_value = tape_lib.properties[prop_name]
            assert prop_value == exp_prop_value
