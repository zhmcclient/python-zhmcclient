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
A :term:`Storage Path` is an element object nested inside a
:term:`Storage Control Unit`. It defines a communication path from the
storage control unit to a storage adapter, optionally through one or two
storage switches.

The :term:`Storage Path` resources are accessible via the
:attr:`~zhmcclient.StorageControlUnit.storage_paths` property of a
:class:`~zhmcclient.StorageControlUnit` object.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_STORAGE_PATH


__all__ = ['StoragePathManager', 'StoragePath']


class StoragePathManager(BaseManager):
    """
    Manager providing access to the
    :term:`storage paths <storage path>` of a storage control unit.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.StorageControlUnit.storage_paths` of a
      :class:`~zhmcclient.StorageControlUnit` object.
    """

    def __init__(self, storage_control_unit):
        # This function should not go into the docs.
        # Parameters:
        #   storage_control_unit (:class:`~zhmcclient.StorageControlUnit`):
        #     Storage control unit defining the scope for this manager.

        super().__init__(
            resource_class=StoragePath,
            class_name=RC_STORAGE_PATH,
            session=storage_control_unit.manager.session,
            parent=storage_control_unit,
            base_uri=storage_control_unit.uri + '/storage-paths',
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='element-uri',
            query_props=[],
        )
        self._storage_control_unit = storage_control_unit

    @property
    def storage_control_unit(self):
        """
        :class:`~zhmcclient.StorageControlUnit`: The storage control unit
        this manager belongs to.
        """
        return self._storage_control_unit

    @logged_api_call
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the storage paths of this storage control unit.

        The properties in the returned resource objects are by default only
        "element-uri" and "element-id" and can be expanded
        with the "full_properties" and "additional_properties" parameters of
        this method.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The listing of resources is handled by performing an HMC list operation
        in context of the parent resource, in an optimized way. For details,
        see :ref:`Listing resources`.

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          full_properties (bool):
            If `True`, the set of properties in the returned resource objects
            will be expanded to the full set of readable properties defined in
            the data model for
            Storage Path element objects within Storage Control Unit objects
            in the :term:`HMC API` book.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

          additional_properties (list of string):
            A list of property names.
            If specified, the set of properties in the returned resource objects
            will be expanded with the specified properties.
            `None` is treated the same as an empty list.

        Returns:

          : A list of :class:`~zhmcclient.StoragePath` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        result_prop = 'storage-paths'
        list_uri = self._base_uri
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args,
            additional_properties)

    @logged_api_call
    def create(self, properties):
        """
        Create a new storage path in this storage control unit.

        This calls the "Create Storage Path" operation
        (``POST /api/storage-control-units/{id}/storage-paths``).

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body
            contents' in section 'Create Storage Path' in the
            :term:`HMC API` book.

            Required fields: ``adapter-port-uri``.
            Optional fields: ``exit-switch-uri``, ``exit-port``.

        Returns:

          :class:`~zhmcclient.StoragePath`: The new storage path.

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
        uri = result['element-uri']
        props = copy.deepcopy(properties)
        props[self._uri_prop] = uri
        storage_path = StoragePath(self, uri, uri, props)
        return storage_path

    @logged_api_call
    def delete(self, element_id):
        """
        Delete a storage path from this storage control unit.

        This calls the "Delete Storage Path" operation
        (``DELETE /api/storage-control-units/{id}/storage-paths/{path-id}``).

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          element_id (str): The element ID of the storage path to delete.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        path_uri = self._base_uri + '/' + element_id
        self.session.delete(uri=path_uri)


class StoragePath(BaseResource):
    """
    Representation of a :term:`storage path`.

    A storage path is an element object nested inside a
    :term:`storage control unit`. It defines a communication path from the
    control unit to an adapter, optionally through one or two storage switches.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.StoragePathManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.StoragePathManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource (same as URI for storage paths).
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, StoragePathManager), (
            "StoragePath init: Expected manager type "
            f"{StoragePathManager}, got {type(manager)}"
        )
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this storage path.

        This calls the "Update Storage Path Properties" operation
        (``POST /api/storage-control-units/{cu-id}/storage-paths/{path-id}``).

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted. Writeable properties
            include: ``adapter-port-uri``, ``exit-switch-uri``, ``exit-port``.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self.uri, resource=self, body=properties)
        self.update_properties_local(copy.deepcopy(properties))

    @logged_api_call
    def delete(self):
        """
        Delete this storage path.

        This calls the "Delete Storage Path" operation
        (``DELETE /api/storage-control-units/{cu-id}/storage-paths/{path-id}``).

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
        self.cease_existence_local()

    def dump(self):
        """
        Dump this StoragePath resource with its properties as a resource
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
