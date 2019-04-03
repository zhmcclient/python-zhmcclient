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
A :term:`Virtual Switch` is a virtualized networking switch connecting
:term:`NICs <NIC>` with a :term:`Network Port`.

Virtual Switches are generated automatically every time a new
:term:`Network Adapter` is detected and configured.

Virtual Switch resources are contained in :term:`CPC` resources.

Virtual Switches only exist in CPCs that are in DPM mode.
"""

from __future__ import absolute_import

import re
import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call

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

        super(VirtualSwitchManager, self).__init__(
            resource_class=VirtualSwitch,
            class_name='virtual-switch',
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
    def list(self, full_properties=False, filter_args=None):
        """
        List the Virtual Switches in this CPC.

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

        Returns:

          : A list of :class:`~zhmcclient.VirtualSwitch` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        resource_obj_list = []
        resource_obj = self._try_optimized_lookup(filter_args)
        if resource_obj:
            resource_obj_list.append(resource_obj)
            # It already has full properties
        else:
            query_parms, client_filters = self._divide_filter_args(filter_args)

            resources_name = 'virtual-switches'
            uri = '{}/{}{}'.format(self.cpc.uri, resources_name, query_parms)

            result = self.session.get(uri)
            if result:
                props_list = result[resources_name]
                for props in props_list:

                    resource_obj = self.resource_class(
                        manager=self,
                        uri=props[self._uri_prop],
                        name=props.get(self._name_prop, None),
                        properties=props)

                    if self._matches_filters(resource_obj, client_filters):
                        resource_obj_list.append(resource_obj)
                        if full_properties:
                            resource_obj.pull_full_properties()

        self._name_uri_cache.update_from(resource_obj_list)
        return resource_obj_list


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
        assert isinstance(manager, VirtualSwitchManager), \
            "VirtualSwitch init: Expected manager type %s, got %s" % \
            (VirtualSwitchManager, type(manager))
        super(VirtualSwitch, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def get_connected_nics(self):
        """
        List the :term:`NICs <NIC>` connected to this Virtual Switch.

        This method performs the "Get Connected VNICs of a Virtual Switch" HMC
        operation.

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
            self.uri + '/operations/get-connected-vnics')
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
        self.manager.session.post(self.uri, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.properties.update(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)
