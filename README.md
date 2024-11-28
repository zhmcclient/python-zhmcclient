# zhmcclient - A pure Python client library for the IBM Z HMC Web Services API

[![Version on Pypi](https://img.shields.io/pypi/v/zhmcclient.svg)](https://pypi.python.org/pypi/zhmcclient/)
[![Test status (master)](https://github.com/zhmcclient/python-zhmcclient/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/zhmcclient/python-zhmcclient/actions/workflows/test.yml?query=branch%3Amaster)
[![Docs status (master)](https://readthedocs.org/projects/python-zhmcclient/badge/?version=latest)](https://readthedocs.org/projects/python-zhmcclient/builds/)
[![Test coverage (master)](https://coveralls.io/repos/github/zhmcclient/python-zhmcclient/badge.svg?branch=master)](https://coveralls.io/github/zhmcclient/python-zhmcclient?branch=master)
[![CodeClimate status](https://codeclimate.com/github/zhmcclient/python-zhmcclient/badges/gpa.svg)](https://codeclimate.com/github/zhmcclient/python-zhmcclient)

# Overview

The zhmcclient package is a client library written in pure Python that
interacts with the Web Services API of the Hardware Management Console
(HMC) of [IBM Z](http://www.ibm.com/systems/z/) or
[LinuxONE](http://www.ibm.com/systems/linuxone/) machines. The goal of
this package is to make the HMC Web Services API easily consumable for
Python programmers.

The HMC Web Services API is the access point for any external tools to
manage the IBM Z or LinuxONE platform. It supports management of the
lifecycle and configuration of various platform resources, such as
partitions, CPU, memory, virtual switches, I/O adapters, and more.

The zhmcclient package encapsulates both protocols supported by the HMC
Web Services API:

- REST over HTTPS for request/response-style operations driven by the
  client. Most of these operations complete synchronously, but some
  long-running tasks complete asynchronously.
- JMS (Java Messaging Services) for notifications from the HMC to the
  client. This can be used to be notified about changes in the system,
  or about completion of asynchronous tasks started using REST.

# Installation

The quick way:

``` bash
$ pip install zhmcclient
```

For more details, see the
[Installation section](http://python-zhmcclient.readthedocs.io/en/stable/intro.html#installation)
in the documentation.

# Quickstart

The following example code lists the partitions on CPCs in DPM mode that
are accessible for the user:

``` python
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
```

Possible output when running the script:

``` text
P000S67B PART1
P000S67B PART2
P0000M96 PART1
```

# Documentation and Change Log

For the latest released version on PyPI:

- [Documentation](http://python-zhmcclient.readthedocs.io/en/stable)
- [Change log](http://python-zhmcclient.readthedocs.io/en/stable/changes.html)

# zhmc CLI

Before version 0.18.0 of the zhmcclient package, it contained the zhmc
CLI. Starting with zhmcclient version 0.18.0, the zhmc CLI has been
moved from this project into the new
[zhmccli project](https://github.com/zhmcclient/zhmccli).

If your project uses the zhmc CLI, and you are upgrading the zhmcclient
package from before 0.18.0 to 0.18.0 or later, your project will need to
add the [zhmccli package](https://pypi.python.org/pypi/zhmccli) to its
dependencies.

# Contributing

For information on how to contribute to this project, see the
[Development section](http://python-zhmcclient.readthedocs.io/en/stable/development.html)
in the documentation.

# License

The zhmcclient package is licensed under the
[Apache 2.0 License](https://github.com/zhmcclient/python-zhmcclient/tree/stable/LICENSE).
