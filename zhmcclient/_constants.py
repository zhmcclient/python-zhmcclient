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
           'DEFAULT_MAX_REDIRECTS']


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
DEFAULT_READ_TIMEOUT = 30

#: Default number of HTTP read retries,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_READ_RETRIES = 3

#: Default max. number of HTTP redirects,
#: if not specified in the ``retry_timeout_config`` init argument to
#: :class:`~zhmcclient.Session`.
DEFAULT_MAX_REDIRECTS = 30
