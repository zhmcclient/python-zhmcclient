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
An :term:`Adapter` is a physical adapter card (e.g. OSA-Express adapter,
Crypto adapter) or a logical adapter (e.g. HiperSockets switch).

Adapter resources are contained in :term:`CPC` resources.

Adapters only exist in CPCs that are in DPM mode.

There are four types of Adapters:

1. Network Adapters:
   Network adapters enable communication through different networking
   transport protocols. These network adapters are OSA-Express,
   HiperSockets and RoCE-Express.
   DPM automatically discovers OSA-Express and RoCE-Express adapters
   because they are physical cards that are installed on the CPC.
   In contrast, HiperSockets are logical adapters and must be
   created and configured by an administrator using the 'Create Hipersocket'
   operation (see create_hipersocket()).
   Network Interface Cards (NICs) provide a partition with access to networks.
   Each NIC represents a unique connection between the partition
   and a specific network adapter.

2. Storage Adapters:
   Fibre Channel connections provide high-speed connections between CPCs
   and storage devices.
   DPM automatically discovers any storage adapters installed on the CPC.
   Host bus adapters (HBAs) provide a partition with access to external
   storage area networks (SANs) and devices that are connected to a CPC.
   Each HBA represents a unique connection between the partition
   and a specific storage adapter.

3. Accelerator Adapters:
   Accelerator adapters provide specialized functions to
   improve performance or use of computer resource like the IBM System z
   Enterprise Data Compression (zEDC) feature.
   DPM automatically discovers accelerators that are installed on the CPC.
   An accelerator virtual function provides a partition with access
   to zEDC features that are installed on a CPC.
   Each virtual function represents a unique connection between
   the partition and a physical feature card.

4. Crypto Adapters:
   Crypto adapters provide cryptographic processing functions.
   DPM automatically discovers cryptographic features that are installed
   on the CPC.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._port import PortManager

__all__ = ['AdapterManager', 'Adapter']


class AdapterManager(BaseManager):
    """
    Manager providing access to the :term:`Adapters <Adapter>` in a particular
    :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible as properties in higher level resources (in this case, the
    :class:`~zhmcclient.Cpc` object).
    """

    def __init__(self, cpc):
        # This function should not go into the docs.
        # Parameters:
        #   cpc (:class:`~zhmcclient.Cpc`):
        #     CPC defining the scope for this manager.
        super(AdapterManager, self).__init__(Adapter, cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: :term:`CPC` defining the scope for this
        manager.
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
        adapters_res = self.session.get(self.cpc.uri + '/adapters')
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
        Create and configure a HiperSockets Adapter in this CPC.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Hipersocket' in the :term:`HMC API` book.

        Returns:

          Adapter:
            The resource object for the new HiperSockets Adapter.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.cpc.uri + '/adapters', body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = properties.copy()
        props.update(result)
        return Adapter(self, props['object-uri'], props)


class Adapter(BaseResource):
    """
    Representation of an :term:`Adapter`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of an Adapter, see section 'Data model' in section
    'Adapter object' in the :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.AdapterManager`).
    """

    def __init__(self, manager, uri, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.AdapterManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        if not isinstance(manager, AdapterManager):
            raise AssertionError("Adapter init: Expected manager type %s, "
                                 "got %s" %
                                 (AdapterManager, type(manager)))
        super(Adapter, self).__init__(manager, uri, properties,
                                      uri_prop='object-uri',
                                      name_prop='name')
        # The manager objects for child resources (with lazy initialization):
        self._ports = None

    @property
    def ports(self):
        """
        :class:`~zhmcclient.PortManager`: Access to the :term:`Ports <Port>` of
        this Adapter.
        """
        # We do here some lazy loading.
        if not self._ports:
            self._ports = PortManager(self)
        return self._ports

    def delete(self):
        """
        Delete this Adapter.

        The Adapter must be a HiperSockets Adapter.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self.uri)

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
        self.manager.session.post(self.uri, body=properties)
