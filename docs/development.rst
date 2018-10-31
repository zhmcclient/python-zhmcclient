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

To run unit tests in the currently active Python environment, issue one of
these example variants of ``make test``:

.. code-block:: text

    $ make test                                  # Run all unit tests
    $ TESTCASES=test_resource.py make test       # Run only this test source file
    $ TESTCASES=TestInit make test               # Run only this test class
    $ TESTCASES="TestInit or TestSet" make test  # py.test -k expressions are possible

To run the unit tests and some more commands that verify the project is in good
shape in all supported Python environments, use Tox:

.. code-block:: text

    $ tox                              # Run all tests on all supported Python versions
    $ tox -e py27                      # Run all tests on Python 2.7
    $ tox -e py27 test_resource.py     # Run only this test source file on Python 2.7
    $ tox -e py27 TestInit             # Run only this test class on Python 2.7
    $ tox -e py27 TestInit or TestSet  # py.test -k expressions are possible

The positional arguments of the ``tox`` command are passed to ``py.test`` using
its ``-k`` option. Invoke ``py.test --help`` for details on the expression
syntax of its ``-k`` option.

Running function tests against a real HMC and CPC
-------------------------------------------------

The function tests (in ``tests/function/test_*.py``) can be run against a
faked HMC/CPC (using the zhmcclient mock support), or against a real HMC/CPC.

By default, the function tests are run against the faked HMC/CPC. To run them
against a real HMC/CPC, you must:

* Specify the name of the target CPC in the ``ZHMC_TEST_CPC`` environment
  variable. This environment variable is the control point that decides
  between using a real HMC/CPC and using the faked environment::

      export ZHMC_TEST_CPC=S67B

* Have an HMC credentials file at location ``examples/hmccreds.yaml`` that
  specifies the target CPC (among possibly further CPCs) in its ``cpcs`` item::

      cpcs:

        S67B:
          description: "z13s in DPM mode"
          contact: "Joe"
          hmc_host: "10.11.12.13"
          hmc_userid: myuserid
          hmc_password: mypassword

        # ... more CPCs

There is an example HMC credentials file in the repo, at
``examples/example_hmccreds.yaml``. For a description of its format, see
`Format of the HMC credentials file`_.

Enabling logging for function tests
-----------------------------------

The function tests always log to stderr. What can be logged are the
following two components:

* ``api``: Calls to and returns from zhmcclient API functions (at debug level).
* ``hmc``: Interactions with the HMC (i.e. HTTP requests and responses, at
  debug level).

By default, the log component and level is set to::

    all=warning

meaning that all components log at warning level or higher.

To set different log levels for the log components, set the ``ZHMC_LOG``
environment variable as follows::

    export ZHMC_LOG=COMP=LEVEL[,COMP=LEVEL[,...]]

Where:

* ``COMP`` is one of: ``all``, ``api``, ``hmc``.
* ``LEVEL`` is one of: ``error``, ``warning``, ``info``, ``debug``.

For example, to enable logging of the zhmcclient API calls and the
interactions with the HMC, use::

    export ZHMC_LOG=api=debug,hmc=debug

or, shorter::

    export ZHMC_LOG=all=debug

Format of the HMC credentials file
----------------------------------

The HMC credentials file is used for specifying real HMCs/CPCs to be used by
function tests. Its syntax is YAML, and the ``cpcs`` item relevant for function
testing has the following structure::

    cpcs:

      "CPC1":
        description: "z13 test system"
        contact: "Amy"
        hmc_host: "10.10.10.11"           # required
        hmc_userid: "myuser1"             # required
        hmc_password: "mypassword1"       # required

      "CPC2":
        description: "z14 development system"
        contact: "Bob"
        hmc_host: "10.10.10.12"
        hmc_userid: "myuser2"
        hmc_password: "mypassword2"

In the example above, any words in double quotes are data and can change,
and any words without double quotes are considered keywords and must be
specified as shown.

"CPC1" and "CPC2" are CPC names that are used to select an entry in the
file. The entry for a CPC contains data about the HMC managing that CPC,
with its host, userid and password. If two CPCs are managed by the same
HMC, there would be two CPC entries with the same HMC data.


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

* Releasing the master branch as a new major or minor version (M+1.0.0 or M.N+1.0)
* Releasing a stable branch as a new update (= fix) version (M.N.U+1)

This description assumes that you are authorized to push to the upstream repo
at https://github.com/zhmcclient/python-zhmcclient and that the upstream repo
has the remote name ``origin`` in your local clone.

1.  Switch to your work directory of your local clone of the python-zhmcclient Git
    repo and perform the following steps in that directory.

2.  Set shell variables for the version and branch to be released:

    * ``MNU`` - Full version number M.N.U this release should have
    * ``MN`` - Major and minor version numbers M.N of that full version
    * ``BRANCH`` - Name of the branch to be released

    When releasing the master branch as a new major or minor version (e.g. ``0.19.0``):

    .. code-block:: text

        MNU=0.19.0
        MN=0.19
        BRANCH=master

    When releasing a stable branch as a new update (=fix) version (e.g. ``0.18.1``):

    .. code-block:: text

        MNU=0.18.1
        MN=0.18
        BRANCH=stable_$MN

3.  Check out the branch to be released, make sure it is up to date with upstream, and
    create a topic branch for the version to be released:

    .. code-block:: text

        git status  # Double check the work directory is clean
        git checkout $BRANCH
        git pull
        git checkout -b release_$MNU

4.  Edit the change log:

    .. code-block:: text

        vi docs/changes.rst

    and make the following changes in the section of the version to be released:

    * Finalize the version to the version to be released.
    * Remove the statement that the version is in development.
    * Change the release date to today´s date.
    * Make sure that all changes are described.
    * Make sure the items shown in the change log are relevant for and understandable
      by users.
    * In the "Known issues" list item, remove the link to the issue tracker and add
      text for any known issues you want users to know about.
    * Remove all empty list items in that section.

5.  Commit your changes and push them upstream:

    .. code-block:: text

        git add docs/changes.rst
        git commit -sm "Release $MNU"
        git push --set-upstream origin release_$MNU

6.  On GitHub, create a Pull Request for branch ``release_$MNU``. This will trigger the
    CI runs in Travis and Appveyor.

    Important: When creating Pull Requests, GitHub by default targets the ``master``
    branch. If you are releasing a stable branch, you need to change the target branch
    of the Pull Request to ``stable_M.N``.

7.  On GitHub, close milestone ``M.N.U``.

8.  On GitHub, once the checks for this Pull Request succeed:

    * Merge the Pull Request (no review is needed).

      Because this updates the ``stable_M.N`` branch, it triggers an RTD docs build of
      its stable version. However, because the git tag for this version is not assigned
      yet, this RTD build will show an incorrect version (a dev version based on the
      previous version tag). This will be fixed in a subsequent step.

    * Delete the branch of the Pull Request (``release_M.N.U``)

9.  Checkout the branch you are releasing, update it from upstream, and delete the local
    topic branch you created:

    .. code-block:: text

        git checkout $BRANCH
        git pull
        git branch -d release_$MNU

10. Tag the version:

    Important: This is the basis on which 'pbr' determines the package version. The tag
    string must be exactly the version string ``M.N.U``.

    Create a tag for the new version and push the tag addition upstream:

    .. code-block:: text

        git status    # Double check the branch to be released is checked out
        git tag $MNU
        git push --tags

    The pushing of the tag triggers another RTD docs build of its stable version, this time
    with the correct version as defined in the tag.

    If the previous commands fail because this tag already exists for some reason, delete
    the tag locally and remotely:

    .. code-block:: text

        git tag --delete $MNU
        git push --delete origin $MNU

    and try again.

11. On GitHub, edit the new tag ``M.N.U``, and create a release description on it. This
    will cause it to appear in the Release tab.

    You can see the tags in GitHub via Code -> Releases -> Tags.

12. Do a fresh install of this version in your active Python environment. This ensures
    that 'pbr' determines the correct version. Otherwise, it may determine some development
    version.

    .. code-block:: text

        # workon zhmc... # make sure your virtual environment is active
        make clobber install
        make help    # Double check that it shows version ``M.N.U``

13. Upload the package to PyPI:

    .. code-block:: text

        make upload

    This will show the package version and will ask for confirmation.

    **Important:** Double check that the correct package version (``M.N.U``,
    without any development suffix) is shown.

    **Attention!!** This only works once for each version. You cannot
    re-release the same version to PyPI, or otherwise update it.

    Verify that the released version arrived on PyPI:
    https://pypi.python.org/pypi/zhmcclient/

14. On RTD, verify that it shows the correct version for its stable version:

    RTD stable version: https://python-zhmcclient.readthedocs.io/en/stable.

    If it does not, trigger a build of RTD version "stable" on the RTD project
    page:

    RTD build page: https://readthedocs.org/projects/python-zhmcclient/builds/

    Once that build is complete, verify again.

15. If you released the master branch, it needs a new fix stream.

    Create a branch for its fix stream and push it upstream:

    .. code-block:: text

        git status    # Double check the branch to be released is checked out
        git checkout -b stable_$MN
        git push --set-upstream origin stable_$MN

    Log on to the
    `RTD project python-zhmcclient <https://readthedocs.org/projects/python-zhmcclient/versions>`_
    and activate the new version (=branch) ``stable_M.N`` as a version to be
    built.

16. If you released the master branch, a new version should be started
    as described in :ref:`starting a new version`.

    This may be a new minor version on the same major version, or a new
    major version.


.. _`Starting a new version`:

Starting a new version
----------------------

This section shows the steps for starting development of a new version.

These steps may be performed right after the steps for
:ref:`releasing a version`, or independently.

This section covers all variants of new versions:

* A new major or minor version for new development based upon the master branch.
* A new update (=fix) version based on a stable branch.

This description assumes that you are authorized to push to the upstream repo
at https://github.com/zhmcclient/python-zhmcclient and that the upstream repo
has the remote name ``origin`` in your local clone.

1.  Switch to your work directory of your local clone of the python-zhmcclient Git
    repo and perform the following steps in that directory.

2.  Set shell variables for the version to be started and its base branch:

    * ``MNU`` - Full version number M.N.U of the new version to be started
    * ``MN`` - Major and minor version numbers M.N of that full version
    * ``BRANCH`` - Name of the branch the new version is based upon

    When starting a (major or minor) version (e.g. ``0.20.0``) based on the master branch:

    .. code-block:: text

        MNU=0.20.0
        MN=0.20
        BRANCH=master

    When starting an update (=fix) version (e.g. ``0.19.1``) based on a stable branch:

    .. code-block:: text

        MNU=0.19.1
        MN=0.19
        BRANCH=stable_$MN

3.  Check out the branch the new version is based on, make sure it is up to
    date with upstream, and create a topic branch for the new version:

    .. code-block:: text

        git status  # Double check the work directory is clean
        git checkout $BRANCH
        git pull
        git checkout -b start_$MNU

4.  Edit the change log:

    .. code-block:: text

        vi docs/changes.rst

    and insert the following section before the top-most section:

    .. code-block:: text

        Version 0.19.0
        ^^^^^^^^^^^^^^

        Released: not yet

        **Incompatible changes:**

        **Deprecations:**

        **Bug fixes:**

        **Enhancements:**

        **Known issues:**

        * See `list of open issues`_.

        .. _`list of open issues`: https://github.com/zhmcclient/python-zhmcclient/issues

5.  Commit your changes and push them upstream:

    .. code-block:: text

        git add docs/changes.rst
        git commit -sm "Start $MNU"
        git push --set-upstream origin start_$MNU

6.  On GitHub, create a Pull Request for branch ``start_M.N.U``.

    Important: When creating Pull Requests, GitHub by default targets the ``master``
    branch. If you are starting based on a stable branch, you need to change the
    target branch of the Pull Request to ``stable_M.N``.

7.  On GitHub, create a milestone for the new version ``M.N.U``.

    You can create a milestone in GitHub via Issues -> Milestones -> New
    Milestone.

8.  On GitHub, go through all open issues and pull requests that still have
    milestones for previous releases set, and either set them to the new
    milestone, or to have no milestone.

9.  On GitHub, once the checks for this Pull Request succeed:

    * Merge the Pull Request (no review is needed)
    * Delete the branch of the Pull Request (``start_M.N.U``)

10. Checkout the branch the new version is based on, update it from upstream, and
    delete the local topic branch you created:

    .. code-block:: text

        git checkout $BRANCH
        git pull
        git branch -d start_$MNU
