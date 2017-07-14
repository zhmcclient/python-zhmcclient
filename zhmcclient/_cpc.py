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

import warnings
import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._lpar import LparManager
from ._partition import PartitionManager
from ._activation_profile import ActivationProfileManager
from ._adapter import AdapterManager
from ._virtual_switch import VirtualSwitchManager
from ._logging import get_logger, logged_api_call

__all__ = ['CpcManager', 'Cpc']

LOG = get_logger(__name__)


class CpcManager(BaseManager):
    """
    Manager providing access to the :term:`CPCs <CPC>` exposed by the HMC this
    client is connected to.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Client` object:

    * :attr:`~zhmcclient.Client.cpcs`
    """

    def __init__(self, client):
        # This function should not go into the docs.
        # Parameters:
        #   client (:class:`~zhmcclient.Client`):
        #      Client object for the HMC to be used.

        # Resource properties that are supported as filter query parameters
        # (for server-side filtering).
        query_props = [
            'name',
        ]

        super(CpcManager, self).__init__(
            resource_class=Cpc,
            class_name='cpc',
            session=client.session,
            parent=None,
            base_uri='/api/cpcs',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props)

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the CPCs exposed by the HMC this client is connected to.

        Authorization requirements:

        * Object-access permission to any CPC to be included in the result.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          : A list of :class:`~zhmcclient.Cpc` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        resource_obj_list = []
        resource_obj = self._try_optimized_lookup(filter_args)
        if resource_obj:
            resource_obj_list.append(resource_obj)
            # It already has full properties
        else:
            query_parms, client_filters = self._divide_filter_args(filter_args)

            resources_name = 'cpcs'
            uri = '/api/{}{}'.format(resources_name, query_parms)

            result = self.session.get(uri)
            if result:
                props_list = result[resources_name]
                for props in props_list:

                    resource_obj = self.resource_class(
                        manager=self,
                        uri=props[self._uri_prop],
                        name=props.get(self._name_prop, None),
                        properties=props)

                    if self._matches_filters(resource_obj, client_filters):
                        resource_obj_list.append(resource_obj)
                        if full_properties:
                            resource_obj.pull_full_properties()

        self._name_uri_cache.update_from(resource_obj_list)
        return resource_obj_list


class Cpc(BaseResource):
    """
    Representation of a :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.CpcManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.CpcManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, CpcManager), \
            "Cpc init: Expected manager type %s, got %s" % \
            (CpcManager, type(manager))
        super(Cpc, self).__init__(manager, uri, name, properties)

        # The manager objects for child resources (with lazy initialization):
        self._lpars = None
        self._partitions = None
        self._adapters = None
        self._virtual_switches = None
        self._reset_activation_profiles = None
        self._image_activation_profiles = None
        self._load_activation_profiles = None

    @property
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
        :class:`~zhmcclient.VirtualSwitchManager`: Access to the
        :term:`Virtual Switches <Virtual Switch>` in this CPC.

        **Deprecated:** This attribute is deprecated and using it will cause a
        :exc:`~py:exceptions.DeprecationWarning` to be issued. Use
        :attr:`~zhmcclient.Cpc.virtual_switches` instead.
        """
        warnings.warn(
            "Use of the vswitches attribute on zhmcclient.Cpc objects is "
            "deprecated; use the virtual_switches attribute instead",
            DeprecationWarning)
        return self.virtual_switches

    @property
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
    @logged_api_call
    def dpm_enabled(self):
        """
        bool: Indicates whether this CPC is currently in DPM mode
        (Dynamic Partition Manager mode).

        If the CPC is not currently in DPM mode, or if the CPC does not
        support DPM mode (i.e. before z13), `False` is returned.

        Authorization requirements:

        * Object-access permission to this CPC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        return self.prop('dpm-enabled', False)

    _MAX_PARTITIONS_BY_MACHINE_TYPE = {
        '2817': 60,  # z196
        '2818': 30,  # z114
        '2827': 60,  # zEC12
        '2828': 30,  # zBC12
        '2964': 85,  # z13 / Emperor
        '2965': 40,  # z13s / Rockhopper
    }

    @property
    @logged_api_call
    def maximum_active_partitions(self):
        """
        Integer: The maximum number of active logical partitions or partitions
        of this CPC.

        The following table shows the maximum number of active logical
        partitions or partitions by machine generations supported at the HMC
        API:

        ==================  ==================
        Machine generation  Maximum partitions
        ==================  ==================
        z196                                60
        z114                                30
        zEC12                               60
        zBC12                               30
        z13 / Emperor                       85
        z13s / Rockhopper                   40
        ==================  ==================

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`ValueError`: Unknown machine type
        """
        machine_type = self.get_property('machine-type')
        try:
            max_parts = self._MAX_PARTITIONS_BY_MACHINE_TYPE[machine_type]
        except KeyError:
            raise ValueError("Unknown machine type: {!r}".format(machine_type))
        return max_parts

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this CPC.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "CPC Details" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'CPC' in the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self.uri, body=properties)
        # Attempts to change the 'name' property will be rejected by the HMC,
        # so we don't need to update the name-to-URI cache.
        assert self.manager._name_prop not in properties
        self.properties.update(copy.deepcopy(properties))

    @logged_api_call
    def start(self, wait_for_completion=True, operation_timeout=None):
        """
        Start this CPC, using the HMC operation "Start CPC".

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "Start (start a single DPM system)" task.

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Returns:

          `None` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns `None`.

            If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        result = self.manager.session.post(
            self.uri + '/operations/start',
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def stop(self, wait_for_completion=True, operation_timeout=None):
        """
        Stop this CPC, using the HMC operation "Stop CPC".

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "Stop (stop a single DPM system)" task.

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Returns:

          `None` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns `None`.

            If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        result = self.manager.session.post(
            self.uri + '/operations/stop',
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def import_profiles(self, profile_area, wait_for_completion=True,
                        operation_timeout=None):
        """
        Import activation profiles and/or system activity profiles for this CPC
        from the SE hard drive into the CPC using the HMC operation
        "Import Profiles".

        This operation is not permitted when the CPC is in DPM mode.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "CIM Actions ExportSettingsData" task.

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

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Returns:

          `None` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns `None`.

            If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        body = {'profile-area': profile_area}
        result = self.manager.session.post(
            self.uri + '/operations/import-profiles',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def export_profiles(self, profile_area, wait_for_completion=True,
                        operation_timeout=None):
        """
        Export activation profiles and/or system activity profiles from this
        CPC to the SE hard drive using the HMC operation "Export Profiles".

        This operation is not permitted when the CPC is in DPM mode.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "CIM Actions ExportSettingsData" task.

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

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Returns:

          `None` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns `None`.

            If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        body = {'profile-area': profile_area}
        result = self.manager.session.post(
            self.uri + '/operations/export-profiles',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def get_wwpns(self, partitions):
        """
        Return the WWPNs of the host ports (of the :term:`HBAs <HBA>`) of the
        specified :term:`Partitions <Partition>` of this CPC.

        This method performs the HMC operation "Export WWPN List".

        Authorization requirements:

        * Object-access permission to this CPC.
        * Object-access permission to the Partitions designated by the
          "partitions" parameter.
        * Task permission for the "Export WWPNs" task.

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

    @logged_api_call
    def get_free_crypto_domains(self, crypto_adapters):
        """
        Return a list of free crypto domains for the specified crypto adapters.

        Free crypto domains for a set of crypto adapters are those that are not
        assigned to any partition of this CPC on any of these crypto adapters,
        i.e. they are unassigned on all of these crypto adapters.

        This method requires the CPC to be in DPM mode.

        **Experimental:** This method has been added in v0.14.0 and is
        currently considered experimental. Its interface may change
        incompatibly. Once the interface remains stable, this experimental
        marker will be removed.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Object-access permission to all of its Partitions.
        * Object-access permission to all of its crypto Adapters.

        Parameters:

          crypto_adapters (:term:`iterable` of :class:`~zhmcclient.Adapter`):
            The crypto :term:`Adapters <Adapter>` to be investigated.
            `None` means to investigate all crypto adapters of this CPC.

        Returns:

          A list of domain index numbers (integers) of the free crypto domains.
          Returns `None`, if no crypto adapters were specified or defaulted.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        max_domains = None  # maximum number of domains across all adapters
        used_domains = set()

        if crypto_adapters is None:
            crypto_adapters = self.adapters.findall(type='crypto')

        if not crypto_adapters:
            # No crypto adapters were specified or defaulted.
            return None

        # We determine the maximum number of crypto domains independently
        # of the partitions, because (1) it is possible that no partition
        # has a crypto configuration and (2) further down we want the inner
        # loop to be on the crypto adapters because accessing them multiple
        # times does not drive additional HMC operations.
        for ca in crypto_adapters:
            if max_domains is None:
                max_domains = ca.maximum_crypto_domains
            else:
                max_domains = min(ca.maximum_crypto_domains, max_domains)

        partitions = self.partitions.list(full_properties=True)
        for partition in partitions:
            crypto_config = partition.get_property('crypto-configuration')
            if crypto_config:
                adapter_uris = crypto_config['crypto-adapter-uris']
                domain_configs = crypto_config['crypto-domain-configurations']
                for ca in crypto_adapters:
                    if ca.uri in adapter_uris:
                        used_adapter_domains = [dc['domain-index']
                                                for dc in domain_configs]
                        used_domains.update(used_adapter_domains)

        all_domains = set(range(0, max_domains))
        free_domains = all_domains - used_domains
        return sorted(list(free_domains))
