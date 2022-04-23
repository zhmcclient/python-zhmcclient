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
End2end tests for virtual switches (on CPCs in DPM mode).

These tests do not change any existing virtual switches.
"""

from __future__ import absolute_import, print_function

import warnings
import pytest
from requests.packages import urllib3

# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import pick_test_resources, runtest_find_list, End2endTestWarning

urllib3.disable_warnings()

# Properties in minimalistic Task objects (e.g. find_by_name())
VSWITCH_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Task objects returned by list() without full props
VSWITCH_LIST_PROPS = ['object-uri', 'name', 'type']

# Properties whose values can change between retrievals of Task objects
VSWITCH_VOLATILE_PROPS = []


def test_vswitch_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        session = cpc.manager.session

        # Pick the virtual switches to test with
        vswitch_list = cpc.virtual_switches.list()
        if not vswitch_list:
            msg_txt = "No virtual switches (= no network adapters) on CPC {}". \
                format(cpc.name)
            warnings.warn(msg_txt, End2endTestWarning)
            pytest.skip(msg_txt)
        vswitch_list = pick_test_resources(vswitch_list)

        for vswitch in vswitch_list:
            print("Testing on CPC {} with virtual switch {}".
                  format(cpc.name, vswitch.name))
            runtest_find_list(
                session, cpc.virtual_switches, vswitch.name, 'name',
                'description', VSWITCH_VOLATILE_PROPS, VSWITCH_MINIMAL_PROPS,
                VSWITCH_LIST_PROPS)
