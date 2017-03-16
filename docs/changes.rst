.. Copyright 2016 IBM Corp. All Rights Reserved.
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


.. _`Change log`:

Change log
----------


Version 0.11.0
^^^^^^^^^^^^^^

Released: 2017-03-16

**Incompatible changes:**

* Changed the return value of all methods on resource classes that invoke
  asynchronous operations (i.e. all methods that have a `wait_for_completion`
  parameter), as follows:

  - For `wait_for_completion=True`, the JSON object in the 'job-results' field
    is now returned, or `None` if not present (i.e. no result data).
    Previously, the complete response was returned as a JSON object.

  - For `wait_for_completion=False`, a new `Job` object is now returned that
    allows checking and waiting for completion directly on the `Job` object.
    Previously, the whole response of the 'Query Job Status' operation was
    returned as a JSON object, and the job completion was checked on the
    `Session` object, and one could not wait for completion.

* Changed the default value of the `wait_for_completion` parameter of the
  `Session.post()` method from `True` to `False`, in order to avoid
  superfluos timestats entries. This method is not normally used by
  users of the zhmcclient package.

* Removed the version strings from the ``args[]`` property of the
  ``zhmcclient.VersionError`` exception class. They had been available as
  ``args[1]`` and ``args[2]``. ``args[0]`` continues to be the error message,
  and the ``min_api_version`` and ``api_version`` properties continue to
  provide the version strings.

**Deprecations:**

**Bug fixes:**

* Added a minimum version requirement `>=4.0.0` for the dependency on the
  "decorate" Python package (issue #199).

* Increased minimum version of "click-spinner" package to 0.1.7, in order to
  pick up the fix for zhmcclient issue #116.

* Fixed CLI help text for multiple commands, where the text was incorrectly
  flowed into a paragraph.

**Enhancements:**

* Added support for retry/timeout configuration of HTTP sessions, via
  a new ``RetryTimeoutConfig`` class that can be specified for the ``Session``
  object. The retry/timeout configuration can specify:

  - HTTP connect timeout and number of retries.

  - HTTP read timeout (of HTTP responses), and number of retries.

  - Maximum number of HTTP redirects.

* Added new exceptions ``zhmcclient.ConnectTimeout`` (for HTTP connect
  timeout), ``zhmcclient.ResponseReadTimeout`` (for HTTP response read
  timeout), and ``zhmcclient.RequestRetriesExceeded`` (for HTTP request retry
  exceeded). They are all derived from ``zhmcclient.ConnectionError``.

* Fixed a discrepancy between documentation and actual behavior of the return
  value of all methods on resource classes that invoke asynchronous operations
  (i.e. all methods that have a `wait_for_completion` parameter). See also
  the corresponding incompatible change (issue #178).

* In the CLI, added a 'help' command that displays help for interactive mode,
  and a one-line hint that explains how to get help and how to exit
  interactive mode (issue #197).

* In the CLI, added support for command history. The history is stored in
  the file `~/.zhmc_history`.

* In the CLI, changed the prompt of the interactive mode to `zhmc> `.

* Added support for tolerating HTML content in the response, instead of JSON.
  An HTML formatted error message may be in the response for some 4xx and
  5xx HTTP status codes (e.g. when the WS API is disabled). Such responses
  are raised as ``HTTPError`` exceptions with an artificial reason code of 999.

* Fixed an incorrect use of the ``zhmcclient.AuthError`` exception and
  unnecessary checking of HMC behavior, i.e. when the HMC fails with "API
  session token expired" for an operation that does not require logon. This
  error should never be returned for operations that do not require logon. If
  it would be returned, it is now handled in the same way as when the operation
  does require logon, i.e. by a re-logon.

* Added support for deferred status polling to the
  `Lpar.activate/deactivate/load()` methods. The HMC operations issued by these
  methods exhibit "deferred status" behavior, which means that it takes a few
  seconds after successful completion of the asynchronous job that executes the
  operation, until the new status can be observed in the 'status' property of
  the LPAR resource. These methods will poll the LPAR status until the desired
  status value is reached. A status timeout can be specified via a new
  `status_timeout` parameter to these methods, which defaults to 60 seconds.
  If the timeout expires, a new `StatusTimeout` exception is raised
  (issue #191).

* Added operation timeout support to `Session.post()` and to all resource
  methods with a `wait_for_completion` parameter (i.e. the asynchronous
  methods). The operation timeout on the asynchronous methods can be specified
  via a new `operation_timeout` parameter, which defaults to 3600 seconds.
  If the timeout expires, a new `OperationTimeout` exception is raised
  (issue #6).

* Added a new module that defines public constants, and that defines
  default timeout and retry values.

* Experimental: In the CLI, added more supported table formats (plain,
  simple, psql, rst, mediawiki, html, LaTeX).

**Known Issues:**

* See `list of open issues`_.

.. _`list of open issues`: https://github.com/zhmcclient/python-zhmcclient/issues


Version 0.10.0
^^^^^^^^^^^^^^

Released: 2017-02-02

**Incompatible changes:**

* The support for server-side filtering caused an incompatibility for the
  `find()` and `findall()` methods: For String typed resource properties,
  the provided filter string is now interpreted as a regular expression
  that is matched against the actual property value, whereby previously it
  was matched by exact string comparison.

* The parameter signatures of the `__init__()` methods of `BaseResource` and
  `BaseManager` have changed incompatibly. These methods have always been
  considered internal to the package. They are now explicitly stated to be
  internal and their parameters are no longer documented.
  If users have made themselves dependent on these parameters (e.g. by writing
  a mock layer), they will need to adjust to the new parameter signature. See
  the code for details.

**Deprecations:**

**Bug fixes:**

* Fixed a bug where the CLI code tries to access 'cpc'  from the 'partition'
  directly without going via the manager property. This caused
  an AttributeError (issue #161).

* Fixed unrecognized field ('adapter-port') during 'HBA create' (issue #163).

**Enhancements:**

* Added filter arguments to the `list()` method, and added support for
  processing as many filter arguments as supported on the server side via
  filter query parameters in the URI of the HMC List operation. The remaining
  filter arguments are processed on the client side in the `list()` method.

* Changed the keyword arguments of the `find()` and `findall()` methods to be
  interpreted as filter arguments that are passed to the `list()` method.

* Documented the authorization requirements for each method, and in total
  in a new section "Setting up the HMC".

* Added a method `open_os_message_channel()` on Partition and Lpar objects,
  that returns a notification token for receiving operating system messages
  as HMC notifications.

* Experimental: Added a class `NotificationReceiver` that supports receiving
  and iterating through HMC notificationsi for a notification token, e.g.
  those produced by `open_os_message_channel()`.


Version 0.9.0
^^^^^^^^^^^^^

Released: 2017-01-11

**Incompatible changes:**

**Deprecations:**

**Bug fixes:**

* Fixed a bug where accessing the 'name' property via the `properties`
  attribute caused `KeyError` to be raised (issue #137). Note that there
  is now a recommendation to use `get_property()` or the `name` or `uri`
  attributes for accessing specific properties. The `properties` attribute
  should only be used for iterating over the currently present resource
  properties, but not for expecting particular properties.

* Fixing regression in findall(name=..) (issue #141).

**Enhancements:**

* Changed links to HMC API books in Bibliography to no longer require IBM ID
  (issue #131).

* Added example shell script showing how to use the command line interface.

* Improved the examples with better print messages, exception handling,
  access of resource properties, and refreshing of resources.

* Added support for load-parameter field in lpar.load().


Version 0.8.0
^^^^^^^^^^^^^

Released: 2016-12-27

**Incompatible changes:**

**Deprecations:**

**Bug fixes:**

**Enhancements:**

* Added support in CLI for remaining cmds; client improvements.

* Added a tool 'tools/cpcdata' for gathering information about all
  CPCs managed by a set of HMCs. The data can optionally be appended
  to a CSV spreadsheet, for regular monitoring.


Version 0.7.0
^^^^^^^^^^^^^

Released: 2016-12-08

**Bug fixes:**

* IOError during click-spinner 0.1.4 install (issue #120)

**Enhancements:**

* Documentation for zhmc CLI


Version 0.6.0
^^^^^^^^^^^^^

Released: 2016-12-07

**Bug fixes:**

* Fixed typo in help message of cpcinfo.

* Fixed KeyError: 'status' when running example5.py (issue #99).

* Fixed documentation of field Partition.hbas (issue #101).

* Fixed new Flake8 issue E305.

**Enhancements:**

* Started raising a `ParseError` exception when the JSON payload in a HTTP
  response cannot be parsed, and improved the definition of the ParseError
  exception by adding line and column information.

* Improved the `AuthError` and `ConnectionError` exceptions by adding a
  `details` property that provides access to the underlying exception
  describing details.

* For asynchronous operations that are invoked with `wait_for_completion`,
  added an entry in the time statistics for the overall operation
  from the start to completion of the asynchronous operation. That entry
  is for a URI that is the target URI, appended with "+completion".

* Added time statistics entry for overall asynchronous operations.

* Improved VersionError exception class and removed number-of-args tests.

* Added the option to create a session object with a given session id.

* Added base implementation of a command line interface (zhmc)
  for the zhmcclient.


Version 0.5.0
^^^^^^^^^^^^^

Released: 2016-10-04

**Incompatible changes:**

* In ``VirtualSwitch.get_connected_vnics()``, renamed the method to
  :meth:`~zhmcclient.VirtualSwitch.get_connected_nics` and changed its return value
  to return :class:`~zhmcclient.Nic` objects instead of their URIs.

**Deprecations:**

**Bug fixes:**

* Fixed that in `Partition.dump_partition()`, `wait_for_completion` was always
  passed on as `True`, ignoring the corresponding input argument.

**Enhancements:**

* Added a script named ``tools/cpcinfo`` that displays information about CPCs.
  Invoke with ``-h`` for help.

* Added a :meth:`~zhmcclient.BaseResource.prop` method for resources that
  allows specifying a default value in case the property does not exist.

* Added :meth:`~zhmcclient.Cpc.get_wwpns` which performs HMC operation
  'Export WWPN List'.

* Added :meth:`~zhmcclient.Hba.reassign_port` which performs HMC operation
  'Reassign Storage Adapter Port'.

* Clarifications in the :ref:`Resource model` section.

* Optimized :attr:`~zhmcclient.Cpc.dpm_enabled` property to use
  'List Partitions' and  'List Logical Partitions' operations, in order to
  avoid the 'List CPC Properties' operation.

* Improved tutorials.


Version 0.4.0
^^^^^^^^^^^^^

Released: 2016-09-13

This is the base version for this change log.
