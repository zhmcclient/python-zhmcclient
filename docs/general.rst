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

.. _`General features`:

Reference: General features
===========================


.. _`Session`:

Session
-------

.. automodule:: zhmcclient._session

.. autoclass:: zhmcclient.Session
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.Job
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autofunction:: zhmcclient.get_password_interface


.. _`Retry-timeout configuration`:

Retry / timeout configuration
-----------------------------

.. autoclass:: zhmcclient.RetryTimeoutConfig
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`AutoUpdater`:

AutoUpdater
---------------

.. automodule:: zhmcclient._auto_updater

.. autoclass:: zhmcclient.AutoUpdater
  :members:
  :autosummary:
  :autosummary-inherited-members:
  :special-members: __str__


.. _`Client`:

Client
------

.. automodule:: zhmcclient._client

.. autoclass:: zhmcclient.Client
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Time Statistics`:

Time Statistics
---------------

.. automodule:: zhmcclient._timestats

.. autoclass:: zhmcclient.TimeStatsKeeper
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.TimeStats
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Metrics`:

Metrics
-------

.. automodule:: zhmcclient._metrics

.. autoclass:: zhmcclient.MetricsContextManager
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricsContext
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricGroupDefinition
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricDefinition
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricsResponse
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricGroupValues
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricObjectValues
   :members:
   :autosummary:
   :autosummary-inherited-members:
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
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ConnectionError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ConnectTimeout
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ReadTimeout
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.RetriesExceeded
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.AuthError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ClientAuthError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ServerAuthError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.ParseError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.VersionError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.HTTPError
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.OperationTimeout
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.StatusTimeout
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.NotFound
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.NoUniqueMatch
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__

.. autoclass:: zhmcclient.CeasedExistence
   :members:
   :autosummary:
   :autosummary-inherited-members:
   :special-members: __str__


.. _`Constants`:

Constants
---------

.. automodule:: zhmcclient._constants
   :members:


.. _`Utilities`:

Utilities
---------

.. # Note: In order to avoid the issue that automodule members are shown
.. # in their module namespace (e.g. zhmcclient._utils), we maintain the
.. # members of the _utils module manually.

.. automodule:: zhmcclient._utils

.. autofunction:: zhmcclient.datetime_from_timestamp

.. autofunction:: zhmcclient.timestamp_from_datetime
