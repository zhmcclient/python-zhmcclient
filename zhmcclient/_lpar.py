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
A :term:`LPAR` (Logical Partition) is a subset of the hardware resources of a
:term:`CPC` in classic mode (or ensemble mode), virtualized as a separate
computer.

LPARs cannot be created or deleted by the user; they can only be listed.

LPAR resources are contained in CPC resources.

LPAR resources only exist in CPCs that are in classic mode (or ensemble mode).
CPCs in DPM mode have :term:`Partition` resources, instead.
"""


import time
import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._exceptions import StatusTimeout
from ._constants import HMC_LOGGER_NAME
from ._logging import get_logger, logged_api_call
from ._utils import RC_LOGICAL_PARTITION, make_query_str, \
    warn_deprecated_parameter, datetime_from_timestamp, timestamp_from_datetime

__all__ = ['LparManager', 'Lpar']

HMC_LOGGER = get_logger(HMC_LOGGER_NAME)


class LparManager(BaseManager):
    """
    Manager providing access to the :term:`LPARs <LPAR>` in a particular
    :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Cpc` object (in DPM mode):

    * :attr:`~zhmcclient.Cpc.lpars`

    HMC/SE version requirements: None
    """

    def __init__(self, cpc):
        # This function should not go into the docs.
        # Parameters:
        #   cpc (:class:`~zhmcclient.Cpc`):
        #     CPC defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name',
        ]

        super().__init__(
            resource_class=Lpar,
            class_name=RC_LOGICAL_PARTITION,
            session=cpc.manager.session,
            parent=cpc,
            base_uri='/api/logical-partitions',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props,
            supports_properties=True)

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: :term:`CPC` defining the scope for this
        manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the LPARs in this CPC.

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

        * Object-access permission to this CPC.
        * Object-access permission to any LPAR to be included in the result.

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

          : A list of :class:`~zhmcclient.Lpar` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'logical-partitions'
        list_uri = f'{self.cpc.uri}/logical-partitions'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None)


class Lpar(BaseResource):
    """
    Representation of an :term:`LPAR`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.LparManager`).

    HMC/SE version requirements: None
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.LparManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, LparManager), (
            f"Lpar init: Expected manager type {LparManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)

    @logged_api_call(blanked_properties=['ssc-master-pw', 'zaware-master-pw'],
                     properties_pos=1)
    def update_properties(self, properties):
        """
        Update writeable properties of this LPAR.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "Change Object Definition" task.
        * Since HMC 2.14.1: If the "next-activation-profile-name" property is to
          be updated, task permission for the "Change Object Options" task or
          the "Customize/Delete Activation Profiles" task.
        * Before HMC 2.15.0: For an LPAR whose activation-mode is "zaware", task
          permission for the "Firmware Details" task.
        * Since HMC 2.15.0: If any of the "ssc-*" or "zaware-*" properties is to
          be updated, task permission for the "Firmware Details" task.
        * Since HMC 2.15.0: If any of the numbers of allocated or reserved cores
          is to be updated, task permission for the "Logical Processor Add"
          task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'Logical Partition object' in the
            :term:`HMC API` book.

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
    def activate(self, wait_for_completion=True,
                 operation_timeout=None, status_timeout=None,
                 allow_status_exceptions=False, activation_profile_name=None,
                 force=False):
        """
        Activate (start) this LPAR, using the HMC operation "Activate Logical
        Partition".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it may take a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "not-operating" (which indicates that the LPAR is active but
        no operating system is running), or "operating", or if
        `allow_status_exceptions` was set additionally in the state
        "exceptions".

        The following approach is used to determine the desired state to wait
        for if `wait_for_completion=True`:

        - if the 'operating-mode' property of the image profile is 'ssc' or
          'zaware', the desired state is "operating".
        - if the profile specified in `activation_profile_name` is not the
          LPAR's image profile, it is assumed to be a load profile and
          the desired state is "operating".
        - if the 'load-at-activation' property of the image profile is True,
          the desired state is "operating".
        - else, the desired state is "not-operating".

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "Activate" task.

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "not-operating" or "operating" (or in addition
              "exceptions", if `allow_status_exceptions` was set.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached the desired status, after the HMC operation has completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

          allow_status_exceptions (bool):
            Boolean controlling whether LPAR status "exceptions" is considered
            an additional acceptable end status when `wait_for_completion` is
            set.

          activation_profile_name (:term:`string`):
            Name of the load or image activation profile to be used instead
            of the one specified in the `next-activation-profile-name` property
            of the LPAR, or `None`.

            If this parameter specifies an image activation profile, its name
            must match the LPAR name. For non-SSC partitions, the image
            profile's `load-at-activation` property determines whether the
            activation is followed by a load of the control program using the
            load-related parameters from the image profile. SSC partitions are
            always auto-loaded (regardless of the `load-at-activation`
            property).

            If this parameter specifies a load activation profile, the
            activation uses the image profile with the same name as the LPAR.
            The activation is always followed by a load of the control program
            (regardless of the image profile's `load-at-activation` property)
            using the parameters from the load profile.

            If this parameter is `None`, the `next-activation-profile-name`
            property of the LPAR will be used. That property can again specify
            an image profile or a load profile which are treated as described
            above. If that property is `None`, the image profile with the same
            name as the LPAR is used and is treated as described above.

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status.

            TBD: What will happen with the LPAR in that case (deactivated then
            activated? nothing?)

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired LPAR status.
        """
        body = {}
        if activation_profile_name:
            body['activation-profile-name'] = activation_profile_name
        if force:
            body['force'] = force
        result = self.manager.session.post(
            self.uri + '/operations/activate', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            # If an automatic load is performed, the LPAR status will first go
            # to 'not-operating' and then later to 'operating'. So we cannot
            # just wait for any of those two, but need to have an understanding
            # whether we expect auto-load.
            image_profile_mgr = self.manager.parent.image_activation_profiles
            image_profile = image_profile_mgr.find(name=self.name)
            auto_load = image_profile.get_property('load-at-activation')
            # Note that the LPAR 'activation-mode' property is 'not-set' while
            # the LPAR is inactive, so we need to look at the image profile
            # to determine the mode.
            op_mode = image_profile.get_property('operating-mode')
            load_profile_specified = activation_profile_name is not None and \
                activation_profile_name != self.name
            mode_load = op_mode in ('ssc', 'zaware')
            if auto_load or load_profile_specified or mode_load:
                statuses = ["operating"]
            else:
                statuses = ["not-operating"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def deactivate(self, wait_for_completion=True,
                   operation_timeout=None, status_timeout=None,
                   allow_status_exceptions=False, force=False):
        """
        De-activate (stop) this LPAR, using the HMC operation "Deactivate
        Logical Partition".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it may take a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "not-activated", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "Deactivate" task.

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "not-activated" (or in addition "exceptions", if
              `allow_status_exceptions` was set.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached the desired status, after the HMC operation has completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

          allow_status_exceptions (bool):
            Boolean controlling whether LPAR status "exceptions" is considered
            an additional acceptable end status when `wait_for_completion` is
            set.

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status.

            TBD: What will happen with the LPAR in that case (deactivated then
            activated? nothing?)

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired LPAR status.
        """
        body = {}
        if force:
            body['force'] = force
        result = self.manager.session.post(
            self.uri + '/operations/deactivate', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["not-activated"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def scsi_load(self, load_address, wwpn, lun, load_parameter=None,
                  disk_partition_id=None,
                  operating_system_specific_load_parameters=None,
                  boot_record_logical_block_address=None, force=False,
                  wait_for_completion=True, operation_timeout=None,
                  status_timeout=None, allow_status_exceptions=False,
                  secure_boot=False, os_ipl_token=None, clear_indicator=True):
        # pylint: disable=invalid-name
        """
        Load (boot) this LPAR from a designated SCSI device, using the
        HMC operation "SCSI Load".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "operating", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "SCSI Load" task.

        Parameters:

          load_address (:term:`string`):
            Device number of the boot device.

          wwpn (:term:`string`):
            Worldwide port name (WWPN) of the target SCSI device to be
            used for this operation, in hexadecimal.

          lun (:term:`string`):
            Hexadecimal logical unit number (LUN) to be used for the
            SCSI load.

          load_parameter (:term:`string`):
            Optional load control string.
            If empty string or `None`, it is not passed to the HMC, and the
            HMC default of an empty string will be used.

          disk_partition_id (:term:`integer`):
            Optional disk-partition-id (also called the boot program
            selector) to be used for the SCSI load.
            If `None`, it is not passed to the HMC, and the HMC default
            of 0 will be used.

          operating_system_specific_load_parameters (:term:`string`):
            Optional operating system specific load parameters to be
            used for the SCSI load.
            If empty string or `None`, it is not passed to the HMC, and the
            HMC default of an empty string will be used.

          boot_record_logical_block_address (:term:`string`):
            Optional hexadecimal boot record logical block address to
            be used for the SCSI load.
            If `None`, it is not passed to the HMC, and the HMC default
            of "0" will be used.

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "operating" (or in addition "exceptions", if
              `allow_status_exceptions` was set.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached the desired status, after the HMC operation has completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

          allow_status_exceptions (bool):
            Boolean controlling whether LPAR status "exceptions" is considered
            an additional acceptable end status when `wait_for_completion` is
            set.

          secure_boot (bool):
            Boolean controlling whether the system checks the software
            signature of what is loaded against what the distributor signed it
            with.
            If `False` or `None`, it is not passed to the HMC, and the
            HMC default of `False` will be used.
            Requires the LPAR to be on a z15 or later.

          os_ipl_token (:term:`string`):
            Optional hexadecimal value to be used for the SCSI load.
            If `None`, it is not passed to the HMC.

          clear_indicator (bool):
            Optional boolean controlling whether the memory should be
            cleared before performing the load or not cleared.
            If `True` or `None`, it is not passed to the HMC, and the HMC
            default of `True` will be used if the LPAR is on a z14 with
            SE version 2.14.1 or higher.
            Requires the LPAR to be on a z14 with SE version 2.14.1 or higher.

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired LPAR status.
        """
        body = {}
        body['load-address'] = load_address
        body['world-wide-port-name'] = wwpn
        body['logical-unit-number'] = lun
        if load_parameter:
            body['load-parameter'] = load_parameter
        if disk_partition_id is not None:
            body['disk-partition-id'] = disk_partition_id
        if operating_system_specific_load_parameters:
            body['operating-system-specific-load-parameters'] = \
                operating_system_specific_load_parameters
        if boot_record_logical_block_address is not None:
            body['boot-record-logical-block-address'] = \
                boot_record_logical_block_address
        if os_ipl_token is not None:
            body['os-ipl-token'] = os_ipl_token
        if clear_indicator not in (True, None):
            # Note: Requires SE >= 2.14.1, but caller needs to control this
            body['clear-indicator'] = clear_indicator
        if force:
            body['force'] = force
        if secure_boot:
            # Note: Requires SE >= 2.15, but caller needs to control this
            body['secure-boot'] = secure_boot
        result = self.manager.session.post(
            self.uri + '/operations/scsi-load', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["operating"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def scsi_dump(self, load_address, wwpn, lun, load_parameter=None,
                  disk_partition_id=None,
                  operating_system_specific_load_parameters=None,
                  boot_record_logical_block_address=None, os_ipl_token=None,
                  wait_for_completion=True, operation_timeout=None,
                  status_timeout=None, allow_status_exceptions=False,
                  force=False, secure_boot=False):
        # pylint: disable=invalid-name
        """
        Load a standalone dump program from a designated SCSI device
        in this LPAR, using the HMC operation "SCSI Dump".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "operating", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "SCSI Dump" task.

        Parameters:

          load_address (:term:`string`):
            Device number of the boot device.

          wwpn (:term:`string`):
            Worldwide port name (WWPN) of the target SCSI device to be
            used for this operation, in hexadecimal.

          lun (:term:`string`):
            Hexadecimal logical unit number (LUN) to be used for the
            SCSI dump.

          load_parameter (:term:`string`):
            Optional load control string.
            If empty string or `None`, it is not passed to the HMC, and the
            HMC default of an empty string will be used.

          disk_partition_id (:term:`integer`):
            Optional disk-partition-id (also called the boot program
            selector) to be used for the SCSI dump.
            If `None`, it is not passed to the HMC, and the HMC default
            of 0 will be used.

          operating_system_specific_load_parameters (:term:`string`):
            Optional operating system specific load parameters to be
            used for the SCSI dump.
            If empty string or `None`, it is not passed to the HMC, and the
            HMC default of an empty string will be used.

          boot_record_logical_block_address (:term:`string`):
            Optional hexadecimal boot record logical block address to
            be used for the SCSI dump.
            If `None`, it is not passed to the HMC, and the HMC default
            of "0" will be used.

          os_ipl_token (:term:`string`):
            Optional hexadecimal value to be used for the SCSI dump.
            If `None`, it is not passed to the HMC.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "operating" (or in addition "exceptions", if
              `allow_status_exceptions` was set.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached the desired status, after the HMC operation has completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

          allow_status_exceptions (bool):
            Boolean controlling whether LPAR status "exceptions" is considered
            an additional acceptable end status when `wait_for_completion` is
            set.

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status.

          secure_boot (bool):
            Boolean controlling whether the system checks the software
            signature of what is loaded against what the distributor signed it
            with.
            If `False` or `None`, it is not passed to the HMC, and the
            HMC default of `False` will be used.
            Requires the LPAR to be on a z15 or later.

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired LPAR status.
        """
        body = {}
        body['load-address'] = load_address
        body['world-wide-port-name'] = wwpn
        body['logical-unit-number'] = lun
        if load_parameter:
            body['load-parameter'] = load_parameter
        if disk_partition_id is not None:
            body['disk-partition-id'] = disk_partition_id
        if operating_system_specific_load_parameters:
            body['operating-system-specific-load-parameters'] = \
                operating_system_specific_load_parameters
        if boot_record_logical_block_address is not None:
            body['boot-record-logical-block-address'] = \
                boot_record_logical_block_address
        if os_ipl_token is not None:
            body['os-ipl-token'] = os_ipl_token
        if force:
            body['force'] = force
        if secure_boot:
            # Note: Requires SE >= 2.15, but caller needs to control this
            body['secure-boot'] = secure_boot
        result = self.manager.session.post(
            self.uri + '/operations/scsi-dump', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["operating"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def nvme_load(self, load_address, load_parameter=None, secure_boot=False,
                  clear_indicator=True, disk_partition_id=None,
                  operating_system_specific_load_parameters=None,
                  boot_record_logical_block_address=None, force=False,
                  wait_for_completion=True, operation_timeout=None,
                  status_timeout=None, allow_status_exceptions=False):
        # pylint: disable=invalid-name
        """
        Load (boot) this LPAR from a designated NVMe device, using the
        HMC operation "NVMe Load".

        This operation requires z15 or later.

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "operating", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Task permission for the "Load" task.

        Parameters:

          load_address (:term:`string`):
            Device number of the boot device.

          load_parameter (:term:`string`):
            Optional load control string.
            If empty string or `None`, it is not passed to the HMC, and the
            HMC default of an empty string will be used.

          secure_boot (bool):
            Boolean controlling whether the system checks the software
            signature of what is loaded against what the distributor signed it
            with.
            If `False` or `None`, it is not passed to the HMC, and the
            HMC default of `False` will be used.
            Requires the LPAR to be on a z15 or later.

          clear_indicator (bool):
            Optional boolean controlling whether the memory should be
            cleared before performing the load or not cleared.
            If `True` or `None`, it is not passed to the HMC, and the HMC
            default of `True` will be used if the LPAR is on a z14 with
            SE version 2.14.1 or higher.
            Requires the LPAR to be on a z14 with SE version 2.14.1 or higher.

          disk_partition_id (:term:`integer`):
            Optional disk-partition-id (also called the boot program
            selector) to be used for the NVMe Load.
            If `None`, it is not passed to the HMC, and the HMC default
            of 0 will be used.

          operating_system_specific_load_parameters (:term:`string`):
            Optional operating system specific load parameters to be
            used for the NVMe Load.
            If empty string or `None`, it is not passed to the HMC, and the
            HMC default of an empty string will be used.

          boot_record_logical_block_address (:term:`string`):
            Optional hexadecimal boot record logical block address to
            be used for the NVMe Load.
            If `None`, it is not passed to the HMC, and the HMC default
            of "0" will be used.

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "operating" (or in addition "exceptions", if
              `allow_status_exceptions` was set.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached the desired status, after the HMC operation has completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

          allow_status_exceptions (bool):
            Boolean controlling whether LPAR status "exceptions" is considered
            an additional acceptable end status when `wait_for_completion` is
            set.

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired LPAR status.
        """
        body = {}
        body['load-address'] = load_address
        if load_parameter:
            body['load-parameter'] = load_parameter
        if disk_partition_id is not None:
            body['disk-partition-id'] = disk_partition_id
        if operating_system_specific_load_parameters:
            body['operating-system-specific-load-parameters'] = \
                operating_system_specific_load_parameters
        if boot_record_logical_block_address is not None:
            body['boot-record-logical-block-address'] = \
                boot_record_logical_block_address
        if clear_indicator not in (True, None):
            # Note: Requires SE >= 2.14.1, but caller needs to control this
            body['clear-indicator'] = clear_indicator
        if force:
            body['force'] = force
        if secure_boot:
            # Note: Requires SE >= 2.15, but caller needs to control this
            body['secure-boot'] = secure_boot
        result = self.manager.session.post(
            self.uri + '/operations/nvme-load', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["operating"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def nvme_dump(self, load_address, load_parameter=None,
                  secure_boot=False, disk_partition_id=None,
                  operating_system_specific_load_parameters=None,
                  boot_record_logical_block_address=None, force=False,
                  wait_for_completion=True, operation_timeout=None,
                  status_timeout=None, allow_status_exceptions=False):
        # pylint: disable=invalid-name
        """
        Load a standalone dump program from a designated NVMe device
        in this LPAR, using the HMC operation "NVMe Dump".

        This operation requires z15 or later.

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "operating", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Task permission for the "NVMe Dump" task.

        Parameters:

          load_address (:term:`string`):
            Device number of the boot device.

          load_parameter (:term:`string`):
            Optional load control string.
            If empty string or `None`, it is not passed to the HMC, and the
            HMC default of an empty string will be used.

          secure_boot (bool):
            Boolean controlling whether the system checks the software
            signature of what is loaded against what the distributor signed it
            with.
            If `False` or `None`, it is not passed to the HMC, and the
            HMC default of `False` will be used.
            Requires the LPAR to be on a z15 or later.

          disk_partition_id (:term:`integer`):
            Optional disk-partition-id (also called the boot program
            selector) to be used for the NVMe dump.
            If `None`, it is not passed to the HMC, and the HMC default
            of 0 will be used.

          operating_system_specific_load_parameters (:term:`string`):
            Optional operating system specific load parameters to be
            used for the NVMe dump.
            If empty string or `None`, it is not passed to the HMC, and the
            HMC default of an empty string will be used.

          boot_record_logical_block_address (:term:`string`):
            Optional hexadecimal boot record logical block address to
            be used for the NVMe dump.
            If `None`, it is not passed to the HMC, and the HMC default
            of "0" will be used.

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "operating" (or in addition "exceptions", if
              `allow_status_exceptions` was set.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached the desired status, after the HMC operation has completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

          allow_status_exceptions (bool):
            Boolean controlling whether LPAR status "exceptions" is considered
            an additional acceptable end status when `wait_for_completion` is
            set.

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired LPAR status.
        """
        body = {}
        body['load-address'] = load_address
        if load_parameter:
            body['load-parameter'] = load_parameter
        if disk_partition_id is not None:
            body['disk-partition-id'] = disk_partition_id
        if operating_system_specific_load_parameters:
            body['operating-system-specific-load-parameters'] = \
                operating_system_specific_load_parameters
        if boot_record_logical_block_address is not None:
            body['boot-record-logical-block-address'] = \
                boot_record_logical_block_address
        if force:
            body['force'] = force
        if secure_boot:
            # Note: Requires SE >= 2.15, but caller needs to control this
            body['secure-boot'] = secure_boot
        result = self.manager.session.post(
            self.uri + '/operations/nvme-dump', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["operating"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def load(self, load_address=None, load_parameter=None,
             clear_indicator=True, store_status_indicator=False,
             wait_for_completion=True, operation_timeout=None,
             status_timeout=None, allow_status_exceptions=False,
             force=False):
        """
        Load (boot) this LPAR from a load address (boot device), using the HMC
        operation "Load Logical Partition".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "operating", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "Load" task.

        Parameters:

          load_address (:term:`string`): Device number of the boot device.
            Up to z13, this parameter is required.
            Starting with z14, this parameter is optional and defaults to the
            load address specified in the 'last-used-load-address' property of
            the Lpar.

          load_parameter (:term:`string`): Optional load control string.
            If empty string or `None`, it is not passed to the HMC, and the
            HMC default of an empty string will be used.

          clear_indicator (bool):
            Optional boolean controlling whether the memory should be
            cleared before performing the load or not cleared. The
            default value is `True`.

          store_status_indicator (bool):
            Optional boolean controlling whether the status should be
            stored before performing the Load. The default value is `False`.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "operating" (or in addition "exceptions", if
              `allow_status_exceptions` was set.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached the desired status, after the HMC operation has completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

          allow_status_exceptions (bool):
            Boolean controlling whether LPAR status "exceptions" is considered
            an additional acceptable end status when `wait_for_completion` is
            set.

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status.

            TBD: What will happen with the LPAR in that case (deactivated then
            activated? nothing?)

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired LPAR status.
        """
        body = {}
        if load_address:
            body['load-address'] = load_address
        if load_parameter:
            body['load-parameter'] = load_parameter
        if force:
            body['force'] = force
        if not clear_indicator:
            body['clear-indicator'] = clear_indicator
        if store_status_indicator:
            body['store-status-indicator'] = store_status_indicator
        result = self.manager.session.post(
            self.uri + '/operations/load', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["operating"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def load_from_ftp(
            self, host, username, password, load_file, protocol='ftp',
            wait_for_completion=True, operation_timeout=None,
            status_timeout=None, allow_status_exceptions=False):
        """
        Load (boot) this LPAR from an FTP server, using the HMC operation
        "Load Logical Partition from FTP".

        This operation is not permitted for an LPAR whose 'activation-mode'
        property is "zaware" or "ssc".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "operating", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        HMC/SE version requirements:

        * SE version >= 2.16.0

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "Load from Removable Media or Server" task.

        Parameters:

          host (string): Host name or IP address of the FTP server.

          username (string): User name for the account on the FTP server.

          password (string): Password that is associated with the user name on
            the FTP server.

          load_file (string): Path name of the file to be read from the FTP
            server and loaded into the LPAR.

          protocol (string): Network protocol for transferring files. Must be
            one of:

              * "ftp" - File Transfer Protocol
              * "ftps" - FTP Secure
              * "sftp" - SSH File Transfer Protocol

            Default: "ftp"

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "operating" (or in addition "exceptions", if
              `allow_status_exceptions` was set.

            * If `False`, this method will return immediately once the HMC has
              accepted the request to perform the operation.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the operation. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached the desired status, after the HMC operation has completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

          allow_status_exceptions (bool):
            Boolean controlling whether LPAR status "exceptions" is considered
            an additional acceptable end status when `wait_for_completion` is
            set.

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired LPAR status.
        """
        body = {
            'host-name': host,
            'user-name': username,
            'password': password,
            'file-path': load_file,
            'protocol': protocol,
        }
        result = self.manager.session.post(
            self.uri + '/operations/load-from-ftp', body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["operating"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def stop(self, wait_for_completion=True, operation_timeout=None,
             status_timeout=None, allow_status_exceptions=False):
        """
        Stop this LPAR, using the HMC operation "Stop Logical
        Partition". The stop operation stops the processors from
        processing instructions.

        This operation is not permitted for an LPAR whose 'activation-mode'
        property is "zaware" or "ssc".

        In order to succeed, the 'status' property of the LPAR must have one of
        the following values:

        * "not-operating"
        * "operating"
        * "exceptions"

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "Stop" task.

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

          status_timeout (:term:`number`):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

          allow_status_exceptions (bool):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

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
        warn_deprecated_parameter(
            Lpar, Lpar.stop, 'status_timeout', status_timeout, None)
        warn_deprecated_parameter(
            Lpar, Lpar.stop, 'allow_status_exceptions',
            allow_status_exceptions, False)
        body = None
        result = self.manager.session.post(
            self.uri + '/operations/stop', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def start(self, wait_for_completion=True, operation_timeout=None,
              status_timeout=None, allow_status_exceptions=False):
        """
        Start this LPAR, using the HMC operation "Start Logical
        Partition". The start operation starts the processors to process
        instructions.

        This operation is not permitted for an LPAR whose 'activation-mode'
        property is "zaware" or "ssc".

        In order to succeed, the 'status' property of the LPAR must have one of
        the following values:

        * "not-operating"
        * "operating"
        * "exceptions"

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "Start" task.

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

          status_timeout (:term:`number`):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

          allow_status_exceptions (bool):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

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
        warn_deprecated_parameter(
            Lpar, Lpar.start, 'status_timeout', status_timeout, None)
        warn_deprecated_parameter(
            Lpar, Lpar.start, 'allow_status_exceptions',
            allow_status_exceptions, False)
        body = None
        result = self.manager.session.post(
            self.uri + '/operations/start', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def reset_clear(self, force=False, wait_for_completion=True,
                    operation_timeout=None, status_timeout=None,
                    allow_status_exceptions=False, os_ipl_token=None):
        """
        Reset this LPAR and clears its memory.

        This includes clearing its pending interruptions, resetting its channel
        subsystem and resetting its processors, and clearing its memory, using
        the HMC operation "Reset Clear".

        In order to succeed, the 'status' property of the LPAR must have one of
        the following values:

        * "not-operating"
        * "operating" - this requires setting the "force" flag
        * "exceptions" - this requires setting the "force" flag

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "Reset Clear" task.

        Parameters:

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status. The default is `False`.

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

          status_timeout (:term:`number`):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

          allow_status_exceptions (bool):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

          os_ipl_token (:term:`string`):
            Applicable only to z/OS, this parameter requests that this
            operation only be performed if the provided value matches the
            current value of the 'os-ipl-token' property of the LPAR.

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
        warn_deprecated_parameter(
            Lpar, Lpar.reset_clear, 'status_timeout', status_timeout, None)
        warn_deprecated_parameter(
            Lpar, Lpar.reset_clear, 'allow_status_exceptions',
            allow_status_exceptions, False)
        body = {}
        if force:
            body['force'] = force
        if os_ipl_token:
            body['os-ipl-token'] = os_ipl_token
        result = self.manager.session.post(
            self.uri + '/operations/reset-clear', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def reset_normal(self, force=False, wait_for_completion=True,
                     operation_timeout=None, status_timeout=None,
                     allow_status_exceptions=False, os_ipl_token=None):
        """
        Reset this LPAR without clearing its memory.

        This includes clearing its pending interruptions, resetting its channel
        subsystem and resetting its processors, using the HMC operation
        "Reset Normal".

        In order to succeed, the 'status' property of the LPAR must have one of
        the following values:

        * "not-operating"
        * "operating" - this requires setting the "force" flag
        * "exceptions" - this requires setting the "force" flag

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "Reset Clear" task.

        Parameters:

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status. The default is `False`.

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

          status_timeout (:term:`number`):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

          allow_status_exceptions (bool):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

          os_ipl_token (:term:`string`):
            Applicable only to z/OS, this parameter requests that this
            operation only be performed if the provided value matches the
            current value of the 'os-ipl-token' property of the LPAR.

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
        warn_deprecated_parameter(
            Lpar, Lpar.reset_normal, 'status_timeout', status_timeout, None)
        warn_deprecated_parameter(
            Lpar, Lpar.reset_normal, 'allow_status_exceptions',
            allow_status_exceptions, False)
        body = {}
        if force:
            body['force'] = force
        if os_ipl_token:
            body['os-ipl-token'] = os_ipl_token
        result = self.manager.session.post(
            self.uri + '/operations/reset-normal', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def open_os_message_channel(self, include_refresh_messages=True):
        """
        Open a JMS message channel to this LPAR's operating system, returning
        the string "topic" representing the message channel.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Operating System Messages" task at least
          in view-only mode.

        Parameters:

          include_refresh_messages (bool):
            Boolean controlling whether refresh operating systems messages
            should be sent, as follows:

            * If `True`, refresh messages will be recieved when the user
              connects to the topic. The default.

            * If `False`, refresh messages will not be recieved when the user
              connects to the topic.

        Returns:

          :term:`string`:

            Returns a string representing the os-message-notification JMS
            topic. The user can connect to this topic to start the flow of
            operating system messages.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'include-refresh-messages': include_refresh_messages}
        result = self.manager.session.post(
            self.uri + '/operations/open-os-message-channel',
            resource=self, body=body)
        return result['topic-name']

    @logged_api_call
    def send_os_command(self, os_command_text, is_priority=False):
        """
        Send a command to the operating system running in this LPAR.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Operating System Messages" task in
          modification mode.

        Parameters:

          os_command_text (string): The text of the operating system command.

          is_priority (bool):
            Boolean controlling whether this is a priority operating system
            command, as follows:

            * If `True`, this message is treated as a priority operating
              system command.

            * If `False`, this message is not treated as a priority
              operating system command. The default.

        Returns:

          None

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'is-priority': is_priority,
                'operating-system-command-text': os_command_text}
        self.manager.session.post(
            self.uri + '/operations/send-os-cmd', resource=self, body=body)

    @logged_api_call
    def list_os_messages(
            self, begin=None, end=None, is_held=None, is_priority=None,
            max_messages=0):
        """
        List all currently available operating system messages for this
        LPAR.

        Only a certain amount of OS message data from each LPAR is
        preserved by the HMC for retrieval by this operation. If the OS
        produces more than that amount, the oldest non-held, non-priority
        OS messages are no longer available. A gap in the sequence numbers
        indicates a loss of messages. A loss may be due to that space
        limitation, or it may be due to the deletion of messages by a console
        user or the OS.

        HMC/SE version requirements:

        * SE version >= 2.14.0

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Task permission to the "Operating System Messages" task (optionally
          in view-only mode).

        Parameters:

          begin (integer): A message sequence number to limit returned
            messages. OS messages with a sequence number less than this are
            omitted from the results. If `None`, no such filtering is
            performed.

          end (integer): A message sequence number to limit returned
            messages. OS messages with a sequence number greater than this are
            omitted from the results. If `None`, no such filtering is
            performed.

          is_held(bool): Limit the returned messages to only held (if `True`)
            or only non-held (if `False`) messages. If `None`, no such filtering
            is performed.

          is_priority(bool): Limit the returned messages to only priority (if
            `True`) or non-priority (if `False`) messages. If `None`, no such
            filtering is performed.

          max_messages(int): Limits the returned messages to the specified
            maximum number, starting from the begin of the sequence numbers
            in the result that would otherwise be returned.
            If 0, no such filtering is performed.

        Returns:

          list of dict: List of OS messages, where each OS message is a dict
          with the items defined for the "os-message-info" data structure
          in the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms = []
        if begin is not None:
            query_parms.append(f'begin-sequence-number={begin}')
        if end is not None:
            query_parms.append(f'end-sequence-number={end}')
        if is_held is not None:
            query_parms.append(f'is-held={str(is_held).lower()}')
        if is_priority is not None:
            query_parms.append(
                f'is-priority={str(is_priority).lower()}')
        if max_messages > 0:
            query_parms.append(f'max-messages={max_messages}')
        query_str = make_query_str(query_parms)
        result = self.manager.session.get(
            f'{self.uri}/operations/list-os-messages{query_str}',
            resource=self)
        return result

    @logged_api_call
    def psw_restart(self, wait_for_completion=True, operation_timeout=None,
                    status_timeout=None, allow_status_exceptions=False):
        """
        Restart this LPAR, using the HMC operation "PSW Restart".

        In order to succeed, the 'status' property of the LPAR must have one of
        the following values:

        * "not-operating"
        * "operating"
        * "exceptions"

        HMC/SE version requirements: None

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Before HMC API version 3.6 in an update to HMC 2.15.0: Object-access
          permission to the CPC of this LPAR.
        * Task permission for the "PSW Restart" task.

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

          status_timeout (:term:`number`):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

          allow_status_exceptions (bool):
            **Deprecated:** This property was used for handling deferred status
            behavior, which is not actually needed. Setting it to a non-default
            value will cause a :exc:`~py:exceptions.DeprecationWarning` to be
            issued.

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
        warn_deprecated_parameter(
            Lpar, Lpar.psw_restart, 'status_timeout', status_timeout, None)
        warn_deprecated_parameter(
            Lpar, Lpar.psw_restart, 'allow_status_exceptions',
            allow_status_exceptions, False)
        body = None
        result = self.manager.session.post(
            self.uri + '/operations/psw-restart', resource=self, body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def wait_for_status(self, status, status_timeout=None):
        """
        Wait until the status of this LPAR has a desired value.

        HMC/SE version requirements: None

        Parameters:

          status (:term:`string` or iterable of :term:`string`):
            Desired LPAR status or set of status values to reach; one or more
            of the following values:

            * ``"not-activated"`` - The LPAR is not active.
            * ``"not-operating"`` - The LPAR is active but no operating system
              is running in the LPAR.
            * ``"operating"`` - The LPAR is active and an operating system is
              running in the LPAR.
            * ``"exceptions"`` - The LPAR or its CPC has one or more unusual
              conditions.

            Note that the description of LPAR status values in the
            :term:`HMC API` book (as of its version 2.13.1) is partly
            confusing.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached one of the desired status values. The special value 0 means
            that no timeout is set.
            `None` means that the default status timeout will be used.
            If the timeout expires , a :exc:`~zhmcclient.StatusTimeout` is
            raised.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired LPAR status.
        """
        if status_timeout is None:
            status_timeout = \
                self.manager.session.retry_timeout_config.status_timeout
        if status_timeout > 0:
            end_time = time.time() + status_timeout
        if isinstance(status, (list, tuple)):
            statuses = status
        else:
            statuses = [status]
        HMC_LOGGER.debug("Waiting for LPAR %r to have status: %s "
                         "(timeout: %s sec)",
                         self.name, status, status_timeout)
        while True:

            # Fastest way to get actual status value:
            lpars = self.manager.cpc.lpars.list(
                filter_args={'name': self.name})
            assert len(lpars) == 1
            this_lpar = lpars[0]
            actual_status = this_lpar.get_property('status')

            if actual_status in statuses:
                return

            # pylint: disable=possibly-used-before-assignment
            if status_timeout > 0 and time.time() > end_time:
                raise StatusTimeout(
                    f"Waiting for LPAR {self.name} to reach status(es) "
                    f"'{statuses}' timed out after {status_timeout} s - "
                    f"current status is '{actual_status}'",
                    actual_status, statuses, status_timeout)

            time.sleep(1)  # Avoid hot spin loop

    @logged_api_call
    def assign_certificate(self, certificate):
        """
        Assigns a :term:`Certificate` to this LPAR.

        HMC/SE version requirements:

        * :ref`API feature` "secure-boot-with-certificates"

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Object-access permission to the specified certificate.
        * Task permission to the "Assign Secure Boot Certificates" task.

        Parameters:

          certificate (:class:`~zhmcclient.Certificate`):
            Certificate to be assigned. The certificate must not currently
            be assigned to this LPAR.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'certificate-uri': certificate.uri}
        self.manager.session.post(
            self.uri + '/operations/assign-certificate', resource=self,
            body=body)

    @logged_api_call
    def unassign_certificate(self, certificate):
        """
        Unassign a :term:`Certificate` from this LPAR.

        HMC/SE version requirements:

        * :ref`API feature` "secure-boot-with-certificates"

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Object-access permission to the specified certificate.
        * Task permission to the "Assign Secure Boot Certificates" task.

        Parameters:

          certificate (:class:`~zhmcclient.Certificate`):
            Certificate to be unassigned. The certificate must currently be
            assigned to this LPAR.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'certificate-uri': certificate.uri}
        self.manager.session.post(
            self.uri + '/operations/unassign-certificate', resource=self,
            body=body)

    @logged_api_call
    def get_sustainability_data(
            self, range="last-week", resolution="one-hour",
            custom_range_start=None, custom_range_end=None):
        # pylint: disable=redefined-builtin
        """
        Get energy management related metrics for the LPAR on a specific
        historical time range. The metrics are returned as multiple data points
        covering the requested time range with the requested resolution.
        This method performs the "Get LPAR Historical Sustainability Data"
        HMC operation.

        HMC/SE version requirements:

        * :ref`API feature` "environmental-metrics"

        Authorization requirements:

        * Object-access permission to this LPAR
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
          of the "Get LPAR Historical Sustainability Data" HMC operation.
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
