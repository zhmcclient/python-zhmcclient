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

zhmcclient - A pure Python client library for the z Systems HMC Web Services API
================================================================================

.. contents:: Contents:
   :local:

Overview
--------

This project provides the ``zhmcclient`` Python package, which is a client
library for the z Systems Hardware Management Console (HMC) Web Services API.

The goal of this project is to make the HMC Web Services API easily consumable
for Python programmers. The various manageable resources in the z Systems or
LinuxONE environment are provided as Python classes, and the operations against
them are provided as Python methods.

At this point, a small subset of the HMC Web Services API has been implemented.
The goal is to implement a reasonable subset of the API, with a focus on DPM
(Dynamic Partition Manager).

Using it & examples
-------------------

At this point, you need to clone the Git repository in order to use the
client.

::

    $ git clone <zhmcclient-repo-url>

It is beneficial to set up a `virtual Python environment`_,
because that leaves your system Python installation unchanged.

.. _virtual Python environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/

In order to establish any prereqs, issue from within the work directory of
your clone (with a virtual Python environment activated):

::

    $ make develop

For example code, see the Python scripts in the
`examples directory of the Git repository`_.
In order to run the examples, most of them need a so called `HMC credentials
file`, which you can copy from the example file
``examples/example_hmxcreds.yaml``, and then you need to update it (it should be
fairly self-explanatory).

.. _examples directory of the Git repository: https://github.rtp.raleigh.ibm.com/openstack-zkvm/python-zhmcclient/tree/master/examples

Documentation
-------------

At this point, the documentation of the package needs to be generated
by the users, using these commands (in a `virtual Python environment`_,
and in the working directory of the cloned Git repository):

::

    $ make develop
    $ make builddoc

The top-level document of the so generated API documentation will be
``build_doc/html/docs/index.html``.

The documentation describes all manageable resources supported by the client
library, but not their resource properties. See
`Hardware Management Console Web Services API`_ for information about the
resource properties.

.. _Hardware Management Console Web Services API: http://www-01.ibm.com/support/docview.wss?uid=isg29b97f40675618ba085257a6a00777bea&aid=1

Development and test
--------------------

It is recommended to establish a virtual Python environment, based upon one of
the supported Python versions (2.7, 3.4, 3.5).

The project uses ``make`` to do things in the currently active Python
environment. The command ``make help`` (or just ``make``) displays a list of valid
``make`` targets and a short description of what each target does.

Here is a list of the most important ``make`` commands:

* To establish the prerequisites in the currently active Python environment:

  ::

      $ make develop

* To build the API documentation:

  ::

      $ make builddoc

* To run the unit tests:

  ::

      $ make test

* To run only part of the unit tests:

  ::

      $ TESTCASES=TestInit make test

The ``tox`` command is supported to invoke various ``make`` targets across all
supported Python environments. It can be used to validate that the whole
project is in a good state:

::

    $ tox

Tox can also be used to run the unit tests or parts thereof in its own
virtual environment, as shown in the following examples:

::

    $ tox -e py27                      # Run all tests on Python 2.7
    $ tox -e py27 test_resource.py     # Run only this test source file on Python 2.7
    $ tox -e py27 TestInit             # Run only this test class on Python 2.7
    $ tox -e py27 TestInit or TestSet  # Simple expressions are possible

The ``tox`` positional arguments are passed to ``py.test`` using its ``-k``
option. Invoke ``py.test --help`` for details on the expression syntax of
its ``-k`` option.

Contributing
------------

Contribution rules are described in `CONTRIBUTING.rst`_.

.. _CONTRIBUTING.rst: https://github.rtp.raleigh.ibm.com/openstack-zkvm/python-zhmcclient/tree/master/CONTRIBUTING.rst

License
-------

python-zhmcclient is licensed under the Apache 2.0 License.
