# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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
Unit tests for _client module.
"""


import pytest

from zhmcclient import Client, CpcManager, MetricsContextManager
from zhmcclient_mock import FakedSession


@pytest.mark.parametrize(
    "hmc_name, hmc_version, api_version", [
        ('fake-hmc', '2.13.1', '1.8'),
    ]
)
def test_client_initial_attrs(hmc_name, hmc_version, api_version):
    """Test initial attributes of Client."""

    session = FakedSession('fake-host', hmc_name, hmc_version, api_version)

    # Execute the code to be tested
    client = Client(session)

    assert client.session is session
    assert isinstance(client.cpcs, CpcManager)
    assert client.cpcs.session is session
    assert isinstance(client.metrics_contexts, MetricsContextManager)
    assert client.metrics_contexts.session is session
    assert client.metrics_contexts.client is client


@pytest.mark.parametrize(
    "hmc_name, hmc_version, api_version", [
        ('fake-hmc1', '2.13.1', '1.8'),
        ('fake-hmc2', '2.14.0', '2.20'),
    ]
)
def test_version_info(hmc_name, hmc_version, api_version):
    """All tests for Client.version_info()."""

    session = FakedSession('fake-host', hmc_name, hmc_version, api_version)

    # Client object under test
    client = Client(session)

    # Execute the code to be tested
    version_info = client.version_info()

    exp_version_info = tuple([int(v) for v in api_version.split('.')])

    assert version_info == exp_version_info


@pytest.mark.parametrize(
    "hmc_name, hmc_version, api_version", [
        ('fake-hmc1', '2.13.1', '1.8'),
        ('fake-hmc2', '2.14.0', '2.20'),
    ]
)
def test_query_api_version(hmc_name, hmc_version, api_version):
    """All tests for Client.query_api_version()."""

    session = FakedSession('fake-host', hmc_name, hmc_version, api_version)

    # Client object under test
    client = Client(session)

    # Execute the code to be tested
    api_version_info = client.query_api_version()

    api_major_version = int(api_version.split('.')[0])
    api_minor_version = int(api_version.split('.')[1])

    exp_api_version_info = {
        'api-major-version': api_major_version,
        'api-minor-version': api_minor_version,
        'hmc-version': hmc_version,
        'hmc-name': hmc_name,
    }

    assert api_version_info == exp_api_version_info


TESTCASES_GET_INVENTORY = [
    # Testcases for test_get_inventory()
    # Each item in the list is a testcase with these properties:
    # - input_resources: Input parameter 'resources'.
    # - exp_exc_type: Expected exception type, or None.
    # - exp_inventory: Expected result inventory, as a dict with:
    #   key: Resource class
    #   value: List of resource names
    (
        None,
        Exception,
        None
    ),
    (
        [],
        None,
        {}
    ),
    (
        ['cpc'],
        None,
        {
            'cpc': ['CPC1'],
        }
    ),
    (
        ['core-resources'],
        None,
        {
            'cpc': ['CPC1'],
        }
    ),
    (
        ['partition'],
        None,
        {}
    ),
]


@pytest.mark.parametrize(
    "input_resources, exp_exc_type, exp_inventory",
    TESTCASES_GET_INVENTORY
)
def test_get_inventory(input_resources, exp_exc_type, exp_inventory):
    """All tests for Client.get_inventory()."""

    session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')

    # Client object under test
    client = Client(session)

    # We set up a fixed faked HMC environment
    session.hmc.cpcs.add({
        'object-id': 'fake-cpc1-oid',
        # object-uri is set up automatically
        'parent': None,
        'class': 'cpc',
        'name': 'CPC1',
        'description': 'CPC #1 (classic mode)',
        'status': 'active',
        'dpm-enabled': False,
        'is-ensemble-member': False,
        'iml-mode': 'lpar',
    })

    if exp_exc_type:
        try:

            # Execute the code to be tested
            client.get_inventory(input_resources)

        except exp_exc_type:
            pass
    else:

        # Execute the code to be tested
        inventory = client.get_inventory(input_resources)

        # Go through actual result and check against expected result
        seen_names_by_class = {}  # Resource classes and names already seen
        for resource_props in inventory:

            assert 'class' in resource_props
            res_class = resource_props['class']

            assert 'name' in resource_props
            res_name = resource_props['name']

            assert res_class in exp_inventory
            exp_names = exp_inventory[res_class]

            assert res_name in exp_names

            if res_class not in seen_names_by_class:
                seen_names_by_class[res_class] = []
            seen_names_by_class[res_class].append(res_name)

        # Check if there are any expected names that have not been in the result
        for exp_class, exp_names in exp_inventory.items():
            assert exp_class in seen_names_by_class
            seen_names = seen_names_by_class[exp_class]
            for exp_name in exp_names:
                assert exp_name in seen_names
