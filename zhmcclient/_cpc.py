# Copyright 2016-2021 IBM Corp. All Rights Reserved.
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
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from ._manager import BaseManager
from ._resource import BaseResource
from ._lpar import LparManager
from ._partition import PartitionManager, Partition
from ._activation_profile import ActivationProfileManager
from ._adapter import AdapterManager
from ._virtual_switch import VirtualSwitchManager
from ._capacity_group import CapacityGroupManager
from ._logging import logged_api_call
from ._exceptions import ParseError, ConsistencyError
from ._utils import matches_filters, divide_filter_args, \
    RC_CPC, RC_ADAPTER, RC_CAPACITY_GROUP, RC_HBA, RC_NIC, RC_PARTITION, \
    RC_NETWORK_PORT, RC_STORAGE_PORT, RC_STORAGE_TEMPLATE, RC_STORAGE_GROUP, \
    RC_STORAGE_TEMPLATE_VOLUME, RC_STORAGE_VOLUME, RC_VIRTUAL_FUNCTION, \
    RC_VIRTUAL_STORAGE_RESOURCE, RC_VIRTUAL_SWITCH, RC_STORAGE_SITE, \
    RC_STORAGE_FABRIC, RC_STORAGE_SWITCH, RC_STORAGE_SUBSYSTEM, \
    RC_STORAGE_PATH, RC_STORAGE_CONTROL_UNIT, RC_VIRTUAL_TAPE_RESOURCE, \
    RC_TAPE_LINK, RC_TAPE_LIBRARY

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
            class_name=RC_CPC,
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
            query_parms, client_filters = divide_filter_args(
                self._query_props, filter_args)

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

                    if matches_filters(resource_obj, client_filters):
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
        self._capacity_groups = None
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
    def capacity_groups(self):
        """
        :class:`~zhmcclient.CapacityGroupManager`: Access to the
        :term:`Capacity Groups <Capacity Group>` in this CPC.
        """
        # We do here some lazy loading.
        if not self._capacity_groups:
            self._capacity_groups = CapacityGroupManager(self)
        return self._capacity_groups

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

    # Note: From HMC API version 2.24 on (i.e. starting with 8561), the Cpc
    # object supports a 'maximum-partitions' property, but only in DPM mode.
    # Therefore, we need to continue maintaining max partitions for all future
    # machine types.

    # Machine types with same max partitions for all models:
    _MAX_PARTITIONS_BY_MACHINE_TYPE = {
        '2817': 60,  # z196
        '2818': 30,  # z114
        '2827': 60,  # zEC12
        '2828': 30,  # zBC12
        '2964': 85,  # z13 / Emperor
        '2965': 40,  # z13s / Rockhopper
        '3906': 85,  # z14 / Emperor II
        '3907': 40,  # z14-ZR1 / Rockhopper II
    }

    # Machine types with different max partitions across their models:
    _MAX_PARTITIONS_BY_MACHINE_TYPE_MODEL = {
        ('8561', 'T01'): 85,  # z15
        ('8561', 'LT1'): 85,  # z15
        ('8562', 'GT2'): 85,  # z15 (85 is an exception for 8562)
        ('8562', 'T02'): 40,  # z15
        ('8562', 'LT2'): 40,  # z15
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
        z14-ZR1 / -LR1                            40
        z15-T01 / -LT1 / -GT2                     85
        z15-T02 / -LT2                            40
        =========================  ==================

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`ValueError`: Unknown machine type
        """
        machine_type = self.get_property('machine-type')
        machine_model = self.get_property('machine-model')
        try:
            return self._MAX_PARTITIONS_BY_MACHINE_TYPE[machine_type]
        except KeyError:
            pass
        try:
            return self._MAX_PARTITIONS_BY_MACHINE_TYPE_MODEL[
                (machine_type, machine_model)]
        except KeyError:
            pass
        try:
            return self.get_property('maximum-partitions')
        except KeyError:
            new_exc = ValueError("Unknown machine type/model: {}-{}".
                                 format(machine_type, machine_model))
            new_exc.__cause__ = None
            raise new_exc  # ValueError

    def dump(self):
        """
        Dump this Cpc resource with its properties and child resources
        (recursively) as a resource definition.

        The returned resource definition has the following format::

            {
                # Resource properties:
                "properties": {...},

                # Child resources for any CPC mode:
                "capacity_groups": [...],

                # Child resources for DPM mode:
                "partitions": [...],
                "adapters": [...],
                "virtual_switches": [...],

                # Child resources for classic mode:
                "lpars": [...],  # Faked Lpar children
                "reset_activation_profiles": [...],
                "image_activation_profiles": [...],
                "load_activation_profiles": [...],
            }

        Returns:
          dict: Resource definition of this resource.
        """

        # Dump the resource properties
        resource_dict = super(Cpc, self).dump()

        # Dump the child resources
        capacity_groups = self.capacity_groups.dump()
        if capacity_groups:
            resource_dict['capacity_groups'] = capacity_groups
        partitions = self.partitions.dump()
        if partitions:
            resource_dict['partitions'] = partitions
        adapters = self.adapters.dump()
        if adapters:
            resource_dict['adapters'] = adapters
        virtual_switches = self.virtual_switches.dump()
        if virtual_switches:
            resource_dict['virtual_switches'] = virtual_switches
        lpars = self.lpars.dump()
        if lpars:
            resource_dict['lpars'] = lpars
        reset_act_profiles = self.reset_activation_profiles.dump()
        if reset_act_profiles:
            resource_dict['reset_activation_profiles'] = reset_act_profiles
        image_act_profiles = self.image_activation_profiles.dump()
        if image_act_profiles:
            resource_dict['image_activation_profiles'] = image_act_profiles
        load_act_profiles = self.load_activation_profiles.dump()
        if load_act_profiles:
            resource_dict['load_activation_profiles'] = load_act_profiles

        return resource_dict

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
        return feature['state']  # pylint: disable=undefined-loop-variable

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

        This method serializes with other methods that access or change
        properties on the same Python object.

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
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, body=properties)
        # Attempts to change the 'name' property will be rejected by the HMC,
        # so we don't need to update the name-to-URI cache.
        assert self.manager._name_prop not in properties
        self.update_properties_local(copy.deepcopy(properties))

    @logged_api_call
    def start(self, wait_for_completion=True, operation_timeout=None):
        """
        Start this CPC, using the HMC operation "Start CPC".

        This operation performs an orderly start of the CPC, including:

        * Turning CPC power on.
        * Performing a power-on reset, this includes allocating system
          resources to the CPC.
        * Starting partitions that are in the auto-start list of the CPC.

        The CPC must be set for DPM operational mode (i.e. its 'dpm-enabled'
        property is True) and must currently be inactive.

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
        Stop this DPM-mode CPC, using the HMC operation "Stop CPC".

        This operation performs an orderly shutdown of the CPC, including:

        * Stopping all partitions.
        * Ending hardware activity.
        * Clearing, releasing, and de-allocating hardware resources.
        * Turning off CPC power.

        The CPC must be set for DPM operational mode (i.e. its 'dpm-enabled'
        property is True) and must currently be active.

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
    def activate(self, activation_profile_name, force=False,
                 wait_for_completion=True, operation_timeout=None):
        """
        Activate this classic-mode CPC, using the HMC operation "Activate CPC".

        This operation performs an orderly start of the CPC, including:

        * Turning CPC power on.
        * Performing a power-on reset, this includes allocating system
          resources to the CPC as defined by the reset activation profile.
        * Activating LPARs that are in the auto-start list defined by the
          reset activation profile.

        If the CPC is already active in classic mode, only the operations are
        performed that are needed to get into the state defined by the
        specified reset activation profile.

        The CPC must be set for classic operational mode (i.e. its 'dpm-enabled'
        property is False).

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "Activate" task.

        Parameters:

          activation_profile_name (:term:`string`):
            Name of the reset activation profile used to activate the CPC.

          force (bool):
            Boolean controlling whether the operation is permitted if the CPC
            is in 'operating' status.

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
        body = {
            'activation-profile-name': activation_profile_name,
            'force': force,
        }
        result = self.manager.session.post(
            self.uri + '/operations/activate',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def deactivate(self, force=False, wait_for_completion=True,
                   operation_timeout=None):
        """
        Deactivate this CPC, using the HMC operation "Deactivate CPC".

        This operation performs an orderly shutdown of the CPC, including:

        * Stopping all LPARs.
        * Ending hardware activity.
        * Clearing, releasing, and de-allocating hardware resources.
        * Turning off CPC power.

        The CPC must be set for classic operational mode (i.e. its 'dpm-enabled'
        property is False).

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "Deactivate" task.

        Parameters:

          force (bool):
            Boolean controlling whether the operation is permitted if the CPC
            is in 'operating' status.

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
        body = {'force': force}
        result = self.manager.session.post(
            self.uri + '/operations/deactivate',
            body,
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

    @logged_api_call
    def add_temporary_capacity(
            self, record_id, software_model=None, processor_info=None,
            test=False, force=False):
        """
        Add temporary processors to the CPC or increase temporary model
        capacity of the CPC.

        This method performs the "Add Temporary Capacity" HMC operation.

        If the request would exceed the processor capacity that is installed on
        the CPC or the limits of the capacity record, the operation will fail,
        unless the `force` parameter is `True`.

        Parameters:

          record_id (:term:`string`):
            The ID of the capacity record to be used for any updates of the
            processor capacity.

          software_model (:term:`string`):
            The name of the software model to be activated for the CPC.
            This must be one of the software models defined within the
            specified capacity record. The software model implies the number
            of general purpose processors that will be active once the
            operation succeeds.

            If `None`, the software model and the number of general purpose
            processors of the CPC will remain unchanged.

          processor_info (dict):
            The number of specialty processors to be added to the CPC.

            If `None`, the number of specialty processors of the CPC will
            remain unchanged.

            Each item in the dictionary identifies the number of one type of
            specialty processor. The key of the item must be a string
            specifying the type of specialty processor ('aap', 'cbp', 'icf',
            'ifl', 'iip', 'sap'), and the value of the item must be an integer
            specifying the number of processors of that type to be added.

            If an item for a type of specialty processor is not provided, or
            if the value of the item is `None`, the number of specialty
            processors of that type will remain unchanged.

          test (bool):
            Indicates whether test (`True`) or real (`False`) resources should
            be activated. Test resources are automatically deactivated after
            24h.

          force (bool):
            `True` indicates that the operation should proceed if not enough
            processors are available. `True` is permitted only for CBU, CPE
            and loaner capacity records.

        Authorization requirements:

        * Object-access permission to the CPC.
        * Task permission to the "Perform Model Conversion" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        body = {
            'record-id': record_id,
            'force': force,
            'test': test,
        }
        if software_model:
            body['software-model'] = software_model
        if processor_info:
            pi = []
            for ptype, pvalue in processor_info.items():
                pi_item = {
                    'processor-type': ptype,
                }
                if pvalue is not None:
                    pi_item['num-processor-steps'] = pvalue
                pi.append(pi_item)
            body['processor-info'] = pi

        self.manager.session.post(
            self.uri + '/operations/add-temp-capacity',
            body=body)

    @logged_api_call
    def remove_temporary_capacity(
            self, record_id, software_model=None, processor_info=None):
        """
        Remove temporary processors from the CPC or decrease temporary model
        capacity of the CPC.

        This method performs the "Remove Temporary Capacity" HMC operation.

        You can only remove activated resources for the specific offering.
        You cannot remove dedicated engines or the last processor of a processor
        type. If you remove resources back to the base configuration, the
        capacity record activation is completed. That is, if you remove the
        last temporary processor, your capacity record is deactivated. For a
        CBU and On/Off CoD record, to add resources again, you must use another
        :meth:`add_temporary_capacity` operation. For an On/Off CoD test or
        CPE record, once the record is deactivated, it is no longer available
        for use. You can then delete the record.

        After removal of the resources, the capacity record remains as an
        installed record. If you want a record deleted, you must manually
        delete the record on the "Installed Records" page in the HMC GUI.

        Parameters:

          record_id (:term:`string`):
            The ID of the capacity record to be used for any updates of the
            processor capacity.

          software_model (:term:`string`):
            The name of the software model to be activated for the CPC.
            This must be one of the software models defined within the
            specified capacity record. The software model implies the number
            of general purpose processors that will be active once the
            operation succeeds.

            If `None`, the software model and the number of general purpose
            processors of the CPC will remain unchanged.

          processor_info (dict):
            The number of specialty processors to be removed from the CPC.

            If `None`, the number of specialty processors of the CPC will
            remain unchanged.

            Each item in the dictionary identifies the number of one type of
            specialty processor. The key of the item must be a string
            specifying the type of specialty processor ('aap', 'cbp', 'icf',
            'ifl', 'iip', 'sap'), and the value of the item must be an integer
            specifying the number of processors of that type to be removed.

            If an item for a type of specialty processor is not provided, or
            if the value of the item is `None`, the number of specialty
            processors of that type will remain unchanged.

        Authorization requirements:

        * Object-access permission to the CPC.
        * Task permission to the "Perform Model Conversion" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        body = {
            'record-id': record_id,
        }
        if software_model:
            body['software-model'] = software_model
        if processor_info:
            pi = []
            for ptype, pvalue in processor_info.items():
                pi_item = {
                    'processor-type': ptype,
                }
                if pvalue is not None:
                    pi_item['num-processor-steps'] = pvalue
                pi.append(pi_item)
            body['processor-info'] = pi

        self.manager.session.post(
            self.uri + '/operations/remove-temp-capacity',
            body=body)

    @logged_api_call
    def set_auto_start_list(self, auto_start_list):
        """
        Set the auto-start list of partitions for this CPC.

        The current auto-start list is replaced with this new list.

        The auto-start list may contain named partition groups that are formed
        just for the purpose of auto-starting (they have nothing to do with
        Group objects on the HMC).

        This method performs the "Set Auto-Start List" HMC operation.

        This method requires the CPC to be in DPM mode.

        Parameters:

          auto_start_list (list): The auto-start list to be set.

            Each list item is one of:

            - tuple(partition, post_start_delay)
            - tuple(partition_list, name, description, post_start_delay)

            Where:

            - partition (:class:`~zhmcclient.Partition`): The partition to be
              auto-started.
            - post_start_delay (int): Delay in seconds to wait after starting
              this partition or partition group, and before the next partition
              or partition group in the list is started.
            - partition_list (list of :class:`~zhmcclient.Partition`): The
              partitions in the partition group to be auto-started.
            - name (string): Name of the partition group.
            - description (string): Description of the partition group.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "System Details" task.
        * Object-access permission to all partitions specified in the auto-start
          list.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        auto_start_body = []
        for item in auto_start_list:
            if isinstance(item[0], Partition):
                partition, post_start_delay = item
                auto_start_item = {
                    'type': 'partition',
                    'post-start-delay': post_start_delay,
                    'partition-uri': partition.uri,
                }
                auto_start_body.append(auto_start_item)
            elif isinstance(item[0], (list, tuple)):
                partition_list, name, description, post_start_delay = item
                auto_start_item = {
                    'type': 'partition-group',
                    'post-start-delay': post_start_delay,
                    'name': name,
                    'description': description,
                    'partition-uris': [p.uri for p in partition_list],
                }
                auto_start_body.append(auto_start_item)
            else:
                raise TypeError(
                    "Invalid type for auto_start_list parameter: {}".
                    format(type(auto_start_list)))

        body = {
            'auto-start-list': auto_start_body,
        }
        self.manager.session.post(
            self.uri + '/operations/set-auto-start-list',
            body=body)

    @logged_api_call
    def import_dpm_configuration(self, dpm_configuration):
        """
        Import a DPM configuration into this CPC.

        This includes settable CPC properties, settable properties of physical
        adapters, Hipersocket adapters, partitions with their child objects,
        virtual functions, virtual switches, capacity groups, storage related
        resources, storage ports, and network ports.

        This method performs the "Import DPM Configuration" HMC operation.

        This method requires the CPC to be in DPM mode.

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Import Dynamic Partition Manager
          Configuration" task.

        Parameters:

          dpm_configuration (dict): A DPM configuration, represented as a
            dictionary with the fields described for the
            "Import DPM Configuration" operation in the :term:`HMC API` book.

            Resource URIs are represented as URI strings in the fields of
            the DPM configuration, as described for the request body fields
            of the HMC operation. URIs of imported resource objects can be
            chosen to be preserved or newly allocated via the "preserve-uris"
            field.

            Adapter PCHIDs may be different between the imported adapter
            objects and the actual adapters in this CPC and can be mapped
            via the "adapter-mapping" field.

            Host WWPNs of FICON adapters can be chosen to be preserved
            or newly allocated via the "preserve-wwpns" field.

        Returns:
          list or None:
            If the complete input DPM configuration has been applied
            to the CPC, `None` is returned.

            If only a part of the input DPM configuration has been applied,
            a list of dict objects is returned that describe what was not
            applied.
            For details, see the description of the response of the
            "Import DPM Configuration" operation in the :term:`HMC API` book.

            To verify that the complete input DPM configuration has been
            applied, the caller must verify the return value to be `None` and
            not just verify that no exceptions have been raised.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = dpm_configuration
        result = self.manager.session.post(
            self.uri + '/operations/import-dpm-config',
            body=body)
        return result

    @logged_api_call
    def export_dpm_configuration(self):
        """
        Export a DPM configuration from this CPC and return it.

        The DPM configuration includes settable CPC properties and all DPM
        specific objects of or associated with the CPC, such as adapters with
        their ports, virtual switches, partitions with their child objects,
        capacity groups, and various storage and tape related resources.

        Note that all adapters of the CPC are exported, even when they are not
        used by partitions.

        This method performs the "Get Inventory" HMC operation and extracts
        all information into the result.

        This method requires the CPC to be in DPM mode.

        Authorization requirements:

        * Object-access permission to this CPC.

        Returns:
          dict:
            A DPM configuration, represented as a dictionary with the
            fields described for the "Import DPM Configuration" operation
            in the :term:`HMC API` book.

            Resource URIs are represented as URI strings in the fields of
            the DPM configuration, as described for the request body fields
            of the HMC operation.

            The optional "preserve-uris", "preserve-wwpns", and
            "adapter-mapping" fields will not be in the returned dictionary,
            so their defaults will be used when importing this DPM configuration
            unchanged to a CPC.

            The returned DPM configuration object can be passed to
            :meth:`~zhmcclient.Cpc.import_dpm_configuration` either unchanged,
            or after changing it, e.g. by adding the optional "preserve-uris",
            "preserve-wwpns", or "adapter-mapping" fields.

        Raises:
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.ConsistencyError` - issues with inventory data
        """
        inventory_list = retrieveInventoryData(self.manager.client)
        cpc_uri = self.get_property('object-uri')
        config_dict = convertToConfig(inventory_list, cpc_uri)
        return config_dict


# Functions used by Cpc.export_dpm_configuration().
# Some of these functions were adapted from code in the
# exportDpmResourcesToFile.py script available at
# https://www-01.ibm.com/servers/resourcelink/lib03020.nsf/0/2C88A77CEA71062E8525829500667BCD?OpenDocument

def extractByParent(classname, parent_list, inventory_list):
    """
    Extract all items from inventory_list that have the classname and where the
    parent is in parent_list.

    This is used for example to get all partitions of a CPC or all NICs of a
    partition.
    """
    result_list = [x for x in inventory_list
                   if (x['class'] == classname and x['parent'] in parent_list)]
    return result_list


def extractByPropertyInListValue(classname, prop_name, values, inventory_list):
    """
    Extract all items from inventory_list that have the classname and where the
    value of the prop_name property is in the values list.

    Used for example to get all storage groups that have value for property
    'cpc-uri' in a list of CPC uris.
    """
    result_list = [x for x in inventory_list
                   if x['class'] == classname and x[prop_name] in values]
    return result_list


def extractByValueInListProperty(classname, value, prop_name, inventory_list):
    """
    Extract all items from inventory_list that have the classname and where
    value is in the value of the prop_name array property.

    Used for example to get all storage-sites that have a 'cpc-uris' list
    containing the specified cpc-uri value.
    """
    result_list = [x for x in inventory_list
                   if x['class'] == classname and value in x[prop_name]]
    return result_list


def extractCpc(cpc_uri, inventory_list):
    """
    Extract the CPC item from inventory_list that has the specified cpc_uri.
    """
    cpcs = [x for x in inventory_list
            if x['class'] == RC_CPC and x['object-uri'] == cpc_uri]
    cpc_len = len(cpcs)
    if cpc_len == 0:
        raise ConsistencyError(
            "Inventory data does not contain CPC with URI {}".
            format(cpc_uri))
    if cpc_len > 1:
        raise ConsistencyError(
            "Inventory data contains multiple ({}) CPCs with URI {}".
            format(cpc_len, cpc_uri))
    cpc = cpcs[0]
    return cpc


def extractAdapters(cpc_uri, inventory_list):
    """
    Extract all items from inventory_list with class "adapter" and parent
    cpc_uri.
    """

    # Export all adapters even when not used. If False, only adapters that
    # are used, are exported.
    all_adapters = True

    result_list = []
    excluded_classes = (RC_ADAPTER, RC_NETWORK_PORT, RC_STORAGE_PORT)
    for x in inventory_list:
        if x['class'] == RC_ADAPTER and x['parent'] == cpc_uri:
            # It is an adapter of this CPC
            if all_adapters:
                result_list.append(x)
            elif containsItemsWithSubstring(
                    x['object-uri'], excluded_classes, inventory_list):
                # The adapter is used.
                # Note that the test above checks only adapter URIs, but in
                # case of OSA adapters the virtual switches are referencing
                # the backing network ports, and in case of FICON adapters the
                # HBAs/VSRs are referencing the storage ports. The reason this
                # test works nevertheless, is that the storage and network ports
                # are element resources that are children of the adapter
                # resources, and thus their URIs happen to contain the adapter
                # URIs.
                result_list.append(x)
    return result_list


def containsItemsWithSubstring(substr, excluded_classes, inventory_list):
    """
    Check if inventory_list contains items where substr appears in the
    string representation of the item, excluding the items with a class in
    excluded_classes.
    """
    find_list = [x for x in inventory_list
                 if x['class'] not in excluded_classes
                 and str(x).find(substr) != -1]  # noqa: W503
    found = len(find_list) > 0
    return found


def retrieveInventoryData(client):
    """
    Retrieve inventory data from the HMC.
    Returns the inventory list from Client.get_inventory().
    """
    resource_classes = ['dpm-resources', 'cpc']
    inventory_list = client.get_inventory(resource_classes)
    for res in inventory_list:
        uri = res.get('object-uri') or res.get('element-uri')
        if not uri:
            raise ConsistencyError(
                "Inventory data has an item without URI property: {}".
                format(res))
    return inventory_list


def convertToConfig(inventory_list, cpc_uri):
    """
    Convert the inventory list to a DPM configuration dict.
    """
    config_dict = OrderedDict()

    cpc = extractCpc(cpc_uri, inventory_list)
    cpc_uris = [cpc_uri]

    config_dict['se-version'] = cpc.get('se-version', None)
    config_dict['available-features-list'] = \
        cpc.get('available-features-list', [])
    config_dict['cpc-properties'] = {
        'auto-start-list': cpc.get('auto-start-list', None),
        'description': cpc.get('description', None),
        'management-world-wide-port-name':
            cpc.get('management-world-wide-port-name', None),
    }

    config_dict['adapters'] = extractAdapters(
        cpc_uri, inventory_list)
    adapter_uris = [x['object-uri'] for x in config_dict['adapters']]

    config_dict['partitions'] = extractByParent(
        RC_PARTITION, cpc_uris, inventory_list)
    partition_uris = [x['object-uri'] for x in config_dict['partitions']]

    config_dict['nics'] = extractByParent(
        RC_NIC, partition_uris, inventory_list)
    config_dict['hbas'] = extractByParent(
        RC_HBA, partition_uris, inventory_list)
    config_dict['virtual-functions'] = extractByParent(
        RC_VIRTUAL_FUNCTION, partition_uris, inventory_list)

    config_dict['virtual-switches'] = extractByParent(
        RC_VIRTUAL_SWITCH, cpc_uris, inventory_list)

    config_dict['capacity-groups'] = extractByParent(
        RC_CAPACITY_GROUP, cpc_uris, inventory_list)

    config_dict['storage-sites'] = extractByValueInListProperty(
        RC_STORAGE_SITE, cpc_uri, 'cpc-uris', inventory_list)
    storage_site_uris = [x['object-uri'] for x in config_dict['storage-sites']]

    config_dict['storage-subsystems'] = extractByPropertyInListValue(
        RC_STORAGE_SUBSYSTEM, 'storage-site-uri', storage_site_uris,
        inventory_list)
    storage_subsystem_uris = \
        [x['object-uri'] for x in config_dict['storage-subsystems']]

    config_dict['storage-fabrics'] = extractByPropertyInListValue(
        RC_STORAGE_FABRIC, 'cpc-uri', cpc_uris, inventory_list)
    config_dict['storage-switches'] = extractByPropertyInListValue(
        RC_STORAGE_SWITCH, 'storage-site-uri', storage_site_uris,
        inventory_list)

    config_dict['storage-control-units'] = extractByPropertyInListValue(
        RC_STORAGE_CONTROL_UNIT, 'parent', storage_subsystem_uris,
        inventory_list)
    storage_control_unit_uris = \
        [x['object-uri'] for x in config_dict['storage-control-units']]

    config_dict['storage-paths'] = extractByPropertyInListValue(
        RC_STORAGE_PATH, 'parent', storage_control_unit_uris, inventory_list)

    config_dict['storage-ports'] = extractByPropertyInListValue(
        RC_STORAGE_PORT, 'parent', adapter_uris, inventory_list)

    config_dict['network-ports'] = extractByPropertyInListValue(
        RC_NETWORK_PORT, 'parent', adapter_uris, inventory_list)

    config_dict['storage-groups'] = extractByPropertyInListValue(
        RC_STORAGE_GROUP, 'cpc-uri', cpc_uris, inventory_list)
    storage_group_uris = \
        [x['object-uri'] for x in config_dict['storage-groups']]

    config_dict['storage-volumes'] = extractByPropertyInListValue(
        RC_STORAGE_VOLUME, 'parent', storage_group_uris, inventory_list)

    config_dict['storage-templates'] = extractByPropertyInListValue(
        RC_STORAGE_TEMPLATE, 'cpc-uri', cpc_uris, inventory_list)
    storage_template_uris = \
        [x['object-uri'] for x in config_dict['storage-templates']]

    config_dict['storage-template-volumes'] = extractByPropertyInListValue(
        RC_STORAGE_TEMPLATE_VOLUME, 'parent', storage_template_uris,
        inventory_list)

    config_dict['virtual-storage-resources'] = extractByPropertyInListValue(
        RC_VIRTUAL_STORAGE_RESOURCE, 'parent', storage_group_uris,
        inventory_list)

    config_dict['tape-links'] = extractByPropertyInListValue(
        RC_TAPE_LINK, 'cpc-uri', cpc_uris, inventory_list)
    tape_link_uris = [x['object-uri'] for x in config_dict['tape-links']]

    config_dict['tape-libraries'] = extractByPropertyInListValue(
        RC_TAPE_LIBRARY, 'cpc-uri', cpc_uris, inventory_list)

    config_dict['virtual-tape-resources'] = extractByParent(
        RC_VIRTUAL_TAPE_RESOURCE, tape_link_uris, inventory_list)

    return config_dict
