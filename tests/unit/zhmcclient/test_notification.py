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


import json
import threading
from collections import namedtuple
import logging
import time
from unittest.mock import patch
import pytest
import stomp

from zhmcclient._notification import NotificationReceiver
from zhmcclient._utils import stomp_uses_frames
from zhmcclient._exceptions import SubscriptionNotFound, \
    NotificationConnectionError
from zhmcclient._constants import JMS_LOGGER_NAME, \
    STOMP_MIN_CONNECTION_CHECK_TIME

# We use the JMS logger for logging. The log is reported by pytest in case
# of testcase errors when using pytest option:
# --log-level debug
# Because threads are involved, it makes sense to add the thread name in the
# log format using pytest option:
# --log-format "%(asctime)s %(threadName)s %(name)s %(levelname)s %(message)s
JMS_LOGGER = logging.getLogger(JMS_LOGGER_NAME)


def create_event_args(headers, message):
    """
    Transform headers, message to event method parameters.
    This is the inverse of get_headers_message().
    """
    if stomp_uses_frames(stomp.__version__):
        Frame = namedtuple('frame', ['headers', 'body'])
        frame = Frame(headers, message)
        frame_args = (frame,)
    else:
        frame_args = headers, message
    return frame_args


class MockedStompConnection:
    """
    A class that replaces stomp.Connection for the usage scope in the
    zhmcclient._notification module, and that adds the ability to
    queue STOMP messages.
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable=unused-argument
        """
        For the mocked connection, we ignore the args (host/port, etc).
        """
        self._state_connected = False
        self._listener = None
        self._connect_userid = None
        self._connect_password = None
        self._connect_wait = None
        self._subscriptions = []  # items: tuple(dest, id, ack)
        self._queued_messages = []  # items: tuple(headers, message_str)
        self._sender_thread = None
        self._ssl_args = None
        self._ssl_kwargs = None

    def set_ssl(self, *args, **kwargs):
        # pylint: disable=unused-argument
        """
        Mocks the same-named method of stomp.Connection.
        """
        assert not self._state_connected
        self._ssl_args = args
        self._ssl_kwargs = kwargs

    def set_listener(self, name, listener):
        # pylint: disable=unused-argument
        """
        Mocks the same-named method of stomp.Connection.
        """
        assert not self._state_connected
        self._listener = listener

    def start(self):
        """
        Mocks the same-named method of stomp.Connection.
        """
        assert not self._state_connected

    def connect(self, userid, password, wait):
        """
        Mocks the same-named method of stomp.Connection.
        """
        JMS_LOGGER.debug(
            "test_notifcation: MockedStompConnection.connect() called")
        if not self._state_connected:
            self._state_connected = True
            self._connect_userid = userid
            self._connect_password = password
            self._connect_wait = wait

    def is_connected(self):
        """
        Mocks the same-named method of stomp.Connection.
        """
        return self._state_connected

    def subscribe(self, destination, id, ack):
        # pylint: disable=redefined-builtin
        """
        Mocks the same-named method of stomp.Connection.
        """
        assert self._state_connected
        self._subscriptions.append((destination, id, ack))

    def unsubscribe(self, id):
        # pylint: disable=redefined-builtin
        """
        Mocks the same-named method of stomp.Connection.
        """
        assert self._state_connected
        for _dest, _id, _ack in self._subscriptions:
            if _id == id:
                self._subscriptions.remove((_dest, _id, _ack))

    def disconnect(self, receipt=None):
        # pylint: disable=unused-argument
        """
        Mocks the same-named method of stomp.Connection.
        """
        JMS_LOGGER.debug(
            "test_notifcation: MockedStompConnection.disconnect() called")
        if self._state_connected:
            self._state_connected = False

    def mock_add_message(self, headers, message):
        """
        Adds a STOMP message to the queue.
        """
        assert self._sender_thread is None
        if not isinstance(message, str):
            message = json.dumps(message)
        self._queued_messages.append((headers, message))

    def mock_start(self):
        """
        Start the STOMP message sender thread.

        This can be done independent of the connection state.
        """
        assert self._sender_thread is None
        self._sender_thread = threading.Thread(target=self.mock_sender_run)
        JMS_LOGGER.debug("test_notifcation: Starting mock sender thread")
        self._sender_thread.start()

    def mock_stop(self):
        """
        Wait for the STOMP message sender thread to finish.

        This can be done independent of the connection state.
        """
        assert self._sender_thread is not None
        JMS_LOGGER.debug(
            "test_notifcation: Waiting for mock sender thread to finish")
        self._sender_thread.join(STOMP_MIN_CONNECTION_CHECK_TIME + 2)
        self._sender_thread = None
        JMS_LOGGER.debug(
            "test_notifcation: Mock sender thread finished")

    def mock_sender_run(self):
        """
        Thread function that runs in the mock sender thread.

        It simulates the HMC sending STOMP messages by sending the previously
        queued STOMP messages to the notification listener.

        It returns when all messages have been sent and thus ends the mock
        sender thread in which it runs.
        """
        JMS_LOGGER.debug(
            "test_notifcation: Mock sender thread gets control")
        for msg_item in self._queued_messages:
            # The following method blocks until it can deliver a message
            headers, message_str = msg_item
            frame_args = create_event_args(headers, message_str)
            self._listener.on_message(*frame_args)
        self._listener.on_disconnected()
        JMS_LOGGER.debug(
            "test_notifcation: Mock sender thread is done")

    def mock_get_subscription(self, topic):
        """
        Find the subscription with the specified topic name and return it.
        """
        for _dest, _id, _ack in self._subscriptions:
            dest = '/topic/' + topic
            if _dest == dest:
                return (_dest, _id, _ack)
        return None


def receiver_run(receiver, msg_items):
    """
    Thread function that will be run in the receiver thread.

    It invokes receiver.notifications() to get notifications which are
    appended to the msg_items list.

    It ends when the main thread calls receiver.close() which causes
    receiver.notifications() to return and thus end the loop.
    """
    JMS_LOGGER.debug(
        "test_notifcation: Receiver thread gets control")
    try:
        for headers, message in receiver.notifications():
            msg_items.append((headers, message))
    except NotificationConnectionError:
        # This happens at the end of some testcases.
        pass
    JMS_LOGGER.debug(
        "test_notifcation: Receiver thread is done")


def receive_notifications(receiver):
    """
    Start a thread running the receiver function and wait for its completion.
    """
    msg_items = []
    receiver_thread = threading.Thread(target=receiver_run,
                                       args=(receiver, msg_items))
    JMS_LOGGER.debug(
        "test_notifcation: Starting receiver thread")
    receiver_thread.start()
    # Allow for some time to process the received messages
    time.sleep(0.5)
    JMS_LOGGER.debug(
        "test_notifcation: Triggering receiver close")
    receiver.close()
    JMS_LOGGER.debug(
        "test_notifcation: Waiting for receiver thread to finish")
    receiver_thread.join(STOMP_MIN_CONNECTION_CHECK_TIME + 1)
    if receiver_thread.is_alive():
        raise AssertionError("receiver_thread is still alive")
    return msg_items


class TestNotificationOneTopic:
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

    def setup_receiver(self):
        """Set up the notification receiver for the test"""
        receiver = NotificationReceiver(self.topic, self.hmc, self.userid,
                                        self.password)
        receiver.connect()
        mocked_conn = receiver._conn  # pylint: disable=protected-access
        assert isinstance(mocked_conn, MockedStompConnection)
        return receiver, mocked_conn

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_no_messages(self):
        """Test function for not receiving any notification."""

        receiver, mocked_conn = self.setup_receiver()

        # We do not add any STOMP messages

        mocked_conn.mock_start()  # pylint: disable=no-member
        msg_items = receive_notifications(receiver)
        mocked_conn.mock_stop()  # pylint: disable=no-member

        assert msg_items == []

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_one_message(self):
        """Test function for receiving one notification."""

        receiver, mocked_conn = self.setup_receiver()

        # Add one STOMP message to be sent
        message_obj = dict(a=1, b=2)
        # pylint: disable=no-member
        mocked_conn.mock_add_message(self.std_headers, message_obj)

        mocked_conn.mock_start()  # pylint: disable=no-member
        msg_items = receive_notifications(receiver)
        mocked_conn.mock_stop()  # pylint: disable=no-member

        assert len(msg_items) == 1

        msg0 = msg_items[0]
        assert msg0[0] == self.std_headers
        assert msg0[1] == message_obj


class TestNotificationTwoTopics:
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

    def setup_receiver(self):
        """Set up the notification receiver for the test"""
        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        receiver.connect()
        mocked_conn = receiver._conn  # pylint: disable=protected-access
        assert isinstance(mocked_conn, MockedStompConnection)
        return receiver, mocked_conn

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_no_messages(self):
        """Test function for not receiving any notification."""

        receiver, mocked_conn = self.setup_receiver()

        # We do not add any STOMP messages

        mocked_conn.mock_start()  # pylint: disable=no-member
        msg_items = receive_notifications(receiver)
        mocked_conn.mock_stop()  # pylint: disable=no-member

        assert msg_items == []

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_one_message(self):
        """Test function for receiving one notification."""

        receiver, mocked_conn = self.setup_receiver()

        # Add one STOMP message to be sent
        message_obj = dict(a=1, b=2)
        # pylint: disable=no-member
        mocked_conn.mock_add_message(self.std_headers, message_obj)

        mocked_conn.mock_start()  # pylint: disable=no-member
        msg_items = receive_notifications(receiver)
        mocked_conn.mock_stop()  # pylint: disable=no-member

        assert len(msg_items) == 1

        msg0 = msg_items[0]
        assert msg0[0] == self.std_headers
        assert msg0[1] == message_obj


class TestNotificationSubscriptionMgmt:
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

    def setup_receiver(self):
        """Set up the notification receiver for the test"""
        receiver = NotificationReceiver(self.topics, self.hmc, self.userid,
                                        self.password)
        receiver.connect()
        mocked_conn = receiver._conn  # pylint: disable=protected-access
        assert isinstance(mocked_conn, MockedStompConnection)
        return receiver, mocked_conn

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_is_subscribed(self):
        """Test function for is_subscribed() method."""

        receiver, mocked_conn = self.setup_receiver()

        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic2')

        result = receiver.is_subscribed('fake-topic1')
        assert result is True

        result = receiver.is_subscribed('foo')
        assert result is False

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_get_subscription(self):
        """Test function for get_subscription() method."""

        receiver, mocked_conn = self.setup_receiver()

        id_value1 = receiver.get_subscription('fake-topic1')
        id_value2 = receiver.get_subscription('fake-topic2')
        assert id_value1 != id_value2

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic2')

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_get_subscription_nonexisting(self):
        """Test function for get_subscription() method for a non-existing
        subscription.."""

        receiver, mocked_conn = self.setup_receiver()

        with pytest.raises(SubscriptionNotFound):
            receiver.get_subscription('bla')

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic2')

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_subscribe(self):
        """Test function for subscribe() method."""

        receiver, mocked_conn = self.setup_receiver()

        receiver.subscribe('foo')

        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('foo')

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic2')

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_unsubscribe(self):
        """Test function for unsubscribe() method."""

        receiver, mocked_conn = self.setup_receiver()

        receiver.unsubscribe('fake-topic1')

        # pylint: disable=no-member
        assert not mocked_conn.mock_get_subscription('fake-topic1')

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic2')

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_unsubscribe_nonexisting(self):
        """Test function for unsubscribe() for a non-existing subscription."""

        receiver, mocked_conn = self.setup_receiver()

        with pytest.raises(SubscriptionNotFound):
            receiver.unsubscribe('bla')

        # Check that the subscriptions are still in place
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic1')
        # pylint: disable=no-member
        assert mocked_conn.mock_get_subscription('fake-topic2')
