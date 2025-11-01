# Copyright 2025 IBM Corp. All Rights Reserved.
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
Pytest fixtures for end2end tests.
"""


import os
import time
import logging
import pytest


LOG_FORMAT_STRING = '%(asctime)s %(levelname)s %(name)s: %(message)s'

LOG_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'

LOG_DATETIME_TIMEZONE = time.gmtime


@pytest.fixture(scope='function')
def zhmc_logger(request):
    # Note: The first paragraph is shown by 'pytest --fixtures'
    """
    Pytest fixture that provides a logger for an end2end test function.

    This functionm creates a logger named after the test function.
    Using this fixture as an argument in a test function resolves to that
    logger.

    Logging is enabled by setting the env var TESTLOGFILE. If logging is
    enabled, the logger is set to debug level, otherwise the logger is disabled.

    During setup of the fixture, a log entry for entering the test function
    is written, and during teardown of the fixture, a log entry for leaving
    the test function is written.

    Because this fixture is called for each invocation of a test
    function, it ends up being called multiple times within the same Python
    process. Therefore, the logger is created only when it does not exist yet.

    Returns:
        logging.Logger: Logger for the test function
    """
    log_file = os.getenv('TESTLOGFILE', None)
    if log_file:
        logging.Formatter.converter = LOG_DATETIME_TIMEZONE
        log_formatter = logging.Formatter(
            LOG_FORMAT_STRING, datefmt=LOG_DATETIME_FORMAT)
        log_handler = logging.FileHandler(log_file, encoding='utf-8')
        log_handler.setFormatter(log_formatter)

    testfunc_name = request.function.__name__
    testfunc_logger = logging.getLogger(testfunc_name)

    if log_file and log_handler not in testfunc_logger.handlers:
        testfunc_logger.addHandler(log_handler)

    if log_file:
        testfunc_logger.setLevel(logging.DEBUG)
    else:
        testfunc_logger.setLevel(logging.NOTSET)

    testfunc_logger.debug("Entered test function")
    try:
        yield testfunc_logger
    finally:
        testfunc_logger.debug("Leaving test function")
