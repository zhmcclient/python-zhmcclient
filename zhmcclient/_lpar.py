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
A :term:`LPAR` (Logical Partition) is a subset of the hardware resources of a
:term:`CPC` in classic mode (or ensemble mode), virtualized as a separate
computer.

LPARs cannot be created or deleted by the user; they can only be listed.

LPAR resources are contained in CPC resources.

LPAR resources only exist in CPCs that are in classic mode (or ensemble mode).
CPCs in DPM mode have :term:`Partition` resources, instead.
"""

from __future__ import absolute_import

import time
import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._exceptions import StatusTimeout
from ._logging import logged_api_call

__all__ = ['LparManager', 'Lpar']


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

        super(LparManager, self).__init__(
            resource_class=Lpar,
            class_name='logical-partition',
            session=cpc.manager.session,
            parent=cpc,
            base_uri='/api/logical-partitions',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props)

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
        resource_obj_list = []
        resource_obj = self._try_optimized_lookup(filter_args)
        if resource_obj:
            resource_obj_list.append(resource_obj)
            # It already has full properties
        else:
            query_parms, client_filters = self._divide_filter_args(filter_args)

            resources_name = 'logical-partitions'
            uri = '{}/{}{}'.format(self.cpc.uri, resources_name, query_parms)

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


class Lpar(BaseResource):
    """
    Representation of an :term:`LPAR`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.LparManager`).
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
        assert isinstance(manager, LparManager), \
            "Lpar init: Expected manager type %s, got %s" % \
            (LparManager, type(manager))
        super(Lpar, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this LPAR.

        Authorization requirements:

        * Object-access permission to this LPAR.
        * Task permission for the "Change Object Definition" task.
        * Object-access permission to the CPC of this LPAR.
        * For an LPAR whose activation-mode is "zaware", task permission for
          the "Firmware Details" task.

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
        self.manager.session.post(self.uri, body=properties)
        # Attempts to change the 'name' property will be rejected by the HMC,
        # so we don't need to update the name-to-URI cache.
        assert self.manager._name_prop not in properties
        self.properties.update(copy.deepcopy(properties))

    @logged_api_call
    def activate(self, wait_for_completion=True,
                 operation_timeout=None, status_timeout=None,
                 allow_status_exceptions=False, activation_profile_name=None,
                 force=False):
        """
        Activate (start) this LPAR, using the HMC operation "Activate Logical
        Partition".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "not-operating" (which indicates that the LPAR is active but
        no operating system is running), or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        Authorization requirements:

        * Object-access permission to the CPC containing this LPAR.
        * Object-access permission to this LPAR.
        * Task permission for the "Activate" task.

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "not-operating" (or in addition "exceptions", if
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
            the default async operation timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

          allow_status_exceptions (bool):
            Boolean controlling whether LPAR status "exceptions" is considered
            an additional acceptable end status when `wait_for_completion` is
            set.

          activation_profile_name (:term:`string`):
            Name of the image :class:`ActivationProfile` to use for activation.

            `None` means that the activation profile specified in the
            `next-activation-profile-name` property of the LPAR is used.

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
            self.uri + '/operations/activate',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
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
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "not-activated", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        Authorization requirements:

        * Object-access permission to the CPC containing this LPAR.
        * Object-access permission to this LPAR.
        * Task permission for the "Deactivate" task.

        Parameters:

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "non-activated" (or in addition "exceptions", if
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
            the default async operation timeout of the session is used.
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
            self.uri + '/operations/deactivate',
            body,
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
                  status_timeout=None, allow_status_exceptions=False):
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

        Authorization requirements:

        * Object-access permission to the CPC containing this LPAR.
        * Object-access permission to this LPAR.
        * Task permission for the "SCSI Load" task.

        Parameters:

          load_address (:term:`string`):
            Device number of the boot device.

          wwpn (:term:`string`):
            Worldwide port name (WWPN) of the target SCSI device to be
            used for this operation, in hexadecimal.

          lun (:term:`string`):
            Hexadecimal logical unit number (LUN) to be used for the
            SCSI Load.

          load_parameter (:term:`string`):
            Optional load control string.  If empty string or `None`,
            it is not passed to the HMC.

          disk_partition_id (:term:`integer`):
             Optional disk-partition-id (also called the boot program
             selector) to be used for the SCSI Load. If `None`, it is
             not passed to the HMC.

          operating_system_specific_load_parameters (:term:`string`):
             Optional operating system specific load parameters to be
             used for the SCSI Load.

          boot_record_logical_block_address (:term:`string`):
             Optional hexadecimal boot record logical block address to
             be used for the SCSI Load.

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status. The default value is `True`.

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
            the default async operation timeout of the session is used.
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
        if boot_record_logical_block_address:
            body['boot-record-logical-block-address'] = \
                boot_record_logical_block_address
        if force:
            body['force'] = force
        result = self.manager.session.post(
            self.uri + '/operations/scsi-load',
            body,
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

        Authorization requirements:

        * Object-access permission to the CPC containing this LPAR.
        * Object-access permission to this LPAR.
        * Task permission for the "Load" task.

        Parameters:

          load_address (:term:`string`): Device number of the boot device.
            Up to z13, this parameter is required.
            Starting with z14, this parameter is optional and defaults to the
            load address specified in the 'last-used-load-address' property of
            the Lpar.

          load_parameter (:term:`string`): Optional load control string.
            If empty string or `None`, it is not passed to the HMC.

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
            the default async operation timeout of the session is used.
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
            self.uri + '/operations/load',
            body,
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

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "operating", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        Authorization requirements:

        * Object-access permission to the CPC containing this LPAR.
        * Object-access permission to this LPAR.
        * Task permission for the "Stop" task.

        Parameters:

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
            the default async operation timeout of the session is used.
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
        result = self.manager.session.post(
            self.uri + '/operations/stop',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["operating"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def reset_clear(self, force=False, wait_for_completion=True,
                    operation_timeout=None, status_timeout=None,
                    allow_status_exceptions=False):
        """
        Initialize this LPAR by clearing its pending interruptions,
        resetting its channel subsystem, and resetting its processors,
        using the HMC operation "Reset Clear".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "operating", or if `allow_status_exceptions` was
        set additionally in the state "exceptions".

        Authorization requirements:

        * Object-access permission to the CPC containing this LPAR.
        * Object-access permission to this LPAR.
        * Task permission for the "Reset Clear" task.

        Parameters:

          force (bool):
            Boolean controlling whether this operation is permitted when the
            LPAR is in the "operating" status. The default is `False`.

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
            the default async operation timeout of the session is used.
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
            self.uri + '/operations/reset-clear',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["operating"]
            if allow_status_exceptions:
                statuses.append("exceptions")
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def open_os_message_channel(self, include_refresh_messages=True):
        """
        Open a JMS message channel to this LPAR's operating system, returning
        the string "topic" representing the message channel.

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
            self.uri + '/operations/open-os-message-channel', body)
        return result['topic-name']

    @logged_api_call
    def send_os_command(self, os_command_text, is_priority=False):
        """
        Send a command to the operating system running in this LPAR.

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
            self.uri + '/operations/send-os-cmd', body)

    @logged_api_call
    def wait_for_status(self, status, status_timeout=None):
        """
        Wait until the status of this LPAR has a desired value.

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
        while True:

            # Fastest way to get actual status value:
            lpars = self.manager.cpc.lpars.list(
                filter_args={'name': self.name})
            assert len(lpars) == 1
            this_lpar = lpars[0]
            actual_status = this_lpar.get_property('status')

            if actual_status in statuses:
                return

            if status_timeout > 0 and time.time() > end_time:
                raise StatusTimeout(
                    "Waiting for LPAR {} to reach status(es) '{}' timed out "
                    "after {} s - current status is '{}'".
                    format(self.name, statuses, status_timeout, actual_status),
                    actual_status, statuses, status_timeout)

            time.sleep(1)  # Avoid hot spin loop
