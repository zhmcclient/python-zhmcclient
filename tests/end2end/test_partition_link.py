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


import random
import uuid
from copy import copy
from pprint import pprint
import time
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    skipif_no_partition_link_feature, runtest_find_list, \
    runtest_get_properties, assert_properties, standard_partition_props

urllib3.disable_warnings()

# Properties in minimalistic PartitionLink objects (e.g. find_by_name())
PARTLINK_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in PartitionLink objects returned by list() without full props
PARTLINK_LIST_PROPS = ['object-uri', 'cpc-uri', 'name', 'state', 'type']

# Properties whose values can change between retrievals of PartitionLink objs
PARTLINK_VOLATILE_PROPS = []


def replace_expressions(obj, replacements):
    """
    Return a deep copy of the input object, with any string values that are
    expressions containing replacement strings in 'replacements', with the
    corresponding values from 'replacements'.

    This is used to be able to specify adapters and partitions in the testcases
    as strings such as 'adapter_1' and then get them replaced with actual
    adapter or partition objects.

    The function is called recursively while walking through the initially
    provided properties dict.

    Parameters:
      obj (dict or object): The input object. Initially, a dict with properties.
      replacements (dict): Replacement values.

    Returns:
      object: A deep copy of the input object, with any replacements made.
    """
    if isinstance(obj, dict):
        ret_obj = {}
        for name, value in obj.items():
            ret_obj[name] = replace_expressions(value, replacements)
        return ret_obj

    if isinstance(obj, list):
        ret_obj = []
        for value in obj:
            ret_obj.append(replace_expressions(value, replacements))
        return ret_obj

    if isinstance(obj, str):
        ret_obj = obj
        if any(map(lambda rep: rep in obj, replacements.keys())):
            ret_obj = eval(f'{obj}', replacements)  # pylint: disable=eval-used
        return ret_obj

    return copy(obj)


def wait_for_states(
        partition_link, states=('complete', 'incomplete'), timeout=30):
    """
    Wait for a partition link to reach one of the specified states.

    Raises:
      OperationTimeout: Timed out.
    """

    if timeout > 0:
        start_time = time.time()

    while True:
        try:
            partition_link.pull_properties(['state'])
            state = partition_link.properties['state']
            if state in states:
                return
        except ConnectionError:
            print("Retrying after ConnectionError while waiting for states "
                  f"{states} in partition link {partition_link.name!r} "
                  f"(currently has state {state}).")

        if timeout > 0:
            current_time = time.time()
            if current_time > start_time + timeout:
                raise zhmcclient.OperationTimeout(
                    f"Waiting for states {states} in partition link "
                    f"{partition_link.name} timed out (timeout: {timeout} s, "
                    f"currently has state {state}).)",
                    timeout)

        time.sleep(2)  # Avoid hot spin loop


@pytest.mark.parametrize(
    "pl_type", [
        'hipersockets',
        'smc-d',
        'ctc'
    ])
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
    "pl_type", [
        'hipersockets',
        'smc-d',
        'ctc'
    ])
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
        partlink_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
        partlink_name_new = partlink_name + ' new'

        # Test creating the partition link.
        # For Hipersockets and SMC-D-type partition links, we create the
        # link with no partitions attached.
        # For CTC-type partition links, we create the link with one path
        # and two initial partitions.

        partlink_input_props = {
            'cpc-uri': cpc.uri,
            'name': partlink_name,
            'description': 'Test partition link for zhmcclient end2end tests',
            'type': pl_type,
        }

        if pl_type == 'ctc':

            adapters = cpc.adapters.list(
                filter_args={'type': 'fc', 'state': 'online'})
            if len(adapters) < 1:
                pytest.skip(f"CPC {cpc.name} has no online FC adapters "
                            "for CTC partition link creation")
            adapter = random.choice(adapters)

            part1_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
            part1_props = standard_partition_props(cpc, part1_name)
            part1 = cpc.partitions.create(part1_props)
            part2_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
            part2_props = standard_partition_props(cpc, part2_name)
            part2 = cpc.partitions.create(part2_props)

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

        partlink = None
        try:
            # The code to be tested
            partlink = console.partition_links.create(partlink_input_props)

            wait_for_states(partlink)

            # Remove input properties that are not in data model or that are
            # different iindata model, so that we can check.
            if 'partitions' in partlink_input_props:
                del partlink_input_props['partitions']  # not in data model
            if 'paths' in partlink_input_props:
                del partlink_input_props['paths']  # different in data model

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

        finally:
            # Test deleting the partition link
            if partlink:
                wait_for_states(partlink)

                # The code to be tested
                partlink.delete()

                with pytest.raises(zhmcclient.NotFound):
                    console.partition_links.find(name=partlink_name_new)


PARTLINK_CREATE_DELETE_TESTCASES = [
    # testcases for the test_partlink_create() test function.
    # Each list item is a testcase that is defined with the following
    # tuple items:
    # - desc (string): description of the testcase.
    # - pl_type (string): Type of the partition link, as for its 'type' prop.
    # - input_props (dict): Input properties for the create() method.
    #   The test function adds these properties automatically:
    #   - cpc-uri
    #   - name
    #   - type
    # - exp_props (dict): Expected properties in the created partition link.
    #   The test function adds these properties automatically:
    #   - cpc-uri
    #   - name
    #   - type
    # - exp_exc_type (class): Exception that is expected to be raised during
    #   PartitionLink.create(), or None.
    (
        "Hipersockets with minimal input properties",
        'hipersockets',
        {},
        {
            'bus-connections': [],
            'starting-device-number': '7400',  # default
            'maximum-transmission-unit-size': 8,  # default
        },
        None
    ),
    (
        "SMC-D with minimal input properties",
        'smc-d',
        {},
        {
            'bus-connections': [],
            'starting-fid': 4096,  # default
        },
        None
    ),
    (
        "CTC with minimal input properties",
        'ctc',
        {
            'partitions': ['partition_1.uri', 'partition_2.uri'],
            'paths': [
                {
                    'adapter-port-uri': 'adapter_1.uri',  # Replaced
                    'connecting-adapter-port-uri': 'adapter_1.uri',  # Replaced
                },
            ],
        },
        {
            'paths': [
                {
                    'starting-device-number': '4000',
                    # 'devices': [
                    #     {
                    #         # ctc-endpoint
                    #     }
                    # ],
                    'adapter-port-info': {
                        'adapter-uri': 'adapter_1.uri',  # Replaced
                        'adapter-name': 'adapter_1.name',  # Replaced
                    },
                    'connecting-adapter-port-info': {
                        'adapter-uri': 'adapter_1.uri',  # Replaced
                        'adapter-name': 'adapter_1.name',  # Replaced
                    },
                },
            ],
            'devices-per-path': 4  # default
        },
        None
    ),
]


@pytest.mark.parametrize(
    "desc, pl_type, input_props, exp_props, exp_exc_type",
    PARTLINK_CREATE_DELETE_TESTCASES)
def test_partlink_create_delete(
        dpm_mode_cpcs,  # noqa: F811
        desc, pl_type, input_props, exp_props, exp_exc_type):
    # pylint: disable=redefined-outer-name, exec-used, unused-argument
    """
    Test creation of a partition link (and deletion, for cleanup)
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_partition_link_feature(cpc)

        print(f"Testing on CPC {cpc.name}")

        console = cpc.manager.client.consoles.console
        partlink_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
        replacements = {}  # Replacements for testcase expressions
        part1 = None
        part2 = None

        # For CTC, get two FC adapters and two stopped partitions
        if pl_type == 'ctc':

            adapters = cpc.adapters.list(
                filter_args={'type': 'fc', 'state': 'online'})
            if len(adapters) < 2:
                pytest.skip(f"CPC {cpc.name} has no two online FC adapters "
                            "for CTC partition link creation")
            adapter_1, adapter_2 = random.choices(adapters, k=2)
            replacements['adapter_1'] = adapter_1
            replacements['adapter_2'] = adapter_2

            part1_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
            part1_props = standard_partition_props(cpc, part1_name)
            part1 = cpc.partitions.create(part1_props)
            part2_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
            part2_props = standard_partition_props(cpc, part2_name)
            part2 = cpc.partitions.create(part2_props)
            replacements['partition_1'] = part1
            replacements['partition_2'] = part2

        # Prepare the input properties for PartitionLink.create()
        partlink_input_props = {
            'cpc-uri': cpc.uri,
            'name': partlink_name,
            'type': pl_type,
        }
        partlink_input_props.update(input_props)

        # Replace the variable names for adapters and partitions in the
        # input properties with real data.
        partlink_input_props = replace_expressions(
            partlink_input_props, replacements)

        partlink = None
        try:

            if exp_exc_type:
                with pytest.raises(exp_exc_type):

                    # The code to be tested
                    partlink = console.partition_links.create(
                        partlink_input_props)

            else:
                try:

                    # The code to be tested
                    partlink = console.partition_links.create(
                        partlink_input_props)

                except zhmcclient.PartitionLinkError as exc:
                    print("PartitionLinkError during PartitionLink.create(): "
                          f"{exc}")
                    print("Input properties of PartitionLink.create():")
                    pprint(partlink_input_props)
                    raise
                except zhmcclient.HTTPError as exc:
                    print(f"HTTPError during PartitionLink.create(): {exc}")
                    print("Input properties of PartitionLink.create():")
                    pprint(partlink_input_props)
                    raise

                wait_for_states(partlink)

                # Prepare the expected properties
                partlink_exp_props = {
                    'cpc-uri': cpc.uri,
                    'name': partlink_name,
                    'type': pl_type,
                }
                partlink_exp_props.update(exp_props)

                partlink_exp_props = replace_expressions(
                    partlink_exp_props, replacements)

                partlink.pull_full_properties()

                assert_properties(partlink.properties, partlink_exp_props)

        finally:
            # Cleanup, but also code to be tested
            wait_for_states(partlink)
            if partlink:
                partlink.delete()
            if part1:
                part1.delete()
            if part2:
                part2.delete()
            with pytest.raises(zhmcclient.NotFound):
                console.partition_links.find(name=partlink_name)


def test_partlink_zzz_cleanup(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name, exec-used, unused-argument
    """
    Cleanup any created partitions and partition links that may have not been
    cleaned up by the other testcase functions.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        skipif_no_partition_link_feature(cpc)

        print(f"Testing on CPC {cpc.name}")

        console = cpc.manager.client.consoles.console

        name_pattern = fr'{TEST_PREFIX}.*'
        partlinks = console.partition_links.findall(name=name_pattern)
        for partlink in partlinks:

            print("Deleting test partition link from a prior test run: "
                  f"{partlink.name!r} on CPC {cpc.name}")

            try:
                partlink.delete()
            except zhmcclient.HTTPError as exc:
                print(f"HTTPError during PartitionLink.delete(): {exc}")

        parts = cpc.partitions.findall(name=name_pattern)
        for part in parts:

            print("Deleting test partition from a prior test run: "
                  f"{part.name!r} on CPC {cpc.name}")

            try:
                part.delete()
            except zhmcclient.HTTPError as exc:
                print(f"HTTPError during Partition.delete(): {exc}")
