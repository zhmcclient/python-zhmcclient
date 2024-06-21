# Copyright 2017,2021 IBM Corp. All Rights Reserved.
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
Unit tests for _task module.
"""


import re
import pytest

from zhmcclient import Client, Task
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestTask:
    """All tests for the Task and TaskManager classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Set up a faked session, and add a faked Console without any
        child resources.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

        self.faked_console = self.session.hmc.consoles.add({
            'object-id': None,
            # object-uri will be automatically set
            'parent': None,
            'class': 'console',
            'name': 'fake-console1',
            'description': 'Console #1',
        })
        self.console = self.client.consoles.find(name=self.faked_console.name)

    def add_task(self, name, view_only=True):
        """
        Add a faked task object to the faked Console and return it.
        """
        faked_task = self.faked_console.tasks.add({
            'element-id': f'oid-{name}',
            # element-uri will be automatically set
            'parent': '/api/console',
            'class': 'task',
            'name': name,
            'description': f'Task {name}',
            'view-only-mode-supported': view_only,
        })
        return faked_task

    def test_task_manager_repr(self):
        """Test TaskManager.__repr__()."""

        task_mgr = self.console.tasks

        # Execute the code to be tested
        repr_str = repr(task_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{task_mgr.__class__.__name__}\s+at\s+'
            rf'0x{id(task_mgr):08x}\s+\(\\n.*',
            repr_str)

    def test_task_manager_initial_attrs(self):
        """Test initial attributes of TaskManager."""

        task_mgr = self.console.tasks

        # Verify all public properties of the manager object
        assert task_mgr.resource_class == Task
        assert task_mgr.class_name == 'task'
        assert task_mgr.session is self.session
        assert task_mgr.parent is self.console
        assert task_mgr.console is self.console

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(full_properties=False),
             ['element-uri', 'name']),
            (dict(full_properties=True),
             ['element-uri', 'name', 'description']),
            ({},  # test default for full_properties (False)
             ['element-uri', 'name']),
        ]
    )
    @pytest.mark.parametrize(
        "filter_args, exp_names", [
            (None,
             ['a', 'b']),
            ({},
             ['a', 'b']),
            ({'name': 'a'},
             ['a']),
        ]
    )
    def test_task_manager_list(
            self, filter_args, exp_names, full_properties_kwargs, prop_names):
        """Test TaskManager.list()."""

        faked_task1 = self.add_task(name='a')
        faked_task2 = self.add_task(name='b')
        faked_tasks = [faked_task1, faked_task2]
        exp_faked_tasks = [u for u in faked_tasks if u.name in exp_names]
        task_mgr = self.console.tasks

        # Execute the code to be tested
        tasks = task_mgr.list(filter_args=filter_args,
                              **full_properties_kwargs)

        assert_resources(tasks, exp_faked_tasks, prop_names)

    def test_task_repr(self):
        """Test Task.__repr__()."""

        faked_task1 = self.add_task(name='a')
        task1 = self.console.tasks.find(name=faked_task1.name)

        # Execute the code to be tested
        repr_str = repr(task1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{task1.__class__.__name__}\s+at\s+'
            rf'0x{id(task1):08x}\s+\(\\n.*',
            repr_str)
