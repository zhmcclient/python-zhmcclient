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
A :term:`User Role` resource represents an authority role which can be assigned
to one or more HMC users.

A User Role may allow access to specific managed objects, classes of managed
objects, groups and/or tasks. There are two types of User Roles: user-defined
and system-defined. User-defined User Roles are created by an HMC user, whereas
the system-defined User Roles are pre-defined, standard User Roles supplied
with the HMC.
"""

from __future__ import absolute_import

import copy
import six

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call

__all__ = ['UserRoleManager', 'UserRole']


class UserRoleManager(BaseManager):
    """
    Manager providing access to the :term:`User Role` resources of a HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Console` object:

    * :attr:`zhmcclient.Console.user_roles`
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

        super(UserRoleManager, self).__init__(
            resource_class=UserRole,
            class_name='user-role',
            session=console.manager.session,
            parent=console,
            base_uri='/api/user-roles',
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
        List the :term:`User Role` resources representing the user roles
        defined in this HMC.

        Authorization requirements:

        * User-related-access permission to the User Role objects included in
          the result, or task permission to the "Manage User Roles" task.

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

          : A list of :class:`~zhmcclient.UserRole` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        resource_obj_list = []
        query_parms, client_filters = self._divide_filter_args(filter_args)
        resources_name = 'user-roles'
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
        Create a new (user-defined) User Role in this HMC.

        Authorization requirements:

        * Task permission to the "Manage User Roles" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create User Role' in the :term:`HMC API` book.

        Returns:

          UserRole:
            The resource object for the new User Role.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.console.uri + '/user-roles',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        user_role = UserRole(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return user_role


class UserRole(BaseResource):
    """
    Representation of a :term:`User Role`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.UserRoleManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.UserRoleManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, UserRoleManager), \
            "Console init: Expected manager type %s, got %s" % \
            (UserRoleManager, type(manager))
        super(UserRole, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this User Role.

        The User Role must be user-defined. System-defined User Roles cannot be
        deleted.

        Authorization requirements:

        * Task permission to the "Manage User Roles" task.

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
        Update writeable properties of this User Role.

        The User Role must be user-defined. System-defined User Roles cannot be
        updated.

        Authorization requirements:

        * Task permission to the "Manage User Roles" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'User Role object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self.uri, body=properties)

        # The name of User Roles cannot be updated. An attempt to do so should
        # cause HTTPError to be raised in the POST above, so we assert that
        # here, because we omit the extra code for handling name updates:
        assert self.manager._name_prop not in properties
        self.properties.update(copy.deepcopy(properties))

    @logged_api_call
    def add_permission(self, permitted_object, include_members=False,
                       view_only=True):
        """
        Add permission for the specified permitted object(s) to this User Role,
        thereby granting that permission to all users that have this User Role.

        The granted permission depends on the resource class of the permitted
        object(s):

        * For Task resources, the granted permission is task permission for
          that task.

        * For Group resources, the granted permission is object access
          permission for the group resource, and optionally also for the
          group members.

        * For any other resources, the granted permission is object access
          permission for these resources.

        The User Role must be user-defined.

        Authorization requirements:

        * Task permission to the "Manage User Roles" task.

        Parameters:

          permitted_object (:class:`~zhmcclient.BaseResource` or :term:`string`):
            Permitted object(s), either as a Python resource object (e.g.
            :class:`~zhmcclient.Partition`), or as a resource class string (e.g.
            'partition').

            Must not be `None`.

          include_members (bool): Controls whether for Group resources, the
            operation applies additionally to its group member resources.

            This parameter will be ignored when the permitted object does not
            specify Group resources.

          view_only (bool): Controls whether for Task resources, the operation
            aplies to the view-only version of the task (if `True`), or to
            the full version of the task (if `False`). Only certain tasks
            support a view-only version.

            This parameter will be ignored when the permitted object does not
            specify Task resources.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """  # noqa: E501
        if isinstance(permitted_object, BaseResource):
            perm_obj = permitted_object.uri
            perm_type = 'object'
        elif isinstance(permitted_object, six.string_types):
            perm_obj = permitted_object
            perm_type = 'object-class'
        else:
            raise TypeError(
                "permitted_object must be a string or BaseResource, but is: "
                "{}".format(type(permitted_object)))
        body = {
            'permitted-object': perm_obj,
            'permitted-object-type': perm_type,
            'include-members': include_members,
            'view-only-mode': view_only,
        }
        self.manager.session.post(
            self.uri + '/operations/add-permission',
            body=body)

    @logged_api_call
    def remove_permission(self, permitted_object, include_members=False,
                          view_only=True):
        """
        Remove permission for the specified permitted object(s) from this User
        Role, thereby no longer granting that permission to all users that have
        this User Role.

        The granted permission depends on the resource class of the permitted
        object(s):

        * For Task resources, the granted permission is task permission for
          that task.

        * For Group resources, the granted permission is object access
          permission for the group resource, and optionally also for the
          group members.

        * For any other resources, the granted permission is object access
          permission for these resources.

        The User Role must be user-defined.

        Authorization requirements:

        * Task permission to the "Manage User Roles" task.

        Parameters:

          permitted_object (:class:`~zhmcclient.BaseResource` or :term:`string`):
            Permitted object(s), either as a Python resource object (e.g.
            :class:`~zhmcclient.Partition`), or as a resource class string (e.g.
            'partition').

            Must not be `None`.

          include_members (bool): Controls whether for Group resources, the
            operation applies additionally to its group member resources.

            This parameter will be ignored when the permitted object does not
            specify Group resources.

          view_only (bool): Controls whether for Task resources, the operation
            aplies to the view-only version of the task (if `True`), or to
            the full version of the task (if `False`). Only certain tasks
            support a view-only version.

            This parameter will be ignored when the permitted object does not
            specify Task resources.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """  # noqa: E501
        if isinstance(permitted_object, BaseResource):
            perm_obj = permitted_object.uri
            perm_type = 'object'
        elif isinstance(permitted_object, six.string_types):
            perm_obj = permitted_object
            perm_type = 'object-class'
        else:
            raise TypeError(
                "permitted_object must be a string or BaseResource, but is: "
                "{}".format(type(permitted_object)))
        body = {
            'permitted-object': perm_obj,
            'permitted-object-type': perm_type,
            'include-members': include_members,
            'view-only-mode': view_only,
        }
        self.manager.session.post(
            self.uri + '/operations/remove-permission',
            body=body)
