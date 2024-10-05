.. Copyright 2016,2021 IBM Corp. All Rights Reserved.
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

.. _`Resources`:

Reference: Resources
====================

This section describes the resource model supported by the zhmcclient package.

Note that the zhmcclient package supports only a subset of the resources
described in the :term:`HMC API` book. We will grow the implemented subset
over time, and if you find that a particular resource you need is missing,
please open an issue in the `zhmcclient issue tracker`_.

.. _zhmcclient issue tracker: https://github.com/zhmcclient/python-zhmcclient/issues

See :ref:`Resource model concepts` for a description of the concepts used
in representing the resource model.

The resource descriptions in this section do not detail the resource
properties. The description of the resource properties of a particular HMC
resource type can be found in its "Data model" section in the :term:`HMC API`
book. Each Python resource class mentions the corresponding HMC resource type.

The data types used in these "Data model" sections are represented in Python
data types according to the mapping shown in the following table:

===========================  =====================
HMC API data type            Python data type
===========================  =====================
Boolean                      :class:`py:bool`
Byte, Integer, Long, Short   :term:`integer`
Float                        :class:`py:float`
String, String Enum          :term:`unicode string`
:term:`timestamp`            :term:`integer`
Array                        :class:`py:list`
Object                       :class:`py:dict`
===========================  =====================


.. _`CPCs`:

CPCs
----

.. automodule:: zhmcclient._cpc

.. autoclass:: zhmcclient.CpcManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Cpc
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. autoclass:: zhmcclient.STPNode
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Unmanaged CPCs`:

Unmanaged CPCs
--------------

.. automodule:: zhmcclient._unmanaged_cpc

.. autoclass:: zhmcclient.UnmanagedCpcManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.UnmanagedCpc
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Groups`:

Groups
------

.. automodule:: zhmcclient._group

.. autoclass:: zhmcclient.GroupManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Group
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Activation profiles`:

Activation profiles
-------------------

.. automodule:: zhmcclient._activation_profile

.. autoclass:: zhmcclient.ActivationProfileManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ActivationProfile
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`LPARs`:

LPARs
-----

.. automodule:: zhmcclient._lpar

.. autoclass:: zhmcclient.LparManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Lpar
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Partitions`:

Partitions
----------

.. automodule:: zhmcclient._partition

.. autoclass:: zhmcclient.PartitionManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Partition
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Adapters`:

Adapters
--------

.. automodule:: zhmcclient._adapter

.. autoclass:: zhmcclient.AdapterManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Adapter
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Ports`:

Ports
-----

.. automodule:: zhmcclient._port

.. autoclass:: zhmcclient.PortManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Port
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`NICs`:

NICs
----

.. automodule:: zhmcclient._nic

.. autoclass:: zhmcclient.NicManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Nic
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`HBAs`:

HBAs
----

.. automodule:: zhmcclient._hba

.. autoclass:: zhmcclient.HbaManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Hba
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Virtual Functions`:

Virtual Functions
-----------------

.. automodule:: zhmcclient._virtual_function

.. autoclass:: zhmcclient.VirtualFunctionManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.VirtualFunction
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Virtual Switches`:

Virtual Switches
----------------

.. automodule:: zhmcclient._virtual_switch

.. autoclass:: zhmcclient.VirtualSwitchManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.VirtualSwitch
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Storage Groups`:

Storage Groups
-----------------

.. automodule:: zhmcclient._storage_group

.. autoclass:: zhmcclient.StorageGroupManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.StorageGroup
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Storage Volumes`:

Storage Volumes
-----------------

.. automodule:: zhmcclient._storage_volume

.. autoclass:: zhmcclient.StorageVolumeManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.StorageVolume
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Virtual Storage Resources`:

Virtual Storage Resources
-------------------------

.. automodule:: zhmcclient._virtual_storage_resource

.. autoclass:: zhmcclient.VirtualStorageResourceManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.VirtualStorageResource
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Storage Group Templates`:

Storage Group Templates
-----------------------

.. automodule:: zhmcclient._storage_group_template

.. autoclass:: zhmcclient.StorageGroupTemplateManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.StorageGroupTemplate
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Storage Volume Templates`:

Storage Volume Templates
------------------------

.. automodule:: zhmcclient._storage_volume_template

.. autoclass:: zhmcclient.StorageVolumeTemplateManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.StorageVolumeTemplate
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Partition Links`:

Partition Links
---------------

.. automodule:: zhmcclient._partition_link

.. autoclass:: zhmcclient.PartitionLinkManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.PartitionLink
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Capacity Groups`:

Capacity Groups
-----------------

.. automodule:: zhmcclient._capacity_group

.. autoclass:: zhmcclient.CapacityGroupManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.CapacityGroup
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Console`:

Console
-------

.. automodule:: zhmcclient._console

.. autoclass:: zhmcclient.ConsoleManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Console
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`User`:

User
----

.. automodule:: zhmcclient._user

.. autoclass:: zhmcclient.UserManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.User
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`User Role`:

User Role
---------

.. automodule:: zhmcclient._user_role

.. autoclass:: zhmcclient.UserRoleManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.UserRole
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`User Pattern`:

User Pattern
------------

.. automodule:: zhmcclient._user_pattern

.. autoclass:: zhmcclient.UserPatternManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.UserPattern
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Password Rule`:

Password Rule
-------------

.. automodule:: zhmcclient._password_rule

.. autoclass:: zhmcclient.PasswordRuleManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.PasswordRule
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Task`:

Task
----

.. automodule:: zhmcclient._task

.. autoclass:: zhmcclient.TaskManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Task
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`LDAP Server Definition`:

LDAP Server Definition
----------------------

.. automodule:: zhmcclient._ldap_server_definition

.. autoclass:: zhmcclient.LdapServerDefinitionManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.LdapServerDefinition
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`MFA Server Definition`:

MFA Server Definition
---------------------

.. automodule:: zhmcclient._mfa_server_definition

.. autoclass:: zhmcclient.MfaServerDefinitionManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MfaServerDefinition
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Certificates`:

Certificates
-----------------

.. automodule:: zhmcclient._certificates

.. autoclass:: zhmcclient.CertificateManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Certificate
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__
