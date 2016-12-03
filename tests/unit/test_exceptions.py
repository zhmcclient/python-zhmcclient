#!/usr/bin/env python
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
Unit tests for _exceptions module.
"""

from __future__ import absolute_import, print_function

import unittest

from zhmcclient import Error, ConnectionError, AuthError, ParseError,\
    VersionError, HTTPError

# TODO: Add tests for NoUniqueMatch
# TODO: Add tests for NotFound


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


class NumberArgsTestMixin(object):
    """
    Mixin to test exception classes with the allowable numbers of input
    arguments.
    """

    # Derived classes set these class variables as instance variables:

    # Exception class to be tested
    exc_class = None

    # Minimum number of input arguments to ctor
    min_args = None

    # Maximum number of input arguments to ctor
    max_args = None

    def test_good(self):
        """Test exception class with the allowable number of input arguments,
        where the first argument is always a string."""

        for nargs in range(self.min_args, self.max_args + 1):
            args = ['zaphod']
            args.extend((nargs - 1) * [42])

            exc = self.exc_class(*args)

            self.assertTrue(isinstance(exc, Error))
            self.assertTrue(isinstance(exc.args, tuple))
            self.assertEqual(len(exc.args), len(args),
                             "Expected %d arguments, got: %r" %
                             (len(args), exc.args))
            for i, arg in enumerate(args):
                self.assertEqual(exc.args[i], arg,
                                 "For argument at index %d, expected %r, "
                                 "got: %r" % (i, arg, exc.args[i]))


class DetailsTestMixin(object):
    """
    Mixin to test exception classes with a `details` property.
    """

    # Derived classes set these class variables as instance variables:

    # Exception class to be tested
    exc_class = None

    def test_details_none(self):
        """Test details property with None."""

        exc = self.exc_class("Bla bla", None)

        self.assertIsNone(exc.details)

    def test_details_default(self):
        """Test details property with default."""

        exc = self.exc_class("Bla bla")

        self.assertIsNone(exc.details)

    def test_details_valueerror(self):
        """Test details property with a ValueError."""

        details_exc = ValueError("value error")

        exc = self.exc_class("Bla bla", details_exc)

        self.assertEqual(exc.details, details_exc)


class TestConnectionError(unittest.TestCase, NumberArgsTestMixin,
                          DetailsTestMixin):
    """
    Test the simple exception class ``ConnectionError``.
    """

    def setUp(self):
        self.exc_class = ConnectionError
        self.min_args = 1
        self.max_args = 1


class TestAuthError(unittest.TestCase, NumberArgsTestMixin, DetailsTestMixin):
    """
    Test the simple exception class ``AuthError``.
    """

    def setUp(self):
        self.exc_class = AuthError
        self.min_args = 1
        self.max_args = 1


class TestParseError(unittest.TestCase, NumberArgsTestMixin):
    """
    Test the simple exception class ``ParseError``.
    """

    def setUp(self):
        self.exc_class = ParseError
        self.min_args = 1
        self.max_args = 1

    def test_line_column_1(self):
        """A simple message string that matches the line/col parsing."""

        exc = self.exc_class("Bla: line 42 column 7 (char 6)")

        self.assertEqual(exc.line, 42)
        self.assertEqual(exc.column, 7)

    def test_line_column_2(self):
        """A minimally matching message string."""

        exc = self.exc_class(": line 7 column 42 ")

        self.assertEqual(exc.line, 7)
        self.assertEqual(exc.column, 42)

    def test_line_column_3(self):
        """A message string that does not match (because of the 'x' in the
        line)."""

        exc = self.exc_class(": line 7x column 42 ")

        self.assertEqual(exc.line, None)
        self.assertEqual(exc.column, None)


class TestVersionError(unittest.TestCase, NumberArgsTestMixin):
    """
    Test the simple exception class ``VersionError``.
    """

    def setUp(self):
        self.exc_class = VersionError
        self.min_args = 3
        self.max_args = 3

    def test_api_version(self):
        """Test that the minimum and actual API version can be retrieved."""

        min_api_version = (2, 3)
        api_version = (1, 4)

        exc = self.exc_class("Bla", min_api_version, api_version)

        self.assertEqual(exc.min_api_version, min_api_version)
        self.assertEqual(exc.api_version, api_version)


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

        # Check str()
        exp_str = "{http-status},{reason}: {message} [{request-method} "\
                  "{request-uri}]".format(**resp_body)
        self.assertEqual(str(exc), exp_str)

        # Check repr()
        exp_repr = "HTTPError(http_status={http-status}, reason={reason}, "\
                   "message={message}, request_method={request-method}, "\
                   "request_uri={request-uri}, ...)".format(**resp_body)
        self.assertEqual(repr(exc), exp_repr)


if __name__ == '__main__':
    unittest.main()
