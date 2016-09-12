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
A **Port** represents a commuportation endpoint of an Adapter
of a physical z Systems or LinuxONE computer that is in DPM mode
(Dynamic Partition Manager mode).
Objects of this class are not provided when the CPC is not in DPM mode.
A Port is always contained in an Adapter.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['PortManager', 'Port']


class PortManager(BaseManager):
    """
    Manager object for Ports. This manager object is scoped to the Ports
    of a particular Adapter.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, adapter):
        """
        Parameters:

          adapter (:class:`~zhmcclient.Adapter`):
             defining the scope for this manager object.
        """
        super(PortManager, self).__init__(adapter)

    @property
    def adapter(self):
        """
        :class:`~zhmcclient.Adapter`: Parent object (Adapter)
        defining the scope for this manager object.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the Portis of this Adapter.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.Port` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        port_list = []
        storage_family = ('ficon')
        network_family = ('osa', 'roce', 'hipersockets')
        if self.adapter.get_property('adapter-family') in storage_family:
            ports_res = self.adapter.get_property('storage-port-uris')
        elif self.adapter.get_property('adapter-family') in network_family:
            ports_res = self.adapter.get_property('network-port-uris')
        else:
            return port_list
        if ports_res:
            for port_uri in ports_res:
                port = Port(self, port_uri, {'element-uri': port_uri})
                if full_properties:
                    port.pull_full_properties()
                port_list.append(port)
        return port_list


class Port(BaseResource):
    """
    Representation of an :term:`Port`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of an Port resource, see section
    'Data model - Port Element Object' in section 'Adapter object' in the
    :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.PortManager`).
    """

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.PortManager`):
            Manager object for this resource.

          uri (string):
            Canoportal URI path of the Port object.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, PortManager)
        super(Port, self).__init__(manager, uri, properties)

    def update_properties(self, properties):
        """
        Updates one or more of the writable properties of Port
        with the specified resource properties.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model - Port Element Object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self._uri, body=properties)
