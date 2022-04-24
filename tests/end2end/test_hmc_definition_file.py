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

from requests.packages import urllib3

import zhmcclient
# pylint: disable=unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401
from zhmcclient.testutils import hmc_definition_file

urllib3.disable_warnings()


def test_hmcdef_cpcs(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test that the HMC actually manages the CPCs defined in its HMC definition
    and that these CPCs actually have the properties defined there.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition

    cpcs = client.cpcs.list()
    cpc_names = [cpc.name for cpc in cpcs]

    for cpc_name in hd.cpcs:
        def_cpc_props = dict(hd.cpcs[cpc_name])

        print("Checking CPC {c} defined in HMC definition file".
              format(c=cpc_name))

        assert cpc_name in cpc_names, \
            "CPC {c} defined for HMC {n} at {h} in HMC definition " \
            "file is not managed by that HMC. Actually managed " \
            "CPCs: {cl}". \
            format(c=cpc_name, n=hd.nickname, h=hd.hmc_host,
                   cl=', '.join(cpc_names))

        cpc = client.cpcs.find(name=cpc_name)

        try:
            cpc.pull_full_properties()
        except zhmcclient.ConnectionError as exc:
            print("Cannot retrieve properties for CPC {c} (skipping it): "
                  "{e}: {m}".
                  format(c=cpc_name, e=exc.__class__.__name__, m=exc))
            continue

        cpc_props = dict(cpc.properties)
        for def_prop_name in def_cpc_props:

            hmc_prop_name = def_prop_name.replace('_', '-')
            assert hmc_prop_name in cpc_props, \
                "Property {dp!r} defined for CPC {c} in HMC nickname {n!r} " \
                "in HMC definition file does not actually exist on that CPC " \
                "(as {hp!r})". \
                format(dp=def_prop_name, hp=hmc_prop_name, c=cpc_name,
                       n=hd.nickname)

            cpc_value = cpc_props[hmc_prop_name]
            def_cpc_value = def_cpc_props[def_prop_name]
            assert def_cpc_value == cpc_value, \
                "Property {dp!r} defined for CPC {c} in HMC nickname {n!r} " \
                "in HMC definition file has an unexpected value: " \
                "HMC definition file: {dv!r}, actual value: {hv!r}". \
                format(dp=def_prop_name, c=cpc_name, n=hd.nickname,
                       dv=def_cpc_value, hv=cpc_value)


def test_hmcdef_check_all_hmcs():
    """
    Check out the HMCs specified in the HMC definition file.
    Skip HMCs that cannot be contacted.
    """
    def_file = hmc_definition_file()
    hmc_defs = def_file.list_all_hmcs()

    rt_config = zhmcclient.RetryTimeoutConfig(
        connect_timeout=10,
        connect_retries=1,
        read_timeout=30,
    )

    # Check real HMCs and their CPCs
    for hd in hmc_defs:

        if hd.hmc_host is None:
            print("Skipping faked HMC {n} defined in HMC definition file".
                  format(n=hd.nickname))
            continue

        for cpc_name in hd.cpcs:

            print("Checking CPC {c} defined for HMC {n} at {h} in HMC "
                  "definition file".
                  format(c=cpc_name, n=hd.nickname, h=hd.hmc_host))

            session = zhmcclient.Session(
                hd.hmc_host, hd.hmc_userid, hd.hmc_password,
                verify_cert=hd.hmc_verify_cert,
                retry_timeout_config=rt_config)

            try:
                client = zhmcclient.Client(session)

                try:
                    session.logon()
                except zhmcclient.ConnectionError as exc:
                    print("Cannot logon to HMC {h} (skipping it): {e}: {m}".
                          format(h=hd.hmc_host,
                                 e=exc.__class__.__name__, m=exc))
                    continue

                cpcs = client.cpcs.list()
                cpc_names = [cpc.name for cpc in cpcs]

                assert cpc_name in cpc_names, \
                    "CPC {c} defined for HMC {n} at {h} in HMC definition " \
                    "file is not managed by that HMC. Actually managed " \
                    "CPCs: {cl}". \
                    format(c=cpc_name, n=hd.nickname, h=hd.hmc_host,
                           cl=', '.join(cpc_names))

            finally:
                session.logoff()
