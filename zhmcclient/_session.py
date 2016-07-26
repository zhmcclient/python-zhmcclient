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
Session class: A session to the HMC, optionally in context of an HMC user.
"""

from __future__ import absolute_import

import json
import time
import requests

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
    A session to the HMC, optionally in context of an HMC user.

    The session supports operations that require to be authenticated, as well
    as operations that don't (e.g. obtaining the API version).
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
        self._session_id = None

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
        :term:`header dict`: HTTP headers to be used in each request.

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

    def logon(self):
        """
        Make sure the session is logged on to the HMC.
        """
        if not self.is_logon():
            self._do_logon()

    def logoff(self):
        """
        Make sure the session is logged off from the HMC.
        """
        if self.is_logon():
            session_uri = '/api/sessions/this-session'
            self.delete(session_uri, logon_required=False)
            self._session_id = None
            self._headers.pop('X-API-Session', None)

    def is_logon(self):
        """
        Return a boolean indicating whether the session is currently logged on
        to the HMC.
        """
        return self._session_id is not None

    def _do_logon(self):
        """
        Log on, unconditionally. This can be used to re-logon.
        This requires credentials to be provided.
        """
        if self._userid is None or self._password is None:
            raise AuthError("Userid or password not provided.")
        logon_uri = '/api/sessions'
        logon_body = {
            'userid': self._userid,
            'password': self._password
        }
        self._headers.pop('X-API-Session', None)  # Just in case
        logon_res = self.post(logon_uri, logon_body, logon_required=False)
        self._session_id = logon_res['api-session']
        self._headers['X-API-Session'] = self._session_id

    def get(self, uri, logon_required=True):
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

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC. For example, the API version retrieval
            operation does not require that.

        Returns:

          :term:`json object` with the operation result.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
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
                if logon_required:
                    self._do_logon()
                else:
                    raise AuthError("API session token unexpectedly expired "
                                    "for GET on resource that does not "
                                    "require authentication: {}".
                                    format(uri))
                return self.get(uri, logon_required)
            else:
                exc = HTTPError(result.json())
                raise AuthError("HTTP authentication failed: {}".
                                format(str(exc)))
        else:
            raise HTTPError(result.json())

    def post(self, uri, body=None, logon_required=True):
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
            JSON object to be used as the HTTP request body (payload).
            `None` means the same as an empty dictionary, namely that no HTTP
            body is included in the request.

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC. For example, the logon operation does not
            require that.

        Returns:

          :term:`json object` with the operation result.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        url = self.base_url + uri
        if body is None:
            body = {}
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
                        time.sleep(1)  # Avoid hot spin loop
                else:
                    raise HTTPError(result.json())
        elif result.status_code == 403:
            reason = result.json().get('reason', None)
            if reason == 5:
                # API session token expired: re-logon and retry
                if logon_required:
                    self._do_logon()
                else:
                    raise AuthError("API session token unexpectedly expired "
                                    "for POST on resource that does not "
                                    "require authentication: {}".
                                    format(uri))
                return self.post(uri, body, logon_required)
            else:
                exc = HTTPError(result.json())
                raise AuthError("HTTP authentication failed: {}".
                                format(str(exc)))
        else:
            raise HTTPError(result.json())

    def delete(self, uri, logon_required=True):
        """
        Perform the HTTP DELETE method against the resource identified by a
        URI.

        A set of standard HTTP headers is automatically part of the request.

        If the HMC session token is expired, this method re-logs on and retries
        the operation.

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g.
            "/api/session/{session-id}".
            This URI is relative to the base URL of the session (see
            the :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC. For example, for the logoff operation, it
            does not make sense to first log on.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        url = self.base_url + uri
        try:
            result = requests.delete(url, headers=self.headers, verify=False)
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(str(exc))
        if result.status_code == 200:
            return
        elif result.status_code == 403:
            reason = result.json().get('reason', None)
            if reason == 5:
                # API session token expired: re-logon and retry
                if logon_required:
                    self._do_logon()
                else:
                    raise AuthError("API session token unexpectedly expired "
                                    "for DELETE on resource that does not "
                                    "require authentication: {}".
                                    format(uri))
                self.delete(uri, logon_required)
                return
            else:
                exc = HTTPError(result.json())
                raise AuthError("HTTP authentication failed: {}".
                                format(str(exc)))
        else:
            raise HTTPError(result.json())
