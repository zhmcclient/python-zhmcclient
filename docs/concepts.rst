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


.. _`Specifying multiple redundant HMCs`:

Specifying multiple redundant HMCs
----------------------------------

The zhmcclient package supports the specification of one or more HMCs through
the `host` init parameter of :class:`zhmcclient.Session`.

That paranmeter can be specified as a single HMC, for example:

.. code-block:: python

    session = zhmcclient.Session(host='10.11.12.13', ...)

or as a list of one or more HMCs, for example:

.. code-block:: python

    session = zhmcclient.Session(host=['10.11.12.13', '10.11.12.14'], ...)

There is no difference between specifying a single HMC as a string or as a
list with one item.

When a list is specified, it must contain at least one HMC.

If the list contains more than one HMC, a working HMC is selected from that list
during each logon (and re-logon) to the HMC, and that HMC continues to be used
by that :class:`zhmcclient.Session` object until logoff.

If a :class:`zhmcclient.Session` object is created by specifying the
`session_id` init parameter, the corresponding HMC host for that session must
be provided as the only HMC in the `host` init parameter.


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


.. _`Auto-updating`:

Auto-updating
-------------

The resource objects returned by the zhmcclient library support auto-updating
of resource properties.

Similarly, the resource manager objects returned by the zhmcclient library
support auto-updating of their list of resources they maintain locally.

By default, auto-updating is disabled for any resource or manager objects.
The :meth:`~zhmcclient.BaseResource.pull_full_properties` method can be used
to have the properties of the resource object updated explicitly, and
the :meth:`~zhmcclient.BaseManager.list` method (or related ``find...()``
methods) can be used to list the resources in scope of a resource manager
object.

If auto-updating is enabled for a resource object (by means of
:meth:`zhmcclient.BaseResource.enable_auto_update`), the zhmcclient library
subscribes on the HMC for object notifications that inform the client about
changes to resource properties. When receiving such notifications, the client
updates the properties on the local resource objects that are enabled for
auto-updating, to the new values.

If auto-updating is enabled for a manager object (by means of
:meth:`zhmcclient.BaseManager.enable_auto_update`), the zhmcclient library
subscribes on the HMC for object notifications that inform the client about
changes to the resource inventory. When receiving such notifications, the client
updates the list of resources maintained by the local manager objects
that are enabled for auto-updating, to add or remove resources.

There is only one subscription at the HMC for each zhmcclient session that has
auto-updating enabled, so if auto-updating is enabled for a second and further
resource or manager objects, the already existing subscription is used. When
disabling auto-updating, the last resource or manager that is disabled will
unsubscribe at the HMC.

The subscription for object notifications will cause the following notifications
to be sent from the HMC to the client:

*  property change notifications for any properties that have the
   property-change (pc) qualifier set, for all resources,
*  status change notifications for any properties that have the
   status-change (sc) qualifier set, for all resources,
*  inventory change notifications for any resources that come into existence or
   go out of existence.

The auto-update support for resource objects processes the property and status change
notifications by updating the correponding properties in those resource objects
that have been enabled for auto-updating. As a result, these properties will
always have the value the resource object has on the HMC.
The inventory change notification is used to set the
:attr:`~zhmcclient.BaseResource.ceased_existence` attribute of the resource if
it no longer exists on the HMC.

Property, status and inventory change notifications for resource objects that
have not been enabled for auto-updating will be ignored.

The auto-update support for manager objects processes the inventory change
notifications to add or remove resource objects to or from the list of resources
it maintains locally, as the corresponding resources are created or deleted on
the HMC.

The delay for a changed property value or for a new or remnoved resource to
become visible in the zhmcclient resource or manager objects after the actual
change on the HMC, is very short. If the change is triggered by an HTTP request
to the HMC, the notification is usually received and processed before the
corresponding HTTP response is received.

Note that accessing the properties of a zhmcclient resource object is not any
slower when auto-update is enabled - the auto-update happens asynchronously
to the access, and depending on whether the access happens before or after an
auto-update, you get the old or new value. Similarly for the access to the
resource lists of a zhmcclient manager object.

Example for auto-updating of resources:

.. code-block:: python

    cpc = ...  # A zhmcclient.Cpc object
    partition_name = 'PART1'

    # Two different zhmcclient.Partition objects representing the same partition on the HMC
    partition1 = cpc.partitions.find(name=partition_name)
    partition2 = cpc.partitions.find(name=partition_name)
    assert id(partition1) != id(partition2)

    partition1.enable_auto_update()  # Enable auto-update for this partition object
    prop_name = 'description'

    while True:
        try:
            value1 = partition1.prop(prop_name)
        except zhmcclient.CeasedExistence:
            value1 = "N/A"
        value2 = partition2.prop(prop_name)
        print("Property '{}' of objects 1: {!r}, 2: {!r}".
              format(prop_name, value1, value2))
        sleep(1)

This example creates two different partition objects representing the same
partition on the HMC. It enables auto-update for one of the partition objects
but not for the other, in order to show the different behavior.

The example then prints the value of the 'description' property of both
partition objects in a loop, so that in parallel, a change of the description
of the partition can be performed on the HMC (not shown in the example).

Once the description of the partition on the HMC is changed, the partition
object that has auto-update enabled will show the new value, while the other
one will show the same value unchanged:

.. code-block:: text

    Property 'description' of objects 1: 'foo', 2: 'foo'
    Property 'description' of objects 1: 'foo', 2: 'foo'
    Property 'description' of objects 1: 'foo', 2: 'foo'

    # description property is changed to 'bar' on the HMC

    Property 'description' of objects 1: 'bar', 2: 'foo'
    Property 'description' of objects 1: 'bar', 2: 'foo'
    Property 'description' of objects 1: 'bar', 2: 'foo'

If the partition is deleted on the HMC, the partition object that has
auto-update enabled will raise :exc:`zhmcclient.CeasedExistence` upon
accessing the property value, while the other one will show the same value
unchanged:

.. code-block:: text

    Property 'description' of objects 1: 'foo', 2: 'foo'
    Property 'description' of objects 1: 'foo', 2: 'foo'
    Property 'description' of objects 1: 'foo', 2: 'foo'

    # partition gets deleted on the HMC

    Property 'description' of objects 1: 'N/A', 2: 'foo'
    Property 'description' of objects 1: 'N/A', 2: 'foo'
    Property 'description' of objects 1: 'N/A', 2: 'foo'

Example for auto-updating of resource managers:

.. code-block:: python

    cpc = ...  # A zhmcclient.Cpc object

    # Partition manager object for that CPC
    part_mgr = cpc.partitions

    # Get list of partitions when auto-updating is not enabled
    part_list = part_mgr.list()

    part_mgr.enable_auto_update()

    # Get list of partitions when auto-updating is enabled
    part_list = part_mgr.list()

The list() method for an auto-updated partition manager is faster because
only the locally maintained list of resources is returned, yet it is
automatically up to date with the partitions on the HMC.

Note that this also works for other list-related methods such as
:meth:`~zhmcclient.BaseManager.find()` or
:meth:`~zhmcclient.BaseManager.findall()`.


.. _`Feature enablement`:

Feature enablement
------------------

.. _`Firmware features`:

Firmware features
~~~~~~~~~~~~~~~~~

*Firmware features* have been introduced in HMC/SE version 2.14.0 with
HMC API version 2.23. They had originally been called just "features", and
with the later introduction of "API features", they had been renamed to
"firmware features".

Firmware features exist at the level of the CPC/SE. In order to support users
who are authorized for access to partitions but not to the CPC, the HMC WS-API
makes the information also available on partition objects, but all partitions
show the same feature information for the CPC of the partition.

Firmware features can be *available* (or not). A firmware feature is available
when it has been introduced with a particular HMC/SE version.

When a firmware feature is available, it can be *enabled* (or not). When it
is enabled, its functionality is active.

The enablement state of firmware features cannot be controlled through the
HMC WS-API. Firmware features may be always enabled once introduced (that is
the case for all currently existing firmware features), or can be enabled by
using standard feature enablement mechanisms.

The available firmware features and their enablement state are indicated
in the "available-features-list" property on the :meth:`zhmcclient.Cpc` and
:meth:`zhmcclient.Partition` objects.

Firmware features can be retrieved or tested with the following methods:

* :meth:`zhmcclient.Cpc.list_firmware_features`
* :meth:`zhmcclient.Cpc.firmware_feature_enabled`
* :meth:`zhmcclient.Cpc.feature_info`
* :meth:`zhmcclient.Partition.list_firmware_features`
* :meth:`zhmcclient.Partition.firmware_feature_enabled`
* :meth:`zhmcclient.Partition.feature_info`

Firmware features have the following :ref:`HMC/SE version requirements`:

===========================================  =============  =============  ====================
Firmware feature                             HMC version    SE version     Enablement mechanism
===========================================  =============  =============  ====================
dpm-storage-management                       >= 2.14.0 (1)  >= 2.14.0 (1)  Always enabled
dpm-fcp-tape-management                      >= 2.15.0      >= 2.15.0      Always enabled
dpm-smcd-partition-link-management           >= 2.16.0      >= 2.16.0      Always enabled
===========================================  =============  =============  ====================

Note (1): Requires to be at HMC API version >= 2.23, which on HMC 2.14
requires MCL P42675.232 and on SE 2.14 requires MCL P42601.286.

Firmware features are discussed further in :term:`HMC API` book Chapter 6,
"Features".

.. _`API features`:

API features
~~~~~~~~~~~~

*API features* have been introduced in HMC version 2.16.0 with
HMC API version 4.10. On an HMC 2.16, this requires bundle H14 and on an
SE 2.16, this requires bundle S19.

API features exist at the level of the HMC, at the level of each CPC/SE,
or both.

The functionality of an API feature is available when introduced with a
particular HMC/SE version, so there is no separate enablement state (you can
say that they are always enabled). If an API feature applies to both HMC and SE,
then it must be available on both HMC and SE in order for its functionality
to become fully available.

API features can be retrieved or tested with the following methods:

* :meth:`zhmcclient.Console.list_api_features`
* :meth:`zhmcclient.Console.api_feature_enabled`
* :meth:`zhmcclient.Cpc.list_api_features`
* :meth:`zhmcclient.Cpc.api_feature_enabled`

API features have the following :ref:`HMC/SE version requirements`:

===========================================  =============  =============
API feature                                  HMC version    SE version
===========================================  =============  =============
adapter-network-information                  >= 2.16.0 (1)  >= 2.16.0 (1)
bcpii-notifications                          N/A (2)        >= 2.16.0 (1)
cpc-delete-retrieved-internal-code           >= 2.16.0 (1)  >= 2.16.0 (1)
cpc-install-and-activate                     >= 2.16.0 (1)  >= 2.16.0 (1)
create-delete-activation-profiles            >= 2.16.0 (1)  >= 2.16.0 (1)
dpm-ctc-partition-link-management            >= 2.16.0 (1)  >= 2.16.0 (1)
dpm-hipersockets-partition-link-management   >= 2.16.0 (1)  >= 2.16.0 (1)
dpm-smcd-partition-link-management           >= 2.16.0 (1)  >= 2.16.0 (1)
environmental-metrics                        >= 2.16.0 (1)  >= 2.16.0 (1)
hmc-delete-retrieved-internal-code           >= 2.16.0 (1)  N/A (2)
ldap-direct-authentication                   >= 2.16.0 (1)  N/A (2)
mobile-enhanced-push                         >= 2.16.0 (1)  >= 2.16.0 (1)
oem-hmc-ids                                  >= 2.16.0 (1)  N/A (2)
pmg-child-management-permission              >= 2.16.0 (1)  N/A (2)
rc-409-15                                    >= 2.16.0 (1)  >= 2.16.0 (1)
rcl-history                                  >= 2.16.0 (1)  >= 2.16.0 (1)
rcl-progress                                 >= 2.16.0 (1)  >= 2.16.0 (1)
report-a-problem                             >= 2.16.0 (1)  >= 2.16.0 (1)
secure-boot-with-certificates                >= 2.16.0 (1)  >= 2.16.0 (1)
secure-execution-key-management              >= 2.16.0 (1)  >= 2.16.0 (1)
switch-support-elements                      >= 2.16.0 (1)  >= 2.16.0 (1)
===========================================  =============  =============

Note (1): Requires to be at HMC API version >= 4.10, which on HMC 2.16 requires
bundle H14 and on SE 2.16 requires bundle S19.

Note (2): N/A means that the API feature does not have a dependency on the
version of that element (HMC or SE) (in addition to the normal version
requirements between HMC and SE). For example, the
"hmc-delete-retrieved-internal-code" API feature depends only on the HMC
version, so it is available with all SE versions that can be managed by the HMC.

API features are discussed further in :term:`HMC API` book Chapter 6,
"Features".
