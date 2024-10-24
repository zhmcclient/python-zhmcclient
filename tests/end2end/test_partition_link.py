# Copyright 2024 IBM Corp. All Rights Reserved.
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
End2end tests for partition links (on CPCs in DPM mode).

These tests do not change any existing partition links or partitions, but
create, modify and delete test partition links and test partitions.
"""


import warnings
import random
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    skipif_no_partition_link_feature, runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic PartitionLink objects (e.g. find_by_name())
PARTLINK_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in PartitionLink objects returned by list() without full props
PARTLINK_LIST_PROPS = ['object-uri', 'cpc-uri', 'name', 'state', 'type']

# Properties whose values can change between retrievals of PartitionLink objs
PARTLINK_VOLATILE_PROPS = []


@pytest.mark.parametrize(
    "pl_type", ['hipersockets', 'smc-d', 'ctc'])
def test_partlink_find_list(dpm_mode_cpcs, pl_type):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_partition_link_feature(cpc)

        console = cpc.manager.client.consoles.console
        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the partition links to test with
        filter_args = {
            'cpc-uri': cpc.uri,
            'type': pl_type,
        }
        partlink_list = console.partition_links.list(filter_args=filter_args)
        if not partlink_list:
            skip_warn(f"No partition links of type {pl_type} associated to "
                      f"CPC {cpc.name} managed by HMC {hd.host}")
        partlink_list = pick_test_resources(partlink_list)

        for partlink in partlink_list:
            print(f"Testing on CPC {cpc.name} with {pl_type} partition link "
                  f"{partlink.name!r}")
            runtest_find_list(
                session, console.partition_links, partlink.name, 'name',
                'object-uri', PARTLINK_VOLATILE_PROPS, PARTLINK_MINIMAL_PROPS,
                PARTLINK_LIST_PROPS)


@pytest.mark.parametrize(
    "pl_type", ['hipersockets', 'smc-d', 'ctc'])
def test_partlink_property(dpm_mode_cpcs, pl_type):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_partition_link_feature(cpc)

        console = cpc.manager.client.consoles.console
        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the partition links to test with
        filter_args = {
            'cpc-uri': cpc.uri,
            'type': pl_type,
        }
        partlink_list = console.partition_links.list(filter_args=filter_args)
        if not partlink_list:
            skip_warn(f"No partition links of type {pl_type} associated to "
                      f"CPC {cpc.name} managed by HMC {hd.host}")
        partlink_list = pick_test_resources(partlink_list)

        for partlink in partlink_list:
            print(f"Testing on CPC {cpc.name} with {pl_type} partition link "
                  f"{partlink.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(partlink.manager, non_list_prop)


@pytest.mark.parametrize(
    "pl_type", [
        'hipersockets',
        'smc-d',
        'ctc'
    ])
def test_partlink_crud(dpm_mode_cpcs, pl_type):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a partition link.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_partition_link_feature(cpc)

        print(f"Testing on CPC {cpc.name}")

        console = cpc.manager.client.consoles.console
        partlink_name = TEST_PREFIX + ' test_partlink_crud partlink1'
        partlink_name_new = partlink_name + ' new'

        # Ensure clean starting point
        try:
            partlink = console.partition_links.find(name=partlink_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                f"Deleting test partition link from previous run: "
                f"{partlink_name!r} on CPC {cpc.name}", UserWarning)
            partlink.delete()
        try:
            partlink = console.partition_links.find(name=partlink_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test partition link from previous run: "
                f"{partlink_name_new!r} on CPC {cpc.name}", UserWarning)
            partlink.delete()

        # Test creating the partition link.
        # For Hipersockets and SMC-D-type partition links, we create the
        # link with no partitions attached.
        # For CTC-type partition links, we attach one partition.

        partlink_input_props = {
            'cpc-uri': cpc.uri,
            'name': partlink_name,
            'description': 'Test partition link for zhmcclient end2end tests',
            'type': pl_type,
        }

        if pl_type == 'ctc':
            # Provide one partition to attach to.
            partitions = cpc.partitions.list(filter_args={'status': 'stopped'})
            if len(partitions) < 2:
                pytest.skip(f"CPC {cpc.name} has no two stopped partitions "
                            "for CTC partition link creation")
            part1, part2 = random.choices(partitions, k=2)
            adapters = cpc.adapters.list(filter_args={'type': 'fc'})
            if not adapters:
                pytest.skip(f"CPC {cpc.name} has no FICON-type adapters for "
                            "CTC partition link creation")
            adapter = random.choice(adapters)
            path = {
                'adapter-port-uri': adapter.uri,
                'connecting-adapter-port-uri': adapter.uri,
            }
            partlink_input_props['partitions'] = [part1.uri, part2.uri]
            partlink_input_props['paths'] = [path]
            partlink_input_props['devices-per-path'] = 1

        partlink_auto_props = {
            'cpc-name': cpc.name,
        }

        # The code to be tested
        partlink = console.partition_links.create(partlink_input_props)

        for pn, exp_value in partlink_input_props.items():
            assert partlink.properties[pn] == exp_value, (
                f"Unexpected value for property {pn!r} of partition link:\n"
                f"{partlink.properties!r}")
        partlink.pull_full_properties()
        for pn, exp_value in partlink_input_props.items():
            assert partlink.properties[pn] == exp_value, (
                f"Unexpected value for property {pn!r} of partition link:\n"
                f"{partlink.properties!r}")
        for pn, exp_value in partlink_auto_props.items():
            assert pn in partlink.properties, (
                f"Automatically returned property {pn!r} is not in "
                f"created partition link:\n{partlink!r}")
            assert partlink.properties[pn] == exp_value, (
                f"Unexpected value for property {pn!r} of partition link:\n"
                f"{partlink.properties!r}")

        # Test updating a property of the partition link

        new_desc = "Updated partition link description."

        # The code to be tested
        partlink.update_properties(dict(description=new_desc))

        assert partlink.properties['description'] == new_desc
        partlink.pull_full_properties()
        assert partlink.properties['description'] == new_desc

        # Test renaming the partition link

        # The code to be tested
        partlink.update_properties(dict(name=partlink_name_new))

        assert partlink.properties['name'] == partlink_name_new
        partlink.pull_full_properties()
        assert partlink.properties['name'] == partlink_name_new
        with pytest.raises(zhmcclient.NotFound):
            console.partition_links.find(name=partlink_name)

        # Test deleting the partition link

        # The code to be tested
        partlink.delete()

        with pytest.raises(zhmcclient.NotFound):
            console.partition_links.find(name=partlink_name_new)
