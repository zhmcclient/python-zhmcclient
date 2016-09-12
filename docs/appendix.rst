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


.. _`BaseManager`:
.. _`BaseResource`:
.. _`Base classes for resources`:

Base classes for resources
--------------------------

.. automodule:: zhmcclient._manager

.. autoclass:: zhmcclient.BaseManager
   :members:
   :special-members: __str__

.. automodule:: zhmcclient._resource

.. autoclass:: zhmcclient.BaseResource
   :members:
   :special-members: __str__


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


.. _'Resource model`:

Resource model
--------------

This section lists the resources that are available at the :term:`HMC API`,
in alphabetical order.

The *Scope* specifies whether the resource is available within a CPC and in
what mode of the CPC, vs. being available across CPCs.

Some of the items in this section are qualified as *short terms*. They are not
separate types of resources, but specific usages of resources. For example,
"storage adapter" is a short term for the resource "adapter" when used for
attaching storage.

.. glossary::

  Activation Profile
     A general term for specific activation profiles:

     * :term:`Reset Activation Profile`
     * :term:`Image Activation Profile`
     * :term:`Load Activation Profile`

     Scope: CPC in classic (or ensemble) mode

  Accelerator Adapter
     Short term for an :term:`Adapter` providing accelerator functions (e.g.
     the z Systems Enterprise Data Compression (zEDC) adapter for data
     compression).

  Adapter
     A physical adapter card (e.g. OSA-Express adapter, Crypto adapter) or a
     logical adapter (e.g. HiperSockets switch).

     For details, see section :ref:`Adapters`.

     Scope: CPC in DPM mode

  Adapter Port
  Port
     The physical connector port (jack) of an :term:`Adapter`.

     For details, see section :ref:`Ports`.

     Scope: CPC in DPM mode

  Capacity Group
     TBD

     Scope: CPC in DPM mode

  Capacity Record
     TBD

     Scope: CPC in any mode

  Console
     TBD

     Scope: HMC

  CPC
     A physical z Systems or LinuxONE computer.

     For details, see section :ref:`CPCs`.

     Scope: CPC

  Crypto Adapter
     Short term for an :term:`Adapter` providing cryptographic functions.

  FCP Adapter
     Short term for a :term:`Storage Adapter` supporting FCP.

  Group
     TBD

     Scope: HMC

  Group Profile
     TBD

     Scope: CPC in classic (or ensemble) mode

  Hardware Message
     TBD

     Scope: HMC, and CPC in any mode

  HBA
  vHBA
     A logical entity that provides a :term:`Partition` with access to
     external storage area networks (SANs) through an :term:`FCP Adapter`.

     For details, see section :ref:`HBAs`.

     Scope: CPC in DPM mode

  Image Activation Profile
     TBD

     Scope: CPC in classic (or ensemble) mode

  Job
     TBD

     Scope: HMC

  LDAP Server Definition
     TBD

     Scope: HMC

  Load Activation Profile
     TBD

     Scope: CPC in classic (or ensemble) mode

  Logical Partition
  LPAR
     A subset of the hardware resources of a :term:`CPC` in classic mode (or
     ensemble mode), virtualized as a separate computer.

     For details, see section :ref:`LPARs`.

     Scope: CPC in classic (or ensemble) mode

  Metrics Context
     TBD

     Scope: HMC

  Network Adapter
     Short term for an :term:`Adapter` for attaching networks (e.g. OSA-Express
     adapter).

  Network Port
     Short term for an :term:`Adapter Port` of a :term:`Network Adapter`.

  NIC
  vNIC
     Network Interface Card, a logical entity that provides a
     :term:`Partition` with access to external communication networks through a
     :term:`Network Adapter`.

     For details, see section :ref:`NICs`.

     Scope: CPC in DPM mode

  Partition
     A subset of the hardware resources of a :term:`CPC` in DPM mode,
     virtualized as a separate computer.

     For details, see section :ref:`Partitions`.

     Scope: CPC in DPM mode

  Password Rule
     TBD

     Scope: HMC

  Reset Activation Profile
     TBD

     Scope: CPC in classic (or ensemble) mode

  Session
     TBD

     Scope: HMC

  Storage Adapter
     Short term for an :term:`Adapter` for attaching storage.

  Storage Port
     Short term for an :term:`Adapter Port` of a :term:`Storage Adapter`.

  Task
     TBD

     Scope: HMC

  User
     TBD

     Scope: HMC

  User Pattern
     TBD

     Scope: HMC

  User Role
     TBD

     Scope: HMC

  Virtual Function
     A logical entity that provides a :term:`Partition` with access to
     :term:`Accelerator Adapters <Accelerator Adapter>`.

     For details, see section :ref:`Virtual functions`.

     Scope: CPC in DPM mode

  Virtual Machine
     TBD

     Scope: CPC in classic (or ensemble) mode

  Virtual Switch
     A virtualized networking switch connecting :term:`NICs <NIC>` with a
     :term:`Network Port`.

     For details, see section :ref:`Virtual switches`.

     Scope: CPC in DPM mode

  
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

