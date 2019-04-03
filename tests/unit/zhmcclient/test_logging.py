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
Unit tests for _logging module.
"""

from __future__ import absolute_import, print_function

import re
import logging
import pytest
from testfixtures import LogCapture

from zhmcclient._logging import logged_api_call, get_logger


#
# Various uses of the @logged_api_call decorator
#

@logged_api_call
def decorated_global_function():
    """A decorated function at the global (module) level."""
    pass


def global1_function():

    @logged_api_call
    def decorated_inner1_function():
        """A decorated inner function defined in a global function."""
        pass

    return decorated_inner1_function


def get_decorated_inner1_function():
    return global1_function()


def global2_function():

    def inner1_function():

        @logged_api_call
        def decorated_inner2_function():
            """A decorated inner function defined in another inner function
            that is defined in a global function."""
            pass

        return decorated_inner2_function

    return inner1_function()


def get_decorated_inner2_function():
    return global2_function()


class Decorator1Class(object):

    @logged_api_call
    def decorated_method(self):
        """A decorated method of a class."""
        pass


class Decorator2Class(object):

    @staticmethod
    def method():

        @logged_api_call
        def decorated_inner_function():
            """A decorated inner function defined in a method of a class."""
            pass

        return decorated_inner_function

    @staticmethod
    def get_decorated_inner_function():
        return Decorator2Class.method()


#
# Supporting definitions
#

class CallerClass(object):

    @staticmethod
    def call_from_method(func, *args, **kwargs):
        """
        A supporting method that calls the specified function with the
        specified arguments and keyword arguments. This is used by the test
        cases so that this function acts as a caller for the decorated API
        function.
        """
        return func(*args, **kwargs)


def call_from_global(func, *args, **kwargs):
    """
    A supporting global function that calls the specified function with the
    specified arguments and keyword arguments. This is used by the test cases
    so that this function acts as a caller for the decorated API function.
    """
    return func(*args, **kwargs)


# Some expected values that are constant
_EXP_LOGGER_NAME = 'zhmcclient.api'
_EXP_LOG_LEVEL = 'DEBUG'
_EXP_LOG_MSG_ENTER_PATTERN = "Called: .*, args: .*, kwargs: .*"
_EXP_LOG_MSG_LEAVE_PATTERN = "Return: .*, result: .*"


@pytest.fixture()
def capture():
    """
    This way of defining a fixture works around the issue that when
    using the decorator testfixtures.log_capture() instead, pytest
    fails with "fixture 'capture' not found".
    """
    with LogCapture(level=logging.DEBUG) as log:
        yield log


#
# Test cases
#

class TestLoggingDecorator(object):
    """All test cases for the @logged_api_call decorator."""

    def assert_log_capture(self, log_capture, exp_apifunc):

        assert len(log_capture.records) == 2

        enter_record = log_capture.records[0]
        assert enter_record.name == _EXP_LOGGER_NAME
        assert enter_record.levelname == _EXP_LOG_LEVEL
        assert re.match(_EXP_LOG_MSG_ENTER_PATTERN, enter_record.msg)
        # We don't check the function name and its pos and kw args

        leave_record = log_capture.records[1]
        assert leave_record.name == _EXP_LOGGER_NAME
        assert leave_record.levelname == _EXP_LOG_LEVEL
        assert re.match(_EXP_LOG_MSG_LEAVE_PATTERN, leave_record.msg)
        # We don't check the function name and its pos and kw args

    def test_1a_global_from_global(self, capture):
        """Simple test calling a decorated global function from a global
        function."""

        call_from_global(decorated_global_function)

        self.assert_log_capture(capture, 'decorated_global_function()')

    def test_1b_global_from_method(self, capture):
        """Simple test calling a decorated global function from a method."""

        CallerClass().call_from_method(decorated_global_function)

        self.assert_log_capture(capture, 'decorated_global_function()')

    def test_2a_global_inner1_from_global(self, capture):
        """Simple test calling a decorated inner function defined in a global
        function from a global function."""

        decorated_inner1_function = get_decorated_inner1_function()

        call_from_global(decorated_inner1_function)

        self.assert_log_capture(capture,
                                'global1_function.decorated_inner1_function()')

    def test_2b_global_inner1_from_method(self, capture):
        """Simple test calling a decorated inner function defined in a global
        function from a method."""

        decorated_inner1_function = get_decorated_inner1_function()

        CallerClass().call_from_method(decorated_inner1_function)

        self.assert_log_capture(capture,
                                'global1_function.decorated_inner1_function()')

    def test_3a_global_inner2_from_global(self, capture):
        """Simple test calling a decorated inner function defined in an inner
        function defined in a global function from a global function."""

        decorated_inner2_function = get_decorated_inner2_function()

        call_from_global(decorated_inner2_function)

        self.assert_log_capture(capture,
                                'inner1_function.decorated_inner2_function()')

    def test_3b_global_inner1_from_method(self, capture):
        """Simple test calling a decorated inner function defined in an inner
        function defined in a global function from a method."""

        decorated_inner2_function = get_decorated_inner2_function()

        CallerClass().call_from_method(decorated_inner2_function)

        self.assert_log_capture(capture,
                                'inner1_function.decorated_inner2_function()')

    def test_4a_method_from_global(self, capture):
        """Simple test calling a decorated method from a global function."""

        decorated_method = Decorator1Class.decorated_method
        d = Decorator1Class()

        call_from_global(decorated_method, d)

        self.assert_log_capture(capture, 'Decorator1Class.decorated_method()')

    def test_4b_method_from_method(self, capture):
        """Simple test calling a decorated method from a method."""

        decorated_method = Decorator1Class.decorated_method
        d = Decorator1Class()

        CallerClass().call_from_method(decorated_method, d)

        self.assert_log_capture(capture, 'Decorator1Class.decorated_method()')

    def test_5a_method_from_global(self, capture):
        """Simple test calling a decorated inner function defined in a method
        from a global function."""

        decorated_inner_function = \
            Decorator2Class.get_decorated_inner_function()

        call_from_global(decorated_inner_function)

        self.assert_log_capture(capture,
                                'method.decorated_inner_function()')

    def test_5b_method_from_method(self, capture):
        """Simple test calling a decorated inner function defined in a method
        from a method."""

        decorated_inner_function = \
            Decorator2Class.get_decorated_inner_function()

        CallerClass().call_from_method(decorated_inner_function)

        self.assert_log_capture(capture,
                                'method.decorated_inner_function()')

    def test_decorated_class(self):
        """Test that using the decorator on a class raises TypeError."""

        with pytest.raises(TypeError):

            @logged_api_call
            class DecoratedClass(object):
                pass

    def test_decorated_property(self):
        """Test that using the decorator on a property raises TypeError."""

        with pytest.raises(TypeError):

            class Class(object):

                @logged_api_call
                @property
                def decorated_property(self):
                    return self


class TestGetLogger(object):
    """All test cases for get_logger()."""

    def test_root_logger(self):
        """Test that get_logger('') returns the Python root logger."""

        py_logger = logging.getLogger()

        zhmc_logger = get_logger('')

        assert zhmc_logger is py_logger

    def test_foo_logger(self):
        """Test that get_logger('zhmcclient.foo') returns the same-named
        Python logger and has at least one handler."""

        py_logger = logging.getLogger('zhmcclient.foo')

        zhmc_logger = get_logger('zhmcclient.foo')

        assert zhmc_logger is py_logger
        assert len(zhmc_logger.handlers) >= 1
