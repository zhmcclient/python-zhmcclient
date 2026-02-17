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
Starting with SE version 2.15.0, tape link management capabilities have been
introduced to support management of connections between tape libraries and
partitions in DPM mode.

Tape links represent logical connections between a :term:`tape library` and a
:term:`partition`. They enable partitions to access tape storage devices
through FCP adapters. Each tape link defines the relationship and access
parameters for a partition to communicate with a specific tape library.

Tape links are child resources of :term:`tape libraries <tape library>`.
In the zhmcclient, the :class:`~zhmcclient.TapeLink` objects are accessible
via the :attr:`~zhmcclient.TapeLibrary.tape_links` property of a
:class:`~zhmcclient.TapeLibrary` object.

Tape links can be listed, created, deleted, and updated. They facilitate
the attachment of tape libraries to partitions, enabling tape storage
operations within the partition environment.

Tape links can only be managed on CPCs that support the tape library
management feature (SE version >= 2.15.0).
"""


import copy
import re

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_TAPE_LINK, append_query_parms

__all__ = ['TapeLinkManager', 'TapeLink']


class TapeLinkManager(BaseManager):
    """
    Manager providing access to the :term:`tape links <tape link>` of a
    :term:`tape library`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.TapeLibrary.tape_links` of a
      :class:`~zhmcclient.TapeLibrary` object.

    HMC/SE version requirements:

    * SE version >= 2.15.0
    """

    def __init__(self, tape_library):
        # This function should not go into the docs.
        # Parameters:
        #   tape_library (:class:`~zhmcclient.TapeLibrary`):
        #     Tape library defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name',
            'partition-uri',
        ]

        super().__init__(
            resource_class=TapeLink,
            class_name=RC_TAPE_LINK,
            session=tape_library.manager.session,
            parent=tape_library,
            base_uri=f'{tape_library.uri}/tape-links',
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=query_props)
        self._tape_library = tape_library

    @property
    def tape_library(self):
        """
        :class:`~zhmcclient.TapeLibrary`: The :term:`tape library` defining
        the scope for this manager.
        """
        return self._tape_library

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the tape links defined in this tape library.

        Tape links for which the authenticated user does not have
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

        * Object-access permission to this tape library.
        * Object-access permission to any tape links to be included in the
          result.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            tape link is being retrieved, vs. only the following short
            set: "element-uri", "name", and "partition-uri".

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

        Returns:

          : A list of :class:`~zhmcclient.TapeLink` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
          :exc:`~zhmcclient.FilterConversionError`
        """
        result_prop = 'tape-links'
        list_uri = self._base_uri
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None)

    @logged_api_call
    def create(self, properties):
        """
        Create a tape link in this tape library.

        The new tape link establishes a connection between this tape library
        and a partition, enabling the partition to access tape storage devices.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape library.
        * Object-access permission to the partition specified in the
          'partition-uri' property.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Tape Link' in the :term:`HMC API` book.

            The 'partition-uri' property identifies the partition to which
            this tape link will connect, and is required to be specified.

        Returns:

          :class:`~zhmcclient.TapeLink`:
            The resource object for the new tape link.
            The object will have its 'element-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self._base_uri, body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        tape_link = TapeLink(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return tape_link


class TapeLink(BaseResource):
    """
    Representation of a :term:`tape link`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.TapeLinkManager`).

    HMC/SE version requirements:

    * SE version >= 2.15.0
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.TapeLinkManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, TapeLinkManager), (
            f"TapeLink init: Expected manager type {TapeLinkManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)
        self._partition = None
        self._virtual_tape_resources = None

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: The :term:`partition` to which this
        tape link is connected.

        The returned :class:`~zhmcclient.Partition` has only a minimal set of
        properties populated.
        """
        # We do here some lazy loading.
        if not self._partition:
            partition_uri = self.get_property('partition-uri')
            tape_library = self.manager.tape_library
            cpc = tape_library.manager.console.manager.client.cpcs.find(
                **{'object-uri': tape_library.get_property('cpc-uri')})
            part_mgr = cpc.partitions
            self._partition = part_mgr.resource_object(partition_uri)
        return self._partition

    @property
    def virtual_tape_resources(self):
        """
        :class:`~zhmcclient.VirtualTapeResourceManager`: Access to the
        :term:`virtual tape resources <Virtual Tape Resource>` in this
        tape link.
        """
        # We do here some lazy loading.
        if not self._virtual_tape_resources:
            from ._virtual_tape_resource import VirtualTapeResourceManager
            self._virtual_tape_resources = VirtualTapeResourceManager(self)
        return self._virtual_tape_resources

    @logged_api_call
    def delete(self):
        """
        Delete this tape link and remove the connection between the tape
        library and the partition.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape link.
        * Object-access permission to the tape library containing this tape
          link.
        * Task permission to the "Configure Storage - System Programmer" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(
            uri=self.uri + '/operations/delete', resource=self, body={})
        # pylint: disable=protected-access
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))
        self.cease_existence_local()

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this tape link.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape link.
        * Object-access permission to the tape library containing this tape
          link.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are listed for operation
            'Modify Tape Link Properties' in section 'Tape Link element object'
            in the :term:`HMC API` book.

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
    def get_partitions(self, name=None, status=None):
        """
        Return the partitions associated with this tape link, optionally
        filtered by partition name and status.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape link.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          name (:term:`string`): Filter pattern (regular expression) to limit
            returned partitions to those that have a matching name. If `None`,
            no filtering for the partition name takes place.

          status (:term:`string`): Filter string to limit returned partitions
            to those that have a matching status. The value must be a valid
            partition status property value. If `None`, no filtering for the
            partition status takes place.

        Returns:

          List of :class:`~zhmcclient.Partition` objects representing the
          partitions associated with this tape link,
          with a minimal set of properties ('object-id', 'name', 'status').

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        query_parms = []
        if name is not None:
            append_query_parms(query_parms, 'name', name)
        if status is not None:
            append_query_parms(query_parms, 'status', status)
        query_parms_str = '&'.join(query_parms)
        if query_parms_str:
            query_parms_str = f'?{query_parms_str}'

        uri = f'{self.uri}/operations/get-partitions{query_parms_str}'

        tape_library = self.manager.tape_library
        cpc = tape_library.manager.console.manager.client.cpcs.find(
            **{'object-uri': tape_library.get_property('cpc-uri')})
        part_mgr = cpc.partitions

        result = self.manager.session.get(uri, resource=self)
        props_list = result['partitions']
        part_list = []
        for props in props_list:
            part = part_mgr.resource_object(props['object-uri'], props)
            part_list.append(part)
        return part_list

    @logged_api_call
    def get_histories(self):
        """
        Get the historical records for this tape link.

        The corresponding HMC operation is "Get Tape Link Histories".

        This operation retrieves historical information about the tape link,
        including connection events, configuration changes, and operational
        status over time.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape link.
        * Task permission to the "Configure Storage - System Programmer" task
          or to the "Configure Storage - Storage Administrator" task.

        Returns:

          :term:`json object`:
            A JSON object with the tape link histories. For details about the
            items in the JSON object, see section 'Response body contents' in
            section 'Get Tape Link Histories' in the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.get(
            self.uri + '/operations/get-tape-link-histories', resource=self)
        return result

    @logged_api_call
    def get_environment_report(self):
        """
        Get the latest environment report for this tape link.

        The corresponding HMC operation is "Get Tape Link Environment Report".

        The environment report provides information about the tape link's
        operational environment, including connectivity status, adapter
        information, and any environmental issues or warnings.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape link.
        * Task permission to the "Configure Storage - System Programmer" task
          or to the "Configure Storage - Storage Administrator" task.

        Returns:

          :term:`json object`:
            A JSON object with the environment report. For details about the
            items in the JSON object, see section 'Response body contents' in
            section 'Get Tape Link Environment Report' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.get(
            self.uri + '/operations/get-tape-link-environment-report',
            resource=self)
        return result

    @logged_api_call
    def update_environment_report(self, properties):
        """
        Update the environment report for this tape link.

        The corresponding HMC operation is
        "Update Tape Link Environment Report".

        This operation allows updating specific fields in the tape link's
        environment report, such as acknowledging warnings or updating
        configuration parameters.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape link.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): Properties to be updated in the environment report.
            Allowable properties are defined in section 'Request body contents'
            in section 'Update Tape Link Environment Report' in the
            :term:`HMC API` book.

        Returns:

          :term:`json object`:
            A JSON object with the operation results. For details about the
            items in the JSON object, see section 'Response body contents' in
            section 'Update Tape Link Environment Report' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.manager.session.post(
            self.uri + '/operations/update-tape-link-environment-report',
            resource=self, body=properties)
        return result

    @logged_api_call
    def add_adapter_ports(self, ports):
        """
        Add a list of tape adapter ports to this tape link's adapter ports list.

        These adapter ports become candidates for use as backing adapters when
        creating virtual tape resources when the tape link is attached to a
        partition. The adapter ports should have connectivity to the tape
        library.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape link.
        * Object-access permission to the adapter of each specified port.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          ports (:class:`py:list`): List of :class:`~zhmcclient.Port` objects
            representing the ports to be added. All specified ports must not
            already be members of this tape link's adapter ports list.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'adapter-port-uris': [p.uri for p in ports],
        }
        self.manager.session.post(
            self.uri + '/operations/add-adapter-ports', resource=self,
            body=body)

    @logged_api_call
    def remove_adapter_ports(self, ports):
        """
        Remove a list of tape adapter ports from this tape link's adapter
        ports list.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape link.
        * Object-access permission to the adapter of each specified port.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          ports (:class:`py:list`): List of :class:`~zhmcclient.Port` objects
            representing the ports to be removed. All specified ports must
            currently be members of this tape link's adapter ports list and
            must not be referenced by any of the tape link's virtual tape
            resources.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'adapter-port-uris': [p.uri for p in ports],
        }
        self.manager.session.post(
            self.uri + '/operations/remove-adapter-ports',
            resource=self, body=body)

    @logged_api_call
    def replace_adapter_port(self, current_port, new_port):
        """
        Replace a tape adapter port in this tape link's adapter ports list
        with a different port.

        This operation allows replacing an adapter port that is currently in
        use with a new port, which can be useful for maintenance or
        reconfiguration scenarios.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Authorization requirements:

        * Object-access permission to this tape link.
        * Object-access permission to the adapters of both specified ports.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          current_port (:class:`~zhmcclient.Port`): The port object
            representing the port to be replaced. This port must currently be
            a member of this tape link's adapter ports list.

          new_port (:class:`~zhmcclient.Port`): The port object representing
            the new port to replace the current port. This port must not
            already be a member of this tape link's adapter ports list.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {
            'current-adapter-port-uri': current_port.uri,
            'new-adapter-port-uri': new_port.uri,
        }
        self.manager.session.post(
            self.uri + '/operations/replace-adapter-port',
            resource=self, body=body)

    @logged_api_call
    def list_adapter_ports(self, full_properties=False):
        """
        Return the current adapter port list of this tape link.

        The result reflects the actual list of ports used by the CPC for this
        tape link. The source for this information is the 'adapter-port-uris'
        property of the tape link object.

        HMC/SE version requirements:

        * SE version >= 2.15.0

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            adapter port is being retrieved, vs. only the following short
            set: "element-uri", "element-id", "class", "parent".

        Returns:

          List of :class:`~zhmcclient.Port` objects representing the
          current adapter ports of this tape link.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        tape_library = self.manager.tape_library
        cpc = tape_library.manager.console.manager.client.cpcs.find(
            **{'object-uri': tape_library.get_property('cpc-uri')})
        adapter_mgr = cpc.adapters
        port_list = []
        port_uris = self.get_property('adapter-port-uris')
        if port_uris:
            for port_uri in port_uris:
                m = re.match(r'^(/api/adapters/[^/]*)/.*', port_uri)

                adapter_uri = m.group(1)
                adapter = adapter_mgr.resource_object(adapter_uri)

                port_mgr = adapter.ports
                port = port_mgr.resource_object(port_uri)
                port_list.append(port)
                if full_properties:
                    port.pull_full_properties()

        return port_list

# Made with Bob
