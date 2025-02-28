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


import warnings
import copy
import json
from collections import OrderedDict

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
from ._utils import get_features, \
    datetime_from_timestamp, timestamp_from_datetime, \
    RC_CPC, RC_ADAPTER, RC_HBA, RC_NIC, RC_PARTITION, \
    RC_NETWORK_PORT, RC_STORAGE_PORT, RC_STORAGE_TEMPLATE, RC_STORAGE_GROUP, \
    RC_STORAGE_TEMPLATE_VOLUME, RC_STORAGE_VOLUME, RC_VIRTUAL_FUNCTION, \
    RC_VIRTUAL_STORAGE_RESOURCE, RC_VIRTUAL_SWITCH, RC_STORAGE_SITE, \
    RC_STORAGE_FABRIC, RC_STORAGE_SWITCH, RC_STORAGE_SUBSYSTEM, \
    RC_STORAGE_PATH, RC_STORAGE_CONTROL_UNIT, RC_VIRTUAL_TAPE_RESOURCE, \
    RC_TAPE_LINK, RC_TAPE_LIBRARY, RC_CERTIFICATE

__all__ = ['STPNode', 'CpcManager', 'Cpc']


class STPNode:
    # pylint: disable=too-few-public-methods
    """
    Data structure defining a CPC that is referenced by an STP configuration.

    That CPC does not need to be managed by the HMC.

    This object is used in the following methods:

      * :meth:`zhmcclient.Cpc.set_stp_config`
    """

    def __init__(
            self, object_uri, type, model, manuf, po_manuf, seq_num, node_name):
        # pylint: disable=redefined-builtin
        """
        Parameters:

          object_uri (string): The object-uri of the CPC, if the CPC is managed
            by the HMC. Otherwise, `None`.

          type (string): Machine type of the CPC (6 chars left padded with
            zeros), or an empty string.

          model (string): Machine model of the CPC (3 chars), or an empty
            string.

          manuf (string): Manufacturer of the CPC (3 chars), or an empty
            string.

          po_manuf (string): Plant code of the manufacturer of the CPC
            (2 chars), or an empty string.

          seq_num (string): Sequence number of the CPC (12 chars), or an empty
            string.

          node_name (string): Name of the CPC (1-8 chars).
        """
        self.object_uri = object_uri
        self.type = type
        self.model = model
        self.manuf = manuf
        self.po_manuf = po_manuf
        self.seq_num = seq_num
        self.node_name = node_name

    def json(self):
        """
        Returns this data structure as a JSON string suitable for being used as
        an argument in methods that use this data structure.
        """
        ret_dict = {
            'object-uri': self.object_uri,
            'type': self.type,
            'model': self.model,
            'manuf': self.manuf,
            'po-manuf': self.po_manuf,
            'seq-num': self.seq_num,
            'node-name': self.node_name,
        }
        return json.dumps(ret_dict)


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

    HMC/SE version requirements: None
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

        super().__init__(
            resource_class=Cpc,
            class_name=RC_CPC,
            session=client.session,
            parent=None,
            base_uri='/api/cpcs',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props,
            supports_properties=True)
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

        Any resource property may be specified in a filter argument. For
        details about filter arguments, see :ref:`Filtering`.

        The listing of resources is handled in an optimized way:

        * If this manager is enabled for :ref:`auto-updating`, a locally
          maintained resource list is used (which is automatically updated via
          inventory notifications from the HMC) and the provided filter
          arguments are applied.

        * Otherwise, if the filter arguments specify the resource name as a
          single filter argument with a straight match string (i.e. without
          regular expressions), an optimized lookup is performed based on a
          locally maintained name-URI cache.

        * Otherwise, the HMC List operation is performed with the subset of the
          provided filter arguments that can be handled on the HMC side and the
          remaining filter arguments are applied on the client side on the list
          result.

        HMC/SE version requirements: None

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
        result_prop = 'cpcs'
        list_uri = '/api/cpcs'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None)


class Cpc(BaseResource):
    """
    Representation of a managed :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.CpcManager`).

    HMC/SE version requirements: None
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
        assert isinstance(manager, CpcManager), (
            f"Cpc init: Expected manager type {CpcManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)

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
            self._reset_activation_profiles = ActivationProfileManager(
                self, profile_type='reset')
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
            self._image_activation_profiles = ActivationProfileManager(
                self, profile_type='image')
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
            self._load_activation_profiles = ActivationProfileManager(
                self, profile_type='load')
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
    # Keep in sync with tests/end2end/test_cpc.py.
    _MAX_PARTITIONS_BY_MACHINE_TYPE = {
        '2817': 60,  # z196
        '2818': 30,  # z114
        '2827': 60,  # zEC12
        '2828': 30,  # zBC12
        '2964': 85,  # z13 / Emperor
        '2965': 40,  # z13s / Rockhopper
        '3906': 85,  # z14 / Emperor II
        '3907': 40,  # z14-ZR1 / Rockhopper II
        '8561': 85,  # z15-T01 / LinuxOne III (-LT1)
        '3931': 85,  # z16-A01
    }

    # Machine types with different max partitions across their models:
    # Keep in sync with tests/end2end/test_cpc.py.
    _MAX_PARTITIONS_BY_MACHINE_TYPE_MODEL = {
        ('8562', 'T02'): 40,  # z15-T02
        ('8562', 'LT2'): 40,  # LinuxOne III (-LT2)
        ('8562', 'GT2'): 85,  # z15-GT2
    }

    @property
    @logged_api_call
    def maximum_active_partitions(self):
        """
        Integer: The maximum number of partitions of this CPC.

        For CPCs in DPM mode, the number indicates the maximum number of
        partitions. For CPCs in classic mode, the number indicates the maximum
        number of logical partitions (LPARs) that can be active at the same
        time.

        The following table shows the maximum number of partitions by machine
        generation:

        =============================  ==================
        Machine generation             Maximum partitions
        =============================  ==================
        z196                                          60
        z114                                          30
        zEC12                                         60
        zBC12                                         30
        z13 / Emperor                                 85
        z13s / Rockhopper                             40
        z14 / Emperor II                              85
        z14-ZR1 / Rockhopper II                       40
        z15-T01 / LinuxOne III (-LT1)                 85
        z15-T02 / LinuxOne III (-LT2)                 40
        z15-GT2                                       85
        z16-A01                                       85
        =============================  ==================

        HMC/SE version requirements: None

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
            new_exc = ValueError(
                f"Unknown machine type/model: {machine_type}-{machine_model}")
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
        resource_dict = super().dump()

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
        Indicates whether the specified
        :ref:`firmware feature <firmware features>` is enabled for this CPC.

        The specified firmware feature must be available for the CPC.

        For a list of available firmware features, see section
        "Firmware Features" in the :term:`HMC API` book, or use the
        :meth:`feature_info` method.

        HMC/SE version requirements:

        * HMC version >= 2.14.0 with HMC API version >= 2.23

        Authorization requirements:

        * Object-access permission to this CPC.

        Parameters:

          feature_name (:term:`string`): The name of the firmware feature.

        Returns:

          bool: `True` if the firmware feature is enabled, or `False` if the
          firmware feature is disabled.

        Raises:

          :exc:`ValueError`: Firmware features are not supported on the HMC.
          :exc:`ValueError`: The specified firmware feature is not available
            for the CPC.
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        feature_list = self.prop('available-features-list', None)
        if feature_list is None:
            raise ValueError("Firmware features are not supported on the HMC")
        for feature in feature_list:
            if feature['name'] == feature_name:
                break
        else:
            raise ValueError(
                f"Firmware feature {feature_name} is not available for CPC "
                f"{self.name}")
        return feature['state']  # pylint: disable=undefined-loop-variable

    @logged_api_call
    def feature_info(self):
        """
        Returns information about the :ref:`firmware features` available for
        this CPC.

        HMC/SE version requirements:

        * HMC version >= 2.14.0 with HMC API version >= 2.23

        Authorization requirements:

        * Object-access permission to this CPC.

        Returns:

          :term:`iterable`:
            An iterable where each item represents one firmware feature that is
            available for this CPC.

            Each item is a dictionary with the following items:

            * `name` (:term:`unicode string`): Name of the feature.
            * `description` (:term:`unicode string`): Short description of
              the feature.
            * `state` (bool): Enablement state of the feature (`True` if
              enabled, `False` if disabled).

        Raises:

          :exc:`ValueError`: Firmware features are not supported on the HMC.
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        feature_list = self.prop('available-features-list', None)
        if feature_list is None:
            raise ValueError("Firmware features are not supported on the HMC")
        return feature_list

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this CPC.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements: None

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
        self.manager.session.post(self.uri, resource=self, body=properties)
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

        HMC/SE version requirements:

        * SE version >= 2.13.1

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

            This job supports cancellation. Note that it may no longer be
            possible to cancel the job after some point. The job status and
            reason codes will indicate whether the job was canceled or ran to
            completion.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        result = self.manager.session.post(
            self.uri + '/operations/start', resource=self,
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

        HMC/SE version requirements:

        * SE version >= 2.13.1

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
            This job does not support cancellation.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        result = self.manager.session.post(
            self.uri + '/operations/stop', resource=self,
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

        HMC/SE version requirements: None

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
            This job does not support cancellation.

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
            self.uri + '/operations/activate', resource=self, body=body,
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

        HMC/SE version requirements: None

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
            This job does not support cancellation.

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
            self.uri + '/operations/deactivate', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def import_profiles(self, profile_area):
        """
        Import activation profiles and/or system activity profiles for this CPC
        from the SE hard drive into the CPC using the HMC operation
        "Import Profiles".

        This operation is not permitted when the CPC is in DPM mode.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "CIM Actions ExportSettingsData" task.

        Parameters:

          profile_area (int):
            The numbered hard drive area (1-4) from which the profiles are
            imported.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'profile-area': profile_area}
        result = self.manager.session.post(
            self.uri + '/operations/import-profiles', resource=self, body=body)
        return result

    @logged_api_call
    def export_profiles(self, profile_area):
        """
        Export activation profiles and/or system activity profiles from this
        CPC to the SE hard drive using the HMC operation "Export Profiles".

        This operation is not permitted when the CPC is in DPM mode.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission for the "CIM Actions ExportSettingsData" task.

        Parameters:

          profile_area (int):
             The numbered hard drive area (1-4) to which the profiles are
             exported. Any existing data is overwritten.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'profile-area': profile_area}
        result = self.manager.session.post(
            self.uri + '/operations/export-profiles', resource=self, body=body)
        return result

    @logged_api_call
    def get_wwpns(self, partitions):
        """
        Return the WWPNs of the host ports (of the :term:`HBAs <HBA>`) of the
        specified :term:`Partitions <Partition>` of this CPC.

        This method performs the HMC operation "Export WWPN List".

        The CPC must be set for DPM operational mode (i.e. its 'dpm-enabled'
        property is True) and must currently be active.

        HMC/SE version requirements:

        * SE version >= 2.13.1

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
        result = self.manager.session.post(
            self._uri + '/operations/export-port-names-list', resource=self,
            body=body)
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
        checked, regardless of whether they are active. This ensures
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

        HMC/SE version requirements:

        * SE version >= 2.13.1

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
                        used_adapter_domains = []
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

        HMC/SE version requirements: None

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
            This job does not support cancellation.

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
            self.uri + '/operations/set-cpc-power-save', resource=self,
            body=body, wait_for_completion=wait_for_completion,
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
        of a CPC define whether the power consumption of the CPC is
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

        HMC/SE version requirements: None

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
            This job does not support cancellation.

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
            self.uri + '/operations/set-cpc-power-capping', resource=self,
            body=body, wait_for_completion=wait_for_completion,
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

        HMC/SE version requirements: None

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
        result = self.manager.session.get(
            self.uri + '/energy-management-data', resource=self)
        em_list = result['objects']
        if len(em_list) != 1:
            uris = [em_obj['object-uri'] for em_obj in em_list]
            raise ParseError(
                "Energy management data returned for no resource or for "
                f"more than one resource: {uris!r}")
        em_cpc_obj = em_list[0]
        if em_cpc_obj['object-uri'] != self.uri:
            raise ParseError(
                "Energy management data returned for an unexpected resource: "
                f"{em_cpc_obj['object-uri']!r}")
        if em_cpc_obj['error-occurred']:
            raise ParseError(
                "Errors occurred when retrieving energy management data for "
                f"CPC. Operation result: {result!r}")
        cpc_props = em_cpc_obj['properties']
        return cpc_props

    @logged_api_call
    def list_associated_storage_groups(
            self, full_properties=False, filter_args=None):
        """
        Return the :term:`storage groups <storage group>` that are associated
        to this CPC.

        Storage groups for which the authenticated user does not have
        object-access permission are not included.

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

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
                f"with value: {filter_args['cpc-uri']}")
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

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

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
            self.uri + '/operations/validate-lun-path', resource=self,
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

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to the CPC.
        * Task permission to the "Perform Model Conversion" task.

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
            self.uri + '/operations/add-temp-capacity', resource=self,
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

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to the CPC.
        * Task permission to the "Perform Model Conversion" task.

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
            self.uri + '/operations/remove-temp-capacity', resource=self,
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

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "System Details" task.
        * Object-access permission to all partitions specified in the auto-start
          list.

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
                    "Invalid type for auto_start_list parameter: "
                    f"{type(auto_start_list)}")

        body = {
            'auto-start-list': auto_start_body,
        }
        self.manager.session.post(
            self.uri + '/operations/set-auto-start-list', resource=self,
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

        HMC/SE version requirements:

        * SE version >= 2.14.0

        Authorization requirements:

        * Object-access permission to this CPC.
        * Object-access permission to Secure Boot Certificate objects (only
          applies when the request body contains one or more secure boot
          Certificate objects to be assigned to Partitions).
        * Task permission for the "Import Secure Boot Certificates" task
          (only applies when the request body contains one or more Certificate
          objects).
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
            self.uri + '/operations/import-dpm-config', resource=self,
            body=body)
        return result

    @logged_api_call
    def export_dpm_configuration(self, include_unused_adapters=False):
        """
        Export a DPM configuration from this CPC and return it.

        The DPM configuration includes settable CPC properties and all DPM
        specific objects of or associated with the CPC, such as adapters with
        their ports, virtual switches, partitions with their child objects,
        capacity groups, various storage and tape related resources, and
        certificate objects.

        By default, only those adapters, virtual switches, network and
        storage port objects of the CPC are exported that are referenced by
        other DPM specific configuration objects.

        This method performs the "Get Inventory" HMC operation and extracts
        the relevant elements into the result.

        This method requires the CPC to be in DPM mode.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this CPC.
        * Object-access permission to all Certificate objects associated to
          this CPC.

        Parameters:

          include_unused_adapters (bool):
            Controls whether the full set of adapters and corresponding
            resources should be returned, vs. only those that are referenced
            by other DPM objects that are part of the return data.

        Returns:

          dict:
            A DPM configuration, represented as a dictionary with the
            fields described for the "Import DPM Configuration" operation
            in the :term:`HMC API` book.

            Resource URIs are represented as URI strings in the fields of
            the DPM configuration, as described for the request body fields
            of the HMC operation.

            Empty fields are omitted from the returned configuration. This
            allows using newer versions of zhmcclient that may have added
            support for a feature of a new generation of Z systems with
            older generations of Z systems that did not yet have the feature.

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
        config_dict = self._convert_to_config(inventory_list,
                                              include_unused_adapters)
        features = self.list_api_features()
        if len(features) > 0:
            config_dict['available-api-features-list'] = features
        return config_dict

    @logged_api_call
    def list_api_features(self, name=None):
        """
        Returns information about the Web Services API features available on
        the CPC, see :ref:`Feature enablement`.

        HMC/SE version requirements:

        * HMC version >= 2.16.0 with HMC API version >= 4.10

        Authorization requirements:

        * None

        Parameters:

          name:
            A regular expression used to limit returned objects to those that
            have a matching name field.

        Returns:

          list of strings: The list of API features that are available on this
          CPC. Below the required HMC version, an empty list is returned.
        """
        return get_features(self.manager.session, self.uri, name)

    @logged_api_call
    def single_step_install(
            self, bundle_level=None, accept_firmware=True,
            ftp_host=None, ftp_protocol=None,
            ftp_user=None, ftp_password=None,
            ftp_directory=None, wait_for_completion=True,
            operation_timeout=None):
        """
        Upgrades the firmware on the Support Element (SE) of this CPC.

        This is done by performing the "CPC Single Step Install" operation
        which performs the following steps:

        * A backup of the target CPC is performed to its SE hard drive.
        * If `accept_firmware` is True, the firmware currently installed on the
          SE of this CPC is accepted. Note that once firmware is accepted, it
          cannot be removed.
        * The new firmware identified by the bundle-level field is retrieved
          from the IBM support site or from an FTP server, and installed.
        * The newly installed firmware is activated, which includes rebooting
          the SE of this CPC.

        If an error occurs when installing the upgrades for the different
        firmware components, any components that were successfully installed
        are rolled back.

        If an error occurs after the firmware is accepted, the firmware remains
        accepted.

        Note that it is not possible to downgrade the SE firmware with this
        operation.

        HMC/SE version requirements:

        * HMC version >= 2.16.0

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Single Step Internal Code Changes" task.

        Parameters:

          bundle_level (string): Name of the bundle to be installed on the SE
            of this CPC (e.g. 'S51').
            If `None`, all locally available code changes, or in case of
            retrieving code changes from an FTP server, all code changes on
            the FTP server, will be installed.

          accept_firmware (bool): Accept the previous bundle level before
            installing the new level.

          ftp_host (string): The hostname for the FTP server from which
            the firmware will be retrieved, or `None` to retrieve it from the
            IBM support site.

          ftp_protocol (string): The protocol to connect to the FTP
            server, if the firmware will be retrieved from an FTP server,
            or `None`. Valid values are: "ftp", "ftps", "sftp".

          ftp_user (string): The username for the FTP server login,
            if the firmware will be retrieved from an FTP server, or `None`.

          ftp_password (string): The password for the FTP server login,
            if the firmware will be retrieved from an FTP server, or `None`.

          ftp_directory (string): The path name of the directory on the
            FTP server with the firmware files,
            if the firmware will be retrieved from an FTP server, or `None`.

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

            This job supports cancellation. Note there are only a few
            interruption points in the firmware install process, so it may be
            some time before the job is canceled, and after some point, will
            continue on to completion. The job status and reason codes will
            indicate whether the job was canceled or ran to completion. If the
            job is successfully canceled, any steps that were successfully
            completed will not be rolled back.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """

        # The 'wait_for_completion' parameter from 2.12.0 became
        # 'ftp_host' after that, so we detect the passing of
        # 'wait_for_completion' as a positional argument.
        assert ftp_host is None or \
            isinstance(ftp_host, str)

        body = {
            'accept-firmware': accept_firmware,
        }

        if bundle_level is not None:
            body['bundle-level'] = bundle_level

        if ftp_host is not None:
            body['ftp-retrieve'] = True
            body['ftp-server-host'] = ftp_host
            body['ftp-server-user'] = ftp_user
            body['ftp-server-password'] = ftp_password
            body['ftp-server-directory'] = ftp_directory
            body['ftp-server-protocol'] = ftp_protocol

        result = self.manager.session.post(
            self.uri + '/operations/single-step-install', resource=self,
            body=body, wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)

        return result

    @logged_api_call
    def install_and_activate(
            self, bundle_level=None, ec_levels=None,
            install_disruptive=False, wait_for_completion=True,
            operation_timeout=None):
        """
        Installs and activates firmware on the Support Element (SE) of this CPC.

        Brief summary of firmware levels:

            The firmware is segmented into different subsystems called
            "Engineering Change" (EC), or sometimes "EC stream". An EC stream
            is identified by an EC number (e.g. "P30719").

            Each EC stream is at a particular code level called "Microcode
            Level" (MCL), or sometimes "MCL level". An MCL level for an EC
            stream is identified by an MCL number (e.g. "001"). MCL numbers
            are unique only within their EC stream and are consecutive numbers
            that increase towards newer MCL levels. Updates within an EC stream
            are installed sequentially, so if an EC stream has a particular
            MCL level installed, that implies that all earlier MCL levels
            within that EC stream are also installed.

            A particular set of MCL numbers for each EC stream is collected
            into a "bundle level" for the SE (e.g. "S81") or HMC (e.g. "H20").

        The firmware level for this method can be specified in three ways:

        * By specifying `bundle_level`: The updates for the specified bundle
          level will be installed.
        * By specifying `ec_levels`: Specific MCL levels for the specified EC
          streams will be installed.
        * By not specifying `bundle_level and `ec_levels`: All locally
          available updates will be installed.

        In all cases, the updates to be installed must already be available on
        the SE; they are *not* automatically downloaded from the IBM support
        site or from an FTP server.

        This method is implemented by performing the "CPC Install and Activate"
        operation which performs the following steps:

        * The specified updates are installed.
        * If all updates are installed successfully, they are activated, which
          includes rebooting the SE of this CPC.

        If an error occurs when installing the updates, any updates that were
        successfully installed are rolled back.

        Note that this operation does *not* perform a backup, an accept of
        previously activated updates, or an accept of the newly installed
        updates.

        Note that this operation does not require that previously activated
        updates are first accepted before invoking this operation.

        Note that it is not possible to downgrade the SE firmware with this
        operation.

        HMC/SE version requirements:

        * :ref`API feature` "cpc-install-and-activate"

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Change Internal Code" task.

        Parameters:

          bundle_level (string): Name of the bundle to be installed on the SE
            of this CPC (e.g. 'S51').

            This parameter is mutually exclusive with `ec_levels`. If both
            are not provided, all locally available updates will be installed.

          ec_levels (list of tuple(ec,mcl)): Updates to be installed on the
            SE of this CPC, as a list of tuples (ec, mcl) where:

              - ec (string): EC number of the EC stream (e.g. "P30719")
              - mcl (string): MCL number within the EC stream (e.g. "001")

            This parameter is mutually exclusive with `bundle_level`. If both
            are not provided, all locally available updates will be installed.

          install_disruptive (bool):
            Install disruptive changes.

            - If `True`, all firmware will be installed regardless of whether
              it is disruptive to CPC operations.
            - If `False` and `bundle_level` or `ec_levels` is specified, the
              request will fail if the operation encounters a disruptive
              change.
            - If `False` and neither `bundle_level` or `ec_levels` are
              specified, all concurrent changes will be installed, and the
              disruptive ones will be left uninstalled.

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

          string or `None` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns a string that is the
            'message' field of the successfully completed job, or `None` if the
            successfully completed job has no message.

            If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC.
            This job does not support cancellation.
            Once that job successfully completes, it may optionally have a
            'message' field in its 'job-results' field.

            In all cases, if a message is returned it may indicate that
            disruptive updates were not installed, or that updates are in
            pending state because some follow-up action is needed. In the
            latter case, the "View Internal Code Changes Summary" task on the
            HMC or SE GUI will provide a list of the additional actions that
            are required. It is not possible to query this information via the
            API.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """

        body = {}
        if bundle_level is not None:
            body['bundle-level'] = bundle_level
        if ec_levels is not None:
            body['ec-levels'] = \
                [{"number": ec[0], "mcl": ec[1]} for ec in ec_levels]
        if install_disruptive:
            body['install-disruptive'] = True

        job = self.manager.session.post(
            self.uri + '/operations/install-and-activate', resource=self,
            body=body, wait_for_completion=False)

        if wait_for_completion:
            job_result_obj = job.wait_for_completion(operation_timeout)
            if job_result_obj:
                return job_result_obj.get('message', None)
            return None

        return job

    @logged_api_call
    def delete_retrieved_internal_code(
            self, ec_levels=None, wait_for_completion=True,
            operation_timeout=None):
        """
        Deletes retrieved updates that have not been installed on the Support
        Element (SE) of this CPC.

        This is done by performing the "CPC Delete Retrieved Internal Code"
        operation which performs the following steps:

        * The specified retrieved and uninstalled firmware updates are deleted
          from the SE of this CPC.

        If an error occurs when deleting the updates, then only the updates
        that were unsuccessfully deleted will remain on the system; any updates
        that were deleted before reaching an error will remain deleted upon
        completion of the operation.

        Note that it is not possible to downgrade the SE firmware with this
        operation.

        HMC/SE version requirements:

        * :ref`API feature` "cpc-install-and-activate"

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Change Internal Code" task.

        Parameters:

          ec_levels (list of tuple(ec,mcl)): The MCL levels of retrieved and
            uninstalled updates that will be deleted on the SE of this CPC, as
            a list of tuples (ec, mcl) where:

              - ec (string): EC number of the EC stream (e.g. "P30719")
              - mcl (string): MCL number within the EC stream (e.g. "001")

            Within each specified EC stream, only the one update for the
            specified MCL level will be deleted.

            If `None`, all retrieved and uninstalled updates are deleted on the
            SE of this CPC.

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
            This job does not support cancellation.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """

        body = {}
        if ec_levels is not None:
            body['ec-levels'] = \
                [{"number": ec[0], "mcl": ec[1]} for ec in ec_levels]

        result = self.manager.session.post(
            self.uri + '/operations/delete-retrieved-internal-code',
            resource=self, body=body, wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)

        return result

    @logged_api_call
    def swap_current_time_server(self, stp_id):
        """
        Makes this CPC the current time server of an STP-only Coordinated Timing
        Network (CTN).

        This is done by performing the "Swap Current Time Server" operation.

        The CTN must be STP-only; mixed CTNs will be rejected.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Manage System Time" and "Modify Assigned
          Server Roles" tasks.

        Parameters:

          stp_id (string): STP identifier of the CTN.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'stp-id': stp_id,
        }
        self.manager.session.post(
            self.uri + '/operations/swap-cts', body=body)

    @logged_api_call
    def set_stp_config(
            self, stp_id, new_stp_id, force, preferred_time_server,
            backup_time_server, arbiter, current_time_server):
        """
        Sets the configuration of the STP-only Coordinated Timing Network
        (CTN) whose current time server is this CPC.

        This is done by performing the "Set STP Configuration" operation.

        The CTN must be STP-only; mixed CTNs will be rejected.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Manage System Time" and "Modify Assigned
          Server Roles" tasks.

        Parameters:

          stp_id (string): Current STP identifier of the CTN to be updated.
            This CPC must be the current time server of the CTN.

          new_stp_id (string): The new STP identifier for the CTN.
            If `None`, the STP identifier of the CTN is not changed.

          force (bool): Required. Indicates whether a disruptive operation is
            allowed (`True`) or rejected (`False`). Must not be `None`.

          preferred_time_server (zhmcclient.STPNode): Identifies the CPC to be
            the preferred time server of the CTN. Must not be `None`.

          backup_time_server (zhmcclient.STPNode): Identifies the CPC to be the
            backup time server of the CTN. If `None`, the CTN will have no
            backup time server.

          arbiter (zhmcclient.STPNode): Identifies the CPC to be the arbiter for
            the CTN. If `None`, the CTN will have no arbiter.

          current_time_server (string): Identifies which time server takes on
            the role of the current time server. Must be one of:

            * "preferred" - the preferred time server is the current time server
            * "backup" - the backup time server is the current time server

            Must not be `None`.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'stp-id': stp_id,
            'force': force,
            'preferred-time-server': preferred_time_server.json(),
            'current-time-server': current_time_server,
        }
        if new_stp_id:
            body['new-stp-id'] = new_stp_id
        if backup_time_server:
            body['backup-time-server'] = backup_time_server.json()
        if arbiter:
            body['arbiter'] = arbiter.json()
        self.manager.session.post(
            self.uri + '/operations/set-stp-config', body=body)

    @logged_api_call
    def change_stp_id(self, stp_id):
        """
        Changes the STP identifier of the STP-only Coordinated Timing Network
        (CTN) whose current time server is this CPC.

        This is done by performing the "Change STP-only Coordinated Timing
        Network" operation.

        The CTN must be STP-only; mixed CTNs will be rejected.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Manage System Time" and "Rename CTN" tasks.

        Parameters:

          stp_id (string): STP identifier of the CTN to be updated.
            This CPC must be the current time server of the CTN.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'stp-id': stp_id,
        }
        self.manager.session.post(
            self.uri + '/operations/change-stponly-ctn', body=body)

    @logged_api_call
    def join_ctn(self, stp_id):
        """
        Causes this CPC to join an STP-only Coordinated Timing Network (CTN).

        This is done by performing the "Join STP-only Coordinated Timing
        Network" operation.

        If the CPC is already a member of a different CTN but not in the role
        of the current time server, it is removed from that CTN.

        If the CPC object has an ETR ID, the ETR ID is removed.

        The CPC must not be the current time server of a different CTN.

        The CTN must be STP-only; mixed CTNs will be rejected.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Manage System Time" and "Add Systems to CTN"
          tasks.

        Parameters:

          stp_id (string): STP identifier of the CTN to be joined.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'stp-id': stp_id,
        }
        self.manager.session.post(
            self.uri + '/operations/join-stponly-ctn', body=body)

    @logged_api_call
    def leave_ctn(self):
        """
        Causes this CPC to leave its current STP-only Coordinated Timing
        Network (CTN).

        This is done by performing the "Leave STP-only Coordinated Timing
        Network" operation.

        The CTN must be STP-only; mixed CTNs will be rejected.

        The CPC must not be the current time server of its current CTN.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Manage System Time" and "Remove Systems from
          CTN" tasks.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(
            self.uri + '/operations/leave-stponly-ctn')

    def _convert_to_config(self, inventory_list, include_unused_adapters):
        """
        Convert the inventory list to a DPM configuration dict.

        Important: In order to support export of DPM configs with zhmcclient
        versions that have support for newer features from older machines and
        import into older machines, any dictionary items for NEWLY added
        features must be omitted if empty.
        """
        cpc_uri = self.get_property('object-uri')
        cpc_uris = [cpc_uri]

        config_dict = OrderedDict()

        config_dict['se-version'] = self.prop('se-version')
        config_dict['available-features-list'] = self.prop(
            'available-features-list', [])
        config_dict['cpc-properties'] = {
            'auto-start-list': self.prop('auto-start-list'),
            'description': self.prop('description'),
            'management-world-wide-port-name':
                self.prop('management-world-wide-port-name'),
        }
        config_dict['capacity-groups'] = [
            dict(group.properties) for group in
            self.capacity_groups.list(full_properties=True)]

        partitions = extractByParent(
            RC_PARTITION, cpc_uris, inventory_list)
        # This item is required by the "Import DPM Configuration" operation
        config_dict['partitions'] = partitions
        partition_uris = [x['object-uri'] for x in partitions]

        adapters = extractAdapters(cpc_uri, inventory_list)
        if adapters:
            config_dict['adapters'] = adapters
        adapter_uris = [x['object-uri'] for x in adapters]

        nics = extractByParent(
            RC_NIC, partition_uris, inventory_list)
        if nics:
            config_dict['nics'] = nics

        hbas = extractByParent(
            RC_HBA, partition_uris, inventory_list)
        if hbas:
            config_dict['hbas'] = hbas

        virtual_functions = extractByParent(
            RC_VIRTUAL_FUNCTION, partition_uris, inventory_list)
        if virtual_functions:
            config_dict['virtual-functions'] = virtual_functions

        virtual_switches = extractByParent(
            RC_VIRTUAL_SWITCH, cpc_uris, inventory_list)
        if virtual_switches:
            config_dict['virtual-switches'] = virtual_switches

        storage_sites = extractByValueInListProperty(
            RC_STORAGE_SITE, cpc_uri, 'cpc-uris', inventory_list)
        if storage_sites:
            config_dict['storage-sites'] = storage_sites
        storage_site_uris = [x['object-uri'] for x in storage_sites]

        storage_subsystems = extractByPropertyInListValue(
            RC_STORAGE_SUBSYSTEM, 'storage-site-uri', storage_site_uris,
            inventory_list)
        if storage_subsystems:
            config_dict['storage-subsystems'] = storage_subsystems
        storage_subsystem_uris = [x['object-uri'] for x in storage_subsystems]

        storage_fabrics = extractByPropertyInListValue(
            RC_STORAGE_FABRIC, 'cpc-uri', cpc_uris, inventory_list)
        if storage_fabrics:
            config_dict['storage-fabrics'] = storage_fabrics

        storage_switches = extractByPropertyInListValue(
            RC_STORAGE_SWITCH, 'storage-site-uri', storage_site_uris,
            inventory_list)
        if storage_switches:
            config_dict['storage-switches'] = storage_switches

        storage_control_units = extractByPropertyInListValue(
            RC_STORAGE_CONTROL_UNIT, 'parent', storage_subsystem_uris,
            inventory_list)
        if storage_control_units:
            config_dict['storage-control-units'] = storage_control_units
        storage_control_unit_uris = [x['object-uri']
                                     for x in storage_control_units]

        storage_paths = extractByPropertyInListValue(
            RC_STORAGE_PATH, 'parent', storage_control_unit_uris,
            inventory_list)
        if storage_paths:
            config_dict['storage-paths'] = storage_paths

        storage_ports = extractByPropertyInListValue(
            RC_STORAGE_PORT, 'parent', adapter_uris, inventory_list)
        if storage_ports:
            config_dict['storage-ports'] = storage_ports

        network_ports = extractByPropertyInListValue(
            RC_NETWORK_PORT, 'parent', adapter_uris, inventory_list)
        if network_ports:
            config_dict['network-ports'] = network_ports

        storage_groups = extractByPropertyInListValue(
            RC_STORAGE_GROUP, 'cpc-uri', cpc_uris, inventory_list)
        if storage_groups:
            config_dict['storage-groups'] = storage_groups
        storage_group_uris = [x['object-uri'] for x in storage_groups]

        storage_volumes = extractByPropertyInListValue(
            RC_STORAGE_VOLUME, 'parent', storage_group_uris, inventory_list)
        if storage_volumes:
            config_dict['storage-volumes'] = storage_volumes

        storage_templates = extractByPropertyInListValue(
            RC_STORAGE_TEMPLATE, 'cpc-uri', cpc_uris, inventory_list)
        if storage_templates:
            config_dict['storage-templates'] = storage_templates
        storage_template_uris = [x['object-uri'] for x in storage_templates]

        storage_template_volumes = extractByPropertyInListValue(
            RC_STORAGE_TEMPLATE_VOLUME, 'parent', storage_template_uris,
            inventory_list)
        if storage_template_volumes:
            config_dict['storage-template-volumes'] = storage_template_volumes

        virtual_storage_resources = extractByPropertyInListValue(
            RC_VIRTUAL_STORAGE_RESOURCE, 'parent', storage_group_uris,
            inventory_list)
        if virtual_storage_resources:
            config_dict['virtual-storage-resources'] = virtual_storage_resources

        tape_links = extractByPropertyInListValue(
            RC_TAPE_LINK, 'cpc-uri', cpc_uris, inventory_list)
        if tape_links:
            config_dict['tape-links'] = tape_links
        tape_link_uris = [x['object-uri'] for x in tape_links]

        tape_libraries = extractByPropertyInListValue(
            RC_TAPE_LIBRARY, 'cpc-uri', cpc_uris, inventory_list)
        if tape_libraries:
            config_dict['tape-libraries'] = tape_libraries

        virtual_tape_resources = extractByParent(
            RC_VIRTUAL_TAPE_RESOURCE, tape_link_uris, inventory_list)
        if virtual_tape_resources:
            config_dict['virtual-tape-resources'] = virtual_tape_resources

        classname_for_partition_links = 'partition-link'
        partition_links = extractByPropertyInListValue(
            classname_for_partition_links, 'cpc-uri', cpc_uris, inventory_list)
        if partition_links:
            config_dict['partition-links'] = partition_links

        certificates = extractByPropertyInListValue(
            RC_CERTIFICATE, 'parent', cpc_uris, inventory_list)
        if certificates:
            _add_encoded(self.manager.console, certificates)
            config_dict['certificates'] = certificates

        if not include_unused_adapters:
            _drop_unused_adapters_and_resources(config_dict)

        sort_lists(config_dict)

        return config_dict

    @logged_api_call
    def get_sustainability_data(
            self, range="last-week", resolution="one-hour",
            custom_range_start=None, custom_range_end=None):
        # pylint: disable=redefined-builtin
        """
        Get energy management related metrics for the CPC on a specific
        historical time range. The metrics are returned as multiple data points
        covering the requested time range with the requested resolution.
        This method performs the "Get CPC Historical Sustainability Data" HMC
        operation.

        HMC/SE version requirements:

        * :ref`API feature` environmental-metrics"

        Authorization requirements:

        * Object-access permission to this CPC
        * Task permission to the "Environmental Dashboard" task

        Parameters:

          range (:term:`string`):
            Time range for the requested data points, as follows:

            * "last-day" - Last 24 hours.
            * "last-week" - Last 7 days (default).
            * "last-month" - Last 30 days.
            * "last-three-months" - Last 90 days.
            * "last-six-months" - Last 180 days.
            * "last-year" - Last 365 days.
            * "custom" - From `custom_range_start` to `custom_range_end`.

          resolution (:term:`string`):
            Resolution for the requested data points. This is the time interval
            in between the data points. For systems where the
            "environmental-metrics" API feature is not available, the minimum
            resolution is "one-hour".

            The possible values are as follows:

            * "fifteen-minutes" - 15 minutes.
            * "one-hour" - 60 minutes (default).
            * "one-day" - 24 hours.
            * "one-week" - 7 days.
            * "one-month" - 30 days.

          custom_range_start (:class:`~py:datetime.datetime`):
            Start of custom time range. Timezone-naive values are interpreted
            using the local system time. Required if `range` is "custom".

          custom_range_end (:class:`~py:datetime.datetime`):
            End of custom time range. Timezone-naive values are interpreted
            using the local system time. Required if `range` is "custom".

        Returns:

          dict: A dictionary with items as described for the response body
          of the "Get CPC Historical Sustainability Data" HMC operation.
          Timestamp fields are represented as timezone-aware
          :class:`~py:datetime.datetime` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'range': range,
            'resolution': resolution,
        }
        if range == "custom":
            body['custom-range-start'] = \
                timestamp_from_datetime(custom_range_start)
            body['custom-range-end'] = \
                timestamp_from_datetime(custom_range_end)
        result = self.manager.session.post(
            self.uri + '/operations/get-historical-sustainability-data',
            body=body)
        for field_array in result.values():
            for item in field_array:
                if 'timestamp' in item:
                    item['timestamp'] = \
                        datetime_from_timestamp(item['timestamp'])
        return result


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
    resource_classes = ['dpm-resources']
    api_features = client.consoles.console.list_api_features()
    if 'secure-boot-with-certificates' in api_features:
        resource_classes.append('certificate-resources')

    inventory_list = client.get_inventory(resource_classes)
    error_msgs = []
    for item in inventory_list:
        if item.get('class') == 'inventory-error':
            details = ""
            if item.get('inventory-error-code') == 5:
                details = \
                    f" / Details: {dict(item.get('inventory-error-details'))}"

            msg = (
                f"Inventory error {item.get('inventory-error-code')} for "
                f"resource with URI {item.get('uri')}: "
                f"{item.get('inventory-error-text')}{details}")
            error_msgs.append(msg)
    if error_msgs:
        msgs = '\n  '.join(error_msgs)
        raise ConsistencyError(
            f"Some resources could not be fully inventoried:\n  {msgs}")
    return inventory_list


def _add_encoded(console, certificates):
    """
    Takes a list of dicts representing certificate objects and adds
    the corresponding encoded certificate data to each dict.
    """
    for cert_dict in certificates:
        cert = console.certificates.list(
            filter_args={'name': cert_dict['name']})[0]
        cert_dict.update(cert.get_encoded())


def _drop_unused_adapters_and_resources(dpm_config):
    """
    Removes all adapters, virtual switch, storage/network port objects from
    dpm_config in place that aren't referenced by actual DPM configuration
    elements.
    """
    _remove_unreferenced_keys(dpm_config, 'virtual-switches', ['adapters'])
    removed_adapters = _remove_unreferenced_keys(dpm_config, 'adapters',
                                                 ['network-ports',
                                                  'storage-ports'])
    _remove_child_elements(dpm_config, 'network-ports', removed_adapters)
    _remove_child_elements(dpm_config, 'storage-ports', removed_adapters)


def _remove_unreferenced_keys(dpm_config, key_to_update, keys_to_ignore):
    """
    Creates a string representation of dpm_config, EXCLUDING keys key_to_update
    and keys_to_ignore. Then iterates the list of key_to_update
    entries within dpm_config to collect those that are referenced by their
    object-id within that string representation. Then updates dpm_config
    for key_to_update in place to that list of elements that are actually
    referenced.
    Returns a list of object-uri fields of all dropped objects.
    """
    config = str(
        {key: dpm_config[key] for key in dpm_config
         if (key != key_to_update and key not in keys_to_ignore)})
    referenced_keys = []
    dropped_uris = []
    for elem in dpm_config[key_to_update]:
        if elem['object-id'] in config:
            referenced_keys.append(elem)
        else:
            dropped_uris.append(elem['object-uri'])
    dpm_config[key_to_update] = referenced_keys
    return dropped_uris


def _remove_child_elements(dpm_config, key_to_update, dropped_parents):
    """
    Updates dpm_config for key_to_update in place removing all those elements
    with a parent in the list of dropped_parents.
    """
    retained = []
    for elem in dpm_config[key_to_update]:
        if elem['parent'] not in dropped_parents:
            retained.append(elem)
    dpm_config[key_to_update] = retained


def sort_lists(dpm_config):
    """
    Sorts all elements in dpm_config that are lists (of strings/dicts).
    """
    for key in dpm_config:
        if isinstance(dpm_config[key], list):
            dpm_config[key] = _sorted(dpm_config[key])


def _sorted(items):
    """
    Returns a sorted version of the given items (if they are dicts/strings).
    """
    sorted_items = items
    if len(items) > 1:
        if isinstance(items[0], str):
            sorted_items = sorted(items)
        elif isinstance(items[0], dict):
            sort_key = _sort_key(items[0])
            if sort_key is not None:
                sorted_items = sorted(items, key=lambda x: x[sort_key])
    return sorted_items


def _sort_key(item):
    for key in ['adapter-id', 'name', 'element-id', 'object-id']:
        if key in item:
            return key
    return None
