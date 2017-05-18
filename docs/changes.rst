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


Version 0.13.0
^^^^^^^^^^^^^^

Released: 2017-05-18

**Incompatible changes:**

* In the CLI, changed the default for number of processors for the
  ``zhmc partition create`` command to create 1 IFL by default, if neither
  IFLs nor CPs had been specified. Also, a specified number of 0 processors
  is now passed on to the HMC (and rejected there) instead of being removed
  by the CLI. This keeps the logic simpler and more understandable. See
  also issue #258.

**Deprecations:**

* Deprecated the ``BaseManager.flush()`` method in favor of the new
  ``BaseManager.invalidate_cache()`` method.

**Bug fixes:**

* Fixed that the defaults for memory for the ``zhmc partition create`` command
  were ignored (issue #246).

* The default values for the retry / timeout configuration for a session has
  been changed to disable read retries and to set the read timeout to 1 hour.
  In addition, read retries are now restricted to HTTP GET methods, in case
  the user enabled read retries. See issue #249.

* Fixed that resource creation, deletion, and resource property updating now
  properly updates the resource name-to-URI cache in the zhmcclient that is
  maintained in the `*Manager` objects. As part of that, the `BaseManager`
  init function got an additional required argument `session`, but because
  creation of manager objects is not part of the external API, this should not
  affect users. See issue #253.

* In the unit testcases for the `update_properties()` and `delete()` methods of
  resource classes, fixed incorrect assumptions about their method return
  values. See issue #256.

* In the unit testcases for the `update_properties()` and `delete()` methods of
  resource classes, fixed incorrectly returned response bodies for mocked
  DELETE and POST (for update), and replaced that with status 204 (no content).
  This came up as part of fixing issue #256.

* Fixed that ``find(name)`` raised ``NotFound`` for existing resources, for
  resource types that are elements (i.e. NICs, HBAs, VFs, Ports) (issue #264).

* Fixed that the filter arguments for ``find()``, ``findall()``, and ``list()``
  for string properties when matched on the client side are matched using
  regular expressions instead of exact matching, consistent with the
  zhmcclient documentation, and with server-side matching on the HMC. See
  issue #263.

* Fixed that the filter arguments for ``find()``, ``findall()``, and ``list()``
  when used with lists of match values incorrectly applied ANDing between the
  list items. They now apply ORing, consistent with the zhmcclient
  documentation, and with server-side matching on the HMC. See issue #267.

* Fixed that the ``Cpc.dpm_enabled`` property incorrectly returned ``True`` on
  a z13 in classic mode. See issue #277.

* Fixed errors in zhmcclient mock support related to DPM mode checking.

* Fixed that filter arguments specifying properties that are not on each
  resource, resulted in raising KeyError. An example was when the
  "card-location" property was specified when finding adapters; that property
  does not exist for Hipersocket adapters, but for all other types. This
  situation is now handled by treating such resources as non-matching.
  See issue #271.

* Fix when providing 'load-parameter' option. See issue #273

**Enhancements:**

* Added content to the "Concepts" chapter in the documentation.

* The `update_properties()` method of all Python resource objects now also
  updates the properties of that Python resource object with the properties
  provided by the user (in addition to issuing the corresponding Update
  Properties HMC operation. This was done because that is likely the
  expectation of users, and we already store user-provided properties in Python
  resource objects when creating resources so it is now consistent with that.
  This came up as part of issue #253.

* As part of fixing the name-to-URI cache, a new attribute
  `name_uri_cache_timetolive` was added to class `RetryTimeoutConfig`, which
  allows controlling after what time the name-to-URI cache is automatically
  invalidated. The default for that is set in a new
  `DEFAULT_NAME_URI_CACHE_TIMETOLIVE` constant. Also, the `*Manager` classes
  now have a new method `invalidate_cache()` which can be used to
  manually invalidate the name-to-URI cache, for cases where multiple parties
  (besides the current zhmcclient instance) change resources on the HMC.
  This came up as part of issue #253.

* Improved the documentation of the lookup methods (list(), find(), findall())
  and of the resource filtering concept in section 'Filtering'. Related to
  issue #261.

* Added zhmcclient mock support for the Create Hipersocket and Delete
  Hipersocket operations.

* Added support for filtering in the zhmcclient mock support.

* In order to improve the ability to debug the resource and manager objects at
  the API and the faked resource and manager objects of the mock support,
  the ``__repr()__`` methods ahave been improved. Because these functions now
  display a lot of data, and because testing their string layout is not very
  interesting, all unit test cases that tested the result of ``__repr()__``
  methods have been removed.

* Add basic Secure Service Container support to the CLI.

**Known issues:**

* See `list of open issues`_.

.. _`list of open issues`: https://github.com/zhmcclient/python-zhmcclient/issues


Version 0.12.0
^^^^^^^^^^^^^^

Released: 2017-04-13

**Incompatible changes:**

* The password retrieval function that can optionally be passed to
  ``Session()`` has changed its interface; it is now being called with host and
  userid. Related to issue #225.

**Deprecations:**

**Bug fixes:**

* Added WWPN support in mocking framework (issue #212).

* Fixed error in mock support where the `operation_timeout` argument to
  `FakedSession.post()` was missing.

* Fixed a bug in the unit test for the mock support, that caused incomplete
  expected results not to be surfaced, and fixed the incomplete testcases.

* Fixed in the CLI that the spinner character was part of the output.

* Improved robustness of timestats tests by measuring the actual sleep time
  instead of going by the requested sleep time.

* Added support for 'error' field in 'job-results' (fixes issue #228).

* Fixed version mismatches in CI test environment when testing with
  the minimum package level by consistently using the latest released
  packages as of zhmcclient v0.9.0 (2016-12-27). This caused an increase
  in versions of packages needed for the runtime.

**Enhancements:**

* Improved the mock support by adding the typical attributes of its superclass
  `FakedBaseResource` to the `FakedHmc` class.

* Improved the mock support by adding `__repr__()` methods to all `Faked*`
  classes that return an object representation suitable for debugging.

* In the mock support, the following resource properties are now auto-set if
  not specified in the input properties:

  - Cpc:

    - 'dpm-enabled' is auto-set to `False`, if not specified.
    - 'is-ensemble-member' is auto-set to `False`, if not specified.
    - 'status' is auto-set, if not specified, as follows: If the
      'dpm-enabled' property is `True`, it is set to 'active';
      otherwise it is set to 'operating'.

  - Partition: 'status' is auto-set to 'stopped', if not specified.

  - Lpar: 'status' is auto-set to 'not-activated', if not specified.

  - Adapter: 'status' is auto-set to 'active', if not specified.

* In the CLI, added ``-y`` as a shorter alternative to the existing ``--yes``
  options, that allow skipping confirmation prompts.

* Added OS-X as a test environment to the Travis CI setup.

* In the CLI, added a ``-p`` / ``--password`` option for specifying the HMC
  password (issue #225).

* Added logging support to the zhmc CLI (issue #113).

* Added 'load-parameter' option to 'zhmc lpar load' (issue #226).

**Known Issues:**


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

* Changed the names of the Python loggers as follows:

  1. Logger 'zhmcclient.api' logs API calls made by the user of the package,
     at log level DEBUG. Internal calls to API functions are no longer logged.

  2. Logger 'zhmcclient.hmc' logs HMC operations. Their log level has been
     changed from INFO to DEBUG.

* Removed the log calls for the HMC request ID.

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

* In the CLI, changed the prompt of the interactive mode to ``zhmc>``.

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

* Improved the content of the log messages for logged API calls and HMC
  operations to now contain the function call arguments and return values (for
  API calls) and the HTTP request and response details (for HMC operations).
  For HMC operations and API calls that contain the HMC password, the password
  is hidden in the log message by replacing it with a few '*' characters.

**Known Issues:**


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
