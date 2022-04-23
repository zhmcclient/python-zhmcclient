.. Copyright 2016-2021 IBM Corp. All Rights Reserved.
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
    $ tox -e py27                      # Run all tests on Python 2.7
    $ tox -e py27 test_resource.py     # Run only this test source file on Python 2.7
    $ tox -e py27 TestInit             # Run only this test class on Python 2.7
    $ tox -e py27 TestInit or TestSet  # pytest -k expressions are possible


.. _`Running end2end tests`:

Running end2end tests
^^^^^^^^^^^^^^^^^^^^^

Prepare an :ref:`HMC definition file` that defines real and/or mocked HMCs the tests
should be run against.
The HMC definition file can be created from this
`example HMC definition file <https://github.com/zhmcclient/python-zhmcclient/blob/master/tests/example_hmc_definitions.yaml>`_.
Its format is described in the comment header of the example file.

To run the end2end tests in the currently active Python environment, issue:

.. code-block:: text

    $ make end2end

By default, the HMC definition file named ``.zhmc_hmc_definitions.yaml`` in
the home directory of the current user is used. A different path name can
be specified with the ``TESTHMCFILE`` environment variable.

By default, the tests are run against the nickname ``default`` in the HMC
definition file, which can be used for a single HMC or a group. A different
nickname can be specified with the ``TESTHMC`` environment variable.

For example:

.. code-block:: text

    $ TESTHMCFILE=`./hmcs.yaml` make end2end  # Run against 'default' in the specified file
    $ TESTHMC=`HMC1` make end2end             # Run against 'HMC1' in default file


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


.. _`HMC definition file`:

HMC definition file
^^^^^^^^^^^^^^^^^^^

The HMC definition file specifies HMCs and/or groups of HMCs to run the end2end
tests against.

Its format is described in the comment header of the
`example HMC definition file <https://github.com/zhmcclient/python-zhmcclient/blob/master/tests/example_hmc_definitions.yaml>`_.


.. _`zhmcclient.testutils module`:

zhmcclient.testutils module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :mod:`zhmcclient.testutils` module provides support for running tests against
real or mocked HMCs defined in a :ref:`HMC definition file`.

It defines
`pytest fixtures <https://docs.pytest.org/en/latest/explanation/fixtures.html>`_
and encapsulates the access to the HMC definition file.

.. autofunction:: zhmcclient.testutils.hmc_definition

.. autofunction:: zhmcclient.testutils.hmc_session

.. autofunction:: zhmcclient.testutils.one_cpc

.. autofunction:: zhmcclient.testutils.all_cpcs

.. autofunction:: zhmcclient.testutils.dpm_mode_cpcs

.. autofunction:: zhmcclient.testutils.classic_mode_cpcs

.. autofunction:: zhmcclient.testutils.hmc_definition_file

.. autofunction:: zhmcclient.testutils.hmc_definitions

.. autoclass:: zhmcclient.testutils.HMCDefinition
   :members:
   :autosummary:
   :special-members: __repr__

.. autoclass:: zhmcclient.testutils.HMCDefinitionFile
   :members:
   :autosummary:

.. autoclass:: zhmcclient.testutils.HMCDefinitionFileError
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
* Releasing a new minor version (M.Nnew.0) based on the master branch
* Releasing a new update version (M.N.Unew) based on the stable branch of its
  minor version

This description assumes that you are authorized to push to the remote repo
at https://github.com/zhmcclient/python-zhmcclient and that the remote repo
has the remote name ``origin`` in your local clone.

Any commands in the following steps are executed in the main directory of your
local clone of the python-zhmcclient Git repo.

1.  Set shell variables for the version that is being released and the branch
    it is based on:

    * ``MNU`` - Full version M.N.U that is being released
    * ``MN`` - Major and minor version M.N of that full version
    * ``BRANCH`` - Name of the branch the version that is being released is
      based on

    When releasing a new major version (e.g. ``1.0.0``) based on the master
    branch:

    .. code-block:: sh

        MNU=1.0.0
        MN=1.0
        BRANCH=master

    When releasing a new minor version (e.g. ``0.9.0``) based on the master
    branch:

    .. code-block:: sh

        MNU=0.9.0
        MN=0.9
        BRANCH=master

    When releasing a new update version (e.g. ``0.8.1``) based on the stable
    branch of its minor version:

    .. code-block:: sh

        MNU=0.8.1
        MN=0.8
        BRANCH=stable_${MN}

2.  Create a topic branch for the version that is being released:

    .. code-block:: sh

        git checkout ${BRANCH}
        git pull
        git checkout -b release_${MNU}

3.  Edit the version file:

    .. code-block:: sh

        vi zhmcclient/_version.py

    and set the ``__version__`` variable to the version that is being released:

    .. code-block:: python

        __version__ = 'M.N.U'

4.  Edit the change log:

    .. code-block:: sh

        vi docs/changes.rst

    and make the following changes in the section of the version that is being
    released:

    * Finalize the version.
    * Change the release date to today's date.
    * Make sure that all changes are described.
    * Make sure the items shown in the change log are relevant for and
      understandable by users.
    * In the "Known issues" list item, remove the link to the issue tracker and
      add text for any known issues you want users to know about.
    * Remove all empty list items.

5.  When releasing based on the master branch, edit the GitHub workflow file
    ``test.yml``:

    .. code-block:: sh

        vi .github/workflows/test.yml

    and in the ``on`` section, increase the version of the ``stable_*`` branch
    to the new stable branch ``stable_M.N`` created earlier:

    .. code-block:: yaml

        on:
          schedule:
            . . .
          push:
            branches: [ master, stable_M.N ]
          pull_request:
            branches: [ master, stable_M.N ]

6.  Commit your changes and push the topic branch to the remote repo:

    .. code-block:: sh

        git status  # Double check the changed files
        git commit -asm "Release ${MNU}"
        git push --set-upstream origin release_${MNU}

7.  On GitHub, create a Pull Request for branch ``release_M.N.U``. This will
    trigger the CI runs.

    Important: When creating Pull Requests, GitHub by default targets the
    ``master`` branch. When releasing based on a stable branch, you need to
    change the target branch of the Pull Request to ``stable_M.N``.

8.  On GitHub, close milestone ``M.N.U``.

9.  On GitHub, once the checks for the Pull Request for branch ``start_M.N.U``
    have succeeded, merge the Pull Request (no review is needed). This
    automatically deletes the branch on GitHub.

10. Add a new tag for the version that is being released and push it to
    the remote repo. Clean up the local repo:

    .. code-block:: sh

        git checkout ${BRANCH}
        git pull
        git tag -f ${MNU}
        git push -f --tags
        git branch -D release_${MNU}
        git branch -D -r origin/release_${MNU}

11. When releasing based on the master branch, create and push a new stable
    branch for the same minor version:

    .. code-block:: sh

        git checkout -b stable_${MN}
        git push --set-upstream origin stable_${MN}
        git checkout ${BRANCH}

    Note that no GitHub Pull Request is created for any ``stable_*`` branch.

12. On GitHub, edit the new tag ``M.N.U``, and create a release description on
    it. This will cause it to appear in the Release tab.

    You can see the tags in GitHub via Code -> Releases -> Tags.

13. On ReadTheDocs, activate the new version ``M.N.U``:

    * Go to https://readthedocs.org/projects/python-zhmcclient/versions/
      and log in.

    * Activate the new version ``M.N.U`` (it should be automatically active)

      This triggers a build of that version. Verify that the build succeeds
      and that new version is shown in the version selection popup at
      https://python-zhmcclient.readthedocs.io/

14. Upload the package to PyPI:

    .. code-block:: sh

        make upload

    This will show the package version and will ask for confirmation.

    **Attention!** This only works once for each version. You cannot release
    the same version twice to PyPI.

    Verify that the released version arrived on PyPI at
    https://pypi.python.org/pypi/zhmcclient/


.. _`Starting a new version`:

Starting a new version
----------------------

This section shows the steps for starting development of a new version.

This section covers all variants of new versions:

* Starting a new major version (Mnew.0.0) based on the master branch
* Starting a new minor version (M.Nnew.0) based on the master branch
* Starting a new update version (M.N.Unew) based on the stable branch of its
  minor version

This description assumes that you are authorized to push to the remote repo
at https://github.com/zhmcclient/python-zhmcclient and that the remote repo
has the remote name ``origin`` in your local clone.

Any commands in the following steps are executed in the main directory of your
local clone of the python-zhmcclient Git repo.

1.  Set shell variables for the version that is being started and the branch it
    is based on:

    * ``MNU`` - Full version M.N.U that is being started
    * ``MN`` - Major and minor version M.N of that full version
    * ``BRANCH`` -  Name of the branch the version that is being started is
      based on

    When starting a new major version (e.g. ``1.0.0``) based on the master
    branch:

    .. code-block:: sh

        MNU=1.0.0
        MN=1.0
        BRANCH=master

    When starting a new minor version (e.g. ``0.9.0``) based on the master
    branch:

    .. code-block:: sh

        MNU=0.9.0
        MN=0.9
        BRANCH=master

    When starting a new minor version (e.g. ``0.8.1``) based on the stable
    branch of its minor version:

    .. code-block:: sh

        MNU=0.8.1
        MN=0.8
        BRANCH=stable_${MN}

2.  Create a topic branch for the version that is being started:

    .. code-block:: sh

        git checkout ${BRANCH}
        git pull
        git checkout -b start_${MNU}

3.  Edit the version file:

    .. code-block:: sh

        vi zhmcclient/_version.py

    and update the version to a draft version of the version that is being
    started:

    .. code-block:: python

        __version__ = 'M.N.U.dev1'

4.  Edit the change log:

    .. code-block:: sh

        vi docs/changes.rst

    and insert the following section before the top-most section:

    .. code-block:: rst

        Version M.N.U.dev1
        ^^^^^^^^^^^^^^^^^^

        This version contains all fixes up to version M.N-1.x.

        Released: not yet

        **Incompatible changes:**

        **Deprecations:**

        **Bug fixes:**

        **Enhancements:**

        **Cleanup:**

        **Known issues:**

        * See `list of open issues`_.

        .. _`list of open issues`: https://github.com/zhmcclient/python-zhmcclient/issues

5.  Commit your changes and push them to the remote repo:

    .. code-block:: sh

        git status  # Double check the changed files
        git commit -asm "Start ${MNU}"
        git push --set-upstream origin start_${MNU}

6.  On GitHub, create a Pull Request for branch ``start_M.N.U``.

    Important: When creating Pull Requests, GitHub by default targets the
    ``master`` branch. When starting a version based on a stable branch, you
    need to change the target branch of the Pull Request to ``stable_M.N``.

7.  On GitHub, create a milestone for the new version ``M.N.U``.

    You can create a milestone in GitHub via Issues -> Milestones -> New
    Milestone.

8.  On GitHub, go through all open issues and pull requests that still have
    milestones for previous releases set, and either set them to the new
    milestone, or to have no milestone.

9.  On GitHub, once the checks for the Pull Request for branch ``start_M.N.U``
    have succeeded, merge the Pull Request (no review is needed). This
    automatically deletes the branch on GitHub.

10. Update and clean up the local repo:

    .. code-block:: sh

        git checkout ${BRANCH}
        git pull
        git branch -D start_${MNU}
        git branch -D -r origin/start_${MNU}
