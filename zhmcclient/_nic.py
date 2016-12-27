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

__all__ = ['NicManager', 'Nic']


class NicManager(BaseManager):
    """
    Manager providing access to the :term:`NICs <NIC>` in a particular
    :term:`Partition`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible as properties in higher level resources (in this case, the
    :class:`~zhmcclient.Partition` object).
    """

    def __init__(self, partition):
        # This function should not go into the docs.
        # Parameters:
        #   partition (:class:`~zhmcclient.Partition`):
        #     Partition defining the scope for this manager.
        super(NicManager, self).__init__(Nic, partition)

    @property
    def partition(self):
        """
        :class:`~zhmcclient.Partition`: :term:`Partition` defining the scope
        for this manager.
        """
        return self._parent

    def list(self, full_properties=False):
        """
        List the NICs in this Partition.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.Nic` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        nic_uris = self.partition.get_property('nic-uris')
        nic_list = []
        if nic_uris:
            for uri in nic_uris:
                nic = Nic(self, uri)
                if full_properties:
                    nic.pull_full_properties()
                nic_list.append(nic)
        return nic_list

    def create(self, properties):
        """
        Create and configure a NIC in this Partition.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create NIC' in the :term:`HMC API` book.

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
        return Nic(self, props['element-uri'], props)

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
        return Nic(self, nic_uri, nic_props)


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

    def __init__(self, manager, uri, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.NicManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        if not isinstance(manager, NicManager):
            raise AssertionError("Nic init: Expected manager type %s, got %s" %
                                 (NicManager, type(manager)))
        super(Nic, self).__init__(manager, uri, properties,
                                  uri_prop='element-uri',
                                  name_prop='name')

    def delete(self):
        """
        Delete this NIC.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.delete(self._uri)

    def update_properties(self, properties):
        """
        Update writeable properties of this NIC.

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
        self.manager.session.post(self._uri, body=properties)
