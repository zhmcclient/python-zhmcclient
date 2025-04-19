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
End2end tests for hw_messages.

These tests do not delete any existing hardware messages.
"""


import random
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import runtest_find_list, skip_warn, pick_test_resources

urllib3.disable_warnings()

# Properties in minimalistic objects (e.g. find_by_name())
HW_MESSAGE_MINIMAL_PROPS = ['element-uri']

# Properties in objects returned by list() without full props
# Note: 'element-id' is added by the list() method.
HW_MESSAGE_LIST_PROPS = ['element-uri', 'element-id', 'text', 'timestamp']

# Properties whose values can change between retrievals of objects
HW_MESSAGE_VOLATILE_PROPS = []


@pytest.mark.parametrize(
    "parent", ['cpc', 'console']
)
def test_hw_message_find_list(hmc_session, parent):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    if parent == 'cpc':
        parent_obj = random.choice(client.cpcs.list())
        parent_str = f"CPC {parent_obj.name!r}"
    else:
        assert parent == 'console'
        parent_obj = console
        parent_str = "Console"

    # Compare items returned by list() with/without full_properties
    hw_message_list = parent_obj.hw_messages.list()
    hw_message_list_full = parent_obj.hw_messages.list(full_properties=True)
    assert len(hw_message_list) == len(hw_message_list_full)
    hw_message_full_by_id = {}
    for hw_message in hw_message_list_full:
        element_id = hw_message.properties['element-id']
        hw_message_full_by_id[element_id] = hw_message
    for hw_message in hw_message_list:
        element_id = hw_message.properties['element-id']
        assert element_id in hw_message_full_by_id
        hw_message_full = hw_message_full_by_id[element_id]
        for prop_name in HW_MESSAGE_LIST_PROPS:
            assert prop_name in hw_message.properties, (
                f"Property {prop_name!r} not found in hardware-message "
                f"object {element_id!r} returned by list()")
            assert prop_name in hw_message_full.properties, (
                f"Property {prop_name!r} not found in hardware-message "
                f"object {element_id!r} returned by list(full_properties=True)")

    # Pick the hw_messages to test with
    if not hw_message_list:
        skip_warn(f"No hardware messages for {parent_str} on HMC {hd.host}")
    hw_message_list = pick_test_resources(hw_message_list)

    for hw_message in hw_message_list:
        element_id = hw_message.properties['element-id']
        print(f"Testing with hardware message {element_id!r} on {parent_str}")
        runtest_find_list(
            hmc_session, parent_obj.hw_messages, element_id, 'element-id',
            'timestamp', HW_MESSAGE_VOLATILE_PROPS, HW_MESSAGE_MINIMAL_PROPS,
            HW_MESSAGE_LIST_PROPS)
