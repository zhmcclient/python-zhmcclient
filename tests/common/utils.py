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
Utility functions for tests.
"""

import sys
import os
import logging
from dateutil import tz

import zhmcclient
from zhmcclient_mock._hmc import FakedBaseResource, \
    FakedMetricGroupDefinition, FakedMetricObjectValues

# Logger names by log component
LOGGER_NAMES = {
    'all': '',  # root logger
    'api': zhmcclient.API_LOGGER_NAME,
    'hmc': zhmcclient.HMC_LOGGER_NAME,
}

DEFAULT_LOG = 'all=warning'

DEFAULT_RT_CONFIG = zhmcclient.RetryTimeoutConfig(
    connect_timeout=10,
    connect_retries=1,
    operation_timeout=300,
    status_timeout=60,
)


def assert_resources(resources, exp_resources, prop_names):
    """
    Assert that a list of resource objects is equal to an expected list of
    resource objects (or faked resource objects).

    This is done by comparing:
    - The resource URIs, making sure that the two lists have matching URIs.
    - The specified list of property names.

    Parameters:

      resources (list): List of BaseResource objects to be checked.

      exp_resources (list): List of BaseResource or FakedResource objects
        defining the expected number of objects and property values.

      prop_names (list): List of property names to be checked. If `None`, all
        properties in the expected resource object are checked.
    """

    # Assert the resource URIs
    uris = {res.uri for res in resources}
    exp_uris = {res.uri for res in exp_resources}
    assert uris == exp_uris, \
        f"Unexpected URIs: got: {uris}, expected: {exp_uris}"

    for res in resources:

        # Search for the corresponding expected resource
        exp_res = None
        for _exp_res in exp_resources:
            if _exp_res.uri == res.uri:
                exp_res = _exp_res
                break
        assert exp_res is not None

        # Assert the property names to be checked
        if prop_names is None:
            _prop_names = exp_res.properties.keys()
        else:
            _prop_names = prop_names
        for prop_name in _prop_names:

            # Not all resources in a list result have all properties
            # (e.g. Crypto adapter does not have 'port-count'), so we check
            # the property on the actual resource only when the expected
            # resource has the property.
            if prop_name in exp_res.properties:

                assert prop_name in res.properties, (
                    f"Expected property {prop_name!r} missing in resource "
                    f"{res.name!r}: Resource: {res!r}")

                prop_value = res.properties[prop_name]
                exp_prop_value = exp_res.properties[prop_name]
                assert prop_value == exp_prop_value, (
                    f"Unexpected value for property {prop_name!r} in resource "
                    f"{res.name!r}: got: {prop_value!r}, expected: "
                    f"{exp_prop_value!r}, resource: {res!r}")


def info(capsys, format_str, format_args=None):
    """
    Print an information message during test execution that is not being
    captured by py.test (i.e. it is shown even when py.test is not invoked
    with '-s').

    Parameters:

      capsys: The pytest 'capsys' fixture the testcase function must specify as
        an argument and pass to this function here.

      format_str (string): Percent-based format string.

      format_args: Argument(s) for the format string.
    """

    if format_args is not None:
        msg = (format_str % format_args)
    else:
        msg = format_str

    with capsys.disabled():
        print(msg)


def print_logging():
    """
    Debug function that prints the relevant settings of all Python loggers
    that are relevant for zhmcclient.
    """
    logger_names = LOGGER_NAMES.values()
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        print_logger(logger)


def print_logger(logger):
    """
    Debug function that prints the relevant settings of a Python logger.
    """
    print(f"Debug: Logger {logger.name!r}:")
    print(f"Debug:   logger level: {logger.level} "
          f"({logging.getLevelName(logger.level)})")
    if not logger.handlers:
        print("Debug:   No handlers")
    for handler in logger.handlers:
        print(f"Debug:   Handler {type(handler)}:")
        print(f"Debug:     handler level: {handler.level} "
              f"({logging.getLevelName(handler.level)})")
        _fmt = getattr(handler.formatter, '_fmt', None)
        print(f"Debug:     handler format: {_fmt!r}")


def setup_logging():
    """
    Set up logging for the zhmcclient, based on the value of the ZHMC_LOG
    env. variable with the following value::

        COMP=LEVEL[,COMP=LEVEL[,...]]

    Where:

      * ``COMP`` is one of: ``all``, ``api``, ``hmc``.
      * ``LEVEL`` is one of: ``error``, ``warning``, ``info``, ``debug``.

    If the variable is not set, this defaults to::

        all=warning
    """

    log = os.environ.get('ZHMC_LOG', None)

    if log is None:
        log = DEFAULT_LOG

    log_components = LOGGER_NAMES.keys()

    for lc in log_components:
        reset_logger(lc)

    handler = logging.StreamHandler(stream=sys.stderr)
    fs = '%(levelname)s %(name)s: %(message)s'
    handler.setFormatter(logging.Formatter(fs))

    log_specs = log.split(',')
    for log_spec in log_specs:

        # ignore extra ',' at begin, end or in between
        if log_spec == '':
            continue

        try:
            log_comp, log_level = log_spec.split('=', 1)
        except ValueError:
            raise ValueError("Missing '=' in COMP=LEVEL specification "
                             f"in ZHMC_LOG variable: {log_spec}")

        level = getattr(logging, log_level.upper(), None)
        if level is None:
            raise ValueError("Invalid level in COMP=LEVEL specification "
                             f"in ZHMC_LOG variable: {log_spec}")

        if log_comp not in log_components:
            raise ValueError("Invalid component in COMP=LEVEL specification "
                             f"in ZHMC_LOG variable: {log_spec}")

        setup_logger(log_comp, handler, level)


def reset_logger(log_comp):
    """
    Reset the logger for the specified log component (unless it is the root
    logger) to add a NullHandler if it does not have any handlers. Having a
    handler prevents a log request to be propagated to the parent logger.
    """

    name = LOGGER_NAMES[log_comp]
    logger = logging.getLogger(name)

    if name != '' and not logger.handlers:
        logger.addHandler(logging.NullHandler())


def setup_logger(log_comp, handler, level):
    """
    Setup the logger for the specified log component to add the specified
    handler (removing a possibly present NullHandler) and to set it to the
    specified log level. The handler is also set to the specified log level
    because the default level of a handler is 0 which causes it to process all
    levels.
    """

    name = LOGGER_NAMES[log_comp]
    logger = logging.getLogger(name)

    for h in logger.handlers:
        if isinstance(h, logging.NullHandler):
            logger.removeHandler(h)

    handler.setLevel(level)
    logger.addHandler(handler)
    logger.setLevel(level)


def assert_equal_hmc(hmc1, hmc2):
    """
    Assert that two FakedHmc objects are equal.
    """
    assert hmc1.api_version == hmc2.api_version
    assert hmc1.hmc_name == hmc2.hmc_name
    assert hmc1.hmc_version == hmc2.hmc_version
    assert hmc1.enabled == hmc2.enabled

    consoles1 = hmc1.consoles.list()
    consoles2 = hmc2.consoles.list()
    assert len(consoles1) == len(consoles2)
    for i, console1 in enumerate(consoles1):
        console2 = consoles2[i]
        assert_equal_resource(console1, console2)

        users1 = console1.users.list()
        users2 = console2.users.list()
        assert len(users1) == len(users2)
        for j, user1 in enumerate(users1):
            user2 = users2[j]
            assert_equal_resource(user1, user2)

        user_roles1 = console1.user_roles.list()
        user_roles2 = console2.user_roles.list()
        assert len(user_roles1) == len(user_roles2)
        for j, user_role1 in enumerate(user_roles1):
            user_role2 = user_roles2[j]
            assert_equal_resource(user_role1, user_role2)

        user_patterns1 = console1.user_patterns.list()
        user_patterns2 = console2.user_patterns.list()
        assert len(user_patterns1) == len(user_patterns2)
        for j, user_pattern1 in enumerate(user_patterns1):
            user_pattern2 = user_patterns2[j]
            assert_equal_resource(user_pattern1, user_pattern2)

        password_rules1 = console1.password_rules.list()
        password_rules2 = console2.password_rules.list()
        assert len(password_rules1) == len(password_rules2)
        for j, password_rule1 in enumerate(password_rules1):
            password_rule2 = password_rules2[j]
            assert_equal_resource(password_rule1, password_rule2)

        tasks1 = console1.tasks.list()
        tasks2 = console2.tasks.list()
        assert len(tasks1) == len(tasks2)
        for j, task1 in enumerate(tasks1):
            task2 = tasks2[j]
            assert_equal_resource(task1, task2)

        lsds1 = console1.ldap_server_definitions.list()
        lsds2 = console2.ldap_server_definitions.list()
        assert len(lsds1) == len(lsds2)
        for j, lsd1 in enumerate(lsds1):
            lsd2 = lsds2[j]
            assert_equal_resource(lsd1, lsd2)

        # Do not compare unmanaged CPCs, since they are not dumped.

        storage_groups1 = console1.storage_groups.list()
        storage_groups2 = console2.storage_groups.list()
        assert len(storage_groups1) == len(storage_groups2)
        for j, storage_group1 in enumerate(storage_groups1):
            storage_group2 = storage_groups2[j]
            assert_equal_resource(storage_group1, storage_group2)

            storage_volumes1 = storage_group1.storage_volumes.list()
            storage_volumes2 = storage_group2.storage_volumes.list()
            assert len(storage_volumes1) == len(storage_volumes2)
            for k, storage_volume1 in enumerate(storage_volumes1):
                storage_volume2 = storage_volumes2[k]
                assert_equal_resource(storage_volume1, storage_volume2)

    cpcs1 = hmc1.cpcs.list()
    cpcs2 = hmc1.cpcs.list()
    assert len(cpcs1) == len(cpcs2)
    for i, cpc1 in enumerate(cpcs1):
        cpc2 = cpcs2[i]
        assert_equal_resource(cpc1, cpc2)

        cgs1 = cpc1.capacity_groups.list()
        cgs2 = cpc2.capacity_groups.list()
        assert len(cgs1) == len(cgs2)
        for j, cg1 in enumerate(cgs1):
            cg2 = cgs2[j]
            assert_equal_resource(cg1, cg2)

        partitions1 = cpc1.partitions.list()
        partitions2 = cpc2.partitions.list()
        assert len(partitions1) == len(partitions2)
        for j, partition1 in enumerate(partitions1):
            partition2 = partitions2[j]
            assert_equal_resource(partition1, partition2)

            nics1 = partition1.nics.list()
            nics2 = partition2.nics.list()
            assert len(nics1) == len(nics2)
            for k, nic1 in enumerate(nics1):
                nic2 = nics2[k]
                assert_equal_resource(nic1, nic2)

            if partition1.hbas is not None and partition2.hbas is not None:
                # z14 and above do not have .hbas set
                hbas1 = partition1.hbas.list()
                hbas2 = partition2.hbas.list()
                assert len(hbas1) == len(hbas2)
                for k, hba1 in enumerate(hbas1):
                    hba2 = hbas2[k]
                    assert_equal_resource(hba1, hba2)

            vfs1 = partition1.virtual_functions.list()
            vfs2 = partition2.virtual_functions.list()
            assert len(vfs1) == len(vfs2)
            for k, vf1 in enumerate(vfs1):
                vf2 = vfs2[k]
                assert_equal_resource(vf1, vf2)

        adapters1 = cpc1.adapters.list()
        adapters2 = cpc2.adapters.list()
        assert len(adapters1) == len(adapters2)
        for j, adapter1 in enumerate(adapters1):
            adapter2 = adapters2[j]
            assert_equal_resource(adapter1, adapter2)

            if adapter1.properties.get('type', None) != 'not-configured':
                # Unconfigured FICON adapters cannot retrieve port properties
                ports1 = adapter1.ports.list()
                ports2 = adapter2.ports.list()
                assert len(ports1) == len(ports2)
                for k, port1 in enumerate(ports1):
                    port2 = ports2[k]
                    assert_equal_resource(port1, port2)

        vss1 = cpc1.virtual_switches.list()
        vss2 = cpc2.virtual_switches.list()
        assert len(vss1) == len(vss2)
        for j, vs1 in enumerate(vss1):
            vs2 = vss2[j]
            assert_equal_resource(vs1, vs2)

        lpars1 = cpc1.lpars.list()
        lpars2 = cpc2.lpars.list()
        assert len(lpars1) == len(lpars2)
        for j, lpar1 in enumerate(lpars1):
            lpar2 = lpars2[j]
            assert_equal_resource(lpar1, lpar2)

        raps1 = cpc1.reset_activation_profiles.list()
        raps2 = cpc2.reset_activation_profiles.list()
        assert len(raps1) == len(raps2)
        for j, rap1 in enumerate(raps1):
            rap2 = raps2[j]
            assert_equal_resource(rap1, rap2)

        iaps1 = cpc1.image_activation_profiles.list()
        iaps2 = cpc2.image_activation_profiles.list()
        assert len(iaps1) == len(iaps2)
        for j, iap1 in enumerate(iaps1):
            iap2 = iaps2[j]
            assert_equal_resource(iap1, iap2)

        laps1 = cpc1.load_activation_profiles.list()
        laps2 = cpc2.load_activation_profiles.list()
        assert len(laps1) == len(laps2)
        for j, lap1 in enumerate(laps1):
            lap2 = laps2[j]
            assert_equal_resource(lap1, lap2)

    # TODO: Reactivate metrics comparison once implemented
    # mcs1 = hmc1.metrics_contexts.list()
    # mcs2 = hmc2.metrics_contexts.list()
    # assert len(mcs1) == len(mcs2)
    # for i, mc1 in enumerate(mcs1):
    #     mc2 = mcs2[i]
    #     assert_equal_resource(mc1, mc2)
    # mgd1_mg_names = hmc1.metrics_contexts.get_metric_group_definition_names()
    # mgd2_mg_names = hmc2.metrics_contexts.get_metric_group_definition_names()
    # assert set(mgd1_mg_names) == set(mgd2_mg_names)
    # for mg_name in mgd1_mg_names:
    #     mgd1 = hmc1.metrics_contexts.get_metric_group_definition(mg_name)
    #     mgd2 = hmc2.metrics_contexts.get_metric_group_definition(mg_name)
    #     assert_equal_metric_group_def(mgd1, mgd2)
    # mv1_mg_names = hmc1.metrics_contexts.get_metric_values_group_names()
    # mv1_mg_names = hmc2.metrics_contexts.get_metric_values_group_names()
    # assert set(mv1_mg_names) == set(mv1_mg_names)
    # for mg_name in mv1_mg_names:
    #     mv1_list = hmc1.metrics_contexts.get_metric_values(mg_name)
    #     mv2_list = hmc2.metrics_contexts.get_metric_values(mg_name)
    #     for i, mv1 in enumerate(mv1_list):
    #         mv2 = mv2_list[i]
    #         assert_equal_metric_values(mv1, mv2)


def assert_equal_resource(res1, res2):
    """
    Assert that two Faked resource objects are equal.

    Only the standard attributes are compared.
    """
    assert isinstance(res1, FakedBaseResource)
    assert isinstance(res2, FakedBaseResource)
    assert res1.uri == res2.uri
    assert res1.oid == res2.oid
    names1 = set(res1.properties.keys())
    names2 = set(res2.properties.keys())
    if names1 != names2:
        raise AssertionError(
            "Resources do not have the same set of properties:\n"
            f"- res1 names: {sorted(names1)}\n"
            f"- res2 names: {sorted(names2)}\n")
    for name in res1.properties:
        value1 = res1.properties[name]
        value2 = res2.properties[name]
        if value1 != value2:
            raise AssertionError(
                f"Resources do not have the same value for property {name}:\n"
                f"- res1 value: {value1}\n"
                f"- res2 value: {value2}\n")


def assert_equal_metric_group_def(mgd1, mgd2):
    """
    Assert that two FakedMetricGroupDefinition objects are equal.
    """
    assert isinstance(mgd1, FakedMetricGroupDefinition)
    assert isinstance(mgd2, FakedMetricGroupDefinition)
    assert mgd1.name == mgd2.name
    assert mgd1.types == mgd2.types


def assert_equal_metric_values(mv1, mv2):
    """
    Assert that two FakedMetricObjectValues objects are equal.
    """
    assert isinstance(mv1, FakedMetricObjectValues)
    assert isinstance(mv2, FakedMetricObjectValues)
    assert mv1.group_name == mv2.group_name
    assert mv1.resource_uri == mv2.resource_uri
    assert mv1.timestamp == mv2.timestamp
    assert mv1.values == mv2.values


def timestamp_aware(dt):
    """
    Return the input datetime object as a timezone-aware datetime object.

    If the input object is already timezone-aware, it is returned.

    If the input object is timezone-naive, the local timezone information is
    added to a copy of the input object and that copy is returned.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz.tzlocal())  # new object
    return dt


def assert_blanked_in_message(message, properties, blanked_properties):
    """
    Assert that a message containing a string representation of a properties
    dict has the desired properties blanked out.

    Parameters:
        message (str): The message to be checked.
        properties (dict): Properties that can possibly be in the message
          (with hyphened names).
        blanked_properties (list of str): The names of the properties that
          need to be blanked out in the message (with hyphened names).
    """
    for pname in blanked_properties:
        if pname in properties:
            exp_str = f"'{pname}': '{zhmcclient.BLANKED_OUT_STRING}'"
            assert message.find(exp_str) > 0
