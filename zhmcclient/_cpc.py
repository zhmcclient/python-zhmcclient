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
A **Central Processor Complex (CPC)** is a physical z Systems computer.
A particular HMC can manage multiple CPCs.

The HMC can manage a range of old and new CPC generations. Some older CPC
generations are not capable of supporting the HMC Web Services API; these older
CPCs can be managed using the GUI of the HMC, but not through its Web Services
API. Therefore, such older CPCs will not show up at the HMC Web Services API,
and thus will not show up in the API of this Python package.

TODO: List earliest CPC generation that supports the HMC Web Services API.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._lpar import LparManager

__all__ = ['CpcManager', 'Cpc']


class CpcManager(BaseManager):
    """
    Manager object for CPCs. This manager object is scoped to the HMC Web
    Services API capable CPCs managed by the HMC that is associated with a
    particular client.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, client):
        """
        Parameters:

          client (:class:`~zhmcclient.Client`):
            Client object for the HMC to be used.
        """
        super(CpcManager, self).__init__()
        self._session = client.session

    def list(self):
        """
        List the CPCs in scope of this manager object.

        Returns:

          : A list of :class:`~zhmcclient.Cpc` objects.
        """
        cpcs_res = self.session.get('/api/cpcs')
        cpc_list = []
        if cpcs_res:
            cpc_items = cpcs_res['cpcs']
            for cpc_props in cpc_items:
                cpc_list.append(Cpc(self, cpc_props))
        return cpc_list


class Cpc(BaseResource):
    """
    Representation of a CPC.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.
    """

    def __init__(self, manager, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.CpcManager`):
            Manager object for this CPC.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, CpcManager)
        super(Cpc, self).__init__(manager, properties)
        self._lpars = LparManager(self)

    @property
    def lpars(self):
        """
        :class:`~zhmcclient.LparManager`: Manager object for the LPARs in this
        CPC.
        """
        return self._lpars
