# Copyright 2024 IBM Corp. All Rights Reserved.
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
A :term:`Partition Link` interconnects two or more
:term:`Partitions <Partition>` that share the same network configuration.

Partition Links have been introduced with SE 2.16. Conceptually, Partition Links
can connect different :term:`CPCs <CPC>`. However, the implementation is currently
limited to the same DPM-enabled CPC. Currently, one Partition Link
resource is always associated with a single CPC at any time.

Partition Links are based on different technologies, indicated in their
``type`` property:

* ``smc-d`` - Shared Memory Communications - Direct Memory Access (SMC-D)
  (Version 2 or later).
  Support for this technology is indicated via :ref:`API feature <API features>`
  "dpm-smcd-partition-link-management".
* ``hipersockets`` - Hipersockets.
  Support for this technology is indicated via :ref:`API feature <API features>`
  "dpm-hipersockets-partition-link-management".
* ``ctc`` - FICON Channel to Channel (CTC) interconnect, using corresponding
  cabling between FICON adapters.
  Support for this technology is indicated via :ref:`API feature <API features>`
  "dpm-ctc-partition-link-management".

Partition Links have a ``state`` property that indicates their current attachment
state to any partitions:

* ``complete`` - All requests for attaching or detaching the partition link to or
  from partitions are complete.
* ``incomplete`` - All requests for attaching or detaching the partition link to
  or from partitions are complete, but the partition link is attached to less
  than 2 partitions.
* ``updating`` - Some requests for attaching or detaching the partition link to
  or from partitions are incomplete.

This section describes the interface for Partition Links using resource class
:class:`~zhmcclient.PartitionLink` and the corresponding manager class
:class:`~zhmcclient.PartitionLinkManager`.

Because conceptually, Partition Links can connect different CPCs, this client
has designed :class:`~zhmcclient.PartitionLink` resources to be available
through the :class:`~zhmcclient.Console` resource, via its
:attr:`~zhmcclient.Console.partition_links` property.

The earlier interfaces for Hipersockets are also supported:

* represented as :class:`~zhmcclient.Adapter`, including support for
  creation and deletion.
* Attachment to a partition is managed via creation and deletion of
  :class:`~zhmcclient.Nic` resources on the partition.
"""


import copy
import re

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import append_query_parms, RC_PARTITION_LINK

__all__ = ['PartitionLinkManager', 'PartitionLink']


class PartitionLinkManager(BaseManager):
    """
    Manager providing access to the :term:`partition links <partition link>` of
    the HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.Console.partition_links` of a
      :class:`~zhmcclient.Console` object.

    HMC/SE version requirements:

    * SE version >= 2.16.0
    * for technology-specific support, see the API features described in
      :ref:`Partition Links`
    """

    def __init__(self, console):
        # This function should not go into the docs.
        # Parameters:
        #   console (:class:`~zhmcclient.Console`):
        #     CPC or HMC defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'cpc-uri',
            'name',
            'type',
            'fulfillment-state',
        ]

        super().__init__(
            resource_class=PartitionLink,
            class_name=RC_PARTITION_LINK,
            session=console.manager.session,
            parent=console,
            base_uri='/api/partition-links',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props)
        self._console = console

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`: The Console object representing the HMC.
        """
        return self._console

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the partition links known to the HMC.

        Partition links for which the authenticated user does not have
        object-access permission are not included.

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

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to any partition links to be included in the
          result.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            partition link is being retrieved, vs. only the following short
            set: "object-uri", "cpc-uri", "name", "fulfillment-state", and
            "type".

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

        Returns:

          : A list of :class:`~zhmcclient.PartitionLink` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'partition-links'
        list_uri = self._base_uri
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None)

    @logged_api_call
    def create(self, properties=None):
        """
        Create a partition link from the input properties.

        The input properties may specify an initial attachment of the partition
        link to one or more partitions.

        Additional attachments to partitions and detachments from partitions
        can be performed with :meth:`~zhmcclient.PartitionLink.modify`.

        The new partition link will be associated with the CPC identified by the
        ``cpc-uri`` input property.

        HMC/SE version requirements:

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to the CPC that will be associated with
          the new partition link.
        * Task permission to the "Create Partition Link" task.
        * Object-access permission to all Partitions for the initially requested
          attachments.
        * Object-access permission to all FICON adapter objects used for the
          CTC connections for the initially requested attachments.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Partition Link' in the :term:`HMC API` book.

            The 'cpc-uri' property identifies the CPC to which the new
            partition link will be associated, and is required to be specified
            in this parameter.

        Returns:

          :class:`~zhmcclient.PartitionLink`:
            The resource object for the new partition link.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # TODO: Adjust implementation

        if properties is None:
            properties = {}

        if 'template-uri' in properties:
            raise ValueError(
                "Property 'template-uri' is not permitted - use the "
                "'template' parameter to create partition links from "
                "templates.")

        if template is not None:
            properties['template-uri'] = template.uri

        result = self.session.post(self._base_uri, body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        partition_link = PartitionLink(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return partition_link


class PartitionLink(BaseResource):
    """
    Representation of a :term:`partition link`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.PartitionLinkManager`).

    HMC/SE version requirements:

    * SE version >= 2.16.0
    * for technology-specific support, see the API features described in
      :ref:`Partition Links`
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.PartitionLinkManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, PartitionLinkManager), (
            f"PartitionLink init: Expected manager type {PartitionLinkManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)
        # The manager objects for child resources (with lazy initialization):
        self._cpc = None

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: The :term:`CPC` to which this partition link
        is associated.

        The returned :class:`~zhmcclient.Cpc` has only a minimal set of
        properties populated.
        """
        # We do here some lazy loading.
        if not self._cpc:
            cpc_uri = self.get_property('cpc-uri')
            cpc_mgr = self.manager.console.manager.client.cpcs
            self._cpc = cpc_mgr.resource_object(cpc_uri)
        return self._cpc

    @logged_api_call
    def list_attached_partitions(self, name=None, status=None):
        """
        Return the partitions to which this partition link is currently
        attached, optionally filtered by partition name and status.

        HMC/SE version requirements:

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to this partition link.

        Parameters:

          name (:term:`string`): Filter pattern (regular expression) to limit
            returned partitions to those that have a matching name. If `None`,
            no filtering for the partition name takes place.

          status (:term:`string`): Filter string to limit returned partitions
            to those  that have a matching status. The value must be a valid
            partition status property value. If `None`, no filtering for the
            partition status takes place.

        Returns:

          List of :class:`~zhmcclient.Partition` objects representing the
          partitions to whivch this partition link is currently attached,
          with a minimal set of properties ('object-id', 'name', 'status').

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # TODO: Adjust implementation

        query_parms = []
        if name is not None:
            append_query_parms(query_parms, 'name', name)
        if status is not None:
            append_query_parms(query_parms, 'status', status)
        query_parms_str = '&'.join(query_parms)
        if query_parms_str:
            query_parms_str = f'?{query_parms_str}'

        uri = f'{self.uri}/operations/get-partitions{query_parms_str}'

        sg_cpc = self.cpc
        part_mgr = sg_cpc.partitions

        result = self.manager.session.get(uri, resource=self)
        props_list = result['partitions']
        part_list = []
        for props in props_list:
            part = part_mgr.resource_object(props['object-uri'], props)
            part_list.append(part)
        return part_list

    def attach_to_partition(self, partition, nics_properties):
        """
        Attach this partition link to a partition, creating one or more NICs in
        the partition.
        """
        pass  # TODO: Implement

    def detach_from_partition(self, partition):
        """
        Detach this partition link from a partition, deleting all corresponding
        NICs from the partition.
        """
        pass  # TODO: Implement

    @logged_api_call
    def delete(self, force_detach=False):
        """
        Delete this partition link on the HMC.

        If there are active partitions to which the partition link is attached,
        the operation will fail by default. The force_detach parameter can be
        used to forcefully detach the partition link from active partitions
        before deleting it.

        HMC/SE version requirements:

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to this partition link.
        * Object-access permission to all partitions that currently have this
          partition link attached.
        * Task permission to the "Delete Partition Link" task.

        Parameters:

            force_detach (bool): TBD

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # TODO: Adjust implementation

        body = {}

        if email_to_addresses:
            body['email-to-addresses'] = email_to_addresses
            if email_cc_addresses:
                body['email-cc-addresses'] = email_cc_addresses
            if email_insert:
                body['email-insert'] = email_insert
        else:
            if email_cc_addresses:
                raise ValueError(
                    "email_cc_addresses must not be specified if there is no "
                    f"email_to_addresses: {email_cc_addresses!r}")
            if email_insert:
                raise ValueError(
                    "email_insert must not be specified if there is no "
                    f"email_to_addresses: {email_insert!r}")

        self.manager.session.post(
            uri=self.uri + '/operations/delete', resource=self, body=body)

        # pylint: disable=protected-access
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))
        self.cease_existence_local()

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this partition link.

        This method can bse used to attach and detach this partition link
        to and from partitions, by modifying the appropriate resource
        properties.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to the CPC that will be associated with
          the new partition link.
        * Task permission to the "Create Partition Link" task.
        * Object-access permission to all Partitions for the initially requested
          attachments.
        * Object-access permission to all FICON adapter objects used for the
          CTC connections for the initially requested attachments.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are listed for operation
            'Modify Partition Link' in section 'Partition Link object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        uri = f'{self.uri}/operations/modify'
        self.manager.session.post(uri, resource=self, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)

    def dump(self):
        """
        Dump this PartitionLink resource with its properties as a resource
        definition.

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
