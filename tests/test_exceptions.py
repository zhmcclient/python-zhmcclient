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

from __future__ import absolute_import

import unittest
import warnings
import six

from zhmcclient._exceptions import Error, ConnectionError, AuthError,\
                                   ParseError, VersionError, HTTPError,\
                                   NoUniqueMatch, NotFound


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

        exc = MyError()

        self.assertTrue(isinstance(exc, Error))
        self.assertTrue(isinstance(exc.args, tuple))
        self.assertEqual(len(exc.args), 0)

    def test_one(self):

        exc = MyError('zaphod')

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], 'zaphod')

    def test_two(self):

        exc = MyError('zaphod', 42)

        self.assertEqual(len(exc.args), 2)
        self.assertEqual(exc.args[0], 'zaphod')
        self.assertEqual(exc.args[1], 42)

    def test_one_tuple(self):

        exc = MyError(('zaphod', 42))

        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], ('zaphod', 42))


class SimpleTestMixin(object):
    """
    Mixin to test a number of simple exception classes.

    Simple exception classes take a message string as the single input
    argument.
    """

    CLASS = None  # Exception class to be tested

    def test_empty(self):

        try:
            exc = self.CLASS()
        except TypeError as e:
            self.assertEqual(e.args[0],
                             "__init__() takes exactly 2 arguments (1 given)")
        except Exception as e:
            self.fail("Exception was raised: %r" % e)
        else:
            self.fail("No exception was raised.")

    def test_two(self):

        try:
            exc = self.CLASS('zaphod', 42)
        except TypeError as e:
            self.assertEqual(e.args[0],
                             "__init__() takes exactly 2 arguments (3 given)")
        except Exception as e:
            self.fail("Exception was raised: %r" % e)
        else:
            self.fail("No exception was raised.")

    def test_one(self):

        exc = self.CLASS('zaphod')

        self.assertTrue(isinstance(exc, Error))
        self.assertTrue(isinstance(exc.args, tuple))
        self.assertEqual(len(exc.args), 1)
        self.assertEqual(exc.args[0], 'zaphod')


class TestConnectionError(unittest.TestCase, SimpleTestMixin):
    """
    Test the simple exception class ``ConnectionError``.
    """

    def setUp(self):
        self.CLASS = ConnectionError


class TestAuthError(unittest.TestCase, SimpleTestMixin):
    """
    Test the simple exception class ``AuthError``.
    """

    def setUp(self):
        self.CLASS = AuthError


class TestParseError(unittest.TestCase, SimpleTestMixin):
    """
    Test the simple exception class ``ParseError``.
    """

    def setUp(self):
        self.CLASS = ParseError


class TestVersionError(unittest.TestCase, SimpleTestMixin):
    """
    Test the simple exception class ``VersionError``.
    """

    def setUp(self):
        self.CLASS = VersionError


class TestHTTPError(unittest.TestCase, SimpleTestMixin):
    """
    Test exception class ``HTTPError``.
    """

    def test_empty(self):

        try:
            exc = HTTPError()
        except TypeError as e:
            self.assertEqual(e.args[0],
                             "__init__() takes exactly 2 arguments (1 given)")
        except Exception as e:
            self.fail("Exception was raised: %r" % e)
        else:
            self.fail("No exception was raised.")

    def test_two(self):

        try:
            exc = HTTPError(dict(reason=42), 42)
        except TypeError as e:
            self.assertEqual(e.args[0],
                             "__init__() takes exactly 2 arguments (3 given)")
        except Exception as e:
            self.fail("Exception was raised: %r" % e)
        else:
            self.fail("No exception was raised.")

    def test_one(self):

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
        self.assertEqual(exc.request_query_parms, resp_body['request-query-parms'])
        self.assertEqual(exc.request_headers, resp_body['request-headers'])
        self.assertEqual(exc.request_authenticated_as, resp_body['request-authenticated-as'])
        self.assertEqual(exc.request_body, resp_body['request-body'])
        self.assertEqual(exc.request_body_as_string, resp_body['request-body-as-string'])
        self.assertEqual(exc.request_body_as_string_partial, resp_body['request-body-as-string-partial'])
        self.assertEqual(exc.stack, resp_body['stack'])
        self.assertEqual(exc.error_details, resp_body['error-details'])

        # Check str()
        exp_str = str(resp_body['http-status']) + ',' + \
                  str(resp_body['reason']) + ': ' + resp_body['message']
        self.assertEqual(str(exc), exp_str)

        # Check repr()
        exp_repr = 'HTTPError(' + str(resp_body['http-status']) + ', ' + \
                   str(resp_body['reason']) + ', ' + resp_body['message'] + \
                   ', ...)'
        self.assertEqual(repr(exc), exp_repr)


if __name__ == '__main__':
    unittest.main()
