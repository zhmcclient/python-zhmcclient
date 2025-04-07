# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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


import time
import yaml

from ._cpc import CpcManager
from ._console import ConsoleManager
from ._metrics import MetricsContextManager, MetricsResponse, CLASS_FROM_GROUP
from ._logging import logged_api_call
from ._exceptions import Error, OperationTimeout

__all__ = ['Client']


class Client:
    """
    A client to an HMC.

    This is the main class for users of this package.

    HMC/SE version requirements: None
    """

    def __init__(self, session):
        """
        Parameters:

          session (:class:`~zhmcclient.Session`):
            Session with the HMC.
        """
        self._session = session
        self._cpcs = CpcManager(self)
        self._consoles = ConsoleManager(self)
        self._metrics_contexts = MetricsContextManager(self)
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
          Manager object for the CPCs in scope of this client. This includes
          managed and unmanaged CPCs.
        """
        return self._cpcs

    @property
    def consoles(self):
        """
        :class:`~zhmcclient.ConsoleManager`:
          Manager object for the (one) Console representing the HMC this client
          is connected to.
        """
        return self._consoles

    @property
    def metrics_contexts(self):
        """
        :class:`~zhmcclient.MetricsContextManager`:
          Manager object for the :term:`Metrics Contexts <Metrics Context>` in
          scope of this client (i.e. in scope of its HMC).
        """
        return self._metrics_contexts

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
        return self._api_version['api-major-version'], \
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

        If resources cannot be fully inventoried, the returned list contains
        items describing the errors. They can be identified by their 'class'
        property having a value of 'inventory-error'. Note that the presence
        of such error items does not cause any exceptions to be raised.

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

          list of dict: The list of resources for the requested resource
            classes and resource classifiers. Each list item is a dictionary
            with the resource properties using the HMC property names.

        Example:

            resource_classes = ['partition', 'adapter']
            resource_list = client.get_inventory(resource_classes)

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.ConnectionError`
        """
        uri = '/api/services/inventory'
        body = {'resources': resources}
        result = self.session.post(uri, body=body)
        return result

    @logged_api_call
    def wait_for_available(self, operation_timeout=None):
        """
        Wait for the Console (HMC) this client is connected to, to become
        available. The Console is considered available if the
        :meth:`~zhmcclient.Client.query_api_version` method succeeds.

        If the Console does not become available within the operation timeout,
        an :exc:`~zhmcclient.OperationTimeout` exception is raised.

        Parameters:

          operation_timeout (:term:`number`):
            Timeout in seconds, when waiting for the Console to become
            available. The special value 0 means that no timeout is set. `None`
            means that the default async operation timeout of the session is
            used.

            If the timeout expires, a :exc:`~zhmcclient.OperationTimeout`
            is raised.

        Raises:

          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for the Console to become available.
        """
        if operation_timeout is None:
            operation_timeout = \
                self.session.retry_timeout_config.operation_timeout
        if operation_timeout > 0:
            start_time = time.time()
        while True:
            try:
                self.query_api_version()
            except Error:
                pass
            else:
                break
            if operation_timeout > 0:
                current_time = time.time()
                # noinspection PyUnboundLocalVariable
                if current_time > start_time + operation_timeout:
                    raise OperationTimeout(
                        f"Waiting for Console at {self.session.host} to become "
                        "available timed out (operation timeout: "
                        f"{operation_timeout} s)", operation_timeout)
            time.sleep(10)  # Avoid hot spin loop

    def to_hmc_yaml(self):
        """
        Inspect the HMC of this client and return the HMC and its resources
        as an HMC definition YAML string.

        This method can be used on clients for sessions to real HMCs and
        faked sessions.

        The returned YAML string can be used to instantiate a faked session
        using :meth:`zhmcclient_mock.FakedSession.from_hmc_yaml`.

        The returned HMC definition YAML string has the following format::

            hmc_definition:

              # Internal state:
              host: hmc1
              api_version: '2.20'
              metric_group_definitions: [...]
              metric_values: [...]

              # Child resources:
              metrics_contexts:
              - properties: {...}
              consoles:
              - properties: {...}
                storage_groups:
                - properties: {...}
                ...
              cpcs:
              - properties: {...}
                partitions:
                - properties: {...}
                ...

        Returns:

          string: HMC definition YAML string.
        """
        hmc_dict = self.to_hmc_dict()
        hmc_yaml = yaml.safe_dump(
            hmc_dict,
            encoding=None, allow_unicode=True,
            default_flow_style=False, indent=2)
        return hmc_yaml

    def to_hmc_dict(self):
        """
        Inspect the HMC of this client and return the HMC and its resources
        as an HMC definition dictionary.

        This method can be used on clients for sessions to real HMCs and
        faked sessions.

        The returned dictionary has only items of type dict, list, string,
        int, float, bool or None. That makes it convertible to simple formats
        such as JSON or YAML, so it can be externalized (e.g. persisted).

        The returned dictionary can be used to instantiate a faked session
        using :meth:`zhmcclient_mock.FakedSession.from_hmc_dict`.

        The returned HMC definition dictionary has the following format::

            {
                "hmc_definition": {

                    # Internal state:
                    "host": "hmc1",
                    "api_version": "2.20",
                    "metric_group_definitions": [...],
                    "metric_values": [...],

                    # Child resources:
                    "metrics_contexts": [...],
                    "consoles": [...],
                    "cpcs": [...],
                }
            }

        Returns:

          dict: HMC definition dictionary.
        """
        resource_dict = self.dump()
        hmc_dict = {
            'hmc_definition': resource_dict
        }
        return hmc_dict

    def dump(self):
        """
        Dump this Client with its properties and child resources
        (recursively) as a resource definition.

        The returned resource definition has the following format::

            {
                # Internal state:
                "host": "hmc1",
                "api_version": "2.20",
                "metric_values": [...],

                # Child resources:
                "metrics_contexts": [...],
                "consoles": [...],
                "cpcs": [...],
            }

        Returns:

          dict: Resource definition of this Client.
        """

        resource_dict = {}

        # Dump internal state
        av = self.query_api_version()
        api_version_str = f"{av['api-major-version']}.{av['api-minor-version']}"
        resource_dict['host'] = self.session.host
        resource_dict['api_version'] = api_version_str

        # Get the current metric values for all metric groups and dump them
        mc = self.metrics_contexts.create({
            'anticipated-frequency-seconds': 15,
            'metric-groups': list(CLASS_FROM_GROUP.keys()),
        })
        mr_str = mc.get_metrics()
        mr = MetricsResponse(mc, mr_str)
        mc.delete()
        resource_dict['metric_values'] = []
        for mg in mr.metric_group_values:
            for mv in mg.object_values:
                mv_dict = mv.dump()
                if mv_dict:
                    resource_dict['metric_values'].append(mv_dict)

        # Dump child resources
        metrics_contexts = self.metrics_contexts.dump()
        if metrics_contexts:
            resource_dict['metrics_contexts'] = metrics_contexts
        consoles = self.consoles.dump()
        if consoles:
            resource_dict['consoles'] = consoles
        cpcs = self.cpcs.dump()
        if cpcs:
            resource_dict['cpcs'] = cpcs

        return resource_dict
