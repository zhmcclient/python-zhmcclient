# Copyright 2017,2021 IBM Corp. All Rights Reserved.
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

This section describes the interface for *unmanaged* CPCs using resource class
:class:`~zhmcclient.UnmanagedCpc` and the corresponding manager class
:class:`~zhmcclient.UnmanagedCpcManager`.
"""


from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_CPC

__all__ = ['UnmanagedCpcManager', 'UnmanagedCpc']


class UnmanagedCpcManager(BaseManager):
    """
    Manager providing access to the :term:`CPCs <CPC>` that have been
    discovered by the HMC this client is connected to, but are not managed by
    it. They may or may not be managed by another HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Console` object:

    * :attr:`~zhmcclient.Console.unmanaged_cpcs`

    HMC/SE version requirements:

    * HMC version >= 2.13.1
    """

    def __init__(self, console):
        # This function should not go into the docs.
        # Parameters:
        #   console (:class:`~zhmcclient.Console`):
        #      Console object for the HMC to be used.

        # Resource properties that are supported as filter query parameters
        # (for server-side filtering).
        query_props = [
            'name',
        ]

        super().__init__(
            resource_class=UnmanagedCpc,
            class_name=RC_CPC,
            session=console.manager.session,
            parent=console,
            base_uri='/api/console',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props)

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`: :term:`Console` defining the scope for
        this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the unmanaged CPCs exposed by the HMC this client is connected to.

        Because the CPCs are unmanaged, the returned
        :class:`~zhmcclient.UnmanagedCpc` objects cannot perform any operations
        and will have only the following properties:

        * ``object-uri``
        * ``name``

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

        * HMC version >= 2.13.1

        Authorization requirements: None

        Parameters:

          full_properties (bool):
            Ignored (exists for consistency with other list() methods).

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          : A list of :class:`~zhmcclient.UnmanagedCpc` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'cpcs'
        list_uri = f'{self.parent.uri}/operations/list-unmanaged-cpcs'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None)


class UnmanagedCpc(BaseResource):
    """
    Representation of an unmanaged :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.UnmanagedCpcManager`).

    HMC/SE version requirements:

    * HMC version >= 2.13.1
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.UnmanagedCpcManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, UnmanagedCpcManager), (
            f"UnmanagedCpc init: Expected manager type {UnmanagedCpcManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)
