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
from ._logging import get_logger, logged_api_call

__all__ = ['PortManager', 'Port']

LOG = get_logger(__name__)


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

        super(PortManager, self).__init__(
            resource_class=Port,
            session=adapter.manager.session,
            parent=adapter,
            uri_prop='element-uri',
            name_prop='name',
            query_props=[],
            list_has_name=False)

    @property
    def adapter(self):
        """
        :class:`~zhmcclient.Adapter`: :term:`Adapter` defining the scope for
        this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the Ports of this Adapter.

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
        resource_obj_list = []
        storage_family = ('ficon')
        network_family = ('osa', 'roce', 'hipersockets')
        if self.adapter.get_property('adapter-family') in storage_family:
            uris = self.adapter.get_property('storage-port-uris')
        elif self.adapter.get_property('adapter-family') in network_family:
            uris = self.adapter.get_property('network-port-uris')
        else:
            return resource_obj_list
        if uris:
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
        if not isinstance(manager, PortManager):
            raise AssertionError("Port init: Expected manager type %s, "
                                 "got %s" %
                                 (PortManager, type(manager)))
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
        self.properties.update(properties.copy())
        if self.manager._name_prop in properties:
            self.manager._name_uri_cache.update(self.name, self.uri)
