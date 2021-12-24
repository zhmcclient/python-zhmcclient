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

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.cpc_fixtures import classic_mode_cpcs  # noqa: F401, E501

urllib3.disable_warnings()


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
        print("Testing CPC {} (classic mode)".format(cpc.name))

        ap_mgr_attr = profile_type + '_activation_profiles'
        ap_class = profile_type + '-activation-profile'

        ap_mgr = getattr(cpc, ap_mgr_attr)

        # Test listing activation profiles

        ap_list = ap_mgr.list()

        assert len(ap_list) >= 1
        for ap in ap_list:
            assert isinstance(ap, zhmcclient.ActivationProfile)

        # Pick the last one returned
        ap = ap_list[-1]
        ap_name = ap.name

        # Test finding the activation profile based on its (cached) name

        ap_found = ap_mgr.find(name=ap_name)

        assert ap_found.name == ap_name

        # There are no other server-side filtered props besides name

        # Test finding the partition based on a client-side filtered prop

        aps_found = ap_mgr.findall(**{'class': ap_class})

        assert ap_name in [ap.name for ap in aps_found]  # noqa: F812
