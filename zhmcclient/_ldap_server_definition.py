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
A :term:`LDAP Server Definition` resource represents a definition that contains
information about an LDAP server that may be used for HMC user authentication
purposes.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_LDAP_SERVER_DEFINITION

__all__ = ['LdapServerDefinitionManager', 'LdapServerDefinition']


class LdapServerDefinitionManager(BaseManager):
    """
    Manager providing access to the :term:`LDAP Server Definition` resources of
    a HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Console` object:

    * :attr:`zhmcclient.Console.ldap_server_definitions`

    HMC/SE version requirements:

    * HMC version == 2.13.0
    """

    def __init__(self, console):
        # This function should not go into the docs.
        # Parameters:
        #   console (:class:`~zhmcclient.Console`):
        #      Console object representing the HMC.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        # Because this resource has case-insensitive names, this list must
        # contain the name property.
        query_props = [
            'name',
        ]

        super().__init__(
            resource_class=LdapServerDefinition,
            class_name=RC_LDAP_SERVER_DEFINITION,
            session=console.manager.session,
            parent=console,
            base_uri='/api/console/ldap-server-definitions',
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=query_props,
            case_insensitive_names=True)

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`: :term:`Console` defining the scope for
        this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the :term:`LDAP Server Definition` resources representing the
        definitions of LDAp servers in this HMC.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The listing of resources is handled in an optimized way:

        * If this manager is enabled for :ref:`auto-updating`, a locally
          maintained resource list is used (which is automatically updated via
          inventory notifications from the HMC) and the provided filter
          arguments are applied.

        * Otherwise, if the filter arguments specify the resource name as a
          single filter argument with a straight match string (i.e. without
          regular expressions), an optimized lookup is performed based on a
          locally maintained name-URI cache.

        * Otherwise, the HMC List operation is performed with the subset of the
          provided filter arguments that can be handled on the HMC side and the
          remaining filter arguments are applied on the client side on the list
          result.

        HMC/SE version requirements:

        * HMC version == 2.13.0

        Authorization requirements:

        * User-related-access permission to the LDAP Server Definition objects
          included in the result, or task permission to the "Manage LDAP Server
          Definitions" task.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          : A list of :class:`~zhmcclient.LdapServerDefinition` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'ldap-server-definitions'
        list_uri = f'{self.console.uri}/ldap-server-definitions'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None)

    @logged_api_call(blanked_properties=['bind-password'], properties_pos=1)
    def create(self, properties):
        """
        Create a new LDAP Server Definition in this HMC.

        HMC/SE version requirements:

        * HMC version == 2.13.0

        Authorization requirements:

        * Task permission to the "Manage LDAP Server Definitions" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create LDAP Server Definition' in the :term:`HMC API`
            book.

        Returns:

          LdapServerDefinition:
            The resource object for the new LDAP Server Definition.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(
            self.console.uri + '/ldap-server-definitions', body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        ldap_server_definition = LdapServerDefinition(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return ldap_server_definition


class LdapServerDefinition(BaseResource):
    """
    Representation of a :term:`LDAP Server Definition`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.LdapServerDefinitionManager`).

    HMC/SE version requirements:

    * HMC version == 2.13.0
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.LdapServerDefinitionManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, LdapServerDefinitionManager), (
            "Console init: Expected manager type "
            f"{LdapServerDefinitionManager}, got {type(manager)}")
        super().__init__(
            manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this LDAP Server Definition.

        HMC/SE version requirements:

        * HMC version == 2.13.0

        Authorization requirements:

        * Task permission to the "Manage LDAP Server Definitions" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.delete(self.uri, resource=self)
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))
        self.cease_existence_local()

    @logged_api_call(blanked_properties=['bind-password'], properties_pos=1)
    def update_properties(self, properties):
        """
        Update writeable properties of this LDAP Server Definitions.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * HMC version == 2.13.0

        Authorization requirements:

        * Task permission to the "Manage LDAP Server Definitions" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'LDAP Server Definition object' in
            the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, resource=self, body=properties)

        # The name of LDAP Server Definitions cannot be updated. An attempt to
        # do so should cause HTTPError to be raised in the POST above, so we
        # assert that here, because we omit the extra code for handling name
        # updates:
        assert self.manager._name_prop not in properties
        self.update_properties_local(copy.deepcopy(properties))
