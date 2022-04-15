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
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

urllib3.disable_warnings()


def test_cpc_definitions(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test that the HMC manages the CPCs in the HMC definition and that they
    have the attributes defined there.
    """
    client = zhmcclient.Client(hmc_session)
    cpcs = client.cpcs.list()
    cpc_names = [cpc.name for cpc in cpcs]

    hd = hmc_session.hmc_definition
    for cpc_name in hd.cpcs:

        def_cpc_props = dict(hd.cpcs[cpc_name])
        assert cpc_name in cpc_names, \
            "CPC '{c}' defined in HMC definition file is not managed by " \
            "the HMC".format(c=cpc_name)

        cpc = client.cpcs.find(name=cpc_name)
        cpc.pull_full_properties()

        cpc_props = dict(cpc.properties)
        for def_prop_name in def_cpc_props:

            hmc_prop_name = def_prop_name.replace('_', '-')
            assert hmc_prop_name in cpc_props, \
                "Property '{dp}' defined in HMC definition file does not " \
                "exist in CPC '{c}' (as '{hp}')". \
                format(dp=def_prop_name, hp=hmc_prop_name, c=cpc_name)

            cpc_value = cpc_props[hmc_prop_name]
            def_cpc_value = def_cpc_props[def_prop_name]
            assert def_cpc_value == cpc_value, \
                "Unexpected value for property '{dp}' in CPC '{c}': " \
                "HMC definition file: {dv!r}, CPC: {hv!r}". \
                format(dp=def_prop_name, c=cpc_name, dv=def_cpc_value,
                       hv=cpc_value)
