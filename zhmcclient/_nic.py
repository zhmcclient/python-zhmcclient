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
A **NIC** object represents a single Network interface card (NIC)
of a physical z Systems or LinuxONE computer that is in DPM mode
(Dynamic Partition Manager mode).
Objects of this class are not provided when the CPC is not in DPM mode.
Each NIC represents a unique connection between a partition and
a specific network adapter that is defined or installed on the CPC.

A NIC is always contained in a partition.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['NicManager', 'Nic']


class NicManager(BaseManager):
    """
    Manager object for NICs. This manager object is scoped to the NICs
    of a particular Partition.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, partition):
        """
        Parameters:

          partition (:class:`~zhmcclient.Partition`):
            Partition defining the scope for this manager object.
        """
        super(NicManager, self).__init__(partition)

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: Parent object (Partition)
        defining the scope for this manager object.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the NICs in scope of this manager object.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.Nic` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        nics_res = self.partition.get_property('nic-uris')
        nic_list = []
        if nics_res:
            for nic_uri in nics_res:
                nic = Nic(self, nic_uri, {'element-uri': nic_uri})
                if full_properties:
                    nic.pull_full_properties()
                nic_list.append(nic)
        return nic_list

    def create(self, properties):
        """
        Create and configures a NIC with the specified resource properties.

        Parameters:

          properties (dict): Properties for the new NIC.
            See the section in the :term:`HMC API` about the specific HMC
            operation and about the 'Create NIC' description of the members
            of the passed properties dict.

        Returns:

          Nic: The resource object for the new NIC.
            The object will have its 'element-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        partition_uri = self.partition.get_property('object-uri')
        result = self.session.post(partition_uri + '/nics', body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = properties.copy()
        props.update(result)
        return Nic(self, props['element-uri'], props)


class Nic(BaseResource):
    """
    Representation of a NIC.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Properties of a Nic:
      See the sub-section 'Data model - NIC Element Object' of the section
      'Partition object' in the :term:`HMC API`.
    """

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.NicManager`):
            Manager object for this resource.

          uri (string):
            Canonical URI path of the Nic object.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, NicManager)
        super(Nic, self).__init__(manager, uri, properties)

    def delete(self):
        """
        Deletes this NIC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self._uri)

    def update_properties(self, properties):
        """
        Updates one or more of the writable properties of NIC
        with the specified resource properties.

        Parameters:

          properties (dict): Updated properties for the NIC.
            See the sub-section 'Data model - NIC Element Object'
            of the section 'Partition object' in the :term:`HMC API`.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self._uri, body=properties)
