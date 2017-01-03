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
Base definitions for resource manager classes.

Resource manager classes exist for each resource type and are helper classes
that provide functionality common for the resource type.

Resource manager objects are not necessarily singleton objects, because they
have a scope of a certain set of resource objects. For example, the resource
manager object for LPARs exists once for each CPC managed by the HMC, and the
resource object scope of each LPAR manager object is the set of LPARs in that
CPC.
"""

from __future__ import absolute_import

from ._exceptions import NotFound, NoUniqueMatch

__all__ = ['BaseManager']


class BaseManager(object):
    """
    Abstract base class for manager classes (e.g.
    :class:`~zhmcclient.CpcManager`).

    It defines the interface for the derived manager classes, and implements
    methods that have a common implementation for the derived manager classes.
    """

    def __init__(self, resource_class, parent=None):
        """
        Parameters:

          resource_class (class):
            Python class for the resources of this manager.

          parent (subclass of :class:`~zhmcclient.BaseResource`):
            Parent resource defining the scope for this manager.

            `None`, if the manager has no parent, i.e. when it manages
            top-level resources.
        """
        self._resource_class = resource_class
        self._parent = parent
        self._uris = {}
        # Note: Managers of top-level resources must update the following
        # instance variables in their init:
        self._session = parent.manager.session if parent else None

    def _get_uri(self, name):
        """
        Look up a resource of this manager by name, using and possibly
        refreshing the cached name-to-URI mapping.
        """
        try:
            return self._uris[name]
        except KeyError:
            res_list = self.list()
            for res in res_list:
                self._uris[res.name] = res.uri
            try:
                return self._uris[name]
            except KeyError:
                raise NotFound

    @property
    def resource_class(self):
        """
        The Python class of the parent resource of this manager.
        """
        return self._resource_class

    @property
    def session(self):
        """
        :class:`~zhmcclient.Session`:
          Session with the HMC.
        """
        if self._session is None:
            raise AssertionError("%s.session: No session set (in top-level "
                                 "resource manager class?)" %
                                 self.__class__.__name__)
        return self._session

    @property
    def parent(self):
        """
        Subclass of :class:`~zhmcclient.BaseResource`:
          Parent resource defining the scope for this manager.

          `None`, if the manager has no parent, i.e. when it manages top-level
          resources.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        Interface for a method that lists resources, and that needs to be
        implemented by resource manager classes derived from this base class.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          List of resource objects managed by this manager.

        Raises:

          See derived resource manager classes in :ref:`Resources`.
        """
        raise NotImplementedError

    def find(self, **kwargs):
        """
        Find exactly one resource that is managed by this manager, by the value
        of zero or more resource properties.

        If more than one resource property is specified, all of them need to
        match for the resource to be found.

        If only the 'name' resource property is specified, an optimized lookup
        is performed that uses a name-to-URI mapping cached in this manager
        object.

        Keyword Arguments:

          : Each keyword argument is used to filter the resources managed by
            this manager, whereby the name of the keyword argument is used to
            look up the same-named resource property, and the value of the
            keyword argument is used to compare the resource property value
            against.

            Note that some resource property names are not valid as Python
            parameter names (e.g. "adapter-family"). Such resource properties
            can still be used for this method, but must be specified via a
            parameter dictionary (see the example for details).

        Returns:

          : The single resource object that was found.

        Raises:

          :exc:`~zhmcclient.NotFound`
          :exc:`~zhmcclient.NoUniqueMatch`
          Exceptions raised by :meth:`~zhmcclient.BaseManager.list`

        Example:

          The following example finds a CPC by its name. Because the 'name'
          resource property is also a valid Python variable name, there are two
          ways to specify the parameters to this method:

          * As named parameters::

              cpc = client.cpcs.find(name='CPC001')

          * As a parameter dictionary::

              find_args = {'name': 'CPC0001'}
              cpc = client.cpcs.find(**find_args)
        """
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if num_matches == 0:
            raise NotFound
        elif num_matches > 1:
            raise NoUniqueMatch
        else:
            return matches[0]

    def findall(self, **kwargs):
        """
        Find zero or more resources that are managed by this manager, by the
        value of zero or more resource properties.

        If more than one resource property is specified, all of them need to
        match for the resources to be found.

        If only the 'name' resource property is specified, an optimized lookup
        is performed that uses a name-to-URI mapping cached in this manager
        object.

        Keyword Arguments:

          : Each keyword argument is used to filter the resources managed by
            this manager, whereby the name of the keyword argument is used to
            look up the same-named resource property, and the value of the
            keyword argument is used to compare the resource property value
            against.

            Note that some resource property names are not valid as Python
            parameter names (e.g. "adapter-family"). Such resource properties
            can still be used for this method, but must be specified via a
            parameter dictionary (see the example for details).

        Returns:

          : A list of zero or more resource objects that were found.

        Raises:

          Exceptions raised by :meth:`~zhmcclient.BaseManager.list`.

        Example:

          The following example finds adapters of the OSA family in a CPC.
          Because the resource property for the adapter family is named
          'adapter-family', it is not suitable as a Python variable name.
          Therefore, the only way to specify it is via a parameter dictionary::

              find_args = {'adapter-family': 'osa'}
              osa_adapters = cpc.adapters.findall(**find_args)
        """
        found = list()
        if list(kwargs.keys()) == ['name']:
            obj = self.find_by_name(kwargs['name'])
            found.append(obj)
        else:
            searches = kwargs.items()
            listing = self.list()
            for obj in listing:
                try:
                    if all(obj.get_property(propname) == value
                           for (propname, value) in searches):
                        found.append(obj)
                except AttributeError:
                    continue
        return found

    def find_by_name(self, name):
        """
        Find a resource by name (i.e. value of its 'name' resource property)
        and return its Python resource object (e.g. for a CPC, a
        :class:`~zhmcclient.Cpc` object is returned).

        This method performs an optimized lookup that uses a name-to-URI
        mapping cached in this manager object.

        This method is automatically used by the
        :meth:`~zhmcclient.BaseManager.find` and
        :meth:`~zhmcclient.BaseManager.findall` methods, so it does not
        normally need to be used directly by users.

        Parameters:

          name (string):
            Name of the resource (value of its 'name' resource property).

        Returns:

          Resource object, if found.

        Raises:

          :exc:`~zhmcclient.NotFound`: Resource not found.
          Exceptions raised by the `list()` method in the derived classes.

        Example:

          The following example finds a CPC by its name::

              cpc = client.cpcs.find_by_name('CPC001')
        """
        uri = self._get_uri(name)
        obj = self.resource_class(self, uri)
        return obj

    def flush(self):
        """
        Flush the cached name-to-URI mapping.

        This only needs to be done after renaming a resource.
        """
        self._uris.clear()
