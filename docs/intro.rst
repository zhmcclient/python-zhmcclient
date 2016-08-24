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

.. _`Introduction`:

Introduction
============

.. _`What this package provides`:

What this package provides
--------------------------

The **zhmcclient** Python package is a a Python client library that interacts
with the Web Services API of the z Systems Hardware Management Console (HMC)
(see :term:`HMC API`).
This package is written in pure Python.

The Web Services API of the HMC is the access point for any external tools to
manage the z Systems platform; it supports management of the lifecycle and
configuration of various platform resources, such as logical partitions, CPU,
memory, or I/O adapters.

The Web Services API of the HMC supports two protocols for its clients:

* A REST API for request/response-style interactions driven by the client.
  Most of them complete synchronously, but some long-running tasks
  complete asynchronously.

* JMS for notifications from the HMC to the client (e.g. about changes in the
  system, or about completion of asynchronous tasks started using the REST API.

This Python package currently supports only the REST API with a subset of the
defined functionality. Support for JMS is intended to be added in the future,
as well as completing the functionality of the REST API.

.. _`Supported environments`:

Supported environments
----------------------

This package is supported in these environments:

* Operating systems: Linux, Windows, OS-X

* Python versions: 2.7, 3.4 and higher 3.x

* HMC versions: 2.11 and higher

The following table shows for each HMC version the supported HMC API version
and the supported z System and LinuxOne machine generations:

===========  ===============  ======================  =================================
HMC version  HMC API version  HMC API book            Machine generations
===========  ===============  ======================  =================================
2.11.0       1.1              :term:`HMC API 2.11.0`  up to z196/z114
2.11.1       1.2              :term:`HMC API 2.11.1`  up to z196/z114
2.12.0       1.3              :term:`HMC API 2.12.0`  up to zEC12/zBC12
2.12.1       1.4/1.5          :term:`HMC API 2.12.1`  up to zEC12/zBC12
2.13.0       1.6              :term:`HMC API 2.13.0`  up to z13/z13s/Emperor/Rockhopper
2.13.1       1.7              :term:`HMC API 2.13.1`  up to z13/z13s/Emperor/Rockhopper
===========  ===============  ======================  =================================

.. _`Deprecation policy`:

Deprecation policy
------------------

This package attempts to be as backwards compatible as possible.

However, occasionally functionality needs to be retired, because it is flawed and
a better but incompatible replacement has emerged.
Such changes are done by deprecating existing functionality,
without removing it. The deprecated functionality is still supported throughout
new minor releases. Eventually, a new major release will break compatibility and
will remove the deprecated functionality.

In order to prepare the users for that, deprecation of functionality
is stated in the API documentation, and is made visible at runtime by issuing
Python warnings of type ``DeprecationWarning`` (see the Python
:mod:`py:warnings` module).

Since Python 2.7, ``DeprecationWarning`` messages are suppressed by default.
They can be shown for example in any of these ways:

* By specifying the Python command line option: ``-W default``
* By invoking Python with the environment variable: ``PYTHONWARNINGS=default``

It is recommended that the users of this package run their test code with
``DeprecationWarning`` messages being shown, so they become aware of any use of
deprecated functionality.

Here is a summary of the deprecation and compatibility policy used by
this package, by release type:

* New update release (M.N.U -> M.N.U+1): No new deprecations; fully backwards
  compatible.
* New minor release (M.N.U -> M.N+1.0): New deprecations may be added; as
  backwards compatible as possible.
* New major release (M.N.U -> M+1.0.0): Deprecated functionality may get
  removed; backwards compatibility may be broken.

Compatibility is always seen from the perspective of the user of this package, so
a backwards compatible new release of this package means that the user can safely
upgrade to that new release without encountering compatibility issues.

.. _'Special type names`:

Special type names
------------------

This documentation uses a few special terms to refer to Python types:

.. glossary::

   string
      a :term:`unicode string` or a :term:`byte string`

   unicode string
      a Unicode string type (:func:`unicode <py2:unicode>` in
      Python 2, and :class:`py3:str` in Python 3)

   byte string
      a byte string type (:class:`py2:str` in Python 2, and
      :class:`py3:bytes` in Python 3). Unless otherwise
      indicated, byte strings in this package are always UTF-8 encoded.

   number
      one of the number types :class:`py:int`, :class:`py2:long` (Python 2
      only), or :class:`py:float`.

   integer
      one of the integer types :class:`py:int` or :class:`py2:long` (Python 2
      only).

   json object
      a :class:`py:dict` object that is a Python representation of a valid JSON
      object. See :ref:`py:py-to-json-table` for details.

   header dict
      a :class:`py:dict` object that specifies HTTP header fields, as follows:

        * `key` (:term:`string`): Name of the header field, in any lexical case.
          Dictionary key lookup is case sensitive, however.
        * `value` (:term:`string`): Value of the header field.

   callable
      a type for callable objects (e.g. a function, calling a class returns a
      new instance, instances are callable if they have a
      :meth:`~py:object.__call__` method).

   DeprecationWarning
      a standard Python warning that indicates a deprecated functionality.
      See section `Deprecation policy`_ and the standard Python module
      :mod:`py:warnings` for details.

.. _`References`:

References
----------

.. glossary::

   X.509
      `ITU-T X.509, Information technology - Open Systems Interconnection - The Directory: Public-key and attribute certificate frameworks <http://www.itu.int/rec/T-REC-X.509/en>`_

   RFC2616
      `IETF RFC2616, Hypertext Transfer Protocol - HTTP/1.1, June 1999 <https://tools.ietf.org/html/rfc2616>`_

   RFC2617
      `IETF RFC2617, HTTP Authentication: Basic and Digest Access Authentication, June 1999 <https://tools.ietf.org/html/rfc2617>`_

   RFC3986
      `IETF RFC3986, Uniform Resource Identifier (URI): Generic Syntax, January 2005 <https://tools.ietf.org/html/rfc3986>`_

   RFC6874
      `IETF RFC6874, Representing IPv6 Zone Identifiers in Address Literals and Uniform Resource Identifiers, February 2013 <https://tools.ietf.org/html/rfc6874>`_

   HMC API
       One of the following HMC API books:

   HMC API 2.11.1
       `IBM SC27-2616-01, z Systems Hardware Management Console Web Services API (Version 2.11.1) <https://www-304.ibm.com/servers/resourcelink/lib03010.nsf/0/38BA3E47697D87E385257967006AB34E/>`_

   HMC API 2.12.0
       `IBM SC27-2617-01, z Systems Hardware Management Console Web Services API (Version 2.12.0) <https://www-304.ibm.com/servers/resourcelink/lib03010.nsf/0/9B97F40675618BA085257A6A00777BEA/>`_

   HMC API 2.12.1
       `IBM SC27-2626-00a, z Systems Hardware Management Console Web Services API (Version 2.12.1) <https://www-304.ibm.com/servers/resourcelink/lib03010.nsf/0/3DDB93B38680A72F85257BA600515AA7/>`_

   HMC API 2.13.0
       `IBM SC27-2627-00a, z Systems Hardware Management Console Web Services API (Version 2.13.0) <https://www-304.ibm.com/servers/resourcelink/lib03010.nsf/0/7FA57A5A8A5297B185257DE7004E7144/>`_

   HMC API 2.13.1
       `IBM SC27-2634-01, z Systems Hardware Management Console Web Services API (Version 2.13.1) <https://www-304.ibm.com/servers/resourcelink/lib03010.nsf/0/CB468B15654CA89B85257F7200746C16/>`_

