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
The :class:`zhmcclient.OSConsole` class encapsulates the interactions with
the console of an operating system running in a partition, by using the
WebSocket protocol supported by the HMC, which connects that internally to the
OS console.

The OS console can also be interacted with through any WebSocket client,
using the WebSocket URI returned by the
:meth:`zhmcclient.Partition.create_os_websocket` method. Thus, the use of this
class is not mandatory but it simplifies some of the interactions quite
significantly.

Example code using the class to login and execute a 'uname -a' command:

.. code-block:: python

    partition = ...  # a zhmcclient.Partition object

    cons = zhmcclient.OSConsole(partition)

    try:
        cons.connect()
        cons.login_linux('admin', 'password')

        output = cons.execute_command('uname -a')
        print(f"uname -a: {output}")

    finally:
        if cons.is_connected():
            cons.disconnect()
"""

import re
import ssl
import websocket
import certifi

from ._constants import DEFAULT_HMC_PORT, DEFAULT_WS_TIMEOUT, OS_LOGGER_NAME
from ._exceptions import OSConsoleConnectedError, OSConsoleNotConnectedError, \
    OSConsoleWebSocketError, OSConsoleAuthError
from ._logging import get_logger

__all__ = ['OSConsole']

OS_LOGGER = get_logger(OS_LOGGER_NAME)


class OSConsole:
    """
    This class encapsulates the interactions with the console of an operating
    system running in a partition, by using the WebSocket protocol supported by
    the HMC.

    HMC/SE version requirements:

    * HMC version >= 2.14.0 with HMC API version >= 2.22
    """

    def __init__(self, partition, ws_timeout=DEFAULT_WS_TIMEOUT):
        """
        Parameters:

          partition (:class:`~zhmcclient.Partition`): Targeted partition for
            connecting to its operating system console.

          ws_timeout (int): WebSocket connect and read timeout in seconds.
            This timeout is used to detect the end of output on the OS console.
            If it is too short, output will be missed. The timeout should not
            be shorter than 5 seconds.
            Default: :attr:`~zhmcclient._constants.DEFAULT_WS_TIMEOUT`.
        """
        self.partition = partition
        self.ws_timeout = ws_timeout

        self.ws_uri = None
        self.ws_full_uri = None
        self.ws = None
        self.previous_text = None

    def _check_connected(self):
        if self.ws is None:
            raise OSConsoleNotConnectedError(
                "Not connected to the OS console")

    def _check_not_connected(self):
        if self.ws is not None:
            cpc = self.partition.manager.parent
            raise OSConsoleConnectedError(
                "Already connected to the OS console for partition "
                f"{cpc.name}.{self.partition.name}")

    def is_connected(self):
        """
        Return a boolean indicating whether this object is currently connected
        to the OS console.
        """
        return self.ws is not None

    def connect(self):
        """
        Create a WebSocket on the HMC and use it to connect to the OS console.

        This object must not currently be connected to the OS console.

        Raises:

          zhmcclient.Error: Issue when creating the WebSocket on the HMC.
          OSConsoleConnectedError: Already connected to the OS console.
          OSConsoleWebSocketError: Issue when connecting via the WebSocket.
        """
        self._check_not_connected()

        self.ws_uri = self.partition.create_os_websocket()
        # may raise zhmcclient.Error

        session = self.partition.manager.session
        self.ws_full_uri = \
            f"wss://{session.actual_host}:{DEFAULT_HMC_PORT}{self.ws_uri}"

        sslopt = {}
        if isinstance(session.verify_cert, str):
            sslopt["cert_reqs"] = ssl.CERT_REQUIRED
            sslopt["ca_cert_path"] = session.verify_cert
        elif session.verify_cert is True:
            sslopt["cert_reqs"] = ssl.CERT_REQUIRED
            sslopt["ca_cert_path"] = certifi.where()
        else:
            sslopt["cert_reqs"] = ssl.CERT_NONE
        self.ws = websocket.WebSocket(sslopt=sslopt)

        try:
            self.ws.connect(self.ws_full_uri, timeout=self.ws_timeout)
        except (websocket.WebSocketException, OSError) as exc:
            raise OSConsoleWebSocketError(str(exc))

        self.previous_text = None

    def disconnect(self):
        """
        Disconnect from the OS console.

        This object must currently be connected to the OS console.

        Raises:

          OSConsoleNotConnectedError: Not connected to the OS console.
          OSConsoleWebSocketError: Issue when closing the WebSocket.
        """
        self._check_connected()

        try:
            self.ws.close()
        except (websocket.WebSocketException, OSError) as exc:
            raise OSConsoleWebSocketError(str(exc))

        self.ws = None
        self.ws_uri = None
        self.ws_full_uri = None
        self.previous_text = None

    def recv_all(self):
        """
        Receive all text data from the OS console until no more data is
        available within the WebSocket timeout, and return that.

        This object must currently be connected to the OS console.

        In the string that is returned, any sequence of one or more CR (U+000D)
        characters followed by NL (U+000A) has been translated to NL (i.e. the
        CR characters are removed).

        Returns:

          str: Received text data, as a Unicode string.

        Raises:

          OSConsoleNotConnectedError: Not connected to the OS console.
          OSConsoleWebSocketError: Issue when reading data from the WebSocket.
        """
        self._check_connected()

        data_items = []
        if self.previous_text is not None:
            data_items.append(self.previous_text)
            self.previous_text = None
        while True:
            try:
                data = self.ws.recv()
            except websocket.WebSocketTimeoutException:
                return ''.join(data_items)
            except (websocket.WebSocketException, OSError) as exc:
                raise OSConsoleWebSocketError(str(exc))

            assert isinstance(data, str), f"data is not a string: {data!r}"
            data = re.sub(r'\r+\n', r'\n', data)
            data_items.append(data)

    def recv_line(self):
        """
        Receive one line of text data from the OS console and return that.

        This object must currently be connected to the OS console.

        This may include possibly multiple calls to receive messages from
        the WebSocket. Any excess data is buffered and is processed by
        the next call to :meth:`recv_line` or :meth:`recv_all`.

        A line end is detected in the data as follows:

        * when an NL (U+000A) character is encountered
        * when the WebSocket read timeout has expired without encountering NL

        In the string that is returned, any sequence of one or more CR (U+000D)
        characters followed by NL (U+000A) has been translated to NL (i.e. the
        CR characters are removed).

        Returns:

          str: The line of text data, normally terminated by NL. If the
          WebSocket read timeout has expired without encountering NL, the
          string will not have a trailing NL. If the WebSocket read timeout
          has expired without getting any data, the empty string will be
          returned.

        Raises:

          OSConsoleNotConnectedError: Not connected to the OS console.
          OSConsoleWebSocketError: Issue when reading data from the WebSocket.
        """
        self._check_connected()

        line_parts = []
        while True:

            # Get data if there is no previous data
            if not self.previous_text:
                try:
                    text = self.ws.recv()
                except websocket.WebSocketTimeoutException:
                    break
                except (websocket.WebSocketException, OSError) as exc:
                    raise OSConsoleWebSocketError(str(exc))
                # The HMC always returns text data:
                assert isinstance(text, str)
                self.previous_text = re.sub(r'\r+\n', r'\n', text)

            # Process the data to extract the line
            line, end, remainder = self.previous_text.partition('\n')
            line_parts.append(line)
            line_parts.append(end)
            self.previous_text = remainder
            if end:
                break

        return ''.join(line_parts)

    def send(self, text):
        """
        Send text data to the OS console.

        This object must currently be connected to the OS console.

        The data can be one or more lines, separated by NL, and typically also
        terminated by NL. The lines are interpreted as commands in the OS
        console.

        Parameters:

          text (str): The text data, as a Unicode string.

        Raises:

          OSConsoleNotConnectedError: Not connected to the OS console.
          OSConsoleWebSocketError: Issue when sending data to the WebSocket.
        """
        self._check_connected()

        self.ws.send_text(text)

    def login_linux(self, username, password):
        """
        Login to a Linux operating system running in the partition.

        This object must currently be connected to the OS console.

        Raises:

          OSConsoleNotConnectedError: Not connected to the OS console.
          OSConsoleWebSocketError: Issue when sending data to or receiving
            data from the WebSocket.
          OSConsoleAuthError: Authentication issue when logging in to Linux.
        """
        # The check for connection is performed in self.recv_all()
        while True:
            lines = self.recv_all()
            OS_LOGGER.debug("login_linux: Received: %r", lines)
            if lines and re.search(
                    r"login:$", lines.strip(), flags=re.I + re.M):
                OS_LOGGER.debug(
                    "login_linux: Found login prompt, sending username")
                self.send(username + '\n')
                lines = self.recv_all()
                OS_LOGGER.debug("Received: %r", lines)
                if lines and re.search(
                        r"password:$", lines.strip(), flags=re.I + re.M):
                    OS_LOGGER.debug(
                        "login_linux: Found password prompt, sending password")
                    self.send(password + '\n')
                    lines = self.recv_all()
                    OS_LOGGER.debug("login_linux: Received: %r", lines)
                    if lines and re.search(
                            r"(login incorrect|login timed out)",
                            lines, flags=re.I + re.M):
                        msg = re.sub(
                            r"\n[^\n]*login:", "", lines, flags=re.I + re.M)
                        msg = msg.strip().replace('\n', ' ')
                        raise OSConsoleAuthError(msg)
                    OS_LOGGER.debug("login_linux: Successfully logged in")
                    break
            else:
                OS_LOGGER.debug(
                    "login_linux: Sending empty line to get to login prompt")
                self.send('\n')

    def execute_command(self, command):
        """
        Execute a command in the OS console and return its output lines.

        This object must currently be connected to the OS console.
        Depending on the operating system, this object also needs to be logged
        in to the OS.

        The execution environment for the commands is always the console of
        the OS, so it depends on the type of OS:

        * On z/VM, the commands are executed as CP commands.
          The command output is returned as output lines.

        * On Linux, the commands are executed as normal shell commands
          in the console environment.
          The command output with stdout and stderr merged into one stream is
          returned as output lines.

        The exit code of the commands is not available.

        In the output lines string that is returned, any sequence of one or
        more CR (U+000D) characters followed by NL (U+000A) has been translated
        to NL (i.e. the CR characters are removed).

        Parameters:

          command (str): Command string (without any trailing NL).

        Returns:

          str: Command output lines. The lines are separated by NL.

        Raises:

          OSConsoleNotConnectedError: Not connected to the OS console.
          OSConsoleWebSocketError: Issue when sending data to or receiving
            data from the WebSocket.
        """
        # The check for connection is performed in self.send()
        OS_LOGGER.debug("execute_command: Sending command: %r", command)
        self.send(command + '\n')
        output = self.recv_all()
        OS_LOGGER.debug("execute_command: Received command output: %r", output)
        return output
