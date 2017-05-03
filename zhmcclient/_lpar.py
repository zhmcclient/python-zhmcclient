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

from ._manager import BaseManager
from ._resource import BaseResource
from ._exceptions import StatusTimeout
from ._logging import get_logger, logged_api_call

__all__ = ['LparManager', 'Lpar']

LOG = get_logger(__name__)


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
            session=cpc.manager.session,
            parent=cpc,
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
        query_parms, client_filters = self._divide_filter_args(filter_args)

        resources_name = 'logical-partitions'
        uri = '{}/{}{}'.format(self.cpc.uri, resources_name, query_parms)

        resource_obj_list = []
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
        if not isinstance(manager, LparManager):
            raise AssertionError("Lpar init: Expected manager type %s, "
                                 "got %s" %
                                 (LparManager, type(manager)))
        super(Lpar, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def activate(self, wait_for_completion=True,
                 operation_timeout=None, status_timeout=None):
        """
        Activate (start) this LPAR, using the HMC operation "Activate Logical
        Partition".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "not-operating" (which indicates that the LPAR is active but
        no operating system is running).

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
              becoming "not-operating".

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
            self.uri + '/operations/activate',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            self._wait_for_status("not-operating", status_timeout)
        return result

    @logged_api_call
    def deactivate(self, wait_for_completion=True,
                   operation_timeout=None, status_timeout=None):
        """
        De-activate (stop) this LPAR, using the HMC operation "Deactivate
        Logical Partition".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "not-activated".

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
              becoming "non-activated".

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
        body = {'force': True}
        result = self.manager.session.post(
            self.uri + '/operations/deactivate',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            self._wait_for_status("not-activated", status_timeout)
        return result

    @logged_api_call
    def load(self, load_address, load_parameter="", wait_for_completion=True,
             operation_timeout=None, status_timeout=None):
        """
        Load (boot) this LPAR from a load address (boot device), using the HMC
        operation "Load Logical Partition".

        This HMC operation has deferred status behavior: If the asynchronous
        job on the HMC is complete, it takes a few seconds until the LPAR
        status has reached the desired value. If `wait_for_completion=True`,
        this method repeatedly checks the status of the LPAR after the HMC
        operation has completed, and waits until the status is in the desired
        state "operating".

        Authorization requirements:

        * Object-access permission to the CPC containing this LPAR.
        * Object-access permission to this LPAR.
        * Task permission for the "Load" task.

        Parameters:

          load_address (:term:`string`): Device number of the boot device.

          load_parameter (:term:`string`): Optional load control string.

          wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the requested asynchronous HMC operation, as follows:

            * If `True`, this method will wait for completion of the
              asynchronous job performing the operation, and for the status
              becoming "operating".

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
        body = {'load-address': load_address}
        if load_parameter != "":
            body['load-parameter'] = load_parameter
        result = self.manager.session.post(
            self.uri + '/operations/load',
            body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout)
        if wait_for_completion:
            self._wait_for_status("operating", status_timeout)
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

    def _wait_for_status(self, status, status_timeout=None):
        """
        Wait until the status of this LPAR has a desired value.

        Parameters:

          status (:term:`string`):
            Desired LPAR status(es) to reach; one of the following values:
            * ``"not-activated"`` - The LPAR is not active.
            * ``"not-operating" - The LPAR is active but no operating system is
              running in the LPAR.
            * ``"operating"`` - The LPAR is active and an operating system is
              running in the LPAR.

            The fourth possible LPAR status value ``"exceptions"`` indicates
            that the LPAR or its CPC has one or more unusual conditions. This
            value should not normally be specified for this parameter. Each
            time the ``"exceptions"`` status is seen by this method, a log
            entry at the info level is written to record that, but otherwise
            it is treated like other undesired suatus values.

            Note that the description of LPAR status values in the
            :term:`HMC API` book (as of its version 2.13.1) is partly
            confusing.

          status_timeout (:term:`number`):
            Timeout in seconds, for waiting that the status of the LPAR has
            reached the desired status. The special value 0 means that no
            timeout is set.
            If the timeout expires when `wait_for_completion=True`, a
            :exc:`~zhmcclient.StatusTimeout` is raised.

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
        while True:

            # Fastest way to get actual status value:
            lpars = self.manager.cpc.lpars.list(
                filter_args={'name': self.name})
            assert len(lpars) == 1
            this_lpar = lpars[0]
            actual_status = this_lpar.get_property('status')

            if actual_status == status:
                return
            elif actual_status == "exceptions":
                LOG.info("LPAR {} in CPC {} has status 'exceptions' while "
                         "waiting for status '{}' (if no other errors follow, "
                         "this was a temporary condition)".
                         format(this_lpar.name, this_lpar.manager.cpc.name,
                                status))

            if status_timeout > 0 and time.time() > end_time:
                raise StatusTimeout(
                    "Waiting for LPAR {} to reach status '{}' timed out after "
                    "{} s - current status is '{}'".
                    format(self.name, status, status_timeout, actual_status))

            time.sleep(1)  # Avoid hot spin loop
