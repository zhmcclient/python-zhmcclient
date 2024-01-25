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
    runtest_get_properties, ensure_lpar_inactive, set_resource_property, \
    setup_logging

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

# Properties returned by default from list_permitted_lpars()
LPAR_LIST_PERMITTED_PROPS = [
    'name', 'object-uri', 'activation-mode', 'status',
    'has-unacceptable-status', 'cpc-name', 'cpc-object-uri',
    # HMCs return 'se-version' on HMC API version 4.10 or higher
]


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


TESTCASES_CONSOLE_LIST_PERMITTED_LPARS = [
    # Testcases for test_console_list_permitted_lpars()

    # Each testcase is a tuple of:
    # * desc: description
    # * input_kwargs: Keyword arguments to the test function
    # * exp_prop_names: List of expected property names
    (
        "Default arguments",
        {},
        LPAR_LIST_PERMITTED_PROPS,
    ),
    (
        "Explicit defaults for arguments",
        {
            'full_properties': False,
            'filter_args': None,
            'additional_properties': None
        },
        LPAR_LIST_PERMITTED_PROPS,
    ),
    (
        "One server-side filter",
        {
            'filter_args': {'status': 'not-operating'},
        },
        LPAR_LIST_PERMITTED_PROPS,
    ),
    (
        "One client-side filter that is not in result",
        {
            'filter_args': {'has-operating-system-messages': False},
        },
        LPAR_LIST_PERMITTED_PROPS,
    ),
    (
        "Empty additional properties",
        {
            'additional_properties': [],
        },
        LPAR_LIST_PERMITTED_PROPS,
    ),
    (
        "One additional property",
        {
            'additional_properties': ['description'],
        },
        LPAR_LIST_PERMITTED_PROPS + ['description'],
    ),
    (
        "Full properties",
        {
            'full_properties': True,
        },
        LPAR_LIST_PERMITTED_PROPS + ['has-operating-system-messages'],
    ),
]


@pytest.mark.parametrize(
    "desc, input_kwargs, exp_prop_names",
    TESTCASES_CONSOLE_LIST_PERMITTED_LPARS)
def test_console_list_permitted_lpars(
        classic_mode_cpcs, desc, input_kwargs, exp_prop_names):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test Console.list_permitted_lpars() method
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    logger = setup_logging(LOGGING, 'test_console_list_permitted_lpars',
                           LOG_FILE)
    logger.debug("Entered test function with: "
                 "desc=%r, input_kwargs=%r, exp_prop_names=%r",
                 desc, input_kwargs, exp_prop_names)

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        logger.debug("Testing with CPC %s", cpc.name)

        client = cpc.manager.client
        console = client.consoles.console

        logger.debug("Calling list_permitted_lpars() with kwargs: %r",
                     input_kwargs)

        # Execute the code to be tested
        lpars = console.list_permitted_lpars(**input_kwargs)

        logger.debug("list_permitted_lpars() returned %d LPARs", len(lpars))

        for lpar in lpars:
            lpar_props = dict(lpar.properties)
            for pname in exp_prop_names:
                assert pname in lpar_props, (
                    "Property {!r} missing from returned LPAR properties, "
                    "got: {!r}".format(pname, lpar_props))

    logger.debug("Leaving test function")


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


LPAR_ACTIVATE_TESTCASES = [
    # Testcases for test_lpar_activate().
    # The list items are tuples with the following items:
    # - desc (string): description of the testcase.
    # - lpar_mode (string): Activation mode of the LPAR.
    # - ap_type (string): Type of activation profile to be used for
    #   activation_profile_name parm in Lpar.activate(): 'image', 'wrongimage',
    #   'load', None.
    # - nap_type (string): Type of activation profile to be used for
    #   'next-activation-profile-name' prop of LPAR: 'image', 'load'.
    # - auto_load (bool): Value for 'load-at-activation' in image profile.
    # - input_kwargs (dict): Input parameters for Lpar.activate() in addition
    #   to activation_profile_name.
    # - exp_props (dict): Dict of expected properties of the Lpar after
    #   calling Lpar.activate().
    # - exp_exc_type (class): Expected exception type, or None for success.
    # - run (bool or 'pdb'): Whether to run the test or call the debugger.

    (
        "General LPAR w/o auto-load, default parms, next profile is image",
        'general',
        None,
        'image',
        False,
        dict(),
        {
            'status': 'not-operating',
        },
        None,
        True,
    ),
    (
        "General LPAR with auto-load, default parms, next profile is image",
        'general',
        None,
        'image',
        True,
        dict(),
        {
            'status': 'operating',
        },
        None,
        True,
    ),
    (
        "General LPAR w/o auto-load, image profile as parm",
        'general',
        'image',
        'image',
        False,
        dict(),
        {
            'status': 'not-operating',
        },
        None,
        True,
    ),
    (
        "Linux LPAR with auto-load, image profile as parm",
        'linux',
        'image',
        'image',
        True,
        dict(),
        {
            'status': 'operating',
        },
        None,
        True,
    ),

    (
        "Linux LPAR w/o auto-load, default parms, next profile is image",
        'linux',
        None,
        'image',
        False,
        dict(),
        {
            'status': 'not-operating',
        },
        None,
        True,
    ),
    (
        "Linux LPAR with auto-load, default parms, next profile is image",
        'linux',
        None,
        'image',
        True,
        dict(),
        {
            'status': 'operating',
        },
        None,
        True,
    ),
    (
        "Linux LPAR w/o auto-load, image profile as parm",
        'linux',
        'image',
        'image',
        False,
        dict(),
        {
            'status': 'not-operating',
        },
        None,
        True,
    ),
    (
        "Linux LPAR with auto-load, image profile as parm",
        'linux',
        'image',
        'image',
        True,
        dict(),
        {
            'status': 'operating',
        },
        None,
        True,
    ),

    (
        "SSC LPAR (always auto-loads), default parms, next profile is image",
        'ssc',
        None,
        'image',
        False,
        dict(),
        {
            'status': 'operating',
        },
        None,
        True,
    ),
    (
        "SSC LPAR (always auto-loads), image profile as parm",
        'ssc',
        'image',
        'image',
        False,
        dict(),
        {
            'status': 'operating',
        },
        None,
        True,
    ),
    (
        "Linux LPAR, wrong image profile",
        'linux',
        'wrongimage',
        'image',
        False,
        dict(),
        None,
        # HTTP 500,263: LPAR name and image profile name must match
        zhmcclient.HTTPError,
        True,
    ),
    (
        "SSC LPAR, wrong image profile",
        'ssc',
        'wrongimage',
        'image',
        False,
        dict(),
        None,
        # HTTP 500,263: LPAR name and image profile name must match
        zhmcclient.HTTPError,
        True,
    ),

    # TODO: Add testcases with load profiles
]


@pytest.mark.parametrize(
    "desc, lpar_mode, ap_type, nap_type, auto_load, input_kwargs, "
    "exp_props, exp_exc_type, run",
    LPAR_ACTIVATE_TESTCASES)
def test_lpar_activate(
        desc, lpar_mode, ap_type, nap_type, auto_load, input_kwargs, exp_props,
        exp_exc_type, run, classic_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name, unused-argument
    """
    Test Lpar.activate().

    Note: These tests require that the following properties are present in the
    HMC inventory file for the CPC item of the HMC that is tested against:

    * 'loadable_lpars' - The names of LPARs for some operating modes, that
      properly reach the 'operating' status when activated under auto-load
      conditions. If this item is missing, all tests will be skipped.
      If the entries for certain operating modes are missing, the tests
      for these operating modes are skipped.

    * 'load_profiles' - The names of load profiles that can be used to properly
      load the corresponding partitions in 'loadable_lpars'. If this item is
      missing, all tests will be skipped. If the entries for certain operating
      modes are missing, the load-profile related tests for these operating
      modes are skipped.

    Example::

        A01:
          . . .
          cpcs:
            P0000A01:           # <- CPC item of the HMC that is tested against
              machine_type: "3931"
              machine_model: "A01"
              dpm_enabled: false
              loadable_lpars:   # <- specific entry for this test
                general: "LP01"      # key: operating mode, value: LPAR name
                linux-only: "LP02
                ssc: "LP03"
              load_profiles:    # <- specific entry for this test
                general: "LP01LOAD"  # key: op. mode, value: load profile name
                linux-only: "LP02LOAD"
                ssc: "LP03LOAD"

    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    if not run:
        skip_warn("Testcase is disabled in testcase definition")

    logger = setup_logging(LOGGING, 'test_lpar_activate', LOG_FILE)

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        # The following has no check since classic_mode_cpcs only contains
        # CPCs that have such an item:
        hd_cpc = hd.cpcs[cpc.name]

        try:
            loadable_lpars = hd_cpc['loadable_lpars']
        except KeyError:
            pytest.skip("Inventory file entry for HMC nickname {h!r} does not "
                        "have a 'loadable_lpars' property in its entry for "
                        "CPC {c!r}".
                        format(h=hd.nickname, c=cpc.name))
        try:
            load_profiles = hd_cpc['load_profiles']
        except KeyError:
            pytest.skip("Inventory file entry for HMC nickname {h!r} does not "
                        "have a 'load_profiles' property in its entry for "
                        "CPC {c!r}".
                        format(h=hd.nickname, c=cpc.name))

        try:
            lpar_name = loadable_lpars[lpar_mode]
        except (KeyError, TypeError):
            pytest.skip("Inventory file entry for HMC nickname {h!r} does not "
                        "have an entry for operating mode {om!r} in its "
                        "'loadable_lpars' property for CPC {c!r}".
                        format(h=hd.nickname, c=cpc.name, om=lpar_mode))

        # Find the image profile corresponding to the LPAR, and the other
        # (wrong) image profile names for specific tests with that.
        iap_name = lpar_name
        all_iaps = cpc.image_activation_profiles.list()
        lpar_iaps = [_iap for _iap in all_iaps if _iap.name == lpar_name]
        if len(lpar_iaps) >= 1:
            iap = lpar_iaps[0]
        else:
            pytest.skip("Image activation profile {p!r} does not exist on "
                        "CPC {c}.".format(c=cpc.name, p=iap_name))
        wrong_iap_names = [_iap.name for _iap in all_iaps
                           if _iap.name != lpar_name]

        if ap_type == 'image':
            ap_name = lpar_name
        if ap_type == 'wrongimage':
            ap_name = random.choice(wrong_iap_names)
        elif ap_type == 'load':
            try:
                ap_name = load_profiles[lpar_mode]
            except (KeyError, TypeError):
                pytest.skip("Inventory file entry for HMC nickname {h!r} does "
                            "not have an entry for operating mode {om!r} in "
                            "its 'load_profiles' property for CPC {c!r}".
                            format(h=hd.nickname, c=cpc.name, om=lpar_mode))
        else:
            ap_name = None

        if nap_type == 'image':
            nap_name = lpar_name
        elif nap_type == 'load':
            try:
                nap_name = load_profiles[lpar_mode]
            except (KeyError, TypeError):
                pytest.skip("Inventory file entry for HMC nickname {h!r} does "
                            "not have an entry for operating mode {om!r} in "
                            "its 'load_profiles' property for CPC {c!r}".
                            format(h=hd.nickname, c=cpc.name, om=lpar_mode))
        else:
            nap_name = None

        try:
            lpar = cpc.lpars.find(name=lpar_name)
        except zhmcclient.NotFound:
            pytest.skip("LPAR {p!r} does not exist on CPC {c}.".
                        format(c=cpc.name, p=lpar_name))

        if ap_type == 'load' or nap_type == 'load':
            lap_name = load_profiles[lpar_mode]
            try:
                cpc.load_activation_profiles.find(name=lap_name)
            except zhmcclient.NotFound:
                pytest.skip("Load activation profile {p!r} does not exist on "
                            "CPC {c}.".format(c=cpc.name, p=lap_name))

        op_mode = iap.get_property('operating-mode')
        assert op_mode == lpar_mode, (
            "Incorrect testcase definition: Operating mode {om!r} in image "
            "activation profile {p!r} on CPC {c} does not match the "
            "lpar_mode {lm!r} of the testcase".
            format(c=cpc.name, p=iap_name, om=op_mode, lm=lpar_mode))

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

        logger.info("Preparation: Setting 'next-activation-profile-name' = %r "
                    "in LPAR %r", nap_name, lpar.name)
        saved_nap_name = set_resource_property(
            lpar, 'next-activation-profile-name', nap_name)

        logger.info("Preparation: Setting 'load-at-activation' = %r in image "
                    "profile %r", auto_load, iap.name)
        saved_auto_load = set_resource_property(
            iap, 'load-at-activation', auto_load)

        try:
            logger.info("Test: Activating LPAR %r (profile arg: %r, "
                        "add. args: %r)", lpar.name, ap_name, input_kwargs)

            if exp_exc_type:

                with pytest.raises(exp_exc_type):

                    # Exercise the code to be tested
                    lpar.activate(
                        activation_profile_name=ap_name, **input_kwargs)

            else:

                # Exercise the code to be tested
                lpar.activate(
                    activation_profile_name=ap_name, **input_kwargs)

                # In case of an image profile with auto-load, the activate()
                # method waits until status 'operating' is reached. If that
                # cannot be reached, StatusTimeout is raised.

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

            logger.info("Cleanup: Setting 'next-activation-profile-name' = %r "
                        "in LPAR %r", saved_nap_name, lpar.name)
            set_resource_property(
                lpar, 'next-activation-profile-name', saved_nap_name)

            logger.info("Cleanup: Setting 'load-at-activation' = %r in image "
                        "profile %r", saved_auto_load, iap.name)
            set_resource_property(iap, 'load-at-activation', saved_auto_load)
