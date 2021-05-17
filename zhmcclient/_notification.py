#!/usr/bin/env python
# Copyright 2017 IBM Corp. All Rights Reserved.
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

    receiver = zhmcclient.NotificationReceiver(topic, hmc, userid, password)

    try:
        for headers, message in receiver.notifications():
            print("HMC notification #%s:" % headers['session-sequence-nr'])
            os_msg_list = message['os-messages']
            for os_msg in os_msg_list:
                msg_txt = os_msg['message-text'].strip('\\n')
                msg_id = os_msg['message-id']
                print("OS message #%s:\\n%s" % (msg_id, msg_txt))
    except zhmcclient.NotificationError as exc:
        print("Notification Error: {}".format(exc))
    except KeyboardInterrupt:
        print("Keyboard Interrupt - Leaving notification receiver loop...")
    finally:
        print("Closing notification receiver...")
        receiver.close()

When running this example code in one terminal, and stopping or starting
the partition in another terminal, one can monitor the shutdown or boot
messages issued by the operating system. The following commands use the
``zhmc`` CLI provided in the :term:`zhmccli project` to do that:

.. code-block:: text

    $ zhmc partition stop {cpc-name} {partition-name}
    $ zhmc partition start {cpc-name} {partition-name}
"""

import threading
import json

from ._logging import logged_api_call
from ._constants import DEFAULT_STOMP_PORT
from ._exceptions import NotificationJMSError, NotificationParseError

__all__ = ['NotificationReceiver']


class NotificationReceiver(object):
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
    """

    def __init__(self, topic_names, host, userid, password,
                 port=DEFAULT_STOMP_PORT):
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
            Userid of the HMC user to be used.
            Must not be `None`.

          password (:term:`string`):
            Password of the HMC user to be used.
            Must not be `None`.

          port (:term:`integer`):
            STOMP TCP port. Defaults to
            :attr:`~zhmcclient._constants.DEFAULT_STOMP_PORT`.
        """
        if not isinstance(topic_names, (list, tuple)):
            topic_names = [topic_names]
        self._topic_names = topic_names
        self._host = host
        self._port = port
        self._userid = userid
        self._password = password

        # Wait timeout to honor keyboard interrupts after this time:
        self._wait_timeout = 10.0  # seconds

        # Subscription ID. We use some value that allows to identify on the
        # HMC that this is the zhmcclient, but otherwise we are not using
        # this value ourselves.
        self._sub_id = 'zhmcclient.%s' % id(self)

        # Sync variables for thread-safe handover between listener thread and
        # receiver thread:
        self._handover_dict = {}
        self._handover_cond = threading.Condition()

        # Lazy importing for stomp, because it is so slow (ca. 5 sec)
        if 'Stomp_Connection' not in globals():
            # pylint: disable=import-outside-toplevel
            from stomp import Connection as Stomp_Connection

        self._conn = Stomp_Connection(
            [(self._host, self._port)], use_ssl="SSL")
        listener = _NotificationListener(self._handover_dict,
                                         self._handover_cond)
        self._conn.set_listener('', listener)
        self._conn.connect(self._userid, self._password, wait=True)

        for topic_name in self._topic_names:
            dest = "/topic/" + topic_name
            self._conn.subscribe(destination=dest, id=self._sub_id, ack='auto')

    @logged_api_call
    def notifications(self):
        """
        Generator method that yields all HMC notifications (= JMS messages)
        received by this notification receiver.

        Example::

            desired_topic_types = ('security-notification',
                                   'audit-notification')
            topics = session.get_notification_topics()
            topic_names = [t['topic-name']
                           for t in topics
                           if t['topic-type'] in desired_topic_types]

            receiver = zhmcclient.NotificationReceiver(
                topic_names, hmc, userid, password)

            for headers, message in receiver.notifications():
                . . . # processing of topic-specific message format

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
            converted into a JSON object.

            The properties of the JSON object vary by notification type.

            For a description of the JSON properties, see the sub-sections
            for each notification type within section "Notification message
            formats" in chapter 4. "Asynchronous notification" in the
            :term:`HMC API` book.

        Raises:
            :exc:`~zhmcclient.NotificationJMSError`: Received JMS error from
              the HMC.
            :exc:`~zhmcclient.NotificationParseError`: Cannot parse JMS message
              body as JSON.
        """

        while True:
            with self._handover_cond:  # serialize body via lock

                # Wait until MessageListener has a new notification
                while len(self._handover_dict) == 0:
                    self._handover_cond.wait(self._wait_timeout)

                if self._handover_dict['headers'] is None:
                    return

                # Process the notification
                headers = self._handover_dict['headers']
                message = self._handover_dict['message']
                msgtype = self._handover_dict['msgtype']

                if msgtype == 'error':
                    if 'message' in headers:
                        # Not sure that is always the case, but it was the case
                        # in issue #770.
                        details = ": {}".format(headers['message'].strip())
                    else:
                        details = ""
                    raise NotificationJMSError(
                        "Received JMS error from HMC{}".format(details),
                        headers, message)

                try:
                    msg_obj = json.loads(message)
                except Exception as exc:
                    raise NotificationParseError(
                        "Cannot convert JMS message body to JSON: {}: {}".
                        format(exc.__class__.__name__, exc),
                        message)

                yield headers, msg_obj

                del self._handover_dict['headers']
                del self._handover_dict['message']
                del self._handover_dict['msgtype']

                # Indicate to MessageListener that we are ready for next
                # notification
                self._handover_cond.notifyAll()

    @logged_api_call
    def close(self):
        """
        Disconnect and close the JMS session with the HMC.

        This implicitly unsubscribes from the notification topic this receiver
        was created for, and causes the
        :meth:`~zhmcclient.NotificationReceiver.notifications` method to
        stop its iterations.
        """
        self._conn.disconnect()


class _NotificationListener(object):
    """
    A notification listener class for use by the Python `stomp` package.

    This is an internal class that does not need to be accessed or created by
    the user. An object of this class is automatically created by the
    :class:`~zhmcclient.NotificationReceiver` class, for its notification
    topic.

    Note: In the stomp examples, this class inherits from
    stomp.ConnectionListener. However, since that class defines only empty
    methods and since we want to import the stomp module in a lazy manner,
    we are not using that class, and stomp does not require us to.
    """

    def __init__(self, handover_dict, handover_cond):
        """
        Parameters:

          handover_dict (dict): Dictionary for handing over the notification
            header and message from this listener thread to the receiver
            thread. Must initially be an empty dictionary.

          handover_cond (threading.Condition): Condition object for handing
            over the notification from this listener thread to the receiver
            thread. Must initially be a new threading.Condition object.
        """

        # Sync variables for thread-safe handover between listener thread and
        # receiver thread:
        self._handover_dict = handover_dict  # keys: headers, message
        self._handover_cond = handover_cond

        # Wait timeout to honor keyboard interrupts after this time:
        self._wait_timeout = 10.0  # seconds

    def on_disconnected(self):
        """
        Event method that gets called when the JMS session has been
        disconnected.

        It hands over a termination notification (headers and message are
        None).
        """

        with self._handover_cond:  # serialize body via lock

            # Wait until receiver has processed the previous notification
            while len(self._handover_dict) > 0:
                self._handover_cond.wait(self._wait_timeout)

            # Indicate to receiver that there is a termination notification
            self._handover_dict['headers'] = None  # terminate receiver
            self._handover_dict['message'] = None
            self._handover_dict['msgtype'] = 'disconnected'
            self._handover_cond.notifyAll()

    def on_error(self, headers, message):
        """
        Event method that gets called when this listener has received a JMS
        error. This happens for example when the client registers for a
        non-existing topic.

        Parameters:

          headers (dict): JMS message headers, as described for `headers` tuple
            item returned by the
            :meth:`~zhmcclient.NotificationReceiver.notifications` method.

          message (string): JMS message body as a string, which contains a
            serialized JSON object. The JSON object is described in the
            `message` tuple item returned by the
            :meth:`~zhmcclient.NotificationReceiver.notifications` method).
        """

        with self._handover_cond:  # serialize body via lock

            # Wait until receiver has processed the previous notification
            while len(self._handover_dict) > 0:
                self._handover_cond.wait(self._wait_timeout)

            # Indicate to receiver that there is a new notification
            self._handover_dict['headers'] = headers
            self._handover_dict['message'] = message
            self._handover_dict['msgtype'] = 'error'
            self._handover_cond.notifyAll()

    def on_message(self, headers, message):
        """
        Event method that gets called when this listener has received a JMS
        message (representing an HMC notification).

        Parameters:

          headers (dict): JMS message headers, as described for `headers` tuple
            item returned by the
            :meth:`~zhmcclient.NotificationReceiver.notifications` method.

          message (string): JMS message body as a string, which contains a
            serialized JSON object. The JSON object is described in the
            `message` tuple item returned by the
            :meth:`~zhmcclient.NotificationReceiver.notifications` method).
        """

        with self._handover_cond:  # serialize body via lock

            # Wait until receiver has processed the previous notification
            while len(self._handover_dict) > 0:
                self._handover_cond.wait(self._wait_timeout)

            # Indicate to receiver that there is a new notification
            self._handover_dict['headers'] = headers
            self._handover_dict['message'] = message
            self._handover_dict['msgtype'] = 'message'
            self._handover_cond.notifyAll()
