# Copyright 2019-2021 IBM Corp. All Rights Reserved.
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

from __future__ import absolute_import, print_function

from requests.packages import urllib3
import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: disable=unused-import
from zhmcclient.testutils.cpc_fixtures import all_cpcs  # noqa: F401

urllib3.disable_warnings()

# Properties in minimalistic Cpc objects (e.g. find_by_name())
CPC_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in short Cpc objects (e.g. list() without full properties)
CPC_SHORT_PROPS = [
    'object-uri', 'name', 'status', 'has-unacceptable-status', 'dpm-enabled',
    'se-version', 'target-name']

# Properties whose values can change between retrievals
CPC_VOLATILE_PROPS = [
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
    'ec-mcl-description'  # TODO: Remove once 'last-update' volat. issue fixed
]


def assert_cpc_props(cpc, exp_props, ignore_values=None, prop_names=None):
    """
    Check the properties of a Cpc object.
    """
    checked_prop_names = set()
    for prop_name in exp_props:

        if prop_names is not None and prop_name not in prop_names:
            continue  # Only check properties in prop_names

        assert prop_name in cpc.properties, \
            "Property '{p}' not found in Cpc object '{c}'". \
            format(p=prop_name, c=cpc.name)

        if ignore_values is not None and prop_name not in ignore_values:
            act_value = cpc.properties[prop_name]
            exp_value = exp_props[prop_name]
            assert act_value == exp_value, \
                "Property '{p}' has unexpected value in Cpc object '{c}'". \
                format(p=prop_name, c=cpc.name)

        checked_prop_names.add(prop_name)

    extra_prop_names = set(cpc.properties.keys()) - checked_prop_names

    assert not extra_prop_names, \
        "The following properties were unexpectedly present in Cpc object " \
        "'{c}' : {e}".format(c=cpc.name, e=', '.join(extra_prop_names))


def get_cpc_props(session, cpc_uri):
    """
    Get CPC properties directly using the "Get CPC Properties" operation.
    """
    cpc_props = session.get(cpc_uri)
    return cpc_props


def test_cpc_find_list(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test find/list methods for CPCs:
    - find_by_name(name)
    - find(**filter_args)
      - name filter (cache/server-side)
    - findall(**filter_args)
      - no filter
      - name filter (cache/server-side)
      - status filter (client-side)
    - list(full_properties=False, filter_args=None)
      - no filter + short
      - name filter (cache/server-side) + full
      - name filter (cache/server-side) + short
      - status filter (client-side) + short
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for cpc_name in hd.cpcs:

        # The code to be tested: find_by_name(name)
        found_cpc = client.cpcs.find_by_name(cpc_name)

        # Get full properties directly, for comparison
        exp_cpc_props = get_cpc_props(hmc_session, found_cpc.uri)

        cpc_status = exp_cpc_props['status']  # a client-side filter property

        assert_cpc_props(
            found_cpc, exp_cpc_props, ignore_values=CPC_VOLATILE_PROPS,
            prop_names=CPC_MINIMAL_PROPS)

        # The code to be tested: find() with name filter (cache/server-side)
        found_cpc = client.cpcs.find(name=cpc_name)

        assert_cpc_props(
            found_cpc, exp_cpc_props, ignore_values=CPC_VOLATILE_PROPS,
            prop_names=CPC_MINIMAL_PROPS)

        # The code to be tested: findall() with no filter
        found_cpcs = client.cpcs.findall()

        assert len(found_cpcs) == len(hd.cpcs)
        assert cpc_name in [_cpc.name for _cpc in found_cpcs]
        found_cpc = [_cpc for _cpc in found_cpcs if _cpc.name == cpc_name][0]
        assert_cpc_props(
            found_cpc, exp_cpc_props, ignore_values=CPC_VOLATILE_PROPS,
            prop_names=CPC_SHORT_PROPS)

        # The code to be tested: findall() with name filter (server-side)
        found_cpcs = client.cpcs.findall(name=cpc_name)

        assert len(found_cpcs) == 1
        found_cpc = found_cpcs[0]
        assert_cpc_props(
            found_cpc, exp_cpc_props, ignore_values=CPC_VOLATILE_PROPS,
            prop_names=CPC_MINIMAL_PROPS)

        # The code to be tested: findall() with status filter (client-side)
        found_cpcs = client.cpcs.findall(status=cpc_status)

        assert len(found_cpcs) >= 1
        assert cpc_name in [_cpc.name for _cpc in found_cpcs]
        found_cpc = [_cpc for _cpc in found_cpcs if _cpc.name == cpc_name][0]
        assert_cpc_props(
            found_cpc, exp_cpc_props, ignore_values=CPC_VOLATILE_PROPS,
            prop_names=CPC_SHORT_PROPS)

        # The code to be tested: list() with no filter and short properties
        found_cpcs = client.cpcs.list()

        assert len(found_cpcs) == len(hd.cpcs)
        assert cpc_name in [_cpc.name for _cpc in found_cpcs]
        found_cpc = [_cpc for _cpc in found_cpcs if _cpc.name == cpc_name][0]
        assert_cpc_props(
            found_cpc, exp_cpc_props, ignore_values=CPC_VOLATILE_PROPS,
            prop_names=CPC_SHORT_PROPS)

        # The code to be tested: list() with name filter and full properties
        found_cpcs = client.cpcs.list(
            full_properties=True, filter_args=dict(name=cpc_name))

        assert len(found_cpcs) == 1
        found_cpc = found_cpcs[0]

        assert_cpc_props(
            found_cpc, exp_cpc_props, ignore_values=CPC_VOLATILE_PROPS)

        # The code to be tested: list() with name filter and short properties
        found_cpcs = client.cpcs.list(filter_args=dict(name=cpc_name))

        assert len(found_cpcs) == 1
        found_cpc = found_cpcs[0]
        assert_cpc_props(
            found_cpc, exp_cpc_props, ignore_values=CPC_VOLATILE_PROPS,
            prop_names=CPC_SHORT_PROPS)

        # The code to be tested: list() with status filter (client-side) and
        # short properties
        found_cpcs = client.cpcs.list(filter_args=dict(status=cpc_status))

        assert len(found_cpcs) >= 1
        assert cpc_name in [_cpc.name for _cpc in found_cpcs]
        found_cpc = [_cpc for _cpc in found_cpcs if _cpc.name == cpc_name][0]
        assert_cpc_props(
            found_cpc, exp_cpc_props, ignore_values=CPC_VOLATILE_PROPS,
            prop_names=CPC_SHORT_PROPS)

# Read-only tests:
# TODO: Test for dpm_enabled property
# TODO: Test for maximum_active_partitions property
# TODO: Test for feature_enabled(feature_name)
# TODO: Test for feature_info()
# TODO: Test for export_profiles(profile_area, wait_for_completion=True,
#                                operation_timeout=None)
# TODO: Test for get_wwpns(partitions)
# TODO: Test for get_free_crypto_domains(crypto_adapters=None)
# TODO: Test for get_energy_management_properties()
# TODO: Test for validate_lun_path(host_wwpn, host_port, wwpn, lun)
# TODO: Test for export_dpm_configuration()

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
