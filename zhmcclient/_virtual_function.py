# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
A :term:`Virtual Function` is a logical entity that provides a
:term:`Partition` with access to
:term:`Accelerator Adapters <Accelerator Adapter>`.

Virtual Function resources are contained in Partition resources.

Virtual Functions only exist in :term:`CPCs <CPC>` that are in DPM mode.
"""

from __future__ import absolute_import

import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call

__all__ = ['VirtualFunctionManager', 'VirtualFunction']


class VirtualFunctionManager(BaseManager):
    """
    Manager providing access to the
    :term:`Virtual Functions <Virtual Function>` in a particular
    :term:`Partition`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Partition` object (in DPM mode):

    * :attr:`~zhmcclient.Partition.virtual_functions`
    """

    def __init__(self, partition):
        # This function should not go into the docs.
        # Parameters:
        #   partition (:class:`~zhmcclient.Partition`):
        #     Partition defining the scope for this manager.
        super(VirtualFunctionManager, self).__init__(
            resource_class=VirtualFunction,
            class_name='virtual-function',
            session=partition.manager.session,
            parent=partition,
            base_uri='{}/virtual-functions'.format(partition.uri),
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
    def list(self, full_properties=False, filter_args=None):
        """
        List the Virtual Functions of this Partition.

        Authorization requirements:

        * Object-access permission to this Partition.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          : A list of :class:`~zhmcclient.VirtualFunction` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        resource_obj_list = []
        uris = self.partition.get_property('virtual-function-uris')
        if uris:
            for uri in uris:

                resource_obj = self.resource_class(
                    manager=self,
                    uri=uri,
                    name=None,
                    properties=None)

                if self._matches_filters(resource_obj, filter_args):
                    resource_obj_list.append(resource_obj)
                    if full_properties:
                        resource_obj.pull_full_properties()

        self._name_uri_cache.update_from(resource_obj_list)
        return resource_obj_list

    @logged_api_call
    def create(self, properties):
        """
        Create a Virtual Function in this Partition.

        Authorization requirements:

        * Object-access permission to this Partition.
        * Object-access permission to the backing accelerator Adapter.
        * Task permission for the "Partition Details" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Virtual Function' in the :term:`HMC API` book.

        Returns:

          VirtualFunction:
            The resource object for the new Virtual Function.
            The object will have its 'element-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.partition.uri + '/virtual-functions',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        vf = VirtualFunction(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return vf


class VirtualFunction(BaseResource):
    """
    Representation of a :term:`Virtual Function`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of a Virtual Function, see section
    'Data model - Virtual Function Element Object' in section
    'Partition object' in the :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.VirtualFunctionManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.VirtualFunctionManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, VirtualFunctionManager), \
            "VirtualFunction init: Expected manager type %s, got %s" % \
            (VirtualFunctionManager, type(manager))
        super(VirtualFunction, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this Virtual Function.

        Authorization requirements:

        * Object-access permission to the Partition of this Virtual Function.
        * Task permission for the "Partition Details" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self._uri)
        self.manager._name_uri_cache.delete(
            self.properties.get(self.manager._name_prop, None))

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this Virtual Function.

        Authorization requirements:

        * Object-access permission to the Partition of this Virtual Function.
        * When updating the "adapter-uri" property, object-access permission to
          the Adapter identified in that URI.
        * Task permission for the "Partition Details" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model - Virtual Function element object' in the
            :term:`HMC API` book.

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
