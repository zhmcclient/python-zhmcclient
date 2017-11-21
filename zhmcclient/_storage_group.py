# Copyright 2018 IBM Corp. All Rights Reserved.
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
Starting with the z14-ZR1 and LinuxONE Rockhopper II machine generations, the
"dpm-storage-management" firmware feature has been introduced to support a
simpler management of FCP and FICON (=ECKD) storage for DPM mode. If machines
of these generations are in DPM mode, the feature is always enabled and cannot
be disabled.

When the "dpm-storage-management" feature is enabled, :term:`storage group`
and :term:`storage volume` resources can be defined on the HMC, and can cause
fulfillment requests to be sent via email to storage administrators.
Once these requests are satisfied on the actual storage subsystem and possibly
SAN switches, the changes are automatically discovered by DPM and reflected
in the state of these resources. Thus, the allocation of actual storage volumes
on the storage subsystem is not performed by DPM.

The sending of email is optional, and if the changes are done by some
automation tool, they will also be discovered automatically. That way, the
whole process of allocating and attaching volumes can be fully automated, if
so desired.

The top level resource objects are :term:`storage groups <storage group>`.
Storage groups are defined globally at the HMC level, and are associated with a
CPC. They can only be associated with one CPC at a time. In the zhmcclient, the
:class:`~zhmcclient.StorageGroup` objects are accessible via the
:attr:`~zhmcclient.ConsoleManager.storage_groups` property.

Storage groups are a grouping mechanism for
:term:`storage volumes <storage volume>`. An FCP-type storage
group can contain only FCP type storage volumes, and a FICON-type storage
group can contain only FICON/ECKD type storage volumes.

Attachment and detachment of volumes to a partition happens at the level of
storage groups, and always applies to all volumes defined in the storage group.

The storage-related z/Architecture devices that are visible to a partition are
different for the two storage architectures: For FCP, the virtualized HBA is
visible as a device, and the storage volumes (LUNs) are not represented as
devices. For FICON, each ECKD volume is visible as a device, but the
virtualized FICON adapter port is not represented as a device. When the
"dpm-storage-management" feature is enabled, each storage-related
z/Architecture device that is visible to a partition is represented as a
:term:`virtual storage resource` object. The virtual storage resource objects
are instantiated automatically when a storage group is attached to a partition.
The :term:`HBA` resource objects known from DPM mode before the introduction of
the "dpm-storage-management" feature are not exposed anymore (their equivalent
are now the :term:`virtual storage resource` objects).

Single storage volumes cannot be attached to partitions, only entire storage
groups can be. In fact, storage volume objects do not even exist outside the
scope of storage groups.
A particular storage volume can be contained in only one storage group.

Storage groups can be listed, created, deleted, and updated, and their storage
volumes can also be listed, created, deleted, and updated.

Storage groups can be attached to zero or more partitions. Attachment to
multiple partitions at the same time is possible for storage groups that are
defined to be shareable. In case of multiple attachments of a storage group, it
contains the storage volume objects only once for all attachments, but the
virtual storage resource objects are instantiated separately for each
attachment.

Storage groups can only be associated with CPCs that have the
"dpm-storage-management" feature enabled.
"""

from __future__ import absolute_import

import copy
import re

from ._manager import BaseManager
from ._resource import BaseResource
from ._storage_volume import StorageVolumeManager
from ._virtual_storage_resource import VirtualStorageResourceManager
from ._logging import get_logger, logged_api_call

__all__ = ['StorageGroupManager', 'StorageGroup']

LOG = get_logger(__name__)


class StorageGroupManager(BaseManager):
    """
    Manager providing access to the :term:`storage groups <storage group>` of
    the HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.Console.storage_groups` of a
      :class:`~zhmcclient.Console` object.
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

        super(StorageGroupManager, self).__init__(
            resource_class=StorageGroup,
            class_name='storage-group',
            session=console.manager.session,
            parent=console,
            base_uri='/api/storage-groups',
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
        List the storage groups defined in the HMC.

        Storage groups for which the authenticated user does not have
        object-access permission are not included.

        Authorization requirements:

        * Object-access permission to any storage groups to be included in the
          result.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            storage volume is being retrieved, vs. only the following short
            set: "object-uri", "cpc-uri", "name", "fulfillment-state", and
            "type".

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

        Returns:

          : A list of :class:`~zhmcclient.StorageGroup` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        resource_obj_list = []

        if filter_args is None:
            filter_args = {}

        resource_obj = self._try_optimized_lookup(filter_args)
        if resource_obj:
            resource_obj_list.append(resource_obj)
            # It already has full properties
        else:
            query_parms, client_filters = self._divide_filter_args(filter_args)
            uri = '{}{}'.format(self._base_uri, query_parms)

            result = self.session.get(uri)
            if result:
                props_list = result['storage-groups']
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
        Create and configure a storage group.

        The new storage group will be associated with the CPC identified by the
        `cpc-uri` input property.

        Authorization requirements:

        * Object-access permission to the CPC that will be associated with
          the new storage group.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Storage Group' in the :term:`HMC API` book.

            The 'cpc-uri' property identifies the CPC to which the new
            storage group will be associated, and is required to be specified
            in this parameter.

        Returns:

          :class:`~zhmcclient.StorageGroup`:
            The resource object for the new storage group.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if properties is None:
            properties = {}

        result = self.session.post(self._base_uri, body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        storage_group = StorageGroup(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return storage_group


class StorageGroup(BaseResource):
    """
    Representation of a :term:`storage group`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.StorageGroupManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.StorageGroupManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, StorageGroupManager), \
            "StorageGroup init: Expected manager type %s, got %s" % \
            (StorageGroupManager, type(manager))
        super(StorageGroup, self).__init__(manager, uri, name, properties)
        # The manager objects for child resources (with lazy initialization):
        self._storage_volumes = None
        self._virtual_storage_resources = None
        self._cpc = None

    @property
    def storage_volumes(self):
        """
        :class:`~zhmcclient.StorageVolumeManager`: Access to the
        :term:`storage volumes <storage volume>` in this storage group.
        """
        # We do here some lazy loading.
        if not self._storage_volumes:
            self._storage_volumes = StorageVolumeManager(self)
        return self._storage_volumes

    @property
    def virtual_storage_resources(self):
        """
        :class:`~zhmcclient.VirtualStorageResourceManager`: Access to the
        :term:`virtual storage resources <Virtual Storage Resource>` in this
        storage group.
        """
        # We do here some lazy loading.
        if not self._virtual_storage_resources:
            self._virtual_storage_resources = \
                VirtualStorageResourceManager(self)
        return self._virtual_storage_resources

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: The :term:`CPC` to which this storage group
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
        Return the partitions to which this storage group is currently
        attached, optionally filtered by partition name and status.

        Authorization requirements:

        * Object-access permission to this storage group.
        * Task permission to the "Configure Storage - System Programmer" task.

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
          partitions to whivch this storage group is currently attached,
          with a minimal set of properties ('object-id', 'name', 'status').

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        query_parms = []
        if name is not None:
            self.manager._append_query_parms(query_parms, 'name', name)
        if status is not None:
            self.manager._append_query_parms(query_parms, 'status', status)
        query_parms_str = '&'.join(query_parms)
        if query_parms_str:
            query_parms_str = '?{}'.format(query_parms_str)

        uri = '{}/operations/get-partitions{}'.format(
            self.uri, query_parms_str)

        sg_cpc = self.cpc
        part_mgr = sg_cpc.partitions

        result = self.manager.session.get(uri)
        props_list = result['partitions']
        part_list = []
        for props in props_list:
            part = part_mgr.resource_object(props['object-uri'], props)
            part_list.append(part)
        return part_list

    @logged_api_call
    def delete(self, email_to_addresses=None, email_cc_addresses=None,
               email_insert=None):
        """
        Delete this storage group and its storage volume resources on the HMC,
        and optionally send emails to storage administrators requesting
        deletion of the storage volumes on the storage subsystem and cleanup of
        any resources related to the storage group (e.g. zones on a SAN switch,
        or host objects on a storage subsystem).

        Authorization requirements:

        * Object-access permission to this storage group.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          email_to_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrator to be notified.
            If `None` or empty, no email will be sent.

          email_cc_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrator to be copied
            on the notification email.
            If `None` or empty, nobody will be copied on the email.
            Must be `None` or empty if `email_to_addresses` is `None` or empty.

          email_insert (:term:`string`): Additional text to be inserted in the
            notification email.
            The text can include HTML formatting tags.
            If `None`, no additional text will be inserted.
            Must be `None` or empty if `email_to_addresses` is `None` or empty.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`ValueError`: Incorrect input arguments
        """

        body = {}

        if email_to_addresses:
            body['email-to-addresses'] = email_to_addresses
            if email_cc_addresses:
                body['email-cc-addresses'] = email_cc_addresses
            if email_insert:
                body['email-insert'] = email_insert
        else:
            if email_cc_addresses:
                raise ValueError("email_cc_addresses must not be specified if "
                                 "there is no email_to_addresses: %r" %
                                 email_cc_addresses)
            if email_insert:
                raise ValueError("email_insert must not be specified if "
                                 "there is no email_to_addresses: %r" %
                                 email_insert)

        self.manager.session.post(
            uri=self.uri + '/operations/delete', body=body)

        self.manager._name_uri_cache.delete(
            self.properties.get(self.manager._name_prop, None))

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this storage group.

        This includes the `storage-volumes` property which contains requests
        for creations, deletions and updates of
        :class:`~zhmcclient.StorageVolume` resources of this storage group.
        As an alternative to this bulk approach for managing storage volumes,
        each :class:`~zhmcclient.StorageVolume` resource can individually be
        created, deleted and updated using the respective methods on
        :attr:`~zhmcclient.StorageGroup.storage_volumes`.

        Authorization requirements:

        * Object-access permission to this storage group.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are listed for operation
            'Modify Storage Group Properties' in section 'Storage Group object'
            in the :term:`HMC API` book. This includes the email addresses
            of the storage administrators.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        uri = '{}/operations/modify'.format(self.uri)
        self.manager.session.post(uri, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.properties.update(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)

    @logged_api_call
    def add_candidate_adapter_ports(self, ports):
        """
        Add a list of storage adapter ports to this storage group's candidate
        adapter ports list.

        This operation only applies to storage groups of type "fcp".

        These adapter ports become candidates for use as backing adapters when
        creating virtual storage resources when the storage group is attached
        to a partition. The adapter ports should have connectivity to the
        storage area network (SAN).

        Candidate adapter ports may only be added before the CPC discovers a
        working communications path, indicated by a "verified" status on at
        least one of this storage group's WWPNs. After that point, all
        adapter ports in the storage group are automatically detected and
        manually adding them is no longer possible.

        Because the CPC discovers working communications paths automatically,
        candidate adapter ports do not need to be added by the user. Any
        ports that are added, are validated by the CPC during discovery,
        and may or may not actually be used.

        Authorization requirements:

        * Object-access permission to this storage group.
        * Object-access permission to the adapter of each specified port.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          ports (:class:`py:list`): List of :class:`~zhmcclient.Port` objects
            representing the ports to be added. All specified ports must not
            already be members of this storage group's candidate adapter ports
            list.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'adapter-port-uris': [p.uri for p in ports],
        }
        self.manager.session.post(
            self.uri + '/operations/add-candidate-adapter-ports',
            body=body)

    @logged_api_call
    def remove_candidate_adapter_ports(self, ports):
        """
        Remove a list of storage adapter ports from this storage group's
        candidate adapter ports list.

        This operation only applies to storage groups of type "fcp".

        Because the CPC discovers working communications paths automatically,
        candidate adapter ports do not need to be managed by the user. Any
        ports that are removed using this function, might actually be added
        again by the CPC dependent on the results of discovery.

        Authorization requirements:

        * Object-access permission to this storage group.
        * Object-access permission to the adapter of each specified port.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          ports (:class:`py:list`): List of :class:`~zhmcclient.Port` objects
            representing the ports to be removed. All specified ports must
            currently be members of this storage group's candidate adapter
            ports list and must not be referenced by any of the group's virtual
            storage resources.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'adapter-port-uris': [p.uri for p in ports],
        }
        self.manager.session.post(
            self.uri + '/operations/remove-candidate-adapter-ports',
            body=body)

    @logged_api_call
    def list_candidate_adapter_ports(self, full_properties=False):
        """
        Return the current candidate storage adapter port list of this storage
        group.

        The result reflects the actual list of ports used by the CPC, including
        any changes that have been made during discovery. The source for this
        information is the 'candidate-adapter-port-uris' property of the
        storage group object.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            candidate storage adapter port is being retrieved, vs. only the
            following short set: "element-uri", "element-id", "class",
            "parent".

            TODO: Verify short list of properties.

        Returns:

          List of :class:`~zhmcclient.Port` objects representing the
          current candidate storage adapter ports of this storage group.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        sg_cpc = self.cpc
        adapter_mgr = sg_cpc.adapters
        port_list = []
        port_uris = self.get_property('candidate-adapter-port-uris')
        if port_uris:
            for port_uri in port_uris:
                m = re.match(r'^(/api/adapters/[^/]*)/.*', port_uri)

                adapter_uri = m.group(1)
                adapter = adapter_mgr.resource_object(adapter_uri)

                port_mgr = adapter.ports
                port = port_mgr.resource_object(port_uri)
                port_list.append(port)
                if full_properties:
                    port.pull_full_properties()

        return port_list
