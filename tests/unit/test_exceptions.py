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


class SimpleTestMixin(object):
    """
    Mixin to test a number of simple exception classes.

    Simple exception classes take a message string as the single input
    argument.
    """

    exc_class = Exception  # Exception class to be tested

    def test_empty(self):
        """Test simple exception with no argument."""

        try:
            self.exc_class()
        except TypeError as e:
            self.assertRegexpMatches(
                e.args[0],
                r"__init__\(\) (takes.* 2 .*arguments .*1 .*given.*|"
                r"missing 1 .*argument.*)")
        except Exception as e:  # pylint: disable=broad-except
            self.fail("Exception was raised: %r" % e)
        else:
            self.fail("No exception was raised.")

    def test_one(self):
        """Test simple exception with one argument."""

        exc = self.exc_class('zaphod')

        self.assertTrue(isinstance(exc, Error))
        self.assertTrue(isinstance(exc.args, tuple))
        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], 'zaphod')

    def test_two(self):
        """Test simple exception with two arguments."""

        try:
            self.exc_class('zaphod', 42)
        except TypeError as e:
            self.assertRegexpMatches(
                e.args[0],
                r"__init__\(\) takes.* 2 .*arguments .*3 .*given.*")
        except Exception as e:  # pylint: disable=broad-except
            self.fail("Exception was raised: %r" % e)
        else:
            self.fail("No exception was raised.")


class TestConnectionError(unittest.TestCase, SimpleTestMixin):
    """
    Test the simple exception class ``ConnectionError``.
    """

    def setUp(self):
        self.exc_class = ConnectionError


class TestAuthError(unittest.TestCase, SimpleTestMixin):
    """
    Test the simple exception class ``AuthError``.
    """

    def setUp(self):
        self.exc_class = AuthError


class TestParseError(unittest.TestCase, SimpleTestMixin):
    """
    Test the simple exception class ``ParseError``.
    """

    def setUp(self):
        self.exc_class = ParseError


class TestVersionError(unittest.TestCase, SimpleTestMixin):
    """
    Test the simple exception class ``VersionError``.
    """

    def setUp(self):
        self.exc_class = VersionError


class TestHTTPError(unittest.TestCase, SimpleTestMixin):
    """
    Test exception class ``HTTPError``.
    """

    def test_empty(self):
        """Test HTTPError with no arguments (expecting failure)."""

        try:
            # pylint: disable=no-value-for-parameter
            HTTPError()
        except TypeError as e:
            self.assertRegexpMatches(
                e.args[0],
                r"__init__\(\) (takes.* 2 .*arguments .*1 .*given.*|"
                r"missing 1 .*argument.*)")
        except Exception as e:  # pylint: disable=broad-except
            self.fail("Exception was raised: %r" % e)
        else:
            self.fail("No exception was raised.")

    def test_two(self):
        """Test HTTPError with two arguments (expecting failure)."""

        try:
            # pylint: disable=too-many-function-args
            HTTPError(dict(reason=42), 42)
        except TypeError as e:
            self.assertRegexpMatches(
                e.args[0],
                r"__init__\(\) takes.* 2 .*arguments .*3 .*given.*")
        except Exception as e:  # pylint: disable=broad-except
            self.fail("Exception was raised: %r" % e)
        else:
            self.fail("No exception was raised.")

    def test_one(self):
        """Test HTTPError with one argument."""

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
