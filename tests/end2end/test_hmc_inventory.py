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
End2end tests for testing whether the HMCs in the HMC inventory file match
reality.
"""


from requests.packages import urllib3
import pytest

import zhmcclient
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401
from zhmcclient.testutils import HMCDefinitions
from zhmcclient.testutils import all_cpcs  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
from zhmcclient.testutils import classic_mode_cpcs  # noqa: F401, E501
# pylint: enable=unused-import

from .utils import is_cpc_property_hmc_inventory

urllib3.disable_warnings()


def _print_cpc(cpc):
    mode_str = 'DPM' if cpc.dpm_enabled else 'classic'
    print(f"Found test CPC {cpc.name} ({mode_str} mode)")


def test_hmcdef_all_cpcs(all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Display all CPCs to be tested.
    """
    for cpc in all_cpcs:
        _print_cpc(cpc)


def test_hmcdef_dpm_cpcs(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Display DPM mode CPCs to be tested.
    """
    for cpc in dpm_mode_cpcs:
        _print_cpc(cpc)


def test_hmcdef_classic_cpcs(classic_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Display classic mode CPCs to be tested.
    """
    for cpc in classic_mode_cpcs:
        _print_cpc(cpc)


def test_hmcdef_cpcs(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test that the HMC actually manages the CPCs defined in its inventory file
    and that these CPCs actually have the properties defined there.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition

    cpcs = client.cpcs.list()
    cpc_names = [cpc.name for cpc in cpcs]

    for cpc_name in hd.cpcs:
        def_cpc_props = dict(hd.cpcs[cpc_name])

        print(f"Checking CPC {cpc_name}")

        assert cpc_name in cpc_names, (
            f"CPC {cpc_name} defined in inventory file for HMC {hd.nickname!r} "
            f"at {hd.host} is not managed by that HMC. Actually managed "
            f"CPCs: {', '.join(cpc_names)}")

        cpc = client.cpcs.find(name=cpc_name)

        try:
            cpc.pull_full_properties()
        except zhmcclient.ConnectionError as exc:
            print(f"Cannot retrieve properties for CPC {cpc_name} "
                  f"(skipping it): {exc.__class__.__name__}: {exc}")
            continue

        cpc_props = dict(cpc.properties)
        for def_prop_name in def_cpc_props:

            if not is_cpc_property_hmc_inventory(def_prop_name):
                continue

            hmc_prop_name = def_prop_name.replace('_', '-')
            assert hmc_prop_name in cpc_props, (
                f"Property {def_prop_name!r} defined in inventory file for "
                f"CPC {cpc_name} for HMC {hd.nickname!r} does not actually "
                f"exist on that CPC (as {hmc_prop_name!r})")

            cpc_value = cpc_props[hmc_prop_name]
            def_cpc_value = def_cpc_props[def_prop_name]
            assert def_cpc_value == cpc_value, (
                f"Property {def_prop_name!r} defined in inventory file for "
                f"CPC {cpc_name} for HMC {hd.nickname!r} has an unexpected "
                f"value: inventory file: {def_cpc_value!r}, actual value: "
                f"{cpc_value!r}")


@pytest.mark.skip   # Disabled by default
def test_hmcdef_check_all_hmcs():
    """
    Check out the HMCs specified in the HMC inventory file.
    Skip HMCs that cannot be contacted.
    """
    hmcdefs = HMCDefinitions()
    hd_list = hmcdefs.list_all_hmcs()

    rt_config = zhmcclient.RetryTimeoutConfig(
        connect_timeout=10,
        connect_retries=1,
        read_timeout=30,
    )

    # Check real HMCs and their CPCs
    for hd in hd_list:

        if hd.mock_file:
            print(f"Skipping mocked HMC {hd.nickname!r}")
            continue

        for cpc_name in hd.cpcs:

            print(f"Checking CPC {cpc_name} defined for HMC {hd.nickname!r} at "
                  f"{hd.host}")

            session = zhmcclient.Session(
                hd.host, hd.userid, hd.password,
                verify_cert=hd.verify_cert,
                retry_timeout_config=rt_config)

            try:
                client = zhmcclient.Client(session)

                try:
                    session.logon()
                except zhmcclient.ConnectionError as exc:
                    print(f"Cannot logon to HMC at {hd.host} (skipping it): "
                          f"{exc.__class__.__name__}: {exc}")
                    continue

                cpcs = client.cpcs.list()
                cpc_names = [cpc.name for cpc in cpcs]

                assert cpc_name in cpc_names, (
                    f"CPC {cpc_name} defined in inventory file for HMC "
                    f"{hd.nickname!r} at {hd.host} is not managed by that "
                    f"HMC. Actually managed CPCs: {', '.join(cpc_names)}")

            finally:
                session.logoff()
