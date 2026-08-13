# Copyright 2026 IBM Corp. All Rights Reserved.
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
A :term:`Storage Subsystem` represents a single storage subsystem in the
FICON storage configuration associated with a DPM-enabled CPC.

A storage subsystem describes a physical storage device (e.g. DS8000 series)
that is connected to a storage site via one or more connection endpoints
(storage switches or adapters). It belongs to exactly one storage site.

The Storage Subsystem object APIs provide access to the set of storage
subsystems within the FICON configuration. APIs exist to list and query
storage subsystems, update selected properties, move a subsystem to a
different storage site, and add or remove connection endpoints.

The :term:`Storage Subsystem` resources are accessible via the
:attr:`~zhmcclient.Console.storage_subsystems` property of the
:class:`~zhmcclient.Console` object.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_STORAGE_SUBSYSTEM


__all__ = ['StorageSubsystemManager', 'StorageSubsystem']


class StorageSubsystemManager(BaseManager):
    """
    Manager providing access to the
    :term:`storage subsystems <storage subsystem>` of the HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.Console.storage_subsystems` of a
      :class:`~zhmcclient.Console` object.
    """

    def __init__(self, console):
        # This function should not go into the docs.
        # Parameters:
        #   console (:class:`~zhmcclient.Console`):
        #     Console defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        query_props = [
            'name',
            'storage-site-uri',
        ]

        super().__init__(
            resource_class=StorageSubsystem,
            class_name=RC_STORAGE_SUBSYSTEM,
            session=console.manager.session,
            parent=console,
            base_uri='/api/storage-subsystems',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props,
        )
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
        List the storage subsystems defined in the HMC.

        Storage subsystems for which the authenticated user does not have
        task permission to the "Configure Storage – System Programmer" or
        "Configure Storage – Storage Administrator" tasks are not included.

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

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            storage subsystem is being retrieved, vs. only the following short
            set: ``object-uri``, ``name``, and ``storage-site-uri``.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

        Returns:

          : A list of :class:`~zhmcclient.StorageSubsystem` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        result_prop = 'storage-subsystems'
        list_uri = self._base_uri
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None
        )


class StorageSubsystem(BaseResource):
    """
    Representation of a :term:`storage subsystem`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.StorageSubsystemManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.StorageSubsystemManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, StorageSubsystemManager), (
            "StorageSubsystem init: Expected manager type "
            f"{StorageSubsystemManager}, got {type(manager)}"
        )
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this storage subsystem.

        This calls the "Update Storage Subsystem Properties" operation
        (``POST /api/storage-subsystems/{id}``).

        This method serializes with other methods that access or change
        properties on the same Python object.

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the writeable properties of the storage
            subsystem resource defined in the :term:`HMC API` book.

            Writeable properties include: ``name``, ``description``.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self.uri, resource=self, body=properties)
        # pylint: disable=protected-access
        is_rename = self.manager._name_prop in properties
        if is_rename:
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            self.manager._name_uri_cache.update(self.name, self.uri)

    @logged_api_call
    def move_to_storage_site(self, storage_site_uri):
        """
        Move this storage subsystem to a different storage site.

        This calls the "Move Storage Subsystem to Storage Site" operation
        (``POST /api/storage-subsystems/{id}/operations/move-storage-site``).

        The storage subsystem is moved from its current storage site to the
        specified storage site within the same FICON configuration. The
        ``storage-site-uri`` property of this subsystem is updated, and
        the ``storage-subsystem-uris`` arrays on both the old and new
        storage site objects are updated accordingly.

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          storage_site_uri (str): The canonical URI path of the target
            storage site.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'storage-site-uri': storage_site_uri}
        self.manager.session.post(
            uri=self.uri + '/operations/move-storage-site',
            resource=self,
            body=body,
        )
        self.update_properties_local({'storage-site-uri': storage_site_uri})

    @logged_api_call
    def add_connection_endpoint(self, endpoint_uri, port_id=None):
        """
        Add a connection endpoint to this storage subsystem.

        This calls the "Add Connection Endpoint" operation
        (``POST /api/storage-subsystems/{id}/operations/
        add-connection-endpoint``).

        The new connection endpoint is added to the ``connection-endpoints``
        property of this storage subsystem.

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          endpoint_uri (str): The canonical URI path for the Storage Switch or
            Adapter object to which this subsystem is connected.

          port_id (str or None): A two-character lowercase hexadecimal number
            that represents the switch port. This value is required if
            ``endpoint_uri`` references a Storage Switch object and is
            prohibited if ``endpoint_uri`` references an Adapter object.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'endpoint-uri': endpoint_uri}
        if port_id is not None:
            body['port-id'] = port_id
        self.manager.session.post(
            uri=self.uri + '/operations/add-connection-endpoint',
            resource=self,
            body=body,
        )

    @logged_api_call
    def remove_connection_endpoint(self, endpoint_uri, port_id=None):
        """
        Remove a connection endpoint from this storage subsystem.

        This calls the "Remove Connection Endpoint" operation
        (``POST /api/storage-subsystems/{id}/operations/
        remove-connection-endpoint``).

        The specified connection endpoint is removed from the
        ``connection-endpoints`` property of this storage subsystem.

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          endpoint_uri (str): The canonical URI path for the Storage Switch or
            Adapter object from which this subsystem is to be disconnected.

          port_id (str or None): A two-character lowercase hexadecimal number
            that represents the switch port. This value is required if
            ``endpoint_uri`` references a Storage Switch object and is
            ignored if ``endpoint_uri`` references an Adapter object.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'endpoint-uri': endpoint_uri}
        if port_id is not None:
            body['port-id'] = port_id
        self.manager.session.post(
            uri=self.uri + '/operations/remove-connection-endpoint',
            resource=self,
            body=body,
        )

    def dump(self):
        """
        Dump this StorageSubsystem resource with its properties as a resource
        definition.

        The returned resource definition has the following format::

            {
                # Resource properties:
                "properties": {...},
            }

        Returns:

          dict: Resource definition of this resource.
        """
        resource_dict = super().dump()
        return resource_dict
