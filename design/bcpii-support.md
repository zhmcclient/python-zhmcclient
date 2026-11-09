# BCPII support in the zhmcclient

This document describes the design of the BCPII support and its integration
into the zhmcclient Python package.

## Overview

The BCPII support in the zhmcclient consists of:

* The "WS-API proxy" server.

  The WS-API proxy consumes the BCPII demon provided by the Linux s390tools
  package and provides a Unix Domain Socket interface that is compatible with
  the HMC WS-API, for use by the zhmcclient code.

* Integration of the WS-API proxy into the zhmcclient package.

  Because the BCPII support has a number of Python package dependencies on top
  of what the original zhmcclient package needs, the BCPII support will be
  installed as a pip *extra* named "bcpii" (i.e. `pip install zhmcclient[bcpii]`).

  The integration will start the WS-API proxy server as a detached process, when
  needed. That process runs as a singleton and multiple zhmcclient applications
  will use the same WS-API proxy server instance.

## Terminology

The following terminology will be used in the documentation of the zhmcclient
package:

* The support for BCPII in the zhmcclient package will be referred to as
  "BCPII support".

* The proxy server provided by the zhmcclient package that provides a HMC WS-API
  compatible API using Unix Domain Sockets will be referred to as "WS-API proxy"
  or "WS-API proxy server".

* The BCPII demon provided by the s390tools Linux package will be referred to as
  "BCPII demon".

## Supported environments

The BCPII support in the zhmcclient requires at least HMC 2.17.0 (due to the use
of the "List Targetable HMCs" operation on BCPII) and a z16 or higher system
from where the zhmcclient application runs (for support of the BCPII V2
interface in the LPAR).

Note that a 2.17 HMC supports managing z15 systems and that works for the BCPII
support in the zhmcclient as long as the zhmcclient application does not run
in an LPAR on a z15 system.

Trying to use the BCPII support in the zhmcclient in an LPAR on an earlier
system than z16 or against an HMC earlier than 2.17.0 results in an appropriate
error to the zhmcclient application.

## Selecting the HMC

In order to avoid new parameters (which would perculate up to all other projects
using the zhmcclient), the HMC on BCPII is selected with the existing `host`
input parameter of `zhmcclient.Session()``.

The string format of the `host` parameter for selecting BCPII is:

* For selecting the first HMC target returned by the "List Targetable HMCs"
  operation:

  ```
  bcpii:first
  ```

* For selecting a specific HMC:

  ```
  bcpii:<hmc-target-name>
  ```

  where `<hmc-target-name>` is the BCPII target name of the HMC.

## Support for selecting SEs as target

With the approach for specifying an HMC target name, one could also specify an
SE target name. However, since the zhmcclient depends on building up a resource
tree from the HMC on down, that will probably not work without significant
rework of the zhmcclient resource representation.

In a first stage, selecting SEs as BCPII target will not be supported.

Whether that can be supported in the future, is TBD.

## Running the WS-API proxy server

The WS-API proxy server will be started when the first zhmcclient program
specifies that a BCPII target should be used. The proxy server will run
as a detached process, so it keeps running when the process that started it
(i.e. the zhmcclient application) terminates. There will be only one WS-API
proxy server process for use by all zhmcclient application processes.

There will be serialization on both sides:

* The WS-API proxy server ensures that only one instance of itself is running.

  The approach for that is to serialize the server on a system wide exclusive
  lock.

  The Linux "flock" support (using Python `fcntl.flock()`) will be used for
  that lock, because the Linux system cleans up such locks upon termination of
  the zhmcclient application process, regardless of how it terminates, even
  when forcefully killed (e.g. `kill -9`).

  The server code does not need to release that lock and will use this approach:

  - Try to acquire the server lock
  - If that fails, exit (because another server instance is already running)
  - Run the proxy server

* The zhmcclient code that starts the WS-API proxy server process will serialize
  against other zhmcclient application processes doing the same, using this
  approach:

  - Try to connect to the WS-API proxy
  - If that fails:
    - Take the startup lock (retry until it can be acquired)
    - Try to connect again
    - If that fails:
      - Spawn the WS-API proxy server process
      - Wait until it accepts connections
    - Release the startup lock

  The startup lock is also an exclusive and system wide lock using the Linux
  "flock" support, because the system cleans it up automatically regardless of
  how the zhmcclient application process terminates, e.g. when it is forcefully
  killed while holding the startup lock.

Having both approaches may seem redundant, but it makes sense:

* The server lock ensures that only one server is running.

* If support for the server lock exists, then the startup lock is not needed
  from a functional perspective. However, the startup lock is a performance
  optimization that avoids starting a new server (that would exit because it
  cannot get the server lock) when a server is already running.

## Terminating the WS-API proxy server

In a first stage, the WS-API proxy server simply keeps on running once it has
been started by a zhmcclient application process, even when all zhmcclient
application processes have terminated.

**Future stage**: In a future stage, an automatic termination of the WS-API
proxy server can be implemented.

Note that there are use cases such as the zhmccli package which has a
"zhmc session logon" command that opens an HMC session and leaves it open for
use by subsequent commands. The ibm.ibm_zhmc Ansible collection has a similar
functionality in its "zhmc_session" module. From a zhmcclient perspective, this
means the zhmcclient application process has terminated but the HMC session
rightfully stays open. Since the WS-API proxy is the owner of the session ID
and the session ID store is in memory, the WS-API proxy must keep on running
in such cases.

Therefore, an automatic termination of the WS-API proxy must be based on
counting open sessions and not on counting client processes.

## Session handling

One of the things the WS-API proxy does is to emulate the HMC session logon
and logoff. The underlying BCPII demon supports JWT based authentication of
each request and does not have a concept of a session.

To support sessions, the WS-API proxy maintains a store of HMC session IDs
for currently open sessions.

In a first stage, the session ID store will be in memory. This means, a crash
of the proxy server will loose all open sessions, and while the deferred start
logic in the zhmcclient code will start the WS-API proxy again automatically,
the old sessions will be lost and the zhmcclient application will get an
invalid session error.

**Future stage**: In a future stage, this can be improved by persisting the
session ID store, so that a restarted WS-API proxy can resume with the same set
of open sessions as before the crash. It needs to be investigated what
additional state of the server would need to be preserved across a server
restart.

## Implementation of the WS-API proxy

The WS-API proxy uses the "FastAPI" package for the API handling and "uvicorn"
for running the server. These packages use Python async support, which in turn
requires most code in the the WS-API proxy to also use Python async support.
That results in a state-of-the-art implementation that is lightweight, fast and
can handle many clients.
