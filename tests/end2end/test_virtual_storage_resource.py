# Copyright 2024 IBM Corp. All Rights Reserved.
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
End2end tests for virtual storage resources (VSRs) (on CPCs in DPM mode).

These tests do not change any existing VSRs.
"""


import pytest
from requests.packages import urllib3

# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, \
    skipif_no_storage_mgmt_feature, runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic VirtualStorageResource objects
# (e.g. find_by_name())
VSR_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in VirtualStorageResource objects returned by list() without full
# props
VSR_LIST_PROPS = ['element-uri', 'name', 'device-number', 'adapter-port-uri',
                  'partition-uri']

# Properties whose values can change between retrievals of
# VirtualStorageResource objs
VSR_VOLATILE_PROPS = []


def test_vsr_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_storage_mgmt_feature(cpc)

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the VSRs to test with
        grp_vol_tuples = []
        stogrp_list = cpc.list_associated_storage_groups(
            filter_args={type: 'fcp'})
        for stogrp in stogrp_list:
            vsr_list = stogrp.virtual_storage_resources.list()
            for vsr in vsr_list:
                grp_vol_tuples.append((stogrp, vsr))
        if not grp_vol_tuples:
            skip_warn("No storage groups with VSRs associated to CPC "
                      f"{cpc.name} managed by HMC {hd.host}")
        grp_vol_tuples = pick_test_resources(grp_vol_tuples)

        for stogrp, vsr in grp_vol_tuples:
            print(f"Testing on CPC {cpc.name} with VSR "
                  f"{vsr.name!r} of storage group {stogrp.name!r}")
            runtest_find_list(
                session, stogrp.virtual_storage_resources, vsr.name, 'name',
                'description',
                VSR_VOLATILE_PROPS, VSR_MINIMAL_PROPS, VSR_LIST_PROPS,
                unique_name=True)


def test_vsr_property(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_storage_mgmt_feature(cpc)

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the VSRs to test with
        grp_vol_tuples = []
        stogrp_list = cpc.list_associated_storage_groups(
            filter_args={type: 'fcp'})
        for stogrp in stogrp_list:
            vsr_list = stogrp.virtual_storage_resources.list()
            for vsr in vsr_list:
                grp_vol_tuples.append((stogrp, vsr))
        if not grp_vol_tuples:
            skip_warn("No storage groups with VSRs associated to CPC "
                      f"{cpc.name} managed by HMC {hd.host}")
        grp_vol_tuples = pick_test_resources(grp_vol_tuples)

        for stogrp, vsr in grp_vol_tuples:
            print(f"Testing on CPC {cpc.name} with VSR "
                  f"{vsr.name!r} of storage group {stogrp.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(vsr.manager, non_list_prop)
