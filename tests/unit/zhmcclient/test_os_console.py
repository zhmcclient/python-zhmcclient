# Copyright 2024 IBM Corp. All Rights Reserved.
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
Unit tests for _os_console module.
"""

from unittest import mock
import pytest
import websocket

from zhmcclient import OSConsole, Partition, OSConsoleConnectedError, \
    OSConsoleNotConnectedError

# pylint: disable=unused-import,line-too-long
from tests.common.http_mocked_fixtures import http_mocked_session  # noqa: F401
from tests.common.http_mocked_fixtures import http_mocked_cpc_dpm  # noqa: F401
from tests.common.http_mocked_fixtures import http_mocked_partition  # noqa: F401,E501
# pylint: enable=unused-import,line-too-long


def test_osc_initial_attrs(http_mocked_partition):  # noqa: F811
    # pylint: disable=redefined-outer-name, unused-argument
    """Test initial attributes of OSConsole."""

    ws_timeout = 42

    # Execute the code to be tested
    osc = OSConsole(partition=http_mocked_partition, ws_timeout=ws_timeout)

    assert osc.partition is http_mocked_partition
    assert osc.ws_timeout == ws_timeout

    assert osc.ws_uri is None
    assert osc.ws_full_uri is None
    assert osc.ws is None
    assert osc.previous_text is None

    assert osc.is_connected() is False


@mock.patch.object(Partition, 'create_os_websocket')
@mock.patch('websocket.WebSocket')
def test_osc_connect(
        websocket_mock, create_os_websocket_mock,
        http_mocked_partition):  # noqa: F811
    # pylint: disable=redefined-outer-name, unused-argument
    """All tests for OSConsole.connect/disconnect/is_connected()."""

    create_os_websocket_mock.return_value = '/api/websocket/fake-ws1'

    osc = OSConsole(partition=http_mocked_partition)

    # Test 1: Connect if not connected -> success
    osc.connect()
    assert osc.is_connected() is True

    # Test 2: Connect if connected -> fails
    with pytest.raises(OSConsoleConnectedError):
        osc.connect()
    assert osc.is_connected() is True

    # Test 3: Disconnect if connected -> success
    osc.disconnect()
    assert osc.is_connected() is False

    # Test 4: Disconnect if not connected -> fails
    with pytest.raises(OSConsoleNotConnectedError):
        osc.disconnect()
    assert osc.is_connected() is False


LPAR_OSC_RECV_ALL_TESTCASES = [
    # Testcases for test_osc_recv_all().
    # The list items are tuples with the following items:
    # - desc (string): description of the testcase.
    # - connected (bool): Whether initially to connect.
    # - recv_chunks (list): Data chunks to be received.
    # - exp_data (str): Expected received data.
    # - exp_exc_type (class): Expected exception type, or None for success.

    (
        "Not connected",
        False,
        ['line1\r\r\n'],
        None,
        OSConsoleNotConnectedError,
    ),
    (
        "No data",
        True,
        [],
        '',
        None,
    ),
    (
        "One chunk of data without NL",
        True,
        ['line1'],
        'line1',
        None,
    ),
    (
        "One chunk of data with NL",
        True,
        ['line1\n'],
        'line1\n',
        None,
    ),
    (
        "Two chunks of data with NL",
        True,
        ['line1\n', 'line2\n'],
        'line1\nline2\n',
        None,
    ),
    (
        "One chunk of data with one CR before NL",
        True,
        ['line1\r\n'],
        'line1\n',
        None,
    ),
    (
        "One chunk of data with two CRs before NL",
        True,
        ['line1\r\r\n'],
        'line1\n',
        None,
    ),
]


@pytest.mark.parametrize(
    "desc, connected, recv_chunks, exp_data, exp_exc_type",
    LPAR_OSC_RECV_ALL_TESTCASES)
@mock.patch.object(Partition, 'create_os_websocket')
@mock.patch('websocket.WebSocket')
def test_osc_recv_all(
        websocket_mock, create_os_websocket_mock,
        http_mocked_partition,  # noqa: F811
        desc, connected, recv_chunks, exp_data, exp_exc_type):
    # pylint: disable=redefined-outer-name, unused-argument
    """All tests for OSConsole.recv_all()."""

    create_os_websocket_mock.return_value = '/api/websocket/fake-ws1'
    osc = OSConsole(partition=http_mocked_partition, ws_timeout=1)

    if connected:
        osc.connect()

    if exp_exc_type:
        with pytest.raises(exp_exc_type):

            # The code to be tested
            osc.recv_all()

    else:

        # Prepare the data to be received
        last_chunk = websocket.WebSocketTimeoutException()
        osc.ws.recv.side_effect = recv_chunks + [last_chunk]

        # The code to be tested
        data = osc.recv_all()

        assert data == exp_data

        # pylint: disable=no-member
        assert osc.ws.recv.call_count == len(recv_chunks) + 1

    if osc.is_connected():
        osc.disconnect()


LPAR_OSC_RECV_LINE_TESTCASES = [
    # Testcases for test_osc_recv_line().
    # The list items are tuples with the following items:
    # - desc (string): description of the testcase.
    # - connected (bool): Whether initially to connect.
    # - recv_chunks (list): Data chunks available for receiving.
    # - exp_call_count (str): Expected number of calls to ws.recv()
    # - exp_data (str): Expected received data.
    # - exp_exc_type (class): Expected exception type, or None for success.

    (
        "Not connected",
        False,
        ['line1\n'],
        1,
        None,
        OSConsoleNotConnectedError,
    ),
    (
        "No data available",
        True,
        [],
        1,
        '',
        None,
    ),
    (
        "One chunk of data without NL available",
        True,
        ['line1'],
        2,
        'line1',
        None,
    ),
    (
        "One chunk of data with NL available",
        True,
        ['line1\n'],
        1,
        'line1\n',
        None,
    ),
    (
        "Two chunks of data with NL available",
        True,
        ['line1\n', 'line2\n'],
        1,
        'line1\n',
        None,
    ),
    (
        "One chunk of data with one CR before NL available",
        True,
        ['line1\r\n'],
        1,
        'line1\n',
        None,
    ),
    (
        "One chunk of data with two CRs before NL available",
        True,
        ['line1\r\r\n'],
        1,
        'line1\n',
        None,
    ),
    (
        "One chunk of data with two CRs before NL available",
        True,
        ['line1\r\r\n'],
        1,
        'line1\n',
        None,
    ),
    (
        "One chunk of data without NL and one chunk with NL available",
        True,
        ['line1', '\n'],
        2,
        'line1\n',
        None,
    ),
]


@pytest.mark.parametrize(
    "desc, connected, recv_chunks, exp_call_count, exp_data, exp_exc_type",
    LPAR_OSC_RECV_LINE_TESTCASES)
@mock.patch.object(Partition, 'create_os_websocket')
@mock.patch('websocket.WebSocket')
def test_osc_recv_line(
        websocket_mock, create_os_websocket_mock,
        http_mocked_partition,  # noqa: F811
        desc, connected, recv_chunks, exp_call_count, exp_data, exp_exc_type):
    # pylint: disable=redefined-outer-name, unused-argument
    """All tests for OSConsole.recv_line()."""

    create_os_websocket_mock.return_value = '/api/websocket/fake-ws1'
    osc = OSConsole(partition=http_mocked_partition, ws_timeout=1)

    if connected:
        osc.connect()

    if exp_exc_type:
        with pytest.raises(exp_exc_type):

            # The code to be tested
            osc.recv_line()

    else:

        # Prepare the data to be received
        last_chunk = websocket.WebSocketTimeoutException()
        osc.ws.recv.side_effect = recv_chunks + [last_chunk]

        # The code to be tested
        data = osc.recv_line()

        assert data == exp_data

        # pylint: disable=no-member
        assert osc.ws.recv.call_count == exp_call_count

    if osc.is_connected():
        osc.disconnect()


LPAR_OSC_SEND_TESTCASES = [
    # Testcases for test_osc_send().
    # The list items are tuples with the following items:
    # - desc (string): description of the testcase.
    # - connected (bool): Whether initially to connect.
    # - send_data (list): Data to be sent, or None.
    # - exp_exc_type (class): Expected exception type, or None for success.

    (
        "Not connected",
        False,
        None,
        OSConsoleNotConnectedError,
    ),
    (
        "No data",
        True,
        '',
        None,
    ),
    (
        "Data without NL",
        True,
        'line1',
        None,
    ),
    (
        "Data with one trailing NL",
        True,
        'line1\n',
        None,
    ),
    (
        "Data with two NLs",
        True,
        'line1\nline2\n',
        None,
    ),
]


@pytest.mark.parametrize(
    "desc, connected, send_data, exp_exc_type",
    LPAR_OSC_SEND_TESTCASES)
@mock.patch.object(Partition, 'create_os_websocket')
@mock.patch('websocket.WebSocket')
def test_osc_send(
        websocket_mock, create_os_websocket_mock,
        http_mocked_partition,  # noqa: F811
        desc, connected, send_data, exp_exc_type):
    # pylint: disable=redefined-outer-name, unused-argument
    """All tests for OSConsole.send()."""

    create_os_websocket_mock.return_value = '/api/websocket/fake-ws1'
    osc = OSConsole(partition=http_mocked_partition, ws_timeout=1)

    if connected:
        osc.connect()

    if exp_exc_type:
        with pytest.raises(exp_exc_type):

            # The code to be tested
            osc.send(send_data)

    else:

        # The code to be tested
        osc.send(send_data)

        # pylint: disable=no-member
        osc.ws.send_text.assert_called_once_with(send_data)

    if osc.is_connected():
        osc.disconnect()


# TODO: Tests for OSConsole.login_linux()


LPAR_OSC_EXEC_CMD_TESTCASES = [
    # Testcases for test_osc_exec_cmd().
    # The list items are tuples with the following items:
    # - desc (string): description of the testcase.
    # - connected (bool): Whether initially to connect.
    # - command (str): Command to be executed, or None.
    # - output (str): Command output to be received, or None.
    # - exp_exc_type (class): Expected exception type, or None for success.

    (
        "Not connected",
        False,
        'noout',
        None,
        OSConsoleNotConnectedError,
    ),
    (
        "Command with no output",
        True,
        'noout',
        '',
        None,
    ),
    (
        "Command with one line of output",
        True,
        'oneline',
        'line1\n',
        None,
    ),
    (
        "Command with two lines of output",
        True,
        'oneline',
        'line1\nline2\n',
        None,
    ),
]


@pytest.mark.parametrize(
    "desc, connected, command, output, exp_exc_type",
    LPAR_OSC_EXEC_CMD_TESTCASES)
@mock.patch.object(Partition, 'create_os_websocket')
@mock.patch('websocket.WebSocket')
def test_osc_exec_cmd(
        websocket_mock, create_os_websocket_mock,
        http_mocked_partition,  # noqa: F811
        desc, connected, command, output, exp_exc_type):
    # pylint: disable=redefined-outer-name, unused-argument
    """All tests for OSConsole.execute_command()."""

    create_os_websocket_mock.return_value = '/api/websocket/fake-ws1'
    osc = OSConsole(partition=http_mocked_partition, ws_timeout=1)

    if connected:
        osc.connect()

    if exp_exc_type:
        with pytest.raises(exp_exc_type):

            # The code to be tested
            osc.execute_command(command)

    else:

        # Prepare the command output
        last_chunk = websocket.WebSocketTimeoutException()
        osc.ws.recv.side_effect = [output, last_chunk]

        # The code to be tested
        act_output = osc.execute_command(command)

        assert act_output == output

        # pylint: disable=no-member
        osc.ws.send_text.assert_called_once_with(command + '\n')

    if osc.is_connected():
        osc.disconnect()
