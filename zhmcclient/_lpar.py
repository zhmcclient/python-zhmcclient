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
A **Logical Partition (LPAR)** is a subset of a physical z Systems computer,
certain aspects of which are virtualized.

An LPAR is always contained in a CPC.

Objects of this class are not provided when the CPC is enabled for DPM
(Dynamic Partition Manager).
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource

__all__ = ['LparManager', 'Lpar']


class LparManager(BaseManager):
    """
    Manager object for LPARs. This manager object is scoped to the LPARs of a
    particular CPC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, cpc):
        """
        Parameters:

          cpc (:class:`~zhmcclient.Cpc`):
            CPC defining the scope for this manager object.
        """
        super(LparManager, self).__init__(cpc)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: Parent object (CPC) defining the scope for
        this manager object.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the LPARs in scope of this manager object.

        Parameters:

          full_properties (bool):
            Boolean indicating whether the full properties list
            should be retrieved. Otherwise, only the object_info
            properties are returned for each lpar object.

        Returns:

          : A list of :class:`~zhmcclient.Lpar` objects.
        """
        cpc_uri = self.cpc.get_property('object-uri')
        lpars_res = self.session.get(cpc_uri + '/logical-partitions')
        lpar_list = []
        if lpars_res:
            lpar_items = lpars_res['logical-partitions']
            for lpar_props in lpar_items:
                lpar = Lpar(self, lpar_props)
                if full_properties:
                    lpar.pull_full_properties()
                lpar_list.append(lpar)
        return lpar_list


class Lpar(BaseResource):
    """
    Representation of an LPAR.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.
    """

    def __init__(self, manager, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.LparManager`):
            Manager object for this resource.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, LparManager)
        super(Lpar, self).__init__(manager, properties)

    def activate(self):
        """
        Activate this LPAR.

        TODO: Review return value, and idea of immediately retrieving status.
        """
        lpar_object_uri = self.get_property('object-uri')
        body = {}
        result = self.manager.session.post(
        lpar_object_uri + '/operations/activate', body)

    def deactivate(self):
        """
        De-activate this LPAR.

        TODO: Review return value, and idea of immediately retrieving status.
        """
        lpar_object_uri = self.get_property('object-uri')
        body = {'force': True}
        result = self.manager.session.post(
        lpar_object_uri + '/operations/deactivate', body)

    def load(self, load_address):
        """
        Load (boot) this LPAR from a boot device.

        TODO: Review return value, and idea of immediately retrieving status.

        Parameters:

          load_address (:term:`string`): Device number of the boot device.
        """
        lpar_object_uri = self.get_property('object-uri')
        body = {'load-address': load_address}
        result = self.manager.session.post(
            lpar_object_uri + '/operations/load', body)

