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
Unit tests for testutils._hmc_vault_file module.
"""


import os
import tempfile
import pytest

from zhmcclient.testutils._hmc_vault_file import HMCVaultFile, \
    HMCVaultFileError


# Test cases for HMCVaultFile.__init__()
TESTCASES_HMC_VAULT_FILE_INIT = [
    # Format:
    # * desc: Testcase description
    # * file_data: String with data of the HMC vault file to test
    # * exp_exc_type: Expected exception type, or None for success
    (
        "No HMCs in vault file",
        """
hmc_auth:
        """,
        None
    ),
    (
        "One HMC with all variables",
        """
hmc_auth:
  east1:
    userid: my_userid
    password: my_password
    verify: true
    ca_certs: my_cert.pem
        """,
        None
    ),
    (
        "One HMC with minimal set of variables",
        """
hmc_auth:
  east1:
    userid: my_userid
    password: my_password
        """,
        None
    ),
    (
        "Two HMCs, and global variable",
        """
hmc_auth:
  east1:
    userid: my_userid
    password: my_password
    verify: true
    ca_certs: my_cert.pem
  east2:
    userid: my_userid2
    password: my_password2
    verify: false
var1: value1
        """,
        None
    ),
    (
        "Schema validation error: Required top-level element missing",
        """
xx:
        """,
        HMCVaultFileError
    ),
    (
        "Schema validation error: List instead of dict",
        """
hmc_auth: []
        """,
        HMCVaultFileError
    ),
    (
        "YAML scanner error",
        """
hmc_auth: xx: yy:
        """,
        HMCVaultFileError
    ),
    (
        "YAML parser error",
        """
 hmc_auth: x
xx: x
        """,
        HMCVaultFileError
    ),
]


@pytest.mark.parametrize(
    "desc, file_data, exp_exc_type",
    TESTCASES_HMC_VAULT_FILE_INIT)
def test_HMCVaultFile_init(desc, file_data, exp_exc_type):
    # pylint: disable=unused-argument,invalid-name
    """
    Test function for HMCVaultFile.__init__().
    """

    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False) as tf:
        tf.write(file_data)

    try:
        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The function to be tested
                HMCVaultFile(tf.name)

            exc = exc_info.value
            assert isinstance(exc, exp_exc_type)

        else:

            # The function to be tested
            _ = HMCVaultFile(tf.name)

    finally:
        os.remove(tf.name)
