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

.. _`Resources`:

Reference: Resources
====================


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


.. _`CPCs`:

CPCs
----

.. automodule:: zhmcclient._cpc

.. autoclass:: zhmcclient.CpcManager
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.Cpc
   :members:
   :special-members: __str__


.. _`LPARs`:

LPARs
-----

.. automodule:: zhmcclient._lpar

.. autoclass:: zhmcclient.LparManager
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.Lpar
   :members:
   :special-members: __str__


.. _`Partitions`:

Partitions
----------

.. automodule:: zhmcclient._partition

.. autoclass:: zhmcclient.PartitionManager
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.Partition
   :members:
   :special-members: __str__


.. _`Activation profiles`:

Activation profiles
-------------------

.. automodule:: zhmcclient._activation_profile

.. autoclass:: zhmcclient.ActivationProfileManager
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.ActivationProfile
   :members:
   :special-members: __str__
