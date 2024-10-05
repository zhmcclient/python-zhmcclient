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
Exceptions that can be raised by the client.
"""

import re


__all__ = ['Error', 'ConnectionError', 'ConnectTimeout', 'ReadTimeout',
           'RetriesExceeded', 'AuthError', 'ClientAuthError',
           'ServerAuthError', 'ParseError', 'VersionError', 'HTTPError',
           'OperationTimeout', 'StatusTimeout', 'NoUniqueMatch', 'NotFound',
           'MetricsResourceNotFound', 'NotificationError',
           'NotificationJMSError', 'NotificationParseError',
           'NotificationConnectionError', 'NotificationSubscriptionError',
           'SubscriptionNotFound', 'ConsistencyError', 'CeasedExistence',
           'OSConsoleError', 'OSConsoleConnectedError',
           'OSConsoleNotConnectedError', 'OSConsoleWebSocketError',
           'OSConsoleAuthError', 'PartitionLinkError']


class Error(Exception):
    """
    Abstract base class for exceptions specific to this package.

    Exceptions of this class are not raised; only derived exceptions are
    raised.

    Derived from :exc:`~py:exceptions.Exception`.
    """

    def str_def(self):
        """
        Interface definition for the corresponding method derived exception
        classes.

        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts.

        For the exact format returned by derived exception classes, see the
        same-named methods there.
        """
        raise NotImplementedError


class ConnectionError(Error):
    # pylint: disable=redefined-builtin
    """
    This exception indicates a problem with the connection to the HMC, below
    the HTTP level. HTTP errors are indicated via :exc:`~zhmcclient.HTTPError`.

    A retry by the user code is not likely to be successful, unless connect or
    read retries had been disabled when creating the session (see
    :class:`~zhmcclient.Session`).

    Even though this class has exceptions derived from it, exceptions of this
    class may also be raised (if no other derived class matches the
    circumstances).

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, msg, details):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          details (Exception):
            The original exception describing details about the error.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)
        self._details = details

    @property
    def details(self):
        """
        The original exception caught by this package, providing more
        information about the problem.

        This will be one of the following exceptions:

        * Any exception derived from
          :exc:`requests.exceptions.RequestException`.
        """
        return self._details

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return f"{self.__class__.__name__}(message={self.args[0]!r})"

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={};
        """
        return \
            f"classname={self.__class__.__name__!r}; message={self.args[0]!r};"


class ConnectTimeout(ConnectionError):
    """
    This exception indicates that a connection to the HMC timed out after
    exhausting the connect retries (see
    :attr:`zhmcclient.RetryTimeoutConfig.connect_retries`).

    Further retrying by the user code is not likely to be successful, unless
    connect retries had been disabled when creating the session (see
    :class:`~zhmcclient.Session`).

    Derived from :exc:`~zhmcclient.ConnectionError`.
    """

    def __init__(self, msg, details, connect_timeout, connect_retries):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          details (Exception):
            The original exception describing details about the error.

          connect_timeout (:term:`integer`):
            The connect timeout in seconds.

          connect_retries (:term:`integer`):
            The number of connect retries.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg, details)
        self._connect_timeout = connect_timeout
        self._connect_retries = connect_retries

    @property
    def connect_timeout(self):
        """
        :term:`integer`: The connect timeout in seconds.
        """
        return self._connect_timeout

    @property
    def connect_retries(self):
        """
        :term:`integer`: The number of connect retries.
        """
        return self._connect_retries

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"connect_timeout={self.connect_timeout!r}, "
            f"connect_retries={self.connect_retries!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; connect_timeout={}; connect_retries={}; message={};
        """  # noqa: E501
        return (
            f"classname={self.__class__.__name__!r}; "
            f"connect_timeout={self.connect_timeout!r}; "
            f"connect_retries={self.connect_retries!r}; "
            f"message={self.args[0]!r};")


class ReadTimeout(ConnectionError):
    """
    This exception indicates that reading an HTTP response from the HMC timed
    out after exhausting the read retries (see
    :attr:`zhmcclient.RetryTimeoutConfig.read_retries`).

    Further retrying by the user code is not likely to be successful, unless
    read retries had been disabled when creating the session (see
    :class:`~zhmcclient.Session`).

    Derived from :exc:`~zhmcclient.ConnectionError`.
    """

    def __init__(self, msg, details, read_timeout, read_retries):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          details (Exception):
            The original exception describing details about the error.

          read_timeout (:term:`integer`):
            The read timeout in seconds.

          read_retries (:term:`integer`):
            The number of read retries.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg, details)
        self._read_timeout = read_timeout
        self._read_retries = read_retries

    @property
    def read_timeout(self):
        """
        :term:`integer`: The read timeout in seconds.
        """
        return self._read_timeout

    @property
    def read_retries(self):
        """
        :term:`integer`: The number of read retries.
        """
        return self._read_retries

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"read_timeout={self.read_timeout!r}, "
            f"read_retries={self.read_retries!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; read_timeout={}; read_retries={}; message={};
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"read_timeout={self.read_timeout!r}; "
            f"read_retries={self.read_retries!r}; "
            f"message={self.args[0]!r};")


class RetriesExceeded(ConnectionError):
    """
    This exception indicates that the maximum number of retries for connecting
    to the HMC, sending HTTP requests or reading HTTP responses was exceeded,
    for reasons other than connect timeouts (see
    :exc:`~zhmcclient.ConnectTimeout`) or read timeouts (see
    :exc:`~zhmcclient.ReadTimeout`).

    Further retrying by the user code is not likely to be successful, unless
    connect or read retries had been disabled when creating the session (see
    :class:`~zhmcclient.Session`).

    Derived from :exc:`~zhmcclient.ConnectionError`.
    """

    def __init__(self, msg, details, connect_retries):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          details (Exception):
            The original exception describing details about the error.

          connect_retries (:term:`integer`):
            The number of connect retries.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg, details)
        self._connect_retries = connect_retries

    @property
    def connect_retries(self):
        """
        :term:`integer`: The number of connect retries.
        """
        return self._connect_retries

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"connect_retries={self.connect_retries!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; connect_retries={}; message={};
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"connect_retries={self.connect_retries!r}; "
            f"message={self.args[0]!r};")


class AuthError(Error):
    # pylint: disable=abstract-method
    """
    This exception indicates erors related to authentication.

    Exceptions of this class are not raised; only derived exceptions are
    raised.

    Derived from :exc:`~zhmcclient.Error`.
    """
    pass


class ClientAuthError(AuthError):
    """
    This exception indicates an authentication related problem detected on
    the client side.

    Derived from :exc:`~zhmcclient.AuthError`.
    """

    def __init__(self, msg):
        # pylint: disable=useless-super-delegation
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return f"{self.__class__.__name__}(message={self.args[0]!r})"

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={};
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r};")


class ServerAuthError(AuthError):
    """
    This exception indicates an authentication error with the HMC.

    Derived from :exc:`~zhmcclient.AuthError`.
    """

    def __init__(self, msg, details):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          details (Exception):
            The :exc:`~zhmcclient.HTTPError` exception describing the
            error returned by the HMC.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)
        assert isinstance(details, HTTPError)
        self._details = details

    @property
    def details(self):
        """
        The original exception describing details about the error.

        This may be one of the following exceptions:

        * :exc:`~zhmcclient.HTTPError`
        """
        return self._details

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"details.request_method={self.details.request_method!r}, "
            f"details.request_uri={self.details.request_uri!r}, "
            f"details.http_status={self.details.http_status!r}, "
            f"details.reason={self.details.reason!r})")

    def str_def(self):
        # pylint: disable=line-too-long
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; request_method={}; request_uri={}; http_status={}; reason={}; message={};
        """  # noqa: E501
        # pylint: enable=line-too-long
        return (
            f"classname={self.__class__.__name__!r}; "
            f"request_method={self.details.request_method!r}; "
            f"request_uri={self.details.request_uri!r}; "
            f"http_status={self.details.http_status!r}; "
            f"reason={self.details.reason!r}; message={self.args[0]!r};")


class ParseError(Error):
    """
    This exception indicates a parsing error while processing the JSON payload
    in a response from the HMC.

    Derived from :exc:`~zhmcclient.Error`.

    The error location within the payload is automatically determined by
    parsing the error message for the pattern:

    .. code-block:: text

        : line {line} column {column}
    """

    def __init__(self, msg):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

            This should be the message of the `ValueError` exception raised
            by methods of the :class:`py:json.JSONDecoder` class.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)
        self._line = None
        self._column = None
        if msg:
            m = re.search(r': line ([0-9]+) column ([0-9]+) ', msg)
            if m:
                self._line = int(m.group(1))
                self._column = int(m.group(2))

    @property
    def line(self):
        """
        :term:`integer`: The 1-based line number of the error location within
        the JSON payload.

        `None` indicates that the error location is not available.
        """
        return self._line

    @property
    def column(self):
        """
        :term:`integer`: The 1-based column number of the error location within
        the JSON payload.

        `None` indicates that the error location is not available.
        """
        return self._column

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"line={self.line!r}, column={self.column!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; line={}; column={}; message={};
        """
        return (
            f"classname={self.__class__.__name__!r}; line={self.line!r}; "
            f"column={self.column!r}; message={self.args[0]!r};")


class VersionError(Error):
    """
    This exception indicates that a function of the client requires a minimum
    HMC API version which is not supported by the HMC.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, msg, min_api_version, api_version):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          min_api_version (:term:`HMC API version`):
            The minimum HMC API version required to perform the function that
            raised this exception.

          api_version (:term:`HMC API version`):
            The actual HMC API version supported by the HMC.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)
        self._min_api_version = min_api_version
        self._api_version = api_version

    @property
    def min_api_version(self):
        """
        :term:`HMC API version`: The minimum HMC API version required to
        perform the function that raised this exception.
        """
        return self._min_api_version

    @property
    def api_version(self):
        """
        :term:`HMC API version`: The actual HMC API version supported by the
        HMC.
        """
        return self._api_version

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"min_api_version={self.min_api_version!r}, "
            f"api_version={self.api_version!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; min_api_version={}; api_version={}; message={};
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"min_api_version={self.min_api_version!r}; "
            f"api_version={self.api_version!r}; "
            f"message={self.args[0]!r};")


class HTTPError(Error):
    """
    This exception indicates that the HMC returned an HTTP response with a bad
    HTTP status code.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, body):
        """
        Parameters:

          body (:term:`json object`):
            Body of the HTTP error response.

        ``args[0]`` will be set to the 'message' item of the body, or to `None`
        if not present.
        """
        msg = body.get('message', None)
        super().__init__(msg)
        self._body = body

    @property
    def http_status(self):
        """
        :term:`integer`: Numeric HTTP status code (e.g. 500).

        See :term:`RFC2616` for a list of HTTP status codes and reason phrases.
        """
        return self._body.get('http-status', None)

    @property
    def reason(self):
        """
        :term:`integer`: Numeric HMC reason code.

        HMC reason codes provide more details as to the nature of the error
        than is provided by the HTTP status code. This HMC reason code is
        treated as a sub-code of the HTTP status code and thus must be used in
        conjunction with the HTTP status code to determine the error condition.

        Standard HMC reason codes that apply across the entire API are
        described in section 'Common request validation reason codes' in the
        :term:`HMC API` book. Additional operation-specific reason codes may
        also be documented in the description of specific API operations in the
        :term:`HMC API` book.

        The articial reason code 999 is used when the response from the HMC
        contains an HTML-formatted error message.
        """
        return self._body.get('reason', None)

    @property
    def message(self):
        """
        :term:`string`: Message describing the error.

        This message is not currently localized.
        """
        return self._body.get('message', None)

    @property
    def request_method(self):
        """
        :term:`string`: The HTTP method (DELETE, GET, POST, PUT) that caused
        this error response.
        """
        return self._body.get('request-method', None)

    @property
    def request_uri(self):
        """
        :term:`string`: The URI that caused this error response.
        """
        return self._body.get('request-uri', None)

    @property
    def request_query_parms(self):
        """
        List of query-parm-info objects: URI query parameters specified on the
        request.

        Each query-parm-info object identifies a single query parameter by its
        name and includes its value(s).

        An empty list, if the request did not specify any query parameters.
        """
        return self._body.get('request-query-parms', None)

    @property
    def request_headers(self):
        """
        header-info object: HTTP headers specified on the request.

        An empty list, if the request did not specify any HTTP headers.
        """
        return self._body.get('request-headers', None)

    @property
    def request_authenticated_as(self):
        """
        :term:`string`: Name of the HMC user associated with the API session
        under which the request was issued.

        `None`, if the request was issued without an established session or
        there is no HMC user bound to the session.
        """
        return self._body.get('request-authenticated-as', None)

    @property
    def request_body(self):
        """
        The request body, in the form of a JSON document. Note that, since it
        is in the form of a JSON document, this may not be exactly what was
        submitted by the API client program, but it is semantically equivalent.

        If the request body could not be parsed or some other error prevented
        the creation of a JSON document from the request body, this property
        is `None` and the request body is instead available in the
        :attr:`~zhmcclient.HTTPError.request_body_as_string` property.
        """
        return self._body.get('request-body', None)

    @property
    def request_body_as_string(self):
        """
        :term:`string`: The complete request body, or some portion of the
        request body, exactly as it was submitted by the API client program, if
        the :attr:`~zhmcclient.HTTPError.request_body` property is `None`.
        Otherwise, `None`.

        The :attr:`~zhmcclient.HTTPError.request_body_as_string_partial`
        property indicates whether the complete request body is provided in
        this property.
        """
        return self._body.get('request-body-as-string', None)

    @property
    def request_body_as_string_partial(self):
        """
        :class:`py:bool`: Indicates whether the
        :attr:`~zhmcclient.HTTPError.request_body_as_string` property contains
        only part of the request body (`True`) or the entire request body
        (`False`). `None`, if the
        :attr:`~zhmcclient.HTTPError.request_body_as_string` property is
        `None`.
        """
        return self._body.get('request-body-as-string-partial', None)

    @property
    def stack(self):
        """
        :term:`string`: Internal HMC diagnostic information for the error.

        This field is supplied only on selected 5xx HTTP status codes.
        `None`, if not supplied.
        """
        return self._body.get('stack', None)

    @property
    def error_details(self):
        """
        :term:`string`: A nested object that provides additional
        operation-specific error information. This field is provided by
        selected operations, and the format of the nested object is as
        described by that operation.
        """
        return self._body.get('error-details', None)

    def __str__(self):
        """
        Return a human readable string representation of this exception object.
        """
        stack_txt = f' stack={self.stack!r}' if self.stack else ''
        return (
            f"{self.http_status},{self.reason}: {self.message} "
            f"[{self.request_method} {self.request_uri}]{stack_txt}")

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(http_status={self.http_status!r}, "
            f"reason={self.reason!r}, message={self.message!r}, "
            f"request_method={self.request_method!r}, "
            f"request_uri={self.request_uri!r}, stack={self.stack!r}, ...)")

    def str_def(self):
        # pylint: disable=line-too-long
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; request_method={}; request_uri={}; http_status={}; reason={}; message={};
        """  # noqa: E501
        # pylint: enable=line-too-long
        return (
            f"classname={self.__class__.__name__!r}; "
            f"request_method={self.request_method!r}; "
            f"request_uri={self.request_uri!r}; "
            f"http_status={self.http_status!r}; "
            f"reason={self.reason!r}; message={self.args[0]!r};")


class OperationTimeout(Error):
    """
    This exception indicates that the waiting for completion of an asynchronous
    HMC operation has timed out.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, msg, operation_timeout):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          operation_timeout (:term:`integer`):
            The operation timeout in seconds.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)
        self._operation_timeout = operation_timeout

    @property
    def operation_timeout(self):
        """
        :term:`integer`: The operation timeout in seconds.
        """
        return self._operation_timeout

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"operation_timeout={self.operation_timeout!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; operation_timeout={}; message={};
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"operation_timeout={self.operation_timeout!r}; "
            f"message={self.args[0]!r};")


class StatusTimeout(Error):
    """
    This exception indicates that the waiting for reaching a desired LPAR
    or Partition status has timed out.

    The possible status values for an LPAR are:

    * ``"not-activated"`` - The LPAR is not active.
    * ``"not-operating"`` - The LPAR is active but no operating system is
      running in the LPAR.
    * ``"operating"`` - The LPAR is active and an operating system is
      running in the LPAR.
    * ``"exceptions"`` - The LPAR or its CPC has one or more unusual
      conditions.

    The possible status values for a Partition are described in the
    'status' property of the data model for the partition resource in the
    :term:`HMC API` book.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, msg, actual_status, desired_statuses, status_timeout):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          actual_status (:term:`string`):
            The actual status (at the point in time when the status timeout
            expired).

          desired_statuses (iterable of :term:`string`):
            The desired status values that were supposed to be reached.

          status_timeout (:term:`number`):
            The status timeout (in seconds) that has expired.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)
        self._actual_status = actual_status
        self._desired_statuses = desired_statuses
        self._status_timeout = status_timeout

    @property
    def actual_status(self):
        """
        :term:`string`: The actual status (at the point in time when the
        status timeout expired).
        """
        return self._actual_status

    @property
    def desired_statuses(self):
        """
        iterable of :term:`string`: The desired status values that were
        supposed to be reached.
        """
        return self._desired_statuses

    @property
    def status_timeout(self):
        """
        :term:`number`: The status timeout (in seconds) that has expired.
        """
        return self._status_timeout

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"actual_status={self.actual_status!r}, "
            f"desired_statuses={self.desired_statuses!r}, "
            f"status_timeout={self.status_timeout!r})")

    def str_def(self):
        # pylint: disable=line-too-long
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; actual_status={}; desired_statuses={}; status_timeout={}; message={};
        """  # noqa: E501
        # pylint: enable=line-too-long
        return (
            f"classname={self.__class__.__name__!r}; "
            f"actual_status={self.actual_status!r}; "
            f"desired_statuses={self.desired_statuses!r}; "
            f"status_timeout={self.status_timeout!r}; "
            f"message={self.args[0]!r};")


class NoUniqueMatch(Error):
    """
    This exception indicates that more than one resource matched the filter
    arguments.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, filter_args, manager, resources):
        """
        Parameters:

          filter_args (dict):
            Dictionary of filter arguments by which the resource was attempted
            to be found. Keys are the resource property names, values are
            the match values for that property.

          manager (:class:`~zhmcclient.BaseManager`):
            The manager of the resource, in whose scope the resource was
            attempted to be found.

            Must not be `None`.

          resources (:term:`iterable` of :class:`~zhmcclient.BaseResource`):
            The resources that did match the filter.

            Must not be `None`.

        ``args[0]`` will be set to an exception message that is automatically
        constructed from the input parameters.
        """
        parent = manager.parent
        if parent:
            in_str = f" in {parent.__class__.__name__} {parent.name!r}"
        else:
            in_str = ""
        resource_uris = [r.uri for r in resources]
        msg = (
            f"Found more than one {manager.resource_class.__name__} using "
            f"filter arguments {filter_args!r}{in_str}, with "
            f"URIs: {resource_uris!r}")
        super().__init__(msg)
        self._filter_args = filter_args
        self._manager = manager
        self._resources = list(resources)
        self._resource_uris = resource_uris

    @property
    def filter_args(self):
        """
        dict: Dictionary of filter arguments by which the resource was
        attempted to be found. Keys are the resource property names, values
        are the match values for that property.
        """
        return self._filter_args

    @property
    def manager(self):
        """
        :class:`~zhmcclient.BaseManager`: The manager of the resource, in whose
        scope the resource was attempted to be found.
        """
        return self._manager

    @property
    def resources(self):
        """
        List of :class:`~zhmcclient.BaseResource`: The resources that matched
        the filter.
        """
        return self._resources

    @property
    def resource_uris(self):
        """
        List of URIs of the resources that matched the filter.
        """
        return self._resource_uris

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        parent = self.manager.parent
        parent_classname = parent.__class__.__name__ if parent else None
        parent_name = parent.name if parent else None
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"resource_classname={self.manager.resource_class.__name__!r}, "
            f"filter_args={self.filter_args!r}, "
            f"parent_classname={parent_classname!r}, "
            f"parent_name={parent_name!r}, "
            f"resource_uris={self.resource_uris!r})")

    def str_def(self):
        # pylint: disable=line-too-long
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; resource_classname={}; filter_args={}; parent_classname={}; manager_name={}; message={}; resource_uris={}
        """  # noqa: E501
        # pylint: enable=line-too-long
        parent = self.manager.parent
        parent_classname = parent.__class__.__name__ if parent else None
        parent_name = parent.name if parent else None
        return (
            f"classname={self.__class__.__name__!r}; "
            f"resource_classname={self.manager.resource_class.__name__!r}; "
            f"filter_args={self.filter_args!r}; "
            f"parent_classname={parent_classname!r}; "
            f"parent_name={parent_name!r}; message={self.args[0]!r}; "
            f"resource_uris={self.resource_uris!r}")


class NotFound(Error):
    """
    This exception indicates that a resource was not found.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, filter_args=None, manager=None, message=None):
        """
        Parameters:

          filter_args (dict):
            Dictionary of filter arguments by which the resource was attempted
            to be found. Keys are the resource property names, values are
            the match values for that property.

            May be `None` if the `message` parameter is `None`.
            Will be ignored if the `message` parameter is not `None`.

          manager (:class:`~zhmcclient.BaseManager`):
            The manager of the resource, in whose scope the resource was
            attempted to be found.

            Must not be `None` if the `message` parameter is `None`.
            Will be ignored if the `message` parameter is not `None`.

          message (string):
            The exception message.

            If `None`, the message will be automatically created from the
            `filter_args` and `manager` parameters.

        ``args[0]`` will be set to an exception message that is automatically
        constructed from the input parameters.
        """
        if message is not None:
            msg = message
            filter_args = None
            manager = None
        else:
            assert manager is not None
            parent = manager.parent
            if parent:
                in_str = f" in {parent.__class__.__name__} {parent.name!r}"
            else:
                in_str = ""
            if filter_args and len(filter_args) == 1 and \
                    manager._name_prop in filter_args:
                msg = (
                    f"Could not find {manager.resource_class.__name__} "
                    f"{filter_args[manager._name_prop]!r}{in_str}.")
            else:
                msg = (
                    f"Could not find {manager.resource_class.__name__} "
                    f"using filter arguments {filter_args!r}{in_str}.")
        super().__init__(msg)
        self._filter_args = filter_args
        self._manager = manager

    @property
    def filter_args(self):
        """
        dict: Dictionary of filter arguments by which the resource was
        attempted to be found. Keys are the resource property names, values
        are the match values for that property.

        Will be `None` if the `message` init parameter was not `None`.
        """
        return self._filter_args

    @property
    def manager(self):
        """
        :class:`~zhmcclient.BaseManager`: The manager of the resource, in whose
        scope the resource was attempted to be found.

        Will be `None` if the `message` init parameter was not `None`.
        """
        return self._manager

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        resource_classname = self.manager.resource_class.__name__ \
            if self.manager else None
        parent = self.manager.parent if self.manager else None
        parent_classname = parent.__class__.__name__ if parent else None
        parent_name = parent.name if parent else None
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"resource_classname={resource_classname!r}, "
            f"filter_args={self.filter_args!r}, "
            f"parent_classname={parent_classname!r}, "
            f"parent_name={parent_name!r})")

    def str_def(self):
        # pylint: disable=line-too-long
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; resource_classname={}; filter_args={}; parent_classname={}; parent_name={}; message={};
        """  # noqa: E501
        # pylint: enable=line-too-long
        resource_classname = self.manager.resource_class.__name__ \
            if self.manager else None
        parent = self.manager.parent if self.manager else None
        parent_classname = parent.__class__.__name__ if parent else None
        parent_name = parent.name if parent else None
        return (
            f"classname={self.__class__.__name__!r}; "
            f"resource_classname={resource_classname!r}; "
            f"filter_args={self.filter_args!r}; "
            f"parent_classname={parent_classname!r}; "
            f"parent_name={parent_name!r}; message={self.args[0]!r};")


class MetricsResourceNotFound(Error):
    # pylint: disable=redefined-builtin
    """
    This exception indicates that the resource referenced by a metric object
    value was not found on the HMC.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, msg, resource_class, managers):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          resource_class (:class:`~zhmcclient.BaseResource`):
            The zhmcclient resource class of the resource that was not found.

          managers (list of :class:`~zhmcclient.BaseManager`):
            List of zhmcclient resource managers that were searched for the
            resource.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)
        self._resource_class = resource_class
        self._managers = managers

    @property
    def resource_class(self):
        """
        The zhmcclient resource class of the resource that was not found.
        """
        return self._resource_class

    @property
    def managers(self):
        """
        List of zhmcclient resource managers that were searched for the
        resource
        """
        return self._managers

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return f"{self.__class__.__name__}(message={self.args[0]!r})"

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={}
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r}")


class NotificationError(Error):
    """
    Abstract base class for exceptions raised by
    :class:`~zhmcclient.NotificationListener`.

    Exceptions of this class are not raised; only derived exceptions are
    raised.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def str_def(self):
        """
        Interface definition for the corresponding method derived exception
        classes.

        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts.

        For the exact format returned by derived exception classes, see the
        same-named methods there.
        """
        raise NotImplementedError


class NotificationJMSError(NotificationError):
    """
    This exception indicates that a JMS error was returned by the HMC in
    the notification protocol.

    Derived from :exc:`~zhmcclient.NotificationError`.
    """

    def __init__(self, msg, jms_headers, jms_message):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

            This is either the 'message' item from the JMS headers if present,
            or a generic message.

          jms_headers (dict):
            The JMS headers returned by the HMC.

          jms_message (:term:`string`):
            The JMS message body returned by the HMC.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)
        self._jms_headers = jms_headers
        self._jms_message = jms_message

    @property
    def jms_headers(self):
        """
        dict: The JMS headers returned by the HMC.
        """
        return self._jms_headers

    @property
    def jms_message(self):
        """
        :term:`string`: The JMS message body returned by the HMC.
        """
        return self._jms_message

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"jms_headers={self.jms_headers!r}, "
            f"jms_message={self.jms_message!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={}
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r};")


class NotificationParseError(NotificationError):
    """
    This exception indicates that the message body of a JMS message could not
    be parsed as JSON format.

    Derived from :exc:`~zhmcclient.NotificationError`.
    """

    def __init__(self, msg, jms_message):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          jms_message (:term:`string`):
            The JMS message body returned by the HMC.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)
        self._jms_message = jms_message

    @property
    def jms_message(self):
        """
        :term:`string`: The JMS message body returned by the HMC.
        """
        return self._jms_message

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"jms_message={self.jms_message!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={}
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r};")


class NotificationConnectionError(NotificationError):
    """
    This exception indicates an issue with the STOMP connection to the HMC.

    Derived from :exc:`~zhmcclient.NotificationError`.
    """

    def __init__(self, msg):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        # pylint: disable=useless-super-delegation
        super().__init__(msg)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={}
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r};")


class NotificationSubscriptionError(NotificationError):
    """
    This exception indicates an issue with the STOMP subscription or
    unsubscription to the HMC.

    Derived from :exc:`~zhmcclient.NotificationError`.
    """

    def __init__(self, msg):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        # pylint: disable=useless-super-delegation
        super().__init__(msg)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={}
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r};")


class SubscriptionNotFound(NotificationError):
    """
    This exception indicates that a subscripton for a topic was not found.

    Derived from :exc:`~zhmcclient.NotificationError`.
    """

    def __init__(self, msg):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        # pylint: disable=useless-super-delegation
        super().__init__(msg)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={}
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r};")


class ConsistencyError(Error):
    # pylint: disable=abstract-method
    """
    This exception indicates that an inconsistency has been detected.

    Please report such exceptions in the zhmcclient issue tracker
    at https://github.com/zhmcclient/python-zhmcclient/issues.

    Derived from :exc:`~zhmcclient.Error`.
    """
    pass


class CeasedExistence(Error):
    # pylint: disable=abstract-method
    """
    This exception indicates that the corresponding HMC resource for an
    auto-updated zhmcclient resource no longer exists.

    This exception will only be raised for zhmcclient resources that are
    enabled for :ref:`auto-updating`.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, resource_uri):
        """
        Parameters:

          resource_uri (:term:`string`):
            URI of the resource that no longer exists.

        ``args[0]`` will be set to a default message.
        """
        msg = f"Resource no longer exists: {resource_uri}"
        super().__init__(msg)
        self._resource_uri = resource_uri

    @property
    def resource_uri(self):
        """
        :term:`string`: The URI of the resource that no longer exists.
        """
        return self._resource_uri

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}(message={self.args[0]!r}, "
            f"resource_uri={self.resource_uri!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={}; resource_uri={}
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r}; "
            f"resource_uri={self.resource_uri!r}")


class OSConsoleError(Error):
    """
    This exception indicates errors related to OS consoles.

    Exceptions of this class are not raised; only derived exceptions are
    raised.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, msg):
        # pylint: disable=useless-super-delegation
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super().__init__(msg)

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return f"{self.__class__.__name__}(message={self.args[0]!r})"

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={};
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r};")


class OSConsoleConnectedError(OSConsoleError):
    """
    This exception indicates that the WebSocket is connected when it should not
    be connected.
    """
    pass


class OSConsoleNotConnectedError(OSConsoleError):
    """
    This exception indicates that the WebSocket is not connected when it should
    be connected.
    """
    pass


class OSConsoleWebSocketError(OSConsoleError):
    """
    This exception indicates a problem with a WebSocket operation.
    """
    pass


class OSConsoleAuthError(OSConsoleError):
    """
    This exception indicates an authentication issue when logging in to the OS
    console.
    """
    pass


class PartitionLinkError(Error):
    # pylint: disable=redefined-builtin
    """
    This exception indicates that an operation on a partition link has completed
    its asynchronous operation with failed operation results or with pending
    retries during SE restart.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, operation_results):
        """
        Parameters:

          operation_results (list of dict):
            The 'operation-results' field of the job completion result.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        op_msg_list = []
        for op_result in operation_results:
            uri = op_result['partition-uri']
            status = op_result['operation-status']
            op_msg_list.append(f"operation status {status} for partition {uri}")
        op_msg = ", ".join(op_msg_list)
        msg = f"Partition link operation failed with: {op_msg}"
        super().__init__(msg)
        self._operation_results = operation_results

    @property
    def operation_results(self):
        """
        list of dict: The value of the 'operation-results' field of the job
        completion result.
        """
        return self._operation_results

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return (
            f"{self.__class__.__name__}("
            f"message={self.args[0]!r}, "
            f"operation_results={self._operation_results!r})")

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={}; operation_results={}
        """
        return (
            f"classname={self.__class__.__name__!r}; "
            f"message={self.args[0]!r}; "
            f"operation_results={self._operation_results!r}")
