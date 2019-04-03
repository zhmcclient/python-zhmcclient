# Copyright 2019 IBM Corp. All Rights Reserved.
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

import os
import errno
import logging
import pytest
import yaml
import yamlordereddictloader
import zhmcclient
import zhmcclient_mock
from zhmcclient.testutils.hmc_definitions import HMCDefinitionFile, \
    HMCDefinition

# HMC nickname or HMC group nickname in HMC definition file
TESTHMC = os.getenv('TESTHMC', 'default')
HMC_DEF_LIST = HMCDefinitionFile().list_hmcs(TESTHMC)

# Log file
TESTLOGFILE = os.getenv('TESTLOGFILE', None)
LOG_HANDLER = logging.FileHandler(TESTLOGFILE, encoding='utf-8')
LOG_FORMAT_STRING = '%(asctime)s %(name)s %(levelname)s %(message)s'
LOG_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT_STRING))


class FakedHMCFileError(Exception):
    """
    Exception indicating an issue with the faked HMC file.
    """
    pass


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
    params=HMC_DEF_LIST,
    scope='module',
    ids=fixtureid_hmc_definition
)
def hmc_definition(request):
    """
    Fixture representing the set of HMC definitions to use for the end2end
    tests.

    Returns the `HMCDefinition` object of each HMC to test against.
    """
    return request.param


@pytest.fixture(
    scope='module'
)
def hmc_session(request, hmc_definition):
    """
    Pytest fixture representing the set of `zhmcclient.Session` objects to use
    for the end2end tests.

    Because the `hmc_definition` parameter of this fixture is again a fixture,
    `hmc_definition` needs to be imported as well when this fixture is used.

    Returns a `zhmcclient.Session` object that is logged on to the HMC.

    Upon teardown, the `zhmcclient.Session` object is logged off.
    """
    hd = hmc_definition

    # We use the cached skip reason from previous attempts
    skip_msg = getattr(hd, 'skip_msg', None)
    if skip_msg:
        pytest.skip("Skip reason from earlier attempt: {0}".format(skip_msg))

    if hd.faked_hmc_file:
        # A faked HMC

        # Read the faked HMC file
        filepath = os.path.join(
            os.path.dirname(hd.hmc_filepath),
            hd.faked_hmc_file)
        try:
            with open(filepath) as fp:
                try:
                    data = yaml.load(fp, Loader=yamlordereddictloader.Loader)
                except (yaml.parser.ParserError,
                        yaml.scanner.ScannerError) as exc:
                    raise FakedHMCFileError(
                        "Invalid YAML syntax in faked HMC file {0!r}: {1} {2}".
                        format(filepath, exc.__class__.__name__, exc))
        except IOError as exc:
            if exc.errno == errno.ENOENT:
                raise FakedHMCFileError(
                    "The faked HMC file {0!r} was not found".
                    format(filepath))
            else:
                raise

        client = data['faked_client']
        session = zhmcclient_mock.FakedSession(
            client['hmc_host'],
            client['hmc_name'],
            client['hmc_version'],
            client['api_version'])
        for cpc in client['cpcs']:
            session.hmc.cpcs.add(cpc['properties'])

    else:
        # A real HMC

        # Enable debug logging if specified
        if TESTLOGFILE:

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
            hd.hmc_host, hd.hmc_userid, hd.hmc_password)

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

    yield session

    session.logoff()
