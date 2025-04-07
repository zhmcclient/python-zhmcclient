# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_NETWORK_PORT, RC_STORAGE_PORT

__all__ = ['PortManager', 'Port']

# Resource class names, by port type:
PORT_CLASSES = {
    'network': RC_NETWORK_PORT,
    'storage': RC_STORAGE_PORT,
    None: '',
}


class PortManager(BaseManager):
    """
    Manager providing access to the :term:`Ports <Port>` of a particular
    :term:`Adapter`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible as properties in higher level resources (in this case, the
    :class:`~zhmcclient.Adapter` object).

    HMC/SE version requirements:

    * SE version >= 2.13.1
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

        try:
            port_class = PORT_CLASSES[port_type]
        except KeyError:
            raise ValueError(f"Unknown port type: {port_type}")

        super().__init__(
            resource_class=Port,
            session=adapter.manager.session,
            class_name=port_class,
            parent=adapter,
            base_uri='',
            # TODO: Re-enable the following when unit/test_hba.py has been
            # converted to using the zhmcclient mock support:
            # base_uri=f'{adapter.uri}/{adapter.port_uri_segment}'
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

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The listing of resources is handled in an optimized way:

        * If this manager is enabled for :ref:`auto-updating`, a locally
          maintained resource list is used (which is automatically updated via
          inventory notifications from the HMC) and the provided filter
          arguments are applied.

        * Otherwise, if the filter arguments specify the resource name as a
          single filter argument with a straight match string (i.e. without
          regular expressions), an optimized lookup is performed based on a
          locally maintained name-URI cache.

        * Otherwise, the corresponding array property for this resource in the
          parent object is used to list the resources, and the provided filter
          arguments are applied.

        HMC/SE version requirements:

        * SE version >= 2.13.1

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

        return self._list_with_parent_array(
            self.adapter, uris_prop, full_properties, filter_args)


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

    HMC/SE version requirements:

    * SE version >= 2.13.1
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
        assert isinstance(manager, PortManager), (
            f"Port init: Expected manager type {PortManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this Port.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.13.1

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
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, resource=self, body=properties)
        # Attempts to change the 'name' property will be rejected by the HMC,
        # so we don't need to update the name-to-URI cache.
        assert self.manager._name_prop not in properties
        self.update_properties_local(copy.deepcopy(properties))

    def dump(self):
        """
        Dump the Port resource with its properties as a resource definition.

        If the adapter of this port is a FICON adapter in the not-configured
        state, the port properties cannot be retrieved from the HMC, so
        an empty dict is returned.

        Otherwise, the returned resource definition has the following format::

            {
                "properties": {...},
            }

        Returns:

          dict: Resource definition of this Port resource.
        """
        resource_dict = {}
        adapter = self.manager.parent

        if adapter.prop('type') != 'not-configured':
            # "Get Storage Port Properties" on the port of an unconfigured FICON
            # adapter would return HTTP 404,4: "Get for Storage Port Properties
            # is not supported for this card type".
            self.pull_full_properties()
            resource_dict['properties'] = dict(self._properties)
            # No child resources
        return resource_dict
