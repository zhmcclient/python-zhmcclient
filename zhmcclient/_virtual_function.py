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
A **Virtual Function** represents a unique connection between the partition
and a accelerator adapter like System z Enterprise Data Compression (zEDC)
that is configured on a physical z Systems or LinuxONE computer
that is in DPM mode (Dynamic Partition Manager mode).
Objects of this class are not provided when the CPC is not in DPM mode.

A Virtual Function is always contained in a partition.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['VirtualFunctionManager', 'VirtualFunction']


class VirtualFunctionManager(BaseManager):
    """
    Manager object for Virtual Functions. This manager object is scoped
    to the Virtual Functions of a particular Partition.

    Derived from :class:`~zhmcclient.BaseManager`;
    see there for common methods and attributes.
    """

    def __init__(self, partition):
        """
        Parameters:

          partition (:class:`~zhmcclient.Partition`):
            Partition defining the scope for this manager object.
        """
        super(VirtualFunctionManager, self).__init__(partition)

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: Parent object (Partition)
        defining the scope for this manager object.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the Virtual Functions in scope of this manager object.

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
        Create and configures a Virtual Function with
        the specified resource properties.

        Parameters:

          properties (dict): Properties for the new Virtual Function.
            See the section in the :term:`HMC API` about the specific HMC
            operation and about the 'Create Virtual Function' description
            of the members of the passed properties dict.

        Returns:

          VirtualFunction: The resource object for the new virtual function.
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
    Representation of a Virtual Function.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Properties of a VirtualFunction:
      See the sub-section 'Data model - Virtual Function Element Object'
      of the section 'Partition object' in the :term:`HMC API`.
    """

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.VirtualFunctionManager`):
            Manager object for this resource.

          uri (string):
            Canonical URI path of the VirtualFunction object.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, VirtualFunctionManager)
        super(VirtualFunction, self).__init__(manager, uri, properties)

    def delete(self):
        """
        Deletes this Virtual Function.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self._uri)

    def update_properties(self, properties):
        """
        Updates one or more of the writable properties of Virtual Function
        with the specified resource properties.

        Parameters:

          properties (dict): Updated properties for the Virtual Function.
            See the sub-section 'Data model - Virtual Function Element Object'
            of the section 'Partition object' in the :term:`HMC API`.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self._uri, body=properties)
