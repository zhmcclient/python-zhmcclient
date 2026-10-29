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
Pytest config file for this subtree that provides support for logging.
"""

import os
import logging
import pytest
from zhmcclient.testutils import LOG_FILE_ENV_VAR, LOG_FORMAT, \
    LOG_DATETIME_FORMAT, LOG_DATETIME_TIMEZONE

# Path name of the log file, or None if logging is disabled
LOG_FILE = os.environ.get(LOG_FILE_ENV_VAR)

# Name of the Python logger for end2end test functions
TESTFUNC_LOGGER_NAME = "test.end2end"

# Log level
LOG_LEVEL = logging.DEBUG


def file_handler(logger, log_file):
    """
    Returns the FileHandler of the logger that logs to the specified log file,
    or None if no such handler could be found.

    Parameters:

      logger (logging.Logger): Logger to be checked.

      log_file (str): Path name of log file to be checked.

    Returns:

      logging.FileHandler: File handler for the log file, or None if not found.
    """
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and \
                handler.baseFilename == log_file:
            return handler
    return None


def setup_logging(log_file):
    """
    Set up logging for end2end testcases.

    If a log file is specified, logging is enabled and one logger is created
    with a file handler to the log file:

      * The test function Logger.
        That logger is named as defined in TESTFUNC_LOGGER_NAME and is used
        for logging the entry to and exit from the end2end test functions
        and for additional logging within the end2end test functions.

    If no log file is specified, logging is disabled. The same two loggers are
    created but disabled by setting them to log level NOTSET.

    Note that the zhmcclient logging is also enabled to go to the same log
    file and controlled by the same env var, via the zhmcclient testutils
    support. For details, see zhmcclient/testutils/_hmc_session_functions.py.

    This setup function tolerates being called multiple times in the same
    Python process and will set up the loggers only once. However, it will
    be called only once in each Python process running pytest.

    Parameters:

      log_file (str): Path name of log file, if logging should be enabled.
        `None`, if logging should be disabled.
    """

    testfunc_logger = logging.getLogger(TESTFUNC_LOGGER_NAME)

    if log_file:

        abs_log_file = os.path.abspath(log_file)
        formatter = logging.Formatter(
            LOG_FORMAT, datefmt=LOG_DATETIME_FORMAT)

        # Globally set the timezone conversion on Python logging
        logging.Formatter.converter = LOG_DATETIME_TIMEZONE

        # Add the file handler to the test function logger, if needed.
        testfunc_handler = file_handler(testfunc_logger, abs_log_file)
        if testfunc_handler is None:
            testfunc_handler = logging.FileHandler(
                abs_log_file, encoding='utf-8')
            testfunc_logger.addHandler(testfunc_handler)
        testfunc_handler.setFormatter(formatter)
        testfunc_logger.setLevel(LOG_LEVEL)

        testfunc_logger.info(
            "Logging is enabled for logger %s at level %s",
            TESTFUNC_LOGGER_NAME, logging.getLevelName(LOG_LEVEL))

    else:
        testfunc_logger.setLevel(logging.NOTSET)


def pytest_configure(config):
    # pylint: disable=unused-argument
    """
    Initialize logging once per pytest process, if a log file is given.
    """
    if LOG_FILE:
        setup_logging(LOG_FILE)


@pytest.fixture(autouse=True)
def test_logger(request):
    """
    Pytest fixture that provides the test function logger to end2end test
    functions and will log entry into and exit from each end2end test function
    call.

    This fixture has "autouse" set, so the entry into and exit from the test
    function will be automatically logged, if logging is enabled via the
    env var.

    When a test function needs to perform additional logging, this fixture can
    be specified as a parameter to the test function and resolves to the test
    function logger, which will log if logging is enabled via the env var.
    """
    logger = logging.getLogger(TESTFUNC_LOGGER_NAME)
    nodeid = request.node.nodeid

    logger.info("ENTER %s", nodeid)

    # The yield is protected in order to ensure that errors in other fixtures
    # do not cause the exit log to be skipped.
    try:
        yield logger
    finally:
        logger.info("LEAVE %s", nodeid)
