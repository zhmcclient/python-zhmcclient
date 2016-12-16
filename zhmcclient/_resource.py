# Copyright 2016 IBM Corp. All Rights Reserved.
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

__all__ = ['BaseResource']


class BaseResource(object):
    """
    Abstract base class for resource classes (e.g. :class:`~zhmcclient.Cpc`)
    representing manageable resources.

    Such resource objects are representations of real manageable resources in
    the systems managed by the HMC.

    It defines the interface for the derived resource classes, and implements
    methods that have a common implementation for the derived resource classes.
    """

    def __init__(self, manager, uri, properties, uri_prop, name_prop):
        """
        Parameters:

          manager (subclass of :class:`~zhmcclient.BaseManager`):
            Manager object for this resource object (and for all resource
            objects of the same type in the scope of that manager). Must not be
            `None`.

          uri (string):
            Canonical URI path of the resource.
            Will be used to set the corresponding property in this resource
            object (see `uri_prop` parameter).
            Must not be `None`.

          properties (dict):
            Properties for this resource object. May be `None` or empty.

            * Key: Name of the property.
            * Value: Value of the property.

            The properties on this resource object are mutable. However, the
            properties of the actual resource in the HMC may or may not be
            mutable. Mutability for each property of a resource is indicated
            with the 'w' qualifier in its data model in the :term:`HMC API`
            book.

          uri_prop (string):
            Name of the resource property that is the canonical URI path of
            the resource (e.g. 'object-uri' or 'element-uri').
            Must not be `None`.

          name_prop (string):
            Name of the resource property that is the name of the resource
            (e.g. 'name'). Must not be `None`.
        """

        # We want to surface precondition violations as early as possible,
        # so we test those that are not surfaced through the init code:
        assert manager is not None
        assert uri is not None
        assert uri_prop is not None
        assert name_prop is not None

        self._manager = manager
        self._uri = uri
        self._properties = dict(properties) if properties else {}
        self._properties[uri_prop] = uri
        self._uri_prop = uri_prop
        self._name_prop = name_prop

        self._name = None  # Will be retrieved once needed
        self._properties_timestamp = int(time.time())
        self._full_properties = False

    @property
    def properties(self):
        """
        dict:
          The properties of this resource. Will not be `None`.

          * Key: Name of the property.
          * Value: Value of the property.

          See the respective 'Data model' sections in the :term:`HMC API` book
          for a description of the resources along with their properties.

          The dictionary contains either the full set of resource properties,
          or a subset thereof, or can be empty in some cases.

          Because this dictionary may be empty in some cases, the name and the
          URI of the resource should be obtained via the
          :attr:`~zhmcclient.BaseResource.name` and
          :attr:`~zhmcclient.BaseResource.uri` attributes of this object,
          respectively.
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
        # The name property of the actual resource in the HMC will never
        # be None, so we can use `None` for indicating that it is not yet
        # initialized.
        if self._name is None:
            self._name = self.get_property(self._name_prop)
        return self._name

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

    def pull_full_properties(self):
        """
        Retrieve the full set of resource properties and cache them in this
        object.

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

    def get_property(self, name):
        """
        Return the value of a resource property.

        If the resource property is not cached in this object yet, the full set
        of resource properties is retrieved and cached in this object, and the
        resource property is again attempted to be returned.

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

    def prop(self, name, default=None):
        """
        Return the value of a resource property, applying a default if it
        does not exist.

        If the resource property is not cached in this object yet, the full set
        of resource properties is retrieved and cached in this object, and the
        resource property is again attempted to be returned.

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
        Return a human readable representation of this resource.

        Example::

            Cpc(name=P0000S12,
                object-uri=/api/cpcs/f1bc49af-f71a-3467-8def-3c186b5d9352,
                status=service-required)
        """
        properties_keys = self._properties.keys()
        search_keys = ['status', 'object-uri', 'element-uri', 'name',
                       'type', 'class']
        sorted_keys = sorted([k for k in properties_keys if k in search_keys])
        info = ", ".join("%s=%s" % (k, self._properties[k])
                         for k in sorted_keys)
        return "%s(%s)" % (self.__class__.__name__, info)

    def __repr__(self):
        """
        Return a representation of this resource suitable for debugging its
        state.
        """
        return self.__str__()
