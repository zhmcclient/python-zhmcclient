#!/usr/bin/env python

"""
Base definitions for resource classes.

Resource objects represent the real manageable resources in the systems managed
by the HMC.
"""

from __future__ import absolute_import

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
