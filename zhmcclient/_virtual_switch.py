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
A Virtual Switch object is a virtualized representation of
networking vswitch and port of a physical z Systems or LinuxONE computer
that is in DPM mode (Dynamic Partition Manager mode).
Objects of this class are not provided when the CPC is not in DPM mode.
Network vswitchs without a physical port, such as hipersockets
or single port OSAs are virtualized to a single virtual switch.
Network vswitchs with multiple ports are virtualized into multiple virtual
switches one for each port. Virtual switches are generated automatically
every time a new network vswitch is detected and configured.
The virtual switch serves as the connection point for network interfaces
(VNICs) created by the virtual server administrator.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['VirtualSwitchManager', 'VirtualSwitch']


class VirtualSwitchManager(BaseManager):
    """
    Manager object for Virtual Switches. This manager object is scoped to the
    vswitchs of a particular CPC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, cpc):
        """
        Parameters:

          cpc (:class:`~zhmcclient.Cpc`):
            CPC defining the scope for this manager object.
        """
        super(VirtualSwitchManager, self).__init__(cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: Parent object (CPC) defining the scope for
        this manager object.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the Virtual Switches in scope of this manager object.

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
    Representation of an VirtualSwitch.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Properties of an VirtualSwitch:
      See the sub-section 'Data model' of the section 'VirtualSwitch object'
      in the :term:`HMC API`.
    """

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.VirtualSwitchManager`):
            Manager object for this resource.

          uri (string):
            Canonical URI path of the VirtualSwitch object.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, VirtualSwitchManager)
        super(VirtualSwitch, self).__init__(manager, uri, properties)

    def get_connected_vnics(self):
        """
        Retrieves the list of network interfaces (VNICs)
        connected to a single Virtual VirtualSwitch.

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
        Updates one or more of the writable properties of a vswitch
        with the specified resource properties.

        Parameters:

          properties (dict): Updated properties for the vswitch.
            See the section in the :term:`HMC API` about
            the specific HMC operation 'Update VirtualSwitch Properties'
            description of the members of the passed properties
            dict.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        vswitch_uri = self.get_property('object-uri')
        self.manager.session.post(vswitch_uri, body=properties)
