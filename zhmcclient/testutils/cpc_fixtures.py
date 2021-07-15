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

import pytest
import zhmcclient

# pylint: disable=unused-import
from .hmc_definition_fixtures import hmc_session  # noqa: F401, E501


def fixtureid_cpc(fixture_value):
    """
    Return a fixture ID to be used by pytest, for fixtures `one_cpc()` and
    `all_cpcs()`.

    Parameters:
      * fixture_value (zhmcclient.Cpc): The Cpc object the test runs against.
    """
    cpc = fixture_value
    assert isinstance(cpc, zhmcclient.Cpc)
    return "CPC={}".format(cpc.name)


@pytest.fixture(
    scope='module',
    ids=fixtureid_cpc
)
def one_cpc(request, hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Fixture representing a single, arbitrary CPC managed by the HMC.

    Returns a `zhmcclient.Cpc` object, with full properties.
    """
    client = zhmcclient.Client(hmc_session)
    cpcs = client.cpcs.list()
    assert len(cpcs) >= 1
    cpc = cpcs[0]
    cpc.pull_full_properties()
    return cpc


@pytest.fixture(
    scope='module',
    ids=fixtureid_cpc
)
def all_cpcs(request, hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name,unused-argument
    """
    Fixture representing the set of all CPCs managed by the HMC.

    Returns a list of `zhmcclient.Cpc` objects, with full properties.
    """
    client = zhmcclient.Client(hmc_session)
    cpcs = client.cpcs.list(full_properties=True)
    return cpcs
