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
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.CpcManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.CpcManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Cpc
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Cpc
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Cpc
      :attributes:

   .. rubric:: Details


.. _`Unmanaged CPCs`:

Unmanaged CPCs
--------------

.. automodule:: zhmcclient._unmanaged_cpc

.. autoclass:: zhmcclient.UnmanagedCpcManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.UnmanagedCpcManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.UnmanagedCpcManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.UnmanagedCpc
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.UnmanagedCpc
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.UnmanagedCpc
      :attributes:

   .. rubric:: Details


.. _`Activation profiles`:

Activation profiles
-------------------

.. automodule:: zhmcclient._activation_profile

.. autoclass:: zhmcclient.ActivationProfileManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.ActivationProfileManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.ActivationProfileManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.ActivationProfile
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.ActivationProfile
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.ActivationProfile
      :attributes:

   .. rubric:: Details


.. _`LPARs`:

LPARs
-----

.. automodule:: zhmcclient._lpar

.. autoclass:: zhmcclient.LparManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.LparManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.LparManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Lpar
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Lpar
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Lpar
      :attributes:

   .. rubric:: Details


.. _`Partitions`:

Partitions
----------

.. automodule:: zhmcclient._partition

.. autoclass:: zhmcclient.PartitionManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.PartitionManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.PartitionManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Partition
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Partition
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Partition
      :attributes:

   .. rubric:: Details


.. _`Adapters`:

Adapters
--------

.. automodule:: zhmcclient._adapter

.. autoclass:: zhmcclient.AdapterManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.AdapterManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.AdapterManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Adapter
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Adapter
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Adapter
      :attributes:

   .. rubric:: Details


.. _`Ports`:

Ports
-----

.. automodule:: zhmcclient._port

.. autoclass:: zhmcclient.PortManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.PortManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.PortManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Port
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Port
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Port
      :attributes:

   .. rubric:: Details


.. _`NICs`:

NICs
----

.. automodule:: zhmcclient._nic

.. autoclass:: zhmcclient.NicManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.NicManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.NicManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Nic
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Nic
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Nic
      :attributes:

   .. rubric:: Details


.. _`HBAs`:

HBAs
----

.. automodule:: zhmcclient._hba

.. autoclass:: zhmcclient.HbaManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.HbaManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.HbaManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Hba
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Hba
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Hba
      :attributes:

   .. rubric:: Details


.. _`Virtual Functions`:

Virtual Functions
-----------------

.. automodule:: zhmcclient._virtual_function

.. autoclass:: zhmcclient.VirtualFunctionManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.VirtualFunctionManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.VirtualFunctionManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.VirtualFunction
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.VirtualFunction
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.VirtualFunction
      :attributes:

   .. rubric:: Details


.. _`Virtual Switches`:

Virtual Switches
----------------

.. automodule:: zhmcclient._virtual_switch

.. autoclass:: zhmcclient.VirtualSwitchManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.VirtualSwitchManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.VirtualSwitchManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.VirtualSwitch
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.VirtualSwitch
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.VirtualSwitch
      :attributes:

   .. rubric:: Details


.. _`Storage Groups`:

Storage Groups
-----------------

.. automodule:: zhmcclient._storage_group

.. autoclass:: zhmcclient.StorageGroupManager
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.StorageGroup
   :members:
   :special-members: __str__


.. _`Storage Volumes`:

Storage Volumes
-----------------

.. automodule:: zhmcclient._storage_volume

.. autoclass:: zhmcclient.StorageVolumeManager
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.StorageVolume
   :members:
   :special-members: __str__


.. _`Virtual Storage Resources`:

Virtual Storage Resources
-------------------------

.. automodule:: zhmcclient._virtual_storage_resource

.. autoclass:: zhmcclient.VirtualStorageResourceManager
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.VirtualStorageResource
   :members:
   :special-members: __str__


.. _`Console`:

Console
-------

.. automodule:: zhmcclient._console

.. autoclass:: zhmcclient.ConsoleManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.ConsoleManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.ConsoleManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Console
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Console
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Console
      :attributes:

   .. rubric:: Details


.. _`User`:

User
----

.. automodule:: zhmcclient._user

.. autoclass:: zhmcclient.UserManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.UserManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.UserManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.User
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.User
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.User
      :attributes:

   .. rubric:: Details


.. _`User Role`:

User Role
---------

.. automodule:: zhmcclient._user_role

.. autoclass:: zhmcclient.UserRoleManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.UserRoleManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.UserRoleManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.UserRole
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.UserRole
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.UserRole
      :attributes:

   .. rubric:: Details


.. _`User Pattern`:

User Pattern
------------

.. automodule:: zhmcclient._user_pattern

.. autoclass:: zhmcclient.UserPatternManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.UserPatternManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.UserPatternManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.UserPattern
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.UserPattern
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.UserPattern
      :attributes:

   .. rubric:: Details


.. _`Password Rule`:

Password Rule
-------------

.. automodule:: zhmcclient._password_rule

.. autoclass:: zhmcclient.PasswordRuleManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.PasswordRuleManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.PasswordRuleManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.PasswordRule
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.PasswordRule
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.PasswordRule
      :attributes:

   .. rubric:: Details


.. _`Task`:

Task
----

.. automodule:: zhmcclient._task

.. autoclass:: zhmcclient.TaskManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.TaskManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.TaskManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Task
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Task
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Task
      :attributes:

   .. rubric:: Details


.. _`LDAP Server Definition`:

LDAP Server Definition
----------------------

.. automodule:: zhmcclient._ldap_server_definition

.. autoclass:: zhmcclient.LdapServerDefinitionManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.LdapServerDefinitionManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.LdapServerDefinitionManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.LdapServerDefinition
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.LdapServerDefinition
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.LdapServerDefinition
      :attributes:

   .. rubric:: Details
