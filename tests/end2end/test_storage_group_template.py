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
End2end tests for storage group templates (on CPCs in DPM mode).

These tests do not change any existing storage group templates, but create,
modify and delete test storage group templates.
"""

from __future__ import absolute_import, print_function

import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import pick_test_resources, skipif_no_storage_mgmt_feature, \
    runtest_find_list, TEST_PREFIX, skip_warn

urllib3.disable_warnings()

# Properties in minimalistic StorageGroupTemplate objects (e.g. find_by_name())
STOGRPTPL_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in StorageGroupTemplate objects returned by list() without full
# props
STOGRPTPL_LIST_PROPS = ['object-uri', 'cpc-uri', 'name', 'type']

# Properties whose values can change between retrievals of StorageGroupTemplate
# objs
STOGRPTPL_VOLATILE_PROPS = []


def test_stogrptpl_find_list(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the storage group templates to test with
        stogrptpl_list = console.storage_group_templates.findall(
            **{'cpc-uri': cpc.uri})
        if not stogrptpl_list:
            skip_warn("No storage group templates associated to CPC {c} "
                      "managed by HMC {h}".format(c=cpc.name, h=hd.host))
        stogrptpl_list = pick_test_resources(stogrptpl_list)

        for stogrptpl in stogrptpl_list:
            print("Testing on CPC {c} with storage group template {g!r}".
                  format(c=cpc.name, g=stogrptpl.name))
            runtest_find_list(
                session, console.storage_group_templates, stogrptpl.name,
                'name', 'object-uri', STOGRPTPL_VOLATILE_PROPS,
                STOGRPTPL_MINIMAL_PROPS, STOGRPTPL_LIST_PROPS)


def test_stogrptpl_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a storage group template.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_storage_mgmt_feature(cpc)

        print("Testing on CPC {c}".format(c=cpc.name))

        console = cpc.manager.client.consoles.console
        stogrptpl_name = TEST_PREFIX + ' test_stogrptpl_crud stogrptpl1'
        stogrptpl_name_new = stogrptpl_name + ' new'

        # Ensure clean starting point
        try:
            stogrptpl = console.storage_group_templates.find(
                name=stogrptpl_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test storage group template from previous run: {g!r} "
                "on CPC {c}".format(g=stogrptpl_name, c=cpc.name), UserWarning)
            stogrptpl.delete()
        try:
            stogrptpl = console.storage_group_templates.find(
                name=stogrptpl_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test storage group template from previous run: {g!r} "
                "on CPC {c}".
                format(g=stogrptpl_name_new, c=cpc.name), UserWarning)
            stogrptpl.delete()

        # Test creating the storage group template

        stogrptpl_input_props = {
            'cpc-uri': cpc.uri,
            'name': stogrptpl_name,
            'description': 'Test storage grp tpl for zhmcclient end2end tests',
            'type': 'fcp',
        }
        stogrptpl_auto_props = {
            'shared': True,
        }

        # The code to be tested
        stogrptpl = console.storage_group_templates.create(
            stogrptpl_input_props)

        for pn, exp_value in stogrptpl_input_props.items():
            assert stogrptpl.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage group tpl:\n" \
                "{!r}".format(pn, sorted(stogrptpl.properties))
        stogrptpl.pull_full_properties()
        for pn, exp_value in stogrptpl_input_props.items():
            assert stogrptpl.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage group tpl:\n" \
                "{!r}".format(pn, sorted(stogrptpl.properties))
        for pn, exp_value in stogrptpl_auto_props.items():
            assert stogrptpl.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage group tpl:\n" \
                "{!r}".format(pn, sorted(stogrptpl.properties))

        # Test updating a property of the storage group template

        new_desc = "Updated storage group template description."

        # The code to be tested
        stogrptpl.update_properties(dict(description=new_desc))

        assert stogrptpl.properties['description'] == new_desc
        stogrptpl.pull_full_properties()
        assert stogrptpl.properties['description'] == new_desc

        # Test renaming the storage group template

        # The code to be tested
        stogrptpl.update_properties(dict(name=stogrptpl_name_new))

        assert stogrptpl.properties['name'] == stogrptpl_name_new
        stogrptpl.pull_full_properties()
        assert stogrptpl.properties['name'] == stogrptpl_name_new
        with pytest.raises(zhmcclient.NotFound):
            console.storage_group_templates.find(name=stogrptpl_name)

        # Test deleting the storage group template

        # The code to be tested
        stogrptpl.delete()

        with pytest.raises(zhmcclient.NotFound):
            console.storage_group_templates.find(name=stogrptpl_name_new)
