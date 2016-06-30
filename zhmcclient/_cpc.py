#!/usr/bin/env python                                                                                                        

from __future__ import absolute_import

from ._manager import BaseManager
from ._lpar import LparManager

__all__ = ['CpcManager', 'Cpc']

class CpcManager(BaseManager):
    """
    Manager object for the CPCs in scope of a particular HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods.
    """

    def __init__(self, session):
        """
        Parameters:

          session (:class:`~zhmcclient.Session`):
            Session object for the HMC to be used.
        """
        self._session = session

    @property
    def session(self):
        """
        :class:`~zhmcclient.Session`: Session object used for the HMC.
        """
        return self._session

    def list(self):
        """
        List the CPCs in scope of the HMC.

        Returns:

          : A list of :class:`~zhmcclient.Cpc` objects.
        """
        cpcs_resp = self.session.get('/api/cpcs')
        cpc_list = []
        if cpcs_resp:
            cpc_items = cpcs_resp['cpcs']
            for cpc_attrs in cpc_items:
                cpc_list.append(Cpc(self, cpc_attrs))
        return cpc_list


class Cpc(object):
    """
    A CPC in scope of an HMC.
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
        self._manager = manager
        self._lpars = LparManager(self, manager.session)
        for k, v in attrs.items():
            setattr(self, k, v)

    @property
    def manager(self):
        """
        :class:`~zhmcclient.CpcManager`: Manager object for this CPC.
        """
        return self._manager

    @property
    def lpars(self):
        """
        :class:`~zhmcclient.LparManager`: Manager object for the LPARs in this
        CPC.
        """
        return self._lpars

