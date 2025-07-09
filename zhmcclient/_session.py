# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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


import json
import time
import re
from copy import copy
from collections.abc import Iterable
import requests
import urllib3

from ._exceptions import HTTPError, ServerAuthError, ClientAuthError, \
    ParseError, ConnectTimeout, ReadTimeout, RetriesExceeded, \
    OperationTimeout, Error
from ._exceptions import ConnectionError  # pylint: disable=redefined-builtin

from ._timestats import TimeStatsKeeper
from ._auto_updater import AutoUpdater
from ._logging import get_logger, logged_api_call
from ._constants import DEFAULT_CONNECT_TIMEOUT, DEFAULT_CONNECT_RETRIES, \
    DEFAULT_READ_TIMEOUT, DEFAULT_READ_RETRIES, DEFAULT_MAX_REDIRECTS, \
    DEFAULT_OPERATION_TIMEOUT, DEFAULT_STATUS_TIMEOUT, \
    DEFAULT_NAME_URI_CACHE_TIMETOLIVE, HMC_LOGGER_NAME, \
    HTML_REASON_WEB_SERVICES_DISABLED, HTML_REASON_OTHER, \
    DEFAULT_HMC_PORT, BLANKED_OUT_STRING
from ._utils import repr_obj_id
from ._version import __version__

__all__ = ['Session', 'Job', 'RetryTimeoutConfig', 'get_password_interface']

HMC_LOGGER = get_logger(HMC_LOGGER_NAME)

_HMC_SCHEME = "https"
_STD_HEADERS = {
    'User-Agent': f'python-zhmcclient/{__version__}',
    'Content-type': 'application/json',
    'Accept': '*/*'
}

# Properties whose values are always blanked out in the HMC log entries
BLANKED_OUT_PROPERTIES = [
    'boot-ftp-password',    # partition create/update
    'bind-password',        # LDAP server def. create/update
    'ssc-master-pw',        # image profile cr/upd, part. cr/upd, LPAR upd
    'password',             # user create/update
    'zaware-master-pw',     # image profile create/update, LPAR update
]

# Name of the HMC property indicating internal inconsistencies
IMPLEMENTATION_ERRORS_PROP = "@@implementation-errors"


def _handle_request_exc(exc, retry_timeout_config):
    """
    Handle a :exc:`request.exceptions.RequestException` exception that was
    raised.
    """
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        new_exc = ConnectTimeout(_request_exc_message(exc), exc,
                                 retry_timeout_config.connect_timeout,
                                 retry_timeout_config.connect_retries)
        new_exc.__cause__ = None
        raise new_exc  # ConnectTimeout

    if isinstance(exc, requests.exceptions.ReadTimeout):
        new_exc = ReadTimeout(_request_exc_message(exc), exc,
                              retry_timeout_config.read_timeout,
                              retry_timeout_config.read_retries)
        new_exc.__cause__ = None
        raise new_exc  # ReadTimeout

    if isinstance(exc, requests.exceptions.RetryError):
        new_exc = RetriesExceeded(_request_exc_message(exc), exc,
                                  retry_timeout_config.connect_retries)
        new_exc.__cause__ = None
        raise new_exc  # RetriesExceeded

    msg = "{} (exception received by zhmcclient: {}.{})".format(
        _request_exc_message(exc), exc.__class__.__module__,
        exc.__class__.__name__)
    new_exc = ConnectionError(msg, exc)
    new_exc.__cause__ = None
    raise new_exc  # ConnectionError


def _request_exc_message(exc):
    """
    Return a reasonable exception message from a
    :exc:`request.exceptions.RequestException` exception.

    The approach is to dig deep to the original reason, if the original
    exception is present, skipping irrelevant exceptions such as
    `urllib3.exceptions.MaxRetryError`, and eliminating useless object
    representations such as the connection pool object in
    `urllib3.exceptions.NewConnectionError`.

    Parameters:

      exc (:exc:`~request.exceptions.RequestException`): Exception

    Returns:

      string: A reasonable exception message from the specified exception.
    """
    messages = []
    for arg in exc.args:

        if isinstance(arg, Exception):
            org_exc = arg
            if isinstance(org_exc, urllib3.exceptions.MaxRetryError):
                message = f"{org_exc}, reason: {org_exc.reason}"
            else:
                message = str(org_exc)
        else:
            message = str(arg)

        # Eliminate useless object representations
        # e.g. "<urllib3.connection.HTTPSConnection object at 0x1077de710>, "
        message = re.sub(r'<[a-zA-Z_0-9.]+ object at 0x[0-9a-f]+>(, )?', '',
                         message)

        messages.append(message)

    return ", ".join(messages)


class RetryTimeoutConfig:
    # pylint: disable=too-few-public-methods
    """
    A configuration setting that specifies verious retry counts and timeout
    durations.

    HMC/SE version requirements: None
    """

    def __init__(self, connect_timeout=None, connect_retries=None,
                 read_timeout=None, read_retries=None, max_redirects=None,
                 operation_timeout=None, status_timeout=None,
                 name_uri_cache_timetolive=None):
        """
        For all parameters, `None` means that this object does not specify a
        value for the parameter, and that a default value should be used
        (see :ref:`Constants`).

        All parameters are available as instance attributes.

        Parameters:

          connect_timeout (:term:`number`): Connect timeout in seconds.
            This timeout applies to making a connection at the socket level.
            The same socket connection is used for sending an HTTP request to
            the HMC and for receiving its HTTP response.
            The special value 0 means that no timeout is set.

          connect_retries (:term:`integer`): Number of retries (after the
            initial attempt) for connection-related issues. These retries are
            performed for failed DNS lookups, failed socket connections, and
            socket connection timeouts.

          read_timeout (:term:`number`): Read timeout in seconds.
            This timeout applies to reading at the socket level, when receiving
            an HTTP response.
            The special value 0 means that no timeout is set.

          read_retries (:term:`integer`): Number of retries (after the
            initial attempt) for read-related issues. These retries are
            performed for failed socket reads and socket read timeouts.
            A retry consists of resending the original HTTP request. The
            zhmcclient restricts these retries to just the HTTP GET method.
            For other HTTP methods, no retry will be performed.

          max_redirects (:term:`integer`): Maximum number of HTTP redirects.

          operation_timeout (:term:`number`): Asynchronous operation timeout in
            seconds. This timeout applies when waiting for the completion of
            asynchronous HMC operations. The special value 0 means that no
            timeout is set.

          status_timeout (:term:`number`): Resource status timeout in seconds.
            This timeout applies when waiting for the transition of the status
            of a resource to a desired status. The special value 0 means that
            no timeout is set.

          name_uri_cache_timetolive (:term:`number`): Time to the next
            automatic invalidation of the Name-URI cache of manager objects, in
            seconds since the last invalidation. The special value 0 means
            that no Name-URI cache is maintained (i.e. the caching is
            disabled).
        """
        self.connect_timeout = connect_timeout
        self.connect_retries = connect_retries
        self.read_timeout = read_timeout
        self.read_retries = read_retries
        self.max_redirects = max_redirects
        self.operation_timeout = operation_timeout
        self.status_timeout = status_timeout
        self.name_uri_cache_timetolive = name_uri_cache_timetolive

        # Read retries only for these HTTP methods:
        self.allowed_methods = {'GET'}

    _attrs = ('connect_timeout', 'connect_retries', 'read_timeout',
              'read_retries', 'max_redirects', 'operation_timeout',
              'status_timeout', 'name_uri_cache_timetolive',
              'allowed_methods')

    def override_with(self, override_config):
        """
        Return a new configuration object that represents the configuration
        from this configuration object acting as a default, and the specified
        configuration object overriding that default for any of its
        attributes that are not `None`.

        Parameters:

          override_config (:class:`~zhmcclient.RetryTimeoutConfig`):
            The configuration object overriding the defaults defined in this
            configuration object.

        Returns:

          :class:`~zhmcclient.RetryTimeoutConfig`:
            A new configuration object representing this configuration object,
            overridden by the specified configuration object.
        """
        ret = RetryTimeoutConfig()
        for attr in RetryTimeoutConfig._attrs:
            value = getattr(self, attr)
            if override_config and getattr(override_config, attr) is not None:
                value = getattr(override_config, attr)
            setattr(ret, attr, value)
        return ret


def get_password_interface(host, userid):
    """
    Interface to the password retrieval function that is invoked by
    :class:`~zhmcclient.Session` if no password is provided.

    Parameters:

      host (string): Hostname or IP address of the HMC
      userid (string): Userid on the HMC

    Returns:

      string: Password of the userid on the HMC
    """
    raise NotImplementedError


def _headers_for_logging(headers):
    """
    Return the input headers dict with blanked out values for any headers that
    carry sensitive information, so that it can be logged or displayed.

    The headers argument is not modified; if it needs to be changed, a copy is
    made that is changed.
    """
    if headers and 'X-API-Session' in headers:
        headers = headers.copy()
        headers['X-API-Session'] = BLANKED_OUT_STRING
    return headers


class Session:
    """
    A session to the HMC, optionally in context of an HMC user.

    The session supports operations that require to be authenticated, as well
    as operations that don't (e.g. obtaining the API version).

    The session can keep statistics about the elapsed time for issuing HTTP
    requests against the HMC API. Instance variable
    :attr:`~zhmcclient.Session.time_stats_keeper` is used to enable/disable the
    measurements, and to print the statistics.

    HMC/SE version requirements: None
    """

    default_rt_config = RetryTimeoutConfig(
        connect_timeout=DEFAULT_CONNECT_TIMEOUT,
        connect_retries=DEFAULT_CONNECT_RETRIES,
        read_timeout=DEFAULT_READ_TIMEOUT,
        read_retries=DEFAULT_READ_RETRIES,
        max_redirects=DEFAULT_MAX_REDIRECTS,
        operation_timeout=DEFAULT_OPERATION_TIMEOUT,
        status_timeout=DEFAULT_STATUS_TIMEOUT,
        name_uri_cache_timetolive=DEFAULT_NAME_URI_CACHE_TIMETOLIVE,
    )

    def __init__(self, host, userid=None, password=None, session_id=None,
                 get_password=None, retry_timeout_config=None,
                 port=DEFAULT_HMC_PORT, verify_cert=True):
        # pylint: disable=line-too-long
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
          In this case, the `host` parameter must specify the single HMC that
          has that session.

        * `session_id` only: The specified session-id will be stored in this
          session object, so that the session is initially in a logged-on
          state. Subsequent operations that require logon will use the stored
          session-id. Once the HMC expires the session-id, subsequent
          operations that require logon will cause an
          :exc:`~zhmcclient.ServerAuthError` to be raised (because
          userid/password have not been specified, so an automatic re-logon is
          not possible).
          In this case, the `host` parameter must specify the single HMC that
          has that session.

        * Neither `userid`/`password` nor `session_id`: Only operations that do
          not require logon, are possible.

        Parameters:

          host (:term:`string` or iterable of :term:`string`):
            HMC host or list of HMC hosts to try from.
            For valid formats, see the :attr:`~zhmcclient.Session.host`
            property.
            If `session_id` is specified, this must be the single HMC that has
            that session.
            Must not be `None`.

          userid (:term:`string`):
            Userid of the HMC user to be used, or `None`.

          password (:term:`string`):
            Password of the HMC user to be used, if `userid` was specified.

          session_id (:term:`string`):
            Session-id to be used for this session, or `None`.

          get_password (:term:`callable`):
            A password retrieval function, or `None`.

            If provided, this function will be called if a password is needed
            but not provided. This mechanism can be used for example by command
            line interfaces for prompting for the password.

            The password retrieval function must follow the interface
            defined in :func:`~zhmcclient.get_password_interface`.

          retry_timeout_config (:class:`~zhmcclient.RetryTimeoutConfig`):
            The retry/timeout configuration for this session for use by any of
            its HMC operations, overriding any defaults.

            `None` for an attribute in that configuration object means that the
            default value will be used for that attribute.

            `None` for the entire `retry_timeout_config` parameter means that a
            default configuration will be used with the default values for all
            of its attributes.

            See :ref:`Constants` for the default values.

          port (:term:`integer`):
            HMC TCP port. Defaults to
            :attr:`~zhmcclient._constants.DEFAULT_HMC_PORT`.
            For details, see the :attr:`~zhmcclient.Session.port` property.

          verify_cert (bool or :term:`string`):
            Controls whether and how the client verifies the server certificate
            presented by the HMC during SSL/TLS handshake:

            * `False`: Do not verify the HMC certificate. Not verifying the HMC
              certificate means the zhmcclient will not detect hostname
              mismatches, expired certificates, revoked certificates, or
              otherwise invalid certificates. Since this mode makes the
              connection vulnerable to man-in-the-middle attacks, it is insecure
              and should not be used in production environments.

            * `True`: Verify the HMC certificate using the CA certificates from
              the first of these locations:

              - The file or directory in the REQUESTS_CA_BUNDLE env.var, if set
              - The file or directory in the CURL_CA_BUNDLE env.var, if set
              - The Python 'certifi' package (which contains the
                `Mozilla Included CA Certificate List <https://wiki.mozilla.org/CA/Included_Certificates>`_).

            * :term:`string`: Path name of a certificate file or directory.
              Verify the HMC certificate using the CA certificates in that file
              or directory.

            For details, see the :ref:`HMC certificate` section.

            *Added in version 0.31*
        """  # noqa: E501
        # pylint: enable=line-too-long

        if isinstance(host, str):
            self._hosts = [host]
        else:
            self._hosts = list(host)
            assert len(self._hosts) >= 1
        self._port = port
        self._userid = userid
        self._password = password
        self._verify_cert = verify_cert
        self._get_password = get_password
        self._retry_timeout_config = self.default_rt_config.override_with(
            retry_timeout_config)
        self._headers = copy(_STD_HEADERS)  # dict with standard HTTP headers
        if session_id is not None:
            # Create a logged-on state (nearly same state as in _do_logon())
            self._session_id = session_id
            self._session = self._new_session(self.retry_timeout_config)
            self._headers['X-API-Session'] = session_id
            assert len(self._hosts) == 1
            self._actual_host = self._hosts[0]
            self._base_url = \
                self._create_base_url(self._actual_host, self._port)
            # The following are set in _do_logon()) but not here:
            self._session_credential = None
            self._object_topic = None
            self._job_topic = None
        else:
            # Create a logged-off state (same state as in _do_logoff())
            self._session_id = None
            self._session = None
            self._actual_host = None
            self._base_url = None
            self._session_credential = None
            self._object_topic = None
            self._job_topic = None
        self._time_stats_keeper = TimeStatsKeeper()
        self._auto_updater = AutoUpdater(self)

    def __repr__(self):
        """
        Return a string with the state of this session, for debug purposes.
        """
        headers = _headers_for_logging(self.headers)
        blanked_session_id = BLANKED_OUT_STRING if self._session_id else None
        blanked_password = BLANKED_OUT_STRING if self._password else None
        ret = (
            f"{repr_obj_id(self)} (\n"
            f"  _hosts={self._hosts!r},\n"
            f"  _userid={self._userid!r},\n"
            f"  _password={blanked_password!r},\n"
            f"  _verify_cert={self._verify_cert!r},\n"
            f"  _get_password={self._get_password!r},\n"
            f"  _retry_timeout_config={self._retry_timeout_config!r},\n"
            f"  _actual_host={self._actual_host!r},\n"
            f"  _base_url={self._base_url!r},\n"
            f"  _headers={headers!r},\n"
            f"  _session_id={blanked_session_id!r},\n"
            f"  _session={self._session!r}\n"
            f"  _object_topic={self._object_topic!r}\n"
            f"  _job_topic={self._job_topic!r}\n"
            f"  _auto_updater={self._auto_updater!r}\n"
            ")")
        return ret

    @property
    def host(self):
        """
        :term:`string` or list of :term:`string`: HMC host or redundant HMC
        hosts to use. The first working HMC from this list will actually be
        used. The working state of the HMC is detrmined using the
        'Query API Version' operation for which no authentication is needed.

        Each host will be in one of the following formats:

          * a short or fully qualified DNS hostname
          * a literal (= dotted) IPv4 address
          * a literal IPv6 address, formatted as defined in :term:`RFC3986`
            with the extensions for zone identifiers as defined in
            :term:`RFC6874`, supporting ``-`` (minus) for the delimiter
            before the zone ID string, as an additional choice to ``%25``
        """
        if len(self._hosts) == 1:
            host = self._hosts[0]
        else:
            host = self._hosts
        return host

    @property
    def actual_host(self):
        """
        :term:`string` or `None`: The HMC host that is actually used for this
        session, if the session is in the logged-on state. `None`, if the
        session is in the logged-off state.

        The HMC host will be in one of the following formats:

          * a short or fully qualified DNS hostname
          * a literal (= dotted) IPv4 address
          * a literal IPv6 address, formatted as defined in :term:`RFC3986`
            with the extensions for zone identifiers as defined in
            :term:`RFC6874`, supporting ``-`` (minus) for the delimiter
            before the zone ID string, as an additional choice to ``%25``
        """
        return self._actual_host

    @property
    def port(self):
        """
        :term:`integer`: HMC TCP port that is used for this session.
        """
        return self._port

    @property
    def userid(self):
        """
        :term:`string`: HMC userid that is used for this session.

        If `None`, only operations that do not require authentication, can be
        performed.
        """
        return self._userid

    @property
    def verify_cert(self):
        """
        bool or :term:`string`: Controls whether and how the client verifies
        server certificate presented by the HMC during SSL/TLS handshake.

        For details, see the same-named init parameter.
        """
        return self._verify_cert

    @property
    def get_password(self):
        """
        The password retrieval function, or `None`.

        The password retrieval function must follow the interface defined in
        :func:`~zhmcclient.get_password_interface`.
        """
        return self._get_password

    @property
    def retry_timeout_config(self):
        """
        :class:`~zhmcclient.RetryTimeoutConfig`: The effective retry/timeout
        configuration for this session for use by any of its HMC operations,
        taking into account the defaults and the session-specific overrides.
        """
        return self._retry_timeout_config

    @property
    def base_url(self):
        """
        :term:`string` or `None`: Base URL of the HMC that is actually used for
        this session, if the session is in the logged-on state. `None`, if the
        session is in the logged-off state.

        Example:

        .. code-block:: text

            https://myhmc.acme.com:6794
        """
        return self._base_url

    @property
    def headers(self):
        """
        :term:`header dict`: HTTP headers that are used in requests sent
        for this session.

        Initially, this is the following set of headers:

        .. code-block:: text

            Content-type: application/json
            Accept: */*

        When the session is logged on to the HMC, the session token is added
        to these headers:

        .. code-block:: text

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
        :term:`string` or `None`: Session ID (= HMC session token) used for this
        session, if the session is in the logged-on state. `None`, if the
        session is in the logged-off state.

        In the logged-off state, any request that requires logon will first
        cause a session to be created on the HMC and will store the session ID
        returned by the HMC in this property.

        In the logged-on state, the session ID stored in this property will be
        used for any requests to the HMC.
        """
        return self._session_id

    @property
    def session_credential(self):
        """
        :term:`string` or `None`: Session credential for this session returned
        by the HMC, if the session is in the logged-on state. `None`, if the
        session is in the logged-off state.
        """
        return self._session_credential

    @property
    def session(self):
        """
        :term:`string` or `None`: :class:`requests.Session` object for this
        session, if the session is in the logged-on state. `None`, if the
        session is in the logged-off state.
        """
        return self._session

    @property
    def object_topic(self):
        """
        :term:`string` or `None`: Name of the notification topic the HMC will
        use to send object-related notification messages to this session, if
        the session is in the logged-on state. `None`, if the session is in the
        logged-off state.

        The associated topic type is "object-notification".
        """
        return self._object_topic

    @property
    def job_topic(self):
        """
        :term:`string` or `None`: Name of the notification topic the HMC will
        use to send job notification messages to this session, if the session
        is in the logged-on state. `None`, if the session is in the logged-off
        state.

        The associated topic type is "job-notification".
        """
        return self._job_topic

    @property
    def auto_updater(self):
        """
        :class:`~zhmcclient.AutoUpdater`: Updater for
        :ref:`auto-updating` of resource and manager objects.
        """
        return self._auto_updater

    @logged_api_call
    def logon(self, verify=False, always=False):
        """
        Make sure this session object is logged on to the HMC.

        If `verify=False`, this method determines the logged-on state of this
        session object based on whether there is a session ID set in this
        session object. If a session ID is set, it is assumed to be valid and
        no new session is created on the HMC. Otherwise, a new session will be
        created on the HMC.

        If `verify=True`, this method determines the logged-on state of this
        session object in addition by performing a read operation on the HMC
        that requires to be logged on but no specific authorizations. If a
        session ID is set and if that operation succeeds, no new session is
        created on the HMC. Any failure of that read operation will be ignored.
        Otherwise, a new session will be created on the HMC.

        When a new session has been successfully created on the HMC, the
        :attr:`session_id` attribute of this session object will be set to the
        session ID returned by the HMC to put it into the logged-on state.

        Any exceptions raised from this method are always related to the
        creation of a new session on the HMC - any failures of the read
        operation in the verification case are always ignored.

        Parameters:

          verify (bool): Verify the validity of an existing session ID.

          always (bool): Unconditionally log on, regardless of an existing
            session ID.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        need_logon = False
        if self._session_id is None or always:
            need_logon = True
        elif verify:
            try:
                self.get('/api/console', logon_required=False,
                         renew_session=False)
            except Error:
                need_logon = True
        if need_logon:
            self._do_logon()

    @logged_api_call
    def logoff(self, verify=False):
        # pylint: disable=unused-argument
        """
        Make sure this session object is logged off from the HMC.

        If a session ID is set in this session object, its session will be
        deleted on the HMC. If that delete operation fails due to an invalid
        session ID, that failure will be ignored. Any other failures of that
        delete operation will be raised as exceptions.

        When the session has been successfully deleted on the HMC, the
        :attr:`session_id` attribute of this session object will be set to
        `None` to put it into the logged-off state.

        Parameters:

          verify (bool): Deprecated: This parameter will be ignored.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if self._session_id:
            self._do_logoff()

    @logged_api_call
    def is_logon(self, verify=False):
        """
        Return a boolean indicating whether this session object is logged on to
        the HMC.

        If `verify=False`, this method determines the logged-on state based
        on whether there is a session ID set in this object. If a session ID is
        set, it is assumed to be valid, and `True` is returned. Otherwise,
        `False` is returned. In that case, no exception is ever raised.

        If `verify=True`, this method determines the logged-on state in
        addition by verifying a session ID that is set, by performing a read
        operation on the HMC that requires to be logged on but no specific
        authorizations. If a session ID is set and if that read operation
        succeeds, `True` is returned. If no session ID is set or if that read
        operation fails due to an invalid session ID, `False` is returned.
        Any other failures of that read operation are raised as exceptions,
        because that indicates that a verification with the HMC could not be
        performed.

        Parameters:

          verify (bool): Verify the validity of an existing session ID.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if self._session_id is None:
            return False
        if verify:
            try:
                self.get('/api/console', logon_required=False,
                         renew_session=False)
            except ServerAuthError:
                return False
        return True

    def _do_logon(self):
        """
        Log on, unconditionally. This can be used to re-logon.
        This requires credentials to be provided.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # Determine working HMC for this session
        self._actual_host = self._determine_actual_host()
        self._base_url = self._create_base_url(self._actual_host, self._port)

        HMC_LOGGER.debug("Logging on to HMC %s", self._actual_host)

        if self._userid is None:
            raise ClientAuthError("Userid is not provided.")

        if self._password is None:
            if self._get_password:
                self._password = \
                    self._get_password(self._actual_host, self._userid)
            elif self._session_id:
                raise ClientAuthError(
                    "Session ID is not valid and no password for fresh "
                    "logon was provided.")
            else:
                raise ClientAuthError("Password is not provided.")

        # Create an HMC session
        logon_uri = '/api/sessions'
        logon_body = {
            'userid': self._userid,
            'password': self._password
        }
        self._headers.pop('X-API-Session', None)  # Just in case
        self._session = self._new_session(self.retry_timeout_config)
        logon_res = self.post(logon_uri, body=logon_body, logon_required=False)
        self._session_id = logon_res['api-session']
        self._session_credential = logon_res['session-credential']
        self._headers['X-API-Session'] = self._session_id
        self._object_topic = logon_res['notification-topic']
        self._job_topic = logon_res['job-notification-topic']

    @staticmethod
    def _create_base_url(host, port):
        """
        Encapsulates how the base URL of the HMC is constructed.
        """
        return f"{_HMC_SCHEME}://{host}:{port}"

    def _determine_actual_host(self):
        """
        Determine the actual HMC host to be used.

        If a single HMC host is specified, that host is used without further
        verification as to whether it is available.

        If more than one HMC host is specified, the first available host is
        used. Availability of the HMC is determined using the
        'Query API Version' operation, for which no logon is required.
        If no available HMC can be found, raises the ConnectionError of the
        last HMC that was tried.
        """

        if len(self._hosts) == 1:
            host = self._hosts[0]
            HMC_LOGGER.debug("Using the only HMC specified without verifying "
                             "its availability: %s", host)
            return host

        last_exc = None
        for host in self._hosts:
            HMC_LOGGER.debug("Trying HMC for availability: %s", host)
            self._base_url = self._create_base_url(host, self._port)
            try:
                self.get('/api/version', logon_required=False,
                         renew_session=False)
            except ConnectionError as exc:
                last_exc = exc
                continue

            HMC_LOGGER.debug("Using available HMC: %s", host)
            return host

        HMC_LOGGER.debug("Did not find an available HMC in: %s",
                         self._hosts)
        raise last_exc

    @staticmethod
    def _new_session(retry_timeout_config):
        """
        Return a new `requests.Session` object.
        """
        retry = urllib3.Retry(
            total=retry_timeout_config.connect_retries,
            connect=retry_timeout_config.connect_retries,
            read=retry_timeout_config.read_retries,
            allowed_methods=retry_timeout_config.allowed_methods,
            redirect=retry_timeout_config.max_redirects)
        session = requests.Session()
        session.mount('https://',
                      requests.adapters.HTTPAdapter(max_retries=retry))
        session.mount('http://',
                      requests.adapters.HTTPAdapter(max_retries=retry))
        return session

    def _do_logoff(self):
        """
        Log off, unconditionally.

        This deletes the session on the HMC. If that deletion operation fails
        due to an invalid session ID, that failure is ignored.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ConnectionError`
        """
        HMC_LOGGER.debug("Logging off from HMC %s", self._actual_host)

        session_uri = '/api/sessions/this-session'
        try:
            self.delete(session_uri, logon_required=False, renew_session=False)
        except (ServerAuthError, ConnectionError):
            # HMC shutdown or broken network causes ConnectionError.
            # Invalid credentials cause ServerAuthError.
            pass

        self._actual_host = None
        self._base_url = None
        self._session_id = None
        self._session = None
        self._headers.pop('X-API-Session', None)
        self._object_topic = None
        self._job_topic = None

    @staticmethod
    def _log_http_request(
            method, url, resource, headers=None, content=None,
            content_len=None):
        """
        Log the HTTP request of an HMC REST API call, at the debug level.

        Parameters:

          method (:term:`string`): HTTP method name in upper case, e.g. 'GET'

          url (:term:`string`): HTTP URL (base URL and operation URI)

          headers (iterable): HTTP headers used for the request

          content (:term:`string`): HTTP body (aka content) used for the
            request (byte string or unicode string)

          content_len (int): Length of content in Bytes, or `None` for
            determining the length from the content string
        """

        content_msg = None
        if content is not None:
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            assert isinstance(content, str)
            if content_len is None:
                content_len = len(content)  # may change after JSON conversion
            try:
                content_dict = json2dict(content)
            except ValueError:
                # If the content is not JSON, we assume it does not contain
                # structured data such as a password or session IDs.
                pass
            else:
                for pname in BLANKED_OUT_PROPERTIES:
                    if pname in content_dict:
                        content_dict[pname] = BLANKED_OUT_STRING
                content = dict2json(content_dict)
            trunc = 30000
            if content_len > trunc:
                content_label = f"content(first {trunc} B of {content_len} B)"
                content_msg = content[0:trunc] + '...(truncated)'
            else:
                content_label = f'content({content_len} B)'
                content_msg = content
        else:
            content_label = 'content'
            content_msg = content

        if resource:
            names = []
            res_class = resource.manager.class_name
            while resource:
                # Using resource.name gets into an infinite recursion when
                # the resource name is not present, due to pulling the
                # properties in that case. We take the careful approach.
                name_prop = resource.manager.name_prop
                name = resource.properties.get(name_prop, '<unknown>')
                names.insert(0, name)
                resource = resource.manager.parent
            res_str = f" ({res_class} {'.'.join(names)})"
        else:
            res_str = ""

        HMC_LOGGER.debug("Request: %s %s%s, headers: %r, %s: %r",
                         method, url, res_str, _headers_for_logging(headers),
                         content_label, content_msg)

    @staticmethod
    def _log_http_response(
            method, url, resource, status, headers=None, content=None):
        """
        Log the HTTP response of an HMC REST API call, at the debug level.

        Parameters:

          method (:term:`string`): HTTP method name in upper case, e.g. 'GET'

          url (:term:`string`): HTTP URL (base URL and operation URI)

          status (integer): HTTP status code

          headers (iterable): HTTP headers returned in the response

          content (:term:`string`): HTTP body (aka content) returned in the
            response (byte string or unicode string)
        """

        if content is not None:
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            assert isinstance(content, str)
            content_len = len(content)  # may change after JSON conversion
            try:
                content_dict = json2dict(content)
            except ValueError:
                # If the content is not JSON (e.g. response from metrics
                # context retrieval), we assume it does not contain structured
                # data such as a password or session IDs.
                pass
            else:
                if 'request-headers' in content_dict:
                    headers_dict = content_dict['request-headers']
                    if 'x-api-session' in headers_dict:
                        headers_dict['x-api-session'] = BLANKED_OUT_STRING
                if 'api-session' in content_dict:
                    content_dict['api-session'] = BLANKED_OUT_STRING
                if 'session-credential' in content_dict:
                    content_dict['session-credential'] = BLANKED_OUT_STRING
                content = dict2json(content_dict)
            if status >= 400:
                content_label = 'content'
                content_msg = content
            else:
                trunc = 30000
                if content_len > trunc:
                    content_label = \
                        f"content(first {trunc} B of {content_len} B)"
                    content_msg = content[0:trunc] + '...(truncated)'
                else:
                    content_label = f'content({len(content)} B)'
                    content_msg = content
        else:
            content_label = 'content'
            content_msg = content

        if resource:
            names = []
            res_class = resource.manager.class_name
            while resource:
                # Using resource.name gets into an infinite recursion when
                # the resource name is not present, due to pulling the
                # properties in that case. We take the careful approach.
                name_prop = resource.manager.name_prop
                name = resource.properties.get(name_prop, '<unknown>')
                names.insert(0, name)
                resource = resource.manager.parent
            res_str = f" ({res_class} {'.'.join(names)})"
        else:
            res_str = ""

        HMC_LOGGER.debug("Respons: %s %s%s, status: %s, "
                         "headers: %r, %s: %r",
                         method, url, res_str, status,
                         _headers_for_logging(headers),
                         content_label, content_msg)

    @logged_api_call
    def get(self, uri, resource=None, logon_required=True, renew_session=True):
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

          renew_session (bool):
            Boolean indicating whether the session should be renewed in case
            it is expired.

        Returns:

          :term:`json object` with the operation result.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        elif self._base_url is None:
            self._actual_host = self._determine_actual_host()
            self._base_url = \
                self._create_base_url(self._actual_host, self._port)
        url = self._base_url + uri
        self._log_http_request('GET', url, resource=resource,
                               headers=self.headers)
        stats = self.time_stats_keeper.get_stats('get ' + uri)
        stats.begin()
        req = self._session or requests
        req_timeout = (self.retry_timeout_config.connect_timeout,
                       self.retry_timeout_config.read_timeout)
        try:
            result = req.get(url, headers=self.headers, verify=self.verify_cert,
                             timeout=req_timeout)
        # Note: The requests method may raise OSError/IOError in case of
        # HMC certificate validation issues (e.g. incorrect cert path)
        except (requests.exceptions.RequestException, OSError) as exc:
            _handle_request_exc(exc, self.retry_timeout_config)
        finally:
            stats.end()
        self._log_http_response('GET', url, resource=resource,
                                status=result.status_code,
                                headers=result.headers,
                                content=result.content)

        if result.status_code == 200:
            return _result_object(result)
        if result.status_code == 403:
            result_object = _result_object(result)
            reason = result_object.get('reason', None)
            message = result_object.get('message', None)
            HMC_LOGGER.debug("Received HTTP status 403.%d on GET %s: %s",
                             reason, uri, message)

            if reason in (4, 5):
                # 403.4: No session ID was provided
                # 403.5: Session ID was invalid
                if renew_session:
                    self._do_logon()
                    return self.get(
                        uri, resource=resource, logon_required=False,
                        renew_session=False)

            if reason == 1:
                # Login user's authentication is fine; this is an authorization
                # issue, so we don't raise ServerAuthError.
                raise HTTPError(result_object)

            msg = result_object.get('message', None)
            raise ServerAuthError(
                "HTTP authentication failed with "
                f"{result.status_code},{reason}: {msg}",
                HTTPError(result_object))

        result_object = _result_object(result)
        raise HTTPError(result_object)

    @logged_api_call
    def post(self, uri, resource=None, body=None, logon_required=True,
             wait_for_completion=False, operation_timeout=None,
             renew_session=True, busy_retries=0, busy_wait=0):
        """
        Perform the HTTP POST method against the resource identified by a URI,
        using a provided request body.

        A set of standard HTTP headers is automatically part of the request.

        HMC operations using HTTP POST are either synchronous or asynchronous.
        Asynchronous operations return the URI of an asynchronously executing
        job that can be queried for status and result.

        Examples for synchronous operations:

        * With no result: "Logon", "Update CPC Properties"
        * With a result: "Create Partition"

        Examples for asynchronous operations:

        * With no result: "Start Partition"

        The `wait_for_completion` parameter of this method can be used to deal
        with asynchronous HMC operations in a synchronous way.

        If executing the operation reveals that the HMC session token is
        expired, this method re-logs on and retries the operation.

        The timeout and retry

        Parameters:

          uri (:term:`string`):
            Relative URI path of the resource, e.g. "/api/session".
            This URI is relative to the base URL of the session (see the
            :attr:`~zhmcclient.Session.base_url` property).
            Must not be `None`.

          body (:term:`json object` or :term:`string` or file-like object):
            The HTTP request body (payload).
            If a JSON object (=dict) is provided, it will be serialized into
            a UTF-8 encoded binary string.
            If a Unicode string is provided, it will be encoded into a UTF-8
            encoded binary string.
            If a binary string is provided, it will be used unchanged.
            If a file-like object is provided, it must return binary strings,
            i.e. the file must have been opened in binary mode.
            `None` means the same as an empty dictionary, namely that no HTTP
            body is included in the request.

          logon_required (bool):
            Boolean indicating whether the operation requires that the session
            is logged on to the HMC. For example, the "Logon" operation does
            not require that.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation.

            A value of `True` will cause an additional entry in the time
            statistics to be created that represents the entire asynchronous
            operation including the waiting for its completion.
            That time statistics entry will have a URI that is the targeted
            URI, appended with "+completion".

            For synchronous HMC operations, this parameter has no effect on
            the operation execution or on the return value of this method, but
            it should still be set (or defaulted) to `False` in order to avoid
            the additional entry in the time statistics.

          operation_timeout (:term:`number`):
            Timeout in seconds, when waiting for completion of an asynchronous
            operation. The special value 0 means that no timeout is set. `None`
            means that the default async operation timeout of the session is
            used.

            For `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised when the timeout
            expires.

            For `wait_for_completion=False`, this parameter has no effect.

          renew_session (bool):
            Boolean indicating whether the session should be renewed in case
            it is expired.

          busy_retries (int): Number of retries when HMC returns busy
            (HTTP status 409 with reason code 1 or 2).

          busy_wait (float): Waiting time in seconds between busy retries.

        Returns:

          : A :term:`json object` or `None` or a :class:`~zhmcclient.Job`
          object, as follows:

          * For synchronous HMC operations, and for asynchronous HMC
            operations with `wait_for_completion=True`:

            If this method returns, the HMC operation has completed
            successfully (otherwise, an exception is raised).
            For asynchronous HMC operations, the associated job has been
            deleted.

            The return value is the result of the HMC operation as a
            :term:`json object`, or `None` if the operation has no result.
            See the section in the :term:`HMC API` book about the specific
            HMC operation for a description of the members of the returned
            JSON object.

            If the HMC operation response has a "Location" header, it is the
            URI of the newly created resource. If the response does not
            have an 'object-uri' or 'element-uri' field, this method adds the
            URI from the "Location" header field to the response as the
            'location-uri' field. This is needed e.g. for the
            "Create Partition Link" operation, because that operation does not
            return the new URI in any response field.

          * For asynchronous HMC operations with `wait_for_completion=False`:

            If this method returns, the asynchronous execution of the HMC
            operation has been started successfully as a job on the HMC (if
            the operation could not be started, an exception is raised).

            The return value is a :class:`~zhmcclient.Job` object
            representing the job on the HMC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the asynchronous operation.
          :exc:`TypeError`: Body has invalid type.
        """
        if logon_required:
            self.logon()
        elif self._base_url is None:
            self._actual_host = self._determine_actual_host()
            self._base_url = \
                self._create_base_url(self._actual_host, self._port)
        url = self._base_url + uri
        headers = self.headers.copy()  # Standard headers

        log_len = None
        if body is None:
            data = None
            log_data = None
        elif isinstance(body, dict):
            data = json.dumps(body)
            # Produces unicode string on py3, and unicode or byte string on py2.
            # Content-type is already set to 'application/json' in standard
            # headers.
            if isinstance(data, str):
                log_data = data
                data = data.encode('utf-8')
            else:
                log_data = data
        elif isinstance(body, str):
            data = body.encode('utf-8')
            log_data = body
            headers['Content-type'] = 'application/octet-stream'
        elif isinstance(body, bytes):
            data = body
            log_data = body
            headers['Content-type'] = 'application/octet-stream'
        elif isinstance(body, Iterable):
            # File-like objects, e.g. io.BufferedReader or io.TextIOWrapper
            # returned from open() or io.open().
            data = body
            try:
                mode = body.mode
            except AttributeError:
                mode = 'unknown'
            log_data = f"<file-like object with mode {mode}>"
            log_len = -1
            headers['Content-type'] = 'application/octet-stream'
        else:
            raise TypeError(f"Body has invalid type: {type(body)}")

        self._log_http_request('POST', url, resource=resource, headers=headers,
                               content=log_data, content_len=log_len)
        req = self._session or requests
        req_timeout = (self.retry_timeout_config.connect_timeout,
                       self.retry_timeout_config.read_timeout)
        if wait_for_completion:
            stats_total = self.time_stats_keeper.get_stats(
                'post ' + uri + '+completion')
            stats_total.begin()
        try:
            stats = self.time_stats_keeper.get_stats('post ' + uri)
            stats.begin()
            try:
                if data is None:
                    result = req.post(url, headers=headers,
                                      verify=self.verify_cert,
                                      timeout=req_timeout)
                else:
                    result = req.post(url, data=data, headers=headers,
                                      verify=self.verify_cert,
                                      timeout=req_timeout)
            # Note: The requests method may raise OSError/IOError in case of
            # HMC certificate validation issues (e.g. incorrect cert path)
            except (requests.exceptions.RequestException, OSError) \
                    as exc:
                _handle_request_exc(exc, self.retry_timeout_config)
            finally:
                stats.end()
            self._log_http_response('POST', url, resource=resource,
                                    status=result.status_code,
                                    headers=result.headers,
                                    content=result.content)

            if result.status_code in (200, 201):
                return _result_object(result)

            if result.status_code == 204:
                # No content
                return None

            if result.status_code == 202:
                if result.content == b'':
                    # Some operations (e.g. "Restart Console",
                    # "Shutdown Console" or "Cancel Job") return 202
                    # with no response content.
                    return None

                # This is the most common case to return 202: An
                # asynchronous job has been started.
                result_object = _result_object(result)
                try:
                    location_uri = result.headers['Location']
                except KeyError:
                    location_uri = None
                job_uri = result_object['job-uri']
                job = Job(self, job_uri, 'POST', uri)
                if wait_for_completion:
                    result = job.wait_for_completion(operation_timeout)
                    # The following addition of 'location-uri' from the
                    # Location header is for cases where a create operation
                    # does not return the new URI in the response. For example,
                    # the "Create Partition Link" operation does that.
                    if location_uri and 'element-uri' not in result and \
                            'object-uri' not in result:
                        result['location-uri'] = location_uri
                    return result
                return job

            if result.status_code == 403:
                result_object = _result_object(result)
                reason = result_object.get('reason', None)
                message = result_object.get('message', None)
                HMC_LOGGER.debug("Received HTTP status 403.%d on POST %s: %s",
                                 reason, uri, message)

                if reason in (4, 5):
                    # 403.4: No session ID was provided
                    # 403.5: Session ID was invalid
                    if renew_session:
                        self._do_logon()
                        return self.post(
                            uri, resource=resource, body=body,
                            logon_required=False, renew_session=False,
                            wait_for_completion=wait_for_completion,
                            operation_timeout=operation_timeout,
                            busy_retries=busy_retries, busy_wait=busy_wait)

                if reason == 1:
                    # Login user's authentication is fine; this is an
                    # authorization issue, so we don't raise ServerAuthError.
                    raise HTTPError(result_object)

                msg = result_object.get('message', None)
                raise ServerAuthError(
                    "HTTP authentication failed with "
                    f"{result.status_code},{reason}: {msg}",
                    HTTPError(result_object))

            if result.status_code == 409:
                result_object = _result_object(result)
                reason = result_object.get('reason', None)
                message = result_object.get('message', None)
                if reason in (1, 2) and busy_retries > 0:
                    # Reason codes for retrying:
                    # 409.1: Target object is not in correct state.
                    # 409.2: Target object is busy performing another operation.
                    HMC_LOGGER.debug(
                        "Retrying operation (%d retries left) after %d s upon "
                        "receiving HTTP status 409.%d on POST %s: %s ",
                        busy_retries, busy_wait, reason, uri, message)
                    busy_retries -= 1
                    if busy_wait > 0:
                        time.sleep(busy_wait)
                    return self.post(
                        uri, resource=resource, body=body,
                        logon_required=False, renew_session=False,
                        wait_for_completion=wait_for_completion,
                        operation_timeout=operation_timeout,
                        busy_retries=busy_retries, busy_wait=busy_wait)

            result_object = _result_object(result)
            raise HTTPError(result_object)

        finally:
            if wait_for_completion:
                stats_total.end()

    @logged_api_call
    def delete(
            self, uri, resource=None, logon_required=True, renew_session=True,
            busy_retries=0, busy_wait=0):
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

          renew_session (bool):
            Boolean indicating whether the session should be renewed in case
            it is expired. For example, for the logoff operation, it does not
            make sense to do that.

          busy_retries (int): Number of retries when HMC returns busy
            (HTTP status 409 with reason code 1 or 2).

          busy_wait (float): Waiting time in seconds between busy retries.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if logon_required:
            self.logon()
        elif self._base_url is None:
            self._actual_host = self._determine_actual_host()
            self._base_url = \
                self._create_base_url(self._actual_host, self._port)
        url = self._base_url + uri
        self._log_http_request('DELETE', url, resource=resource,
                               headers=self.headers)
        stats = self.time_stats_keeper.get_stats('delete ' + uri)
        stats.begin()
        req = self._session or requests
        req_timeout = (self.retry_timeout_config.connect_timeout,
                       self.retry_timeout_config.read_timeout)
        try:
            result = req.delete(url, headers=self.headers,
                                verify=self.verify_cert, timeout=req_timeout)
        # Note: The requests method may raise OSError/IOError in case of
        # HMC certificate validation issues (e.g. incorrect cert path)
        except (requests.exceptions.RequestException, OSError) as exc:
            _handle_request_exc(exc, self.retry_timeout_config)
        finally:
            stats.end()
        self._log_http_response('DELETE', url, resource=resource,
                                status=result.status_code,
                                headers=result.headers,
                                content=result.content)

        if result.status_code in (200, 204):
            return

        if result.status_code == 403:
            result_object = _result_object(result)
            reason = result_object.get('reason', None)
            message = result_object.get('message', None)
            HMC_LOGGER.debug("Received HTTP status 403.%d on DELETE %s: %s",
                             reason, uri, message)

            if reason in (4, 5):
                # 403.4: No session ID was provided
                # 403.5: Session ID was invalid
                if renew_session:
                    self._do_logon()
                    self.delete(uri, resource=resource, logon_required=False,
                                renew_session=False,
                                busy_retries=busy_retries, busy_wait=busy_wait)
                    return

            if reason == 1:
                # Login user's authentication is fine; this is an authorization
                # issue, so we don't raise ServerAuthError.
                raise HTTPError(result_object)

            msg = result_object.get('message', None)
            raise ServerAuthError(
                "HTTP authentication failed with "
                f"{result.status_code},{reason}: {msg}",
                HTTPError(result_object))

        if result.status_code == 409:
            result_object = _result_object(result)
            reason = result_object.get('reason', None)
            message = result_object.get('message', None)
            if reason in (1, 2) and busy_retries > 0:
                # Reason codes for retrying:
                # 409.1: Target object is not in correct state.
                # 409.2: Target object is busy performing another operation.
                HMC_LOGGER.debug(
                    "Retrying operation (%d retries left) after %d s upon "
                    "receiving HTTP status 409.%d on DELETE %s: %s ",
                    busy_retries, busy_wait, reason, uri, message)
                busy_retries -= 1
                if busy_wait > 0:
                    time.sleep(busy_wait)
                self.delete(
                    uri, resource=resource, logon_required=False,
                    renew_session=False, busy_retries=busy_retries,
                    busy_wait=busy_wait)
                return

        result_object = _result_object(result)
        raise HTTPError(result_object)

    @logged_api_call
    def get_notification_topics(self):
        """
        The 'Get Notification Topics' operation returns a structure that
        describes the JMS notification topics associated with this session.

        Returns:

          : A list with one item for each notification topic. Each item is a
          dictionary with the following keys:

          * ``"topic-type"`` (string): Topic type, e.g. "job-notification".
          * ``"topic-name"`` (string): Topic name; can be used for
            subscriptions.
          * ``"object-uri"`` (string): When topic-type is
            "os-message-notification", this item is the canonical URI path
            of the Partition for which this topic exists.
            This field does not exist for the other topic types.
          * ``"include-refresh-messages"`` (bool): When the topic-type is
            "os-message-notification", this item indicates whether refresh
            operating system messages will be sent on this topic.
        """
        topics_uri = '/api/sessions/operations/get-notification-topics'
        response = self.get(topics_uri)
        return response['topics']

    def auto_update_subscribed(self):
        """
        Return whether this session is currently subscribed for
        :ref:`auto-updating`.

        Return:
          bool: Indicates whether session is subscribed.
        """
        return self._auto_updater.is_open()

    @logged_api_call
    def subscribe_auto_update(self):
        """
        Subscribe this session for :ref:`auto-updating`, if not currently
        subscribed.

        When not yet subscribed, the session is also logged on.

        When subscribed, object notifications will be sent by the HMC as
        resource objects on the HMC change their properties or come or go.
        These object notifications will be received by the client and will then
        update the properties of any Python resource objects that are enabled
        for auto-updating.

        This method is automatically called by
        :meth:`~zhmcclient.BaseResource.enable_auto_update` and thus does not
        need to be called by the user.
        """
        if not self._auto_updater.is_open():
            self._auto_updater.open()

    @logged_api_call
    def unsubscribe_auto_update(self):
        """
        Unsubscribe this session from :ref:`auto-updating`, if
        currently subscribed.

        When unsubscribed, object notifications are no longer sent by the HMC.

        This method is automatically called by
        :meth:`~zhmcclient.BaseResource.disable_auto_update` and thus does not
        need to be called by the user.
        """
        if self._auto_updater.is_open():
            self._auto_updater.close()


class Job:
    """
    A job on the HMC that performs an asynchronous HMC operation.

    This class supports checking the job for completion, and waiting for job
    completion.
    """

    def __init__(self, session, uri, op_method, op_uri):
        """
        Parameters:

          session (:class:`~zhmcclient.Session`):
            Session with the HMC.
            Must not be `None`.

          uri (:term:`string`):
            Canonical URI of the job on the HMC.
            Must not be `None`.

            Example: ``"/api/jobs/{job-id}"``

          op_method (:term:`string`):
            Name of the HTTP method of the operation that is executing
            asynchronously on the HMC.
            Must not be `None`.

            Example: ``"POST"``

          op_uri (:term:`string`):
            Canonical URI of the operation that is executing asynchronously on
            the HMC.
            Must not be `None`.

            Example: ``"/api/partitions/{partition-id}/stop"``
        """
        self._session = session
        self._uri = uri
        self._op_method = op_method
        self._op_uri = op_uri

    @property
    def session(self):
        """
        :class:`~zhmcclient.Session`: Session with the HMC.
        """
        return self._session

    @property
    def uri(self):
        """
        :term:`string`: Canonical URI of the job on the HMC.

        Example: ``"/api/jobs/{job-id}"``
        """
        return self._uri

    @property
    def op_method(self):
        """
        :term:`string`: Name of the HTTP method of the operation that is
        executing asynchronously on the HMC.

        Example: ``"POST"``
        """
        return self._op_method

    @property
    def op_uri(self):
        """
        :term:`string`: Canonical URI of the operation that is executing
        asynchronously on the HMC.

        Example: ``"/api/partitions/{partition-id}/stop"``
        """
        return self._op_uri

    @logged_api_call
    def query_status(self):
        """
        Get the current status of this job, and if completed also the
        operation results.

        This method performs the "Query Job Status" operation on the job.

        This is a low level operation, consider using
        :meth:`~zhmcclient.Job.check_for_completion` or
        :meth:`~zhmcclient.Job.wait_for_completion` instead.

        If the job no longer exists, :exc:`~zhmcclient.HTTPError` is raised
        with status code 404 and reason code 1.

        Returns:

          tuple(job_status, op_status, op_reason, op_result): With the following
          items:

          * job_status(string): Job status, one of:

            - "running" - indicates that the job was found and it has not ended
              at the time of the query.
            - "cancel-pending" - indicates that the job was found and it has
              not ended but cancellation has been requested.
            - "canceled" - indicates that the job's normal course of execution
              was interrupted by a cancel request, and the job has now ended.
            - "complete" - indicates that the job was found and has completed
              the operation, and the job has now ended.

          * op_status(int): HTTP status code of the operation performed by
            the job. Will be `None` if the job has not ended.

          * op_reason(int): HTTP reason code of the operation performed by
            the job. Will be `None` if the job has not ended.

          * op_result(dict): Result of the operation performed by
            the job, as described in the zhmcclient method that performed
            the operation. Will be `None` if the job has not ended.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        try:
            result = self.session.get(self.uri)
        except Error as exc:
            HMC_LOGGER.debug("Request: GET %s failed with %s: %s",
                             self.uri, exc.__class__.__name__, exc)
            raise

        job_status = result['status']
        op_status = result.get('job-status-code', None)
        op_reason = result.get('job-reason-code', None)
        op_result = result.get('job-results', None)

        return job_status, op_status, op_reason, op_result

    @logged_api_call
    def delete(self):
        """
        Delete this ended job on the HMC.

        This method performs the "Delete Completed Job Status" operation on the
        job.

        This is a low level operation, consider using
        :meth:`~zhmcclient.Job.check_for_completion` or
        :meth:`~zhmcclient.Job.wait_for_completion` instead, which delete the
        ended job.

        If the job has not ended (i.e. its `status` property is not "canceled"
        or"complete"), :exc:`~zhmcclient.HTTPError` is raised with status code
        409 and reason code 40.

        If the job no longer exists, :exc:`~zhmcclient.HTTPError` is raised
        with status code 404 and reason code 1.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        try:
            self.session.delete(self.uri)
        except Error as exc:
            HMC_LOGGER.debug("Request: DELETE %s failed with %s: %s",
                             self.uri, exc.__class__.__name__, exc)
            raise

    @logged_api_call
    def check_for_completion(self):
        """
        Check once for completion of the job and return completion status and
        result if it has completed.

        If the job completed in error, an :exc:`~zhmcclient.HTTPError`
        exception is raised.

        Returns:

          : A tuple (status, result) with:

          * status (:term:`string`): Completion status of the job, as
            returned in the ``status`` field of the response body of the
            "Query Job Status" HMC operation, as follows:

            * ``"complete"``: Job completed (successfully).
            * any other value: Job is not yet complete.

          * result (:term:`json object` or `None`): `None` for incomplete
            jobs. For completed jobs, the result of the original asynchronous
            operation that was performed by the job, from the ``job-results``
            field of the response body of the "Query Job Status" HMC
            operation. That result is a :term:`json object` as described
            for the asynchronous operation, or `None` if the operation has no
            result.

        Raises:

          :exc:`~zhmcclient.HTTPError`: The job completed in error, or the job
            status cannot be retrieved, or the job cannot be deleted.
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        try:
            job_result_obj = self.session.get(self.uri)
        except Error as exc:
            HMC_LOGGER.debug("Request: GET %s failed with %s: %s",
                             self.uri, exc.__class__.__name__, exc)
            raise

        job_status = job_result_obj['status']
        if job_status == 'complete':
            self.session.delete(self.uri)
            op_status_code = job_result_obj['job-status-code']
            if op_status_code in (200, 201):
                op_result_obj = job_result_obj.get('job-results', None)
            elif op_status_code == 204:
                # No content
                op_result_obj = None
            else:
                error_result_obj = job_result_obj.get('job-results', None)
                if not error_result_obj:
                    message = None
                elif 'message' in error_result_obj:
                    message = error_result_obj['message']
                elif 'error' in error_result_obj:
                    message = error_result_obj['error']
                else:
                    message = None
                error_obj = {
                    'http-status': op_status_code,
                    'reason': job_result_obj['job-reason-code'],
                    'message': message,
                    'request-method': self.op_method,
                    'request-uri': self.op_uri,
                }
                raise HTTPError(error_obj)
        else:
            op_result_obj = None
        return job_status, op_result_obj

    @logged_api_call
    def wait_for_completion(self, operation_timeout=None):
        """
        Wait for completion of the job, then delete the job on the HMC and
        return the result of the original asynchronous HMC operation, if it
        completed successfully.

        If the job completed in error, an :exc:`~zhmcclient.HTTPError`
        exception is raised.

        Parameters:

          operation_timeout (:term:`number`):
            Timeout in seconds, when waiting for completion of the job. The
            special value 0 means that no timeout is set. `None` means that the
            default async operation timeout of the session is used.

            If the timeout expires, a :exc:`~zhmcclient.OperationTimeout`
            is raised.

            This method gives completion of the job priority over strictly
            achieving the timeout. This may cause a slightly longer duration of
            the method than prescribed by the timeout.

        Returns:

          :term:`json object` or `None`:
            The result of the original asynchronous operation that was
            performed by the job, from the ``job-results`` field of the
            response body of the "Query Job Status" HMC operation. That result
            is a :term:`json object` as described for the asynchronous
            operation, or `None` if the operation has no result.

        Raises:

          :exc:`~zhmcclient.HTTPError`: The job completed in error, or the job
            status cannot be retrieved, or the job cannot be deleted.
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for job completion.
        """

        if operation_timeout is None:
            operation_timeout = \
                self.session.retry_timeout_config.operation_timeout
        if operation_timeout > 0:
            start_time = time.time()

        while True:
            try:
                job_status, op_result_obj = self.check_for_completion()
            except ConnectionError:
                HMC_LOGGER.debug("Retrying after ConnectionError while waiting"
                                 " for completion of job %s. This could be "
                                 "because HMC is restarting.", self.uri)
                job_status = None

            # We give completion of status priority over strictly achieving
            # the timeout, so we check status first. This may cause a longer
            # duration of the method than prescribed by the timeout.
            if job_status == 'complete':
                return op_result_obj

            if operation_timeout > 0:
                current_time = time.time()
                if current_time > start_time + operation_timeout:
                    raise OperationTimeout(
                        f"Waiting for completion of job {self.uri} timed out "
                        f"(operation timeout: {operation_timeout} s)",
                        operation_timeout)

            time.sleep(10)  # Avoid hot spin loop

    @logged_api_call
    def cancel(self):
        """
        Attempt to cancel this job.

        This method performs the "Cancel Job" operation on the job.

        The specific nature of the job and its current state of execution can
        affect the success of the cancellation.

        Not all jobs support cancellation; this is described in each zhmcclient
        method that can return a job.

        If the job exists, supports cancellation and has not yet completed (i.e.
        its `status` property is "running"), the cancellation is made pending
        for the job and its `status` property is changed to "cancel-pending".

        If the operation performed by the job does not support cancellation,
        :exc:`~zhmcclient.HTTPError` is raised with status code 404 and reason
        code 4.

        If the job supports cancellation and exists, but already has a
        cancellation request pending (i.e. its `status` property is
        "cancel-pending"), :exc:`~zhmcclient.HTTPError` is raised with status
        409 and reason code 42.

        If the job supports cancellation and exists, but already has ended
        (i.e. its `status` property is "complete" or "canceled"),
        :exc:`~zhmcclient.HTTPError` is raised with status code 409 and reason
        code 41.

        If the job supports cancellation but no longer exists,
        :exc:`~zhmcclient.HTTPError` is raised with status code 404 and reason
        code 1.

        Raises:

          :exc:`~zhmcclient.HTTPError`: The job cancellation attempt failed.
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ClientAuthError`
          :exc:`~zhmcclient.ServerAuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        uri = f'{self.uri}/operations/cancel'
        try:
            self.session.post(uri)
        except Error as exc:
            HMC_LOGGER.debug("Request: POST %s failed with %s: %s",
                             uri, exc.__class__.__name__, exc)
            raise


def _text_repr(text, max_len=1000):
    """
    Return the input text as a Python string representation (i.e. using repr())
    that is limited to a maximum length.
    """
    if text is None:
        text_repr = 'None'
    elif len(text) > max_len:
        text_repr = repr(text[0:max_len]) + '...'
    else:
        text_repr = repr(text)
    return text_repr


def _result_object(result):
    """
    Return the JSON payload in the HTTP response as a Python dict.

    Parameters:

        result (requests.Response): HTTP response object.

    Raises:

        :exc:`~zhmcclient.ParseError`: Error parsing the returned JSON.
    """
    content_type = result.headers.get('content-type', None)

    if content_type is None or content_type.startswith('application/json'):
        # This function is only called when there is content expected.
        # Therefore, a response without content will result in a ParseError.
        try:
            result_obj = result.json()
        except ValueError as exc:
            new_exc = ParseError(
                f"JSON parse error in HTTP response: {exc.args[0]}. "
                f"HTTP request: {result.request.method} {result.request.url}. "
                f"Response status {result.status_code}. "
                f"Response content-type: {content_type!r}. "
                f"Content (max.1000, decoded using {result.encoding}): "
                f"{_text_repr(result.text, 1000)}")
            new_exc.__cause__ = None
            raise new_exc  # zhmcclient.ParseError

        # The property '@@implementation-errors' can be returned to indicate
        # internal inconsistencies not severe enough to return an error.
        if IMPLEMENTATION_ERRORS_PROP in result_obj:
            HMC_LOGGER.warning(
                "Ignored the %r property returned by the HMC for URI %s: %r",
                IMPLEMENTATION_ERRORS_PROP, result.url,
                result_obj[IMPLEMENTATION_ERRORS_PROP])
            del result_obj[IMPLEMENTATION_ERRORS_PROP]

        return result_obj

    if content_type.startswith('text/html'):
        # We are in some error situation. The HMC returns HTML content
        # for some 5xx status codes. We try to deal with it somehow,
        # but we are not going as far as real HTML parsing.
        m = re.search(r'charset=([^;,]+)', content_type)
        if m:
            encoding = m.group(1)  # e.g. RFC "ISO-8859-1"
        else:
            encoding = 'utf-8'
        try:
            html_uni = result.content.decode(encoding)
        except LookupError:
            html_uni = result.content.decode()

        # We convert to one line to be regexp-friendly.
        html_oneline = html_uni.replace('\r\n', '\\n').replace('\r', '\\n').\
            replace('\n', '\\n')

        # Check for some well-known errors:
        if re.search(r'javax\.servlet\.ServletException: '
                     r'Web Services are not enabled\.', html_oneline):
            html_title = "Console Configuration Error"
            html_details = "Web Services API is not enabled on the HMC."
            html_reason = HTML_REASON_WEB_SERVICES_DISABLED
        else:
            m = re.search(
                r'<title>([^<]*)</title>.*'
                r'<h2>Details:</h2>(.*)(<hr size="1" noshade>)?</body>',
                html_oneline)
            if m:
                html_title = m.group(1)
                # Spend a reasonable effort to make the HTML readable:
                html_details = m.group(2).replace('<p>', '\\n').\
                    replace('<br>', '\\n').replace('\\n\\n', '\\n').strip()
            else:
                html_title = "Console Internal Error"
                html_details = f"Response body: {html_uni!r}"
            html_reason = HTML_REASON_OTHER
        message = f"{html_title}: {html_details}"

        # We create a minimal JSON error object (to the extent we use it
        # when processing it):
        result_obj = {
            'http-status': result.status_code,
            'reason': html_reason,
            'message': message,
            'request-uri': result.request.url,
            'request-method': result.request.method,
        }
        return result_obj

    if content_type.startswith('application/vnd.ibm-z-zmanager-metrics'):
        content_bytes = result.content
        assert isinstance(content_bytes, bytes)
        return content_bytes.decode('utf-8')  # as a unicode object

    raise ParseError(
        f"Unknown content type in HTTP response: {content_type}. "
        f"HTTP request: {result.request.method} {result.request.url}. "
        f"Response status {result.status_code}. "
        f"Content (max.1000, decoded using {result.encoding}): "
        f"{_text_repr(result.text, 1000)}")


def json2dict(json_str):
    """
    Convert a JSON string into a dict.

    Parameters:

      json_str (string): Unicode or binary string in JSON format.

    Returns:

      dict: JSON string converted to a dict.

    Raises:

      ValueError: Cannot parse JSON string
    """
    json_dict = json.loads(json_str)  # May raise ValueError
    return json_dict


def dict2json(json_dict):
    """
    Convert a dict into a JSON string.

    Parameters:

      json_dict (dict): The dict.

    Returns:

      unicode string (py3) or byte string (py2): Dict converted to a JSON
      string.
    """
    json_str = json.dumps(json_dict)
    return json_str
