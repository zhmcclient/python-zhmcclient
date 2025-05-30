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
Pytest fixtures for CPCs.
"""


import pytest
import zhmcclient

# pylint: disable=unused-import
from ._hmc_definition_fixtures import hmc_session  # noqa: F401
from ._hmc_inventory_file import HMCInventoryFileError


__all__ = ['all_cpcs', 'dpm_mode_cpcs', 'classic_mode_cpcs']


def fixtureid_cpcs(fixture_value):
    """
    Return a fixture ID to be used by pytest, for fixtures returning a list of
    CPCs.

    Parameters:

      * fixture_value (list of zhmcclient.Cpc): The list of CPCs.
    """
    if not isinstance(fixture_value, list):
        return None  # Use pytest auto-generated ID
    cpc_list = fixture_value
    cpcs_str = ','.join([cpc.name for cpc in cpc_list])
    return f"CPCs={cpcs_str}"


@pytest.fixture(
    scope='module',
    ids=fixtureid_cpcs
)
def all_cpcs(request, hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Pytest fixture representing the set of all CPCs to test against, regardless
    of their operational mode.

    The set of CPCs to test against is defined in the ``cpcs`` variable in the
    HMC entry in the :ref:`HMC inventory file`; if that variable is omitted, it
    is the set of all managed CPCs.

    A test function parameter with the name of this fixture resolves to a list
    of :class:`zhmcclient.Cpc` objects representing that set of CPCs. These
    objects have the "short" set of properties from :meth:`zhmcclient.Cpc.list`.

    The test function is invoked just once with the list of CPCs, and the
    test function needs to loop through the CPCs (or a subset).

    Because the `hmc_session` parameter of this fixture is again a fixture,
    the :func:`zhmcclient.testutils.hmc_session`
    function needs to be imported as well when this fixture is used.
    """
    return defined_cpcs(hmc_session, 'any')


@pytest.fixture(
    scope='module',
    ids=fixtureid_cpcs
)
def dpm_mode_cpcs(request, hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Pytest fixture representing the set of CPCs in DPM mode to test against.

    The set of CPCs to test against is the subset of all CPCs to be tested that
    is in DPM mode.

    The set of all CPCs to be tested is defined in the ``cpcs`` variable in the
    HMC entry in the :ref:`HMC inventory file`; if that variable is omitted, it
    is the set of all managed CPCs.

    A test function parameter with the name of this fixture resolves to a list
    of :class:`zhmcclient.Cpc` objects representing that set of CPCs. These
    objects have the "short" set of properties from :meth:`zhmcclient.Cpc.list`.

    The test function is invoked just once with the list of CPCs, and the
    test function needs to loop through the CPCs (or a subset).

    Because the `hmc_session` parameter of this fixture is again a fixture,
    the :func:`zhmcclient.testutils.hmc_session`
    function needs to be imported as well when this fixture is used.
    """
    return defined_cpcs(hmc_session, 'dpm')


@pytest.fixture(
    scope='module',
    ids=fixtureid_cpcs
)
def classic_mode_cpcs(request, hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Pytest fixture representing the set of CPCs in classic mode to test against.

    The set of CPCs to test against is the subset of all CPCs to be tested that
    is in classic mode.

    The set of all CPCs to be tested is defined in the ``cpcs`` variable in the
    HMC entry in the :ref:`HMC inventory file`; if that variable is omitted, it
    is the set of all managed CPCs.

    A test function parameter with the name of this fixture resolves to a list
    of :class:`zhmcclient.Cpc` objects representing that set of CPCs. These
    objects have the "short" set of properties from :meth:`zhmcclient.Cpc.list`.

    The test function is invoked just once with the list of CPCs, and the
    test function needs to loop through the CPCs (or a subset).

    Because the `hmc_session` parameter of this fixture is again a fixture,
    the :func:`zhmcclient.testutils.hmc_session`
    function needs to be imported as well when this fixture is used.
    """
    return defined_cpcs(hmc_session, 'classic')


def defined_cpcs(session, mode):
    """
    Return a list of CPCs defined in the HMC definition file, that are
    managed by the HMC, and that have the desired operational mode.

    Parameters:

      session (:class:`zhmcclient.Session`): The session with the HMC.

      mode (string): The desired mode of the CPC ('dpm', 'classic', 'any').

    Returns:

      list of :class:`zhmcclient.Cpc`: The CPCs in the desired mode.
    """
    client = zhmcclient.Client(session)
    managed_cpcs = client.cpcs.list()
    managed_cpc_names = [cpc.name for cpc in managed_cpcs]
    hd = session.hmc_definition
    test_cpc_names = list(hd.cpcs.keys()) if hd.cpcs else managed_cpc_names

    result_cpcs = []
    for cpc_name in test_cpc_names:

        cpcs = [cpc for cpc in managed_cpcs if cpc.name == cpc_name]
        if not cpcs:
            raise HMCInventoryFileError(
                f"CPC {cpc_name} defined for HMC {hd.nickname} in the HMC "
                "inventory file is not managed by that HMC. "
                f"Managed CPCs: {', '.join(managed_cpc_names)}")
        cpc = cpcs[0]

        if hd.cpcs and cpc_name in hd.cpcs:
            hd_props = hd.cpcs[cpc_name]
            hd_dpm_enabled = hd_props.get('dpm_enabled', None)
            if hd_dpm_enabled is not None and hd_dpm_enabled != cpc.dpm_enabled:
                raise HMCInventoryFileError(
                    f"CPC {cpc_name} defined for HMC {hd.nickname} in the HMC "
                    f"inventory file defines dpm_enabled={hd_dpm_enabled}, "
                    f"but the actual CPC has dpm_enabled={cpc.dpm_enabled}.")

        if mode == 'dpm' and not cpc.dpm_enabled:
            continue
        if mode == 'classic' and cpc.dpm_enabled:
            continue
        result_cpcs.append(cpc)

    return result_cpcs
