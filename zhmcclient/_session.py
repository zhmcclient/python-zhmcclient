#!/usr/bin/env python

from __future__ import absolute_import

import requests
import json
import time

from ._exceptions import HTTPError, AuthError, ConnectionError

__all__ = ['Session']

_HMC_PORT = 6794
_HMC_SCHEME = "https"
_STD_HEADERS = {
    'Content-type': 'application/json',
    'Accept': '*/*'
}

class Session(object):
    """
    A session to the HMC in context of an HMC user.
    """

    def __init__(self, host, userid=None, password=None):
        """
        Creating a session object will not immediately cause a logon to be
        attempted; the logon is deferred until needed.

        Parameters:

          host (:term:`string`):
            HMC host. For valid formats, see the
            :attr:`~zhmcclient.Session.host` property.
            Must not be `None`.

          userid (:term:`string`):
            Userid of the HMC user to be used.
            If `None`, only operations that do not require authentication, can
            be performed.

          password (:term:`string`):
            Password of the HMC user to be used.

        TODO: Add support for client-certificate-based authentication.
        """
        self._host = host
        self._userid = userid
        self._password = password
        self._base_url = "{scheme}://{host}:{port}".format(
            scheme=_HMC_SCHEME,
            host=self._host,
            port=_HMC_PORT)
        self._headers = _STD_HEADERS
        self._api_session = None
        self._api_major_version = None
        self._api_minor_version = None

    @property
    def host(self):
        """
        :term:`string`: HMC host, in one of the following formats:

          * a short or fully qualified DNS hostname
          * a literal (= dotted) IPv4 address
          * a literal IPv6 address, formatted as defined in :term:`RFC3986`
            with the extensions for zone identifiers as defined in
            :term:`RFC6874`, supporting ``-`` (minus) for the delimiter
            before the zone ID string, as an additional choice to ``%25``
        """
        return self._host

    @property
    def userid(self):
        """
        :term:`string`: Userid of the HMC user to be used.

        If `None`, only operations that do not require authentication, can be
        performed.
        """
        return self._userid

    @property
    def base_url(self):
        """
        :term:`string`: Base URL of the HMC in this session.

        Example:

        ::

            https://myhmc.acme.com:6794
        """
        return self._base_url

    @property
    def headers(self):
        """
        :term:`header dict`: Standard HTTP headers to be used in each request.

        Initially, this is the following set of headers:

        ::

            Content-type: application/json
            Accept: */*

        When the session is logged on to the HMC, the session token is added
        to these headers:

        ::

            X-API-Session: ...
        """
        return self._headers

    def version_info(self):
        """
        Returns API version information for the HMC on this session.

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
            version_url = self.base_url + '/api/version'
            try:
                result = requests.get(
                    version_url, headers=self.headers, verify=False)
            except requests.exceptions.RequestException as exc:
                raise ConnectionError(str(exc))
            if result.status_code in (200, 204):
                version_resp = result.json()
                self._api_major_version = version_resp['api-major-version']
                self._api_minor_version = version_resp['api-minor-version']
            else:
                raise HTTPError(result.json())
        return self._api_major_version, self._api_minor_version

    def _logon(self):
        """
        Make sure we are logged on.
        """
        if self._api_session is None:
            self._do_logon()

    def _do_logon(self):
        """
        Log on, unconditionally. This can be used to re-logon.
        """
        if self._userid is None or self._password is None:
            raise AuthError("Userid or password not provided.")
        session_url = self.base_url + '/api/session'
        logon_req = {
            'userid': self._userid,
            'password': self._password
        }
        self._headers.pop('X-API-Session', None) # Just in case
        data = json.dumps(logon_req)
        try:
            result = requests.post(
                session_url, data=data, headers=self.headers, verify=False)
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(str(exc))
        if result.status_code in (200, 204):
            logon_resp = result.json()
            self._api_session = logon_resp['api-session']
            self._api_major_version = logon_resp['api-major-version']
            self._api_minor_version = logon_resp['api-minor-version']
            self._headers['X-API-Session'] = self._api_session
        elif result.status_code == 403:
            exc = HTTPError(result.json())
            raise AuthError("HTTP authentication failed: {}".\
                            format(str(exc)))
        else:
            raise HTTPError(result.json())

    def get(self, uri):
        """
        Perform the HTTP GET method against the resource identified by a URI.

        A set of standard HTTP headers is automatically part of the request.

        If the HMC session token is expired, this method re-logs on and retries
        the operation.

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g. "/api/session".
            This URI is relative to the base URL of the session (see
            the :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

        Returns:

          :term:`json object` with the operation result.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self._logon()
        url = self.base_url + uri
        try:
            result = requests.get(url, headers=self.headers, verify=False)
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(str(exc))
        if result.status_code == 200:
            return result.json()
        elif result.status_code == 403:
            reason = result.json().get('reason', None)
            if reason == 5:
                # API session token expired: re-logon and retry
                self._do_logon()
                return self.get(uri)
            else:
                exc = HTTPError(result.json())
                raise AuthError("HTTP authentication failed: {}".\
                                format(str(exc)))
        else:
            raise HTTPError(result.json())

    def post(self, uri, body):
        """
        Perform the HTTP POST method against the resource identified by a URI,
        using a provided request body.

        A set of standard HTTP headers is automatically part of the request.

        If the HMC performs the operation asynchronously, this method polls
        until the operation result is available.

        If the HMC session token is expired, this method re-logs on and retries
        the operation.

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g. "/api/session".
            This URI is relative to the base URL of the session (see the
            :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

          body (:term:`json object`):
            JSON request payload.
            Must not be `None`.

        Returns:

          :term:`json object` with the operation result.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self._logon()
        url = self.base_url + uri
        data = json.dumps(body)
        try:
            result = requests.post(
                url, data=data, headers=self.headers, verify=False)
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(str(exc))
        if result.status_code in (200, 204):
            return result.json()
        elif result.status_code == 202:
            job_url = self.base_url + result.json()['job-uri']
            while 1:
                result = requests.get(job_url, headers=self.headers,
                                      verify=False)
                if result.status_code in (200, 204):
                    if result.json()['status'] == 'complete':
                        return result.json()
                    else:
                        # TODO: Add support for timeout
                        time.sleep(1) # Avoid hot spin loop
                else:
                    raise HTTPError(result.json())
        elif result.status_code == 403:
            reason = result.json().get('reason', None)
            if reason == 5:
                # API session token expired: re-logon and retry
                self._do_logon()
                return self.post(uri, body)
            else:
                exc = HTTPError(result.json())
                raise AuthError("HTTP authentication failed: {}".\
                                format(str(exc)))
        else:
            raise HTTPError(result.json())

