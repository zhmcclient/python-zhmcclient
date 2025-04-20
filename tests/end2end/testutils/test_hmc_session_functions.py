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
End2end tests for testutils._hmc_session_functions module.
"""

import pytest
from requests.packages import urllib3
import zhmcclient
import zhmcclient_mock

# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import
from zhmcclient.testutils import setup_hmc_session, teardown_hmc_session_id, \
    teardown_hmc_session, is_valid_hmc_session_id

urllib3.disable_warnings()


@pytest.mark.parametrize(
    "teardown", ['session', 'session_id']
)
def test_session_setup(hmc_definition, teardown):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test setup_hmc_session().
    """

    # The code to be tested.
    session = setup_hmc_session(hmc_definition)

    try:
        if hmc_definition.mock_file:
            assert isinstance(session, zhmcclient_mock.FakedSession)
        else:
            assert isinstance(session, zhmcclient.Session)
            assert not isinstance(session, zhmcclient_mock.FakedSession)

    finally:
        if teardown == 'session':
            teardown_hmc_session(session)
        else:
            teardown_hmc_session_id(hmc_definition, session.session_id)


@pytest.mark.parametrize(
    "teardown", ['session', 'session_id']
)
def test_session_valid_session(hmc_definition, teardown):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test is_valid_hmc_session_id() with a valid session.
    """

    session = setup_hmc_session(hmc_definition)

    try:
        # The code to be tested.
        is_valid = is_valid_hmc_session_id(hmc_definition, session.session_id)

        assert is_valid is True

    finally:
        if teardown == 'session':
            teardown_hmc_session(session)
        else:
            teardown_hmc_session_id(hmc_definition, session.session_id)


def test_session_invalid_session(hmc_definition):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test is_valid_hmc_session_id() with an invalid session.
    """
    invalid_session_id = 'invalid-session-id'

    is_valid = is_valid_hmc_session_id(hmc_definition, invalid_session_id)

    assert is_valid is False
