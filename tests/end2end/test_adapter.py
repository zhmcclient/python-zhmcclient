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
End2end tests for adapters (on CPCs in DPM mode).

These tests do not change any existing adapters, but create, modify
and delete Hipersocket adapters.
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

from .utils import pick_test_resources, runtest_find_list, TEST_PREFIX, \
    skip_warn

urllib3.disable_warnings()

# Properties in minimalistic Adapter objects (e.g. find_by_name())
ADAPTER_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Adapter objects returned by list() without full props
ADAPTER_LIST_PROPS = ['object-uri', 'name', 'adapter-id', 'adapter-family',
                      'type', 'status']

# Properties whose values can change between retrievals of Adapter objects
ADAPTER_VOLATILE_PROPS = []


def test_adapter_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the adapters to test with
        adapter_list = cpc.adapters.list()
        if not adapter_list:
            skip_warn("No adapters on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.hmc_host))
        adapter_list = pick_test_resources(adapter_list)

        for adapter in adapter_list:
            print("Testing on CPC {c} with adapter {a!r}".
                  format(c=cpc.name, a=adapter.name))
            runtest_find_list(
                session, cpc.adapters, adapter.name, 'name', 'object-uri',
                ADAPTER_VOLATILE_PROPS, ADAPTER_MINIMAL_PROPS,
                ADAPTER_LIST_PROPS)


def test_adapter_hs_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a Hipersocket adapter.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print("Testing on CPC {c}".format(c=cpc.name))

        adapter_name = TEST_PREFIX + ' test_adapter_crud adapter1'
        adapter_name_new = adapter_name + ' new'

        # Ensure a clean starting point for this test
        try:
            adapter = cpc.adapters.find(name=adapter_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test Hipersocket adapter from previous run: "
                "{a!r} on CPC {c}".
                format(a=adapter_name, c=cpc.name), UserWarning)
            adapter.delete()
        try:
            adapter = cpc.adapters.find(name=adapter_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test Hipersocket adapter from previous run: "
                "{a!r} on CPC {c}".
                format(a=adapter_name_new, c=cpc.name), UserWarning)
            adapter.delete()

        # Create a Hipersocket adapter
        adapter_input_props = {
            'name': adapter_name,
            'description': 'Test adapter for zhmcclient end2end tests',
        }
        adapter_auto_props = {
            'type': 'hipersockets',
        }

        # The code to be tested
        adapter = cpc.adapters.create_hipersocket(adapter_input_props)

        for pn, exp_value in adapter_input_props.items():
            assert adapter.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        adapter.pull_full_properties()
        for pn, exp_value in adapter_input_props.items():
            assert adapter.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        for pn, exp_value in adapter_auto_props.items():
            assert adapter.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)

        # Test updating a property of the adapter

        new_desc = "Updated adapter description."

        # The code to be tested
        adapter.update_properties(dict(description=new_desc))

        assert adapter.properties['description'] == new_desc
        adapter.pull_full_properties()
        assert adapter.properties['description'] == new_desc

        # Test renaming the adapter

        # The code to be tested
        adapter.update_properties(dict(name=adapter_name_new))

        assert adapter.properties['name'] == adapter_name_new
        adapter.pull_full_properties()
        assert adapter.properties['name'] == adapter_name_new
        with pytest.raises(zhmcclient.NotFound):
            cpc.adapters.find(name=adapter_name)

        # Test deleting the adapter

        # The code to be tested
        adapter.delete()

        with pytest.raises(zhmcclient.NotFound):
            cpc.adapters.find(name=adapter_name_new)
