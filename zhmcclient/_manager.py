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

from requests.utils import quote

from ._exceptions import NotFound, NoUniqueMatch

__all__ = ['BaseManager']


class BaseManager(object):
    """
    Abstract base class for manager classes (e.g.
    :class:`~zhmcclient.CpcManager`).

    It defines the interface for the derived manager classes, and implements
    methods that have a common implementation for the derived manager classes.

    Objects of derived manager classes should not be created by users of this
    package by simply instantiating them. Instead, such objects are created by
    this package as instance variables of :class:`~zhmcclient.Client` and
    other resource objects, e.g. :attr:`~zhmcclient.Client.cpcs`. For this
    reason, the `__init__()`  method of this class and of its derived manager
    classes are considered internal interfaces and their parameters are not
    documented and may change incompatibly.
    """

    def __init__(self, resource_class, parent, uri_prop, name_prop,
                 query_props):
        # This method intentionally has no docstring, because it is internal.
        #
        # Parameters:
        #   resource_class (class):
        #     Python class for the resources of this manager.
        #     Must not be `None`.
        #   parent (subclass of :class:`~zhmcclient.BaseResource`):
        #     Parent resource defining the scope for this manager.
        #     `None`, if the manager has no parent, i.e. when it manages
        #     top-level resources (e.g. CPC).
        #   uri_prop (string):
        #     Name of the resource property that is the canonical URI path of
        #     the resource (e.g. 'object-uri' or 'element-uri').
        #     Must not be `None`.
        #   name_prop (string):
        #     Name of the resource property that is the name of the resource
        #     (e.g. 'name').
        #     Must not be `None`.
        #   query_props (iterable of strings):
        #     List of names of resource properties that are supported as filter
        #     query parameters in HMC list operations for this type of resource
        #     (i.e. for server-side filtering).
        #     Must not be `None`.
        #     If the support for a resource property changes within the set of
        #     HMC versions that support this type of resource, this list must
        #     represent the version of the HMC this session is connected to.

        # We want to surface precondition violations as early as possible,
        # so we test those that are not surfaced through the init code:
        assert resource_class is not None
        assert uri_prop is not None
        assert name_prop is not None
        assert query_props is not None

        self._resource_class = resource_class
        self._parent = parent
        self._uri_prop = uri_prop
        self._name_prop = name_prop
        self._query_props = query_props

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

    def _divide_filter_args(self, filter_args):
        """
        Divide the filter arguments into filter query parameters for filtering
        on the server side, and the remaining client-side filters.

        Parameters:

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          : tuple (query_parms_str, client_filter_args)
        """
        query_parms = []  # query parameter strings
        client_filter_args = {}

        if filter_args is not None:
            for prop_name in filter_args:
                prop_match = filter_args[prop_name]
                if prop_name in self._query_props:
                    self._append_query_parms(query_parms, prop_name,
                                             prop_match)
                else:
                    client_filter_args[prop_name] = prop_match
        query_parms_str = '&'.join(query_parms)
        if query_parms_str:
            query_parms_str = '?{}'.format(query_parms_str)

        return query_parms_str, client_filter_args

    def _append_query_parms(self, query_parms, prop_name, prop_match):
        if isinstance(prop_match, (list, tuple)):
            for pm in prop_match:
                self._append_query_parms(query_parms, prop_name, pm)
        else:
            # Just in case, we also escape the property name
            parm_name = quote(prop_name, safe='')
            parm_value = quote(str(prop_match), safe='')
            qp = '{}={}'.format(parm_name, parm_value)
            query_parms.append(qp)

    def _matches_filters(self, obj, filter_args):
        """
        Return a boolean indicating whether a resource object matches a set
        of filter arguments.
        This is used for client-side filtering.

        Depending on the properties specified in the filter arguments, this
        method retrieves the resource properties from the HMC.

        Parameters:

          obj (BaseResource):
            Resource object.

          filter_args (dict):
            Filter arguments. For details, see :ref:`Filtering`.
            `None` causes the resource to always match.

        Returns:

          bool: Boolean indicating whether the resource object matches the
            filter arguments.
        """
        if filter_args is not None:
            for prop_name in filter_args:
                prop_match = filter_args[prop_name]
                if not self._matches_prop(obj, prop_name, prop_match):
                    return False
        return True

    def _matches_prop(self, obj, prop_name, prop_match):
        if isinstance(prop_match, (list, tuple)):
            for pm in prop_match:
                if not self._matches_prop(obj, prop_name, pm):
                    return False
        else:
            # TODO: Here, we could match by regexp.
            if obj.get_property(prop_name) != prop_match:
                return False
        return True

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

    def list(self, full_properties=False, filter_args=None):
        """
        Interface for a method that lists resources, and that needs to be
        implemented by resource manager classes derived from this base class.

        Authorization requirements:

        * see the `list()` method in the derived classes.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only a minimal set as returned by the list
            operation.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          List of resource objects managed by this manager. The resource
          objects have a set of properties according to the `full_properties`
          parameter.

        Raises:

          : Exceptions raised by the `list()` methods in derived resource
            manager classes (see :ref:`Resources`).
        """
        raise NotImplementedError

    def find(self, **filter_args):
        """
        Find exactly one resource that is managed by this manager, by matching
        their resource properties against the specified filter arguments, and
        return its Python resource object (e.g. for a CPC,
        :class:`~zhmcclient.Cpc` object is returned).

        If only the 'name' resource property is specified, an optimized lookup
        is performed that uses a name-to-URI mapping cached in this manager
        object.

        Authorization requirements:

        * see the `list()` method in the derived classes.

        Keyword Arguments:

          : The keyword arguments are used as filter arguments that narrow the
            list of returned resources to those that match the specified filter
            arguments. For details, see :ref:`Filtering`.

            Note that some resource property names are not valid as Python
            parameter names (e.g. "adapter-family"). Such resource properties
            can still be used for filtering, but must be specified by the
            caller via a parameter dictionary (see the example for details).

        Returns:

          Resource object, if found. The resource object has a minimal set of
          properties.

        Raises:

          :exc:`~zhmcclient.NotFound`: No matching resource found.
          :exc:`~zhmcclient.NoUniqueMatch`: More than one matching resource
            found.
          : Exceptions raised by the `list()` methods in derived resource
            manager classes (see :ref:`Resources`).

        Example:

          The following example finds a CPC by its name. Because the 'name'
          resource property is also a valid Python variable name, there are two
          ways for the caller to specify the filter arguments for this method:

          * As named parameters::

              cpc = client.cpcs.find(name='CPC001')

          * As a parameter dictionary::

              filter_args = {'name': 'CPC0001'}
              cpc = client.cpcs.find(**filter_args)
        """
        obj_list = self.findall(**filter_args)
        num_objs = len(obj_list)
        if num_objs == 0:
            raise NotFound
        elif num_objs > 1:
            raise NoUniqueMatch
        else:
            return obj_list[0]

    def findall(self, **filter_args):
        """
        Find zero or more resources that are managed by this manager, by
        matching their resource properties against the specified filter
        arguments, and return a list of their Python resource objects (e.g. for
        CPCs, a list of :class:`~zhmcclient.Cpc` objects is returned).

        If only the 'name' resource property is specified, an optimized lookup
        is performed that uses a name-to-URI mapping cached in this manager
        object.

        Authorization requirements:

        * see the `list()` method in the derived classes.

        Keyword Arguments:

          : The keyword arguments are used as filter arguments that narrow the
            list of returned resources to those that match the specified filter
            arguments. For details, see :ref:`Filtering`.

            Note that some resource property names are not valid as Python
            parameter names (e.g. "adapter-family"). Such resource properties
            can still be used for this method, but must be specified via a
            parameter dictionary (see the example for details).

        Returns:

          A list of zero or more resource objects that were found. The resource
          objects have a minimal set of properties.

        Raises:

          : Exceptions raised by the `list()` methods in derived resource
            manager classes (see :ref:`Resources`).

        Example:

          The following example finds adapters of the OSA family in a CPC.
          Because the resource property for the adapter family is named
          'adapter-family', it is not suitable as a Python variable name.
          Therefore, the only way for the caller to specify it is via a
          parameter dictionary::

              filter_args = {'adapter-family': 'osa'}
              osa_adapters = cpc.adapters.findall(**filter_args)
        """
        if len(filter_args) == 1 and self._name_prop in filter_args:
            try:
                obj = self.find_by_name(filter_args[self._name_prop])
            except NotFound:
                return []
            return [obj]
        else:
            obj_list = self.list(filter_args=filter_args)
            return obj_list

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

        Authorization requirements:

        * see the `list()` method in the derived classes.

        Parameters:

          name (string):
            Name of the resource (value of its 'name' resource property).

        Returns:

          Resource object, if found. The resource object has a minimal set of
          properties.

        Raises:

          :exc:`~zhmcclient.NotFound`: No matching resource found.
          : Exceptions raised by the `list()` methods in derived resource
            manager classes (see :ref:`Resources`).

        Example:

          The following example finds a CPC by its name::

              cpc = client.cpcs.find_by_name('CPC001')
        """
        uri = self._get_uri(name)
        obj = self.resource_class(
            manager=self,
            uri=uri,
            name=name,
            properties=None)
        return obj

    def flush(self):
        """
        Flush the cached name-to-URI mapping.

        This only needs to be done after renaming a resource.
        """
        self._uris.clear()
