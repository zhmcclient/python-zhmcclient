# Copyright 2026 IBM Corp. All Rights Reserved.
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
Utility functions for testing (for all types of test).
"""

import enum
import pytest


class RunMode(enum.Enum):
    """
    An indicator for parametrized testcases on what to do with the testcase.
    """
    RUN = "run"       # Run the testcase and expect it to pass
    XFAIL = "xfail"   # Run the testcase and expect it to fail
    SKIP = "skip"     # Skip the testcase
    PDB = "pdb"       # Invoke the pdb debugger in the test function


def handle_runmode(request, runmode):
    """
    Handle the run mode of a testcase.

    Parameters:

      request (pytest.Request): Pytest request for the test function call.
        This can be obtained by the test function by specifying the 'request'
        fixture as a parameter.

      runmode (RunMode): Run mode of the testcase.
    """
    if runmode == RunMode.SKIP:
        pytest.skip("Testcase marked with RunMode.SKIP")
    elif runmode == RunMode.XFAIL:
        request.node.add_marker(
            pytest.mark.xfail(reason="Testcase marked with RunMode.XFAIL"))
    elif runmode == RunMode.PDB:
        # pylint: disable=forgotten-debug-statement
        breakpoint()   # return to get into the test function
    else:
        assert runmode == RunMode.RUN
