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
A :term:`Port` is a physical connector port (jack) of an :term:`Adapter`.

Port resources are contained in Adapter resources.

Ports only exist in :term:`CPCs <CPC>` that are in DPM mode.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['PortManager', 'Port']


class PortManager(BaseManager):
    """
    Manager providing access to the :term:`Ports <Port>` of a particular
    :term:`Adapter`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible as properties in higher level resources (in this case, the
    :class:`~zhmcclient.Adapter` object).
    """

    def __init__(self, adapter):
        # This function should not go into the docs.
        # Parameters:
        #   adapter (:class:`~zhmcclient.Adapter`):
        #     Adapter defining the scope for this manager.
        super(PortManager, self).__init__(Port, adapter)

    @property
    def adapter(self):
        """
        :class:`~zhmcclient.Adapter`: :term:`Adapter` defining the scope for
        this manager.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the Ports of this Adapter.

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
                port = Port(self, port_uri)
                if full_properties:
                    port.pull_full_properties()
                port_list.append(port)
        return port_list


class Port(BaseResource):
    """
    Representation of a :term:`Port`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of a Port, see section
    'Data model - Port Element Object' in section 'Adapter object' in the
    :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.PortManager`).
    """

    def __init__(self, manager, uri, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.PortManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        if not isinstance(manager, PortManager):
            raise AssertionError("Port init: Expected manager type %s, "
                                 "got %s" %
                                 (PortManager, type(manager)))
        super(Port, self).__init__(manager, uri, properties,
                                   uri_prop='element-uri',
                                   name_prop='name')

    def update_properties(self, properties):
        """
        Update writeable properties of this Port.

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
