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


from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import runtest_find_list, runtest_get_properties, \
    validate_list_features

urllib3.disable_warnings()

# Properties in minimalistic Console objects (e.g. find_by_name())
CONSOLE_MINIMAL_PROPS = ['object-uri']

# Properties in Console objects returned by list() without full props
CONSOLE_LIST_PROPS = ['object-uri']

# Properties whose values can change between retrievals of Console objects
CONSOLE_VOLATILE_PROPS = []


def test_console_find_list(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    client = zhmcclient.Client(hmc_session)

    # Pick the single console
    console = client.consoles.console

    runtest_find_list(
        hmc_session, client.consoles, console.name, 'name',
        'object-uri', CONSOLE_VOLATILE_PROPS, CONSOLE_MINIMAL_PROPS,
        CONSOLE_LIST_PROPS)


def test_console_property(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    client = zhmcclient.Client(hmc_session)

    # Select a property that is not returned by list()
    non_list_prop = 'description'

    runtest_get_properties(client.consoles, non_list_prop)


def test_console_list_features(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Tests Console.list_api_features() with and without passing a parameter.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console

    validate_list_features(client.query_api_version(),
                           console.list_api_features(),
                           console.list_api_features('cpc.*'))
