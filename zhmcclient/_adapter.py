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
An **Adapter** resource represents a single adapter in a CPC.
Most of the adapters are physical adapters which are installed in the I/O
drawer of a CPC, but there also are not-physical adapters like HiperSockets.

Adapter resources resources are contained in CPC resources.

Adapters only exist in CPCs that are in DPM mode.

There are four types of Adapters:

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
    Manager providing access to the Adapters in a particular CPC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, cpc):
        """
        Parameters:

          cpc (:class:`~zhmcclient.Cpc`):
            CPC defining the scope for this manager.
        """
        super(AdapterManager, self).__init__(cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: CPC defining the scope for this manager.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the Adapters in this CPC.

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
        Create and configure a HiperSockets Adapter.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Hipersocket' in the :term:`HMC API` book.

        Returns:

          Adapter: The resource object for the new HiperSockets adapter.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.cpc.get_property('object-uri')
        result = self.session.post(cpc_uri + '/adapters', body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = properties.copy()
        props.update(result)
        return Adapter(self, props['object-uri'], props)


class Adapter(BaseResource):
    """
    Representation of an Adapter.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of an Adapter, see section 'Data model' in section
    'Adapter object' in the :term:`HMC API` book.
    """

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.AdapterManager`):
            Manager for this Adapter.

          uri (string):
            Canonical URI path of this Adapter.

          properties (dict):
            Properties to be set for this Adapter.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, AdapterManager)
        super(Adapter, self).__init__(manager, uri, properties)

    def delete(self):
        """
        Delete this Adapter.

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
        Update writeable properties of this Adapter.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'Adapter object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        adapter_uri = self.get_property('object-uri')
        self.manager.session.post(adapter_uri, body=properties)
