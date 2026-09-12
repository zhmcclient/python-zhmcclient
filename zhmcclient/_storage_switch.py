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
A :term:`Storage Switch` represents a single physical storage switch in the
FICON storage configuration associated with a DPM-enabled CPC.

A storage switch belongs to exactly one storage site and one storage fabric.
It can be moved between sites and fabrics using dedicated operations.

The Storage Switch object APIs provide access to the set of storage switches
within the FICON configuration associated with a CPC that is enabled for DPM.
APIs exist to define and undefine storage switches, list storage switches,
query storage switch properties, update selected properties, and move a switch
to a different storage site or storage fabric.

The :term:`Storage Switch` resources are accessible via the
:attr:`~zhmcclient.Console.storage_switches` property of the
:class:`~zhmcclient.Console` object.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_STORAGE_SWITCH


__all__ = ['StorageSwitchManager', 'StorageSwitch']


class StorageSwitchManager(BaseManager):
    """
    Manager providing access to the :term:`storage switches <storage switch>`
    of the HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.Console.storage_switches` of a
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
            'domain-id',
        ]

        super().__init__(
            resource_class=StorageSwitch,
            class_name=RC_STORAGE_SWITCH,
            session=console.manager.session,
            parent=console,
            base_uri='/api/storage-switches',
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
        List the storage switches defined in the HMC.

        Storage switches for which the authenticated user does not have
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
            storage switch is being retrieved, vs. only the following short
            set: ``object-uri``, ``name``, ``domain-id``, and
            ``storage-fabric-uri``.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

        Returns:

          : A list of :class:`~zhmcclient.StorageSwitch` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        result_prop = 'storage-switches'
        list_uri = self._base_uri
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None
        )

    @logged_api_call
    def define(self, properties):
        """
        Define a new storage switch with the specified properties.

        This calls the "Define Storage Switch" operation on the HMC console
        (``POST /api/console/operations/define-storage-switch``).

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body
            contents' in section 'Define Storage Switch' in the
            :term:`HMC API` book.

            Required fields: ``domain-id``, ``storage-fabric-uri``,
            ``storage-site-uri``.
            Optional fields: ``name``, ``description``, ``port-count``.

        Returns:

          :class:`~zhmcclient.StorageSwitch`: The new storage switch.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(
            uri='/api/console/operations/define-storage-switch',
            body=properties,
        )
        uri = result['object-uri']
        name = properties.get(self._name_prop)
        props = copy.deepcopy(properties)
        props[self._uri_prop] = uri
        storage_switch = StorageSwitch(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return storage_switch


class StorageSwitch(BaseResource):
    """
    Representation of a :term:`storage switch`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.StorageSwitchManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.StorageSwitchManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, StorageSwitchManager), (
            "StorageSwitch init: Expected manager type "
            f"{StorageSwitchManager}, got {type(manager)}"
        )
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def undefine(self):
        """
        Undefine (delete) this storage switch.

        This calls the "Undefine Storage Switch" operation
        (``POST /api/storage-switches/{id}/operations/undefine``).

        If the storage switch contains switch ports, they are removed as well.

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(
            uri=self.uri + '/operations/undefine',
            resource=self,
            body=None,
        )
        # pylint: disable=protected-access
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None)
        )
        self.cease_existence_local()

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this storage switch.

        This calls the "Update Storage Switch Properties" operation
        (``POST /api/storage-switches/{id}``).

        This method serializes with other methods that access or change
        properties on the same Python object.

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the writeable properties of the storage
            switch resource defined in the :term:`HMC API` book.

            Writeable properties: ``name``, ``description``, ``domain-id``,
            ``port-count``.

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
        Move this storage switch to a different storage site.

        This calls the "Move Storage Switch to Storage Site" operation
        (``POST /api/storage-switches/{id}/operations/move-storage-site``).

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          storage_site_uri (str): The canonical URI path of the target storage
            site.

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
    def move_to_storage_fabric(self, storage_fabric_uri):
        """
        Move this storage switch to a different storage fabric.

        This calls the "Move Storage Switch to Storage Fabric" operation
        (``POST /api/storage-switches/{id}/operations/move-storage-fabric``).

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          storage_fabric_uri (str): The canonical URI path of the target
            storage fabric.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'storage-fabric-uri': storage_fabric_uri}
        self.manager.session.post(
            uri=self.uri + '/operations/move-storage-fabric',
            resource=self,
            body=body,
        )
        self.update_properties_local(
            {'storage-fabric-uri': storage_fabric_uri})

    def dump(self):
        """
        Dump this StorageSwitch resource with its properties as a resource
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
