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
End2end tests for CPCs that do not change anything.
"""

from __future__ import absolute_import, print_function

import requests.packages.urllib3
import zhmcclient
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils.cpc_fixtures import all_cpcs  # noqa: F401

requests.packages.urllib3.disable_warnings()

# Detect machine generation from machine type
MACHINE_GENERATIONS = {
    '2817': 'gen11',  # z196
    '2818': 'gen11',  # z114
    '2827': 'gen12',  # EC12
    '2828': 'gen12',  # BC12
    '2964': 'gen13',  # z13
    '2965': 'gen13',  # z13s
    '3906': 'gen14',  # z14
    '3907': 'gen14',  # z14-ZR1 (MR)
}

# Properties in Cpc objects returned by List CPC Objects
PROPS_CPC_LIST = {
    'gen11': ['object-uri', 'name', 'status'],
    'gen12': ['object-uri', 'name', 'status'],
    'gen13': ['object-uri', 'name', 'status'],
    'gen14': ['object-uri', 'name', 'status', 'has-unacceptable-status',
              'dpm-enabled', 'se-version'],
}

# Properties in minimalistic Cpc objects
PROPS_CPC_MINIMAL = ['object-uri', 'name']


def assert_cpc_minimal(cpc, exp_name, exp_prop_names):
    act_prop_names = cpc.properties.keys()

    for prop_name in exp_prop_names:
        assert prop_name in act_prop_names, \
            "CPC {0}".format(exp_name)

    assert cpc.properties['name'] == exp_name, \
        "CPC {0}".format(exp_name)
    assert cpc.name == exp_name, \
        "CPC {0}".format(exp_name)


# Printing is disabled by default, rename to test_...() to enable it.
def disabled_test_print_cpcs(all_cpcs):  # noqa: F811
    """
    Print some information about the CPCs under test.
    """
    for cpc in sorted(all_cpcs, key=lambda obj: obj.name):

        hd = cpc.manager.client.session.hmc_definition

        print("")
        print("CPC {} on HMC {}:".format(cpc.name, hd.nickname))

        if cpc.dpm_enabled:

            print("  Partitions:")
            partitions = cpc.partitions.list()
            for partition in sorted(partitions, key=lambda obj: obj.name):
                print("    {}".format(partition.name))

            print("  Adapters:")
            adapters = cpc.adapters.list()
            for adapter in sorted(adapters, key=lambda obj: obj.name):
                print("    {}".format(adapter.name))

        else:

            print("  LPARs:")
            lpars = cpc.lpars.list()
            for lpar in sorted(lpars, key=lambda obj: obj.name):
                print("    {}".format(lpar.name))

            print("  Reset profiles:")
            reset_profiles = cpc.reset_activation_profiles.list()
            for reset_profile in sorted(reset_profiles,
                                        key=lambda obj: obj.name):
                print("    {}".format(reset_profile.name))

            print("  Load profiles:")
            load_profiles = cpc.load_activation_profiles.list()
            for load_profile in sorted(load_profiles,
                                       key=lambda obj: obj.name):
                print("    {}".format(load_profile.name))

            print("  Image profiles:")
            image_profiles = cpc.image_activation_profiles.list()
            for image_profile in sorted(image_profiles,
                                        key=lambda obj: obj.name):
                print("    {}".format(image_profile.name))


def test_cpc_find_by_name(hmc_session):  # noqa: F811
    """
    Test that all CPCs in the HMC definition can be found using find_by_name().
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for def_name in hd.cpcs:

        # The code to be tested
        cpc = client.cpcs.find_by_name(def_name)

        assert_cpc_minimal(cpc, def_name, PROPS_CPC_MINIMAL)


def test_cpc_find_with_name(hmc_session):  # noqa: F811
    """
    Test that all CPCs in the HMC definition can be found using find()
    with the name as a filter argument.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for def_name in hd.cpcs:

        # The code to be tested
        found_cpc = client.cpcs.find(name=def_name)

        assert_cpc_minimal(found_cpc, def_name, PROPS_CPC_MINIMAL)


def test_cpc_findall_with_name(hmc_session):  # noqa: F811
    """
    Test that all CPCs in the HMC definition can be found using findall()
    with the name as a filter argument.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for def_name in hd.cpcs:

        # The code to be tested
        found_cpcs = client.cpcs.findall(name=def_name)

        assert len(found_cpcs) == 1
        found_cpc = found_cpcs[0]
        assert_cpc_minimal(found_cpc, def_name, PROPS_CPC_MINIMAL)


def test_cpc_list_with_name(hmc_session):  # noqa: F811
    """
    Test that all CPCs in the HMC definition can be found using list()
    with the name as a filter argument.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for def_name in hd.cpcs:

        # The code to be tested
        found_cpcs = client.cpcs.list(filter_args=dict(name=def_name))

        exp_prop_names = []
        def_machine_type = hd.cpcs[def_name].get('machine_type', None)
        if def_machine_type:
            gen = MACHINE_GENERATIONS.get(def_machine_type, None)
            if gen:
                exp_prop_names = PROPS_CPC_LIST[gen]

        assert len(found_cpcs) == 1
        found_cpc = found_cpcs[0]
        assert_cpc_minimal(found_cpc, def_name, exp_prop_names)


def test_cpc_list_with_name_full(hmc_session):  # noqa: F811
    """
    Test that all CPCs in the HMC definition can be found using list()
    with full properties and the name as a filter argument.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for def_name in hd.cpcs:

        # The code to be tested
        found_cpcs = client.cpcs.list(filter_args=dict(name=def_name),
                                      full_properties=True)

        exp_prop_names = []
        def_machine_type = hd.cpcs[def_name].get('machine_type', None)
        if def_machine_type:
            gen = MACHINE_GENERATIONS.get(def_machine_type, None)
            if gen:
                exp_prop_names = PROPS_CPC_LIST[gen]

        assert len(found_cpcs) == 1
        found_cpc = found_cpcs[0]
        assert_cpc_minimal(found_cpc, def_name, exp_prop_names)
