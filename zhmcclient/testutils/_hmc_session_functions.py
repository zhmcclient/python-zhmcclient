# Copyright 2019,2021,2025 IBM Corp. All Rights Reserved.
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
Helper functions for HMC session management.
"""


import os
import re
import time
import logging
import pytest
import zhmcclient
import zhmcclient_mock

__all__ = ['setup_hmc_session', 'teardown_hmc_session',
           'teardown_hmc_session_id', 'is_valid_hmc_session_id',
           'LOG_FORMAT_STRING', 'LOG_DATETIME_FORMAT', 'LOG_DATETIME_TIMEZONE']

LOG_FORMAT_STRING = '%(asctime)s %(levelname)s %(name)s: %(message)s'

LOG_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'

LOG_DATETIME_TIMEZONE = time.gmtime


def setup_hmc_session(hd):
    """
    Setup an HMC session and return a new session object for it.

    If the HMC definition represents a real HMC, log on to an HMC and return
    a new :class:`zhmcclient.Session` object.

    If the HMC definition represents a mocked HMC, create a new mock environment
    from that and return a :class:`zhmcclient_mock.FakedSession` object.

    Parameters:

      hd (:class:`~zhmcclient.testutils.HMCDefinition`): The HMC definition of
        the HMC the test runs against.

    Returns:

      :class:`~zhmcclient.Session`): Sesson object for the logged-on real or
      mocked session with the HMC.
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
    Log off from a valid session with a real HMC, identified by a zhmcclient
    session object.

    If the session represents a mocked HMC, nothing is done.

    Parameters:

      session (:class:`~zhmcclient.Session`): Session with a real or mocked HMC.
    """
    if not isinstance(session, zhmcclient_mock.FakedSession):
        session.logoff()


def teardown_hmc_session_id(hd, session_id):
    """
    Log off from a valid session with a real HMC, identified by its session ID.

    If the HMC definition represents a mocked HMC, nothing is done.

    Raises zhmcclient exceptions if the session ID is not valid.

    Parameters:

      hd (:class:`~zhmcclient.testutils.HMCDefinition`): The HMC definition of
        the HMC the test runs against.

      session_id (str): HMC session ID.
    """
    if hd.mock_file is None:
        session = zhmcclient.Session(
            hd.host, hd.userid, session_id=session_id,
            verify_cert=hd.verify_cert)
        session.logoff()


def is_valid_hmc_session_id(hd, session_id):
    """
    Return a boolean indicating whether an HMC session ID is valid.

    If the HMC definition represents a real HMC, the specified session ID
    is tested with an HMC operation.

    If the HMC definition represents a mocked HMC, no such test is performed,
    and the specified session ID is considered valid if it is `None`.

    Raises zhmcclient exceptions if the validity cannot be determined.

    Parameters:

      hd (:class:`~zhmcclient.testutils.HMCDefinition`): The HMC definition of
        the HMC the test runs against.

      session_id (str): HMC session ID to be tested for validity.
    """
    if hd.mock_file is not None:
        return session_id is None

    session = zhmcclient.Session(
        hd.host, hd.userid, session_id=session_id, verify_cert=hd.verify_cert)
    try:
        # This simply performs the GET with the session header set to the
        # session_id.
        session.get('/api/cpcs', logon_required=False, renew_session=False)
    except zhmcclient.ServerAuthError as exc:
        if re.search(r'x-api-session header did not map to a known session',
                     str(exc)):
            return False
        raise
    return True
