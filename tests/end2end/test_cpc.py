# Copyright 2019,2021 IBM Corp. All Rights Reserved.
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
End2end tests for CPCs.

These tests do not change any CPC properties.
"""


from datetime import timedelta, datetime, timezone
import pytest
from requests.packages import urllib3
import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import all_cpcs, classic_mode_cpcs, dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, assert_res_prop, runtest_find_list, \
    runtest_get_properties, validate_list_features, \
    cleanup_and_import_example_certificate, has_api_feature

urllib3.disable_warnings()

# Properties in minimalistic Cpc objects (e.g. find_by_name())
CPC_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Cpc objects returned by list() without full properties
CPC_LIST_PROPS = [
    'object-uri', 'name', 'status']
CPC_LIST_PROPS_Z15 = [
    'object-uri', 'name', 'status', 'has-unacceptable-status', 'dpm-enabled',
    'se-version']

# Properties whose values can change between retrievals
CPC_VOLATILE_PROPS = [
    'last-energy-advice-time',
    'zcpc-ambient-temperature',
    'zcpc-dew-point',
    'zcpc-exhaust-temperature',
    'zcpc-heat-load',
    'zcpc-heat-load-forced-air',
    'zcpc-heat-load-water',
    'zcpc-humidity',
    'zcpc-maximum-inlet-air-temperature',
    'zcpc-maximum-inlet-liquid-temperature',
    'zcpc-minimum-inlet-air-temperature',
    'zcpc-power-consumption',
    'cpc-power-consumption',
    'ec-mcl-description'  # TODO: Remove once 'last-update' volat. issue fixed
]

# Machine types with same max partitions for all models:
# Keep in sync with zhmcclient/_cpc.py.
MAX_PARTS_BY_TYPE = {
    '2817': 60,  # z196
    '2818': 30,  # z114
    '2827': 60,  # zEC12
    '2828': 30,  # zBC12
    '2964': 85,  # z13 / Emperor
    '2965': 40,  # z13s / Rockhopper
    '3906': 85,  # z14 / Emperor II
    '3907': 40,  # z14-ZR1 / Rockhopper II
    '8561': 85,  # z15-T01 / LinuxOne III (-LT1)
    '3931': 85,  # z16-A01
}

# Machine types with different max partitions across their models:
# Keep in sync with zhmcclient/_cpc.py.
MAX_PARTS_BY_TYPE_MODEL = {
    ('8562', 'T02'): 40,  # z15-T02
    ('8562', 'LT2'): 40,  # LinuxOne III (-LT2)
    ('8562', 'GT2'): 85,  # z15-GT2
}


def test_cpc_find_list(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test find/list methods for CPCs (any mode).
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition

    for cpc_name in hd.cpcs:
        print(f"Testing with CPC {cpc_name}")

        cpc_list_props = CPC_LIST_PROPS
        se_version = hd.cpcs[cpc_name].get('se_version', None)
        if se_version:
            se_version_info = tuple(map(int, se_version.split('.')))
            if se_version_info >= (2, 15, 0):
                cpc_list_props = CPC_LIST_PROPS_Z15

        runtest_find_list(
            hmc_session, client.cpcs, cpc_name, 'name', 'status',
            CPC_VOLATILE_PROPS, CPC_MINIMAL_PROPS, cpc_list_props)


def test_cpc_property(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    if not all_cpcs:
        pytest.skip("HMC definition does not include any CPCs")

    for cpc in all_cpcs:
        print(f"Testing with CPC {cpc.name}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(cpc.manager, non_list_prop)


def test_cpc_features(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test certain "features" of a CPC (any mode):
    - dpm_enabled property
    - maximum_active_partitions property
    - feature_enabled(feature_name)
    - feature_info()
    - list_api_features()
    """
    if not all_cpcs:
        pytest.skip("HMC definition does not include any CPCs")

    for cpc in all_cpcs:
        print(f"Testing with CPC {cpc.name}")

        cpc.pull_full_properties()
        cpc_mach_type = cpc.properties.get('machine-type', None)
        cpc_mach_model = cpc.properties.get('machine-model', None)
        cpc_features = cpc.properties.get('available-features-list', None)

        exp_cpc_props = dict(cpc.properties)

        # The code to be tested: dpm_enabled property
        dpm_enabled = cpc.dpm_enabled

        exp_dpm_enabled = exp_cpc_props.get('dpm-enabled', False)
        assert_res_prop(dpm_enabled, exp_dpm_enabled, 'dpm-enabled', cpc)

        # The code to be tested: maximum_active_partitions property
        max_parts = cpc.maximum_active_partitions

        exp_max_parts = exp_cpc_props.get('maximum-partitions', None)
        if cpc_mach_type and cpc_mach_model:
            if exp_max_parts is None:
                # Determine from tables
                try:
                    exp_max_parts = MAX_PARTS_BY_TYPE[cpc_mach_type]
                except KeyError:
                    exp_max_parts = MAX_PARTS_BY_TYPE_MODEL[
                        (cpc_mach_type, cpc_mach_model)]
        if exp_max_parts is not None:
            assert_res_prop(max_parts, exp_max_parts, 'maximum-partitions', cpc)

        # Test: feature_enabled(feature_name)
        feature_name = 'storage-management'
        if cpc_features is None:
            # The machine does not yet support features
            with pytest.raises(ValueError):
                # The code to be tested: feature_enabled(feature_name)
                cpc.feature_enabled(feature_name)
        else:
            features = [f for f in cpc_features if f['name'] == feature_name]
            if not features:
                # The machine generally supports features, but not this feature
                with pytest.raises(ValueError):
                    # The code to be tested: feature_enabled(feature_name)
                    cpc.feature_enabled(feature_name)
            else:
                # The machine supports this feature
                # The code to be tested: feature_enabled(feature_name)
                sm_enabled = cpc.feature_enabled(feature_name)
                exp_sm_enabled = features[0]['state']
                assert_res_prop(sm_enabled, exp_sm_enabled,
                                'available-features-list', cpc)

        # Test: feature_info()
        if cpc_features is None:
            # The machine does not yet support features
            with pytest.raises(ValueError):
                # The code to be tested: feature_info()
                cpc.feature_info()
        else:
            # The machine supports features
            # The code to be tested: feature_info()
            features = cpc.feature_info()
            # Note: It is possible that the feature list exists but is empty
            #       (e.g when a z14 HMC manages a z13)
            for i, feature in enumerate(features):
                assert 'name' in feature, (
                    f"Feature #{i} does not have the 'name' attribute "
                    f"in Cpc object for CPC {cpc.name}")
                assert 'description' in feature, (
                    f"Feature #{i} does not have the 'description' attribute "
                    f"in Cpc object for CPC {cpc.name}")
                assert 'state' in feature, (
                    f"Feature #{i} does not have the 'state' attribute "
                    f"in Cpc object for CPC {cpc.name}")

        # Test: list_api_features()
        client = zhmcclient.Client(cpc.manager.session)

        validate_list_features(client.query_api_version(),
                               cpc.list_api_features(),
                               cpc.list_api_features('cpc.*'))


def test_cpc_export_profiles(classic_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test for export_profiles(profile_area, wait_for_completion=True,
                             operation_timeout=None)

    Only for CPCs in classic mode, skipped in DPM mode.
    """
    if not classic_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in classic mode")

    for cpc in classic_mode_cpcs:
        assert not cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        print(f"Testing with CPC {cpc.name}")

        try:

            # The code to be tested
            _ = cpc.export_profiles(profile_area=1)

        except zhmcclient.HTTPError as exc:
            if exc.http_status == 403 and exc.reason == 1:
                skip_warn(
                    f"HMC userid {hd.userid!r} is not authorized for task "
                    f"'Export/Import Profile Data (API only)' on HMC {hd.host}")
            else:
                raise

        # TODO: Complete this test


def test_cpc_export_dpm_config(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test for export_dpm_configuration()

    Only for CPCs in DPM mode, skipped in classic mode.

    Note: export_dpm_configuration() is time-consuming and is invoked twice, so
    depending on the configuration of the CPCs, this test might easily run
    for 5 to 20 minutes!
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print(f"Testing on CPC {cpc.name}")

        cert, cert_props = (None, None)
        if has_api_feature('secure-boot-with-certificates', cpc):
            cert, cert_props = cleanup_and_import_example_certificate(cpc)

        config = cpc.export_dpm_configuration()
        full_config = \
            cpc.export_dpm_configuration(include_unused_adapters=True)

        assert len(config['adapters']) <= len(full_config['adapters'])

        if has_api_feature('secure-boot-with-certificates', cpc):
            assert len(config['certificates']) >= 1
            for exported_cert in config['certificates']:
                if exported_cert['name'] == cert_props['name']:
                    assert exported_cert['certificate'] == \
                           cert_props['certificate']
            cert.delete()


TESTCASES_CPC_GET_SUSTAINABILITY_DATA = [
    # Test cases for test_cpc_get_sustainability_data(), each as a tuple with
    # these items:
    # * tc: Testcase short description
    # * input_kwargs: kwargs to be used as input parameters for
    #   Cpc.get_sustainability_data()
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

CPC_METRICS = {
    # Metrics returned in "Get CPC Historical Sustainability Data" HMC
    # operation.
    # metric name: data type
    "total-wattage": int,
    "partition-wattage": int,
    "infrastructure-wattage": int,
    "unassigned-wattage": int,
    "heat-load": int,
    "heat-load-forced-air": int,
    "processor-utilization": int,
    "ambient-temperature": float,
    "exhaust-heat-temperature": float,
    "dew-point": float,
    "ambient-humidity": int,
}


@pytest.mark.parametrize(
    "tc, input_kwargs, exp_oldest, exp_delta",
    TESTCASES_CPC_GET_SUSTAINABILITY_DATA)
def test_cpc_get_sustainability_data(
        tc, input_kwargs, exp_oldest, exp_delta, all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Test for Cpc.get_sustainability_data(...)
    """
    for cpc in all_cpcs:

        session = cpc.manager.session
        hd = session.hmc_definition

        print(f"Testing with CPC {cpc.name}")

        try:

            # The code to be tested
            data = cpc.get_sustainability_data(**input_kwargs)

        except zhmcclient.HTTPError as exc:
            if exc.http_status == 403 and exc.reason == 1:
                skip_warn(
                    f"HMC userid {hd.userid!r} is not authorized for task "
                    f"'Environmental Dashboard' on HMC {hd.host}")
            elif exc.http_status == 404 and exc.reason == 1:
                skip_warn(
                    f"CPC {cpc.name} on HMC {hd.host} does not support "
                    f"feature: {exc}")
            else:
                raise

        now_dt = datetime.now(timezone.utc)
        exp_oldest_dt = now_dt - exp_oldest

        act_metric_names = set(data.keys())
        exp_metric_names = set(CPC_METRICS.keys())
        assert act_metric_names == exp_metric_names

        for metric_name, metric_array in data.items():
            metric_type = CPC_METRICS[metric_name]

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
                        print("Warning: Oldest data point of metric "
                              f"{metric_name!r} is not within 15 minutes of "
                              "range start: Oldest data point: "
                              f"{dp_timestamp_dt}, Range start: "
                              f"{exp_oldest_dt}, Delta: {delta_sec} sec")
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
                              "of its previous data point. Actual delta: "
                              f"{delta_td}, Expected delta: {exp_delta} "
                              f"(+/-{tolerance_pct}%)")

                previous_dt = dp_timestamp_dt


# Read-only tests:
# TODO: Test for get_wwpns(partitions)
# TODO: Test for get_free_crypto_domains(crypto_adapters=None)
# TODO: Test for get_energy_management_properties()
# TODO: Test for validate_lun_path(host_wwpn, host_port, wwpn, lun)
# TODO: Test for export_dpm_configuration(include_unused_adapters)

# Modifying tests:
# TODO: Test for update_properties(properties)
# TODO: Test for start(wait_for_completion=True, operation_timeout=None)
# TODO: Test for stop(wait_for_completion=True, operation_timeout=None)
# TODO: Test for import_profiles(profile_area, wait_for_completion=True,
#                                operation_timeout=None)
# TODO: Test for set_power_save(power_saving, wait_for_completion=True,
#                               operation_timeout=None)
# TODO: Test for set_power_capping(power_capping_state, power_cap=None,
#                                  wait_for_completion=True,
#                                  operation_timeout=None)
# TODO: Test for add_temporary_capacity(record_id, software_model=None,
#                                       processor_info=None, test=False,
#                                       force=False)
# TODO: Test for remove_temporary_capacity(record_id, software_model=None,
#                                          processor_info=None)
# TODO: Test for set_auto_start_list(auto_start_list)
# TODO: Test for import_dpm_configuration(dpm_configuration)
