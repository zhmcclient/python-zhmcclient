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
End2end tests for HBAs (on CPCs in DPM mode without storage mgmt feature).

These tests do not change any existing partitions or HBAs, but create, modify
and delete test partitions with HBAs.
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
    standard_partition_props, skipif_storage_mgmt_feature, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Hba objects (e.g. find_by_name())
HBA_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in Hba objects returned by list() without full props
HBA_LIST_PROPS = ['element-uri', 'name', 'description', 'wwpn']

# Properties whose values can change between retrievals of Hba objects
HBA_VOLATILE_PROPS = []


def test_hba_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_storage_mgmt_feature(cpc)

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the HBAs to test with
        part_hba_tuples = []
        part_list = cpc.partitions.list()
        for part in part_list:
            hba_list = part.hbas.list()
            for hba in hba_list:
                part_hba_tuples.append((part, hba))
        if not part_hba_tuples:
            skip_warn(
                f"No partitions with HBAs on CPC {cpc.name} managed by HMC "
                f"{hd.host}")
        part_hba_tuples = pick_test_resources(part_hba_tuples)

        for part, hba in part_hba_tuples:
            print(f"Testing on CPC {cpc.name} with HBA {hba.name!r} of "
                  f"partition {part.name!r}")
            runtest_find_list(
                session, part.hbas, hba.name, 'name', 'wwpn',
                HBA_VOLATILE_PROPS, HBA_MINIMAL_PROPS, HBA_LIST_PROPS)


def test_hba_property(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the HBAs to test with
        part_hba_tuples = []
        part_list = cpc.partitions.list()
        for part in part_list:
            hba_list = part.hbas.list()
            for hba in hba_list:
                part_hba_tuples.append((part, hba))
        if not part_hba_tuples:
            skip_warn(
                f"No partitions with HBAs on CPC {cpc.name} managed by "
                f"HMC {hd.host}")
        part_hba_tuples = pick_test_resources(part_hba_tuples)

        for part, hba in part_hba_tuples:
            print(f"Testing on CPC {cpc.name} with HBA {hba.name!r} of "
                  f"partition {part.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(hba.manager, non_list_prop)


def test_hba_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a HBA (and a partition).
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_storage_mgmt_feature(cpc)

        print(f"Testing on CPC {cpc.name}")

        part_name = TEST_PREFIX + ' test_hba_crud part1'
        hba_name = 'hba1'
        hba_name_new = hba_name + ' new'

        # Ensure a clean starting point for this test
        try:
            part = cpc.partitions.find(name=part_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                f"Deleting test partition from previous run: {part_name!r} on "
                f"CPC {cpc.name}", UserWarning)
            status = part.get_property('status')
            if status != 'stopped':
                part.stop()
            part.delete()

        part = None
        try:

            # Pick a FICON adapter backing the HBA
            adapters = cpc.adapters.findall(**{'type': 'fcp'})
            assert len(adapters) >= 1, (
                f"CPC {cpc.name} does not have any FCP-type FICON adapters")
            adapter = adapters[-1]  # Pick the last adapter found
            port = adapter.ports.list()[0]  # Pick its first port

            # Create a partition that will lateron contain the HBA
            part_props = standard_partition_props(cpc, part_name)
            part = cpc.partitions.create(part_props)

            # Test creating a HBA

            hba_input_props = {
                'name': hba_name,
                'description': 'Dummy HBA description.',
                'adapter-port-uri': port.uri,
                'device-number': '0100',
            }
            hba_auto_props = {}

            # The code to be tested
            hba = part.hbas.create(hba_input_props)

            for pn, exp_value in hba_input_props.items():
                assert hba.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r}"
            hba.pull_full_properties()
            for pn, exp_value in hba_input_props.items():
                assert hba.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r}"
            for pn, exp_value in hba_auto_props.items():
                assert hba.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r}"

            # Test updating a property of the HBA

            new_desc = "Updated HBA description."

            # The code to be tested
            hba.update_properties(dict(description=new_desc))

            assert hba.properties['description'] == new_desc
            hba.pull_full_properties()
            assert hba.properties['description'] == new_desc

            # Test renaming the HBA

            # The code to be tested
            hba.update_properties(dict(name=hba_name_new))

            assert hba.properties['name'] == hba_name_new
            hba.pull_full_properties()
            assert hba.properties['name'] == hba_name_new
            with pytest.raises(zhmcclient.NotFound):
                part.hbas.find(name=hba_name)

            # Test deleting the HBA

            # The code to be tested
            hba.delete()

            with pytest.raises(zhmcclient.NotFound):
                part.hbas.find(name=hba_name_new)

        finally:
            # Cleanup
            if part:
                part.delete()
