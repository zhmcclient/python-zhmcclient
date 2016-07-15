#!/usr/bin/env python

"""
Client class: A client to an HMC.
"""

from __future__ import absolute_import

from ._cpc import CpcManager

__all__ = ['Client']

class Client(object):
    """
    A client to an HMC.

    This is the main class for users of this package.
    """

    def __init__(self, session):
        """
        Parameters:

          session (:class:`~zhmcclient.Session`):
            Session with the HMC.
        """
        self._session = session
        self._cpcs = CpcManager(self)
        self._api_major_version = None
        self._api_minor_version = None

    @property
    def session(self):
        """
        :class:`~zhmcclient.Session`:
          Session with the HMC.
        """
        return self._session

    @property
    def cpcs(self):
        """
        :class:`~zhmcclient.CpcManager`:
          Manager object for the CPCs in scope of this client (i.e. in scope
          of its HMC).
        """
        return self._cpcs

    def version_info(self):
        """
        Returns API version information for the HMC.

        This operation does not require authentication.

        Returns:

          : A tuple of (api_major_version, api_minor_version), where:

            * `api_major_version` (:term:`integer`): The numeric major version
              of the API supported by the HMC.

            * `api_minor_version` (:term:`integer`): The numeric minor version
              of the API supported by the HMC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if self._api_major_version is None:
            version_res = self._session.get('/api/version',
                                            logon_required=False)
            self._api_major_version = version_res['api-major-version']
            self._api_minor_version = version_res['api-minor-version']
        return self._api_major_version, self._api_minor_version
