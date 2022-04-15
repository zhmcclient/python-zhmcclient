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

from __future__ import absolute_import, print_function

import random
import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import all_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import runtest_find_list, TEST_PREFIX, End2endTestWarning

urllib3.disable_warnings()

# Properties in minimalistic UserRole objects (e.g. find_by_name())
UROLE_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in UserRole objects returned by list() without full props
UROLE_LIST_PROPS = ['object-uri', 'name', 'type']

# Properties whose values can change between retrievals of UserRole objects
UROLE_VOLATILE_PROPS = []


def test_urole_find_list(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not all_cpcs:
        pytest.skip("No CPCs provided")

    for cpc in all_cpcs:
        session = cpc.manager.session
        console = cpc.manager.client.consoles.console
        client = console.manager.client

        api_version = client.query_api_version()
        hmc_version = api_version['hmc-version']
        # pylint: disable=unnecessary-lambda
        hmc_version_info = list(map(lambda v: int(v), hmc_version.split('.')))
        if hmc_version_info < [2, 13, 0]:
            pytest.skip("HMC {hv} does not yet support user roles".
                        format(hv=hmc_version))

        # Pick a random user role
        urole_list = console.user_roles.list()
        if not urole_list:
            msg_txt = "No user roles defined on CPC {}". \
                format(cpc.name)
            warnings.warn(msg_txt, End2endTestWarning)
            pytest.skip(msg_txt)
        urole = random.choice(urole_list)

        print("Testing on CPC {}".format(cpc.name))

        runtest_find_list(
            session, console.user_roles, urole.name, 'name',
            'object-uri', UROLE_VOLATILE_PROPS, UROLE_MINIMAL_PROPS,
            UROLE_LIST_PROPS)


def test_urole_crud(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a user role.
    """
    if not all_cpcs:
        pytest.skip("No CPCs provided")

    for cpc in all_cpcs:
        print("Testing on CPC {}".format(cpc.name))

        session = cpc.manager.session
        console = cpc.manager.client.consoles.console
        client = console.manager.client
        hd = session.hmc_definition

        api_version = client.query_api_version()
        hmc_version = api_version['hmc-version']
        # pylint: disable=unnecessary-lambda
        hmc_version_info = list(map(lambda v: int(v), hmc_version.split('.')))
        if hmc_version_info < [2, 13, 0]:
            pytest.skip("HMC {hv} does not yet support user roles".
                        format(hv=hmc_version))

        urole_name = TEST_PREFIX + ' test_urole_crud urole1'
        urole_name_new = urole_name + ' new'

        # Ensure a clean starting point for this test
        try:
            urole = console.user_roles.find(name=urole_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test user role from previous run: '{p}' "
                "on CPC '{c}'".
                format(p=urole_name, c=cpc.name), UserWarning)
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
                msg_txt = "HMC userid '{u}' is not authorized for the " \
                    "'Manage User Roles' task on HMC {h}". \
                    format(u=hd.hmc_userid, h=hd.hmc_host)
                warnings.warn(msg_txt, End2endTestWarning)
                pytest.skip(msg_txt)
            else:
                raise

        for pn, exp_value in urole_input_props.items():
            assert urole.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        urole.pull_full_properties()
        for pn, exp_value in urole_input_props.items():
            assert urole.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        for pn, exp_value in urole_auto_props.items():
            assert urole.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)

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
