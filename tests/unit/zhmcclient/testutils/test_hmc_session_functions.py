# Copyright 2025 IBM Corp. All Rights Reserved.
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
Unit tests for testutils._hmc_session_functions module.
"""


import os
import re
import pytest

from zhmcclient.testutils._hmc_session_functions import run_password_command
from zhmcclient import PasswordCommandFailure

# Command delimiter in the shell
DELIM = "&" if os.name == 'nt' else ";"

# echo command to print a space and NL
# On Windows, a command sequence for that was not found, so only NL is printed.
ECHO_SPACE_NL = "echo." if os.name == 'nt' else "echo ' '"

# Command to sleep for 2 seconds
SLEEP_2 = "ping -n 3 127.0.0.1 >nul" if os.name == 'nt' else "sleep 2"

# Test cases for test_run_password_command()
TESTCASES_RUN_PASSWORD_COMMAND = [
    # Format:
    # * desc: Testcase description
    # * input_kwargs: Input args for run_password_command()
    # * exp_password: Expected resulting password
    # * exp_exc_type: Expected exception type, or None for success
    # * exp_exc_msg: Expected exception message regex pattern
    (
        "Command with literal string",
        dict(
            command="echo mypw",
            variables=dict(host="myhost", userid="myuserid"),
            timeout=10,
        ),
        "mypw",
        None, None
    ),
    (
        "Command with host and userid variables",
        dict(
            command="echo {host}-{userid}-mypw",
            variables=dict(host="myhost", userid="myuserid"),
            timeout=10,
        ),
        "myhost-myuserid-mypw",
        None, None
    ),
    (
        "Command returns password with leading and trailing space and NL",
        dict(
            # On Windows, the quotes for echo must be double quotes
            command="{es}{d}echo mypw{d}{es}".format(
                d=DELIM, es=ECHO_SPACE_NL),
            variables=dict(host="myhost", userid="myuserid"),
            timeout=10,
        ),
        "mypw",
        None, None
    ),
    (
        "Invalid command",
        dict(
            command="foo_invalid",
            variables=dict(host="myhost", userid="myuserid"),
            timeout=10,
        ),
        None,
        PasswordCommandFailure,
        "Password command .* failed .*(not found|command not found|not "
        "recognized as an internal or external command)"
    ),
    (
        "Command returns non-zero exit code and stderr",
        dict(
            command="echo foo 1>&2{d}exit 42".format(d=DELIM),
            variables=dict(host="myhost", userid="myuserid"),
            timeout=10,
        ),
        None,
        PasswordCommandFailure,
        "Password command .* failed with exit code 42: foo"
    ),
    (
        "Command returns password with space inside",
        dict(
            command="echo 'foo bar'",
            variables=dict(host="myhost", userid="myuserid"),
            timeout=10,
        ),
        None,
        PasswordCommandFailure,
        r"Password command .* succeeded but its standard output contains "
        "whitespace characters"
    ),
    (
        "Command that times out",
        dict(
            command="{s2}{d}echo mypw".format(d=DELIM, s2=SLEEP_2),
            variables=dict(host="myhost", userid="myuserid"),
            timeout=1,
        ),
        None,
        PasswordCommandFailure,
        r"Password command .* timed out after 1 s"
    ),
]


@pytest.mark.parametrize(
    "desc, input_kwargs, exp_password, exp_exc_type, exp_exc_msg",
    TESTCASES_RUN_PASSWORD_COMMAND)
def test_run_password_command(
        desc, input_kwargs, exp_password, exp_exc_type, exp_exc_msg):
    # pylint: disable=unused-argument,invalid-name
    """
    Test function for run_password_command().
    """

    if exp_exc_type:
        with pytest.raises(exp_exc_type) as exc_info:

            # The function to be tested
            run_password_command(**input_kwargs)

        exc = exc_info.value
        assert isinstance(exc, exp_exc_type)
        assert re.match(exp_exc_msg, str(exc))

    else:

        # The function to be tested
        password = run_password_command(**input_kwargs)
        assert password == exp_password
