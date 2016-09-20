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
Unit tests for _logging module.
"""

from __future__ import absolute_import, print_function

import logging
import unittest
from testfixtures import log_capture

from zhmcclient._logging import _log_call


class TestLogging(unittest.TestCase):
    """All test cases for the _log_call decorator."""

    @log_capture(level=logging.DEBUG)
    def test_logging_decorator(self, capture):
        """Simple test for the _log_call decorator."""

        @_log_call
        def do_something():
            """A decorated function that is called."""
            pass

        do_something()
        capture.check(('tests.unit.test_logging',
                       'DEBUG',
                       'Entering test_logging_decorator.do_something()'),
                      ('tests.unit.test_logging',
                       'DEBUG',
                       'Leaving test_logging_decorator.do_something()'))

# TODO: Add test cases for _get_logger(), specifically for null-handler
