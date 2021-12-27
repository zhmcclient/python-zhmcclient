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
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils.cpc_fixtures import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import runtest_find_list, TEST_PREFIX

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
        pytest.skip("No CPCs in DPM mode provided")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))

        session = cpc.manager.session

        # Pick a NIC on a partition
        part_list = cpc.partitions.list()
        nic = None
        part = None
        for _part in part_list:
            nic_list = _part.nics.list()
            if nic_list:
                nic = nic_list[0]
                part = _part
                break
        assert nic

        runtest_find_list(
            session, part.nics, nic.name, 'name', 'type',
            NIC_VOLATILE_PROPS, NIC_MINIMAL_PROPS, NIC_LIST_PROPS)


def test_nic_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a NIC (and a partition).
    """
    if not dpm_mode_cpcs:
        pytest.skip("No CPCs in DPM mode provided")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))

        part_name = TEST_PREFIX + '.test_nic_crud.part1'
        nic_name = 'nic1'
        adapter_name = TEST_PREFIX + '.test_nic_crud.adapter1'

        # Ensure a clean starting point for this test
        try:
            part = cpc.partitions.find(name=part_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test partition from previous run: '{p}' on CPC '{c}'".
                format(p=part_name, c=cpc.name), UserWarning)
            status = part.get_property('status')
            if status != 'stopped':
                part.stop()
            part.delete()

        try:
            adapter = cpc.adapters.find(name=adapter_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test adapter from previous run: '{a}' on CPC '{c}'".
                format(a=adapter_name, c=cpc.name), UserWarning)
            adapter.delete()

        part = None
        adapter = None
        try:

            # Create a partition containing the NIC
            part_input_props = {
                'name': part_name,
                'description': 'Test partition for zhmcclient end2end tests',
                'ifl-processors': 2,
                'initial-memory': 1024,
                'maximum-memory': 2048,
                'processor-mode': 'shared',  # used for filtering
                'type': 'linux',  # used for filtering
            }
            part = cpc.partitions.create(part_input_props)

            # Create a Hipersocket adapter backing the NIC
            adapter_input_props = {
                'name': adapter_name,
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

            nic_name_new = nic_name + '_new'

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
