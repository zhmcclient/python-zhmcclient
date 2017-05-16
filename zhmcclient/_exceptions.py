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
Exceptions that can be raised by the client.
"""

import re


__all__ = ['Error', 'ConnectionError', 'ConnectTimeout', 'ReadTimeout',
           'RetriesExceeded', 'AuthError', 'ParseError', 'VersionError',
           'HTTPError', 'OperationTimeout', 'StatusTimeout',
           'NoUniqueMatch', 'NotFound']


class Error(Exception):
    """
    Abstract base class for exceptions specific to this package.

    Derived from :exc:`~py:exceptions.Exception`.
    """

    def __init__(self, *args):
        """
        Parameters:

          *args:
            A list of input arguments for the exception object.

            The derived classes define more specific parameters.

            These input arguments will be available as tuple items in the
            ``args`` instance variable of the exception object.
        """
        super(Error, self).__init__(*args)


class ConnectionError(Error):
    """
    This exception indicates a problem with the connection to the HMC, below
    the HTTP level. HTTP errors are indicated via :exc:`~zhmcclient.HTTPError`.

    A retry by the user code is not likely to be successful, unless connect or
    read retries had been disabled when creating the session (see
    :class:`~zhmcclient.Session`).

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, msg, details=None):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          details (Exception):
            The original exception describing details about the error.
        """
        super(ConnectionError, self).__init__(msg)
        self._details = details

    @property
    def details(self):
        """
        The original exception caught by this package, providing more
        information about the problem, if there was such an original exception.
        `None`, otherwise.

        This may be one of the following exceptions:

        * Any exception derived from
          :exc:`requests.exceptions.RequestException`.
        """
        return self._details


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


class AuthError(Error):
    """
    This exception indicates an authentication error with the HMC, either at
    the TLS/SSL handshake level (e.g. with CA certificates), or at the HTTP
    level.

    Derived from :exc:`~zhmcclient.Error`.
    """

    def __init__(self, msg, details=None):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

          details (Exception):
            The original exception describing details about the error.
        """
        super(AuthError, self).__init__(msg)
        self._details = details

    @property
    def details(self):
        """
        The original exception describing details about the error, if there
        was such an original exception. `None`, otherwise.

        This may be one of the following exceptions:

        * :exc:`~zhmcclient.HTTPError`
        """
        return self._details


class ParseError(Error):
    """
    This exception indicates a parsing error while processing the JSON payload
    in a response from the HMC.

    Derived from :exc:`~zhmcclient.Error`.

    The error location within the payload is automatically determined by
    parsing the error message for the pattern::

      ``': line 1 column 2 '``
    """

    def __init__(self, msg):
        """
        Parameters:

          msg (:term:`string`):
            A human readable message describing the problem.

            This should be the message of the `ValueError` exception raised
            by methods of the :class:`py:json.JSONDecoder` class.
        """
        super(ParseError, self).__init__(msg)
        m = re.search(r': line ([0-9]+) column ([0-9]+) ', msg)
        if m:
            self._line = int(m.group(1))
            self._column = int(m.group(2))
        else:
            self._line = None
            self._column = None

    @property
    def line(self):
        """
        The 1-based line number of the error location within the JSON payload,
        as an integer.

        `None` indicates that the error location is not available.
        """
        return self._line

    @property
    def column(self):
        """
        The 1-based column number of the error location within the JSON
        payload, as an integer.

        `None` indicates that the error location is not available.
        """
        return self._column


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


class HTTPError(Error):
    """
    This exception indicates that the HMC returned an HTTP response with a bad
    HTTP status code.

    Derived from :exc:`~zhmcclient.Error`.
    """

    html_error_reason = 999  # Used when the HMC returns HTML content

    def __init__(self, body):
        """
        Parameters:

          body (:term:`json object`):
            Body of the HTTP error response.
        """
        super(HTTPError, self).__init__(body)
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
        return "HTTPError(http_status={}, reason={}, message={}, "\
               "request_method={}, request_uri={}, ...)".\
               format(self.http_status, self.reason, self.message,
                      self.request_method, self.request_uri)


class OperationTimeout(Error):
    """
    This exception indicates that the waiting for completion of an asynchronous
    HMC operation has timed out.

    Derived from :exc:`~zhmcclient.Error`.
    """
    pass


class StatusTimeout(Error):
    """
    This exception indicates that the waiting for reaching a desired resource
    status has timed out.

    Derived from :exc:`~zhmcclient.Error`.
    """
    pass


class NoUniqueMatch(Error):
    """
    This exception indicates that a find function has found more than one item.

    Derived from :exc:`~zhmcclient.Error`.
    """
    pass


class NotFound(Error):
    """
    This exception indicates that a find function did not find an item.

    Derived from :exc:`~zhmcclient.Error`.
    """
    pass
