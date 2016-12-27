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
A :term:`Virtual Switch` is a virtualized networking switch connecting
:term:`NICs <NIC>` with a :term:`Network Port`.

Virtual Switches are generated automatically every time a new
:term:`Network Adapter` is detected and configured.

Virtual Switch resources are contained in :term:`CPC` resources.

Virtual Switches only exist in CPCs that are in DPM mode.
"""

from __future__ import absolute_import

import re

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['VirtualSwitchManager', 'VirtualSwitch']


class VirtualSwitchManager(BaseManager):
    """
    Manager providing access to the :term:`Virtual Switches <Virtual Switch>`
    in a particular :term:`CPC`.

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
        super(VirtualSwitchManager, self).__init__(VirtualSwitch, cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: :term:`CPC` defining the scope for this
        manager.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the Virtual Switches in this CPC.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.VirtualSwitch` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        vswitch_res = self.session.get(self.cpc.uri + '/virtual-switches')
        vswitch_list = []
        if vswitch_res:
            vswitch_items = vswitch_res['virtual-switches']
            for vswitch_props in vswitch_items:
                vswitch = VirtualSwitch(self, vswitch_props['object-uri'],
                                        vswitch_props)
                if full_properties:
                    vswitch.pull_full_properties()
                vswitch_list.append(vswitch)
        return vswitch_list


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

    def __init__(self, manager, uri, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.VirtualSwitchManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        if not isinstance(manager, VirtualSwitchManager):
            raise AssertionError("VirtualSwitch init: Expected manager "
                                 "type %s, got %s" %
                                 (VirtualSwitchManager, type(manager)))
        super(VirtualSwitch, self).__init__(manager, uri, properties,
                                            uri_prop='object-uri',
                                            name_prop='name')

    def get_connected_nics(self):
        """
        List the :term:`NICs <NIC>` connected to this Virtual Switch.

        This method performs the "Get Connected VNICs of a Virtual Switch" HMC
        operation.

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
                part = self.manager.cpc.partitions.partition_object(part_id)
                parts[part_id] = part
            nic = part.nics.nic_object(nic_id)
            nic_list.append(nic)
        return nic_list

    def update_properties(self, properties):
        """
        Update writeable properties of this Virtual Switch.

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
