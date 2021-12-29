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
End2end tests for tasks (on CPCs in DPM mode).

These tests do not change any existing tasks, but create,
modify and delete test tasks.
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

# Properties in minimalistic Task objects (e.g. find_by_name())
TASK_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in Task objects returned by list() without full props
TASK_LIST_PROPS = ['element-uri', 'name']

# Properties whose values can change between retrievals of Task objects
TASK_VOLATILE_PROPS = []


def test_task_find_list(all_cpcs):  # noqa: F811
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
            pytest.skip("HMC {hv} does not yet support tasks".
                        format(hv=hmc_version))

        # Pick a task
        task_list = console.tasks.list()
        assert task_list
        task = task_list[-1]  # Pick the last one returned

        print("Testing on CPC {}".format(cpc.name))

        runtest_find_list(
            session, console.tasks, task.name, 'name', 'element-uri',
            TASK_VOLATILE_PROPS, TASK_MINIMAL_PROPS, TASK_LIST_PROPS)
