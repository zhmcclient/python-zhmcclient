# Copyright 2017 IBM Corp. All Rights Reserved.
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
Function tests for HMC credentials file.
"""

from __future__ import absolute_import, print_function

import requests.packages.urllib3

import pytest
import zhmcclient
from tests.common.utils import HmcCredentials, info

requests.packages.urllib3.disable_warnings()


class TestHMCCredentialsFile(object):
    """
    Test your HMC credentials file, if you have one at the default location.
    """

    def setup_method(self):
        self.hmc_creds = HmcCredentials()

    def test_1_format(self, capsys):
        """Test the format of the HMC credentials file."""

        cpc_items = self.hmc_creds.get_cpc_items()

        if cpc_items is None:
            pytest.skip("HMC credentials file not found: %r" %
                        self.hmc_creds.filepath)
            return

        assert len(cpc_items) > 0

    @pytest.mark.skip("Disabled contacting all HMCs in credentials file")
    def test_2_hmcs(self, capsys):
        """
        Check out the HMCs specified in the HMC credentials file.
        Skip HMCs that cannot be contacted.
        """

        cpc_items = self.hmc_creds.get_cpc_items()

        if cpc_items is None:
            pytest.skip("HMC credentials file not found: %r" %
                        self.hmc_creds.filepath)
            return

        rt_config = zhmcclient.RetryTimeoutConfig(
            connect_timeout=10,
            connect_retries=1,
        )

        # Check HMCs and their CPCs
        for cpc_name in cpc_items:

            cpc_item = cpc_items[cpc_name]

            hmc_host = cpc_item['hmc_host']

            info(capsys, "Checking HMC %r for CPC %r", (hmc_host, cpc_name))

            session = zhmcclient.Session(
                hmc_host, cpc_item['hmc_userid'], cpc_item['hmc_password'],
                retry_timeout_config=rt_config)

            client = zhmcclient.Client(session)

            try:
                session.logon()
            except zhmcclient.ConnectionError as exc:
                info(capsys, "Skipping HMC %r for CPC %r: %s",
                     (hmc_host, cpc_name, exc))
                continue

            cpcs = client.cpcs.list()
            cpc_names = [cpc.name for cpc in cpcs]
            if cpc_name not in cpc_names:
                raise AssertionError(
                    "CPC {!r} not found in HMC {!r}.\n"
                    "Existing CPCs: {!r}".
                    format(cpc_name, hmc_host, cpc_names))

            session.logoff()
