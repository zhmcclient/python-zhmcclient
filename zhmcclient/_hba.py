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
A :term:`HBA` (Host Bus Adapter) is a logical entity that provides a
:term:`Partition` with access to external storage area networks (SANs) through
an :term:`FCP Adapter`. More specifically, an HBA connects a Partition with an
:term:`Adapter Port` on an FCP Adapter.

HBA resources are contained in Partition resources.

HBA resources only exist in :term:`CPCs <CPC>` that are in DPM mode and when
the "dpm-storage-management" feature is not enabled. See section
:ref:`Storage Groups` for details. When the "dpm-storage-management" feature is
enabled, :term:`virtual HBAs <HBA>` are represented as
:term:`Virtual Storage Resource` resources.
"""

from __future__ import absolute_import

import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import get_logger, logged_api_call

__all__ = ['HbaManager', 'Hba']

LOG = get_logger(__name__)


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
    """

    def __init__(self, partition):
        # This function should not go into the docs.
        # Parameters:
        #   partition (:class:`~zhmcclient.Partition`):
        #     Partition defining the scope for this manager.

        super(HbaManager, self).__init__(
            resource_class=Hba,
            class_name='hba',
            session=partition.manager.session,
            parent=partition,
            base_uri='{}/hbas'.format(partition.uri),
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

        The returned HBAs have only the 'element-uri' property set.

        Filtering is supported only for the 'element-uri' property.

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
        resource_obj_list = []
        uris = self.partition.get_property('hba-uris')
        if uris:
            for uri in uris:

                resource_obj = self.resource_class(
                    manager=self,
                    uri=uri,
                    name=None,
                    properties=None)

                if self._matches_filters(resource_obj, filter_args):
                    resource_obj_list.append(resource_obj)
                    if full_properties:
                        resource_obj.pull_full_properties()

        self._name_uri_cache.update_from(resource_obj_list)
        return resource_obj_list

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
        assert isinstance(manager, HbaManager), \
            "Hba init: Expected manager type %s, got %s" % \
            (HbaManager, type(manager))
        super(Hba, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this HBA.

        Authorization requirements:

        * Object-access permission to the Partition containing this HBA.
        * Task permission to the "Partition Details" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self._uri)
        self.manager._name_uri_cache.delete(
            self.properties.get(self.manager._name_prop, None))

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this HBA.

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
    def reassign_port(self, port):
        """
        Reassign this HBA to a new underlying :term:`FCP port`.

        This method performs the HMC operation "Reassign Storage Adapter Port".

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
        self.manager.session.post(self._uri +
                                  '/operations/reassign-storage-adapter-port',
                                  body=body)
        self.properties.update(body)
