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
Utility functions for end2end tests.
"""


import os
import re
import random
import time
import warnings
import logging
from copy import deepcopy
import pprint
from collections.abc import Mapping, MappingView
import pytest

import zhmcclient
from zhmcclient.testutils import LOG_FORMAT_STRING, LOG_DATETIME_FORMAT, \
    LOG_DATETIME_TIMEZONE

# Prefix used for names of resources that are created during tests
TEST_PREFIX = 'zhmcclient_tests_end2end'


@pytest.fixture(scope='function')
def logger(request):
    """
    Pytest fixture that provides a logger for an end2end test function.

    This functionm creates a logger named after the test function.
    Using this fixture as an argument in a test function resolves to that
    logger.

    Logging is enabled by setting the env var TESTLOGFILE. If logging is
    enabled, the logger is set to debug level, otherwise the logger is disabled.

    During setup of the fixture, a log entry for entering the test function
    is written, and during teardown of the fixture, a log entry for leaving
    the test function is written.

    Because this fixture is called for each invocation of a test
    function, it ends up being called multiple times within the same Python
    process. Therefore, the logger is created only when it does not exist yet.

    Returns:
        logging.Logger: Logger for the test function
    """

    log_file = os.getenv('TESTLOGFILE', None)
    if log_file:
        logging.Formatter.converter = LOG_DATETIME_TIMEZONE
        log_formatter = logging.Formatter(
            LOG_FORMAT_STRING, datefmt=LOG_DATETIME_FORMAT)
        log_handler = logging.FileHandler(log_file, encoding='utf-8')
        log_handler.setFormatter(log_formatter)

    testfunc_name = request.function.__name__
    testfunc_logger = logging.getLogger(testfunc_name)

    if log_file and log_handler not in testfunc_logger.handlers:
        testfunc_logger.addHandler(log_handler)

    if log_file:
        testfunc_logger.setLevel(logging.DEBUG)
    else:
        testfunc_logger.setLevel(logging.NOTSET)

    testfunc_logger.debug("Entered test function")
    try:
        yield testfunc_logger
    finally:
        testfunc_logger.debug("Leaving test function")


class End2endTestWarning(UserWarning):
    """
    Python warning indicating an issue with an end2end test.
    """
    pass


def assert_properties(act_obj, exp_obj):
    """
    Check that actual properties match expected properties.

    The expected properties may specify only a subset of the actual properties.
    Only the expected properties are checked.

    The property values may have any type, including nested dictionaries and
    lists. For nested dictionaries and lists, each item is matched recursively.

    Parameters:
      act_obj (dict): The actual object. Initially, a dict with properties.
      exp_obj (dict): The expected object. Initially, a dict with properties.
    """
    if isinstance(exp_obj, dict):
        for name, exp_value in exp_obj.items():
            assert name in act_obj, (
                f"Expected property {name!r} is not in actual properties:\n"
                f"{act_obj!r}")
            act_value = act_obj[name]
            assert_properties(act_value, exp_value)
    elif isinstance(exp_obj, list):
        for i, exp_value in enumerate(exp_obj):
            act_value = act_obj[i]
            assert_properties(act_value, exp_value)
    else:
        assert act_obj == exp_obj, (
            f"Unexpected value: {act_obj!r}; Expected: {exp_obj!r}")


def assert_res_props(res, exp_props, ignore_values=None, prop_names=None):
    """
    Check the properties of a resource object.
    """
    res_props = dict(res.properties)
    # checked_prop_names = set()
    for prop_name in exp_props:

        if prop_names is not None and prop_name not in prop_names:
            continue  # Only check properties in prop_names

        assert prop_name in res_props, (
            f"Property {prop_name!r} not found in {res.prop('class')} "
            f"object {res.name!r}")

        if ignore_values is not None and prop_name not in ignore_values:
            act_value = res_props[prop_name]
            exp_value = exp_props[prop_name]
            assert_res_prop(act_value, exp_value, prop_name, res)

        # checked_prop_names.add(prop_name)

    # extra_prop_names = set(res_props.keys()) - checked_prop_names

    # TODO: Decide whether we want to check the exact set, or the minimum set.
    # assert not extra_prop_names, (
    #     "The following properties were unexpectedly present in "
    #     f"{res.prop('class')} object{res.name!r} : "
    #     f"{', '.join(extra_prop_names)}")


def assert_res_prop(act_value, exp_value, prop_name, res):
    """
    Check a property of a resource object.
    """
    assert act_value == exp_value, (
        f"Property {prop_name!r} has unexpected value in {res.prop('class')} "
        f"object {res.name!r}: Expected: {exp_value!r}, actual: {act_value!r}")


def _res_name(item):
    """Return the resource name, used by pick_test_resources()"""
    if isinstance(item, (tuple, list)):
        return item[0].name
    return item.name


def pick_test_resources(res_list):
    """
    Return the list of resources to be tested.

    The env.var "TESTRESOURCES" controls which resources are picked for the
    test, as follows:

    * 'random': (default) one random choice from the input list of resources.
    * 'all': the complete input list of resources.
    * '<pattern>': The resources with names matching the regexp pattern.

    Parameters:

      res_list (list of zhmcclient.BaseResource or tuple thereof):
        List of resources to pick from. Tuple items are a resource and its
        parent resources.

    Returns:

      list of zhmcclient.BaseResource: Picked list of resources.
    """

    test_res = os.getenv('TESTRESOURCES', 'random')

    if test_res == 'random':
        return [random.choice(res_list)]

    if test_res == 'all':
        return sorted(res_list, key=_res_name)

    # match the pattern
    ret_list = []
    for item in res_list:
        if re.search(test_res, _res_name(item)):
            ret_list.append(item)
    return sorted(ret_list, key=_res_name)


def runtest_find_list(session, manager, name, server_prop, client_prop,
                      volatile_props, minimal_props, list_props, add_props=None,
                      unique_name=True):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Run tests for find/list methods for a resource type:
    - find_by_name(name) (only if not unique_name)
    - pull_full_properties()
    - find(**filter_args)
      - server-side filter
    - findall(**filter_args)
      - no filter
      - server-side filter
      - client-side filter
    - list(full_properties=False, filter_args=None, additional_properties=None)
      - no filter + short
      - no filter + additional_properties
      - server-side filter + full
      - server-side filter + short
      - client-side filter + short

    Parameters:

      session (zhmcclient.Session): Session to an HMC.

      manager (zhmcclient.BaseManager): Manager for listing the resources.

      name (string): Name of resource to be found.

      server_prop (string): Name of resource property for server-side filtering,
        or None for no tests with server-side filtering.

      client_prop (string): Name of resource property for client-side filtering,
        or None for no tests with client-side filtering.

      volatile_props (list of string): Names of properties that are ignored when
        comparing resources because they are volatile.

      minimal_props (list of string): Names of properties that are in
        minimalistic resources (e.g. returned by find_by_name()).

      list_props (list of string): Names of properties that are returned by
        list()).

      add_props (list of string): Names of additional properties to be returned
        by list(additional_properties)). If None, the additional properties test
        is not executed.

      unique_name (bool): Indicates that the resource name is expected to be
        unique within its parent resource. That is normally the case, the only
        known exception are storage volumes in HMC 2.14.0 (they were introduced
        in 2.14.0 and made unique in 2.14.1).
    """
    if unique_name:
        # The code to be tested: find_by_name(name)
        found_res = manager.find_by_name(name)

        # Get full properties directly, for comparison
        exp_props = session.get(found_res.uri)

        if client_prop:
            client_value = exp_props[client_prop]

        if server_prop:
            server_value = exp_props[server_prop]

        # Get the object-id of the resource from its URI
        oid = found_res.uri.split('/')[-1]
        oid_prop = manager._oid_prop  # pylint: disable=protected-access

        assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                         prop_names=minimal_props)

        # The code to be tested: find(oid), for optimized lookup
        found_res = manager.find(**{oid_prop: oid})

        assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                         prop_names=minimal_props)

        # The code to be tested: pull_full_properties()
        found_res.pull_full_properties()

        assert_res_props(found_res, exp_props, ignore_values=volatile_props)

        if server_prop:
            # The code to be tested: find() with server-side filter
            found_res = manager.find(**{server_prop: server_value})

            assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                             prop_names=minimal_props)

            # The code to be tested: findall() with server-side filter
            found_res_list = manager.findall(**{server_prop: server_value})

            assert len(found_res_list) == 1
            found_res = found_res_list[0]
            assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                             prop_names=minimal_props)

        if client_prop:
            # The code to be tested: findall() with client-side filter
            # pylint: disable=used-before-assignment
            found_res_list = manager.findall(**{client_prop: client_value})

            assert name in map(lambda _res: _res.name, found_res_list)
            found_res_list = list(filter(lambda _res: _res.name == name,
                                         found_res_list))
            found_res = found_res_list[0]
            if len(found_res_list) > 1:
                raise AssertionError(
                    f"{found_res.prop('class')} findall(client_filter) result "
                    f"with non-unique name {name!r}: {found_res_list}")
            assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                             prop_names=list_props)

        if server_prop:
            # Code to be tested: list() with server-side filter and full props
            found_res_list = manager.list(
                full_properties=True, filter_args={server_prop: server_value})

            assert len(found_res_list) == 1
            found_res = found_res_list[0]
            assert_res_props(found_res, exp_props, ignore_values=volatile_props)

        if server_prop:
            # Code to be tested: list() with server-side filter and short props
            found_res_list = manager.list(
                filter_args={server_prop: server_value})

            assert len(found_res_list) == 1
            found_res = found_res_list[0]
            assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                             prop_names=minimal_props)

        if client_prop:
            # Code to be tested: list() with client-side filter and short props
            found_res_list = manager.list(
                filter_args={client_prop: client_value})

            assert name in [_res.name for _res in found_res_list]
            found_res = [_res for _res in found_res_list
                         if _res.name == name][0]
            assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                             prop_names=minimal_props)

    # The code to be tested: findall() with no filter
    found_res_list = manager.findall()

    assert name in map(lambda _res: _res.name, found_res_list)
    found_res_list = list(filter(lambda _res: _res.name == name,
                                 found_res_list))
    found_res = found_res_list[0]
    if len(found_res_list) > 1:
        found_uri_list = [r.uri for r in found_res_list]
        parent = manager.parent
        uri_str = '\n'.join(found_uri_list)
        raise AssertionError(
            f"{found_res.prop('class')} findall() result for "
            f"{parent.prop('class')} {parent.name!r} has non-unique name "
            f"{name!r} for the following {len(found_res_list)} objects:\n"
            f"{uri_str}")
    assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                     prop_names=list_props)

    # The code to be tested: list() with no filter and short properties
    found_res_list = manager.list()

    # Because we have only the expected properties for the resource with
    # the specified name, we only compare that one resource.
    assert name in map(lambda _res: _res.name, found_res_list)
    found_res_list = list(filter(lambda _res: _res.name == name,
                                 found_res_list))
    found_res = found_res_list[0]
    if len(found_res_list) > 1:
        raise AssertionError(
            f"{found_res.prop('class')} list() result with non-unique name "
            f"{name!r}: {found_res_list}")
    assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                     prop_names=list_props)

    if add_props is not None:
        # The code to be tested: list() with no filter and additional properties
        found_res_list = manager.list(additional_properties=add_props)

        # Because we have only the expected properties for the resource with
        # the specified name, we only compare that one resource.
        assert name in map(lambda _res: _res.name, found_res_list)
        found_res_list = list(filter(lambda _res: _res.name == name,
                                     found_res_list))
        found_res = found_res_list[0]
        if len(found_res_list) > 1:
            raise AssertionError(
                f"{found_res.prop('class')} list() result with non-unique "
                f"name {name!r}: {found_res_list}")
        assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                         prop_names=list_props + add_props)


def runtest_get_properties(manager, non_list_prop):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Run tests for pull_full_properties/pull_properties/get_property/prop
    methods for a resource type.

    Parameters:

      manager (zhmcclient.BaseManager): Manager for listing the resources.

      non_list_prop (string): Name of a resource property that is not returned
        with the List HMC operation.
    """

    assert isinstance(manager, zhmcclient.BaseManager)

    # Indicates whether pull_properties() is expected to pull just the
    # specified properties. We make this dependent only on whether the
    # mock support for the resource implements it, and not on the HMC
    # version, because the zhmcclient mock support only implements the
    # latest CPC and HMC generation, for simplicity.
    supports_properties = manager.supports_properties

    # Part 1: First chunk of methods to be tested

    # Get a fresh resource with list properties
    manager.invalidate_cache()
    resources = manager.list()
    resource = random.choice(resources)

    local_pnames = set(resource.properties.keys())
    local_pnames_plus = local_pnames | {non_list_prop}

    # Validate that the non_list_prop property is not listed.
    # This is really just checking that the testcase was invoked correctly.
    assert non_list_prop not in local_pnames, (
        f"non_list_prop={non_list_prop!r}, local_pnames={local_pnames!r}")

    # Validate initial state of the resource w.r.t. properties
    assert resource.full_properties is False

    # Validate that get_property() does not pull additional properties
    for pname in local_pnames:
        _ = resource.get_property(pname)
        assert resource.full_properties is False, \
            f"resource={resource!r}"
        current_pnames = set(resource.properties.keys())
        assert current_pnames == local_pnames, (
            f"current_pnames={current_pnames!r}, local_pnames={local_pnames!r}")

    # Validate that prop() does not pull additional properties
    for pname in local_pnames:
        _ = resource.prop(pname)
        assert resource.full_properties is False, \
            f"resource={resource!r}"
        current_pnames = set(resource.properties.keys())
        assert current_pnames == local_pnames, (
            f"current_pnames={current_pnames!r}, local_pnames={local_pnames!r}")

    # Validate that get_property() on non_list_prop pulls full properties
    _ = resource.get_property(non_list_prop)
    assert resource.full_properties is True, \
        f"resource={resource!r}"
    current_pnames = set(resource.properties.keys())
    assert current_pnames > local_pnames_plus, (
        f"current_pnames={current_pnames!r}, "
        f"local_pnames_plus={local_pnames_plus!r}")

    # Part 2: Second chunk of methods to be tested

    # Get a fresh resource with list properties
    manager.invalidate_cache()
    resources = manager.list()
    resource = random.choice(resources)

    local_pnames = set(resource.properties.keys())
    local_pnames_plus = local_pnames | {non_list_prop}

    # Validate initial state of the resource w.r.t. properties
    assert resource.full_properties is False

    # Validate that pull_properties() with no properties does not fetch props
    if supports_properties:
        prior_pnames = set(resource.properties.keys())
        resource.pull_properties([])
        current_pnames = set(resource.properties.keys())
        assert current_pnames == prior_pnames, (
            f"current_pnames={current_pnames!r}, "
            f"prior_pnames={prior_pnames!r}")

    # Validate pull_properties() with a non-list-result property
    resource.pull_properties([non_list_prop])
    current_pnames = set(resource.properties.keys())
    if supports_properties:
        # We get just the specified property in addition
        assert current_pnames == local_pnames_plus, (
            f"current_pnames={current_pnames!r}, "
            f"local_pnames_plus={local_pnames_plus!r}")
        assert resource.full_properties is False, \
            f"resource={resource!r}"
    else:
        # We get the full set of properties
        assert resource.full_properties is True, \
            f"resource={resource!r}"

    # Part 3: Third chunk of methods to be tested

    # Get a fresh resource with list properties
    manager.invalidate_cache()
    resources = manager.list()
    resource = random.choice(resources)

    local_pnames = set(resource.properties.keys())
    assert resource.full_properties is False

    # Validate that pull_full_properties() pulls full properties
    resource.pull_full_properties()
    assert resource.full_properties is True
    current_pnames = set(resource.properties.keys())
    assert current_pnames > local_pnames_plus, (
        f"current_pnames={current_pnames!r}, "
        f"local_pnames_plus={local_pnames_plus!r}")

    # Validate that pull_properties() with non_list_prop still has full props
    resource.pull_properties([non_list_prop])
    assert resource.full_properties is True


def validate_api_features(
        api_version_info, all_features, filtered_features, name_filter):
    """
    Tests the (already retrieved) results of calls to list_api_features().

    Can be used for validating the corresponding method results on Console and
    CPC objects.

    Parameters:

        api_version_info (tuple(int,int)): HMC API version, as int tuple

        all_features (list(string)): Result of a call to list_api_features()

        filtered_features (list(string)): Result of a call to
          list_api_features(name_filter)

        name_filter (string): The name filter
    """
    assert len(filtered_features) <= len(all_features)

    if api_version_info < (4, 10):
        # API features aren't supported prior 4.10, list must be empty
        assert len(all_features) == 0
        assert len(filtered_features) == 0
        return

    # Even when API features are supported, the lists can still be empty.
    # (for example when HMC/SE driver wasn't restarted after features
    # where enabled)
    if len(all_features) > 0:
        # But when there are some available API features, there are a few that
        # are always present.
        exp_features = [
            'cpc-install-and-activate',
            'cpc-delete-retrieved-internal-code',
            'dpm-smcd-partition-link-management',
            'report-a-problem',
        ]
        exp_filtered_features = []
        exp_rest_features = []
        for fn in exp_features:
            if re.match(name_filter, fn):
                exp_filtered_features.append(fn)
            else:
                exp_rest_features.append(fn)
        for feature in exp_features:
            assert feature in all_features
        for feature in exp_filtered_features:
            assert feature in filtered_features
        for feature in exp_rest_features:
            assert feature not in filtered_features


def validate_firmware_features(api_version_info, features):
    """
    Tests the (already retrieved) results of calls to list_firmware_features().

    Can be used for validating the corresponding method results on CPC and
    Partition objects.

    Parameters:

        api_version_info (tuple(int,int)): HMC API version, as int tuple

        features (list(string)): Result of a call to list_firmware_features()
    """
    if api_version_info < (2, 23):
        # Firmware features aren't supported prior 2.23, list must be empty
        assert len(features) == 0
        return

    # Even when firmware features are supported, the lists can still be empty.
    # (for example when HMC/SE driver wasn't restarted after features
    # where enabled)
    if len(features) > 0:
        # But when there are some available firmware features, there are a few
        # that are always present and enabled.
        exp_features = ['dpm-storage-management']
        for name in exp_features:
            assert name in features, (
                f"HMC did not return firmware feature {name!r} as enabled")


def skipif_no_storage_mgmt_feature(cpc):
    """
    Skip the test if the "DPM Storage Management" feature is not enabled for
    the specified CPC, or if the CPC does not yet support it.
    """
    try:
        smf = cpc.feature_enabled('dpm-storage-management')
    except ValueError:
        smf = False
    if not smf:
        skip_warn("DPM Storage Mgmt feature not enabled or not supported "
                  f"on CPC {cpc.name}")


def skipif_storage_mgmt_feature(cpc):
    """
    Skip the test if the "DPM Storage Management" feature is enabled for
    the specified CPC.
    """
    try:
        smf = cpc.feature_enabled('dpm-storage-management')
    except ValueError:
        smf = False
    if smf:
        skip_warn(f"DPM Storage Mgmt feature enabled on CPC {cpc.name}")


def skipif_no_group_support(client):
    """
    Skip the test if the HMC version does not support groups yet.
    """
    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 13, 0):
        skip_warn(
            f"HMC has version {hmc_version} and does not yet support groups")


def skipif_no_secure_boot_feature(cpc):
    """
    Skip the test if the API feature "secure-boot-with-certificates" isn't
    available on the specified CPC & console.
    """
    _skipif_api_feature_not_on_cpc_and_hmc("secure-boot-with-certificates", cpc)


def _skipif_api_feature_not_on_cpc_and_hmc(feature, cpc):
    """
    Skip the test if the given API feature isn't available on the specified CPC
     and its console.
    """
    cpc_features = cpc.list_api_features()

    if feature not in cpc_features:
        skip_warn(f"API feature {feature} not available on CPC {cpc.name}")

    console = cpc.manager.client.consoles.console
    console_features = console.list_api_features()
    if feature not in console_features:
        skip_warn(f"API feature {feature} not available on HMC {console.name}")


def skipif_no_partition_link_feature(cpc):
    """
    Skip the test if not all of the Partition Link related API features are
    enabled for the specified CPC, or if the CPC does not yet support all of
    them:

    * "dpm-smcd-partition-link-management"
    * "dpm-hipersockets-partition-link-management"
    * "dpm-ctc-partition-link-management"

    Note that there are code levels for z16 where only SMC-D is enabled, but not
    Hipersockets and CTC.
    """
    has_all_features = (
        has_api_feature(
            "dpm-smcd-partition-link-management", cpc) and  # noqa: W504
        has_api_feature(
            "dpm-hipersockets-partition-link-management", cpc) and  # noqa: W504
        has_api_feature(
            "dpm-ctc-partition-link-management", cpc))
    if not has_all_features:
        skip_warn("The partition link related API features are not all enabled "
                  f"or not all supported on CPC {cpc.name}")


def has_api_feature(feature, cpc):
    """
    Returns True if the given API feature is available on the specified CPC
    and its console.
    """
    cpc_features = cpc.list_api_features()
    console = cpc.manager.client.consoles.console
    console_features = console.list_api_features()

    return feature in cpc_features and feature in console_features


def standard_partition_props(cpc, part_name):
    """
    Return the input properties for a standard partition in the specified CPC.
    """
    part_input_props = {
        'name': part_name,
        'description': 'Test partition for zhmcclient end2end tests',
        'initial-memory': 1024,
        'maximum-memory': 2048,
        'processor-mode': 'shared',  # used for filtering
        'type': 'linux',  # used for filtering
    }

    # Get the properties used lateron, to improve performance.
    cpc.pull_properties([
        'processor-count-ifl',
        'processor-count-general-purpose',
    ])

    if cpc.prop('processor-count-ifl'):
        part_input_props['ifl-processors'] = 2
    elif cpc.prop('processor-count-general-purpose'):
        part_input_props['cp-processors'] = 2
    else:
        part_input_props['cp-processors'] = 1
        pc_names = filter(lambda p: p.startswith('processor-count-'),
                          cpc.properties.keys())
        pc_list = [f"{n}={cpc.properties[n]}" for n in pc_names]
        warnings.warn(
            f"CPC {cpc.name} shows neither IFL nor CP processors, "
            "specifying 1 CP for partition creation. "
            f"CPC processor-count properties are: {', '.join(pc_list)}",
            End2endTestWarning)

    return part_input_props


def skip_warn(msg):
    """
    Issue an End2endTestWarning and skip the current pytest testcase with the
    specified message.
    """
    warnings.warn(msg, End2endTestWarning, stacklevel=2)
    pytest.skip(msg)


def cleanup_and_import_example_certificate(cpc):
    """
    Removes any existing example certificate, then imports an example
    certificate.

    The certificate is valid until 2033-04-15, but should probably be regularly
    renewed.

    Returns the imported Certificate objects and the dict used for import
    """
    console = cpc.manager.console

    cert_name = f"{TEST_PREFIX} timestamp {time.strftime('%H.%M.%S')}"
    cert_name_new = cert_name + ' updated'

    try:
        cert = console.certificates.find(name=cert_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            f"Deleting test cert from previous run: {cert_name!r} on CPC "
            f"{cpc.name}", UserWarning)
        cert.delete()
    try:
        cert = console.certificates.find(name=cert_name_new)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            f"Deleting test cert from previous run: {cert_name_new!r} on "
            f"CPC {cpc.name}", UserWarning)
        cert.delete()
    props = {
        # pylint: disable=line-too-long
        "certificate": "MIIFdjCCA14CCQCILyUhzc9RUjANBgkqhkiG9w0BAQsFADB9MQswCQYDVQQGEwJVUzELMAkGA1UECAwCTlkxDzANBgNVBAcMBkFybW9uazETMBEGA1UECgwKemhtY2NsaWVudDETMBEGA1UECwwKemhtY2NsaWVudDEmMCQGA1UEAwwdaHR0cHM6Ly9naXRodWIuY29tL3pobWNjbGllbnQwHhcNMjMwNDE4MDY0OTAyWhcNMzMwNDE1MDY0OTAyWjB9MQswCQYDVQQGEwJVUzELMAkGA1UECAwCTlkxDzANBgNVBAcMBkFybW9uazETMBEGA1UECgwKemhtY2NsaWVudDETMBEGA1UECwwKemhtY2NsaWVudDEmMCQGA1UEAwwdaHR0cHM6Ly9naXRodWIuY29tL3pobWNjbGllbnQwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQDH8F7xMisAESV35LqjC3p6AsrGZ3kEOE5W8wcy0q7TEF9TO7TsAPdWit0e7WT20R1gYErv9uyFJeI4idIjWgTT8GVPixwcXClyywh/ND54voHrMZdbDGbvs5+wcfX/7BDtjRUtzuMtvDswEZqaQU/2W+rDRpb/FolwXDTNm17dSomegm7sw8xQsZGACkU2GPXarJcHWrgytyVghxbIPEvtrOP8XQf/FIBud6Z7/WFONFPSYVFkkmxCM/hOPJBj0CvG6WXV0yNN9a10lcy0yVel0JfX9g0FM0FH4H8pSKEqV2byTcoQjlKQehsuw49TzKEU5pEcdwIz5sMN2XOy8V0bHuoIyoZ54NpkVtqPAMr5MQjvluuiZnU5/6shVfJjChHfYHZQ/rRQbnJhIaKTXgfCUKjm/RrzHwMhy71upSDmhKDB2A5Z1o/pOsHqwUPDW17GBNmFDE/SnbpHhGxemnWWebfxTredFQ6YAy+zThDCXTzglSLsgi64ThDJsHN32/PEa0IiXM6moeRPZOK2NapFF8jFq8WYXvlk0Ianfl9TvgrfEufVx2o+V/0DUxo7TxeoukRuHWsJ7SGfFnWUhoj75mJxgvVLA82SdgTllPWYXTIJBUZ+XsoauOsH+VkDoNINEU3pQOySZj5dzzTYwglnLTBOP8KGxA5zLXSRleSFqwIDAQABMA0GCSqGSIb3DQEBCwUAA4ICAQAXnZZoJgo8I8zOHoQQa0Ocik9k9MCeO7M0gPtD+Xe9JRfoMolxaEZnezmADuJTCepUOUi1cgZXCScmDer2Zc2Y9pldJKhAitBiaajUrTfd0Dl8Gd8WGip8NN+8L9CsELZ+/hQnTG2GHGwi21s/yWt4yT3h2cIViuBqRvNTaxkMh1Devtzlx7haVjNCcDO5muIVBTBynJiaQV5zRaTYiLh+hT6O4OccOHJfnRdFkBRCnnCXE4qtrJg9XJ+NqkP3y0MBZueeQsdnmz9LgSwTiQHWgBI7nJSk0sLgw4AaT18xaZsx9xalKDcy7PN9Ya8IldcG4z+DP2cAoZsKejbZBfsvkV/gYC0g/LxBw0sGJrDaFc8BGDeJRxqwrpsJC8YnXFDi5/SwKII0CpOtb2MxwZC2uzmA9srnV05ta8MbdIQ2xsA8T0MDkTjOPqpJDUg9cqXZbOEOiUywJpYG6XxJdkbxx+IYyOyv8Rn0kLwwAgml7JF3w75fCDKwMw2gEY/0inqtS2NleA8XmA+CZ16YTTBQobyLUrsauVmJm4adRKFgq1OxCRbCGPeRRtD772cpAue2ZTD6Oa8UQlCkEdmXQYjp2PoguWmFI/X9T9P4oREZ182hP4b3EFr2WAhH2waURJmXVATR8IsvKxkSbBxCdVn1zhD55zuOBNLX5f4kq/4ipQ==",  # noqa: E501
        "description":
            "Example certificate for end2end tests.",
        "name": cert_name,
        "type": "secure-boot"
    }

    return console.certificates.import_certificate(cpc, props), props


class StatusError(Exception):
    """
    Indicates that a desired status cannot be reached.
    """
    pass


def ensure_lpar_inactive(lpar):
    """
    Ensure that the LPAR is inactive, regardless of what its current status is.

    If this function returns, the status of the LPAR will be 'not-activated'.

    If that status cannot be reached within the operation and status timeout
    of the session, StatusError is raised.

    Parameters:

      lpar (zhmcclient.Lpar): The LPAR (must exist).

    Raises:

      StatusError: The inactive status cannot be reached.
      zhmcclient.CeasedExistence: The LPAR no longer exists.
      zhmcclient.Error: Any zhmcclient exception can happen, except
        OperationTimeout and StatusTimeout (which result in StatusError).
    """
    org_status = pull_lpar_status(lpar)
    if org_status == 'not-activated':
        return

    try:
        lpar.deactivate(force=True)
    except zhmcclient.OperationTimeout:
        status = pull_lpar_status(lpar)
        timeout = lpar.manager.session.retry_timeout_config.operation_timeout
        raise StatusError(
            f"Could not get LPAR {lpar.name!r} from status {org_status!r} into "
            f"status 'not-activated' within operation timeout {timeout}; "
            f"current status is: {status!r}")
    except zhmcclient.StatusTimeout:
        status = pull_lpar_status(lpar)
        timeout = lpar.manager.session.retry_timeout_config.status_timeout
        raise StatusError(
            f"Could not get LPAR {lpar.name!r} from status {org_status!r} into "
            f"status 'not-activated' within status timeout {timeout}; "
            f"current status is: {status!r}")

    # This is just an additional check which should not fail.
    status = pull_lpar_status(lpar)
    if status != 'not-activated':
        raise StatusError(
            f"Could not get LPAR {lpar.name!r} from status {org_status!r} into "
            "status 'not-activated' for unknown reasons; "
            f"current status is: {status!r}")


def set_resource_property(resource, name, value):
    """
    Set a property on a zhmcclient resource to a value and return the current
    value (retrieved freshly from the HMC).

    Parameters:

      resource (zhmcclient.BaseResource): The resource (e.g. LPAR).
      name (string): Name of the property.
      value (object): New value for the property.

    Returns:

      object: Old value of the property.

    Raises:

      zhmcclient.CeasedExistence: The resource no longer exists.
      zhmcclient.Error: Any zhmcclient exception can happen, except
        OperationTimeout and StatusTimeout.
    """
    resource.pull_full_properties()
    old_value = resource.get_property(name)
    resource.update_properties({name: value})
    return old_value


def pull_lpar_status(lpar):
    """
    Retrieve the current LPAR status on the HMC as fast as possible and return
    it.

    LPAR status values and their meaning:

    Status         Resources allocated  OS running  Notes
    ---------------------------------------------------------------------------
    not-activated  no                   no
    not-operating  yes                  no          All CPUs are stopped
    operating      yes                  yes         No degradations
    exceptions     yes                  yes         Some CPUs are stopped

    Note that the status "acceptable" is only shown on the SE GUI, but will
    never appear at the WS-API.

    Raises:

      zhmcclient.CeasedExistence: The LPAR no longer exists.
      zhmcclient.Error: Any zhmcclient exception can happen.
    """
    lpars = lpar.manager.cpc.lpars.list(filter_args={'name': lpar.name})
    if len(lpars) != 1:
        raise zhmcclient.CeasedExistence(lpar.uri)
    this_lpar = lpars[0]
    actual_status = this_lpar.get_property('status')
    return actual_status


def is_cpc_property_hmc_inventory(name):
    """
    Return whether a CPC property defined in the HMC inventory file is
    actually a CPC property (vs. a special property).
    """
    special_properties = (
        'loadable_lpars',
        'load_profiles',
    )
    return name not in special_properties


def skip_missing_api_feature(
        console, console_feature, cpc=None, cpc_feature=None):
    """
    Skip pytest testcase if an HMC Console or CPC API feature is not
    available.
    """
    client = console.manager.client

    api_version_info = client.version_info()
    if api_version_info < (4, 10):
        pytest.skip(
            f"HMC API version {'.'.join(map(str, api_version_info))} is below "
            "minimum version 4.10 required for API features")

    if console_feature:
        if not console.list_api_features(console_feature):
            pytest.skip(
                f"Console API feature {console_feature!r} is not available")

    if cpc_feature:
        if not cpc.list_api_features(cpc_feature):
            pytest.skip(
                f"CPC API feature {cpc_feature!r} is not available for "
                f"CPC {cpc.name!r}")


def pformat_as_dict(dict_):
    """
    Return the pretty-printed dict-like input object, where any MappingView or
    Mapping has been replaced with a standard dict, and any tuple has been
    replaced with a standard list.
    """
    return pprint.pformat(
        copy_dict(dict_), indent=2, width=160, sort_dicts=False, compact=True)


def copy_dict(dict_):
    """
    Return a deep copy of the dict-like input object, where any MappingView or
    Mapping has been replaced with a standard dict.
    """
    ret = {}
    for k, v in dict_.items():
        if isinstance(v, (Mapping, MappingView)):
            v = copy_dict(v)
        elif isinstance(v, (list, tuple)):
            v = copy_list(v)
        else:
            v = deepcopy(v)
        ret[k] = v
    return ret


def copy_list(list_):
    """
    Return a deep copy of the list-like input object, where any list or tuple
    has been replaced with a standard list.
    """
    ret = []
    for v in list_:
        if isinstance(v, (Mapping, MappingView)):
            v = copy_dict(v)
        elif isinstance(v, (list, tuple)):
            v = copy_list(v)
        else:
            v = deepcopy(v)
        ret.append(v)
    return ret
