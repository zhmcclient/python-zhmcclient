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
Unit tests for _logging module.
"""

import logging
from testfixtures import log_capture
import unittest

from zhmcclient._logging import _log_call


class TestLogging(unittest.TestCase):

    @log_capture(level=logging.INFO)
    def test_logging_decorator(self, capture):

        @_log_call
        def do_something():
            pass

        do_something()
        capture.check(('tests.test_logging',
                       'INFO',
                       'tests.test_logging.do_something => entering...'),
                      ('tests.test_logging',
                       'INFO',
                       'tests.test_logging.do_something <= exit.'))
