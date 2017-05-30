.. Copyright 2017 IBM Corp. All Rights Reserved.
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

================================================
Design for handling network errors in zhmcclient
================================================

The zhmcclient package uses the Python
`requests <https://pypi.python.org/pypi/requests/>`_ package for any HMC REST
API calls, and the Python `stomp <https://pypi.python.org/pypi/stomp/>`_
package for handling HMC JMS notifications.

This design document covers error handling using the `requests` package.

Some facts
==========

Layering of components
----------------------

The following picture shows the layering of components w.r.t. networking:

.. code-block:: text

  +---------------------+
  |                     |
  |  application (py)   |
  |                     |
  +---------------------+
  |                     |
  |   zhmcclient (py)   |
  |                     |
  +---------------------+
  |                     |
  |    requests (py)    |
  |                     |
  +---------------------+
  |                     |  - Handles HTTP connection keep-alive and pooling
  |    urllib3 (py)     |  - Handles HTTP basic/digest authentication
  |  (part of requests) |  - Handles HTTP request retrying
  +---------------------+
  |                     |
  |    httplib (py)     |
  |                     |
  +---------------+     |
  |               |     |
  |  socket (py)  |     |
  |               |     |
  +---------------+-----+
  |    _socket (py)     |
  |                     |
  |  _socketmodule.so   |
  |                     |
  +---------------------+  - Handles read timeouts ??
  |     socket API      |  - Handles connection timeouts ??
  |    TCP/IP stack     |  - Handles SSL certificate verification ??
  |                     |  - Handles TCP packet retransmission
  +---------------------+

The following call flow for an HTTP GET request and response shows how these
layers are used:

.. code-block:: text

    -> zhmcclient/_session.py(392): Session.get()
      -> requests/sessions.py(501): Session.get()
         -> requests/sessions.py(488)request()
            -> requests/sessions.py(609)send()
               -> requests/adapters.py(423)send()
                  -> requests/packages/urllib3/connectionpool.py(600)urlopen()
                     -> requests/packages/urllib3/connectionpool.py(356)_make_request()
                        -> httplib.py(1022): HTTPConnection.request()
                           -> httplib.py(1056): HTTPConnection._send_request()
                              -> httplib.py(1018): HTTPConnection.endheaders()
                                 -> httplib.py(869): HTTPConnection._send_output()
                                    -> httplib.py(829): HTTPConnection.send()
                                       -> _socketmodule.so: socket.connect(), if needed (not used by urllib3)
                                       -> _socketmodule.so: socket.sendall()
                     -> requests/packages/urllib3/connectionpool.py(379)_make_request()
                        -> httplib.py(1089): HTTPConnection.getresponse()
                           -> httplib.py(444): HTTPResponse.begin()
                              -> httplib.py(400): HTTPResponse._read_status()
                                 -> socket.py(424): _fileobject.readline()
                                    -> _socketmodule.so: socket.recv()
            -> requests/sessions.py(641)send()
               -> requests/models.py(797)content()
                  -> requests/models.py(719)generate()
                     -> requests/packages/urllib3/response.py(432)stream()
                        -> requests/packages/urllib3/response.py(380)read()
                           -> httplib.py(602): HTTPResponse.read()
                              -> socket.py(355): _fileobject.read()
                                 -> _socketmodule.so: socket.recv()
                           -> httplib.py(610): HTTPResponse.read()
                              -> httplib.py(555): HTTPResponse.close()
                                 -> socket.py(284): _fileobject.close()
                                    -> socket.py(300): _fileobject.flush()
                                       -> _socketmodule.so: socket.sendall(), if anything remaining
                                    -> _socketmodule.so: socket.close()

Timeouts
--------

There are hard coded timeouts in the TCP/IP stack.

The `requests` package allows specifying two timeouts (on HTTP methods such as
``get()``):

* Connect timeout:

  Number of seconds the `requests` package will wait for the
  local machine to establish a TCP connection to a remote machine. This timeout
  is passed to the ``connect()`` call on the socket.

  The `requests` package recommends to set the connect timeout to slightly
  larger than a multiple of 3 (seconds), which is the default TCP packet
  retransmission window.

  This timeout is indicated by raising a ``requests.exceptions.ConnectTimeout``
  exception.

* Read timeout:

  Number of seconds the local machine will wait for the remote
  machine to send a response at the socket level. Specifically, it's the number
  of seconds that the local machine will wait *between* Bytes sent from the
  remote machine. However, in 99.9% of cases, this is the time before the
  remote machine sends the *first* Byte.

  This timeout is indicated by raising a ``requests.exceptions.ReadTimeout``
  exception.

The zhmcclient package currently does not set any of these timeouts, so the
default of waiting forever applies.

**TBD:** Despite the fact that the `requests` connection timeout is not set,
a connection attempt times out after 60 sec, by raising
``requests.exceptions.ConnectionError``.
It is not clear under which conditions this situation is indicated using
``requests.exceptions.ConnectTimeout``.

The zhmcclient itself supports two timeouts at a higher level (as of
`PR #195 <https://github.com/zhmcclient/python-zhmcclient/pull/195>`_
which is targeted for v0.11.0 of the `zhmcclient` package:

* Operation timeout:

  Number of seconds the client will wait for completion of asynchronous
  HMC operations. This applies to ``Session.post()`` and to all resource
  methods with a ``wait_for_completion`` parameter (i.e. the asynchronous
  methods).

  The operation timeout can be specified with the ``operation_timeout``
  parameter on these methods, and defaults to no timeout.

  This timeout is indicated by raising a ``zhmcclient.Timeout`` exception.

* LPAR status timeout:

  Number of seconds the client will wait for the LPAR status to take on the
  value it is supposed to take on given the previous operation affecting
  the LPAR status. This applies to the ``Lpar.activate/deactivate/load()``
  methods. The HMC operations issued by these methods exhibit "deferred status"
  behavior, which means that it takes a few seconds after successful completion
  of the asynchronous job that executes the operation, until the new status can
  be observed in the `status` property of the LPAR resource. These methods will
  poll the LPAR status until the desired status value is reached.

  The LPAR status timeout can be specified with the ``status_timeout``
  parameter on these methods, and defaults to 1 hour.

  This timeout is also indicated by raising a ``zhmcclient.Timeout`` exception.

Reference material:

* `Timeouts in requests package <http://docs.python-requests.org/en/master/user/advanced/#timeouts>`_

Exceptions
----------

The `requests` package wrappers all exceptions of underlying components, except
for programming errors (e.g. ``TypeError``, ``ValueError``, ``KeyError``), into
exceptions that are derived from ``requests.exceptions.RequestException``.

The ``requests.exceptions.RequestException`` exception is never raised itself.

All exceptions derived from ``requests.exceptions.RequestException`` will have
the following attributes:

* ``exc.args[0]``:

  - For ``HTTPError``, ``TooManyRedirects``, ``MissingSchema``,
    ``InvalidSchema``, ``InvalidURL``, ``InvalidHeader``,
    ``UnrewindableBodyError``:
    An error message generated by the `requests` package.

  - For ``ConnectionError``, ``ProxyError``, ``SSLError``, ``ConnectTimeout``,
    ``ReadTimeout``, ``ChunkedEncodingError``, ``ContentDecodingError``,
    ``RetryError``:
    The underlying exception that was raised. This is not documented, though.

  - For ``StreamConsumedError``: ``exc.args=None``.

* ``exc.request`` - ``None``, or the ``requests.PreparedRequest`` object
  representing the HTTP request.

* ``exc.response`` - ``None``, or the ``requests.Response`` object representing
  the HTTP response.

The ``HTTPError`` exception is only raised when the caller requests that bad
HTTP status codes should be returned as exceptions (via
``Session.status_as_exception()``). The zhmcclient package does not do that, so
this exception is never raised, and bad HTTP status codes are checked after
the HTTP method (e.g. ``get()``) returns normally.

The inheritance hierarchy of the exceptions of the `requests` package can be
gathered from the
`requests.exceptions source code <http://docs.python-requests.org/en/master/_modules/requests/exceptions/>`_.

The `zhmcclient` package in turn wrappers the exceptions of the `requests`
package into:

* ``zhmcclient.HTTPError`` - caused by most bad HTTP status codes and
  represents the parameters in the HMC error response. Some HTTP status codes
  are automatically recovered, such as status 403 / reason 5 (API session token
  expired) by re-logon, or status 202 by polling for asynchronous job
  completion.

* ``zhmcclient.ParseError`` - caused by invalid JSON in the HTTP response.

* ``zhmcclient.AuthError`` - caused by HTTP status 403, when reason != 5, or
  when reason == 5 and the resource did not require authentication. The latter
  case is merely a check against unexpected behavior of the HMC and is not
  really needed, or should be acted upon differently.

* ``zhmcclient.ConnectionError`` - caused by all exceptions of the `requests`
  package.

Retries
-------

There are multiple levels of retries:

- The TCP/IP stack retries sends on TCP sockets as part of its error recovery.

- The `requests` package retries the sending of HTTP requests. Actually, this
  is handled by the `urllib3` package, but can be controlled through the
  `requests` package by setting an alternative transport adapter. Such adapters
  are matched by shortest prefix match, so the following works::

      s = requests.Session(.....)
      s.mount('https://', HTTPAdapter(max_retries=10))
      s.mount('http://', HTTPAdapter(max_retries=10))

  This will replace the default transport adapters, which are set in
  `requests.Session()`::

      self.mount('https://', HTTPAdapter())
      self.mount('http://', HTTPAdapter())

  The default for max_retries is 0.

Design changes
==============

The following design changes are proposed for the `zhmcclient` package:

Proposal for timeouts
---------------------

**Proposal(DONE):** Start using the timeouts of the `requests` package, by
setting them as attributes on the ``zhmcclient.Session`` object, with
reasonable default values, and with the ability to override the default values
when creating a ``Session`` object.

The proposed default values are:

* connect timeout: 60 s

* read timeout: 120 s

Having a read timeout assumes that the HMC REST operations all respond within
a maximum time. The asynchronous REST operations all respond rather quickly,
indicating what the job is that performs the asynchronous operation.
Some synchronous REST operations sometimes take long, e.g. up to 45 seconds.
That's why the read timeout should be a good bit larger than that.

Also, the design for the timeouts for async operation completion and LPAR
status transition introduced in
`PR #195 <https://github.com/zhmcclient/python-zhmcclient/pull/195>`_ should
be changed to be consistent with the way timeouts are defined in this design.

**Proposal(TODO):** Change after merging PR #195.

Proposal for exceptions
-----------------------

* ``zhmcclient.ConnectionError`` is currently raised for all exceptions of the
  `requests` package. When we start supporting the timeouts of the `requests`
  package, it is appropriate to distinguish timeouts from other errors. Also,
  it might be useful to separate errors that are likely caused by the
  networking environment (and that could therefore be retried) from errors that
  are not going to recover by retrying. Further, it might be useful to
  distinguish unrecoverable errors that need to be fixed on the client, from
  unrecoverable errors that need to be fixed on the server.

  **Proposal(DONE):** This proposal does not go as far as outlined above. It is
  proposed to handle the `requests` exceptions raised from HTTP methods such as
  ``get()``, as follows:

  - ``TooManyRedirects``, ``MissingSchema``, ``InvalidSchema``, ``InvalidURL``,
    ``InvalidHeader``, ``UnrewindableBodyError``, ``ConnectionError``,
    ``ProxyError``, ``SSLError``, ``ChunkedEncodingError``,
    ``ContentDecodingError``, ``StreamConsumedError``:

    These will be wrappered using ``zhmcclient.ConnectionError`` as today,
    but the exception message will be cleaned up as much as possible:

    - If ``exc.args[0]`` is an ``Exception``, this is the underlying exception
      that was wrapppered by the `requests` exception. Use that underlying
      exception instead.

    - Eliminate ``MaxRetryError`` and use the exception in its ``reason``
      attribute instead.

    - Eliminate the representation of objects in the exception message, e.g.
      ``"NewConnectionError('<requests.packages.urllib3.connection.VerifiedHTTPSConnection object at 0x2922150>:
      Failed to establish a new connection: [Errno 110] Connection timed out',)"``

  - ``ConnectTimeout``, ``ResponseReadTimeout``, ``RequestRetriesExceeded``:

    These will be wrappered by new exceptions ``zhmcclient.ConnectTimeout``,
    ``zhmcclient.ReadTimeout``, ``zhmcclient.RetryError``.

* As described above, ``zhmcclient.AuthError`` is also raised when the HMC
  indicates "API session token expired" for an operation that does not require
  logon (e.g. "Query API Version"). First, checking this is a bit overdoing it
  because there is no harm if the HMC decides that session checking is
  performed always, and second, the handling of this unexpected behavior as
  by raising ``zhmcclient.AuthError`` is misleading for the user.

  **Proposal(DONE):** It is proposed to not handle this situation also by
  re-logon, i.e. to no longer make the behavior dependent on whether the
  operation requires logon.

* ``zhmcclient.VersionError`` currently stores the discovered version in
  ``exc.args[1:2]``. It is not recommended to use ``exc.args[]`` for anything
  else but the exception message, and to use additional instance attributes
  for that, instead.

  **Proposal(DONE):** It is proposed to store this information in additional
  instance attributes, and to remove it from the ``exc.args[]`` array. This is
  an incompatible change, but it is not very critical.

No change is proposed for the other `zhmcclient` exceptions (``ParseError``,
``HTTPError``).

Proposal for retries
--------------------

**Proposal (TODO):** Start using the ``max_retries`` parameter of the
``HTTPAdapter`` transport adapter, by setting the max retries after connect
timeouts and read timeouts as attributes on the ``zhmcclient.Session`` object,
with a reasonable default value, and with the ability to override the default
value when creating a ``Session`` object.

The proposed default values are:

* connect retries: 3

* read retries: 3
