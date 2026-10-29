# Copyright 2017,2021 IBM Corp. All Rights Reserved.
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
A :term:`Console` resource represents an HMC.

In a paired setup with primary and alternate HMC, each HMC is represented as
a separate :term:`Console` resource.
"""


import warnings
import time

from ._constants import HMC_LOGGER_NAME
from ._exceptions import HTTPError
from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import get_logger, logged_api_call
from ._utils import timestamp_from_datetime, divide_filter_args, \
    matches_filters, make_query_str, RC_CONSOLE
from ._storage_group import StorageGroupManager
from ._storage_group_template import StorageGroupTemplateManager
from ._tape_library import TapeLibraryManager
from ._tape_link import TapeLinkManager
from ._storage_fabric import StorageFabricManager
from ._storage_site import StorageSiteManager
from ._storage_switch import StorageSwitchManager
from ._storage_subsystem import StorageSubsystemManager
from ._storage_control_unit import StorageControlUnitManager
from ._user import UserManager
from ._user_role import UserRoleManager
from ._user_pattern import UserPatternManager
from ._password_rule import PasswordRuleManager
from ._task import TaskManager
from ._ldap_server_definition import LdapServerDefinitionManager
from ._mfa_server_definition import MfaServerDefinitionManager
from ._sso_server_definition import SSOServerDefinitionManager
from ._unmanaged_cpc import UnmanagedCpcManager
from ._group import GroupManager
from ._utils import get_api_features
from ._certificates import CertificateManager
from ._partition_link import PartitionLinkManager
from ._hw_message import HwMessageManager

__all__ = ['ConsoleManager', 'Console']

HMC_LOGGER = get_logger(HMC_LOGGER_NAME)


class ConsoleManager(BaseManager):
    """
    Manager providing access to the :term:`Console` representing the HMC this
    client is connected to.

    In a paired setup with primary and alternate HMC, each HMC is represented
    as a separate :term:`Console` resource.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Client` object:

    * :attr:`zhmcclient.Client.consoles`

    HMC/SE version requirements: None
    """

    def __init__(self, client):
        # This function should not go into the docs.
        # Parameters:
        #   client (:class:`~zhmcclient.Client`):
        #      Client object for the HMC to be used.

        super().__init__(
            resource_class=Console,
            class_name=RC_CONSOLE,
            session=client.session,
            parent=None,
            base_uri='/api/console',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=None,
            list_has_name=False,
            supports_properties=True)
        self._client = client
        self._console = None

    @property
    def client(self):
        """
        :class:`~zhmcclient.Client`:
          The client defining the scope for this manager.
        """
        return self._client

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`:
          The :term:`Console` representing the HMC this client is connected to.

          The returned object is cached, so it is looked up only upon first
          access to this property.

          The returned object has only the following properties set:

          * 'class'
          * 'parent'
          * 'object-uri'

          Use :meth:`~zhmcclient.BaseResource.get_property` or
          :meth:`~zhmcclient.BaseResource.prop` to access any properties
          regardless of whether they are already set or first need to be
          retrieved.
        """
        if self._console is None:
            self._console = self.resource_object('/api/console')
        return self._console

    @logged_api_call
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the (one) :term:`Console` representing the HMC this client is
        connected to.

        The properties in the returned resource objects are by default only
        the "object-uri" and "object-id" properties and can be expanded with
        the "full_properties" and "additional_properties" parameters of this
        method.

        The listing of resources is handled by constructing a singleton object
        that represents the HMC of the current session, in an optimized way.
        For details, see :ref:`Listing resources`.

        HMC/SE version requirements: None

        Authorization requirements:

        * None

        Parameters:

          full_properties (bool):
            If `True`, the set of properties in the returned resource objects
            will be expanded to the full set of readable properties defined in
            the data model for
            Console objects
            in the :term:`HMC API` book.

          filter_args (dict):
            This parameter exists for consistency with other list() methods
            and will be ignored.

          additional_properties (list of string):
            A list of property names.
            If specified, the set of properties in the returned resource objects
            will be expanded with the specified properties.
            `None` is treated the same as an empty list.

        Returns:

          : A list of :class:`~zhmcclient.Console` objects, containing the one
          :term:`Console` representing the HMC this client is connected to.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        return self._list_singleton(
            self._base_uri, full_properties, additional_properties)


class Console(BaseResource):  # pylint: disable=too-many-instance-attributes
    """
    Representation of a :term:`Console`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.ConsoleManager`).

    HMC/SE version requirements: None
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.ConsoleManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, ConsoleManager), (
            f"Console init: Expected manager type {ConsoleManager}, got "
            f"{type(manager)}")
        super().__init__(manager, uri, name, properties)

        # The manager objects for child resources (with lazy initialization):
        self._storage_groups = None
        self._storage_group_templates = None
        self._tape_library = None
        self._tape_links = None
        self._storage_fabrics = None
        self._storage_switches = None
        self._storage_subsystems = None
        self._storage_control_units = None
        self._partition_links = None
        self._storage_sites = None
        self._users = None
        self._user_roles = None
        self._user_patterns = None
        self._password_rules = None
        self._tasks = None
        self._ldap_server_definitions = None
        self._mfa_server_definitions = None
        self._sso_server_definitions = None
        self._unmanaged_cpcs = None
        self._groups = None
        self._certificates = None
        self._api_feature_set = None
        self._hw_messages = None

    @property
    def storage_groups(self):
        """
        :class:`~zhmcclient.StorageGroupManager`:
          Manager object for the Storage Groups in scope of this Console.
        """
        # We do here some lazy loading.
        if not self._storage_groups:
            self._storage_groups = StorageGroupManager(self)
        return self._storage_groups

    @property
    def storage_group_templates(self):
        """
        :class:`~zhmcclient.StorageGroupTemplateManager`:
          Manager object for the Storage Group Templates in scope of this
          Console.
        """
        # We do here some lazy loading.
        if not self._storage_group_templates:
            self._storage_group_templates = StorageGroupTemplateManager(self)
        return self._storage_group_templates

    @property
    def tape_library(self):
        """
        :class:`~zhmcclient.TapeLibraryManager`: Access to the
        :term:`tape libraries <tape library>` of this Console.
        """
        # We do here some lazy loading.
        if not self._tape_library:
            self._tape_library = TapeLibraryManager(self)
        return self._tape_library

    @property
    def tape_links(self):
        """
        :class:`~zhmcclient.StorageGroupManager`:
          Manager object for the Storage Groups in scope of this Console.
        """
        # We do here some lazy loading.
        if not self._tape_links:
            self._tape_links = TapeLinkManager(self)
        return self._tape_links

    @property
    def storage_fabrics(self):
        """
        :class:`~zhmcclient.StorageFabricManager`:
          Manager object for the Storage Fabrics in scope of this Console.
        """
        # We do here some lazy loading.
        if not self._storage_fabrics:
            self._storage_fabrics = StorageFabricManager(self)
        return self._storage_fabrics

    @property
    def storage_sites(self):
        """
        :class:`~zhmcclient.StorageSiteManager`:
          Manager object for the Storage Sites in scope of this Console.
        """
        # We do here some lazy loading.
        if not self._storage_sites:
            self._storage_sites = StorageSiteManager(self)
        return self._storage_sites

    @property
    def storage_switches(self):
        """
        :class:`~zhmcclient.StorageSwitchManager`:
          Manager object for the Storage Switches in scope of this Console.
        """
        # We do here some lazy loading.
        if not self._storage_switches:
            self._storage_switches = StorageSwitchManager(self)
        return self._storage_switches

    @property
    def storage_subsystems(self):
        """
        :class:`~zhmcclient.StorageSubsystemManager`:
          Manager object for the Storage Subsystems in scope of this Console.
        """
        # We do here some lazy loading.
        if not self._storage_subsystems:
            self._storage_subsystems = StorageSubsystemManager(self)
        return self._storage_subsystems

    @property
    def storage_control_units(self):
        """
        :class:`~zhmcclient.StorageControlUnitManager`:
          Manager object for the Storage Control Units in scope of this
          Console.
        """
        # We do here some lazy loading.
        if not self._storage_control_units:
            self._storage_control_units = StorageControlUnitManager(self)
        return self._storage_control_units

    @property
    def partition_links(self):
        """
        :class:`~zhmcclient.PartitionLinkManager`:
          Manager object for the Partition Links in scope of this Console.
        """
        # We do here some lazy loading.
        if not self._partition_links:
            self._partition_links = PartitionLinkManager(self)
        return self._partition_links

    @property
    def users(self):
        """
        :class:`~zhmcclient.UserManager`: Access to the :term:`Users <User>` in
        this Console.
        """
        # We do here some lazy loading.
        if not self._users:
            self._users = UserManager(self)
        return self._users

    @property
    def user_roles(self):
        """
        :class:`~zhmcclient.UserRoleManager`: Access to the
        :term:`User Roles <User Role>` in this Console.
        """
        # We do here some lazy loading.
        if not self._user_roles:
            self._user_roles = UserRoleManager(self)
        return self._user_roles

    @property
    def user_patterns(self):
        """
        :class:`~zhmcclient.UserPatternManager`: Access to the
        :term:`User Patterns <User Pattern>` in this Console.
        """
        # We do here some lazy loading.
        if not self._user_patterns:
            self._user_patterns = UserPatternManager(self)
        return self._user_patterns

    @property
    def password_rules(self):
        """
        :class:`~zhmcclient.PasswordRuleManager`: Access to the
        :term:`Password Rules <Password Rule>` in this Console.
        """
        # We do here some lazy loading.
        if not self._password_rules:
            self._password_rules = PasswordRuleManager(self)
        return self._password_rules

    @property
    def tasks(self):
        """
        :class:`~zhmcclient.TaskManager`: Access to the :term:`Tasks <Task>` in
        this Console.
        """
        # We do here some lazy loading.
        if not self._tasks:
            self._tasks = TaskManager(self)
        return self._tasks

    @property
    def ldap_server_definitions(self):
        """
        :class:`~zhmcclient.LdapServerDefinitionManager`: Access to the
        :term:`LDAP Server Definitions <LDAP Server Definition>` in this
        Console.
        """
        # We do here some lazy loading.
        if not self._ldap_server_definitions:
            self._ldap_server_definitions = LdapServerDefinitionManager(self)
        return self._ldap_server_definitions

    @property
    def mfa_server_definitions(self):
        """
        :class:`~zhmcclient.MfaServerDefinitionManager`: Access to the
        :term:`MFA Server Definitions <MFA Server Definition>` in this
        Console.
        """
        # We do here some lazy loading.
        if not self._mfa_server_definitions:
            self._mfa_server_definitions = MfaServerDefinitionManager(self)
        return self._mfa_server_definitions

    @property
    def sso_server_definitions(self):
        """
        :class:`~zhmcclient.SSOServerDefinitionManager`: Access to the
        :term:`sso Server Definitions <sso Server Definition>` in this
        Console.
        """
        # We do here some lazy loading.
        if not self._sso_server_definitions:
            self._sso_server_definitions = SSOServerDefinitionManager(self)
        return self._sso_server_definitions

    @property
    def unmanaged_cpcs(self):
        """
        :class:`~zhmcclient.UnmanagedCpcManager`: Access to the unmanaged
        :term:`CPCs <CPC>` in this Console.
        """
        # We do here some lazy loading.
        if not self._unmanaged_cpcs:
            self._unmanaged_cpcs = UnmanagedCpcManager(self)
        return self._unmanaged_cpcs

    @property
    def groups(self):
        """
        :class:`~zhmcclient.GroupManager`: Access to user-defined
        :term:`Groups <Group>` in this Console.
        """
        # We do here some lazy loading.
        if not self._groups:
            self._groups = GroupManager(self)
        return self._groups

    @property
    def hw_messages(self):
        """
        :class:`~zhmcclient.HwMessageManager`: Access to
        :term:`Hardware Messages <Hardware Message>` for this Console.
        """
        # We do here some lazy loading.
        if not self._hw_messages:
            self._hw_messages = HwMessageManager(self)
        return self._hw_messages

    def _list_with_permitted(
            self, manager_attr, list_uri, result_prop, full_properties,
            additional_properties, client_filters, query_parms):
        """
        List resource objects by using the "List Permitted <resource_type>"
        operation.

        That operation does not require object access permission to the parent
        CPCs of the returned resource objects. That is also the reason why this
        method does not fall back to using "List <resource_type> of CPC", which
        would require object access permission to the CPC.

        The "List Permitted <resource_type>" operation is supported as follows:
        - "List Permitted Partitions": Requires HMC version 2.14.0
          (initial GA, API version 2.20).
        - "List Permitted Logical Partitions": Requires HMC version 2.14.0
          (initial GA, API version 2.20).
        - "List Permitted Adapters": Requires HMC version 2.16.0
          (initial GA, API version 4.1).

        The "additional-properties" query parameter of the
        "List Permitted <resource_type>" operation is always attempted to be
        used because the latest HMC version supports it for all resource types.
        If an older HMC version is used that does not support it yet, this
        method falls back to retrieving all properties using a bulk operation.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        Parameters:

          manager_attr (str): Name of the manager attribute on the parent
            zhmcclient.Cpc object.
            This must match the desired resource type to be listed
            (Adapter, Partition, Logical Partition).

          list_uri (string):
            Canonical URI for the "List Permitted" operation.
            This must match the desired resource type to be listed
            (Adapter, Partition, Logical Partition).

          result_prop (string):
            Name of property in result of "List Permitted" operation that
            contains the resource list.

          full_properties (bool):
            If `True`, the set of properties in the returned resource objects
            will be expanded to the full set of readable properties defined in
            the data model for the resource type in the :term:`HMC API` book.
            The "additional_properties" parameter is ignored in that case.

          additional_properties (list of string):
            A list of property names.
            If specified, the set of properties in the returned resource objects
            will be expanded with the specified properties.
            `None` is treated the same as an empty list.

          query_parms (list of str): Additional query parameters for the
            List operation. Each list item must be a string (e.g. "key=value")
            that is URI-encoded and ready to be appended to the URI as a query
            parameter.

        Returns:

          : A list of zhmcclient resource objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        has_full_properties = False

        if full_properties:

            resource_obj_list, _ = self._list_permitted_operation(
                manager_attr, list_uri, result_prop, client_filters,
                query_parms)

            if resource_obj_list:
                manager = resource_obj_list[0].manager
                # pylint: disable=protected-access
                manager._get_properties_bulk(resource_obj_list)

                has_full_properties = True

        elif additional_properties:

            # The "additional-properties" query parameter of the
            # "List Permitted <resource_type>" operation is always attempted
            # to be used because the latest HMC version supports it for all
            # resource types.

            HMC_LOGGER.debug(
                "Performing HMC List Permitted %s with "
                "additional-properties because the latest HMC version "
                "supports it and additional_properties is requested",
                manager_attr)
            resource_obj_list, ap_unsupported = self._list_permitted_operation(
                manager_attr, list_uri, result_prop, client_filters,
                query_parms, additional_properties)

            if ap_unsupported:
                # We are on an older HMC that does not support it.

                HMC_LOGGER.debug(
                    "Performing HMC List Permitted %s without "
                    "additional-properties because the actual HMC version does "
                    "not support it but additional_properties is requested",
                    manager_attr)
                resource_obj_list, _ = self._list_permitted_operation(
                    manager_attr, list_uri, result_prop, client_filters,
                    query_parms)

                if resource_obj_list:
                    manager = resource_obj_list[0].manager

                    # pylint: disable=protected-access
                    if manager._supports_properties:

                        HMC_LOGGER.debug(
                            "Performing HMC Bulk Get %s with properties "
                            "because the latest HMC version supports it and "
                            "additional_properties is requested",
                            manager.class_name)
                        # pylint: disable=protected-access
                        p_unsupported = manager._get_properties_bulk(
                            resource_obj_list,
                            properties=additional_properties)

                    else:
                        p_unsupported = True

                    if p_unsupported:
                        # Either the latest HMC version does not support it, or
                        # we are on an older HMC that does not support it.

                        HMC_LOGGER.debug(
                            "Performing HMC Bulk Get %s without properties "
                            "because the actual HMC version does not support "
                            "it but additional_properties is requested",
                            manager.class_name)
                        # pylint: disable=protected-access
                        manager._get_properties_bulk(resource_obj_list)

                        has_full_properties = True

        else:
            # Neither full_properties nor additional_properties

            resource_obj_list, _ = self._list_permitted_operation(
                manager_attr, list_uri, result_prop, client_filters,
                query_parms)

        if has_full_properties:
            for resource_obj in resource_obj_list:
                # pylint: disable=protected-access
                resource_obj._full_properties = True

        # The local resources and the name-URI-cache are not updated by
        # this method.

        return resource_obj_list

    def _list_permitted_operation(
            self, manager_attr, list_uri, result_prop, client_filters,
            query_parms, additional_properties=None):
        """
        Perform an HMC "List Permitted <resource_type>" operation and
        optionally perform client side filtering on the result.

        This method can only be called on the Console manager object.

        Parameters:

          manager_attr (str): Name of the manager attribute on the parent
            zhmcclient.Cpc object.
            This must match the desired resource type to be listed
            (Adapter, Partition, Logical Partition).

          list_uri (string):
            Canonical URI for the "List Permitted" operation.
            This must match the desired resource type to be listed
            (Adapter, Partition, Logical Partition).

          result_prop (string):
            Name of property in result of "List Permitted" operation that
            contains the resource list.

          client_filters (dict):
            Filters that need to be processed on the list result by the client.
            `None` causes no client filtering to happen, i.e. all resources are
            returned.

          query_parms (list of str): Additional query parameters for the
            "List Permitted" operation. Each list item must be a string (e.g.
            "key=value") that is URI-encoded and ready to be appended to the
            URI as a query parameter.

          additional_properties (list of string):
            A list of property names for use in the "additional-properties"
            query parameter of the "List Permitted" operation.
            If `None` or the empty list, the "additional-properties" query
            parameter will not be used.

        Returns:

          tuple(objs, unsupported): A tuple with:
            * objs (list): List of zhmcclient resource objects.
            * unsupported (bool): Indicates whether the "additional-properties"
              query parameter is unsupported by this version of the HMC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        _query_parms = list(query_parms)
        if additional_properties:
            ap_parm = f"additional-properties={','.join(additional_properties)}"
            _query_parms.append(ap_parm)
        query_parms_str = make_query_str(_query_parms)
        uri = f'{list_uri}{query_parms_str}'

        try:
            result = self.manager.session.get(uri)
        except HTTPError as exc:

            # If the entire "List Permitted" operation is not supported by
            # the actual HMC version, we do not fall back to an alternative
            # because we want to avoid introducing the requirement for object
            # access permission to the parent CPC.

            if additional_properties and \
                    exc.http_status == 400 and exc.reason == 1:
                # The "additional-properties" query parameter is not
                # supported in this older version of the HMC.
                return [], True

            raise

        cpc_manager = self.manager.client.cpcs
        cpcs_by_uri = {}  # caches local Cpc objects for CPCs already seen
        resource_obj_list = []
        if result:

            for props in result[result_prop]:

                # Determine the CPC of the resource. That will provide
                # the manager object for the resource.

                # We assume that all "List Permitted" operations have the
                # following CPC-related properties in their response:
                # * 'cpc-object-uri' (required)
                # * 'cpc-name' (required)
                # * 'se-version' (optional)
                # * 'dpm-enabled' (optional)
                cpc_uri = props['cpc-object-uri']
                try:
                    cpc = cpcs_by_uri[cpc_uri]
                except KeyError:
                    # Create a 'skeleton' local Cpc object we can hang the
                    # resource objects off of, even if the user does not have
                    # access permissions to these CPCs. Note that different
                    # resource objects can have different parent CPCs.
                    cpc_props = {}
                    cpc_props['name'] = props['cpc-name']
                    if 'se-version' in props:
                        cpc_props['se-version'] = props['se-version']
                    if 'dpm-enabled' in props:
                        cpc_props['dpm-enabled'] = props['dpm-enabled']
                    cpc = cpc_manager.resource_object(cpc_uri, cpc_props)
                    cpcs_by_uri[cpc_uri] = cpc

                manager = getattr(cpc, manager_attr)

                resource_obj = manager.resource_class(
                    manager=manager,
                    uri=props[manager.uri_prop],
                    name=props.get(manager.name_prop, None),
                    properties=props)

                if matches_filters(resource_obj, client_filters):
                    resource_obj_list.append(resource_obj)

        return resource_obj_list, False

    @logged_api_call
    def restart(self, force=False, wait_for_available=True,
                operation_timeout=None):
        """
        Restart the HMC represented by this Console object.

        Once the HMC is online again, this Console object, as well as any other
        resource objects accessed through this HMC, can continue to be used.
        An automatic re-logon will be performed under the covers, because the
        HMC restart invalidates the currently used HMC session.

        HMC/SE version requirements: None

        Authorization requirements:

        * Task permission for the "Shutdown/Restart" task.
        * "Remote Restart" must be enabled on the HMC.

        Parameters:

          force (bool):
            Boolean controlling whether the restart operation is processed when
            users are connected (`True`) or not (`False`). Users in this sense
            are local or remote GUI users. HMC WS API clients do not count as
            users for this purpose.

          wait_for_available (bool):
            Boolean controlling whether this method should wait for the HMC to
            become available again after the restart, as follows:

            * If `True`, this method will wait until the HMC has restarted and
              is available again. The
              :meth:`~zhmcclient.Client.query_api_version` method will be used
              to check for availability of the HMC.

            * If `False`, this method will return immediately once the HMC
              has accepted the request to be restarted.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for HMC availability after the
            restart. The special value 0 means that no timeout is set. `None`
            means that the default async operation timeout of the session is
            used. If the timeout expires when `wait_for_available=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for the HMC to become available again after the restart.
        """
        body = {'force': force}
        self.manager.session.post(
            self.uri + '/operations/restart', resource=self, body=body)
        if wait_for_available:
            time.sleep(10)
            self.manager.client.wait_for_available(
                operation_timeout=operation_timeout)

    @logged_api_call
    def shutdown(self, force=False):
        """
        Shut down and power off the HMC represented by this Console object.

        While the HMC is powered off, any Python resource objects retrieved
        from this HMC may raise exceptions upon further use.

        In order to continue using Python resource objects retrieved from this
        HMC, the HMC needs to be started again (e.g. by powering it on
        locally). Once the HMC is available again, Python resource objects
        retrieved from that HMC can continue to be used.
        An automatic re-logon will be performed under the covers, because the
        HMC startup invalidates the currently used HMC session.

        HMC/SE version requirements:

        * HMC version >= 2.12.0

        Authorization requirements:

        * Task permission for the "Shutdown/Restart" task.
        * "Remote Shutdown" must be enabled on the HMC.

        Parameters:

          force (bool):
            Boolean controlling whether the shutdown operation is processed
            when users are connected (`True`) or not (`False`). Users in this
            sense are local or remote GUI users. HMC WS API clients do not
            count as users for this purpose.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'force': force}
        self.manager.session.post(
            self.uri + '/operations/shutdown', resource=self, body=body)

    @logged_api_call
    def make_primary(self):
        """
        Change the role of the alternate HMC represented by this Console object
        to become the primary HMC.

        If that HMC is already the primary HMC, this method does not change its
        rols and succeeds.

        The HMC represented by this Console object must participate in a
        {primary, alternate} pairing.

        HMC/SE version requirements: None

        Authorization requirements:

        * Task permission for the "Manage Alternate HMC" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(
            self.uri + '/operations/make-primary', resource=self)

    @staticmethod
    def _time_query_parms(begin_time, end_time):
        """Return the URI query paramterer string for the specified begin time
        and end time."""
        query_parms = []
        if begin_time is not None:
            begin_ts = timestamp_from_datetime(begin_time)
            qp = f'begin-time={begin_ts}'
            query_parms.append(qp)
        if end_time is not None:
            end_ts = timestamp_from_datetime(end_time)
            qp = f'end-time={end_ts}'
            query_parms.append(qp)
        query_parms_str = '&'.join(query_parms)
        if query_parms_str:
            query_parms_str = '?' + query_parms_str
        return query_parms_str

    @logged_api_call
    def get_audit_log(self, begin_time=None, end_time=None):
        """
        Return the console audit log entries, optionally filtered by their
        creation time.

        HMC/SE version requirements:

        * HMC version >= 2.13.0

        Authorization requirements:

        * Task permission to the "Audit and Log Management" task.

        Parameters:

          begin_time (:class:`~py:datetime.datetime`):
            Begin time for filtering. Log entries with a creation time older
            than the begin time will be omitted from the results.

            If `None`, no such filtering is performed (and the oldest available
            log entries will be included).

          end_time (:class:`~py:datetime.datetime`):
            End time for filtering. Log entries with a creation time newer
            than the end time will be omitted from the results.

            If `None`, no such filtering is performed (and the newest available
            log entries will be included).

        Returns:

          :term:`json object`:
            A JSON object with the log entries, as described in section
            'Response body contents' of operation 'Get Console Audit Log' in
            the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms = self._time_query_parms(begin_time, end_time)
        uri = self.uri + '/operations/get-audit-log' + query_parms
        result = self.manager.session.get(uri, resource=self)
        return result

    @logged_api_call
    def get_security_log(self, begin_time=None, end_time=None):
        """
        Return the console security log entries, optionally filtered by their
        creation time.

        HMC/SE version requirements:

        * HMC version >= 2.13.0

        Authorization requirements:

        * Task permission to the "View Security Logs" task.

        Parameters:

          begin_time (:class:`~py:datetime.datetime`):
            Begin time for filtering. Log entries with a creation time older
            than the begin time will be omitted from the results.

            If `None`, no such filtering is performed (and the oldest available
            log entries will be included).

          end_time (:class:`~py:datetime.datetime`):
            End time for filtering. Log entries with a creation time newer
            than the end time will be omitted from the results.

            If `None`, no such filtering is performed (and the newest available
            log entries will be included).

        Returns:

          :term:`json object`:
            A JSON object with the log entries, as described in section
            'Response body contents' of operation 'Get Console Security Log' in
            the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms = self._time_query_parms(begin_time, end_time)
        uri = self.uri + '/operations/get-security-log' + query_parms
        result = self.manager.session.get(uri, resource=self)
        return result

    @logged_api_call
    def list_unmanaged_cpcs(self, name=None):
        """
        List the unmanaged CPCs of this HMC.

        For details, see :meth:`~zhmcclient.UnmanagedCpc.list`.

        HMC/SE version requirements:

        * HMC version >= 2.13.1

        Authorization requirements: None

        Parameters:

          name (:term:`string`):
            Regular expression pattern for the CPC name, as a filter that
            narrows the list of returned CPCs to those whose name property
            matches the specified pattern.

            `None` causes no filtering to happen, i.e. all unmanaged CPCs
            discovered by the HMC are returned.

        Returns:

          : A list of :class:`~zhmcclient.UnmanagedCpc` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        filter_args = {}
        if name is not None:
            filter_args['name'] = name
        cpcs = self.unmanaged_cpcs.list(filter_args=filter_args)
        return cpcs

    @logged_api_call
    def list_permitted_partitions(
            self, full_properties=False, filter_args=None,
            additional_properties=None):
        """
        List the permitted partitions of CPCs in DPM mode managed by this HMC.

        *Added in version 1.0*

        Any CPCs in classic mode managed by the HMC will be ignored for this
        operation.

        The properties in the returned resource objects are by default those
        returned by the
        "List Permitted Partitions"
        HMC operation defined in the :term:`HMC API` book and can be expanded
        with the "full_properties" and "additional_properties" parameters of
        this method.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        HMC/SE version requirements:

        * HMC version >= 2.14.0

        Authorization requirements:

        * Object permission to the partition objects included in the result.

        Parameters:

          full_properties (bool):
            If `True`, the set of properties in the returned resource objects
            will be expanded to the full set of readable properties defined in
            the data model for Partition objects in the :term:`HMC API` book.

          filter_args (dict):
            Filter arguments for limiting the partitions in the result.
            `None` causes no filtering to happen.

            The following filter arguments are supported by server-side
            filtering:

            * name (string): Limits the result to partitions whose name
              match the specified regular expression.

            * type (string): Limits the result to partitions with a matching
              "type" property value (i.e. "linux", "ssc", "zvm").

            * status (string): Limits the result to partitions with a matching
              "status" property value.

            * has-unacceptable-status (bool): Limits the result to partitions
              with a matching "has-unacceptable-status" property value.

            * cpc-name (string): Limits the result to partitions whose CPC
              has a name that matches the specified regular expression.

            Any other valid property of partitions is supported by
            client-side filtering:

            * <property-name>: Any other property of partitions.

          additional_properties (list of string):
            A list of property names.
            If specified, the set of properties in the returned resource objects
            will be expanded with the specified properties.
            `None` is treated the same as an empty list.

        Returns:

          : A list of :class:`~zhmcclient.Partition` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms, client_filters = divide_filter_args(
            ['name', 'type', 'status', 'has-unacceptable-status', 'cpc-name'],
            filter_args)

        manager_attr = "partitions"
        list_uri = f"{self.uri}/operations/list-permitted-partitions"
        result_prop = "partitions"

        partition_obj_list = self._list_with_permitted(
            manager_attr, list_uri, result_prop, full_properties,
            additional_properties, client_filters, query_parms)

        return partition_obj_list

    @logged_api_call
    def list_permitted_lpars(
            self, full_properties=False, filter_args=None,
            additional_properties=None):
        """
        List the permitted LPARs of CPCs in classic mode managed by this HMC.

        *Added in version 1.0*

        Any CPCs in DPM mode managed by the HMC will be ignored for this
        operation.

        The properties in the returned resource objects are by default those
        returned by the
        "List Permitted Logical Partitions"
        HMC operation defined in the :term:`HMC API` book and can be expanded
        with the "full_properties" and "additional_properties" parameters of
        this method.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        HMC/SE version requirements:

        * HMC version >= 2.14.0

        Authorization requirements:

        * Object permission to the LPAR objects included in the result.

        Parameters:

          full_properties (bool):
            If `True`, the set of properties in the returned resource objects
            will be expanded to the full set of readable properties defined in
            the data model for Logical Partition objects in the
            :term:`HMC API` book.

          filter_args (dict):
            Filter arguments for limiting the LPARs in the result.
            `None` causes no filtering to happen.

            The following filter arguments are supported by server-side
            filtering:

            * name (string): Limits the result to LPARs whose name
              match the specified regular expression.

            * activation-mode (string): Limits the result to LPARs with a
              matching "activation-mode" property value.

            * status (string): Limits the result to LPARs with a matching
              "status" property value.

            * has-unacceptable-status (bool): Limits the result to LPARs
              with a matching "has-unacceptable-status" property value.

            * cpc-name (string): Limits the result to LPARs whose CPC
              has a name that matches the specified regular expression.

            Any other valid property of LPARs is supported by
            client-side filtering:

            * <property-name>: Any other property of LPARs.

          additional_properties (list of string):
            A list of property names.
            If specified, the set of properties in the returned resource objects
            will be expanded with the specified properties.
            `None` is treated the same as an empty list.

        Returns:

          : A list of :class:`~zhmcclient.Lpar` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms, client_filters = divide_filter_args(
            ['name', 'type', 'status', 'has-unacceptable-status', 'cpc-name'],
            filter_args)

        manager_attr = "lpars"
        list_uri = f"{self.uri}/operations/list-permitted-logical-partitions"
        result_prop = "logical-partitions"

        lpar_obj_list = self._list_with_permitted(
            manager_attr, list_uri, result_prop, full_properties,
            additional_properties, client_filters, query_parms)

        return lpar_obj_list

    @logged_api_call
    def list_permitted_adapters(
            self, full_properties=False, filter_args=None,
            additional_properties=None):
        """
        List the permitted adapters of all CPCs managed by this HMC.

        The result will include all adapters of any DPM CPCs and z16 or later
        classic-mode CPCs that are managed by the targeted HMC and to which the
        user has object-access permission.

        The properties in the returned resource objects are by default those
        returned by the
        "List Permitted Adapters"
        HMC operation defined in the :term:`HMC API` book and can be expanded
        with the "full_properties" and "additional_properties" parameters of
        this method.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        HMC/SE version requirements:

        * HMC version >= 2.16.0
        * The adapters of CPCs with SE version < 2.16.0 that are not enabled
          for DPM are not included in the result.

        Authorization requirements:

        * Object permission to the adapter objects included in the result.

        Parameters:

          full_properties (bool):
            If `True`, the set of properties in the returned resource objects
            will be expanded to the full set of readable properties defined in
            the data model for Adapter objects in the :term:`HMC API` book.

          filter_args (dict):
            Filter arguments for limiting the adapters in the result.
            `None` causes no filtering to happen.

            The following filter arguments are supported by server-side
            filtering:

            * name (string): Limits the result to adapters whose name
              match the specified regular expression.

            * adapter-id (string): Limits the result to adapters with a matching
              "adapter-id" property value (i.e. PCHID).

            * adapter-family (string): Limits the result to adapters with a
              matching "adapter-family" property value (e.g. "hipersockets").

            * type (string): Limits the result to adapters with a matching
              "type" property value (e.g. "hipersockets").

            * status (string): Limits the result to adapters with a matching
              "status" property value.

            * firmware-update-pending (bool): Limits the result to adapters with
              a matching firmware-update-pending state.

            * cpc-name (string): Limits the result to adapters whose CPC
              has a name that matches the specified regular expression.

            * dpm-enabled (bool): Limits the result to adapters whose CPC
              has a matching "dpm-enabled" property.

            Any other valid property of adapters is supported by
            client-side filtering:

            * <property-name>: Any other property of adapters.

          additional_properties (list of string):
            A list of property names.
            If specified, the set of properties in the returned resource objects
            will be expanded with the specified properties.
            `None` is treated the same as an empty list.

        Returns:

          : A list of :class:`~zhmcclient.Adapter` objects.

          If no additional or full properties are specified, the returned
          adapters will have the following properties:

          * object-uri, name, adapter-id, adapter-family, type, status,
          * firmware-update-pending (if CPC >=2.16 and
            LI_1580_CRYPTO_AUTO_TOGGLE feature is enabled)

          and the following properties for their parent CPC:

          * cpc-name (CPC property 'name')
          * cpc-object-uri (CPC property 'object-uri')
          * se-version (CPC property 'se-version')
          * dpm-enabled (CPC property 'dpm-enabled')

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms, client_filters = divide_filter_args(
            ['name', 'adapter-id', 'adapter-family', 'type', 'status',
             'firmware-update-pending', 'cpc-name', 'dpm-enabled'],
            filter_args)

        manager_attr = "adapters"
        list_uri = f"{self.uri}/operations/list-permitted-adapters"
        result_prop = "adapters"

        adapter_obj_list = self._list_with_permitted(
            manager_attr, list_uri, result_prop, full_properties,
            additional_properties, client_filters, query_parms)

        return adapter_obj_list

    @logged_api_call
    def list_api_features(self, name=None, force=None):
        # pylint: disable=unused-argument
        """
        Returns the :ref:`API features` enabled (=available) on this console.

        If the HMC does not support API features yet (i.e. before HMC version
        2.16.0 and HMC API version 4.10), the result will be an empty list.

        The result is not cached in this object, because different 'name'
        filters can have different results.

        For a list of possible API features, see section "API features" in the
        :term:`HMC API` book, starting with 2.16.0.

        HMC/SE version requirements: None

        Authorization requirements: None

        Parameters:

          name (string):
            A regular expression used to limit the result to matching API
            features. If `None`, no such filtering takes place.

          force (bool):
            Deprecated: This parameter will be ignored; the API feature data
            is always retrieved from the HMC.
            This parameter is deprecated.

        Returns:

          list of string: The names of the API features that are enabled
          (=available) on this console.
        """
        if force is not None:
            warnings.warn(
                "The 'force' parameter of "
                "zhmcclient.Console.list_api_features() is deprecated",
                DeprecationWarning, stacklevel=2)
        return get_api_features(self, name)

    @logged_api_call
    def api_feature_enabled(self, feature_name, force=False):
        """
        Indicates whether the specified
        :ref:`API feature <API features>` is enabled (= available) for this
        console.

        If the HMC does not support API features yet (i.e. before HMC version
        2.16.0 and HMC API version 4.10), the feature is considered disabled.

        For a list of possible API features, see section "API features" in the
        :term:`HMC API` book.

        The API feature data is cached in this object.

        HMC/SE version requirements: None

        Authorization requirements: None

        Parameters:

          feature_name (:term:`string`): The name of the API feature.

          force (bool): If True, retrieves the API feature data from the
            HMC, even when it was already cached.

        Returns:

          bool: Boolean indicating whether the API feature is enabled
          (= available) on this console.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self._setup_api_feature_set(force)
        return feature_name in self._api_feature_set

    def _setup_api_feature_set(self, force=False):
        """
        Set up `self._api_feature_set` with the names of the enabled
        API features from the result of the "List Console API Features"
        operation, if it is not yet set up.

        Parameters:
          force (bool): If True, retrieves the list of API features from the
            HMC and performs the setup, even when it was already set up.
        """
        if self._api_feature_set is None or force:
            self._api_feature_set = set(get_api_features(self))

    @property
    def certificates(self):
        """
        :class:`~zhmcclient.CertificateManager`: Access to the
        :term:`Certificates <Certificate>` in this HMC.
        """
        # We do here some lazy loading.
        if not self._certificates:
            self._certificates = CertificateManager(self)
        return self._certificates

    @logged_api_call
    def single_step_install(
            self, bundle_level=None, backup_location_type='usb',
            accept_firmware=True, ftp_host=None,
            ftp_protocol=None, ftp_user=None,
            ftp_password=None, ftp_directory=None,
            wait_for_completion=True, operation_timeout=None):
        """
        Upgrades the firmware on this HMC to a new bundle level.

        This is done by performing the "Console Single Step Install" operation
        which performs the following steps:

        * If `accept_firmware` is True, the firmware currently installed on the
          this HMC is accepted. Note that once firmware is accepted, it
          cannot be removed.
        * A backup of the this HMC is performed to the specified backup device.
        * The new firmware identified by the bundle-level field is retrieved
          from the IBM support site or from an FTP server, and installed.
        * The newly installed firmware is activated, which includes rebooting
          this HMC.

        Note that it is not possible to downgrade the HMC firmware with this
        operation.

        For HMCs that run on an HMA that also hosts an SE (e.g. z16 and higher),
        the HMC firmware can only be upgraded if the HMA hosts an alternate SE.

        HMC/SE version requirements:

        * HMC version >= 2.16.0

        Authorization requirements:

        * Task permission to the "Single Step Console Internal Code" task.

        Parameters:

          bundle_level (string): Name of the bundle to be installed on the HMC
            (e.g. 'H71').
            If `None`, all locally available code changes, or in case of
            retrieving code changes from an FTP server, all code changes on
            the FTP server, will be installed.

          backup_location_type (string): Type of backup location for the
            HMC backup that is performed:

              - "ftp": The FTP server that was used for the last console backup
                as defined on the "Configure Backup Settings" user interface
                task in the HMC GUI.
              - "usb": The USB storage device mounted to the HMC.

          accept_firmware (bool): Accept the previous bundle level before
            installing the new level.

          ftp_host (string): The hostname for the FTP server from which
            the firmware will be retrieved, or `None` to retrieve it from the
            IBM support site.

          ftp_protocol (string): The protocol to connect to the FTP
            server, if the firmware will be retrieved from an FTP server,
            or `None`. Valid values are: "ftp", "ftps", "sftp".

          ftp_user (string): The username for the FTP server login,
            if the firmware will be retrieved from an FTP server, or `None`.

          ftp_password (string): The password for the FTP server login,
            if the firmware will be retrieved from an FTP server, or `None`.

          ftp_directory (string): The path name of the directory on the
            FTP server with the firmware files,
            if the firmware will be retrieved from an FTP server, or `None`.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation including any HMC
            restarts, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation including any HMC
              restarts.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation including any HMC restarts. The
            special value 0 means that no timeout is set. `None` means that
            the default async operation timeout of the session is used. If the
            timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Returns:

          `None` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns `None`.

            If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC. The Job object will be valid across
            any HMC restarts that occur during the upgrade operation.

            This job supports cancellation. Note there are only a few
            interruption points in the firmware install process, so it may be
            some time before the job is canceled, and after some point, will
            continue on to completion. The job status and reason codes will
            indicate whether the job was canceled or ran to completion. If the
            job is successfully canceled, any steps that were successfully
            completed will not be rolled back.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """

        # The 'wait_for_completion' parameter from 2.12.0 became
        # 'ftp_host' after that, so we detect the passing of
        # 'wait_for_completion' as a positional argument.
        assert ftp_host is None or \
            isinstance(ftp_host, str)

        body = {
            'backup-location-type': backup_location_type,
            'accept-firmware': accept_firmware,
        }

        if bundle_level is not None:
            body['bundle-level'] = bundle_level

        if ftp_host is not None:
            body['ftp-retrieve'] = True
            body['ftp-server-host'] = ftp_host
            body['ftp-server-user'] = ftp_user
            body['ftp-server-password'] = ftp_password
            body['ftp-server-directory'] = ftp_directory
            body['ftp-server-protocol'] = ftp_protocol

        result = self.manager.session.post(
            self.uri + '/operations/single-step-install', resource=self,
            body=body, wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)

        return result

    @logged_api_call
    def delete_uninstalled_firmware(
            self, ec_levels=None,
            wait_for_completion=True, operation_timeout=None):
        """
        Deletes retrieved but uninstalled firmware on this HMC.

        This is done by performing the "Console Delete Retrieved Internal Code"
        operation.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "hmc-delete-retrieved-internal-code"

        Authorization requirements:

        * Task permission to the "Change Console Internal Code" task.

        Parameters:

          ec_levels (list of tuple(ec,mcl)): The specific EC levels back to
            which the firmware should be deleted.
            If `None`, all uninstalled MCLs are deleted.

            The EC levels are specified as a list of tuples (ec, mcl) where:

              - ec (string): EC number of the EC stream (e.g. "P30719")
              - mcl (string): MCL number within the EC stream (e.g. "001")

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation including any HMC
            restarts, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation including any HMC
              restarts.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation including any HMC restarts. The
            special value 0 means that no timeout is set. `None` means that
            the default async operation timeout of the session is used. If the
            timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Returns:

          string or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns a string with the
            message text describing the detailed error that occurred when the
            operation was not successful.

            If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC. The Job object will be valid across
            any HMC restarts that occur during the upgrade operation.
            This job does not support cancellation.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """

        body = {}

        if ec_levels is not None:
            body['ec-levels'] = \
                [{"number": ec[0], "mcl": ec[1]} for ec in ec_levels]

        result = self.manager.session.post(
            self.uri + '/operations/delete-retrieved-internal-code',
            resource=self,
            body=body, wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)

        return result

    @logged_api_call
    def report_console_problem(self, customer_name, customer_phone_number,
                               problem_description, problem_type,
                               wait_for_completion=True,
                               operation_timeout=None):
        """
        Report a console problem on this HMC.

        This is done by performing the "Report a Console Problem"
        operation.

        HMC/SE version requirements: None

        Authorization requirements:

        * Task permission to the "Report a Console Problem" task.
        * Automatic service call reporting must be enabled

        Parameters:

          customer_name (string): The name of the customer
            reporting the console problem.

          customer_phone_number (string): The phone number of
            the customer reporting the console problem.

          problem_description (string): A description of the
            problem.

          problem_type (string): The problem type (i.e. "health",
            "hmc", "test").

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation including any HMC
            restarts, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation including any HMC
              restarts.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation including any HMC restarts. The
            special value 0 means that no timeout is set. `None` means that
            the default async operation timeout of the session is used. If the
            timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Returns:

          string or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns a string with the
            message text describing the detailed error that occurred when the
            operation was not successful.

            If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC. The Job object will be valid across
            any HMC restarts that occur during the upgrade operation.
            This job does not support cancellation.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        body = {
            'customer-name': customer_name,
            'customer-phone-number': customer_phone_number,
            'problem-description': problem_description,
            'problem-type': problem_type
        }

        result = self.manager.session.post(
            self.uri + '/operations/report-problem',
            resource=self,
            body=body, wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)

        return result

    def dump(self):
        """
        Dump this Console resource with its properties and child resources
        (recursively) as a resource definition.

        The returned resource definition has the following format::

            {
                # Resource properties:
                "properties": {...},

                # Child resources:
                "users": [...],
                "user_roles": [...],
                "user_patterns": [...],
                "password_rules": [...],
                "tasks": [...],
                "ldap_server_definitions": [...],
                "mfa_server_definitions": [...],
                "sso_server_definitions": [...],
                "unmanaged_cpcs": [...],
                "storage_groups": [...],
                "tape_libraries": [...],
                "tape_links": [...],
            }

        Returns:

          dict: Resource definition of this resource.
        """

        # Dump the resource properties
        resource_dict = super().dump()

        # Dump the child resources
        users = self.users.dump()
        if users:
            resource_dict['users'] = users
        user_roles = self.user_roles.dump()
        if user_roles:
            resource_dict['user_roles'] = user_roles
        user_patterns = self.user_patterns.dump()
        if user_patterns:
            resource_dict['user_patterns'] = user_patterns
        password_rules = self.password_rules.dump()
        if password_rules:
            resource_dict['password_rules'] = password_rules
        tasks = self.tasks.dump()
        if tasks:
            resource_dict['tasks'] = tasks
        ldap_server_definitions = self.ldap_server_definitions.dump()
        if ldap_server_definitions:
            resource_dict['ldap_server_definitions'] = ldap_server_definitions
        mfa_server_definitions = self.mfa_server_definitions.dump()
        if mfa_server_definitions:
            resource_dict['mfa_server_definitions'] = mfa_server_definitions
        sso_server_definitions = self.sso_server_definitions.dump()
        if sso_server_definitions:
            resource_dict['sso_server_definitions'] = sso_server_definitions
        storage_groups = self.storage_groups.dump()
        if storage_groups:
            resource_dict['storage_groups'] = storage_groups
        tape_libraries = self.tape_library.dump()
        if tape_libraries:
            resource_dict['tape_libraries'] = tape_libraries
        tape_links = self.tape_links.dump()
        if tape_links:
            resource_dict['tape_links'] = tape_links

        # Note: Unmanaged CPCs are not dumped, since their properties cannot
        #       be retrieved.

        return resource_dict
