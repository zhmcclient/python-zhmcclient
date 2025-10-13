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
Unit tests for the deprecated zhmcclient_mock module.
"""


import importlib
import sys
import pytest


def test_zhmcclient_mock_deprecated():
    """
    Test that zhmcclient_mock can still be imported but issues a
    DeprecationWarning.
    """

    # Remove cached import to force a fresh import
    sys.modules.pop("zhmcclient_mock", None)

    with pytest.warns(
            DeprecationWarning,
            match="The zhmcclient_mock module is deprecated"):
        importlib.import_module("zhmcclient_mock")


def test_zhmcclient_mock_symbols():
    """
    Test that zhmcclient_mock still provides certain symbols.
    """

    # pylint: disable=import-outside-toplevel,unused-import
    from zhmcclient_mock import FakedSession  # noqa: F401
    # pylint: enable=import-outside-toplevel,unused-import
