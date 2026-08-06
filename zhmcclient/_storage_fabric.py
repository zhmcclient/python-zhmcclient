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
A :term:`Storage Fabric` represents a single storage fabric in the FICON
configuration associated with a DPM-enabled CPC.

A storage fabric is a collection of interconnected storage switches. If the
storage configuration contains multiple storage sites, a storage fabric can,
and typically does, span those sites.

The Storage Fabric object APIs provide access to the set of storage fabrics
within the FICON configuration associated with a CPC that is enabled for DPM.
APIs exist to create and delete storage fabrics, list storage fabrics, query
storage fabric properties, and update selected properties of storage fabrics.

The :term:`Storage Fabric` resources are accessible via the
:attr:`~zhmcclient.Console.storage_fabrics` property of the
:class:`~zhmcclient.Console` object.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_STORAGE_FABRIC


__all__ = ['StorageFabricManager', 'StorageFabric']


class StorageFabricManager(BaseManager):
    """
    Manager providing access to the :term:`storage fabrics <storage fabric>`
    of the HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.Console.storage_fabrics` of a
      :class:`~zhmcclient.Console` object.
    """

    def __init__(self, console):
        # This function should not go into the docs.
        # Parameters:
        #   console (:class:`~zhmcclient.Console`):
        #     Console defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        query_props = [
            'cpc-uri',
            'name',
        ]

        super().__init__(
            resource_class=StorageFabric,
            class_name=RC_STORAGE_FABRIC,
            session=console.manager.session,
            parent=console,
            base_uri='/api/storage-fabrics',
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
        List the storage fabrics defined in the HMC.

        Storage fabrics for which the authenticated user does not have
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
            storage fabric is being retrieved, vs. only the following short
            set: ``object-uri``, ``name``, and ``cpc-uri``.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

        Returns:

          : A list of :class:`~zhmcclient.StorageFabric` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        result_prop = 'storage-fabrics'
        list_uri = self._base_uri
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None
        )

    @logged_api_call
    def create(self, properties):
        """
        Create a storage fabric with the specified properties.

        Authorization requirements:

        * Object-access permission to the CPC associated with this storage
          fabric.
        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body
            contents' in section 'Create Storage Fabric' in the
            :term:`HMC API` book.

            Required fields: ``cpc-uri``, ``name``.
            Optional fields: ``description``, ``high-integrity``.

        Returns:

          :class:`~zhmcclient.StorageFabric`: The new storage fabric.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(
            uri=self._base_uri,
            body=properties,
        )
        # The "Create Storage Fabric" operation returns the object-uri of the
        # new storage fabric in the response body.
        uri = result['object-uri']
        name = properties.get(self._name_prop)
        props = copy.deepcopy(properties)
        props[self._uri_prop] = uri
        storage_fabric = StorageFabric(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return storage_fabric


class StorageFabric(BaseResource):
    """
    Representation of a :term:`storage fabric`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.StorageFabricManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.StorageFabricManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, StorageFabricManager), (
            "StorageFabric init: Expected manager type "
            f"{StorageFabricManager}, got {type(manager)}"
        )
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this storage fabric.

        The storage fabric must be empty; it cannot contain any storage
        switches (i.e. its ``storage-switch-uris`` property must be empty).

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(uri=self.uri, resource=self)
        # pylint: disable=protected-access
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None)
        )
        self.cease_existence_local()

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this storage fabric.

        This method serializes with other methods that access or change
        properties on the same Python object.

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the writeable properties of the storage
            fabric resource defined in the :term:`HMC API` book.

            Writeable properties: ``name``, ``description``, ``high-integrity``.

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
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)

    def dump(self):
        """
        Dump this StorageFabric resource with its properties as a resource
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
