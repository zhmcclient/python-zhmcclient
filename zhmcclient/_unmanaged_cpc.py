# Copyright 2017 IBM Corp. All Rights Reserved.
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

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call

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

        super(UnmanagedCpcManager, self).__init__(
            resource_class=UnmanagedCpc,
            class_name='cpc',
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

        Authorization requirements:

        * None

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
        resource_obj_list = []
        resource_obj = self._try_optimized_lookup(filter_args)
        if resource_obj:
            resource_obj_list.append(resource_obj)
        else:
            query_parms, client_filters = self._divide_filter_args(filter_args)

            uri = self.parent.uri + '/operations/list-unmanaged-cpcs' + \
                query_parms

            result = self.session.get(uri)
            if result:
                props_list = result['cpcs']
                for props in props_list:

                    resource_obj = self.resource_class(
                        manager=self,
                        uri=props[self._uri_prop],
                        name=props.get(self._name_prop, None),
                        properties=props)

                    if self._matches_filters(resource_obj, client_filters):
                        resource_obj_list.append(resource_obj)

        self._name_uri_cache.update_from(resource_obj_list)
        return resource_obj_list


class UnmanagedCpc(BaseResource):
    """
    Representation of an unmanaged :term:`CPC`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.UnmanagedCpcManager`).
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
        assert isinstance(manager, UnmanagedCpcManager), \
            "UnmanagedCpc init: Expected manager type %s, got %s" % \
            (UnmanagedCpcManager, type(manager))
        super(UnmanagedCpc, self).__init__(manager, uri, name, properties)
