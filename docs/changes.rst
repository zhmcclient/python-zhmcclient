
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

.. _`Change log`:

Change log
----------

.. towncrier start
Version 1.21.1
^^^^^^^^^^^^^^

Released: 2025-07-10

**Bug fixes:**

* Fixed safety issues up to 2025-06-04.

* Increased minimum version of "urllib3" to 2.2.3 in order to pick up changes
  that help when using unstable networks. Specifically, enabling
  enforce_content_length by default and distinguishing too much from not enough
  response data. (`#1888.2 <https://github.com/zhmcclient/python-zhmcclient/issues/1888.2>`_)

* Dev: Fixed Sphinx build issue by excluding snowballstemmer 3.0.0.

* Changed the default for HTTP read retries from 0 to 3. This applies only to
  the HTTP "GET" method. This should help when using unstable networks. (`#1888 <https://github.com/zhmcclient/python-zhmcclient/issues/1888>`_)

**Enhancements:**

* Improved the error message in connection related exceptions by eliminating
  useless object representations. In zhmcclient.ConnectionError, added the
  qualified type of the original exception received by zhmcclient.


Version 1.21.0
^^^^^^^^^^^^^^

Released: 2025-04-28

**Deprecations:**

* Deprecated the feature_enabled() method of the Cpc and Partition classes,
  because it is too complex to use. Use the new firmware_feature_enabled()
  method instead. (`#1828 <https://github.com/zhmcclient/python-zhmcclient/issues/1828>`_)

**Bug fixes:**

* Fixed safety issues up to 2025-04-21.

* Dev: Fixed permissions for creating GitHub release when releasing a version

* Docs: Clarified that 'Cpc.get_wwpns()' is only supported for SE version 2.13.1,
  because the underlying HMC operation "Export WWPN List" was no longer supported
  since z14. (`#1713 <https://github.com/zhmcclient/python-zhmcclient/issues/1713>`_)

* Fixed a datetime conversion error by excluding pytz 2025.2 (`#1800 <https://github.com/zhmcclient/python-zhmcclient/issues/1800>`_)

* Fixed that 'Console.list_permitted_adapters()' was used in the metrics support
  by incorrectly checking for the API version 4.1. The code now checks for
  availability of the API feature 'adapter-network-information', instead. (`#1803 <https://github.com/zhmcclient/python-zhmcclient/issues/1803>`_)

* Ensure dpm-export doesn't fail on unknown dict keys during final "reduction"
  phase. (`#1821 <https://github.com/zhmcclient/python-zhmcclient/issues/1821>`_)

* The list_api_features() method of the Cpc and Console classes had cached the
  API feature data. This was a problem because the use of the 'name' filter
  can create different results. The method no longer caches the API feature
  data. (`#1827 <https://github.com/zhmcclient/python-zhmcclient/issues/1827>`_)

* Docs: Fixed incorrect statement about DPM in description of
  zhmcclient.LparManager class. (`#1844 <https://github.com/zhmcclient/python-zhmcclient/issues/1844>`_)

**Enhancements:**

* Added new public functions to and documented existing functions and attributes
  in the zhmcclient.testutils module in support of end2end tests for projects
  using zhmcclient: 'setup_hmc_session()', 'teardown_hmc_session()',
  'teardown_hmc_session_id()', 'is_valid_hmc_session_id()', 'LOG_FORMAT_STRING',
  'LOG_DATETIME_FORMAT', 'LOG_DATETIME_TIMEZONE'.

* Added zhmcclient mock support for all operations related to hardware
  messages for Console and CPC. (`#1672 <https://github.com/zhmcclient/python-zhmcclient/issues/1672>`_)

* Added a resource class 'zhmcclient.HwMessage' and corresponding manager
  class 'zhmcclient.HwMessageManager' to support hardware messages. The
  hardware messages are accessible for CPC and Console via a new property
  'hw_messages'. A HwMessage object supports list() and find..() methods,
  property retrieval, 'delete()', 'request_service()',
  'get_service_information()' and 'decline_service()'. Added end2end and unit
  tests. (`#1672 <https://github.com/zhmcclient/python-zhmcclient/issues/1672>`_)

* Added support for caching the API features returned by
  'Console.list_api_features()' and 'Cpc.list_api_features()'. (`#1803 <https://github.com/zhmcclient/python-zhmcclient/issues/1803>`_)

* The property '@@implementation-errors' can be returned by the HMC to indicate
  internal inconsistencies not severe enough to return an error. Such cases
  should be considered HMC defects.
  When that property is in an HMC result, a warning is now logged and the
  property is removed. (`#1820 <https://github.com/zhmcclient/python-zhmcclient/issues/1820>`_)

* Added list_firmware_features() to the Cpc and Partition classes. The firmware
  feature data is cached. The method lists the enabled firmware features
  regardless of the HMC/SE version and regardless of whether the firmware
  feature is available. If the HMC/SE version does not support firmware
  features yet (2.14 and HMC API version 2.23), an empty list is returned. (`#1828 <https://github.com/zhmcclient/python-zhmcclient/issues/1828>`_)

* Added api_feature_enabled() to the Cpc and Console classes, in order
  to test for whether a specific API feature is enabled (=available). The
  API feature data is cached, and the cache data structure is optimized for
  fast lookup of the feature name. (`#1828 <https://github.com/zhmcclient/python-zhmcclient/issues/1828>`_)

* Added firmware_feature_enabled() to the Cpc and Partition classes, in order
  to test for whether a specific firmware feature is enabled. The firmware
  feature data is cached, and the cache data structure is optimized for fast
  lookup of the feature name. (`#1828 <https://github.com/zhmcclient/python-zhmcclient/issues/1828>`_)

* Added zhmcclient_mock support for the "List CPC API Features" and
  "List Console API Features" operations. (`#1830 <https://github.com/zhmcclient/python-zhmcclient/issues/1830>`_)

* When a 'list()' method specific full_properties=True, the retrieval of the
  resource properties in the list result is implemented using the bulk operation
  "Submit Requests". That operation has a limit for the request size of 256 kB.
  So far, that limit could not possibly be reached. The support for hardware
  messages made it necessary to improve that implementation by splitting the
  bulk operation into multiple operations when the request size limit is
  exceeded. (`#1836 <https://github.com/zhmcclient/python-zhmcclient/issues/1836>`_)

**Cleanup:**

* Replaced any use of 'OrderedDict' with the standard Python 'dict', since they
  are ordered since Python 3.6. As a result, the representation of resource
  properties in 'repr()' methods of zhmcclient resources now uses the standard
  dict representation and its properties are no longer sorted. This allowed to
  eliminate the dependency to the 'yamlloader' package.


Version 1.20.0
^^^^^^^^^^^^^^

Released: 2025-03-24

**Bug fixes:**

* Fixed missing package dependencies for development.

* End2end test: Fixed issue by filtering out non-FCP storage groups in
  test_virtual_storage_resource.

* Fixed safety issues up to 2025-02-26.

* Added support for busy retries to 'Session.post()' and 'Session.delete()'
  when the HTTP request returns HTTP status 409 with reason codes 1 or 2.
  The waiting time between retries can also be specified. This can be used
  by resource class methods that need that.
  By default, no retries are performed.
  Changed 'PartitionLink.update_properties()' and 'PartitionLink.delete()' to
  specify busy retries.

* Fixed a datetime conversion error by excluding pytz 2025.1. (`#1755 <https://github.com/zhmcclient/python-zhmcclient/issues/1755>`_)

* When handling inventory errors during "Export DPM configuration", only access
  field "inventory-error-details" if "inventory-error-code" is 5. (`#1760 <https://github.com/zhmcclient/python-zhmcclient/issues/1760>`_)

* Remove unused network and storage port objects from export data, too. (`#1764 <https://github.com/zhmcclient/python-zhmcclient/issues/1764>`_)

* Ensure proper detection of all unreferenced adapters. (`#1764 <https://github.com/zhmcclient/python-zhmcclient/issues/1764>`_)

* Fixed incorrect CPC name in exception message when a NIC could not be found
  during metrics processing. (`#1775 <https://github.com/zhmcclient/python-zhmcclient/issues/1775>`_)

* Fixed that metrics processing for partition metrics failed on HMC versions older
  than 2.14.0. (`#1775 <https://github.com/zhmcclient/python-zhmcclient/issues/1775>`_)

**Enhancements:**

* Improved 'repr()' of 'zhmcclient.Session' objects by showing when password and
  session_id are 'None'.

* Added check for incorrectly named towncrier change fragment files.

* Added support for waiting for partition links to reach one of a specified set
  of states with a new 'zhmcclient.PartitionLink.wait_for_states()' method.
  This can be used to ensure that a partition link is in a stable state before
  proceeding with other operations on it.

* Added log entries for logging on and off at the HMC, after the HMC to be used
  has been determined.

* Improved error reporting for failed HMC logon by distinguishing the case where
  a password is not provided but a session ID that is invalid.

* End2end test: Added support for specifying in the HMC inventory file that all
  managed CPCs are to be tested, by omitting the 'cpcs' property for the HMC
  entry. Previously, omitting that property meant to test no CPC. (`#1134 <https://github.com/zhmcclient/python-zhmcclient/issues/1134>`_)

* End2end test: Specifying a CPC in an HMC entry of the HMC inventory file that
  is not managed by the HMC now causes pytest to error out. Previously, the CPC
  was skipped and a warning was issued. This is to better indicate that the
  expectation of the HMC inventory file was not met by the actual environment. (`#1134 <https://github.com/zhmcclient/python-zhmcclient/issues/1134>`_)

* End2end test: Specifying the 'dpm_enabled' property for a CPC in an HMC entry
  of the HMC inventory file with a value that does not match the actual CPC now
  causes pytest to error out. Previously, the CPC was skipped and a warning was
  issued. This is to better indicate that the expectation of the HMC inventory
  file was not met by the actual environment. (`#1134 <https://github.com/zhmcclient/python-zhmcclient/issues/1134>`_)

* Dev: Started using the trusted publisher concept of Pypi in order to avoid
  dealing with Pypi access tokens. (`#1738 <https://github.com/zhmcclient/python-zhmcclient/issues/1738>`_)

* Improved performance of looking up LPARs and adapters in metrics processing. (`#1775 <https://github.com/zhmcclient/python-zhmcclient/issues/1775>`_)

* Docs: Clarified in 'Console.list_permitted_adapters()' that the method does
  not return adapters of Z systems before SE version 2.16.0. (`#1775 <https://github.com/zhmcclient/python-zhmcclient/issues/1775>`_)

**Cleanup:**

* End2end test: In the test method 'test_partlink_zzz_cleanup()' which cleans
  up partition links and partitions from previous runs, added the recommendation
  to open zhmcclient issue in its message reporting partition links or partitions
  that had to be cleaned up. The partition link names have been changed to
  indicate which test method produced them. The test method
  'test_partlink_zzz_cleanup()' stays in place for the time being, as an
  additional safety net. (`#1749 <https://github.com/zhmcclient/python-zhmcclient/issues/1749>`_)

* End2end test: Consolidated different ways to enable logging in end2end test
  functions. Logging is now consistently enabled with the TESTLOGFILE env var.
  The log message format has been changed. (`#1750 <https://github.com/zhmcclient/python-zhmcclient/issues/1750>`_)


Version 1.19.0
^^^^^^^^^^^^^^

Released: 2025-01-23

**Bug fixes:**

* Fixed safety issues up to 2025-01-23.

* Dev: In the make commands to create/update AUTHORS.md, added a reftag to the
  'git shortlog' command to fix the issue that without a terminal (e.g. in GitHub
  Actions), the command did not display any authors.

* Dev: Fixed checks and missing removal of temp file in make targets for releasing
  and starting a version.

* Fixed that all password-like properties are no longer written in clear text to
  the Python loggers "zhmcclient.api" and "zhmcclient.hmc", but are now blanked
  out. Previously, that was done only for the "zhmcclient.hmc" logger for creation
  and update of HMC users.

* Fixed that incorrect password-like properties were added with blanked-out values
  to the API and HMC log.

* Circumvented an issue when installing pywinpty 2.0.14 with latest version of
  maturin on Python 3.8, by excluding pywinpty 2.0.14.

* Fixed incorrect HTTP method name in log messages for receiving HTTP status
  403 in Session.post() and Session.delete().

* Fixed incorrect check for start branch in 'make start_tag'. (`#1689 <https://github.com/zhmcclient/python-zhmcclient/issues/1689>`_)

* Test: Python 3.13 was pinned to 3.13.0 to work around a pylint issue on
  Python 3.13.1. (`#1728 <https://github.com/zhmcclient/python-zhmcclient/issues/1728>`_)

**Enhancements:**

* Dev: Enhanced the zhmcclient API logging code so that in the debugger,
  zhmcclient API functions now have less logging steps to go through until the
  actual API function is reached.

* Added a boolean parameter 'always' to the 'zhmcclient.Session.logon()' method,
  which causes the session to always be logged on, regardless of an existing
  session ID.

* Increased the timeout for HMC operations that is used in end2end tests, from
  300 sec to 1800 sec. Note that this does not change the default timeout for
  users of the zhmcclient library, which continues to be 3600 sec.

* Added zhmcclient mock support for MFA Server Definitions with a new
  'zhmcclient_mock.FakedMfaServerDefinition' class (and a corresponding manager
  class). (`#1668 <https://github.com/zhmcclient/python-zhmcclient/issues/1668>`_)

* Added support for MFA Server Definitions with a new 'zhmcclient.MfaServerDefinition'
  resource class (and corresponding manager class). (`#1668 <https://github.com/zhmcclient/python-zhmcclient/issues/1668>`_)

* Because the "Create Partition Link" HMC operation does not return the
  'object-uri' property of the created partition link, the handling of HTTP POST
  operations has been enhanced to add the URI returned in the "Location" header
  field as an artificial property 'location-uri' to the result data, if the
  "Location" header field is set and the result data does not contain 'object-uri'
  or 'element-uri'. (`#1678 <https://github.com/zhmcclient/python-zhmcclient/issues/1678>`_)

* Added support for Partition Links with a new 'zhmcclient.PartitionLink'
  resource class (and corresponding manager class). Added the following
  methods for partition links to the 'zhmcclient.Partition' class:
  'attach_network_link()', 'detach_network_link()',
  'attach_ctc_link()', 'detach_ctc_link()', 'list_attached_partition_links()'. (`#1678 <https://github.com/zhmcclient/python-zhmcclient/issues/1678>`_)

**Cleanup:**

* Consolidated duplicate authors in AUTHORS.md file.

* Accommodated rollout of Ubuntu 24.04 on GitHub Actions by using ubuntu-22.04
  as the OS image for Python 3.8 based test runs.


Version 1.18.0
^^^^^^^^^^^^^^

Released: 2024-10-08

**Incompatible changes:**

* Dev: Changed the installation of the zhmcclient package that is done in
  'make install' from being editable to being non-editable, since pip will stop
  supporting editable installs.

**Bug fixes:**

* Addressed safety issues up to 2024-08-18.

* Fixed installation errors on Python 3.13 by increasing the minimum versions of
  install dependencies PyYAML to 6.0.2, pyrsistent to 0.20.0 and wheel to 0.41.3.
  This was done for all Python versions, to simplify dependencies.
  Increased the minimum versions of some development dependencies for the same
  reason.

* Fixed new issue 'too-many-positional-arguments' reported by Pylint 3.3.0.

* Fixed dependabot issue #25. This caused the minimum version of the
  'jsonschema' package to be increased to 4.18.0.

* Docs: Fixed the description of the 'Cpc.list_associated_storage_groups()'
  method; it previously had stated that when the "dpm-storage-management" firmware
  feature is not enabled, the method would be returning an empty list. That was
  corrected in the documentation to match the actual behavior, which is to
  fail. (`#1543 <https://github.com/zhmcclient/python-zhmcclient/issues/1543>`_)

* Docs: Fixed an RTD build issue that lead to not showing any API documentation. (`#1611 <https://github.com/zhmcclient/python-zhmcclient/issues/1611>`_)

* Circumvented an issue with pytz by excluding pytz version 2024.2. (`#1660 <https://github.com/zhmcclient/python-zhmcclient/issues/1660>`_)

* Test: Fixed the issue that coveralls was not found in the test workflow on MacOS
  with Python 3.9-3.11, by running it without login shell. Added Python 3.11 on
  MacOS to the normal tests. (`#1665 <https://github.com/zhmcclient/python-zhmcclient/issues/1665>`_)

**Enhancements:**

* Test: Added unit tests for exceptions that did not have one.

* Fixed a missing closing parenthesis in MetricsResourceNotFound.__repr__().

* Test: Improved end2end test for 'Console.list_permitted_adapters()'.

* Added support for encapsulating the interactions with an OS console through
  the WebSocket protocol, by adding a new 'zhmcclient.OSConsole' class. This
  builds on top of the new support for OS console access through the
  WebSocket protocol. (`#618 <https://github.com/zhmcclient/python-zhmcclient/issues/618>`_)

* Added support for using the integrated ASCII console of operating systems
  running in partitions in DPM mode via the WebSocket protocol, by adding a new
  method 'zhmcclient.Partition.create_os_websocket()'.
  Added a new documentation section "Using WebSocket to access OS console" that
  documents how to interact with the integrated ASCII console from Python code. (`#618 <https://github.com/zhmcclient/python-zhmcclient/issues/618>`_)

* Test: Added tests for Python 3.13 (rc.1). (`#1505 <https://github.com/zhmcclient/python-zhmcclient/issues/1505>`_)

* Test: Added tests for Python 3.13 (final version). (`#1506 <https://github.com/zhmcclient/python-zhmcclient/issues/1506>`_)

* Docs: Documented HMC/SE version requirements and improved the description of
  firmware and API features. (`#1543 <https://github.com/zhmcclient/python-zhmcclient/issues/1543>`_)

**Cleanup:**

* Docs: Simplified version retrieval in docs build by using setuptools_scm.

* Test: Increased minimum version of pylint to 3.0.1 to address an issue
  when importing setuptools_scm in conf.py.

* Dev: Relaxed the conditions when safety issues are tolerated:
  Issues in development dependencies are now tolerated in normal and scheduled
  test workflow runs (but not in local make runs and release test workflow runs).
  Issues in installation dependencies are now tolerated in normal test workflow
  runs (but not in local make runs and scheduled/release test workflow runs).

* Dev: Added to the release instructions to roll back fixes for safety issues
  into any maintained stable branches.

* Dev: Added to the release instructions to check and fix dependabot issues,
  and to roll back any fixes into any maintained stable branches.

* Docs: Clarified descriptions of the 'feature_enabled()' and
  'feature_info()' methods of classes 'Partition' and 'Cpc'.


Version 1.17.0
^^^^^^^^^^^^^^

Released: 2024-07-11

**Bug fixes:**

* Install: Increased the minimum version of the 'jsonschema' package to 3.1.0
  to get a fix for a 'pkg_resources.DistributionNotFound' exception that occurs
  in certain cases.

* Test: Fixed str/int issue in end2end tests in skip_missing_api_feature().

* Mock: Fixed the "Modify Storage Group Properties" HMC operation in the
  zhmcclient mock support.

* Mock: Consolidated the different assumptions in the zhmcclient mock support and
  the end2end testcases regarding whether the implemented behavior depends on the
  mocked HMC or CPC generation (e.g. support or not support the 'properties'
  query parameter on some List operations). Now, the zhmcclient mock support
  always implements only the behavior of the latest HMC / CPC generation.

* Addressed safety issues up to 2024-06-21

* Install: Changed the name of the dependent package 'stomp.py' to use its
  canonical name 'stomp-py' since that prevented installation of packages using
  zhmcclient under certain circumstances (e.g. with minimum package levels). (`#1516 <https://github.com/zhmcclient/python-zhmcclient/issues/1516>`_)

* Docs: Fixed incorrect formatting of bullet lists. (`#1544 <https://github.com/zhmcclient/python-zhmcclient/issues/1544>`_)

* Mock+Test: Added missing defaults for properties 'shared', 'description' and
  'fulfillment-state' to the mocked 'Create Storage Group' operation.
  Added missing properties and fixed property name typos in the end2end
  mock test files mocked_hmc_z14.yaml and mocked_hmc_z16.yaml. (`#1548 <https://github.com/zhmcclient/python-zhmcclient/issues/1548>`_)

* Docs: Added bibliography entries for HMC API books 2.11 - 2.12 back in,
  without links (they are not downloadable anymore). (`#1560 <https://github.com/zhmcclient/python-zhmcclient/issues/1560>`_)

* Mock: Fixed the handling of the 'additional-properties' query parameter
  when not provided, by no longer producing a property with empty name. (`#1580 <https://github.com/zhmcclient/python-zhmcclient/issues/1580>`_)

* Mock: Updated the set of properties returned by
  'LdapServerDefinitionManager.list()' and 'CpcManager.list()' when used in a
  mocked environment, to the behavior of HMC version 2.16.0. (`#1580 <https://github.com/zhmcclient/python-zhmcclient/issues/1580>`_)

* Fixed mock support for create user pattern. (`#1581 <https://github.com/zhmcclient/python-zhmcclient/issues/1581>`_)

* Mock: Fixed that resource properties returned from zhmcclient mock support
  were not independent of the internal resource object's state. For properties
  that are lists or dicts, that has lead to the issue that changes to the
  internal state of the (mocked) resource object were immediately visible
  to a user that had previouly obtained the resource properties. (`#1583 <https://github.com/zhmcclient/python-zhmcclient/issues/1583>`_)

**Enhancements:**

* Test: Added more exhaustive z14 and z16 mock files to the tests/end2end
  directory and used them for the 'make end2end_mocked' tests.

* Test: Improved the checking in the test_storage_volume.py end2end test module.

* Test: Enabled the checking for success again in "make end2end_mocked".

* Mock: Added zhmcclient mock support for "Get Partitions Assigned to Adapter"
  operation. (`#1247 <https://github.com/zhmcclient/python-zhmcclient/issues/1247>`_)

* Mock: Added zhmcclient mock support for the "Get Inventory" operation, and
  enabled and improved its unit test. (`#1248 <https://github.com/zhmcclient/python-zhmcclient/issues/1248>`_)

* Added zhmcclient mock support for 'Console.list_permitted_adapters()'.
  This is used by the end2end_mocked testcases of the ibm.ibm_zhmc Ansible
  collection. (`#1309 <https://github.com/zhmcclient/python-zhmcclient/issues/1309>`_)

* Dev: Migrated from setup.py to pyproject.toml with setuptools as build backend.
  This provides for automatic determination of the package version without
  having to edit a version file. (`#1485 <https://github.com/zhmcclient/python-zhmcclient/issues/1485>`_)

* In addition to the `zhmcclient.__version__` property which provides the package
  version as a string, a new `zhmcclient.__version_tuple__` property provides
  it as a tuple of integer values. (`#1485 <https://github.com/zhmcclient/python-zhmcclient/issues/1485>`_)

* Added support for running the 'ruff' checker via "make ruff" and added that
  to the test workflow. (`#1526 <https://github.com/zhmcclient/python-zhmcclient/issues/1526>`_)

* Added support for running the 'bandit' checker with a new make target
  'bandit', and added that to the GitHub Actions test workflow. Adjusted
  the code in order to pass the bandit check:

    - Changed the use of 'yamlloader.ordereddict.Loader' to 'SafeLoader'.
    - Added bandit ignore markers where appropriate. (`#1527 <https://github.com/zhmcclient/python-zhmcclient/issues/1527>`_)

* Dev: Encapsulated the starting of a new version into a new 'make start' target.
  This performs the steps up to creating a PR. (`#1532 <https://github.com/zhmcclient/python-zhmcclient/issues/1532>`_)

* Dev: Encapsulated the releasing of a version into a new 'make release' target.
  This performs the steps up to creating a PR.
  The release to PyPI happens when the PR is merged. (`#1533 <https://github.com/zhmcclient/python-zhmcclient/issues/1533>`_)

* Mock: Added zhmcclient mock support for Storage Group Templates and their
  Volumes. (`#1541 <https://github.com/zhmcclient/python-zhmcclient/issues/1541>`_)

* Mock: Added zhmcclient mock support for Virtual Storage Resources in Storage
  Groups. (`#1565 <https://github.com/zhmcclient/python-zhmcclient/issues/1565>`_)

**Cleanup:**

* Fixed new issues reported by new flake8 7.0.0.

* Dev: Changed the outdated 'py.test' command name to 'pytest'.

* Dropped support for Python below 3.8. Cleaned up the dependencies, Makefile,
  source code, and test code.

  Increased minimum version of the following Python packages the installation
  depends upon:
  - pytz to 2019.1 (only on Python 3.8/3.9 - was already there on Python >= 3.10)
  - pytest (extra: test) to 6.2.5 (only on Python 3.8/3.9 - was already there
    on Python >= 3.10) (`#1489 <https://github.com/zhmcclient/python-zhmcclient/issues/1489>`_)

* Dev: Dropped the 'make upload' target, because the release to PyPI has
  been migrated to using a publish workflow. (`#1532 <https://github.com/zhmcclient/python-zhmcclient/issues/1532>`_)

* Converted most remaining uses of format() to f-strings. (`#1542 <https://github.com/zhmcclient/python-zhmcclient/issues/1542>`_)

* Docs: Reduced number of versions shown in generated documentation to only
  the latest fix version of each minor version, and the master version.
  Updated the release instructions and links in the documentation accordingly. (`#1567 <https://github.com/zhmcclient/python-zhmcclient/issues/1567>`_)

* Mock: Changed all 'list()' methods when used in a mocked environment, to return
  the properties with a value of 'None' instead of omitting it, when the mock
  environment did not add the property. (`#1580 <https://github.com/zhmcclient/python-zhmcclient/issues/1580>`_)


Version 1.16.0
^^^^^^^^^^^^^^

Released: 2024-06-12

**Incompatible changes:**

* Incompatible changes in the notification support:

  - The 'NotificationReceiver.notifications()' method now continues running when
    there are no notifications, and only ever returns when
    'NotificationReceiver.close()' is called (in some other thread).
    Before this change, the method returned when there were no notifications, so
    it had to be invoked by the user in a loop. Such user code should be adjusted
    to remove the loop and deal with the return indicating a close of the
    receiver.

  - In addition, the 'NotificationReceiver.notifications()' method can now raise
    the new exceptions 'zhmcclient.NotificationConnectionError' and
    'zhmcclient.NotificationSubscriptionError'.

  - The 'NotificationReceiver.subscribe/unsubscribe()' methods can now raise the
    new exception 'zhmcclient.NotificationSubscriptionError'.

  - Note that the 'NotificationReceiver.close()' method can raise
    'stomp.exception.StompException'. This could already be raised before this
    change, but had not been documented before.

  Issue: (`#1502 <https://github.com/zhmcclient/python-zhmcclient/issues/1502>`_)

**Enhancements:**

* Test: Relaxed the verification of log messages in test_auto_updater.py
  to tolerate additional log messages.

* Added a class 'StompRetryTimeoutConfig' for defining retry, timeout and
  keepalive/heartbeat parameters for the STOMP connection for HMC
  notifications. Added new 'stomp_rt_config' init parameters to the
  'NotificationReceiver' and 'AutoUpdater' classes, to specify these config
  parameters. Added default values for the configuration in zhmcclient constants. (`#1498 <https://github.com/zhmcclient/python-zhmcclient/issues/1498>`_)

* Improved the notification support in several ways:

  - Replaced the event-based handover of a single item from the notification
    listener thread to the caller's thread with a Python Queue, for better
    reliability. It turned out that messages could have been lost in some cases
    with the previous design.

  - The 'NotificationReceiver.notifications()' method now continues running
    when there are no notifications, and only ever returns when
    'NotificationReceiver.close()' is called (by some other thread).

  - Added methods 'connect()' and 'is_connected()' to the 'NotificationReceiver'
    class. The init method of 'NotificationReceiver' no longer connects,
    but the 'notifications()' method now calls 'connect()', so overall this is
    compatible with the prior behavior.

  - Added new exceptions 'NotificationConnectionError' and
    'NotificationSubscriptionError' that may be raised by some
    'NotificationReceiver' methods.

  - Documented the stomp-py exceptions that can be raised from
    'NotificationReceiver' methods.

  - Added proper detection of STOMP connection loss if STOMP heartbeating is
    enabled. The connection loss is surfaced by raising
    'NotificationConnectionError' in 'NotificationReceiver.notifications()'.
    This allows users to retry 'NotificationReceiver.notifications()' upon
    connection loss.

  - Added a new public constant 'STOMP_MIN_CONNECTION_CHECK_TIME' that defines
    the minimum time between checks for STOMP connection loss. The actual check
    time is determined by the heartbeat receive time and is bound by this minimum
    time.

  - Added the missing event methods to the internal '_NotificationListener' class
    in case they are ever invoked (needed due to lazy importing of stomp-py).

  - Added more log messages around STOMP connect / disconnect.

  Issue: (`#1502 <https://github.com/zhmcclient/python-zhmcclient/issues/1502>`_)

* Added support for getting new z16 environmental metrics about CPC and LPAR
  or partitions by adding 'get_sustainability_data()' methods to Cpc, Lpar,
  and Partition. (`#1511 <https://github.com/zhmcclient/python-zhmcclient/issues/1511>`_)

**Cleanup:**

* Removed the pinning of stomp.py to <7.0.0 and increased its minimum version
  to 8.1.1 (for Python>=3.7) to pick up fixes, and adjusted to the changed
  interface of the stomp event listener methods and the 'stomp.Connection()' call. (`#1499 <https://github.com/zhmcclient/python-zhmcclient/issues/1499>`_)

* Test: Upgraded Github Actions plugin actions/setup-python to v5 to no longer
  use the deprecated node version 16. (`#1503 <https://github.com/zhmcclient/python-zhmcclient/issues/1503>`_)


Version 1.15.0
^^^^^^^^^^^^^^

Released: 2024-06-07

**Incompatible changes:**

* The 'zhmcclient.User' object will no longer be able to store the 'password'
  property. The 'password' property is filtered out when creating the User object
  in 'UserManager.create()' and when updating the User object in
  'User.update_properties()'. (`#1490 <https://github.com/zhmcclient/python-zhmcclient/issues/1490>`_)

**Bug fixes:**

* Fixed safety issues up to 2024-06-07

* Addressed dependabot issues up to 2024-06-07

* Dev: In the Github Actions test workflow for Python 3.5, 3.6 and 3.7, changed
  macos-latest back to macos-12 because macos-latest got upgraded from macOS 12
  to macOS 14 which no longer supports these Python versions.

* Dev: Workaround for cert issue with pip in Python 3.5 in Github Actions.

* Dev: Addressed new issues raised by Pylint 3.1.

* Dev: Fixed new issue 'possibly-used-before-assignment' in Pylint 3.2.0.

* Docs: Fixed broken links to HMC books since IBM changed the links. As part
  of that, removed Bibliography entries for the HMC API book versions 2.11/2.12,
  and for all versions of the HMC Operations Guide (which changed to become the
  HMC Help System PDFs). (`#1459 <https://github.com/zhmcclient/python-zhmcclient/issues/1459>`_)

* Docs: Fixed formatting of badges on README page by converting it to
  Markdown. (`#1473 <https://github.com/zhmcclient/python-zhmcclient/issues/1473>`_)

* Test: Upgraded Github actions plugin actions/github-script to v7 to no longer
  use the deprecated Node.js 16. (`#1483 <https://github.com/zhmcclient/python-zhmcclient/issues/1483>`_)

**Enhancements:**

* Test: Added the option 'ignore-unpinned-requirements: False' to both
  safety policy files because for safety 3.0, the default is to ignore
  unpinned requirements (in requirements.txt).

  Increased safety minimum version to 3.0 because the new option is not
  tolerated by safety 2.x. Safety now runs only on Python >=3.7 because
  that is what safety 3.0 requires.

* Changed safety run for install dependencies to use the exact minimum versions
  of the dependent packages, by moving them into a separate
  minimum-constraints-install.txt file that is included by the existing
  minimum-constraints.txt file.

* The safety run for all dependencies now must succeed when the test workflow
  is run for a release (i.e. branch name 'release\_...').

* Added support for "Console Delete Retrieved Internal Code" HMC operation
  via a new 'zhmcclient.Console.delete_uninstalled_firmware()' method. (`#1431 <https://github.com/zhmcclient/python-zhmcclient/issues/1431>`_)

* Added new method Nic.backing_port() to return the backing adapter port
  of the NIC. (`#1451 <https://github.com/zhmcclient/python-zhmcclient/issues/1451>`_)

* Dev: Migrated from a manually maintained change log file to using change
  fragment files with the 'towncrier' package. This simplifies the procedures
  for starting and releasing a version, and avoids merge conflicts when there
  are multiple Pull Requests at the same time. For details, read the new
  'Making a change' section in the documentation. (`#1485 <https://github.com/zhmcclient/python-zhmcclient/issues/1485>`_)


Version 1.14.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 1.13.4.

Released: 2024-02-17

**Incompatible changes:**

* The incompatibility caused by the recent change to support regular expression
  matching for the resource name in the 'find()' method, which was released in
  zhmcclient versions 1.12.3 and 1.13.0, turned out to be too heavy. The change
  is now undone to go back to string comparison for the name matching in
  'find()'. The 'findall()' method which was also changed in these releases
  keeps the regular expression matching for consistency with 'list()'.
  (issue #1395)

**Bug fixes:**

* Docs: Increased minimum Sphinx versions to 7.1.0 on Python 3.8 and to 7.2.0 on
  Python >=3.9 and adjusted dependent package versions in order to fix a version
  incompatibility between sphinxcontrib-applehelp and Sphinx.
  Disabled Sphinx runs on Python <=3.7 in order to no longer having to deal
  with older Sphinx versions. (issue #1396)

* Changed the recently released support for regular expression matching for the
  resource name in 'find()' back to matching by string comparison. The
  'findall()' method keeps the regular expression matching for consistency
  with 'list()'. (issue #1395)

* Fixed that the resource name in the filter arguments of 'findall()' and
  'list()' was not matched case insensitvely with regular expressions for the
  resource types that have case insensitive names (user, user pattern, password
  rule, LDAP server definition). (related to issue #1395)

* Fixed that 'Console.list_permitted_lpars()' ignored the
  'additional_properties' parameter. (issue #1410)

* Test: Fixed that unit tests did not properly check missing properties in
  the returned resources. (related to issue #1410)

* Fixed that 'list()' methods returned only a minimal set of properties
  for each resource when the resource was found in the name-to-URI cache,
  and in that case missed some properties that are documented for the
  corresponding HMC list operation. This was fixed by removing the optimization
  of using the name-to-URI cache in 'list()' methods. (related to issue #1410)

* In the zhmcclient mock support, fixed the processing of the
  'additional-properties' query parameters for the mock support of the following
  zhmcclient list methods: 'Console.list_permitted_lpars()',
  'Cpc.adapters.list()', 'Cpc.partitions.list()', 'Cpc.virtual_switches.list()',
  'Cpc.image_activation_profiles.list()'. (related to issue #1410)

* Development: Fixed dependency issue with safety 3.0.0 by pinning it.

* Performance: In zhmcclient version 1.13.0, an optimization was added where
  list() and find_local() were now utilizing the name-to-URI cache when only the
  resource name was specified as a filter argument. This caused the 'se-version'
  property to no longer be in the local zhmcclient.Cpc objects that were used
  as the parent objects of the Lpar/Partition objects returned by
  Console.list_permitted_lpars/partitions() and caused a performance
  degradation in the zhmc_lpar_list and zhmc_partition_list Ansible modules due
  to repeated "Get CPC Properties" operations for retrieving the 'se-version'
  property. This was fixed in the Console.list_permitted_lpars/partitions()
  methods.

* Fixed the call to pipdeptree in the test workflow to use 'python -m'
  because otherwise it does not show the correct packages of the virtual env.

* Fixed the 'Cpc.delete_retrieved_internal_code()' method which passed its
  'ec_level' parameter incorrectly to the HMC operation. Added unit tests.
  (issue #1432)

**Enhancements:**

* Test: Added Python 3.8 with latest package levels to normal tests because
  that is now the minimum version to run Sphinx. (related to issue #1396)

* Added support for a new make target 'authors' that generates an AUTHORS.md
  file from the git commit history. Added the invocation of 'make authors' to
  the description of how to release a version in the development
  documentation. (issue #1393)

* In Console.list_permitted_lpars/partitions(), added CPC-related properties
  to the returned resource objects, that are returned by the HMC: 'cpc-name',
  'cpc-object-uri', 'se-version'. (issue #1421)

* In Console.list_permitted_lpars(), the additional_properties parameter
  is now supported also for HMC versions older than 2.16 GA 1.5. In that
  case, the zhmcclient handles adding the properties. (related to issue #1421)

* The pull_full_properties() and pull_properties() methods of zhmcclient
  resource objects no longer replace existing properties but now update them,
  so that additionally present properties (e.g. the CPC-related properties
  returned from Console.list_permitted_lpars/partitions()) are preserved.
  (related to issue #1421)

**Cleanup:**

* Increased versions of GitHub Actions plugins to increase node.js runtime
  to version 20.


Version 1.13.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 1.12.2.

Released: 2024-01-11

**Incompatible changes:**

* The 'Cpc.single_step_install()' and 'Console.single_step_install()' methods
  added in version 1.12.0 got additional optional parameters for FTP server
  retrieval added before the existing 'wait_for_completion' parameter. If you
  were using these methods and specified 'wait_for_completion' or
  'operation_timeout' as positional arguments, these methods will now raise
  an AssertionError and you need to change your code to specify them as keyword
  arguments, instead.

* When creating a 'zhmcclient.Session' object with a 'session_id' parameter that
  is not None, the 'host' parameter with the HMC host for that session now also
  needs to be provided. (related to issue #1024)

* The 'base_url' property of the 'zhmcclient.Session' object is now 'None' when
  the session is in the logged-off state. (related to issue #1024)

* The 'list()' methods of zhmcclient manager objects when invoked with
  full_properties=False and with the resource name as the only filter argument
  now return only a minimal set of properties for the returned resource:
  'class', 'parent', 'name', 'object/element-id', 'object/element-uri'.
  Previously, the full set of properties was returned in such a case.
  Code that accesses one of the no longer returned properties via
  'resource.properties' will now fail with KeyError. This can be fixed by
  changing such code to access the property via 'resource.get_property()',
  or by specifying 'full_properties=True' on the 'list()' method.
  (part of issue #1070)

* The 'delete()' methods of zhmcclient resource objects now also set the
  ceased-existence flag on the resource object. This causes 'get_property()'
  and prop()' when called for locally available properties to now raise
  CeasedExistence. Previously, the locally available property value was
  returned. (part of issue #1070)

**Bug fixes:**

* Addressed safety issues up to 2023-11-26.

* Test: Fixed end2end test function test_hmcdef_cpcs() to no longer stumble over
  'loadable_lpars' and 'load_profiles' properties in HMC inventory file.
  (issue #1374)

* Test: Fixed end2end testcase 'test_actprof_crud()' to skip the test when the
  required 'create-delete-activation-profiles' API feature is not available.
  (issue #1375)

* Docs: Clarified that the 'session' and 'session_credential' properties of the
  'zhmcclient.Session' object are 'None' when the session is in the logged-off
  state. (related to issue #1024)

* Clarified the HMC version requirements for 'Console.list_permitted_adapters()'.

* Docs: Clarified in 'StorageGroup.list_candidate_adapter_ports()' that the
  method is only for FCP-type storage groups.

* Fixed that the 'find()' and 'findall()' methods now also support regular
  expression matching when the resource name is passed as a filter argument.
  (issue #1070)

**Enhancements:**

* Added support for retrievel of firmware from an FTP server to the
  Cpc/Console.single_step_install() methods. (issue #1342)

* Additional log entries when HTTP status 403 is received, for easier detection.

* Added support for additional SE firmware upgrade related HMC operations:
  (issue #1357)

  - "CPC Install and Activate" as 'Cpc.install_and_activate()'
  - "CPC Delete Retrieved Internal Code" as 'Cpc.delete_retrieved_internal_code()'

* Added support for tolerating HMC restarts while waiting for a job to complete.
  Session.wait_for_completion() now retries in case of ConnectionError instead of
  raising the error. (issue #1365)

* Added the session-credential value returned by HMC logon as a new property
  'session_credential' to the 'zhmcclient.Session' object. (related to issue
  #1350)

* Clarified in the description of 'zhmcclient.NotificationReceiver' that
  its userid and password init parameters are actually the message broker's
  userid and password, and that in case of MFA being configured, they must be
  the session ID and session credential returned from the HMC logon.
  (issue #1350)

* Added support for targeting multiple redundant HMCs, from which the first
  one reachable at session creation time will be used for the duration of the
  session. The multiple HMCs are provided via the same 'Session' init parameter
  'host' as before, which now can be a list of hosts in addition to being a
  single host. Because redundant HMCs can be configured differently regarding
  what data they sync between them, there is no automatic failover to another
  HMC if the initially determined HMC becomes unavailable during the session.
  (issue #1024)

* Added support for specifying multiple redundant HMCs in the 'ansible_host'
  property of HMC definition files. The property can now specify a single HMC
  like before, or a a list of redundant HMCs. (issue #1024)

* Mock support: Added mock support for the Logon and Logoff HMC operations.
  (related to issue #1024)

* Improved the 'list()' methods of zhmcclient manager classes by using the
  name-to-URI cache when the resource name is passed as a filter argument.
  This improvement avoids retrieving the resource from the HMC when it can be
  found in the name-to-URI case, and therefore the resource will have only a
  minimal set of properties in that case. See the corresponding entry in the
  Incompatibilities section. (part of issue #1070)

* Improved the 'delete()' methods of zhmcclient resource classes by setting
  the ceased-existence flag on the resource. This will cause optimized
  find-like methods that operate on local data to properly raise
  CeasedExistence when used on the deleted resource object.
  (part of issue #1070)


Version 1.12.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 1.11.4.

Released: 2023-11-16

**Incompatible changes:**

* The pull_full_properties(), pull_properties(), get_property() and props()
  methods on resource objects
  now raise zhmcclient.CeasedExistence in all cases where the resource no
  longer exists on the HMC. This provides a consistent behavior across different
  cases the method can encounter. Previously, that exception was raised only for
  resources that had auto-update enabled, and resources with auto-update
  disabled raised zhmcclient.HTTPError(404,1) instead when the resource no
  longer existed on the HMC.
  If you use these methods and check for resource existence using
  HTTPError(404,1), you need to change this to check for CeasedExistence
  instead.

* The pull_properties() methods on resource objects now retrieves all properties
  from the HMC when one or more of the specified properties are not supported
  by the resource. This provides a consistent behavior across the different
  cases the method can encounter. Previously, that method behaved differently
  when the property was not supported by the resource: It has retrieved all
  properties when the resource type or HMC version does not support property
  filtering, but has raised HTTPError(400,14) in case the resource type and
  HMC version did support property filtering.
  If you use this method and check for HTTPError(400,14), this check can now be
  removed.

**Deprecations:**

* Use of the 'status_timeout' and 'allow_status_exceptions' parameters of the
  following methods has been deprecated because the underlying HMC operations
  do not actually have deferred status behavior. The waiting for an expected
  status has been removed from these methods:
  - Lpar.stop()
  - Lpar.psw_restart()
  - Lpar.reset_normal()
  - Lpar.reset_clear()

**Bug fixes:**

* Test: Circumvented a pip-check-reqs issue by excluding its version 2.5.0.

* Addressed safety issues up to 2023-11-05.

* Fixed the maximum number of concurrent threads in bulk operations to be
  the documented maximum of 10.

* Test: Added unit tests and end2end tests for list permitted partitions operation

* Docs: Corrected and improved the description of the Lpar.activate() method.

* Test: Added end2end tests for LPAR activation in classic mode.

* Fixed the waiting for LPAR status in Lpar.activate(). Previously, the method
  was waiting for 'operating' or 'not-operating', so when an auto-load
  happened it already returned when status 'not-operating' was reached, but
  the load was still going on in parallel. Now, the method finds out whether
  the LPAR is expected to auto-load or not and waits for the corresponding
  status.

* Added a debug log entry when Lpar.wait_for_status() is called. This happens
  for example when Lpar.activate/deactivate/load() are called with
  wait_for_completion.

* Fixed that the Lpar.reset_normal() and Lpar.reset_clear() methods were
  waiting for a status "operational", which never happens with these operations.
  This was fixed by removing the waiting for an expected status, because the
  underlying HMC operations do not actually have deferred status behavior.
  (issue #1304)

* Fixed the incorrect empty request body in Lpar.psw_restart().

* Shortened the status timeout from 900 sec to 60 sec. This timeout is used
  when waiting for an expected Partition or LPAR status after operations
  that change the status and that have deferred status behavior (ie. the
  status changes only after the asynchronous HMC job is complete).
  This change allows to more reasonably surface the situation where an LPAR
  load succeeds but the status of the LPAR does not go to 'operating' due to
  issues with the operating system.

* Docs: Fixed the description of the 'status_timeout' parameter of the Partition
  and Lpar methods that have deferred status behavior.

* The 'wait_for_completion' and 'operation_timeout' parameters of
  Cpc.export_profiles() and Cpc.import_profiles() have never worked, because
  the underlying HMC operations are not actually asynchronous. This has been
  fixed by removing these parameters from these functions. This does not count
  as an incompatible change because using these parameters with non-default
  values has failed.  (part of issue #1299)

**Enhancements:**

* Added support for Python 3.12. Had to increase the minimum versions of
  setuptools to 66.1.0 and pip to 23.1.2 in order to address removal of the
  long deprecated pkgutils.ImpImporter in Python 3.12, as well as several
  packages used only for development. (issue #1300)

* Mock support: Improved mocked Hipersocket adapters; they now have all their
  properties and default values for all except adapter-id and channel-path-id.

* Added support for the "List OS Messages" operation on partitions (in DPM mode)
  and LPARs (in classic mode). (issue #1278)

* Examples: Added example script increase_crypto_config.py for increasing the
  crypto configuration of a partition on a CPC in DPM mode.

* The pull_properties() method on resource objects was extended so that its
  'properties' parameter can now also be a single string (in addition to the
  already supported list or tuple of strings).

* Added a get_properties_pulled() method for resource objects, which gets the
  current value of a set of properties from the HMC. If the resource has
  auto-update enabled, it gets the value from the (automatically updated) local
  cache. Otherwise, it retrieves the properties from the HMC in the fastest
  possible way, considering property filtering if supported.

* Added support for passing an exception message directly to the
  zhmcclient.NotFound exception, instead of creating it from the 'manager' and
  'filter_args' parameters, which are now optional.

* Added support for asynchronous job cancellation via a new method Job.cancel().
  Documented for all asynchronous methods returning Job objects whether or not
  they can be cancelled. (issue #1299)

* Added support for low level management of asynchronous jobs via new methods
  Job.query_status() and Job.delete(). Note that higher level methods
  Job.check_for_completion() and Job.wait_for_completion() already existed.
  (issue #1299)

* Added support for creation and deletion of activation profiles on z16.
  This requires the SE to have a code level that has the
  'create-delete-activation-profiles' API feature enabled.
  (issue #1329)

* Added Lpar.start() to perform the "Start Logical Partition" operation in
  classic mode. (issue #1308)


Version 1.11.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 1.10.1.

Released: 2023-09-07

**Incompatible changes:**

* Fixed BaseResource.pull_properties() by returning None when no properties
  were specified. Before that, it returned the full set of properties when
  the Get Properties operation for the resource does not support the 'properties'
  query parameter, and produced 'properties=' as a query parameter when
  the resource does support the 'properties' query parameter.

  This is incompatible when your code uses pull_properties() on resource objects
  and relies on the prior behavior.

* Installation of this package using "setup.py" is no longer supported.
  Use "pip" instead.

**Bug fixes:**

* Fixed safety issues from 2023-08-27.

* Fixed zhmcclient_mock support for LDAP Server Definitions.

* Fixed end2end testcases for adapters, auto-updating, and groups.

* Fixed that SubscriptionNotFound exception message did not resolve its
  format string.

* Fixed the zhmcclient_mock support by adding support for query parameters,
  fixing the the Group operations and the "Query API Version" operation,
  and fixing the z16 mock environment definitions.
  Auto-update tests are now skipped when testing against mocked environments,
  because the mock support does not support notifications.

**Enhancements:**

* Docs: Improved documentation for developing tests.

* Implemented mock support for aggregation service operation "Submit requests"
  (bulk operations) (issue #1250).

* Added support for requesting additional properties in list() methods for
  Adapter, Certificate, Partition, VirtualSwitch, ImageActivationProfile
  resources, and for Console.list_permitted_lpars().

* Improved performance of list() method of all resource types when called
  with full_properties=True by using a bulk operation (aggregation service).

* Test: Added a new make target "end2end_mocked" to run the end2end tests against
  the mocked environments in the "examples" directory. As part of that, combined
  the coverage results of unit tests and end2end tests into a single data file
  that each test contributes to.

**Cleanup:**

* Consolidated common code of list() methods into the _utils.py module.


Version 1.10.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 1.9.1.

Released: 2023-08-04

**Bug fixes:**

* Fixed issue with PyYAML 5.4 installation on Python>=3.10 that fails since
  the recent release of Cython 3.

* Fixed example mocked environments to be useable in end2end test.

**Enhancements:**

* Added support for upgrading the HMC and SE to a new bundle level via new
  zhmcclient.Console.single_step_install() and
  zhmcclient.Cpc.single_step_install() methods. (issue #1219)

* Added resource class and name to HMC log entries. (issue #1058)

* Test: Added pytest fixtures for mocking at the HTTP level for unit tests
  in cases where zhmcclient mock support is not implemented.

* Added support for LPAR Load from FTP via a new Lpar.load_from_ftp()
  method. (issue #1048)

* Added support for STP configuration of CPCs via new operations of
  zhmcclient.Cpc: swap_current_time_server(), set_stp_config(),
  change_stp_id(), join_ctn(), leave_ctn(). (issue #750)

**Cleanup:**

* Fixed new issue reported by flake8 6.1.0.

* Converted all the percent-style string usages to format style except
  the logging calls. Logging will continue to use percent-style. (issue #663)


Version 1.9.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.8.2.

Released: 2023-07-14

**Incompatible changes:**

* Renamed the `Session.resource_updater` property to `auto_updater` and the
  `zhmcclient.ResourceUpdater` class to `AutoUpdater` to take into account that
  the class and property now represent auto-updated manager objects in addition
  to auto-updated resource objects. Note that the property and class are
  still experimental in this version.

**Deprecations:**

* Deprecated the 'verify' parameter of 'Session.logoff()'. Its use with
  verify=True caused an invalid session to first be renewed and then deleted
  again. It is no longer used.

**Bug fixes:**

* Fixed and improved session creation, deletion and automatic renewal.
  Fixed the arguments passed to the retried HTTP operations in case the session
  gets renewed.
  Added the ability to log off sessions properly in case the session ID is
  invalid, by adding a 'renew_session' flag to Session.get/post/delete() (this
  ability is needed for zhmccli to address its issue #421).
  Fixed Session.is_logon(verify=True) which would log on in certain cases.
  Optimized Session.logoff(verify=True) which had logged on and then off again
  in case the session was already invalid.
  Improved and fixed the descriptions of Session.logon(), logoff(), is_logon()
  and session_id.

* In addition to 403.5 (session ID invalid), 403.4 (no session ID provided) is
  now also automatically handled by the zhmcclient in the same way, i.e. by
  performing a logon to the HMC and a retry of the HMC operation.

* Circumvented the removal of Python 2.7 from the Github Actions plugin
  setup-python, by using the Docker container python:2.7.18-buster instead.

* Addressed safety issues from 6+7/2023, by increasing 'requests' to 2.31.0
  on Python >=3.7, and by increasing other packages only needed for development.

* Fixed the handling of HTTP status 202 with empty response content: The
  old code tested the content for '' but the content is always a binary string.
  In Python 3.x, that check results in False and subsequently in an attempt
  to parse the empty string using JSON, which failed with a ParseError.
  Fixed by comparing the empty string against b''.

* Improved the handling of logoff: It now also tolerates a ConnectionError,
  which may be raised when the console.restart() method is used and the
  HMC quickly enough becomes unavailable.

* Fixed the bug issue template by correcting the command to display debug data.

**Enhancements:**

* Reworked export_dpm_configuration() to avoid using the "cpc" category when
  doing the initial GET Inventory call. This reduces the likelihood of running
  into problems during export due to problems with any of the CPCs managed by
  the HMC.

* Improved performance of metrics retrieval and processing for NIC and partition
  related metrics for CPCs in DPM mode.

* Added optimized lookup by name in list() methods of the following resource
  classes: `LdapServerDefinition`, `PasswordRule`, `Task`, `User`,
  `UserPattern`, `UserRole`,

* Added support for auto-updated resource managers. An auto-updated resource
  manager has its list of resources automatically updated as resources are
  created and deleted on the HMC, based on HMC notifications. (issue #1055)

  Added an example script examples/show_auto_updated_partition_manager.py
  to demonstrate an auto-updating enabled partition manager.

  Renamed the existing example script show_auto_update.py to
  show_auto_updated_partition.py, for clarity.

* Docs: In the description of the list() methods of the resource manager
  classes, described the optimized lookup behavior for auto-updated managers
  and optimized access via the name-to-URI cache.

* In the NotificationReceiver class, added support for managing subscriptions
  for topics dynamically with new methods 'subscribe()', 'unsubscribe()',
  'is_subscribed()' and 'get_subscription()'.


Version 1.8.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.7.3.

Released: 2023-05-16

**Incompatible changes:**

* The default value for the 'full_properties' parameter of the 'list()' method
  of some zhmcclient resource types (Console, LDAPServerDefinition,
  PasswordRule, User, UserPattern, UserRole, Task) has been changed from 'True'
  to 'False' in order to improve performance. This change also affects the
  set of properties of resources returned by 'find()' and 'findall()'.

  In many cases, this is not an incompatible change since property access by
  methods such as 'get_property()' or 'prop()' causes resource property
  retrieval under the covers if the full set of properties had not been
  retrieved in 'list()'.

  However, there are also cases where this change is incompatible, for example
  when accessing the resource properties via the 'properties' property. In such
  cases, you need to change the call to 'list()' by specifying
  'full_properties=True'. In cases where you had used 'find()' or 'findall()',
  that parameter cannot be specified, and you need to fall back to using
  'list()'.

**Bug fixes:**

* Addressed safety issues by increasing minimum versions of packages, where
  possible.

* Changed use of 'method_whitelist' in urllib3.Retry to 'allowed_methods'.
  The old method was deprecated in urllib3 1.26.0 and removed in 2.0.0.
  Related to that, increased the minimum versions of urllib3 to 1.26.5 and of
  requests to 2.25.0. Added urllib3 to the dependencies for installing zhmcclient,
  because the indirect depndency of requests is not sufficient. (issue #1145)

* Fixed RTD docs build issue with OpenSSL version by providing a .readthedocs.yaml
  file that specifies Ubuntu 22.04 as the build OS.

* Added trouble shooting info for urllib3 2.0 ImportError requiring
  OpenSSL 1.1.1+.

* Increased dependent package jsonschema to >=3.0.1 to resolve dependency
  issue with jupyter. (issue #1165)

**Enhancements:**

* Disabled the default retrieval of the full set of properties in list()
  methods that was enabled by default, for the following resource types:
  Console, LDAPServerDefinition, PasswordRule, User, UserPattern, UserRole,
  Task. This provides a performance boost in cases where find() or findall()
  is used with filters that can be handled by the HMC, because in such cases
  the resource properties do not need to be retrieved.

* Added a 'pull_properties()' method to zhmcclient resource classes, that
  performs a "Get Properties" HMC operation with the 'properties' query
  parameter defined. This can be used to speed up certain property retrieval
  operations, for example on the Console or on CPCs. (issue #862)

* Added a 'list_sibling_adapters()' method to the zhmcclient.Adapter class
  that lists the other Adapter objects on the same physical adapter card.
  Added end2end testcases for the new method.

* Test: Added end2end testcases for property retrieval.

* Added zhmcclient.GroupManager and zhmcclient.Group to support Group resources.
  Group resources represent user-defined groups of resources; they can be used
  for example in User Role permissions. Added zhmcclient mock support for
  Group resources. Added testcases for both of that. (issue #1017)

* Enhanced export_dpm_configuration() to include Certificate objects.

* Introduced Certificate objects as new category of resources and added new
  methods to assign/unassign Certificate objects to/from DPM mode partitions and
  classic mode LPARs and activation profiles.

* Added two new methods Console.list_api_features() and
  Cpc.list_api_features() and accompanying documentation to support the
  new "API features" concept.

**Cleanup:**

* So far, the `Partition.hbas` property was set to `None` for CPCs that have the
  "dpm-storage-management" feature enabled (i.e. starting with z14), because
  HBAs are then represented as Virtual Storage Resource objects. For
  consistency, this property was changed to provide an `HbaManager` object.
  Since that property uses lazy initialization, there is no change at runtime
  unless the property is actually accessed.


Version 1.7.0
^^^^^^^^^^^^^

Released: 2023-03-26

**Incompatible changes:**

* export_dpm_configuration(): the default behavior when exporting the DPM
  configuration has been changed to only include those adapters that are
  referenced by other elements of the exported configuration data.
  Old behavior is available by passing a new parameter to the function. (#1115)

**Bug fixes:**

* Added the missing dependent packages for using the 'zhmcclient.testutils'
  sub-package by adding a Paython package extra named 'testutils'. This is
  only needed when performing end2end tests, or when using the example scripts.
  The extra can be installed with 'pip install zhmcclient[testutils]'.

* Fixed incorrect list of managers in 'managers' attribute of zhmcclient
  exception 'MetricsResourceNotFound' when a CPC was not found. (issue #1120)

**Enhancements:**

* Added missing test environments (Python >=3.6 on MacOS and Windows) to the
  weekly full tests.

* Addressed issues reported by safety by increasing package versions. (#1103)

* Test: Added more tools to missing requirements checking.

* export_dpm_configuration(): sorting result lists for more stable output


Version 1.6.0
^^^^^^^^^^^^^

Released: 2023-03-02

**Bug fixes:**

* Accommodated use of Ubuntu 22.04 in Github Actions as the default ubuntu.

* Fixed install error of twine -> keyring dependency pywin32-ctypes on Windows
  with Python 3.8 and higher. (issue #1078)

**Enhancements:**

* Simplified release process by adding a new GitHub Actions workflow publish.yml
  to build and publish to PyPI.

* Enhanced method Cpc.export_dpm_configuration() to support Partition Link
  objects (introduced with Z16).

* Docs: Added a section "Setting up firewalls or proxies" that provides
  information which ports to open for accessing the HMC. (issue #1088)

**Cleanup:**

* Addressed issues in test workflow reported by Github Actions. (issue #1091)


Version 1.5.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.4.1.

Released: 2022-10-25

**Bug fixes:**

* Fixed a flake8 AttributeError when using importlib-metadata 5.0.0 on
  Python >=3.7, by pinning importlib-metadata to <5.0.0 on these Python versions.

* Fixed an AttributeError in the VirtualStorageResource.adapter_port property.
  (issue #1059)

**Enhancements:**

* Added a new method Adapter.list_assigned_partitions() that performs the
  HMC operation "Get Partitions Assigned to Adapter".

* Added a new method Lpar.reset_normal() that performs the HMC operation
  "Reset Normal" on Logical Partitions (in classic mode).

* Added an optional 'os_ipl_token' parameter to the Lpar.reset_clear()
  method.


Version 1.4.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.3.3.

Released: 2022-08-20

**Incompatible changes:**

* Mocked HMC definitions now require userid and password in the vault file.

* Auto-updated resources now auto-detect if the corresponding HMC resource no
  longer exists and accessing the zhmcclient resource in that case with certain
  attributes and methods causes a new `zhmcclient.CeasedExistence` exception to
  be raised. The documentation shows which attributes and methods do that.

* The zhmcclient/debuginfo.py script has been removed since the instructions using
  it only worked when having the repo local, but not when installing from Pypi.
  To display debug info, you can now use:
  python -c "import zhmcclient; print(zhmcclient.debuginfo())".

**Bug fixes:**

* Pylint: Migrated config file to pylint 2.14; No longer installing Pylint on
  Python 2.7; Enabled running Pylint again on Python 3.5, Increased minimum
  version of Pylint to 2.10.0 on Python 3.5 and higher.

* Addressed issues discovered by Pylint 2.10 and higher (it was pinned to 2.7.0
  before).

* Made the `JMS_LOGGER_NAME` symbol publicly available, in order for users
  to have a symbol for the JMS logger name.

* Fixed an AttributeError on 'HMCDefinition.filepath' when using the testutils
  support for mocked environments. (issue #1001)

* Fixed the 'dump()' method on the Client class and other resource classes
  to accommodate for HBAs on z14 and later, unconfigured FICON adapters, and
  presence of unmanaged CPCs.

* Fixed the add_permissions() and remove_permissions() methods of UserRole
  by no longer including the 'include-members' and 'view-only-mode' parameters
  in the request payload, since the HMC requires them to be omitted unless
  the type of permitted resource allows them.

* Fixes in default values for properties in mock support of 'Create Partition'.

* Test: Added tolerance against non-unique storage volume names in HMC 2.14.0
  in the storage volume end2end tests. (issue #962)

**Enhancements:**

* Relative path names for mock files specified in the HMC inventory file are
  now interpreted relative to the directory of the HMC inventory file.
  (part of issue #1001)

* Added optional 'userid' and 'password' arguments to the
  'FakedSession.from_hmc_yaml_file()' method and to the methods it calls, in
  order to use a userid to log on to the mocked HMC, consistent with real HMCs.
  (part of issue #1001)

* Added a dump_hmc_definition.py example script that dumps the resources of
  an HMC to a HMC definition file for use as a mock definition.

* Improved mock support for password rules and user roles by creating default
  properties. (issue #1018)

* Auto-updated resources now auto-detect if the corresponding HMC resource no
  longer exists. This can be tested with a new `ceased_existence` attribute on
  the resources. Accessing the zhmcclient resource in that case with certain
  attributes and methods causes a new `zhmcclient.CeasedExistence` exception to
  be raised. The documentation shows which attributes and methods do that.
  (Issue #996)

* Added an example script 'list_cpcs.py' that lists managed CPCs with version,
  status, operational mode.

* Improved the mock support for Create Partition by doing more input validation
  and by setting all default properties on the new partitions.

* Improved waiting for job of asynchronous operation:
  Increased wait time between 'Get Job Properties' operations from 1 second
  to 10 seconds to release stress on the HMC. Now logging failures of
  'Get Job Properties operation. No longer removing the original message in the
  urllib3.exceptions.MaxRetryError exception.

* In Lpar.scsi_load(), added parameters 'os_ipl_token' and 'clear_indicator',
  to support the corresponding parameters of the 'SCSI Load' operation. Clarified
  the description of parameters of Lpar.scsi_load() and Lpar.scsi_dump().

* Added tests for Lpar.scsi_load() and Lpar.scsi_dump().

* Added mock support for Lpar.scsi_load() and Lpar.scsi_dump(), including tests.

* Added Lpar.nvme_load() and Lpar.nvme_dump() methods, and tests.

* Added mock support for Lpar.nvme_load() and Lpar.nvme_dump(), and tests.

**Cleanup:**

* Removed unintended internal names from the zhmcclient namespace in the area
  of logging and timestamp conversion.


Version 1.3.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.2.2.

Released: 2022-05-17

**Incompatible changes:**

* 'Lpar.list()' with filters that have no matching LPAR now returns an empty
  result set, consistent with other zhmcclient 'list()' methods. Previously,
  'Lpar.list()' raised HTTPError 404.1 when no LPAR matched the filters.
  If you used 'Lpar.list()' with filters, you may need to adjust the handling
  of the case where no LPARs match the filter. (issue #954)

* End2end test: Changed the format of files that define the HMCs to test against,
  from a zhmcclient-specific HMC definition file in YAML format to a pair of
  Ansible-compatible inventory and vault files in YAML format.
  The HMC inventory file is '.zhmc_inventory.yaml' in the user's home directory
  by default and can be set using the 'TESTINVENTORY' environment variable.
  The HMC vault file is '.zhmc_vault.yaml' in the user's home directory
  by default and can be set using the 'TESTVAULT' environment variable.
  The format of the HMC definition file used so far is no longer supported.
  (issues #950, #986)

* Renamed the properties of the 'zhmcclient.testutils.HMCDefinition' to remove
  the 'hmc&nbsp;_' prefix, e.g. 'hmc_userid' became 'userid', etc. (part of issue #986)

**Bug fixes:**

* Added the missing `secure_boot` parameter to `zhmcclient.Lpar.scsi_dump()`
  (issue #945)

* Fixed the handling of JMS notifications that have no content, such as the
  job completion notification and the inventory change notification.
  (issue #956)

* End2end test: Made user test tolerant against missing password rule 'Basic'.
  (issue #960)

* End2end test: Added CPC property 'last-energy-advice-time' to the list of
  volatile CPC properties in 'test_cpc_find_list()'.

**Enhancements:**

* Docs: Added documentation for the 'zhmcclient.testutils' module to the
  "Development" chapter. (issue #950)

* Docs: Improved and fixed the "Testing" section in the "Development" chapter.
  (issue #950)

* Added a new function 'zhmcclient.testutils.hmc_definitions()' that
  can be used by example scripts to access HMC definitions.

* Examples: Simplified and cleaned up the example scripts. They now use
  the HMC inventory and vault files. Deleted scripts that were too complex and
  not particularly instructive (cpcdata.py, cpcinfo.py). Renamed some scripts
  for better clarity on what they do. (issue #953)

* End2end test: Added env.var 'TESTRESOURCES' that can be used to control
  which resources are picked for testing with. By default, a random choice
  from all resources is picked. (issue #963)

* Added support for z16 in Python property 'Cpc.maximum_active_partitions'.

* Improved description of 'Cpc.maximum_active_partitions' to better
  clarify the difference between DPM partitions and classic mode LPARs.

* Removed optional empty fields in the exported DPM configuration data returned
  by 'Cpc.export_dpm_configuration()'. This allows using newer versions of
  zhmcclient that added support for new features with older machines that did
  not yet have the feature. (issue #988)

**Cleanup:**

* Made the handling of 'Lpar.list()' with filters that have no matching LPAR
  consistent with other zhmcclient 'list()' methods that return an empty
  result set in such cases. Previously, 'Lpar.list()' raised HTTPError 404.1
  when no LPAR matched the filters. (issue #954)

* Removed the unused 'FakedHMCFileError' class from the
  'zhmcclient.testutils.hmc_definition_fixtures' module. (issue #950)

* Removed code in tests/common/utils.py that supported the old format for
  defining HMCs. (issue #966)

* Transitioned test code for the old format for defining HMCs to the new
  format, and removed some test code. (issue #966)

* End2end test: Removed CPC scope from test functions for HMC-based resources
  (e.g. users)


Version 1.2.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.1.1.

Released: 2022-03-28

**Incompatible changes:**

* The installation of this package using `setup.py install` is no longer
  recommended. Use `pip install` instead.

* The "timestamp" init parameter of "FakedMetricObjectValues" now gets
  converted to a timezone-aware datetime object using the local timezone, if
  provided as timezone-naive datetime object. This may be incompatible for
  users of the zhmcclient mock support if the mock support is used in testcases
  that have expected timestamps.

* Mock support for metrics: The representation of metric group definitions has
  been moved from the FakedMetricsContextManager class to the FakedHmc class,
  where they are now predefined and no longer need to be added by the user of
  the mock support. As a result, the add_metric_group_definition() method
  has been dropped. The get_metric_group_definition() and
  get_metric_group_definition_names() methods have also been dropped and
  the predefined metric groups can now be accessed via a new property
  FakedHmc.metric_groups that provides an immutable view.

* Mock support for metrics: The representation of metric values has
  been moved from the FakedMetricsContextManager class to the FakedHmc class.
  The add_metric_values() method has been moved accordingly. The
  get_metric_values() and get_metric_values_group_names() methods have been
  dropped and the metric values can now be accessed via a new property
  FakedHmc.metric_values that provides an immutable view.

**Bug fixes:**

* Fixed an issue that delete() of element objects e.g. NICs, HBAs, VFs,
  storage volumes, storage template volumes) did not update the uris list in
  the local properties of its parent object.

* Fixed the issue that 'StorageVolumeTemplate.delete()' provided an incorrect
  field in the request to the HMC. (issue #900)

* Fixed the issue that resource types with case-insensitive names were matched
  case-sensitively in find..() and list() methods. This affected resource
  types User, UserRole, UserPattern, PasswordRule, and LDAPServerDefinition.
  The mock support was also fixed accordingly. This required adding 'nocasedict'
  as a new package dependency. (issue #894)

* Fixed issues in the zhmcclient_mock support for the "Update LPAR Properties"
  operation. (issue #909)

* Doc fix: Added the missing classes "FakedMetricGroupDefinition",
  "FakedMetricObjectValues", "FakedCapacityGroupManager", and "FakedCapacityGroup"
  to section "Mock support" and fixed errors in doc links to some of these
  classes.

* Mock support: Fixes for storage groups and added support for storage volumes.

* Mock support: Fixed that operations on activation profiles succeed with an
  empty result set in case the CPC is in DPM mode, instead of failing.

* Mock support: Fixed a follow-on error in repr() when FakedAdapter() raised
  InputError.

* Mock support: Fixed list of properties returned by the "List Adapters of CPC"
  operation.

* Fixed that the "timestamp" init parameter of "FakedMetricObjectValues" gets
  converted to a timezone-aware datetime object using the local timezone, if
  provided as a timezone-naive datetime object.

* Fixed installation of pywinpty (used by Jupyter notebook) on Python >=3.6,
  by pinning it to <1.0.

**Enhancements:**

* Added support for Python 3.10. This required increasing the minimum version of
  a number of packages, both for installation and development. (issue #867)

* End2end tests: Added support for verify_cert parameter in HMC definition file.
  Changed test env var TESTHMCDIR with hard coded filename to TESTHMCFILE.

* Added support for activating and deactivating a CPC in classic mode, by
  adding Cpc.activate() and Cpc.deactivate().

* Added support for saving real and faked HMCs to HMC definitions, via new
  methods to_hmc_yaml_file(), to_hmc_yaml() and to_hmc_dict() on the 'Client'
  class.
  Added support for restoring faked HMCs from HMC definitions, via new methods
  from_hmc_yaml_file(), from_hmc_yaml() and from_hmc_dict() on the
  'FakedSession' class.
  This required adding the following Python packages as dependencies:
  PyYAML, yamlloader, jsonschema, dateutil.

* Mock support: Added checks for non-modifiable properties in Update operations
  and for defaulting properties in Create operations.

* Docs: Improved example on README page and in Introduction section of the
  documentation to be much faster.

* Fixed that some content of request exceptions was lost when re-raising them
  as zhmcclient exceptions. (issue #845)

**Cleanup:**

* Removed the ability to build the Windows executable, triggered by the fact
  that the corresponding build command has been removed in Python 3.10.
  The Windows executable has never been part of the zhmcclient package on Pypi,
  and building it seems odd anyway. (issue #865)


Version 1.1.0
^^^^^^^^^^^^^

This version contains all fixes up to version 1.0.3.

Released: 2021-11-18

**Bug fixes:**

* Fixed maturity level from 4 (Beta) to 5 (Production/Stable).

* Fixed an issue in 'Lpar.stop()' where incorrectly an empty body was sent, and
  an incorrect status has been waited for.

* Fixed a TypeError in 'Partition.mount_iso_image()'. (issue #833)

* Fixed install error of wrapt 1.13.0 on Python 2.7 on Windows due to lack of
  MS Visual C++ 9.0 on GitHub Actions, by pinning it to <1.13.

* Fixed Sphinx doc build error on Python 2.7.

* Docs: Fixed description of Client.get_inventory().

* Dev: Excluded more-itertools 8.11.0 on Python 3.5.

**Enhancements:**

* Added support for the 'Set Auto-Start List' operation on CPCs by adding
  a method 'Cpc.set_auto_start_list()', and the corresponding mock support.
  (issue #472)

* Improved the log entries when file-like objects are passed to
  'Partition.mount_iso_image()'.

* Changed the 'User-Agent' header sent with each HTTP request to show
  'python-zhmcclient/<version>'.

* Added support for 'Cpc.import_dpm_configuration()'. (issue #851)

* Added support for 'Cpc.export_dpm_configuration()'.

* Added a new exception class 'ConsistencyError' that indicates consistency
  errors that should be reported.

* Added a new example script examples/export_dpm_config.py.

**Cleanup:**

* Defined HMC resource class names centrally.


Version 1.0.0
^^^^^^^^^^^^^

This version contains all fixes up to version 0.32.1.

Released: 2021-08-05

**Incompatible changes:**

* Dropped support for Python 3.4. Python 3.4 has had its last release as 3.4.10
  on March 18, 2019 and has officially reached its end of life as of that date.
  Current Linux distributions no longer support Python 3.4. (issue #792)

**Bug fixes:**

* Fixed an install error of lazy-object-proxy on Python 3.5 by no longer
  installing pylint/astroid/typed-ast/lazy-object-proxy on Python 3.5. It
  was already not invoked anymore on Python 3.5, but still installed.

* Increased minimum version of Pylint to 2.5.2 on Python 3.6 and higher.

* Fixed a bug where 'Console.list_permitted_partitions()' and
  'Console.list_permitted_lpars()' when run on HMC/SE version 2.14.0 failed
  when accessing the 'se-version' property of the partition unconditionally.
  That property was introduced only in HMC/SE version 2.14.1. (issue #816)

**Enhancements:**

* Made read and write access to the properties dictionary of zhmcclient resource
  objects thread-safe by adding a Python threading.RLock on each resource object.

* Added support for auto-updating of resources. For details, see the new
  section 'Concepts -> Auto-updating of resources'. (issue #762)

**Cleanup:**

* Removed old build tools that were needed on Travis and Appveyor
  (remove_duplicate_setuptools.py and retry.bat) (issue #809)


Version 0.32.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 0.31.1.

Released: 2021-07-02

**Bug fixes:**

* Docs: Fixed and added missing authorization requirements for the Partition
  and Lpar methods.

* Examples: Fixed errors in and improved metrics examples.

* Fixed issues raised by new Pylint version 2.9.1.

**Enhancements:**

* Added support for 'Console.list_permitted_partitions()' and
  'Console.list_permitted_lpars()'. These methods require HMC 2.14.0 or later.
  (issue #793)

* The Console object returned by 'client.consoles.console' is now a locally
  built object in order to avoid needless property retrieval.



Version 0.31.0
^^^^^^^^^^^^^^

This version contains all fixes up to version 0.30.2.

Released: 2021-06-10

**Incompatible changes:**

* Method 'NotificationReceiver.notifications()' now raises JMS errors returned
  by the HMC as a new exception 'NotificationJMSError'. JSON parse errors
  are now raised as a new exception 'NotificationParseError'. Both new
  exceptions are based on a new base exception 'NotificationError'. (issue #770)

* By default, the zhmcclient now verifies the HMC certificate using the
  CA certificates in the Python 'certifi' package. This can be controlled with
  a new 'verify_cert' init parameter to the 'zhmcclient.Session' class. (issue #779)

* The 'properties' attribute of the resource classes (e.g. 'Partition') now
  is an immutable 'DictView' object in order to enforce the stated rule that
  that callers must not modify the properties dictionary. If your code used to
  make such modifications nevertheless, it will now get a 'TypeError' or
  'AttributeError' exception, dependent on the nature of the modification.

**Bug fixes:**

* Fixed a missing argument in 'NotificationListener.on_message()' by pinning
  stomp.py such that 6.1.0 and 6.1.1 are excluded. (issue #763)

* Fixed a package dependency issue when setting up the development environment
  with the "pywinpty" package on Python 2.7 and Windows. (issue #772)

* JMS errors returned by the HMC are now handled by raising a new exception
  'NotificationJMSError' in the 'NotificationReceiver.notifications()' method.
  Previously, an exception was raised in the thread running the notification
  receiver, rendering it unusable after that had happened. (issue #770)

* Fixed a TypeError for concatenating str and bytes. (issue #782)

**Enhancements:**

* Added a 'verify_cert' init parameter to the 'zhmcclient.Session' class to
  enable verification of the server certificate presented by the HMC during
  SSL/TLS handshake. By default, the certificate is validated against
  the CA certificates provided in the Python 'certifi' package. (issue #779)

* Added catching of OSError/IOError exceptions raised by the 'requests' package
  for certain certificate validation failures, re-raising such exceptions as a
  pywbem.ConnectionError.

* Docs: Added a section "Security" to the documentation that describes security
  related aspects in the communication between the zhmcclient and the HMC.
  (related to issue #779)

* Docs: Added a section "Troubleshooting" to appendix of the documentation that
  currently lists two cases of communication related issues.
  (related to issue #779)

* The 'properties' attribute of the resource classes (e.g. 'Partition') now
  is an immutable 'DictView' object provided by the 'immutable-views' package,
  in order to enforce the stated rule that that callers must not modify the
  properties dictionary of resource objects.


Version 0.30.0
^^^^^^^^^^^^^^

Released: 2021-04-06

**Bug fixes:**

* Docs: Properties of classes are now shown in the Attributes summary table
  of the class. (issue #726)

* Docs: Fixed the incorrect default value documented for the `force` parameter
  of `Lpar.scsi_load()`. The correct default is `False`. (part of issue #748).

* Fixed StatusTimeout when activating an LPAR that goes straight to status
  "operating", by adding "operating" as a valid target value for the
  operational status. (issue #755)

**Enhancements:**

* Added an optional parameter `secure_boot` to `Lpar.scsi_load()` (issue #748).

* Added an optional parameter `force` to `Lpar.scsi_dump()` (issue #748).


Version 0.29.0
^^^^^^^^^^^^^^

Released: 2021-03-23

**Bug fixes:**

* Mitigated the coveralls HTTP status 422 by pinning coveralls-python to
  <3.0.0.

* Docs: Removed outdated reference to KVM for IBM z Systems Admin book that
  was used as a second example in the Introduction section.

* Docs: Added the missing Methods and Attributes tables to the description of
  resources related to the storage management feature (e,g. StorageGroup).
  (issue #708)

**Enhancements:**

* Added a new `Partition.start_dump_program()` method that performs the HMC
  operation 'Start Dump Program'. That operation is supported on CPCs in DPM
  mode that have the DPM storage management feature (i.e. z14 and later) and
  complements the 'Dump Partition' HMC operation that is supported only on
  CPCs in DPM mode that do not have the DPM storage management feature
  (i.e. z13 and earlier). Mock support for the 'Start Dump Program' operation
  was also added. (issue #705).

* Improved zhmcclient HMC logging in error cases by not truncating the HTTP
  response content for HTTP status 400 and higher. (issue #717) Also the
  truncation limit was increased to 30000 to accommodate most HMC responses.

* Improved display of `zhmcclient.HTTPError` exceptions by adding the 'stack'
  field if present. (issue #716)

* Suppressed exceptions that were caught and a new exception was raised
  in the except clause, by setting `__cause__ = None` on the new exception.
  This avoids lengthy and unnecessary tracebacks that contain the message
  'Another exception occurred when handling ...'. (issue #715)

* Improved the handling of resource not found errors during metrics processing
  by adding a new `zhmcclient.MetricsResourceNotFound` exception that may now
  be raised when accessing the `MetricObjectValues.resource` property.
  (zhmc-prometheus-exporter issue #113)

* Blanked out value of 'x-api-session' field (Session ID) when logging error
  responses. (zhmccli issue #136)

* Added support for Capacity Groups in DPM mode, by adding resource classes
  `zhmcclient.CapacityGroup` and `zhmcclient.CapacityGroupManager` and a
  property `zhmcclient.Cpc.capacity_groups` for accessing them.
  (issue #734)

**Cleanup:**

* Docs: Moved change log up one level to avoid Sphinx warning about duplicate
  labels.


Version 0.28.0
^^^^^^^^^^^^^^

Released: 2020-12-20

**Incompatible changes:**

* Removed the installed scripts `cpcdata` and `cpcinfo` and added them as
  `cpcdata.py` and `cpcinfo.py` to the examples folder.

**Bug fixes:**

* Test: Increased time tolerance for time-based tests.

* Docs: Added z15 to supported environments (issue #684).

* Fixed an AttributeError in `UserPatternManager.reorder()`
  (related to issue #661).

* Test: Fixed an AttributeError in test utilities class `HMCDefinition`
  (related to issue #661).

* Test: Fixed incorrect assignment in adapter test
  (related to issue #661).

**Enhancements:**

* Migrated from Travis and Appveyor to GitHub Actions. This required several
  changes in package dependencies for development.

* Added support for operations for managing temporary processor capacity:
  `Cpc.add_temporary_capacity()` and `Cpc.remove_temporary_capacity()`.

* Added support for status timeout in `Partition.stop()` that waits for partition
  stop to reach desired status.

* Test: Resolved remaining Pylint issues and enforcing no issues from now on
  (issue #661).


Version 0.27.0
^^^^^^^^^^^^^^

Released: 2020-09-10

This version contains all fixes up to 0.26.2.

**Bug fixes:**

* Fixed Travis setup by removing circumventions for old issues that caused
  problems meanwhile.

* Adjusted versions of dependent packages for development environment to
  fix issues on Python 3.4.

* Fixed AttributeError when calling partition.list_attached_storage_groups().
  (See issue #629)

* Docs: Fixed description to start a new version that was missing updating the
  version to the new development version.
  (See issue #639)

* Docs: Fixed description of installation from a repo branch.
  (See issue #638)

* Test: Fixed missing ffi.h file on CygWin when testing (See issue #655)

* Docs: Fixed links to HMC WS API books that have become invalid.
  (See issue #665)

* Fixed empty port list returned by PortManager.list() for CNA adapters.

* Install: Fixed the broken installation from the source distribution archive
  on Pypi (see issue #651)

* Test: Pinned 'pyrsistent' package (used by jupyter notebook) to <0.16.0 on
  Python 2.7 and to <0.15.0 on Python 3.4.

* Test: Fixed issue where virtualenv on pypy3 created env one level higher.
  (see issue #673)

**Enhancements:**

* Added an easy way to print debug information for inclusion into issues, via
  `python -m zhmcclient.debuginfo`.
  (See issue #640)

* Added `discover_fcp()` and `get_connection_report()` methods to the
  `StorageGroup` resource. Added an example `discover_storage_group.py` that
  uses the two new methods.
  (See issue #623)

* Test: Running coveralls for all Python versions in order to cover Python
  version-specific code. The coveralls.io web site consolidates these runs
  properly into a single result.

* Docs: Added links to HMC WS APi and Operations books for z15.
  (Related to issue #665)

* Added the z15 machine types 8561 and 8562 for detecting the maximum number
  of partitions, and started exploiting the new 'maximum-partitions' property
  of the CPC for this purpose.

**Cleanup**

* Docs: Removed link to "KVM for IBM z Systems - System Administration" book,
  because the product is no longer supported. (Related to issue #665)

* Changed the theme of the documentation on RTD from classic to sphinx_rtd_theme
  (See issue #668)

* Test: Added 'make installtest' to the Makefile to test installation of the
  package into an empty virtualenv using all supported installation methods.
  Added these install tests to the Travis CI tests. (related to issue #651)


Version 0.26.0
^^^^^^^^^^^^^^

Released: 2020-01-24

This version contains all changes from 0.25.1.

**Bug fixes:**

* Added the missing os_ipl_token parameter to Lpar.scsi_dump().

* Migrated from using the yamlordereddictloader package to using the
  yamlloader package, because yamlordereddictloader got deprecated.
  (See issue #605)

* Pinned version of PyYAML to <5.3 for Python 3.4 because 5.3 removed support
  for Python 3.4

* Increased minimum version of stomp.py to 4.1.23 to pick up a fix for
  hangs during NotificationReceiver.close(). (See issue #572)

**Enhancements:**

* Promoted the development status of the zhmcclient package on Pypi from
  3 - Alpha to 4 - Beta.

* Added support for Python 3.8 to the package metadata and to the Travis and
  Appveyor and Tox environments. (See issue #596)

* Dropped the use of the pbr package. The package version is now managed
  in zhmcclient/_version.py. (See issue #594)

* Test: Added support for TESTOPTS env var to Makefile to be able to specify
  py.test options when invoking make test.


Version 0.25.0
^^^^^^^^^^^^^^

Released: 2019-12-18

**Bug fixes:**

* Docs: Fixed incorrect statement about HMC version 2.14.0 supporting both
  GA generations of z14 machines.

**Enhancements:**

* Docs: Added HMC version 2.14.1 in "Bibliography" and "Introduction" sections.

* Added support for following LPAR operations:

  - Lpar.psw_restart() (HMC: “PSW Restart”)
  - Lpar.scsi_dump() (HMC: “SCSI Dump”)

* Added support for Storage Template objects in DPM mode (see issue #589).


Version 0.24.0
^^^^^^^^^^^^^^

Released: 2019-08-15

**Incompatible changes:**

* Operations that resulted in HTTP status 403, reason 1 ("The user under which
  the API request was authenticated does not have the required authority to
  perform the requested action.") so far raised `ServerAuthError`. However,
  that exception does not represent that situation properly, because the
  login user is actually properly authenticated.
  The handling of this case was changed to now raise `HTTPError` instead of
  `ServerAuthError`.
  This change is only incompatible to users of the zhmcclient API who have
  code handling this exception specifically.

**Bug fixes:**

* Fixed LookupError on unknown encoding ISO-5589-1 in test_session.py test
  that occurred with latest requests_mock package.

* Increased minimum version of flake8 to 3.7.0 due to difficulties with
  recognizing certain 'noqa' statements. This required explicitly specifying
  its dependent pycodestyle and pyflakes packages with their minimum versions,
  because the dependency management did not work with our minimum
  package versions.

* Fixed use of incorrect HTTP method in `Console.get_audit_log()` and
  `Console.get_security_log()`. See issue #580.

**Enhancements:**

* Improved end2end test support for zhmcclient and its using projects.
  The zhmcclient.testutils package already provides some support for end2end
  tests by users of the zhmcclient package. It is also used by the end2end
  tests of the zhmcclient package itself. This change improves that support,
  mainly from a perspective of projects using zhmcclient.

* Improved the show_os_messages.py example.

* Blanked out the session ID value in the log record for logging off.

* Changed import of 'stomp' module used for notifications from the HMC, to be
  lazy, in order to speed up the import of 'zhmcclient' for its users.
  The 'stomp' module is now imported when the first
  `zhmcclient.NotificationReceiver` object is created. Also, only the class
  needed is imported now, instead of the entire module.

* Added timezone support to the utility function
  `zhmcclient.datetime_from_timestamp()`. The desired timezone for the returned
  object can now be specified as an optional argument, defaulting to UTC for
  compatibility. This allows displaying HMC timestamps in local time rather
  than just UTC time.

* Added support for specifying multiple notification topics to
  `zhmcclient.NotificationReceiver`.


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
