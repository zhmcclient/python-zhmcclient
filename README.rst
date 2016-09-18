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
    :alt: Test status (master)

.. image:: https://readthedocs.org/projects/python-zhmcclient/badge/?version=latest
    :target: http://python-zhmcclient.readthedocs.io/en/latest/
    :alt: Docs build status (latest)

.. image:: https://img.shields.io/coveralls/zhmcclient/python-zhmcclient.svg
    :target: https://coveralls.io/r/zhmcclient/python-zhmcclient
    :alt: Test coverage (master)

.. contents:: Contents:
   :local:

Overview
========

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

Installation
============

The quick way:

.. code-block:: bash

    $ pip install zhmcclient

For more details see the `Installation section`_ in the documentation.

.. _Installation section: http://python-zhmcclient.readthedocs.io/en/stable/intro.html#installation

Quickstart
===========

.. code-block:: python

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

Documentation
=============

The zhmcclient documentation is on RTD:

* `Documentation for version on Pypi`_
* `Documentation for master branch in Git repo`_

.. _Documentation for version on Pypi: http://python-zhmcclient.readthedocs.io/en/stable/
.. _Documentation for master branch in Git repo: http://python-zhmcclient.readthedocs.io/en/latest/

Development, testing, and contributing
======================================

For more details, see the `Development section`_ in the documentation.

.. _Development section: http://python-zhmcclient.readthedocs.io/en/stable/development.html

License
=======

python-zhmcclient is licensed under the `Apache 2.0 License`_.

.. _Apache 2.0 License: https://github.com/zhmcclient/python-zhmcclient/tree/master/LICENSE
