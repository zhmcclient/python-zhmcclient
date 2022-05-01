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

zhmcclient - A pure Python client library for the IBM Z HMC Web Services API
============================================================================

.. PyPI download statistics are broken, but the new PyPI warehouse makes PyPI
.. download statistics available through Google BigQuery
.. (https://bigquery.cloud.google.com).
.. Query to list package downloads by version:
..
   SELECT
     file.project,
     file.version,
     COUNT(*) as total_downloads,
     SUM(CASE WHEN REGEXP_EXTRACT(details.python, r"^([^\.]+\.[^\.]+)") = "2.6" THEN 1 ELSE 0 END) as py26_downloads,
     SUM(CASE WHEN REGEXP_EXTRACT(details.python, r"^([^\.]+\.[^\.]+)") = "2.7" THEN 1 ELSE 0 END) as py27_downloads,
     SUM(CASE WHEN REGEXP_EXTRACT(details.python, r"^([^\.]+)\.[^\.]+") = "3" THEN 1 ELSE 0 END) as py3_downloads,
   FROM
     TABLE_DATE_RANGE(
       [the-psf:pypi.downloads],
       TIMESTAMP("19700101"),
       CURRENT_TIMESTAMP()
     )
   WHERE
     file.project = 'zhmcclient'
   GROUP BY
     file.project, file.version
   ORDER BY
     file.version DESC

.. image:: https://img.shields.io/pypi/v/zhmcclient.svg
    :target: https://pypi.python.org/pypi/zhmcclient/
    :alt: Version on Pypi

.. # .. image:: https://img.shields.io/pypi/dm/zhmcclient.svg
.. #     :target: https://pypi.python.org/pypi/zhmcclient/
.. #     :alt: Pypi downloads

.. image:: https://github.com/zhmcclient/python-zhmcclient/workflows/test/badge.svg?branch=master
    :target: https://github.com/zhmcclient/python-zhmcclient/actions/
    :alt: Actions status

.. image:: https://readthedocs.org/projects/python-zhmcclient/badge/?version=latest
    :target: https://readthedocs.org/projects/python-zhmcclient/builds/
    :alt: ReadTheDocs status

.. image:: https://coveralls.io/repos/github/zhmcclient/python-zhmcclient/badge.svg?branch=master
    :target: https://coveralls.io/github/zhmcclient/python-zhmcclient?branch=master
    :alt: Coveralls status

.. image:: https://codeclimate.com/github/zhmcclient/python-zhmcclient/badges/gpa.svg
    :target: https://codeclimate.com/github/zhmcclient/python-zhmcclient
    :alt: CodeClimate status

.. contents:: Contents:
   :local:

Overview
========

The zhmcclient package is a client library
written in pure Python that interacts with the Web Services API of the Hardware
Management Console (HMC) of `IBM Z`_ or `LinuxONE`_ machines. The goal of
this package is to make the HMC Web Services API easily consumable for Python
programmers.

.. _IBM Z: http://www.ibm.com/systems/z/
.. _LinuxONE: http://www.ibm.com/systems/linuxone/

The HMC Web Services API is the access point for any external tools to
manage the IBM Z  or LinuxONE platform. It supports management of the
lifecycle and configuration of various platform resources, such as partitions,
CPU, memory, virtual switches, I/O adapters, and more.

The zhmcclient package encapsulates both protocols supported by the HMC Web
Services API:

* REST over HTTPS for request/response-style operations driven by the client.
  Most of these operations complete synchronously, but some long-running tasks
  complete asynchronously.

* JMS (Java Messaging Services) for notifications from the HMC to the client.
  This can be used to be notified about changes in the system, or about
  completion of asynchronous tasks started using REST.

Installation
============

The quick way:

.. code-block:: bash

    $ pip install zhmcclient

For more details, see the `Installation section`_ in the documentation.

.. _Installation section: http://python-zhmcclient.readthedocs.io/en/latest/intro.html#installation

Quickstart
===========

The following example code lists the partitions on CPCs in DPM mode that are
accessible for the user:

.. code-block:: python

    #!/usr/bin/env python

    import zhmcclient
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()

    # Set these variables for your environment:
    host = "<IP address or hostname of the HMC>"
    userid = "<userid on that HMC>"
    password = "<password of that HMC userid>"
    verify_cert = False

    session = zhmcclient.Session(host, userid, password, verify_cert=verify_cert)
    client = zhmcclient.Client(session)
    console = client.consoles.console

    partitions = console.list_permitted_partitions()
    for part in partitions:
        cpc = part.manager.parent
        print("{} {}".format(cpc.name, part.name))

Possible output when running the script:

.. code-block:: text

    P000S67B PART1
    P000S67B PART2
    P0000M96 PART1

Documentation and Change Log
============================

For the latest released version on PyPI:

* `Documentation`_
* `Change log`_

.. _Documentation: http://python-zhmcclient.readthedocs.io/en/latest/
.. _Change log: http://python-zhmcclient.readthedocs.io/en/latest/changes.html

zhmc CLI
========

Before version 0.18.0 of the zhmcclient package, it contained the zhmc CLI.
Starting with zhmcclient version 0.18.0, the zhmc CLI has been moved from this
project into the new `zhmccli project`_.

If your project uses the zhmc CLI, and you are upgrading the zhmcclient
package from before 0.18.0 to 0.18.0 or later, your project will need to add
the `zhmccli package`_ to its dependencies.

.. _zhmccli project: https://github.com/zhmcclient/zhmccli

.. _zhmccli package: https://pypi.python.org/pypi/zhmccli


Contributing
============

For information on how to contribute to this project, see the
`Development section`_ in the documentation.

.. _Development section: http://python-zhmcclient.readthedocs.io/en/latest/development.html

License
=======

The zhmcclient package is licensed under the `Apache 2.0 License`_.

.. _Apache 2.0 License: https://github.com/zhmcclient/python-zhmcclient/tree/master/LICENSE
