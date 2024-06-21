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
End2end tests for user roles (on CPCs in DPM mode).

These tests do not change any existing user roles, but create,
modify and delete test user roles.
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

# Properties in minimalistic UserRole objects (e.g. find_by_name())
UROLE_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in UserRole objects returned by list() without full props
UROLE_LIST_PROPS = ['object-uri', 'name', 'type']

# Properties whose values can change between retrievals of UserRole objects
UROLE_VOLATILE_PROPS = []


def test_urole_find_list(hmc_session):  # noqa: F811
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
            "user roles")

    # Pick the user roles to test with
    urole_list = console.user_roles.list()
    if not urole_list:
        skip_warn(f"No user roles defined on HMC {hd.host}")
    urole_list = pick_test_resources(urole_list)

    for urole in urole_list:
        print(f"Testing with user role {urole.name!r}")
        runtest_find_list(
            hmc_session, console.user_roles, urole.name, 'name',
            'object-uri', UROLE_VOLATILE_PROPS, UROLE_MINIMAL_PROPS,
            UROLE_LIST_PROPS)


def test_urole_property(hmc_session):  # noqa: F811
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
            "user roles")

    # Pick the user roles to test with
    urole_list = console.user_roles.list()
    if not urole_list:
        skip_warn(f"No user roles defined on HMC {hd.host}")
    urole_list = pick_test_resources(urole_list)

    for urole in urole_list:
        print(f"Testing with user role {urole.name!r}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(urole.manager, non_list_prop)


def test_urole_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a user role.
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
            "user roles")

    urole_name = TEST_PREFIX + ' test_urole_crud urole1'
    urole_name_new = urole_name + ' new'

    # Ensure a clean starting point for this test
    try:
        urole = console.user_roles.find(name=urole_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            f"Deleting test user role from previous run: {urole_name!r}",
            UserWarning)
        urole.delete()

    # Test creating the user role

    urole_input_props = {
        'name': urole_name,
        'description': 'Test user role for zhmcclient end2end tests',
    }
    urole_auto_props = {
        'type': 'user-defined',
        'is-inheritance-enabled': False,
    }

    # The code to be tested
    try:
        urole = console.user_roles.create(
            urole_input_props)
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 403 and exc.reason == 1:
            skip_warn(
                f"HMC userid {hd.userid!r} is not authorized for task "
                f"'Manage User Roles' on HMC {hd.host}")
        else:
            raise

    for pn, exp_value in urole_input_props.items():
        assert urole.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    urole.pull_full_properties()
    for pn, exp_value in urole_input_props.items():
        assert urole.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    for pn, exp_value in urole_auto_props.items():
        assert urole.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"

    # Test updating a property of the user role

    new_desc = "Updated user role description."

    # The code to be tested
    urole.update_properties(dict(description=new_desc))

    assert urole.properties['description'] == new_desc
    urole.pull_full_properties()
    assert urole.properties['description'] == new_desc

    # Test that user roles cannot be renamed

    with pytest.raises(zhmcclient.HTTPError) as exc_info:

        # The code to be tested
        urole.update_properties(dict(name=urole_name_new))

    exc = exc_info.value
    assert exc.http_status == 400
    assert exc.reason == 6
    with pytest.raises(zhmcclient.NotFound):
        console.user_roles.find(name=urole_name_new)

    # Test deleting the user role

    # The code to be tested
    urole.delete()

    with pytest.raises(zhmcclient.NotFound):
        console.user_roles.find(name=urole_name)
