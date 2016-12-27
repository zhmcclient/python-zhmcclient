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
A :term:`CPC` (Central Processor Complex) is a physical z Systems or LinuxONE
computer.

A particular HMC can manage multiple CPCs.

The HMC can manage a range of old and new CPC generations. Some older CPC
generations are not capable of supporting the HMC Web Services API; these older
CPCs can be managed using the GUI of the HMC, but not through its Web Services
API. Therefore, such older CPCs will not be exposed at the HMC Web Services
API, and thus will not show up in the API of this Python package.

TODO: List earliest CPC generation that supports the HMC Web Services API.

A CPC can be in any of the following three modes:

- DPM mode: Dynamic Partition Manager is enabled for the CPC.
- Classic mode: The CPC does not have Dynamic Partition Manager enabled,
  and is not member of an ensemble.
- Ensemble mode: The CPC is member of an ensemble. This Python client
  does not support the functionality that is specific to ensemble mode.

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
from ._adapter import AdapterManager
from ._virtual_switch import VirtualSwitchManager
from ._logging import _log_call
from ._exceptions import HTTPError


__all__ = ['CpcManager', 'Cpc']


class CpcManager(BaseManager):
    """
    Manager providing access to the :term:`CPCs <CPC>` exposed by the HMC this
    client is connected to.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible as properties in higher level resources (in this case,
    the :class:`~zhmcclient.Client` object connecting to the HMC).
    """

    def __init__(self, client):
        # This function should not go into the docs.
        # Parameters:
        #   client (:class:`~zhmcclient.Client`):
        #      Client object for the HMC to be used.
        super(CpcManager, self).__init__(Cpc)
        self._session = client.session

    @_log_call
    def list(self, full_properties=False):
        """
        List the CPCs exposed by the HMC this client is connected to.

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
    Representation of a :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.CpcManager`).
    """

    def __init__(self, manager, uri, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.CpcManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        if not isinstance(manager, CpcManager):
            raise AssertionError("Cpc init: Expected manager type %s, got %s" %
                                 (CpcManager, type(manager)))
        super(Cpc, self).__init__(manager, uri, properties,
                                  uri_prop='object-uri',
                                  name_prop='name')
        # The manager objects for child resources (with lazy initialization):
        self._lpars = None
        self._partitions = None
        self._adapters = None
        self._virtual_switches = None
        self._reset_activation_profiles = None
        self._image_activation_profiles = None
        self._load_activation_profiles = None

    @property
    @_log_call
    def lpars(self):
        """
        :class:`~zhmcclient.LparManager`: Access to the :term:`LPARs <LPAR>` in
        this CPC.
        """
        # We do here some lazy loading.
        if not self._lpars:
            self._lpars = LparManager(self)
        return self._lpars

    @property
    @_log_call
    def partitions(self):
        """
        :class:`~zhmcclient.PartitionManager`: Access to the
        :term:`Partitions <Partition>` in this CPC.
        """
        # We do here some lazy loading.
        if not self._partitions:
            self._partitions = PartitionManager(self)
        return self._partitions

    @property
    @_log_call
    def adapters(self):
        """
        :class:`~zhmcclient.AdapterManager`: Access to the
        :term:`Adapters <Adapter>` in this CPC.
        """
        # We do here some lazy loading.
        if not self._adapters:
            self._adapters = AdapterManager(self)
        return self._adapters

    @property
    @_log_call
    def virtual_switches(self):
        """
        :class:`~zhmcclient.VirtualSwitchManager`: Access to the
        :term:`Virtual Switches <Virtual Switch>` in this CPC.
        """
        # We do here some lazy loading.
        if not self._virtual_switches:
            self._virtual_switches = VirtualSwitchManager(self)
        return self._virtual_switches

    @property
    def vswitches(self):
        """
        Deprecated: Use :attr:`~zhmcclient.Cpc.virtual_switches` instead.
        """
        # TODO: Issue a deprecation warning
        return self.virtual_switches

    @property
    @_log_call
    def reset_activation_profiles(self):
        """
        :class:`~zhmcclient.ActivationProfileManager`: Access to the
        :term:`Reset Activation Profiles <Reset Activation Profile>` in this
        CPC.
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
        :class:`~zhmcclient.ActivationProfileManager`: Access to the
        :term:`Image Activation Profiles <Image Activation Profile>` in this
        CPC.
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
        :class:`~zhmcclient.ActivationProfileManager`: Access to the
        :term:`Load Activation Profiles <load Activation Profile>` in this
        CPC.
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
        # This is an optimized implementation that is faster than the
        # "Get CPC Properties" operation (which would return the information
        # directly in its "dpm-enabled" property).
        try:
            # We perform a test operation that only succeeds when the CPC is in
            # DPM mode:
            self.partitions.list()
            return True
        except HTTPError as exc:
            if exc.http_status == 404 and exc.reason == 1:
                # Description of this error: The request URI does not designate
                # an existing resource of the expected type, or designates a
                # resource for which the API user does not have object-access
                # permission.
                # Because this error response does not distinguish between
                # these two cases, we need to perform the opposite test
                # operation as well:
                self.lpars.list()
                return False
            else:
                raise

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
        result = self.manager.session.post(
            self.uri + '/operations/start',
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
        result = self.manager.session.post(
            self.uri + '/operations/stop',
            wait_for_completion=wait_for_completion)
        return result

    @_log_call
    def import_profiles(self, profile_area, wait_for_completion=True):
        """
        Import activation profiles and/or system activity profiles for this CPC
        from the SE hard drive into the CPC using the HMC operation
        "Import Profiles".

        This operation is not permitted when the CPC is in DPM mode.

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
        body = {'profile-area': profile_area}
        result = self.manager.session.post(
            self.uri + '/operations/import-profiles', body,
            wait_for_completion=wait_for_completion)
        return result

    @_log_call
    def export_profiles(self, profile_area, wait_for_completion=True):
        """
        Export activation profiles and/or system activity profiles from this
        CPC to the SE hard drive using the HMC operation "Export Profiles".

        This operation is not permitted when the CPC is in DPM mode.

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
        body = {'profile-area': profile_area}
        result = self.manager.session.post(
            self.uri + '/operations/export-profiles', body,
            wait_for_completion=wait_for_completion)
        return result

    def get_wwpns(self, partitions):
        """
        Return the WWPNs of the host ports (of the :term:`HBAs <HBA>`) of the
        specified :term:`Partitions <Partition>` of this CPC.

        This method performs the HMC operation "Export WWPN List".

        Parameters:

          partitions (:term:`iterable` of :class:`~zhmcclient.Partition`):
            :term:`Partitions <Partition>` to be used.

        Returns:

          A list of items for each WWPN, where each item is a dict with the
          following keys:

          * 'partition-name' (string): Name of the :term:`Partition`.
          * 'adapter-id' (string): ID of the :term:`FCP Adapter`.
          * 'device-number' (string): Virtual device number of the :term:`HBA`.
          * 'wwpn' (string): WWPN of the HBA.

        Raises:

          :exc:`~zhmcclient.HTTPError`: See the HTTP status and reason codes of
            operation "Export WWPN List" in the :term:`HMC API` book.
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'partitions': [p.uri for p in partitions]}
        result = self.manager.session.post(self._uri + '/operations/'
                                           'export-port-names-list', body=body)
        # Parse the returned comma-separated string for each WWPN into a dict:
        wwpn_list = []
        dict_keys = ('partition-name', 'adapter-id', 'device-number', 'wwpn')
        for wwpn_item in result['wwpn-list']:
            dict_values = wwpn_item.split(',')
            wwpn_list.append(dict(zip(dict_keys, dict_values)))
        return wwpn_list
