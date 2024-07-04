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
End2end tests for user patterns (on CPCs in DPM mode).

These tests do not change any existing user patterns, but create,
modify and delete test user patterns.
"""


import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic UserPattern objects (e.g. find_by_name())
UPATT_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in UserPattern objects returned by list() without full props
UPATT_LIST_PROPS = ['element-uri', 'name', 'type']

# Properties whose values can change between retrievals of UserPattern objects
UPATT_VOLATILE_PROPS = []


def test_upatt_find_list(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 13, 0):
        skip_warn(
            f"HMC {hd.host} of version {hmc_version} does not yet support "
            "user patterns")

    # Pick the user patterns to test with
    upatt_list = console.user_patterns.list()
    if not upatt_list:
        skip_warn(f"No user patterns defined on HMC {hd.host}")
    upatt_list = pick_test_resources(upatt_list)

    for upatt in upatt_list:
        print(f"Testing with user pattern {upatt.name!r}")
        runtest_find_list(
            hmc_session, console.user_patterns, upatt.name, 'name',
            'element-uri', UPATT_VOLATILE_PROPS, UPATT_MINIMAL_PROPS,
            UPATT_LIST_PROPS)


def test_upatt_property(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 13, 0):
        skip_warn(
            f"HMC {hd.host} of version {hmc_version} does not yet support "
            "user patterns")

    # Pick the user patterns to test with
    upatt_list = console.user_patterns.list()
    if not upatt_list:
        skip_warn(f"No user patterns defined on HMC {hd.host}")
    upatt_list = pick_test_resources(upatt_list)

    for upatt in upatt_list:
        print(f"Testing with user pattern {upatt.name!r}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(upatt.manager, non_list_prop)


def test_upatt_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a user pattern.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 13, 0):
        skip_warn(
            f"HMC {hd.host} of version {hmc_version} does not yet support "
            "user patterns")

    upatt_name = TEST_PREFIX + ' test_upatt_crud upatt1'
    upatt_name_new = upatt_name + ' new'

    # Ensure a clean starting point for this test
    try:
        upatt = console.user_patterns.find(name=upatt_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            f"Deleting test user pattern from previous run: {upatt_name!r}",
            UserWarning)
        upatt.delete()

    # Pick a template user to be the template user for the user pattern
    template_users = console.users.findall(type='template')
    if not template_users:
        skip_warn(f"No template users on HMC {hd.host}")
    template_user = template_users[0]

    # Test creating the user pattern

    upatt_input_props = {
        'name': upatt_name,
        'description': 'Test user pattern for zhmcclient end2end tests',
        'pattern': TEST_PREFIX + ' test_upatt_crud .+',
        'type': 'regular-expression',
        'retention-time': 180,
        'specific-template-uri': template_user.uri,
    }
    upatt_auto_props = {}

    # The code to be tested
    try:
        upatt = console.user_patterns.create(upatt_input_props)
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 403 and exc.reason == 1:
            skip_warn(
                f"HMC userid {hd.userid!r} is not authorized for task "
                f"'Manage User Patterns' on HMC {hd.host}")
        else:
            raise

    for pn, exp_value in upatt_input_props.items():
        assert upatt.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    upatt.pull_full_properties()
    for pn, exp_value in upatt_input_props.items():
        assert upatt.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    for pn, exp_value in upatt_auto_props.items():
        assert upatt.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"

    # Test updating a property of the user pattern

    new_desc = "Updated user pattern description."

    # The code to be tested
    upatt.update_properties(dict(description=new_desc))

    assert upatt.properties['description'] == new_desc
    upatt.pull_full_properties()
    assert upatt.properties['description'] == new_desc

    # Test renaming the user pattern

    # The code to be tested
    upatt.update_properties(dict(name=upatt_name_new))

    assert upatt.properties['name'] == upatt_name_new
    upatt.pull_full_properties()
    assert upatt.properties['name'] == upatt_name_new
    with pytest.raises(zhmcclient.NotFound):
        console.user_patterns.find(name=upatt_name)

    # Test deleting the user pattern

    # The code to be tested
    upatt.delete()

    with pytest.raises(zhmcclient.NotFound):
        console.user_patterns.find(name=upatt_name_new)
