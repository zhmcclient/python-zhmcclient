# Copyright 2018,2021 IBM Corp. All Rights Reserved.
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
A :term:`virtual storage resource` object represents a storage-related
z/Architecture device that is visible to a partition and that provides access
for that partition to a :term:`storage volume`.

The storage-related z/Architecture devices that are visible to a partition are
different for the two storage architectures: For FCP, the virtualized HBA is
visible as a device, and the storage volumes (LUNs) are not represented as
devices. For FICON, each ECKD volume is visible as a device, but the
virtualized FICON adapter port is not represented as a device.

What the virtual storage resource objects represent, therefore depends on
the storage architecture of the storage volume they are used for:

* For FCP, a virtual storage resource object represents the virtualized HBA
  in the partition that is used to access the LUN. However, each usage of
  the virtual HBA in context of a storage group has its own virtual storage
  resource object.
* For FICON, a virtual storage resource object represents the ECKD volume.

Virtual storage resource objects are instantiated automatically when a storage
group is attached to a partition, and are removed automatically upon
detachment.

The :term:`HBA` resource objects known from DPM mode before introduction of the
"dpm-storage-management" firmware feature are no longer exposed.

Virtual storage resource objects are contained in :term:`storage group`
objects.

Storage groups and storage volumes only can be defined in CPCs that are in
DPM mode and that have the "dpm-storage-management"
:ref:`firmware feature <firmware features>` enabled.
"""


import re
import copy
# from requests.utils import quote

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_VIRTUAL_STORAGE_RESOURCE

__all__ = ['VirtualStorageResourceManager', 'VirtualStorageResource']


class VirtualStorageResourceManager(BaseManager):
    """
    Manager providing access to the :term:`virtual storage resources
    <Virtual Storage Resource>` in a particular :term:`storage group`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.StorageGroup` object:

    * :attr:`~zhmcclient.StorageGroup.virtual_storage_resources`

    HMC/SE version requirements:

    * :ref:`firmware feature <firmware features>` "dpm-storage-management"
    """

    def __init__(self, storage_group):
        # This function should not go into the docs.
        # Parameters:
        #   storage_group (:class:`~zhmcclient.StorageGroup`):
        #     Storage group defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name',
            'device-number',
            'adapter-port-uri',
            'partition-uri',
        ]

        super().__init__(
            resource_class=VirtualStorageResource,
            class_name=RC_VIRTUAL_STORAGE_RESOURCE,
            session=storage_group.manager.session,
            parent=storage_group,
            base_uri=f'{storage_group.uri}/virtual-storage-resources',
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=query_props)

    @property
    def storage_group(self):
        """
        :class:`~zhmcclient.StorageGroup`: :term:`Storage group` defining the
        scope for this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the virtual storage resources in this storage group.

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

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to this storage group.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            storage volume is being retrieved, vs. only the following short
            set: "element-uri", "name", "device-number", "adapter-port-uri",
            and "partition-uri".

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          : A list of :class:`~zhmcclient.VirtualStorageResource` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'virtual-storage-resources'
        list_uri = f'{self.storage_group.uri}/virtual-storage-resources'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None)


class VirtualStorageResource(BaseResource):
    """
    Representation of a :term:`virtual storage resource`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.VirtualStorageResourceManager`).

    HMC/SE version requirements:

    * :ref:`firmware feature <firmware features>` "dpm-storage-management"
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.VirtualStorageResourceManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, VirtualStorageResourceManager), (
            "VirtualStorageResource init: Expected manager type "
            f"{VirtualStorageResourceManager}, got {type(manager)}")
        super().__init__(
            manager, uri, name, properties)
        self._attached_partition = None
        self._adapter_port = None
        self._storage_volume = None

    @property
    def attached_partition(self):
        """
        :class:`~zhmcclient.Partition`: The partition to which this virtual
        storage resource is attached.

        The returned partition object has only a minimal set of properties set
        ('object-id', 'object-uri', 'class', 'parent').

        Note that a virtual storage resource is always attached to a partition,
        as long as it exists.

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to the storage group owning this
          virtual storage resource.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if self._attached_partition is None:
            part_mgr = self.manager.storage_group.manager.cpc.partitions
            part = part_mgr.resource_object(self.get_property('partition-uri'))
            self._attached_partition = part
        return self._attached_partition

    @property
    def adapter_port(self):
        """
        :class:`~zhmcclient.Port`: The storage adapter port associated with
        this virtual storage resource, once discovery has determined which
        port to use for this virtual storage resource.

        This applies to both, FCP and FICON/ECKD typed storage groups.

        The returned adapter port object has only a minimal set of properties
        set ('object-id', 'object-uri', 'class', 'parent').

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to the storage group owning this
          virtual storage resource.
        * Object-access permission to the CPC of the storage adapter.
        * Object-access permission to the storage adapter.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if self._adapter_port is None:
            port_uri = self.get_property('adapter-port-uri')
            assert port_uri is not None
            m = re.match(r'^(/api/adapters/[^/]+)/.*', port_uri)
            adapter_uri = m.group(1)
            adapter_mgr = self.manager.storage_group.cpc.adapters
            filter_args = {'object-uri': adapter_uri}
            adapter = adapter_mgr.find(**filter_args)
            port_mgr = adapter.ports
            port = port_mgr.resource_object(port_uri)
            self._adapter_port = port
        return self._adapter_port

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this virtual storage resource.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to the storage group owning this
          virtual storage resource.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'Virtual Storage Resource object'
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
