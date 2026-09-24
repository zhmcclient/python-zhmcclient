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
A :term:`Storage Control Unit` represents a single storage control unit in
the FICON storage configuration associated with a DPM-enabled CPC.

A storage control unit belongs to exactly one
:term:`storage subsystem <Storage Subsystem>` and is identified within that
subsystem by its ``logical-address`` property. Each storage control unit
can have up to 8 :term:`storage paths <Storage Path>` and a set of volume
ranges that describe the storage volumes it manages.

The :term:`Storage Control Unit` resources are accessible via the
:attr:`~zhmcclient.Console.storage_control_units` property of the
:class:`~zhmcclient.Console` object.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_STORAGE_CONTROL_UNIT
from ._storage_path import StoragePathManager


__all__ = ['StorageControlUnitManager', 'StorageControlUnit']


class StorageControlUnitManager(BaseManager):
    """
    Manager providing access to the
    :term:`storage control units <storage control unit>` of the HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.Console.storage_control_units` of a
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
            'logical-address',
        ]

        super().__init__(
            resource_class=StorageControlUnit,
            class_name=RC_STORAGE_CONTROL_UNIT,
            session=console.manager.session,
            parent=console,
            base_uri='/api/storage-control-units',
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
        List the storage control units defined in the HMC.

        Storage control units for which the authenticated user does not have
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
            storage control unit is being retrieved, vs. only the following
            short set: ``object-uri``, ``name``, and ``logical-address``.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

        Returns:

          : A list of :class:`~zhmcclient.StorageControlUnit` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        result_prop = 'storage-control-units'
        list_uri = self._base_uri
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None
        )


class StorageControlUnit(BaseResource):
    """
    Representation of a :term:`storage control unit`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.StorageControlUnitManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.StorageControlUnitManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, StorageControlUnitManager), (
            "StorageControlUnit init: Expected manager type "
            f"{StorageControlUnitManager}, got {type(manager)}"
        )
        super().__init__(manager, uri, name, properties)
        self._storage_paths = None

    @property
    def storage_paths(self):
        """
        :class:`~zhmcclient.StoragePathManager`: Manager for the storage paths
        of this storage control unit.
        """
        if self._storage_paths is None:
            self._storage_paths = StoragePathManager(self)
        return self._storage_paths

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this storage control unit.

        This calls the "Update Storage Control Unit Properties" operation
        (``POST /api/storage-control-units/{id}``).

        This method serializes with other methods that access or change
        properties on the same Python object.

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the writeable properties of the storage
            control unit resource defined in the :term:`HMC API` book.

            Writeable properties include: ``name``, ``description``,
            ``logical-address``.

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
    def undefine(self):
        """
        Undefine (delete) this storage control unit.

        This calls the "Undefine Storage Control Unit" operation
        (``POST /api/storage-control-units/{id}/operations/undefine``).

        If the storage control unit contains storage paths or volume ranges,
        they are removed as well. The control unit's URI is removed from the
        parent storage subsystem's ``storage-control-unit-uris`` list property.

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
    def add_volume_range(self, starting_volume, ending_volume=None,
                         volume_type='base'):
        """
        Add a volume range to this storage control unit.

        This calls the "Add Volume Range" operation
        (``POST /api/storage-control-units/{id}/operations/add-volume-range``).

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          starting_volume (str): A two-character lowercase hexadecimal number
            representing the first unit address in the volume range.

          ending_volume (str or None): A two-character lowercase hexadecimal
            number representing the last unit address. Defaults to
            ``starting_volume`` (a range of one volume).

          volume_type (str): The volume type: ``"base"`` or ``"alias"``.
            Default: ``"base"``.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'starting-volume': starting_volume,
            'type': volume_type,
        }
        if ending_volume is not None:
            body['ending-volume'] = ending_volume
        self.manager.session.post(
            uri=self.uri + '/operations/add-volume-range',
            resource=self,
            body=body,
        )

    @logged_api_call
    def remove_volume_range(self, starting_volume, ending_volume=None,
                            volume_type='base'):
        """
        Remove a volume range from this storage control unit.

        This calls the "Remove Volume Range" operation
        (``POST /api/storage-control-units/{id}/operations/
        remove-volume-range``).

        Authorization requirements:

        * Task permission to the "Configure Storage – System Programmer" or
          "Configure Storage – Storage Administrator" tasks.

        Parameters:

          starting_volume (str): A two-character lowercase hexadecimal number
            representing the first unit address of the range to remove.

          ending_volume (str or None): A two-character lowercase hexadecimal
            number representing the last unit address. Defaults to
            ``starting_volume``.

          volume_type (str): The volume type: ``"base"`` or ``"alias"``.
            Default: ``"base"``.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'starting-volume': starting_volume,
            'type': volume_type,
        }
        if ending_volume is not None:
            body['ending-volume'] = ending_volume
        self.manager.session.post(
            uri=self.uri + '/operations/remove-volume-range',
            resource=self,
            body=body,
        )

    def dump(self):
        """
        Dump this StorageControlUnit resource with its properties as a
        resource definition.

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
