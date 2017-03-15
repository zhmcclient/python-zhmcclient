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

.. autoclass:: zhmcclient.Job
   :members:
   :special-members: __str__


.. _`Retry-timeout configuration`:

Retry / timeout configuration
-----------------------------

.. autoclass:: zhmcclient.RetryTimeoutConfig
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

.. autoclass:: zhmcclient.ConnectTimeout
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.ReadTimeout
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.RetriesExceeded
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

.. autoclass:: zhmcclient.OperationTimeout
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.StatusTimeout
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.NotFound
   :members:
   :special-members: __str__

.. autoclass:: zhmcclient.NoUniqueMatch
   :members:
   :special-members: __str__


.. _`Constants`:

Constants
---------

.. automodule:: zhmcclient._constants
   :members:


.. _`Filtering`:

Filtering
---------

Some methods (e.g. :meth:`~zhmcclient.BaseManager.list` or
:meth:`~zhmcclient.BaseManager.find`) support the concept of resource
filtering. This concept allows narrowing the set of returned resources based
upon matching their resource properties against filter arguments.

The filter arguments are used to construct filter query parameters in the
HMC operations, so that they are processed on the server side by the HMC.

The methods that support resource filtering either have keyword arguments
``**filter_args``, or have a parameter ``filter_args`` that can be `None` for
no filtering or a dictionary to enable filtering. In both cases,
``filter_args`` is a dictionary.

The dictionary keys specify the names of the resource properties that need to
match for the resource to be included in the result. A resource is included
in the result only if all resource properties specified in the dictionary
match.

The dictionary value specifies how the corresponding resource property matches:

* For resource properties of type String (as per the resource's data model in
  the :term:`HMC API`), the dictionary value is interpreted as a regular
  expression that must match the actual resource property value. The regular
  expression syntax used is the same as that used by the Java programming
  language, as specified for the ``java.util.regex.Pattern`` class (see
  http://docs.oracle.com/javase/7/docs/api/java/util/regex/Pattern.html).

* For resource properties of type String Enum, the dictionary value is
  interpreted as an exact string that must be equal to the actual resource
  property value.

* TBD: What happens for other types of resource properties?

* If the dictionary value is a list or a tuple, the resource matches if any
  item in the list or tuple matches.

Examples:

* This example uses the :meth:`~zhmcclient.BaseManager.findall` method to
  return those OSA adapters in cage '1234' of a given CPC, whose state is
  'stand-by', 'reserved', or 'unknown'::

      filter_args = {
          'adapter-family': 'osa',
          'card-location': '1234-.*',
          'state': ['stand-by', 'reserved', 'unknown'],
      }
      osa_adapters = cpc.adapters.findall(**filter_args)

  The returned resource objects will have only a minimal set of properties.

* This example uses the :meth:`~zhmcclient.BaseManager.list` method to return
  the same set of OSA adapters as the previous example, but the returned
  resource objects have the full set of properties::

      osa_adapters = cpc.adapters.list(full_properties=True,
                                       filter_args=filter_args)
