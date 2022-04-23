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
End2end tests for testing whether the HMC definitions in the HMC definition
file match reality.
"""

from __future__ import absolute_import, print_function

import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401
from zhmcclient.testutils import hmc_definition_file

from tests.common.utils import info

urllib3.disable_warnings()


def test_hmcdef_cpcs(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test that the HMC actually manages the CPCs defined in its HMC definition
    and that these CPCs actually have the properties defined there.
    """
    client = zhmcclient.Client(hmc_session)
    cpcs = client.cpcs.list()
    cpc_names = [cpc.name for cpc in cpcs]

    hd = hmc_session.hmc_definition
    for cpc_name in hd.cpcs:
        def_cpc_props = dict(hd.cpcs[cpc_name])

        assert cpc_name in cpc_names, \
            "CPC '{c}' defined in HMC definition file for HMC nickname '{h}' " \
            "is not actually managed by that HMC". \
            format(c=cpc_name, h=hd.nickname)

        cpc = client.cpcs.find(name=cpc_name)
        cpc.pull_full_properties()

        cpc_props = dict(cpc.properties)
        for def_prop_name in def_cpc_props:

            hmc_prop_name = def_prop_name.replace('_', '-')
            assert hmc_prop_name in cpc_props, \
                "Property '{dp}' defined in HMC definition file for " \
                "CPC '{c}' in HMC nickname '{h}' does not actually " \
                "exist on that CPC (as '{hp}')". \
                format(dp=def_prop_name, hp=hmc_prop_name, c=cpc_name,
                       h=hd.nickname)

            cpc_value = cpc_props[hmc_prop_name]
            def_cpc_value = def_cpc_props[def_prop_name]
            assert def_cpc_value == cpc_value, \
                "Property '{dp}' defined in HMC definition file for " \
                "CPC '{c}' in HMC nickname '{h}' has an unexpected value: " \
                "HMC definition file: {dv!r}, actual value: {hv!r}". \
                format(dp=def_prop_name, c=cpc_name, h=hd.nickname,
                       dv=def_cpc_value, hv=cpc_value)


@pytest.mark.skip("Disabled by default")
def test_hmcdef_check_all_hmcs(capsys):
    """
    Check out the HMCs specified in the HMC definition file.
    Skip HMCs that cannot be contacted.
    """
    def_file = hmc_definition_file()
    hmc_defs = def_file.list_all_hmcs()

    rt_config = zhmcclient.RetryTimeoutConfig(
        connect_timeout=10,
        connect_retries=1,
    )

    # Check HMCs and their CPCs
    for hd in hmc_defs:

        if hd.hmc_host is None:
            # Faked HMC
            continue

        for cpc_name in hd.cpcs:

            info(capsys,
                 "Checking HMC {} at {} defined in HMC definition "
                 "file for its managed CPC {}".
                 format(hd.nickname, hd.hmc_host, cpc_name))

            session = zhmcclient.Session(
                hd.hmc_host, hd.hmc_userid, hd.hmc_password,
                verify_cert=hd.hmc_verify_cert,
                retry_timeout_config=rt_config)

            try:
                client = zhmcclient.Client(session)

                try:
                    session.logon()
                except zhmcclient.ConnectionError as exc:
                    info(capsys,
                         "Skipping HMC {} at {} defined in HMC definition "
                         "file: {}: {}".
                         format(hd.nickname, hd.hmc_host,
                                exc.__class__.__name__, exc))
                    continue

                cpcs = client.cpcs.list()
                cpc_names = [cpc.name for cpc in cpcs]
                if cpc_name not in cpc_names:
                    raise AssertionError(
                        "CPC {} defined in HMC definition file for HMC {} "
                        "at {} is not managed by that HMC. Actually managed "
                        "CPCs: {}".
                        format(cpc_name, hd.nickname, hd.hmc_host,
                               ', '.join(cpc_names)))
            finally:
                session.logoff()
