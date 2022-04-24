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

from __future__ import absolute_import, print_function

import os
import re
import random
import warnings
import pytest

# Prefix used for names of resources that are created during tests
TEST_PREFIX = 'zhmcclient_tests_end2end'


class End2endTestWarning(UserWarning):
    """
    Python warning indicating an issue with an end2end test.
    """
    pass


def assert_res_props(res, exp_props, ignore_values=None, prop_names=None):
    """
    Check the properties of a resource object.
    """
    res_props = dict(res.properties)
    # checked_prop_names = set()
    for prop_name in exp_props:

        if prop_names is not None and prop_name not in prop_names:
            continue  # Only check properties in prop_names

        assert prop_name in res_props, \
            "Property {p!r} not found in {k} object {o!r}". \
            format(p=prop_name, k=res.prop('class'), o=res.name)

        if ignore_values is not None and prop_name not in ignore_values:
            act_value = res_props[prop_name]
            exp_value = exp_props[prop_name]
            assert_res_prop(act_value, exp_value, prop_name, res)

        # checked_prop_names.add(prop_name)

    # extra_prop_names = set(res_props.keys()) - checked_prop_names

    # TODO: Decide whether we want to check the exact set, or the minimum set.
    # assert not extra_prop_names, \
    #     "The following properties were unexpectedly present in {k} object " \
    #     "{o!r} : {e}". \
    #     format(k=res.prop('class'), o=res.name, e=', '.join(extra_prop_names))


def assert_res_prop(act_value, exp_value, prop_name, res):
    """
    Check a property of a resource object.
    """
    assert act_value == exp_value, \
        "Property {p!r} has unexpected value in {k} object {o!r}: " \
        "Expected: {ev!r}, actual: {av!r}". \
        format(p=prop_name, k=res.prop('class'), o=res.name, ev=exp_value,
               av=act_value)


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
                      volatile_props, minimal_props, list_props):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Run tests for find/list methods for a resource type:
    - find_by_name(name)
    - pull_full_properties()
    - find(**filter_args)
      - server-side filter
    - findall(**filter_args)
      - no filter
      - server-side filter
      - client-side filter
    - list(full_properties=False, filter_args=None)
      - no filter + short
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
    """
    # The code to be tested: find_by_name(name)
    found_res = manager.find_by_name(name)

    # Get full properties directly, for comparison
    exp_props = session.get(found_res.uri)

    # Get the object-id of the resource from its URI
    oid = found_res.uri.split('/')[-1]
    oid_prop = manager._oid_prop  # pylint: disable=protected-access

    if client_prop:
        client_value = exp_props[client_prop]

    if server_prop:
        server_value = exp_props[server_prop]

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

    # The code to be tested: findall() with no filter
    found_res_list = manager.findall()

    assert name in map(lambda _res: _res.name, found_res_list)
    found_res_list = list(filter(lambda _res: _res.name == name,
                                 found_res_list))
    found_res = found_res_list[0]
    if len(found_res_list) > 1:
        found_uri_list = [r.uri for r in found_res_list]
        parent = manager.parent
        raise AssertionError(
            "{k} findall() result for {pk} {pn!r} has non-unique name {n!r} "
            "for the following {no} objects:\n{o}".
            format(k=found_res.prop('class'), pk=parent.prop('class'),
                   pn=parent.name, n=name, no=len(found_res_list),
                   o='\n'.join(found_uri_list)))
    assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                     prop_names=list_props)

    if server_prop:
        # The code to be tested: findall() with server-side filter
        found_res_list = manager.findall(**{server_prop: server_value})

        assert len(found_res_list) == 1
        found_res = found_res_list[0]
        assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                         prop_names=minimal_props)

    if client_prop:
        # The code to be tested: findall() with client-side filter
        found_res_list = manager.findall(**{client_prop: client_value})

        assert name in map(lambda _res: _res.name, found_res_list)
        found_res_list = list(filter(lambda _res: _res.name == name,
                                     found_res_list))
        found_res = found_res_list[0]
        if len(found_res_list) > 1:
            raise AssertionError(
                "{k} findall(client_filter) result with non-unique name {n!r}: "
                "{o}".
                format(k=found_res.prop('class'), n=name, o=found_res_list))
        assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                         prop_names=list_props)

    # The code to be tested: list() with no filter and short properties
    found_res_list = manager.list()

    assert name in map(lambda _res: _res.name, found_res_list)
    found_res_list = list(filter(lambda _res: _res.name == name,
                                 found_res_list))
    found_res = found_res_list[0]
    if len(found_res_list) > 1:
        raise AssertionError(
            "{k} list() result with non-unique name {n!r}: {o}".
            format(k=found_res.prop('class'), n=name, o=found_res_list))
    assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                     prop_names=list_props)

    if server_prop:
        # The code to be tested: list() with server-side filter and full props
        found_res_list = manager.list(full_properties=True,
                                      filter_args={server_prop: server_value})

        assert len(found_res_list) == 1
        found_res = found_res_list[0]
        assert_res_props(found_res, exp_props, ignore_values=volatile_props)

    if server_prop:
        # The code to be tested: list() with server-side filter and short props
        found_res_list = manager.list(filter_args={server_prop: server_value})

        assert len(found_res_list) == 1
        found_res = found_res_list[0]
        assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                         prop_names=list_props)

    if client_prop:
        # The code to be tested: list() with client-side filter and short props
        found_res_list = manager.list(filter_args={client_prop: client_value})

        assert name in [_res.name for _res in found_res_list]
        found_res = [_res for _res in found_res_list if _res.name == name][0]
        assert_res_props(found_res, exp_props, ignore_values=volatile_props,
                         prop_names=list_props)


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
                  "on CPC {c}".format(c=cpc.name))


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
        skip_warn("DPM Storage Mgmt feature enabled on CPC {c}".
                  format(c=cpc.name))


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
    if cpc.prop('processor-count-ifl'):
        part_input_props['ifl-processors'] = 2
    elif cpc.prop('processor-count-general-purpose'):
        part_input_props['cp-processors'] = 2
    else:
        part_input_props['cp-processors'] = 1
        pc_names = filter(lambda p: p.startswith('processor-count-'),
                          cpc.properties.keys())
        pc_list = ["{n}={v}".format(n=n, v=cpc.properties[n]) for n in pc_names]
        warnings.warn(
            "CPC {c} shows neither IFL nor CP processors, specifying 1 CP "
            "for partition creation. "
            "CPC processor-count properties are: {p}".
            format(c=cpc.name, p=', '.join(pc_list)), End2endTestWarning)

    return part_input_props


def skip_warn(msg):
    """
    Issue an End2endTestWarning and skip the current pytest testcase with the
    specified message.
    """
    warnings.warn(msg, End2endTestWarning, stacklevel=2)
    pytest.skip(msg)
