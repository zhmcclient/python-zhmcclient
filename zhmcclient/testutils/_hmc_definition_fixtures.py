# Copyright 2019-2021 IBM Corp. All Rights Reserved.
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

from __future__ import absolute_import

import os
import logging
import pytest
import zhmcclient
import zhmcclient_mock

from ._hmc_definitions import HMCDefinitionFile, HMCDefinition

__all__ = ['hmc_definitions', 'hmc_definition', 'hmc_session']

HOME_DIR = os.path.expanduser("~")

# Path name of HMC definition file
DEFAULT_TESTHMCFN = '.zhmc_hmc_definitions.yaml'
DEFAULT_TESTHMCFILE = os.path.join(HOME_DIR, DEFAULT_TESTHMCFN)
TESTHMCFILE = os.getenv('TESTHMCFILE', DEFAULT_TESTHMCFILE)

# Test nickname in HMC definition file
DEFAULT_TESTHMC = 'default'
TESTHMC = os.getenv('TESTHMC', DEFAULT_TESTHMC)

# Log file
TESTLOGFILE = os.getenv('TESTLOGFILE', None)
if TESTLOGFILE:
    LOG_HANDLER = logging.FileHandler(TESTLOGFILE, encoding='utf-8')
    LOG_FORMAT_STRING = '%(asctime)s %(name)s %(levelname)s %(message)s'
    LOG_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT_STRING))
else:
    LOG_HANDLER = None
    LOG_FORMAT_STRING = None


def hmc_definitions():
    """
    Return the list of HMC definitions for a HMC nickname in a HMC
    definition file.

    The HMC nickname is taken from the environment variable "TESTHMC" if
    set, or otherwise is the default nickname "{def_nick}."

    The path name of the HMC definition file is taken from the environment
    variable "TESTHMCFILE" is set, or otherwise is "{def_fn}" in the home
    directory of the user.

    Returns:
      list of :class:`zhmcclient.testutils.HMCDefinition`:
      The selected HMC definitions.
    """.format(def_nick=DEFAULT_TESTHMC, def_fn=DEFAULT_TESTHMCFN)

    # The Sphinx build imports this module and the use of this function
    # in the hmc_definition() fixture along with the wildcard imports in
    # the testutils/__init__.py module causes this function to be executed upon
    # module import. Since there is no HMC definition file when GitHub Actions
    # or ReadTheDocs builds the documentation, the 'TESTHMCFILE_NOLOAD'
    # emv.var is used to disable the loading of the file in these cases.
    # This env.var needs to be set to 'True' in the following places:
    # * In .github/workflows/test.yml when invoking 'make builddoc'.
    # * In the ReadTheDocs advanced settings, as a private env.var.
    noload = os.getenv('TESTHMCFILE_NOLOAD')

    if noload:
        return []
    def_file = HMCDefinitionFile(filepath=TESTHMCFILE)
    hmc_defs = def_file.list_hmcs(TESTHMC)
    return hmc_defs


def fixtureid_hmc_definition(fixture_value):
    """
    Return a fixture ID to be used by pytest, for fixture `hmc_definition()`.

    Parameters:
      * fixture_value (HMCDefinition): The HMC definition of the HMC the test
        runs against.
    """
    hd = fixture_value
    assert isinstance(hd, HMCDefinition)
    return "hmc_definition={}".format(hd.nickname)


@pytest.fixture(
    params=hmc_definitions(),
    scope='module',
    ids=fixtureid_hmc_definition
)
def hmc_definition(request):
    """
    Fixture representing the set of HMC definitions to use for the end2end
    tests.

    A test function parameter using this fixture resolves to the
    :class:`~zhmcclient.testutils.HMCDefinition`
    object of each HMC to test against.
    """
    return request.param


@pytest.fixture(
    scope='module'
)
def hmc_session(request, hmc_definition):
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Pytest fixture representing the set of HMC sessions to use for the
    end2end tests.

    Because the `hmc_definition` parameter of this fixture is again a fixture,
    the :func:`zhmcclient.testutils.hmc_definition` function needs to be
    imported as well when this fixture is used.

    A test function parameter using this fixture resolves to the
    :class:`zhmcclient.Session` or :class:`zhmcclient_mock.FakedSession` object
    for the HMC session to test against.
    The session is already logged on to the HMC.

    Upon fixture teardown, the session is automatically logged off from the HMC.
    """
    session = setup_hmc_session(hmc_definition)
    yield session
    teardown_hmc_session(session)


def setup_hmc_session(hd):
    """
    Setup an HMC session and return a new zhmcclient.Session object for it.

    If the HMC definition represents a real HMC, log on to an HMC and return
    a new zhmcclient.Session object.

    If the HMC definition represents a faked HMC, create a new faked environment
    from that and return a zhmcclient_mock.FakedSession object.
    """
    # We use the cached skip reason from previous attempts
    skip_msg = getattr(hd, 'skip_msg', None)
    if skip_msg:
        pytest.skip("Skip reason from earlier attempt: {0}".format(skip_msg))

    if hd.faked_hmc_file:
        # A faked HMC

        # Create a faked session from the HMC definition file
        filepath = os.path.join(
            os.path.dirname(hd.hmc_filepath),
            hd.faked_hmc_file)
        session = zhmcclient_mock.FakedSession.from_hmc_yaml_file(filepath)

    else:
        # A real HMC

        # Enable debug logging if specified
        if LOG_HANDLER:

            logger = logging.getLogger('zhmcclient.hmc')
            if LOG_HANDLER not in logger.handlers:
                logger.addHandler(LOG_HANDLER)
            logger.setLevel(logging.DEBUG)

            logger = logging.getLogger('zhmcclient.api')
            if LOG_HANDLER not in logger.handlers:
                logger.addHandler(LOG_HANDLER)
            logger.setLevel(logging.DEBUG)

        # Creating a session does not interact with the HMC (logon is deferred)
        session = zhmcclient.Session(
            hd.hmc_host, hd.hmc_userid, hd.hmc_password,
            verify_cert=hd.hmc_verify_cert)

        # Check access to the HMC
        try:
            session.logon()
        except zhmcclient.Error as exc:
            msg = "Cannot log on to HMC {0} at {1} due to {2}: {3}". \
                format(hd.nickname, hd.hmc_host, exc.__class__.__name__, exc)
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
