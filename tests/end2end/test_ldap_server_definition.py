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

from __future__ import absolute_import, print_function

import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils.cpc_fixtures import all_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import runtest_find_list, TEST_PREFIX, TestWarning

urllib3.disable_warnings()

# Properties in minimalistic CapacityGroup objects (e.g. find_by_name())
LDAPSRVDEF_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in CapacityGroup objects returned by list() without full props
LDAPSRVDEF_LIST_PROPS = ['element-uri', 'name']

# Properties whose values can change between retrievals of CapacityGroup objects
LDAPSRVDEF_VOLATILE_PROPS = []


def test_ldapsrvdef_find_list(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not all_cpcs:
        pytest.skip("No CPCs provided")

    for cpc in all_cpcs:
        session = cpc.manager.session
        console = cpc.manager.client.consoles.console

        # Pick a LDAP server definition
        ldapsrvdef_list = console.ldap_server_definitions.list()
        if not ldapsrvdef_list:
            msg_txt = "No LPAR Server Definitions defined on CPC {}". \
                format(cpc.name)
            warnings.warn(msg_txt, TestWarning)
            pytest.skip(msg_txt)

        ldapsrvdef = ldapsrvdef_list[-1]  # Pick the last one returned

        print("Testing on CPC {}".format(cpc.name))

        runtest_find_list(
            session, console.ldap_server_definitions, ldapsrvdef.name, None,
            'element-uri', LDAPSRVDEF_VOLATILE_PROPS, LDAPSRVDEF_MINIMAL_PROPS,
            LDAPSRVDEF_LIST_PROPS)


def test_ldapsrvdef_crud(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a LDAP server definition.
    """
    if not all_cpcs:
        pytest.skip("No CPCs provided")

    for cpc in all_cpcs:
        print("Testing on CPC {}".format(cpc.name))

        session = cpc.manager.session
        console = cpc.manager.client.consoles.console

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
                "Deleting test LDAP server definition from previous run: '{p}' "
                "on CPC '{c}'".
                format(p=ldapsrvdef_name, c=cpc.name), UserWarning)
            status = ldapsrvdef.get_property('status')
            if status != 'stopped':
                ldapsrvdef.stop()
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
            'tolerate-untrusted-certificates': False,
        }

        # The code to be tested
        try:
            ldapsrvdef = console.ldap_server_definitions.create(
                ldapsrvdef_input_props)
        except zhmcclient.HTTPError as exc:
            if exc.http_status == 403 and exc.reason == 1:
                hd = session.hmc_definition
                msg_txt = "HMC userid '{u}' is not authorized for 'Manage " \
                    "LDAP Server Definitions' task on HMC {h}". \
                    format(u=hd.hmc_userid, h=hd.hmc_host)
                warnings.warn(msg_txt, TestWarning)
                pytest.skip(msg_txt)

        for pn, exp_value in ldapsrvdef_input_props.items():
            assert ldapsrvdef.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        ldapsrvdef.pull_full_properties()
        for pn, exp_value in ldapsrvdef_input_props.items():
            assert ldapsrvdef.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        for pn, exp_value in ldapsrvdef_auto_props.items():
            assert ldapsrvdef.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)

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
