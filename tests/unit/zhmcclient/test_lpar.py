# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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
Unit tests for _lpar module.
"""


import re
import copy
import logging
from unittest import mock
import pytest
import requests_mock

from zhmcclient import Client, Lpar, HTTPError, StatusTimeout, Job
from zhmcclient_mock import FakedSession, LparActivateHandler, \
    LparDeactivateHandler, LparLoadHandler
from tests.common.utils import assert_resources, assert_blanked_in_message

# pylint: disable=unused-import,line-too-long
from tests.common.http_mocked_fixtures import http_mocked_session  # noqa: F401
from tests.common.http_mocked_fixtures import http_mocked_cpc_classic  # noqa: F401,E501
from tests.common.http_mocked_fixtures import http_mocked_lpar  # noqa: F401
# pylint: enable=unused-import,line-too-long


# Object IDs and names of our faked LPARs:
LPAR1_OID = 'lpar1-oid'
LPAR1_NAME = 'lpar 1'
LPAR2_OID = 'lpar2-oid'
LPAR2_NAME = 'lpar 2'

# Object IDs and names of our faked image activation profiles:
IMAGEPROFILE1_OID = 'imageprofile1-oid'
IMAGEPROFILE1_NAME = 'imageprofile 1'
IMAGEPROFILE2_OID = 'imageprofile2-oid'
IMAGEPROFILE2_NAME = 'imageprofile 2'

CPC_NAME = 'fake-cpc1-name'

# Properties returned by default from list_permitted_lpars()
LIST_PERMITTED_LPARS_PROPS = [
    'name', 'object-uri', 'activation-mode', 'status',
    'has-unacceptable-status', 'cpc-name', 'cpc-object-uri',
    # The zhmcclient_mock support always returns 'se-version'
    'se-version'
]


class TestLpar:
    """All tests for Lpar and LparManager classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Set up a faked session, and add a faked CPC in classic mode without any
        child resources.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.16.0', '4.1')
        self.session.retry_timeout_config.status_timeout = 1
        self.client = Client(self.session)

        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'fake-cpc1-oid',
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': CPC_NAME,
            'description': 'CPC #1 (classic mode)',
            'status': 'active',
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'iml-mode': 'lpar',
        })
        self.cpc = self.client.cpcs.find(name=CPC_NAME)

    def add_lpar1(self):
        """Add lpar 1 (type linux)."""

        faked_lpar = self.faked_cpc.lpars.add({
            'object-id': LPAR1_OID,
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'logical-partition',
            'name': LPAR1_NAME,
            'description': 'LPAR #1 (Linux)',
            'status': 'operating',
            'activation-mode': 'linux',
            'last-used-load-address': '',
            'last-used-load-parameter': '',
            'last-used-world-wide-port-name': '',
            'last-used-logical-unit-number': '',
            'last-used-disk-partition-id': 0,
            'last-used-operating-system-specific-load-parameters': '',
            'last-used-boot-record-logical-block-address': '0',
            'last-used-load-type': 'ipltype-standard',
            'last-used-secure-boot': False,
            'last-used-clear-indicator': True,
        })
        return faked_lpar

    def add_imageprofile1(self):
        """Add image profile for lpar 1 (no auto-load)."""

        faked_imageprofile = self.faked_cpc.image_activation_profiles.add({
            'object-id': IMAGEPROFILE1_OID,
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'image-activation-profile',
            'name': LPAR1_NAME,
            'description': 'Image profile for LPAR #1 (Linux)',
            'ipl-address': '00000',
            'ipl-parameter': '',
            'ipl-type': 'ipltype-standard',
            'load-at-activation': False,
            'operating-mode': 'linux',
        })
        return faked_imageprofile

    def add_lpar2(self):
        """Add lpar 2 (type ssc)."""

        faked_lpar = self.faked_cpc.lpars.add({
            'object-id': LPAR2_OID,
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'logical-partition',
            'name': LPAR2_NAME,
            'description': 'LPAR #2 (SSC)',
            'status': 'operating',
            'activation-mode': 'ssc',
            'last-used-load-address': '',
            'last-used-load-parameter': '',
            'last-used-world-wide-port-name': '',
            'last-used-logical-unit-number': '',
            'last-used-disk-partition-id': 0,
            'last-used-operating-system-specific-load-parameters': '',
            'last-used-boot-record-logical-block-address': '0',
            'last-used-load-type': 'ipltype-standard',
            'last-used-secure-boot': False,
            'last-used-clear-indicator': True,
        })
        return faked_lpar

    def add_imageprofile2(self):
        """Add image profile for lpar 2 (auto-load due to SSC)."""

        faked_imageprofile = self.faked_cpc.image_activation_profiles.add({
            'object-id': IMAGEPROFILE2_OID,
            # object-uri will be automatically set
            'parent': self.faked_cpc.uri,
            'class': 'image-activation-profile',
            'name': LPAR2_NAME,
            'description': 'Image profile for LPAR #2 (SSC)',
            'ipl-address': '00000',
            'ipl-parameter': '',
            'ipl-type': 'ipltype-standard',
            'load-at-activation': False,
            'operating-mode': 'ssc',
        })
        return faked_imageprofile

    def test_lparmanager_initial_attrs(self):
        """Test initial attributes of LparManager."""

        lpar_mgr = self.cpc.lpars

        # Verify all public properties of the manager object
        assert lpar_mgr.resource_class == Lpar
        assert lpar_mgr.session == self.session
        assert lpar_mgr.parent == self.cpc
        assert lpar_mgr.cpc == self.cpc

    # TODO: Test for LparManager.__repr__()

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            ({},
             ['object-uri', 'name', 'status']),
            (dict(full_properties=False),
             ['object-uri', 'name', 'status']),
            (dict(full_properties=True),
             None),
        ]
    )
    def test_lparmanager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test LparManager.list() with full_properties."""

        # Add two faked LPARs
        faked_lpar1 = self.add_lpar1()
        faked_lpar2 = self.add_lpar2()

        exp_faked_lpars = [faked_lpar1, faked_lpar2]
        lpar_mgr = self.cpc.lpars

        # Execute the code to be tested
        lpars = lpar_mgr.list(**full_properties_kwargs)

        assert_resources(lpars, exp_faked_lpars, prop_names)

    @pytest.mark.parametrize(
        "filter_args, exp_names", [
            ({'object-id': LPAR1_OID},
             [LPAR1_NAME]),
            ({'object-id': LPAR2_OID},
             [LPAR2_NAME]),
            ({'object-id': [LPAR1_OID, LPAR2_OID]},
             [LPAR1_NAME, LPAR2_NAME]),
            ({'object-id': [LPAR1_OID, LPAR1_OID]},
             [LPAR1_NAME]),
            ({'object-id': LPAR1_OID + 'foo'},
             []),
            ({'object-id': [LPAR1_OID, LPAR2_OID + 'foo']},
             [LPAR1_NAME]),
            ({'object-id': [LPAR2_OID + 'foo', LPAR1_OID]},
             [LPAR1_NAME]),
            ({'name': LPAR1_NAME},
             [LPAR1_NAME]),
            ({'name': LPAR2_NAME},
             [LPAR2_NAME]),
            ({'name': [LPAR1_NAME, LPAR2_NAME]},
             [LPAR1_NAME, LPAR2_NAME]),
            ({'name': LPAR1_NAME + 'foo'},
             []),
            ({'name': [LPAR1_NAME, LPAR2_NAME + 'foo']},
             [LPAR1_NAME]),
            ({'name': [LPAR2_NAME + 'foo', LPAR1_NAME]},
             [LPAR1_NAME]),
            ({'name': [LPAR1_NAME, LPAR1_NAME]},
             [LPAR1_NAME]),
            ({'name': '.*lpar 1'},
             [LPAR1_NAME]),
            ({'name': 'lpar 1.*'},
             [LPAR1_NAME]),
            ({'name': 'lpar .'},
             [LPAR1_NAME, LPAR2_NAME]),
            ({'name': '.par 1'},
             [LPAR1_NAME]),
            ({'name': '.+'},
             [LPAR1_NAME, LPAR2_NAME]),
            ({'name': 'lpar 1.+'},
             []),
            ({'name': '.+lpar 1'},
             []),
            ({'name': LPAR1_NAME,
              'object-id': LPAR1_OID},
             [LPAR1_NAME]),
            ({'name': LPAR1_NAME,
              'object-id': LPAR1_OID + 'foo'},
             []),
            ({'name': LPAR1_NAME + 'foo',
              'object-id': LPAR1_OID},
             []),
            ({'name': LPAR1_NAME + 'foo',
              'object-id': LPAR1_OID + 'foo'},
             []),
        ]
    )
    def test_lparmanager_list_filter_args(self, filter_args, exp_names):
        """Test LparManager.list() with filter_args."""

        # Add two faked LPARs
        self.add_lpar1()
        self.add_lpar2()

        lpar_mgr = self.cpc.lpars

        # Execute the code to be tested
        lpars = lpar_mgr.list(filter_args=filter_args)

        assert len(lpars) == len(exp_names)
        if exp_names:
            names = [p.properties['name'] for p in lpars]
            assert set(names) == set(exp_names)

    def test_lpar_repr(self):
        """Test Lpar.__repr__()."""

        # Add a faked LPAR
        faked_lpar = self.add_lpar1()

        lpar_mgr = self.cpc.lpars
        lpar = lpar_mgr.find(name=faked_lpar.name)

        # Execute the code to be tested
        repr_str = repr(lpar)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{lpar.__class__.__name__}\s+at\s+'
            rf'0x{id(lpar):08x}\s+\(\\n.*',
            repr_str)

    @pytest.mark.parametrize(
        "lpar_name", [
            LPAR1_NAME,
            LPAR2_NAME,
        ]
    )
    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New lpar description'},
            {'acceptable-status': ['operating', 'not-operating'],
             'description': 'New lpar description'},
            {'ssc-master-userid': 'user',
             'ssc-master-pw': 'bla'},
            {'zaware-master-userid': 'user',
             'zaware-master-pw': 'bla'},
        ]
    )
    def test_lpar_update_properties(self, caplog, input_props, lpar_name):
        """Test Lpar.update_properties()."""

        logger_name = "zhmcclient.api"
        caplog.set_level(logging.DEBUG, logger=logger_name)

        # Add faked lpars
        self.add_lpar1()
        self.add_lpar2()

        lpar_mgr = self.cpc.lpars
        lpar = lpar_mgr.find(name=lpar_name)

        lpar.pull_full_properties()
        saved_properties = copy.deepcopy(lpar.properties)

        # Execute the code to be tested
        lpar.update_properties(properties=input_props)

        # Get its API call log record
        call_record = caplog.records[-2]

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in lpar.properties
            prop_value = lpar.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        lpar.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in lpar.properties
            prop_value = lpar.properties[prop_name]
            assert prop_value == exp_prop_value

        # Verify the API call log record for blanked-out properties.
        assert_blanked_in_message(
            call_record.message, input_props,
            ['ssc-master-pw', 'zaware-master-pw'])

    @pytest.mark.parametrize(
        "initial_profile, profile_kwargs, exp_profile, exp_profile_exc", [
            ('', {},
             None, HTTPError({'http-status': 500, 'reason': 263})),
            (LPAR1_NAME, {},
             LPAR1_NAME, None),
            (LPAR2_NAME, {},
             None, HTTPError({'http-status': 500, 'reason': 263})),
            ('', dict(activation_profile_name=LPAR1_NAME),
             LPAR1_NAME, None),
            (LPAR1_NAME, dict(activation_profile_name=LPAR1_NAME),
             LPAR1_NAME, None),
            (LPAR2_NAME, dict(activation_profile_name=LPAR1_NAME),
             LPAR1_NAME, None),
            ('', dict(activation_profile_name=LPAR2_NAME),
             None, HTTPError({'http-status': 500, 'reason': 263})),
            (LPAR1_NAME, dict(activation_profile_name=LPAR2_NAME),
             None, HTTPError({'http-status': 500, 'reason': 263})),
            (LPAR2_NAME, dict(activation_profile_name=LPAR2_NAME),
             None, HTTPError({'http-status': 500, 'reason': 263})),
        ]
    )
    @pytest.mark.parametrize(
        "initial_status, status_kwargs, act_exp_status, exp_status_exc", [

            ('not-activated', {},  # Verify that force has a default
             'not-operating', None),
            ('not-activated', dict(force=False),
             'not-operating', None),
            ('not-activated', dict(force=True),
             'not-operating', None),

            ('not-operating', dict(force=False),
             'not-operating', None),
            ('not-operating', dict(force=True),
             'not-operating', None),

            ('operating', {},  # Verify that force default is False
             'not-operating', HTTPError({'http-status': 500, 'reason': 263})),
            ('operating', dict(force=False),
             'not-operating', HTTPError({'http-status': 500, 'reason': 263})),
            ('operating', dict(force=True),
             'not-operating', None),

            ('exceptions', dict(force=False),
             'not-operating', None),
            ('exceptions', dict(force=True),
             'not-operating', None),

            ('not-activated', {},
             'exceptions', StatusTimeout(None, None, None, None)),
            ('not-activated', dict(allow_status_exceptions=False),
             'exceptions', StatusTimeout(None, None, None, None)),
            ('not-activated', dict(allow_status_exceptions=True),
             'exceptions', None),
        ]
    )
    @mock.patch.object(LparActivateHandler, 'get_status')
    def test_lpar_activate(
            self, get_status_mock,
            initial_status, status_kwargs, act_exp_status, exp_status_exc,
            initial_profile, profile_kwargs, exp_profile, exp_profile_exc):
        """Test Lpar.activate()."""

        # Add a faked LPAR
        faked_lpar = self.add_lpar1()
        faked_lpar.properties['status'] = initial_status
        faked_lpar.properties['next-activation-profile-name'] = initial_profile

        # Add a faked image profile
        self.add_imageprofile1()

        lpar_mgr = self.cpc.lpars
        lpar = lpar_mgr.find(name=faked_lpar.name)

        input_kwargs = dict(status_kwargs, **profile_kwargs)

        exp_excs = []
        if exp_status_exc:
            exp_excs.append(exp_status_exc)
        if exp_profile_exc:
            exp_excs.append(exp_profile_exc)

        get_status_mock.return_value = act_exp_status

        if exp_excs:

            with pytest.raises(Exception) as exc_info:

                # Execute the code to be tested
                lpar.activate(**input_kwargs)

            exc = exc_info.value

            exp_exc_classes = [e.__class__ for e in exp_excs]
            assert isinstance(exc, tuple(exp_exc_classes))

            if isinstance(exc, HTTPError):
                exp_httperror = [e for e in exp_excs
                                 if isinstance(e, HTTPError)][0]
                assert exc.http_status == exp_httperror.http_status
                assert exc.reason == exp_httperror.reason

        else:

            # Execute the code to be tested.
            ret = lpar.activate(**input_kwargs)

            assert ret is None

            lpar.pull_full_properties()

            status = lpar.get_property('status')
            assert status == act_exp_status

            last_profile_name = lpar.get_property(
                'last-used-activation-profile')
            assert last_profile_name == exp_profile

    @pytest.mark.parametrize(
        "initial_status, input_kwargs, act_exp_status, exp_status_exc", [

            ('not-activated', {},  # Verify that force has a default
             'not-activated', HTTPError({'http-status': 500, 'reason': 263})),
            ('not-activated', dict(force=False),
             'not-activated', HTTPError({'http-status': 500, 'reason': 263})),
            ('not-activated', dict(force=True),
             'not-activated', None),

            ('not-operating', dict(force=False),
             'not-activated', None),
            ('not-operating', dict(force=True),
             'not-activated', None),

            ('operating', {},  # Verify that force default is False
             'not-activated', HTTPError({'http-status': 500, 'reason': 263})),
            ('operating', dict(force=False),
             'not-activated', HTTPError({'http-status': 500, 'reason': 263})),
            ('operating', dict(force=True),
             'not-activated', None),

            ('exceptions', dict(force=False),
             'not-activated', None),
            ('exceptions', dict(force=True),
             'not-activated', None),

            ('not-operating', {},
             'exceptions', StatusTimeout(None, None, None, None)),
            ('not-operating', dict(allow_status_exceptions=False),
             'exceptions', StatusTimeout(None, None, None, None)),
            ('not-operating', dict(allow_status_exceptions=True),
             'exceptions', None),
        ]
    )
    @mock.patch.object(LparDeactivateHandler, 'get_status')
    def test_lpar_deactivate(
            self, get_status_mock,
            initial_status, input_kwargs, act_exp_status, exp_status_exc):
        """Test Lpar.deactivate()."""

        # Add a faked LPAR
        faked_lpar = self.add_lpar1()
        faked_lpar.properties['status'] = initial_status

        lpar_mgr = self.cpc.lpars
        lpar = lpar_mgr.find(name=faked_lpar.name)

        get_status_mock.return_value = act_exp_status

        exp_excs = []
        if exp_status_exc:
            exp_excs.append(exp_status_exc)

        if exp_excs:

            with pytest.raises(Exception) as exc_info:

                # Execute the code to be tested
                lpar.deactivate(**input_kwargs)

            exc = exc_info.value

            exp_exc_classes = [e.__class__ for e in exp_excs]
            assert isinstance(exc, tuple(exp_exc_classes))

            if isinstance(exc, HTTPError):
                exp_httperror = [e for e in exp_excs
                                 if isinstance(e, HTTPError)][0]
                assert exc.http_status == exp_httperror.http_status
                assert exc.reason == exp_httperror.reason

        else:

            # Execute the code to be tested.
            ret = lpar.deactivate(**input_kwargs)

            assert ret is None

            lpar.pull_full_properties()

            status = lpar.get_property('status')
            assert status == act_exp_status

    @pytest.mark.parametrize(
        "initial_loadparm, loadparm_kwargs, exp_loadparm, exp_loadparm_exc", [
            (None, {},
             '', None),
            (None, dict(load_parameter='abcd'),
             'abcd', None),
            ('abcd', {},
             'abcd', None),
            ('fooo', dict(load_parameter='abcd'),
             'abcd', None),
        ]
    )
    @pytest.mark.parametrize(
        "initial_loadaddr, loadaddr_kwargs, exp_loadaddr, exp_loadaddr_exc", [
            (None, {},
             None, HTTPError({'http-status': 400, 'reason': 5})),
            (None, dict(load_address='5176'),
             '5176', None),
            ('5176', {},
             '5176', None),
            ('1234', dict(load_address='5176'),
             '5176', None),
        ]
    )
    @pytest.mark.parametrize(
        "initial_status, status_kwargs, act_exp_status, exp_status_exc"
        ", initial_stored_status, exp_stored_status, exp_store_status_exc", [
            ('not-activated', {},
             'operating', HTTPError({'http-status': 409, 'reason': 0}),
             None, None, None),
            ('not-activated', dict(force=False),
             'operating', HTTPError({'http-status': 409, 'reason': 0}),
             None, None, None),
            ('not-activated', dict(force=True),
             'operating', HTTPError({'http-status': 409, 'reason': 0}),
             None, None, None),

            ('not-operating', dict(force=False),
             'operating', None,
             None, None, None),
            ('not-operating', dict(force=True),
             'operating', None,
             None, None, None),

            ('operating', {},
             'operating', HTTPError({'http-status': 500, 'reason': 263}),
             None, None, None),
            ('operating', dict(force=False),
             'operating', HTTPError({'http-status': 500, 'reason': 263}),
             None, None, None),
            ('operating', dict(force=True),
             'operating', None,
             None, None, None),

            ('exceptions', dict(force=False),
             'operating', None,
             None, None, None),
            ('exceptions', dict(force=True),
             'operating', None,
             None, None, None),

            ('not-operating', {},
             'exceptions', StatusTimeout(None, None, None, None),
             None, None, None),
            ('not-operating', dict(allow_status_exceptions=False),
             'exceptions', StatusTimeout(None, None, None, None),
             None, None, None),
            ('not-operating', dict(allow_status_exceptions=True),
             'exceptions', None,
             None, None, None),

            ('not-operating', dict(store_status_indicator=False),
             'operating', None,
             None, None, None),
            ('not-operating', dict(store_status_indicator=True),
             'operating', None,
             None, 'not-operating', None),
        ]
    )
    @pytest.mark.parametrize(
        "initial_memory, memory_kwargs, exp_memory, exp_memory_exc", [
            ('foobar', {},
             '', None),
            ('foobar', dict(clear_indicator=False),
             'foobar', None),
            ('foobar', dict(clear_indicator=True),
             '', None),
        ]
    )
    @mock.patch.object(LparLoadHandler, 'get_status')
    def test_lpar_load(
            self, get_status_mock,
            initial_status, status_kwargs, act_exp_status, exp_status_exc,
            initial_loadaddr, loadaddr_kwargs, exp_loadaddr, exp_loadaddr_exc,
            initial_loadparm, loadparm_kwargs, exp_loadparm, exp_loadparm_exc,
            initial_memory, memory_kwargs, exp_memory, exp_memory_exc,
            initial_stored_status, exp_stored_status, exp_store_status_exc):
        # pylint: disable=unused-argument
        """Test Lpar.load()."""

        # Add a faked LPAR
        faked_lpar = self.add_lpar1()
        faked_lpar.properties['status'] = initial_status
        faked_lpar.properties['last-used-load-address'] = initial_loadaddr
        faked_lpar.properties['last-used-load-parameter'] = initial_loadparm
        faked_lpar.properties['memory'] = initial_memory

        # Add a faked image profile
        self.add_imageprofile1()

        lpar_mgr = self.cpc.lpars
        lpar = lpar_mgr.find(name=faked_lpar.name)

        input_kwargs = dict(status_kwargs, **loadaddr_kwargs)
        input_kwargs.update(**loadparm_kwargs)
        input_kwargs.update(**memory_kwargs)

        exp_excs = []
        if exp_status_exc:
            exp_excs.append(exp_status_exc)
        if exp_loadaddr_exc:
            exp_excs.append(exp_loadaddr_exc)
        if exp_loadparm_exc:
            exp_excs.append(exp_loadparm_exc)
        if exp_memory_exc:
            exp_excs.append(exp_memory_exc)
        if exp_store_status_exc:
            exp_excs.append(exp_store_status_exc)

        get_status_mock.return_value = act_exp_status

        if exp_excs:

            with pytest.raises(Exception) as exc_info:

                # Execute the code to be tested
                lpar.load(**input_kwargs)

            exc = exc_info.value

            exp_exc_classes = [e.__class__ for e in exp_excs]
            assert isinstance(exc, tuple(exp_exc_classes))

            if isinstance(exc, HTTPError):
                exp_httperror = [e for e in exp_excs
                                 if isinstance(e, HTTPError)][0]
                assert exc.http_status == exp_httperror.http_status
                assert exc.reason == exp_httperror.reason

        else:

            # Execute the code to be tested.
            ret = lpar.load(**input_kwargs)

            assert ret is None

            lpar.pull_full_properties()

            status = lpar.get_property('status')
            assert status == act_exp_status

            last_loadaddr = lpar.get_property('last-used-load-address')
            assert last_loadaddr == exp_loadaddr

            last_loadparm = lpar.get_property('last-used-load-parameter')
            assert last_loadparm == exp_loadparm

            last_memory = lpar.get_property('memory')
            assert last_memory == exp_memory

            stored_status = lpar.get_property('stored-status')
            assert stored_status == exp_stored_status

    TESTCASES_SCSI_LOAD = [
        # Testcases for test_lpar_scsi_load()

        # Each testcase is a tuple of:
        # * desc: description
        # * initial_status: Status before scsi_load() is called
        # * result_status: Status to be set by scsi_load()
        # * input_kwargs: Keyword arguments to scsi_load()
        # * exp_properties: Props to validate after a successful scsi_load()
        # * exc_exp: Expected exception object, or None

        (
            "Missing input parameter 'load_address'",
            'activated',
            'operating',
            {'wwpn': '1234',
             'lun': '5678'},
            {},
            TypeError()
        ),
        (
            "Missing input parameter 'wwpn'",
            'activated',
            'operating',
            {'load_address': '0010A',
             'lun': '5678'},
            {},
            TypeError()
        ),
        (
            "Missing input parameter 'lun'",
            'activated',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234'},
            {},
            TypeError()
        ),
        (
            "Minimally required input parameters, test defaults for optional",
            'activated',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678'},
            {'status': 'operating',
             'last-used-load-address': '0010A',
             'last-used-load-parameter': '',
             'last-used-world-wide-port-name': '1234',
             'last-used-logical-unit-number': '5678',
             'last-used-disk-partition-id': 0,
             'last-used-operating-system-specific-load-parameters': '',
             'last-used-boot-record-logical-block-address': '0',
             'last-used-load-type': 'ipltype-scsi',
             'last-used-secure-boot': False,
             'last-used-clear-indicator': True},
            None
        ),
        (
            "All input parameters for last-used props",
            'activated',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678',
             'load_parameter': 'foo_lp',
             'disk_partition_id': 42,
             'operating_system_specific_load_parameters': 'foo_oslp',
             'boot_record_logical_block_address': '42',
             'secure_boot': True,
             'clear_indicator': False},
            {'status': 'operating',
             'last-used-load-address': '0010A',
             'last-used-load-parameter': 'foo_lp',
             'last-used-world-wide-port-name': '1234',
             'last-used-logical-unit-number': '5678',
             'last-used-disk-partition-id': 42,
             'last-used-operating-system-specific-load-parameters': 'foo_oslp',
             'last-used-boot-record-logical-block-address': '42',
             'last-used-load-type': 'ipltype-scsi',
             'last-used-secure-boot': True,
             'last-used-clear-indicator': False},
            None
        ),
        (
            "Incorrect initial status 'not-activated'",
            'not-activated',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678'},
            {},
            HTTPError({'http-status': 409, 'reason': 0})
        ),
        (
            "Initial status 'operating', testing default for 'force'",
            'operating',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678'},
            {},
            HTTPError({'http-status': 500, 'reason': 263})  # TODO: Check
        ),
        (
            "Initial status 'operating', 'force' is False",
            'operating',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678',
             'force': False},
            {},
            HTTPError({'http-status': 500, 'reason': 263})  # TODO: Check
        ),
        (
            "Initial status 'operating', 'force' is True",
            'operating',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678',
             'force': True},
            {'status': 'operating'},
            None
        ),
        (
            "Initial status 'exceptions'",
            'exceptions',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678'},
            {'status': 'operating'},
            None
        ),

    ]

    @pytest.mark.parametrize(
        "desc, initial_status, result_status, input_kwargs, exp_properties, "
        "exc_exp",
        TESTCASES_SCSI_LOAD)
    @mock.patch.object(LparLoadHandler, 'get_status')
    def test_lpar_scsi_load(
            self, get_status_mock,
            desc, initial_status, result_status, input_kwargs, exp_properties,
            exc_exp):
        # pylint: disable=unused-argument
        """Test Lpar.scsi_load()."""

        # Add a faked LPAR and set its properties
        faked_lpar = self.add_lpar1()
        faked_lpar.properties['status'] = initial_status

        # Add a faked image profile
        self.add_imageprofile1()

        lpar_mgr = self.cpc.lpars
        lpar = lpar_mgr.find(name=faked_lpar.name)

        get_status_mock.return_value = result_status

        if exc_exp:

            with pytest.raises(Exception) as exc_info:

                # Execute the code to be tested
                lpar.scsi_load(**input_kwargs)

            exc = exc_info.value

            assert isinstance(exc, exc_exp.__class__)
            if isinstance(exc, HTTPError):
                assert exc.http_status == exc_exp.http_status
                assert exc.reason == exc_exp.reason

        else:

            # Execute the code to be tested.
            ret = lpar.scsi_load(**input_kwargs)

            # TODO: Job result not implemented yet
            assert ret is None

            lpar.pull_full_properties()

            for pname, exp_value in exp_properties.items():
                act_value = lpar.get_property(pname)
                assert act_value == exp_value, \
                    f"Unexpected value for property {pname!r}: " \
                    f"got {act_value!r}, expected {exp_value!r}"

    TESTCASES_SCSI_DUMP = [
        # Testcases for test_lpar_scsi_dump()

        # Each testcase is a tuple of:
        # * desc: description
        # * initial_status: Status before scsi_dump() is called
        # * result_status: Status to be set by scsi_dump()
        # * input_kwargs: Keyword arguments to scsi_dump()
        # * exp_properties: Props to validate after a successful scsi_dump()
        # * exc_exp: Expected exception object, or None

        (
            "Missing input parameter 'load_address'",
            'activated',
            'operating',
            {'wwpn': '1234',
             'lun': '5678'},
            {},
            TypeError()
        ),
        (
            "Missing input parameter 'wwpn'",
            'activated',
            'operating',
            {'load_address': '0010A',
             'lun': '5678'},
            {},
            TypeError()
        ),
        (
            "Missing input parameter 'lun'",
            'activated',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234'},
            {},
            TypeError()
        ),
        (
            "Minimally required input parameters, test defaults for optional",
            'activated',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678'},
            {'status': 'operating',
             'last-used-load-address': '0010A',
             'last-used-load-parameter': '',
             'last-used-world-wide-port-name': '1234',
             'last-used-logical-unit-number': '5678',
             'last-used-disk-partition-id': 0,
             'last-used-operating-system-specific-load-parameters': '',
             'last-used-boot-record-logical-block-address': '0',
             'last-used-load-type': 'ipltype-scsidump',
             'last-used-secure-boot': False,
             'last-used-clear-indicator': True},
            None
        ),
        (
            "All input parameters for last-used props",
            'activated',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678',
             'load_parameter': 'foo_lp',
             'disk_partition_id': 42,
             'operating_system_specific_load_parameters': 'foo_oslp',
             'boot_record_logical_block_address': '42',
             'secure_boot': True},
            {'status': 'operating',
             'last-used-load-address': '0010A',
             'last-used-load-parameter': 'foo_lp',
             'last-used-world-wide-port-name': '1234',
             'last-used-logical-unit-number': '5678',
             'last-used-disk-partition-id': 42,
             'last-used-operating-system-specific-load-parameters': 'foo_oslp',
             'last-used-boot-record-logical-block-address': '42',
             'last-used-load-type': 'ipltype-scsidump',
             'last-used-secure-boot': True},
            None
        ),
        (
            "Incorrect initial status 'not-activated'",
            'not-activated',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678'},
            {},
            HTTPError({'http-status': 409, 'reason': 0})
        ),
        (
            "Initial status 'operating', testing default for 'force'",
            'operating',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678'},
            {},
            HTTPError({'http-status': 500, 'reason': 263})  # TODO: Check
        ),
        (
            "Initial status 'operating', 'force' is False",
            'operating',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678',
             'force': False},
            {},
            HTTPError({'http-status': 500, 'reason': 263})  # TODO: Check
        ),
        (
            "Initial status 'operating', 'force' is True",
            'operating',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678',
             'force': True},
            {'status': 'operating'},
            None
        ),
        (
            "Initial status 'exceptions'",
            'exceptions',
            'operating',
            {'load_address': '0010A',
             'wwpn': '1234',
             'lun': '5678'},
            {'status': 'operating'},
            None
        ),

    ]

    @pytest.mark.parametrize(
        "desc, initial_status, result_status, input_kwargs, exp_properties, "
        "exc_exp",
        TESTCASES_SCSI_DUMP)
    @mock.patch.object(LparLoadHandler, 'get_status')
    def test_lpar_scsi_dump(
            self, get_status_mock,
            desc, initial_status, result_status, input_kwargs, exp_properties,
            exc_exp):
        # pylint: disable=unused-argument
        """Test Lpar.scsi_dump())."""

        # Add a faked LPAR and set its properties
        faked_lpar = self.add_lpar1()
        faked_lpar.properties['status'] = initial_status

        # Add a faked image profile
        self.add_imageprofile1()

        lpar_mgr = self.cpc.lpars
        lpar = lpar_mgr.find(name=faked_lpar.name)

        get_status_mock.return_value = result_status

        if exc_exp:

            with pytest.raises(Exception) as exc_info:

                # Execute the code to be tested
                lpar.scsi_dump(**input_kwargs)

            exc = exc_info.value

            assert isinstance(exc, exc_exp.__class__)
            if isinstance(exc, HTTPError):
                assert exc.http_status == exc_exp.http_status
                assert exc.reason == exc_exp.reason

        else:

            # Execute the code to be tested.
            ret = lpar.scsi_dump(**input_kwargs)

            # TODO: Job result not implemented yet
            assert ret is None

            lpar.pull_full_properties()

            for pname, exp_value in exp_properties.items():
                act_value = lpar.get_property(pname)
                assert act_value == exp_value, \
                    f"Unexpected value for property {pname!r}: " \
                    f"got {act_value!r}, expected {exp_value!r}"

    TESTCASES_NVME_LOAD = [
        # Testcases for test_lpar_nvme_load()

        # Each testcase is a tuple of:
        # * desc: description
        # * initial_status: Status before nvme_load() is called
        # * result_status: Status to be set by nvme_load()
        # * input_kwargs: Keyword arguments to nvme_load()
        # * exp_properties: Props to validate after a successful nvme_load()
        # * exc_exp: Expected exception object, or None

        (
            "Missing input parameter 'load_address'",
            'activated',
            'operating',
            {},
            {},
            TypeError()
        ),
        (
            "Minimally required input parameters, test defaults for optional",
            'activated',
            'operating',
            {'load_address': '0010A'},
            {'status': 'operating',
             'last-used-load-address': '0010A',
             'last-used-load-parameter': '',
             'last-used-disk-partition-id': 0,
             'last-used-operating-system-specific-load-parameters': '',
             'last-used-boot-record-logical-block-address': '0',
             'last-used-load-type': 'ipltype-nvme',
             'last-used-secure-boot': False,
             'last-used-clear-indicator': True},
            None
        ),
        (
            "All input parameters for last-used props",
            'activated',
            'operating',
            {'load_address': '0010A',
             'load_parameter': 'foo_lp',
             'disk_partition_id': 42,
             'operating_system_specific_load_parameters': 'foo_oslp',
             'boot_record_logical_block_address': '42',
             'secure_boot': True,
             'clear_indicator': False},
            {'status': 'operating',
             'last-used-load-address': '0010A',
             'last-used-load-parameter': 'foo_lp',
             'last-used-disk-partition-id': 42,
             'last-used-operating-system-specific-load-parameters': 'foo_oslp',
             'last-used-boot-record-logical-block-address': '42',
             'last-used-load-type': 'ipltype-nvme',
             'last-used-secure-boot': True,
             'last-used-clear-indicator': False},
            None
        ),
        (
            "Incorrect initial status 'not-activated'",
            'not-activated',
            'operating',
            {'load_address': '0010A'},
            {},
            HTTPError({'http-status': 409, 'reason': 0})
        ),
        (
            "Initial status 'operating', testing default for 'force'",
            'operating',
            'operating',
            {'load_address': '0010A'},
            {},
            HTTPError({'http-status': 500, 'reason': 263})  # TODO: Check
        ),
        (
            "Initial status 'operating', 'force' is False",
            'operating',
            'operating',
            {'load_address': '0010A',
             'force': False},
            {},
            HTTPError({'http-status': 500, 'reason': 263})  # TODO: Check
        ),
        (
            "Initial status 'operating', 'force' is True",
            'operating',
            'operating',
            {'load_address': '0010A',
             'force': True},
            {'status': 'operating'},
            None
        ),
        (
            "Initial status 'exceptions'",
            'exceptions',
            'operating',
            {'load_address': '0010A'},
            {'status': 'operating'},
            None
        ),

    ]

    @pytest.mark.parametrize(
        "desc, initial_status, result_status, input_kwargs, exp_properties, "
        "exc_exp",
        TESTCASES_NVME_LOAD)
    @mock.patch.object(LparLoadHandler, 'get_status')
    def test_lpar_nvme_load(
            self, get_status_mock,
            desc, initial_status, result_status, input_kwargs, exp_properties,
            exc_exp):
        # pylint: disable=unused-argument
        """Test Lpar.nvme_load()."""

        # Add a faked LPAR and set its properties
        faked_lpar = self.add_lpar1()
        faked_lpar.properties['status'] = initial_status

        # Add a faked image profile
        self.add_imageprofile1()

        lpar_mgr = self.cpc.lpars
        lpar = lpar_mgr.find(name=faked_lpar.name)

        get_status_mock.return_value = result_status

        if exc_exp:

            with pytest.raises(Exception) as exc_info:

                # Execute the code to be tested
                lpar.nvme_load(**input_kwargs)

            exc = exc_info.value

            assert isinstance(exc, exc_exp.__class__)
            if isinstance(exc, HTTPError):
                assert exc.http_status == exc_exp.http_status
                assert exc.reason == exc_exp.reason

        else:

            # Execute the code to be tested.
            ret = lpar.nvme_load(**input_kwargs)

            # TODO: Job result not implemented yet
            assert ret is None

            lpar.pull_full_properties()

            for pname, exp_value in exp_properties.items():
                act_value = lpar.get_property(pname)
                assert act_value == exp_value, \
                    f"Unexpected value for property {pname!r}: " \
                    f"got {act_value!r}, expected {exp_value!r}"

    TESTCASES_NVME_DUMP = [
        # Testcases for test_lpar_nvme_dump()

        # Each testcase is a tuple of:
        # * desc: description
        # * initial_status: Status before nvme_dump() is called
        # * result_status: Status to be set by nvme_dump()
        # * input_kwargs: Keyword arguments to nvme_dump()
        # * exp_properties: Props to validate after a successful nvme_dump()
        # * exc_exp: Expected exception object, or None

        (
            "Missing input parameter 'load_address'",
            'activated',
            'operating',
            {},
            {},
            TypeError()
        ),
        (
            "Minimally required input parameters, test defaults for optional",
            'activated',
            'operating',
            {'load_address': '0010A'},
            {'status': 'operating',
             'last-used-load-address': '0010A',
             'last-used-load-parameter': '',
             'last-used-disk-partition-id': 0,
             'last-used-operating-system-specific-load-parameters': '',
             'last-used-boot-record-logical-block-address': '0',
             'last-used-load-type': 'ipltype-nvmedump',
             'last-used-secure-boot': False,
             'last-used-clear-indicator': True},
            None
        ),
        (
            "All input parameters for last-used props",
            'activated',
            'operating',
            {'load_address': '0010A',
             'load_parameter': 'foo_lp',
             'disk_partition_id': 42,
             'operating_system_specific_load_parameters': 'foo_oslp',
             'boot_record_logical_block_address': '42',
             'secure_boot': True},
            {'status': 'operating',
             'last-used-load-address': '0010A',
             'last-used-load-parameter': 'foo_lp',
             'last-used-disk-partition-id': 42,
             'last-used-operating-system-specific-load-parameters': 'foo_oslp',
             'last-used-boot-record-logical-block-address': '42',
             'last-used-load-type': 'ipltype-nvmedump',
             'last-used-secure-boot': True},
            None
        ),
        (
            "Incorrect initial status 'not-activated'",
            'not-activated',
            'operating',
            {'load_address': '0010A'},
            {},
            HTTPError({'http-status': 409, 'reason': 0})
        ),
        (
            "Initial status 'operating', testing default for 'force'",
            'operating',
            'operating',
            {'load_address': '0010A'},
            {},
            HTTPError({'http-status': 500, 'reason': 263})  # TODO: Check
        ),
        (
            "Initial status 'operating', 'force' is False",
            'operating',
            'operating',
            {'load_address': '0010A',
             'force': False},
            {},
            HTTPError({'http-status': 500, 'reason': 263})  # TODO: Check
        ),
        (
            "Initial status 'operating', 'force' is True",
            'operating',
            'operating',
            {'load_address': '0010A',
             'force': True},
            {'status': 'operating'},
            None
        ),
        (
            "Initial status 'exceptions'",
            'exceptions',
            'operating',
            {'load_address': '0010A'},
            {'status': 'operating'},
            None
        ),

    ]

    @pytest.mark.parametrize(
        "desc, initial_status, result_status, input_kwargs, exp_properties, "
        "exc_exp",
        TESTCASES_NVME_DUMP)
    @mock.patch.object(LparLoadHandler, 'get_status')
    def test_lpar_nvme_dump(
            self, get_status_mock,
            desc, initial_status, result_status, input_kwargs, exp_properties,
            exc_exp):
        # pylint: disable=unused-argument
        """Test Lpar.nvme_dump())."""

        # Add a faked LPAR and set its properties
        faked_lpar = self.add_lpar1()
        faked_lpar.properties['status'] = initial_status

        # Add a faked image profile
        self.add_imageprofile1()

        lpar_mgr = self.cpc.lpars
        lpar = lpar_mgr.find(name=faked_lpar.name)

        get_status_mock.return_value = result_status

        if exc_exp:

            with pytest.raises(Exception) as exc_info:

                # Execute the code to be tested
                lpar.nvme_dump(**input_kwargs)

            exc = exc_info.value

            assert isinstance(exc, exc_exp.__class__)
            if isinstance(exc, HTTPError):
                assert exc.http_status == exc_exp.http_status
                assert exc.reason == exc_exp.reason

        else:

            # Execute the code to be tested.
            ret = lpar.nvme_dump(**input_kwargs)

            # TODO: Job result not implemented yet
            assert ret is None

            lpar.pull_full_properties()

            for pname, exp_value in exp_properties.items():
                act_value = lpar.get_property(pname)
                assert act_value == exp_value, \
                    f"Unexpected value for property {pname!r}: " \
                    f"got {act_value!r}, expected {exp_value!r}"

    @pytest.mark.parametrize(
        "filter_args, exp_names", [
            ({'cpc-name': 'bad'},
             []),
            ({'cpc-name': CPC_NAME},
             [LPAR1_NAME, LPAR2_NAME]),
            ({},
             [LPAR1_NAME, LPAR2_NAME]),
            (None,
             [LPAR1_NAME, LPAR2_NAME]),
            ({'name': LPAR1_NAME},
             [LPAR1_NAME]),
        ]
    )
    def test_console_list_permitted_lpars(self, filter_args, exp_names):
        """Test Console.list_permitted_lpars() with filter_args."""

        # Add two faked partitions
        self.add_lpar1()
        self.add_lpar2()

        self.session.hmc.consoles.add({
            'object-id': None,
            # object-uri will be automatically set
            'parent': None,
            'class': 'console',
            'name': 'fake-console1',
            'description': 'Console #1',
        })

        console = self.client.consoles.console

        # Execute the code to be tested
        lpars = console.list_permitted_lpars(filter_args=filter_args)

        assert len(lpars) == len(exp_names)
        if exp_names:
            names = [p.properties['name'] for p in lpars]
            assert set(names) == set(exp_names)

        for lpar in lpars:
            lpar_props = dict(lpar.properties)
            for pname in LIST_PERMITTED_LPARS_PROPS:
                assert pname in lpar_props, (
                    f"Property {pname!r} missing from returned LPAR "
                    f"properties, got: {lpar_props!r}")

    @pytest.mark.parametrize(
        "list_kwargs, prop_names", [
            ({},
             LIST_PERMITTED_LPARS_PROPS),
            (dict(additional_properties=[]),
             LIST_PERMITTED_LPARS_PROPS),
            (dict(additional_properties=['description']),
             LIST_PERMITTED_LPARS_PROPS + ['description']),
            (dict(additional_properties=['description', 'activation-mode']),
             LIST_PERMITTED_LPARS_PROPS + ['description', 'activation-mode']),
            (dict(additional_properties=['ssc-host-name']),
             LIST_PERMITTED_LPARS_PROPS + ['ssc-host-name']),
        ]
    )
    def test_console_list_permlpars_add_props(
            self, list_kwargs, prop_names):
        """
        Test Console.list_permitted_lpars() with additional_properties.
        """

        # Add two faked partitions
        faked_lpar1 = self.add_lpar1()
        faked_lpar2 = self.add_lpar2()

        self.session.hmc.consoles.add({
            'object-id': None,
            # object-uri will be automatically set
            'parent': None,
            'class': 'console',
            'name': 'fake-console1',
            'description': 'Console #1',
        })

        console = self.client.consoles.console

        # Execute the code to be tested
        lpars = console.list_permitted_lpars(**list_kwargs)

        exp_faked_lpars = [faked_lpar1, faked_lpar2]

        assert_resources(lpars, exp_faked_lpars, prop_names)


def test_lpar_start(http_mocked_lpar):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test function for Lpar.start()
    """
    session = http_mocked_lpar.manager.session
    uri = http_mocked_lpar.uri + '/operations/start'

    job_uri = '/api/jobs/job-1'

    exp_request_body = None
    exp_status_code = 202
    result_body = {
        'job-uri': job_uri,
    }
    exp_result_job = Job(session, job_uri, 'POST', uri)

    rm_adapter = requests_mock.Adapter(case_sensitive=True)
    with requests_mock.mock(adapter=rm_adapter) as m:

        m.post(uri, status_code=exp_status_code, json=result_body)

        result_job = http_mocked_lpar.start(wait_for_completion=False)

        assert rm_adapter.called
        request_body = rm_adapter.last_request.body
        assert request_body == exp_request_body
        assert result_job.uri == exp_result_job.uri
        assert result_job.op_method == exp_result_job.op_method
        assert result_job.op_uri == exp_result_job.op_uri


def test_lpar_stop(http_mocked_lpar):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test function for Lpar.stop()
    """
    session = http_mocked_lpar.manager.session
    uri = http_mocked_lpar.uri + '/operations/stop'

    job_uri = '/api/jobs/job-1'

    exp_request_body = None
    exp_status_code = 202
    result_body = {
        'job-uri': job_uri,
    }
    exp_result_job = Job(session, job_uri, 'POST', uri)

    rm_adapter = requests_mock.Adapter(case_sensitive=True)
    with requests_mock.mock(adapter=rm_adapter) as m:

        m.post(uri, status_code=exp_status_code, json=result_body)

        result_job = http_mocked_lpar.stop(wait_for_completion=False)

        assert rm_adapter.called
        request_body = rm_adapter.last_request.body
        assert request_body == exp_request_body
        assert result_job.uri == exp_result_job.uri
        assert result_job.op_method == exp_result_job.op_method
        assert result_job.op_uri == exp_result_job.op_uri

    # TODO: Test for Lpar.psw_restart()
    # TODO: Test for Lpar.reset_clear()
    # TODO: Test for Lpar.reset_normal()


def test_lpar_load_from_ftp(http_mocked_lpar):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test function for Lpar.load_from_ftp()
    """
    session = http_mocked_lpar.manager.session
    uri = http_mocked_lpar.uri + '/operations/load-from-ftp'

    # Define the input parameters for the test call
    host = 'test-ftp-host-1'
    username = 'test-user'
    password = 'test-pwd'
    load_file = '/images/load1.img'
    protocol = 'sftp'

    job_uri = '/api/jobs/job-1'

    exp_request_body = {
        'host-name': host,
        'user-name': username,
        'password': password,
        'file-path': load_file,
        'protocol': protocol,
    }
    exp_status_code = 202
    result_body = {
        'job-uri': job_uri,
    }
    exp_result_job = Job(session, job_uri, 'POST', uri)

    rm_adapter = requests_mock.Adapter(case_sensitive=True)
    with requests_mock.mock(adapter=rm_adapter) as m:

        m.post(uri, status_code=exp_status_code, json=result_body)

        result_job = http_mocked_lpar.load_from_ftp(
            host, username, password, load_file, protocol,
            wait_for_completion=False)

        assert rm_adapter.called
        request_body = rm_adapter.last_request.json()
        assert request_body == exp_request_body
        assert result_job.uri == exp_result_job.uri
        assert result_job.op_method == exp_result_job.op_method
        assert result_job.op_uri == exp_result_job.op_uri
