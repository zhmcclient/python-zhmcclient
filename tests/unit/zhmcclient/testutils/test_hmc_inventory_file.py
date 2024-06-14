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
Unit tests for testutils._hmc_inventory_file module.
"""


import os
import tempfile
import pytest

from zhmcclient.testutils._hmc_inventory_file import HMCInventoryFile, \
    HMCInventoryFileError


# Test cases for HMCInventoryFile.__init__()
TESTCASES_HMC_INVENTORY_FILE_INIT = [
    # Format:
    # * desc: Testcase description
    # * file_data: String with data of the HMC inventory file to test
    # * exp_exc_type: Expected exception type, or None for success
    (
        "Typical inventory file",
        """
all:
  hosts:
    globalservices:  # host alias
      description: bla
      contact: bla
      access_via: bla
      ansible_host: 1.2.3.4
      cpcs:
        CPC1:
          dpm_mode: true
      extra_host_var1: bla
    global.services.com:  # host DNS name
      description: bla
      contact: bla
      access_via: bla
      cpcs:
        CPC1:
          dpm_mode: true
      extra_host_var1: bla
    1.2.3.4:  # IPv4 address
      extra_host_var1: bla
    "01:02:03:04:0a::0d":  # IPv6 address
      extra_host_var1: bla
  vars:
    extra_group_var1: bla
  children:
    east:
      hosts:
        1.2.3.5:
          description: bla
      vars:
        extra_group_var1: bla
      children:
        dbserver:
          hosts:
            1.2.3.6:
              extra_group_var1: bla
        """,
        None
    ),
    (
        "DNS hostname without variables",
        """
all:
  hosts:
    app.services.com:
        """,
        None
    ),
    (
        "DNS hostname with numeric range - not supported",
        """
all:
  hosts:
    app[1:20:2].services.com:
        """,
        HMCInventoryFileError
    ),
    (
        "DNS hostname with alphabetic range - not supported",
        """
all:
  hosts:
    app[a:f].services.com:
        """,
        HMCInventoryFileError
    ),
    (
        "Top-level group with empty hosts, vars, children",
        """
all:
  hosts:
  vars:
  children:
        """,
        None
    ),
    (
        "Empty top-level group",
        """
all:
        """,
        None
    ),
    (
        "Schema validation error: Required top-level element missing",
        """
xx:
        """,
        HMCInventoryFileError
    ),
    (
        "Schema validation error: Invalid additional element",
        """
all:
  xx:
        """,
        HMCInventoryFileError
    ),
    (
        "Schema validation error: List instead of dict",
        """
all: []
        """,
        HMCInventoryFileError
    ),
    (
        "YAML scanner error",
        """
all: xx: yy:
        """,
        HMCInventoryFileError
    ),
    (
        "YAML parser error",
        """
 all: x
xx: x
        """,
        HMCInventoryFileError
    ),
]


@pytest.mark.parametrize(
    "desc, file_data, exp_exc_type",
    TESTCASES_HMC_INVENTORY_FILE_INIT)
def test_HMCInventoryFile_init(desc, file_data, exp_exc_type):
    # pylint: disable=unused-argument,invalid-name
    """
    Test function for HMCInventoryFile.__init__().
    """

    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False) as tf:
        tf.write(file_data)

    try:
        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The function to be tested
                HMCInventoryFile(tf.name)

            exc = exc_info.value
            assert isinstance(exc, exp_exc_type)

        else:

            # The function to be tested
            _ = HMCInventoryFile(tf.name)

    finally:
        os.remove(tf.name)
