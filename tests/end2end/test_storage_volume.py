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
End2end tests for storage volumes (on CPCs in DPM mode).

These tests do not change any existing storage volumes, but create, modify and
delete test storage volumes.
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

# Properties in minimalistic StorageVolume objects (e.g. find_by_name())
STOVOL_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in StorageVolume objects returned by list() without full props
STOVOL_LIST_PROPS = ['element-uri', 'name', 'fulfillment-state', 'size',
                     'usage']

# Properties whose values can change between retrievals of StorageVolume objs
STOVOL_VOLATILE_PROPS = []


def test_stovol_find_list(dpm_mode_cpcs):  # noqa: F811
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
        client = cpc.manager.client

        api_version = client.query_api_version()
        hmc_version_str = api_version['hmc-version']
        hmc_version = tuple(map(int, hmc_version_str.split('.')))

        # Pick the storage volumes to test with
        grp_vol_tuples = []
        stogrp_list = cpc.list_associated_storage_groups()
        for stogrp in stogrp_list:
            stovol_list = stogrp.storage_volumes.list()
            for stovol in stovol_list:
                grp_vol_tuples.append((stogrp, stovol))
        if not grp_vol_tuples:
            skip_warn("No storage groups with volumes associated to CPC "
                      f"{cpc.name} managed by HMC {hd.host}")
        grp_vol_tuples = pick_test_resources(grp_vol_tuples)

        # Storage volumes were introduced in HMC 2.14.0 but their names were
        # made unique only in 2.14.1.
        unique_name = (hmc_version >= (2, 14, 1))
        if not unique_name:
            print("Tolerating non-unique storage volume names on HMC "
                  f"version {hmc_version}")
        for stogrp, stovol in grp_vol_tuples:
            print(f"Testing on CPC {cpc.name} with storage volume "
                  f"{stovol.name!r} of storage group {stogrp.name!r}")
            runtest_find_list(
                session, stogrp.storage_volumes, stovol.name, 'name', 'size',
                STOVOL_VOLATILE_PROPS, STOVOL_MINIMAL_PROPS, STOVOL_LIST_PROPS,
                unique_name=unique_name)


def test_stovol_property(dpm_mode_cpcs):  # noqa: F811
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
        client = cpc.manager.client
        hd = session.hmc_definition

        api_version = client.query_api_version()
        hmc_version_str = api_version['hmc-version']
        hmc_version = tuple(map(int, hmc_version_str.split('.')))

        # Pick the storage volumes to test with
        grp_vol_tuples = []
        stogrp_list = cpc.list_associated_storage_groups()
        for stogrp in stogrp_list:
            stovol_list = stogrp.storage_volumes.list()
            for stovol in stovol_list:
                grp_vol_tuples.append((stogrp, stovol))
        if not grp_vol_tuples:
            skip_warn("No storage groups with volumes associated to CPC "
                      f"{cpc.name} managed by HMC {hd.host}")
        grp_vol_tuples = pick_test_resources(grp_vol_tuples)

        # Storage volumes were introduced in HMC 2.14.0 but their names were
        # made unique only in 2.14.1.
        unique_name = (hmc_version >= (2, 14, 1))
        if not unique_name:
            print("Tolerating non-unique storage volume names on HMC "
                  f"version {hmc_version}")
        for stogrp, stovol in grp_vol_tuples:
            print(f"Testing on CPC {cpc.name} with storage volume "
                  f"{stovol.name!r} of storage group {stogrp.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(stovol.manager, non_list_prop)


def test_stovol_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a storage volume in a storage group.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_storage_mgmt_feature(cpc)

        print(f"Testing on CPC {cpc.name}")

        console = cpc.manager.client.consoles.console

        stogrp_name = TEST_PREFIX + ' test_stovol_crud stogrp1'
        stovol_name = 'stovol1'
        stovol_name_new = stovol_name + ' new'

        # Ensure clean starting point
        try:
            stogrp = console.storage_groups.find(name=stogrp_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test storage group from previous run: "
                f"{stogrp_name!r} on CPC {cpc.name}", UserWarning)
            stogrp.delete()

        stogrp = None
        try:

            # Create a storage group for the volume
            stogrp_input_props = {
                'cpc-uri': cpc.uri,
                'name': stogrp_name,
                'description': 'Dummy storage group description.',
                'type': 'fcp',
            }
            stogrp = console.storage_groups.create(stogrp_input_props)

            # Test creating a volume

            stovol_input_props = {
                'name': stovol_name,
                'description': 'Dummy storage volume description.',
                'size': 100,  # MB
            }
            stovol_auto_props = {
                'fulfillment-state': 'pending',
                'usage': 'data',
            }

            # The code to be tested
            stovol = stogrp.storage_volumes.create(stovol_input_props)

            for pn, exp_value in stovol_input_props.items():
                assert pn in stovol.properties, (
                    f"Input property {pn!r} is not in created storage volume:\n"
                    f"{stovol!r}")
                assert stovol.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r} of storage " \
                    f"volume:\n{stovol.properties!r}"
            stovol.pull_full_properties()
            for pn, exp_value in stovol_input_props.items():
                assert stovol.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r} of storage " \
                    f"volume:\n{stovol.properties!r}"
            for pn, exp_value in stovol_auto_props.items():
                assert pn in stovol.properties, (
                    f"Automatically returned property {pn!r} is not in "
                    f"created storage volume:\n{stovol!r}")
                assert stovol.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r} of storage " \
                    f"volume:\n{stovol.properties!r}"

            # Test updating a property of the storage volume

            new_desc = "Updated storage volume description."

            # The code to be tested
            stovol.update_properties(dict(description=new_desc))

            assert stovol.properties['description'] == new_desc
            stovol.pull_full_properties()
            assert stovol.properties['description'] == new_desc

            # Test renaming the storage volume

            # The code to be tested
            stovol.update_properties(dict(name=stovol_name_new))

            assert stovol.properties['name'] == stovol_name_new
            stovol.pull_full_properties()
            assert stovol.properties['name'] == stovol_name_new
            with pytest.raises(zhmcclient.NotFound):
                stogrp.storage_volumes.find(name=stovol_name)

            # Test deleting the storage volume

            # The code to be tested
            stovol.delete()

            with pytest.raises(zhmcclient.NotFound):
                stogrp.storage_volumes.find(name=stovol_name_new)

        finally:
            # Cleanup
            if stogrp:
                stogrp.delete()
