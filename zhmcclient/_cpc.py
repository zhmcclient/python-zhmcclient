#!/usr/bin/env python

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._lpar import LparManager

__all__ = ['CpcManager', 'Cpc']

class CpcManager(BaseManager):
    """
    Manager object for the CPCs in scope of a particular HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods.
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
        List the CPCs in scope of the HMC.

        Returns:

          : A list of :class:`~zhmcclient.Cpc` objects.
        """
        cpcs_res = self.session.get('/api/cpcs')
        cpc_list = []
        if cpcs_res:
            cpc_items = cpcs_res['cpcs']
            for cpc_attrs in cpc_items:
                cpc_list.append(Cpc(self, cpc_attrs))
        return cpc_list


class Cpc(BaseResource):
    """
    The representation of a CPC resource in scope of an HMC.
    """

    def __init__(self, manager, attrs):
        """
        Parameters:

          manager (:class:`~zhmcclient.CpcManager`):
            Manager object for this CPC.

          attrs (dict):
            Attributes to be attached to this object.
        """
        assert isinstance(manager, CpcManager)
        super(Cpc, self).__init__(manager, attrs)
        self._lpars = LparManager(self)

    @property
    def lpars(self):
        """
        :class:`~zhmcclient.LparManager`: Manager object for the LPARs in this
        CPC.
        """
        return self._lpars

