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
An :term:`AI Accelerator Function` is a logical entity that provides a
:term:`Partition` with access to an AI accelerator adapter of type "ai".

Each AI Accelerator Function is either a physical function (PF) assigned to
a management partition, or a virtual function (VF) assigned to a management
or consumer partition.

AI Accelerator Function resources are contained in Partition resources.

AI Accelerator Functions only exist in :term:`CPCs <CPC>` that are in DPM
mode and have the "ai-adapter" :ref:`API feature <API features>` enabled.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_AI_FUNCTION

__all__ = ['AiAcceleratorFunctionManager', 'AiAcceleratorFunction']


class AiAcceleratorFunctionManager(BaseManager):
    """
    Manager providing access to the
    :term:`AI Accelerator Functions <AI Accelerator Function>` in a particular
    :term:`Partition`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Partition` object (in DPM mode):

    * :attr:`~zhmcclient.Partition.ai_accelerator_functions`

    HMC/SE version requirements:

    * :ref:`API feature <API features>` "ai-adapter"
    """

    def __init__(self, partition):
        # This function should not go into the docs.
        # Parameters:
        #   partition (:class:`~zhmcclient.Partition`):
        #     Partition defining the scope for this manager.
        super().__init__(
            resource_class=AiAcceleratorFunction,
            class_name=RC_AI_FUNCTION,
            session=partition.manager.session,
            parent=partition,
            base_uri=f'{partition.uri}/ai-accelerator-functions',
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=[],
            list_has_name=False)

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: :term:`Partition` defining the scope
        for this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the AI Accelerator Functions in this Partition.

        The properties in the returned resource objects are by default those
        returned by the
        "List Partitions of a CPC"
        HMC operation defined in the :term:`HMC API` book and can be expanded
        with the "full_properties" and "additional_properties" parameters of
        this method.

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The listing of resources is handled by performing an HMC list operation
        in context of the parent resource, in an optimized way. For details,
        see :ref:`Listing resources`.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "ai-adapter"

        Authorization requirements:

        * Object-access permission to this Partition.

        Parameters:

          full_properties (bool):
            If `True`, the set of properties in the returned resource objects
            will be expanded to the full set of readable properties defined in
            the data model for
            NIC element objects within Partition objects
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

          : A list of :class:`~zhmcclient.AiAcceleratorFunction` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        return self._list_with_parent_array(
            self.partition, 'ai-accelerator-function-uris', full_properties,
            filter_args, additional_properties)

    @logged_api_call
    def create(self, adapter_uri, ai_accelerator_functions=None):
        """
        Create one or more AI Accelerator Functions in this Partition.

        This performs the "Create AI Accelerator Functions" HMC operation
        (``POST /api/partitions/{partition-id}/operations/
        create-ai-accelerator-functions``).

        For a management partition (type ``"ssc"``), the
        ``ai_accelerator_functions`` list is required and must contain exactly
        one entry with ``"is-physical-function": true``. A virtual function is
        auto-generated if not specified.

        For a consumer partition, the list must contain only virtual functions
        (``"is-physical-function"`` must be ``false`` or omitted). No physical
        function is allowed.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "ai-adapter"

        Authorization requirements:

        * Object-access permission to this Partition.
        * Object-access permission to the Adapter of type "ai" specified by
          ``adapter_uri``.
        * Task permission to the "Partition Details" task.

        Parameters:

          adapter_uri (string):
            The canonical URI path of the adapter of type ``"ai"`` for which
            AI Accelerator Functions will be created.

          ai_accelerator_functions (list of dict):
            Optional list of AI Accelerator Function property objects
            specifying the property values for the functions to be created.

            Each entry is a dict that may contain the following fields:

            * ``"name"`` (string, optional): Name of the function (1-64 chars).
            * ``"device-number"`` (string, optional): Device number (4 chars).
            * ``"description"`` (string, optional): Description (0-1024 chars).
            * ``"is-physical-function"`` (bool, optional): Whether this is a
              physical function. Set to ``True`` for a management partition's
              physical function. Default: ``False``.

            If ``None``, the field is omitted from the request body (valid for
            consumer partitions).

        Returns:

          list of :class:`~zhmcclient.AiAcceleratorFunction`:
            The resource objects for the newly created AI Accelerator
            Functions, in the same order as returned by the HMC. Each object
            will have its ``"element-uri"`` property set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'adapter-uri': adapter_uri}
        if ai_accelerator_functions is not None:
            body['ai-accelerator-functions'] = ai_accelerator_functions

        result = self.session.post(
            self.partition.uri + '/operations/create-ai-accelerator-functions',
            body=body)

        # Build resource objects from the returned URIs
        ai_function_objects = []
        for uri in result.get('ai-accelerator-function-uris', []):
            ai_func = AiAcceleratorFunction(self, uri, None, None)
            self._name_uri_cache.update(None, uri)
            ai_function_objects.append(ai_func)
        return ai_function_objects

    @logged_api_call
    def delete_functions(self, ai_accelerator_function_uris):
        """
        Delete one or more AI Accelerator Functions from this Partition.

        This performs the "Delete AI Accelerator Functions" HMC operation
        (``POST /api/partitions/{partition-id}/operations/
        delete-ai-accelerator-functions``).

        All URIs in the list must belong to the same adapter of type ``"ai"``
        and to this partition. The list must contain at least 1 and at most 2
        URIs (1 for consumer partitions, 2 for management partitions).

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "ai-adapter"

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Partition Details" task.

        Parameters:

          ai_accelerator_function_uris (list of string):
            The canonical URI paths of the AI Accelerator Functions to delete.
            Minimum length: 1. Maximum length: 2. All URIs must belong to the
            same adapter of type ``"ai"``.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'ai-accelerator-function-uris': ai_accelerator_function_uris}
        self.session.post(
            self.partition.uri + '/operations/delete-ai-accelerator-functions',
            body=body)


class AiAcceleratorFunction(BaseResource):
    """
    Representation of an :term:`AI Accelerator Function`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of an AI Accelerator Function resource, see section
    'Data model - AI Accelerator Function element object' in section
    'Partition object' in the :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.AiAcceleratorFunctionManager`).

    HMC/SE version requirements:

    * :ref:`API feature <API features>` "ai-adapter"
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.AiAcceleratorFunctionManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, AiAcceleratorFunctionManager), (
            "AiAcceleratorFunction init: Expected manager type "
            f"{AiAcceleratorFunctionManager}, got {type(manager)}")
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def get_properties(self):
        """
        Retrieve and return the current properties of this AI Accelerator
        Function.

        This performs the "Get AI Accelerator Function Properties" HMC
        operation (``GET /api/partitions/{partition-id}/
        ai-accelerator-functions/{ai-accelerator-function-id}``).

        The retrieved properties are also stored locally in this object and
        can be accessed via :meth:`~zhmcclient.BaseResource.get_property`.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "ai-adapter"

        Authorization requirements:

        * Object-access permission to the Partition containing this AI
          Accelerator Function.

        Returns:

          dict: The properties of this AI Accelerator Function.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.get(self._uri, resource=self)
        self.update_properties_local(result)
        return result

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this AI Accelerator Function.

        This performs the "Update AI Accelerator Function Properties" HMC
        operation (``POST /api/partitions/{partition-id}/
        ai-accelerator-functions/{ai-accelerator-function-id}``).

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "ai-adapter"

        Authorization requirements:

        * Object-access permission to the Partition containing this AI
          Accelerator Function.
        * Task permission to the "Partition Details" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            The following properties are writable:

            * ``"name"`` (string): New name (1-64 chars).
            * ``"device-number"`` (string): New device number (4 chars).
            * ``"description"`` (string): New description (0-1024 chars).

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, body=properties, resource=self)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)

    @logged_api_call
    def delete(self):
        """
        Delete this AI Accelerator Function.

        This performs the "Delete AI Accelerator Functions" HMC operation for
        this single AI Accelerator Function (see
        :meth:`~zhmcclient.AiAcceleratorFunctionManager.delete_functions`).

        Note that the HMC enforces constraints on which functions can be
        deleted: For example, deleting the physical function of a management
        partition is rejected while consumer partitions have functions on the
        same adapter.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "ai-adapter"

        Authorization requirements:

        * Object-access permission to the Partition containing this AI
          Accelerator Function.
        * Task permission to the "Partition Details" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.delete_functions([self.uri])
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))

        parent_uris = self.manager.parent.get_properties_local(
            'ai-accelerator-function-uris')
        if parent_uris:
            try:
                parent_uris.remove(self.uri)
            except ValueError:
                pass

        self.cease_existence_local()
