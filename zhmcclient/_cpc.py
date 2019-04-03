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
A :term:`CPC` (Central Processor Complex) is a physical IBM Z or LinuxONE
computer.

A particular HMC can manage multiple CPCs and can discover other CPCs that
are not managed by that HMC. Such other CPCs are called "unmanaged CPCs" and
they may or may not be managed by another HMC.

This section describes the interface for *managed* CPCs using resource class
:class:`~zhmcclient.Cpc` and the corresponding manager class
:class:`~zhmcclient.CpcManager`.

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
from ._logging import logged_api_call
from ._exceptions import ParseError

__all__ = ['CpcManager', 'Cpc']


class CpcManager(BaseManager):
    """
    Manager providing access to the managed :term:`CPCs <CPC>` exposed by the
    HMC this client is connected to.

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
        self._client = client

    @property
    def client(self):
        """
        :class:`~zhmcclient.Client`:
          The client defining the scope for this manager.
        """
        return self._client

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`:
          The :term:`Console` representing the HMC this CPC is managed by.

          The returned object is cached, so it is looked up only upon first
          access to this property.

          The returned object has only the following properties set:

          * 'object-uri'

          Use :meth:`~zhmcclient.BaseResource.get_property` or
          :meth:`~zhmcclient.BaseResource.prop` to access any properties
          regardless of whether they are already set or first need to be
          retrieved.
        """
        return self.client.consoles.console

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the CPCs managed by the HMC this client is connected to.

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
    Representation of a managed :term:`CPC`.

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
        '3906': 85,  # z14 / Emperor II
        '3907': 40,  # z14-ZR1 / Rockhopper II
        # Note: From HMC API version 2.24 on, the Cpc object supports a
        # 'maximum-partitions' property. Because that API version was
        # introduced while model 3907 was already avbailable, the property is
        # guaranteed to be available only on models after 3907.
        # TODO: Exploit the new 'maximum-partitions' property.
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

        =========================  ==================
        Machine generation         Maximum partitions
        =========================  ==================
        z196                                      60
        z114                                      30
        zEC12                                     60
        zBC12                                     30
        z13 / Emperor                             85
        z13s / Rockhopper                         40
        z14 / Emperor II                          85
        z14-ZR1 / Rockhopper II                   40
        =========================  ==================

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
    def feature_enabled(self, feature_name):
        """
        Indicates whether the specified feature is enabled for this CPC.

        The HMC must generally support features, and the specified feature must
        be available for the CPC.

        For a list of available features, see section "Features" in the
        :term:`HMC API`, or use the :meth:`feature_info` method.

        Authorization requirements:

        * Object-access permission to this CPC.

        Parameters:

          feature_name (:term:`string`): The name of the feature.

        Returns:

          bool: `True` if the feature is enabled, or `False` if the feature is
          disabled (but available).

        Raises:

          :exc:`ValueError`: Features are not supported on the HMC.
          :exc:`ValueError`: The specified feature is not available for the
            CPC.
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        feature_list = self.prop('available-features-list', None)
        if feature_list is None:
            raise ValueError("Firmware features are not supported on CPC %s" %
                             self.name)
        for feature in feature_list:
            if feature['name'] == feature_name:
                break
        else:
            raise ValueError("Firmware feature %s is not available on CPC %s" %
                             (feature_name, self.name))
        return feature['state']

    @logged_api_call
    def feature_info(self):
        """
        Returns information about the features available for this CPC.

        Authorization requirements:

        * Object-access permission to this CPC.

        Returns:

          :term:`iterable`:
            An iterable where each item represents one feature that is
            available for this CPC.

            Each item is a dictionary with the following items:

            * `name` (:term:`unicode string`): Name of the feature.
            * `description` (:term:`unicode string`): Short description of
              the feature.
            * `state` (bool): Enablement state of the feature (`True` if the
              enabled, `False` if disabled).

        Raises:

          :exc:`ValueError`: Features are not supported on the HMC.
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        feature_list = self.prop('available-features-list', None)
        if feature_list is None:
            raise ValueError("Firmware features are not supported on CPC %s" %
                             self.name)
        return feature_list

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
    def get_free_crypto_domains(self, crypto_adapters=None):
        """
        Return a list of crypto domains that are free for usage on a list of
        crypto adapters in this CPC.

        A crypto domain is considered free for usage if it is not assigned to
        any defined partition of this CPC in access mode 'control-usage' on any
        of the specified crypto adapters.

        For this test, all currently defined partitions of this CPC are
        checked, regardless of whether or not they are active. This ensures
        that a crypto domain that is found to be free for usage can be assigned
        to a partition for 'control-usage' access to the specified crypto
        adapters, without causing a crypto domain conflict when activating that
        partition.

        Note that a similar notion of free domains does not exist for access
        mode 'control', because a crypto domain on a crypto adapter can be
        in control access by multiple active partitions.

        This method requires the CPC to be in DPM mode.

        **Example:**

            .. code-block:: text

                           crypto domains
               adapters     0   1   2   3
                          +---+---+---+---+
                 c1       |A,c|a,c|   | C |
                          +---+---+---+---+
                 c2       |b,c|B,c| B | C |
                          +---+---+---+---+

            In this example, the CPC has two crypto adapters c1 and c2. For
            simplicity of the example, we assume these crypto adapters support
            only 4 crypto domains.

            Partition A uses only adapter c1 and has domain 0 in
            'control-usage' access (indicated by an upper case letter 'A' in
            the corresponding cell) and has domain 1 in 'control' access
            (indicated by a lower case letter 'a' in the corresponding cell).

            Partition B uses only adapter c2 and has domain 0 in 'control'
            access and domains 1 and 2 in 'control-usage' access.

            Partition C uses both adapters, and has domains 0 and 1 in
            'control' access and domain 3 in 'control-usage' access.

            The domains free for usage in this example are shown in the
            following table, for each combination of crypto adapters to be
            investigated:

            ===============  ======================
            crypto_adapters  domains free for usage
            ===============  ======================
            c1               1, 2
            c2               0
            c1, c2           (empty list)
            ===============  ======================

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

          A sorted list of domain index numbers (integers) of the crypto
          domains that are free for usage on the specified crypto adapters.

          Returns `None`, if ``crypto_adapters`` was an empty list or if
          ``crypto_adapters`` was `None` and the CPC has no crypto adapters.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
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
        max_domains = None  # maximum number of domains across all adapters
        for ca in crypto_adapters:
            if max_domains is None:
                max_domains = ca.maximum_crypto_domains
            else:
                max_domains = min(ca.maximum_crypto_domains, max_domains)

        used_domains = set()  # Crypto domains used in control-usage mode
        partitions = self.partitions.list(full_properties=True)
        for partition in partitions:
            crypto_config = partition.get_property('crypto-configuration')
            if crypto_config:
                adapter_uris = crypto_config['crypto-adapter-uris']
                domain_configs = crypto_config['crypto-domain-configurations']
                for ca in crypto_adapters:
                    if ca.uri in adapter_uris:
                        used_adapter_domains = list()
                        for dc in domain_configs:
                            if dc['access-mode'] == 'control-usage':
                                used_adapter_domains.append(dc['domain-index'])
                        used_domains.update(used_adapter_domains)

        all_domains = set(range(0, max_domains))
        free_domains = all_domains - used_domains
        return sorted(list(free_domains))

    @logged_api_call
    def set_power_save(self, power_saving, wait_for_completion=True,
                       operation_timeout=None):
        """
        Set the power save setting of this CPC.

        The current power save setting in effect for a CPC is described in the
        "cpc-power-saving" property of the CPC.

        This method performs the HMC operation "Set CPC Power Save". It
        requires that the feature "Automate/advanced management suite"
        (FC 0020) is installed and enabled, and fails otherwise.

        This method will also fail if the CPC is under group control.

        Whether a CPC currently allows this method is described in the
        "cpc-power-save-allowed" property of the CPC.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "Power Save" task.

        Parameters:

          power_saving (:term:`string`):
            The new power save setting, with the possible values:

            * "high-performance" - The power consumption and performance of
              the CPC are not reduced. This is the default setting.
            * "low-power" - Low power consumption for all components of the
              CPC enabled for power saving.
            * "custom" - Components may have their own settings changed
              individually. No component settings are actually changed when
              this mode is entered.

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

          :exc:`~zhmcclient.HTTPError`: See the HTTP status and reason codes of
            operation "Set CPC Power Save" in the :term:`HMC API` book.
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        body = {'power-saving': power_saving}
        result = self.manager.session.post(
            self.uri + '/operations/set-cpc-power-save',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            # The HMC API book does not document what the result data of the
            # completed job is. It turns out that the completed job has this
            # dictionary as its result data:
            #    {'message': 'Operation executed successfully'}
            # We transform that to None.
            return None
        return result

    @logged_api_call
    def set_power_capping(self, power_capping_state, power_cap=None,
                          wait_for_completion=True, operation_timeout=None):
        """
        Set the power capping settings of this CPC. The power capping settings
        of a CPC define whether or not the power consumption of the CPC is
        limited and if so, what the limit is. Use this method to limit the
        peak power consumption of a CPC, or to remove a power consumption
        limit for a CPC.

        The current power capping settings in effect for a CPC are described in
        the "cpc-power-capping-state" and "cpc-power-cap-current" properties of
        the CPC.

        This method performs the HMC operation "Set CPC Power Capping". It
        requires that the feature "Automate/advanced management suite"
        (FC 0020) is installed and enabled, and fails otherwise.

        This method will also fail if the CPC is under group control.

        Whether a CPC currently allows this method is described in the
        "cpc-power-cap-allowed" property of the CPC.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "Power Capping" task.

        Parameters:

          power_capping_state (:term:`string`):
            The power capping state to be set, with the possible values:

            * "disabled" - The power cap of the CPC is not set and the peak
              power consumption is not limited. This is the default setting.
            * "enabled" - The peak power consumption of the CPC is limited to
              the specified power cap value.
            * "custom" - Individually configure the components for power
              capping. No component settings are actually changed when this
              mode is entered.

          power_cap (:term:`integer`):
            The power cap value to be set, as a power consumption in Watt. This
            parameter is required not to be `None` if
            `power_capping_state="enabled"`.

            The specified value must be between the values of the CPC
            properties "cpc-power-cap-minimum" and "cpc-power-cap-maximum".

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

          :exc:`~zhmcclient.HTTPError`: See the HTTP status and reason codes of
            operation "Set CPC Power Save" in the :term:`HMC API` book.
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        body = {'power-capping-state': power_capping_state}
        if power_cap is not None:
            body['power-cap-current'] = power_cap
        result = self.manager.session.post(
            self.uri + '/operations/set-cpc-power-capping',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            # The HMC API book does not document what the result data of the
            # completed job is. Just in case there is similar behavior to the
            # "Set CPC Power Save" operation, we transform that to None.
            # TODO: Verify job result of a completed "Set CPC Power Capping".
            return None
        return result

    @logged_api_call
    def get_energy_management_properties(self):
        """
        Return the energy management properties of the CPC.

        The returned energy management properties are a subset of the
        properties of the CPC resource, and are also available as normal
        properties of the CPC resource. In so far, there is no new data
        provided by this method. However, because only a subset of the
        properties is returned, this method is faster than retrieving the
        complete set of CPC properties (e.g. via
        :meth:`~zhmcclient.BaseResource.pull_full_properties`).

        This method performs the HMC operation "Get CPC Energy Management
        Data", and returns only the energy management properties for this CPC
        from the operation result. Note that in non-ensemble mode of a CPC, the
        HMC operation result will only contain data for the CPC alone.

        It requires that the feature "Automate/advanced management suite"
        (FC 0020) is installed and enabled, and returns empty values for most
        properties, otherwise.

        Authorization requirements:

        * Object-access permission to this CPC.

        Returns:

          dict: A dictionary of properties of the CPC that are related to
          energy management. For details, see section "Energy management
          related additional properties" in the data model for the CPC
          resource in the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`: See the HTTP status and reason codes of
            operation "Get CPC Energy Management Data" in the :term:`HMC API`
            book.
          :exc:`~zhmcclient.ParseError`: Also raised by this method when the
            JSON response could be parsed but contains inconsistent data.
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.get(self.uri + '/energy-management-data')
        em_list = result['objects']
        if len(em_list) != 1:
            uris = [em_obj['object-uri'] for em_obj in em_list]
            raise ParseError("Energy management data returned for no resource "
                             "or for more than one resource: %r" % uris)
        em_cpc_obj = em_list[0]
        if em_cpc_obj['object-uri'] != self.uri:
            raise ParseError("Energy management data returned for an "
                             "unexpected resource: %r" %
                             em_cpc_obj['object-uri'])
        if em_cpc_obj['error-occurred']:
            raise ParseError("Errors occurred when retrieving energy "
                             "management data for CPC. Operation result: %r" %
                             result)
        cpc_props = em_cpc_obj['properties']
        return cpc_props

    @logged_api_call
    def list_associated_storage_groups(
            self, full_properties=False, filter_args=None):
        """
        Return the :term:`storage groups <storage group>` that are associated
        to this CPC.

        If the CPC does not support the "dpm-storage-management" feature, or
        does not have it enabled, an empty list is returned.

        Storage groups for which the authenticated user does not have
        object-access permission are not included.

        Authorization requirements:

        * Object-access permission to any storage groups to be included in the
          result.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            storage group is being retrieved, vs. only the following short set:
            "object-uri", "cpc-uri", "name", "fulfillment-state", and
            "type".

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

            The 'cpc-uri' property is automatically added to the filter
            arguments and must not be specified in this parameter.

        Returns:

          : A list of :class:`~zhmcclient.StorageGroup` objects.

        Raises:

          ValueError: The filter_args parameter specifies the 'cpc-uri'
            property
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        if filter_args is None:
            filter_args = {}
        else:
            filter_args = filter_args.copy()
        if 'cpc-uri' in filter_args:
            raise ValueError(
                "The filter_args parameter specifies the 'cpc-uri' property "
                "with value: %s" % filter_args['cpc-uri'])
        filter_args['cpc-uri'] = self.uri

        sg_list = self.manager.console.storage_groups.list(
            full_properties, filter_args)

        return sg_list

    @logged_api_call
    def validate_lun_path(self, host_wwpn, host_port, wwpn, lun):
        """
        Validate if an FCP storage volume on an actual storage subsystem is
        reachable from this CPC, through a specified host port and using
        a specified host WWPN.

        This method performs the "Validate LUN Path" HMC operation.

        If the volume is reachable, the method returns. If the volume is not
        reachable (and no other errors occur), an :exc:`~zhmcclient.HTTPError`
        is raised, and its :attr:`~zhmcclient.HTTPError.reason` property
        indicates the reason as follows:

        * 484: Target WWPN cannot be reached.
        * 485: Target WWPN can be reached, but LUN cannot be reached.

        The CPC must have the "dpm-storage-management" feature enabled.

        Parameters:

          host_wwpn (:term:`string`):
            World wide port name (WWPN) of the host (CPC),
            as a hexadecimal number of up to 16 characters in any lexical case.

            This may be the WWPN of the physical storage port, or a WWPN of a
            virtual HBA. In any case, it must be the kind of WWPN that is used
            for zoning and LUN masking in the SAN.

          host_port (:class:`~zhmcclient.Port`):
            Storage port on the CPC that will be used for validating
            reachability.

          wwpn (:term:`string`):
            World wide port name (WWPN) of the FCP storage subsystem containing
            the storage volume,
            as a hexadecimal number of up to 16 characters in any lexical case.

          lun (:term:`string`):
            Logical Unit Number (LUN) of the storage volume within its FCP
            storage subsystem,
            as a hexadecimal number of up to 16 characters in any lexical case.

        Authorization requirements:

        * Object-access permission to the storage group owning this storage
          volume.
        * Task permission to the "Configure Storage - Storage Administrator"
          task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        # The operation requires exactly 16 characters in lower case
        host_wwpn_16 = format(int(host_wwpn, 16), '016x')
        wwpn_16 = format(int(wwpn, 16), '016x')
        lun_16 = format(int(lun, 16), '016x')

        body = {
            'host-world-wide-port-name': host_wwpn_16,
            'adapter-port-uri': host_port.uri,
            'target-world-wide-port-name': wwpn_16,
            'logical-unit-number': lun_16,
        }
        self.manager.session.post(
            self.uri + '/operations/validate-lun-path',
            body=body)
