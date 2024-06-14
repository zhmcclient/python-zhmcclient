# Copyright 2022 IBM Corp. All Rights Reserved.
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
Unit tests for testutils._hmc_definitions module.
"""


import os
import tempfile
import pytest

from zhmcclient.testutils._hmc_definitions import HMCDefinitions, \
    HMCNoVaultError, HMCNotFound

# Test cases for all methods and properties of HMCDefinitions.
TESTCASES_HMC_DEFINITIONS_ALL = [
    # Format:
    # * desc: Testcase description
    # * inv_data: String with data of the HMC inventory file to test
    # * vault_data: String with data of the HMC vault file to test
    # * testhmc: Group or host name of the HMCs to be tested
    # * exp_hmc_defs: Dict of expected HMCDefinition properties
    # * exp_init_exc_type: Expected exception type during init, or None
    # * exp_list_exc_type: Expected exception type during list, or None
    (
        "Empty inventory and vault files",
        """
all:
  hosts:
        """,
        """
hmc_auth:
        """,
        None,
        {
            "all": {},
        },
        None, None
    ),
    (
        "One real HMC with all properties",
        """
all:
  hosts:
    host1:
      description: host1
      contact: contact1
      access_via: Intranet
      ansible_host: 1.2.3.1
      cpcs:
        CPC1:
          dpm_enabled: true
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
    verify: true
    ca_certs: mycerts.pem
        """,
        None,
        {
            "all": {
                "host1": {
                    "description": "host1",
                    "contact": "contact1",
                    "access_via": "Intranet",
                    "mock_file": None,
                    "host": "1.2.3.1",
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": "mycerts.pem",
                    "cpcs": {
                        "CPC1": {
                            "dpm_enabled": True,
                        },
                    },
                    "add_vars": {},
                },
            },
        },
        None, None
    ),
    (
        "One real HMC with minimal properties",
        """
all:
  hosts:
    host1:
      ansible_host: 1.2.3.1
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        None,
        {
            "all": {
                "host1": {
                    "description": "",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {},
                },
            },
        },
        None, None
    ),
    (
        "One mocked HMC with all properties",
        """
all:
  hosts:
    host1:
      description: host1
      contact: contact1
      access_via: Intranet
      mock_file: host1_mock.yaml
      cpcs:
        CPC1:
          dpm_enabled: true
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        None,
        {
            "all": {
                "host1": {
                    "description": "host1",
                    "contact": "contact1",
                    "access_via": "Intranet",
                    "host": None,
                    "mock_file": "host1_mock.yaml",
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {
                        "CPC1": {
                            "dpm_enabled": True,
                        },
                    },
                    "add_vars": {},
                },
            },
        },
        None, None
    ),
    (
        "One mocked HMC with minimal properties",
        """
all:
  hosts:
    host1:
      mock_file: host1_mock.yaml
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        None,
        {
            "all": {
                "host1": {
                    "description": "",
                    "contact": "",
                    "access_via": "",
                    "host": None,
                    "mock_file": "host1_mock.yaml",
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {},
                },
            },
        },
        None, None
    ),
    (
        "One real HMC that is used in a child group without overridden props",
        """
all:
  hosts:
    host1:
      description: desc1
      ansible_host: 1.2.3.1
  children:
    group1:
      hosts:
        host1:
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        None,
        {
            "all": {
                "host1": {
                    "description": "desc1",
                    "host": "1.2.3.1",
                    "userid": "userid1",
                    "password": "password1",
                },
            },
            "group1": {
                "host1": {
                    "description": "desc1",
                    "host": "1.2.3.1",
                    "userid": "userid1",
                    "password": "password1",
                },
            },
        },
        None, None
    ),
    (
        "One real HMC that is used in a child group and overrides all props",
        """
all:
  hosts:
    host1:
      description: desc_parent
      ansible_host: 1.2.3.1
      contact: contact_parent
      access_via: access_via_parent
      cpcs:
        CPC1:
          dpm_enabled: true
  children:
    group1:
      hosts:
        host1:
          description: desc_child
          ansible_host: 2.2.3.1
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
    verify: true
    ca_certs: mycerts.pem
        """,
        None,
        {
            "all": {
                "host1": {
                    "description": "desc_parent",
                    "host": "1.2.3.1",
                    "contact": "contact_parent",
                    "access_via": "access_via_parent",
                    "cpcs": {
                        "CPC1": {
                            "dpm_enabled": True,
                        },
                    },
                    "add_vars": {},
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": "mycerts.pem",
                },
            },
            "group1": {
                "host1": {
                    "description": "desc_child",
                    "host": "2.2.3.1",
                    "contact": "contact_parent",
                    "access_via": "access_via_parent",
                    "cpcs": {
                        "CPC1": {
                            "dpm_enabled": True,
                        },
                    },
                    "add_vars": {},
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": "mycerts.pem",
                },
            },
        },
        None, None
    ),
    (
        "One mocked HMC that is used in a child group without overridden props",
        """
all:
  hosts:
    host1:
      description: desc1
      mock_file: mymock.yaml
  children:
    group1:
      hosts:
        host1:
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        None,
        {
            "all": {
                "host1": {
                    "description": "desc1",
                    "host": None,
                    "mock_file": "mymock.yaml",
                    "userid": "userid1",
                    "password": "password1",
                },
            },
            "group1": {
                "host1": {
                    "description": "desc1",
                    "host": None,
                    "mock_file": "mymock.yaml",
                    "userid": "userid1",
                    "password": "password1",
                },
            },
        },
        None, None
    ),
    (
        "One real HMC with missing corresponding vault file entry",
        """
all:
  hosts:
    host1:
      ansible_host: 1.2.3.1
        """,
        """
hmc_auth:
  host2:
    userid: userid2
    password: password2
        """,
        None,
        None,
        HMCNoVaultError, None
    ),
    (
        "One real HMC with incorrect testhmc",
        """
all:
  hosts:
    host1:
      ansible_host: 1.2.3.1
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        "host2",
        None,
        None, HMCNotFound
    ),
    (
        "One host and one child group with a second host",
        """
all:
  hosts:
    host1:
      description: host1
      ansible_host: 1.2.3.1
  children:
    east:
      hosts:
        1.2.3.2:
          description: host2
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
  1.2.3.2:
    userid: userid2
    password: password2
        """,
        'host1',
        {
            "all": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {},
                },
                "1.2.3.2": {
                    "description": "host2",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.2",
                    "mock_file": None,
                    "userid": "userid2",
                    "password": "password2",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {},
                },
            },
            "east": {
                "1.2.3.2": {
                    "description": "host2",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.2",
                    "mock_file": None,
                    "userid": "userid2",
                    "password": "password2",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {},
                },
            },
        },
        None, None
    ),
    (
        "Additional variables at top level host",
        """
all:
  hosts:
    host1:
      description: host1
      ansible_host: 1.2.3.1
      var1: value1
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        'host1',
        {
            "all": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {
                        "var1": "value1",
                    },
                },
            },
        },
        None, None
    ),
    (
        "Variables at top level propagated to top-level hosts",
        """
all:
  hosts:
    host1:
      description: host1
      ansible_host: 1.2.3.1
  vars:
    var1: value1
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        'host1',
        {
            "all": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {
                        "var1": "value1",
                    },
                },
            },
        },
        None, None
    ),
    (
        "Variables at top level propagated to top-level hosts and child hosts",
        """
all:
  hosts:
    host1:
      description: host1
      ansible_host: 1.2.3.1
  vars:
    var1: value1
  children:
    east:
      hosts:
        host1:
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        'host1',
        {
            "all": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {
                        "var1": "value1",
                    },
                },
            },
            "east": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {
                        "var1": "value1",
                    },
                },
            },
        },
        None, None
    ),
    (
        "Variables at top level overridden at child group level and propagated",
        """
all:
  hosts:
    host1:
      description: host1
      ansible_host: 1.2.3.1
  vars:
    var1: value1
  children:
    east:
      hosts:
        host1:
      vars:
        var1: value2
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        'host1',
        {
            "all": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {
                        "var1": "value1",
                    },
                },
            },
            "east": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {
                        "var1": "value2",
                    },
                },
            },
        },
        None, None
    ),
    (
        "Variables at top level overridden at top host level",
        """
all:
  hosts:
    host1:
      description: host1
      ansible_host: 1.2.3.1
      var1: value2
  vars:
    var1: value1
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        'host1',
        {
            "all": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {
                        "var1": "value2",
                    },
                },
            },
        },
        None, None
    ),
    (
        "Variables at top level overridden at child group level and again at "
        "child host level",
        """
all:
  hosts:
    host1:
      description: host1
      ansible_host: 1.2.3.1
  vars:
    var1: value1
  children:
    east:
      hosts:
        host1:
          var1: value3
      vars:
        var1: value2
        """,
        """
hmc_auth:
  host1:
    userid: userid1
    password: password1
        """,
        'host1',
        {
            "all": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {
                        "var1": "value1",
                    },
                },
            },
            "east": {
                "host1": {
                    "description": "host1",
                    "contact": "",
                    "access_via": "",
                    "host": "1.2.3.1",
                    "mock_file": None,
                    "userid": "userid1",
                    "password": "password1",
                    "verify": True,
                    "ca_certs": None,
                    "cpcs": {},
                    "add_vars": {
                        "var1": "value3",
                    },
                },
            },
        },
        None, None
    ),
]


@pytest.mark.parametrize(
    "desc, inv_data, vault_data, testhmc, exp_hmc_defs, exp_init_exc_type, "
    "exp_list_exc_type",
    TESTCASES_HMC_DEFINITIONS_ALL)
def test_HMCDefinitions_all(
        desc, inv_data, vault_data, testhmc, exp_hmc_defs, exp_init_exc_type,
        exp_list_exc_type):
    # pylint: disable=unused-argument,invalid-name
    """
    Test function for all methods and properties of HMCDefinitions.
    """

    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False) as tf_inv:
        tf_inv.write(inv_data)

    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False) as tf_vault:
        tf_vault.write(vault_data)

    try:
        if exp_init_exc_type:
            with pytest.raises(exp_init_exc_type) as exc_info:

                # The function to be tested
                HMCDefinitions(
                    inventory_file=tf_inv.name, vault_file=tf_vault.name,
                    testhmc=testhmc, load=True)

            exc = exc_info.value
            assert isinstance(exc, exp_init_exc_type)

        elif exp_list_exc_type:

            # The function to be tested
            hmc_defs = HMCDefinitions(
                inventory_file=tf_inv.name, vault_file=tf_vault.name,
                testhmc=testhmc, load=True)

            with pytest.raises(exp_list_exc_type) as exc_info:

                # The function to be tested
                hmc_defs.list_hmcs(testhmc)

            exc = exc_info.value
            assert isinstance(exc, exp_list_exc_type)

        else:  # success

            # The function to be tested
            hmc_defs = HMCDefinitions(
                inventory_file=tf_inv.name, vault_file=tf_vault.name,
                testhmc=testhmc, load=True)

            # The function to be tested
            group_names = hmc_defs.group_names

            for group_name in group_names:

                # The function to be tested
                hd_list = hmc_defs.list_hmcs(group_name)

                assert_hmcdefs(group_name, hd_list, exp_hmc_defs)

            # The function to be tested
            hd_list = hmc_defs.list_all_hmcs()

            assert_hmcdefs('all', hd_list, exp_hmc_defs)

    finally:
        os.remove(tf_inv.name)
        os.remove(tf_vault.name)


def assert_hmcdefs(group_name, hd_list, exp_hmc_defs):
    """
    Check a HMC definition list for a particular group name.

    This accesses and thus tests further properties of the HMCDefinitions class.
    """
    assert group_name in exp_hmc_defs

    exp_props_dict = exp_hmc_defs[group_name]
    for hd in hd_list:

        # The function to be tested
        nickname = hd.nickname
        assert nickname in exp_props_dict

        exp_props = exp_props_dict[nickname]

        if 'description' in exp_props:
            # The function to be tested
            description = hd.description
            assert description == exp_props['description']

        if 'contact' in exp_props:
            # The function to be tested
            contact = hd.contact
            assert contact == exp_props['contact']

        if 'host' in exp_props:
            # The function to be tested
            host = hd.host
            assert host == exp_props['host']

        if 'userid' in exp_props:
            # The function to be tested
            userid = hd.userid
            assert userid == exp_props['userid']

        if 'password' in exp_props:
            # The function to be tested
            password = hd.password
            assert password == exp_props['password']

        if 'verify' in exp_props:
            # The function to be tested
            verify = hd.verify
            assert verify == exp_props['verify']

        if 'ca_certs' in exp_props:
            # The function to be tested
            ca_certs = hd.ca_certs
            assert ca_certs == exp_props['ca_certs']

        if 'cpcs' in exp_props:
            # The function to be tested
            cpcs = hd.cpcs
            assert cpcs == exp_props['cpcs']

        if 'add_vars' in exp_props:
            # The function to be tested
            add_vars = hd.add_vars
            assert add_vars == exp_props['add_vars']
