# Copyright 2016 IBM Corp. All Rights Reserved.
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
A **Central Processor Complex (CPC)** is a physical z Systems or LinuxONE
computer. A particular HMC can manage multiple CPCs.

The HMC can manage a range of old and new CPC generations. Some older CPC
generations are not capable of supporting the HMC Web Services API; these older
CPCs can be managed using the GUI of the HMC, but not through its Web Services
API. Therefore, such older CPCs will not show up at the HMC Web Services API,
and thus will not show up in the API of this Python package.

TODO: List earliest CPC generation that supports the HMC Web Services API.

A CPC can be in any of the following three modes:

- DPM mode: Dynamic Partition Manager is enabled for the CPC.
- Ensemble mode: The CPC is member of an ensemble. This Python client
  does not support the functionality that is specific to ensemble mode.
- Classic mode: The CPC does not have Dynamic Partition Manager enabled,
  and is not member of an ensemble.

The functionality supported at the HMC API and thus also for users of this
Python client, depends on the mode in which the CPC currently is. If a
particular functionality is available only in a specific mode, that is
indicated in the description of the functionality.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._lpar import LparManager
from ._partition import PartitionManager
from ._logging import _log_call


__all__ = ['CpcManager', 'Cpc']


class CpcManager(BaseManager):
    """
    Manager object for CPCs. This manager object is scoped to the HMC Web
    Services API capable CPCs managed by the HMC that is associated with a
    particular client.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, client):
        """
        Parameters:

          client (:class:`~zhmcclient.Client`):
            Client object for the HMC to be used.
        """
        super(CpcManager, self).__init__()
        self._session = client.session

    @_log_call
    def list(self, full_properties=False):
        """
        List the CPCs in scope of this manager object.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.Cpc` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpcs_res = self.session.get('/api/cpcs')
        cpc_list = []
        if cpcs_res:
            cpc_items = cpcs_res['cpcs']
            for cpc_props in cpc_items:
                cpc = Cpc(self, cpc_props)
                if full_properties:
                    cpc.pull_full_properties()
                cpc_list.append(cpc)
        return cpc_list


class Cpc(BaseResource):
    """
    Representation of a CPC.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.
    """

    def __init__(self, manager, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.CpcManager`):
            Manager object for this CPC.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, CpcManager)
        super(Cpc, self).__init__(manager, properties)
        # We do here some lazy loading.
        self._lpars = None
        self._partitions = None

    @property
    @_log_call
    def lpars(self):
        """
        :class:`~zhmcclient.LparManager`: Manager object for the LPARs in this
        CPC. `None`, if the CPC is in DPM mode.
        """
        # We do here some lazy loading.
        if not self._lpars:
            if self.dpm_enabled:
                self._lpars = None
            else:
                self._lpars = LparManager(self)
        return self._lpars

    @property
    @_log_call
    def partitions(self):
        """
        :class:`~zhmcclient.PartitionManager`: Manager object for the
        partitions in this CPC. `None`, if the CPC is not in DPM mode.
        """
        # We do here some lazy loading.
        if not self._partitions:
            if self.dpm_enabled:
                self._partitions = PartitionManager(self)
            else:
                self._partitions = None
        return self._partitions

    @property
    @_log_call
    def dpm_enabled(self):
        """
        bool: Indicates whether this CPC is currently in DPM mode
        (Dynamic Partition Manager mode).

        If the CPC is not currently in DPM mode, or if the CPC does not
        support DPM mode (i.e. before z13), `False` is returned.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        try:
            return self.get_property('dpm-enabled')
        except KeyError:
            return False

    def start(self, wait_for_completion=True):
        """
        Start this CPC.

        Parameters:

          wait_for_completion (bool):
            Boolean indicating whether the method should wait until
            the operation/job has completed.
            If wait_for_completion is 'False' the status of the operation/job
            has to be retrieved via the method 'query_job_status' method.

        Returns:

          :term:`json object` with the operation result.

            In the default case of a synchronous operation
            (wait_for_completion=True) the return value is a JSON object with
            members like status, job-status-code and job-reason-code.
            See the respective sections in :term:`HMC API` for a description
            of the response body contents of the Query Job Status operation.

            In case of an asynchronous operation (wait_for_completion=False),
            the return value is a JSON object with a member job-id whose value
            needs to be used for query_job_status().

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.get_property('object-uri')
        result = self.manager.session.post(cpc_uri + '/operations/start',
            wait_for_completion=wait_for_completion)
        return result

    def stop(self, wait_for_completion=True):
        """
        Stop this CPC.

        Parameters:

          wait_for_completion (bool):
            Boolean indicating whether the method should wait until
            the operation/job has completed.
            If wait_for_completion is 'False' the status of the operation/job
            has to be retrieved via the method 'query_job_status' method.

        Returns:

          :term:`json object` with the operation result.

            In the default case of a synchronous operation
            (wait_for_completion=True) the return value is a JSON object with
            members like status, job-status-code and job-reason-code.
            See the respective sections in :term:`HMC API` for a description
            of the response body contents of the Query Job Status operation.

            In case of an asynchronous operation (wait_for_completion=False),
            the return value is a JSON object with a member job-id whose value
            needs to be used for query_job_status().

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.get_property('object-uri')
        result = self.manager.session.post(cpc_uri + '/operations/stop',
            wait_for_completion=wait_for_completion)
        return result
