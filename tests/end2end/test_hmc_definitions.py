# Copyright 2019 IBM Corp. All Rights Reserved.
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

import requests.packages.urllib3

import zhmcclient
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501

requests.packages.urllib3.disable_warnings()


def test_cpc_definitions(hmc_session):  # noqa: F811
    """
    Test that the HMC manages the CPCs in the HMC definition and that they
    have the attributes defined there.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for def_name in hd.cpcs:
        def_cpc_dict = hd.cpcs[def_name]
        def_machine_type = def_cpc_dict.get('machine_type', None)
        def_dpm_enabled = def_cpc_dict.get('dpm', None)

        act_cpcs = client.cpcs.list()
        act_names = [cpc.name for cpc in act_cpcs]
        assert def_name in act_names, \
            "CPC {0}".format(def_name)

        act_cpc = client.cpcs.find(name=def_name)

        if def_dpm_enabled is not None:
            act_dpm_enabled = act_cpc.dpm_enabled
            assert def_dpm_enabled == act_dpm_enabled, \
                "CPC {0}".format(def_name)

        if def_machine_type is not None:
            act_machine_type = act_cpc.get_property('machine-type')
            assert def_machine_type == act_machine_type, \
                "CPC {0}".format(def_name)
