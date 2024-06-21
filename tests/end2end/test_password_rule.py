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
End2end tests for password rules (on CPCs in DPM mode).

These tests do not change any existing password rules, but create,
modify and delete test password rules.
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

# Properties in minimalistic PasswordRule objects (e.g. find_by_name())
PWRULE_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in PasswordRule objects returned by list() without full props
PWRULE_LIST_PROPS = ['element-uri', 'name', 'type']

# Properties whose values can change between retrievals of PasswordRule objects
PWRULE_VOLATILE_PROPS = []


def test_pwrule_find_list(hmc_session):  # noqa: F811
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
            "password rules")

    # Pick the password rules to test with
    pwrule_list = console.password_rules.list()
    if not pwrule_list:
        skip_warn(f"No password rules defined on HMC {hd.host}")
    pwrule_list = pick_test_resources(pwrule_list)

    for pwrule in pwrule_list:
        print(f"Testing with password rule {pwrule.name!r}")
        runtest_find_list(
            hmc_session, console.password_rules, pwrule.name, 'name',
            'element-uri', PWRULE_VOLATILE_PROPS, PWRULE_MINIMAL_PROPS,
            PWRULE_LIST_PROPS)


def test_pwrule_property(hmc_session):  # noqa: F811
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
            "password rules")

    # Pick the password rules to test with
    pwrule_list = console.password_rules.list()
    if not pwrule_list:
        skip_warn(f"No password rules defined on HMC {hd.host}")
    pwrule_list = pick_test_resources(pwrule_list)

    for pwrule in pwrule_list:
        print(f"Testing with password rule {pwrule.name!r}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(pwrule.manager, non_list_prop)


def test_pwrule_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a password rule.
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
            "password rules")

    pwrule_name = TEST_PREFIX + ' test_pwrule_crud pwrule1'
    pwrule_name_new = pwrule_name + ' new'

    # Ensure a clean starting point for this test
    try:
        pwrule = console.password_rules.find(name=pwrule_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            f"Deleting test password rule from previous run: {pwrule_name!r}",
            UserWarning)
        pwrule.delete()

    # Test creating the password rule

    pwrule_input_props = {
        'name': pwrule_name,
        'description': 'Test password rule for zhmcclient end2end tests',
        'expiration': 90,
    }
    pwrule_auto_props = {
        'min-length': 8,
        'max-length': 256,
    }

    # The code to be tested
    try:
        pwrule = console.password_rules.create(
            pwrule_input_props)
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 403 and exc.reason == 1:
            skip_warn(
                f"HMC userid {hd.userid!r} is not authorized for task "
                f"'Manage Password Rules' on HMC {hd.host}")
        else:
            raise

    for pn, exp_value in pwrule_input_props.items():
        assert pwrule.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    pwrule.pull_full_properties()
    for pn, exp_value in pwrule_input_props.items():
        assert pwrule.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    for pn, exp_value in pwrule_auto_props.items():
        assert pwrule.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"

    # Test updating a property of the password rule

    new_desc = "Updated password rule description."

    # The code to be tested
    pwrule.update_properties(dict(description=new_desc))

    assert pwrule.properties['description'] == new_desc
    pwrule.pull_full_properties()
    assert pwrule.properties['description'] == new_desc

    # Test that password rules cannot be renamed

    with pytest.raises(zhmcclient.HTTPError) as exc_info:

        # The code to be tested
        pwrule.update_properties(dict(name=pwrule_name_new))

    exc = exc_info.value
    assert exc.http_status == 400
    assert exc.reason == 6
    with pytest.raises(zhmcclient.NotFound):
        console.password_rules.find(name=pwrule_name_new)

    # Test deleting the password rule

    # The code to be tested
    pwrule.delete()

    with pytest.raises(zhmcclient.NotFound):
        console.password_rules.find(name=pwrule_name)
