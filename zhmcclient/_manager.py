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

import six
import re
from datetime import datetime, timedelta
import warnings
from requests.utils import quote

from ._logging import logged_api_call
from ._exceptions import NotFound, NoUniqueMatch, HTTPError
from ._utils import repr_list

__all__ = ['BaseManager']


class _NameUriCache(object):
    """
    A Name-URI cache, that caches the mapping between resource names and
    resource URIs. It supports looking up resource URIs by resource names.

    This class is used by the implementation of manager classes, and is not
    part of the external API.
    """

    def __init__(self, manager, timetolive):
        """
        Parameters:

          manager (BaseManager): Manager that holds this Name-URI cache. The
            manager object is expected to have a ``list()`` method, which
            is used to list the resources of that manager, in order to
            fill this cache.

          timetolive (number): Time in seconds until the cache will invalidate
            itself automatically, since it was last invalidated.
        """
        self._manager = manager
        self._timetolive = timetolive

        # The cached data, as a dictionary with:
        # Key (string): Name of a resource (unique within its parent resource)
        # Value (string): URI of that resource
        self._uris = {}

        # Point in time when the cache was last invalidated
        self._invalidated = datetime.now()

    def get(self, name):
        """
        Get the resource URI for a specified resource name.

        If an entry for the specified resource name does not exist in the
        Name-URI cache, the cache is refreshed from the HMC with all resources
        of the manager holding this cache.

        If an entry for the specified resource name still does not exist after
        that, ``NotFound`` is raised.
        """
        self.auto_invalidate()
        try:
            return self._uris[name]
        except KeyError:
            self.refresh()
            try:
                return self._uris[name]
            except KeyError:
                raise NotFound({self._manager._name_prop: name}, self._manager)

    def auto_invalidate(self):
        """
        Invalidate the cache if the current time is past the time to live.
        """
        current = datetime.now()
        if current > self._invalidated + timedelta(seconds=self._timetolive):
            self.invalidate()

    def invalidate(self):
        """
        Invalidate the cache.

        This empties the cache and sets the time of last invalidation to the
        current time.
        """
        self._uris = {}
        self._invalidated = datetime.now()

    def refresh(self):
        """
        Refresh the Name-URI cache from the HMC.

        This is done by invalidating the cache, listing the resources of this
        manager from the HMC, and populating the cache with that information.
        """
        self.invalidate()
        full = not self._manager._list_has_name
        res_list = self._manager.list(full_properties=full)
        self.update_from(res_list)

    def update_from(self, res_list):
        """
        Update the Name-URI cache from the provided resource list.

        This is done by going through the resource list and updating any cache
        entries for non-empty resource names in that list. Other cache entries
        remain unchanged.
        """
        for res in res_list:
            # We access the properties dictionary, in order to make sure
            # we don't drive additional HMC interactions.
            name = res.properties.get(self._manager._name_prop, None)
            uri = res.properties.get(self._manager._uri_prop, None)
            self.update(name, uri)

    def update(self, name, uri):
        """
        Update or create the entry for the specified resource name in the
        Name-URI cache, and set it to the specified URI.

        If the specified name is `None` or the empty string, do nothing.
        """
        if name:
            self._uris[name] = uri

    def delete(self, name):
        """
        Delete the entry for the specified resource name from the Name-URI
        cache.

        If the specified name is `None` or the empty string, or if an entry for
        the specified name does not exist, do nothing.
        """
        if name:
            try:
                del self._uris[name]
            except KeyError:
                pass


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

    def __init__(self, resource_class, class_name, session, parent, base_uri,
                 oid_prop, uri_prop, name_prop, query_props,
                 list_has_name=True):
        # This method intentionally has no docstring, because it is internal.
        #
        # Parameters:
        #   resource_class (class):
        #     Python class for the resources of this manager.
        #     Must not be `None`.
        #   class_name (string):
        #     Resource class name (e.g. 'cpc' for a CPC resource). Must
        #     be the value of the 'class' property of the resource.
        #     Must not be `None`.
        #   session (:class:`~zhmcclient.Session`):
        #     Session for this manager.
        #     Must not be `None`.
        #   parent (subclass of :class:`~zhmcclient.BaseResource`):
        #     Parent resource defining the scope for this manager.
        #     `None`, if the manager has no parent, i.e. when it manages
        #     top-level resources (e.g. CPC).
        #   base_uri (string):
        #     Base URI of the resources of this manager. The base URI has no
        #     trailing slash and becomes the resource URI by appending '/' and
        #     the value of the property specified in 'oid_prop'.
        #     Must not be `None`.
        #   oid_prop (string):
        #     Name of the resource property whose value is appended to the
        #     base URI to form the resource URI (e.g. 'object-id' or
        #     'element-id').
        #     Must not be `None`.
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
        #     May be `None`.
        #     If the support for a resource property changes within the set of
        #     HMC versions that support this type of resource, this list must
        #     represent the version of the HMC this session is connected to.
        #   list_has_name (bool):
        #     Indicates whether the list() method for the resource populates
        #     the name property (i.e. name_prop). For example, for NICs the
        #     list() method returns minimalistic Nic objects without name.

        # We want to surface precondition violations as early as possible,
        # so we test those that are not surfaced through the init code:
        assert resource_class is not None
        assert class_name is not None
        assert session is not None
        assert base_uri is not None
        assert oid_prop is not None
        assert uri_prop is not None
        assert name_prop is not None

        self._resource_class = resource_class
        self._class_name = class_name
        self._session = session
        self._parent = parent
        self._base_uri = base_uri
        self._oid_prop = oid_prop
        self._uri_prop = uri_prop
        self._name_prop = name_prop
        self._query_props = query_props
        self._list_has_name = list_has_name

        self._name_uri_cache = _NameUriCache(
            self, session.retry_timeout_config.name_uri_cache_timetolive)

    def __repr__(self):
        """
        Return a string with the state of this manager object, for debug
        purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _resource_class={_resource_class!r},\n"
            "  _class_name={_class_name!r},\n"
            "  _session={_session_classname} at 0x{_session_id:08x},\n"
            "  _parent={_parent_classname} at 0x{_parent_id:08x},\n"
            "  _base_uri={_base_uri!r},\n"
            "  _oid_prop={_oid_prop!r},\n"
            "  _uri_prop={_uri_prop!r},\n"
            "  _name_prop={_name_prop!r},\n"
            "  _query_props={_query_props},\n"
            "  _list_has_name={_list_has_name!r},\n"
            "  _name_uri_cache={_name_uri_cache!r}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                _resource_class=self._resource_class,
                _class_name=self._class_name,
                _session_classname=self._session.__class__.__name__,
                _session_id=id(self._session),
                _parent_classname=self._parent.__class__.__name__,
                _parent_id=id(self._parent),
                _base_uri=self._base_uri,
                _oid_prop=self._oid_prop,
                _uri_prop=self._uri_prop,
                _name_prop=self._name_prop,
                _query_props=repr_list(self._query_props, indent=2),
                _list_has_name=self._list_has_name,
                _name_uri_cache=self._name_uri_cache,
            ))
        return ret

    def invalidate_cache(self):
        """
        Invalidate the Name-URI cache of this manager.

        The zhmcclient maintains a Name-URI cache in each manager object, which
        caches the mappings between resource URIs and resource names, to speed
        up certain zhmcclient methods.

        The Name-URI cache is properly updated during changes on the resource
        name (e.g. via :meth:`~zhmcclient.Partition.update_properties`) or
        changes on the resource URI (e.g. via resource creation or deletion),
        if these changes are performed through the same Python manager object.

        However, changes performed through a different manager object (e.g.
        because a different session, client or parent resource object was
        used), or changes performed in a different Python process, or changes
        performed via other means than the zhmcclient library (e.g. directly on
        the HMC) will not automatically update the Name-URI cache of this
        manager.

        In cases where the resource name or resource URI are effected by such
        changes, the Name-URI cache can be manually invalidated by the user,
        using this method.

        Note that the Name-URI cache automatically invalidates itself after a
        certain time since the last invalidation. That auto invalidation time
        can be configured using the
        :attr:`~zhmcclient.RetryTimeoutConfig.name_uri_cache_timetolive`
        attribute of the :class:`~zhmcclient.RetryTimeoutConfig` class.
        """
        self._name_uri_cache.invalidate()

    def _try_optimized_lookup(self, filter_args):
        """
        Try to optimize the lookup by checking whether the filter arguments
        specify the property that is used as the last segment in the resource
        URI, with a plain string as match value (i.e. not using regular
        expression matching).

        If so, the lookup is performed by constructing the resource URI from
        the specified filter argument, and by issuing a Get Properties
        operation on that URI, returning a single resource object.

        Parameters:

          filter_args (dict):
            Filter arguments. For details, see :ref:`Filtering`.

        Returns:

          resource object, or `None` if the optimization was not possible.
        """
        if filter_args is None or len(filter_args) != 1 or \
                self._oid_prop not in filter_args:
            return None

        oid_match = filter_args[self._oid_prop]
        if not isinstance(oid_match, six.string_types) or \
                not re.match(r'^[a-zA-Z0-9_\-]+$', oid_match):
            return None

        # The match string is a plain string (not a reg.expression)

        # Construct the resource URI from the filter property
        # and issue a Get <Resource> Properties on that URI
        uri = self._base_uri + '/' + oid_match

        try:
            props = self.session.get(uri)
        except HTTPError as exc:
            if exc.http_status == 404 and exc.reason == 1:
                # No such resource
                return None
            raise

        resource_obj = self.resource_class(
            manager=self,
            uri=props[self._uri_prop],
            name=props.get(self._name_prop, None),
            properties=props)

        resource_obj._full_properties = True

        return resource_obj

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
        """
        Return a boolean indicating whether a resource object matches with
        a single property against a property match value.
        This is used for client-side filtering.

        Depending on the specified property, this method retrieves the resource
        properties from the HMC.

        Parameters:

          obj (BaseResource):
            Resource object.

          prop_match:
            Property match value that is used to match the actual value of
            the specified property against, as follows:

            - If the match value is a list or tuple, this method is invoked
              recursively to find whether one or more match values inthe list
              match.

            - Else if the property is of string type, its value is matched by
              interpreting the match value as a regular expression.

            - Else the property value is matched by exact value comparison
              with the match value.

        Returns:

          bool: Boolean indicating whether the resource object matches w.r.t.
            the specified property and the match value.
        """
        if isinstance(prop_match, (list, tuple)):
            # List items are logically ORed, so one matching item suffices.
            for pm in prop_match:
                if self._matches_prop(obj, prop_name, pm):
                    return True
        else:
            # Some lists of resources do not have all properties, for example
            # Hipersocket adapters do not have a "card-location" property.
            # If a filter property does not exist on a resource, the resource
            # does not match.
            try:
                prop_value = obj.get_property(prop_name)
            except KeyError:
                return False
            if isinstance(prop_value, six.string_types):
                # HMC resource property is Enum String or (non-enum) String,
                # and is both matched by regexp matching. Ideally, regexp
                # matching should only be done for non-enum strings, but
                # distinguishing them is not possible given that the client
                # has no knowledge about the properties.

                # The regexp matching implemented in the HMC requires begin and
                # end of the string value to match, even if the '^' for begin
                # and '$' for end are not specified in the pattern. The code
                # here is consistent with that: We add end matching to the
                # pattern, and begin matching is done by re.match()
                # automatically.
                re_match = prop_match + '$'
                m = re.match(re_match, prop_value)
                if m:
                    return True
            else:
                if prop_value == prop_match:
                    return True
        return False

    @property
    def resource_class(self):
        """
        The Python class of the parent resource of this manager.
        """
        return self._resource_class

    @property
    def class_name(self):
        """
        The resource class name
        """
        return self._class_name

    @property
    def session(self):
        """
        :class:`~zhmcclient.Session`:
          Session with the HMC.
        """
        assert self._session is not None, \
            "%s.session: No session set (in top-level resource manager " \
            "class?)" % self.__class__.__name__
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

    def resource_object(self, uri_or_oid, props=None):
        """
        Return a minimalistic Python resource object for this resource class,
        that is scoped to this manager.

        This method is an internal helper function and is not normally called
        by users.

        The returned resource object will have the following minimal set of
        properties set automatically:

          * `object-uri`
          * `object-id`
          * `parent`
          * `class`

        Additional properties for the Python resource object can be specified
        by the caller.

        Parameters:

            uri_or_oid (string): `object-uri` or `object-id` of the resource.

            props (dict): Property values in addition to the minimal list of
              properties that are set automatically (see above).

        Returns:

            Subclass of :class:`~zhmcclient.BaseResource`: A Python resource
            object for this resource class.
        """
        if uri_or_oid.startswith('/api/'):
            assert uri_or_oid[-1] != '/'
            uri = uri_or_oid
            oid = uri.split('/')[-1]
        else:
            assert '/' not in uri_or_oid
            oid = uri_or_oid
            uri = '{}/{}'.format(self._base_uri, oid)
        res_props = {
            self._oid_prop: oid,
            'parent': self.parent.uri if self.parent is not None else None,
            'class': self.class_name,
        }
        name = None
        if props:
            res_props.update(props)
            try:
                name = props[self._name_prop]
            except KeyError:
                pass
        return self.resource_class(self, uri, name, res_props)

    @logged_api_call
    def findall(self, **filter_args):
        """
        Find zero or more resources in scope of this manager, by matching
        resource properties against the specified filter arguments, and return
        a list of their Python resource objects (e.g. for CPCs, a list of
        :class:`~zhmcclient.Cpc` objects is returned).

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The zhmcclient implementation handles the specified properties in an
        optimized way: Properties that can be filtered on the HMC are actually
        filtered there (this varies by resource type), and the remaining
        properties are filtered on the client side.

        If the "name" property is specified as the only filter argument, an
        optimized lookup is performed that uses a name-to-URI cache in this
        manager object. This this optimized lookup uses the specified match
        value for exact matching and is not interpreted as a regular
        expression.

        Authorization requirements:

        * see the `list()` method in the derived classes.

        Parameters:

          \\**filter_args:
            All keyword arguments are used as filter arguments. Specifying no
            keyword arguments causes no filtering to happen. See the examples
            for usage details.

        Returns:

          List of resource objects in scope of this manager object that match
          the filter arguments. These resource objects have a minimal set of
          properties.

        Raises:

          : Exceptions raised by the `list()` methods in derived resource
            manager classes (see :ref:`Resources`).

        Examples:

        * The following example finds partitions in a CPC by status. Because
          the 'status' resource property is also a valid Python variable name,
          there are two ways for the caller to specify the filter arguments for
          this method:

          As named parameters::

              run_states = ['active', 'degraded']
              run_parts = cpc.partitions.find(status=run_states)

          As a parameter dictionary::

              run_parts = cpc.partitions.find(**{'status': run_states})

        * The following example finds adapters of the OSA family in a CPC
          with an active status. Because the resource property for the adapter
          family is named 'adapter-family', it is not suitable as a Python
          variable name. Therefore, the caller can specify the filter argument
          only as a parameter dictionary::

              filter_args = {'adapter-family': 'osa', 'status': 'active'}
              active_osa_adapters = cpc.adapters.findall(**filter_args)
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

    @logged_api_call
    def find(self, **filter_args):
        """
        Find exactly one resource in scope of this manager, by matching
        resource properties against the specified filter arguments, and return
        its Python resource object (e.g. for a CPC, a :class:`~zhmcclient.Cpc`
        object is returned).

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The zhmcclient implementation handles the specified properties in an
        optimized way: Properties that can be filtered on the HMC are actually
        filtered there (this varies by resource type), and the remaining
        properties are filtered on the client side.

        If the "name" property is specified as the only filter argument, an
        optimized lookup is performed that uses a name-to-URI cache in this
        manager object. This this optimized lookup uses the specified match
        value for exact matching and is not interpreted as a regular
        expression.

        Authorization requirements:

        * see the `list()` method in the derived classes.

        Parameters:

          \\**filter_args:
            All keyword arguments are used as filter arguments. Specifying no
            keyword arguments causes no filtering to happen. See the examples
            for usage details.

        Returns:

          Resource object in scope of this manager object that matches the
          filter arguments. This resource object has a minimal set of
          properties.

        Raises:

          :exc:`~zhmcclient.NotFound`: No matching resource found.
          :exc:`~zhmcclient.NoUniqueMatch`: More than one matching resource
            found.
          : Exceptions raised by the `list()` methods in derived resource
            manager classes (see :ref:`Resources`).

        Examples:

        * The following example finds a CPC by its name. Because the 'name'
          resource property is also a valid Python variable name, there are
          two ways for the caller to specify the filter arguments for this
          method:

          As named parameters::

              cpc = client.cpcs.find(name='CPC001')

          As a parameter dictionary::

              filter_args = {'name': 'CPC0001'}
              cpc = client.cpcs.find(**filter_args)

        * The following example finds a CPC by its object ID. Because the
          'object-id' resource property is not a valid Python variable name,
          the caller can specify the filter argument only as a parameter
          dictionary::

              filter_args = {'object-id': '12345-abc...de-12345'}
              cpc = client.cpcs.find(**filter_args)
        """
        obj_list = self.findall(**filter_args)
        num_objs = len(obj_list)
        if num_objs == 0:
            raise NotFound(filter_args, self)
        elif num_objs > 1:
            raise NoUniqueMatch(filter_args, self, obj_list)
        else:
            return obj_list[0]

    def list(self, full_properties=False, filter_args=None):
        """
        Find zero or more resources in scope of this manager, by matching
        resource properties against the specified filter arguments, and return
        a list of their Python resource objects (e.g. for CPCs, a list of
        :class:`~zhmcclient.Cpc` objects is returned).

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The zhmcclient implementation handles the specified properties in an
        optimized way: Properties that can be filtered on the HMC are actually
        filtered there (this varies by resource type), and the remaining
        properties are filtered on the client side.

        At the level of the :class:`~zhmcclient.BaseManager` class, this method
        defines the interface for the `list()` methods implemented in the
        derived resource classes.

        Authorization requirements:

        * see the `list()` method in the derived classes.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only a minimal set as returned by the list
            operation.

          filter_args (dict):
            Filter arguments. `None` causes no filtering to happen. See the
            examples for usage details.

        Returns:

          List of resource objects in scope of this manager object that match
          the filter arguments. These resource objects have a set of properties
          according to the `full_properties` parameter.

        Raises:

          : Exceptions raised by the `list()` methods in derived resource
            manager classes (see :ref:`Resources`).

        Examples:

        * The following example finds those OSA adapters in cage '1234' of a
          given CPC, whose state is 'stand-by', 'reserved', or 'unknown'::

              filter_args = {
                  'adapter-family': 'osa',
                  'card-location': '1234-.*',
                  'state': ['stand-by', 'reserved', 'unknown'],
              }
              osa_adapters = cpc.adapters.list(full_properties=True,
                                               filter_args=filter_args)

          The returned resource objects will have the full set of properties.
        """
        raise NotImplementedError

    @logged_api_call
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
            Regular expression matching is not supported for the name for this
            optimized lookup.

        Returns:

          Resource object in scope of this manager object that matches the
          filter arguments. This resource object has a minimal set of
          properties.

        Raises:

          :exc:`~zhmcclient.NotFound`: No matching resource found.
          : Exceptions raised by the `list()` methods in derived resource
            manager classes (see :ref:`Resources`).

        Examples:

        * The following example finds a CPC by its name::

              cpc = client.cpcs.find_by_name('CPC001')
        """
        uri = self._name_uri_cache.get(name)
        obj = self.resource_class(
            manager=self,
            uri=uri,
            name=name,
            properties=None)
        return obj

    @logged_api_call
    def flush(self):
        """
        Invalidate the Name-URI cache of this manager.

        **Deprecated:** This method is deprecated and using it will cause a
        :exc:`~py:exceptions.DeprecationWarning` to be issued. Use
        :meth:`~zhmcclient.BaseManager.invalidate_cache` instead.
        """
        warnings.warn(
            "Use of flush() on zhmcclient manager objects is deprecated; "
            "use invalidate_cache() instead", DeprecationWarning)
        self.invalidate_cache()
