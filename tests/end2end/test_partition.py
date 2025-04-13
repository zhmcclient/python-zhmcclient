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
import uuid
from datetime import timedelta, datetime, timezone
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
from .utils import logger  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    standard_partition_props, runtest_find_list, runtest_get_properties, \
    pformat_as_dict, assert_res_prop, validate_firmware_features

urllib3.disable_warnings()

# Properties in minimalistic Partition objects (e.g. find_by_name())
PART_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Partition objects returned by list() without full props
PART_LIST_PROPS = ['object-uri', 'name', 'status', 'type']

# Properties in Partition objects for list(additional_properties)
PART_ADDITIONAL_PROPS = ['description', 'short-name']

# Properties whose values can change between retrievals of Partition objects
PART_VOLATILE_PROPS = []


def assert_ctc_partition_link(partlink, num_paths, num_partitions):
    """
    Assert that the partition link currently has the expected number of
    connections between partitions, and the expected number of paths.
    Each partition must be connected to every other partition.
    """
    paths = partlink.get_property('paths')

    act_num_paths = len(paths)
    assert act_num_paths == num_paths, (
        "Unexpected number of paths in CTC-type partition link "
        f"{partlink.name!r}:\n"
        f"  Expected: {num_paths}\n"
        f"  Actual: {act_num_paths}\n"
        "Partition link properties:\n"
        f"{pformat_as_dict(partlink.properties)}")

    # Number of connections between all partitions
    num_devices = int(num_partitions * (num_partitions - 1) / 2)

    for path in paths:
        act_num_devices = len(path['devices'])
        assert act_num_devices == num_devices, (
            "Unexpected number of partition connections in CTC-type "
            f"partition link {partlink.name!r}:\n"
            f"  Expected: {num_devices}\n"
            f"  Actual: {act_num_devices}\n"
            "Partition link properties:\n"
            f"{pformat_as_dict(partlink.properties)}")


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


def test_partition_features(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test features of the CPC of a partition:
    - For firmware features:
      - feature_enabled() - deprecated
      - firmware_feature_enabled()
      - feature_info()
      - list_firmware_features()
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the partition to test with
        part_list = cpc.partitions.list()
        if not part_list:
            skip_warn(
                f"No partitions on CPC {cpc.name} managed by HMC {hd.host}")
        part = random.choice(part_list)

        client = cpc.manager.client
        api_version_info = client.version_info()

        cpc.pull_properties(['available-features-list'])
        cpc_fw_features = cpc.prop('available-features-list', None)

        part.pull_properties(['available-features-list'])
        part_fw_features = part.prop('available-features-list', None)

        fw_feature_name = 'dpm-storage-management'
        if cpc_fw_features is None:
            # The machine does not yet support firmware features
            with pytest.raises(ValueError):
                # The code to be tested: feature_enabled()
                part.feature_enabled(fw_feature_name)
            enabled = part.firmware_feature_enabled(fw_feature_name)
            assert enabled is False
        else:

            # Verify that the feature lists of Partition and CPC are equal
            assert len(part_fw_features) == len(cpc_fw_features)
            part_state_by_name = {f['name']: f['state']
                                  for f in part_fw_features}
            for cpc_feature in cpc_fw_features:
                name = cpc_feature['name']
                assert name in part_state_by_name, (
                    f"Firmware feature {name!r} is available for CPC but not "
                    f"for partition {part.name!r}")
                part_enabled = part_state_by_name[name]
                cpc_enabled = cpc_feature['state']
                assert part_enabled == cpc_enabled, (
                    f"Firmware feature {name!r} has different enablement state "
                    f"on CPC {cpc_enabled} than on partition {part.name!r} "
                    f"({part_enabled})")

            if fw_feature_name not in part_state_by_name:
                # The machine generally supports firmware features, but this
                # feature is not available
                with pytest.raises(ValueError):
                    # The code to be tested: feature_enabled()
                    part.feature_enabled(fw_feature_name)
                # The code to be tested: firmware_feature_enabled()
                enabled = part.firmware_feature_enabled(fw_feature_name)
                assert enabled is False
            else:
                # The machine has this feature available
                # The code to be tested: feature_enabled()
                enabled = part.feature_enabled(fw_feature_name)
                exp_enabled = part_state_by_name[fw_feature_name]
                assert_res_prop(enabled, exp_enabled,
                                'available-features-list', cpc)
                # The code to be tested: firmware_feature_enabled()
                enabled = part.firmware_feature_enabled(fw_feature_name)
                assert enabled == exp_enabled
        # Test: feature_info()
        if cpc_fw_features is None:
            # The machine does not yet support features
            with pytest.raises(ValueError):
                # The code to be tested: feature_info()
                part.feature_info()
        else:
            # The machine supports features
            # The code to be tested: feature_info()
            features = part.feature_info()
            # Note: It is possible that the feature list exists but is empty
            #       (e.g when a z14 HMC manages a z13)
            for i, feature in enumerate(features):
                assert 'name' in feature, (
                    f"Feature #{i} does not have the 'name' attribute "
                    f"in Partition object for partition {part.name}")
                assert 'description' in feature, (
                    f"Feature #{i} does not have the 'description' attribute "
                    f"in Partition object for partition {part.name}")
                assert 'state' in feature, (
                    f"Feature #{i} does not have the 'state' attribute "
                    f"in Partition object for partition {part.name}")
        # The code to be tested: list_firmware_features()
        fw_features = part.list_firmware_features()
        validate_firmware_features(api_version_info, fw_features)


def test_part_list_os_messages(logger, dpm_mode_cpcs):  # noqa: F811
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
                logger.debug(
                    "Listing OS messages of partition %s with no begin/end",
                    part.name)
                result = part.list_os_messages()
            except zhmcclient.HTTPError as exc:
                if exc.http_status == 409 and exc.reason == 332:
                    # Meaning: The messages interface for the partition is not
                    # available
                    logger.debug(
                        "Partition %s cannot list OS messages", part.name)
                    continue
                raise

            all_messages = result['os-messages']
            if len(all_messages) >= 3:
                test_part = part
                break

            logger.debug(
                "Partition %s has only %d OS messages",
                part.name, len(all_messages))

        if test_part is None:
            skip_warn(f"No partition on CPC {cpc.name} has the minimum number "
                      "of 3 OS messages for the test")

        # Test with begin/end selecting the full set of messages
        all_begin = all_messages[0]['sequence-number']
        all_end = all_messages[-1]['sequence-number']
        logger.debug(
            "Listing OS messages of partition %s with begin=%s, end=%s",
            test_part.name, all_begin, all_end)
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
        logger.debug(
            "Listing OS messages of partition %s with begin=%s, end=%s",
            test_part.name, begin, end)
        result = test_part.list_os_messages(begin=begin, end=end)
        messages = result['os-messages']
        assert len(messages) == end - begin + 1
        for message in messages:
            assert message in all_messages


def test_part_create_os_websocket(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test "Get ASCII Console WebSocket URI" operation on partitions
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        if hd.mock_file:
            skip_warn("zhmcclient mock does not support 'Get ASCII Console "
                      "WebSocket URI' operation")

        # Pick the partition to test with
        active_part_list = cpc.partitions.list(filter_args={'status': 'active'})
        if not active_part_list:
            skip_warn(
                f"No partitions on CPC {cpc.name} managed by HMC {hd.host} "
                "with an active status")

        # Pick a random partition to test with
        part = random.choice(active_part_list)

        ws_uri = part.create_os_websocket()

        assert ws_uri.startswith('/api/websock/')


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


TESTCASES_PART_ATTACH_DETACH_NETWORK_LINK = [
    # Test cases for test_part_attach_detach_network_link(), each as a tuple
    # with these items:
    # * desc: Testcase short description
    # * type: Partition link type ("hipersockets", "smc-d")
    # * number_of_nics: Number of NICs to be created during attach
    # * nic_property_list: Properties of the NICs to be created during attach
    (
        "Hipersockets, 1 NIC with default properties",
        "hipersockets",
        1,
        []
    ),
    (
        "Hipersockets, 2 NICs with default properties",
        "hipersockets",
        2,
        []
    ),
    (
        "Hipersockets, 1 NIC with devno",
        "hipersockets",
        1,
        [
            {
                'device-number': '4711',
            },
        ]
    ),
    (
        "Hipersockets, 1 NIC with VLAN",
        "hipersockets",
        1,
        [
            {
                'vlan-id': 53,
            },
        ]
    ),
    (
        "SMC-D, 1 NIC with default properties",
        "smc-d",
        1,
        []
    ),
    (
        "SMC-D, 2 NICs with default properties",
        "smc-d",
        2,
        []
    ),
    (
        "SMC-D, 1 NIC with with devno",
        "smc-d",
        1,
        [
            {
                'device-number': '4711',
            },
        ]
    ),
    # Note: Disabled because it currently fails
    # (
    #     "SMC-D, 1 NIC with with FID",
    #     "smc-d",
    #     1,
    #     [
    #         {
    #             'fid': 53,
    #         },
    #     ]
    # ),
]


@pytest.mark.parametrize(
    "desc, type, number_of_nics, nic_property_list",
    TESTCASES_PART_ATTACH_DETACH_NETWORK_LINK)
def test_part_attach_detach_network_link(
        desc, type, number_of_nics, nic_property_list,
        dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument,redefined-builtin
    """
    Test for Partition.attach/detach_network_link()
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        console = cpc.manager.client.consoles.console
        session = cpc.manager.session
        hd = session.hmc_definition

        if hd.mock_file:
            skip_warn("zhmcclient mock does not support "
                      "Partition.attach/detach_network_link()")

        part = None
        partlink = None

        try:

            partlink_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
            partlink_input_props = {
                "name": partlink_name,
                "type": type,
                "cpc-uri": cpc.uri,
            }
            partlink = console.partition_links.create(partlink_input_props)
            part_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
            part = cpc.partitions.create(
                standard_partition_props(cpc, part_name))

            # The code to be tested
            part.attach_network_link(
                partlink, number_of_nics, nic_property_list)

            # Verify the partition link is now attached
            attached_pls = part.list_attached_partition_links()
            assert len(attached_pls) == 1
            attached_pl = attached_pls[0]
            assert attached_pl.uri == partlink.uri

            # Verify the number of NICs in the partition link data
            partlink.pull_full_properties()
            bc_list = partlink.get_property('bus-connections')
            assert len(bc_list) == 1   # = attached partitions
            bc = bc_list[0]
            assert bc["partition-uri"] == part.uri
            assert len(bc["nics"]) == number_of_nics

            # Verify the number of NIC element objects in the partition
            # Note: for SMC-D, NICs are not represented in the partition
            part.pull_full_properties()
            nics = part.nics.list()
            nic_uris = part.get_property('nic-uris')
            if type == "hipersockets":
                assert len(nics) == len(nic_uris) == number_of_nics
            else:  # type == "smc-d":
                assert len(nics) == len(nic_uris) == 0

            # The code to be tested
            part.detach_network_link(partlink)

            # Verify the partition link is no longer attached
            attached_pls = part.list_attached_partition_links()
            assert len(attached_pls) == 0

            # Verify the number of NICs in the partition link data
            partlink.pull_full_properties()
            bc_list = partlink.get_property('bus-connections')
            assert len(bc_list) == 0   # = attached partitions

            # Verify the number of NIC element objects in the partition
            # Note: for SMC-D, NICs are not represented in the partition
            part.pull_full_properties()
            nics = part.nics.list()
            nic_uris = part.get_property('nic-uris')
            if type == "hipersockets":
                # Note: Detaching a partition link currently does not delete
                # the NIC in the partition.
                if len(nics) > 0 or len(nic_uris) > 0:
                    # warnings.warn(
                    print("Debug: Detaching Hipersocket partition link did "
                          "not delete the NICs in the partition:\n"
                          f"{nic_uris}\n{nics}")
            else:  # type == "smc-d":
                assert len(nics) == len(nic_uris) == 0

        finally:
            if partlink:
                partlink.delete()
            if part:
                part.delete()


TESTCASES_PART_ATTACH_DETACH_CTC_LINK = [
    # Test cases for test_part_attach_detach_ctc_link(), each as a tuple
    # with these items:
    # * desc: Testcase short description
    # * num_partitions: Number of partitions for creating the PL
    # * num_paths: Number of paths for creating the PL
    (
        "2 partitions, 1 path",
        2,
        1,
    ),
    (
        "3 partitions, 2 paths",
        3,
        2,
    ),
]


@pytest.mark.parametrize(
    "desc, num_partitions, num_paths",
    TESTCASES_PART_ATTACH_DETACH_CTC_LINK)
def test_part_attach_detach_ctc_link(
        logger, dpm_mode_cpcs,  # noqa: F811
        desc, num_partitions, num_paths):
    # pylint: disable=redefined-outer-name,unused-argument,redefined-builtin
    """
    Test for Partition.attach/detach_ctc_link()
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        logger.debug("Testing with CPC %s", cpc.name)

        console = cpc.manager.client.consoles.console
        session = cpc.manager.session
        hd = session.hmc_definition

        if hd.mock_file:
            skip_warn("zhmcclient mock does not support "
                      "Partition.attach/detach_ctc_link()")

        pl_parts = []
        partlink = None
        test_part = None

        try:

            # Select the adapters for the paths of the partition link.
            # We use the same adapter for each connection, because if we use
            # different adapters, we cannot determine which ones actually do
            # have a physical connection.
            adapters = cpc.adapters.list(
                filter_args={'type': 'fc', 'status': 'active'})
            if len(adapters) < num_paths:
                pytest.skip(f"CPC {cpc.name} has less than {num_paths} "
                            "online FC adapters for CTC")
            path_adapters = random.sample(adapters, num_paths)

            # Create the initial partitions for the partition link
            for i in range(0, num_partitions):
                part_name = f"{TEST_PREFIX}_{i}_{uuid.uuid4().hex}"
                logger.debug("Preparing properties for creation of initial "
                             "PL partition %s", part_name)
                part_props = standard_partition_props(cpc, part_name)
                logger.debug("Creating initial PL partition %s", part_name)
                part = cpc.partitions.create(part_props)
                pl_parts.append(part)

            # Create the partition link
            partlink_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
            paths = []
            for i in range(0, num_paths):
                path = {
                    "adapter-port-uri": path_adapters[i].uri,
                    "connecting-adapter-port-uri": path_adapters[i].uri,
                }
                paths.append(path)
            partlink_input_props = {
                "name": partlink_name,
                "type": 'ctc',
                "cpc-uri": cpc.uri,
                "partitions": [p.uri for p in pl_parts],
                "paths": paths,
            }
            logger.debug("Creating partition link %s", partlink_name)
            partlink = console.partition_links.create(partlink_input_props)

            logger.debug("Partition link after creation (default properties):\n"
                         "%s", pformat_as_dict(partlink.properties))
            partlink.pull_full_properties()
            logger.debug("Partition link after creation (full properties):\n"
                         "%s", pformat_as_dict(partlink.properties))
            assert_ctc_partition_link(partlink, num_paths, num_partitions)

            # Create the test partition (to which the PL is attached)
            test_part_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
            logger.debug("Preparing properties for creation of "
                         "test partition %s", test_part_name)
            test_part_props = standard_partition_props(cpc, test_part_name)
            logger.debug("Creating test partition %s", test_part_name)
            test_part = cpc.partitions.create(test_part_props)

            # Verify the partition link is not attached.
            # The code to be tested
            attached_pls = test_part.list_attached_partition_links()
            assert len(attached_pls) == 0

            logger.debug("Attaching partition link to test partition")

            # The code to be tested
            test_part.attach_ctc_link(partlink)
            num_partitions += 1

            partlink.pull_full_properties()
            logger.debug("Partition link after attach (full properties):\n"
                         "%s", pformat_as_dict(partlink.properties))
            assert_ctc_partition_link(partlink, num_paths, num_partitions)

            # Verify the partition link is now attached.
            # The code to be tested
            attached_pls = test_part.list_attached_partition_links()
            assert len(attached_pls) == 1
            attached_pl = attached_pls[0]
            assert attached_pl.uri == partlink.uri

            logger.debug("Detaching partition link from test partition")

            # The code to be tested
            test_part.detach_ctc_link(partlink)
            num_partitions -= 1

            partlink.pull_full_properties()
            logger.debug("Partition link after detach (full properties):\n"
                         "%s", pformat_as_dict(partlink.properties))
            assert_ctc_partition_link(partlink, num_paths, num_partitions)

            # Verify the partition link is no longer attached.
            # The code to be tested
            attached_pls = test_part.list_attached_partition_links()
            assert len(attached_pls) == 0

        finally:
            if partlink:
                logger.debug("Deleting partition link %s", partlink.name)
                partlink.delete()
            if test_part:
                logger.debug("Deleting test partition %s", test_part.name)
                test_part.delete()
            for part in pl_parts:
                logger.debug("Deleting initial PL partition %s", part.name)
                part.delete()
