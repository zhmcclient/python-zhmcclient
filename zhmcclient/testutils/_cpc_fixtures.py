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
Pytest fixtures for CPCs.
"""

from __future__ import absolute_import

import warnings
import pytest
import zhmcclient

# pylint: disable=unused-import
from ._hmc_definition_fixtures import hmc_session  # noqa: F401

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
    return "CPCs={}".format(cpcs_str)


@pytest.fixture(
    scope='module',
    ids=fixtureid_cpcs
)
def all_cpcs(request, hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Pytest fixture representing the set of all CPCs that are defined in the HMC
    definition file for the selected HMC or HMC group.

    A test function parameter using this fixture resolves to a list of
    :class:`zhmcclient.Cpc` objects representing that set of CPCs. These
    objects have the "short" set of properties from :meth:`zhmcclient.Cpc.list`.

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
    Pytest fixture representing the set of CPCs in DPM mode that are
    defined in the HMC definition file for the selected HMC or HMC group.

    A test function parameter using this fixture resolves to a list of
    :class:`zhmcclient.Cpc` objects representing that set of CPCs. These
    objects have the "short" set of properties from :meth:`zhmcclient.Cpc.list`.

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
    Pytest fixture representing the set of CPCs in classic mode that are
    defined in the HMC definition file for the selected HMC or HMC group.

    A test function parameter using this fixture resolves to a list of
    :class:`zhmcclient.Cpc` objects representing that set of CPCs. These
    objects have the "short" set of properties from :meth:`zhmcclient.Cpc.list`.

    Because the `hmc_session` parameter of this fixture is again a fixture,
    the :func:`zhmcclient.testutils.hmc_session`
    function needs to be imported as well when this fixture is used.
    """
    return defined_cpcs(hmc_session, 'classic')


def defined_cpcs(session, mode):
    """
    Return a list of CPCs defined in the HMC definition file, that are actually
    managed by the HMC, and that actually have the desired operational mode.

    Parameters:

      session (:class:`zhmcclient.Session`): The session with the HMC.

      mode (string): The desired mode of the CPC ('dpm', 'classic', 'any').

    Returns:
      list of :class:`zhmcclient.Cpc`: The CPCs in the desired mode.
    """
    client = zhmcclient.Client(session)
    actual_cpcs = client.cpcs.list()
    actual_cpc_names = [cpc.name for cpc in actual_cpcs]
    hd = session.hmc_definition
    result_cpcs = []
    for cpc_name in hd.cpcs:
        cpcs = [cpc for cpc in actual_cpcs if cpc.name == cpc_name]
        if not cpcs:
            msg_txt = (
                "CPC {c} defined for HMC {n} at {h} in HMC definition file is "
                "not managed by that HMC. Actually managed CPCs: {cl}".
                format(c=cpc_name, n=hd.nickname, h=hd.host,
                       cl=', '.join(actual_cpc_names)))
            warnings.warn(msg_txt, UserWarning)
            pytest.skip(msg_txt)
        cpc = cpcs[0]

        if mode == 'dpm' and not cpc.dpm_enabled:
            continue
        if mode == 'classic' and cpc.dpm_enabled:
            continue
        result_cpcs.append(cpc)

    return result_cpcs
