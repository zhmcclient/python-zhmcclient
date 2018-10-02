# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Unit tests for _notification module.

The test strategy is to mock the STOMP messages of the HMC using the
requests_mock package.
"""

from __future__ import absolute_import, print_function

import json
import threading
from mock import patch

from zhmcclient._notification import NotificationReceiver


class MockedStompConnection(object):
    """
    A class that replaces stomp.Connection for the usage scope in the
    zhmcclient._notification module, and that adds the ability to
    queue STOMP messages.
    """

    def __init__(self, *args, **kwargs):
        """We ignore the args:
            [(self._host, self._port)], use_ssl="SSL")
        """
        self._state_connected = False
        self._listener = None
        self._connect_userid = None
        self._connect_password = None
        self._connect_wait = None
        self._subscribe_destination = None
        self._subscribe_id = None
        self._subscribe_ack = None
        self._queued_messages = []  # items: tuple(headers, message_str)
        self._sender_thread = None

    def set_listener(self, name, listener):
        """Mocks the same-named method of stomp.Connection."""
        assert not self._state_connected
        self._listener = listener

    def start(self):
        """Mocks the same-named method of stomp.Connection."""
        assert not self._state_connected

    def connect(self, userid, password, wait):
        """Mocks the same-named method of stomp.Connection."""
        assert not self._state_connected
        self._state_connected = True
        self._connect_userid = userid
        self._connect_password = password
        self._connect_wait = wait

    def subscribe(self, destination, id, ack):
        """Mocks the same-named method of stomp.Connection."""
        assert self._state_connected
        self._subscribe_destination = destination
        self._subscribe_id = id
        self._subscribe_ack = ack

    def disconnect(self):
        """Mocks the same-named method of stomp.Connection."""
        assert self._state_connected
        self._sender_thread.join()
        self._sender_thread = None
        self._state_connected = False

    def mock_add_message(self, headers, message_obj):
        """Adds a STOMP message to the queue."""
        assert self._sender_thread is None
        message_str = json.dumps(message_obj)
        self._queued_messages.append((headers, message_str))

    def mock_start(self):
        """Start the STOMP message sender thread."""
        assert self._state_connected
        self._sender_thread = threading.Thread(target=self.mock_sender_run)
        self._sender_thread.start()

    def mock_sender_run(self):
        """Simulates the HMC sending STOMP messages. This method runs in a
        separate thread and processes the queued STOMP messages and sends
        them to the notification listener set up by the NotificationReceiver
        class."""
        for msg_item in self._queued_messages:
            # The following method blocks until it can deliver a message
            headers, message_str = msg_item
            self._listener.on_message(headers, message_str)
        self._listener.on_disconnected()


def receiver_run(receiver, msg_items):
    for headers, message in receiver.notifications():
        msg_items.append((headers, message))
    return msg_items


def receive_notifications(receiver):
    msg_items = []
    receiver_thread = threading.Thread(target=receiver_run,
                                       args=(receiver, msg_items))
    receiver_thread.start()
    receiver.close()
    receiver_thread.join(1.0)
    if receiver_thread.is_alive():
        raise AssertionError("receiver_thread is still alive")
    return msg_items


class TestNotification(object):

    def setup_method(self):
        self.topic = 'fake-topic'
        self.hmc = 'fake-hmc'
        self.userid = 'fake-userid'
        self.password = 'fake-password'
        self.std_headers = {
            'notification-type': 'fake-type'
        }

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_no_messages(self):
        receiver = NotificationReceiver(self.topic, self.hmc, self.userid,
                                        self.password)

        conn = receiver._conn

        # We do not add any STOMP messages

        conn.mock_start()
        msg_items = receive_notifications(receiver)

        assert msg_items == []

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_one_message(self):
        receiver = NotificationReceiver(self.topic, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn

        # Add one STOMP message to be sent
        message_obj = dict(a=1, b=2)
        conn.mock_add_message(self.std_headers, message_obj)

        conn.mock_start()
        msg_items = receive_notifications(receiver)

        assert len(msg_items) == 1

        msg0 = msg_items[0]
        assert msg0[0] == self.std_headers
        assert msg0[1] == message_obj
