# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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
import six
import pytest

from zhmcclient._notification import NotificationReceiver
from zhmcclient._exceptions import SubscriptionNotFound


class MockedStompConnection(object):
    """
    A class that replaces stomp.Connection for the usage scope in the
    zhmcclient._notification module, and that adds the ability to
    queue STOMP messages.
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable=unused-argument
        """We ignore the args:
            [(self._host, self._port)], use_ssl="SSL")
        """
        self._state_connected = False
        self._listener = None
        self._connect_userid = None
        self._connect_password = None
        self._connect_wait = None
        self._subscriptions = []  # items: tuple(dest, id, ack)
        self._queued_messages = []  # items: tuple(headers, message_str)
        self._sender_thread = None

    def set_listener(self, name, listener):
        # pylint: disable=unused-argument
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
        # pylint: disable=redefined-builtin
        """Mocks the same-named method of stomp.Connection."""
        assert self._state_connected
        self._subscriptions.append((destination, id, ack))

    def unsubscribe(self, id):
        # pylint: disable=redefined-builtin
        """Mocks the same-named method of stomp.Connection."""
        assert self._state_connected
        for _dest, _id, _ack in self._subscriptions:
            if _id == id:
                self._subscriptions.remove((_dest, _id, _ack))

    def disconnect(self):
        """Mocks the same-named method of stomp.Connection."""
        assert self._state_connected
        self._sender_thread.join()
        self._sender_thread = None
        self._state_connected = False

    def mock_add_message(self, headers, message):
        """Adds a STOMP message to the queue."""
        assert self._sender_thread is None
        if not isinstance(message, six.string_types):
            message = json.dumps(message)
        self._queued_messages.append((headers, message))

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

    def mock_get_subscription(self, topic):
        """Find the subscription with the specified topic name and return it"""
        for _dest, _id, _ack in self._subscriptions:
            dest = '/topic/' + topic
            if _dest == dest:
                return (_dest, _id, _ack)
        return None


def receiver_run(receiver, msg_items):
    """
    Receiver function that will be run in a thread.
    It invokes the receiver until out of notifications, then return them as a
    list.
    """
    for headers, message in receiver.notifications():
        msg_items.append((headers, message))
    return msg_items


def receive_notifications(receiver):
    """
    Start a thread running the receiver function and wait for its completion.
    """
    msg_items = []
    receiver_thread = threading.Thread(target=receiver_run,
                                       args=(receiver, msg_items))
    receiver_thread.start()
    receiver.close()
    receiver_thread.join(1.0)
    if receiver_thread.is_alive():
        raise AssertionError("receiver_thread is still alive")
    return msg_items


class TestNotificationOneTopic(object):
    """
    Test class for one notification topic.
    """

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

        self.topic = 'fake-topic'
        self.hmc = 'fake-hmc'
        self.userid = 'fake-userid'
        self.password = 'fake-password'
        self.std_headers = {
            'notification-type': 'fake-type'
        }

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_no_messages(self):
        """Test function for not receiving any notification."""

        receiver = NotificationReceiver(self.topic, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        # We do not add any STOMP messages

        conn.mock_start()  # pylint: disable=no-member
        msg_items = receive_notifications(receiver)

        assert msg_items == []

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_one_message(self):
        """Test function for receiving one notification."""

        receiver = NotificationReceiver(self.topic, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        # Add one STOMP message to be sent
        message_obj = dict(a=1, b=2)
        # pylint: disable=no-member
        conn.mock_add_message(self.std_headers, message_obj)

        conn.mock_start()  # pylint: disable=no-member
        msg_items = receive_notifications(receiver)

        assert len(msg_items) == 1

        msg0 = msg_items[0]
        assert msg0[0] == self.std_headers
        assert msg0[1] == message_obj


class TestNotificationTwoTopics(object):
    """
    Test class for two notification topics.
    """

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

        self.topics = ('fake-topic1', 'fake-topic2')
        self.hmc = 'fake-hmc'
        self.userid = 'fake-userid'
        self.password = 'fake-password'
        self.std_headers = {
            'notification-type': 'fake-type'
        }

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_no_messages(self):
        """Test function for not receiving any notification."""

        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        # We do not add any STOMP messages

        conn.mock_start()  # pylint: disable=no-member
        msg_items = receive_notifications(receiver)

        assert msg_items == []

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_one_message(self):
        """Test function for receiving one notification."""

        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        # Add one STOMP message to be sent
        message_obj = dict(a=1, b=2)
        # pylint: disable=no-member
        conn.mock_add_message(self.std_headers, message_obj)

        conn.mock_start()  # pylint: disable=no-member
        msg_items = receive_notifications(receiver)

        assert len(msg_items) == 1

        msg0 = msg_items[0]
        assert msg0[0] == self.std_headers
        assert msg0[1] == message_obj


class TestNotificationSubscriptionMgmt(object):
    """
    Test class for subscription management.
    """

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

        self.topics = ('fake-topic1', 'fake-topic2')
        self.hmc = 'fake-hmc'
        self.userid = 'fake-userid'
        self.password = 'fake-password'
        self.std_headers = {
            'notification-type': 'fake-type'
        }

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_is_subscribed(self):
        """Test function for is_subscribed() method."""

        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic2')

        result = receiver.is_subscribed('fake-topic1')
        assert result is True

        result = receiver.is_subscribed('foo')
        assert result is False

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_get_subscription(self):
        """Test function for get_subscription() method."""

        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        id_value1 = receiver.get_subscription('fake-topic1')
        id_value2 = receiver.get_subscription('fake-topic2')
        assert id_value1 != id_value2

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic2')

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_get_subscription_nonexisting(self):
        """Test function for get_subscription() method for a non-existing
        subscription.."""

        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        with pytest.raises(SubscriptionNotFound):
            receiver.get_subscription('bla')

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic2')

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_subscribe(self):
        """Test function for subscribe() method."""

        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        receiver.subscribe('foo')

        # pylint: disable=no-member
        assert conn.mock_get_subscription('foo')

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic2')

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_unsubscribe(self):
        """Test function for unsubscribe() method."""

        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        receiver.unsubscribe('fake-topic1')

        # pylint: disable=no-member
        assert not conn.mock_get_subscription('fake-topic1')

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic2')

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_unsubscribe_nonexisting(self):
        """Test function for unsubscribe() for a non-existing subscription."""

        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        conn = receiver._conn  # pylint: disable=protected-access

        with pytest.raises(SubscriptionNotFound):
            receiver.unsubscribe('bla')

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert conn.mock_get_subscription('fake-topic2')
