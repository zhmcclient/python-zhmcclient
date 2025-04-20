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


import pytest

from ._hmc_definition import HMCDefinition
from ._hmc_definitions import hmc_definitions
from ._hmc_session_functions import setup_hmc_session, teardown_hmc_session

__all__ = ['hmc_definition', 'hmc_session']


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
