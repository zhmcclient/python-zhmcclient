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

"""
End2end tests for storage volumes (on CPCs in DPM mode).

These tests do not change any existing storage volumes, but create, modify and
delete test storage volumes.
"""

from __future__ import absolute_import, print_function

import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils.cpc_fixtures import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skipif_no_storage_mgmt_feature, runtest_find_list, \
    TEST_PREFIX

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
        pytest.skip("No CPCs in DPM mode provided")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))
        skipif_no_storage_mgmt_feature(cpc)

        session = cpc.manager.session

        # Pick a storage group associated to this CPC
        stogrp_list = cpc.list_associated_storage_groups()
        assert len(stogrp_list) >= 1
        stogrp = stogrp_list[-1]  # Pick the last one returned

        # Pick a storage volume in this storage group
        stovol_list = stogrp.storage_volumes.list()
        assert len(stovol_list) >= 1
        stovol = stovol_list[-1]  # Pick the last one returned

        runtest_find_list(
            session, stogrp.storage_volumes, stovol.name, 'name', 'size',
            STOVOL_VOLATILE_PROPS, STOVOL_MINIMAL_PROPS, STOVOL_LIST_PROPS)


def test_stovol_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a storage volume in a storage group.
    """
    if not dpm_mode_cpcs:
        pytest.skip("No CPCs in DPM mode provided")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))
        skipif_no_storage_mgmt_feature(cpc)

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
                "Deleting test storage group from previous run: '{s}' on "
                "CPC '{c}'".format(s=stogrp_name, c=cpc.name), UserWarning)
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
                assert stovol.properties[pn] == exp_value, \
                    "Unexpected value for property {!r} of storage volume:\n" \
                    "{!r}".format(pn, sorted(stovol.properties))
            stovol.pull_full_properties()
            for pn, exp_value in stovol_input_props.items():
                assert stovol.properties[pn] == exp_value, \
                    "Unexpected value for property {!r} of storage volume:\n" \
                    "{!r}".format(pn, sorted(stovol.properties))
            for pn, exp_value in stovol_auto_props.items():
                assert stovol.properties[pn] == exp_value, \
                    "Unexpected value for property {!r} of storage volume:\n" \
                    "{!r}".format(pn, sorted(stovol.properties))

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
