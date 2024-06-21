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

These tests do not change any existing tasks.
"""


from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, runtest_find_list, \
    runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Task objects (e.g. find_by_name())
TASK_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in Task objects returned by list() without full props
TASK_LIST_PROPS = ['element-uri', 'name']

# Properties whose values can change between retrievals of Task objects
TASK_VOLATILE_PROPS = []


def test_task_find_list(hmc_session):  # noqa: F811
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
            "tasks")

    # Pick the tasks to test with
    task_list = console.tasks.list()
    assert task_list  # system-defined and therefore never empty
    task_list = pick_test_resources(task_list)

    for task in task_list:
        print(f"Testing with task {task.name!r}")
        runtest_find_list(
            hmc_session, console.tasks, task.name, 'name', 'element-uri',
            TASK_VOLATILE_PROPS, TASK_MINIMAL_PROPS, TASK_LIST_PROPS)


def test_task_property(hmc_session):  # noqa: F811
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
            "tasks")

    # Pick the tasks to test with
    task_list = console.tasks.list()
    assert task_list  # system-defined and therefore never empty
    task_list = pick_test_resources(task_list)

    for task in task_list:
        print(f"Testing with task {task.name!r}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(task.manager, non_list_prop)
