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

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Session
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Session
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.Job
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Job
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Job
      :attributes:

   .. rubric:: Details

.. autofunction:: zhmcclient.get_password_interface


.. _`Retry-timeout configuration`:

Retry / timeout configuration
-----------------------------

.. autoclass:: zhmcclient.RetryTimeoutConfig
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.RetryTimeoutConfig
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.RetryTimeoutConfig
      :attributes:

   .. rubric:: Details


.. _`Client`:

Client
------

.. automodule:: zhmcclient._client

.. autoclass:: zhmcclient.Client
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.Client
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.Client
      :attributes:

   .. rubric:: Details


.. _`Time Statistics`:

Time Statistics
---------------

.. automodule:: zhmcclient._timestats

.. autoclass:: zhmcclient.TimeStatsKeeper
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.TimeStatsKeeper
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.TimeStatsKeeper
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.TimeStats
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.TimeStats
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.TimeStats
      :attributes:

   .. rubric:: Details


.. _`Metrics`:

Metrics
-------

.. automodule:: zhmcclient._metrics

.. autoclass:: zhmcclient.MetricsContextManager
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.MetricsContextManager
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.MetricsContextManager
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.MetricsContext
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.MetricsContext
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.MetricsContext
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.MetricGroupDefinition
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricDefinition
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.MetricsResponse
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.MetricsResponse
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.MetricsResponse
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.MetricGroupValues
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.MetricGroupValues
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.MetricGroupValues
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.MetricObjectValues
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.MetricObjectValues
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.MetricObjectValues
      :attributes:

   .. rubric:: Details


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
   :special-members: __str__

   .. rubric:: Details

.. autoclass:: zhmcclient.ConnectionError
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.ConnectionError
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.ConnectionError
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.ConnectTimeout
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.ConnectTimeout
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.ConnectTimeout
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.ReadTimeout
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.ReadTimeout
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.ReadTimeout
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.RetriesExceeded
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.RetriesExceeded
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.RetriesExceeded
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.AuthError
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.AuthError
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.AuthError
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.ClientAuthError
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.ClientAuthError
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.ClientAuthError
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.ServerAuthError
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.ServerAuthError
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.ServerAuthError
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.ParseError
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.ParseError
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.ParseError
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.VersionError
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.VersionError
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.VersionError
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.HTTPError
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.HTTPError
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.HTTPError
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.OperationTimeout
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.OperationTimeout
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.OperationTimeout
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.StatusTimeout
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.StatusTimeout
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.StatusTimeout
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.NotFound
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.NotFound
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.NotFound
      :attributes:

   .. rubric:: Details

.. autoclass:: zhmcclient.NoUniqueMatch
   :members:
   :special-members: __str__

   .. rubric:: Methods

   .. autoautosummary:: zhmcclient.NoUniqueMatch
      :methods:
      :nosignatures:

   .. rubric:: Attributes

   .. autoautosummary:: zhmcclient.NoUniqueMatch
      :attributes:

   .. rubric:: Details


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
