# Copyright 2023 IBM Corp. All Rights Reserved.
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
A :term:`Group` is a user-defined group of resources that are managed by the
HMC.

Groups can be used for example in User Role permissions.

Groups can be one of two kinds:

* pattern-matching groups: Membership is implicit and the result of pattern
  matching on the resource name. This is supported only for members that are
  CPCs, Logical Partitions (i.e. classic mode), or other Groups.

* explicit groups: Each member is added and removed explicitly, using the
  :meth:`Group.add_member` and :meth:`Group.remove_member` methods.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_GROUP

__all__ = ['GroupManager', 'Group']


class GroupManager(BaseManager):
    """
    Manager providing access to the :term:`Groups <Group>` exposed by the
    HMC this client is connected to.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    HMC/SE version requirements: None
    """

    def __init__(self, console):
        # This function should not go into the docs.
        # Parameters:
        #   console (:class:`~zhmcclient.Console`):
        #      Console object representing the HMC.

        # Resource properties that are supported as filter query parameters
        # (for server-side filtering).
        query_props = [
            'name',
        ]

        super().__init__(
            resource_class=Group,
            class_name=RC_GROUP,
            session=console.manager.session,
            parent=console,
            base_uri='/api/groups',
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
    def list(self, full_properties=False, filter_args=None):
        """
        List the Groups managed by the HMC this client is connected to.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to any Group to be included in the result.

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

          : A list of :class:`~zhmcclient.Group` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'groups'
        list_uri = '/api/groups'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None)

    @logged_api_call
    def create(self, properties):
        """
        Create a Group in the HMC.

        HMC/SE version requirements: None

        Authorization requirements:

        * Task permission to the "Grouping" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Custom Group' in the :term:`HMC API` book.

        Returns:

          Group:
            The resource object for the new Group.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self._base_uri, body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        group = Group(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return group


class Group(BaseResource):
    """
    Representation of a :term:`Group`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.GroupManager`).

    Note that Group objects do not have any writeable properties, so they
    do not have an ``update_properties()`` method.

    HMC/SE version requirements: None
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.GroupManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, GroupManager), (
            f"Group init: Expected manager type {GroupManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)

    def dump(self):
        """
        Dump this Group resource with its properties as a resource definition.

        The returned resource definition has the following format::

            {
                # Resource properties:
                "properties": {...},
            }

        Returns:

          dict: Resource definition of this resource.
        """

        # Dump the resource properties
        resource_dict = super().dump()

        return resource_dict

    # Note: Group resources cannot have their properties updated,
    #       hence there is no update_properties() method.

    @logged_api_call
    def delete(self):
        """
        Delete this Group.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this Group.
        * Task permission to the "Grouping" task.

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

    @logged_api_call
    def add_member(self, uri):
        """
        Add a resource as a new member to the Group.

        The group must be defined without a pattern-matching specification.
        The member resource must not already be a member of this group.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this Group.
        * Object-access permission to the resource that is added as a member.
        * Task permission to the "Grouping" task.

        Parameters:

          uri (:term:`string`): URI of the resource to be added.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'object-uri': uri}
        ops_uri = self.uri + '/operations/add-member'
        self.manager.session.post(ops_uri, resource=self, body=body)

    @logged_api_call
    def remove_member(self, uri):
        """
        Remove a member resource from the Group.

        The group must be defined without a pattern-matching specification.
        The resource must be a member of this group.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this Group.
        * Object-access permission to the resource that is added as a member.
        * Task permission to the "Grouping" task.

        Parameters:

          uri (:term:`string`): URI of the resource to be removed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'object-uri': uri}
        ops_uri = self.uri + '/operations/remove-member'
        self.manager.session.post(ops_uri, resource=self, body=body)

    @logged_api_call
    def list_members(self):
        """
        List Group members.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this Group.
        * Object-access permission to each member resource of the Group.

        Returns:

          list: List of members.
          Each list item is a dictionary with items:

          - "object-uri" (term:`string`): URI of the member resource.
          - "name" (term:`string`): Name of the member resource.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`

        """
        uri = self.uri + '/members'
        result = self.manager.session.get(uri, resource=self)
        return result['members']
