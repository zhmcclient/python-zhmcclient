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

.. _`Development`:

Development
===========

This section only needs to be read by developers of the zhmcclient package.
People that want to make a fix or develop some extension, and people that
want to test the project are also considered developers for the purpose of
this section.


.. _`Code of Conduct Section`:

Code of Conduct
---------------

Help us keep zhmcclient open and inclusive. Please read and follow our
`Code of Conduct`_.

.. _Code of Conduct: https://github.com/zhmcclient/python-zhmcclient/blob/master/CODE_OF_CONDUCT.md


.. _`Repository`:

Repository
----------

The repository for zhmcclient is on GitHub:

https://github.com/zhmcclient/python-zhmcclient


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

.. code-block:: text

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

.. code-block:: text

    $ make builddoc

The top-level document to open with a web browser will be
``build_doc/html/docs/index.html``.


.. _`Testing`:

Testing
-------

The zhmcclient project supports the following kinds of tests:

* unit tests against a mocked HMC, using ``pytest``
* end2end tests against a real or mocked HMC, using ``pytest``
* install tests (Linux and MacOS only)


.. _`Running unit tests`:

Running unit tests
^^^^^^^^^^^^^^^^^^

To run the unit tests in the currently active Python environment, issue:

.. code-block:: text

    $ make test

By default, all unit tests are run. The ``TESTCASES`` environment variable can
be used to limit the testcases that are run. Its value is passed to the ``-k``
option of the ``pytest`` command.
For example:

.. code-block:: text

    $ TESTCASES=test_resource.py make test       # Run only this test source file
    $ TESTCASES=test_func1  make test            # Run only this test function or test class
    $ TESTCASES="test_func1 or test_func2" make test  # Run both of these test functions or classes

Additional options for the ``pytest`` command can be specified with the
``TESTOPTS`` environment variable.
For example:

.. code-block:: text

    $ TESTOPTS='-x' make test                    # Stop after first test case failure
    $ TESTOPTS='--pdb' make test                 # Invoke debugger on each test case failure

Invoke ``pytest --help`` for details on its options including the syntax of the
``-k`` option, or see
`pytest options <https://docs.pytest.org/en/latest/reference/reference.html#command-line-flags>`_.

To run the unit tests and some more commands that verify the project is in good
shape in all supported Python environments, use Tox.
The positional arguments of the ``tox`` command are passed to ``pytest`` using
its ``-k`` option.
For example:

.. code-block:: text

    $ tox                              # Run all tests on all supported Python versions
    $ tox -e py38                      # Run all tests on Python 3.8
    $ tox -e py38 test_resource.py     # Run only this test source file on Python 3.8
    $ tox -e py38 TestInit             # Run only this test class on Python 3.8
    $ tox -e py38 TestInit or TestSet  # pytest -k expressions are possible


.. _`Running end2end tests`:

Running end2end tests
^^^^^^^^^^^^^^^^^^^^^

Prepare an :ref:`HMC inventory file` that defines real and/or mocked HMCs the
tests should be run against, and an :ref:`HMC vault file` with credentials for
the real HMCs.

There are examples for these files, that describe their format in the comment
header:

* `Example HMC inventory file <https://github.com/zhmcclient/python-zhmcclient/blob/master/examples/example_hmc_inventory.yaml>`_.
* `Example HMC vault file <https://github.com/zhmcclient/python-zhmcclient/blob/master/examples/example_hmc_vault.yaml>`_.

To run the end2end tests in the currently active Python environment, issue:

.. code-block:: text

    $ make end2end

By default, the HMC inventory file named ``.zhmc_inventory.yaml`` in
the home directory of the current user is used. A different path name can
be specified with the ``TESTINVENTORY`` environment variable.

By default, the HMC vault file named ``.zhmc_vault.yaml`` in
the home directory of the current user is used. A different path name can
be specified with the ``TESTVAULT`` environment variable.

By default, the tests are run against the group name or HMC nickname
``default`` defined in the HMC inventory file. A different group name or
HMC nickname can be specified with the ``TESTHMC`` environment variable.

Examples:

* Run against group or HMC nickname 'default' using the specified HMC inventory
  and vault files:

  .. code-block:: text

      $ TESTINVENTORY=`./hmc_inventory.yaml` TESTVAULT=`./hmc_vault.yaml` make end2end

* Run against group or HMC nickname 'HMC1' using the default HMC inventory and
  vault files:

  .. code-block:: text

      $ TESTHMC=`HMC1` make end2end


.. _`Running end2end tests against example mocked environments`:

Running end2end tests against example mocked environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``examples`` directory contains example mocked environments defined in the
following YAML files:

* ``examples/example_mocked_z16_classic.yaml`` - HMC with a z16 in classic mode
* ``examples/example_mocked_z16_dpm.yaml`` - HMC with a z16 in DPM mode

It also contains an inventory and vault file for these mocked environments.
The inventory file defines its default group to use these mocked environments:

* ``examples/example_hmc_inventory.yaml``
* ``examples/example_hmc_vault.yaml``

These mock environments can be used to run the end2end tests against, by executing:

.. code-block:: text

    $ make end2end_mocked


.. _`Enabling logging during end2end tests`:

Enabling logging during end2end tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**TODO: At this point, the `setup_logging()` function that enables the logging
described in this section is not used in the end2end tests**

The end2end tests have the ability to log the API calls to the zhmcclient library
and the interactions with the (real or mocked) HMC.

By default, logging is set up such that the zhmcclient library logs messages
with a log level of "warning" or higher, to stderr.

The log level and the components to be logged can be set using the ``ZHMC_LOG``
environment variable:

.. code-block:: text

    $ export ZHMC_LOG=COMP=LEVEL[,COMP=LEVEL[,...]]

Where:

* ``COMP`` is one of: ``all``, ``api``, ``hmc``.
* ``LEVEL`` is one of: ``error``, ``warning``, ``info``, ``debug``.

For example, to enable logging of the zhmcclient API calls and the
interactions with the HMC, use:

.. code-block:: text

    $ export ZHMC_LOG=api=debug,hmc=debug

or, shorter:

.. code-block:: text

    $ export ZHMC_LOG=all=debug


.. _`HMC inventory file`:

HMC inventory file
^^^^^^^^^^^^^^^^^^

The HMC inventory file specifies HMCs and/or groups of HMCs to be used for any
code that uses the :mod:`zhmcclient.testutils` module, such as the end2end tests,
the `example scripts`_, other zhmcclient projects, or even projects by users of
the zhmcclient library.

.. _example scripts: https://github.com/zhmcclient/python-zhmcclient/tree/master/examples

The HMCs and HMC groups defined in the HMC inventory file have nicknames and
the nickname to be used for end2end tests and the example scripts can be
specified using the ``TESTHMC`` environment variable, for example:

.. code-block:: bash

    $ TESTHMC=HMC1 make end2end             # run end2end tests against nickname "HMC1"

    $ TESTHMC=HMC1 examples/list_cpcs.py    # run this example script against nickname "HMC1"

If no nickname is specified using the ``TESTHMC`` environment variable, the
nickname "default" is used, for example:

.. code-block:: bash

    $ make end2end             # run end2end tests against nickname "default""

    $ examples/list_cpcs.py    # run this example script against nickname "default""

By default, the HMC inventory file ``~/.zhmc_inventory.yaml`` is used.
A different path name can be specified with the ``TESTINVENTORY`` environment
variable.

The following describes the structure of the HMC inventory file:

.. code-block:: yaml

    all:                                # Nickname of the top-level HMC group; must be 'all'.

      hosts:                            # Definition of all HMCs, each with an item as follows:

        <hmc_nick>:                     # Nickname of an HMC; may be a DNS hostname, IP address,
                                        #   or arbitrary string.

          description: <string>         # Optional: One line description of the HMC.

          contact: <string>             # Optional: Informal reference to a contact for the HMC.

          access_via: <string>          # Optional: Reminder on network setup needed for access.

          ansible_host: <host>          # If real HMC: DNS hostname or IP address of HMC, if
                                        #   arbitrary string was used as HMC nickname.
                                        #   This can specify a single HMC or a list of redundant
                                        #   HMCs.

          mock_file: <path_name>        # If mocked HMC: Relative path name of HMC mock file.
          cpcs:                         # CPCs to test against. Can be a subset or all CPCs
                                        #   managed by the HMC.

            <cpc_name>:                 # CPC name.

              dpm_enabled: <bool>       # Whether the CPC is in DPM mode (true) or classic mode
                                        #   (false). This is used to include the CPC in pytest
                                        #   fixtures that select CPCs based on their mode.

              <prop_name>: <prop_value>  # Optional: Additional expected CPC properties, for
                                        #   use by test functions.

          <var_name>: <var_value>       # Optional: Additional variables for this HMC, for use
                                        #   by test functions.

      vars:                             # Optional: Additional variables for all HMCs, for use
                                        #   by test functions.
        <var_name>: <var_value>

      children:                         # Optional: HMC groups.

        <group_nick>:                   # Nickname of this HMC group.

          hosts:                        # The HMCs in this group.

            <hmc_nick>:                 # Reference to an HMC in this group via its nickname.

              ...                       # Optional: Additional variables to override the ones
                                        #   inherited from the parent HMC definition. Not
                                        #   normally needed.

          vars:                         # Optional: Additional variables for the HMCs in this
                                        #   group.
            <var_name>: <var_value>

          children:                     # Optional: Grand child groups. Only ever needed when
            ...                         #   using variable inheritance for some reason.
                                        #   Can be further nested.

Here is the example HMC inventory file
`examples/example_hmc_inventory.yaml <https://github.com/zhmcclient/python-zhmcclient/blob/master/examples/example_hmc_inventory.yaml>`_:

.. literalinclude:: ../examples/example_hmc_inventory.yaml
   :language: yaml

In that example HMC inventory file, the following nicknames of single HMCs are
defined:

* HMC1 - The HMC at 10.11.12.13.
* MOCKED_Z16_CLASSIC - The mocked HMC defined in mock file
  `examples/example_mocked_z16_classic.yaml <https://github.com/zhmcclient/python-zhmcclient/blob/master/examples/example_mocked_z16_classic.yaml>`_.
* MOCKED_Z16_DPM - The mocked HMC defined in mock file
  `examples/example_mocked_z16_dpm.yaml <https://github.com/zhmcclient/python-zhmcclient/blob/master/examples/example_mocked_z16_dpm.yaml>`_.

The following nicknames of HMC groups are defined:

* all - All HMCs, i.e. HMC1, MOCKED_Z16_CLASSIC, and MOCKED_Z16_DPM.
* default - The HMCs with nicknames MOCKED_Z16_CLASSIC and MOCKED_Z16_DPM.
* dev - The HMC with nickname HMC1.

The tests that use CPCs or resources within CPCs will be run against
only the subset of CPCs that are defined in the ``cpcs`` variables of the HMC
entries. In that example HMC inventory file, those are:

* For HMC1: Only the CPCs XYZ1 and XYZ2.
* For MOCKED_Z16_CLASSIC: Only the CPC CPC1.
* For MOCKED_Z16_DPM: Only the CPC CPC1.

Any variables defined for the HMCs are available to the test functions via an
:class:`~zhmcclient.testutils.HMCDefinition` object. See pytest fixture
:func:`~zhmcclient.testutils.hmc_session` for details.

The format of HMC inventory files is compatible with the format of Ansible
inventory files in YAML format, with the following extensions:

* Certain variables in the definition of HMC hosts have a defined meaning. See
  the format description above for details.

and the following limitations:

* DNS host names or IP addresses with ranges (e.g. ``myhost[0:9].xyz.com``)
  are not supported.

For more details on the format of Ansible inventory files, see
`Ansible: How to build your inventory <https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html>`_.


.. _`HMC vault file`:

HMC vault file
^^^^^^^^^^^^^^

The HMC vault file specifies credentials for real HMCs to be used for any
code that uses the :mod:`zhmcclient.testutils` module, such as the end2end tests,
the `example scripts`_, other zhmcclient projects, or even projects by users of
the zhmcclient library.

It is required to have the HMC credentials in the HMC vault file; they cannot
be specified in the HMC inventory file.

By default, the HMC vault file ``~/.zhmc_vault.yaml`` is used.
A different path name can be specified with the ``TESTVAULT`` environment
variable.

The data items for HMCs in the HMC vault file are looked up using the HMC
names from the HMC inventory file, so they must match.

The following describes the structure of the HMC vault file:

.. code-block:: yaml

    hmc_auth:

      <hmc_nick>:                     # Nickname of an HMC defined in the inventory file

        userid: <string>              # HMC userid

        password: <string>            # HMC password

        verify: <bool>                # Indicates whether the server certificate returned
                                      #   by the HMC should be validated.

        ca_certs: <ca_certs>          # Used for verify_cert init parm of zhmcclient.Session

    <var_name>: <var_value>           # Any other variables are allowed but will be ignored

For details about ``<ca_certs>``, see the description of the ``verify_cert``
init parameter of the :class:`zhmcclient.Session` class.

Here is the example HMC vault file
`examples/example_hmc_vault.yaml <https://github.com/zhmcclient/python-zhmcclient/blob/master/examples/example_hmc_vault.yaml>`_:

.. literalinclude:: ../examples/example_hmc_vault.yaml
   :language: yaml

The format of HMC vault files is compatible with the format of Ansible vault
files in YAML format, with the following limitations:

* In the current release, HMC vault files cannot be encrypted. To mitigate that,
  set restrictive file permissions on the HMC vault files.


.. _`Developing tests`:

Developing tests
----------------

The :mod:`zhmcclient.testutils` module provides support for developing tests
that run against real HMCs or mocked HMCs defined with the :ref:`mock support`.

These HMCs are defined in an :ref:`HMC inventory file`, and their credentials
are defined in an :ref:`HMC vault file`.


zhmcclient.testutils module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: zhmcclient.testutils

This module defines
`pytest fixtures <https://docs.pytest.org/en/latest/explanation/fixtures.html>`_
for use by the test functions and encapsulates the access to the HMC inventory
and vault files.

Look at the existing test functions in
https://github.com/zhmcclient/python-zhmcclient/tree/master/tests for real-life
examples.


Pytest fixtures
^^^^^^^^^^^^^^^

Pytest fixtures are used as parameters of test functions. When used, they are
specified just with their name. Pytest resolves the parameters of test
functions to its known fixtures, based upon the parameter name.
For more details on pytest fixtures in general, see
`pytest fixtures <https://docs.pytest.org/en/latest/explanation/fixtures.html>`_.

The :mod:`zhmcclient.testutils` module provides the following pytest fixtures:

.. autofunction:: zhmcclient.testutils.hmc_definition

.. autofunction:: zhmcclient.testutils.hmc_session

.. autofunction:: zhmcclient.testutils.all_cpcs

.. autofunction:: zhmcclient.testutils.dpm_mode_cpcs

.. autofunction:: zhmcclient.testutils.classic_mode_cpcs

Encapsulation of HMC inventory file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :mod:`zhmcclient.testutils` module provides the following elements to
encapsulate access to the :ref:`HMC inventory file`, e.g. by test functions:

.. autofunction:: zhmcclient.testutils.hmc_definitions

.. autofunction:: zhmcclient.testutils.print_hmc_definitions

.. autoclass:: zhmcclient.testutils.HMCDefinitions
   :members:
   :autosummary:
   :special-members: __repr__

.. autoclass:: zhmcclient.testutils.HMCDefinition
   :members:
   :autosummary:
   :special-members: __repr__

.. autoclass:: zhmcclient.testutils.HMCInventoryFile
   :members:
   :autosummary:

Encapsulation of HMC vault file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :mod:`zhmcclient.testutils` module provides the following elements to
encapsulate access to the :ref:`HMC vault file`, e.g. by test functions:

.. autoclass:: zhmcclient.testutils.HMCVaultFile
   :members:
   :autosummary:

Exceptions
^^^^^^^^^^

The :mod:`zhmcclient.testutils` module may raise the following exceptions:

.. autoclass:: zhmcclient.testutils.HMCInventoryFileError
   :members:
   :autosummary:

.. autoclass:: zhmcclient.testutils.HMCVaultFileError
   :members:
   :autosummary:

.. autoclass:: zhmcclient.testutils.HMCNoVaultError
   :members:
   :autosummary:

.. autoclass:: zhmcclient.testutils.HMCNotFound
   :members:
   :autosummary:


.. _`Contributing`:

Contributing
------------

Third party contributions to this project are welcome!

In order to contribute, create a `Git pull request`_, considering this:

.. _Git pull request: https://help.github.com/articles/using-pull-requests/

* Test is required.
* Each commit should only contain one "logical" change.
* A "logical" change should be put into one commit, and not split over multiple
  commits.
* Large new features should be split into stages.
* The commit message should not only summarize what you have done, but explain
  why the change is useful.
* The commit message must follow the format explained below.

What comprises a "logical" change is subject to sound judgement. Sometimes, it
makes sense to produce a set of commits for a feature (even if not large).
For example, a first commit may introduce a (presumably) compatible API change
without exploitation of that feature. With only this commit applied, it should
be demonstrable that everything is still working as before. The next commit may
be the exploitation of the feature in other components.

For further discussion of good and bad practices regarding commits, see:

* `OpenStack Git Commit Good Practice`_
* `How to Get Your Change Into the Linux Kernel`_

.. _OpenStack Git Commit Good Practice: https://wiki.openstack.org/wiki/GitCommitMessages
.. _How to Get Your Change Into the Linux Kernel: https://www.kernel.org/doc/Documentation/process/submitting-patches.rst


.. _`Making a change`:

Making a change
---------------

To make a change, create a topic branch. You can assume that you are the only
one using that branch, so force-pushes to that branch and rebasing that branch
is fine.

When you are ready to push your change, describe the change for users of the
package in a change fragment file. To create a change fragment file, execute:

For changes that have a corresponding issue:

.. code-block:: sh

    towncrier create <issue>.<type>.rst --edit

For changes that have no corresponding issue:

.. code-block:: sh

    towncrier create noissue.<number>.<type>.rst --edit

For changes where you do not want to create or modify a change log entry,
simply don't provide a change fragment file.

where:

* ``<issue>`` - The issue number of the issue that is addressed by the change.
  If the change addresses more than one issue, copy the new change fragment file
  after its content has been edited, using the other issue number in the file
  name. It is important that the file content is exactly the same, so that
  towncrier can create a single change log entry from the two (or more) files.

  If the change has no related issue, use the ``noissue.<number>.<type>.rst``
  file name format, where ``<number>`` is any number that results in a file name
  that does not yet exist in the ``changes`` directory.

* ``<type>`` - The type of the change, using one of the following values:

  - ``incompatible`` - An incompatible change. This will show up in the
    "Incompatible Changes" section of the change log. The text should include
    a description of the incompatibility from a user perspective and if
    possible, how to mitigate the change or what replacement functionality
    can be used instead.

  - ``deprecation`` - An externally visible functionality is being deprecated
    in this release.
    This will show up in the "Deprecations" section of the change log.
    The deprecated functionality still works in this release, but may go away
    in a future release. If there is a replacement functionality, the text
    should mention it.

  - ``fix`` - A bug fix in the code, documentation or development environment.
    This will show up in the "Bug fixes" section of the change log.

  - ``feature`` - A feature or enhancement in the code, documentation or
    development environment.
    This will show up in the "Enhancements" section of the change log.

  - ``cleanup`` - A cleanup in the code, documentation or development
    environment, that does not fix a bug and is not an enhanced functionality.
    This will show up in the "Cleanup" section of the change log.

This command will create a new change fragment file in the ``changes``
directory and will bring up your editor (usually vim).

If your change does multiple things of different types listed above, create
a separate change fragment file for each type.

If you need to modify an existing change log entry as part of your change,
edit the existing corresponding change fragment file.

Add the new or changed change fragment file(s) to your commit. The test
workflow running on your Pull Request will check whether your change adds or
modifies change fragment files.

You can review how your changes will show up in the final change log for
the upcoming release by running:

.. code-block:: sh

    towncrier build --draft

Always make sure that your pushed branch has either just one commit, or if you
do multiple things, one commit for each logical change. What is not OK is to
keep the possibly multiple commits it took you to get to the final result for
the change.


.. _`Format of commit messages`:

Format of commit messages
-------------------------

A commit message must start with a short summary line, followed by a blank
line.

Optionally, the summary line may start with an identifier that helps
identifying the type of change or the component that is affected, followed by
a colon.

It can include a more detailed description after the summary line. This is
where you explain why the change was done, and summarize what was done.

It must end with the DCO (Developer Certificate of Origin) sign-off line in the
format shown in the example below, using your name and a valid email address of
yours. The DCO sign-off line certifies that you followed the rules stated in
`DCO 1.1`_. In short, you certify that you wrote the patch or otherwise have
the right to pass it on as an open-source patch.

.. _DCO 1.1: https://raw.githubusercontent.com/zhmcclient/python-zhmcclient/master/DCO1.1.txt

We use `GitCop`_ during creation of a pull request to check whether the commit
messages in the pull request comply to this format.
If the commit messages do not comply, GitCop will add a comment to the pull
request with a description of what was wrong.

.. _GitCop: http://gitcop.com/

Example commit message:

.. code-block:: text

    cookies: Add support for delivering cookies

    Cookies are important for many people. This change adds a pluggable API for
    delivering cookies to the user, and provides a default implementation.

    Signed-off-by: Random J Developer <random@developer.org>

Use ``git commit --amend`` to edit the commit message, if you need to.

Use the ``--signoff`` (``-s``) option of ``git commit`` to append a sign-off
line to the commit message with your name and email as known by Git.

If you like filling out the commit message in an editor instead of using
the ``-m`` option of ``git commit``, you can automate the presence of the
sign-off line by using a commit template file:

* Create a file outside of the repo (say, ``~/.git-signoff.template``)
  that contains, for example:

  .. code-block:: text

      <one-line subject>

      <detailed description>

      Signed-off-by: Random J Developer <random@developer.org>

* Configure Git to use that file as a commit template for your repo:

  .. code-block:: text

      git config commit.template ~/.git-signoff.template


.. _`Releasing a version`:

Releasing a version
-------------------

This section shows the steps for releasing a version to `PyPI
<https://pypi.python.org/>`_.

It covers all variants of versions that can be released:

* Releasing a new major version (Mnew.0.0) based on the master branch
* Releasing a new minor version (M.Nnew.0) based on the master branch or based
  on an earlier stable branch
* Releasing a new update version (M.N.Unew) based on the stable branch of its
  minor version

This description assumes that you are authorized to push to the remote repo
at https://github.com/zhmcclient/python-zhmcclient and that the remote repo
has the remote name ``origin`` in your local clone.

Any commands in the following steps are executed in the main directory of your
local clone of the python-zhmcclient Git repo.

1.  On GitHub, verify open items in milestone ``M.N.U``.

    Verify that milestone ``M.N.U`` has no open issues or PRs anymore. If there
    are open PRs or open issues, make a decision for each of those whether or
    not it should go into version ``M.N.U`` you are about to release.

    If there are open issues or PRs that should go into this version, abandon
    the release process.

    If none of the open issues or PRs should go into this version, change their
    milestones to a future version, and proceed with the release process. You
    may need to create the milestone for the future version.

2.  Run the Safety tool:

    .. code-block:: sh

        make safety

    If any of the two safety runs fails, fix the safety issues that are reported,
    in a separate branch/PR.

    Roll back the PR into any maintained stable branches.

3.  Check for any
    `dependabot alerts <https://github.com/zhmcclient/python-zhmcclient/security/dependabot>`_.

    If there are any dependabot alerts, fix them in a separate branch/PR.

    Roll back the PR into any maintained stable branches.

4.  Create and push the release branch (replace M,N,U accordingly):

    .. code-block:: sh

        VERSION=M.N.U make release_branch

    This uses the default branch determined from ``VERSION``: For ``M.N.0``,
    the ``master`` branch is used, otherwise the ``stable_M.N`` branch is used.
    That covers for all cases except if you want to release a new minor version
    based on an earlier stable branch. In that case, you need to specify that
    branch:

    .. code-block:: sh

        VERSION=M.N.0 BRANCH=stable_M.N make release_branch

    This includes the following steps:

    * create the release branch (``release_M.N.U``), if not yet existing
    * make sure the AUTHORS.md file is up to date
    * update the change log from the change fragment files, and delete those
    * commit the changes to the release branch
    * push the release branch

    If this command fails, the fix can be committed to the release branch
    and the command above can be retried.

5.  On GitHub, create a Pull Request for the release branch ``release_M.N.U``.

    Important: GitHub uses ``master`` as the default target branch. When
    releasing based on a stable branch, you need to change the target branch
    to the intended ``stable_M.N`` branch.

    Set the milestone of that PR to version ``M.N.U``.

    This PR should normally be set to be reviewed by at least one of the
    maintainers.

    The PR creation will cause the "test" workflow to run. That workflow runs
    tests for all defined environments, since it discovers by the branch name
    that this is a PR for a release.

6.  On GitHub, once the checks for that Pull Request have succeeded, merge the
    Pull Request (no review is needed). This automatically deletes the branch
    on GitHub.

    If the PR did not succeed, fix the issues.

7.  On GitHub, close milestone ``M.N.U``.

    Verify that the milestone has no open items anymore. If it does have open
    items, investigate why and fix (probably step 1 was not performed).

8.  Publish the package (replace M,N,U accordingly):

    .. code-block:: sh

        VERSION=M.N.U make release_publish

    or (see step 4):

    .. code-block:: sh

        VERSION=M.N.0 BRANCH=stable_M.N make release_publish

    This includes the following steps:

    * create and push the release tag
    * clean up the release branch

    Pushing the release tag will cause the "publish" workflow to run. That workflow
    builds the package, publishes it on PyPI, creates a release for it on
    GitHub, and finally creates a new stable branch on GitHub if the master
    branch was released.

9.  Verify the publishing

    Wait for the "publish" workflow for the new release to have completed:
    https://github.com/zhmcclient/python-zhmcclient/actions/workflows/publish.yml

    Then, perform the following verifications:

    * Verify that the new version is available on PyPI at
      https://pypi.python.org/pypi/zhmcclient/

    * Verify that the new version has a release on GitHub at
      https://github.com/zhmcclient/python-zhmcclient/releases

    * Verify that the new version shows up in the version list when clicking
      on "v:master" at the bottom of the left hand pane at
      https://python-zhmcclient.readthedocs.io/. You may need to reload the
      page, or click on a different version, or restart your browser to get it
      updated, and ReadTheDocs first needs to finish its build for that to work.

      If the new version does not show up after some time, go to
      https://readthedocs.org/projects/python-zhmcclient/builds/ to see whether
      the new version was built, and if so, whether there was a build problem.

      If the new version was not built at all, log on to
      https://readthedocs.org/ and go to
      https://readthedocs.org/projects/python-zhmcclient/versions/
      and edit the new version and set it to "active" (normally, that is done
      automatically by ReadTheDocs for new tags).

10. Hide previous fix version on ReadTheDocs

    When releasing a fix version != 0 (e.g. M.N.1), log on to
    https://readthedocs.org/ and go to
    https://readthedocs.org/projects/python-zhmcclient/versions/ and
    edit the previous fix version (i.e. ``M.N.U-1``) and set it to "hidden"
    (it remains active). Hiding it causes it to be removed from the version
    list shown when clicking on "v:master" at
    https://python-zhmcclient.readthedocs.io/. Keeping it active will
    ensure that any links to that version that were obtained earlier, still
    work.


.. _`Starting a new version`:

Starting a new version
----------------------

This section shows the steps for starting development of a new version.

This section covers all variants of new versions:

* Starting a new major version (Mnew.0.0) based on the master branch
* Starting a new minor version (M.Nnew.0) based on the master branch or based
  on an earlier stable branch
* Starting a new update version (M.N.Unew) based on the stable branch of its
  minor version

This description assumes that you are authorized to push to the remote repo
at https://github.com/zhmcclient/python-zhmcclient and that the remote repo
has the remote name ``origin`` in your local clone.

Any commands in the following steps are executed in the main directory of your
local clone of the python-zhmcclient Git repo.

1.  Create and push the start branch (replace M,N,U accordingly):

    .. code-block:: sh

        VERSION=M.N.U make start_branch

    This uses the default branch determined from ``VERSION``: For ``M.N.0``,
    the ``master`` branch is used, otherwise the ``stable_M.N`` branch is used.
    That covers for all cases except if you want to start a new minor version
    based on an earlier stable branch. In that case, you need to specify that
    branch:

    .. code-block:: sh

        VERSION=M.N.0 BRANCH=stable_M.N make start_branch

    This includes the following steps:

    * create the start branch (``start_M.N.U``), if not yet existing
    * create a dummy change
    * commit and push the start branch (``start_M.N.U``)

2.  On GitHub, create a milestone for the new version ``M.N.U``.

    You can create a milestone in GitHub via Issues -> Milestones -> New
    Milestone.

3.  On GitHub, create a Pull Request for the start branch ``start_M.N.U``.

    Important: GitHub uses ``master`` as the default target branch. When
    releasing based on a stable branch, you need to change the target branch
    to the intended ``stable_M.N`` branch.

    No review is needed for this PR.

    Set the milestone of that PR to the new version ``M.N.U``.

4.  On GitHub, go through all open issues and pull requests that still have
    milestones for previous releases set, and either set them to the new
    milestone, or to have no milestone.

    Note that when the release process has been performed as described, there
    should not be any such issues or pull requests anymore. So this step here
    is just an additional safeguard.

5.  On GitHub, once the checks for the Pull Request for branch ``start_M.N.U``
    have succeeded, merge the Pull Request (no review is needed). This
    automatically deletes the branch on GitHub.

6.  Update and clean up the local repo (replace M,N,U accordingly):

    .. code-block:: sh

        VERSION=M.N.U make start_tag

    or (see step 1):

    .. code-block:: sh

        VERSION=M.N.0 BRANCH=stable_M.N make start_tag

    This includes the following steps:

    * checkout and pull the branch that was started (``master`` or ``stable_M.N``)
    * delete the start branch (``start_M.N.U``) locally and remotely
    * create and push the start tag (``M.N.Ua0``)
