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

.. _`Appendix`:

Appendix
========

This section contains information that is referenced from other sections,
and that does not really need to be read in sequence.

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
      a standard Python warning that indicates the use of deprecated
      functionality. See section :ref:`Deprecations` for details.

.. _`Bibliography`:

Bibliography
------------

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
       The Web Services API of the z Systems Hardware Management Console, described in the following books:

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

