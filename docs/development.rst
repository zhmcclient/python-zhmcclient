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


.. _`Development`:

Development
===========

This section only needs to be read by developers of the zhmcclient package.
People that want to make a fix or develop some extension, and people that
want to test the project are also considered developers for the purpose of
this section.


.. _`Setting up the development environment`:

Setting up the development environment
--------------------------------------

The development environment is pretty easy to set up.

Besides having a supported operating system with a supported Python version
(see :ref:`Supported environments`), it is recommended that you set up a
`virtual Python environment`_.

.. _virtual Python environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/

Then, with a virtual Python environment active, clone the Git repo of this
project and prepare the development environment with ``make develop``:

::

    $ git clone git@github.com:zhmcclient/python-zhmcclient.git
    $ cd python-zhmcclient
    $ make develop

This will install all prerequisites the package needs to run, as well as all
prerequisites that you need for development.

Generally, this project uses Make to do things in the currently active
Python environment. The command ``make help`` (or just ``make``) displays a
list of valid Make targets and a short description of what each target does.


.. _`Building the documentation`:

Building the documentation
--------------------------

The ReadTheDocs (RTD) site is used to publish the documentation for the
zhmcclient package at http://python-zhmcclient.readthedocs.io/

This page automatically gets updated whenever the ``master`` branch of the
Git repo for this package changes.

In order to build the documentation locally from the Git work directory, issue:

::

    $ make builddoc

The top-level document to open with a web browser will be
``build_doc/html/docs/index.html``.


.. _`Testing`:

Testing
-------

To run unit tests in the currently active Python environment, issue one of
these example variants of ``make test``:

::

    $ make test                                  # Run all unit tests
    $ TESTCASES=test_resource.py make test       # Run only this test source file
    $ TESTCASES=TestInit make test               # Run only this test class
    $ TESTCASES="TestInit or TestSet" make test  # py.test -k expressions are possible

To run the unit tests and some more commands that verify the project is in good
shape in all supported Python environments, use Tox:

::

    $ tox                              # Run all tests on all supported Python versions
    $ tox -e py27                      # Run all tests on Python 2.7
    $ tox -e py27 test_resource.py     # Run only this test source file on Python 2.7
    $ tox -e py27 TestInit             # Run only this test class on Python 2.7
    $ tox -e py27 TestInit or TestSet  # py.test -k expressions are possible

The positional arguments of the ``tox`` command are passed to ``py.test`` using
its ``-k`` option. Invoke ``py.test --help`` for details on the expression
syntax of its ``-k`` option.


.. _`Contributing`:

Contributing
------------

You are welcome to contribute to the project! The rules for contributing are
described in the file `CONTRIBUTING.rst`_.

.. _CONTRIBUTING.rst: https://github.com/zhmcclient/python-zhmcclient/tree/master/CONTRIBUTING.rst
