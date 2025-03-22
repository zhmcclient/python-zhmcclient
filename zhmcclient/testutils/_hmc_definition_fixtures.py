# Copyright 2019,2021 IBM Corp. All Rights Reserved.
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
Pytest fixtures for mocked HMCs.
"""


import os
import logging
import time
import pytest
import zhmcclient
import zhmcclient_mock

from ._hmc_definition import HMCDefinition
from ._hmc_definitions import hmc_definitions

__all__ = ['hmc_definition', 'hmc_session', 'LOG_FORMAT_STRING',
           'LOG_DATETIME_FORMAT', 'LOG_DATETIME_TIMEZONE']

# Log parameters when logging is enabled via TESTLOGFILE
LOG_FORMAT_STRING = '%(asctime)s %(levelname)s %(name)s: %(message)s'
LOG_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'
LOG_DATETIME_TIMEZONE = time.gmtime  # Used as formatter converter function


def fixtureid_hmc_definition(fixture_value):
    """
    Return a fixture ID to be used by pytest, for fixture `hmc_definition()`.

    Parameters:

      fixture_value (HMCDefinition): The HMC definition of the HMC the test
        runs against.
    """
    if not isinstance(fixture_value, HMCDefinition):
        return None  # Use pytest auto-generated ID
    hd = fixture_value
    show_hmc = False  # Enable to show HMC/userid or mock file in tests
    if not show_hmc:
        hmc_str = ""
    elif hd.mock_file:
        hmc_str = f"(mock_file={hd.mock_file})"
    else:
        hmc_str = f"(host={hd.host}, userid={hd.userid})"
    ret_str = f"hmc_definition={hd.nickname}{hmc_str}"
    return ret_str


@pytest.fixture(
    params=hmc_definitions(load=None),
    scope='module',
    ids=fixtureid_hmc_definition
)
def hmc_definition(request):
    """
    Pytest fixture representing the set of HMC definitions to use for a test.

    A test function parameter with the name of this fixture resolves to the
    :class:`~zhmcclient.testutils.HMCDefinition`
    object of each HMC to test against.

    The test function is called once for each HMC, if the targeted HMC is a
    group.
    """
    return request.param


@pytest.fixture(
    scope='module'
)
def hmc_session(request, hmc_definition):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Pytest fixture representing the set of HMC sessions to run a test against.

    A test function parameter with the name of this fixture resolves to the
    :class:`zhmcclient.Session` or :class:`zhmcclient_mock.FakedSession` object
    for each HMC to test against.

    The session is already logged on to the HMC.

    The session object has an additional property named ``hmc_definition``
    that is the :class:`~zhmcclient.testutils.HMCDefinition` object for the
    corresponding HMC definition in the :ref:`HMC inventory file`.

    Because the `hmc_definition` parameter of this fixture is again a fixture,
    the :func:`zhmcclient.testutils.hmc_definition` function needs to be
    imported as well when this fixture is used.

    Upon fixture teardown, the session is automatically logged off from the HMC.
    """
    session = setup_hmc_session(hmc_definition)
    yield session
    teardown_hmc_session(session)


def setup_hmc_session(hd):
    """
    Setup an HMC session and return a new session object for it.

    If the HMC definition represents a real HMC, log on to an HMC and return
    a new :class:`zhmcclient.Session` object.

    If the HMC definition represents a mocked HMC, create a new mock environment
    from that and return a :class:`zhmcclient_mock.FakedSession` object.
    """
    # We use the cached skip reason from previous attempts
    skip_msg = getattr(hd, 'skip_msg', None)
    if skip_msg:
        pytest.skip(f"Skip reason from earlier attempt: {skip_msg}")

    if hd.mock_file:
        # A mocked HMC

        # Create a mocked session using the mock file from the inventory file
        session = zhmcclient_mock.FakedSession.from_hmc_yaml_file(
            hd.mock_file, userid=hd.userid, password=hd.password)

        # Set the HMC definition host to the host found in the mock file.
        hd.host = session.host

    else:
        # A real HMC

        # Enable debug logging if specified
        log_file = os.getenv('TESTLOGFILE', None)
        if log_file:

            logging.Formatter.converter = LOG_DATETIME_TIMEZONE
            log_formatter = logging.Formatter(
                LOG_FORMAT_STRING, datefmt=LOG_DATETIME_FORMAT)
            log_handler = logging.FileHandler(log_file, encoding='utf-8')
            log_handler.setFormatter(log_formatter)

            logger = logging.getLogger('zhmcclient.hmc')
            if log_handler not in logger.handlers:
                logger.addHandler(log_handler)
            logger.setLevel(logging.DEBUG)

            logger = logging.getLogger('zhmcclient.api')
            if log_handler not in logger.handlers:
                logger.addHandler(log_handler)
            logger.setLevel(logging.DEBUG)

            logger = logging.getLogger('zhmcclient.jms')
            if log_handler not in logger.handlers:
                logger.addHandler(log_handler)
            logger.setLevel(logging.DEBUG)

            logger = logging.getLogger('zhmcclient.os')
            if log_handler not in logger.handlers:
                logger.addHandler(log_handler)
            logger.setLevel(logging.DEBUG)

        rt_config = zhmcclient.RetryTimeoutConfig(
            read_timeout=1800,
        )

        # Creating a session does not interact with the HMC (logon is deferred)
        session = zhmcclient.Session(
            hd.host, hd.userid, hd.password, verify_cert=hd.verify_cert,
            retry_timeout_config=rt_config)

        # Check access to the HMC
        try:
            session.logon()
        except zhmcclient.Error as exc:
            msg = (
                f"Cannot log on to HMC {hd.nickname} at {hd.host} "
                f"due to {exc.__class__.__name__}: {exc}")
            hd.skip_msg = msg
            pytest.skip(msg)

    hd.skip_msg = None
    session.hmc_definition = hd

    return session


def teardown_hmc_session(session):
    """
    Log off from an HMC session.
    """
    session.logoff()
