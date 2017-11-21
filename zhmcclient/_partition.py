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

from __future__ import absolute_import

import time
import copy
from requests.utils import quote

from ._manager import BaseManager
from ._resource import BaseResource
from ._exceptions import StatusTimeout
from ._nic import NicManager
from ._hba import HbaManager
from ._virtual_function import VirtualFunctionManager
from ._logging import get_logger, logged_api_call

__all__ = ['PartitionManager', 'Partition']

LOG = get_logger(__name__)


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

        super(PartitionManager, self).__init__(
            resource_class=Partition,
            class_name='partition',
            session=cpc.manager.session,
            parent=cpc,
            base_uri='/api/partitions',
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
        List the Partitions in this CPC.

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

        Returns:

          : A list of :class:`~zhmcclient.Partition` objects.

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

            resources_name = 'partitions'
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

    @logged_api_call
    def create(self, properties):
        """
        Create and configure a Partition in this CPC.

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
        assert isinstance(manager, PartitionManager), \
            "Partition init: Expected manager type %s, got %s" % \
            (PartitionManager, type(manager))
        super(Partition, self).__init__(manager, uri, name, properties)
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

        If the "dpm-storage-management" feature is enabled, this property is
        `None`.
        """
        # We do here some lazy loading.
        if not self._hbas:
            try:
                dpm_sm = self.feature_enabled('dpm-storage-management')
            except ValueError:
                dpm_sm = False
            if not dpm_sm:
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
        Indicates whether the specified feature is enabled for the CPC of this
        partition.

        The HMC must generally support features, and the specified feature must
        be available for the CPC.

        For a list of available features, see section "Features" in the
        :term:`HMC API`, or use the :meth:`feature_info` method.

        Authorization requirements:

        * Object-access permission to this partition.

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
                             self.manager.cpc.name)
        for feature in feature_list:
            if feature['name'] == feature_name:
                break
        else:
            raise ValueError("Firmware feature %s is not available on CPC %s" %
                             (feature_name, self.manager.cpc.name))
        return feature['state']

    @logged_api_call
    def feature_info(self):
        """
        Returns information about the features available for the CPC of this
        partition.

        Authorization requirements:

        * Object-access permission to this partition.

        Returns:

          :term:`iterable`:
            An iterable where each item represents one feature that is
            available for the CPC of this partition.

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
                             self.manager.cpc.name)
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

        Authorization requirements:

        * Object-access permission to this Partition.
        * Object-access permission to the CPC containing this Partition.
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
            the default async operation timeout of the session is used.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

        Returns:

          :class:`py:dict` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns an empty
            :class:`py:dict` object.

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
            waiting for the desired partition status.
        """
        result = self.manager.session.post(
            self.uri + '/operations/start',
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            statuses = ["active", "degraded"]
            self.wait_for_status(statuses, status_timeout)
        return result

    @logged_api_call
    def stop(self, wait_for_completion=True, operation_timeout=None):
        """
        Stop (deactivate) this Partition, using the HMC operation "Stop
        Partition".

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

        Returns:

          :class:`py:dict` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns an empty
            :class:`py:dict` object.

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
    def delete(self):
        """
        Delete this Partition.

        Authorization requirements:

        * Object-access permission to this Partition.
        * Task permission to the "Delete Partition" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self.uri)
        self.manager._name_uri_cache.delete(
            self.properties.get(self.manager._name_prop, None))

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this Partition.

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
        self.manager.session.post(self.uri, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self.properties.update(copy.deepcopy(properties))
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

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        result = self.manager.session.post(
            self.uri + '/operations/scsi-dump',
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout,
            body=parameters)
        return result

    @logged_api_call
    def psw_restart(self, wait_for_completion=True, operation_timeout=None):
        """
        Initiates a PSW restart for this Partition, using the HMC operation
        'Perform PSW Restart'.

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

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """
        result = self.manager.session.post(
            self.uri + '/operations/psw-restart',
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
        query_parms_str = '?image-name={}&ins-file-name={}'. \
            format(quote(image_name, safe=''), quote(ins_file_name, safe=''))
        self.manager.session.post(
            self.uri + '/operations/mount-iso-image' + query_parms_str,
            body=image)

    @logged_api_call
    def unmount_iso_image(self):
        """
        Unmount the currently mounted ISO from this Partition using the HMC
        operation 'Unmount ISO Image'. This operation sets the partition's
        'boot-iso-image-name' and 'boot-iso-ins-file' properties to null.

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
            self.uri + '/operations/unmount-iso-image')

    @logged_api_call
    def open_os_message_channel(self, include_refresh_messages=True):
        """
        Open a JMS message channel to this partition's operating system,
        returning the string "topic" representing the message channel.

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
        Send a command to the operating system running in this partition.

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
        Wait until the status of this partition has a desired value.

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

            # Fastest way to get actual status value:
            parts = self.manager.cpc.partitions.list(
                filter_args={'name': self.name})
            assert len(parts) == 1
            this_part = parts[0]
            actual_status = this_part.get_property('status')

            if actual_status in statuses:
                return

            if status_timeout > 0 and time.time() > end_time:
                raise StatusTimeout(
                    "Waiting for partition {} to reach status(es) '{}' timed "
                    "out after {} s - current status is '{}'".
                    format(self.name, statuses, status_timeout, actual_status),
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

        Authorization requirements:

        * Object-access permission to this Partition.
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
            self.uri + '/operations/increase-crypto-configuration', body)

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

        Authorization requirements:

        * Object-access permission to this Partition.
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
            self.uri + '/operations/decrease-crypto-configuration', body)

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
            self.uri + '/operations/change-crypto-domain-configuration', body)

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

        The CPC must have the "dpm-storage-management" feature enabled.

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
            self.uri + '/operations/attach-storage-group', body)

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

        The CPC must have the "dpm-storage-management" feature enabled.

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
            self.uri + '/operations/detach-storage-group', body)

    @logged_api_call
    def list_attached_storage_groups(self, full_properties=False):
        """
        Return the storage groups that are attached to this partition.

        The CPC must have the "dpm-storage-management" feature enabled.

        Authorization requirements:

        * Object-access permission to this partition.
        * Task permission to the "Partition Details" task.

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
            cpc = self.manager.cpc
            for sg_uri in sg_uris:
                sg = cpc.storage_groups.resource_object(sg_uri)
                sg_list.append(sg)
                if full_properties:
                    sg.pull_full_properties()
        return sg_list
