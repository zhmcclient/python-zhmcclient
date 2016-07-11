#!/usr/bin/env python

from __future__ import absolute_import
import collections

__all__ = ['BaseResource']

class BaseResource(object):
    """
    Abstract base class for resource classes (e.g. :class:`~zhmcclient.Cpc`)
    representing manageable resources.

    It defines the interface for the derived resource classes, and implements
    methods that have a common implementation for the derived resource classes.

    This class behaves like a dictionary of the properties of the represented
    manageable resource, where the names of the properties are the
    dictionary keys, and the property values are the dictionary values.
    However, only a subset of the Python dictionary methods are supported.
    """

    def __init__(self, manager, properties):
        """
        Parameters:

          manager (subclass of :class:`~zhmcclient.BaseManager`):
            Manager object for this resource (and for all resources of the same
            type in the scope of that manager).

          properties (mapping):
            Properties to be set for this resource object. Property qualifiers
            (read-only, etc.) are not represented on this object.

            The properties on this object are mutable. However, whether or not
            a particular property of the represented manageable resource can be
            updated is described in its property qualifiers (see section
            "Property characteristics" in chapter 5 of :term:`HMC API` for
            a description of the concept of property qualifiers, and the
            respective sections describing the resources for their actual
            definitions of property qualifiers.)

            * Key: Name of the property.
            * Value: Value of the property.

        Raises:
          TypeError: Invalid type of properties argument.
        """
        # A check for manager being a BaseManager creates a cyclic import
        # dependency and is therefore not performed.
        self._manager = manager
        if not isinstance(properties, collections.Mapping):
            raise TypeError("properties argument must be a mapping, but " \
                            "is of type %s" % properties.__class__.__name__)
        self._properties = properties

    def __len__(self):
        """
        Return the number of properties of this resource object.

        Note: This special method is used by ``len(resource)``.
        """
        return len(self._properties)

    def __getitem__(self, key):
        """
        Return the value of a property with a particular name in this resource
        object.

        Parameters:

          key (:term:`string`): Property name.

        Raises:

          :exc:`KeyError`: This resource object does not have a property with
            that name.

        Note: This special method is used by ``value = resource[name]``.
        """
        return self._properties[key]

    def __setitem__(self, key, value):
        """
        Set the value of a property with a particular name in this resource
        object.

        Parameters:

          key (:term:`string`): Property name.

          value (:term:`object`): Property value.

        Note: This special method is used by ``resource[name] = value``.
        """
        self._properties[key] = value

    def __delitem__(self, key):
        """
        Remove property with a particular name from this resource object.

        Parameters:

          key (:term:`string`): Property name.

        Note: This special method is used by ``del resource[name]``.
        """
        del self._properties[key]

    def __contains__(self, key):
        """
        Return a boolean indicating whether the resource object has a property
        with a particular name.

        Parameters:

          key (:term:`string`): Property name.

        Note: This special method is used by ``name in resource`` and
        ``name not in resource``.
        """
        return key in self._properties

    def __iter__(self):
        """
        Return an iterator over the resource object's property names.

        Note: This is a shortcut for :meth:`~zhmcclient.BaseResource.iterkeys`.

        Note: This special method is used by ``iter(resource)`` and by
        ``for name in resource``.
        """
        return six.iterkeys(self._properties)

    def __eq__(self, other):
        """
        Return a boolean indicating whether two resource objects are equal.

        Two resource objects are considered equal, if they have equal sets
        of property names, and if the values of matching properties are equal
        (based on their `==` operator).

        Other attributes (e.g. the resource manager) are not considered for
        the comparison.

        Note: This special method is used when two resource objects are
        compared with the `==` operator.
        """
        if len(self) != len(other):
            return False
        for key in self.iterkeys():
            if key not in other:
                return False
        for key, self_value in self.iteritems():
            try:
                if not self_value == other[key]:
                    return False
            except TypeError:
                return False # not comparable -> considered not equal
        return True

    def __ne__(self, other):
        """
        Return a boolean indicating whether two resource objects are not equal.

        Implemented by delegating to the `==` operator, see
        :meth:`~zhmcclient.BaseResource.__eq__` for details.

        Note: This special method is used when two resource objects are
        compared with the `!=` operator.
        """
        return not self == other

    # Note: Ordering comparisons (e.g. __lt__, etc.) between resource objects
    #       are not supported, because they are not totally ordered.

    def clear(self):
        """
        Remove all properties from this resource object.
        """
        self._properties.clear()

    def get(self, key, default=None):
        """
        Return the value of a property with a particular name in this resource
        object or a default value if a property with that name does not exist.

        Parameters:
          key (:term:`string`): Property name.
          default (:term:`object`): Default value to be returned.
        """
        return self._properties.get(key, default)

    def has_key(self, key):
        """
        Return a boolean indicating whether the resource object has a property
        with a particular name.

        Parameters:
          key (:term:`string`): Property name.
        """
        return key in self._properties

    def items(self):
        """
        Return a copied list of the resource object's properties, where each
        list item is a tuple of property name and value.
        """
        return self._properties.items()

    def iteritems(self):
        """
        Return an iterator over the resource object's properties, where each
        item is a tuple of property name and value.

        Using :meth:`~zhmcclient.BaseResource.iteritems` while adding or
        deleting properties may raise a :exc:`RuntimeError` or fail to iterate
        over all properties.
        """
        return self._properties.iteritems()

    def iterkeys(self):
        """
        Return an iterator over the resource object's property names.

        Using :meth:`~zhmcclient.BaseResource.iterkeys` while adding or
        deleting properties may raise a :exc:`RuntimeError` or fail to iterate
        over all properties.
        """
        return self._properties.iterkeys()

    def itervalues(self):
        """
        Return an iterator over the resource object's property values.

        Using :meth:`~zhmcclient.BaseResource.itervalues` while adding or
        deleting properties may raise a :exc:`RuntimeError` or fail to iterate
        over all properties.
        """
        return self._properties.itervalues()

    def keys(self):
        """
        Return a copied list of the resource object's property names.
        """
        return self._properties.keys()

    def update(self, *args, **kwargs):
        """
        Update the properties of this resource object from the provided
        arguments.

        Each positional argument can be:

          * a dictionary (including :class:`~zhmcclient.BaseResource`) of
            property names and values.

          * an :term:`py:iterable` of tuples of property name and value.

        Each keyword argument specifies a property with name and value.

        Note that some resource property names are invalid Python argument
        names, for example ``object-uri``. Such properties cannot be updated
        via keyword arguments, but via positional arguments.
        """
        self._properties.update(*args, **kwargs)

    def values(self):
        """
        Return a copied list of the resource object's property values.
        """
        return self._properties.values()

    def viewitems(self):
        """
        Return a new view of the resource object's properties, where each
        view item is a tuple of its property name and its value.

        See :ref:`Python dictionary view objects <py:dict-views>` for details.
        """
        return self._properties.viewitems()

    def viewkeys(self):
        """
        Return a new view of the resource object's property names, where each
        view item is the property name.

        See :ref:`Python dictionary view objects <py:dict-views>` for details.
        """
        return self._properties.viewkeys()

    def viewvalues(self):
        """
        Return a new view of the resource object's property values, where each
        view item is the property value.

        See :ref:`Python dictionary view objects <py:dict-views>` for details.
        """
        return self._properties.viewvalues()

    @property
    def manager(self):
        """
        Subclass of :class:`~zhmcclient.BaseManager`:
          Manager object for this resource (and for all resources of the same
          type in the scope of that manager).
        """
        return self._manager

