#!/usr/bin/env python
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
Unit tests for _exceptions module.
"""

from __future__ import absolute_import, print_function

import unittest

from zhmcclient import Error, ConnectionError, ConnectTimeout, ReadTimeout, \
    RetriesExceeded, ClientAuthError, ServerAuthError, ParseError, \
    VersionError, HTTPError, OperationTimeout, StatusTimeout, NoUniqueMatch, \
    NotFound, Client
from zhmcclient_mock import FakedSession


class MyError(Error):
    """
    Concrete class to get instances of abstract base class ``Error``.
    """

    def __init__(self, *args, **kwargs):
        super(MyError, self).__init__(*args, **kwargs)


class TestError(unittest.TestCase):
    """
    Test the ``Error`` exception class.

    Because this is an abstract base class, we use our own derived class.
    """

    def test_empty(self):
        """Test Error exception with no argument."""

        exc = MyError()

        self.assertTrue(isinstance(exc, Error))
        self.assertTrue(isinstance(exc.args, tuple))
        self.assertEqual(len(exc.args), 0)

    def test_one(self):
        """Test Error exception with one argument."""

        exc = MyError('zaphod')

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], 'zaphod')

    def test_two(self):
        """Test with two arguments."""

        exc = MyError('zaphod', 42)

        self.assertEqual(len(exc.args), 2)
        self.assertEqual(exc.args[0], 'zaphod')
        self.assertEqual(exc.args[1], 42)

    def test_one_tuple(self):
        """Test Error exception with one argument that is a tuple of two
        items."""

        exc = MyError(('zaphod', 42))

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], ('zaphod', 42))


class TestConnectionError(unittest.TestCase):
    """
    Test exception class ``ConnectionError``.
    """

    def setUp(self):
        self.message = "bla bla connection error"
        self.details_exc = ValueError("value error")

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""

        exc = ConnectionError(self.message, self.details_exc)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ConnectionError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ConnectionError'), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_msg_named(self):
        """Test exception created with named arguments."""

        exc = ConnectionError(msg=self.message, details=self.details_exc)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ConnectionError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ConnectionError'), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestConnectTimeout(unittest.TestCase):
    """
    Test exception class ``ConnectTimeout``.
    """

    def setUp(self):
        self.message = "bla bla connection timeout"
        self.details_exc = ValueError("value error")
        self.connect_timeout = 30
        self.connect_retries = 3

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""

        exc = ConnectTimeout(self.message, self.details_exc,
                             self.connect_timeout, self.connect_retries)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        self.assertEqual(exc.connect_timeout, self.connect_timeout)
        self.assertEqual(exc.connect_retries, self.connect_retries)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ConnectTimeout\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ConnectTimeout'), str_def)
        self.assertIn('connect_timeout={!r};'.
                      format(exc.connect_timeout), str_def)
        self.assertIn('connect_retries={!r};'.
                      format(exc.connect_retries), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_msg_named(self):
        """Test exception created with named arguments."""

        exc = ConnectTimeout(msg=self.message, details=self.details_exc,
                             connect_timeout=self.connect_timeout,
                             connect_retries=self.connect_retries)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        self.assertEqual(exc.connect_timeout, self.connect_timeout)
        self.assertEqual(exc.connect_retries, self.connect_retries)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ConnectTimeout\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ConnectTimeout'), str_def)
        self.assertIn('connect_timeout={!r};'.
                      format(exc.connect_timeout), str_def)
        self.assertIn('connect_retries={!r};'.
                      format(exc.connect_retries), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestReadTimeout(unittest.TestCase):
    """
    Test exception class ``ReadTimeout``.
    """

    def setUp(self):
        self.message = "bla bla read timeout"
        self.details_exc = ValueError("value error")
        self.read_timeout = 30
        self.read_retries = 3

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""

        exc = ReadTimeout(self.message, self.details_exc,
                          self.read_timeout, self.read_retries)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        self.assertEqual(exc.read_timeout, self.read_timeout)
        self.assertEqual(exc.read_retries, self.read_retries)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ReadTimeout\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ReadTimeout'), str_def)
        self.assertIn('read_timeout={!r};'.
                      format(exc.read_timeout), str_def)
        self.assertIn('read_retries={!r};'.
                      format(exc.read_retries), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_msg_named(self):
        """Test exception created with named arguments."""

        exc = ReadTimeout(msg=self.message, details=self.details_exc,
                          read_timeout=self.read_timeout,
                          read_retries=self.read_retries)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        self.assertEqual(exc.read_timeout, self.read_timeout)
        self.assertEqual(exc.read_retries, self.read_retries)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ReadTimeout\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ReadTimeout'), str_def)
        self.assertIn('read_timeout={!r};'.
                      format(exc.read_timeout), str_def)
        self.assertIn('read_retries={!r};'.
                      format(exc.read_retries), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestRetriesExceeded(unittest.TestCase):
    """
    Test exception class ``RetriesExceeded``.
    """

    def setUp(self):
        self.message = "bla bla retries exceeded"
        self.details_exc = ValueError("value error")
        self.connect_retries = 3

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""

        exc = RetriesExceeded(self.message, self.details_exc,
                              self.connect_retries)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        self.assertEqual(exc.connect_retries, self.connect_retries)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^RetriesExceeded\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('RetriesExceeded'), str_def)
        self.assertIn('connect_retries={!r};'.
                      format(exc.connect_retries), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_msg_named(self):
        """Test exception created with named arguments."""

        exc = RetriesExceeded(msg=self.message, details=self.details_exc,
                              connect_retries=self.connect_retries)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        self.assertEqual(exc.connect_retries, self.connect_retries)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^RetriesExceeded\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('RetriesExceeded'), str_def)
        self.assertIn('connect_retries={!r};'.
                      format(exc.connect_retries), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestClientAuthError(unittest.TestCase):
    """
    Test exception class ``ClientAuthError``.
    """

    def setUp(self):
        self.message = "bla bla client auth error"

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""

        exc = ClientAuthError(self.message)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ClientAuthError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ClientAuthError'), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_msg_named(self):
        """Test exception created with named arguments."""

        exc = ClientAuthError(msg=self.message)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ClientAuthError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ClientAuthError'), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestServerAuthError(unittest.TestCase):
    """
    Test exception class ``ServerAuthError``.
    """

    def setUp(self):
        resp_body = {
            'http-status': 404,
            'reason': 42,
            'message': 'abc def',
            'request-method': 'POST',
            'request-uri': '/api/cpcs/cpc1',
            'request-query-parms': [],
            'request-headers': {
                'content-type': 'application/json',
            },
            'request-authenticated-as': None,
            'request-body': None,
            'request-body-as-string': None,
            'request-body-as-string-partial': None,
            'stack': None,
            'error-details': None,
        }
        self.details_exc = HTTPError(resp_body)
        self.message = "bla bla server auth error"

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""

        exc = ServerAuthError(self.message, self.details_exc)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ServerAuthError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ServerAuthError'), str_def)
        self.assertIn('request_method={!r};'.
                      format(exc.details.request_method), str_def)
        self.assertIn('request_uri={!r};'.
                      format(exc.details.request_uri), str_def)
        self.assertIn('http_status={!r};'.
                      format(exc.details.http_status), str_def)
        self.assertIn('reason={!r};'.
                      format(exc.details.reason), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_msg_named(self):
        """Test exception created with named arguments."""

        exc = ServerAuthError(msg=self.message, details=self.details_exc)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.details, self.details_exc)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ServerAuthError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ServerAuthError'), str_def)
        self.assertIn('request_method={!r};'.
                      format(exc.details.request_method), str_def)
        self.assertIn('request_uri={!r};'.
                      format(exc.details.request_uri), str_def)
        self.assertIn('http_status={!r};'.
                      format(exc.details.http_status), str_def)
        self.assertIn('reason={!r};'.
                      format(exc.details.reason), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestParseError(unittest.TestCase):
    """
    Test exception class ``ParseError``.
    """

    def setUp(self):
        self.exc_class = ParseError

    def test_line_column_1(self):
        """A simple message string that matches the line/col parsing."""
        message = "Bla: line 42 column 7 (char 6)"

        exc = ParseError(message)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], message)

        self.assertEqual(exc.line, 42)
        self.assertEqual(exc.column, 7)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ParseError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ParseError'), str_def)
        self.assertIn('line={!r};'.format(exc.line), str_def)
        self.assertIn('column={!r};'.format(exc.column), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_line_column_2(self):
        """A minimally matching message string."""
        message = ": line 7 column 42 "

        exc = ParseError(message)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], message)

        self.assertEqual(exc.line, 7)
        self.assertEqual(exc.column, 42)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ParseError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ParseError'), str_def)
        self.assertIn('line={!r};'.format(exc.line), str_def)
        self.assertIn('column={!r};'.format(exc.column), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_line_column_3(self):
        """A message string that does not match (because of the 'x' in the
        line)."""
        message = ": line 7x column 42 "

        exc = ParseError(message)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], message)

        self.assertEqual(exc.line, None)
        self.assertEqual(exc.column, None)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^ParseError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('ParseError'), str_def)
        self.assertIn('line={!r};'.format(exc.line), str_def)
        self.assertIn('column={!r};'.format(exc.column), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestVersionError(unittest.TestCase):
    """
    Test exception class ``VersionError``.
    """

    def test_api_version(self):
        """Test that the minimum and actual API version can be retrieved."""
        min_api_version = (2, 3)
        api_version = (1, 4)
        message = "invalid version"

        exc = VersionError(message, min_api_version, api_version)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], message)

        self.assertEqual(exc.min_api_version, min_api_version)
        self.assertEqual(exc.api_version, api_version)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^VersionError\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('VersionError'), str_def)
        self.assertIn('min_api_version={!r};'.
                      format(exc.min_api_version), str_def)
        self.assertIn('api_version={!r};'.format(exc.api_version), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestHTTPError(unittest.TestCase):
    """
    Test exception class ``HTTPError``.
    """

    def test_good(self):
        """Test HTTPError with a good input argument."""

        resp_body = {
            'http-status': 404,
            'reason': 42,
            'message': 'abc def',
            'request-method': 'POST',
            'request-uri': '/api/cpcs/cpc1',
            'request-query-parms': [],
            'request-headers': {
                'content-type': 'application/json',
            },
            'request-authenticated-as': None,  # TODO: Real value
            'request-body': None,  # TODO: Real value
            'request-body-as-string': None,  # TODO: Real value
            'request-body-as-string-partial': None,  # TODO: Real value
            'stack': None,  # TODO: Real value
            'error-details': None,  # TODO: Real value
        }

        exc = HTTPError(resp_body)

        self.assertTrue(isinstance(exc, Error))

        self.assertEqual(len(exc.args), 1)
        self.assertTrue(isinstance(exc.args[0], dict))

        # Check the result properties:
        self.assertEqual(exc.http_status, resp_body['http-status'])
        self.assertEqual(exc.reason, resp_body['reason'])
        self.assertEqual(exc.message, resp_body['message'])
        self.assertEqual(exc.request_method, resp_body['request-method'])
        self.assertEqual(exc.request_uri, resp_body['request-uri'])
        self.assertEqual(exc.request_query_parms,
                         resp_body['request-query-parms'])
        self.assertEqual(exc.request_headers, resp_body['request-headers'])
        self.assertEqual(exc.request_authenticated_as,
                         resp_body['request-authenticated-as'])
        self.assertEqual(exc.request_body, resp_body['request-body'])
        self.assertEqual(exc.request_body_as_string,
                         resp_body['request-body-as-string'])
        self.assertEqual(exc.request_body_as_string_partial,
                         resp_body['request-body-as-string-partial'])
        self.assertEqual(exc.stack, resp_body['stack'])
        self.assertEqual(exc.error_details, resp_body['error-details'])

        # Check repr()
        repr_str = repr(exc)
        repr_pattern = r'^HTTPError\(.*\)$'
        self.assertRegexpMatches(repr_str, repr_pattern)

        # Check str()
        exp_str = "{http-status},{reason}: {message} [{request-method} "\
                  "{request-uri}]".format(**resp_body)
        self.assertEqual(str(exc), exp_str)

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('HTTPError'), str_def)
        self.assertIn('request_method={!r};'.
                      format(exc.request_method), str_def)
        self.assertIn('request_uri={!r};'.
                      format(exc.request_uri), str_def)
        self.assertIn('http_status={!r};'.
                      format(exc.http_status), str_def)
        self.assertIn('reason={!r};'.
                      format(exc.reason), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestOperationTimeout(unittest.TestCase):
    """
    Test exception class ``OperationTimeout``.
    """

    def setUp(self):
        self.message = "bla bla operation timeout"
        self.details_exc = ValueError("value error")
        self.operation_timeout = 200

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""

        exc = OperationTimeout(self.message, self.operation_timeout)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.operation_timeout, self.operation_timeout)

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('OperationTimeout'), str_def)
        self.assertIn('operation_timeout={!r};'.
                      format(exc.operation_timeout), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_msg_named(self):
        """Test exception created with named arguments."""

        exc = OperationTimeout(msg=self.message,
                               operation_timeout=self.operation_timeout)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.operation_timeout, self.operation_timeout)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^OperationTimeout\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('OperationTimeout'), str_def)
        self.assertIn('operation_timeout={!r};'.
                      format(exc.operation_timeout), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestStatusTimeout(unittest.TestCase):
    """
    Test exception class ``StatusTimeout``.
    """

    def setUp(self):
        self.message = "bla bla operation timeout"
        self.details_exc = ValueError("value error")
        self.status_timeout = 90
        self.desired_statuses = ['foo on']
        self.actual_status = 'foo off'

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""

        exc = StatusTimeout(self.message, self.actual_status,
                            self.desired_statuses, self.status_timeout)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.actual_status, self.actual_status)
        self.assertEqual(exc.desired_statuses, self.desired_statuses)
        self.assertEqual(exc.status_timeout, self.status_timeout)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^StatusTimeout\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('StatusTimeout'), str_def)
        self.assertIn('actual_status={!r};'.
                      format(exc.actual_status), str_def)
        self.assertIn('desired_statuses={!r};'.
                      format(exc.desired_statuses), str_def)
        self.assertIn('status_timeout={!r};'.
                      format(exc.status_timeout), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)

    def test_msg_named(self):
        """Test exception created with named arguments."""

        exc = StatusTimeout(msg=self.message,
                            actual_status=self.actual_status,
                            desired_statuses=self.desired_statuses,
                            status_timeout=self.status_timeout)

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], self.message)

        self.assertEqual(exc.actual_status, self.actual_status)
        self.assertEqual(exc.desired_statuses, self.desired_statuses)
        self.assertEqual(exc.status_timeout, self.status_timeout)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^StatusTimeout\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('StatusTimeout'), str_def)
        self.assertIn('actual_status={!r};'.
                      format(exc.actual_status), str_def)
        self.assertIn('desired_statuses={!r};'.
                      format(exc.desired_statuses), str_def)
        self.assertIn('status_timeout={!r};'.
                      format(exc.status_timeout), str_def)
        self.assertIn('message={!r};'.format(exc.args[0]), str_def)


class TestNoUniqueMatch(unittest.TestCase):
    """
    Test exception class ``NoUniqueMatch``.
    """

    def setUp(self):
        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'faked-cpc1',
            'parent': None,
            'class': 'cpc',
            'name': 'cpc_1',
            'description': 'CPC #1',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
        })
        self.faked_osa1 = self.faked_cpc.adapters.add({
            'object-id': 'fake-osa1',
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': 'osa 1',
            'description': 'OSA #1',
            'status': 'active',
            'type': 'osd',
        })
        self.faked_osa2 = self.faked_cpc.adapters.add({
            'object-id': 'fake-osa2',
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': 'osa 2',
            'description': 'OSA #2',
            'status': 'active',
            'type': 'osd',
        })
        self.client = Client(self.session)
        self.cpc = self.client.cpcs.list()[0]
        self.adapters = self.cpc.adapters.list()

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""
        filter_args = {'type': 'osa', 'status': 'active'}

        exc = NoUniqueMatch(filter_args, self.cpc.adapters, self.adapters)

        self.assertEqual(len(exc.args), 1)
        # auto-generated message, we don't expect a particular value

        self.assertEqual(exc.filter_args, filter_args)
        self.assertEqual(exc.manager, self.cpc.adapters)
        self.assertEqual(exc.resources, self.adapters)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^NoUniqueMatch\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('NoUniqueMatch'), str_def)
        self.assertIn('resource_classname={!r};'.format('Adapter'), str_def)
        self.assertIn('filter_args={!r};'.
                      format(exc.filter_args), str_def)
        self.assertIn('parent_classname={!r};'.format('Cpc'), str_def)
        self.assertIn('parent_name={!r};'.format(self.cpc.name), str_def)

    def test_named(self):
        """Test exception created with named arguments."""
        filter_args = {'type': 'osa', 'status': 'active'}

        exc = NoUniqueMatch(filter_args=filter_args, manager=self.cpc.adapters,
                            resources=tuple(self.adapters))

        self.assertEqual(len(exc.args), 1)
        # auto-generated message, we don't expect a particular value

        self.assertEqual(exc.filter_args, filter_args)
        self.assertEqual(exc.manager, self.cpc.adapters)
        self.assertEqual(exc.resources, self.adapters)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^NoUniqueMatch\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('NoUniqueMatch'), str_def)
        self.assertIn('resource_classname={!r};'.format('Adapter'), str_def)
        self.assertIn('filter_args={!r};'.
                      format(exc.filter_args), str_def)
        self.assertIn('parent_classname={!r};'.format('Cpc'), str_def)
        self.assertIn('parent_name={!r};'.format(self.cpc.name), str_def)


class TestNotFound(unittest.TestCase):
    """
    Test exception class ``NotFound``.
    """

    def setUp(self):
        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'faked-cpc1',
            'parent': None,
            'class': 'cpc',
            'name': 'cpc_1',
            'description': 'CPC #1',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
        })
        self.faked_osa1 = self.faked_cpc.adapters.add({
            'object-id': 'fake-osa1',
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': 'osa 1',
            'description': 'OSA #1',
            'status': 'active',
            'type': 'osd',
        })
        self.client = Client(self.session)
        self.cpc = self.client.cpcs.list()[0]
        self.adapter = self.cpc.adapters.list()[0]

    def test_unnamed(self):
        """Test exception created with unnamed arguments."""
        filter_args = {'type': 'osa', 'status': 'active'}

        exc = NotFound(filter_args, self.cpc.adapters)

        self.assertEqual(len(exc.args), 1)
        # auto-generated message, we don't expect a particular value

        self.assertEqual(exc.filter_args, filter_args)
        self.assertEqual(exc.manager, self.cpc.adapters)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^NotFound\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('NotFound'), str_def)
        self.assertIn('resource_classname={!r};'.format('Adapter'), str_def)
        self.assertIn('filter_args={!r};'.
                      format(exc.filter_args), str_def)
        self.assertIn('parent_classname={!r};'.format('Cpc'), str_def)
        self.assertIn('parent_name={!r};'.format(self.cpc.name), str_def)

    def test_named(self):
        """Test exception created with named arguments."""
        filter_args = {'type': 'osa', 'status': 'active'}

        exc = NotFound(filter_args=filter_args, manager=self.cpc.adapters)

        self.assertEqual(len(exc.args), 1)
        # auto-generated message, we don't expect a particular value

        self.assertEqual(exc.filter_args, filter_args)
        self.assertEqual(exc.manager, self.cpc.adapters)

        # Check repr()
        self.assertRegexpMatches(repr(exc), r'^NotFound\(.*\)$')

        # Check str()
        self.assertEqual(str(exc), exc.args[0])

        # Check str_def()
        str_def = exc.str_def()
        self.assertIn('classname={!r};'.format('NotFound'), str_def)
        self.assertIn('resource_classname={!r};'.format('Adapter'), str_def)
        self.assertIn('filter_args={!r};'.
                      format(exc.filter_args), str_def)
        self.assertIn('parent_classname={!r};'.format('Cpc'), str_def)
        self.assertIn('parent_name={!r};'.format(self.cpc.name), str_def)


if __name__ == '__main__':
    unittest.main()
