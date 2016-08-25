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

.. _`General features`:

Reference: General features
===========================


.. _`Session`:

Session
-------

.. automodule:: zhmcclient._session

.. autoclass:: zhmcclient.Session
   :members:
   :special-members: __str__


.. _`Client`:

Client
------

.. automodule:: zhmcclient._client

.. autoclass:: zhmcclient.Client
   :members:
   :special-members: __str__


.. _`Time Statistics`:

Time Statistics
---------------

.. automodule:: zhmcclient._timestats

.. autoclass:: zhmcclient.TimeStatsKeeper
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.TimeStats
   :members:
   :special-members: __str__


.. _`Logging`:

Logging
-------

.. automodule:: zhmcclient._logging


.. _`Exceptions`:

Exceptions
----------

.. automodule:: zhmcclient._exceptions

.. autoclass:: zhmcclient.Error

.. autoclass:: zhmcclient.ConnectionError
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.AuthError
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.ParseError
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.VersionError
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.HTTPError
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.NotFound
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.NoUniqueMatch
   :members:
   :special-members: __str__
