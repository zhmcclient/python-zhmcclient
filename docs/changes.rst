.. Copyright 2016-2018 IBM Corp. All Rights Reserved.
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


Version 0.23.0
^^^^^^^^^^^^^^

Released: 2019-04-04

**Bug fixes:**

* Fixed the list_storage_groups.py example. It used a non-existing property
  on the Cpc class.

* Passwords and session tokens are now correctly blanked out in logs.
  See issue #560.

**Enhancements:**

* Added support for the new "Zeroize Crypto Domain" operation that allows
  zeroizing a single crypto domain on a crypto adapter. This operation is
  supported on z14 GA2 and higher, and the corresponding LinuxOne systems.

* Changes in logging support:

  - Removed the notion of module-specific loggers from the description
    of the logging chapter, because that was not used at all, and is not
    expected to be used in the future: Errors are supposed to be raised
    as exceptions and not logged, and warnings are supposed to be issued
    as Python warnings and not logged.

  - Escaped newlines to blanks in log messages, so that all log messages
    are now on a single line.

  - Changed the syntax for zhmcclient.api log messages, to start with
    "Called:" and "Return:" instead of "==>" and "<==".

  - Changed the syntax for zhmcclient.hmc log messages, to start with
    "Request:" and "Respons:" instead of "HMC request:" and
    "HMC response:", in order to have the URLs column-adjusted.


Version 0.22.0
^^^^^^^^^^^^^^

Released: 2019-01-07

**Enhancements:**

* Added a mitigation for a firmware defect that causes filtering of
  adapters by adapter-id to return an empty result when the specified
  adapter-id contains hex digits ('a' to 'f'). See issue #549.


Version 0.21.0
^^^^^^^^^^^^^^

Released: 2018-10-31

**Bug fixes:**

* Update Requests package to 2.20.0 to fix following vulnerability of
  the National Vulnerability Database:
  https://nvd.nist.gov/vuln/detail/CVE-2018-18074


Version 0.20.0
^^^^^^^^^^^^^^

Released: 2018-10-24

**Bug fixes:**

* Docs: Added missing support statements for the LinuxOne Emperor II machine
  generations to the documentation (The corresponding z14 was already listed).

**Enhancements:**

* Docs: Streamlined, improved and fixed the description how to release a version
  and how to start a new version, in the development section of the documentation.

* Added support for Python 3.7. This required increasing the minimum versions
  of several Python packages in order to pick up their Python 3.7 support:

  - `pyzmq` from 16.0.2 to 16.0.4 (While 16.0.4 works for this, only
    17.0.0 declares Python 3.6(!) support on Pypi, and Python 3.7 support is not
    officially declared on Pypi yet for this package).
  - `PyYAML` from 3.12 to 3.13 (see PyYAML issue
    https://github.com/yaml/pyyaml/issues/126).

* Docs: Added support statements for the z14-ZR1 and LinuxONE Rockhopper II
  machine generations to the documentation.

* Added support for the z14-ZR1 and LinuxONE Rockhopper II machine generations
  to the `Cpc.maximum_active_partitions()` method.

* Provided direct access to the (one) `Console` object, from the
  `ConsoleManager` and `CpcManager` objects, via a new `console` property.
  This is for convenience and avoids having to code `find()` or `list()` calls.
  The returned `Console` object is cached in the manager object.

  Also, added a `console` property to the `FakedConsoleManager` class in the
  mock support, for the same purpose.

* Added a property `client` to class `CpcManager` for navigating from a `Cpc`
  object back to the `Client` object which is the top of the resource tree.

* Added support for the new concept of firmware features to Cpcs and Partitions,
  by adding methods `feature_enabled()` and `feature_info()` to classes `Cpc`
  and `Partition` for inspection of firmware features. The firmware feature
  concept was introduced starting with the z14-ZR1 and LinuxONE Rockhopper II
  machine generation. The DPM storage management feature is the first of these
  new firmware features.

* Added support for the DPM storage management feature that is available starting
  with the z14-ZR1 and LinuxONE Rockhopper II machine generation. This includes
  new resources like Storage Groups, Storage Volumes, and Virtual Storage Resources.
  It also includes new methods for managing storage group attachment to Partitions.
  The new items in the documentation are:

  - In 5.1. CPCs: `list_associated_storage_groups()`, `validate_lun_path()`.
  - In 5.5. Partitions: `attach_storage_group()`, `detach_storage_group()`,
    `list_attached_storage_groups()`.
  - 5.12. Storage Groups
  - 5.13. Storage Volumes
  - 5.14. Virtual Storage Resources
  - In 5.15 Console: `storage_groups`

* Added support for changing the type of storage adapters between FICON and FCP,
  via a new method `Adapter.change_adapter_type()`. This capability was introduced
  with the z14-ZR1 and LinuxONE Rockhopper II machine generation.


Version 0.19.11
^^^^^^^^^^^^^^^

Released: 2018-05-14

Note: The version number of this release jumped from 0.19.0 right to 0.19.11,
for tooling reasons.

**Enhancements:**

* Docs: Improved the description of installation without Internet access, and
  considerations on system Python vs. virtual Python environments.

* Lowered the minimum version requirements for installing the zhmcclient
  package, for the packages: requests, pbr, decorator. Added support for
  tolerating decorator v3.4 in the zhmcclient _logging module.

* Adjusted development environment to changes in Appveyor CI environment.


Version 0.19.0
^^^^^^^^^^^^^^

Released: 2018-03-15

**Incompatible changes:**

* The ``Lpar.deactivate()`` method is now non-forceful by default, but can be
  made to behave like previously by specifying the new ``force`` parameter.
  In force mode, the deactivation operation is permitted when the LPAR status
  is "operating".

**Bug fixes:**

* Fixed a flawed setup of setuptools in Python 2.7 on the Travis CI, where
  the metadata directory of setuptools existed twice, by adding a script
  `remove_duplicate_setuptools.py` that removes the moot copy of the metadata
  directory (issue #434).

* Fixed a bug where multiple Session objects shared the same set of
  HTTP header fields, causing confusion in the logon status.

**Enhancements:**

* Migrated all remaining test cases from unittest to pytest, and started
  improving the testcases using pytest specific features such as
  parametrization.

* Added support for a ``force`` parameter in the ``Lpar.activate()``,
  ``Lpar.deactivate()``, and ``Lpar.load()`` methods. It controls whether the
  operation is permitted when the LPAR status is "operating".

  Note that this changes ``Lpar.deactivate()`` to be non-forceful by default
  (force=True was hard coded before this change).

* Added support for an ``activation_profile_name`` option in the
  ``Lpar.activate()`` method, that allows specifying the activation profile
  to be used. The default is as before: The profile that is specified in the
  ``next-activation-profile`` property of the ``Lpar`` object.

* Made the ``load_address`` parameter of ``Lpar.load()`` optional in order
  to support z14. Up to z13, the HMC now returns an error if no load
  address is specified. Adjusted the zhmcclient mock support accordingly.

* Added LPAR status checks in the zhmcclient mock support, so that activate,
  deactivate and load returns the same errors as the real system when the
  initial LPAR status is not permitted, or when the activation profile name
  does not match the LPAR name, or when no load address is specified.

* Improved the testcases for the Lpar and LparManager classes.

* Added the ability to mock the resulting status of the faked Lpars in the
  zhmcclient mock support, for the Activate, Deactivate, and Load operations.
  Added a new chapter "URI handlers" in section "Mock support" of the
  documentation, to describe this new ability.

* Added support for CPC energy management operations:

  - ``Cpc.set_power_save()`` (HMC: "Set CPC Power Save")
  - ``Cpc.set_power_capping()`` (HMC: "Set CPC Power Capping")
  - ``Cpc.get_energy_management_properties()`` (HMC: "Get CPC Energy
    Management Data")

* The zhmcclient package no longer adds a NullHandler to the Python root
  logger (but still to the zhmcclient.api/.hmc loggers).

* Added a function test concept that tests against a real HMC.


Version 0.18.0
^^^^^^^^^^^^^^

Released: 2017-10-19

**Incompatible changes:**

* Removed the zhmc CLI support from this project, moving it into a new GitHub
  project ``zhmcclient/zhmccli``.

  This removes the following prerequisite Python packages for the zhmcclient
  package:

    - click
    - click-repl
    - click-spinner
    - progressbar2
    - tabulate
    - prompt_toolkit  (from click-repl)
    - python-utils  (from progressbar2)
    - wcwidth  (from prompt-toolkit -> click-repl)

**Bug fixes:**

* Fixed a flawed setup of setuptools in Python 2.7 on the Travis CI, where
  the metadata directory of setuptools existed twice, by adding a script
  `remove_duplicate_setuptools.py` that removes the moot copy of the metadata
  directory (issue #434).


Version 0.17.0
^^^^^^^^^^^^^^

Released: 2017-09-20

**Incompatible changes:**

* The zhmcclient mock support for Partitions no longer allows to stop a
  partition when it is in status 'degraded' or 'reservation-error'.
  That is consistent with the real HMC as described in the HMC API book.

* In the `HTTPError` exception class, `args[0]` was set to the `body` argument,
  i.e. to the entore response body. Because by convention, `args[0]` should be
  a human readable message, this has been changed to now set `args[0]` to the
  'message' field in the response body, or to `None` if not present.

**Bug fixes:**

* Fixed the bug that aborting a confirmation question in the CLI (e.g. for
  "zhmc partition delete") caused an AttributeError to be raised. It now
  prints "Aborted!" and in interactive mode, terminates only the current
  command. (issue #418).

* Fixed an AttributeError when calling 'zhmc vfunction update'.
  Access to a partition from nic and vfunction is done via the respective
  manager (issue #416).

* In the zhmc CLI, fixed that creating a new session reused an existing
  session. This prevented switching between userids on the same HMC
  (issue #422).

* Docs: In the "Introduction" chapter of the documentation, fixed the HMC API
  version shown for z14.

* Docs: In the Appendix of the documentation, added IBM book number and link
  for the HMC API book of z14.

**Enhancements:**

* Avoided `DeprecationWarning` on Python 3 for invalid escape sequences
  in some places.

* The zhmcclient mock support for various resource classes did not always
  check for invalid CPC status and for invalid Partition status as
  described in the HMC API book. It now does.

* In the mock support, invalid input to faked resource classes (mainly when
  adding faked resources) is now handled by raising a new exception
  ``zhmcclient_mock.InputError`` (instead of ``ValueError``). The URI
  handler of the mock support now converts that into an HTTP error 400
  (Bad Request), consistent with the HMC API book.

* Added ``datetime_from_timestamp()`` and ``datetime_from_timestamp()``
  functions that convert between Python ``datetime`` objects and HMC timestamp
  numbers.

* Added mock support for Metrics resources.

* Added a ``verify`` argument to ``Session.logoff()``, consistent with
  ``Session.logon()``. This was needed as part of fixing issue #422.

* Added a `__repr__()` function to the `Session` class, for debug purposes.

* In the `ParseError` exception class, a message of `None` is now tolerated,
  for consistency with the other zhmcclient exception classes.

* In the `NotFound` exception class, a `filter_args` parameter of `None` is now
  tolerated, for consistency with the `NoUniqueMatch` exception class.

* Documented for the zhmcclient exception classes how `args[0]` is set.

* Clarified in the documentation that the `manager` and `resources` parameters
  of the `NoUniqueMatch` and `NotFound` exception classes must not be `None`.

* Improved the unit test cases for the `Client` class and for the zhmcclient
  exception classes, and migrated them to py.test.

* Migrated the unit tests for HBAs from unittest to py.test, and
  improved the test cases.

* In the `Hba.reassign_port()` method, updated the `Hba` object with the
  changed port, consistent with other update situations.

* Clarified in the description of `HbaManager.list()` that only the
  'element-uri' property is returned and can be used for filtering.

* The mock support for the "Create NIC" operation now performs more
  checking on the URIs specified in the 'network-adapter-port' or
  'virtual-switch-uri' input properties, raising HTTP status 404 (Not Found)
  as specified in the HMC API book.

* In the ``FakedNic.add()`` method of the mock support, the checking for the
  URIs specified in the 'network-adapter-port' or 'virtual-switch-uri' input
  properties was relaxed to only the minimum, in order to make the setting
  up of faked resources easier.

* Migrated the unit tests for ``Nic`` and ``NicManager`` from unittest to
  py.test, and improved them.

* Improved the way the named tuples ``MetricGroupDefinition`` and
  ``MetricDefinition`` are documented.

* Added support for ``Console`` resource and its child resources ``User``,
  ``User Role``, ``User Pattern``, ``Password Rule``, ``Task``, and
  ``LDAP Server Definition``, both for the zhmcclient API and for the
  zhmcclient mock support.

* As part of support for the ``Console`` resource, added a new resource class
  ``UnmanagedCpc`` which representd unmanaged CPCs that have been discovered by
  the HMC. The existing ``Cpc`` class continues to represent only managed CPCs;
  this has been clarified in the documentation.

* As part of support for the ``Console`` resource, added a method
  ``wait_for_available()`` to the ``Client`` class, which waits until the HMC
  is available again after a restart. This method is used by
  ``Console.restart()``, but it can also be used by zhmcclient users.

* As part of support for the ``Console`` resource, improved ``Session.post()``
  to allow for an empty response body when the operation returns with HTTP
  status 202 (Accepted). This status code so far was always assumed to indicate
  that an asynchronous job had been started, but it can happen in some
  ``Console`` operations as well.

* Improved the error information in the ``ParseError`` exception, by adding
  the "Content-Type" header in cases where that is interesting.

* Add CLI commmands to mount and unmount an ISO to a Partition.


Version 0.16.0
^^^^^^^^^^^^^^

Released: 2017-08-29

**Bug fixes:**

* Fixed CLI: Remove defaults for options for 'partition update' (issue #405).

**Enhancements:**

* Added Code Climate support.


Version 0.15.0
^^^^^^^^^^^^^^

Released: 2017-08-15

**Incompatible changes:**

* In case the user code was specifically processing the reason code 900 used
  for HTML-formatted error responses with HTTP status 500: This reason code
  has been split up into multiple reason codes. See the corresponding item
  in section "Enhancements".

**Bug fixes:**

* Fixed a TypeError: "'odict_values' object does not support indexing" on
  Python 3.x (issue #372).

* Minor fixes in the documentation (e.g. fixed name of ``MetricGroupValues``
  class).

* Fixed the zhmc CLI for Python 3 where multiple commands raised
  AttributeError: "'dict' object has no attribute 'iteritems' in
  ``zhmccli/_helper.py``. (issue #396).

**Enhancements:**

* Added support for the HMC Metric Service. For details, see section 'Metrics' in the
  zhmcclient documentation. There is an example script ``metrics.py`` demonstrating
  the use of the metrics support. The metrics support caused an additional package
  requirement for the ``pytz`` package.

* Added support for a "metrics" command to the zhmc CLI.

* Added support for the IBM z14 system (in internal machine type tables and in the
  documentation).

* zhmccli: Support for 'authorization controls' of a Partition (issue #380)

* Added CLI support for processing weights (issue #383)

* The `HTTPError` raised at the API for HMC Web Services not enabled now has
  a simple error message and uses a specific reason code of 900. Previously,
  the returned HTML-formatted response body was used for the message and a
  generic reason code of 999. All other HTML-formatted error responses still
  use the generic reason code 999. That reason code 999 is now documented to
  be changed to more specific reason codes, over time. (issue #296).

* Reduced the package requirements to only the direct dependencies of
  this package.

* Changed the experimental ``Cpc.get_free_crypto_domains()`` method to test
  only control-usage access to the specified adapters. Improved that method
  by supporting `None` for the list of adapters which means to inspect all
  crypto adapters of the CPC.


Version 0.14.0
^^^^^^^^^^^^^^

Released: 2017-07-07

**Incompatible changes:**

* Changed the return value of ``TimeStatsKeeper.snapshot()`` from a list of
  key/value tuples to a dictionary. This is more flexible and reduces the
  number of data structure conversions in different scenarios. See issue #269.

* Changed the arguments of ``Partition.mount_iso_image()`` incompatibly,
  in order to fix issue #57.

**Bug fixes:**

* Fixed the documentation of several asynchronous ``Partition`` methods that
  incorrectly documented returning ``None`` in case of synchronous invocation,
  to now document returning an empty dictionary:

  - ``Partition.start()``
  - ``Partition.stop()``
  - ``Partition.dump_partition()``
  - ``Partition.psw_restart()``

  All other asynchronous methods did not have this issue. See issue #248.

* Clarified in the documentation of all exceptions that have a ``details``
  instance variable, that it is never ``None``.

* Fixed using '--ssc-dns-servers' option for the CLI commands
  'zhmc partition create/update'. See issue #310.

* Fixed the incorrect parameters of ``Partition.mount_iso_image()``. See
  issue #57.

* Reads the vlan-id as a integer instead as a string for
  the 'zhmc nic create/update' cli command. See issue #337.

* Fixed the AttributeError that occurred when using zhmcclient in Jupyter
  notebooks, or in the python interactive mode. See issue #341.

**Enhancements:**

* Improved content of ``zhmcclient.ParseError`` message for better problem
  analysis.

* Increased the default status timeout from 60 sec to 15 min, in order to
  accomodate for some large environments. The status timeout applies to
  waiting for reaching the desired LPAR status after the HMC operation
  'Activate LPAR' or 'Deactivate LPAR' has completed.

* Allow ``None`` as a value for the ``load_parameter`` argument of
  ``Lpar.load()``, and changed the default to be ``None`` (the latter change
  does not change the behavior).

* Added actual status, desired statuses and status timeout as attributes to
  the ``StatusTimeout`` exception, for programmatic processing by callers.

* In the zhmc CLI, added a ``--allow-status-exceptions`` option for the
  ``lpar activate/deactivate/load`` commands. Setting this option causes the
  LPAR status "exceptions" to be considered an additional valid end status when
  waiting for completion of the operation.

* Improved documentation of CLI output formats.

* Simplified the message of the ``OperationTimeout`` exception.

* Split the ``AuthError`` exception into ``ClientAuthError`` and
  ``ServerAuthError`` that are used depending on where the authentication issue
  is detected. Reason for the split was that the two subclasses have different
  instance variables. The ``AuthError`` exception class is now an abstract
  base class that is never raised but can be used to catch exceptions.

* Made error data available as instance variables of the following exceptions:
  ``ConnectTimeout``, ``ReadTimeout``, ``RetriesExceeded``,
  ``ClientAuthError``, ``ServerAuthError``, ``OperationTimeout``, and
  ``StatusTimeout``, ``NotFound``, ``NoUniqueMatch``.

* Improved unit test cases for ``zhmcclient._exceptions`` module.

* Added support to the zhmc CLI for an interactive session to the console
  of the operating system running in a
  partition (``zhmc partition console``) or LPAR (``zhmc lpar console``).

* Added ``str_def()`` method to all exception classes, which returns a
  definition-style string for parsing by scripts.

* In the zhmc CLI, added options ``-e``, ``--error-format`` for controlling
  the format of error messages. The ``-e def`` option selects the format
  returned by the new ``str_def()`` methods. This format provides for easier
  parsing of details of error messages by invoking scripts.

* Added ``wait_for_status()`` methods to the ``Lpar`` and ``Partition``
  classes, in order to ease the work for users that need to ensure that a
  particular LPAR or partition status is reached.

* Added support for crypto-related methods on the ``Partition`` and
  ``Adapter`` resource classes. Added zhmcclient mock support for
  the faked partition (not yet for the faked adapter).

* Added that ``Partition.start()`` waits for reaching the desired status
  'active' or 'degraded', because it transitions through status 'paused'
  when starting a partition.

* Improved the ``NoUniqueMatch`` exception so that the list of resources that
  did match the filter, are shown with their URIs in the error message, and
  are available as new ``resources`` and ``resource_uris`` attributes. This
  change adds a required argument ``resources`` to the constructor of
  ``NoUniqueMatch``. However, since this exception is only supposed to be
  raised by the zhmcclient implementation, this change is compatible to
  zhmcclient users.

* Moved the invocation of PyLint from the "make check" target into its
  own "make pylint" target, inorder to speed up the CI testing.

* Added the ability for ``Session.post()`` to support binary data as the
  payload. The ``body`` argument may now be a dictionary which is represented
  as a JSON string, a binary string which is used directly, or a unicode
  string which is encoded using UTF-8. This was necessary to fix issue #57.

* In the zhmcclient mock support, added a Python property ``name`` to all
  faked resources, which returns the value of the 'name' resource property.

* Added a Python property ``maximum_crypto_domains`` to the ``Adapter`` class,
  which returns the maximum number of crypto domains of a crypto adapter.

* Added a Python property ``maximum_active_partitions`` to the ``Cpc`` class,
  which returns the maximum number of active LPARs or partitions of a CPC.

* Added ``get_free_crypto_domains()`` method to the ``Cpc`` class,
  in order to find out free domain index numbers for a given set of
  crypto adapters. Note: This method is considered experimental in this
  version.

* Added an ``update_properties()`` method to the ``Lpar`` and ``Cpc``
  resource classes.

* Improved the description of the ``Hba.create()`` and ``Nic.create()``
  methods to describe how the backing adapter port is specified.

* Extended the zhmcclient mock support by adding support for all operations
  thet are supported at the zhmcclient API but were not yet supported for
  mocking, so far.


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


Version 0.12.0
^^^^^^^^^^^^^^

Released: 2017-04-13

**Incompatible changes:**

* The password retrieval function that can optionally be passed to
  ``Session()`` has changed its interface; it is now being called with host and
  userid. Related to issue #225.

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
