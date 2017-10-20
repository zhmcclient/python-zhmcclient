# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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

from __future__ import absolute_import, print_function

import pytest

from zhmcclient import Client, CpcManager, MetricsContextManager
from zhmcclient_mock import FakedSession


class TestClient(object):
    """All tests for Client classes."""

    @pytest.mark.parametrize(
        "hmc_name, hmc_version, api_version", [
            ('fake-hmc', '2.13.1', '1.8'),
        ]
    )
    def test_client_initial_attrs(self, hmc_name, hmc_version, api_version):
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
    def test_version_info(self, hmc_name, hmc_version, api_version):
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
    def test_query_api_version(self, hmc_name, hmc_version, api_version):
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

    @pytest.mark.parametrize(
        "resources, exp_exc, exp_inventory", [
            (None,
             Exception,
             None
             ),
            ([],
             None,
             {}  # TODO: Add expected inventory
             ),
            (['partition'],
             None,
             {}  # TODO: Add expected inventory
             ),
        ]
    )
    def xtest_get_inventory(self, resources, exp_exc, exp_inventory):
        """All tests for Client.get_inventory()."""

        # TODO: Enable once mock support for Client.get_inventory() is there

        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')

        # Client object under test
        client = Client(session)

        # TODO: Set up inventory from expected inventory

        if exp_exc:
            try:

                # Execute the code to be tested
                client.get_inventory(resources)

            except exp_exc:
                pass
        else:

            # Execute the code to be tested
            inventory = client.get_inventory(resources)

            assert inventory == exp_inventory
