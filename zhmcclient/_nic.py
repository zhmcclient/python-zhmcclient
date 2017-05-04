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
A :term:`NIC` (Network Interface Card) is a logical entity that provides a
:term:`Partition` with access to external communication networks through a
:term:`Network Adapter`. More specifically, a NIC connects a Partition with a
:term:`Network Port`, or with a :term:`Virtual Switch` which then connects to
the Network Port.

NIC resources are contained in Partition resources.

NICs only exist in :term:`CPCs <CPC>` that are in DPM mode.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import get_logger, logged_api_call

__all__ = ['NicManager', 'Nic']

LOG = get_logger(__name__)


class NicManager(BaseManager):
    """
    Manager providing access to the :term:`NICs <NIC>` in a particular
    :term:`Partition`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.Partition` object (in DPM mode):

    * :attr:`~zhmcclient.Partition.nics`
    """

    def __init__(self, partition):
        # This function should not go into the docs.
        # Parameters:
        #   partition (:class:`~zhmcclient.Partition`):
        #     Partition defining the scope for this manager.

        super(NicManager, self).__init__(
            resource_class=Nic,
            session=partition.manager.session,
            parent=partition,
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
        List the NICs in this Partition.

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

          : A list of :class:`~zhmcclient.Nic` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        resource_obj_list = []
        uris = self.partition.get_property('nic-uris')
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
        Create and configure a NIC in this Partition.

        Authorization requirements:

        * Object-access permission to this Partition.
        * Object-access permission to the backing Adapter for the new NIC.
        * Task permission to the "Partition Details" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create NIC' in the :term:`HMC API` book.

            The backing Adapter for the new NIC is identified as follows:

            * For OSA and Hipersockets adapters, the Adapter associated with
              the Virtual Switch designated by the "virtual-switch-uri"
              property.
            * For RoCE adapters, the Adapter of the Port designated by the
              "network-adapter-port-uri" property.

        Returns:

          Nic:
            The resource object for the new NIC.
            The object will have its 'element-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result = self.session.post(self.partition.uri + '/nics',
                                   body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = properties.copy()
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        nic = Nic(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return nic

    @logged_api_call
    def nic_object(self, nic_id):
        """
        Return a minimalistic :class:`~zhmcclient.Nic` object for a Nic in this
        Partition.

        This method is an internal helper function and is not normally called
        by users.

        This object will be connected in the Python object tree representing
        the resources (i.e. it has this Partition as a parent), and will have
        the following properties set:

          * `element-uri`
          * `element-id`
          * `parent`
          * `class`

        Parameters:

            nic_id (string): `element-id` of the Nic

        Returns:

            :class:`~zhmcclient.Nic`: A Python object representing the Nic.
        """
        part_uri = self.parent.uri
        nic_uri = part_uri + "/nics/" + nic_id
        nic_props = {
            'element-id': nic_id,
            'parent': part_uri,
            'class': 'nic',
        }
        return Nic(self, nic_uri, None, nic_props)


class Nic(BaseResource):
    """
    Representation of a :term:`NIC`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    For the properties of a NIC resource, see section
    'Data model - NIC Element Object' in section 'Partition object' in the
    :term:`HMC API` book.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.NicManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.NicManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        if not isinstance(manager, NicManager):
            raise AssertionError("Nic init: Expected manager type %s, got %s" %
                                 (NicManager, type(manager)))
        super(Nic, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this NIC.

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
        Update writeable properties of this NIC.

        Authorization requirements:

        * Object-access permission to the Partition containing this NIC.
        * Object-access permission to the backing Adapter for this NIC.
        * Task permission to the "Partition Details" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model - NIC Element Object' in the
            :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self.uri, body=properties)
        self.properties.update(properties.copy())
        if self.manager._name_prop in properties:
            self.manager._name_uri_cache.update(self.name, self.uri)
