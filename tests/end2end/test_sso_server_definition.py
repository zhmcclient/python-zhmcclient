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
End2end tests for SSO server definitions (on CPCs in DPM mode).

These tests do not change any existing SSO server definitions, but create,
modify and delete test SSO server definitions.
"""


import warnings
import pytest
from requests.packages import urllib3

import zhmcclient

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic SSOServerDefinition objects (e.g. find_by_name())
SSOSRVDEF_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in SSOServerDefinition objects returned by list() without full
# props
SSOSRVDEF_LIST_PROPS = ['element-uri', 'name','type']

# Properties whose values can change between retrievals of SSOServerDefinition
# objects
SSOSRVDEF_VOLATILE_PROPS = []


def test_ssosrvdef_find_list(hmc_session):
    """
    Test list(), find(), findall().
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 17, 0):
        skip_warn(f"HMC {hd.host} of version {hmc_version} does not yet "
                  "support SSO server definitions")

    # Pick the SSO server definitions to test with
    ssosrvdef_list = console.sso_server_definitions.list()
    if not ssosrvdef_list:
        skip_warn(f"No SSO server definitions defined on HMC {hd.host}")
    ssosrvdef_list = pick_test_resources(ssosrvdef_list)

    for ssosrvdef in ssosrvdef_list:
        print(f"Testing with SSO server definition {ssosrvdef.name!r}")
        runtest_find_list(
            hmc_session, console.sso_server_definitions, ssosrvdef.name,
            'name', 'element-uri', SSOSRVDEF_VOLATILE_PROPS,
            SSOSRVDEF_MINIMAL_PROPS, SSOSRVDEF_LIST_PROPS)


def test_ssosrvdef_property(hmc_session):
    """
    Test property related methods
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 17, 0):
        skip_warn(f"HMC {hd.host} of version {hmc_version} does not yet "
                  "support SSO server definitions")

    # Pick the SSO server definitions to test with
    ssosrvdef_list = console.sso_server_definitions.list()
    if not ssosrvdef_list:
        skip_warn(f"No SSO server definitions defined on HMC {hd.host}")
    ssosrvdef_list = pick_test_resources(ssosrvdef_list)

    for ssosrvdef in ssosrvdef_list:
        print(f"Testing with SSO server definition {ssosrvdef.name!r}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(ssosrvdef.manager, non_list_prop)


def test_ssosrvdef_crud(hmc_session):
    """
    Test create, read, update and delete a SSO server definition.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 17, 0):
        skip_warn(f"HMC {hd.host} of version {hmc_version} does not yet "
                  "support SSO server definitions")

    ssosrvdef_name = TEST_PREFIX + ' test_ssosrvdef_crud ssosrvdef1'
    ssosrvdef_name_new = ssosrvdef_name + ' new'

    # Ensure a clean starting point for this test
    try:
        ssosrvdef = console.sso_server_definitions.find(
            name=ssosrvdef_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            "Deleting test SSO server definition from previous run: "
            f"{ssosrvdef_name!r}", UserWarning)
        ssosrvdef.delete()

    # Test creating the SSO server definition

    ssosrvdef_input_props = {
        "authentication-page-servers":[
            {
            "hostname-ipaddr":"images1.example.com",
            "port":443
            },
            {
            "hostname-ipaddr":"images2.example.com",
            "port":80
            }
            ],
        "authentication-url":"https://sso1.example.com/auth",
        "client-id":"sso1-123456",
        "client-secret":"sso1-client-secret",
        "description":"Primary SSO server",
        "issuer-url":"https://sso1.example.com/issuer",
        "jwks-url":"https://sso1.example.com/jwks",
        "logout-sso-session-on-reauthentication-failure":true,
        "logout-url":"https://sso1.example.com/logout",
        "name":"SSO Server 1",
        "token-url":"https://sso1.example.com/token",
            "type":"oidc"
    }
    ssosrvdef_auto_props = {
        'logout-url': None,
        'logout-sso-session-on-reauthentication-failure': False,
    }

    # The code to be tested
    try:
        ssosrvdef = console.sso_server_definitions.create(
            ssosrvdef_input_props)
    except zhmcclient.HTTPError as exc:
        if exc.http_status == 403 and exc.reason == 1:
            skip_warn(f"HMC userid {hd.userid!r} is not authorized for task "
                      f"'Manage Single Sign-On Servers' on HMC {hd.host}")
        else:
            raise

    for pn, exp_value in ssosrvdef_input_props.items():
        assert ssosrvdef.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    ssosrvdef.pull_full_properties()
    for pn, exp_value in ssosrvdef_input_props.items():
        assert ssosrvdef.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"
    for pn, exp_value in ssosrvdef_auto_props.items():
        assert ssosrvdef.properties[pn] == exp_value, \
            f"Unexpected value for property {pn!r}"

    # Test updating a property of the SSO server definition

    new_desc = "Updated SSO server definition description."

    # The code to be tested
    ssosrvdef.update_properties(dict(description=new_desc))

    assert ssosrvdef.properties['description'] == new_desc
    ssosrvdef.pull_full_properties()
    assert ssosrvdef.properties['description'] == new_desc

    # Test that SSO server definitions cannot be renamed

    with pytest.raises(zhmcclient.HTTPError) as exc_info:

        # The code to be tested
        ssosrvdef.update_properties(dict(name=ssosrvdef_name_new))

    exc = exc_info.value
    assert exc.http_status == 400
    assert exc.reason == 6
    with pytest.raises(zhmcclient.NotFound):
        console.sso_server_definitions.find(name=ssosrvdef_name_new)

    # Test deleting the SSO server definition

    # The code to be tested
    ssosrvdef.delete()

    with pytest.raises(zhmcclient.NotFound):
        console.sso_server_definitions.find(name=ssosrvdef_name)
