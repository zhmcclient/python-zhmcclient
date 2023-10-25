# Copyright 2021 IBM Corp. All Rights Reserved.
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
End2end tests for LPARs (on CPCs in DPM mode).

These tests do not change any existing LPARs, but create, modify and delete
test LPARs.
"""

from __future__ import absolute_import, print_function

import random
import pdb
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import classic_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, runtest_find_list, \
    runtest_get_properties, ensure_lpar_inactive, setup_logging

urllib3.disable_warnings()

# Print debug messages in tests
DEBUG = False

# Logging for zhmcclient HMC interactions and test functions
LOGGING = False
LOG_FILE = 'test_lpar.log'

# Properties in minimalistic Lpar objects (e.g. find_by_name())
LPAR_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Lpar objects returned by list() without full props
LPAR_LIST_PROPS = ['object-uri', 'name', 'status']

# Properties whose values can change between retrievals of Lpar objects
LPAR_VOLATILE_PROPS = []


def test_lpar_find_list(classic_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the LPARs to test with
        lpar_list = cpc.lpars.list()
        if not lpar_list:
            skip_warn("No LPARs on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))
        lpar_list = pick_test_resources(lpar_list)

        for lpar in lpar_list:
            print("Testing on CPC {c} with LPAR {p!r}".
                  format(c=cpc.name, p=lpar.name))
            runtest_find_list(
                session, cpc.lpars, lpar.name, 'name', 'status',
                LPAR_VOLATILE_PROPS, LPAR_MINIMAL_PROPS, LPAR_LIST_PROPS)


def test_lpar_property(classic_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        client = cpc.manager.client
        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the LPARs to test with
        lpar_list = cpc.lpars.list()
        if not lpar_list:
            skip_warn("No LPARs on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))
        lpar_list = pick_test_resources(lpar_list)

        for lpar in lpar_list:
            print("Testing on CPC {c} with LPAR {p!r}".
                  format(c=cpc.name, p=lpar.name))

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(client, lpar.manager, non_list_prop, (2, 14))


def test_lpar_list_os_messages(classic_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test "List OS Messages" operation on LPARs
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        if hd.mock_file:
            skip_warn("zhmcclient mock does not support 'List OS Messages' "
                      "operation")

        # Pick the LPAR to test with
        lpar_list = cpc.lpars.list()
        if not lpar_list:
            skip_warn("No LPARs on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))

        test_lpar = None
        for lpar in lpar_list:

            # Test: List all messages (without begin or end)
            try:
                if DEBUG:
                    print("Debug: Test: Listing OS messages of LPAR {} "
                          "with no begin/end".format(lpar.name))
                result = lpar.list_os_messages()
            except zhmcclient.HTTPError as exc:
                if exc.http_status == 409 and exc.reason == 332:
                    # Meaning: The messages interface for the LPAR is not
                    # available
                    if DEBUG:
                        print("Debug: LPAR {} cannot list OS messages".
                              format(lpar.name))
                    continue
                raise

            all_messages = result['os-messages']
            if len(all_messages) >= 3:
                test_lpar = lpar
                break

            if DEBUG:
                print("Debug: LPAR {} has only {} OS messages".
                      format(lpar.name, len(all_messages)))

        if test_lpar is None:
            skip_warn("No LPAR on CPC {c} has the minimum number of 3 OS "
                      "messages for the test".format(c=cpc.name))

        # Test with begin/end selecting the full set of messages
        all_begin = all_messages[0]['sequence-number']
        all_end = all_messages[-1]['sequence-number']
        if DEBUG:
            print("Debug: Test: Listing OS messages of LPAR {} with "
                  "begin={}, end={}".format(test_lpar.name, all_begin, all_end))
        result = test_lpar.list_os_messages(begin=all_begin, end=all_end)
        messages = result['os-messages']
        assert len(messages) == all_end - all_begin + 1
        assert messages == all_messages

        # Test with begin/end selecting a subset of messages
        while True:
            seq1 = random.choice(all_messages)['sequence-number']
            if seq1 not in {all_begin, all_end}:
                break
        while True:
            seq2 = random.choice(all_messages)['sequence-number']
            if seq2 not in {all_begin, all_end, seq1}:
                break
        begin = min(seq1, seq2)
        end = max(seq1, seq2)
        if DEBUG:
            print("Debug: Test: Listing OS messages of LPAR {} with "
                  "begin={}, end={}".format(test_lpar.name, begin, end))
        result = test_lpar.list_os_messages(begin=begin, end=end)
        messages = result['os-messages']
        assert len(messages) == end - begin + 1
        for message in messages:
            assert message in all_messages

        # Test with begin/end and maximum messages
        max_messages = random.randint(0, end - begin + 1)
        if DEBUG:
            print("Debug: Test: Listing OS messages of LPAR {} with "
                  "begin={}, end={}, max_messages={}".
                  format(test_lpar.name, begin, end, max_messages))
        result = test_lpar.list_os_messages(
            begin=begin, end=end, max_messages=max_messages)
        messages = result['os-messages']
        assert len(messages) == max_messages
        for message in messages:
            assert message in all_messages

        # Test with is_held
        for is_held in (False, True):
            if DEBUG:
                print("Debug: Test: Listing OS messages of LPAR {} with "
                      "is_held={}".format(test_lpar.name, is_held))
            result = test_lpar.list_os_messages(is_held=is_held)
            messages = result['os-messages']
            for message in messages:
                assert message['is-held'] == is_held

        # Test with is_priority
        for is_priority in (False, True):
            if DEBUG:
                print("Debug: Test: Listing OS messages of LPAR {} with "
                      "is_priority={}".format(test_lpar.name, is_priority))
            result = test_lpar.list_os_messages(is_priority=is_priority)
            messages = result['os-messages']
            for message in messages:
                assert message['is-priority'] == is_priority


# Test LPARs for test_lpar_activate().
# The outer dict is for different types of LPARs:
#   Key: LPAR kind, Value: Dict of LPAR names by CPC
ACTIVATE_TEST_LPARS = {
    'linux-no-autoload': {
        # Linux LPAR whose next profile does not auto-load
        'P0000M96': 'LINUX28',
        'T28': 'BLUEC1',
    },
    'linux-with-autoload': {
        # Linux LPAR whose next profile auto-loads, and which boots an OS
        'P0000M96': 'HISOCKE1',
        # 'T28': 'BCORE2',  # fails with HTTP 500,263: The load failed.
    },
    'ssc': {
        # SSC LPAR (which always auto-loads), and which boots the SSC installer
        # or an SSC appliance
        'P0000M96': 'ANGEL',
        'T28': 'BCORE1',
    },
}

# Test image profiles for test_lpar_activate().
# The outer dict is for different types of image profiles:
#   Key: LPAR kind, Value: Dict of image profile names by CPC
ACTIVATE_TEST_PROFILES = {
    'linux-no-autoload': {
        # Linux profile that does not auto-load
        'P0000M96': 'LINUX28',
        'T28': 'BLUEC1',
    },
    'linux-with-autoload': {
        # Linux profile that does auto-load and specifies a bootable OS
        'P0000M96': 'HISOCKE1',
        'T28': 'BCORE2',
    },
    'ssc': {
        # SSC profile (which always auto-loads), that specifies a bootable
        # SSC image (installer or appliance)
        'P0000M96': 'ANGEL',
        'T28': 'BCORE1',
    },
}

LPAR_ACTIVATE_TESTCASES = [
    # Testcases for test_lpar_activate().
    # The list items are tuples with the following items:
    # - desc (string): description of the testcase.
    # - lpar_kind (string): LPAR kind to be used (from ACTIVATE_TEST_LPARS).
    # - profile_kind (string): Image profile kind to be used (from
    #   ACTIVATE_TEST_PROFILES). None means to use default (next profile).
    # - input_kwargs (dict): Input parameters for Lpar.activate() in addition
    #   to activation_profile_name.
    # - exp_props (dict): Dict of expected properties of the Lpar after
    #   calling Lpar.activate().
    # - exp_exc_type (class): Expected exception type, or None for success.
    # - run (bool or 'pdb'): Whether to run the test or call the debugger.

    (
        "Linux LPAR whose same-named profile is w/o auto-load, default parms",
        'linux-no-autoload',
        None,
        dict(),
        {
            'status': 'not-operating',
        },
        None,
        True,
    ),
    (
        "Linux LPAR whose same-named profile is with auto-load, default parms",
        'linux-with-autoload',
        None,
        dict(),
        {
            'status': 'operating',
        },
        None,
        True,
    ),
    (
        "SSC LPAR (always auto-loads), default parms",
        'ssc',
        None,
        dict(),
        {
            'status': 'operating',
        },
        None,
        True,
    ),
    (
        "Linux LPAR, different image profile name than LPAR name specified",
        'linux-no-autoload',
        'linux-with-autoload',
        dict(),
        None,
        # HTTP 500,263: LPAR name and image profile name must match
        zhmcclient.HTTPError,
        True,
    ),
]


@pytest.mark.parametrize(
    "desc, lpar_kind, profile_kind, input_kwargs, exp_props, exp_exc_type, run",
    LPAR_ACTIVATE_TESTCASES)
def test_lpar_activate(
        desc, lpar_kind, profile_kind, input_kwargs, exp_props, exp_exc_type,
        run, classic_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name, unused-argument
    """
    Test Lpar.activate().
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    if not run:
        skip_warn("Testcase is disabled in testcase definition")

    logger = setup_logging(LOGGING, 'test_lpar_activate', LOG_FILE)

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        test_lpars = ACTIVATE_TEST_LPARS[lpar_kind]
        try:
            lpar_name = test_lpars[cpc.name]
        except KeyError:
            pytest.skip("CPC {c} does not have a definition in the "
                        "ACTIVATE_TEST_LPARS: {tl}".
                        format(c=cpc.name, tl=test_lpars))

        if profile_kind:
            test_profiles = ACTIVATE_TEST_PROFILES[profile_kind]
            try:
                profile_name = test_profiles[cpc.name]
            except KeyError:
                pytest.skip("CPC {c} does not have a definition in the "
                            "ACTIVATE_TEST_PROFILES: {tp}".
                            format(c=cpc.name, tp=test_profiles))
        else:
            profile_name = None

        try:
            lpar = cpc.lpars.find(name=lpar_name)
        except zhmcclient.NotFound:
            pytest.skip("LPAR {p!r} does not exist on CPC {c}.".
                        format(c=cpc.name, p=lpar_name))

        msg = ("Testing on CPC {c} with LPAR {p!r}".
               format(c=cpc.name, p=lpar.name))
        print(msg)
        logger.info(msg)

        if run == 'pdb':
            # pylint: disable=forgotten-debug-statement
            pdb.set_trace()

        logger.info("Preparation: Ensuring that LPAR %r is inactive",
                    lpar.name)
        ensure_lpar_inactive(lpar)

        try:
            next_profile = lpar.get_property('next-activation-profile-name')
            logger.info("Test: Activating LPAR %r (next profile: %r, "
                        "profile arg: %r, add. args: %r)",
                        lpar.name, next_profile, profile_name, input_kwargs)

            if exp_exc_type:

                with pytest.raises(exp_exc_type):

                    # Exercise the code to be tested
                    lpar.activate(
                        activation_profile_name=profile_name, **input_kwargs)

            else:

                # Exercise the code to be tested
                lpar.activate(
                    activation_profile_name=profile_name, **input_kwargs)

                # In case of an image profile with auto-load, the activate()
                # method returns already when status 'non-operating' is reached.
                # However, we want to see that the LPAR actually gets to
                # status 'operating' when auto-load is set. So we need to
                # wait for the desired state to cover for that case.
                exp_status = exp_props['status']
                if exp_status == 'operating':
                    logger.info("Waiting for status of LPAR %r to become %r "
                                "after test",
                                lpar.name, exp_status)
                    lpar.wait_for_status(exp_status, status_timeout=60)

                # Check the expected properties
                lpar.pull_full_properties()
                lpar_props = dict(lpar.properties)
                logger.info("Status of LPAR %r is %r after test",
                            lpar.name, lpar_props['status'])
                for pname, exp_value in exp_props.items():
                    assert pname in lpar_props, (
                        "Expected property {p!r} does not exist in "
                        "actual properties of LPAR {ln!r}".
                        format(p=pname, ln=lpar.name))
                    act_value = lpar_props[pname]
                    assert act_value == exp_value, (
                        "Property {p!r} has unexpected value {av!r}; "
                        "expected value: {ev!r}".
                        format(p=pname, av=act_value, ev=exp_value))
        finally:
            logger.info("Cleanup: Ensuring that LPAR %r is inactive",
                        lpar.name)
            ensure_lpar_inactive(lpar)
