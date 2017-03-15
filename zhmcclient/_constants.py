# Copyright 2017 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Public constants.

These constants are not meant to be changed by the user, they are made
available for inspection and documentation purposes only.

For technical reasons, the online documentation shows these constants in the
``zhmcclient._constants`` namespace, but they are also available in the
``zhmcclient`` namespace and should be used from there.
"""

__all__ = ['DEFAULT_CONNECT_TIMEOUT',
           'DEFAULT_CONNECT_RETRIES',
           'DEFAULT_READ_TIMEOUT',
           'DEFAULT_READ_RETRIES',
           'DEFAULT_MAX_REDIRECTS',
           'DEFAULT_OPERATION_TIMEOUT',
           'DEFAULT_STATUS_TIMEOUT']


#: Default HTTP connect timeout in seconds,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_CONNECT_TIMEOUT = 30

#: Default number of HTTP connect retries,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_CONNECT_RETRIES = 3

#: Default HTTP read timeout in seconds,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_READ_TIMEOUT = 300

#: Default number of HTTP read retries,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_READ_RETRIES = 3

#: Default max. number of HTTP redirects,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_MAX_REDIRECTS = 30

#: Default timeout in seconds for waiting for completion of an asynchronous
#: HMC operation. This is used as a default value in asynchronous methods on
#: resource objects (e.g. :meth:`zhmcclient.Partition.start`), in the
#: :meth:`zhmcclient.Job.wait_for_completion` method, and in the
#: low level method :meth:`zhmcclient.Session.post`.
DEFAULT_OPERATION_TIMEOUT = 3600

#: Default timeout in seconds for waiting for completion of deferred status
#: changes for LPARs. This is used as a default value in asynchronous methods
#: of the :class:`~zhmcclient.Lpar` class that change its status (e.g.
#: :meth:`zhmcclient.Lpar.activate`)).
DEFAULT_STATUS_TIMEOUT = 60
