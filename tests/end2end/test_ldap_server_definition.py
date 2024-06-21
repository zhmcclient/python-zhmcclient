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
End2end tests for LDAP server definitions (on CPCs in DPM mode).

These tests do not change any existing LDAP server definitions, but create,
modify and delete test LDAP server definitions.
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

# Properties in minimalistic LDAPServerDefinition objects (e.g. find_by_name())
LDAPSRVDEF_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in LDAPServerDefinition objects returned by list() without full
# props
LDAPSRVDEF_LIST_PROPS = ['element-uri', 'name']

# Properties whose values can change between retrievals of LDAPServerDefinition
# objects
LDAPSRVDEF_VOLATILE_PROPS = []


def test_ldapsrvdef_find_list(hmc_session):  # noqa: F811
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
        skip_warn(f"HMC {hd.host} of version {hmc_version} does not yet "
                  "support LDAP server definitions")

    # Pick the LDAP server definitions to test with
    ldapsrvdef_list = console.ldap_server_definitions.list()
    if not ldapsrvdef_list:
        skip_warn(f"No LDAP server definitions defined on HMC {hd.host}")
    ldapsrvdef_list = pick_test_resources(ldapsrvdef_list)

    for ldapsrvdef in ldapsrvdef_list:
        print(f"Testing with LDAP server definition {ldapsrvdef.name!r}")
        runtest_find_list(
            hmc_session, console.ldap_server_definitions, ldapsrvdef.name,
            'name', 'element-uri', LDAPSRVDEF_VOLATILE_PROPS,
            LDAPSRVDEF_MINIMAL_PROPS, LDAPSRVDEF_LIST_PROPS)


def test_ldapsrvdef_property(hmc_session):  # noqa: F811
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
        skip_warn(f"HMC {hd.host} of version {hmc_version} does not yet "
                  "support LDAP server definitions")

    # Pick the LDAP server definitions to test with
    ldapsrvdef_list = console.ldap_server_definitions.list()
    if not ldapsrvdef_list:
        skip_warn(f"No LDAP server definitions defined on HMC {hd.host}")
    ldapsrvdef_list = pick_test_resources(ldapsrvdef_list)

    for ldapsrvdef in ldapsrvdef_list:
        print(f"Testing with LDAP server definition {ldapsrvdef.name!r}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(ldapsrvdef.manager, non_list_prop)


def test_ldapsrvdef_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a LDAP server definition.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 13, 0):
        skip_warn(f"HMC {hd.host} of version {hmc_version} does not yet "
                  "support LDAP server definitions")

    ldapsrvdef_name = TEST_PREFIX + ' test_ldapsrvdef_crud ldapsrvdef1'
    ldapsrvdef_name_new = ldapsrvdef_name + ' new'

    # Ensure a clean starting point for this test
    try:
        ldapsrvdef = console.ldap_server_definitions.find(
            name=ldapsrvdef_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            "Deleting test LDAP server definition from previous run: "
            f"{ldapsrvdef_name!r}", UserWarning)
        ldapsrvdef.delete()

    # Test creating the LDAP server definition

    ldapsrvdef_input_props = {
        'name': ldapsrvdef_name,
        'description': 'Test LDAP server def for zhmcclient end2end tests',
        'primary-hostname-ipaddr': '10.11.12.13',
        'location-method': 'pattern',
        'search-distinguished-name': 'user {0}',
    }
    ldapsrvdef_auto_props = {
        'connection-port': None,
        'use-ssl': False,
    }

    # The code to be tested
    try:
        ldapsrvdef = console.ldap_server_definitions.create(
            ldapsrvdef_input_props)
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 403 and exc.reason == 1:
            skip_warn(f"HMC userid {hd.userid!r} is not authorized for task "
                      f"'Manage LDAP Server Definitions' on HMC {hd.host}")
        else:
            raise

    for pn, exp_value in ldapsrvdef_input_props.items():
        assert ldapsrvdef.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    ldapsrvdef.pull_full_properties()
    for pn, exp_value in ldapsrvdef_input_props.items():
        assert ldapsrvdef.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    for pn, exp_value in ldapsrvdef_auto_props.items():
        assert ldapsrvdef.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"

    # Test updating a property of the LDAP server definition

    new_desc = "Updated LDAP server definition description."

    # The code to be tested
    ldapsrvdef.update_properties(dict(description=new_desc))

    assert ldapsrvdef.properties['description'] == new_desc
    ldapsrvdef.pull_full_properties()
    assert ldapsrvdef.properties['description'] == new_desc

    # Test that LDAP server definitions cannot be renamed

    with pytest.raises(zhmcclient.HTTPError) as exc_info:

        # The code to be tested
        ldapsrvdef.update_properties(dict(name=ldapsrvdef_name_new))

    exc = exc_info.value
    assert exc.http_status == 400
    assert exc.reason == 6
    with pytest.raises(zhmcclient.NotFound):
        console.ldap_server_definitions.find(name=ldapsrvdef_name_new)

    # Test deleting the LDAP server definition

    # The code to be tested
    ldapsrvdef.delete()

    with pytest.raises(zhmcclient.NotFound):
        console.ldap_server_definitions.find(name=ldapsrvdef_name)
