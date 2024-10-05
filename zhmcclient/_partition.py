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
A :term:`Partition` is a subset of the hardware resources of a :term:`CPC`
in DPM mode, virtualized as a separate computer.

Partitions can be created and deleted dynamically, and their resources such
as CPU, memory or I/O devices can be configured dynamically.
You can create as many partition definitions as you want, but only a specific
number of partitions can be active at any given time.

TODO: How can a user find out what the maximum is, before it is reached?

Partition resources are contained in CPC resources.

Partition resources only exist in CPCs that are in DPM mode. CPCs in classic
mode (or ensemble mode) have :term:`LPAR` resources, instead.
"""


import time
import copy
from requests.utils import quote

from ._manager import BaseManager
from ._resource import BaseResource
from ._exceptions import StatusTimeout, PartitionLinkError
from ._nic import NicManager
from ._hba import HbaManager
from ._virtual_function import VirtualFunctionManager
from ._logging import logged_api_call
from ._utils import RC_PARTITION, make_query_str, datetime_from_timestamp, \
    timestamp_from_datetime

__all__ = ['PartitionManager', 'Partition']


class PartitionManager(BaseManager):
    """
    Manager providing access to the :term:`Partitions <Partition>` in a
    particular :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Cpc` object (in DPM mode):

    * :attr:`~zhmcclient.Cpc.partitions`

    HMC/SE version requirements:

    * SE version >= 2.13.1
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
            'status',
        ]

        super().__init__(
            resource_class=Partition,
            class_name=RC_PARTITION,
            session=cpc.manager.session,
            parent=cpc,
            base_uri='/api/partitions',
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
    # pylint: disable=arguments-differ
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the Partitions in this CPC.

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

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this CPC.
        * Object-access permission to any Partition to be included in the
          result.

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

          additional_properties (list of string):
            List of property names that are to be returned in addition to the
            default properties.

            This parameter requires HMC 2.16.0 or higher.

        Returns:

          : A list of :class:`~zhmcclient.Partition` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'partitions'
        list_uri = f'{self.cpc.uri}/partitions'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args,
            additional_properties)

    @logged_api_call(blanked_properties=['boot-ftp-password', 'ssc-master-pw'],
                     properties_pos=1)
    def create(self, properties):
        """
        Create and configure a Partition in this CPC.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "New Partition" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Partition' in the :term:`HMC API` book.

        Returns:

          Partition:
            The resource object for the new Partition.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.cpc.uri + '/partitions',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        part = Partition(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return part


class Partition(BaseResource):
    """
    Representation of a :term:`Partition`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.PartitionManager`).

    HMC/SE version requirements:

    * SE version >= 2.13.1
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.PartitionManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, PartitionManager), (
            f"Partition init: Expected manager type {PartitionManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)
        # The manager objects for child resources (with lazy initialization):
        self._nics = None
        self._hbas = None
        self._virtual_functions = None

    @property
    def nics(self):
        """
        :class:`~zhmcclient.NicManager`: Access to the :term:`NICs <NIC>` in
        this Partition.
        """
        # We do here some lazy loading.
        if not self._nics:
            self._nics = NicManager(self)
        return self._nics

    @property
    def hbas(self):
        """
        :class:`~zhmcclient.HbaManager`: Access to the :term:`HBAs <HBA>` in
        this Partition.

        On systems with the "dpm-storage-management"
        :ref:`firmware feature <firmware features>` (i.e. z14), the CPC will
        not have any HBA objects anymore (they are now Virtual Storage Resource
        objects), but this property still provides a manager object for
        consistency.
        """
        # We do here some lazy loading.
        if not self._hbas:
            self._hbas = HbaManager(self)
        return self._hbas

    @property
    def virtual_functions(self):
        """
        :class:`~zhmcclient.VirtualFunctionManager`: Access to the
        :term:`Virtual Functions <Virtual Function>` in this Partition.
        """
        # We do here some lazy loading.
        if not self._virtual_functions:
            self._virtual_functions = VirtualFunctionManager(self)
        return self._virtual_functions

    @logged_api_call
    def feature_enabled(self, feature_name):
        """
        Indicates whether the specified
        :ref:`firmware feature <firmware features>` is enabled for the CPC of
        this partition.

        The specified firmware feature must be available for the CPC.

        For a list of available firmware features, see section
        "Firmware Features" in the :term:`HMC API` book, or use the
        :meth:`feature_info` method.

        HMC/SE version requirements:

        * HMC version >= 2.14.0 with HMC API version >= 2.23

        Authorization requirements:

        * Object-access permission to this partition.

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
                f"{self.manager.cpc.name}")
        return feature['state']  # pylint: disable=undefined-loop-variable

    @logged_api_call
    def feature_info(self):
        """
        Returns information about the :ref:`firmware features` available for
        the CPC of this partition.

        HMC/SE version requirements:

        * HMC version >= 2.14.0 with HMC API version >= 2.23

        Authorization requirements:

        * Object-access permission to this partition.

        Returns:

          :term:`iterable`:
            An iterable where each item represents one firmware feature that is
            available for the CPC of this partition.

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
    def start(self, wait_for_completion=True, operation_timeout=None,
              status_timeout=None):
        """
        Start (activate) this Partition, using the HMC operation "Start
        Partition".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the partition
        status has reached the desired value (it still may show status
        "paused"). If `wait_for_completion=True`, this method repeatedly checks
        the status of the partition after the HMC operation has completed, and
        waits until the status is in one of the desired states "active" or
        "degraded".

        TODO: Describe what happens if the maximum number of active partitions
        is exceeded.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Start Partition" task.

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
            Timeout in seconds, for waiting that the status of the partition
            has reached the desired status, after the HMC operation has
            completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

        Returns:

          :class:`py:dict` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns an empty
            :class:`py:dict` object.

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired partition status.
        """
        result = self.manager.session.post(
            self.uri + '/operations/start', resource=self,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["active", "degraded"]
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def stop(self, wait_for_completion=True, operation_timeout=None,
             status_timeout=None):
        """
        Stop (deactivate) this Partition, using the HMC operation "Stop
        Partition".

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Stop Partition" task.

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
            Timeout in seconds, for waiting that the status of the partition
            has reached the desired status, after the HMC operation has
            completed.
            The special value 0 means that no timeout is set. `None` means that
            the default status timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

        Returns:

          :class:`py:dict` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns an empty
            :class:`py:dict` object.

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
          :exc:`~zhmcclient.StatusTimeout`: The timeout expired while
            waiting for the desired partition status.
        """
        result = self.manager.session.post(
            self.uri + '/operations/stop', resource=self,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["stopped"]
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def delete(self):
        """
        Delete this Partition.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Delete Partition" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.delete(self.uri, resource=self)
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))
        self.cease_existence_local()

    @logged_api_call(blanked_properties=['boot-ftp-password', 'ssc-master-pw'],
                     properties_pos=1)
    def update_properties(self, properties):
        """
        Update writeable properties of this Partition.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Partition Details" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section 'Partition object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, resource=self, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)

    @logged_api_call
    def dump_partition(self, parameters, wait_for_completion=True,
                       operation_timeout=None):
        """
        Dump this Partition, by loading a standalone dump program from a SCSI
        device and starting its execution, using the HMC operation
        'Dump Partition'.

        HMC/SE version requirements:

        * SE version >= 2.13.1 without
          :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Dump Partition" task.

        Parameters:

          parameters (dict): Input parameters for the operation.
            Allowable input parameters are defined in section
            'Request body contents' in section 'Dump Partition' in the
            :term:`HMC API` book.

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

          :class:`py:dict` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns an empty
            :class:`py:dict` object.

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
            self.uri + '/operations/scsi-dump', resource=self,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout,
            body=parameters)
        return result

    @logged_api_call
    def start_dump_program(self, parameters, wait_for_completion=True,
                           operation_timeout=None):
        """
        Dump this Partition, by loading a standalone dump program from a storage
        volume and starting its execution, using the HMC operation
        'Start Dump Program'.

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Dump Partition" task.

        Parameters:

          parameters (dict): Input parameters for the operation.
            Allowable input parameters are defined in section
            'Request body contents' in section 'Start Dump Program' in the
            :term:`HMC API` book.

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

          :class:`py:dict` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns an empty
            :class:`py:dict` object.

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
            self.uri + '/operations/start-dump-program', resource=self,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout,
            body=parameters)
        return result

    @logged_api_call
    def psw_restart(self, wait_for_completion=True, operation_timeout=None):
        """
        Initiates a PSW restart for this Partition, using the HMC operation
        'Perform PSW Restart'.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "PSW Restart" task.

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

          :class:`py:dict` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns an empty
            :class:`py:dict` object.

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
            self.uri + '/operations/psw-restart', resource=self,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        return result

    @logged_api_call
    def mount_iso_image(self, image, image_name, ins_file_name):
        """
        Upload an ISO image and associate it to this Partition
        using the HMC operation 'Mount ISO Image'.

        When the partition already has an ISO image associated,
        the newly uploaded image replaces the current one.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Partition Details" task.

        Parameters:

          image (:term:`byte string` or file-like object):
            The content of the ISO image.

            Images larger than 2GB cannot be specified as a Byte string; they
            must be specified as a file-like object.

            File-like objects must have opened the file in binary mode.

          image_name (:term:`string`): The displayable name of the image.

            This value must be a valid Linux file name without directories,
            must not contain blanks, and must end with '.iso' in lower case.

            This value will be shown in the 'boot-iso-image-name' property of
            this partition.

          ins_file_name (:term:`string`): The path name of the INS file within
            the file system of the ISO image.

            This value will be shown in the 'boot-iso-ins-file' property of
            this partition.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        query_parms_str = (
            f"?image-name={quote(image_name, safe='')}"
            f"&ins-file-name={quote(ins_file_name, safe='')}")
        self.manager.session.post(
            self.uri + '/operations/mount-iso-image' + query_parms_str,
            resource=self, body=image)

    @logged_api_call
    def unmount_iso_image(self):
        """
        Unmount the currently mounted ISO from this Partition using the HMC
        operation 'Unmount ISO Image'. This operation sets the partition's
        'boot-iso-image-name' and 'boot-iso-ins-file' properties to null.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Partition Details" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(
            self.uri + '/operations/unmount-iso-image', resource=self)

    @logged_api_call
    def open_os_message_channel(self, include_refresh_messages=True):
        """
        Open a JMS message channel to this partition's operating system,
        returning the string "topic" representing the message channel.

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
            self.uri + '/operations/open-os-message-channel', resource=self,
            body=body)
        return result['topic-name']

    @logged_api_call
    def send_os_command(self, os_command_text, is_priority=False):
        """
        Send a command to the operating system running in this partition.

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
    def list_os_messages(self, begin=None, end=None):
        """
        List all currently available operating system messages for this
        partition.

        Only a certain amount of OS message data from each partition is
        preserved by the HMC for retrieval by this operation. If the OS
        produces more than that amount, the oldest non-held, non-priority
        OS messages are no longer available. A gap in the sequence numbers
        indicates a loss of messages. A loss may be due to that space
        limitation, or it may be due to the deletion of messages by a console
        user or the OS.

        HMC/SE version requirements:

        * SE version >= 2.14.0

        Authorization requirements:

        * Object-access permission to this Partition.
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
        query_str = make_query_str(query_parms)
        result = self.manager.session.get(
            f'{self.uri}/operations/list-os-messages{query_str}',
            resource=self)
        return result

    @logged_api_call
    def create_os_websocket(self, force_takeover=False):
        """
        Create a WebSocket on the HMC, which allows accessing the console of
        the operating system running in the partition using the integrated
        ASCII console of the HMC, and return the WebSocket URI for use by a
        WebSocket client.

        This is done by performing the "Get ASCII Console WebSocket URI"
        HMC operation.

        For more details on how to use a WebSocket client to interact with the
        integrated ASCII console, see
        :ref:`Using WebSocket to access OS console`.

        HMC/SE version requirements:

        * HMC version >= 2.14.0 with HMC API version >= 2.22

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Integrated ASCII Console" task.

        Parameters:

          force_takeover (bool):
            Boolean controlling whether to break any possibly existing
            WebSockets on other HMCs to the same partition, as follows:

            * If `True`, existing WebSockets are broken up and the operation
              proceeds.

            * If `False`, existing WebSockets are not broken up and the
              operation fails.

            Note that only existing WebSockets on *other* HMCs can be taken
            over, but not existing WebSockets on the current HMC.

        Returns:

          :term:`string`:

            Returns a string representing the canonical URI of the new
            WebSocket, e.g.
            ``/api/websock/4a4f1hj12hldmm26brcpfnydk663gt6gtyxq4iwto26g2r6wq1/1``.

            Depending on which WebSocket client is used, a full URI may need to
            be constructed from the returned string by prepending the secure
            WebSocket URI scheme ``wss`` and the HMC's IP address and port, e.g.
            ``wss://9.10.11.12:6794/api/websock/4a4f1hj12hldmm26brcpfnydk663gt6gtyxq4iwto26g2r6wq1/1``.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """  # pylint: disable=line-too-long
        body = {'force-takeover': force_takeover}
        result = self.manager.session.post(
            self.uri + '/operations/get-ascii-console-websocket-uri',
            resource=self, body=body)
        return result['websocket-uri']

    @logged_api_call
    def wait_for_status(self, status, status_timeout=None):
        """
        Wait until the status of this partition has a desired value.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Parameters:

          status (:term:`string` or iterable of :term:`string`):
            Desired partition status or set of status values to reach; one or
            more of the values defined for the 'status' property in the
            data model for partitions in the :term:`HMC API` book.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the partition
            has reached one of the desired status values. The special value 0
            means that no timeout is set.
            `None` means that the default status timeout will be used.
            If the timeout expires, a :exc:`~zhmcclient.StatusTimeout` is
            raised.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.StatusTimeout`: The status timeout expired while
            waiting for the desired partition status.
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
            actual_status = self.get_properties_pulled('status')

            if actual_status in statuses:
                return

            # pylint: disable=possibly-used-before-assignment
            if status_timeout > 0 and time.time() > end_time:
                raise StatusTimeout(
                    f"Waiting for partition {self.name} to reach status(es) "
                    f"'{statuses}' timed out after {status_timeout} s - "
                    f"current status is '{actual_status}'",
                    actual_status, statuses, status_timeout)

            time.sleep(1)  # Avoid hot spin loop

    @logged_api_call
    def increase_crypto_config(self, crypto_adapters,
                               crypto_domain_configurations):
        """
        Add crypto adapters and/or crypto domains to the crypto configuration
        of this partition.

        The general principle for maintaining crypto configurations of
        partitions is as follows: Each adapter included in the crypto
        configuration of a partition has all crypto domains included in the
        crypto configuration. Each crypto domain included in the crypto
        configuration has the same access mode on all adapters included in the
        crypto configuration.

        Example: Assume that the current crypto configuration of a partition
        includes crypto adapter A and crypto domains 0 and 1. When this method
        is called to add adapter B and domain configurations for domains 1 and
        2, the resulting crypto configuration of the partition will include
        domains 0, 1, and 2 on each of the adapters A and B.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Object-access permission to the specified Crypto Adapter.
        * Task permission to the "Partition Details" task.

        Parameters:

          crypto_adapters (:term:`iterable` of :class:`~zhmcclient.Adapter`):
            Crypto adapters that should be added to the crypto configuration of
            this partition.

          crypto_domain_configurations (:term:`iterable` of `domain_config`):
            Crypto domain configurations that should be added to the crypto
            configuration of this partition.

            A crypto domain configuration (`domain_config`) is a dictionary
            with the following keys:

            * ``"domain-index"`` (:term:`integer`): Domain index of the crypto
              domain.

              The domain index is a number in the range of 0 to a maximum that
              depends on the model of the crypto adapter and the CPC model. For
              the Crypto Express 5S adapter in a z13, the maximum domain index
              is 84.

            * ``"access-mode"`` (:term:`string`): Access mode for the crypto
              domain.

              The access mode specifies the way the partition can use the
              crypto domain on the crypto adapter(s), using one of the
              following string values:

              * ``"control"`` - The partition can load cryptographic keys into
                the domain, but it may not use the domain to perform
                cryptographic operations.

              * ``"control-usage"`` - The partition can load cryptographic keys
                into the domain, and it can use the domain to perform
                cryptographic operations.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        crypto_adapter_uris = [a.uri for a in crypto_adapters]
        body = {'crypto-adapter-uris': crypto_adapter_uris,
                'crypto-domain-configurations': crypto_domain_configurations}
        self.manager.session.post(
            self.uri + '/operations/increase-crypto-configuration',
            resource=self, body=body)

    @logged_api_call
    def decrease_crypto_config(self, crypto_adapters,
                               crypto_domain_indexes):
        """
        Remove crypto adapters and/or crypto domains from the crypto
        configuration of this partition.

        For the general principle for maintaining crypto configurations of
        partitions, see :meth:`~zhmcclient.Partition.increase_crypto_config`.

        Example: Assume that the current crypto configuration of a partition
        includes crypto adapters A, B and C and crypto domains 0, 1, and 2 (on
        each of the adapters). When this method is called to remove adapter C
        and domain 2, the resulting crypto configuration of the partition will
        include domains 0 and 1 on each of the adapters A and B.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Object-access permission to the specified Crypto Adapters.
        * Task permission to the "Partition Details" task.

        Parameters:

          crypto_adapters (:term:`iterable` of :class:`~zhmcclient.Adapter`):
            Crypto adapters that should be removed from the crypto
            configuration of this partition.

          crypto_domain_indexes (:term:`iterable` of :term:`integer`):
            Domain indexes of the crypto domains that should be removed from
            the crypto configuration of this partition. For values, see
            :meth:`~zhmcclient.Partition.increase_crypto_config`.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        crypto_adapter_uris = [a.uri for a in crypto_adapters]
        body = {'crypto-adapter-uris': crypto_adapter_uris,
                'crypto-domain-indexes': crypto_domain_indexes}
        self.manager.session.post(
            self.uri + '/operations/decrease-crypto-configuration',
            resource=self, body=body)

    @logged_api_call
    def change_crypto_domain_config(self, crypto_domain_index, access_mode):
        """
        Change the access mode for a crypto domain that is currently included
        in the crypto configuration of this partition.

        The access mode will be changed for the specified crypto domain on all
        crypto adapters currently included in the crypto configuration of this
        partition.

        For the general principle for maintaining crypto configurations of
        partitions, see :meth:`~zhmcclient.Partition.increase_crypto_config`.

        HMC/SE version requirements:

        * SE version >= 2.13.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Partition Details" task.

        Parameters:

          crypto_domain_index (:term:`integer`):
            Domain index of the crypto domain to be changed. For values, see
            :meth:`~zhmcclient.Partition.increase_crypto_config`.

          access_mode (:term:`string`):
            The new access mode for the crypto domain. For values, see
            :meth:`~zhmcclient.Partition.increase_crypto_config`.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'domain-index': crypto_domain_index,
                'access-mode': access_mode}
        self.manager.session.post(
            self.uri + '/operations/change-crypto-domain-configuration',
            resource=self, body=body)

    @logged_api_call
    def zeroize_crypto_domain(self, crypto_adapter, crypto_domain_index):
        """
        Zeroize a single crypto domain on a crypto adapter.

        Zeroizing a crypto domain clears the cryptographic keys and
        non-compliance mode settings in the crypto domain.

        The crypto domain must be attached to this partition in "control-usage"
        access mode.

        Supported CPC versions: z14 GA2 and above, and the corresponding
        LinuxOne systems.

        HMC/SE version requirements:

        * SE version >= 2.14.1

        Authorization requirements:

        * Object-access permission to this Partition.
        * Object-access permission to the specified Crypto Adapter.
        * Task permission to the "Zeroize Crypto Domain" task.

        Parameters:

          crypto_adapter (:class:`~zhmcclient.Adapter`):
            Crypto adapter with the crypto domain to be zeroized.

          crypto_domain_index (:term:`integer`):
            Domain index of the crypto domain to be zeroized.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'crypto-adapter-uri': crypto_adapter.uri,
            'domain-index': crypto_domain_index
        }
        self.manager.session.post(
            self.uri + '/operations/zeroize-crypto-domain', resource=self,
            body=body)

    @logged_api_call
    def attach_storage_group(self, storage_group):
        """
        Attach a :term:`storage group` to this partition.

        This will cause the :term:`storage volumes <storage volume>` of the
        storage group to be attached to the partition, instantiating any
        necessary :term:`virtual storage resource` objects.

        A storage group can be attached to a partition regardless of its
        fulfillment state. The fulfillment state of its storage volumes
        and thus of the entire storage group changes as volumes are discovered
        by DPM, and will eventually reach "complete".

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to this partition.
        * Object-access permission to the specified storage group.
        * Task permission to the "Partition Details" task.

        Parameters:

          storage_group (:class:`~zhmcclient.StorageGroup`):
            Storage group to be attached. The storage group must not currently
            be attached to this partition.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'storage-group-uri': storage_group.uri}
        self.manager.session.post(
            self.uri + '/operations/attach-storage-group', resource=self,
            body=body)

    @logged_api_call
    def detach_storage_group(self, storage_group):
        """
        Detach a :term:`storage group` from this partition.

        This will cause the :term:`storage volumes <storage volume>` of the
        storage group to be detached from the partition, removing any
        :term:`virtual storage resource` objects that had been created upon
        attachment.

        A storage group can be detached from a partition regardless of its
        fulfillment state. The fulfillment state of its storage volumes
        changes as volumes are discovered by DPM.

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to this partition.
        * Task permission to the "Partition Details" task.

        Parameters:

          storage_group (:class:`~zhmcclient.StorageGroup`):
            Storage group to be detached. The storage group must currently
            be attached to this partition.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'storage-group-uri': storage_group.uri}
        self.manager.session.post(
            self.uri + '/operations/detach-storage-group', resource=self,
            body=body)

    @logged_api_call
    def list_attached_storage_groups(self, full_properties=False):
        """
        Return the storage groups that are attached to this partition.

        HMC/SE version requirements:

        * :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to this partition.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            storage group is being retrieved, vs. only the following short set:
            "object-uri", "object-id", "class", "parent".

            TODO: Verify short list of properties.

        Returns:

          List of :class:`~zhmcclient.StorageGroup` objects representing the
          storage groups that are attached to this partition.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        sg_list = []
        sg_uris = self.get_property('storage-group-uris')
        if sg_uris:
            console = self.manager.cpc.manager.console
            for sg_uri in sg_uris:
                sg = console.storage_groups.resource_object(sg_uri)
                sg_list.append(sg)
                if full_properties:
                    sg.pull_full_properties()
        return sg_list

    def attach_network_link(
            self, partition_link, number_of_nics=1, nic_property_list=None,
            wait_for_completion=True, operation_timeout=None):
        """
        Attach a Hipersockets-type or SMC-D-type partition link to this
        partition, creating corresponding NICs for the partition.

        For Hipersockets-type partition links, the NICs for the partition are
        available as :class:`~zhmcclient.NIC` objects in the
        :attr:`~zhmcclient.Partition.nics` property. For SMC-D type partition
        links, the NICs are not externalized by the HMC as objects. Their
        properties can be found in the :class:`~zhmcclient.PartitionLink`
        object.

        This method performs the "Modify Partition Link" HMC operation with the
        ``added-connections`` parameter.

        By default, this method waits for completion of its asynchronous job.

        HMC/SE version requirements:

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to this partition.
        * Object-access permission to the partition link.
        * Task permission to the "Partition Link Details" task.

        Parameters:

          partition_link (:class:`~zhmcclient.PartitionLink`): The partition
            link that will be attached to this partition.

          number_of_nics (int): Number of NICs to be created for the partition
            as endpoints for the partition link.

          nic_property_list (list of dict): List whose items specify the
            properties for the NICs to be created. `None` is treated as an empty
            list. The list must have no more items than the number of NICs to be
            created. NICs beyond the end of the list are created with default
            properties.

            The following NIC properties may be specified in the list items:

            * ``device-number`` (string): Device number. For Hipersockets, 3
              consecutive device numbers are used, starting with the specified
              device number. For SMC-D, the specified device number is used
              as the single device number. Default: auto-generated.
            * ``fid`` (int): SMC-D only: FID. Default: auto-generated.
            * ``vlan-id`` (int): Hipersockets only: VLAN ID. None means no
              VLAN is used. Default: No VLAN is used.
            * ``mac-address`` (string): Hipersockets only: MAC address.
              Default: auto-generated.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the asynchronous job on the HMC.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job on the HMC. The special value 0 means that no timeout is set.
            `None` means that the default async operation timeout of the
            session is used. If the timeout expires when
            `wait_for_completion=True`, a :exc:`~zhmcclient.OperationTimeout`
            is raised.

        Returns:

          * If `wait_for_completion` is `True`, returns `None`.

          * If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC.
            This job does not support cancellation.

        Raises:

          :exc:`~zhmcclient.PartitionLinkError`
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.

        Examples:

          * Attach a Hipersockets-type partition link to a partition, and
            specify device number and VLAN::

                part1.attach_network_link(
                    hs_link, nic_property_list=[
                        {
                            'device-number': '1300',
                            'vlan-id': '53',
                        }
                    ])
        """
        body = {}
        bc = {
            'partition-uri': self.uri,
            'number-of-nics': number_of_nics,
        }
        if nic_property_list:
            nics = []
            for nic_props in nic_property_list:
                nic = {}
                if 'device-number' in nic_props:
                    nic['device-numbers'] = [nic_props.pop('device-number')]
                nic.update(nic_props)
                nics.append(nic)
            bc['nics'] = nics
        body['added-connections'] = [bc]

        result = self.manager.session.post(
            uri=f'{partition_link.uri}/operations/modify',
            resource=partition_link,
            body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)

        if wait_for_completion:
            for op_result in result['operation-results']:
                if op_result['operation-status'] != "attached":
                    raise PartitionLinkError(result['operation-results'])
            return None

        return result  # Job

    def detach_network_link(
            self, partition_link, wait_for_completion=True,
            operation_timeout=None):
        """
        Detach a Hipersockets-type or SMC-D-type partition link from this
        partition, deleting the corresponding NICs for the partition.

        This method performs the "Modify Partition Link" HMC operation with the
        ``removed-partition-uris`` parameter.

        By default, this method waits for completion of its asynchronous job.

        HMC/SE version requirements:

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to this partition.
        * Object-access permission to the partition link.
        * Task permission to the "Partition Link Details" task.

        Parameters:

          partition_link (:class:`~zhmcclient.PartitionLink`): The partition
            link that will be detached from this partition.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the asynchronous job on the HMC.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job on the HMC. The special value 0 means that no timeout is set.
            `None` means that the default async operation timeout of the
            session is used. If the timeout expires when
            `wait_for_completion=True`, a :exc:`~zhmcclient.OperationTimeout`
            is raised.

        Returns:

          * If `wait_for_completion` is `True`, returns `None`.

          * If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC.
            This job does not support cancellation.

        Raises:

          :exc:`~zhmcclient.PartitionLinkError`
          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        body = {
            'removed-partition-uris': [self.uri],
        }

        result = self.manager.session.post(
            uri=f'{partition_link.uri}/operations/modify',
            resource=partition_link,
            body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)

        if wait_for_completion:
            for op_result in result['operation-results']:
                if op_result['operation-status'] != "detached":
                    raise PartitionLinkError(result['operation-results'])
            return None

        return result  # Job

    def attach_ctc_link(
            self, partition_link, wait_for_completion=True,
            operation_timeout=None):
        """
        Attach a CTC-type partition link to this partition, creating
        corresponding CTC endpoints (devices) in the partition.

        The CTC endpoints are not externalized by the HMC as objects. Their
        properties (e.g. device numbers) can be found in the
        :class:`~zhmcclient.PartitionLink` object.

        This method performs the "Modify Partition Link" HMC operation with the
        ``added-partition-uris`` parameter.

        By default, this method waits for completion of its asynchronous job.

        HMC/SE version requirements:

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to this partition.
        * Object-access permission to the partition link.
        * Task permission to the "Partition Link Details" task.

        Parameters:

          partition_link (:class:`~zhmcclient.PartitionLink`): The partition
            link that will be attached to this partition.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the asynchronous job on the HMC.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job on the HMC. The special value 0 means that no timeout is set.
            `None` means that the default async operation timeout of the
            session is used. If the timeout expires when
            `wait_for_completion=True`, a :exc:`~zhmcclient.OperationTimeout`
            is raised.

        Returns:

          * If `wait_for_completion` is `True`, returns `None`.

          * If `wait_for_completion` is `False`, returns a
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

        Examples:

          * Attach a CTC-type partition link to a partition, using
            auto-generated device numbers::

                part1.attach_ctc_link(part_link)

          * For attaching a CTC-type partition link with specific device
            numbers, the :meth:`~zhmcclient.PartitionLink.update_properties`
            method can be used::

                part_link.update_properties({
                    "added-partition-uris": [part.uri],
                    "modified-paths": [
                        # Repeat for each path of the partition link:
                        {
                            "devices": [
                                # Repeat for each desired communication path
                                # between any two partitions:
                                {
                                    "endpoint-pair": [
                                        {
                                            "device-numbers": [DEVNOxx, ...],
                                            "partition-uri": part.uri
                                        },
                                        {
                                            "device-numbers": [DEVNOxx, ...],
                                            "partition-uri": other_part.uri
                                        }
                                    ]
                                },
                            ],
                            "adapter-port-uri": fc_port1.uri,
                            "connecting-adapter-port-uri": fc_port2.uri
                        }
                    ]
                })
        """
        body = {
            'added-partition-uris': [self.uri],
        }

        result = self.manager.session.post(
            uri=f'{partition_link.uri}/operations/modify',
            resource=partition_link,
            body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)

        if wait_for_completion:
            for op_result in result['operation-results']:
                if op_result['operation-status'] != "attached":
                    raise PartitionLinkError(result['operation-results'])
            return None

        return result  # Job

    def detach_ctc_link(
            self, partition_link, wait_for_completion=True,
            operation_timeout=None):
        """
        Detach a CTC-type partition link from this partition, deleting
        corresponding CTC endpoints (devices) in the partition.

        This method performs the "Modify Partition Link" HMC operation with the
        ``removed-partition-uris`` parameter.

        By default, this method waits for completion of its asynchronous job.

        HMC/SE version requirements:

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to this partition.
        * Object-access permission to the partition link.
        * Task permission to the "Partition Link Details" task.

        Parameters:

          partition_link (:class:`~zhmcclient.PartitionLink`): The partition
            link that will be detached from this partition.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the asynchronous job on the HMC.

          operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job on the HMC. The special value 0 means that no timeout is set.
            `None` means that the default async operation timeout of the
            session is used. If the timeout expires when
            `wait_for_completion=True`, a :exc:`~zhmcclient.OperationTimeout`
            is raised.

        Returns:

          * If `wait_for_completion` is `True`, returns `None`.

          * If `wait_for_completion` is `False`, returns a
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
            'removed-partition-uris': [self.uri],
        }

        result = self.manager.session.post(
            uri=f'{partition_link.uri}/operations/modify',
            resource=partition_link,
            body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)

        if wait_for_completion:
            for op_result in result['operation-results']:
                if op_result['operation-status'] != "detached":
                    raise PartitionLinkError(result['operation-results'])
            return None

        return result  # Job

    @logged_api_call
    def list_attached_partition_links(
            self, type=None, name=None, state=None, additional_properties=None):
        # pylint: disable=redefined-builtin
        """
        Return the partition links attached to this partition, optionally
        filtered by partition link type, name and status.

        This method performs the "List Partition Links" HMC operation.

        HMC/SE version requirements:

        * SE version >= 2.16.0
        * for technology-specific support, see the API features described in
          :ref:`Partition Links`

        Authorization requirements:

        * Object-access permission to this partition.
        * Object-access permission to all partition links returned (only those
          are returned).

        Parameters:

          type (:term:`string`): Filter string to limit returned partition
            links to those with the specified type. Valid values are: "smc-d",
            "hipersockets", "ctc". If `None`, no filtering for the partition
            link type takes place.

          name (:term:`string`): Filter pattern (regular expression)
            to limit returned partition links to those that have a matching
            name. If `None`, no filtering for the partition link name takes
            place.

          state (:term:`string`): Filter string to limit returned partition
            links to those with the specified state. Valid values are:
            "complete", "incomplete", "updating". If `None`, no filtering for
            the partition link state takes place.

          additional_properties (list of string): Additional properties to
            be included in the returned :class:`~zhmcclient.PartitionLink`
            objects, in addition to the minimum list of ('cpc-uri', 'state',
            'name', 'type', 'object-uri'). The properties must be specified
            with hyphens in their names (not underscores).

        Returns:

          List of :class:`~zhmcclient.PartitionLink` objects representing the
          partition links attached to this partition.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc = self.manager.cpc
        console = cpc.manager.console

        filter_args = {
            'cpc-uri': cpc.uri,
        }
        if type:
            filter_args['type'] = type
        if name:
            filter_args['name'] = name
        if state:
            filter_args['state'] = state

        # Always get additional properties that are needed lateron, to avoid
        # extra 'Get Partition Link Properties' operations for them.
        if additional_properties is None:
            additional_properties = []
        additional_props = list(additional_properties)
        if 'paths' not in additional_props:
            additional_props.append('paths')
        if 'bus-connections' not in additional_props:
            additional_props.append('bus-connections')

        pl_list = console.partition_links.list(
            filter_args=filter_args,
            additional_properties=additional_props)

        # Restrict to partition links attached to this partition
        attached_pl_list = []
        for pl in pl_list:
            add_pl = None
            pl_type = pl.get_property('type')
            if pl_type == 'ctc':
                for path_item in pl.get_property('paths'):
                    for device_item in path_item.get('devices'):
                        for endpoint in device_item.get('endpoint-pair'):
                            part_uri = endpoint.get('partition-uri')
                            if part_uri == self.uri:
                                add_pl = pl
                                break
                        if add_pl:
                            break
                    if add_pl:
                        break
            else:
                # Hipersockets or SMC-D
                for bc_item in pl.get_property('bus-connections'):
                    part_uri = bc_item.get('partition-uri')
                    if part_uri == self.uri:
                        add_pl = pl
                        break
            if add_pl:
                attached_pl_list.append(add_pl)

        return attached_pl_list

    @logged_api_call
    def assign_certificate(self, certificate):
        """
        Assigns a :term:`Certificate` to this partition.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "secure-boot-with-certificates"

        Authorization requirements:

        * Object-access permission to this partition.
        * Object-access permission to the specified certificate.
        * Task permission to the "Assign Secure Boot Certificates" task.

        Parameters:

          certificate (:class:`~zhmcclient.Certificate`):
            Certificate to be assigned. The certificate must not currently
            be assigned to this partition.

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
        Unassign a :term:`Certificate` from this partition.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "secure-boot-with-certificates"

        Authorization requirements:

        * Object-access permission to this partition.
        * Object-access permission to the specified certificate.
        * Task permission to the "Assign Secure Boot Certificates" task.

        Parameters:

          certificate (:class:`~zhmcclient.Certificate`):
            Certificate to be unassigned. The certificate must currently be
            assigned to this partition.

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

    def dump(self):
        """
        Dump this Partition resource with its properties and child resources
        (recursively) as a resource definition.

        The returned resource definition has the following format::

            {
                # Resource properties:
                "properties": {...},

                # Child resources:
                "nics": [...],
                "hbas": [...],
                "virtual_functions": [...],
            }

        Returns:

          dict: Resource definition of this resource.
        """

        # Dump the resource properties
        resource_dict = super().dump()

        # Dump the child resources
        nics = self.nics.dump()
        if nics:
            resource_dict['nics'] = nics
        if self.hbas is not None:
            # Note: z14 and later do not have HBAs
            hbas = self.hbas.dump()
            if hbas:
                resource_dict['hbas'] = hbas
        virtual_functions = self.virtual_functions.dump()
        if virtual_functions:
            resource_dict['virtual_functions'] = virtual_functions

        return resource_dict

    @logged_api_call
    def get_sustainability_data(
            self, range="last-week", resolution="one-hour",
            custom_range_start=None, custom_range_end=None):
        # pylint: disable=redefined-builtin
        """
        Get energy management related metrics for the partition on a specific
        historical time range. The metrics are returned as multiple data points
        covering the requested time range with the requested resolution.
        This method performs the "Get Partition Historical Sustainability Data"
        HMC operation.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "environmental-metrics"

        Authorization requirements:

        * Object-access permission to this partition
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
          of the "Get Partition Historical Sustainability Data" HMC operation.
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
