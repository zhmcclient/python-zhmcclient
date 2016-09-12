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
        super(VirtualSwitchManager, self).__init__(cpc)

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
        cpc_uri = self.cpc.get_property('object-uri')
        vswitch_res = self.session.get(cpc_uri + '/virtual-switches')
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

    def __init__(self, manager, uri, properties):
        # This function should not go into the docs.
        # Parameters:
        #   manager (:class:`~zhmcclient.VirtualSwitchManager`):
        #     Manager object for this Virtual Switch.
        #   uri (string):
        #     Canonical URI path of this Virtual Switch.
        #   properties (dict):
        #     Properties to be set for this Virtual Switch.
        #     See initialization of :class:`~zhmcclient.BaseResource` for
        #     details.
        assert isinstance(manager, VirtualSwitchManager)
        super(VirtualSwitch, self).__init__(manager, uri, properties)

    def get_connected_vnics(self):
        """
        List the NICs connected to this Virtual Switch.

        Returns:

          : A list of NIC URIs.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        vswitch_uri = self.get_property('object-uri')
        status = self.manager.session.get(
            vswitch_uri +
            '/operations/get-connected-vnics')
        return status['connected-vnic-uris']

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
        vswitch_uri = self.get_property('object-uri')
        self.manager.session.post(vswitch_uri, body=properties)
