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
Base definitions for resource classes.

Resource objects represent the real manageable resources in the systems managed
by the HMC.
"""

import time
import threading
from collections import OrderedDict
# import contextlib
from immutable_views import DictView

from ._logging import logged_api_call
from ._utils import repr_dict, repr_timestamp, repr_obj_id
from ._exceptions import CeasedExistence, HTTPError

__all__ = ['BaseResource']


class BaseResource:
    """
    Abstract base class for resource classes (e.g. :class:`~zhmcclient.Cpc`)
    representing manageable resources.

    It defines the interface for the derived resource classes, and implements
    methods that have a common implementation for the derived resource classes.

    Objects of derived resource classes are representations of the actual
    manageable resources in the HMC or in systems managed by the HMC.

    Objects of derived resource classes should not be created by users of this
    package by simply instantiating the derived resource classes. Instead, such
    objects are created by this package and are returned to the user as a
    result of methods such as :meth:`~zhmcclient.BaseManager.find` or
    :meth:`~zhmcclient.BaseManager.list`. For this reason, the `__init__()`
    method of this class and of its derived resource classes are considered
    internal interfaces and their parameters are not documented and may change
    incompatibly.
    """

    def __init__(self, manager, uri, name, properties):
        # This method intentionally has no docstring, because it is internal.
        #
        # Parameters:
        #   manager (subclass of :class:`~zhmcclient.BaseManager`):
        #     Manager object for this resource object (and for all resource
        #     objects of the same type in the scope of that manager).
        #     Must not be `None`.
        #   uri (string):
        #     Canonical URI path of the resource.
        #     Must not be `None`.
        #   name (string):
        #     Name of the resource.
        #     May be `None`.
        #   properties (dict):
        #     Properties for this resource object. May be `None` or empty.
        #     * Key: Name of the property.
        #     * Value: Value of the property.

        # We want to surface precondition violations as early as possible,
        # so we test those that are not surfaced through the init code:
        assert manager is not None
        assert uri is not None

        self._manager = manager
        self._uri = uri

        self._properties = dict(properties) if properties else {}
        if name is not None:
            name_prop = self._manager._name_prop
            if name_prop in self._properties:
                assert self._properties[name_prop] == name
            else:
                self._properties[name_prop] = name
        uri_prop = self._manager._uri_prop
        if uri_prop in self._properties:
            assert self._properties[uri_prop] == uri
        else:
            self._properties[uri_prop] = uri

        self._properties_timestamp = int(time.time())
        self._full_properties = False
        # self._property_lock = contextlib.nullcontext()  # test need to lock
        self._property_lock = threading.RLock()
        self._auto_update = False
        self._ceased_existence = False

    @property
    def properties(self):
        """
        :class:`iv:immutable_views.DictView`: The properties of this resource
        that are currently present in this Python object, as a dictionary.

          * Key: Name of the property.
          * Value: Value of the property.

        The returned :class:`iv:immutable_views.DictView` object is an immutable
        dictionary view that behaves like a standard Python :class:`dict`
        except that it prevents any modifications to the dictionary.

        See the respective 'Data model' sections in the :term:`HMC API` book
        for a description of the resources along with their properties.

        The dictionary contains either the full set of resource properties,
        or a subset thereof, or can be empty in some cases.

        Because the presence of properties in this dictionary depends on the
        situation, the purpose of this dictionary is only for iterating
        through the resource properties that are currently present.

        Specific resource properties should be accessed via:

        * The resource name, via the :attr:`~zhmcclient.BaseResource.name`
          attribute.
        * The resource URI, via the :attr:`~zhmcclient.BaseResource.uri`
          attribute.
        * Any resource property, via the
          :meth:`~zhmcclient.BaseResource.get_property` or
          :meth:`~zhmcclient.BaseResource.prop` methods.

        Updates to property values can be done via the ``update_properties()``
        method of the resource class. Which properties can be updated
        is indicated with the 'w' qualifier in the data model of the resource
        in the :term:`HMC API` book.

        If :ref:`auto-updating` is enabled for the
        resource object and the session is enabled for auto-updating as well,
        the property values in the returned :class:`iv:immutable_views.DictView`
        object will change as they change on the HMC.

        If the resource object on the HMC no longer exists, the properties
        show the values that were last updated from the HMC when the object
        still existed.
        """
        return DictView(self._properties)

    @property
    def uri(self):
        """
        string: The canonical URI path of the resource. Will not be `None`.

        Example: ``/api/cpcs/12345``
        """
        return self._uri

    @property
    def name(self):
        """
        string: The name of the resource. Will not be `None`.

        The resource name is unique across its sibling resources of the same
        type and with the same parent resource.

        Accessing this property will cause the properties of this resource
        object to be updated from the HMC, if it does not yet contain the
        property for the resource name.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.CeasedExistence`: Only when not yet available
            locally.
        """
        # pylint: disable=protected-access
        # We avoid storing the name in an instance variable, because it can
        # be modified via update_properties().
        name_prop = self.manager._name_prop
        try:
            with self._property_lock:
                return self._properties[name_prop]
        except KeyError:
            self.pull_full_properties()
            with self._property_lock:
                return self._properties[name_prop]

    @property
    def manager(self):
        """
        Subclass of :class:`~zhmcclient.BaseManager`:
          Manager object for this resource (and for all resources of the same
          type in the scope of that manager). Will not be `None`.
        """
        return self._manager

    @property
    def full_properties(self):
        """
        A boolean indicating whether or not the resource properties in this
        object are the full set of resource properties.

        Note that listing resources and creating new resources produces objects
        that have less than the full set of properties.
        """
        return self._full_properties

    @property
    def properties_timestamp(self):
        """
        The point in time of the last update of the resource properties cached
        in this object, as Unix time (an integer that is the number of seconds
        since the Unix epoch).
        """
        return self._properties_timestamp

    @property
    def ceased_existence(self):
        """
        bool: Indicates that the corresponding object on the HMC no longer
        exists, if auto-update is enabled for the resource. Always `False`, if
        auto-update is not enabled for the resource.
        """
        return self._ceased_existence

    @logged_api_call
    def pull_full_properties(self):
        """
        Retrieve the full set of resource properties from the HMC and cache
        them in this Python object.

        If the resource no longer exists on the HMC,
        :exc:`~zhmcclient.CeasedExistence` will be raised.

        This method serializes with other methods that access or change
        resource properties on the same Python object.

        Authorization requirements:

        * Object-access permission to this resource.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.CeasedExistence`
        """
        with self._property_lock:
            if self._ceased_existence:
                raise CeasedExistence(self._uri)

        try:
            full_properties = self.manager.session.get(self._uri, resource=self)
        except HTTPError as exc:
            if exc.http_status == 404 and exc.reason == 1:
                # The resource no longer exists
                self.cease_existence_local()
                raise CeasedExistence(self._uri)
            raise

        with self._property_lock:
            self._properties.update(full_properties)
            self._properties_timestamp = int(time.time())
            self._full_properties = True

    @logged_api_call
    def pull_properties(self, properties):
        """
        Retrieve the specified set of resource properties from the HMC and
        cache them in this Python object.

        If no properties are specified, the method does nothing.

        The values of other properties that may already be cached in this
        Python object remain unchanged.

        If the HMC does not support property filtering for this type of
        resource, or if the resource on the HMC does not have one or more of
        the specified properties, the full set of properties is retrieved from
        the HMC and cached in this Python object.

        If the resource no longer exists on the HMC,
        :exc:`~zhmcclient.CeasedExistence` will be raised.

        This method serializes with other methods that access or change
        resource properties on the same Python object.

        Authorization requirements:

        * Object-access permission to this resource.

        Parameters:

          properties (:term:`string` or list/tuple of strings):
            Single name or list/tuple of names of the resource properties, using
            the names defined in the respective 'Data model' sections in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.CeasedExistence`
        """
        if not properties:
            return

        if not isinstance(properties, (list, tuple)):
            properties = [properties]

        with self._property_lock:
            if self._ceased_existence:
                raise CeasedExistence(self._uri)

        if self.manager.supports_properties:
            # Note: Older HMC versions may simply ignore the query parameter
            # and return the full list of properties. Newer HMC versions return
            # HTTP 400,1 "unrecognized or unsupported query parameter" if it is
            # not supported for the resource type.
            uri = f"{self._uri}?properties={','.join(properties)}"
            try:
                subset_properties = self.manager.session.get(uri, resource=self)
                # pylint: disable=simplifiable-if-statement
                if len(subset_properties) > len(properties):
                    # We have an older HMC that ignored the query parameter and
                    # returned all properties.
                    is_full = True
                else:
                    is_full = False
            except HTTPError as exc:
                if exc.http_status == 400 and exc.reason == 1:
                    # HMC does not yet support the query parameter, get full set
                    subset_properties = self.manager.session.get(
                        self._uri, resource=self)
                    is_full = True
                elif exc.http_status == 400 and exc.reason == 14:
                    # The resource does not have one or more of the specified
                    # properties, get full set
                    subset_properties = self.manager.session.get(
                        self._uri, resource=self)
                    is_full = True
                elif exc.http_status == 404 and exc.reason == 1:
                    # The resource no longer exists
                    self.cease_existence_local()
                    raise CeasedExistence(self._uri)
                else:
                    raise
        else:
            # Resource does not support the query parameter, get full set
            try:
                subset_properties = self.manager.session.get(
                    self._uri, resource=self)
                is_full = True
            except HTTPError as exc:
                if exc.http_status == 404 and exc.reason == 1:
                    # The resource no longer exists
                    self.cease_existence_local()
                    raise CeasedExistence(self._uri)
                raise

        with self._property_lock:
            if is_full:
                self._properties.update(subset_properties)
                self._properties_timestamp = int(time.time())
                self._full_properties = True
            else:
                self._properties.update(subset_properties)
                # We leave the self._full_properties flag unchanged. If the
                # local object already had full properties pulled earlier, it
                # now still has all of them.
                # We leave the self._properties_timestamp unchanged. The
                # resource now has newer and older properties, and the timestamp
                # indicates the oldest properties.

    @logged_api_call
    def get_property(self, name):
        """
        Return the value of a resource property.

        If the resource property is not cached in this Python object, the full
        set of resource properties is retrieved from the HMC and cached in this
        Python object.

        If the resource no longer exists on the HMC,
        :exc:`~zhmcclient.CeasedExistence` will be raised.

        If the resource on the HMC does not have the property, :exc:`KeyError`
        will be raised.

        This method serializes with other methods that access or change
        resource properties on the same Python object.

        Authorization requirements:

        * Object-access permission to this resource.

        Parameters:

          name (:term:`string`):
            Name of the resource property, using the names defined in the
            respective 'Data model' sections in the :term:`HMC API` book.

        Returns:

          The value of the resource property.

        Raises:

          KeyError: The resource does not have a property with that name.
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.CeasedExistence`
        """
        try:
            with self._property_lock:
                if self._ceased_existence:
                    raise CeasedExistence(self._uri)
                return self._properties[name]
        except KeyError:
            if self._full_properties:
                raise
            self.pull_full_properties()
            with self._property_lock:
                return self._properties[name]

    @logged_api_call
    def prop(self, name, default=None):
        """
        Return the value of a resource property, applying a default if the
        resource does not have a property with that name.

        If the resource property is cached in this Python object, its value is
        used. Otherwise, the full set of resource properties is retrieved from
        the HMC and cached in this Python object.

        If the resource no longer exists on the HMC,
        :exc:`~zhmcclient.CeasedExistence` is raised.

        This method serializes with other methods that access or change
        resource properties on the same Python object.

        Authorization requirements:

        * Object-access permission to this resource.

        Parameters:

          name (:term:`string`):
            Name of the resource property, using the names defined in the
            respective 'Data model' sections in the :term:`HMC API` book.

          default:
            Default value to be used, if the resource does not have a property
            with the specified name.

        Returns:

          The value of the resource property.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.CeasedExistence`
        """
        try:
            return self.get_property(name)
        except KeyError:
            return default

    def get_properties_pulled(self, names):
        """
        Return a set of resource properties with the values they currently have
        on the HMC.

        If auto-update is enabled for the resource, the property value is
        returned from the (automatically updated) local cache. Otherwise, a
        "Get Properties" operation is performed to get the current values. If
        supported by the type of resource, the operation uses the 'properties'
        query parameter to restrict the response to the desired properties.

        If the resource on the HMC does not have a property that was specified,
        its value will default to `None`.

        If the resource no longer exists on the HMC,
        :exc:`~zhmcclient.CeasedExistence` is raised.

        This method serializes with other methods that access or change
        resource properties on the same Python object.

        Authorization requirements:

        * Object-access permission to this resource.

        Parameters:

          names (:term:`string` or list/tuple of strings):
            Single name or list/tuple of names of the resource properties, using
            the names defined in the respective 'Data model' sections in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.CeasedExistence`
        """
        if not self.auto_update_enabled():
            self.pull_properties(names)

        return self.get_properties_local(names)

    def get_properties_local(self, names, defaults=None):
        """
        Return the values of a set of resource properties, using default values
        for those that are not cached in this Python object, without
        retrieving them from the HMC.

        This method serializes with other methods that access or change
        resource properties on the same Python object.

        Parameters:

          names (:term:`string` or list/tuple of strings):
            Single name or list/tuple of names of the resource properties, using
            the names defined in the respective 'Data model' sections in the
            :term:`HMC API` book.

          defaults:
            Single value or list/tuple of values to be used as a default for
            resource properties that are not cached in this Python object. If a
            single value, it is used for all properties that are not cached.
            If a list/tuple, it must be index-correlated with the names
            list/tuple.

        Returns:

          Single value (if names is a single value) or list of values (if names
          is a list/tuple of values) of the properties, with defaults applied.
        """
        if isinstance(names, (list, tuple)):
            with self._property_lock:
                values = []
                for i, name in enumerate(names):
                    try:
                        value = self._properties[name]
                    except KeyError:
                        if isinstance(defaults, (list, tuple)):
                            value = defaults[i]
                        else:
                            value = defaults
                    values.append(value)
                return values
        else:
            with self._property_lock:
                try:
                    return self._properties[names]
                except KeyError:
                    return defaults

    def update_properties_local(self, properties):
        """
        Update the values of a set of resource properties on this Python object
        without propagating the updates to the HMC.

        If a property to be updated is not present in the Python object, it
        is added.

        This method serializes with other methods that access or change
        resource properties on the same Python object.

        Parameters:

          properties (:class:`py:dict`):
            Dictionary of new property values, with:

            - Key: Name of the property, using the names defined in the
              respective 'Data model' sections in the :term:`HMC API` book.

            - Value: New value for the property.
        """
        with self._property_lock:
            for name, value in properties.items():
                self._properties[name] = value

    def cease_existence_local(self):
        """
        Update this Python object to indicate that the corresponding HMC object
        no longer exists.

        This method serializes with other methods that access or change
        resource properties on the same Python object.
        """
        with self._property_lock:
            self._ceased_existence = True

    def __str__(self):
        """
        Return a human readable string representation of this resource.

        This method serializes with other methods that access or change
        resource properties on the same Python object.

        Example result:

        .. code-block:: text

            Cpc(name=P0000S12,
                object-uri=/api/cpcs/f1bc49af-f71a-3467-8def-3c186b5d9352,
                status=service-required)
        """
        with self._property_lock:
            properties_keys = self._properties.keys()
            search_keys = ['status', 'object-uri', 'element-uri', 'name',
                           'type', 'class']
            sorted_keys = sorted([k for k in properties_keys
                                  if k in search_keys])
            info = ", ".join(f"{k}={self._properties[k]!r}"
                             for k in sorted_keys)
            return f"{self.__class__.__name__}({info})"

    def __repr__(self):
        """
        Return a string with the state of this resource, for debug purposes.

        This method serializes with other methods that access or change
        resource properties on the same Python object.

        Note that the derived resource classes that have child resources
        have their own ``__repr__()`` methods, because only they know which
        child resources they have.
        """
        with self._property_lock:
            ret = (
                f"{repr_obj_id(self)} (\n"
                f"  _manager={repr_obj_id(self._manager)},\n"
                f"  _uri={self._uri!r},\n"
                f"  _ceased_existence={self._ceased_existence!r},\n"
                f"  _full_properties={self._full_properties!r},\n"
                f"  _auto_update={self._auto_update!r},\n"
                f"  _properties_timestamp="
                f"{repr_timestamp(self._properties_timestamp)},\n"
                f"  _properties={repr_dict(self._properties, indent=4)}\n"
                ")")
            return ret

    def auto_update_enabled(self):
        """
        Return whether :ref:`auto-updating` is
        currently enabled for the resource object.

        Return:
          bool: Indicates whether auto-update is enabled.
        """
        return self._auto_update

    def enable_auto_update(self):
        """
        Enable :ref:`auto-updating` for this
        resource object, if currently disabled.

        When enabling auto-update, the session to which this resource belongs is
        subscribed for auto-updating if needed (see
        :meth:`~zhmcclient.Session.subscribe_auto_update`), the resource
        object is registered with the session's auto updater via
        :meth:`~zhmcclient.AutoUpdater.register_object`, and all properties
        of this resource object are retrieved from the HMC using
        :meth:`pull_full_properties` in order to have the most current values
        as a basis for the future auto-updating.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.CeasedExistence`
        """
        if not self._auto_update:
            session = self.manager.session
            session.subscribe_auto_update()
            session.auto_updater.register_object(self)
            self._auto_update = True
            self.pull_full_properties()

    def disable_auto_update(self):
        """
        Disable :ref:`auto-updating` for this
        resource object, if currently enabled.

        When disabling auto-updating, the resource object is unregistered from
        the session's auto updater via
        :meth:`~zhmcclient.AutoUpdater.unregister_object`, and the session
        is unsubscribed from auto-updating if the auto updater has no more
        objects registered.
        """
        if self._auto_update:
            self._auto_update = False
            session = self.manager.session
            session.auto_updater.unregister_object(self)
            if not session.auto_updater.has_objects():
                session.unsubscribe_auto_update()

    def dump(self):
        """
        Dump this resource with its properties and child resources
        (recursively) as a resource definition.

        This is the default implementation for the case where the resource has
        no child resources. If the resource does have child resources, this
        method needs to be overridden in the resource subclass.

        The returned resource definition of this implementation has the
        following format::

            {
                "properties": {...},
            }

        Returns:

          dict: Resource definition of this resource.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.CeasedExistence`
        """
        resource_dict = OrderedDict()
        self.pull_full_properties()
        resource_dict['properties'] = OrderedDict(self._properties)
        # No child resources
        return resource_dict
