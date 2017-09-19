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

.. image:: https://travis-ci.org/zhmcclient/python-zhmcclient.svg?branch=master
    :target: https://travis-ci.org/zhmcclient/python-zhmcclient
    :alt: Travis test status (master)

.. image:: https://ci.appveyor.com/api/projects/status/i022iaeu3dao8j5x/branch/master?svg=true
    :target: https://ci.appveyor.com/project/leopoldjuergen/python-zhmcclient
    :alt: Appveyor test status (master)

.. image:: https://readthedocs.org/projects/python-zhmcclient/badge/?version=latest
    :target: http://python-zhmcclient.readthedocs.io/en/latest/
    :alt: Docs build status (latest)

.. image:: https://img.shields.io/coveralls/zhmcclient/python-zhmcclient.svg
    :target: https://coveralls.io/r/zhmcclient/python-zhmcclient
    :alt: Test coverage (master)

.. image:: https://codeclimate.com/github/zhmcclient/python-zhmcclient/badges/gpa.svg
    :target: https://codeclimate.com/github/zhmcclient/python-zhmcclient
    :alt: Code Climate

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

.. _Installation section: http://python-zhmcclient.readthedocs.io/en/stable/intro.html#installation

Quickstart
===========

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

Documentation
=============

The zhmcclient documentation is on RTD:

* `Documentation for latest version on Pypi`_
* `Documentation for master branch in Git repo`_

.. _Documentation for latest version on Pypi: http://python-zhmcclient.readthedocs.io/en/stable/
.. _Documentation for master branch in Git repo: http://python-zhmcclient.readthedocs.io/en/latest/

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

.. _Development section: http://python-zhmcclient.readthedocs.io/en/stable/development.html

License
=======

The zhmcclient package is licensed under the `Apache 2.0 License`_.

.. _Apache 2.0 License: https://github.com/zhmcclient/python-zhmcclient/tree/master/LICENSE
