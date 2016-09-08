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
A **Host Bus Adapter (HBA)** provides a Partition with access to external
storage area networks (SANs) through a storage adapter.

HBA resources are contained in Partition resources.

HBAs only exist in CPCs that are in DPM mode.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['HbaManager', 'Hba']


class HbaManager(BaseManager):
    """
    Manager providing access to the HBAs in a particular Partition.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, partition):
        """
        Parameters:

          partition (:class:`~zhmcclient.Partition`):
            Partition defining the scope for this manager.
        """
        super(HbaManager, self).__init__(partition)

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: Partition defining the scope for this
        manager.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the HBAs in this Partition.

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
        Create and configure an HBA in this Partition.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create HBA' in the :term:`HMC API` book.

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

    For the properties of an HBA resource, see section
    'Data model - HBA Element Object' in section 'Partition object' in the
    :term:`HMC API` book.
    """

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.HbaManager`):
            Manager for this HBA.

          uri (string):
            Canonical URI path of this HBA.

          properties (dict):
            Properties to be set for this HBA.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, HbaManager)
        super(Hba, self).__init__(manager, uri, properties)

    def delete(self):
        """
        Delete this HBA.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self._uri)

    def update_properties(self, properties):
        """
        Update writeable properties of this HBA.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model - HBA Element Object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self._uri, body=properties)
