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
Unit tests for _hw_message module.
"""


import re
from datetime import datetime
import pytest

from zhmcclient import Client, NotFound, HwMessage, timestamp_from_datetime
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


class TestHwMessageConsole:
    """
    All tests for the HwMessage and HwMessageManager classes for the Console.
    """

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
            'element-id': None,
            # element-uri will be automatically set
            'parent': None,
            'class': 'console',
            'name': 'fake-console1',
            'description': 'Console #1',
        })
        self.console = self.client.consoles.find(name=self.faked_console.name)

    def add_hw_message(self, element_id, text, timestamp_dt=None):
        """
        Add a faked hw_message object to the faked Console and return it.
        """
        if timestamp_dt is None:
            timestamp_dt = datetime.now()

        faked_hw_message = self.faked_console.hw_messages.add({
            'element-id': element_id,
            # element-uri will be automatically set
            'parent': None,
            'class': 'hardware-message',
            'text': text,
            'timestamp': timestamp_from_datetime(timestamp_dt),
            'service-supported': True,
            # 'details': ...
        })
        return faked_hw_message

    def test_hw_message_manager_repr(self):
        """Test HwMessageManager.__repr__()."""

        hw_message_mgr = self.console.hw_messages

        # Execute the code to be tested
        repr_str = repr(hw_message_mgr)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{hw_message_mgr.__class__.__name__}\s+at\s+'
            rf'0x{id(hw_message_mgr):08x}\s+\(\\n.*',
            repr_str)

    def test_hw_message_manager_initial_attrs(self):
        """Test initial attributes of HwMessageManager."""

        hw_message_mgr = self.console.hw_messages

        # Verify all public properties of the manager object
        assert hw_message_mgr.resource_class == HwMessage
        assert hw_message_mgr.class_name == 'hardware-message'
        assert hw_message_mgr.session is self.session
        assert hw_message_mgr.parent is self.console

    @pytest.mark.parametrize(
        "full_properties_kwargs, exp_prop_names", [
            (dict(full_properties=False),
             ['element-uri', 'element-id', 'text', 'timestamp']),
            (dict(full_properties=True),
             ['element-uri', 'element-id', 'text', 'timestamp',
              'service-supported']),
            ({},  # test default for full_properties (False)
             ['element-uri', 'element-id', 'text', 'timestamp']),
        ]
    )
    @pytest.mark.parametrize(
        "filter_args, exp_element_ids", [
            (None,
             ['1', '2']),
            ({},
             ['1', '2']),
            ({'element-id': '1'},
             ['1']),
            ({'element-uri': '/api/console/hardware-messages/1'},
             ['1']),
        ]
    )
    def test_hw_message_manager_list(
            self, filter_args, exp_element_ids, full_properties_kwargs,
            exp_prop_names):
        """Test HwMessageManager.list()."""

        faked_hw_message1 = self.add_hw_message(element_id='1', text='foo')
        faked_hw_message2 = self.add_hw_message(element_id='2', text='bar')
        faked_hw_messages = [faked_hw_message1, faked_hw_message2]
        exp_faked_hw_messages = [
            m for m in faked_hw_messages
            if m.properties['element-id'] in exp_element_ids]
        hw_message_mgr = self.console.hw_messages

        # Execute the code to be tested
        hw_messages = hw_message_mgr.list(filter_args=filter_args,
                                          **full_properties_kwargs)

        assert_resources(hw_messages, exp_faked_hw_messages, exp_prop_names)

    def test_hw_message_repr(self):
        """Test HwMessage.__repr__()."""

        faked_hw_message1 = self.add_hw_message(element_id='1', text='foo')
        hw_message_mgr = self.console.hw_messages
        hw_message1 = hw_message_mgr.find(
            **{'element-id': faked_hw_message1.properties['element-id']})

        # Execute the code to be tested
        repr_str = repr(hw_message1)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{hw_message1.__class__.__name__}\s+at\s+'
            rf'0x{id(hw_message1):08x}\s+\(\\n.*',
            repr_str)

    def test_hw_message_delete(self):
        """Test HwMessage.delete()."""

        faked_hw_message1 = self.add_hw_message(element_id='1', text='foo')
        self.add_hw_message(element_id='2', text='bar')

        hw_message_mgr = self.console.hw_messages
        hw_message1 = hw_message_mgr.find(
            **{'element-id': faked_hw_message1.properties['element-id']})

        # Execute the code to be tested.
        hw_message1.delete()

        # Check that the HwMessage no longer exists
        with pytest.raises(NotFound):
            hw_message1 = hw_message_mgr.find(
                **{'element-id': faked_hw_message1.properties['element-id']})
