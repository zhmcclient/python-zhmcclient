# Copyright 2016 IBM Corp. All Rights Reserved.
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

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['VirtualFunctionManager', 'VirtualFunction']


class VirtualFunctionManager(BaseManager):
    """
    Manager providing access to the
    :term:`Virtual Functions <Virtual Function>` in a particular
    :term:`Partition`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible as properties in higher level resources (in this case, the
    :class:`~zhmcclient.Partition` object).
    """

    def __init__(self, partition):
        # This function should not go into the docs.
        # Parameters:
        #   partition (:class:`~zhmcclient.Partition`):
        #     Partition defining the scope for this manager.
        super(VirtualFunctionManager, self).__init__(partition)

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: :term:`Partition` defining the scope
        for this manager.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the Virtual Functions of this Partition.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.VirtualFunction` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        vfs_res = self.partition.get_property('virtual-function-uris')
        vf_list = []
        if vfs_res:
            for vf_uri in vfs_res:
                vf = VirtualFunction(self, vf_uri, {'element-uri': vf_uri})
                if full_properties:
                    vf.pull_full_properties()
                vf_list.append(vf)
        return vf_list

    def create(self, properties):
        """
        Create a Virtual Function in this Partition.

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
        partition_uri = self.partition.get_property('object-uri')
        result = self.session.post(partition_uri + '/virtual-functions',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = properties.copy()
        props.update(result)
        return VirtualFunction(self, props['element-uri'], props)


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

    def __init__(self, manager, uri, properties):
        # This function should not go into the docs.
        # Parameters:
        #   manager (:class:`~zhmcclient.VirtualFunctionManager`):
        #     Manager object for this Virtual Function.
        #   uri (string):
        #     Canonical URI path of this Virtual Function.
        #   properties (dict):
        #     Properties to be set for this Virtual Function.
        #     See initialization of :class:`~zhmcclient.BaseResource` for
        #     details.
        assert isinstance(manager, VirtualFunctionManager)
        super(VirtualFunction, self).__init__(manager, uri, properties)

    def delete(self):
        """
        Delete this Virtual Function.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self._uri)

    def update_properties(self, properties):
        """
        Update writeable properties of this Virtual Function.

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
        self.manager.session.post(self._uri, body=properties)
