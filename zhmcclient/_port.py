# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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

import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call

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

    def __init__(self, adapter, port_type):
        # This function should not go into the docs.
        # Parameters:
        #   adapter (:class:`~zhmcclient.Adapter`):
        #     Adapter defining the scope for this manager.
        #   port_type (string):
        #     Type of Ports managed by this manager:
        #     * `network`: Ports of a network adapter
        #     * `storage`: Ports of a storage adapter
        #     * None: Adapter family without ports

        super(PortManager, self).__init__(
            resource_class=Port,
            session=adapter.manager.session,
            class_name='{}-port'.format(port_type) if port_type else '',
            parent=adapter,
            base_uri='',
            # TODO: Re-enable the following when unit/test_hba.py has been
            # converted to using the zhmcclient mock support:
            # base_uri='{}/{}'.format(adapter.uri, adapter.port_uri_segment),
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=[],
            list_has_name=False)

        self._port_type = port_type

    @property
    def adapter(self):
        """
        :class:`~zhmcclient.Adapter`: :term:`Adapter` defining the scope for
        this manager.
        """
        return self._parent

    @property
    def port_type(self):
        """
        :term:`string`: Type of the Ports managed by this object:

        * ``'network'`` - Ports of a network adapter
        * ``'storage'`` - Ports of a storage adapter
        * ``None`` - Adapter family without ports
        """
        return self._port_type

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the Ports of this Adapter.

        If the adapter does not have any ports, an empty list is returned.

        Authorization requirements:

        * Object-access permission to this Adapter.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          : A list of :class:`~zhmcclient.Port` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        uris_prop = self.adapter.port_uris_prop
        if not uris_prop:
            # Adapter does not have any ports
            return []

        uris = self.adapter.get_property(uris_prop)
        assert uris is not None

        # TODO: Remove the following circumvention once fixed.
        # The following line circumvents a bug for FCP adapters that sometimes
        # causes duplicate URIs to show up in this property:
        uris = list(set(uris))

        resource_obj_list = []
        for uri in uris:

            resource_obj = self.resource_class(
                manager=self,
                uri=uri,
                name=None,
                properties=None)

            if self._matches_filters(resource_obj, filter_args):
                resource_obj_list.append(resource_obj)
                if full_properties:
                    resource_obj.pull_full_properties()

        self._name_uri_cache.update_from(resource_obj_list)
        return resource_obj_list


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

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.PortManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, PortManager), \
            "Port init: Expected manager type %s, got %s" % \
            (PortManager, type(manager))
        super(Port, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this Port.

        Authorization requirements:

        * Object-access permission to the Adapter of this Port.
        * Task permission to the "Adapter Details" task.

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
        self.manager.session.post(self.uri, body=properties)
        # Attempts to change the 'name' property will be rejected by the HMC,
        # so we don't need to update the name-to-URI cache.
        assert self.manager._name_prop not in properties
        self.properties.update(copy.deepcopy(properties))
