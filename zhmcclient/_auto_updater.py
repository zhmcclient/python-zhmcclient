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
Support for the :ref:`auto-updating` of Python zhmcclient resource and manager
objects based on HMC notifications.
"""


import logging
import json
from json import JSONDecodeError
import ssl

from ._constants import DEFAULT_STOMP_PORT, JMS_LOGGER_NAME, \
    DEFAULT_STOMP_CONNECT_TIMEOUT, \
    DEFAULT_STOMP_CONNECT_RETRIES, DEFAULT_STOMP_RECONNECT_SLEEP_INITIAL, \
    DEFAULT_STOMP_RECONNECT_SLEEP_INCREASE, DEFAULT_STOMP_RECONNECT_SLEEP_MAX, \
    DEFAULT_STOMP_RECONNECT_SLEEP_JITTER, DEFAULT_STOMP_KEEPALIVE, \
    DEFAULT_STOMP_HEARTBEAT_SEND_CYCLE, DEFAULT_STOMP_HEARTBEAT_RECEIVE_CYCLE, \
    DEFAULT_STOMP_HEARTBEAT_RECEIVE_CHECK
from ._utils import RC_CPC, RC_CHILDREN_CLIENT, RC_CHILDREN_CPC, \
    RC_CHILDREN_CONSOLE, get_stomp_rt_kwargs, get_headers_message
from ._client import Client
from ._manager import BaseManager
from ._resource import BaseResource
from ._notification import StompRetryTimeoutConfig

__all__ = ['AutoUpdater']

JMS_LOGGER = logging.getLogger(JMS_LOGGER_NAME)


class AutoUpdater:
    """
    A class that automatically updates

    * the properties of zhmcclient resource objects that are enabled for
      auto-updating
    * the list of zhmcclient resource objects in manager objects that are
      enabled for auto-updating

    based on respective notifications from the HMC.

    **Experimental:** This class is considered experimental at this point, and
    its API may change incompatibly as long as it is experimental.

    Note: The user should not create any objects of this class nor invoke any
    methods of this class, because the objects are created automatically
    when a :class:`~zhmcclient.Session` object is subscribed for
    auto-updating via its :meth:`~zhmcclient.Session.subscribe_auto_update`
    method.

    Creating an object of this class performs a logon to the HMC to retrieve
    the notification topics, and then establishes a JMS session with the HMC and
    subscribes for the object notification topic of the session. This causes
    the HMC to emit status notifications, property notifications, and inventory
    notifications, which are processed by this class and cause the updates
    to happen.

    Resource objects can be enabled for auto-updating via their
    :meth:`~zhmcclient.BaseResource.enable_auto_update` method.

    Manager objects can be enabled for auto-updating via their
    :meth:`~zhmcclient.BaseManager.enable_auto_update` method.

    Zhmcclient resource objects or manager objects that are not enabled for
    auto-updating remain unchanged.

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

    def __init__(self, session, stomp_rt_config=None):
        """
        Parameters:

          session (:class:`~zhmcclient.Session`): Session for which the
            auto updater should do its work. This defines the HMC host
            and credentials that are used to establish the JMS session with
            the HMC. The session may or may not be logged on.

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

        self._session = session
        self._rt_config = stomp_rt_config

        # STOMP connection
        self._conn = None

        # Registered resource and manager objects, as:
        #   dict(key: uri, value: dict(key: id, value: object))
        self._registered_objects = {}

        # Subscription ID. We use some value that allows to identify on the
        # HMC that this is the zhmcclient, but otherwise we are not using
        # this value ourselves.
        self._sub_id = f'zhmcclient.{id(self)}'

        # Lazy importing of the stomp module, because the import is slow in some
        # versions.
        # pylint: disable=import-outside-toplevel
        import stomp
        self._stomp = stomp

    def open(self):
        """
        Open the JMS session with the HMC.

        This creates a STOMP connection with the actual HMC of the session and
        subscribes to the object notification topic.

        If the session does not yet have an object notification topic set,
        the session is logged on.
        """
        if not self._session.object_topic:
            self._session.logon()  # This sets actual_host

        rt_kwargs = get_stomp_rt_kwargs(self._rt_config)
        self._conn = self._stomp.Connection(
            [(self._session.actual_host, DEFAULT_STOMP_PORT)], **rt_kwargs)
        set_kwargs = dict()
        set_kwargs['ssl_version'] = ssl.PROTOCOL_TLS_CLIENT
        self._conn.set_ssl(
            for_hosts=[(self._session.actual_host, DEFAULT_STOMP_PORT)],
            **set_kwargs)

        listener = _UpdateListener(self, self._session)
        self._conn.set_listener('', listener)
        # pylint: disable=protected-access
        self._conn.connect(self._session.userid, self._session._password,
                           wait=True)

        dest = "/topic/" + self._session.object_topic
        self._conn.subscribe(destination=dest, id=self._sub_id, ack='auto')

        listener.init_cpcs()

        JMS_LOGGER.info(
            "JMS session for object notification topic '%s' has been "
            "established", self._session.object_topic)

    def close(self):
        """
        Close the JMS session with the HMC.

        This implicitly unsubscribes from the object notification topic this
        auto updater was created for.
        """
        self._conn.disconnect()
        self._conn = None

        JMS_LOGGER.info(
            "JMS session for object notification topic '%s' has been "
            "disconnected", self._session.object_topic)

    def is_open(self):
        """
        Return whether the JMS session with the HMC is open.
        """
        return self._conn is not None

    def register_object(self, obj):
        """
        Register a resource or manager object to this auto updater.

        If this object (identified by its Python id) is already registered,
        nothing is done.
        """
        assert isinstance(obj, (BaseResource, BaseManager))
        uri = obj.uri
        res_id = id(obj)
        if uri not in self._registered_objects:
            self._registered_objects[uri] = {}
        id_dict = self._registered_objects[uri]
        if res_id not in id_dict:
            id_dict[res_id] = obj

    def unregister_object(self, obj):
        """
        Unregister a resource or manager object from this auto updater.

        If this object (identified by its Python id) is already unregistered,
        nothing is done.
        """
        assert isinstance(obj, (BaseResource, BaseManager))
        uri = obj.uri
        res_id = id(obj)
        if uri in self._registered_objects:
            id_dict = self._registered_objects[uri]
            if res_id in id_dict:
                del id_dict[res_id]
            if not id_dict:
                del self._registered_objects[uri]

    def registered_objects(self, uri):
        """
        Generator that yields the resource or manager objects for the specified
        URI.
        """
        if uri in self._registered_objects:
            id_dict = self._registered_objects[uri]
            # pylint: disable=use-yield-from
            yield from id_dict.values()

    def has_objects(self):
        """
        Return boolean indicating whether there are any resource objects
        registered.
        """
        return bool(self._registered_objects)


class _UpdateListener:
    # pylint: disable=too-few-public-methods
    """
    A notification listener class for use by the Python `stomp` package.

    This is an internal class that does not need to be accessed or created by
    the user. An object of this class is automatically created by the
    :class:`~zhmcclient.AutoUpdater` class, for its notification
    topic.

    Note: In the stomp examples, this class inherits from
    stomp.ConnectionListener. However, since that class defines only empty
    methods and since we want to import the stomp module in a lazy manner,
    we are not using that class, and stomp does not require us to.
    """

    def __init__(self, updater, session):
        self._updater = updater
        self._session = session
        self._client = None

        # Lazy importing of the stomp module, because the import is slow in some
        # versions.
        # pylint: disable=import-outside-toplevel
        import stomp
        self._stomp = stomp

    def init_cpcs(self):
        """
        Initialize the CPC manager, for later use when receiving inventory
        notifications for child objects of CPCs.
        """
        if self._client is None:
            self._client = Client(self._session)
            self._client.cpcs.enable_auto_update()

    def _manager_uri_from_notification(self, headers):
        """
        Return the manager URI from the headers of an inventory notification
        and the resource URI.
        """

        try:
            res_class = headers['class']
        except KeyError:
            JMS_LOGGER.error(
                "JMS message for object notification topic '%s' "
                "has no 'class' field in "
                "its headers (ignored): %r",
                self._session.object_topic, headers)
            return None

        if 'element-uri' in headers:
            # The notification is about an element resource. In that case,
            # 'object-uri' identifies the containing (=parent) object resource.

            try:
                parent_uris = [headers['object-uri']]
            except KeyError:
                JMS_LOGGER.error(
                    "JMS message for object notification topic '%s' "
                    "has an 'element-uri' field but no 'object-uri' field in "
                    "its headers (ignored): %r",
                    self._session.object_topic, headers)
                return None

        else:
            # The notification is about an object (non-element) resource.
            # The parent object's URI is not specified in the notification
            # in this case, but there are not too many parent resources that
            # have object resources as children, so we try to find it.

            # In the removal case, it is not important what the parent
            # resource is. We simply return all possible parent resources
            # and the caller will look them all up to find the resource to
            # be removed.
            # In the addition case, it is important to find the parent object
            # because only the parent object has the right manager object into
            # which the new resource is added.

            if res_class == RC_CPC:
                # Could be a managed or unmanaged CPC
                parent_uris = ['/api/console', '/']
            elif res_class in RC_CHILDREN_CLIENT:
                # RC_CHILDREN_CLIENT includes RC_CPC, but that is already
                # processed
                parent_uris = ['/']
            elif res_class in RC_CHILDREN_CPC:
                cpcs = self._client.cpcs.list_resources_local()
                parent_uris = [cpc.uri for cpc in cpcs]
            elif res_class in RC_CHILDREN_CONSOLE:
                # RC_CHILDREN_CONSOLE includes RC_CPC, but that is already
                # processed
                parent_uris = ['/api/console']
            else:
                JMS_LOGGER.error(
                    "JMS message for object notification topic '%s' "
                    "has an unknown 'class' field in "
                    "its headers (ignored): %r",
                    self._session.object_topic, headers)
                return None

        mgr_uris = [f'{_uri}#{res_class}' for _uri in parent_uris]
        return mgr_uris

    def _get_uri(self, headers):
        """
        Return the uri of the object or element resource o which the
        notification applies.

        If the notification is about an element resource, element-uri is
        present and is the URI of that resource, and object-uri is the URI of
        the parent (containing) object.

        If the notification is about an object (=non-element) resource,
        element-uri is not present, and object-uri is the URI of that
        resource.
        """
        if 'element-uri' in headers:
            # The notification is about an element resource
            uri = headers['element-uri']
        else:
            # The notification is about an object (non-element) resource
            try:
                uri = headers['object-uri']
            except KeyError:
                JMS_LOGGER.error(
                    "JMS message for object notification topic '%s' "
                    "has no 'element-uri' field and no 'object-uri' field in "
                    "its headers (ignored): %r",
                    self._session.object_topic, headers)
                return None
        return uri

    def on_message(self, *frame_args):
        """
        Event method that gets called when this listener has received a JMS
        message (representing an HMC notification).

        Parameters:

          frame_args: The STOMP frame. For details, see get_headers_message().
        """
        headers, message = get_headers_message(frame_args)

        noti_type = headers['notification-type']
        if noti_type == 'property-change':
            try:
                msg_obj = json.loads(message)
            except JSONDecodeError:
                JMS_LOGGER.error(
                    "JMS message for object notification topic '%s' "
                    "has a non-JSON message body (ignored): %r",
                    self._session.object_topic, message)
                return
            uri = self._get_uri(headers)
            if uri is None:
                # Some error - details are already logged
                return
            JMS_LOGGER.debug(
                "JMS message for property change notification for topic '%s' "
                "for resource %s with change reports: %r",
                self._session.object_topic, uri, msg_obj['change-reports'])
            # Build the latest values from all change records. They are ordered
            # old to new.
            new_props = {}
            for cr in msg_obj['change-reports']:
                new_props[cr['property-name']] = cr['new-value']
            for obj in self._updater.registered_objects(uri):
                if obj.auto_update_enabled():
                    obj.update_properties_local(new_props)
        elif noti_type == 'status-change':
            try:
                msg_obj = json.loads(message)
            except JSONDecodeError:
                JMS_LOGGER.error(
                    "JMS message for object notification topic '%s' "
                    "has a non-JSON message body (ignored): %r",
                    self._session.object_topic, message)
                return
            uri = self._get_uri(headers)
            if uri is None:
                # Some error - details are already logged
                return
            JMS_LOGGER.debug(
                "JMS message for status change notification for topic '%s' "
                "for resource %s with change reports: %r",
                self._session.object_topic, uri, msg_obj['change-reports'])
            # Build the latest values from all change records. They are ordered
            # old to new.
            new_props = {}
            for cr in msg_obj['change-reports']:
                if 'new-status' in cr:
                    new_props['status'] = cr['new-status']
                if 'new-additional-status' in cr:
                    new_props['additional-status'] = cr['new-additional-status']
                if 'has-unacceptable-status' in cr:
                    new_props['has-unacceptable-status'] = \
                        cr['has-unacceptable-status']
            for obj in self._updater.registered_objects(uri):
                if obj.auto_update_enabled():
                    obj.update_properties_local(new_props)
        elif noti_type == 'inventory-change':
            uri = self._get_uri(headers)
            if uri is None:
                # Some error - details are already logged
                return
            action = headers['action']
            JMS_LOGGER.debug(
                "JMS message for inventory change notification for topic '%s' "
                "for resource %s with action: %r",
                self._session.object_topic, uri, action)
            if action == 'add':
                mgr_uris = self._manager_uri_from_notification(headers)
                if mgr_uris is None:
                    # Some error - details are already logged
                    return
                for mgr_uri in mgr_uris:
                    for mgr_obj in self._updater.registered_objects(mgr_uri):
                        if mgr_obj.auto_update_enabled():
                            mgr_obj.auto_update_trigger_pull()
            elif action == 'remove':
                mgr_uris = self._manager_uri_from_notification(headers)
                if mgr_uris is None:
                    # Some error - details are already logged
                    return
                for mgr_uri in mgr_uris:
                    for mgr_obj in self._updater.registered_objects(mgr_uri):
                        if mgr_obj.auto_update_enabled():
                            mgr_obj.remove_resource_local(uri)
                for obj in self._updater.registered_objects(uri):
                    if obj.auto_update_enabled():
                        obj.cease_existence_local()
            else:
                JMS_LOGGER.error(
                    "JMS message for inventory change notification specifies "
                    "unknown action %r (ignored)",
                    action)
        else:
            JMS_LOGGER.warning(
                "JMS message for notification of type %s for topic '%s' "
                "is ignored",
                noti_type, self._session.object_topic)

    def on_error(self, *frame_args):
        """
        Event method that gets called when this listener has received a JMS
        error. This happens for example when the client registers for a
        non-existing topic.

        Parameters:

          frame_args: The STOMP frame. For details, see get_headers_message().
        """
        _, message = get_headers_message(frame_args)
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
