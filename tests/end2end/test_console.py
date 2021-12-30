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
End2end tests for the single console object.

These tests do not change the console object.
"""

from __future__ import absolute_import, print_function

import pytest
from requests.packages import urllib3

# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils.cpc_fixtures import all_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import runtest_find_list

urllib3.disable_warnings()

# Properties in minimalistic Console objects (e.g. find_by_name())
CONSOLE_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Console objects returned by list() without full props
CONSOLE_LIST_PROPS = ['object-uri', 'name', 'type']

# Properties whose values can change between retrievals of Console objects
CONSOLE_VOLATILE_PROPS = []


def test_pwrule_find_list(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not all_cpcs:
        pytest.skip("No CPCs provided")

    for cpc in all_cpcs:
        session = cpc.manager.session
        client = cpc.manager.client

        # Pick the single console
        console = client.consoles.console

        print("Testing on CPC {}".format(cpc.name))

        runtest_find_list(
            session, client.consoles, console.name, 'name',
            'object-uri', CONSOLE_VOLATILE_PROPS, CONSOLE_MINIMAL_PROPS,
            CONSOLE_LIST_PROPS)
