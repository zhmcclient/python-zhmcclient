.. Copyright 2016-2017 IBM Corp. All Rights Reserved.
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

.. _`Concepts`:

Concepts
========

This section presents some concepts that are helpful to understand when using
the zhmcclient package.


.. _`Topology`:

Topology
--------

The following figure shows the topology of Python applications using the
zhmcclient package with an :term:`HMC` and the :term:`CPCs <CPC>` managed by
that HMC:

.. code-block:: text

  +----------------------------------------+  +--------------------+
  |                  Node 1                |  |       Node 2       |
  |                                        |  |                    |
  |  +----------------+  +--------------+  |  |  +--------------+  |
  |  |  Python app 1  |  | Python app 2 |  |  |  | Python app 3 |  |
  |  +----------------+  +--------------+  |  |  +--------------+  |
  |  |   zhmcclient   |  |  zhmcclient  |  |  |  |  zhmcclient  |  |
  |  | S      S   NR  |  |    S  NR     |  |  |  |     S        |  |
  |  +-v------v---^---+  +----v--^------+  |  |  +-----v--------+  |
  +----|------|---|-----------|--|---------+  +--------|-----------+
       |      |   |           |  |                     |
   REST|  REST|   |JMS    REST|  |JMS              REST|
       |      |   |           |  |                     |
  +----v------v---^-----------v--^---------------------v-----------+
  |                                                                |
  |                             HMC                                |
  |                                                                |
  |                      ... resources ...                         |
  |                                                                |
  +-------------+------------------------------------+-------------+
                |                                    |
                |                                    |
  +-------------+------------+         +-------------+-------------+
  |                          |         |                           |
  |           CPC 1          |         |          CPC 2            |
  |                          |         |                           |
  |     ... resources ...    |         |    ... resources ...      |
  |                          |         |                           |
  +--------------------------+         +---------------------------+

The Python applications can be for example the
``zhmc`` CLI (provided in the :term:`zhmccli project`), your own Python
scripts using the zhmcclient API, or long-lived services that perform some
function. In any case, each Python application in the figure runs in the
runtime of exactly one Python process.

In that Python process, exactly one instance of the zhmcclient Python package
is loaded. Performing HMC operations on a particular HMC requires a
:class:`~zhmcclient.Session` object (shown as ``S`` in the figure). Receiving
notifications from a particular HMC requires a
:class:`~zhmcclient.NotificationReceiver` object (shown as ``NR`` in the
figure).

For example, Python app 1 in the figure has two sessions and one notification
receiver. For simplicity, the two sessions go to the same HMC in this example,
but they could also go to different HMCs. Similarly, a Python app could
receive notifications from more than one HMC.


.. _`Multi-threading considerations`:

Multi-threading considerations
------------------------------

The zhmcclient package supports the use of multi-threading in Python processes,
but each :class:`~zhmcclient.Session`, :class:`~zhmcclient.Client`, and
:class:`~zhmcclient.NotificationReceiver` object can be used by only one thread
at a time. However, this is not verified or enforced by the zhmcclient package,
so ensuring this is a responsibility of the user of the zhmcclient package.

If your Python app is multi-threaded, it is recommended that each thread with a
need to perform HMC operations has its own :class:`~zhmcclient.Session` object
and its own :class:`~zhmcclient.Client` object, and that each thread with a
need to receive HMC notifications has its own
:class:`~zhmcclient.NotificationReceiver` object. These different objects can
very well target the same HMC.


.. _`Resource model concepts`:

Resource model concepts
-----------------------

The zhmcclient package provides a resource model at its API that represents
exactly the resource model described in the :term:`HMC API` book.
Some of these resources are located on the HMC (for example HMC users), and
some on the CPCs managed by the HMC (for example the CPC itself, or partitions
on the CPC).

The entry points for a user of the zhmcclient API are two objects that need
to be created by the user:

* a :class:`~zhmcclient.Session` object. A session object represents a REST
  session with exactly one HMC and handles all aspects of the session, such as
  the credentials for automatic logon and re-logon, the retry and timeout
  configuration, or the logging configuration.

* a :class:`~zhmcclient.Client` object. A client object is the top of the
  resource tree and is initialized with a :class:`~zhmcclient.Session` object
  (if connecting to a real HMC) or with a
  :class:`~zhmcclient_mock.FakedSession` object (in unit tests that work
  against a mocked HMC). Despite its classname, a client object really
  represents the HMC (real or mocked).

A session that is logged on is always in the context of the HMC userid that was
used for the session. That HMC userid determines what the Python application
using that session object can see and what it is allowed to do. See
:ref:`Setting up the HMC` for a list of access rights that are needed in
order to see all resources and to perform all tasks supported by the
zhmcclient package. The :term:`HMC API` book details for each HMC operation
which access rights are needed in order to perform the operation.

A client object is the top of the resource tree exposed by an HMC. Resources
located on the HMC (e.g. HMC userids) are direct or indirect children of the
client object. The CPCs managed by the HMC are direct children of the client
object, and the resources located on each CPC are direct or indirect children
of the :class:`~zhmcclient.Cpc` object representing the CPC. There is a strict
parent-child relationship in the resource model, so that the resource model is
a strict tree without any shared children.

For each actual managed resource on the HMC or its managed CPCs, the
zhmcclient package may provide more than one Python object representing that
resource. For example, the child resources of a resource can be listed by
using the :meth:`~zhmcclient.BaseManager.list` method. Each time that method is
invoked, it returns a new list of Python objects representing the state of
the child resources at the time the call was made.

This is an important principle in the design of the zhmcclient API: Whenever a
Python object representing a resource (i.e. objects of subclasses of
:class:`~zhmcclient.BaseResource`) is returned to the caller of the zhmcclient
API, its state represents the state of the actual managed resource at the time
the call was made, but the state of the Python resource object is not
automatically being updated when the state of the actual managed resource
changes.

As a consequence, there are multiple Python resource objects for the same
actual managed resource.

All Python resource objects provided by the zhmcclient package can be asked to
update their state to match the current state of the actual managed resource,
via the :meth:`~zhmcclient.BaseResource.pull_full_properties` method.
Alternatively, a new Python resource object with the current state of the
actual managed resource can be retrieved using the
:meth:`~zhmcclient.BaseManager.find` method using filters on name or object ID
so that only the desired single resource is returned. See :ref:`Filtering` for
details.

With the exception of the :class:`~zhmcclient.Client` object, Python resource
objects are never created by the user of the zhmcclient package. Instead, they
are always returned back to the user. Most of the time, resource objects are
returned from methods such as :meth:`~zhmcclient.BaseManager.list`,
:meth:`~zhmcclient.BaseManager.find` or
:meth:`~zhmcclient.BaseManager.findall`. They are methods on a manager object
that handles the set of child resources of a particular type within a parent
resource. For example, the :class:`~zhmcclient.Client` object has a
:attr:`~zhmcclient.Client.cpcs` instance attribute of type
:class:`~zhmcclient.CpcManager` which handles the CPCs managed by the HMC.
Invoking :meth:`~zhmcclient.CpcManager.list` returns the CPCs managed by
the HMC as :class:`~zhmcclient.Cpc` resource objects. Each
:class:`~zhmcclient.Cpc` object has again instance attributes for its child
resources, for example its :attr:`~zhmcclient.Cpc.partitions` instance attribute
of type :class:`~zhmcclient.PartitionManager` handles the set of partitions of
that CPC (but not the partitions of other CPCs managed by this HMC).

See :ref:`Resources` for a description of the resource model supported by
the zhmcclient package.


.. _`Error handling`:

Error handling
--------------

Errors are returned to the user by raising exceptions. All exception classes
defined in the zhmcclient package are derived from :class:`zhmcclient.Error`.

Exceptions may be raised that are not derived from :class:`~zhmcclient.Error`.
In all cases where this is possible, this is very likely caused by programming
errors of the user (incorrect type passed in, invalid value passed in, etc.).

Some HTTP status code / reason code combinations returned from the HMC are
silently handled by the zhmcclient package:

* GET, POST, or DELETE with status 403 and reason 5: This combination means
  that the HMC session token has expired. It is handled by re-logon, creating a
  new session token, and retrying the original HMC operation.

* POST with status 202: This status code means that the operation is being
  performed asynchronously. There are two cases for that:

  * If there is a response body, an asynchronous job has been started on the
    HMC that performs the actual operation. If ``wait_for_completion`` is
    ``True`` in the method that invoked the HMC operation, the method waits for
    completion of the job (via polling with GET on the job URI), gathering
    success or failure from the job results. In case of success, the job
    results are returned from the method. In case of failure, an
    :class:`~zhmcclient.HTTPError` is raised based upon the error information
    in the job results.

  * If there is no response body, the operation is performed asynchronously
    on the HMC, but there is no job resource that can be used to poll for
    completion status. This is used only for operations such as restarting the
    HMC.

The other HTTP status / reason code combinations are forwarded to the user by
means of raising :class:`~zhmcclient.HTTPError`. That exception class is
modeled after the error information described in section "Error response
bodies" of the :term:`HMC API` book.

The exception classes defined in the zhmcclient package are described in
section :ref:`Exceptions`.


.. _`Filtering`:

Filtering
---------

The resource lookup methods on manager objects support the concept of resource
filtering. This concept allows narrowing the set of returned resources based
upon the matching of filter arguments.

The methods that support resource filtering, are:

* :meth:`~zhmcclient.BaseManager.findall`
* :meth:`~zhmcclient.BaseManager.find`
* :meth:`~zhmcclient.BaseManager.list`

A resource is included in the result only if it matches all filter arguments
(i.e. this is a logical AND between the filter arguments).

A filter argument specifies a property name and a match value.

Any resource property may be specified in a filter argument. The zhmcclient
implementation handles them in an optimized way: Properties that can be
filtered on the HMC are actually filtered there (this varies by resource type),
and the remaining properties are filtered on the client side.

For the :meth:`~zhmcclient.BaseManager.findall` and
:meth:`~zhmcclient.BaseManager.find` methods, an additional optimization is
implemented: If the "name" property is specified as the only filter argument,
an optimized lookup is performed that uses a name-to-URI cache in this manager
object.

The match value specifies how the corresponding resource property matches:

* For resource properties of type String (as per the resource's data model in
  the :term:`HMC API`), the match value is interpreted as a regular
  expression that must match the actual resource property value. The regular
  expression syntax used is the same as that used by the Java programming
  language, as specified for the ``java.util.regex.Pattern`` class (see
  http://docs.oracle.com/javase/7/docs/api/java/util/regex/Pattern.html).

* For resource properties of type String Enum, the match value is interpreted
  as an exact string that must be equal to the actual resource property value.

* For resource properties of other types, the match value is interpreted
  as an exact value that must be equal to the actual resource property value.

* If the match value is a list or a tuple, a resource matches if any item in
  the list or tuple matches (i.e. this is a logical OR between the list items).

If a property that is specified in filter arguments does not exist on all
resources that are subject to be searched, those resources that do not have the
property are treated as non-matching. An example for this situation is the
"card-location" property of the Adapter resource which does not exist for
Hipersocket adapters.

Examples:

* This example uses the :meth:`~zhmcclient.BaseManager.findall` method to
  return those OSA adapters in cage '1234' of a given CPC, whose state is
  'stand-by', 'reserved', or 'unknown':

  .. code-block:: python

      filter_args = {
          'adapter-family': 'osa',
          'card-location': '1234-.*',
          'state': ['stand-by', 'reserved', 'unknown'],
      }
      osa_adapters = cpc.adapters.findall(**filter_args)

  The returned resource objects will have only a minimal set of properties.

* This example uses the :meth:`~zhmcclient.AdapterManager.list` method to
  return the same set of OSA adapters as the previous example, but the returned
  resource objects have the full set of properties:

  .. code-block:: python

      osa_adapters = cpc.adapters.list(full_properties=True,
                                       filter_args=filter_args)

* This example uses the :meth:`~zhmcclient.BaseManager.find` method to
  return the adapter with a given adapter name:

  .. code-block:: python

      adapter1 = cpc.adapters.find(name='OSA-1')

  The returned resource object will have only a minimal set of properties.

* This example uses the :meth:`~zhmcclient.BaseManager.find` method to
  return the adapter with a given object ID:

  .. code-block:: python

      oid = '12345-abc...-def-67890'
      adapter1 = cpc.adapters.find(**{'object-id':oid})

  The returned resource object will have only a minimal set of properties.
