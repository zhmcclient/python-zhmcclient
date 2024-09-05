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
Unit tests for _exceptions module.
"""


import re
import pytest

from zhmcclient import Client, Adapter
# Import the exceptions, same order as in _exceptions.py
from zhmcclient import (
    Error,
    # ConnectionError - see below
    ConnectTimeout, ReadTimeout,
    RetriesExceeded, AuthError, ClientAuthError,
    ServerAuthError, ParseError, VersionError, HTTPError,
    OperationTimeout, StatusTimeout, NoUniqueMatch, NotFound,
    MetricsResourceNotFound,
    # NotificationError - base class, not raised
    NotificationJMSError, NotificationParseError,
    NotificationConnectionError, NotificationSubscriptionError,
    SubscriptionNotFound, ConsistencyError,
    CeasedExistence,
    # OSConsoleError - base class, not raised
    OSConsoleConnectedError,
    OSConsoleNotConnectedError, OSConsoleWebSocketError,
    OSConsoleAuthError,
)
from zhmcclient import ConnectionError  # pylint: disable=redefined-builtin
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


@pytest.mark.parametrize(
    "exc_class", [
        ConsistencyError,
        NotificationConnectionError,
        NotificationSubscriptionError,
        SubscriptionNotFound,
        OSConsoleConnectedError,
        OSConsoleNotConnectedError,
        OSConsoleWebSocketError,
        OSConsoleAuthError,
    ]
)
def test_simple_exc(exc_class):
    """Test a simple exception class that has only a message argument"""
    msg = 'bla'
    exc = exc_class(msg)

    act_msg = str(exc.args[0])

    assert act_msg == msg


class MyError(Error):
    # pylint: disable=abstract-method
    """
    Concrete class to get instances of abstract base class ``Error``.

    Because ``Error`` is an abstract base class, we use instances of this
    class instead, for testing.
    """
    pass


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
def test_error_initial_attrs(args):
    """
    Test initial attributes of Error.
    """

    # Execute the code to be tested
    exc = MyError(*args)

    assert isinstance(exc, Error)
    assert exc.args == args


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
def test_connectionerror_initial_attrs(arg_names, args):
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
def test_connectionerror_repr(msg, details):
    """All tests for ConnectionError.__repr__()."""

    exc = ConnectionError(msg, details)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, details", [
        ("fake msg", ValueError("fake value error")),
        ("", None),
        (None, None),
    ]
)
def test_connectionerror_str(msg, details):
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
def test_connectionerror_str_def(msg, details):
    """All tests for ConnectionError.str_def()."""

    exc = ConnectionError(msg, details)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0


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
def test_connecttimeout_initial_attrs(arg_names, args):
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
        msg, details, connect_timeout, connect_retries):
    """All tests for ConnectTimeout.__repr__()."""

    exc = ConnectTimeout(msg, details, connect_timeout, connect_retries)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, details, connect_timeout, connect_retries", [
        ("fake msg", ValueError("fake value error"), 30, 3),
        ("", None, 30, 3),
        (None, None, 0, 0),
    ]
)
def test_connecttimeout_str(
        msg, details, connect_timeout, connect_retries):
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
        msg, details, connect_timeout, connect_retries):
    """All tests for ConnectTimeout.str_def()."""

    exc = ConnectTimeout(msg, details, connect_timeout, connect_retries)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0
    assert str_def.find(f' connect_timeout={connect_timeout!r};') >= 0
    assert str_def.find(f' connect_retries={connect_retries!r};') >= 0


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
def test_readtimeout_initial_attrs(arg_names, args):
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
def test_readtimeout_repr(msg, details, read_timeout, read_retries):
    """All tests for ReadTimeout.__repr__()."""

    exc = ReadTimeout(msg, details, read_timeout, read_retries)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, details, read_timeout, read_retries", [
        ("fake msg", ValueError("fake value error"), 30, 3),
        ("", None, 30, 3),
        (None, None, 0, 0),
    ]
)
def test_readtimeout_str(msg, details, read_timeout, read_retries):
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
def test_readtimeout_str_def(msg, details, read_timeout, read_retries):
    """All tests for ReadTimeout.str_def()."""

    exc = ReadTimeout(msg, details, read_timeout, read_retries)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0
    assert str_def.find(f' read_timeout={read_timeout!r};') >= 0
    assert str_def.find(f' read_retries={read_retries!r};') >= 0


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
def test_retriesexceeded_initial_attrs(arg_names, args):
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
def test_retriesexceeded_repr(msg, details, connect_retries):
    """All tests for RetriesExceeded.__repr__()."""

    exc = RetriesExceeded(msg, details, connect_retries)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, details, connect_retries", [
        ("fake msg", ValueError("fake value error"), 3),
        ("", None, 3),
        (None, None, 0),
    ]
)
def test_retriesexceeded_str(msg, details, connect_retries):
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
def test_retriesexceeded_str_def(msg, details, connect_retries):
    """All tests for RetriesExceeded.str_def()."""

    exc = RetriesExceeded(msg, details, connect_retries)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0
    assert str_def.find(f' connect_retries={connect_retries!r};') >= 0


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
def test_clientautherror_initial_attrs(arg_names, args):
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
def test_clientautherror_repr(msg):
    """All tests for ClientAuthError.__repr__()."""

    exc = ClientAuthError(msg)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg", [
        ("fake msg"),
        (""),
        (None),
    ]
)
def test_clientautherror_str(msg):
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
def test_clientautherror_str_def(msg):
    """All tests for ClientAuthError.str_def()."""

    exc = ClientAuthError(msg)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0


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
def test_serverautherror_initial_attrs(arg_names, args):
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
def test_serverautherror_repr(msg, details):
    """All tests for ServerAuthError.__repr__()."""

    exc = ServerAuthError(msg, details)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, details", [
        ("fake msg", HTTPError(HTTP_ERROR_1)),
        ("", HTTPError(HTTP_ERROR_1)),
        (None, HTTPError(HTTP_ERROR_1)),
    ]
)
def test_serverautherror_str(msg, details):
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
def test_serverautherror_str_def(msg, details):
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
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' request_method={request_method!r};') >= 0
    assert str_def.find(f' request_uri={request_uri!r};') >= 0
    assert str_def.find(f' http_status={http_status!r};') >= 0
    assert str_def.find(f' reason={reason!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0


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
def test_parseerror_initial_attrs(arg_names, args, exp_line, exp_column):
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
def test_parseerror_repr(msg):
    """All tests for ParseError.__repr__()."""

    exc = ParseError(msg)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg", [
        ("Bla: line 42 column 7 (char 6)"),
        ("fake msg"),
        (""),
        (None),
    ]
)
def test_parseerror_str(msg):
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
def test_parseerror_str_def(msg):
    """All tests for ParseError.str_def()."""

    exc = ParseError(msg)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' line={exc.line!r};') >= 0
    assert str_def.find(f' column={exc.column!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0


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
def test_versionerror_initial_attrs(arg_names, args):
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
def test_versionerror_repr(msg, min_api_version, api_version):
    """All tests for VersionError.__repr__()."""

    exc = VersionError(msg, min_api_version, api_version)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, min_api_version, api_version", [
        ("fake msg", (2, 1), (1, 2)),
        ("", (2, 1), (1, 2)),
        (None, (2, 1), (1, 2)),
    ]
)
def test_versionerror_str(msg, min_api_version, api_version):
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
def test_versionerror_str_def(msg, min_api_version, api_version):
    """All tests for VersionError.str_def()."""

    exc = VersionError(msg, min_api_version, api_version)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0
    assert str_def.find(f' min_api_version={min_api_version!r};') >= 0
    assert str_def.find(f' api_version={api_version!r};') >= 0


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
def test_httperror_initial_attrs(arg_names, args):
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
def test_httperror_repr(body):
    """All tests for HTTPError.__repr__()."""

    exc = HTTPError(body)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "body", [
        HTTP_ERROR_1,
    ]
)
def test_httperror_str(body):
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
def test_httperror_str_def(body):
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
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' request_method={request_method!r};') >= 0
    assert str_def.find(f' request_uri={request_uri!r};') >= 0
    assert str_def.find(f' http_status={http_status!r};') >= 0
    assert str_def.find(f' reason={reason!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0


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
def test_operationtimeout_initial_attrs(arg_names, args):
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
def test_operationtimeout_repr(msg, operation_timeout):
    """All tests for OperationTimeout.__repr__()."""

    exc = OperationTimeout(msg, operation_timeout)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, operation_timeout", [
        ("fake msg", 3),
        ("", 3),
        (None, 0),
    ]
)
def test_operationtimeout_str(msg, operation_timeout):
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
def test_operationtimeout_str_def(msg, operation_timeout):
    """All tests for OperationTimeout.str_def()."""

    exc = OperationTimeout(msg, operation_timeout)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0
    assert str_def.find(f' operation_timeout={operation_timeout!r};') >= 0


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
def test_statustimeout_initial_attrs(arg_names, args):
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
        msg, actual_status, desired_statuses, status_timeout):
    """All tests for StatusTimeout.__repr__()."""

    exc = StatusTimeout(
        msg, actual_status, desired_statuses, status_timeout)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, actual_status, desired_statuses, status_timeout", [
        ("fake msg", 'foo off', ['foo on', 'bla'], 3),
        ("", '', [], 3),
        (None, None, [], 0),
    ]
)
def test_statustimeout_str(
        msg, actual_status, desired_statuses, status_timeout):
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
        msg, actual_status, desired_statuses, status_timeout):
    """All tests for StatusTimeout.str_def()."""

    exc = StatusTimeout(
        msg, actual_status, desired_statuses, status_timeout)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0
    assert str_def.find(f' actual_status={actual_status!r};') >= 0
    assert str_def.find(f' desired_statuses={desired_statuses!r};') >= 0
    assert str_def.find(f' status_timeout={status_timeout!r};') >= 0


class TestNoUniqueMatch:
    """All tests for exception class NoUniqueMatch."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

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
        assert isinstance(exc.args[0], str)
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
        assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)

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
        assert str_def.find(f' classname={classname!r};') >= 0
        assert str_def.find(
            f' resource_classname={manager.resource_class.__name__!r};') >= 0
        assert str_def.find(f' filter_args={filter_args!r};') >= 0
        assert str_def.find(
            f' parent_classname={manager.parent.__class__.__name__!r};') >= 0
        assert str_def.find(f' parent_name={manager.parent.name!r};') >= 0
        assert str_def.find(' message=') >= 0


class AddManagerIndicator:
    # pylint: disable=too-few-public-methods
    """
    Indicator class for the 'manager' argument of some exceptions.

    If an object of this class is specified in a testcase, it is replaced by an
    actual manager object in the testcase setup.
    """
    pass


# Indicator for the 'manager' argument of of some exceptions.
ADD_MANAGER = AddManagerIndicator()


TESTCASES_NOTFOUND_INITIAL_ATTRS = [
    # Testcases for test_notfound_initial_attrs()
    #
    # Each list item is a testcase with the following tuple items:
    # * desc (str) - Testcase description.
    # * input_args (list) - Positional arguments for NotFound() init.
    # * input_kwargs (dict) - Keyword arguments for NotFound() init.
    # * exp_attrs (dict) - Expected attributes of the NotFound() object.
    # * exp_message_pattern (str) - Regexp pattern to match expected exception
    #   message, or None to not perform a match.
    #
    # The tests all lead to a successful creation of a NotFound object.
    # In all input and expected items, ADD_MANAGER can be used to
    # specify the value for the 'manager' argument or attribute; it will
    # be replaced with a manager object.

    (
        "message as positional arg",
        [None, None, "foo"],
        dict(),
        dict(
            filter_args=None,
            manager=None,
        ),
        r"^foo$"
    ),
    (
        "message as keyword arg",
        [],
        dict(
            message="foo",
        ),
        dict(
            filter_args=None,
            manager=None,
        ),
        r"^foo$"
    ),
    (
        "manager but no filter_args as positional arg",
        [None, ADD_MANAGER],
        dict(),
        dict(
            filter_args=None,
            manager=ADD_MANAGER,
        ),
        r"^Could not find Adapter using filter arguments None in Cpc "
    ),
    (
        "manager but no filter_args as keyword arg",
        [],
        dict(
            manager=ADD_MANAGER,
        ),
        dict(
            filter_args=None,
            manager=ADD_MANAGER,
        ),
        r"^Could not find Adapter using filter arguments None in Cpc "
    ),
    (
        "manager and one filter_arg as positional arg",
        [{"adapter-id": "1c0"}, ADD_MANAGER],
        dict(),
        dict(
            filter_args={"adapter-id": "1c0"},
            manager=ADD_MANAGER,
        ),
        r"^Could not find Adapter using filter arguments {'adapter-id': '1c0'} "
        r"in Cpc "
    ),
    (
        "manager and one filter_arg as keyword arg",
        [],
        dict(
            filter_args={"adapter-id": "1c0"},
            manager=ADD_MANAGER,
        ),
        dict(
            filter_args={"adapter-id": "1c0"},
            manager=ADD_MANAGER,
        ),
        r"^Could not find Adapter using filter arguments {'adapter-id': '1c0'} "
        r"in Cpc "
    ),
    (
        "manager and two filter_arg items as keyword arg",
        [],
        dict(
            filter_args={"adapter-id": "1c0", "name": "foo"},
            manager=ADD_MANAGER,
        ),
        dict(
            filter_args={"adapter-id": "1c0", "name": "foo"},
            manager=ADD_MANAGER,
        ),
        r"^Could not find Adapter using filter arguments "
        r".*(?=.*'adapter-id': '1c0')(?=.*'name': 'foo').* in Cpc "
    ),
    (
        "message overwrites manager/filter_arg",
        [],
        dict(
            message="foo",
            filter_args={"adapter-id": "1c0"},
            manager=ADD_MANAGER,
        ),
        dict(
            filter_args=None,
            manager=None,
        ),
        r"^foo$"
    ),
]


class TestNotFound:
    """All tests for exception class NotFound."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

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
        "desc, input_args, input_kwargs, exp_attrs, exp_message_pattern",
        TESTCASES_NOTFOUND_INITIAL_ATTRS)
    def test_notfound_initial_attrs(
            self, desc, input_args, input_kwargs, exp_attrs,
            exp_message_pattern):
        # pylint: disable=unused-argument
        """Test initial attributes of NotFound."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters

        args = []
        for value in input_args:
            if value == ADD_MANAGER:
                value = manager
            args.append(value)

        kwargs = {}
        for name, value in input_kwargs.items():
            if value == ADD_MANAGER:
                value = manager
            kwargs[name] = value

        # Execute the code to be tested
        exc = NotFound(*args, **kwargs)

        assert isinstance(exc, Error)

        # Validate exception message
        assert len(exc.args) == 1
        message = exc.args[0]
        assert isinstance(message, str)
        if exp_message_pattern:
            assert re.match(exp_message_pattern, message)

        # Validate other exception attributes
        for name, exp_value in exp_attrs.items():
            if exp_value == ADD_MANAGER:
                exp_value = manager
            assert hasattr(exc, name)
            value = getattr(exc, name)
            assert value == exp_value

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
        assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)

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
        assert str_def.find(f' classname={classname!r};') >= 0
        assert str_def.find(
            f' resource_classname={manager.resource_class.__name__!r};') >= 0
        assert str_def.find(f' filter_args={filter_args!r};') >= 0
        assert str_def.find(
            f' parent_classname={manager.parent.__class__.__name__!r};') >= 0
        assert str_def.find(f' parent_name={manager.parent.name!r};') >= 0
        assert str_def.find(' message=') >= 0


TESTCASES_MR_NOTFOUND_INITIAL_ATTRS = [
    # Testcases for test_mr_notfound_initial_attrs()
    #
    # Each list item is a testcase with the following tuple items:
    # * desc (str) - Testcase description.
    # * input_args (list) - Positional arguments for MetricsResourceNotFound()
    # * input_kwargs (dict) - Keyword arguments for MetricsResourceNotFound()
    # * exp_attrs (dict) - Expected attributes of MetricsResourceNotFound()
    # * exp_message_pattern (str) - Regexp pattern to match expected exception
    #   message, or None to not perform a match.
    #
    # The tests all lead to a successful creation of a MetricsResourceNotFound
    # object.
    # In all input and expected items, ADD_MANAGER can be used to
    # specify the value for the 'manager' argument or attribute; it will
    # be replaced with a manager object.

    # MetricsResourceNotFound init args: msg, resource_class, managers

    (
        "Positional args - just msg",
        ["foo", None, None],
        dict(),
        dict(
            resource_class=None,
            managers=None,
        ),
        r"^foo$"
    ),
    (
        "Positional args - all args",
        ["foo", Adapter, [ADD_MANAGER]],
        dict(),
        dict(
            resource_class=Adapter,
        ),
        r"^foo$"
    ),
    (
        "Keyword args - all args",
        [],
        dict(
            msg="foo",
            resource_class=Adapter,
            managers=[ADD_MANAGER]),
        dict(
            resource_class=Adapter,
        ),
        r"^foo$"
    ),
]


class TestMetricsResourceNotFound:
    """All tests for exception class MetricsResourceNotFound."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

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
        "desc, input_args, input_kwargs, exp_attrs, exp_message_pattern",
        TESTCASES_MR_NOTFOUND_INITIAL_ATTRS)
    def test_mr_notfound_initial_attrs(
            self, desc, input_args, input_kwargs, exp_attrs,
            exp_message_pattern):
        # pylint: disable=unused-argument
        """Test initial attributes of MetricsResourceNotFound."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters

        args = []
        for value in input_args:
            if isinstance(value, list) and value[0] == ADD_MANAGER:
                for i, item in enumerate(value):
                    assert item == ADD_MANAGER
                    value[i] = manager
            args.append(value)

        kwargs = {}
        for name, value in input_kwargs.items():
            if isinstance(value, list) and value[0] == ADD_MANAGER:
                for i, item in enumerate(value):
                    assert item == ADD_MANAGER
                    value[i] = manager
            kwargs[name] = value

        # Execute the code to be tested
        exc = MetricsResourceNotFound(*args, **kwargs)

        assert isinstance(exc, Error)

        # Validate exception message
        assert len(exc.args) == 1
        message = exc.args[0]
        assert isinstance(message, str)
        if exp_message_pattern:
            assert re.match(exp_message_pattern, message)

        # Validate other exception attributes
        for name, exp_value in exp_attrs.items():
            assert hasattr(exc, name)
            value = getattr(exc, name)
            if isinstance(exp_value, list) and exp_value[0] == ADD_MANAGER:
                assert len(value) == len(exp_value)
                for i, item in enumerate(exp_value):
                    assert value[i] == item
            else:
                assert value == exp_value

    def test_mr_notfound_repr(self):
        """All tests for MetricsResourceNotFound.__repr__()."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters

        exc = MetricsResourceNotFound("foo", Adapter, [manager])

        classname = exc.__class__.__name__

        # Execute the code to be tested
        repr_str = repr(exc)

        # We check the one-lined string just roughly
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)

    def test_mr_notfound_str(self):
        """All tests for MetricsResourceNotFound.__str__()."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters

        exc = MetricsResourceNotFound("foo", Adapter, [manager])

        exp_str = str(exc.args[0])

        # Execute the code to be tested
        str_str = str(exc)

        assert str_str == exp_str

    def test_mr_notfound_str_def(self):
        """All tests for MetricsResourceNotFound.str_def()."""

        cpc = self.client.cpcs.find(name='cpc_1')
        manager = cpc.adapters

        exc = MetricsResourceNotFound("foo", Adapter, [manager])

        classname = exc.__class__.__name__

        # Execute the code to be tested
        str_def = exc.str_def()

        str_def = ' ' + str_def
        assert str_def.find(f' classname={classname!r};') >= 0
        assert str_def.find(' message=') >= 0


@pytest.mark.parametrize(
    # Input and expected arguments.
    "args", [
        # (msg, jms_headers, jms_message)
        ("fake msg", dict(message='jms error msg1'), 'jms error msg2'),
    ]
)
@pytest.mark.parametrize(
    # Whether each input arg is passed as pos.arg (None) or keyword arg
    # (arg name), or is defaulted (omitted from right).
    "arg_names", [
        (None, None, None),
        ('msg', 'jms_headers', 'jms_message'),
    ]
)
def test_notijmserror_initial_attrs(arg_names, args):
    """Test initial attributes of NotificationJMSError."""

    msg, jms_headers, jms_message = args
    posargs, kwargs = func_args(args, arg_names)

    # Execute the code to be tested
    exc = NotificationJMSError(*posargs, **kwargs)

    assert isinstance(exc, Error)
    assert len(exc.args) == 1
    assert exc.args[0] == msg
    assert exc.jms_headers == jms_headers
    assert exc.jms_message == jms_message


@pytest.mark.parametrize(
    "msg, jms_headers, jms_message", [
        ("fake msg", dict(message='jms error msg1'), 'jms error msg2'),
    ]
)
def test_notijmserror_repr(msg, jms_headers, jms_message):
    """All tests for NotificationJMSError.__repr__()."""

    exc = NotificationJMSError(msg, jms_headers, jms_message)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, jms_headers, jms_message", [
        ("fake msg", dict(message='jms error msg1'), 'jms error msg2'),
    ]
)
def test_notijmserror_str(msg, jms_headers, jms_message):
    """All tests for NotificationJMSError.__str__()."""

    exc = NotificationJMSError(msg, jms_headers, jms_message)

    exp_str = str(exc.args[0])

    # Execute the code to be tested
    str_str = str(exc)

    assert str_str == exp_str


@pytest.mark.parametrize(
    "msg, jms_headers, jms_message", [
        ("fake msg", dict(message='jms error msg1'), 'jms error msg2'),
    ]
)
def test_notijmserror_str_def(msg, jms_headers, jms_message):
    """All tests for NotificationJMSError.str_def()."""

    exc = NotificationJMSError(msg, jms_headers, jms_message)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0


@pytest.mark.parametrize(
    # Input and expected arguments.
    "args", [
        # (msg, jms_message)
        ("fake msg", dict(bla='bla1')),
    ]
)
@pytest.mark.parametrize(
    # Whether each input arg is passed as pos.arg (None) or keyword arg
    # (arg name), or is defaulted (omitted from right).
    "arg_names", [
        (None, None),
        ('msg', 'jms_message'),
    ]
)
def test_notiparseerror_initial_attrs(arg_names, args):
    """Test initial attributes of NotificationParseError."""

    msg, jms_message = args
    posargs, kwargs = func_args(args, arg_names)

    # Execute the code to be tested
    exc = NotificationParseError(*posargs, **kwargs)

    assert isinstance(exc, Error)
    assert len(exc.args) == 1
    assert exc.args[0] == msg
    assert exc.jms_message == jms_message


@pytest.mark.parametrize(
    "msg, jms_message", [
        ("fake msg", dict(bla='bla1')),
    ]
)
def test_notiparseerror_repr(msg, jms_message):
    """All tests for NotificationParseError.__repr__()."""

    exc = NotificationParseError(msg, jms_message)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


@pytest.mark.parametrize(
    "msg, jms_message", [
        ("fake msg", dict(bla='bla1')),
    ]
)
def test_notiparseerror_str(msg, jms_message):
    """All tests for NotificationParseError.__str__()."""

    exc = NotificationParseError(msg, jms_message)

    exp_str = str(exc.args[0])

    # Execute the code to be tested
    str_str = str(exc)

    assert str_str == exp_str


@pytest.mark.parametrize(
    "msg, jms_message", [
        ("fake msg", dict(bla='bla1')),
    ]
)
def test_notiparseerror_str_def(msg, jms_message):
    """All tests for NotificationParseError.str_def()."""

    exc = NotificationParseError(msg, jms_message)

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(f' message={msg!r};') >= 0


TESTCASES_CEASEDEXISTENCE_INITIAL_ATTRS = [
    # Testcases for test_ceasedexistence_initial_attrs()
    #
    # Each list item is a testcase with the following tuple items:
    # * desc (str) - Testcase description.
    # * input_args (list) - Positional arguments for CeasedExistence()
    # * input_kwargs (dict) - Keyword arguments for CeasedExistence()
    # * exp_attrs (dict) - Expected attributes of CeasedExistence()
    # * exp_message_pattern (str) - Regexp pattern to match expected exception
    #   message, or None to not perform a match.
    #
    # The tests all lead to a successful creation of a CeasedExistence
    # object.
    # In all input and expected items, ADD_MANAGER can be used to
    # specify the value for the 'manager' argument or attribute; it will
    # be replaced with a manager object.

    # CeasedExistence init args: resource_uri

    (
        "Positional args",
        ["/api/foo"],
        dict(),
        dict(
            resource_uri="/api/foo",
        ),
        r"^Resource no longer exists: /api/foo$"
    ),
    (
        "Keyword args",
        [],
        dict(
            resource_uri="/api/foo",
        ),
        dict(
            resource_uri="/api/foo",
        ),
        r"^Resource no longer exists: /api/foo$"
    ),
]


@pytest.mark.parametrize(
    "desc, input_args, input_kwargs, exp_attrs, exp_message_pattern",
    TESTCASES_CEASEDEXISTENCE_INITIAL_ATTRS)
def test_ceasedexistence_initial_attrs(
        desc, input_args, input_kwargs, exp_attrs,
        exp_message_pattern):
    # pylint: disable=unused-argument
    """Test initial attributes of CeasedExistence."""

    # Execute the code to be tested
    exc = CeasedExistence(*input_args, **input_kwargs)

    assert isinstance(exc, Error)

    # Validate exception message
    assert len(exc.args) == 1
    message = exc.args[0]
    assert isinstance(message, str)
    if exp_message_pattern:
        assert re.match(exp_message_pattern, message)

    # Validate other exception attributes
    for name, exp_value in exp_attrs.items():
        assert hasattr(exc, name)
        value = getattr(exc, name)
        assert value == exp_value


def test_ceasedexistence_repr():
    """All tests for CeasedExistence.__repr__()."""

    exc = CeasedExistence("/api/foo")

    classname = exc.__class__.__name__

    # Execute the code to be tested
    repr_str = repr(exc)

    # We check the one-lined string just roughly
    repr_str = repr_str.replace('\n', '\\n')
    assert re.match(fr'^{classname}\s*\(.*\)$', repr_str)


def test_ceasedexistence_str():
    """All tests for CeasedExistence.__str__()."""

    exc = CeasedExistence("/api/foo")

    exp_str = str(exc.args[0])

    # Execute the code to be tested
    str_str = str(exc)

    assert str_str == exp_str


def test_ceasedexistence_str_def():
    """All tests for CeasedExistence.str_def()."""

    exc = CeasedExistence("/api/foo")

    classname = exc.__class__.__name__

    # Execute the code to be tested
    str_def = exc.str_def()

    str_def = ' ' + str_def
    assert str_def.find(f' classname={classname!r};') >= 0
    assert str_def.find(' message=') >= 0
