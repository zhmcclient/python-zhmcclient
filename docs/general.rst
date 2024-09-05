.. Copyright 2016,2021 IBM Corp. All Rights Reserved.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
..

.. _`General features`:

Reference: General features
===========================


.. _`Session`:

Session
-------

.. automodule:: zhmcclient._session

.. autoclass:: zhmcclient.Session
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Job
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autofunction:: zhmcclient.get_password_interface


.. _`Retry-timeout configuration`:

Retry / timeout configuration
-----------------------------

.. autoclass:: zhmcclient.RetryTimeoutConfig
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`AutoUpdater`:

AutoUpdater
---------------

.. automodule:: zhmcclient._auto_updater

.. autoclass:: zhmcclient.AutoUpdater
  :members:
  :autosummary:
  :autosummary-inherited-members:
  :special-members: __str__


.. _`Client`:

Client
------

.. automodule:: zhmcclient._client

.. autoclass:: zhmcclient.Client
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Time Statistics`:

Time Statistics
---------------

.. automodule:: zhmcclient._timestats

.. autoclass:: zhmcclient.TimeStatsKeeper
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.TimeStats
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Metrics`:

Metrics
-------

.. automodule:: zhmcclient._metrics

.. autoclass:: zhmcclient.MetricsContextManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricsContext
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricGroupDefinition
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricDefinition
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricsResponse
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricGroupValues
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricObjectValues
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Logging`:

Logging
-------

.. automodule:: zhmcclient._logging


.. _`Exceptions`:

Exceptions
----------

.. automodule:: zhmcclient._exceptions

.. autoclass:: zhmcclient.Error
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ConnectionError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ConnectTimeout
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ReadTimeout
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.RetriesExceeded
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.AuthError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ClientAuthError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ServerAuthError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ParseError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.VersionError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.HTTPError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.OperationTimeout
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.StatusTimeout
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.NotFound
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.NoUniqueMatch
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.CeasedExistence
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.OSConsoleError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.OSConsoleConnectedError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.OSConsoleNotConnectedError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.OSConsoleWebSocketError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.OSConsoleAuthError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Constants`:

Constants
---------

.. automodule:: zhmcclient._constants
   :members:


.. _`Utilities`:

Utilities
---------

.. # Note: In order to avoid the issue that automodule members are shown
.. # in their module namespace (e.g. zhmcclient._utils), we maintain the
.. # members of the _utils module manually.

.. automodule:: zhmcclient._utils

.. autofunction:: zhmcclient.datetime_from_timestamp

.. autofunction:: zhmcclient.timestamp_from_datetime



.. _`Using WebSocket to access OS console`:

Using WebSocket to access OS console
------------------------------------

Starting with HMC version 2.14, it supports the WebSocket protocol for
accessing the console of the operating system running in partitions on
CPCs in DPM mode.

The zhmcclient method
:meth:`zhmcclient.Partition.create_os_websocket` is used to create a WebSocket
for a particular partition and to return its URI.

This section describes how to use that returned WebSocket URI and how to
interact with the OS console using Python code.

The WebSocket URI returned by the above method is a URI path without scheme and
server, e.g.
``/api/websock/4a4f1hj12hldmm26brcpfnydk663gt6gtyxq4iwto26g2r6wq1/1``.
That URI is used on the IP address of the HMC that created it using the Web
Services port of the HMC (port 6794).

Depending on which WebSocket client is used, a full URI needs to be constructed
from the returned URI path by prepending the secure WebSocket URI scheme
``wss`` and the HMC's IP address and port, e.g.
``wss://9.10.11.12:6794/api/websock/4a4f1hj12hldmm26brcpfnydk663gt6gtyxq4iwto26g2r6wq1/1``.

The data returned by the WebSocket are the lines on the OS console, and the
data sent to the WebSocket are the commands executed on the console, and any
login data.

Since the integrated ASCII console is supported only on Z systems in DPM mode,
the operating system running there will be one of:

* some sort of Linux (in a partition with type "linux" or "ssc")
* z/VM (in a partition with type "zvm")

The OS console of z/VM does not require a login procedure, and any lines sent to
the WebSocket are interpreted as CP commands.

The OS console of Linux requires a login procedure, so the data sent by the
WebSocket represents a login prompt that needs to be responded by sending lines
with the Linux userid and password. After that, any further lines sent are
interpreted as Linux console commands.

Here is an example Python script that uses the
`websocket-client <https://pypi.org/project/websocket-client>`_ Python package
and performs a login to a Linux OS and then executes the 'uname' command and
prints its output:

.. code-block:: python

    #!/usr/bin/env python
    # Use WebSocket to console of a partition, login to Linux and execute 'uname'

    import sys
    import re
    import ssl
    import time
    import websocket
    import certifi
    import requests.packages.urllib3
    import zhmcclient

    WS_TIMEOUT = 5  # WebSocket receive timeout in seconds

    HMC_HOST = '...'  # HMC IP address
    HMC_USERID = '...'  # HMC user name
    HMC_PASSWORD = '...'  # HMC password
    HMC_VERIFY_CERT = False  # or path to CA certificate file/dir

    CPC_NAME = '...'  # CPC name
    PARTITION_NAME = '...'  # partition name

    LINUX_USERNAME = '...'  # Linux user name for the partition
    LINUX_PASSWORD = '...'  # Linux password for the partition


    def recv_all(ws):
        """Receive all lines on console"""
        lines = []
        while True:
            try:
                line = ws.recv()
            except websocket.WebSocketTimeoutException:
                return ''.join(lines)
            lines.append(line)


    def linux_login(ws, username, password):
        """Login to a Linux OS"""
        while True:
            lines = recv_all(ws)
            if lines and re.search(r"login:$", lines.strip(), flags=re.I+re.M):
                ws.send(username + '\n')
                lines = recv_all(ws)
                if lines and re.search(r"password:$", lines.strip(), flags=re.I+re.M):
                    ws.send(password + '\n')
                    lines = recv_all(ws)
                    if lines and re.search(r"login incorrect", lines, flags=re.I+re.M):
                        msg = lines.replace('\r\n', '\n')
                        msg = re.sub(r"\n+", "\n", msg, flags=re.M)
                        msg = re.sub(r"\n[^\n]*login:", "", msg, flags=re.I+re.M)
                        msg = msg.strip().replace('\n', ' ')
                        raise Exception(msg)
                    break
            else:
                # Sending empty line to get to login prompt
                ws.send('\n')


    def main():

        requests.packages.urllib3.disable_warnings()

        session = zhmcclient.Session(
            host=HMC_HOST,
            userid=HMC_USERID,
            password=HMC_PASSWORD,
            verify_cert=HMC_VERIFY_CERT)

        client = zhmcclient.Client(session)
        cpc = client.cpcs.find(name=CPC_NAME)
        partition = cpc.partitions.find(name=PARTITION_NAME)

        session = partition.manager.session
        sslopt = {}
        if isinstance(session.verify_cert, str):
            sslopt["cert_reqs"] = ssl.CERT_REQUIRED
            sslopt["ca_cert_path"] = session.verify_cert
        elif session.verify_cert is True:
            sslopt["cert_reqs"] = ssl.CERT_REQUIRED
            sslopt["ca_cert_path"] = certifi.where()
        else:
            sslopt["cert_reqs"] = ssl.CERT_NONE

        ws_uri = partition.create_os_websocket()

        ws = websocket.WebSocket(sslopt=sslopt)

        try:
            print(f"Connecting to WebSocket for partition {cpc.name}.{partition.name}")
            ws.connect(f"wss://{session.actual_host}:6794{ws_uri}", timeout=WS_TIMEOUT)

            print("Logging in to Linux")
            try:
                linux_login(ws, LINUX_USERNAME, LINUX_PASSWORD)
            except Exception as exc:
                print(f"Error: Cannot login: {exc}")
                return 1

            print("Executing 'uname -a' command")
            try:
                ws.send('uname -a\n')
                uname_out = recv_all(ws)
            except Exception as exc:
                print(f"Error: Cannot execute uname: {exc}")
                return 1

            print(f"Output: {uname_out}")

        finally:
            print("Closing WebSocket")
            ws.close()
            return 0


    if __name__ == '__main__':
        rc = main()
        sys.exit(rc)

The :ref:`OSConsole` section describes a more convenient approach for
interacting with the OS consoles.


.. _`OSConsole`:

OSConsole
---------

.. automodule:: zhmcclient._os_console

.. autoclass:: zhmcclient.OSConsole
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__
