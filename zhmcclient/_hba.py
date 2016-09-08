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
An **HBA** object represents a unique connection between a partition
and a physical FICON channel that is configured on the CPC
of a physical z Systems or LinuxONE computer that is in DPM mode
(Dynamic Partition Manager mode).
Host bus adapters (HBAs) provide a partition with access to external
storage area networks (SANs) and devices that are connected to a CPC.

An HBA is always contained in a partition.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['HbaManager', 'Hba']


class HbaManager(BaseManager):
    """
    Manager object for HBAs. This manager object is scoped to the HBAs
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
        super(HbaManager, self).__init__(partition)

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: Parent object (Partition)
        defining the scope for this manager object.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the HBAs in scope of this manager object.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.Hba` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        hbas_res = self.partition.get_property('hba-uris')
        hba_list = []
        if hbas_res:
            for hba_uri in hbas_res:
                hba = Hba(self, hba_uri, {'element-uri': hba_uri})
                if full_properties:
                    hba.pull_full_properties()
                hba_list.append(hba)
        return hba_list

    def create(self, properties):
        """
        Create and configures an HBA with the specified resource properties.

        Parameters:

          properties (dict): Properties for the new HBA.
            See the section in the :term:`HMC API` about the specific HMC
            operation and about the 'Create HBA' description of the members
            of the passed properties dict.

        Returns:

          Hba: The resource object for the new HBA.
            The object will have its 'element-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        partition_uri = self.partition.get_property('object-uri')
        result = self.session.post(partition_uri + '/hbas', body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = properties.copy()
        props.update(result)
        return Hba(self, props['element-uri'], props)


class Hba(BaseResource):
    """
    Representation of an HBA.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Properties of a Hba:
      See the sub-section 'Data model - HBA Element Object' of the section
      'Partition object' in the :term:`HMC API`.
    """

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.HbaManager`):
            Manager object for this resource.

          uri (string):
            Canohbaal URI path of the Hba object.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, HbaManager)
        super(Hba, self).__init__(manager, uri, properties)

    def delete(self):
        """
        Deletes this HBA.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self._uri)

    def update_properties(self, properties):
        """
        Updates one or more of the writable properties of HBA
        with the specified resource properties.

        Parameters:

          properties (dict): Updated properties for the HBA.
            See the sub-section 'Data model - HBA Element Object'
            of the section 'Partition object' in the :term:`HMC API`.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self._uri, body=properties)
