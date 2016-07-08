
.. _`API Reference`:

API Reference
=============

.. _`Sessions`:
.. _`Clients`:

Sessions and clients
--------------------

.. automodule:: zhmcclient._session

.. autoclass:: zhmcclient.Session
   :members:
   :special-members: __str__

.. automodule:: zhmcclient._client

.. autoclass:: zhmcclient.Client
   :members:
   :special-members: __str__

.. _`Exceptions`:

Exceptions
----------

.. automodule:: zhmcclient._exceptions

.. autoclass:: zhmcclient.Error

.. autoclass:: zhmcclient.ConnectionError

.. autoclass:: zhmcclient.AuthError

.. autoclass:: zhmcclient.ParseError

.. autoclass:: zhmcclient.VersionError

.. autoclass:: zhmcclient.HTTPError
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.NotFound

.. autoclass:: zhmcclient.NoUniqueMatch

.. _`CPCs`:

BaseManager and BaseResource
----------------------------

.. automodule:: zhmcclient._manager

.. autoclass:: zhmcclient.BaseManager
   :members:
   :special-members: __str__

.. automodule:: zhmcclient._resource

.. autoclass:: zhmcclient.BaseResource
   :members:
   :special-members: __str__

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

