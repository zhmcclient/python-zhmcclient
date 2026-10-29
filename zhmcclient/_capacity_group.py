# Copyright 2021 IBM Corp. All Rights Reserved.
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
A :term:`Capacity Group` is a group of :term:`partitions <Partition>` that
allows defining a capping for the total amount of physical processors consumed
by the Partitions in the group. The Partitions must be defined with shared
processors, and a Partition can be a member of at most one Capacity Group.

Capacity Group resources are contained in CPC resources.

Capacity Groups only exist in :term:`CPCs <CPC>` that are in DPM mode.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_CAPACITY_GROUP

__all__ = ['CapacityGroupManager', 'CapacityGroup']


class CapacityGroupManager(BaseManager):
    """
    Manager providing access to the :term:`Capacity Groups <Capacity Group>`
    in a particular :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Cpc` object (in DPM mode):

    * :attr:`~zhmcclient.Cpc.capacity_groups`

    HMC/SE version requirements:

    * SE version >= 2.13.1
    """

    def __init__(self, cpc):
        # This function should not go into the docs.
        # Parameters:
        #   cpc (:class:`~zhmcclient.Cpc`):
        #     CPC defining the scope for this manager.

        super().__init__(
            resource_class=CapacityGroup,
            class_name=RC_CAPACITY_GROUP,
            session=cpc.manager.session,
            parent=cpc,
            base_uri=f'{cpc.uri}/capacity-groups',
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=[],
            list_has_name=False)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: :term:`CPC` defining the scope
        for this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the Capacity Groups in this CPC.

        The properties in the returned resource objects are by default those
        returned by the
        "List Capacity Groups of a CPC"
        HMC operation defined in the :term:`HMC API` book and can be expanded
        with the "full_properties" and "additional_properties" parameters of
        this method.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The listing of resources is handled by performing an HMC list operation
        in context of the parent resource, in an optimized way. For details,
        see :ref:`Listing resources`.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this CPC.

        Parameters:

          full_properties (bool):
            If `True`, the set of properties in the returned resource objects
            will be expanded to the full set of readable properties defined in
            the data model for
            Capacity Group objects
            in the :term:`HMC API` book.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

          additional_properties (list of string):
            A list of property names.
            If specified, the set of properties in the returned resource objects
            will be expanded with the specified properties.
            `None` is treated the same as an empty list.

        Returns:

          : A list of :class:`~zhmcclient.CapacityGroup` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
          :exc:`~zhmcclient.FilterPropertyNotFound`
        """
        result_prop = 'capacity-groups'
        list_uri = f'{self.cpc.uri}/capacity-groups'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args,
            additional_properties)

    @logged_api_call
    def create(self, properties):
        """
        Create a Capacity Group in this CPC.

        The new Capacity Group initially has no partitions.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Manage Processor Sharing" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Capacity Group' in the :term:`HMC API` book.

        Returns:

          CapacityGroup:
            The resource object for the new Capacity Group.
            The object will have its 'element-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.cpc.uri + '/capacity-groups',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        capacity_group = CapacityGroup(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return capacity_group


class CapacityGroup(BaseResource):
    """
    Representation of a :term:`Capacity Group`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of a Capacity Group resource, see section
    'Data model' in section 'Capacity Group element object' in the
    :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.CapacityGroupManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.CapacityGroupManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, CapacityGroupManager), (
            "CapacityGroup init: Expected manager type "
            f"{CapacityGroupManager}, got {type(manager)}")
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this Capacity Group.

        The Capacity Group must not contain any Partitions.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to the CPC containing this Capacity Group.
        * Task permission to the "Manage Processor Sharing" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.delete(self._uri, resource=self)
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))
        self.cease_existence_local()

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this Capacity Group.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to the CPC containing this Capacity Group.
        * Task permission to the "Manage Processor Sharing" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'Capacity Group element object'
            in the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, resource=self, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)

    @logged_api_call
    def add_partition(self, partition):
        """
        Add a Partition to this Capacity Group.

        Upon successful completion, the amount of processing capacity that
        could be used by this Partition becomes governed by the absolute
        cap values defined for this Capacity Group.

        A Partition cannot become a member of more than one Capacity Group.
        The Partition must be defined with shared processors and the
        Capacity Group must specify nonzero cap values for the processor types
        used by the Partition. The Partition must be on the same CPC as the
        Capacity Group and must not yet be a member of this (or any other)
        Capacity Group.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to the CPC containing this Capacity Group.
        * Task permission to the "Manage Processor Sharing" task.

        Parameters:

          partition (:class:`~zhmcclient.Partition`): The partition to be added.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'partition-uri': partition.uri,
        }
        self.manager.session.post(
            self.uri + '/operations/add-partition', resource=self,
            body=body)

    @logged_api_call
    def remove_partition(self, partition):
        """
        Remove a Partition from this Capacity Group.

        Upon successful completion, the amount of processing capacity that
        could be used by this Partition is no longer governed by the absolute
        cap values defined for this Capacity Group.

        The Partition must be a member of this Capacity Group.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to the CPC containing this Capacity Group.
        * Task permission to the "Manage Processor Sharing" task.

        Parameters:

          partition (:class:`~zhmcclient.Partition`): The partition to be
            removed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'partition-uri': partition.uri,
        }
        self.manager.session.post(
            self.uri + '/operations/remove-partition', resource=self,
            body=body)
