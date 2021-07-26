#!/usr/bin/env python
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
Resource updater for
:ref:`auto-updating of resources <Auto-updating of resources>`.
"""

import logging
import json
try:
    from json import JSONDecodeError as _JSONDecodeError
except ImportError:
    _JSONDecodeError = ValueError

from ._logging import logged_api_call
from ._constants import DEFAULT_STOMP_PORT, JMS_LOGGER_NAME

__all__ = ['ResourceUpdater']

JMS_LOGGER = logging.getLogger(JMS_LOGGER_NAME)


class ResourceUpdater(object):
    """
    A class that updates the properties of zhmcclient resource objects that are
    enabled for auto-updating.

    **Experimental:** This class is considered experimental at this point, and
    its API may change incompatibly as long as it is experimental.

    Note: The user should not create any objects of this class nor invoke any
    methods of this class, because the objects are created automatically
    when a :class:`~zhmcclient.Session` object is subscribed for
    auto-update (via its :meth:`~zhmcclient.Session.subscribe_auto_update`
    method).

    Creating an object of this class establishes a JMS session with the HMC and
    subscribes for the object notification topic of the session. This causes
    the HMC to emit status notifications, property notifications, and inventory
    notifications, which are processed by this class and cause the properties of
    zhmcclient resource objects to be updated that are registered to this class
    as a result of enabling auto-update for the resorce object
    (via their :meth:`~zhmcclient.BaseResource.enable_auto_update` method).

    Zhmcclient resource objects that are not enabled for auto-updating remain
    unchanged.
    """

    def __init__(self, session):
        """
        Parameters:

          session (:class:`~zhmcclient.Session`): Session for which the
            resource updater should do its work. This defines the HMC host
            and credentials that are used to establish the JMS session with
            the HMC.
        """

        # Registered resource objects, as:
        #   dict(key: uri, value: dict(key: id, value: object))
        self._registered_objects = {}

        # Subscription ID. We use some value that allows to identify on the
        # HMC that this is the zhmcclient, but otherwise we are not using
        # this value ourselves.
        self._sub_id = 'zhmcclient.%s' % id(self)

        # Lazy importing for stomp, because it is so slow (ca. 5 sec)
        if 'Stomp_Connection' not in globals():
            # pylint: disable=import-outside-toplevel
            from stomp import Connection as Stomp_Connection

        self._conn = Stomp_Connection(
            [(session.host, DEFAULT_STOMP_PORT)], use_ssl="SSL")
        listener = _UpdateListener(self, session)
        self._conn.set_listener('', listener)
        # pylint: disable=protected-access
        self._conn.connect(session.userid, session._password, wait=True)

        dest = "/topic/" + session.object_topic
        self._conn.subscribe(destination=dest, id=self._sub_id, ack='auto')

        JMS_LOGGER.info(
            "JMS session for object notification topic '%s' has been "
            "established", session.object_topic)

    @logged_api_call
    def close(self):
        """
        Disconnect and close the JMS session with the HMC.

        This implicitly unsubscribes from the object notification topic this
        updater was created for.
        """
        self._conn.disconnect()

    def register_object(self, resource_obj):
        """
        Register a resource object to this resource updater.

        If this resource object (by id) is already registered, nothing is done.
        """
        res_uri = resource_obj.uri
        res_id = id(resource_obj)
        if res_uri not in self._registered_objects:
            self._registered_objects[res_uri] = {}
        id_dict = self._registered_objects[res_uri]
        if res_id not in id_dict:
            id_dict[res_id] = resource_obj

    def unregister_object(self, resource_obj):
        """
        Unregister a resource object from this resource updater.

        If this resource object (by id) is already unregistered, nothing is
        done.
        """
        res_uri = resource_obj.uri
        res_id = id(resource_obj)
        if res_uri in self._registered_objects:
            id_dict = self._registered_objects[res_uri]
            if res_id in id_dict:
                del id_dict[res_id]
            if not id_dict:
                del self._registered_objects[res_uri]

    def registered_objects(self, resource_uri):
        """
        Generator that yields the resource objects for the specified URI.
        """
        if resource_uri in self._registered_objects:
            id_dict = self._registered_objects[resource_uri]
            for res_obj in id_dict.values():
                yield res_obj

    def has_objects(self):
        """
        Return boolean indicating whether there are any resource objects
        registered.
        """
        return bool(self._registered_objects)


class _UpdateListener(object):
    # pylint: disable=too-few-public-methods
    """
    A notification listener class for use by the Python `stomp` package.

    This is an internal class that does not need to be accessed or created by
    the user. An object of this class is automatically created by the
    :class:`~zhmcclient.ResourceUpdater` class, for its notification
    topic.

    Note: In the stomp examples, this class inherits from
    stomp.ConnectionListener. However, since that class defines only empty
    methods and since we want to import the stomp module in a lazy manner,
    we are not using that class, and stomp does not require us to.
    """

    def __init__(self, updater, session):
        self._updater = updater
        self._session = session

    def on_message(self, headers, message):
        """
        Event method that gets called when this listener has received a JMS
        message (representing an HMC notification).

        Parameters:

          headers (dict): JMS message headers, see HMC API book.

          message (string): JMS message body as a string, which contains a
            serialized JSON object, see HMC API book.
        """

        try:
            msg_obj = json.loads(message)
        except _JSONDecodeError:
            JMS_LOGGER.error(
                "JMS message for object notification topic '%s' "
                "has a non-JSON message body (ignored): %r",
                self._session.object_topic, message)
            return

        try:
            uri = headers['object-uri']
        except KeyError:
            try:
                uri = headers['element-uri']
            except KeyError:
                JMS_LOGGER.error(
                    "JMS message for object notification topic '%s' "
                    "has no URI field in its headers (ignored): %r",
                    self._session.object_topic, headers)
                return

        noti_type = headers['notification-type']
        if noti_type == 'property-change':
            new_props = {}
            for cr in msg_obj['change-reports']:
                new_props[cr['property-name']] = cr['new-value']
            JMS_LOGGER.debug(
                "JMS message for property change notification for topic '%s' "
                "for resource %s with properties: %r",
                self._session.object_topic, uri, new_props)
            for obj in self._updater.registered_objects(uri):
                if obj.auto_update_enabled():
                    obj.update_properties_local(new_props)
        elif noti_type == 'status-change':
            new_props = {}
            for cr in msg_obj['change-reports']:
                new_props['status'] = cr['new-status']
                new_props['additional-status'] = cr['new-additional-status']
                new_props['has-unacceptable-status'] = \
                    cr['has-unacceptable-status']
            JMS_LOGGER.debug(
                "JMS message for status change notification for topic '%s' "
                "for resource %s with properties: %r",
                self._session.object_topic, uri, new_props)
            for obj in self._updater.registered_objects(uri):
                if obj.auto_update_enabled():
                    obj.update_properties_local(new_props)
        else:
            JMS_LOGGER.warning(
                "JMS message for notification of type %s for topic '%s' "
                "for resource %s is ignored",
                noti_type, self._session.object_topic, uri)

    def on_error(self, headers, message):
        # pylint: disable=unused-argument
        """
        Event method that gets called when this listener has received a JMS
        error. This happens for example when the client registers for a
        non-existing topic.

        Parameters:

          headers (dict): JMS message headers.

          message (string): JMS message body as a string, which contains a
            serialized JSON object.
        """
        JMS_LOGGER.error(
            "JMS error message received for object notification topic '%s' "
            "(ignored): %s",
            self._session.object_topic, message)

    def on_disconnected(self):
        """
        Event method that gets called when the JMS session has been
        disconnected.
        """
        JMS_LOGGER.info(
            "JMS session for object notification topic '%s' has been "
            "disconnected",
            self._session.object_topic)
