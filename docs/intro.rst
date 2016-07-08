
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

This package is supported in these Operating System and Python environments:

* on Windows, with Python 2.7, 3.4, 3.5, and higher 3.x

* on Linux, with Python 2.7, 3.4, 3.5, and higher 3.x

* OS-X has not been tested and is therefore not listed, above. You are welcome
  to try it out and report any issues (TODO: Add link to issue tracker).

This package determines the API version supported by the HMC, and rejects
operation if it finds an API version that is not supported. This package
supports the following HMC API versions:

* HMC API version 1.5 and above (i.e. IBM z13 machine, and above). The
  :term:`HMC API` describes this version. Note that the *Version 2.13*
  mentioned in the book title is not the HMC API version.
   
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
       `IBM SC27-2627-00, z Systems Hardware Management Console Web Services API (Version 2.13.0) <http://www-01.ibm.com/support/docview.wss?uid=isg27fa57a5a8a5297b185257de7004e7144>`_
