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
"dpm-storage-management" feature are no longer exposed.

Virtual storage resource objects are contained in :term:`storage group`
objects.

Storage groups and storage volumes only can be defined in CPCs that are in
DPM mode and that have the "dpm-storage-management" feature enabled.
"""

from __future__ import absolute_import

import re
import copy
# from requests.utils import quote

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import get_logger, logged_api_call

__all__ = ['VirtualStorageResourceManager', 'VirtualStorageResource']

LOG = get_logger(__name__)


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

        super(VirtualStorageResourceManager, self).__init__(
            resource_class=VirtualStorageResource,
            class_name='virtual-storage-resource',
            session=storage_group.manager.session,
            parent=storage_group,
            base_uri='{}/virtual-storage-resources'.format(storage_group.uri),
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

        resource_obj_list = []

        resource_obj = self._try_optimized_lookup(filter_args)
        if resource_obj:
            resource_obj_list.append(resource_obj)
            # It already has full properties
        else:
            query_parms, client_filters = self._divide_filter_args(filter_args)

            resources_name = 'virtual-storage-resources'
            uri = '{}/{}{}'.format(self.storage_group.uri, resources_name,
                                   query_parms)

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


class VirtualStorageResource(BaseResource):
    """
    Representation of a :term:`virtual storage resource`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.VirtualStorageResourceManager`).
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
        assert isinstance(manager, VirtualStorageResourceManager), \
            "VirtualStorageResource init: Expected manager type %s, got %s" % \
            (VirtualStorageResourceManager, type(manager))
        super(VirtualStorageResource, self).__init__(
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
            adapter_mgr = self.manager.storage_group.manager.cpc.adapters
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
        self.manager.session.post(self.uri, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.properties.update(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)
