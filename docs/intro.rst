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

.. _`Introduction`:

Introduction
============


.. _`What this package provides`:

What this package provides
--------------------------

The zhmcclient package (also known as python-zhmcclient) is a client library
written in pure Python that interacts with the Web Services API of the Hardware
Management Console (HMC) of `IBM Z`_ or `LinuxONE`_ machines. The goal of
this package is to make the HMC Web Services API easily consumable for Python
programmers.

.. _IBM Z: http://www.ibm.com/systems/z/
.. _LinuxONE: http://www.ibm.com/systems/linuxone/

The HMC Web Services API is the access point for any external tools to
manage the IBM Z or LinuxONE platform. It supports management of the
lifecycle and configuration of various platform resources, such as partitions,
CPU, memory, virtual switches, I/O adapters, and more.

The zhmcclient package encapsulates both protocols supported by the HMC Web
Services API:

* REST over HTTPS for request/response-style operations driven by the client.
  Most of these operations complete synchronously, but some long-running tasks
  complete asynchronously.

* JMS (Java Messaging Services) for notifications from the HMC to the client.
  This is used for notification about changes in the system, or about
  completion of asynchronous tasks started using REST.


.. _`zhmc CLI`:

zhmc CLI
~~~~~~~~

Before version 0.18.0 of the zhmcclient package, it contained the zhmc CLI.
Starting with zhmcclient version 0.18.0, the zhmc CLI has been moved from this
project into the new :term:`zhmccli project`.

If your project uses the zhmc CLI, and you are upgrading the zhmcclient
package from before 0.18.0 to 0.18.0 or later, your project will need to add
the :term:`zhmccli package` to its dependencies.


.. _`Supported environments`:

Supported environments
----------------------

The zhmcclient package is supported in these environments:

* Operating systems: Linux, Windows, OS-X

* Python versions: 2.7, 3.4, and higher 3.x

* HMC versions: 2.11.1 and higher

The following table shows for each HMC version the supported HMC API version
and the supported IBM Z machine generations. The corresponding LinuxONE
machine generations are listed in the notes below the table:

===========  ===============  ======================  =========================================
HMC version  HMC API version  HMC API book            Machine generations
===========  ===============  ======================  =========================================
2.11.1       1.1 - 1.2        :term:`HMC API 2.11.1`  z196 and z114
2.12.0       1.3              :term:`HMC API 2.12.0`  z196 to zEC12 and z114
2.12.1       1.4 - 1.5        :term:`HMC API 2.12.1`  z196 to zEC12 and z114 to zBC12
2.13.0       1.6              :term:`HMC API 2.13.0`  z196 to z13 (1) and z114 to zBC12
2.13.1       1.7, 2.1 - 2.2   :term:`HMC API 2.13.1`  z196 to z13 (1) and z114 to z13s (2)
2.14.0 (5)   2.20 - 2.24      :term:`HMC API 2.14.0`  z196 to z14 (3) and z114 to z14-ZR1 (4)
===========  ===============  ======================  =========================================

Notes:

(1) Supported for z13 and LinuxONE Emperor
(2) Supported for z13s and LinuxONE Rockhopper
(3) Supported for z14 and LinuxONE Emperor II
(4) Supported for z14-ZR1 and LinuxONE Rockhopper II
(5) HMC version 2.14.0 supports both the first and second wave of
    machines; there is no 2.14.1 numbered HMC version anymore.


.. _`Installation`:

Installation
------------

.. _virtual Python environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/
.. _Pypi: http://pypi.python.org/

The easiest way to install the zhmcclient package is by using Pip. Pip ensures
that any dependent Python packages also get installed.

With Pip, there are three options for where to install a Python package and its
dependent packages:

* Into a `virtual Python environment`_. This is done by having the virtual
  Python environment active, and running the Pip install commands as shown in
  the following sections.

  This option is recommended if you intend to develop programs using the
  zhmcclient API, because the packages you install do not interfere with
  other Python projects you may have.

* Into the system Python, just for the current user. This is done by not
  having a virtual Python environment active, and by using the ``--user``
  option on the Pip install commands shown in the following sections.

  This option is recommended if you intend to only use the zhmc CLI, or if
  you are not concerned about interfering with other Python projects you may
  have.

* Into the system Python, for all users of the system. This is done by not
  having a virtual Python environment active, and by using ``sudo`` on the
  Pip install commands shown in the following sections.

  Be aware that this option will replace the content of existing Python
  packages, e.g. when a package version is updated. Such updated packages as
  well as any newly installed Python packages are not known by your operating
  system installer, so the knowledge of your operating system installer is now
  out of sync with the actual set of packages in the system Python.

  Therefore, this approach is not recommended and you should apply this
  approach only after you have thought about how you would maintain these
  Python packages in the future.

Installation of latest released version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following command installs the latest released version of the zhmcclient
package from `Pypi`_ into the currently active Python environment:

.. code-block:: text

    $ pip install zhmcclient

Installation of latest development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to install the latest development level of the zhmcclient package
instead for some reason, you can install directly from the ``master`` branch
of its Git repository.

The following command installs the latest development level of the zhmcclient
package into the currently active Python environment:

.. code-block:: text

    $ pip install git+https://github.com/zhmcclient/python-zhmcclient.git@master

Installation on a system without Internet access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In both cases described above, Internet access is needed to access these
repositories.

If you want to install the zhmcclient package on a system that does not have
Internet access, you can do this by first downloading the zhmcclient package
and its dependent packages on a download system that does have Internet access,
transferring these packages to the target system, and installing them on the
target system from the downloaded packages:

1. On a system with Internet access, download the zhmcclient package and its
   dependent packages:

   .. code-block:: text

      [download-system]$ mkdir packages

      [download-system]$ cd packages

      [download-system]$ pip download zhmcclient
      Collecting zhmcclient
        Using cached https://files.pythonhosted.org/packages/c3/29/7f0acab22b27ff29453ac87c92a2cbec2b16014b0d32c36fcce1ca285be7/zhmcclient-0.19.0-py2.py3-none-any.whl
        Saved ./zhmcclient-0.19.0-py2.py3-none-any.whl
      Collecting stomp.py>=4.1.15 (from zhmcclient)
      . . .
      Successfully downloaded zhmcclient stomp.py pytz requests decorator six pbr docopt idna urllib3 certifi chardet

      [download-system]$ ls -1
      certifi-2018.4.16-py2.py3-none-any.whl
      chardet-3.0.4-py2.py3-none-any.whl
      decorator-4.3.0-py2.py3-none-any.whl
      docopt-0.6.2.tar.gz
      idna-2.6-py2.py3-none-any.whl
      pbr-4.0.2-py2.py3-none-any.whl
      pytz-2018.4-py2.py3-none-any.whl
      requests-2.18.4-py2.py3-none-any.whl
      six-1.11.0-py2.py3-none-any.whl
      stomp.py-4.1.20.tar.gz
      urllib3-1.22-py2.py3-none-any.whl
      zhmcclient-0.19.0-py2.py3-none-any.whl

2. Transfer all downloaded package files to the target system. Note that the
   package files are binary files.

   The actual files you see in your directory may not be the same ones shown in
   this section, because new package versions may have been released meanwhile,
   and new versions may even have different dependent packages.

3. On the target system, install the zhmcclient package in a way that causes
   Pip not to go out to the Pypi repository on the Internet, and instead
   resolves its dependencies by using the packages you transferred from the
   download system into the current directory:

   .. code-block:: text

      [target-system]$ ls -1
      certifi-2018.4.16-py2.py3-none-any.whl
      chardet-3.0.4-py2.py3-none-any.whl
      decorator-4.3.0-py2.py3-none-any.whl
      docopt-0.6.2.tar.gz
      idna-2.6-py2.py3-none-any.whl
      pbr-4.0.2-py2.py3-none-any.whl
      pytz-2018.4-py2.py3-none-any.whl
      requests-2.18.4-py2.py3-none-any.whl
      six-1.11.0-py2.py3-none-any.whl
      stomp.py-4.1.20.tar.gz
      urllib3-1.22-py2.py3-none-any.whl
      zhmcclient-0.19.0-py2.py3-none-any.whl

      [target-system]$ pip install -f . --no-index --upgrade zhmcclient-*.whl
      Looking in links: .
      Processing ./zhmcclient-0.19.0-py2.py3-none-any.whl
      Collecting six>=1.10.0 (from zhmcclient==0.19.0)
      . . .
      Installing collected packages: six, pytz, idna, urllib3, certifi, chardet, requests, decorator, docopt, stomp.py, pbr, zhmcclient
      Successfully installed certifi-2018.4.16 chardet-3.0.4 decorator-4.3.0 docopt-0.6.2 idna-2.6 pbr-4.0.2 pytz-2018.4 requests-2.18.4 six-1.11.0 stomp.py-4.1.20 urllib3-1.22 zhmcclient-0.19.0

Verification of the installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can verify that the zhmcclient package and its dependent packages are
installed correctly by importing the package into Python:

.. code-block:: text

    $ python -c "import zhmcclient; print('ok')"
    ok


.. _`Setting up the HMC`:

Setting up the HMC
------------------

Usage of the zhmcclient package requires that the HMC in question is prepared
accordingly:

1. The Web Services API must be enabled on the HMC.

2. To use all functionality provided in the zhmcclient package, the HMC user ID
   that will be used by the zhmcclient must be authorized for the following
   tasks. The description of each method of the zhmcclient package will mention
   its specific authorization requirements.

   * "Remote Restart" must be enabled on the HMC

   * Use of the Web Services API
   * Shutdown/Restart
   * Manage Alternate HMC
   * Audit and Log Management
   * View Security Logs
   * Manage LDAP Server Definitions
   * Manage Password Rules
   * Manage Users
   * Manage User Patterns
   * Manage User Roles
   * Manage User Templates

   When using CPCs in DPM mode:

   * Start (a CPC in DPM mode)
   * Stop (a CPC in DPM mode)
   * New Partition
   * Delete Partition
   * Partition Details
   * Start Partition
   * Stop Partition
   * Dump Partition
   * PSW Restart (a Partition)
   * Create HiperSockets Adapter
   * Delete HiperSockets Adapter
   * Adapter Details
   * Manage Adapters
   * Export WWPNs

   When using CPCs in classic mode (or ensemble mode):

   * Activate (an LPAR)
   * Deactivate (an LPAR)
   * Load (an LPAR)
   * Customize/Delete Activation Profiles
   * CIM Actions ExportSettingsData

3. (Optional) If desired, the HMC user ID that will be used by the zhmcclient
   can be restricted to accessing only certain resources managed by the HMC.
   To establish such a restriction, create a custom HMC user role, limit
   resource access for that role accordingly, and associate the HMC user ID
   with that role.

   The zhmcclient needs object-access permission for the following resources:

   * CPCs to be accessed

   For CPCs in DPM mode:

   * Partitions to be accessed
   * Adapters to be accessed

   For CPCs in classic mode (or ensemble mode):

   * LPARs to be accessed

For details, see the :term:`HMC Operations Guide`.

A step-by-step description for a similar use case can be found in chapter 11,
section "Enabling the System z HMC to work the Pacemaker STONITH Agent", in the
:term:`KVM for IBM z Systems V1.1.2 System Administration` book.


.. _`Examples`:

Examples
--------

The following example code lists the machines (CPCs) managed by an HMC:

.. code-block:: python

    #!/usr/bin/env python

    import zhmcclient
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()

    # Set these variables for your environment:
    hmc_host = "<IP address or hostname of the HMC>"
    hmc_userid = "<userid on that HMC>"
    hmc_password = "<password of that HMC userid>"

    session = zhmcclient.Session(hmc_host, hmc_userid, hmc_password)
    client = zhmcclient.Client(session)

    cpcs = client.cpcs.list()
    for cpc in cpcs:
        print(cpc)

Possible output when running the script:

.. code-block:: text

    Cpc(name=P000S67B, object-uri=/api/cpcs/fa1f2466-12df-311a-804c-4ed2cc1d6564, status=service-required)

For more example code, see the Python scripts in the `examples directory`_ of
the Git repository, or the :ref:`Tutorial` section of this documentation.

.. _examples directory: https://github.com/zhmcclient/python-zhmcclient/tree/master/examples


.. _`Versioning`:

Versioning
----------

This documentation applies to version |release| of the zhmcclient package. You
can also see that version in the top left corner of this page.

The zhmcclient package uses the rules of `Semantic Versioning 2.0.0`_ for its
version.

.. _Semantic Versioning 2.0.0: http://semver.org/spec/v2.0.0.html

The package version can be accessed by programs using the
``zhmcclient.__version__`` variable [#]_:

.. autodata:: zhmcclient._version.__version__

This documentation may have been built from a development level of the
package. You can recognize a development version of this package by the
presence of a ".devD" suffix in the version string. Development versions are
pre-versions of the next assumed version that is not yet released. For example,
version 0.1.2.dev25 is development pre-version #25 of the next version to be
released after 0.1.1. Version 1.1.2 is an `assumed` next version, because the
`actually released` next version might be 0.2.0 or even 1.0.0.

.. [#] For tooling reasons, that variable is shown as
   ``zhmcclient._version.__version__`` in this documentation, but it should be
   accessed as ``zhmcclient.__version__``.


.. _`Compatibility`:

Compatibility
-------------

In this package, compatibility is always seen from the perspective of the user
of the package. Thus, a backwards compatible new version of this package means
that the user can safely upgrade to that new version without encountering
compatibility issues.

This package uses the rules of `Semantic Versioning 2.0.0`_ for compatibility
between package versions, and for :ref:`deprecations <Deprecations>`.

The public API of this package that is subject to the semantic versioning
rules (and specificically to its compatibility rules) is the API described in
this documentation.

Violations of these compatibility rules are described in section
:ref:`Change log`.


.. _`Deprecations`:

Deprecations
------------

Deprecated functionality is marked accordingly in this documentation and in the
:ref:`Change log`, and is made visible at runtime by issuing Python warnings of
type :exc:`~py:exceptions.DeprecationWarning` (see :mod:`py:warnings` for
details).

Since Python 2.7, :exc:`~py:exceptions.DeprecationWarning` warnings are
suppressed by default. They can be shown for example in any of these ways:

* by specifying the Python command line option:

  ``-W default``

* by invoking Python with the environment variable:

  ``PYTHONWARNINGS=default``

* by issuing in your Python program:

  .. code-block:: python

      warnings.filterwarnings(action='default', category=DeprecationWarning)

It is recommended that users of this package run their test code with
:exc:`~py:exceptions.DeprecationWarning` warnings being shown, so they become
aware of any use of deprecated functionality.

It is even possible to raise an exception instead of issuing a warning message
upon the use of deprecated functionality, by setting the action to ``'error'``
instead of ``'default'``.


.. _`Reporting issues`:

Reporting issues
----------------

If you encounter any problem with this package, or if you have questions of any
kind related to this package (even when they are not about a problem), please
open an issue in the `zhmcclient issue tracker`_.

.. _zhmcclient issue tracker: https://github.com/zhmcclient/python-zhmcclient/issues


.. _`License`:

License
-------

This package is licensed under the `Apache 2.0 License`_.

.. _Apache 2.0 License: https://raw.githubusercontent.com/zhmcclient/python-zhmcclient/master/LICENSE
