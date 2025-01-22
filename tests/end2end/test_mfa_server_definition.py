# Copyright 2025 IBM Corp. All Rights Reserved.
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
End2end tests for MFA server definitions (on CPCs in DPM mode).

These tests do not change any existing MFA server definitions, but create,
modify and delete test MFA server definitions.
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

# Properties in minimalistic MFAServerDefinition objects (e.g. find_by_name())
MFASRVDEF_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in MFAServerDefinition objects returned by list() without full
# props
MFASRVDEF_LIST_PROPS = ['element-uri', 'name']

# Properties whose values can change between retrievals of MFAServerDefinition
# objects
MFASRVDEF_VOLATILE_PROPS = []


def test_mfasrvdef_find_list(hmc_session):  # noqa: F811
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
    if hmc_version_info < (2, 15, 0):
        skip_warn(f"HMC {hd.host} of version {hmc_version} does not yet "
                  "support MFA server definitions")

    # Pick the MFA server definitions to test with
    mfasrvdef_list = console.mfa_server_definitions.list()
    if not mfasrvdef_list:
        skip_warn(f"No MFA server definitions defined on HMC {hd.host}")
    mfasrvdef_list = pick_test_resources(mfasrvdef_list)

    for mfasrvdef in mfasrvdef_list:
        print(f"Testing with MFA server definition {mfasrvdef.name!r}")
        runtest_find_list(
            hmc_session, console.mfa_server_definitions, mfasrvdef.name,
            'name', 'element-uri', MFASRVDEF_VOLATILE_PROPS,
            MFASRVDEF_MINIMAL_PROPS, MFASRVDEF_LIST_PROPS)


def test_mfasrvdef_property(hmc_session):  # noqa: F811
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
    if hmc_version_info < (2, 15, 0):
        skip_warn(f"HMC {hd.host} of version {hmc_version} does not yet "
                  "support MFA server definitions")

    # Pick the MFA server definitions to test with
    mfasrvdef_list = console.mfa_server_definitions.list()
    if not mfasrvdef_list:
        skip_warn(f"No MFA server definitions defined on HMC {hd.host}")
    mfasrvdef_list = pick_test_resources(mfasrvdef_list)

    for mfasrvdef in mfasrvdef_list:
        print(f"Testing with MFA server definition {mfasrvdef.name!r}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(mfasrvdef.manager, non_list_prop)


def test_mfasrvdef_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a MFA server definition.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    api_version = client.query_api_version()
    hmc_version = api_version['hmc-version']
    hmc_version_info = tuple(map(int, hmc_version.split('.')))
    if hmc_version_info < (2, 15, 0):
        skip_warn(f"HMC {hd.host} of version {hmc_version} does not yet "
                  "support MFA server definitions")

    mfasrvdef_name = TEST_PREFIX + ' test_mfasrvdef_crud mfasrvdef1'
    mfasrvdef_name_new = mfasrvdef_name + ' new'

    # Ensure a clean starting point for this test
    try:
        mfasrvdef = console.mfa_server_definitions.find(
            name=mfasrvdef_name)
    except zhmcclient.NotFound:
        pass
    else:
        warnings.warn(
            "Deleting test MFA server definition from previous run: "
            f"{mfasrvdef_name!r}", UserWarning)
        mfasrvdef.delete()

    mfasrvdef = None
    try:

        # Test creating the MFA server definition

        mfasrvdef_input_props = {
            'name': mfasrvdef_name,
            'description': 'Test MFA server def for zhmcclient end2end tests',
            'hostname-ipaddr': '10.11.12.13',
        }
        mfasrvdef_auto_props = {
            'port': 6789,
            'replication-overwrite-possible': False,
        }

        # The code to be tested
        try:
            mfasrvdef = console.mfa_server_definitions.create(
                mfasrvdef_input_props)
        except zhmcclient.HTTPError as exc:
            if exc.http_status == 403 and exc.reason == 1:
                skip_warn(f"HMC userid {hd.userid!r} is not authorized for "
                          "task 'Manage Multi-factor Authentication' on HMC "
                          f"{hd.host}")
            else:
                raise

        for pn, exp_value in mfasrvdef_input_props.items():
            assert mfasrvdef.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"
        mfasrvdef.pull_full_properties()
        for pn, exp_value in mfasrvdef_input_props.items():
            assert mfasrvdef.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"
        for pn, exp_value in mfasrvdef_auto_props.items():
            assert mfasrvdef.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"

        # Test updating a property of the MFA server definition

        new_desc = "Updated MFA server definition description."

        # The code to be tested
        mfasrvdef.update_properties(dict(description=new_desc))

        assert mfasrvdef.properties['description'] == new_desc
        mfasrvdef.pull_full_properties()
        assert mfasrvdef.properties['description'] == new_desc

        # Test that MFA server definitions can be renamed

        # The code to be tested
        mfasrvdef.update_properties(dict(name=mfasrvdef_name_new))

        with pytest.raises(zhmcclient.NotFound):
            console.mfa_server_definitions.find(name=mfasrvdef_name)

    finally:
        if mfasrvdef:
            # Cleanup and test deleting the MFA server definition

            # The code to be tested
            mfasrvdef.delete()

            with pytest.raises(zhmcclient.NotFound):
                console.mfa_server_definitions.find(name=mfasrvdef_name)

            with pytest.raises(zhmcclient.NotFound):
                console.mfa_server_definitions.find(name=mfasrvdef_name_new)
