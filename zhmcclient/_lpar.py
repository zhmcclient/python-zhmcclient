#!/usr/bin/env python

"""
A **Logical Partition (LPAR)** is a subset of a physical z Systems computer,
certain aspects of which are virtualized.

An LPAR is always contained in a CPC.

LPARs can be created and deleted dynamically, and their resources such as
CPU, memory or I/O devices can be configured.

When the CPC is in DPM (Dynamic Partition Manager) mode, LPARs are referred to
as *Partitions*. Otherwise (i.e. in classic mode), they are referred to as
*LPARs*. This documentation always refers to them as LPARs, regardless of
whether the CPC is in DPM mode or in classic mode.
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

    def list(self):
        """
        List the LPARs in scope of this manager object.

        Returns:

          : A list of :class:`~zhmcclient.Lpar` objects.
        """
        cpc_uri = self.cpc["object-uri"]
        lpars_res = self.session.get(cpc_uri + '/logical-partitions')
        lpar_list = []
        if lpars_res:
            lpar_items = lpars_res['logical-partitions']
            for lpar in lpar_items:
                lpar_list.append(Lpar(self, lpar))
        return lpar_list


class Lpar(BaseResource):
    """
    Representation of an LPAR.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common methods
    and attributes.
    """

    def __init__(self, manager, attrs):
        """
        Parameters:

          manager (:class:`~zhmcclient.LparManager`):
            Manager object for this resource.

          attrs (dict):
            Attributes to be attached to this object.
        """
        assert isinstance(manager, LparManager)
        super(Lpar, self).__init__(manager, attrs)

    def activate(self):
        """
        Activate this LPAR.

        TODO: Review return value, and idea of immediately retrieving status.
        """
        if self["status"] == "not-activated":
            lpar_object_uri = self["object-uri"]
            body = {}
            result = self.manager.session.post(lpar_object_uri + '/operations/activate', body)
            self._update_status()
            return True
        else:
            return False

    def deactivate(self):
        """
        De-activate this LPAR.

        TODO: Review return value, and idea of immediately retrieving status.
        """
        if self["status"] in ["operating", "not-operating", "exceptions"]:
            lpar_object_uri = self["object-uri"]
            body = { 'force' : True }
            result = self.manager.session.post(lpar_object_uri + '/operations/deactivate', body)
            self._update_status()
            return True
        else:
            return False

    def load(self, load_address):
        """
        Load (boot) this LPAR from a boot device.

        TODO: Review return value, and idea of immediately retrieving status.

        Parameters:

          load_address (:term:`string`): Device number of the boot device.
        """
        if self["status"] in ["not-operating"]:
            lpar_object_uri = self["object-uri"]
            body = { 'load-address' : load_address }
            result = self.manager.session.post(lpar_object_uri + '/operations/load', body)
            self._update_status()
            return True
        else:
            return False

    def _update_status(self):
        lpar_object_uri = self["object-uri"]
        lpar = self.manager.session.get(lpar_object_uri)
        setattr(self, 'status', lpar.get("status"))
        return

