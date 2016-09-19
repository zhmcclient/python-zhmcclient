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


.. _`Introduction`:

Introduction
============


.. _`What this package provides`:

What this package provides
--------------------------

The zhmcclient package (also known as python-zhmcclient) is a client library
written in pure Python that interacts with the Web Services API of the Hardware
Management Console (HMC) of `z Systems`_ or `LinuxONE`_ machines. The goal of
this package is to make the HMC Web Services API easily consumable for Python
programmers.

.. _z Systems: http://www.ibm.com/systems/z/
.. _LinuxONE: http://www.ibm.com/systems/linuxone/

The HMC Web Services API is the access point for any external tools to
manage the z Systems or LinuxONE platform. It supports management of the
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


.. _`Supported environments`:

Supported environments
----------------------

The zhmcclient package is supported in these environments:

* Operating systems: Linux, Windows, OS-X

* Python versions: 2.7, 3.4, and higher 3.x

* HMC versions: 2.11 and higher

The following table shows for each HMC version the supported HMC API version
and the supported z Systems and LinuxONE machine generations:

===========  ===============  ======================  ========================================
HMC version  HMC API version  HMC API book            Machine generations
===========  ===============  ======================  ========================================
2.11.0       1.1              HMC API 2.11.0          z196/z114
2.11.1       1.2              :term:`HMC API 2.11.1`  z196/z114
2.12.0       1.3              :term:`HMC API 2.12.0`  z196/z114 to zEC12/zBC12
2.12.1       1.4/1.5          :term:`HMC API 2.12.1`  z196/z114 to zEC12/zBC12
2.13.0       1.6              :term:`HMC API 2.13.0`  z196/z114 to z13/z13s/Emperor/Rockhopper
2.13.1       1.7              :term:`HMC API 2.13.1`  z196/z114 to z13/z13s/Emperor/Rockhopper
===========  ===============  ======================  ========================================


.. _`Installation`:

Installation
------------

The easiest way to install the zhmcclient package is by using Pip:

::

    $ pip install zhmcclient

This will download and install the latest released version of zhmcclient and
its dependent packages into your current Python environment (e.g. into your
system Python or into a virtual Python environment).

It is beneficial to set up a `virtual Python environment`_, because that leaves
your system Python installation unchanged.

.. _virtual Python environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/

As an alternative, if you want to install the latest development level of the
zhmcclient package for some reason, clone the Git repository of the package and
install it using Pip from its work directory:

::

    $ git clone git@github.com:zhmcclient/python-zhmcclient.git
    $ cd python-zhmcclient
    $ pip install .

This will install the package from the checked out branch in the Git work
directory (by default, the ``master`` branch) and will download and install its
dependent packages into your current Python environment.

You can verify that the zhmcclient package and its dependent packages are
installed correctly by importing the package into Python:

::

    $ python -c "import zhmcclient; print('ok')"
    ok


.. _`Examples`:

Examples
--------

For a quick start, the following example code lists the machines (CPCs) managed
by a particular HMC:

::

    #!/usr/bin/env python

    import zhmcclient
    import requests.packages.urllib3

    # Set these variables for your environment:
    zhmc = "<IP address or hostname of the HMC>"
    userid = "<userid on that HMC>"
    password = "<password of that HMC userid>"

    requests.packages.urllib3.disable_warnings()

    session = zhmcclient.Session(zhmc, userid, password)
    client = zhmcclient.Client(session)

    vi = client.version_info()
    print("HMC API version: {}.{}".format(vi[0], vi[1]))

    print("Listing CPCs ...")
    cpcs = client.cpcs.list()
    for cpc in cpcs:
        print(cpc)

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

* by issuing in your program:

  ::

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
