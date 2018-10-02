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
           'DEFAULT_HMC_PORT',
           'DEFAULT_READ_TIMEOUT',
           'DEFAULT_READ_RETRIES',
           'DEFAULT_STOMP_PORT',
           'DEFAULT_MAX_REDIRECTS',
           'DEFAULT_OPERATION_TIMEOUT',
           'DEFAULT_STATUS_TIMEOUT',
           'DEFAULT_NAME_URI_CACHE_TIMETOLIVE',
           'HMC_LOGGER_NAME',
           'API_LOGGER_NAME',
           'HTML_REASON_WEB_SERVICES_DISABLED',
           'HTML_REASON_OTHER']


#: Default HTTP connect timeout in seconds,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_CONNECT_TIMEOUT = 30

#: Default number of HTTP connect retries,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_CONNECT_RETRIES = 3

#: Default HMC port number
DEFAULT_HMC_PORT = 6794

#: Default HTTP read timeout in seconds,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
#:
#: Note: The default value for this parameter has been increased to a large
#: value in order to mitigate the behavior of the 'requests' module to
#: retry HTTP methods even if they are not idempotent (e.g. DELETE).
#: See zhmcclient `issue #249
#: <https://github.com/zhmcclient/python-zhmcclient/issues/249>`_.
DEFAULT_READ_TIMEOUT = 3600

#: Default port on which the HMC issues JMS over STOMP messages.
DEFAULT_STOMP_PORT = 61612

#: Default number of HTTP read retries,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
#:
#: Note: The default value for this parameter has been set to 0 in order to
#: mitigate the behavior of the 'requests' module to retry HTTP methods even if
#: they are not idempotent (e.g. DELETE).
#: See zhmcclient `issue #249
#: <https://github.com/zhmcclient/python-zhmcclient/issues/249>`_.
DEFAULT_READ_RETRIES = 0

#: Default max. number of HTTP redirects,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_MAX_REDIRECTS = 30

#: Default timeout in seconds for waiting for completion of an asynchronous
#: HMC operation,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
#:
#: This is used as a default value in asynchronous methods on
#: resource objects (e.g. :meth:`zhmcclient.Partition.start`), in the
#: :meth:`zhmcclient.Job.wait_for_completion` method, and in the
#: low level method :meth:`zhmcclient.Session.post`.
DEFAULT_OPERATION_TIMEOUT = 3600

#: Default timeout in seconds for waiting for completion of deferred status
#: changes for LPARs,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
#:
#: This is used as a default value in asynchronous methods
#: of the :class:`~zhmcclient.Lpar` class that change its status (e.g.
#: :meth:`zhmcclient.Lpar.activate`)).
DEFAULT_STATUS_TIMEOUT = 900

#: Default time to the next automatic invalidation of the Name-URI cache of
#: manager objects, in seconds since the last invalidation,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
#:
#: The special value 0 means that no Name-URI cache is maintained (i.e. the
#: caching is disabled).
DEFAULT_NAME_URI_CACHE_TIMETOLIVE = 300

#: Name of the Python logger that logs HMC operations.
HMC_LOGGER_NAME = 'zhmcclient.hmc'

#: Name of the Python logger that logs zhmcclient API calls made by the user.
API_LOGGER_NAME = 'zhmcclient.api'

#: HTTP reason code: Web Services API is not enabled on the HMC.
HTML_REASON_WEB_SERVICES_DISABLED = 900

#: HTTP reason code: Other HTML-formatted error response. Note that over time,
#: there may be more specific reason codes introduced for such situations.
HTML_REASON_OTHER = 999
