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
A :term:`Virtual Switch` is a virtualized networking switch connecting
:term:`NICs <NIC>` with a :term:`Network Port`.

Virtual Switches are generated automatically every time a new
:term:`Network Adapter` is detected and configured.

Virtual Switch resources are contained in :term:`CPC` resources.

Virtual Switches only exist in CPCs that are in DPM mode.
"""


import re
import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_VIRTUAL_SWITCH

__all__ = ['VirtualSwitchManager', 'VirtualSwitch']


class VirtualSwitchManager(BaseManager):
    """
    Manager providing access to the :term:`Virtual Switches <Virtual Switch>`
    in a particular :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Cpc` object (in DPM mode):

    * :attr:`~zhmcclient.Cpc.virtual_switches`

    HMC/SE version requirements:

    * SE version >= 2.13.1
    """

    def __init__(self, cpc):
        # This function should not go into the docs.
        # Parameters:
        #   cpc (:class:`~zhmcclient.Cpc`):
        #     CPC defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name',
            'type',
        ]

        super().__init__(
            resource_class=VirtualSwitch,
            class_name=RC_VIRTUAL_SWITCH,
            session=cpc.manager.session,
            parent=cpc,
            base_uri='/api/virtual-switches',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: :term:`CPC` defining the scope for this
        manager.
        """
        return self._parent

    @logged_api_call
    # pylint: disable=arguments-differ
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the Virtual Switches in this CPC.

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

        * Otherwise, the HMC List operation is performed with the subset of the
          provided filter arguments that can be handled on the HMC side and the
          remaining filter arguments are applied on the client side on the list
          result.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this CPC.
        * Object-access permission to the backing Adapters of any Virtual
          Switches to be included in the result.

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

          additional_properties (list of string):
            List of property names that are to be returned in addition to the
            default properties.

            This parameter requires HMC 2.16.0 or higher.

        Returns:

          : A list of :class:`~zhmcclient.VirtualSwitch` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'virtual-switches'
        list_uri = f'{self.cpc.uri}/virtual-switches'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args,
            additional_properties)


class VirtualSwitch(BaseResource):
    """
    Representation of a :term:`Virtual Switch`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of a Virtual Switch, see section 'Data model'
    in section 'Virtual Switch object' in the :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.VirtualSwitchManager`).

    HMC/SE version requirements:

    * SE version >= 2.13.1
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.VirtualSwitchManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, VirtualSwitchManager), (
            "VirtualSwitch init: Expected manager type "
            f"{VirtualSwitchManager}, got {type(manager)}")
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def get_connected_nics(self):
        """
        List the :term:`NICs <NIC>` connected to this Virtual Switch.

        This method performs the "Get Connected VNICs of a Virtual Switch" HMC
        operation.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this CPC.
        * Object-access permission to the backing Adapter of this Virtual
          Switch.

        Returns:

          : A list of :term:`Nic` objects. These objects will be connected in
          the resource tree (i.e. have a parent :term:`Partition` object,
          etc.) and will have the following properties set:

          * `element-uri`
          * `element-id`
          * `parent`
          * `class`

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.get(
            self.uri + '/operations/get-connected-vnics', resource=self)
        nic_uris = result['connected-vnic-uris']
        nic_list = []
        parts = {}  # Key: Partition ID; Value: Partition object
        for nic_uri in nic_uris:
            m = re.match(r"^/api/partitions/([^/]+)/nics/([^/]+)/?$", nic_uri)
            part_id = m.group(1)
            nic_id = m.group(2)
            # We remember created Partition objects and reuse them.
            try:
                part = parts[part_id]
            except KeyError:
                part = self.manager.cpc.partitions.resource_object(part_id)
                parts[part_id] = part
            nic = part.nics.resource_object(nic_id)
            nic_list.append(nic)
        return nic_list

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this Virtual Switch.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to the backing Adapter of this Virtual
          Switch.
        * Task permission for the "Manage Adapters" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'Virtual Switch object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, resource=self, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)
