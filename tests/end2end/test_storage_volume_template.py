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
End2end tests for storage volume templates (on CPCs in DPM mode).

These tests do not change any existing storage volume templates, but create,
modify and delete test storage volume templates.
"""

from __future__ import absolute_import, print_function

import random
import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skipif_no_storage_mgmt_feature, runtest_find_list, \
    TEST_PREFIX, End2endTestWarning

urllib3.disable_warnings()

# Properties in minimalistic StorageVolume objects (e.g. find_by_name())
STOVOLTPL_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in StorageVolume objects returned by list() without full props
STOVOLTPL_LIST_PROPS = ['element-uri', 'name', 'size', 'usage']

# Properties whose values can change between retrievals of StorageVolume objs
STOVOLTPL_VOLATILE_PROPS = []


def test_stovoltpl_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))
        skipif_no_storage_mgmt_feature(cpc)

        console = cpc.manager.client.consoles.console
        session = cpc.manager.session

        # Pick a random storage volume template of a random storage group
        # template associated to this CPC
        grp_vol_tuples = []
        stogrptpl_list = console.storage_group_templates.findall(
            **{'cpc-uri': cpc.uri})
        for stogrptpl in stogrptpl_list:
            stovoltpl_list = stogrptpl.storage_volume_templates.list()
            for stovoltpl in stovoltpl_list:
                grp_vol_tuples.append((stogrptpl, stovoltpl))
        if not grp_vol_tuples:
            msg_txt = "No storage group templates with volumes associated to " \
                "CPC {}".format(cpc.name)
            warnings.warn(msg_txt, End2endTestWarning)
            pytest.skip(msg_txt)
        stogrptpl, stovoltpl = random.choice(grp_vol_tuples)

        runtest_find_list(
            session, stogrptpl.storage_volume_templates, stovoltpl.name, 'name',
            'size', STOVOLTPL_VOLATILE_PROPS, STOVOLTPL_MINIMAL_PROPS,
            STOVOLTPL_LIST_PROPS)


def test_stovoltpl_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a storage volume template in a storage
    group template.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))
        skipif_no_storage_mgmt_feature(cpc)

        console = cpc.manager.client.consoles.console

        stogrptpl_name = TEST_PREFIX + ' test_stovoltpl_crud stogrptpl1'
        stovoltpl_name = 'stovoltpl1'
        stovoltpl_name_new = stovoltpl_name + ' new'

        # Ensure clean starting point
        try:
            stogrptpl = console.storage_group_templates.find(
                name=stogrptpl_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test storage group template from previous run: '{s}' "
                "on CPC '{c}'".
                format(s=stogrptpl_name, c=cpc.name), UserWarning)
            stogrptpl.delete()

        stogrptpl = None
        try:

            # Create a storage group template for the volume
            stogrptpl_input_props = {
                'cpc-uri': cpc.uri,
                'name': stogrptpl_name,
                'description': 'Dummy storage group template description.',
                'type': 'fcp',
            }
            stogrptpl = console.storage_group_templates.create(
                stogrptpl_input_props)

            # Test creating a volume

            stovoltpl_input_props = {
                'name': stovoltpl_name,
                'description': 'Dummy storage volume template description.',
                'size': 100,  # MB
            }
            stovoltpl_auto_props = {
                'usage': 'data',
            }

            # The code to be tested
            stovoltpl = stogrptpl.storage_volume_templates.create(
                stovoltpl_input_props)

            for pn, exp_value in stovoltpl_input_props.items():
                assert stovoltpl.properties[pn] == exp_value, \
                    "Unexpected value for property {!r} of storage volume " \
                    "template:\n{!r}".format(pn, sorted(stovoltpl.properties))
            stovoltpl.pull_full_properties()
            for pn, exp_value in stovoltpl_input_props.items():
                assert stovoltpl.properties[pn] == exp_value, \
                    "Unexpected value for property {!r} of storage volume " \
                    "template:\n{!r}".format(pn, sorted(stovoltpl.properties))
            for pn, exp_value in stovoltpl_auto_props.items():
                assert stovoltpl.properties[pn] == exp_value, \
                    "Unexpected value for property {!r} of storage volume " \
                    "template:\n{!r}".format(pn, sorted(stovoltpl.properties))

            # Test updating a property of the storage volume template

            new_desc = "Updated storage volume template description."

            # The code to be tested
            stovoltpl.update_properties(dict(description=new_desc))

            assert stovoltpl.properties['description'] == new_desc
            stovoltpl.pull_full_properties()
            assert stovoltpl.properties['description'] == new_desc

            # Test renaming the storage volume template

            # The code to be tested
            stovoltpl.update_properties(dict(name=stovoltpl_name_new))

            assert stovoltpl.properties['name'] == stovoltpl_name_new
            stovoltpl.pull_full_properties()
            assert stovoltpl.properties['name'] == stovoltpl_name_new
            with pytest.raises(zhmcclient.NotFound):
                stogrptpl.storage_volume_templates.find(name=stovoltpl_name)

            # Test deleting the storage volume template

            # The code to be tested
            stovoltpl.delete()

            with pytest.raises(zhmcclient.NotFound):
                stogrptpl.storage_volume_templates.find(name=stovoltpl_name_new)

        finally:
            # Cleanup
            if stogrptpl:
                stogrptpl.delete()
