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

Contributing to the zhmcclient project
======================================

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
.. _How to Get Your Change Into the Linux Kernel: https://www.kernel.org/doc/Documentation/SubmittingPatches

The `AUTHORS <AUTHORS>`_ file will be automatically updated with your name and
email once your pull request has been merged.

Development and test
--------------------

See the `README.rst <README.rst>`_ file.

Format of commit messages
-------------------------

A commit message must start with a short summary line, followed by a blank
line.

It can include a more detailed description after that. This is where you
explain why the change was done, and summarize what was done.

It must end with the DCO (Developer Certificate of Origin) sign-off line in the
format shown in the example below, using your name and a valid email address of
yours. The DCO sign-off line certifies that you followed the rules stated in
`DCO1.1.txt <DCO1.1.txt>`_. In short, you certify that you wrote the patch or
otherwise have the right to pass it on as an open-source patch.

We use GitCop to check whether the commit messages comply to this format.

Example commit message:

::

    Add support for delivering cookies

    Cookies are important for many people. This change adds a pluggable API for
    delivering cookies to the user, and provides a default implementation.

    Signed-off-by: Random J Developer <random@developer.org>

Use ``git commit --amend`` to edit the commit message, if you need to.
