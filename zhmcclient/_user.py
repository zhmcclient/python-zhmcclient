# Copyright 2017 IBM Corp. All Rights Reserved.
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
A :term:`User` resource represents a user configured in the HMC.
"""

from __future__ import absolute_import

import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call

__all__ = ['UserManager', 'User']


class UserManager(BaseManager):
    """
    Manager providing access to the :term:`User` resources of a HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Console` object:

    * :attr:`zhmcclient.Console.users`
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
        query_props = [
            'name',
            'type',
        ]

        super(UserManager, self).__init__(
            resource_class=User,
            class_name='user',
            session=console.manager.session,
            parent=console,
            base_uri='/api/users',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props)

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`: :term:`Console` defining the scope for
        this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=True, filter_args=None):
        """
        List the :term:`User` resources representing the users defined in this
        HMC.

        Authorization requirements:

        * User-related-access permission to the User object included in the
          result, or, depending on the type of User object, task permission to
          the "Manage Users" task or the "Manage User Templates" task.

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

          : A list of :class:`~zhmcclient.User` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        resource_obj_list = []
        query_parms, client_filters = self._divide_filter_args(filter_args)
        resources_name = 'users'
        uri = '{}/{}{}'.format(self.console.uri, resources_name, query_parms)

        result = self.session.get(uri)
        if result:
            props_list = result[resources_name]
            for props in props_list:

                resource_obj = self.resource_class(
                    manager=self,
                    uri=props[self._uri_prop],
                    name=props.get(self._name_prop, None),
                    properties=props)

                if self._matches_filters(resource_obj, client_filters):
                    resource_obj_list.append(resource_obj)
                    if full_properties:
                        resource_obj.pull_full_properties()

        self._name_uri_cache.update_from(resource_obj_list)
        return resource_obj_list

    @logged_api_call
    def create(self, properties):
        """
        Create a new User in this HMC.

        Authorization requirements:

        * Task permission to the "Manage Users" task to create a standard user
          or the "Manage User Templates" task to create a template user.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create User' in the :term:`HMC API` book.

        Returns:

          User:
            The resource object for the new User.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.console.uri + '/users',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        user = User(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return user


class User(BaseResource):
    """
    Representation of a :term:`User`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.UserManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.UserManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, UserManager), \
            "Console init: Expected manager type %s, got %s" % \
            (UserManager, type(manager))
        super(User, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this User.

        Authorization requirements:

        * Task permission to the "Manage Users" task to delete a non-template
          user, or the "Manage User Templates" task to delete a template user.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self.uri)
        self.manager._name_uri_cache.delete(
            self.properties.get(self.manager._name_prop, None))

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this User.

        Authorization requirements:

        * Task permission to the "Manage Users" task to update a non-template
          user, or the "Manage User Templates" task to update a template user.
        * For a user to update their own password or default-group-uri
          property, user-related-access permission to the user represented
          by this User object, or task permission to the "Manage Users" task is
          required.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'User object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self.uri, body=properties)

        # The name of Users cannot be updated. An attempt to do so should cause
        # HTTPError to be raised in the POST above, so we assert that here,
        # because we omit the extra code for handling name updates:
        assert self.manager._name_prop not in properties
        self.properties.update(copy.deepcopy(properties))

    @logged_api_call
    def add_user_role(self, user_role):
        """
        Add the specified User Role to this User.

        This User must not be a system-defined or pattern-based user.

        Authorization requirements:

        * Task permission to the "Manage Users" task to modify a standard user
          or the "Manage User Templates" task to modify a template user.

        Parameters:

          user_role (:class:`~zhmcclient.UserRole`): User Role to be added.
            Must not be `None`.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'user-role-uri': user_role.uri
        }
        self.manager.session.post(
            self.uri + '/operations/add-user-role',
            body=body)

    @logged_api_call
    def remove_user_role(self, user_role):
        """
        Remove the specified User Role from this User.

        This User must not be a system-defined or pattern-based user.

        Authorization requirements:

        * Task permission to the "Manage Users" task to modify a standard user
          or the "Manage User Templates" task to modify a template user.

        Parameters:

          user_role (:class:`~zhmcclient.UserRole`): User Role to be removed.
            Must not be `None`.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'user-role-uri': user_role.uri
        }
        self.manager.session.post(
            self.uri + '/operations/remove-user-role',
            body=body)
