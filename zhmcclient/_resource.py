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

    def __init__(self, manager, properties):
        """
        Parameters:

          manager (subclass of :class:`~zhmcclient.BaseManager`):
            Manager object for this resource (and for all resources of the same
            type in the scope of that manager).

          properties (dict):
            Properties to be set for this resource object.

            * Key: Name of the property.
            * Value: Value of the property.

            The input dictionary is copied (shallow), so that the input
            dictionary can be modified by the user without affecting the
            properties of resource objects created from that input dictionary.

            Property qualifiers (read-only, etc.) are not represented on the
            resource object. The properties on the resource object are
            mutable. Whether or not a particular property of the represented
            manageable resource can be updated is described in its property
            qualifiers. See section "Property characteristics" in chapter 5 of
            :term:`HMC API` for a description of the concept of property
            qualifiers, and the respective sections describing the resources
            for their actual definitions of property qualifiers.
        """
        self._manager = manager
        self._properties = dict(properties)
        self._properties_timestamp = int(time.time())
        self._full_properties = False

    @property
    def properties(self):
        """
        dict:
          The properties of this resource object.

          * Key: Name of the property.
          * Value: Value of the property.

          See the respective sections in :term:`HMC API` for a description
          of the resources along with their properties.
        """
        return self._properties

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
        return self._full_properties

    @property
    def properties_timestamp(self):
        return self._properties_timestamp

    def pull_full_properties(self):
        full_properties = self.manager.session.get(self.get_property('object-uri'))
        self._properties = dict(full_properties)
        self._properties_timestamp = int(time.time())
        self._full_properties = True

    def get_property(self, name):
        try:
            return self._properties[name]
        except KeyError:
            if self.full_properties:
                raise
            self.pull_full_properties()
            return self._properties[name]

