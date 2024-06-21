# Copyright 2023 IBM Corp. All Rights Reserved.
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
End2end tests for groups.

These tests do not change any existing groups, but create, modify and delete
groups for testing purposes.
"""


import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import pick_test_resources, runtest_find_list, TEST_PREFIX, \
    skip_warn, skipif_no_group_support

urllib3.disable_warnings()

# Properties in minimalistic PasswordRule objects (e.g. find_by_name())
GROUP_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in PasswordRule objects returned by list() without full props
GROUP_LIST_PROPS = ['object-uri', 'name']

# Properties whose values can change between retrievals of PasswordRule objects
GROUP_VOLATILE_PROPS = []


def test_group_find_list(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    skipif_no_group_support(client)

    # Pick the groups to test with
    group_list = console.groups.list()
    if not group_list:
        skip_warn(f"No groups defined on HMC {hd.host}")
    group_list = pick_test_resources(group_list)

    for group in group_list:
        print(f"Testing with group {group.name!r}")
        runtest_find_list(
            hmc_session, console.groups, group.name, 'name',
            'object-uri', GROUP_VOLATILE_PROPS, GROUP_MINIMAL_PROPS,
            GROUP_LIST_PROPS)


def test_group_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a group.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    console = client.consoles.console

    skipif_no_group_support(client)

    # TODO: Get group issue on T224 HMC resolved.
    if hd.host == '9.114.87.7':
        skip_warn(f"Issues with group support on HMC {hd.host}")

    group_name = TEST_PREFIX + ' test_group_crud group'

    # Ensure a clean starting point for this test
    try:
        group = console.groups.find(name=group_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            f"Deleting test group from previous run: {group_name!r}",
            UserWarning)
        group.delete()

    # Test creating the group

    group_input_props = {
        'name': group_name,
        'description': 'Test group for zhmcclient end2end tests',
        'match-info': {},
    }
    group_auto_props = {}

    try:

        # The code to be tested
        try:
            group = console.groups.create(group_input_props)
        except zhmcclient.HTTPError as exc:
            if exc.http_status == 403 and exc.reason == 1:
                skip_warn(
                    f"HMC userid {hd.userid!r} is not authorized for task "
                    f"'Grouping' on HMC {hd.host}")
            else:
                raise

        for pn, exp_value in group_input_props.items():
            assert group.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"
        group.pull_full_properties()
        for pn, exp_value in group_input_props.items():
            assert group.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"
        for pn, exp_value in group_auto_props.items():
            assert group.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"

        # Add a member
        cpc = client.cpcs.list()[0]
        group.add_member(cpc.uri)

        # List members
        members = group.list_members()
        assert len(members) == 1
        member = members[0]
        assert member['object-uri'] == cpc.uri
        assert member['name'] == cpc.name

        # Remove a member
        group.remove_member(cpc.uri)

        # Verify that list of members is empty
        members = group.list_members()
        assert len(members) == 0

    finally:

        # Test deleting the group

        # The code to be tested
        group.delete()

        with pytest.raises(zhmcclient.NotFound):
            console.groups.find(name=group_name)
