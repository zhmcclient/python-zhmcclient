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

import pytest
import re
import six

from zhmcclient import Error, ConnectionError, ConnectTimeout, ReadTimeout, \
    RetriesExceeded, AuthError, ClientAuthError, ServerAuthError, ParseError, \
    VersionError, HTTPError, OperationTimeout, StatusTimeout, NoUniqueMatch, \
    NotFound, Client
from zhmcclient_mock import FakedSession


# Some HTTPError response bodies, used by multiple testcases:

HTTP_ERROR_1 = {
    'http-status': 404,
    'reason': 42,
    'message': 'abc def',
    'request-method': 'POST',
    'request-uri': '/api/cpcs/cpc1',
    'request-query-parms': ['properties=abc,def'],
    'request-headers': {
        'content-type': 'application/json',
    },
    'request-authenticated-as': 'fake_user',
    'request-body': None,
    'request-body-as-string': "fake request body",
    'request-body-as-string-partial': None,
    'stack': None,
    'error-details': None,
}

HTTP_ERROR_2 = {
    'http-status': 404,
    'reason': 42,
    'message': 'abc def',
}

HTTP_ERROR_3 = {
    'message': 'abc def',
}

HTTP_ERROR_4 = {
}


def func_args(arg_values, arg_names):
    """
    Convert args and arg_names into positional args and keyword args.
    """
    posargs = []
    kwargs = {}
    for i, name in enumerate(arg_names):
        value = arg_values[i]
        if name is not None:
            kwargs[name] = value
        else:
            posargs.append(value)
    return posargs, kwargs


class MyError(Error):
    """
    Concrete class to get instances of abstract base class ``Error``.
    """

    def __init__(self, *args, **kwargs):
        super(MyError, self).__init__(*args, **kwargs)


class TestError(object):
    """
    All tests for exception class Error.

    Because this is an abstract base class, we use our own derived class
    MyError.
    """

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (arg1, ...)
            (),  # no args
            ('zaphod',),  # one arg
            ('zaphod', 42),  # two args
            (('zaphod', 42),),  # one arg that is a tuple
        ]
    )
    def test_error_initial_attrs(self, args):
        """Test initial attributes of Error."""

        # Execute the code to be tested
        exc = MyError(*args)

        assert isinstance(exc, Error)
        assert exc.args == args


class TestConnectionError(object):
    """All tests for exception class ConnectionError."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (msg, details)
            ("fake msg", ValueError("fake value error")),
            ("", None),
            (None, None),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None),
            (None, 'details'),
            ('msg', 'details'),
        ]
    )
    def test_connectionerror_initial_attrs(self, arg_names, args):
        """Test initial attributes of ConnectionError."""

        msg, details = args
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = ConnectionError(*posargs, **kwargs)

        assert isinstance(exc, Error)
        assert len(exc.args) == 1
        assert exc.args[0] == msg
        assert exc.details == details

    @pytest.mark.parametrize(
        "msg, details", [
            ("fake msg", ValueError("fake value error")),
            ("", None),
            (None, None),
        ]
    )
    def test_connectionerror_repr(self, msg, details):
        """All tests for ConnectionError.__repr__()."""

        exc = ConnectionError(msg, details)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg, details", [
            ("fake msg", ValueError("fake value error")),
            ("", None),
            (None, None),
        ]
    )
    def test_connectionerror_str(self, msg, details):
        """All tests for ConnectionError.__str__()."""

        exc = ConnectionError(msg, details)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg, details", [
            ("fake msg", ValueError("fake value error")),
            ("", None),
            (None, None),
        ]
    )
    def test_connectionerror_str_def(self, msg, details):
        """All tests for ConnectionError.str_def()."""

        exc = ConnectionError(msg, details)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0


class TestConnectTimeout(object):
    """All tests for exception class ConnectTimeout."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (msg, details, connect_timeout, connect_retries)
            ("fake msg", ValueError("fake value error"), 30, 3),
            ("", None, 30, 3),
            (None, None, 0, 0),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None, None, None),
            ('msg', 'details', 'connect_timeout', 'connect_retries'),
        ]
    )
    def test_connecttimeout_initial_attrs(self, arg_names, args):
        """Test initial attributes of ConnectTimeout."""

        msg, details, connect_timeout, connect_retries = args
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = ConnectTimeout(*posargs, **kwargs)

        assert isinstance(exc, ConnectionError)
        assert len(exc.args) == 1
        assert exc.args[0] == msg
        assert exc.details == details
        assert exc.connect_timeout == connect_timeout
        assert exc.connect_retries == connect_retries

    @pytest.mark.parametrize(
        "msg, details, connect_timeout, connect_retries", [
            ("fake msg", ValueError("fake value error"), 30, 3),
            ("", None, 30, 3),
            (None, None, 0, 0),
        ]
    )
    def test_connecttimeout_repr(
            self, msg, details, connect_timeout, connect_retries):
        """All tests for ConnectTimeout.__repr__()."""

        exc = ConnectTimeout(msg, details, connect_timeout, connect_retries)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg, details, connect_timeout, connect_retries", [
            ("fake msg", ValueError("fake value error"), 30, 3),
            ("", None, 30, 3),
            (None, None, 0, 0),
        ]
    )
    def test_connecttimeout_str(
            self, msg, details, connect_timeout, connect_retries):
        """All tests for ConnectTimeout.__str__()."""

        exc = ConnectTimeout(msg, details, connect_timeout, connect_retries)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg, details, connect_timeout, connect_retries", [
            ("fake msg", ValueError("fake value error"), 30, 3),
            ("", None, 30, 3),
            (None, None, 0, 0),
        ]
    )
    def test_connecttimeout_str_def(
            self, msg, details, connect_timeout, connect_retries):
        """All tests for ConnectTimeout.str_def()."""

        exc = ConnectTimeout(msg, details, connect_timeout, connect_retries)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0
        assert str_def.find(' connect_timeout={!r};'.
                            format(connect_timeout)) >= 0
        assert str_def.find(' connect_retries={!r};'.
                            format(connect_retries)) >= 0


class TestReadTimeout(object):
    """All tests for exception class ReadTimeout."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (msg, details, read_timeout, read_retries)
            ("fake msg", ValueError("fake value error"), 30, 3),
            ("", None, 30, 3),
            (None, None, 0, 0),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None, None, None),
            ('msg', 'details', 'read_timeout', 'read_retries'),
        ]
    )
    def test_readtimeout_initial_attrs(self, arg_names, args):
        """Test initial attributes of ReadTimeout."""

        msg, details, read_timeout, read_retries = args
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = ReadTimeout(*posargs, **kwargs)

        assert isinstance(exc, ConnectionError)
        assert len(exc.args) == 1
        assert exc.args[0] == msg
        assert exc.details == details
        assert exc.read_timeout == read_timeout
        assert exc.read_retries == read_retries

    @pytest.mark.parametrize(
        "msg, details, read_timeout, read_retries", [
            ("fake msg", ValueError("fake value error"), 30, 3),
            ("", None, 30, 3),
            (None, None, 0, 0),
        ]
    )
    def test_readtimeout_repr(
            self, msg, details, read_timeout, read_retries):
        """All tests for ReadTimeout.__repr__()."""

        exc = ReadTimeout(msg, details, read_timeout, read_retries)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg, details, read_timeout, read_retries", [
            ("fake msg", ValueError("fake value error"), 30, 3),
            ("", None, 30, 3),
            (None, None, 0, 0),
        ]
    )
    def test_readtimeout_str(
            self, msg, details, read_timeout, read_retries):
        """All tests for ReadTimeout.__str__()."""

        exc = ReadTimeout(msg, details, read_timeout, read_retries)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg, details, read_timeout, read_retries", [
            ("fake msg", ValueError("fake value error"), 30, 3),
            ("", None, 30, 3),
            (None, None, 0, 0),
        ]
    )
    def test_readtimeout_str_def(
            self, msg, details, read_timeout, read_retries):
        """All tests for ReadTimeout.str_def()."""

        exc = ReadTimeout(msg, details, read_timeout, read_retries)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0
        assert str_def.find(' read_timeout={!r};'.format(read_timeout)) >= 0
        assert str_def.find(' read_retries={!r};'.format(read_retries)) >= 0


class TestRetriesExceeded(object):
    """All tests for exception class RetriesExceeded."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (msg, details, connect_retries)
            ("fake msg", ValueError("fake value error"), 3),
            ("", None, 3),
            (None, None, 0),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None, None),
            ('msg', 'details', 'connect_retries'),
        ]
    )
    def test_retriesexceeded_initial_attrs(self, arg_names, args):
        """Test initial attributes of RetriesExceeded."""

        msg, details, connect_retries = args
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = RetriesExceeded(*posargs, **kwargs)

        assert isinstance(exc, ConnectionError)
        assert len(exc.args) == 1
        assert exc.args[0] == msg
        assert exc.details == details
        assert exc.connect_retries == connect_retries

    @pytest.mark.parametrize(
        "msg, details, connect_retries", [
            ("fake msg", ValueError("fake value error"), 3),
            ("", None, 3),
            (None, None, 0),
        ]
    )
    def test_retriesexceeded_repr(
            self, msg, details, connect_retries):
        """All tests for RetriesExceeded.__repr__()."""

        exc = RetriesExceeded(msg, details, connect_retries)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg, details, connect_retries", [
            ("fake msg", ValueError("fake value error"), 3),
            ("", None, 3),
            (None, None, 0),
        ]
    )
    def test_retriesexceeded_str(
            self, msg, details, connect_retries):
        """All tests for RetriesExceeded.__str__()."""

        exc = RetriesExceeded(msg, details, connect_retries)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg, details, connect_retries", [
            ("fake msg", ValueError("fake value error"), 3),
            ("", None, 3),
            (None, None, 0),
        ]
    )
    def test_retriesexceeded_str_def(
            self, msg, details, connect_retries):
        """All tests for RetriesExceeded.str_def()."""

        exc = RetriesExceeded(msg, details, connect_retries)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0
        assert str_def.find(' connect_retries={!r};'.
                            format(connect_retries)) >= 0


class TestClientAuthError(object):
    """All tests for exception class ClientAuthError."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (msg,)
            ("fake msg",),
            (None,),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None,),
            ('msg',),
        ]
    )
    def test_clientautherror_initial_attrs(self, arg_names, args):
        """Test initial attributes of ClientAuthError."""

        msg = args[0]
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = ClientAuthError(*posargs, **kwargs)

        assert isinstance(exc, AuthError)
        assert len(exc.args) == 1
        assert exc.args[0] == msg

    @pytest.mark.parametrize(
        "msg", [
            ("fake msg"),
            (""),
            (None),
        ]
    )
    def test_clientautherror_repr(self, msg):
        """All tests for ClientAuthError.__repr__()."""

        exc = ClientAuthError(msg)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg", [
            ("fake msg"),
            (""),
            (None),
        ]
    )
    def test_clientautherror_str(self, msg):
        """All tests for ClientAuthError.__str__()."""

        exc = ClientAuthError(msg)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg", [
            ("fake msg"),
            (""),
            (None),
        ]
    )
    def test_clientautherror_str_def(self, msg):
        """All tests for ClientAuthError.str_def()."""

        exc = ClientAuthError(msg)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0


class TestServerAuthError(object):
    """All tests for exception class ServerAuthError."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (msg, details)
            ("fake msg", HTTPError(HTTP_ERROR_1)),
            ("", HTTPError(HTTP_ERROR_1)),
            (None, HTTPError(HTTP_ERROR_1)),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None),
            (None, 'details'),
            ('msg', 'details'),
        ]
    )
    def test_serverautherror_initial_attrs(self, arg_names, args):
        """Test initial attributes of ServerAuthError."""

        msg, details = args
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = ServerAuthError(*posargs, **kwargs)

        assert isinstance(exc, AuthError)
        assert len(exc.args) == 1
        assert exc.args[0] == msg
        assert exc.details == details

    @pytest.mark.parametrize(
        "msg, details", [
            ("fake msg", HTTPError(HTTP_ERROR_1)),
            ("", HTTPError(HTTP_ERROR_1)),
            (None, HTTPError(HTTP_ERROR_1)),
        ]
    )
    def test_serverautherror_repr(self, msg, details):
        """All tests for ServerAuthError.__repr__()."""

        exc = ServerAuthError(msg, details)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg, details", [
            ("fake msg", HTTPError(HTTP_ERROR_1)),
            ("", HTTPError(HTTP_ERROR_1)),
            (None, HTTPError(HTTP_ERROR_1)),
        ]
    )
    def test_serverautherror_str(self, msg, details):
        """All tests for ServerAuthError.__str__()."""

        exc = ServerAuthError(msg, details)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg, details", [
            ("fake msg", HTTPError(HTTP_ERROR_1)),
            ("", HTTPError(HTTP_ERROR_1)),
            (None, HTTPError(HTTP_ERROR_1)),
        ]
    )
    def test_serverautherror_str_def(self, msg, details):
        """All tests for ServerAuthError.str_def()."""

        exc = ServerAuthError(msg, details)

        classname = exc.__class__.__name__
        request_method = details.request_method
        request_uri = details.request_uri
        http_status = details.http_status
        reason = details.reason

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' request_method={!r};'.
                            format(request_method)) >= 0
        assert str_def.find(' request_uri={!r};'.format(request_uri)) >= 0
        assert str_def.find(' http_status={!r};'.format(http_status)) >= 0
        assert str_def.find(' reason={!r};'.format(reason)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0


class TestParseError(object):
    """All tests for exception class ParseError."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args, exp_line, exp_column", [
            # args: (msg,)
            (("Bla: line 42 column 7 (char 6)",), 42, 7),
            (("Bla line 42 column 7 (char 6)",), None, None),
            (("Bla: line 42, column 7 (char 6)",), None, None),
            (("Bla: line 42 column 7, (char 6)",), None, None),
            (("",), None, None),
            ((None,), None, None),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None,),
            ('msg',),
        ]
    )
    def test_parseerror_initial_attrs(
            self, arg_names, args, exp_line, exp_column):
        """Test initial attributes of ParseError."""

        msg = args[0]
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = ParseError(*posargs, **kwargs)

        assert isinstance(exc, Error)
        assert len(exc.args) == 1
        assert exc.args[0] == msg
        assert exc.line == exp_line
        assert exc.column == exp_column

    @pytest.mark.parametrize(
        "msg", [
            ("Bla: line 42 column 7 (char 6)"),
            ("fake msg"),
            (""),
            (None),
        ]
    )
    def test_parseerror_repr(self, msg):
        """All tests for ParseError.__repr__()."""

        exc = ParseError(msg)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg", [
            ("Bla: line 42 column 7 (char 6)"),
            ("fake msg"),
            (""),
            (None),
        ]
    )
    def test_parseerror_str(self, msg):
        """All tests for ParseError.__str__()."""

        exc = ParseError(msg)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg", [
            ("Bla: line 42 column 7 (char 6)"),
            ("fake msg"),
            (""),
            (None),
        ]
    )
    def test_parseerror_str_def(self, msg):
        """All tests for ParseError.str_def()."""

        exc = ParseError(msg)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' line={!r};'.format(exc.line)) >= 0
        assert str_def.find(' column={!r};'.format(exc.column)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0


class TestVersionError(object):
    """All tests for exception class VersionError."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (msg, min_api_version, api_version)
            ("fake msg", (2, 1), (1, 2)),
            ("", (2, 1), (1, 2)),
            (None, (2, 1), (1, 2)),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None, None),
            ('msg', 'min_api_version', 'api_version'),
        ]
    )
    def test_versionerror_initial_attrs(self, arg_names, args):
        """Test initial attributes of VersionError."""

        msg, min_api_version, api_version = args
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = VersionError(*posargs, **kwargs)

        assert isinstance(exc, Error)
        assert len(exc.args) == 1
        assert exc.args[0] == msg
        assert exc.min_api_version == min_api_version
        assert exc.api_version == api_version

    @pytest.mark.parametrize(
        "msg, min_api_version, api_version", [
            ("fake msg", (2, 1), (1, 2)),
            ("", (2, 1), (1, 2)),
            (None, (2, 1), (1, 2)),
        ]
    )
    def test_versionerror_repr(
            self, msg, min_api_version, api_version):
        """All tests for VersionError.__repr__()."""

        exc = VersionError(msg, min_api_version, api_version)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg, min_api_version, api_version", [
            ("fake msg", (2, 1), (1, 2)),
            ("", (2, 1), (1, 2)),
            (None, (2, 1), (1, 2)),
        ]
    )
    def test_versionerror_str(
            self, msg, min_api_version, api_version):
        """All tests for VersionError.__str__()."""

        exc = VersionError(msg, min_api_version, api_version)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg, min_api_version, api_version", [
            ("fake msg", (2, 1), (1, 2)),
            ("", (2, 1), (1, 2)),
            (None, (2, 1), (1, 2)),
        ]
    )
    def test_versionerror_str_def(
            self, msg, min_api_version, api_version):
        """All tests for VersionError.str_def()."""

        exc = VersionError(msg, min_api_version, api_version)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0
        assert str_def.find(' min_api_version={!r};'.
                            format(min_api_version)) >= 0
        assert str_def.find(' api_version={!r};'.
                            format(api_version)) >= 0


class TestHTTPError(object):
    """All tests for exception class HTTPError."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (body,)
            (HTTP_ERROR_1,),
            (HTTP_ERROR_2,),
            (HTTP_ERROR_3,),
            (HTTP_ERROR_4,),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None,),
            ('body',),
        ]
    )
    def test_httperror_initial_attrs(self, arg_names, args):
        """Test initial attributes of HTTPError."""

        body = args[0]
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = HTTPError(*posargs, **kwargs)

        assert isinstance(exc, Error)
        assert len(exc.args) == 1
        assert exc.args[0] == body.get('message', None)
        assert exc.http_status == body.get('http-status', None)
        assert exc.reason == body.get('reason', None)
        assert exc.message == body.get('message', None)
        assert exc.request_method == body.get('request-method', None)
        assert exc.request_uri == body.get('request-uri', None)
        assert exc.request_query_parms == body.get('request-query-parms', None)
        assert exc.request_headers == body.get('request-headers', None)
        assert exc.request_authenticated_as == \
            body.get('request-authenticated-as', None)
        assert exc.request_body == body.get('request-body', None)
        assert exc.request_body_as_string == \
            body.get('request-body-as-string', None)
        assert exc.request_body_as_string_partial == \
            body.get('request-body-as-string-partial', None)
        assert exc.stack == body.get('stack', None)
        assert exc.error_details == body.get('error-details', None)

    @pytest.mark.parametrize(
        "body", [
            HTTP_ERROR_1,
        ]
    )
    def test_httperror_repr(self, body):
        """All tests for HTTPError.__repr__()."""

        exc = HTTPError(body)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "body", [
            HTTP_ERROR_1,
        ]
    )
    def test_httperror_str(self, body):
        """All tests for HTTPError.__str__()."""

        exc = HTTPError(body)

        exp_str = "{http-status},{reason}: {message} [{request-method} "\
                  "{request-uri}]".format(**body)

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "body", [
            HTTP_ERROR_1,
        ]
    )
    def test_httperror_str_def(self, body):
        """All tests for HTTPError.str_def()."""

        exc = HTTPError(body)

        classname = exc.__class__.__name__
        request_method = exc.request_method
        request_uri = exc.request_uri
        http_status = exc.http_status
        reason = exc.reason
        msg = exc.message

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' request_method={!r};'.
                            format(request_method)) >= 0
        assert str_def.find(' request_uri={!r};'.format(request_uri)) >= 0
        assert str_def.find(' http_status={!r};'.format(http_status)) >= 0
        assert str_def.find(' reason={!r};'.format(reason)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0


class TestOperationTimeout(object):
    """All tests for exception class OperationTimeout."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (msg, operation_timeout)
            ("fake msg", 3),
            ("", 3),
            (None, 0),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None),
            ('msg', 'operation_timeout'),
        ]
    )
    def test_operationtimeout_initial_attrs(self, arg_names, args):
        """Test initial attributes of OperationTimeout."""

        msg, operation_timeout = args
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = OperationTimeout(*posargs, **kwargs)

        assert isinstance(exc, Error)
        assert len(exc.args) == 1
        assert exc.args[0] == msg
        assert exc.operation_timeout == operation_timeout

    @pytest.mark.parametrize(
        "msg, operation_timeout", [
            ("fake msg", 3),
            ("", 3),
            (None, 0),
        ]
    )
    def test_operationtimeout_repr(
            self, msg, operation_timeout):
        """All tests for OperationTimeout.__repr__()."""

        exc = OperationTimeout(msg, operation_timeout)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg, operation_timeout", [
            ("fake msg", 3),
            ("", 3),
            (None, 0),
        ]
    )
    def test_operationtimeout_str(
            self, msg, operation_timeout):
        """All tests for OperationTimeout.__str__()."""

        exc = OperationTimeout(msg, operation_timeout)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg, operation_timeout", [
            ("fake msg", 3),
            ("", 3),
            (None, 0),
        ]
    )
    def test_operationtimeout_str_def(
            self, msg, operation_timeout):
        """All tests for OperationTimeout.str_def()."""

        exc = OperationTimeout(msg, operation_timeout)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0
        assert str_def.find(' operation_timeout={!r};'.
                            format(operation_timeout)) >= 0


class TestStatusTimeout(object):
    """All tests for exception class StatusTimeout."""

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # (msg, actual_status, desired_statuses, status_timeout)
            ("fake msg", 'foo off', ['foo on', 'bla'], 3),
            ("", '', [], 3),
            (None, None, [], 0),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None, None, None),
            ('msg', 'actual_status', 'desired_statuses', 'status_timeout'),
        ]
    )
    def test_statustimeout_initial_attrs(self, arg_names, args):
        """Test initial attributes of StatusTimeout."""

        msg, actual_status, desired_statuses, status_timeout = args
        posargs, kwargs = func_args(args, arg_names)

        # Execute the code to be tested
        exc = StatusTimeout(*posargs, **kwargs)

        assert isinstance(exc, Error)
        assert len(exc.args) == 1
        assert exc.args[0] == msg
        assert exc.actual_status == actual_status
        assert exc.desired_statuses == desired_statuses
        assert exc.status_timeout == status_timeout

    @pytest.mark.parametrize(
        "msg, actual_status, desired_statuses, status_timeout", [
            ("fake msg", 'foo off', ['foo on', 'bla'], 3),
            ("", '', [], 3),
            (None, None, [], 0),
        ]
    )
    def test_statustimeout_repr(
            self, msg, actual_status, desired_statuses, status_timeout):
        """All tests for StatusTimeout.__repr__()."""

        exc = StatusTimeout(
            msg, actual_status, desired_statuses, status_timeout)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "msg, actual_status, desired_statuses, status_timeout", [
            ("fake msg", 'foo off', ['foo on', 'bla'], 3),
            ("", '', [], 3),
            (None, None, [], 0),
        ]
    )
    def test_statustimeout_str(
            self, msg, actual_status, desired_statuses, status_timeout):
        """All tests for StatusTimeout.__str__()."""

        exc = StatusTimeout(
            msg, actual_status, desired_statuses, status_timeout)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "msg, actual_status, desired_statuses, status_timeout", [
            ("fake msg", 'foo off', ['foo on', 'bla'], 3),
            ("", '', [], 3),
            (None, None, [], 0),
        ]
    )
    def test_statustimeout_str_def(
            self, msg, actual_status, desired_statuses, status_timeout):
        """All tests for StatusTimeout.str_def()."""

        exc = StatusTimeout(
            msg, actual_status, desired_statuses, status_timeout)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' message={!r};'.format(msg)) >= 0
        assert str_def.find(' actual_status={!r};'.
                            format(actual_status)) >= 0
        assert str_def.find(' desired_statuses={!r};'.
                            format(desired_statuses)) >= 0
        assert str_def.find(' status_timeout={!r};'.
                            format(status_timeout)) >= 0


class TestNoUniqueMatch(object):
    """All tests for exception class NoUniqueMatch."""

    def setup_method(self):
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

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # args: (filter_args,) - manager, resources are added dynamically
            ({'type': 'osa', 'status': 'active'},),
            ({},),
            (None,),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None, None),
            ('filter_args', 'manager', 'resources'),
        ]
    )
    def test_nouniquematch_initial_attrs(self, arg_names, args):
        """Test initial attributes of NoUniqueMatch."""

        filter_args = args[0]

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters
        resources = manager.list()
        resource_uris = [r.uri for r in resources]

        _args = list(args)
        _args.append(manager)
        _args.append(resources)

        posargs, kwargs = func_args(_args, arg_names)

        # Execute the code to be tested
        exc = NoUniqueMatch(*posargs, **kwargs)

        assert isinstance(exc, Error)
        assert len(exc.args) == 1
        assert isinstance(exc.args[0], six.string_types)
        # auto-generated message, we don't expect a particular value
        assert exc.filter_args == filter_args
        assert exc.manager == manager
        assert exc.resources == resources
        assert exc.resource_uris == resource_uris

    @pytest.mark.parametrize(
        "filter_args", [
            {'type': 'osa', 'status': 'active'},
        ]
    )
    def test_nouniquematch_repr(self, filter_args):
        """All tests for NoUniqueMatch.__repr__()."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters
        resources = manager.list()

        exc = NoUniqueMatch(filter_args, manager, resources)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "filter_args", [
            {'type': 'osa', 'status': 'active'},
        ]
    )
    def test_nouniquematch_str(self, filter_args):
        """All tests for NoUniqueMatch.__str__()."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters
        resources = manager.list()

        exc = NoUniqueMatch(filter_args, manager, resources)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "filter_args", [
            {'type': 'osa', 'status': 'active'},
        ]
    )
    def test_nouniquematch_str_def(self, filter_args):
        """All tests for NoUniqueMatch.str_def()."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters
        resources = manager.list()

        exc = NoUniqueMatch(filter_args, manager, resources)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' resource_classname={!r};'.
                            format(manager.resource_class.__name__)) >= 0
        assert str_def.find(' filter_args={!r};'.format(filter_args)) >= 0
        assert str_def.find(' parent_classname={!r};'.
                            format(manager.parent.__class__.__name__)) >= 0
        assert str_def.find(' parent_name={!r};'.
                            format(manager.parent.name)) >= 0
        assert str_def.find(' message=') >= 0


class TestNotFound(object):
    """All tests for exception class NotFound."""

    def setup_method(self):
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
            'status': 'inactive',
            'type': 'osd',
        })
        self.client = Client(self.session)

    @pytest.mark.parametrize(
        # Input and expected arguments.
        "args", [
            # args: (filter_args,) - manager is added dynamically
            ({'type': 'osa', 'status': 'active'},),
            ({},),
            (None,),
        ]
    )
    @pytest.mark.parametrize(
        # Whether each input arg is passed as pos.arg (None) or keyword arg
        # (arg name), or is defaulted (omitted from right).
        "arg_names", [
            (None, None),
            ('filter_args', 'manager'),
        ]
    )
    def test_notfound_initial_attrs(self, arg_names, args):
        """Test initial attributes of NotFound."""

        filter_args = args[0]

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters

        _args = list(args)
        _args.append(manager)

        posargs, kwargs = func_args(_args, arg_names)

        # Execute the code to be tested
        exc = NotFound(*posargs, **kwargs)

        assert isinstance(exc, Error)
        assert len(exc.args) == 1
        assert isinstance(exc.args[0], six.string_types)
        # auto-generated message, we don't expect a particular value
        assert exc.filter_args == filter_args
        assert exc.manager == manager

    @pytest.mark.parametrize(
        "filter_args", [
            {'type': 'osa', 'status': 'active'},
        ]
    )
    def test_notfound_repr(self, filter_args):
        """All tests for NotFound.__repr__()."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters

        exc = NotFound(filter_args, manager)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(r'^{}\s*\(.*\)$'.format(classname), repr_str)

    @pytest.mark.parametrize(
        "filter_args", [
            {'type': 'osa', 'status': 'active'},
        ]
    )
    def test_notfound_str(self, filter_args):
        """All tests for NotFound.__str__()."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters

        exc = NotFound(filter_args, manager)

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    @pytest.mark.parametrize(
        "filter_args", [
            {'type': 'osa', 'status': 'active'},
        ]
    )
    def test_notfound_str_def(self, filter_args):
        """All tests for NotFound.str_def()."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters

        exc = NotFound(filter_args, manager)

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(' classname={!r};'.format(classname)) >= 0
        assert str_def.find(' resource_classname={!r};'.
                            format(manager.resource_class.__name__)) >= 0
        assert str_def.find(' filter_args={!r};'.format(filter_args)) >= 0
        assert str_def.find(' parent_classname={!r};'.
                            format(manager.parent.__class__.__name__)) >= 0
        assert str_def.find(' parent_name={!r};'.
                            format(manager.parent.name)) >= 0
        assert str_def.find(' message=') >= 0
