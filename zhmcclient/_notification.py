#!/usr/bin/env python
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
The HMC supports the publishing of notifications for specific topics. This
includes for example asynchronous job completion, property or status changes,
and operating system messages issued in an LPAR or DPM partition.

The zhmcclient package supports receiving HMC notifications in an easy-to-use
way, as shown in the following example that receives and displays OS messages
for a DPM partition::

    import zhmcclient

    hmc = ...
    userid = ...
    password = ...

    session = zhmcclient.Session(hmc, userid, password)
    client = zhmcclient.Client(session)
    cpc = client.cpcs.find(name=cpcname)
    partition = cpc.partitions.find(name=partname)

    topic = partition.open_os_message_channel(include_refresh_messages=True)

    print("Subscribing for OS messages for partition %s on CPC %s using "
          "notifications..." % (partition.name, cpc.name))

    receiver = zhmcclient.NotificationReceiver(
        topic, hmc, session.session_id, session.session_credential)

    while True:
        try:
            for headers, message in receiver.notifications():
                print("HMC notification #%s:" % headers['session-sequence-nr'])
                os_msg_list = message['os-messages']
                for os_msg in os_msg_list:
                    msg_txt = os_msg['message-text'].strip('\\n')
                    msg_id = os_msg['message-id']
                    print("OS message #%s:\\n%s" % (msg_id, msg_txt))
        except zhmcclient.NotificationError as exc:
            print(f"Notification Error: {exc} - reconnecting")
            continue
        except stomp.exception.StompException as exc:
            print("fSTOMP Error: {exc} - reconnecting")
            continue
        except KeyboardInterrupt:
            print("Keyboard Interrupt - leaving")
            receiver.close()
            break
        else:
            print("Receiver has been closed  - leaving")
            break

When running this example code in one terminal, and stopping or starting
the partition in another terminal, one can monitor the shutdown or boot
messages issued by the operating system. The following commands use the
``zhmc`` CLI provided in the :term:`zhmccli project` to do that:

.. code-block:: text

    $ zhmc partition stop {cpc-name} {partition-name}
    $ zhmc partition start {cpc-name} {partition-name}
"""


import os
import json
import ssl
import queue
from collections import namedtuple
import logging
import uuid

from ._logging import logged_api_call
from ._constants import DEFAULT_STOMP_PORT, DEFAULT_STOMP_CONNECT_TIMEOUT, \
    DEFAULT_STOMP_CONNECT_RETRIES, DEFAULT_STOMP_RECONNECT_SLEEP_INITIAL, \
    DEFAULT_STOMP_RECONNECT_SLEEP_INCREASE, DEFAULT_STOMP_RECONNECT_SLEEP_MAX, \
    DEFAULT_STOMP_RECONNECT_SLEEP_JITTER, DEFAULT_STOMP_KEEPALIVE, \
    DEFAULT_STOMP_HEARTBEAT_SEND_CYCLE, DEFAULT_STOMP_HEARTBEAT_RECEIVE_CYCLE, \
    DEFAULT_STOMP_HEARTBEAT_RECEIVE_CHECK, STOMP_MIN_CONNECTION_CHECK_TIME, \
    JMS_LOGGER_NAME
from ._exceptions import NotificationJMSError, NotificationParseError, \
    SubscriptionNotFound, NotificationConnectionError, \
    NotificationSubscriptionError
from ._utils import get_stomp_rt_kwargs, get_headers_message

__all__ = ['NotificationReceiver', 'StompRetryTimeoutConfig']

# Write a log message for each STOMP heartbeat sent or received
DEBUG_HEARTBEATS = False

JMS_LOGGER = logging.getLogger(JMS_LOGGER_NAME)


class StompRetryTimeoutConfig:
    # pylint: disable=too-few-public-methods
    """
    A configuration setting that specifies various retry and timeout related
    parameters for STOMP connections to the HMC for receiving notifictions.

    HMC/SE version requirements: None
    """

    def __init__(self, connect_timeout=None, connect_retries=None,
                 reconnect_sleep_initial=None, reconnect_sleep_increase=None,
                 reconnect_sleep_max=None, reconnect_sleep_jitter=None,
                 keepalive=None, heartbeat_send_cycle=None,
                 heartbeat_receive_cycle=None, heartbeat_receive_check=None):
        # pylint: disable=line-too-long
        """
        For all parameters, `None` means that this object does not specify a
        value for the parameter, and that a default value will be used
        (see :ref:`Constants`).

        All parameters are available as instance attributes.

        Parameters:

          connect_timeout (:term:`number`): STOMP connect timeout in seconds.
            This timeout applies to making a connection at the socket level.
            The special value 0 means that no timeout is set.

          connect_retries (:term:`integer`): Number of retries (after the
            initial attempt) for STOMP connection-related issues. These retries
            are performed for failed DNS lookups, failed socket connections, and
            socket connection timeouts.
            The special value -1 means that there are infinite retries.

          reconnect_sleep_initial (:term:`number`): Initial STOMP reconnect
            sleep delay in seconds. The reconnect sleep delay is the time to
            wait before reconnecting.

          reconnect_sleep_increase (:term:`number`): Factor by which the
            reconnect sleep delay is increased after each connection attempt.
            For example, 0.5 means to wait 50% longer than before the previous
            attempt, 1.0 means wait twice as long, and 0.0 means keep the delay
            constant.

          reconnect_sleep_max (:term:`number`): Maximum reconnect sleep delay
            in seconds, regardless of the `reconnect_sleep_increase` value.

          reconnect_sleep_jitter (:term:`number`): Random additional time to
            wait before a reconnect to avoid stampeding, as a percentage of the
            current reconnect sleep delay. For example, a value of 0.1 means to
            wait an extra 0%-10% of the delay calculated using the previous
            three parameters.

          keepalive (bool): Enable keepalive at the socket level.

          heartbeat_send_cycle (:term:`number`): Cycle time in which the client
            will send heartbeats to the HMC, in seconds.
            This time is sent to the HMC as the minimum cycle time the client
            can do, and the HMC returns that time as the cycle time in which it
            wants to receive heartbeats.
            The cycle time should not be less than 0.2 sec; a few seconds is
            a reasonable value.
            The special value 0 disables the sending of heartbeats to the HMC.

          heartbeat_receive_cycle (:term:`number`): Cycle time in which the
            HMC will send heartbeats to the client, in seconds.
            This time is sent to the HMC as the cycle time in which the client
            wants to receive heartbeats, and the HMC uses that time to send
            heartbeats.
            The cycle time should not be less than 0.2 sec; a few seconds is
            a reasonable value.
            The special value 0 disables heartbeat sending by the HMC and
            checking on the client side.

          heartbeat_receive_check (:term:`number`): Additional time for
            checking the heartbeats received from the HMC on the client,
            as a percentage of the 'heartbeat_receive_cycle' time.
            For example, a value of 0.5 means to wait an extra 50% of the
            'heartbeat_receive_cycle' time.
            This value should not be less than 0.5, and a value of 1 or 2 is
            a reasonable value.
        """  # noqa: E501
        self.connect_timeout = connect_timeout
        self.connect_retries = connect_retries
        self.reconnect_sleep_initial = reconnect_sleep_initial
        self.reconnect_sleep_increase = reconnect_sleep_increase
        self.reconnect_sleep_max = reconnect_sleep_max
        self.reconnect_sleep_jitter = reconnect_sleep_jitter
        self.keepalive = keepalive
        self.heartbeat_send_cycle = heartbeat_send_cycle
        self.heartbeat_receive_cycle = heartbeat_receive_cycle
        self.heartbeat_receive_check = heartbeat_receive_check

    _attrs = ('connect_timeout', 'connect_retries', 'reconnect_sleep_initial',
              'reconnect_sleep_increase', 'reconnect_sleep_max',
              'reconnect_sleep_jitter', 'keepalive', 'heartbeat_send_cycle',
              'heartbeat_receive_cycle', 'heartbeat_receive_check')

    def override_with(self, override_config):
        """
        Return a new configuration object that represents the configuration
        from this configuration object acting as a default, and the specified
        configuration object overriding that default for any of its
        attributes that are not `None`.

        Parameters:

          override_config (:class:`~zhmcclient.StompRetryTimeoutConfig`):
            The configuration object overriding the defaults defined in this
            configuration object.

        Returns:

          :class:`~zhmcclient.StompRetryTimeoutConfig`:
            A new configuration object representing this configuration object,
            overridden by the specified configuration object.
        """
        ret = StompRetryTimeoutConfig()
        for attr in StompRetryTimeoutConfig._attrs:
            value = getattr(self, attr)
            if override_config and getattr(override_config, attr) is not None:
                value = getattr(override_config, attr)
            setattr(ret, attr, value)
        return ret


class NotificationReceiver:
    """
    A class for receiving HMC notifications that are published to particular
    HMC notification topics.

    **Experimental:** This class is considered experimental at this point, and
    its API may change incompatibly as long as it is experimental.

    Creating an object of this class establishes a JMS session with the
    HMC and subscribes for the specified HMC notification topic(s).

    Notification topic strings are created by the HMC in context of a
    particular client session (i.e. :class:`~zhmcclient.Session` object).
    However, these topic strings can be used by any JMS message listener that
    knows the topic string and that authenticates under some valid HMC userid.
    The HMC userid used by the JMS listener does not need to be the one that
    was used for the client session in which the notification topic was
    originally created.

    HMC/SE version requirements: None
    """

    default_stomp_rt_config = StompRetryTimeoutConfig(
        connect_timeout=DEFAULT_STOMP_CONNECT_TIMEOUT,
        connect_retries=DEFAULT_STOMP_CONNECT_RETRIES,
        reconnect_sleep_initial=DEFAULT_STOMP_RECONNECT_SLEEP_INITIAL,
        reconnect_sleep_increase=DEFAULT_STOMP_RECONNECT_SLEEP_INCREASE,
        reconnect_sleep_max=DEFAULT_STOMP_RECONNECT_SLEEP_MAX,
        reconnect_sleep_jitter=DEFAULT_STOMP_RECONNECT_SLEEP_JITTER,
        keepalive=DEFAULT_STOMP_KEEPALIVE,
        heartbeat_send_cycle=DEFAULT_STOMP_HEARTBEAT_SEND_CYCLE,
        heartbeat_receive_cycle=DEFAULT_STOMP_HEARTBEAT_RECEIVE_CYCLE,
        heartbeat_receive_check=DEFAULT_STOMP_HEARTBEAT_RECEIVE_CHECK,
    )

    def __init__(self, topic_names, host, userid, password,
                 port=DEFAULT_STOMP_PORT, stomp_rt_config=None):
        """
        Parameters:

          topic_names (:term:`string` or list/tuple thereof): Name(s) of the
            HMC notification topic(s).
            Must not be `None`.

          host (:term:`string`):
            HMC host. For valid formats, see the
            :attr:`~zhmcclient.Session.host` property.
            Must not be `None`.

          userid (:term:`string`):
            Userid for logging on to the HMC message broker.
            Must not be `None`.

            If the HMC userid is configured to use MFA, this must be the
            session ID of a session that user has with the HMC.
            Otherwise, it can either be the session ID, or the HMC userid.

          password (:term:`string`):
            Password for logging on to the HMC message broker.
            Must not be `None`.

            If `userid` specifies a session ID, this must be the session
            credential for that session ID.
            If `userid` specifies an HMC userid, this must be the password
            for that userid.

          port (:term:`integer`):
            STOMP TCP port. Defaults to
            :attr:`~zhmcclient._constants.DEFAULT_STOMP_PORT`.

          stomp_rt_config (:class:`~zhmcclient.StompRetryTimeoutConfig`):
            The STOMP retry/timeout configuration for this session, overriding
            any defaults.

            `None` for an attribute in that configuration object means that the
            default value will be used for that attribute.

            `None` for the entire `stomp_rt_config` parameter means that a
            default configuration will be used with the default values for all
            of its attributes.

            See :ref:`Constants` for the default values.
        """
        if not isinstance(topic_names, (list, tuple)):
            topic_names = [topic_names]
        self._topic_names = topic_names
        self._host = host
        self._userid = userid
        self._password = password
        self._port = port
        self._rt_config = stomp_rt_config
        self._rt_config = self.default_stomp_rt_config.override_with(
            stomp_rt_config)

        # Subscription ID numbers that are in use.
        # Each subscription for a topic gets its own unique ID.
        # - key: topic name
        # - value: Subscription ID number
        self._sub_ids = {}

        # Next subscription ID number to be used.
        # After allocating a subscription ID number, this number is increased.
        # It is never decreased again.
        self._next_sub_id = 1

        # Process PID, used to ensure uniqueness of subscription ID
        self._process_pid = os.getpid()

        # Thread-safe handover queue between listener thread and receiver
        # thread
        self._handover_queue = queue.Queue(10)

        # STOMP connection
        self._conn = None

        # Open/closed state of the receiver
        self._closed = False

        # Lazy importing of the stomp module, because the import is slow in some
        # versions.
        # pylint: disable=import-outside-toplevel
        import stomp
        self._stomp = stomp

    @logged_api_call
    def connect(self):
        """
        Create a listener, connect to the HMC and subscribe for the specified
        topics.

        If a connection exists with the HMC, it is first closed.

        Note: STOMP does not nicely recover when just performing a STOMP connect
        after a connection loss, because there are occurrences of
        ssl.SSLError: PROTOCOL_IS_SHUTDOWN. Therefore, we create a new
        listener as well.

        Raises:

            NotificationConnectionError: STOMP connection failed.
            NotificationSubscriptionError: STOMP subscription failed.
        """

        # In case of reconnect, close the previous connection. This will also
        # stop the listener thread.
        if self._conn:
            JMS_LOGGER.info(
                "Disconnecting previous STOMP connection")
            self._conn.disconnect(receipt=uuid.uuid4())

        # Set up the STOMP listener
        JMS_LOGGER.info("Setting up a STOMP connection")
        rt_kwargs = get_stomp_rt_kwargs(self._rt_config)
        self._conn = self._stomp.Connection(
            [(self._host, self._port)], **rt_kwargs)
        set_kwargs = dict()
        set_kwargs['ssl_version'] = ssl.PROTOCOL_TLS_CLIENT
        self._conn.set_ssl(for_hosts=[(self._host, self._port)], **set_kwargs)
        listener = _NotificationListener(self._handover_queue)
        self._conn.set_listener('', listener)

        connected = self.is_connected()
        JMS_LOGGER.info(
            "Connecting via STOMP to the HMC (currently connected: %s)",
            connected)
        try:
            # wait=True causes the connection to be retried for some times
            # and finally raises stomp.ConnectFailedException
            self._conn.connect(self._userid, self._password, wait=True)
        except Exception as exc:
            msg = f"STOMP connection failed: {exc.__class__.__name__}: {exc}"
            JMS_LOGGER.warning(msg)
            raise NotificationConnectionError(msg)
        JMS_LOGGER.info("STOMP connection successfully established")

        for topic_name in self._topic_names:
            self.subscribe(topic_name)

    @logged_api_call
    def is_connected(self):
        """
        Return whether this notification receiver is currently connected to
        the HMC.
        """
        if self._conn:
            return self._conn.is_connected()
        return False

    def _id_value(self, sub_id):
        """
        Create the subscription ID from the subscription ID number.
        """
        id_value = f'zhmcclient.{self._process_pid}.{id(self)}.{sub_id}'
        return id_value

    @logged_api_call
    def subscribe(self, topic_name):
        """
        Subscribe this notification receiver for a topic.

        Parameters:

          topic_name (:term:`string`): Name of the HMC notification topic.
            Must not be `None`.

        Returns:

            string: Subscription ID

        Raises:

            NotificationSubscriptionError: STOMP subscription failed.
        """
        dest = "/topic/" + topic_name
        sub_id = self._next_sub_id
        self._next_sub_id += 1
        self._sub_ids[topic_name] = sub_id
        id_value = self._id_value(sub_id)
        JMS_LOGGER.info(
            "Subscribing via STOMP for object notification topic '%s'",
            topic_name)
        try:
            self._conn.subscribe(destination=dest, id=id_value, ack='auto')
        except Exception as exc:
            msg = f"STOMP subscription failed: {exc.__class__.__name__}: {exc}"
            JMS_LOGGER.warning(msg)
            raise NotificationSubscriptionError(msg)
        return id_value

    @logged_api_call
    def unsubscribe(self, topic_name):
        """
        Unsubscribe this notification receiver from a topic.

        If the topic is not currently subscribed for by this receiver,
        SubscriptionNotFound is raised.

        Parameters:

          topic_name (:term:`string`): Name of the HMC notification topic.
            Must not be `None`.

        Raises:

            SubscriptionNotFound: Topic is not currently subscribed for.
            NotificationSubscriptionError: STOMP unsubscription failed.
        """
        try:
            sub_id = self._sub_ids[topic_name]
        except KeyError:
            raise SubscriptionNotFound(
                f"Subscription topic {topic_name!r} is not currently "
                "subscribed for")
        id_value = self._id_value(sub_id)
        JMS_LOGGER.info(
            "Unsubscribing via STOMP from object notification topic '%s'",
            topic_name)
        try:
            self._conn.unsubscribe(id=id_value)
        except Exception as exc:
            msg = (
                f"STOMP unsubscription failed: {exc.__class__.__name__}: "
                f"{exc}")
            JMS_LOGGER.warning(msg)
            raise NotificationSubscriptionError(msg)

    @logged_api_call
    def is_subscribed(self, topic_name):
        """
        Return whether this notification receiver is currently subscribed for a
        topic.

        Parameters:

          topic_name (:term:`string`): Name of the HMC notification topic.
            Must not be `None`.
        """
        return topic_name in self._sub_ids

    @logged_api_call
    def get_subscription(self, topic_name):
        """
        Return the subscription ID for a topic this notification receiver is
        subscribed for.

        If the topic is not currently subscribed for by this receiver,
        SubscriptionNotFound is raised.

        Parameters:

          topic_name (:term:`string`): Name of the HMC notification topic.
            Must not be `None`.
        """
        try:
            sub_id = self._sub_ids[topic_name]
        except KeyError:
            raise SubscriptionNotFound(
                f"Subscription topic {topic_name!r} is not currently "
                "subscribed for")
        return self._id_value(sub_id)

    @logged_api_call
    def notifications(self):
        """
        Generator method that yields all HMC notifications (= JMS messages)
        received by this notification receiver.

        The method connects to the HMC if needed, so after raising
        :exc:`~zhmcclient.NotificationConnectionError` or
        :exc:`stomp.exception.StompException`, it can simply be called
        again to reconnect and resume waiting for notifications.

        This method returns only when the receiver is closed
        (using :meth:`~zhmcclient.NotificationRecever.close`) by some other
        thread; any errors do not cause the method to return but always cause
        an exception to be raised.

        For an example how to use this method, see
        :ref:`Notifications` or the example scripts.

        Yields:

          : A tuple (headers, message) representing one HMC notification, with:

          * headers (dict): The notification header fields.

            Some important header fields (dict items) are:

            * 'notification-type' (string): The HMC notification type (e.g.
              'os-message', 'job-completion', or others).

            * 'session-sequence-nr' (string): The sequence number of this HMC
              notification within the session created by this notification
              receiver object. This number starts at 0 when this receiver
              object is created, and is incremented each time an HMC
              notification is published to this receiver.

            * 'class' (string): The class name of the HMC resource publishing
              the HMC notification (e.g. 'partition').

            * 'object-id' (string) or 'element-id' (string): The ID of the HMC
              resource publishing the HMC notification.

            For a complete list of notification header fields, see section
            "Message format" in chapter 4. "Asynchronous notification" in the
            :term:`HMC API` book.

          * message (:term:`JSON object`): Body of the HMC notification,
            converted into a JSON object. `None` for notifications that
            have no content in their response body.

            The properties of the JSON object vary by notification type.

            For a description of the JSON properties, see the sub-sections
            for each notification type within section "Notification message
            formats" in chapter 4. "Asynchronous notification" in the
            :term:`HMC API` book.

        Returns:

            None

        Raises:

            :exc:`~zhmcclient.NotificationJMSError`: Received JMS error from
              the HMC.
            :exc:`~zhmcclient.NotificationParseError`: Cannot parse JMS message
              body as JSON.
            :exc:`~zhmcclient.NotificationConnectionError`: Issue with STOMP
              connection to HMC. Detecting lost connections requires that
              heartbeating is enabled in the stomp retry/timeout configuration.
            :exc:`~zhmcclient.NotificationSubscriptionError`: STOMP subscription
              failed.
        """

        # The timeout for getting an item from the handover queue. If the
        # timeout expires, a check for connection loss is performed and then
        # a new get from the handover queue. Since the connection loss
        # detection is based on heartbeat loss, it does not make sense to check
        # more often than the heartbeat receive cycle.
        ho_get_timeout = STOMP_MIN_CONNECTION_CHECK_TIME
        if self._rt_config:
            ho_get_timeout = max(
                ho_get_timeout, self._rt_config.heartbeat_receive_cycle + 1)

        self.connect()

        while True:

            # Get an item from the listener
            while True:

                if self._closed:
                    return

                try:
                    item = self._handover_queue.get(timeout=ho_get_timeout)
                except queue.Empty:
                    # This check detects a disconnect only when heartbeating is
                    # enabled in the stomp retry/timeout configuration.
                    if not self._conn.is_connected():
                        raise NotificationConnectionError(
                            "Lost STOMP connection to HMC")
                    continue
                break

            # Now we have an item from the listener
            if item.msgtype == 'message':
                try:
                    msg_obj = json.loads(item.message)
                except Exception as exc:
                    raise NotificationParseError(
                        "Cannot convert JMS message body to JSON: "
                        f"{exc.__class__.__name__}: {exc}",
                        item.message)
            elif item.msgtype == 'error':
                if 'message' in item.headers:
                    # Not sure that is always the case, but it was the case
                    # in issue #770.
                    details = f": {item.headers['message'].strip()}"
                else:
                    details = ""
                raise NotificationJMSError(
                    f"Received JMS error from HMC{details}",
                    item.headers, item.message)
            elif item.msgtype in ('disconnected', 'heartbeat_timeout'):
                # Get all contiguous such entries to handle them just once
                num_disc = 0
                num_hbto = 0
                if item.msgtype == 'disconnected':
                    num_disc += 1
                elif item.msgtype == 'heartbeat_timeout':
                    num_hbto += 1
                while True:
                    try:
                        item_ = self._handover_queue.get(timeout=ho_get_timeout)
                    except queue.Empty:
                        break
                    if item_.msgtype == 'disconnected':
                        num_disc += 1
                    elif item_.msgtype == 'heartbeat_timeout':
                        num_hbto += 1
                    else:
                        # Put the item back.
                        # TODO: Find way to put it to the front of the queue.
                        try:
                            self._handover_queue.put(item_)
                        except queue.Full:
                            JMS_LOGGER.error(
                                "Handover queue is full (put-back) - "
                                "dropping %s event", item_.msgtype)
                        break
                raise NotificationConnectionError(
                    f"STOMP received {num_hbto} heartbeat timeouts and "
                    f"{num_disc} disconnect messages")
            else:
                raise RuntimeError(
                    f"Invalid handover item: {item.msgtype}")

            yield item.headers, msg_obj

    @logged_api_call
    def close(self):
        """
        Close the receiver and cause its
        :meth:`~zhmcclient.NotificationReceiver.notifications` method
        to return.

        This also disconnects the STOMP session from the HMC, unsubscribing
        for any topics.

        Raises:

            stomp.exception.StompException: From stomp.Connection.disconnect()
        """
        self._closed = True
        self._conn.disconnect()


_NotificationItem = namedtuple(
    '_NotificationItem',
    [
        'msgtype',  # str: message type: 'message', 'error', 'disconnected',
                    #   'heartbeat_timeout'
        'headers',  # dict: STOMP headers (only for msgtype='message')
        'message',  # str: STOMP message in JSON (only for msgtype='message')
    ]
)


class _NotificationListener:
    """
    A notification listener class for use by the Python `stomp-py` package.

    This is an internal class that does not need to be accessed or created by
    the user. An object of this class is automatically created by the
    :class:`~zhmcclient.NotificationReceiver` class, for its notification
    topic.

    Note: In the stomp examples, this class inherits from
    stomp.ConnectionListener. However, since we want to import the stomp module
    in a lazy manner, we are not inheriting from that class, but repeat its
    methods here.
    """

    def __init__(self, handover_queue):
        """
        Parameters:

          handover_queue (Queue): Thread-safe queue between this listener
            object in the listener thread and the notification receiver object
            in the main thread. The queue items are _NotificationItem objects.
        """
        self._handover_queue = handover_queue

        # Lazy importing of the stomp module, because the import is slow in some
        # versions.
        # pylint: disable=import-outside-toplevel
        import stomp
        self._stomp = stomp

    def on_connecting(self, host_and_port):
        """
        Event method that gets called when the TCP/IP connection to the
        HMC has been established or re-established.

        Note that at this point, no connection has been established at the
        STOMP protocol level.

        Parameters:

            host_and_port (tuple(str, int)): Host name and port number to which
              the TCP/IP connection has been established.
        """
        pass

    def on_connected(self, *frame_args):
        # pylint: disable=no-self-use
        """
        Event method that gets called when a STOMP CONNECTED frame has been
        received from the HMC (after a TCP/IP connection has been established
        or re-established).

        Parameters:

          frame_args: The STOMP frame. For details, see get_headers_message().
        """
        headers, _ = get_headers_message(frame_args)
        heartbeat = headers.get('heart-beat', '0,0')
        can_send, want_receive = map(int, heartbeat.split(','))
        if can_send == 0:
            can_send_str = "cannot send heartbeats"
        else:
            can_send_str = f"can send heartbeats every {can_send} msec"
        if want_receive == 0:
            want_receive_str = "does not want to receive heartbeats"
        else:
            want_receive_str = \
                f"wants to receive heartbeats every {want_receive} msec"
        JMS_LOGGER.info(
            "Connected. The HMC %s and %s", can_send_str, want_receive_str)

    def on_disconnecting(self):
        """
        Event method that gets called before a STOMP DISCONNECT frame is sent
        to the HMC.
        """
        pass

        # Lazy importing of the stomp module, because the import is slow in some
        # versions.
        # pylint: disable=import-outside-toplevel
        import stomp
        self._stomp = stomp

    def on_disconnected(self):
        """
        Event method that gets called when the TCP/IP connection to the HMC
        has been lost.

        No messages should be sent via the connection until it has been
        re-established.
        """
        # We detect disconnects in the notifications() method by checking the
        # connection status, because this event method is called not when the
        # disconnect happens, but when the connection is re-established.
        # And it is called twice.
        pass

    def on_heartbeat_timeout(self):
        """
        Event method that gets called when a STOMP heartbeat has not been
        received from the HMC within the specified period.
        """
        # We detect heartbeat issues in the notifications() method by checking
        # the connection status, because this heartbeat event method is called
        # not when the hearbeat is missing, but when the connection is
        # re-established.
        pass

    def on_before_message(self, *frame_args):
        """
        Event method that gets called when a STOMP MESSAGE frame has been
        received from the HMC, but before the on_message() method is called.

        Parameters:

          frame_args: The STOMP frame. For details, see get_headers_message().
        """
        pass

    def on_message(self, *frame_args):
        """
        Event method that gets called when a STOMP MESSAGE frame has been
        received from the HMC (representing an HMC notification).

        Parameters:

          frame_args: The STOMP frame. For details, see get_headers_message().
        """
        headers, message = get_headers_message(frame_args)
        item = _NotificationItem(
            headers=headers, message=message, msgtype='message')
        try:
            self._handover_queue.put(item, timeout=5)
        except queue.Full:
            JMS_LOGGER.error(
                "Handover queue is full - dropping 'message' event")

    def on_receipt(self, *frame_args):
        """
        Event method that gets called when a STOMP RECEIPT frame has been
        received from the HMC.

        This is sent by the HMC if requested by the client using the 'receipt'
        header.

        Parameters:

          frame_args: The STOMP frame. For details, see get_headers_message().
        """
        pass

    def on_error(self, *frame_args):
        """
        Event method that gets called when a STOMP ERROR frame has been
        received from the HMC.

        This happens for example when the client registers for a non-existing
        HMC notification topic.

        Parameters:

          frame_args: The STOMP frame. For details, see get_headers_message().
        """
        headers, message = get_headers_message(frame_args)
        item = _NotificationItem(
            headers=headers, message=message, msgtype='error')
        try:
            self._handover_queue.put(item, timeout=5)
        except queue.Full:
            JMS_LOGGER.error(
                "Handover queue is full - dropping 'error' event")

    def on_send(self, *frame_args):
        # pylint: disable=no-self-use
        """
        Event method that gets called when the STOMP connection is in the
        process of sending a message.

        Parameters:

          frame_args: The STOMP frame. For details, see get_headers_message().
        """
        _, message = get_headers_message(frame_args)
        if message is None and DEBUG_HEARTBEATS:
            JMS_LOGGER.info("Sending STOMP heartbeat to HMC")

    def on_heartbeat(self):
        # pylint: disable=no-self-use
        """
        Event method that gets called when a STOMP heartbeat has been received.
        """
        if DEBUG_HEARTBEATS:
            JMS_LOGGER.info("Received STOMP heartbeat from HMC")

    def on_receiver_loop_completed(self, *frame_args):
        """
        Event method that gets called when the connection receiver_loop has
        finished.

        Parameters:

          frame_args: The STOMP frame. For details, see get_headers_message().
        """
        pass
