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
End2end tests for virtual functions (on CPCs in DPM mode).

These tests do not change any existing partitions or virtual functions, but
create, modify and delete test partitions with virtual functions.
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

from .utils import runtest_find_list, TEST_PREFIX, standard_partition_props, \
    End2endTestWarning

urllib3.disable_warnings()

# Properties in minimalistic VirtualFunction objects (e.g. find_by_name())
VFUNC_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in VirtualFunction objects returned by list() without full props
VFUNC_LIST_PROPS = ['element-uri', 'name', 'description']

# Properties whose values can change between retrievals of VirtualFunction
# objects
VFUNC_VOLATILE_PROPS = []


def test_vfunc_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))

        session = cpc.manager.session

        # Pick a random virtual function on a random partition
        part_vfunc_tuples = []
        part_list = cpc.partitions.list()
        for part in part_list:
            vfunc_list = part.virtual_functions.list()
            for vfunc in vfunc_list:
                part_vfunc_tuples.append((part, vfunc))
        if not part_vfunc_tuples:
            msg_txt = "No partitions with virtual functions on CPC {c}". \
                format(c=cpc.name)
            warnings.warn(msg_txt, End2endTestWarning)
            pytest.skip(msg_txt)
        part, vfunc = random.choice(part_vfunc_tuples)

        runtest_find_list(
            session, part.virtual_functions, vfunc.name, 'name', 'description',
            VFUNC_VOLATILE_PROPS, VFUNC_MINIMAL_PROPS, VFUNC_LIST_PROPS)


def test_vfunc_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a virtual function (and a partition).
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        print("Testing on CPC {} (DPM mode)".format(cpc.name))

        part_name = TEST_PREFIX + ' test_vfunc_crud part1'
        vfunc_name = 'vfunc1'
        vfunc_name_new = vfunc_name + ' new'

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

        part = None
        try:

            # Pick a zEDC accelerator adapter that will back the virtual func.
            edc_adapters = cpc.adapters.findall(type='zedc')
            if not edc_adapters:
                msg_txt = "No zEDC accelerator adapters on CPC {}". \
                    format(cpc.name)
                warnings.warn(msg_txt, End2endTestWarning)
                pytest.skip(msg_txt)
            edc_adapter = edc_adapters[-1]  # Pick the last one

            # Create a partition that will lateron contain the virtual function
            part_props = standard_partition_props(cpc, part_name)
            part = cpc.partitions.create(part_props)

            # Test creating a virtual function

            vfunc_input_props = {
                'name': vfunc_name,
                'description': 'Dummy virtual function description.',
                'adapter-uri': edc_adapter.uri,
                'device-number': '0100',
            }
            vfunc_auto_props = {}

            # The code to be tested
            vfunc = part.virtual_functions.create(vfunc_input_props)

            for pn, exp_value in vfunc_input_props.items():
                assert vfunc.properties[pn] == exp_value, \
                    "Unexpected value for property {!r}".format(pn)
            vfunc.pull_full_properties()
            for pn, exp_value in vfunc_input_props.items():
                assert vfunc.properties[pn] == exp_value, \
                    "Unexpected value for property {!r}".format(pn)
            for pn, exp_value in vfunc_auto_props.items():
                assert vfunc.properties[pn] == exp_value, \
                    "Unexpected value for property {!r}".format(pn)

            # Test updating a property of the virtual function

            new_desc = "Updated virtual function description."

            # The code to be tested
            vfunc.update_properties(dict(description=new_desc))

            assert vfunc.properties['description'] == new_desc
            vfunc.pull_full_properties()
            assert vfunc.properties['description'] == new_desc

            # Test renaming the virtual function

            # The code to be tested
            vfunc.update_properties(dict(name=vfunc_name_new))

            assert vfunc.properties['name'] == vfunc_name_new
            vfunc.pull_full_properties()
            assert vfunc.properties['name'] == vfunc_name_new
            with pytest.raises(zhmcclient.NotFound):
                part.virtual_functions.find(name=vfunc_name)

            # Test deleting the virtual function

            # The code to be tested
            vfunc.delete()

            with pytest.raises(zhmcclient.NotFound):
                part.virtual_functions.find(name=vfunc_name_new)

        finally:
            # Cleanup
            if part:
                part.delete()
