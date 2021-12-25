# Copyright 2017-2021 IBM Corp. All Rights Reserved.
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

# pylint: disable=attribute-defined-outside-init

"""
End2end tests for activation profiles in classic mode.

These tests do not change any activation profiles.

Only tested on CPCs in classic mode, and skipped otherwise.
"""

from __future__ import absolute_import, print_function

import pytest
from requests.packages import urllib3

# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.cpc_fixtures import classic_mode_cpcs  # noqa: F401, E501

from .utils import runtest_find_list

urllib3.disable_warnings()

# Properties in minimalistic ActivationProfile objects (e.g. find_by_name())
ACTPROF_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in ActivationProfile objects returned by list() without full props
ACTPROF_LIST_PROPS = ['element-uri', 'name', 'target-name']

# Properties whose values can change between retrievals
ACTPROF_VOLATILE_PROPS = []


@pytest.mark.parametrize(
    "profile_type", ['reset', 'image', 'load']
)
def test_actprof_find_list(classic_mode_cpcs, profile_type):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled
        print("Testing on CPC {} (classic mode)".format(cpc.name))

        session = cpc.manager.session
        actprof_mgr = getattr(cpc, profile_type + '_activation_profiles')

        # Pick an activation profile
        actprof_list = actprof_mgr.list()
        assert len(actprof_list) >= 1
        actprof = actprof_list[-1]  # Pick the last one returned

        runtest_find_list(
            session, actprof_mgr, actprof.name, 'name', 'element-uri',
            ACTPROF_VOLATILE_PROPS, ACTPROF_MINIMAL_PROPS, ACTPROF_LIST_PROPS)
