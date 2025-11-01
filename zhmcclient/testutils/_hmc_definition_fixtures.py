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
    scope='session',
    ids=fixtureid_hmc_definition
)
def hmc_definition(request):
    # pylint: disable=unused-argument
    # Note: The first paragraph is shown by 'pytest --fixtures'
    """
    Pytest fixture that provides an HMC definition from the HMC inventory file.

    The HMC is selected via the ``TESTHMC`` environment variable when running
    pytest. If the selected HMC is a group in the HMC inventory file, the test
    function is called once for each HMC. For details, see
    :ref:`Running end2end tests`.

    Returns:

      :class:`~zhmcclient.testutils.HMCDefinition`: The HMC definition from the
      HMC inventory file for the HMC to test against.
    """
    return request.param


@pytest.fixture(
    scope='session'
)
def hmc_session(request, hmc_definition):
    # pylint: disable=redefined-outer-name,unused-argument
    # Note: The first paragraph is shown by 'pytest --fixtures'
    """
    Pytest fixture that provides a logged-on HMC session to an HMC defined in
    the HMC inventory file.

    The HMC is selected via the ``TESTHMC`` environment variable when running
    pytest. If the selected HMC is a group in the HMC inventory file, the test
    function is called once for each HMC. For details, see
    :ref:`Running end2end tests`.

    Upon fixture teardown, the session is logged off from the HMC.

    This fixture has a scope of "session", so the same HMC session is reused
    across all test modules for the complete pytest run.

    This fixture is provided in the 'zhmcclient' Python package as a pytest
    plugin, so it is globally known to pytest and can be used without importing
    it.

    Returns:

      :class:`zhmcclient.Session` or :class:`zhmcclient.mock.FakedSession`:
      A logged-on session to the HMC to test against.
      The session object has an additional property named ``hmc_definition``
      that is the :class:`~zhmcclient.testutils.HMCDefinition` object for the
      corresponding HMC definition in the :ref:`HMC inventory file`.
    """
    session = setup_hmc_session(hmc_definition)
    yield session
    teardown_hmc_session(session)
