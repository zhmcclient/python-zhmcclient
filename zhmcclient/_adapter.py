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
An **Adapter** object represents a single adapter of a physical z Systems
or LinuxONE computer that is in DPM mode (Dynamic Partition Manager mode).
Objects of this class are not provided when the CPC is not in DPM mode.

Most of the adapters are physical adapters which are installed
in the I/O cage or drawer of a physical processor frame.
But there also are not physical adapters like HiperSockets.

There are four types of adapter types:

1. Network:
   Network adapters enable communication through different networking
   transport protocols. These network adapters are OSA-Express,
   HiperSockets and 10 GbE RoCE Express.
   DPM automatically discovers OSA-Express and RoCE-Express adapters
   because they are physical cards that are installed on the CPC.
   In contrast, HiperSockets are not physical adapters and must be
   installed and configured by an administrator using the 'Create Hipersocket'
   operation (see create_hipersocket()).
   Network interface cards (NICs) provide a partition with access to networks.
   Each NIC represents a unique connection between the partition
   and a specific network adapter.

2. Storage:
   Fibre Channel connections provide high-speed connections between CPCs
   and storage devices.
   DPM automatically discovers any storage adapters installed on the CPC.
   Host bus adapters (HBAs) provide a partition with access to external
   storage area networks (SANs) and devices that are connected to a CPC.
   Each HBA represents a unique connection between the partition
   and a specific storage adapter.

3. Accelerators:
   Accelerators are adapters that provide specialized functions to
   improve performance or use of computer resource like the IBM System z
   Enterprise Data Compression (zEDC) feature.
   DPM automatically discovers accelerators that are installed on the CPC.
   An accelerator virtual function provides a partition with access
   to zEDC features that are installed on a CPC.
   Each virtual function represents a unique connection between
   the partition and a physical feature card.

4. Cryptos:
   Cryptos are adapters that provide cryptographic processing functions.
   DPM automatically discovers cryptographic features that are installed
   on the CPC.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['AdapterManager', 'Adapter']


class AdapterManager(BaseManager):
    """
    Manager object for Adapters. This manager object is scoped to the
    adapters of a particular CPC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, cpc):
        """
        Parameters:

          cpc (:class:`~zhmcclient.Cpc`):
            CPC defining the scope for this manager object.
        """
        super(AdapterManager, self).__init__(cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: Parent object (CPC) defining the scope for
        this manager object.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the adapters in scope of this manager object.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.Adapter` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.cpc.get_property('object-uri')
        adapters_res = self.session.get(cpc_uri + '/adapters')
        adapter_list = []
        if adapters_res:
            adapter_items = adapters_res['adapters']
            for adapter_props in adapter_items:
                adapter = Adapter(self, adapter_props['object-uri'],
                                  adapter_props)
                if full_properties:
                    adapter.pull_full_properties()
                adapter_list.append(adapter)
        return adapter_list

    def create_hipersocket(self, properties):
        """
        Create and configures a HiperSockets adapter
        with the specified resource properties.

        Parameters:

          properties (dict): Properties for the new adapter.
            See the section in the :term:`HMC API` about the specific HMC
            operation and about the 'Create Hipersocket'
            description of the members of the passed properties
            dict.

        Returns:

          string: The resource URI of the new adapter.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.cpc.get_property('object-uri')
        result = self.session.post(cpc_uri + '/adapters', body=properties)
        return result['object-uri']


class Adapter(BaseResource):
    """
    Representation of an Adapter.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Properties of an Adapter:
      See the sub-section 'Data model' of the section 'Adapter object'
      in the :term:`HMC API`.
    """

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.AdapterManager`):
            Manager object for this resource.

          uri (string):
            Canonical URI path of the Adapter object.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, AdapterManager)
        super(Adapter, self).__init__(manager, uri, properties)

    def delete(self):
        """
        Deletes this adapter.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        adapter_uri = self.get_property('object-uri')
        self.manager.session.delete(adapter_uri)

    def update_properties(self, properties):
        """
        Updates one or more of the writable properties of a adapter
        with the specified resource properties.

        Parameters:

          properties (dict): Updated properties for the adapter.
            See the section in the :term:`HMC API` about
            the specific HMC operation 'Update Adapter Properties'
            description of the members of the passed properties
            dict.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        adapter_uri = self.get_property('object-uri')
        self.manager.session.post(adapter_uri, body=properties)
