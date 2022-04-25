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

import pytest
from requests.packages import urllib3

# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import classic_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import pick_test_resources, runtest_find_list, skip_warn

urllib3.disable_warnings()

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
                      format(c=cpc.name, h=hd.hmc_host))
        lpar_list = pick_test_resources(lpar_list)

        for lpar in lpar_list:
            print("Testing on CPC {c} with LPAR {p!r}".
                  format(c=cpc.name, p=lpar.name))
            runtest_find_list(
                session, cpc.lpars, lpar.name, 'name', 'status',
                LPAR_VOLATILE_PROPS, LPAR_MINIMAL_PROPS, LPAR_LIST_PROPS)
