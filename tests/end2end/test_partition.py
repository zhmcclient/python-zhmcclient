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


import warnings
import random
from datetime import timedelta, datetime, timezone
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
            skip_warn(f"No partitions on CPC {cpc.name} managed by "
                      f"HMC {hd.host}")
        part_list = pick_test_resources(part_list)

        for part in part_list:
            print(f"Testing on CPC {cpc.name} with partition {part.name!r}")
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

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the partitions to test with
        part_list = cpc.partitions.list()
        if not part_list:
            skip_warn(f"No partitions on CPC {cpc.name} managed by HMC "
                      f"{hd.host}")
        part_list = pick_test_resources(part_list)

        for part in part_list:
            print(f"Testing on CPC {cpc.name} with partition {part.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(part.manager, non_list_prop)


def test_part_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a partition.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print(f"Testing on CPC {cpc.name}")

        part_name = TEST_PREFIX + ' test_part_crud part1'
        part_name_new = part_name + ' new'

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
        try:
            part = cpc.partitions.find(name=part_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                f"Deleting test partition from previous run: {part_name_new!r} "
                f"on CPC {cpc.name}", UserWarning)
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
                f"Unexpected value for property {pn!r}"
        part.pull_full_properties()
        for pn, exp_value in part_input_props.items():
            assert part.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"
        for pn, exp_value in part_auto_props.items():
            assert part.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"

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
            skip_warn(
                f"No partitions on CPC {cpc.name} managed by HMC {hd.host}")

        test_part = None
        for part in part_list:

            # Test: List all messages (without begin or end)
            try:
                if DEBUG:
                    print("Debug: Test: Listing OS messages of partition "
                          f"{part.name} with no begin/end")
                result = part.list_os_messages()
            except zhmcclient.HTTPError as exc:
                if exc.http_status == 409 and exc.reason == 332:
                    # Meaning: The messages interface for the partition is not
                    # available
                    if DEBUG:
                        print(f"Debug: Partition {part.name} cannot list OS "
                              "messages")
                    continue
                raise

            all_messages = result['os-messages']
            if len(all_messages) >= 3:
                test_part = part
                break

            if DEBUG:
                print(f"Debug: Partition {part.name} has only "
                      f"{len(all_messages)} OS messages")

        if test_part is None:
            skip_warn(f"No partition on CPC {cpc.name} has the minimum number "
                      "of 3 OS messages for the test")

        # Test with begin/end selecting the full set of messages
        all_begin = all_messages[0]['sequence-number']
        all_end = all_messages[-1]['sequence-number']
        if DEBUG:
            print("Debug: Test: Listing OS messages of partition "
                  f"{test_part.name} with begin={all_begin}, end={all_end}")
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
            print("Debug: Test: Listing OS messages of partition "
                  f"{test_part.name} with begin={begin}, end={end}")
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
            skip_warn(f"No partitions on CPC {cpc.name} managed by HMC "
                      f"{hd.host} for the user {session.userid}")

        permitted_part_list = pick_test_resources(permitted_part_list)
        for partition in permitted_part_list:
            assert isinstance(partition, zhmcclient.Partition)
            for pname in exp_props:
                # The property is supposed to be in the result
                actual_pnames = list(partition.properties.keys())
                assert pname in actual_pnames, \
                    f"Actual partition: {partition!r}"

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


TESTCASES_PART_GET_SUSTAINABILITY_DATA = [
    # Test cases for test_part_get_sustainability_data(), each as a tuple with
    # these items:
    # * tc: Testcase short description
    # * input_kwargs: kwargs to be used as input parameters for
    #   Partition.get_sustainability_data()
    # * exp_oldest: expected delta time from now to oldest data point,
    #   as timedelta
    # * exp_delta: expected delta time between data points, as timedelta
    (
        "Default values (range=last-week, resolution=one-hour)",
        {},
        timedelta(days=7),
        timedelta(hours=1),
    ),
    (
        "range=last-day, resolution=one-hour",
        {
            "range": "last-day",
            "resolution": "one-hour",
        },
        timedelta(hours=24),
        timedelta(hours=1),
    ),
    (
        "range=last-day, resolution=fifteen-minutes",
        {
            "range": "last-day",
            "resolution": "fifteen-minutes",
        },
        timedelta(hours=24),
        timedelta(minutes=15),
    ),
]

PART_METRICS = {
    # Metrics returned in "Get Partition Historical Sustainability Data" HMC
    # operation.
    # metric name: data type
    "wattage": int,
    "processor-utilization": int,
}


@pytest.mark.parametrize(
    "tc, input_kwargs, exp_oldest, exp_delta",
    TESTCASES_PART_GET_SUSTAINABILITY_DATA)
def test_part_get_sustainability_data(
        tc, input_kwargs, exp_oldest, exp_delta,
        dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test for Partition.get_sustainability_data(...)
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        if hd.mock_file:
            skip_warn("zhmcclient mock does not support "
                      "Partition.get_sustainability_data()")

        # Pick the partition to test with
        part_list = cpc.partitions.list()
        if not part_list:
            skip_warn(
                f"No partitions on CPC {cpc.name} managed by HMC {hd.host}")

        # Pick a random partition to test with
        part = random.choice(part_list)

        session = part.manager.session
        hd = session.hmc_definition

        print(f"Testing with partition {part.name}")

        try:

            # The code to be tested
            data = part.get_sustainability_data(**input_kwargs)

        except zhmcclient.HTTPError as exc:
            if exc.http_status == 403 and exc.reason == 1:
                skip_warn(
                    f"HMC userid {hd.userid!r} is not authorized for task "
                    f"'Environmental Dashboard' on HMC {hd.host}")
            elif exc.http_status == 404 and exc.reason == 1:
                skip_warn(
                    f"Partition {part.name} on HMC {hd.host} does not support "
                    f"feature: {exc}")
            else:
                raise

        now_dt = datetime.now(timezone.utc)
        exp_oldest_dt = now_dt - exp_oldest

        act_metric_names = set(data.keys())
        exp_metric_names = set(PART_METRICS.keys())
        assert act_metric_names == exp_metric_names

        for metric_name, metric_array in data.items():
            metric_type = PART_METRICS[metric_name]

            first_item = True
            previous_dt = None
            for dp_item in metric_array:
                # We assume the order is oldest to newest

                assert 'data' in dp_item
                assert 'timestamp' in dp_item
                assert len(dp_item) == 2

                dp_data = dp_item['data']
                dp_timestamp_dt = dp_item['timestamp']

                assert isinstance(dp_data, metric_type), \
                    f"Invalid data type for metric {metric_name!r}"

                if first_item:
                    first_item = False

                    # Verify that the oldest timestamp is within a certain
                    # delta from the range start.
                    # There are cases where that is not satisfied, so we only
                    # issue only a warning (as opposed to failing).
                    delta_sec = abs((dp_timestamp_dt - exp_oldest_dt).seconds)
                    if delta_sec > 15 * 60:
                        print(f"Warning: Oldest data point of metric "
                              f"{metric_name!r} is not within 15 minutes of "
                              "range start: "
                              f"Oldest data point: {dp_timestamp_dt}, "
                              f"Range start: {exp_oldest_dt}, "
                              f"Delta: {delta_sec} sec")
                else:

                    # For second oldest timestamp on, verify that the delta
                    # to the previous data point is the requested resolution.
                    # There are cases where that is not satisfied, so we only
                    # issue only a warning (as opposed to failing).
                    tolerance_pct = 10
                    delta_td = abs(dp_timestamp_dt - previous_dt)
                    if abs(delta_td.seconds - exp_delta.seconds) > \
                            tolerance_pct / 100 * exp_delta.seconds:
                        print("Warning: Timestamp of a data point of metric "
                              f"{metric_name!r} is not within expected delta "
                              "of its previous data point. "
                              f"Actual delta: {delta_td}, "
                              f"Expected delta: {exp_delta} "
                              f"(+/-{tolerance_pct}%)")

                previous_dt = dp_timestamp_dt
