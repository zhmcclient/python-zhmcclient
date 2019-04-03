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
Base definitions for resource classes.

Resource objects represent the real manageable resources in the systems managed
by the HMC.
"""

from __future__ import absolute_import
import time

from ._logging import logged_api_call
from ._utils import repr_dict, repr_timestamp

__all__ = ['BaseResource']


class BaseResource(object):
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

    @property
    def properties(self):
        """
        dict:
          The properties of this resource that are currently present in this
          Python object.
          Will not be `None`.

          * Key: Name of the property.
          * Value: Value of the property.

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

        The properties in this dictionary are mutable. However, the properties
        of the actual manageable resources may or may not be mutable.
        Mutability for each resource property is indicated with the 'w'
        qualifier in its data model in the :term:`HMC API` book.
        """
        return self._properties

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
        """
        # We avoid storing the name in an instance variable, because it can
        # be modified via update_properties().
        return self.get_property(self.manager._name_prop)

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

    @logged_api_call
    def pull_full_properties(self):
        """
        Retrieve the full set of resource properties and cache them in this
        object.

        Authorization requirements:

        * Object-access permission to this resource.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        full_properties = self.manager.session.get(self._uri)
        self._properties = dict(full_properties)
        self._properties_timestamp = int(time.time())
        self._full_properties = True

    @logged_api_call
    def get_property(self, name):
        """
        Return the value of a resource property.

        If the resource property is not cached in this object yet, the full set
        of resource properties is retrieved and cached in this object, and the
        resource property is again attempted to be returned.

        Authorization requirements:

        * Object-access permission to this resource.

        Parameters:

          name (:term:`string`):
            Name of the resource property, using the names defined in the
            respective 'Data model' sections in the :term:`HMC API` book.

        Returns:

          The value of the resource property.

        Raises:

          KeyError: The resource property could not be found (also not in the
            full set of resource properties).
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        try:
            return self._properties[name]
        except KeyError:
            if self._full_properties:
                raise
            self.pull_full_properties()
            return self._properties[name]

    @logged_api_call
    def prop(self, name, default=None):
        """
        Return the value of a resource property, applying a default if it
        does not exist.

        If the resource property is not cached in this object yet, the full set
        of resource properties is retrieved and cached in this object, and the
        resource property is again attempted to be returned.

        Authorization requirements:

        * Object-access permission to this resource.

        Parameters:

          name (:term:`string`):
            Name of the resource property, using the names defined in the
            respective 'Data model' sections in the :term:`HMC API` book.

          default:
            Default value to be used, if the resource property does not exist.

        Returns:

          The value of the resource property.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        try:
            return self.get_property(name)
        except KeyError:
            return default

    def __str__(self):
        """
        Return a human readable string representation of this resource.

        Example result:

        .. code-block:: text

            Cpc(name=P0000S12,
                object-uri=/api/cpcs/f1bc49af-f71a-3467-8def-3c186b5d9352,
                status=service-required)
        """
        properties_keys = self._properties.keys()
        search_keys = ['status', 'object-uri', 'element-uri', 'name',
                       'type', 'class']
        sorted_keys = sorted([k for k in properties_keys if k in search_keys])
        info = ", ".join("%s=%r" % (k, self._properties[k])
                         for k in sorted_keys)
        return "%s(%s)" % (self.__class__.__name__, info)

    def __repr__(self):
        """
        Return a string with the state of this resource, for debug purposes.

        Note that the derived resource classes that have child resources
        have their own ``__repr__()`` methods, because only they know which
        child resources they have.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _manager={_manager_classname} at 0x{_manager_id:08x},\n"
            "  _uri={_uri!r},\n"
            "  _full_properties={_full_properties!r},\n"
            "  _properties_timestamp={_properties_timestamp},\n"
            "  _properties={_properties}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                _manager_classname=self._manager.__class__.__name__,
                _manager_id=id(self._manager),
                _uri=self._uri,
                _full_properties=self._full_properties,
                _properties_timestamp=repr_timestamp(
                    self._properties_timestamp),
                _properties=repr_dict(self._properties, indent=4),
            ))
        return ret
