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
from ._activation_profile import ActivationProfileManager
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
                cpc = Cpc(self, cpc_props['object-uri'], cpc_props)
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

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.CpcManager`):
            Manager object for this CPC.

          uri (string):
            Canonical URI path of the CPC object.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, CpcManager)
        super(Cpc, self).__init__(manager, uri, properties)
        # We do here some lazy loading.
        self._lpars = None
        self._partitions = None
        self._reset_activation_profiles = None
        self._image_activation_profiles = None
        self._load_activation_profiles = None

    @property
    @_log_call
    def lpars(self):
        """
        :class:`~zhmcclient.LparManager`: Manager object for the LPARs in this
        CPC.
        """
        # We do here some lazy loading.
        if not self._lpars:
            self._lpars = LparManager(self)
        return self._lpars

    @property
    @_log_call
    def partitions(self):
        """
        :class:`~zhmcclient.PartitionManager`: Manager object for the
        partitions in this CPC.
        """
        # We do here some lazy loading.
        if not self._partitions:
            self._partitions = PartitionManager(self)
        return self._partitions

    @property
    @_log_call
    def reset_activation_profiles(self):
        """
        :class:`~zhmcclient.ActivationManager`: Manager object for the
        Reset Activation Profiles in this CPC.
        `None`, if the CPC is in DPM mode.
        """
        # We do here some lazy loading.
        if not self._reset_activation_profiles:
            self._reset_activation_profiles = \
                ActivationProfileManager(self, profile_type='reset')
        return self._reset_activation_profiles

    @property
    @_log_call
    def image_activation_profiles(self):
        """
        :class:`~zhmcclient.ActivationManager`: Manager object for the
        Image Activation Profiles in this CPC.
        """
        # We do here some lazy loading.
        if not self._image_activation_profiles:
            self._image_activation_profiles = \
                ActivationProfileManager(self, profile_type='image')
        return self._image_activation_profiles

    @property
    @_log_call
    def load_activation_profiles(self):
        """
        :class:`~zhmcclient.ActivationManager`: Manager object for the
        Load Activation Profiles in this CPC.
        """
        # We do here some lazy loading.
        if not self._load_activation_profiles:
            self._load_activation_profiles = \
                ActivationProfileManager(self, profile_type='load')
        return self._load_activation_profiles

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
        Start this CPC, using the HMC operation "Start CPC".

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

        Returns:

          :term:`json object`:

            If `wait_for_completion` is `True`, returns None.

            If `wait_for_completion` is `False`, returns a JSON object with a
            member named ``job-uri``. The value of ``job-uri`` identifies the
            job that was started, and can be used with the
            :meth:`~zhmcclient.Session.query_job_status` method to determine
            the status of the job and the result of the asynchronous HMC
            operation, once the job has completed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.get_property('object-uri')
        result = self.manager.session.post(
            cpc_uri + '/operations/start',
            wait_for_completion=wait_for_completion)
        return result

    def stop(self, wait_for_completion=True):
        """
        Stop this CPC, using the HMC operation "Stop CPC".

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

        Returns:
          :term:`json object`:

            If `wait_for_completion` is `True`, returns None.

            If `wait_for_completion` is `False`, returns a JSON object with a
            member named ``job-uri``. The value of ``job-uri`` identifies the
            job that was started, and can be used with the
            :meth:`~zhmcclient.Session.query_job_status` method to determine
            the status of the job and the result of the asynchronous HMC
            operation, once the job has completed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.get_property('object-uri')
        result = self.manager.session.post(
            cpc_uri + '/operations/stop',
            wait_for_completion=wait_for_completion)
        return result

    @_log_call
    def import_profiles(self, profile_area, wait_for_completion=True):
        """
        Imports activation profiles and/or system activity profiles for the CPC
        from the SE hard drive into the CPC object using the HMC operation
        "Import Profiles".

        This operation is not permitted when the CPC is enabled for DPM.

        Parameters:

          profile_area (int):
             The numbered hard drive area (1-4) from which the profiles are
             imported.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

        Returns:

          :term:`json object`:

            If `wait_for_completion` is `True`, returns None.

            If `wait_for_completion` is `False`, returns a JSON object with a
            member named ``job-uri``. The value of ``job-uri`` identifies the
            job that was started, and can be used with the
            :meth:`~zhmcclient.Session.query_job_status` method to determine
            the status of the job and the result of the asynchronous HMC
            operation, once the job has completed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.get_property('object-uri')
        body = {'profile-area': profile_area}
        result = self.manager.session.post(
            cpc_uri + '/operations/import-profiles', body,
            wait_for_completion=wait_for_completion)
        return result

    @_log_call
    def export_profiles(self, profile_area, wait_for_completion=True):
        """
        Exports activation profiles and/or system activity profiles from the
        CPC object designated to the SE hard drive using the HMC operation
        "Export Profiles".

        This operation is not permitted when the CPC is enabled for DPM.

        Parameters:

          profile_area (int):
             The numbered hard drive area (1-4) to which the profiles are
             exported. Any existing data is overwritten.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

        Returns:

          :term:`json object`:

            If `wait_for_completion` is `True`, returns None.

            If `wait_for_completion` is `False`, returns a JSON object with a
            member named ``job-uri``. The value of ``job-uri`` identifies the
            job that was started, and can be used with the
            :meth:`~zhmcclient.Session.query_job_status` method to determine
            the status of the job and the result of the asynchronous HMC
            operation, once the job has completed.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.get_property('object-uri')
        body = {'profile-area': profile_area}
        result = self.manager.session.post(
            cpc_uri + '/operations/export-profiles', body,
            wait_for_completion=wait_for_completion)
        return result
