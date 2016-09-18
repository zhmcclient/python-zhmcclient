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

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (subclass of :class:`~zhmcclient.BaseManager`):
            Manager object for this resource (and for all resources of the same
            type in the scope of that manager).

          uri (string):
            Canonical URI path of the resource.

          properties (dict):
            Properties to be set for the resource.

            * Key: Name of the property.
            * Value: Value of the property.

            The input dictionary is copied (shallow), so that the input
            dictionary can be modified by the user without affecting the
            properties of resource objects created from that input dictionary.

            Property qualifiers (read-only, etc.) are not represented on the
            resource object. The properties on the resource object are
            mutable. Whether or not a particular property of the represented
            manageable resource can be updated is described in its property
            qualifiers. See section "Property characteristics" in the
            :term:`HMC API` book for a description of the concept of property
            qualifiers, and the respective sections describing the resources
            for their actual definitions of property qualifiers.
        """
        self._manager = manager
        self._uri = uri
        self._properties = dict(properties)
        self._properties_timestamp = int(time.time())
        self._full_properties = False

    @property
    def properties(self):
        """
        dict:
          The properties of this resource.

          * Key: Name of the property.
          * Value: Value of the property.

          See the respective 'Data model' sections in the :term:`HMC API` book
          for a description of the resources along with their properties.

          The dictionary contains either the full set of resource properties,
          or a subset thereof.
        """
        return self._properties

    @property
    def uri(self):
        """
        string: The canonical URI path of the resource.

        Example: ``/api/cpcs/12345``
        """
        return self._uri

    @property
    def manager(self):
        """
        Subclass of :class:`~zhmcclient.BaseManager`:
          Manager object for this resource (and for all resources of the same
          type in the scope of that manager).
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
