# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
           'OperationTimeout', 'StatusTimeout', 'NoUniqueMatch', 'NotFound']


class Error(Exception):
    """
    Abstract base class for exceptions specific to this package.

    Exceptions of this class are not raised; only derived exceptions are
    raised.

    Derived from :exc:`~py:exceptions.Exception`.
    """

    def __init__(self, *args):
        # Parameters:
        #   *args:
        #     A list of input arguments for the exception object.
        #     The derived classes define more specific parameters.
        #     These input arguments will be available as tuple items in the
        #     ``args`` instance variable of the exception object.
        super(Error, self).__init__(*args)

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
        super(ConnectionError, self).__init__(msg)
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
        return "{}(message={!r})". \
               format(self.__class__.__name__, self.args[0])

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={};
        """
        return "classname={!r}; message={!r};". \
            format(self.__class__.__name__, self.args[0])


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
        super(ConnectTimeout, self).__init__(msg, details)
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
        return "{}(message={!r}, connect_timeout={!r}, " \
               "connect_retries={!r})". \
               format(self.__class__.__name__, self.args[0],
                      self.connect_timeout, self.connect_retries)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; connect_timeout={}; connect_retries={}; message={};
        """  # noqa: E501
        return "classname={!r}; connect_timeout={!r}; connect_retries={!r}; " \
            "message={!r};". \
            format(self.__class__.__name__, self.connect_timeout,
                   self.connect_retries, self.args[0])


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
        super(ReadTimeout, self).__init__(msg, details)
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
        return "{}(message={!r}, read_timeout={!r}, read_retries={!r})". \
               format(self.__class__.__name__, self.args[0],
                      self.read_timeout, self.read_retries)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; read_timeout={}; read_retries={}; message={};
        """
        return "classname={!r}; read_timeout={!r}; read_retries={!r}; " \
            "message={!r};". \
            format(self.__class__.__name__, self.read_timeout,
                   self.read_retries, self.args[0])


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
        super(RetriesExceeded, self).__init__(msg, details)
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
        return "{}(message={!r}, connect_retries={!r})". \
               format(self.__class__.__name__, self.args[0],
                      self.connect_retries)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; connect_retries={}; message={};
        """
        return "classname={!r}; connect_retries={!r}; message={!r};". \
            format(self.__class__.__name__, self.connect_retries, self.args[0])


class AuthError(Error):
    """
    This exception indicates erors related to authentication.

    Exceptions of this class are not raised; only derived exceptions are
    raised.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, *args):
        # Parameters:
        #   *args:
        #     A list of input arguments for the exception object.
        #     The derived classes define more specific parameters.
        #     These input arguments will be available as tuple items in the
        #     ``args`` instance variable of the exception object.
        super(AuthError, self).__init__(*args)


class ClientAuthError(AuthError):
    """
    This exception indicates an authentication related problem detected on
    the client side.

    Derived from :exc:`~zhmcclient.AuthError`.
    """

    def __init__(self, msg):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

        ``args[0]`` will be set to the ``msg`` parameter.
        """
        super(ClientAuthError, self).__init__(msg)

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return "{}(message={!r})". \
               format(self.__class__.__name__, self.args[0])

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; message={};
        """
        return "classname={!r}; message={!r};". \
            format(self.__class__.__name__, self.args[0])


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
        super(ServerAuthError, self).__init__(msg)
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
        return "{}(message={!r}, details.request_method={!r}, " \
            "details.request_uri={!r}, details.http_status={!r}, " \
            "details.reason={!r})". \
               format(self.__class__.__name__, self.args[0],
                      self.details.request_method, self.details.request_uri,
                      self.details.http_status, self.details.reason)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; request_method={}; request_uri={}; http_status={}; reason={}; message={};
        """  # noqa: E501
        return "classname={!r}; request_method={!r}; request_uri={!r}; " \
            "http_status={!r}; reason={!r}; message={!r};". \
            format(self.__class__.__name__, self.details.request_method,
                   self.details.request_uri, self.details.http_status,
                   self.details.reason, self.args[0])


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
        super(ParseError, self).__init__(msg)
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
        return "{}(message={!r}, line={!r}, column={!r})". \
               format(self.__class__.__name__, self.args[0], self.line,
                      self.column)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; line={}; column={}; message={};
        """
        return "classname={!r}; line={!r}; column={!r}; message={!r};". \
            format(self.__class__.__name__, self.line, self.column,
                   self.args[0])


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
        super(VersionError, self).__init__(msg)
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
        return "{}(message={!r}, min_api_version={!r}, api_version={!r})". \
               format(self.__class__.__name__, self.args[0],
                      self.min_api_version, self.api_version)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; min_api_version={}; api_version={}; message={};
        """
        return "classname={!r}; min_api_version={!r}; api_version={!r}; " \
            "message={!r};". \
            format(self.__class__.__name__, self.min_api_version,
                   self.api_version, self.args[0])


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
        super(HTTPError, self).__init__(msg)
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
        return "{},{}: {} [{} {}]".\
               format(self.http_status, self.reason, self.message,
                      self.request_method, self.request_uri)

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        return "{}(http_status={!r}, reason={!r}, message={!r}, " \
               "request_method={!r}, request_uri={!r}, ...)". \
               format(self.__class__.__name__, self.http_status, self.reason,
                      self.message, self.request_method, self.request_uri)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; request_method={}; request_uri={}; http_status={}; reason={}; message={};
        """  # noqa: E501
        return "classname={!r}; request_method={!r}; request_uri={!r}; " \
            "http_status={!r}; reason={!r}; message={!r};". \
            format(self.__class__.__name__, self.request_method,
                   self.request_uri, self.http_status, self.reason,
                   self.args[0])


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
        super(OperationTimeout, self).__init__(msg)
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
        return "{}(message={!r}, operation_timeout={!r})". \
               format(self.__class__.__name__, self.args[0],
                      self.operation_timeout)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; operation_timeout={}; message={};
        """
        return "classname={!r}; operation_timeout={!r}; message={!r};". \
            format(self.__class__.__name__, self.operation_timeout,
                   self.args[0])


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
        super(StatusTimeout, self).__init__(msg)
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
        return "{}(message={!r}, actual_status={!r}, desired_statuses={!r}, " \
            "status_timeout={!r})". \
            format(self.__class__.__name__, self.args[0], self.actual_status,
                   self.desired_statuses, self.status_timeout)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; actual_status={}; desired_statuses={}; status_timeout={}; message={};
        """  # noqa: E501
        return "classname={!r}; actual_status={!r}; desired_statuses={!r}; " \
            "status_timeout={!r}; message={!r};". \
            format(self.__class__.__name__, self.actual_status,
                   self.desired_statuses, self.status_timeout, self.args[0])


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
            in_str = " in {} {!r}". \
                format(parent.__class__.__name__, parent.name)
        else:
            in_str = ""
        resource_uris = [r.uri for r in resources]
        msg = "Found more than one {} using filter arguments {!r}{}, with " \
            "URIs: {!r}". \
            format(manager.resource_class.__name__, filter_args, in_str,
                   resource_uris)
        super(NoUniqueMatch, self).__init__(msg)
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
        return "{}(message={!r}, resource_classname={!r}, filter_args={!r}, " \
               "parent_classname={!r}, parent_name={!r}, " \
               "resource_uris={!r})". \
               format(self.__class__.__name__, self.args[0],
                      self.manager.resource_class.__name__,
                      self.filter_args,
                      parent.__class__.__name__ if parent else None,
                      parent.name if parent else None,
                      self.resource_uris)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; resource_classname={}; filter_args={}; parent_classname={}; manager_name={}; message={}; resource_uris={}
        """  # noqa: E501
        parent = self.manager.parent
        return "classname={!r}; resource_classname={!r}; filter_args={!r}; " \
               "parent_classname={!r}; parent_name={!r}; message={!r}; " \
               "resource_uris={!r}". \
               format(self.__class__.__name__,
                      self.manager.resource_class.__name__,
                      self.filter_args,
                      parent.__class__.__name__ if parent else None,
                      parent.name if parent else None,
                      self.args[0],
                      self.resource_uris)


class NotFound(Error):
    """
    This exception indicates that a resource was not found.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, filter_args, manager):
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

        ``args[0]`` will be set to an exception message that is automatically
        constructed from the input parameters.
        """
        parent = manager.parent
        if parent:
            in_str = " in {} {!r}". \
                format(parent.__class__.__name__, parent.name)
        else:
            in_str = ""
        if filter_args and len(filter_args) == 1 and \
                manager._name_prop in filter_args:
            msg = "Could not find {} {!r}{}.". \
                format(manager.resource_class.__name__,
                       filter_args[manager._name_prop], in_str)
        else:
            msg = "Could not find {} using filter arguments {!r}{}.".\
                format(manager.resource_class.__name__, filter_args, in_str)
        super(NotFound, self).__init__(msg)
        self._filter_args = filter_args
        self._manager = manager

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

    def __repr__(self):
        """
        Return a string with the state of this exception object, for debug
        purposes.
        """
        parent = self.manager.parent
        return "{}(message={!r}, resource_classname={!r}, filter_args={!r}, " \
               "parent_classname={!r}, parent_name={!r})". \
               format(self.__class__.__name__, self.args[0],
                      self.manager.resource_class.__name__,
                      self.filter_args,
                      parent.__class__.__name__ if parent else None,
                      parent.name if parent else None)

    def str_def(self):
        """
        :term:`string`: The exception as a string in a Python definition-style
        format, e.g. for parsing by scripts:

        .. code-block:: text

            classname={}; resource_classname={}; filter_args={}; parent_classname={}; parent_name={}; message={};
        """  # noqa: E501
        parent = self.manager.parent
        return "classname={!r}; resource_classname={!r}; filter_args={!r}; " \
               "parent_classname={!r}; parent_name={!r}; message={!r};". \
               format(self.__class__.__name__,
                      self.manager.resource_class.__name__,
                      self.filter_args,
                      parent.__class__.__name__ if parent else None,
                      parent.name if parent else None,
                      self.args[0])
