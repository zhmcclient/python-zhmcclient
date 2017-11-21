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
The `zhmcclient_mock` package provides a faked HMC with all resources that are
relevant for the `zhmcclient` package. The faked HMC is implemented as a
local Python object and maintains its resource state across operations.
"""

from __future__ import absolute_import

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import six
import re
import copy

from ._idpool import IdPool
from zhmcclient._utils import repr_dict, repr_manager, repr_list, \
    timestamp_from_datetime

__all__ = ['InputError', 'FakedBaseResource', 'FakedBaseManager', 'FakedHmc',
           'FakedConsoleManager', 'FakedConsole',
           'FakedUserManager', 'FakedUser',
           'FakedUserRoleManager', 'FakedUserRole',
           'FakedUserPatternManager', 'FakedUserPattern',
           'FakedPasswordRuleManager', 'FakedPasswordRule',
           'FakedTaskManager', 'FakedTask',
           'FakedLdapServerDefinitionManager', 'FakedLdapServerDefinition',
           'FakedActivationProfileManager', 'FakedActivationProfile',
           'FakedAdapterManager', 'FakedAdapter',
           'FakedCpcManager', 'FakedCpc',
           'FakedUnmanagedCpcManager', 'FakedUnmanagedCpc',
           'FakedHbaManager', 'FakedHba',
           'FakedLparManager', 'FakedLpar',
           'FakedNicManager', 'FakedNic',
           'FakedPartitionManager', 'FakedPartition',
           'FakedPortManager', 'FakedPort',
           'FakedVirtualFunctionManager', 'FakedVirtualFunction',
           'FakedVirtualSwitchManager', 'FakedVirtualSwitch',
           'FakedStorageGroupManager', 'FakedStorageGroup',
           'FakedMetricsContextManager', 'FakedMetricsContext',
           'FakedMetricGroupDefinition', 'FakedMetricObjectValues',
           ]


class InputError(Exception):
    """
    An error that is raised by the faked resource classes and indicates
    that the input is invalid in some way.

    ``args[0]`` will be set to a message detailing the issue.
    """

    def __init__(self, message):
        super(InputError, self).__init__(message)


class FakedBaseResource(object):
    """
    A base class for faked resource classes in the faked HMC.
    """

    def __init__(self, manager, properties):
        self._manager = manager  # May be None
        if properties is not None:
            self._properties = copy.deepcopy(properties)
        else:
            self._properties = {}

        if self.manager:

            if self.manager.oid_prop is None:
                self._oid = None
            else:
                if self.manager.oid_prop not in self.properties:
                    new_oid = self.manager._new_oid()
                    self.properties[self.manager.oid_prop] = new_oid
                self._oid = self.properties[self.manager.oid_prop]

            if self.manager.uri_prop not in self.properties:
                new_uri = self.manager.base_uri
                if self.oid is not None:
                    new_uri += '/' + self.oid
                self.properties[self.manager.uri_prop] = new_uri
            self._uri = self.properties[self.manager.uri_prop]

            if self.manager.class_value:
                if 'class' not in self.properties:
                    self.properties['class'] = self.manager.class_value

            if self.manager.parent:
                if 'parent' not in self.properties:
                    self.properties['parent'] = self.manager.parent.uri

        else:
            self._oid = None
            self._uri = None

    def __repr__(self):
        """
        Return a string with the state of this faked resource, for debug
        purposes.

        Note that the derived faked resource classes that have child resources
        have their own __repr__() methods, because only they know which child
        resources they have.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _manager = {_manager_classname} at 0x{_manager_id:08x}\n"
            "  _oid = {_oid!r}\n"
            "  _uri = {_uri!r}\n"
            "  _properties = {_properties}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                _manager_classname=self._manager.__class__.__name__,
                _manager_id=id(self._manager),
                _oid=self._oid,
                _uri=self._uri,
                _properties=repr_dict(self.properties, indent=2),
            ))
        return ret

    @property
    def manager(self):
        """
        The manager for this resource (a derived class of
        :class:`~zhmcclient_mock.FakedBaseManager`).
        """
        return self._manager

    @property
    def properties(self):
        """
        The properties of this resource (a dictionary).
        """
        return self._properties

    @property
    def oid(self):
        """
        The object ID (property 'object-id' or 'element-id') of this resource.
        """
        return self._oid

    @property
    def uri(self):
        """
        The object URI (property 'object-uri' or 'element-uri') of this
        resource.
        """
        return self._uri

    @property
    def name(self):
        """
        The name (property 'name') of this resource.

        Raises:

          :exc:`KeyError`: Resource does not have a 'name' property.
        """
        return self._properties['name']

    def update(self, properties):
        """
        update the properties of this resource.

        Parameters:

          properties (dict):
            Resource properties to be updated. Any other properties remain
            unchanged.
        """
        self.properties.update(properties)

    def add_resources(self, resources):
        """
        Add faked child resources to this resource, from the provided resource
        definitions.

        Duplicate resource names in the same scope are not permitted.

        Although this method is typically used to initially load the faked
        HMC with resource state just once, it can be invoked multiple times
        and can also be invoked on faked resources (e.g. on a faked CPC).

        Parameters:

          resources (dict):
            resource dictionary with definitions of faked child resources to be
            added. For an explanation of how the resource dictionary is set up,
            see the examples below.

            For requirements on and auto-generation of certain resource
            properties, see the ``add()`` methods of the various faked resource
            managers (e.g. :meth:`zhmcclient_mock.FakedCpcManager.add`). For
            example, the object-id or element-id properties and the
            corresponding uri properties are always auto-generated.

            The resource dictionary specifies a tree of resource managers and
            resources, in an alternating manner. It starts with the resource
            managers of child resources of the target resource, which contains
            a list of those child resources. For an HMC, the CPCs managed by
            the HMC would be its child resources.

            Each resource specifies its own properties (``properties`` key)
            and the resource managers for its child resources. For example, the
            CPC resource specifies its adapter child resources using the
            ``adapters`` key. The keys for the child resource managers are the
            attribute names of these resource managers in the parent resource.
            For example, the ``adapters`` key is named after the
            :attr:`zhmcclient.Cpc.adapters` attribute (which has the same name
            as in its corresponding faked CPC resource:
            :attr:`zhmcclient_mock.FakedCpc.adapters`).

        Raises:

          :exc:`zhmcclient_mock.InputError`: Some issue with the input
            resources.

        Examples:

          Example for targeting a faked HMC for adding a CPC with one adapter::

              resources = {
                  'cpcs': [  # name of manager attribute for this resource
                      {
                          'properties': {
                              'name': 'cpc_1',
                          },
                          'adapters': [  # name of manager attribute for this
                                         # resource
                              {
                                  'properties': {
                                      'object-id': '12',
                                      'name': 'ad_1',
                                  },
                                  'ports': [
                                      {
                                          'properties': {
                                              'name': 'port_1',
                                          }
                                      },
                                  ],
                              },
                          ],
                      },
                  ],
              }

          Example for targeting a faked CPC for adding an LPAR and a load
          activation profile::

              resources = {
                  'lpars': [  # name of manager attribute for this resource
                      {
                          'properties': {
                              # object-id is not provided -> auto-generated
                              # object-uri is not provided -> auto-generated
                              'name': 'lpar_1',
                          },
                      },
                  ],
                  'load_activation_profiles': [  # name of manager attribute
                      {
                          'properties': {
                              # object-id is not provided -> auto-generated
                              # object-uri is not provided -> auto-generated
                              'name': 'lpar_1',
                          },
                      },
                  ],
              }

        """
        for child_attr in resources:
            child_list = resources[child_attr]
            self._process_child_list(self, child_attr, child_list)

    def _process_child_list(self, parent_resource, child_attr, child_list):
        child_manager = getattr(parent_resource, child_attr, None)
        if child_manager is None:
            raise InputError("Invalid child resource type specified in "
                             "resource dictionary: {}".format(child_attr))
        for child_dict in child_list:
            # child_dict is a dict of 'properties' and grand child resources
            properties = child_dict.get('properties', None)
            if properties is None:
                raise InputError("A resource for resource type {} has no"
                                 "properties specified.".format(child_attr))
            child_resource = child_manager.add(properties)
            for grandchild_attr in child_dict:
                if grandchild_attr == 'properties':
                    continue
                grandchild_list = child_dict[grandchild_attr]
                self._process_child_list(child_resource, grandchild_attr,
                                         grandchild_list)


class FakedBaseManager(object):
    """
    A base class for manager classes for faked resources in the faked HMC.
    """

    api_root = '/api'  # root of all resource URIs
    next_oid = 1  # next object ID, for auto-generating them

    def __init__(self, hmc, parent, resource_class, base_uri, oid_prop,
                 uri_prop, class_value):
        self._hmc = hmc
        self._parent = parent
        self._resource_class = resource_class
        self._base_uri = base_uri  # Base URI for resources of this type
        self._oid_prop = oid_prop
        self._uri_prop = uri_prop
        self._class_value = class_value

        # List of Faked{Resource} objects in this faked manager, by object ID
        self._resources = OrderedDict()

    def __repr__(self):
        """
        Return a string with the state of this faked manager, for debug
        purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _hmc = {_hmc_classname} at 0x{_hmc_id:08x}\n"
            "  _parent = {_parent_classname} at 0x{_parent_id:08x}\n"
            "  _resource_class = {_resource_class!r}\n"
            "  _base_uri = {_base_uri!r}\n"
            "  _oid_prop = {_oid_prop!r}\n"
            "  _uri_prop = {_uri_prop!r}\n"
            "  _class_value = {_class_value!r}\n"
            "  _resources = {_resources}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                _hmc_classname=self._hmc.__class__.__name__,
                _hmc_id=id(self._hmc),
                _parent_classname=self._parent.__class__.__name__,
                _parent_id=id(self._parent),
                _resource_class=self._resource_class,
                _base_uri=self._base_uri,
                _oid_prop=self._oid_prop,
                _uri_prop=self._uri_prop,
                _class_value=self._class_value,
                _resources=repr_dict(self._resources, indent=2),
            ))
        return ret

    def _matches_filters(self, obj, filter_args):
        """
        Return a boolean indicating whether a faked resource object matches a
        set of filter arguments.
        This is used for implementing filtering in the faked resource managers.

        Parameters:

          obj (FakedBaseResource):
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
        Return a boolean indicating whether a faked resource object matches
        with a single property against a property match value.
        This is used for implementing filtering in the faked resource managers.

        Parameters:

          obj (FakedBaseResource):
            Resource object.

          prop_match:
            Property match value that is used to match the actual value of
            the specified property against, as follows:

            - If the match value is a list or tuple, this method is invoked
              recursively to find whether one or more match values in the list
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
            if prop_name not in obj.properties:
                return False
            prop_value = obj.properties[prop_name]
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
    def hmc(self):
        """
        The faked HMC this manager is part of (an object of
        :class:`~zhmcclient_mock.FakedHmc`).
        """
        return self._hmc

    @property
    def parent(self):
        """
        The parent (scoping resource) for this manager (an object of a derived
        class of :class:`~zhmcclient_mock.FakedBaseResource`).
        """
        return self._parent

    @property
    def resource_class(self):
        """
        The resource class managed by this manager (a derived class of
        :class:`~zhmcclient_mock.FakedBaseResource`).
        """
        return self._resource_class

    @property
    def base_uri(self):
        """
        The base URI for URIs of resources managed by this manager.
        """
        return self._base_uri

    @property
    def oid_prop(self):
        """
        The name of the resource property for the object ID ('object-id' or
        'element-id' or 'name').
        """
        return self._oid_prop

    @property
    def uri_prop(self):
        """
        The name of the resource property for the object URI ('object-uri' or
        'element-uri').
        """
        return self._uri_prop

    @property
    def class_value(self):
        """
        The value for the "class" property of resources managed by this
        manager, as defined in the data model for the resource.
        For example, for LPAR resources this is set to 'logical-partition'.
        """
        return self._class_value

    def _new_oid(self):
        new_oid = self.next_oid
        self.next_oid += 1
        return str(new_oid)

    def add(self, properties):
        """
        Add a faked resource to this manager.

        For URI-based lookup, the resource is also added to the faked HMC.

        Parameters:

          properties (dict):
            Resource properties. If the URI property (e.g. 'object-uri') or the
            object ID property (e.g. 'object-id') are not specified, they
            will be auto-generated.

        Returns:
          FakedBaseResource: The faked resource object.
        """
        resource = self.resource_class(self, properties)
        self._resources[resource.oid] = resource
        self._hmc.all_resources[resource.uri] = resource
        return resource

    def remove(self, oid):
        """
        Remove a faked resource from this manager.

        Parameters:

          oid (string):
            The object ID of the resource (e.g. value of the 'object-uri'
            property).
        """
        uri = self._resources[oid].uri
        del self._resources[oid]
        del self._hmc.all_resources[uri]

    def list(self, filter_args=None):
        """
        List the faked resources of this manager.

        Parameters:

          filter_args (dict):
            Filter arguments. `None` causes no filtering to happen. See
            :meth:`~zhmcclient.BaseManager.list()` for details.

        Returns:
          list of FakedBaseResource: The faked resource objects of this
            manager.
        """
        res = list()
        for oid in self._resources:
            resource = self._resources[oid]
            if self._matches_filters(resource, filter_args):
                res.append(resource)
        return res

    def lookup_by_oid(self, oid):
        """
        Look up a faked resource by its object ID, in the scope of this
        manager.

        Parameters:

          oid (string):
            The object ID of the faked resource (e.g. value of the 'object-id'
            property).

        Returns:
          FakedBaseResource: The faked resource object.

        Raises:
          KeyError: No resource found for this object ID.
        """
        return self._resources[oid]


class FakedHmc(FakedBaseResource):
    """
    A faked HMC.

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.

    An object of this class represents a faked HMC that can have all faked
    resources that are relevant for the zhmcclient package.

    The Python API to this class and its child resource classes is not
    compatible with the zhmcclient API. Instead, these classes serve as an
    in-memory backend for a faked session class (see
    :class:`zhmcclient_mock.FakedSession`) that replaces the
    normal :class:`zhmcclient.Session` class.

    Objects of this class should not be created by the user. Instead,
    access the :attr:`zhmcclient_mock.FakedSession.hmc` attribute.
    """

    def __init__(self, hmc_name, hmc_version, api_version):
        super(FakedHmc, self).__init__(manager=None, properties=None)
        self.hmc_name = hmc_name
        self.hmc_version = hmc_version
        self.api_version = api_version
        self.cpcs = FakedCpcManager(hmc=self, client=self)
        self.metrics_contexts = FakedMetricsContextManager(
            hmc=self, client=self)
        self.consoles = FakedConsoleManager(hmc=self, client=self)

        # Flat list of all Faked{Resource} objs in this faked HMC, by URI:
        self.all_resources = {}

        self.enable()

    def __repr__(self):
        """
        Return a string with the state of this faked HMC, for debug purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  hmc_name = {hmc_name!r}\n"
            "  hmc_version = {hmc_version!r}\n"
            "  api_version = {api_version!r}\n"
            "  enabled = {enabled!r}\n"
            "  cpcs = {cpcs}\n"
            "  metrics_contexts = {metrics_contexts}\n"
            "  consoles = {consoles}\n"
            "  all_resources (keys only) = {all_resource_keys}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                hmc_name=self.hmc_name,
                hmc_version=self.hmc_version,
                api_version=self.api_version,
                enabled=self.enabled,
                cpcs=repr_manager(self.cpcs, indent=2),
                metrics_contexts=repr_manager(self.metrics_contexts, indent=2),
                consoles=repr_manager(self.consoles, indent=2),
                all_resource_keys=repr_list(self.all_resources.keys(),
                                            indent=2),
            ))
        return ret

    @property
    def enabled(self):
        """
        Return whether the faked HMC is enabled.
        """
        return self._enabled

    def enable(self):
        """
        Enable the faked HMC.
        """
        self._enabled = True

    def disable(self):
        """
        Disable the faked HMC. This will cause an error to be raised when
        a faked session attempts to communicate with the disabled HMC.
        """
        self._enabled = False

    def lookup_by_uri(self, uri):
        """
        Look up a faked resource by its object URI, within this faked HMC.

        Parameters:

          uri (string):
            The object URI of the faked resource (e.g. value of the
            'object-uri' property).

        Returns:
          :class:`~zhmcclient_mock.FakedBaseResource`: The faked resource.

        Raises:
          KeyError: No resource found for this object ID.
        """
        return self.all_resources[uri]


class FakedConsoleManager(FakedBaseManager):
    """
    A manager for faked Console resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, client):
        super(FakedConsoleManager, self).__init__(
            hmc=hmc,
            parent=client,
            resource_class=FakedConsole,
            base_uri=self.api_root + '/console',
            oid_prop=None,  # Console does not have an object ID property
            uri_prop='object-uri',
            class_value='console')
        self._console = None

    @property
    def console(self):
        """
        The faked Console representing the faked HMC (an object of
        :class:`~zhmcclient_mock.FakedConsole`). The object is cached.
        """
        if self._console is None:
            self._console = self.list()[0]
        return self._console

    def add(self, properties):
        """
        Add a faked Console resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-uri' will be auto-generated to '/api/console',
              if not specified.
            * 'class' will be auto-generated to 'console',
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedConsole`: The faked Console resource.
        """
        return super(FakedConsoleManager, self).add(properties)


class FakedConsole(FakedBaseResource):
    """
    A faked Console resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedConsole, self).__init__(
            manager=manager,
            properties=properties)
        self._storage_groups = FakedStorageGroupManager(
            hmc=manager.hmc, console=self)
        self._users = FakedUserManager(hmc=manager.hmc, console=self)
        self._user_roles = FakedUserRoleManager(hmc=manager.hmc, console=self)
        self._user_patterns = FakedUserPatternManager(
            hmc=manager.hmc, console=self)
        self._password_rules = FakedPasswordRuleManager(
            hmc=manager.hmc, console=self)
        self._tasks = FakedTaskManager(hmc=manager.hmc, console=self)
        self._ldap_server_definitions = FakedLdapServerDefinitionManager(
            hmc=manager.hmc, console=self)
        self._unmanaged_cpcs = FakedUnmanagedCpcManager(
            hmc=manager.hmc, console=self)

    def __repr__(self):
        """
        Return a string with the state of this faked Console resource, for
        debug purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _manager = {manager_classname} at 0x{manager_id:08x}\n"
            "  _manager._parent._uri = {parent_uri!r}\n"
            "  _uri = {_uri!r}\n"
            "  _properties = {_properties}\n"
            "  _storage_groups = {_storage_groups}\n"
            "  _users = {_users}\n"
            "  _user_roles = {_user_roles}\n"
            "  _user_patterns = {_user_patterns}\n"
            "  _password_rules = {_password_rules}\n"
            "  _tasks = {_tasks}\n"
            "  _ldap_server_definitions = {_ldap_server_definitions}\n"
            "  _unmanaged_cpcs = {_unmanaged_cpcs}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                manager_classname=self._manager.__class__.__name__,
                manager_id=id(self._manager),
                parent_uri=self._manager.parent.uri,
                _uri=self._uri,
                _properties=repr_dict(self.properties, indent=2),
                _storage_groups=repr_manager(self.storage_groups, indent=2),
                _users=repr_manager(self.users, indent=2),
                _user_roles=repr_manager(self.user_roles, indent=2),
                _user_patterns=repr_manager(self.user_patterns, indent=2),
                _password_rules=repr_manager(self.password_rules, indent=2),
                _tasks=repr_manager(self.tasks, indent=2),
                _ldap_server_definitions=repr_manager(
                    self.ldap_server_definitions, indent=2),
                _unmanaged_cpcs=repr_manager(self.unmanaged_cpcs, indent=2),
            ))
        return ret

    @property
    def storage_groups(self):
        """
        :class:`~zhmcclient_mock.FakedStorageGroupManager`: Access to the faked
        Storage Group resources of this Console.
        """
        return self._storage_groups

    @property
    def users(self):
        """
        :class:`~zhmcclient_mock.FakedUserManager`: Access to the faked User
        resources of this Console.
        """
        return self._users

    @property
    def user_roles(self):
        """
        :class:`~zhmcclient_mock.FakedUserRoleManager`: Access to the faked
        User Role resources of this Console.
        """
        return self._user_roles

    @property
    def user_patterns(self):
        """
        :class:`~zhmcclient_mock.FakedUserPatternManager`: Access to the faked
        User Pattern resources of this Console.
        """
        return self._user_patterns

    @property
    def password_rules(self):
        """
        :class:`~zhmcclient_mock.FakedPasswordRulesManager`: Access to the
        faked Password Rule resources of this Console.
        """
        return self._password_rules

    @property
    def tasks(self):
        """
        :class:`~zhmcclient_mock.FakedTaskManager`: Access to the faked Task
        resources of this Console.
        """
        return self._tasks

    @property
    def ldap_server_definitions(self):
        """
        :class:`~zhmcclient_mock.FakedLdapServerDefinitionManager`: Access to
        the faked LDAP Server Definition resources of this Console.
        """
        return self._ldap_server_definitions

    @property
    def unmanaged_cpcs(self):
        """
        :class:`~zhmcclient_mock.FakedUnmanagedCpcManager`: Access to the faked
        unmanaged CPC resources of this Console.
        """
        return self._unmanaged_cpcs


class FakedUserManager(FakedBaseManager):
    """
    A manager for faked User resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, console):
        super(FakedUserManager, self).__init__(
            hmc=hmc,
            parent=console,
            resource_class=FakedUser,
            base_uri=self.api_root + '/users',
            oid_prop='object-id',
            uri_prop='object-uri',
            class_value='user')

    def add(self, properties):
        """
        Add a faked User resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'class' will be auto-generated to 'user',
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedUser`: The faked User resource.
        """
        return super(FakedUserManager, self).add(properties)


class FakedUser(FakedBaseResource):
    """
    A faked User resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedUser, self).__init__(
            manager=manager,
            properties=properties)


class FakedUserRoleManager(FakedBaseManager):
    """
    A manager for faked User Role resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, console):
        super(FakedUserRoleManager, self).__init__(
            hmc=hmc,
            parent=console,
            resource_class=FakedUserRole,
            base_uri=self.api_root + '/user-roles',
            oid_prop='object-id',
            uri_prop='object-uri',
            class_value='user-role')

    def add(self, properties):
        """
        Add a faked User Role resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'class' will be auto-generated to 'user-role',
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedUserRole`: The faked User Role
          resource.
        """
        return super(FakedUserRoleManager, self).add(properties)


class FakedUserRole(FakedBaseResource):
    """
    A faked User Role resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedUserRole, self).__init__(
            manager=manager,
            properties=properties)


class FakedUserPatternManager(FakedBaseManager):
    """
    A manager for faked User Pattern resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, console):
        super(FakedUserPatternManager, self).__init__(
            hmc=hmc,
            parent=console,
            resource_class=FakedUserPattern,
            base_uri=self.api_root + '/console/user-patterns',
            oid_prop='element-id',
            uri_prop='element-uri',
            class_value='user-pattern')

    def add(self, properties):
        """
        Add a faked User Pattern resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'class' will be auto-generated to 'user-pattern',
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedUserPattern`: The faked User Pattern
          resource.
        """
        return super(FakedUserPatternManager, self).add(properties)


class FakedUserPattern(FakedBaseResource):
    """
    A faked User Pattern resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedUserPattern, self).__init__(
            manager=manager,
            properties=properties)


class FakedPasswordRuleManager(FakedBaseManager):
    """
    A manager for faked Password Rule resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, console):
        super(FakedPasswordRuleManager, self).__init__(
            hmc=hmc,
            parent=console,
            resource_class=FakedPasswordRule,
            base_uri=self.api_root + '/console/password-rules',
            oid_prop='element-id',
            uri_prop='element-uri',
            class_value='password-rule')

    def add(self, properties):
        """
        Add a faked Password Rule resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'class' will be auto-generated to 'password-rule',
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedPasswordRule`: The faked Password Rule
          resource.
        """
        return super(FakedPasswordRuleManager, self).add(properties)


class FakedPasswordRule(FakedBaseResource):
    """
    A faked Password Rule resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedPasswordRule, self).__init__(
            manager=manager,
            properties=properties)


class FakedTaskManager(FakedBaseManager):
    """
    A manager for faked Task resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, console):
        super(FakedTaskManager, self).__init__(
            hmc=hmc,
            parent=console,
            resource_class=FakedTask,
            base_uri=self.api_root + '/console/tasks',
            oid_prop='element-id',
            uri_prop='element-uri',
            class_value='task')

    def add(self, properties):
        """
        Add a faked Task resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'class' will be auto-generated to 'task',
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedTask`: The faked Task resource.
        """
        return super(FakedTaskManager, self).add(properties)


class FakedTask(FakedBaseResource):
    """
    A faked Task resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedTask, self).__init__(
            manager=manager,
            properties=properties)


class FakedLdapServerDefinitionManager(FakedBaseManager):
    """
    A manager for faked LDAP Server Definition resources within a faked HMC
    (see :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, console):
        super(FakedLdapServerDefinitionManager, self).__init__(
            hmc=hmc,
            parent=console,
            resource_class=FakedLdapServerDefinition,
            base_uri=self.api_root + '/console/ldap-server-definitions',
            oid_prop='element-id',
            uri_prop='element-uri',
            class_value='ldap-server-definition')

    def add(self, properties):
        """
        Add a faked LDAP Server Definition resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'class' will be auto-generated to 'ldap-server-definition',
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedLdapServerDefinition`: The faked
          LdapServerDefinition resource.
        """
        return super(FakedLdapServerDefinitionManager, self).add(properties)


class FakedLdapServerDefinition(FakedBaseResource):
    """
    A faked LDAP Server Definition resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedLdapServerDefinition, self).__init__(
            manager=manager,
            properties=properties)


class FakedActivationProfileManager(FakedBaseManager):
    """
    A manager for faked Activation Profile resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, cpc, profile_type):
        ap_uri_segment = profile_type + '-activation-profiles'
        ap_class_value = profile_type + '-activation-profile'
        super(FakedActivationProfileManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedActivationProfile,
            base_uri=cpc.uri + '/' + ap_uri_segment,
            oid_prop='name',  # This is an exception!
            uri_prop='element-uri',
            class_value=ap_class_value)
        self._profile_type = profile_type

    def add(self, properties):
        """
        Add a faked Activation Profile resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'name' (the OID property for this resource type!) will be
              auto-generated with a unique value across all instances of this
              resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the OID ('name')
              property, if not specified.
            * 'class' will be auto-generated to
              '{profile_type}'-activation-profile', if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedActivationProfile`: The faked
            Activation Profile resource.
        """
        return super(FakedActivationProfileManager, self).add(properties)

    @property
    def profile_type(self):
        """
        Type of the activation profile ('reset', 'image', 'load').
        """
        return self._profile_type


class FakedActivationProfile(FakedBaseResource):
    """
    A faked Activation Profile resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedActivationProfile, self).__init__(
            manager=manager,
            properties=properties)


class FakedAdapterManager(FakedBaseManager):
    """
    A manager for faked Adapter resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, cpc):
        super(FakedAdapterManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedAdapter,
            base_uri=self.api_root + '/adapters',
            oid_prop='object-id',
            uri_prop='object-uri',
            class_value='adapter')

    def add(self, properties):
        """
        Add a faked Adapter resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'class' will be auto-generated to 'adapter',
              if not specified.
            * 'status' is auto-set to 'active', if not specified.
            * 'adapter-family' or 'type' is required to be specified, in order
              to determine whether the adapter is a network or storage adapter.
            * 'adapter-family' is auto-set based upon 'type', if not specified.
            * For network adapters, 'network-port-uris' is auto-set to an empty
              list, if not specified.
            * For storage adapters, 'storage-port-uris' is auto-set to an empty
              list, if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedAdapter`: The faked Adapter resource.

        Raises:
          :exc:`zhmcclient_mock.InputError`: Some issue with the input
            properties.
        """
        return super(FakedAdapterManager, self).add(properties)


class FakedAdapter(FakedBaseResource):
    """
    A faked Adapter resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedAdapter, self).__init__(
            manager=manager,
            properties=properties)
        # TODO: Maybe move this stuff into AdapterManager.add()?
        if 'adapter-family' in self.properties:
            family = self.properties['adapter-family']
            if family in ('osa', 'roce', 'hipersockets'):
                self._adapter_kind = 'network'
            elif family in ('ficon',):
                self._adapter_kind = 'storage'
            else:
                self._adapter_kind = 'other'
        elif 'type' in self.properties:
            # because 'type' is more specific than 'adapter-family', we can
            # auto-set 'adapter-family' from 'type'.
            type_ = self.properties['type']
            if type_ in ('osd', 'osm'):
                self.properties['adapter-family'] = 'osa'
                self._adapter_kind = 'network'
            elif type_ == 'roce':
                self.properties['adapter-family'] = 'roce'
                self._adapter_kind = 'network'
            elif type_ == 'hipersockets':
                self.properties['adapter-family'] = 'hipersockets'
                self._adapter_kind = 'network'
            elif type_ == 'fcp':
                self.properties['adapter-family'] = 'ficon'
                self._adapter_kind = 'storage'
            elif type_ == 'crypto':
                self.properties['adapter-family'] = 'crypto'
                self._adapter_kind = 'other'
            elif type_ == 'zedc':
                self.properties['adapter-family'] = 'accelerator'
                self._adapter_kind = 'other'
            else:
                raise InputError("FakedAdapter with object-id=%s has an "
                                 "unknown value in its 'type' property: %s." %
                                 (self.oid, type_))
        else:
            raise InputError("FakedAdapter with object-id=%s must have "
                             "'adapter-family' or 'type' property specified." %
                             self.oid)
        if self.adapter_kind == 'network':
            if 'network-port-uris' not in self.properties:
                self.properties['network-port-uris'] = []
            self._ports = FakedPortManager(hmc=manager.hmc, adapter=self)
        elif self.adapter_kind == 'storage':
            if 'storage-port-uris' not in self.properties:
                self.properties['storage-port-uris'] = []
            self._ports = FakedPortManager(hmc=manager.hmc, adapter=self)
        else:
            self._ports = None
        if 'status' not in self.properties:
            self.properties['status'] = 'active'

    def __repr__(self):
        """
        Return a string with the state of this faked Adapter resource, for
        debug purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _manager = {manager_classname} at 0x{manager_id:08x}\n"
            "  _manager._parent._uri = {parent_uri!r}\n"
            "  _uri = {_uri!r}\n"
            "  _properties = {_properties}\n"
            "  _ports = {_ports}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                manager_classname=self._manager.__class__.__name__,
                manager_id=id(self._manager),
                parent_uri=self._manager.parent.uri,
                _uri=self._uri,
                _properties=repr_dict(self.properties, indent=2),
                _ports=repr_manager(self.ports, indent=2),
            ))
        return ret

    @property
    def ports(self):
        """
        :class:`~zhmcclient_mock.FakedPort`: The Port resources of this
        Adapter.

        If the kind of adapter does not have ports, this is `None`.
        """
        return self._ports

    @property
    def adapter_kind(self):
        """
        string: The kind of adapter, determined from the 'adapter-family' or
        'type' properties. This is currently used to distinguish storage and
        network adapters.

        Possible values are:
        * 'network' - A network adapter (OSA, ROCE, Hipersockets)
        * 'storage' - A storage adapter (FICON, FCP)
        * 'other' - Another adapter (zEDC, Crypto)
        """
        return self._adapter_kind


class FakedCpcManager(FakedBaseManager):
    """
    A manager for faked managed CPC resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, client):
        super(FakedCpcManager, self).__init__(
            hmc=hmc,
            parent=client,
            resource_class=FakedCpc,
            base_uri=self.api_root + '/cpcs',
            oid_prop='object-id',
            uri_prop='object-uri',
            class_value='cpc')

    def add(self, properties):
        """
        Add a faked CPC resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'class' will be auto-generated to 'cpc',
              if not specified.
            * 'dpm-enabled' is auto-set to `False`, if not specified.
            * 'is-ensemble-member' is auto-set to `False`, if not specified.
            * 'status' is auto-set, if not specified, as follows: If the
              'dpm-enabled' property is `True`, it is set to 'active';
              otherwise it is set to 'operating'.

        Returns:
          :class:`~zhmcclient_mock.FakedCpc`: The faked CPC resource.
        """
        return super(FakedCpcManager, self).add(properties)


class FakedCpc(FakedBaseResource):
    """
    A faked managed CPC resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedCpc, self).__init__(
            manager=manager,
            properties=properties)
        self._lpars = FakedLparManager(hmc=manager.hmc, cpc=self)
        self._partitions = FakedPartitionManager(hmc=manager.hmc, cpc=self)
        self._adapters = FakedAdapterManager(hmc=manager.hmc, cpc=self)
        self._virtual_switches = FakedVirtualSwitchManager(
            hmc=manager.hmc, cpc=self)
        self._reset_activation_profiles = FakedActivationProfileManager(
            hmc=manager.hmc, cpc=self, profile_type='reset')
        self._image_activation_profiles = FakedActivationProfileManager(
            hmc=manager.hmc, cpc=self, profile_type='image')
        self._load_activation_profiles = FakedActivationProfileManager(
            hmc=manager.hmc, cpc=self, profile_type='load')
        if 'dpm-enabled' not in self.properties:
            self.properties['dpm-enabled'] = False
        if 'is-ensemble-member' not in self.properties:
            self.properties['is-ensemble-member'] = False
        if 'status' not in self.properties:
            if self.dpm_enabled:
                self.properties['status'] = 'active'
            else:
                self.properties['status'] = 'operating'

    def __repr__(self):
        """
        Return a string with the state of this faked Cpc resource, for debug
        purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _manager = {manager_classname} at 0x{manager_id:08x}\n"
            "  _manager._parent._uri = {parent_uri!r}\n"
            "  _uri = {_uri!r}\n"
            "  _properties = {_properties}\n"
            "  _lpars = {_lpars}\n"
            "  _partitions = {_partitions}\n"
            "  _adapters = {_adapters}\n"
            "  _virtual_switches = {_virtual_switches}\n"
            "  _reset_activation_profiles = {_reset_activation_profiles}\n"
            "  _image_activation_profiles = {_image_activation_profiles}\n"
            "  _load_activation_profiles = {_load_activation_profiles}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                manager_classname=self._manager.__class__.__name__,
                manager_id=id(self._manager),
                parent_uri=self._manager.parent.uri,
                _uri=self._uri,
                _properties=repr_dict(self.properties, indent=2),
                _lpars=repr_manager(self.lpars, indent=2),
                _partitions=repr_manager(self.partitions, indent=2),
                _adapters=repr_manager(self.adapters, indent=2),
                _virtual_switches=repr_manager(
                    self.virtual_switches, indent=2),
                _reset_activation_profiles=repr_manager(
                    self.reset_activation_profiles, indent=2),
                _image_activation_profiles=repr_manager(
                    self.image_activation_profiles, indent=2),
                _load_activation_profiles=repr_manager(
                    self.load_activation_profiles, indent=2),
            ))
        return ret

    @property
    def dpm_enabled(self):
        """
        bool: Indicates whether this CPC is in DPM mode.

        This returns the value of the 'dpm-enabled' property.
        """
        return self.properties['dpm-enabled']

    @property
    def lpars(self):
        """
        :class:`~zhmcclient_mock.FakedLparManager`: Access to the faked LPAR
        resources of this CPC.
        """
        return self._lpars

    @property
    def partitions(self):
        """
        :class:`~zhmcclient_mock.FakedPartitionManager`: Access to the faked
        Partition resources of this CPC.
        """
        return self._partitions

    @property
    def adapters(self):
        """
        :class:`~zhmcclient_mock.FakedAdapterManager`: Access to the faked
        Adapter resources of this CPC.
        """
        return self._adapters

    @property
    def virtual_switches(self):
        """
        :class:`~zhmcclient_mock.FakedVirtualSwitchManager`: Access to the
        faked Virtual Switch resources of this CPC.
        """
        return self._virtual_switches

    @property
    def reset_activation_profiles(self):
        """
        :class:`~zhmcclient_mock.FakedActivationProfileManager`: Access to the
        faked Reset Activation Profile resources of this CPC.
        """
        return self._reset_activation_profiles

    @property
    def image_activation_profiles(self):
        """
        :class:`~zhmcclient_mock.FakedActivationProfileManager`: Access to the
        faked Image Activation Profile resources of this CPC.
        """
        return self._image_activation_profiles

    @property
    def load_activation_profiles(self):
        """
        :class:`~zhmcclient_mock.FakedActivationProfileManager`: Access to the
        faked Load Activation Profile resources of this CPC.
        """
        return self._load_activation_profiles


class FakedUnmanagedCpcManager(FakedBaseManager):
    """
    A manager for faked unmanaged CPC resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, console):
        super(FakedUnmanagedCpcManager, self).__init__(
            hmc=hmc,
            parent=console,
            resource_class=FakedUnmanagedCpc,
            base_uri=self.api_root + '/cpcs',
            oid_prop='object-id',
            uri_prop='object-uri',
            class_value=None)

    def add(self, properties):
        """
        Add a faked unmanaged CPC resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedUnmanagedCpc`: The faked unmanaged CPC
          resource.
        """
        return super(FakedUnmanagedCpcManager, self).add(properties)


class FakedUnmanagedCpc(FakedBaseResource):
    """
    A faked unmanaged CPC resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedUnmanagedCpc, self).__init__(
            manager=manager,
            properties=properties)

    def __repr__(self):
        """
        Return a string with the state of this faked unmanaged Cpc resource,
        for debug purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _manager = {manager_classname} at 0x{manager_id:08x}\n"
            "  _manager._parent._uri = {parent_uri!r}\n"
            "  _uri = {_uri!r}\n"
            "  _properties = {_properties}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                manager_classname=self._manager.__class__.__name__,
                manager_id=id(self._manager),
                parent_uri=self._manager.parent.uri,
                _uri=self._uri,
                _properties=repr_dict(self.properties, indent=2),
            ))
        return ret


class FakedHbaManager(FakedBaseManager):
    """
    A manager for faked HBA resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, partition):
        super(FakedHbaManager, self).__init__(
            hmc=hmc,
            parent=partition,
            resource_class=FakedHba,
            base_uri=partition.uri + '/hbas',
            oid_prop='element-id',
            uri_prop='element-uri',
            class_value='hba')

    def add(self, properties):
        """
        Add a faked HBA resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'class' will be auto-generated to 'hba',
              if not specified.
            * 'adapter-port-uri' identifies the backing FCP port for this HBA
              and is required to be specified.
            * 'device-number' will be auto-generated with a unique value
              within the partition in the range 0x8000 to 0xFFFF, if not
              specified.

            This method also updates the 'hba-uris' property in the parent
            faked Partition resource, by adding the URI for the faked HBA
            resource.

        Returns:
          :class:`~zhmcclient_mock.FakedHba`: The faked HBA resource.

        Raises:
          :exc:`zhmcclient_mock.InputError`: Some issue with the input
            properties.
        """
        new_hba = super(FakedHbaManager, self).add(properties)

        partition = self.parent

        # Reflect the new NIC in the partition
        assert 'hba-uris' in partition.properties
        partition.properties['hba-uris'].append(new_hba.uri)

        # Create a default device-number if not specified
        if 'device-number' not in new_hba.properties:
            devno = partition.devno_alloc()
            new_hba.properties['device-number'] = devno

        # Create a default wwpn if not specified
        if 'wwpn' not in new_hba.properties:
            wwpn = partition.wwpn_alloc()
            new_hba.properties['wwpn'] = wwpn

        return new_hba

    def remove(self, oid):
        """
        Remove a faked HBA resource.

        This method also updates the 'hba-uris' property in the parent
        Partition resource, by removing the URI for the faked HBA resource.

        Parameters:

          oid (string):
            The object ID of the faked HBA resource.
        """
        hba = self.lookup_by_oid(oid)
        partition = self.parent
        devno = hba.properties.get('device-number', None)
        if devno:
            partition.devno_free_if_allocated(devno)
        wwpn = hba.properties.get('wwpn', None)
        if wwpn:
            partition.wwpn_free_if_allocated(wwpn)
        assert 'hba-uris' in partition.properties
        hba_uris = partition.properties['hba-uris']
        hba_uris.remove(hba.uri)
        super(FakedHbaManager, self).remove(oid)  # deletes the resource


class FakedHba(FakedBaseResource):
    """
    A faked HBA resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedHba, self).__init__(
            manager=manager,
            properties=properties)


class FakedLparManager(FakedBaseManager):
    """
    A manager for faked LPAR resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, cpc):
        super(FakedLparManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedLpar,
            base_uri=self.api_root + '/logical-partitions',
            oid_prop='object-id',
            uri_prop='object-uri',
            class_value='logical-partition')

    def add(self, properties):
        """
        Add a faked LPAR resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'class' will be auto-generated to 'logical-partition',
              if not specified.
            * 'status' is auto-set to 'not-activated', if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedLpar`: The faked LPAR resource.
        """
        return super(FakedLparManager, self).add(properties)


class FakedLpar(FakedBaseResource):
    """
    A faked LPAR resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedLpar, self).__init__(
            manager=manager,
            properties=properties)
        if 'status' not in self.properties:
            self.properties['status'] = 'not-activated'


class FakedNicManager(FakedBaseManager):
    """
    A manager for faked NIC resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, partition):
        super(FakedNicManager, self).__init__(
            hmc=hmc,
            parent=partition,
            resource_class=FakedNic,
            base_uri=partition.uri + '/nics',
            oid_prop='element-id',
            uri_prop='element-uri',
            class_value='nic')

    def add(self, properties):
        """
        Add a faked NIC resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'class' will be auto-generated to 'nic',
              if not specified.
            * Either 'network-adapter-port-uri' (for backing ROCE adapters) or
              'virtual-switch-uri'(for backing OSA or Hipersockets adapters) is
              required to be specified.
            * 'device-number' will be auto-generated with a unique value
              within the partition in the range 0x8000 to 0xFFFF, if not
              specified.

            This method also updates the 'nic-uris' property in the parent
            faked Partition resource, by adding the URI for the faked NIC
            resource.

            This method also updates the 'connected-vnic-uris' property in the
            virtual switch referenced by 'virtual-switch-uri' property,
            and sets it to the URI of the faked NIC resource.

        Returns:
          :class:`zhmcclient_mock.FakedNic`: The faked NIC resource.

        Raises:
          :exc:`zhmcclient_mock.InputError`: Some issue with the input
            properties.
        """
        new_nic = super(FakedNicManager, self).add(properties)

        partition = self.parent

        # For OSA-backed NICs, reflect the new NIC in the virtual switch
        if 'virtual-switch-uri' in new_nic.properties:
            vswitch_uri = new_nic.properties['virtual-switch-uri']
            # Even though the URI handler when calling this method ensures that
            # the vswitch exists, this method can be called by the user as
            # well, so we have to handle the possibility that it does not
            # exist:
            try:
                vswitch = self.hmc.lookup_by_uri(vswitch_uri)
            except KeyError:
                raise InputError("The virtual switch specified in the "
                                 "'virtual-switch-uri' property does not "
                                 "exist: {!r}".format(vswitch_uri))
            connected_uris = vswitch.properties['connected-vnic-uris']
            if new_nic.uri not in connected_uris:
                connected_uris.append(new_nic.uri)

        # Create a default device-number if not specified
        if 'device-number' not in new_nic.properties:
            devno = partition.devno_alloc()
            new_nic.properties['device-number'] = devno

        # Reflect the new NIC in the partition
        assert 'nic-uris' in partition.properties
        partition.properties['nic-uris'].append(new_nic.uri)

        return new_nic

    def remove(self, oid):
        """
        Remove a faked NIC resource.

        This method also updates the 'nic-uris' property in the parent
        Partition resource, by removing the URI for the faked NIC resource.

        Parameters:

          oid (string):
            The object ID of the faked NIC resource.
        """
        nic = self.lookup_by_oid(oid)
        partition = self.parent
        devno = nic.properties.get('device-number', None)
        if devno:
            partition.devno_free_if_allocated(devno)
        assert 'nic-uris' in partition.properties
        nic_uris = partition.properties['nic-uris']
        nic_uris.remove(nic.uri)
        super(FakedNicManager, self).remove(oid)  # deletes the resource


class FakedNic(FakedBaseResource):
    """
    A faked NIC resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedNic, self).__init__(
            manager=manager,
            properties=properties)


class FakedPartitionManager(FakedBaseManager):
    """
    A manager for faked Partition resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, cpc):
        super(FakedPartitionManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedPartition,
            base_uri=self.api_root + '/partitions',
            oid_prop='object-id',
            uri_prop='object-uri',
            class_value='partition')

    def add(self, properties):
        """
        Add a faked Partition resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'class' will be auto-generated to 'partition',
              if not specified.
            * 'hba-uris' will be auto-generated as an empty array, if not
              specified.
            * 'nic-uris' will be auto-generated as an empty array, if not
              specified.
            * 'virtual-function-uris' will be auto-generated as an empty array,
              if not specified.
            * 'status' is auto-set to 'stopped', if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedPartition`: The faked Partition
            resource.
        """
        return super(FakedPartitionManager, self).add(properties)


class FakedPartition(FakedBaseResource):
    """
    A faked Partition resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.

    Each partition uses the device number range of 0x8000 to 0xFFFF for
    automatically assigned device numbers of HBAs, NICs and virtual functions.
    Users of the mock support should not use device numbers in that range
    (unless all of them are user-assigned for a particular partition).
    """

    def __init__(self, manager, properties):
        super(FakedPartition, self).__init__(
            manager=manager,
            properties=properties)
        if 'hba-uris' not in self.properties:
            self.properties['hba-uris'] = []
        if 'nic-uris' not in self.properties:
            self.properties['nic-uris'] = []
        if 'virtual-function-uris' not in self.properties:
            self.properties['virtual-function-uris'] = []
        if 'status' not in self.properties:
            self.properties['status'] = 'stopped'
        self._nics = FakedNicManager(hmc=manager.hmc, partition=self)
        self._hbas = FakedHbaManager(hmc=manager.hmc, partition=self)
        self._virtual_functions = FakedVirtualFunctionManager(
            hmc=manager.hmc, partition=self)
        self._devno_pool = IdPool(0x8000, 0xFFFF)
        self._wwpn_pool = IdPool(0x8000, 0xFFFF)

    def __repr__(self):
        """
        Return a string with the state of this faked Partition resource, for
        debug purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _manager = {manager_classname} at 0x{manager_id:08x}\n"
            "  _manager._parent._uri = {parent_uri!r}\n"
            "  _uri = {_uri!r}\n"
            "  _properties = {_properties}\n"
            "  _nics = {_nics}\n"
            "  _hbas = {_hbas}\n"
            "  _virtual_functions = {_virtual_functions}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                manager_classname=self._manager.__class__.__name__,
                manager_id=id(self._manager),
                parent_uri=self._manager.parent.uri,
                _uri=self._uri,
                _properties=repr_dict(self.properties, indent=2),
                _nics=repr_manager(self.nics, indent=2),
                _hbas=repr_manager(self.hbas, indent=2),
                _virtual_functions=repr_manager(
                    self.virtual_functions, indent=2),
            ))
        return ret

    @property
    def nics(self):
        """
        :class:`~zhmcclient_mock.FakedNicManager`: Access to the faked NIC
        resources of this Partition.
        """
        return self._nics

    @property
    def hbas(self):
        """
        :class:`~zhmcclient_mock.FakedHbaManager`: Access to the faked HBA
        resources of this Partition.
        """
        return self._hbas

    @property
    def virtual_functions(self):
        """
        :class:`~zhmcclient_mock.FakedVirtualFunctionManager`: Access to the
        faked Virtual Function resources of this Partition.
        """
        return self._virtual_functions

    def devno_alloc(self):
        """
        Allocates a device number unique to this partition, in the range of
        0x8000 to 0xFFFF.

        Returns:
          string: The device number as four hexadecimal digits in upper case.

        Raises:
          ValueError: No more device numbers available in that range.
        """
        devno_int = self._devno_pool.alloc()
        devno = "{:04X}".format(devno_int)
        return devno

    def devno_free(self, devno):
        """
        Free a device number allocated with :meth:`devno_alloc`.

        The device number must be allocated.

        Parameters:
          devno (string): The device number as four hexadecimal digits.

        Raises:
          ValueError: Device number not in pool range or not currently
            allocated.
        """
        devno_int = int(devno, 16)
        self._devno_pool.free(devno_int)

    def devno_free_if_allocated(self, devno):
        """
        Free a device number allocated with :meth:`devno_alloc`.

        If the device number is not currently allocated or not in the pool
        range, nothing happens.

        Parameters:
          devno (string): The device number as four hexadecimal digits.
        """
        devno_int = int(devno, 16)
        self._devno_pool.free_if_allocated(devno_int)

    def wwpn_alloc(self):
        """
        Allocates a WWPN unique to this partition, in the range of
        0xAFFEAFFE00008000 to 0xAFFEAFFE0000FFFF.

        Returns:
          string: The WWPN as 16 hexadecimal digits in upper case.

        Raises:
          ValueError: No more WWPNs available in that range.
        """
        wwpn_int = self._wwpn_pool.alloc()
        wwpn = "AFFEAFFE0000" + "{:04X}".format(wwpn_int)
        return wwpn

    def wwpn_free(self, wwpn):
        """
        Free a WWPN allocated with :meth:`wwpn_alloc`.

        The WWPN must be allocated.

        Parameters:
          WWPN (string): The WWPN as 16 hexadecimal digits.

        Raises:
          ValueError: WWPN not in pool range or not currently
            allocated.
        """
        wwpn_int = int(wwpn[-4:], 16)
        self._wwpn_pool.free(wwpn_int)

    def wwpn_free_if_allocated(self, wwpn):

        """
        Free a WWPN allocated with :meth:`wwpn_alloc`.

        If the WWPN is not currently allocated or not in the pool
        range, nothing happens.

        Parameters:
          WWPN (string): The WWPN as 16 hexadecimal digits.
        """
        wwpn_int = int(wwpn[-4:], 16)
        self._wwpn_pool.free_if_allocated(wwpn_int)


class FakedPortManager(FakedBaseManager):
    """
    A manager for faked Adapter Port resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, adapter):
        if adapter.adapter_kind == 'network':
            port_uri_segment = 'network-ports'
            port_class_value = 'network-port'
        elif adapter.adapter_kind == 'storage':
            port_uri_segment = 'storage-ports'
            port_class_value = 'storage-port'
        else:
            raise AssertionError("FakedAdapter with object-id=%s must be a "
                                 "storage or network adapter to have ports." %
                                 adapter.oid)
        super(FakedPortManager, self).__init__(
            hmc=hmc,
            parent=adapter,
            resource_class=FakedPort,
            base_uri=adapter.uri + '/' + port_uri_segment,
            oid_prop='element-id',
            uri_prop='element-uri',
            class_value=port_class_value)

    def add(self, properties):
        """
        Add a faked Port resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'class' will be auto-generated to 'network-port' or
              'storage-port', if not specified.

            This method also updates the 'network-port-uris' or
            'storage-port-uris' property in the parent Adapter resource, by
            adding the URI for the faked Port resource.

        Returns:
          :class:`zhmcclient_mock.FakedPort`: The faked Port resource.
        """
        new_port = super(FakedPortManager, self).add(properties)
        adapter = self.parent
        if 'network-port-uris' in adapter.properties:
            adapter.properties['network-port-uris'].append(new_port.uri)
        if 'storage-port-uris' in adapter.properties:
            adapter.properties['storage-port-uris'].append(new_port.uri)
        return new_port

    def remove(self, oid):
        """
        Remove a faked Port resource.

        This method also updates the 'network-port-uris' or 'storage-port-uris'
        property in the parent Adapter resource, by removing the URI for the
        faked Port resource.

        Parameters:

          oid (string):
            The object ID of the faked Port resource.
        """
        port = self.lookup_by_oid(oid)
        adapter = self.parent
        if 'network-port-uris' in adapter.properties:
            port_uris = adapter.properties['network-port-uris']
            port_uris.remove(port.uri)
        if 'storage-port-uris' in adapter.properties:
            port_uris = adapter.properties['storage-port-uris']
            port_uris.remove(port.uri)
        super(FakedPortManager, self).remove(oid)  # deletes the resource


class FakedPort(FakedBaseResource):
    """
    A faked Adapter Port resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedPort, self).__init__(
            manager=manager,
            properties=properties)


class FakedVirtualFunctionManager(FakedBaseManager):
    """
    A manager for faked Virtual Function resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, partition):
        super(FakedVirtualFunctionManager, self).__init__(
            hmc=hmc,
            parent=partition,
            resource_class=FakedVirtualFunction,
            base_uri=partition.uri + '/virtual-functions',
            oid_prop='element-id',
            uri_prop='element-uri',
            class_value='virtual-function')

    def add(self, properties):
        """
        Add a faked Virtual Function resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'element-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'element-uri' will be auto-generated based upon the element ID,
              if not specified.
            * 'class' will be auto-generated to 'virtual-function',
              if not specified.
            * 'device-number' will be auto-generated with a unique value
              within the partition in the range 0x8000 to 0xFFFF, if not
              specified.

            This method also updates the 'virtual-function-uris' property in
            the parent Partition resource, by adding the URI for the faked
            Virtual Function resource.

        Returns:
          :class:`zhmcclient_mock.FakedVirtualFunction`: The faked Virtual
            Function resource.
        """
        new_vf = super(FakedVirtualFunctionManager, self).add(properties)
        partition = self.parent
        assert 'virtual-function-uris' in partition.properties
        partition.properties['virtual-function-uris'].append(new_vf.uri)
        if 'device-number' not in new_vf.properties:
            devno = partition.devno_alloc()
            new_vf.properties['device-number'] = devno
        return new_vf

    def remove(self, oid):
        """
        Remove a faked Virtual Function resource.

        This method also updates the 'virtual-function-uris' property in the
        parent Partition resource, by removing the URI for the faked Virtual
        Function resource.

        Parameters:

          oid (string):
            The object ID of the faked Virtual Function resource.
        """
        virtual_function = self.lookup_by_oid(oid)
        partition = self.parent
        devno = virtual_function.properties.get('device-number', None)
        if devno:
            partition.devno_free_if_allocated(devno)
        assert 'virtual-function-uris' in partition.properties
        vf_uris = partition.properties['virtual-function-uris']
        vf_uris.remove(virtual_function.uri)
        super(FakedVirtualFunctionManager, self).remove(oid)  # deletes res.


class FakedVirtualFunction(FakedBaseResource):
    """
    A faked Virtual Function resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedVirtualFunction, self).__init__(
            manager=manager,
            properties=properties)


class FakedVirtualSwitchManager(FakedBaseManager):
    """
    A manager for faked Virtual Switch resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, cpc):
        super(FakedVirtualSwitchManager, self).__init__(
            hmc=hmc,
            parent=cpc,
            resource_class=FakedVirtualSwitch,
            base_uri=self.api_root + '/virtual-switches',
            oid_prop='object-id',
            uri_prop='object-uri',
            class_value='virtual-switch')

    def add(self, properties):
        """
        Add a faked Virtual Switch resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'class' will be auto-generated to 'virtual-switch',
              if not specified.
            * 'connected-vnic-uris' will be auto-generated as an empty array,
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedVirtualSwitch`: The faked Virtual
            Switch resource.
        """
        return super(FakedVirtualSwitchManager, self).add(properties)


class FakedVirtualSwitch(FakedBaseResource):
    """
    A faked Virtual Switch resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedVirtualSwitch, self).__init__(
            manager=manager,
            properties=properties)
        if 'connected-vnic-uris' not in self.properties:
            self.properties['connected-vnic-uris'] = []


class FakedStorageGroupManager(FakedBaseManager):
    """
    A manager for faked StorageGroup resources within a faked Console (see
    :class:`zhmcclient_mock.FakedConsole`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, console):
        super(FakedStorageGroupManager, self).__init__(
            hmc=hmc,
            parent=console,
            resource_class=FakedStorageGroup,
            base_uri=self.api_root + '/storage-groups',
            oid_prop='object-id',
            uri_prop='object-uri',
            class_value='storage-group')

    def add(self, properties):
        """
        Add a faked StorageGroup resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'class' will be auto-generated to 'storage-group',
              if not specified.
            * 'storage-volume-uris' will be auto-generated as an empty array,
              if not specified.
            * 'shared' is auto-set to False, if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedStorageGroup`: The faked StorageGroup
            resource.
        """
        return super(FakedStorageGroupManager, self).add(properties)


class FakedStorageGroup(FakedBaseResource):
    """
    A faked StorageGroup resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedStorageGroup, self).__init__(
            manager=manager,
            properties=properties)
        if 'storage-volume-uris' not in self.properties:
            self.properties['storage-volume-uris'] = []
        if 'shared' not in self.properties:
            self.properties['shared'] = False
        self._storage_volumes = FakedStorageVolumeManager(
            hmc=manager.hmc, storage_group=self)

    def __repr__(self):
        """
        Return a string with the state of this faked StorageGroup resource, for
        debug purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _manager = {manager_classname} at 0x{manager_id:08x}\n"
            "  _manager._parent._uri = {parent_uri!r}\n"
            "  _uri = {_uri!r}\n"
            "  _properties = {_properties}\n"
            "  _storage_volumes = {_storage_volumes}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                manager_classname=self._manager.__class__.__name__,
                manager_id=id(self._manager),
                parent_uri=self._manager.parent.uri,
                _uri=self._uri,
                _properties=repr_dict(self.properties, indent=2),
                _storage_volumes=repr_manager(self.storage_volumes, indent=2),
            ))
        return ret

    @property
    def storage_volumes(self):
        """
        :class:`~zhmcclient_mock.FakedStorageVolumeManager`: Access to the
        faked StorageVolume resources of this StorageGroup.
        """
        return self._storage_volumes


class FakedStorageVolumeManager(FakedBaseManager):
    """
    A manager for faked StorageVolume resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.
    """

    def __init__(self, hmc, storage_group):
        super(FakedStorageVolumeManager, self).__init__(
            hmc=hmc,
            parent=storage_group,
            resource_class=FakedStorageVolume,
            base_uri=self.api_root + '/storage-groups',
            oid_prop='element-id',
            uri_prop='element-uri',
            class_value='storage-volume')

    def add(self, properties):
        """
        Add a faked StorageVolume resource.

        Parameters:

          properties (dict):
            Resource properties.

            Special handling and requirements for certain properties:

            * 'object-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'object-uri' will be auto-generated based upon the object ID,
              if not specified.
            * 'class' will be auto-generated to 'storage-group',
              if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedStorageVolume`: The faked StorageVolume
            resource.
        """
        return super(FakedStorageVolumeManager, self).add(properties)


class FakedStorageVolume(FakedBaseResource):
    """
    A faked StorageVolume resource within a faked StorageGroup (see
    :class:`zhmcclient_mock.FakedStorageGroup`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.
    """

    def __init__(self, manager, properties):
        super(FakedStorageVolume, self).__init__(
            manager=manager,
            properties=properties)

    def __repr__(self):
        """
        Return a string with the state of this faked StorageVolume resource,
        for debug purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  _manager = {manager_classname} at 0x{manager_id:08x}\n"
            "  _manager._parent._uri = {parent_uri!r}\n"
            "  _uri = {_uri!r}\n"
            "  _properties = {_properties}\n"
            ")".format(
                classname=self.__class__.__name__,
                id=id(self),
                manager_classname=self._manager.__class__.__name__,
                manager_id=id(self._manager),
                parent_uri=self._manager.parent.uri,
                _uri=self._uri,
                _properties=repr_dict(self.properties, indent=2),
            ))
        return ret


class FakedMetricsContextManager(FakedBaseManager):
    """
    A manager for faked Metrics Context resources within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseManager`, see there for
    common methods and attributes.

    Example:

    * The following code sets up the faked data for metrics retrieval for
      partition usage metrics, and then retrieves the metrics:

      .. code-block:: python

          session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
          client = Client(session)

          # URIs of (faked or real) Partitions the metric apply to:
          part1_uri = ...
          part2_uri = ...

          # Add a faked metric group definition for group 'partition-usage':
          session.hmc.metric_contexts.add_metric_group_definition(
              FakedMetricGroupDefinition(
                  name='partition-usage',
                  types=[
                      ('processor-usage', 'integer-metric'),
                      ('network-usage', 'integer-metric'),
                      ('storage-usage', 'integer-metric'),
                      ('accelerator-usage', 'integer-metric'),
                      ('crypto-usage', 'integer-metric'),
                  ]))

          # Prepare the faked metric response for that metric group, with
          # data for two partitions:
          session.hmc.metric_contexts.add_metric_values(
              FakedMetricObjectValues(
                  group_name='partition-usage',
                  resource_uri=part1_uri,
                  timestamp=datetime.now(),
                  values=[
                      ('processor-usage', 15),
                      ('network-usage', 0),
                      ('storage-usage', 1),
                      ('accelerator-usage', 0),
                      ('crypto-usage', 0),
                  ]))
          session.hmc.metric_contexts.add_metric_values(
              FakedMetricObjectValues(
                  group_name='partition-usage',
                  resource_uri=part2_uri,
                  timestamp=datetime.now(),
                  values=[
                      ('processor-usage', 17),
                      ('network-usage', 5),
                      ('storage-usage', 2),
                      ('accelerator-usage', 0),
                      ('crypto-usage', 0),
                  ]))

          # Create a Metrics Context resource for one metric group:
          mc = client.metrics_contexts.create({
              'anticipated-frequency-seconds': 15,
              'metric-groups' ['partition-usage'],
          })

          # Retrieve the metrics for that metric context:
          metrics_response = mc.get_metrics()
    """

    def __init__(self, hmc, client):
        super(FakedMetricsContextManager, self).__init__(
            hmc=hmc,
            parent=client,
            resource_class=FakedMetricsContext,
            base_uri=self.api_root + '/services/metrics/context',
            oid_prop='fake-id',
            uri_prop='fake-uri',
            class_value=None)
        self._metric_group_def_names = []
        self._metric_group_defs = {}  # by group name
        self._metric_value_names = []
        self._metric_values = {}  # by group name

    def add(self, properties):
        """
        Add a faked Metrics Context resource.

        Parameters:

          properties (dict):
            Resource properties, as defined in the description of the
            :class:`~zhmcclient_mock.FakedMetricsContext` class.

            Special handling and requirements for certain properties:

            * 'fake-id' will be auto-generated with a unique value across
              all instances of this resource type, if not specified.
            * 'fake-uri' will be auto-generated based upon the 'fake-id'
              property, if not specified.

        Returns:
          :class:`~zhmcclient_mock.FakedMetricsContext`: The faked Metrics
          Context resource.
        """
        return super(FakedMetricsContextManager, self).add(properties)

    def add_metric_group_definition(self, definition):
        """
        Add a faked metric group definition.

        The definition will be used:

        * For later addition of faked metrics responses.
        * For returning the metric-group-info objects in the response of the
          Create Metrics Context operations.

        For defined metric groups, see chapter "Metric groups" in the
        :term:`HMC API` book.

        Parameters:

          definition (:class:~zhmcclient.FakedMetricGroupDefinition`):
            Definition of the metric group.

        Raises:

          ValueError: A metric group definition with this name already exists.
        """
        assert isinstance(definition, FakedMetricGroupDefinition)
        group_name = definition.name
        if group_name in self._metric_group_defs:
            raise ValueError("A metric group definition with this name "
                             "already exists: {}".format(group_name))
        self._metric_group_defs[group_name] = definition
        self._metric_group_def_names.append(group_name)

    def get_metric_group_definition(self, group_name):
        """
        Get a faked metric group definition by its group name.

        Parameters:

          group_name (:term:`string`): Name of the metric group.

        Returns:

          :class:~zhmcclient.FakedMetricGroupDefinition`: Definition of the
            metric group.

        Raises:

          ValueError: A metric group definition with this name does not exist.
        """
        if group_name not in self._metric_group_defs:
            raise ValueError("A metric group definition with this name does "
                             "not exist: {}".format(group_name))
        return self._metric_group_defs[group_name]

    def get_metric_group_definition_names(self):
        """
        Get the group names of all faked metric group definitions.

        Returns:

          iterable of string: The group names, in the order their metric
            group definitions had been added.
        """
        return self._metric_group_def_names

    def add_metric_values(self, values):
        """
        Add one set of faked metric values for a particular resource to the
        metrics response for a particular metric group, for later retrieval.

        For defined metric groups, see chapter "Metric groups" in the
        :term:`HMC API` book.

        Parameters:

          values (:class:`~zhmclient.FakedMetricObjectValues`):
            The set of metric values to be added. It specifies the resource URI
            and the targeted metric group name.
        """
        assert isinstance(values, FakedMetricObjectValues)
        group_name = values.group_name
        if group_name not in self._metric_values:
            self._metric_values[group_name] = []
        self._metric_values[group_name].append(values)
        if group_name not in self._metric_value_names:
            self._metric_value_names.append(group_name)

    def get_metric_values(self, group_name):
        """
        Get the faked metric values for a metric group, by its metric group
        name.

        The result includes all metric object values added earlier for that
        metric group name, using
        :meth:`~zhmcclient.FakedMetricsContextManager.add_metric_object_values`
        i.e. the metric values for all resources and all points in time that
        were added.

        Parameters:

          group_name (:term:`string`): Name of the metric group.

        Returns:

          iterable of :class:`~zhmclient.FakedMetricObjectValues`: The metric
            values for that metric group, in the order they had been added.

        Raises:

          ValueError: Metric values for this group name do not exist.
        """
        if group_name not in self._metric_values:
            raise ValueError("Metric values for this group name do not "
                             "exist: {}".format(group_name))
        return self._metric_values[group_name]

    def get_metric_values_group_names(self):
        """
        Get the group names of metric groups for which there are faked metric
        values.

        Returns:

          iterable of string: The group names, in the order their metric values
            had been added.
        """
        return self._metric_value_names


class FakedMetricsContext(FakedBaseResource):
    """
    A faked Metrics Context resource within a faked HMC (see
    :class:`zhmcclient_mock.FakedHmc`).

    Derived from :class:`zhmcclient_mock.FakedBaseResource`, see there for
    common methods and attributes.

    The Metrics Context "resource" is really a service and therefore does not
    have a data model defined in the :term:`HMC API` book.
    In order to fit into the zhmcclient mock framework, the faked Metrics
    Context in the zhmcclient mock framework is treated like all other faked
    resources and does have a data model.

    Data Model:

      'fake-id' (:term:`string`): Object ID of the resource.

        Initialization: Optional. If omitted, it will be auto-generated.

      'fake-uri' (:term:`string`): Resource URI of the resource (used for Get
        Metrics operation).

        Initialization: Optional. If omitted, it will be auto-generated from
        the Object ID.

      'anticipated-frequency-seconds' (:term:`integer`):
        The number of seconds the client anticipates will elapse between
        metrics retrievals using this context. The minimum accepted value is
        15.

        Initialization: Required.

      'metric-groups' (list of :term:`string`):
        The metric group names to be returned by a metric retrieval
        using this context.

        Initialization: Optional. If omitted or the empty list, all metric
        groups that are valid for the operational mode of each CPC will be
        returned.
    """

    def __init__(self, manager, properties):
        super(FakedMetricsContext, self).__init__(
            manager=manager,
            properties=properties)
        assert 'anticipated-frequency-seconds' in properties

    def get_metric_group_definitions(self):
        """
        Get the faked metric group definitions for this context object
        that are to be returned from its create operation.

        If a 'metric-groups' property had been specified for this context,
        only those faked metric group definitions of its manager object that
        are in that list, are included in the result. Otherwise, all metric
        group definitions of its manager are included in the result.

        Returns:

          iterable of :class:~zhmcclient.FakedMetricGroupDefinition`: The faked
            metric group definitions, in the order they had been added.
        """
        group_names = self.properties.get('metric-groups', None)
        if not group_names:
            group_names = self.manager.get_metric_group_definition_names()
        mg_defs = []
        for group_name in group_names:
            try:
                mg_def = self.manager.get_metric_group_definition(group_name)
                mg_defs.append(mg_def)
            except ValueError:
                pass  # ignore metric groups without metric group defs
        return mg_defs

    def get_metric_group_infos(self):
        """
        Get the faked metric group definitions for this context object
        that are to be returned from its create operation, in the format
        needed for the "Create Metrics Context" operation response.

        Returns:

          "metric-group-infos" JSON object as described for the "Create Metrics
            Context "operation response.
        """
        mg_defs = self.get_metric_group_definitions()
        mg_infos = []
        for mg_def in mg_defs:
            metric_infos = []
            for metric_name, metric_type in mg_def.types:
                metric_infos.append({
                    'metric-name': metric_name,
                    'metric-type': metric_type,
                })
            mg_info = {
                'group-name': mg_def.name,
                'metric-infos': metric_infos,
            }
            mg_infos.append(mg_info)
        return mg_infos

    def get_metric_values(self):
        """
        Get the faked metrics, for all metric groups and all resources that
        have been prepared on the manager object of this context object.

        Returns:

          iterable of tuple (group_name, iterable of values): The faked
            metrics, in the order they had been added, where:

            group_name (string): Metric group name.

            values (:class:~zhmcclient.FakedMetricObjectValues`):
              The metric values for one resource at one point in time.
        """
        group_names = self.properties.get('metric-groups', None)
        if not group_names:
            group_names = self.manager.get_metric_values_group_names()
        ret = []
        for group_name in group_names:
            try:
                mo_val = self.manager.get_metric_values(group_name)
                ret_item = (group_name, mo_val)
                ret.append(ret_item)
            except ValueError:
                pass  # ignore metric groups without metric values
        return ret

    def get_metric_values_response(self):
        """
        Get the faked metrics, for all metric groups and all resources that
        have been prepared on the manager object of this context object, as a
        string in the format needed for the "Get Metrics" operation response.

        Returns:

          "MetricsResponse" string as described for the "Get Metrics"
            operation response.
        """
        mv_list = self.get_metric_values()
        resp_lines = []
        for mv in mv_list:
            group_name = mv[0]
            resp_lines.append('"{}"'.format(group_name))
            mo_vals = mv[1]
            for mo_val in mo_vals:
                resp_lines.append('"{}"'.format(mo_val.resource_uri))
                resp_lines.append(
                    str(timestamp_from_datetime(mo_val.timestamp)))
                v_list = []
                for n, v in mo_val.values:
                    if isinstance(v, six.string_types):
                        v_str = '"{}"'.format(v)
                    else:
                        v_str = str(v)
                    v_list.append(v_str)
                v_line = ','.join(v_list)
                resp_lines.append(v_line)
                resp_lines.append('')
            resp_lines.append('')
        resp_lines.append('')
        return '\n'.join(resp_lines) + '\n'


class FakedMetricGroupDefinition(object):
    """
    A faked metric group definition (of one metric group).

    An object of this class contains the information (in a differently
    structured way) of a "metric-group-info" object described for the
    "Create Metrics Context" operation in the :term:`HMC API` book.

    The following table lists for each type mentioned in the metric group
    descriptions in chapter "Metric groups" in the :term:`HMC API` book,
    the Python types that are used for representing metric values of that type,
    and the metric type strings used in the metric group definitions for
    that type:

    =============================  ======================  ==================
    Metric group description type  Python type             Metric type string
    =============================  ======================  ==================
    Boolean                        :class:`py:bool`        ``boolean-metric``
    Byte                           :term:`integer`         ``byte-metric``
    Short                          :term:`integer`         ``short-metric``
    Integer                        :term:`integer`         ``integer-metric``
    Long                           :term:`integer`         ``long-metric``
    Double                         :class:`py:float`       ``double-metric``
    String, String Enum            :term:`unicode string`  ``string-metric``
    =============================  ======================  ==================
    """

    def __init__(self, name, types):
        """
        Parameters:

          name (:term:`string`): Name of the metric group.

          types (list of tuple(name, type)): Definition of the metric names
            and their types, as follows:

            * name (string): The metric name.
            * type (string): The metric type string (see table above).
        """
        self.name = name
        self.types = copy.deepcopy(types)

    def __repr__(self):
        """
        Return a string with the state of this object, for debug purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  name = {s.name!r}\n"
            "  types = {s.types!r}\n"
            ")".format(classname=self.__class__.__name__, id=id(self), s=self))
        return ret


class FakedMetricObjectValues(object):
    """
    Faked metric values for one resource and one metric group.

    An object of this class contains the information (in a structured way)
    of an "ObjectValues" item described for the data format of the response
    body of the "Get Metrics" operation in the :term:`HMC API` book.
    """

    def __init__(self, group_name, resource_uri, timestamp, values):
        """
        Parameters:

          group_name (:term:`string`): Name of the metric group to which
            these metric values apply.

          resource_uri (:term:`string`): URI of the resource to which these
            metric values apply.

          timestamp (datetime): Point in time to which these metric values
            apply.

          values (list of tuple(name, value)): The metric values, as follows:

            * name (string): The metric name.
            * value: The metric value as an object of the Python type listed
              in the table in the description of
              :class:`~zhmcclient.FakedMetricGroupDefinition`).
        """
        self.group_name = group_name
        self.resource_uri = resource_uri
        self.timestamp = timestamp
        self.values = copy.deepcopy(values)

    def __repr__(self):
        """
        Return a string with the state of this object, for debug purposes.
        """
        ret = (
            "{classname} at 0x{id:08x} (\n"
            "  group_name = {s.group_name!r}\n"
            "  resource_uri = {s.resource_uri!r}\n"
            "  timestamp = {s.timestamp!r}\n"
            "  values = {s.values!r}\n"
            ")".format(classname=self.__class__.__name__, id=id(self), s=self))
        return ret
