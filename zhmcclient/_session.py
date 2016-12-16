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
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import requests

from ._exceptions import HTTPError, AuthError, ConnectionError, ParseError
from ._timestats import TimeStatsKeeper
from ._logging import _get_logger, _log_call

LOG = _get_logger(__name__)

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

    The session can keep statistics about the elapsed time for issuing HTTP
    requests against the HMC API. Instance variable
    :attr:`~zhmcclient.Session.time_stats_keeper` is used to enable/disable the
    measurements, and to print the statistics.
    """

    def __init__(self, host, userid=None, password=None, session_id=None,
                 get_password=None):
        """
        Creating a session object will not immediately cause a logon to be
        attempted; the logon is deferred until needed.

        There are several alternatives for specifying the authentication
        related parameters:

        * `userid`/`password` only: The session is initially in a logged-off
          state and subsequent operations that require logon will use the
          specified userid and password to automatically log on. The returned
          session-id will be stored in this session object. Subsequent
          operations that require logon will use that session-id. Once the HMC
          expires that session-id, subsequent operations that require logon
          will cause a re-logon with the specified userid and password.

        * `userid`/`password` and `session_id`: The specified session-id will
          be stored in this session object, so that the session is initially in
          a logged-on state. Subsequent operations that require logon will use
          that session-id. Once the HMC expires that session-id, subsequent
          operations that require logon will cause a re-logon with the
          specified userid/password.

        * `session_id` only: The specified session-id will be stored in this
          session object, so that the session is initially in a logged-on
          state. Subsequent operations that require logon will use the stored
          session-id. Once the HMC expires the session-id, subsequent
          operations that require logon will cause an
          :exc:`~zhmcclient.AuthError` to be raised (because userid/password
          have not been specified, so an automatic re-logon is not possible).

        * Neither `userid`/`password` nor `session_id`: Only operations that do
          not require logon, are possible.

        Parameters:

          host (:term:`string`):
            HMC host. For valid formats, see the
            :attr:`~zhmcclient.Session.host` property.
            Must not be `None`.

          userid (:term:`string`):
            Userid of the HMC user to be used, or `None`.

          password (:term:`string`):
            Password of the HMC user to be used, if `userid` was specified.

          session_id (:term:`string`):
            Session-id to be used for this session, or `None`.

          get_password (:term:`callable`):
            A function that returns the password as a string, or `None`.

            If provided, this function will be called if a password is needed
            but not provided.

            This mechanism can be used for example by command line interfaces
            for prompting for the password.
        """
        self._host = host
        self._userid = userid
        self._password = password
        self._get_password = get_password
        self._base_url = "{scheme}://{host}:{port}".format(
            scheme=_HMC_SCHEME,
            host=self._host,
            port=_HMC_PORT)
        self._headers = _STD_HEADERS  # dict with standard HTTP headers
        if session_id is not None:
            # Create a logged-on state (same state as in _do_logon())
            self._session_id = session_id
            self._session = requests.Session()
            self._headers['X-API-Session'] = session_id
        else:
            # Create a logged-off state (same state as in _do_logoff())
            self._session_id = None
            self._session = None
        self._time_stats_keeper = TimeStatsKeeper()
        LOG.debug("Created session object for '%(user)s' on '%(host)s'",
                  {'user': self._userid, 'host': self._host})

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
    def get_password(self):
        """
        bool: The function that returns the password as a string, or `None`.
        """
        return self._get_password

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

    @property
    def time_stats_keeper(self):
        """
        The time statistics keeper (for a usage example, see section
        :ref:`Time Statistics`).
        """
        return self._time_stats_keeper

    @property
    def session_id(self):
        """
        :term:`string`: Session ID for this session, returned by the HMC.
        """
        return self._session_id

    @property
    def session(self):
        """
        :term:`string`: :class:`requests.Session` object for this session.
        """
        return self._session

    @_log_call
    def logon(self, verify=False):
        """
        Make sure the session is logged on to the HMC.

        By default, this method checks whether there is a session-id set
        and considers that sufficient for determining that the session is
        logged on. The `verify` parameter can be used to verify the validity
        of a session-id that is already set, by issuing a dummy operation
        ("Get Console Properties") to the HMC.

        After successful logon to the HMC, the following is stored in this
        session object for reuse in subsequent operations:

        * the HMC session-id, in order to avoid extra userid authentications,
        * a :class:`requests.Session` object, in order to enable connection
          pooling. Connection pooling avoids repetitive SSL/TLS handshakes.

        Parameters:

          verify (bool): If a session-id is already set, verify its validity.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if not self.is_logon(verify):
            self._do_logon()

    @_log_call
    def logoff(self):
        """
        Make sure the session is logged off from the HMC.

        After successful logoff, the HMC session-id and
        :class:`requests.Session` object stored in this object are reset.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if self.is_logon():
            self._do_logoff()

    @_log_call
    def is_logon(self, verify=False):
        """
        Return a boolean indicating whether the session is currently logged on
        to the HMC.

        By default, this method checks whether there is a session-id set
        and considers that sufficient for determining that the session is
        logged on. The `verify` parameter can be used to verify the validity
        of a session-id that is already set, by issuing a dummy operation
        ("Get Console Properties") to the HMC.

        Parameters:

          verify (bool): If a session-id is already set, verify its validity.
        """
        if self._session_id is None:
            return False
        if verify:
            try:
                self.get('/api/console', logon_required=True)
            except AuthError:
                return False
        return True

    def _do_logon(self):
        """
        Log on, unconditionally. This can be used to re-logon.
        This requires credentials to be provided.
        """
        if self._userid is None:
            raise AuthError("Userid is not provided.")
        if self._password is None:
            if self._get_password:
                self._password = self._get_password()
            else:
                raise AuthError("Password is not provided.")
        logon_uri = '/api/sessions'
        logon_body = {
            'userid': self._userid,
            'password': self._password
        }
        self._headers.pop('X-API-Session', None)  # Just in case
        self._session = requests.Session()
        logon_res = self.post(logon_uri, logon_body, logon_required=False)
        self._session_id = logon_res['api-session']
        self._headers['X-API-Session'] = self._session_id

    def _do_logoff(self):
        """
        Log off, unconditionally.
        """
        session_uri = '/api/sessions/this-session'
        self.delete(session_uri, logon_required=False)
        self._session_id = None
        self._session = None
        self._headers.pop('X-API-Session', None)

    @staticmethod
    def _log_hmc_request_id(response):
        """
        Log the identifier the HMC uses to distinguish requests.
        """
        LOG.info("Returned HMC request ID: %r",
                 response.headers.get('X-Request-Id', ''))

    @staticmethod
    def _log_http_method(http_method, uri):
        """
        Log HTTP method name and target URI.
        """
        LOG.info("HTTP request: %s %s", http_method, uri)

    @_log_call
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
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        url = self.base_url + uri
        self._log_http_method('GET', uri)
        stats = self.time_stats_keeper.get_stats('get ' + uri)
        stats.begin()
        req = self._session or requests
        try:
            result = req.get(url, headers=self.headers, verify=False)
            result_object = _result_object(result)
            self._log_hmc_request_id(result)
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(exc.args[0], exc)
        finally:
            stats.end()

        if result.status_code == 200:
            return result_object
        elif result.status_code == 403:
            reason = result_object.get('reason', None)
            if reason == 5:
                # API session token expired: re-logon and retry
                if logon_required:
                    self._do_logon()
                else:
                    raise AuthError("API session token unexpectedly expired "
                                    "for GET on a resource that does not "
                                    "require authentication: {}".
                                    format(uri), HTTPError(result_object))
                return self.get(uri, logon_required)
            else:
                msg = result_object.get('message', None)
                raise AuthError("HTTP authentication failed: {}".
                                format(msg), HTTPError(result_object))
        else:
            raise HTTPError(result_object)

    @_log_call
    def post(self, uri, body=None, logon_required=True,
             wait_for_completion=True):
        """
        Perform the HTTP POST method against the resource identified by a URI,
        using a provided request body.

        A set of standard HTTP headers is automatically part of the request.

        HMC operations using HTTP POST are either synchronous or asynchronous.
        Asynchronous operations return the URI of an asynchronously executing
        job that can be queried for status and result.

        Examples for synchronous operations:

        * With no response body: "Logon", "Update CPC Properties"
        * With a response body: "Create Partition"

        Examples for asynchronous operations:

        * With no ``job-results`` field in the completed job status response:
          "Start Partition"
        * With a ``job-results`` field in the completed job status response
          (under certain conditions): "Activate a Blade", or "Set CPC Power
          Save"

        The `wait_for_completion` parameter of this method can be used to deal
        with asynchronous HMC operations in a synchronous way.

        If executing the operation reveals that the HMC session token is
        expired, this method re-logs on and retries the operation.

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
            is logged on to the HMC. For example, the "Logon" operation does
            not require that.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested HMC operation, as follows:

            * If `True`, this method will wait for completion of the requested
              operation, regardless of whether the operation is synchronous or
              asynchronous.

              This will cause an additional entry in the time statistics to be
              created for the asynchronous operation and waiting for its
              completion. This entry will have a URI that is the targeted URI,
              appended with "+completion".

            * If `False`, this method will immediately return the result of the
              HTTP POST method, regardless of whether the operation is
              synchronous or asynchronous.

        Returns:

          :term:`json object`:

            If `wait_for_completion` is `True`, returns a JSON object
            representing the response body of the synchronous operation, or the
            response body of the completed job that performed the asynchronous
            operation. If a synchronous operation has no response body, `None`
            is returned.

            If `wait_for_completion` is `False`, returns a JSON object
            representing the response body of the synchronous or asynchronous
            operation. In case of an asynchronous operation, the JSON object
            will have a member named ``job-uri``, whose value can be used with
            the :meth:`~zhmcclient.Session.query_job_status` method to
            determine the status of the job and the result of the original
            operation, once the job has completed.

            See the section in the :term:`HMC API` book about the specific HMC
            operation and about the 'Query Job Status' operation, for a
            description of the members of the returned JSON objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        url = self.base_url + uri
        self._log_http_method('POST', uri)
        req = self._session or requests
        if wait_for_completion:
            stats_total = self.time_stats_keeper.get_stats(
                'post ' + uri + '+completion')
            stats_total.begin()
        try:
            stats = self.time_stats_keeper.get_stats('post ' + uri)
            stats.begin()
            try:
                if body is None:
                    result = req.post(url, headers=self.headers,
                                      verify=False)
                else:
                    data = json.dumps(body)
                    result = req.post(url, data=data, headers=self.headers,
                                      verify=False)
                self._log_hmc_request_id(result)
            except requests.exceptions.RequestException as exc:
                raise ConnectionError(exc.args[0], exc)
            finally:
                stats.end()

            if result.status_code in (200, 201):
                return _result_object(result)
            elif result.status_code == 204:
                # No content
                return None
            elif result.status_code == 202:
                result_object = _result_object(result)
                job_uri = result_object['job-uri']
                job_url = self.base_url + job_uri
                if not wait_for_completion:
                    return result_object
                while 1:
                    self._log_http_method('GET', job_uri)
                    stats = self.time_stats_keeper.get_stats('get ' + job_uri)
                    stats.begin()
                    try:
                        result = req.get(job_url, headers=self.headers,
                                         verify=False)
                        self._log_hmc_request_id(result)
                    except requests.exceptions.RequestException as exc:
                        raise ConnectionError(exc.args[0], exc)
                    finally:
                        stats.end()
                    if result.status_code in (200, 204):
                        result_object = _result_object(result)
                        if result_object['status'] == 'complete':
                            self.delete_completed_job_status(job_uri)
                            return result_object
                        else:
                            # TODO: Add support for timeout
                            time.sleep(1)  # Avoid hot spin loop
                    else:
                        raise HTTPError(result_object)
            elif result.status_code == 403:
                result_object = _result_object(result)
                reason = result_object.get('reason', None)
                if reason == 5:
                    # API session token expired: re-logon and retry
                    if logon_required:
                        self._do_logon()
                    else:
                        raise AuthError(
                            "API session token unexpectedly expired "
                            "for POST on a resource that does not "
                            "require authentication: {}".
                            format(uri), HTTPError(result_object))
                    return self.post(uri, body, logon_required)
                else:
                    msg = result_object.get('message', None)
                    raise AuthError("HTTP authentication failed: {}".
                                    format(msg), HTTPError(result_object))
            else:
                result_object = _result_object(result)
                raise HTTPError(result_object)
        finally:
            if wait_for_completion:
                stats_total.end()

    @_log_call
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
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        url = self.base_url + uri
        self._log_http_method('DELETE', uri)
        stats = self.time_stats_keeper.get_stats('delete ' + uri)
        stats.begin()
        req = self._session or requests
        try:
            result = req.delete(url, headers=self.headers, verify=False)
            self._log_hmc_request_id(result)
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(exc.args[0], exc)
        finally:
            stats.end()

        if result.status_code in (200, 204):
            return
        elif result.status_code == 403:
            result_object = _result_object(result)
            reason = result_object.get('reason', None)
            if reason == 5:
                # API session token expired: re-logon and retry
                if logon_required:
                    self._do_logon()
                else:
                    raise AuthError("API session token unexpectedly expired "
                                    "for DELETE on a resource that does not "
                                    "require authentication: {}".
                                    format(uri), HTTPError(result_object))
                self.delete(uri, logon_required)
                return
            else:
                msg = result_object.get('message', None)
                raise AuthError("HTTP authentication failed: {}".
                                format(msg), HTTPError(result_object))
        else:
            result_object = _result_object(result)
            raise HTTPError(result_object)

    @_log_call
    def query_job_status(self, job_uri):
        """
        Perform the "Query Job Status" operation on a job identified by its
        URI and return the status of the job. If the job is complete, the
        return value also contains the result of the operation the job was
        performing asynchronously.

        A set of standard HTTP headers is automatically part of the request.

        If the HMC session token is expired, this method re-logs on and retries
        the operation.

        Parameters:

          job_uri (:term:`string`):
            Job URI; e.g. from the value of the ``job-uri`` field of the
            result of the original operation that was performed asynchronously
            by the job.
            Must not be `None`.

        Returns:

          :term:`json object`:

            A JSON object indicating the status of the job in its ``status``
            member, and if the job is complete (``status='complete'``), also
            with members ``job-status-code``, ``job-reason-code``, and
            optionally ``job-results``.

            For details, see section 'Response body contents' in section
            'Query Job Status' in the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.get(job_uri)
        return result

    @_log_call
    def delete_completed_job_status(self, job_uri):
        """
        Perform the "Delete completed Job Status" operation on a job identified
        by its URI and return the status of the job.

        A set of standard HTTP headers is automatically part of the request.

        If the HMC session token is expired, this method re-logs on and retries
        the operation.

        Parameters:

          job_uri (:term:`string`):
            Job URI; e.g. from the value of the ``job-uri`` field of the
            result of the original operation that was performed asynchronously
            by the job.
            Must not be `None`.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.delete(job_uri)

    @_log_call
    def get_notification_topics(self):
        """
        The 'Get Notification Topics' operation returns a structure that
        describes the JMS notification topics associated with the
        API session.

        Returns:

            : List with one item for each notification topic. The dictionary
            has the following keys:

            * topic-type (string): Topic type, e.g. "job-notification".
            * topic-name (string): Topic name; can be used for subscriptions.
            * object-uri (string): When topic-type is
              "os-message-notification", this item is the canonical URI path
              of the Partition for which this topic exists.
              This field does not exist for the other topic types.
            * include-refresh-messages (bool): When the topic-type is
              "os-message-notification", this item indicates whether refresh
              operating system messages will be sent on this topic.
        """
        topics_uri = '/api/sessions/operations/get-notification-topics'
        response = self.get(topics_uri)
        return response['topics']


def _result_object(result):
    """
    Return the JSON payload in the HTTP response as a Python dict.

    Raises:
        zhmcclient.ParseError: Error parsing the returned JSON.
    """
    try:
        return result.json(object_pairs_hook=OrderedDict)
    except ValueError as exc:
        raise ParseError("Parse error in returned JSON: {}".
                         format(exc.args[0]))
