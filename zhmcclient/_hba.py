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
A :term:`HBA` (Host Bus Adapter) is a logical entity that provides a
:term:`Partition` with access to external storage area networks (SANs) through
an :term:`FCP Adapter`. More specifically, an HBA connects a Partition with an
:term:`Adapter Port` on an FCP Adapter.

HBA resources are contained in Partition resources.

HBA resources only exist in :term:`CPCs <CPC>` that are in DPM mode and when
the "dpm-storage-management" :ref:`firmware feature <firmware features>` is not
enabled. See section :ref:`Storage Groups` for details. When the
"dpm-storage-management" firmware feature is enabled, :term:`virtual HBAs <HBA>`
are represented as :term:`Virtual Storage Resource` resources.
"""


import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_HBA

__all__ = ['HbaManager', 'Hba']


class HbaManager(BaseManager):
    """
    Manager providing access to the :term:`HBAs <HBA>` in a particular
    :term:`Partition`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Partition` object (in DPM mode):

    * :attr:`~zhmcclient.Partition.hbas`

    HMC/SE version requirements:

    * SE version >= 2.13.1 without
      :ref:`firmware feature <firmware features>` "dpm-storage-management"
    """

    def __init__(self, partition):
        # This function should not go into the docs.
        # Parameters:
        #   partition (:class:`~zhmcclient.Partition`):
        #     Partition defining the scope for this manager.

        super().__init__(
            resource_class=Hba,
            class_name=RC_HBA,
            session=partition.manager.session,
            parent=partition,
            base_uri=f'{partition.uri}/hbas',
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=[],
            list_has_name=False)

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: :term:`Partition` defining the scope
        for this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the HBAs in this Partition.

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

        * Otherwise, the corresponding array property for this resource in the
          parent object is used to list the resources, and the provided filter
          arguments are applied.

        HMC/SE version requirements:

        * SE version >= 2.13.1 without
          :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to this Partition.

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

          : A list of :class:`~zhmcclient.Hba` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        return self._list_with_parent_array(
            self.partition, 'hba-uris', full_properties, filter_args)

    @logged_api_call
    def create(self, properties):
        """
        Create and configure an HBA in this Partition.

        The HBA must be backed by an adapter port on an FCP adapter.

        The backing adapter port is specified in the "properties" parameter of
        this method by setting the "adapter-port-uri" property to the URI of
        the backing adapter port.

        The value for the "adapter-port-uri" property can be determined from a
        given adapter name and port index as shown in the following example
        code (omitting any error handling):

        .. code-block:: python

            partition = ...  # Partition object for the new HBA

            adapter_name = 'FCP #1'  # name of adapter with backing port
            adapter_port_index = 0   # port index of backing port

            adapter = partition.manager.cpc.adapters.find(name=adapter_name)

            port = adapter.ports.find(index=adapter_port_index)

            properties['adapter-port-uri'] = port.uri

        HMC/SE version requirements:

        * SE version >= 2.13.1 without
          :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to this Partition.
        * Object-access permission to the backing Adapter for the new HBA.
        * Task permission to the "Partition Details" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create HBA' in the :term:`HMC API` book.

        Returns:

          Hba:
            The resource object for the new HBA.
            The object will have its 'element-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.partition.uri + '/hbas',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        hba = Hba(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return hba


class Hba(BaseResource):
    """
    Representation of an :term:`HBA`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of an HBA resource, see section
    'Data model - HBA Element Object' in section 'Partition object' in the
    :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.HbaManager`).

    HMC/SE version requirements:

    * SE version >= 2.13.1 without
      :ref:`firmware feature <firmware features>` "dpm-storage-management"
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        # Parameters:
        #   manager (:class:`~zhmcclient.HbaManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, HbaManager), (
            f"Hba init: Expected manager type {HbaManager}, "
            f"got {type(manager)}")
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this HBA.

        HMC/SE version requirements:

        * SE version >= 2.13.1 without
          :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to the Partition containing this HBA.
        * Task permission to the "Partition Details" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.delete(self._uri, resource=self)
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))

        parent_hba_uris = self.manager.parent.get_properties_local(
            'hba-uris')
        if parent_hba_uris:
            try:
                parent_hba_uris.remove(self._uri)
            except ValueError:
                pass

        self.cease_existence_local()

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this HBA.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.13.1 without
          :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to the Partition containing this HBA.
        * **TBD: Verify:** Object-access permission to the backing Adapter for
          this HBA.
        * Task permission to the "Partition Details" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model - HBA Element Object' in the
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
    def reassign_port(self, port):
        """
        Reassign this HBA to a new underlying :term:`FCP port`.

        This method performs the HMC operation "Reassign Storage Adapter Port".

        HMC/SE version requirements:

        * SE version >= 2.13.1 without
          :ref:`firmware feature <firmware features>` "dpm-storage-management"

        Authorization requirements:

        * Object-access permission to the Partition containing this HBA.
        * Object-access permission to the Adapter with the new Port.
        * Task permission to the "Partition Details" task.

        Parameters:

          port (:class:`~zhmcclient.Port`): :term:`FCP port` to be used.

        Raises:

          :exc:`~zhmcclient.HTTPError`: See the HTTP status and reason codes of
            operation "Reassign Storage Adapter Port" in the :term:`HMC API`
            book.
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'adapter-port-uri': port.uri}
        self.manager.session.post(
            self._uri + '/operations/reassign-storage-adapter-port',
            resource=self, body=body)
        self.update_properties_local(body)
