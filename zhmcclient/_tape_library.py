# Copyright 2026 IBM Corp. All Rights Reserved.
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
Starting with SE version 2.15.0, tape library management capabilities have been
introduced to support discovery and management of tape storage devices attached
to CPCs in DPM mode.

Tape libraries represent physical tape storage systems that can be discovered
through FCP adapters and managed via the HMC. The tape library feature enables
automated discovery of tape devices and facilitates communication with storage
administrators for SAN zoning configuration.

The top level resource objects are :term:`tape libraries <tape library>`.
Tape libraries are defined globally at the HMC level and are associated with a
CPC. In the zhmcclient, the :class:`~zhmcclient.TapeLibrary` objects are
accessible via the :attr:`~zhmcclient.Console.tape_library` property.

Tape libraries can only be managed on CPCs that support the tape library
management feature (SE version >= 2.15.0).
"""


import copy


from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_TAPE_LIBRARY


__all__ = ["TapeLibraryManager", "TapeLibrary"]


class TapeLibraryManager(BaseManager):
    """
     Manager providing access to the
    :term:`tape libraries <tape libraries>` of the HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.Console.tape_library` of a
      :class:`~zhmcclient.Console` object.

    HMC/SE version requirements:

    * SE version >= 2.15.0
    """

    def __init__(self, console):
        # This function should not go into the docs.
        # Parameters:
        #   console (:class:`~zhmcclient.Console`):
        #     CPC or HMC defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            "cpc-uri",
            "name",
            "state",
        ]

        super().__init__(
            resource_class=TapeLibrary,
            class_name=RC_TAPE_LIBRARY,
            session=console.manager.session,
            parent=console,
            base_uri="/api/tape-libraries",
            oid_prop="object-id",
            uri_prop="object-uri",
            name_prop="name",
            query_props=query_props,
        )
        self._console = console
        self._cpc = None

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`: The Console object representing the HMC.
        """
        return self._console

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: The :term:`CPC` to which this tape library
        is associated.

        The returned :class:`~zhmcclient.Cpc` has only a minimal set of
        properties populated.
        """
        # We do here some lazy loading.
        if not self._cpc:
            # Get the first tape library to extract its CPC URI
            cpc_mgr = self.console.manager.client.cpcs
            # List all CPCs and get the first one
            cpc_list = cpc_mgr.list()
            if cpc_list:
                self._cpc = cpc_list[0]
        return self._cpc

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the tape libraries defined in the HMC.

        Tape libraries for which the authenticated user does not have
        object-access permission are not included.

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

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to any tape libraries to be included in the
        result.

        Parameters:

        full_properties (bool):
            Controls that the full set of resource properties for each returned
            tape library is being retrieved, vs. only the following short
            set: "object-uri", "cpc-uri", "name", and "state".

        filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

        Returns:

        : A list of :class:`~zhmcclient.TapeLibrary` objects.

        Raises:

        :exc:`~zhmcclient.HTTPError`
        :exc:`~zhmcclient.ParseError`
        :exc:`~zhmcclient.AuthError`
        :exc:`~zhmcclient.ConnectionError`
        :exc:`~zhmcclient.FilterConversionError`
        """

        result_prop = "tape-libraries"
        list_uri = self._base_uri
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None
        )

    @logged_api_call
    def request_zoning(
        self, email_to_addresses=None, email_cc_addresses=None
    ):
        """
        Request tape library zoning configuration by sending email notifications
        to storage administrators.

        This operation sends emails to storage administrators requesting them to
        configure SAN zoning for tape library access. The CPC must have at least
        one FCP adapter available for this operation to succeed.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to the CPC.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

        email_to_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrators to be notified.
            If `None` or empty, no email will be sent.

        email_cc_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrators to be copied
            on the notification email.
            If `None` or empty, nobody will be copied on the email.

        Returns:

        dict: A dictionary with the operation results.

        Raises:

        :exc:`~zhmcclient.HTTPError`: HTTP status 409, reason 487 if no FCP
            adapters are available on the CPC.
        :exc:`~zhmcclient.ParseError`
        :exc:`~zhmcclient.AuthError`
        :exc:`~zhmcclient.ConnectionError`
        """

        body = {}
        cpc_uri_temp = self.cpc
        body["cpc-uri"] = cpc_uri_temp.uri
        if email_to_addresses:
            body["email-to-addresses"] = email_to_addresses
            if email_cc_addresses:
                body["email-cc-addresses"] = email_cc_addresses

        result = self.session.post(
            self._base_uri + "/operations/request-tape-library-zoning",
            body=body
        )
        return result

    @logged_api_call
    def discover(
        self, force_restart=False, wait_for_completion=True,
        operation_timeout=None
    ):
        """
        Discover tape libraries connected to the CPC.

        This operation initiates discovery of tape libraries attached to the CPC
        through FCP adapters. The CPC must have a
        management-world-wide-port-name configured
        for this operation to succeed.

        The HMC performs the discovery in an asynchronous job. This method
        supports waiting for completion of the job, or returning immediately
        after the HMC has started the asynchronous job.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to the CPC.
        * Task permission to the "Configure Storage - System Programmer" task
        or to the "Configure Storage - Storage Administrator" task.

        Parameters:

        force_restart (bool):
            Indicates if there is an in-progress discovery operation for the
            CPC, it should be terminated and started again.
            If `False` or there is no in-progress discovery operation,
            a new one is started.

        wait_for_completion (bool):
            Boolean controlling whether this method should wait for completion
            of the asynchronous job performing the discovery.

        operation_timeout (:term:`number`):
            Timeout in seconds, for waiting for completion of the asynchronous
            job performing the discovery. The special value 0 means that no
            timeout is set. `None` means that the default async operation
            timeout of the session is used. If the timeout expires when
            `wait_for_completion=True`, a
            :exc:`~zhmcclient.OperationTimeout` is raised.

        Returns:

        `None` or :class:`~zhmcclient.Job`:

            If `wait_for_completion` is `True`, returns nothing.

            If `wait_for_completion` is `False`, returns a
            :class:`~zhmcclient.Job` object representing the asynchronously
            executing job on the HMC.
            This job does not support cancellation.

        Raises:

        :exc:`~zhmcclient.HTTPError`: HTTP status 409, reason 501 if the CPC
            does not have a management-world-wide-port-name configured.
        :exc:`~zhmcclient.ParseError`
        :exc:`~zhmcclient.AuthError`
        :exc:`~zhmcclient.ConnectionError`
        :exc:`~zhmcclient.OperationTimeout`: The timeout expired while
            waiting for completion of the operation.
        """

        body = {}
        body["force-restart"] = force_restart
        cpc_uri_temp = self.cpc
        body["cpc-uri"] = cpc_uri_temp.uri
        result = self.session.post(
            self._base_uri + "/operations/discover-tape-libraries",
            resource=self,
            body=body,
            wait_for_completion=wait_for_completion,
            operation_timeout=operation_timeout,
        )
        return result


class TapeLibrary(BaseResource):
    """
    Representation of a :term:`tape library`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.TapeLibraryManager`).

    HMC/SE version requirements:

    * SE version >= 2.15.0
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.StorageGroupTemplateManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, TapeLibraryManager), (
            "TapeLibrary init: Expected manager type "
            f"{TapeLibraryManager}, got {type(manager)}"
        )
        super().__init__(manager, uri, name, properties)
        # The manager objects for child resources (with lazy initialization):
        self._tape_library = None
        self._cpc = None

    @logged_api_call
    def undefine(self):
        """
        Undefine (remove) this tape library resource from the HMC.

        This operation removes the tape library resource from the HMC but does
        not affect the physical tape library device.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape library.
        * Task permissions are: "Configure Storage – System Programmer" or
         "Configure Storage – Storage Administrator"

        Raises:

        :exc:`~zhmcclient.HTTPError`
        :exc:`~zhmcclient.ParseError`
        :exc:`~zhmcclient.AuthError`
        :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(uri=self.uri + "/operations/undefine",
                                  resource=self)
        # pylint: disable=protected-access
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None)
        )
        self.cease_existence_local()

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this tape library.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape library.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

        properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the writeable properties defined for
            the tape library resource in the :term:`HMC API` book.

        Raises:

        :exc:`~zhmcclient.HTTPError`
        :exc:`~zhmcclient.ParseError`
        :exc:`~zhmcclient.AuthError`
        :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.post(self.uri,
                                           resource=self, body=properties)
        # pylint: disable=protected-access
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            # pylint: disable=protected-access
            self.manager._name_uri_cache.delete(self.name)
        self.update_properties_local(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)
        return result
