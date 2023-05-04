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
End2end tests for NICs (on CPCs in DPM mode).

These tests do not change any existing partitions or NICs, but create, modify
and delete test partitions with NICs.
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

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    standard_partition_props, runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Nic objects (e.g. find_by_name())
NIC_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in Nic objects returned by list() without full props
NIC_LIST_PROPS = ['element-uri', 'name', 'description', 'type']

# Properties whose values can change between retrievals of Nic objects
NIC_VOLATILE_PROPS = []


def test_nic_find_list(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the NICs to test with
        part_nic_tuples = []
        part_list = cpc.partitions.list()
        for part in part_list:
            nic_list = part.nics.list()
            for nic in nic_list:
                part_nic_tuples.append((part, nic))
        if not part_nic_tuples:
            skip_warn("No partitions with NICs on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))
        part_nic_tuples = pick_test_resources(part_nic_tuples)

        for part, nic in part_nic_tuples:
            print("Testing on CPC {c} with NIC {n!r} of partition {p!r}".
                  format(c=cpc.name, n=nic.name, p=part.name))
            runtest_find_list(
                session, part.nics, nic.name, 'name', 'type',
                NIC_VOLATILE_PROPS, NIC_MINIMAL_PROPS, NIC_LIST_PROPS)


def test_nic_property(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        client = cpc.manager.client
        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the NICs to test with
        part_nic_tuples = []
        part_list = cpc.partitions.list()
        for part in part_list:
            nic_list = part.nics.list()
            for nic in nic_list:
                part_nic_tuples.append((part, nic))
        if not part_nic_tuples:
            skip_warn("No partitions with NICs on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))
        part_nic_tuples = pick_test_resources(part_nic_tuples)

        for part, nic in part_nic_tuples:
            print("Testing on CPC {c} with NIC {n!r} of partition {p!r}".
                  format(c=cpc.name, n=nic.name, p=part.name))

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(client, nic.manager, non_list_prop, None)


def test_nic_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a NIC (and a partition).
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print("Testing on CPC {c}".format(c=cpc.name))

        hs_adapter_name = TEST_PREFIX + ' test_nic_crud adapter1'
        part_name = TEST_PREFIX + ' test_nic_crud part1'
        nic_name = 'nic1'
        nic_name_new = nic_name + ' new'

        # Ensure a clean starting point for this test
        try:
            part = cpc.partitions.find(name=part_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test partition from previous run: {p!r} on CPC {c}".
                format(p=part_name, c=cpc.name), UserWarning)
            status = part.get_property('status')
            if status != 'stopped':
                part.stop()
            part.delete()
        try:
            adapter = cpc.adapters.find(name=hs_adapter_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test Hipersocket adapter from previous run: {a!r} on "
                "CPC {c}".format(a=hs_adapter_name, c=cpc.name), UserWarning)
            adapter.delete()

        part = None
        adapter = None
        try:

            # Create a partition that will lateron contain the NIC
            part_props = standard_partition_props(cpc, part_name)
            part = cpc.partitions.create(part_props)

            # Create a Hipersocket adapter backing the NIC
            adapter_input_props = {
                'name': hs_adapter_name,
                'description': 'Test adapter for zhmcclient end2end tests',
            }
            adapter = cpc.adapters.create_hipersocket(adapter_input_props)

            # Find the vswitch backed by the Hipersockets adapter
            vswitches = cpc.virtual_switches.findall(
                **{'backing-adapter-uri': adapter.uri})
            vswitch = vswitches[0]

            # Test creating a NIC

            nic_input_props = {
                'name': nic_name,
                'description': 'Dummy NIC description.',
                'virtual-switch-uri': vswitch.uri,
                'device-number': '0100',
            }
            nic_auto_props = {
                'type': 'iqd',
                'ssc-management-nic': False,
            }

            # The code to be tested
            nic = part.nics.create(nic_input_props)

            for pn, exp_value in nic_input_props.items():
                assert nic.properties[pn] == exp_value, \
                    "Unexpected value for property {!r}".format(pn)
            nic.pull_full_properties()
            for pn, exp_value in nic_input_props.items():
                assert nic.properties[pn] == exp_value, \
                    "Unexpected value for property {!r}".format(pn)
            for pn, exp_value in nic_auto_props.items():
                assert nic.properties[pn] == exp_value, \
                    "Unexpected value for property {!r}".format(pn)

            # Test updating a property of the NIC

            new_desc = "Updated NIC description."

            # The code to be tested
            nic.update_properties(dict(description=new_desc))

            assert nic.properties['description'] == new_desc
            nic.pull_full_properties()
            assert nic.properties['description'] == new_desc

            # Test renaming the NIC

            # The code to be tested
            nic.update_properties(dict(name=nic_name_new))

            assert nic.properties['name'] == nic_name_new
            nic.pull_full_properties()
            assert nic.properties['name'] == nic_name_new
            with pytest.raises(zhmcclient.NotFound):
                part.nics.find(name=nic_name)

            # Test deleting the NIC

            # The code to be tested
            nic.delete()

            with pytest.raises(zhmcclient.NotFound):
                part.nics.find(name=nic_name_new)

        finally:
            # Cleanup
            if part:
                part.delete()
            if adapter:
                adapter.delete()
