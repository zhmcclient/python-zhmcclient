# Copyright 2017,2021 IBM Corp. All Rights Reserved.
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
End2end tests for storage groups (on CPCs in DPM mode).

These tests do not change any existing storage groups, but create, modify and
delete test storage groups.
"""


import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    skipif_no_storage_mgmt_feature, runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic StorageGroup objects (e.g. find_by_name())
STOGRP_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in StorageGroup objects returned by list() without full props
STOGRP_LIST_PROPS = ['object-uri', 'cpc-uri', 'name', 'fulfillment-state',
                     'type']

# Properties whose values can change between retrievals of StorageGroup objs
STOGRP_VOLATILE_PROPS = []


def test_stogrp_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_storage_mgmt_feature(cpc)

        console = cpc.manager.client.consoles.console
        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the storage groups to test with
        stogrp_list = cpc.list_associated_storage_groups()
        if not stogrp_list:
            skip_warn(f"No storage groups associated to CPC {cpc.name} "
                      f"managed by HMC {hd.host}")
        stogrp_list = pick_test_resources(stogrp_list)

        for stogrp in stogrp_list:
            print(f"Testing on CPC {cpc.name} with storage group "
                  f"{stogrp.name!r}")
            runtest_find_list(
                session, console.storage_groups, stogrp.name, 'name',
                'object-uri', STOGRP_VOLATILE_PROPS, STOGRP_MINIMAL_PROPS,
                STOGRP_LIST_PROPS)


def test_stogrp_property(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the storage groups to test with
        stogrp_list = cpc.list_associated_storage_groups()
        if not stogrp_list:
            skip_warn(f"No storage groups associated to CPC {cpc.name} "
                      f"managed by HMC {hd.host}")
        stogrp_list = pick_test_resources(stogrp_list)

        for stogrp in stogrp_list:
            print(f"Testing on CPC {cpc.name} with storage group "
                  f"{stogrp.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(stogrp.manager, non_list_prop)


def test_stogrp_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a storage group.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_storage_mgmt_feature(cpc)

        print(f"Testing on CPC {cpc.name}")

        console = cpc.manager.client.consoles.console
        stogrp_name = TEST_PREFIX + ' test_stogrp_crud stogrp1'
        stogrp_name_new = stogrp_name + ' new'

        # Ensure clean starting point
        try:
            stogrp = console.storage_groups.find(name=stogrp_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                f"Deleting test storage group from previous run: "
                f"{stogrp_name!r} on CPC {cpc.name}", UserWarning)
            stogrp.delete()
        try:
            stogrp = console.storage_groups.find(name=stogrp_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test storage group from previous run: "
                f"{stogrp_name_new!r} on CPC {cpc.name}", UserWarning)
            stogrp.delete()

        # Test creating the storage group

        stogrp_input_props = {
            'cpc-uri': cpc.uri,
            'name': stogrp_name,
            'description': 'Test storage group for zhmcclient end2end tests',
            'type': 'fcp',
        }
        stogrp_auto_props = {
            'shared': True,
            'fulfillment-state': 'pending',
        }

        # The code to be tested
        stogrp = console.storage_groups.create(stogrp_input_props)

        for pn, exp_value in stogrp_input_props.items():
            assert stogrp.properties[pn] == exp_value, (
                f"Unexpected value for property {pn!r} of storage group:\n"
                f"{stogrp.properties!r}")
        stogrp.pull_full_properties()
        for pn, exp_value in stogrp_input_props.items():
            assert stogrp.properties[pn] == exp_value, (
                f"Unexpected value for property {pn!r} of storage group:\n"
                f"{stogrp.properties!r}")
        for pn, exp_value in stogrp_auto_props.items():
            assert pn in stogrp.properties, (
                f"Automatically returned property {pn!r} is not in "
                f"created storage group:\n{stogrp!r}")
            assert stogrp.properties[pn] == exp_value, (
                f"Unexpected value for property {pn!r} of storage group:\n"
                f"{stogrp.properties!r}")

        # Test updating a property of the storage group

        new_desc = "Updated storage group description."

        # The code to be tested
        stogrp.update_properties(dict(description=new_desc))

        assert stogrp.properties['description'] == new_desc
        stogrp.pull_full_properties()
        assert stogrp.properties['description'] == new_desc

        # Test renaming the storage group

        # The code to be tested
        stogrp.update_properties(dict(name=stogrp_name_new))

        assert stogrp.properties['name'] == stogrp_name_new
        stogrp.pull_full_properties()
        assert stogrp.properties['name'] == stogrp_name_new
        with pytest.raises(zhmcclient.NotFound):
            console.storage_groups.find(name=stogrp_name)

        # Test deleting the storage group

        # The code to be tested
        stogrp.delete()

        with pytest.raises(zhmcclient.NotFound):
            console.storage_groups.find(name=stogrp_name_new)
