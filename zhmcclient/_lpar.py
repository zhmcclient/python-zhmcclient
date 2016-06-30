#!/usr/bin/env python

from __future__ import absolute_import

from ._manager import BaseManager

__all__ = ['LparManager', 'Lpar']

class LparManager(BaseManager):
    """
    Manager object for LPARs of a particular CPC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods.
    """

    def __init__(self, cpc, session=None):
        """
        Parameters:

          cpc (:class:`~zhmcclient.Cpc`):
            CPC containing the LPARs managed by this object.

          session (:class:`~zhmcclient.Session`):
            Session object for the HMC to be used.
            If `None`, the session of the `cpc` parameter is used.
        """
        self._cpc = cpc
        self._session = session or cpc.session

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: CPC containing the LPARs managed by this
        object.
        """
        return self._cpc

    @property
    def session(self):
        """
        :class:`~zhmcclient.Session`: Session object used for the HMC.
        """
        return self._session

    def list(self):
        """
        List the LPARs of the CPC.

        Returns:

          : A list of :class:`~zhmcclient.Lpar` objects.
        """
        cpc_object_uri = getattr(self.cpc, "object-uri")
        lpars = self.session.get(cpc_object_uri + '/logical-partitions')
        lpar_list = []
        if lpars:
            lpar_items = lpars['logical-partitions']
            for lpar in lpar_items:
                lpar_list.append(Lpar(self, lpar))
        return lpar_list


class Lpar(object):
    """
    An LPAR within a CPC.
    """

    def __init__(self, manager, attrs):
        """
        Parameters:

          manager (:class:`~zhmcclient.LparManager`):
            Manager object for this LPAR.

          attrs (dict):
            Attributes to be attached to this object.
        """
        assert isinstance(manager, LparManager)
        self._manager = manager
        for k, v in attrs.items():
            setattr(self, k, v)

    @property
    def manager(self):
        """
        :class:`~zhmcclient.LparManager`: Manager object for this LPAR.
        """
        return self._manager

    def activate(self):
        """
        Activate this LPAR.

        TODO: Review return value, and idea of immediately retrieving status.
        """
        if getattr(self, "status") == "not-activated":
            lpar_object_uri = getattr(self, "object-uri")
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
        if getattr(self, "status") in ["operating", "not-operating", "exceptions"]:
            lpar_object_uri = getattr(self, "object-uri")
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
        if getattr(self, "status") in ["not-operating"]:
            lpar_object_uri = getattr(self, "object-uri")
            body = { 'load-address' : load_address }
            result = self.manager.session.post(lpar_object_uri + '/operations/load', body)
            self._update_status()
            return True
        else:
            return False

    def _update_status(self):
        lpar_object_uri = getattr(self, "object-uri")
        lpar = self.manager.session.get(lpar_object_uri)
        setattr(self, 'status', lpar.get("status"))
        return

