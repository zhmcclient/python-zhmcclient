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
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import classic_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, runtest_find_list, \
    runtest_get_properties

urllib3.disable_warnings()

# Print debug messages in tests
DEBUG = False

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
