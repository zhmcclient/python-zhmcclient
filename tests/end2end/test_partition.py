# Copyright 2017,2021 IBM Corp. All Rights Reserved.
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
End2end tests for partitions (on CPCs in DPM mode).

These tests do not change any existing partitions, but create, modify and delete
test partitions.
"""

from __future__ import absolute_import, print_function

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
    standard_partition_props, runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Print debug messages in tests
DEBUG = False

# Properties in minimalistic Partition objects (e.g. find_by_name())
PART_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Partition objects returned by list() without full props
PART_LIST_PROPS = ['object-uri', 'name', 'status', 'type']

# Properties in Partition objects for list(additional_properties)
PART_ADDITIONAL_PROPS = ['description', 'short-name']

# Properties whose values can change between retrievals of Partition objects
PART_VOLATILE_PROPS = []


def test_part_find_list(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the partitions to test with
        part_list = cpc.partitions.list()
        if not part_list:
            skip_warn("No partitions on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))
        part_list = pick_test_resources(part_list)

        for part in part_list:
            print("Testing on CPC {c} with partition {p!r}".
                  format(c=cpc.name, p=part.name))
            runtest_find_list(
                session, cpc.partitions, part.name, 'name', 'status',
                PART_VOLATILE_PROPS, PART_MINIMAL_PROPS, PART_LIST_PROPS,
                PART_ADDITIONAL_PROPS)


def test_part_property(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the partitions to test with
        part_list = cpc.partitions.list()
        if not part_list:
            skip_warn("No partitions on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))
        part_list = pick_test_resources(part_list)

        for part in part_list:
            print("Testing on CPC {c} with partition {p!r}".
                  format(c=cpc.name, p=part.name))

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(
                client, part.manager, non_list_prop, (2, 16))


def test_part_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a partition.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print("Testing on CPC {c}".format(c=cpc.name))

        part_name = TEST_PREFIX + ' test_part_crud part1'
        part_name_new = part_name + ' new'

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
            part = cpc.partitions.find(name=part_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test partition from previous run: {p!r} on CPC {c}".
                format(p=part_name_new, c=cpc.name), UserWarning)
            status = part.get_property('status')
            if status != 'stopped':
                part.stop()
            part.delete()

        # Test creating the partition

        part_input_props = standard_partition_props(cpc, part_name)
        part_auto_props = {
            'status': 'stopped',
        }

        # The code to be tested
        part = cpc.partitions.create(part_input_props)

        for pn, exp_value in part_input_props.items():
            assert part.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        part.pull_full_properties()
        for pn, exp_value in part_input_props.items():
            assert part.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        for pn, exp_value in part_auto_props.items():
            assert part.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)

        # Test updating a property of the partition

        new_desc = "Updated partition description."

        # The code to be tested
        part.update_properties(dict(description=new_desc))

        assert part.properties['description'] == new_desc
        part.pull_full_properties()
        assert part.properties['description'] == new_desc

        # Test renaming the partition

        # The code to be tested
        part.update_properties(dict(name=part_name_new))

        assert part.properties['name'] == part_name_new
        part.pull_full_properties()
        assert part.properties['name'] == part_name_new
        with pytest.raises(zhmcclient.NotFound):
            cpc.partitions.find(name=part_name)

        # Test deleting the partition

        # The code to be tested
        part.delete()

        with pytest.raises(zhmcclient.NotFound):
            cpc.partitions.find(name=part_name_new)


def test_part_list_os_messages(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test "List OS Messages" operation on partitions
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        if hd.mock_file:
            skip_warn("zhmcclient mock does not support 'List OS Messages' "
                      "operation")

        # Pick the partition to test with
        part_list = cpc.partitions.list()
        if not part_list:
            skip_warn("No partitions on CPC {c} managed by HMC {h}".
                      format(c=cpc.name, h=hd.host))

        test_part = None
        for part in part_list:

            # Test: List all messages (without begin or end)
            try:
                if DEBUG:
                    print("Debug: Test: Listing OS messages of partition {} "
                          "with no begin/end".format(part.name))
                result = part.list_os_messages()
            except zhmcclient.HTTPError as exc:
                if exc.http_status == 409 and exc.reason == 332:
                    # Meaning: The messages interface for the partition is not
                    # available
                    if DEBUG:
                        print("Debug: Partition {} cannot list OS messages".
                              format(part.name))
                    continue
                raise

            all_messages = result['os-messages']
            if len(all_messages) >= 3:
                test_part = part
                break

            if DEBUG:
                print("Debug: Partition {} has only {} OS messages".
                      format(part.name, len(all_messages)))

        if test_part is None:
            skip_warn("No partition on CPC {c} has the minimum number of 3 OS "
                      "messages for the test".format(c=cpc.name))

        # Test with begin/end selecting the full set of messages
        all_begin = all_messages[0]['sequence-number']
        all_end = all_messages[-1]['sequence-number']
        if DEBUG:
            print("Debug: Test: Listing OS messages of partition {} with "
                  "begin={}, end={}".format(test_part.name, all_begin, all_end))
        result = test_part.list_os_messages(begin=all_begin, end=all_end)
        messages = result['os-messages']
        assert len(messages) == all_end - all_begin + 1
        assert messages == all_messages

        # Test with begin/end selecting a subset of messages
        while True:
            seq1 = random.choice(all_messages)['sequence-number']
            if seq1 not in {all_begin, all_end}:
                break
        while True:
            seq2 = random.choice(all_messages)['sequence-number']
            if seq2 not in {all_begin, all_end, seq1}:
                break
        begin = min(seq1, seq2)
        end = max(seq1, seq2)
        if DEBUG:
            print("Debug: Test: Listing OS messages of partition {} with "
                  "begin={}, end={}".format(test_part.name, begin, end))
        result = test_part.list_os_messages(begin=begin, end=end)
        messages = result['os-messages']
        assert len(messages) == end - begin + 1
        for message in messages:
            assert message in all_messages


# Full set of properties that are common on all types of partitions:
COMMON_PROPS_LIST = ['name', 'object-uri', 'type', 'status',
                     'has-unacceptable-status']
FULL_PROPS_LIST = COMMON_PROPS_LIST + [
    'initial-memory', 'maximum-memory', 'partition-id', 'processor-mode',
    'autogenerate-partition-id', 'boot-device', 'boot-network-device',
    'description', 'hba-uris', 'ifl-processors',
    'initial-ifl-processing-weight', 'nic-uris', 'partition-link-uris',
    'storage-group-uris', 'tape-link-uris', 'virtual-function-uris'
]
LIST_PERMITTED_PARTITION_TESTCASES = [
    # The list items are tuples with the following items:
    # - desc (string): description of the testcase.
    # - input_kwargs (dict): Input parameters for the function.
    # - exp_props (List) : Expected properties in the output
    (
        "Default parameters",
        dict(),
        COMMON_PROPS_LIST,
    ),
    (
        "full_properties",
        dict(
            full_properties=True,
        ),
        FULL_PROPS_LIST
    ),
    (
        "full_properties and filtering",
        dict(
            full_properties=True,
            filter_args={'type': 'linux'},
        ),
        FULL_PROPS_LIST
    ),
    (
        "Bad request in filter_args",
        dict(
            filter_args={'name': '@#1c'}
        ),
        COMMON_PROPS_LIST
    ),
    (
        "additional-properties",
        dict(
            additional_properties=['partition-id', 'tape-link-uris']
        ),
        COMMON_PROPS_LIST + ['partition-id', 'tape-link-uris']
    ),
]


@pytest.mark.parametrize(
    "desc, input_kwargs, exp_props",
    LIST_PERMITTED_PARTITION_TESTCASES)
def test_console_list_permitted_partitions(desc, input_kwargs, exp_props,
                                           dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name, unused-argument
    """
    Test list permitted partitions on a cpc
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled
        session = cpc.manager.session
        hd = session.hmc_definition
        client = zhmcclient.Client(session)
        console = client.consoles.console
        features = console.list_api_features()
        if 'additional_properties' in input_kwargs and \
                'dpm-ctc-partition-link-management' not in features and \
                'dpm-hipersockets-partition-link-management' not in features:
            pytest.skip("HMC does not support additional-properties parameter.")

        permitted_part_list = console.list_permitted_partitions(**input_kwargs)
        if not permitted_part_list:
            skip_warn("No partitions on CPC {c} managed by HMC {h} for "
                      "the user {u}".format(c=cpc.name, h=hd.host,
                                            u=session.userid))

        permitted_part_list = pick_test_resources(permitted_part_list)
        for partition in permitted_part_list:
            assert isinstance(partition, zhmcclient.Partition)
            for pname in exp_props:
                # The property is supposed to be in the result
                actual_pnames = list(partition.properties.keys())
                assert pname in actual_pnames, \
                    "Actual partition: {p!r}".format(p=partition)

        # Test list permitted partitions with filtering
        permitted_partitions_filter_agrs = (console.list_permitted_partitions(
            filter_args={'name': permitted_part_list[0].name,
                         'cpc-name': permitted_part_list[
                             0].manager.parent.name}))
        assert len(permitted_partitions_filter_agrs) == 1

        # Test list permitted partitions with bad filter args
        permitted_partitions_filter_agrs = (console.list_permitted_partitions(
            filter_args={'name': permitted_part_list[0].name,
                         'cpc-name': 'bad-cpc'}))
        assert len(permitted_partitions_filter_agrs) == 0
