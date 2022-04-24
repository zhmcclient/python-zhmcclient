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
End2end tests for users (on CPCs in DPM mode).

These tests do not change any existing users, but create,
modify and delete test users.
"""

from __future__ import absolute_import, print_function

import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import pick_test_resources, runtest_find_list, TEST_PREFIX, \
    skip_warn

urllib3.disable_warnings()

# Properties in minimalistic User objects (e.g. find_by_name())
USER_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in User objects returned by list() without full props
USER_LIST_PROPS = ['object-uri', 'name', 'type']

# Properties whose values can change between retrievals of User objects
USER_VOLATILE_PROPS = []


def test_user_find_list(hmc_session):  # noqa: F811
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
        skip_warn("HMC {h} of version {v} does not yet support users".
                  format(h=hd.hmc_host, v=hmc_version))

    # Pick the users to test with
    user_list = console.users.list()
    if not user_list:
        skip_warn("No users defined on HMC {h}".format(h=hd.hmc_host))
    user_list = pick_test_resources(user_list)

    for user in user_list:
        print("Testing with user {u!r}".format(u=user.name))
        runtest_find_list(
            hmc_session, console.users, user.name, 'name',
            'object-uri', USER_VOLATILE_PROPS, USER_MINIMAL_PROPS,
            USER_LIST_PROPS)


def test_user_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a user.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 13, 0):
        skip_warn("HMC {h} of version {v} does not yet support users".
                  format(h=hd.hmc_host, v=hmc_version))

    user_name = TEST_PREFIX + '_test_user_crud_user1'
    user_name_new = user_name + '_new'
    pwrule_name = TEST_PREFIX + '_test_user_crud_pwrule1'

    # Ensure a clean starting point for this test
    try:
        user = console.users.find(name=user_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            "Deleting test user from previous run: {u!r}".
            format(u=user_name), UserWarning)
        user.delete()
    try:
        pwrule = console.password_rules.find(name=pwrule_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            "Deleting test password rule from previous run: {r!r}".
            format(r=pwrule_name), UserWarning)
        pwrule.delete()

    # Pick a password rule for the user
    try:
        pwrule = console.password_rules.find(name='Basic')
    except zhmcclient.NotFound:
        skip_warn("Password rule 'Basic' not found to create test user")

    # Test creating the user

    user_input_props = {
        'name': user_name,
        'description': 'Test user for zhmcclient end2end tests',
        'type': 'standard',
        'authentication-type': 'local',
        'password-rule-uri': pwrule.uri,
        'password': 'Abcd',  # Basic rule: 4-8 alphanumeric
    }
    user_auto_props = {
        'disabled': False,
    }
    task_name = 'Manage Users' \
        if user_input_props['type'] == 'standard' \
        else 'Manage User Templates'

    # The code to be tested
    try:
        user = console.users.create(user_input_props)
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 403 and exc.reason == 1:
            skip_warn("HMC userid {u!r} is not authorized for task {t!r} on "
                      "HMC {h}".
                      format(u=hd.hmc_userid, t=task_name, h=hd.hmc_host))
        else:
            raise

    for pn, exp_value in user_input_props.items():
        if pn == 'password':
            continue
        assert user.properties[pn] == exp_value, \
            "Unexpected value for property {!r}".format(pn)
    user.pull_full_properties()
    for pn, exp_value in user_input_props.items():
        if pn == 'password':
            continue
        assert user.properties[pn] == exp_value, \
            "Unexpected value for property {!r}".format(pn)
    for pn, exp_value in user_auto_props.items():
        assert user.properties[pn] == exp_value, \
            "Unexpected value for property {!r}".format(pn)

    # Test updating a property of the user

    new_desc = "Updated user description."

    # The code to be tested
    user.update_properties(dict(description=new_desc))

    assert user.properties['description'] == new_desc
    user.pull_full_properties()
    assert user.properties['description'] == new_desc

    # Test that users cannot be renamed

    with pytest.raises(zhmcclient.HTTPError) as exc_info:

        # The code to be tested
        user.update_properties(dict(name=user_name_new))

    exc = exc_info.value
    assert exc.http_status == 400
    assert exc.reason == 6
    with pytest.raises(zhmcclient.NotFound):
        console.users.find(name=user_name_new)

    # Test deleting the user

    # The code to be tested
    user.delete()

    with pytest.raises(zhmcclient.NotFound):
        console.users.find(name=user_name)
