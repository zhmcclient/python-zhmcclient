# Copyright 2016-2021 IBM Corp. All Rights Reserved.
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
A :term:`NIC` (Network Interface Card) is a logical entity that provides a
:term:`Partition` with access to external communication networks through a
:term:`Network Adapter`. More specifically, a NIC connects a Partition with a
:term:`Network Port`, or with a :term:`Virtual Switch` which then connects to
the Network Port.

NIC resources are contained in Partition resources.

NICs only exist in :term:`CPCs <CPC>` that are in DPM mode.
"""

from __future__ import absolute_import

import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_NIC

__all__ = ['NicManager', 'Nic']


class NicManager(BaseManager):
    """
    Manager providing access to the :term:`NICs <NIC>` in a particular
    :term:`Partition`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Partition` object (in DPM mode):

    * :attr:`~zhmcclient.Partition.nics`
    """

    def __init__(self, partition):
        # This function should not go into the docs.
        # Parameters:
        #   partition (:class:`~zhmcclient.Partition`):
        #     Partition defining the scope for this manager.

        super(NicManager, self).__init__(
            resource_class=Nic,
            class_name=RC_NIC,
            session=partition.manager.session,
            parent=partition,
            base_uri='{}/nics'.format(partition.uri),
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=[],
            list_has_name=False)

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: :term:`Partition` defining the scope
        for this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the NICs in this Partition.

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

        Authorization requirements:

        * Object-access permission to this Partition.

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

          : A list of :class:`~zhmcclient.Nic` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        return self._list_with_parent_array(
            self.partition, 'nic-uris', full_properties, filter_args)

    @logged_api_call
    def create(self, properties):
        """
        Create and configure a NIC in this Partition.

        The NIC must be backed by an adapter port (on an OSA, ROCE, or
        Hipersockets adapter).

        The way the backing adapter port is specified in the "properties"
        parameter of this method depends on the adapter type, as follows:

        * For OSA and Hipersockets adapters, the "virtual-switch-uri"
          property is used to specify the URI of the virtual switch that is
          associated with the backing adapter port.

          This virtual switch is a resource that automatically exists as soon
          as the adapter resource exists. Note that these virtual switches do
          not show up in the HMC GUI; but they do show up at the HMC REST API
          and thus also at the zhmcclient API as the
          :class:`~zhmcclient.VirtualSwitch` class.

          The value for the "virtual-switch-uri" property can be determined
          from a given adapter name and port index as shown in the following
          example code (omitting any error handling):

          .. code-block:: python

              partition = ...  # Partition object for the new NIC

              adapter_name = 'OSA #1'  # name of adapter with backing port
              adapter_port_index = 0   # port index of backing port

              adapter = partition.manager.cpc.adapters.find(name=adapter_name)

              vswitches = partition.manager.cpc.virtual_switches.findall(
                  **{'backing-adapter-uri': adapter.uri})

              vswitch = None
              for vs in vswitches:
                  if vs.get_property('port') == adapter_port_index:
                      vswitch = vs
                      break

              properties['virtual-switch-uri'] = vswitch.uri

        * For RoCE adapters, the "network-adapter-port-uri" property is used to
          specify the URI of the backing adapter port, directly.

          The value for the "network-adapter-port-uri" property can be
          determined from a given adapter name and port index as shown in the
          following example code (omitting any error handling):

          .. code-block:: python

              partition = ...  # Partition object for the new NIC

              adapter_name = 'ROCE #1'  # name of adapter with backing port
              adapter_port_index = 0   # port index of backing port

              adapter = partition.manager.cpc.adapters.find(name=adapter_name)

              port = adapter.ports.find(index=adapter_port_index)

              properties['network-adapter-port-uri'] = port.uri

        Authorization requirements:

        * Object-access permission to this Partition.
        * Object-access permission to the backing Adapter for the new NIC.
        * Task permission to the "Partition Details" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create NIC' in the :term:`HMC API` book.

        Returns:

          Nic:
            The resource object for the new NIC.
            The object will have its 'element-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.partition.uri + '/nics',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        nic = Nic(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return nic


class Nic(BaseResource):
    """
    Representation of a :term:`NIC`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of a NIC resource, see section
    'Data model - NIC Element Object' in section 'Partition object' in the
    :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.NicManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.NicManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, NicManager), \
            "Nic init: Expected manager type {}, got {}" \
            .format(NicManager, type(manager))
        super(Nic, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this NIC.

        Authorization requirements:

        * Object-access permission to the Partition containing this HBA.
        * Task permission to the "Partition Details" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.delete(self._uri, resource=self)
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))

        parent_nic_uris = self.manager.parent.get_properties_local(
            'nic-uris')
        if parent_nic_uris:
            try:
                parent_nic_uris.remove(self._uri)
            except ValueError:
                pass

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this NIC.

        This method serializes with other methods that access or change
        properties on the same Python object.

        Authorization requirements:

        * Object-access permission to the Partition containing this NIC.
        * Object-access permission to the backing Adapter for this NIC.
        * Task permission to the "Partition Details" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model - NIC Element Object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, body=properties, resource=self)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)
