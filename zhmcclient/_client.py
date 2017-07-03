# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Client class: A client to an HMC.
"""

from __future__ import absolute_import

from ._cpc import CpcManager
from ._logging import get_logger, logged_api_call

__all__ = ['Client']

LOG = get_logger(__name__)


class Client(object):
    """
    A client to an HMC.

    This is the main class for users of this package.
    """

    def __init__(self, session):
        """
        Parameters:

          session (:class:`~zhmcclient.Session`):
            Session with the HMC.
        """
        self._session = session
        self._cpcs = CpcManager(self)
        self._api_version = None

    @property
    def session(self):
        """
        :class:`~zhmcclient.Session`:
          Session with the HMC.
        """
        return self._session

    @property
    def cpcs(self):
        """
        :class:`~zhmcclient.CpcManager`:
          Manager object for the CPCs in scope of this client (i.e. in scope
          of its HMC).
        """
        return self._cpcs

    @logged_api_call
    def version_info(self):
        """
        Returns API version information for the HMC.

        This operation does not require authentication.

        Returns:

          :term:`HMC API version`: The HMC API version supported by the HMC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if self._api_version is None:
            self.query_api_version()
        return self._api_version['api-major-version'],\
            self._api_version['api-minor-version']

    @logged_api_call
    def query_api_version(self):
        """
        The Query API Version operation returns information about
        the level of Web Services API supported by the HMC.

        This operation does not require authentication.

        Returns:

          :term:`json object`:
            A JSON object with members ``api-major-version``,
            ``api-minor-version``, ``hmc-version`` and ``hmc-name``.
            For details about these properties, see section
            'Response body contents' in section 'Query API Version' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ConnectionError`
        """
        version_resp = self._session.get('/api/version',
                                         logon_required=False)
        self._api_version = version_resp
        return self._api_version

    @logged_api_call
    def get_inventory(self, resources):
        """
        Returns a JSON object with the requested resources and their
        properties, that are managed by the HMC.

        This method performs the 'Get Inventory' HMC operation.

        Parameters:

          resources (:term:`iterable` of :term:`string`):
            Resource classes and/or resource classifiers specifying the types
            of resources that should be included in the result. For valid
            values, see the 'Get Inventory' operation in the :term:`HMC API`
            book.

            Element resources of the specified resource types are automatically
            included as children (for example, requesting 'partition' includes
            all of its 'hba', 'nic' and 'virtual-function' element resources).

            Must not be `None`.

        Returns:

          :term:`JSON object`:
            The resources with their properties, for the requested resource
            classes and resource classifiers.

        Example:

            resource_classes = ['partition', 'adapter']
            result_dict = client.get_inventory(resource_classes)

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ConnectionError`
        """
        uri = '/api/services/inventory'
        body = {'resources': resources}
        result = self.session.post(uri, body=body)
        return result
