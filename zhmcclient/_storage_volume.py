# Copyright 2018 IBM Corp. All Rights Reserved.
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
A :class:`~zhmcclient.StorageVolume` object represents an FCP or FICON (ECKD)
:term:`storage volume` that is defined in a :term:`storage group`.

Storage volume objects can be created, but what is created is the definition
of a storage volume in the HMC and CPC. This does not include the act of
actually allocating the volume on a storage subsystem. That is performed by a
storage administrator who :term:`fulfills <fulfillment>` the volumes.

In order to represent that, storage volume objects have a fulfillment state
that is available in their 'fulfillment-state' property.

When a storage group is attached to a :term:`partition`, the group's
storage volumes are attached to the partition and any :term:`virtual storage
resource` objects are instantiated.

Storage volumes are contained in :term:`storage groups <storage group>`.

You can create as many storage volumes as you want in a storage group.

Storage groups and storage volumes only can be defined in CPCs that are in
DPM mode and that have the "dpm-storage-management" feature enabled.
"""

from __future__ import absolute_import

import re
import copy
# from requests.utils import quote

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import get_logger, logged_api_call

__all__ = ['StorageVolumeManager', 'StorageVolume']

LOG = get_logger(__name__)


class StorageVolumeManager(BaseManager):
    """
    Manager providing access to the :term:`storage volumes <storage volume>`
    in a particular :term:`storage group`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.StorageGroup` object:

    * :attr:`~zhmcclient.StorageGroup.storage_volumes`
    """

    def __init__(self, storage_group):
        # This function should not go into the docs.
        # Parameters:
        #   storage_group (:class:`~zhmcclient.StorageGroup`):
        #     Storage group defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name',
            'fulfillment-state',
            'maximum-size',
            'minimum-size',
            'usage',
        ]

        super(StorageVolumeManager, self).__init__(
            resource_class=StorageVolume,
            class_name='storage_volume',
            session=storage_group.manager.session,
            parent=storage_group,
            base_uri='{}/storage-volumes'.format(storage_group.uri),
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=query_props)

    @property
    def storage_group(self):
        """
        :class:`~zhmcclient.StorageGroup`: :term:`Storage group` defining the
        scope for this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the storage volumes in this storage group.

        Authorization requirements:

        * Object-access permission to this storage group.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            storage volume is being retrieved, vs. only the following short
            set: "element-uri", "name", "fulfillment-state", "size", and
            "usage".

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          : A list of :class:`~zhmcclient.StorageVolume` objects.

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

            resources_name = 'storage-volumes'
            uri = '{}/{}{}'.format(self.storage_group.uri, resources_name,
                                   query_parms)

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
    def create(self, properties, email_to_addresses=None,
               email_cc_addresses=None, email_insert=None):
        """
        Create a :term:`storage volume` in this storage group on the HMC, and
        optionally send emails to storage administrators requesting creation of
        the storage volume on the storage subsystem and setup of any resources
        related to the storage volume (e.g. LUN mask definition on the storage
        subsystem).

        This method performs the "Modify Storage Group Properties" operation,
        requesting creation of the volume.

        Authorization requirements:

        * Object-access permission to this storage group.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): Initial property values for the new volume.

            Allowable properties are the fields defined in the
            "storage-volume-request-info" nested object described for
            operation "Modify Storage Group Properties" in the
            :term:`HMC API` book.
            The valid fields are those for the "create" operation. The
            `operation` field must not be provided; it is set automatically
            to the value "create".

            The properties provided in this parameter will be copied and then
            amended with the `operation="create"` field, and then used as a
            single array item for the `storage-volumes` field in the request
            body of the "Modify Storage Group Properties" operation.

            Note that for storage volumes, the HMC does auto-generate a value
            for the "name" property, but that auto-generated name is not unique
            within the parent storage group. If you depend on a unique name,
            you need to specify a "name" property accordingly.

          email_to_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrator to be notified.
            If `None` or empty, no email will be sent.

          email_cc_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrator to be copied
            on the notification email.
            If `None` or empty, nobody will be copied on the email.
            Must be `None` or empty if `email_to_addresses` is `None` or empty.

          email_insert (:term:`string`): Additional text to be inserted in the
            notification email.
            The text can include HTML formatting tags.
            If `None`, no additional text will be inserted.
            Must be `None` or empty if `email_to_addresses` is `None` or empty.

        Returns:

          StorageVolume:
            The resource object for the new storage volume.
            The object will have the following properties set:

            - 'element-uri' as returned by the HMC
            - 'element-id' as determined from the 'element-uri' property
            - 'class' and 'parent'
            - additional properties as specified in the input properties

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`

        Example::

            stovol1 = fcp_stogrp.storage_volumes.create(
                properties=dict(
                    name='vol1',
                    size=30,  # GiB
            ))
        """

        sv_properties = copy.deepcopy(properties)
        sv_properties['operation'] = 'create'
        body = {
            'storage-volumes': [sv_properties],
        }
        if email_to_addresses:
            body['email-to-addresses'] = email_to_addresses
            if email_cc_addresses:
                body['email-cc-addresses'] = email_cc_addresses
            if email_insert:
                body['email-insert'] = email_insert
        else:
            if email_cc_addresses:
                raise ValueError("email_cc_addresses must not be specified if "
                                 "there is no email_to_addresses: %r" %
                                 email_cc_addresses)
            if email_insert:
                raise ValueError("email_insert must not be specified if "
                                 "there is no email_to_addresses: %r" %
                                 email_insert)

        result = self.session.post(
            self.storage_group.uri + '/operations/modify',
            body=body)
        uri = result['element-uris'][0]

        storage_volume = self.resource_object(uri, properties)

        # The name is not guaranteed to be unique, so we don't maintain
        # a name-to-uri cache for storage volumes.

        return storage_volume


class StorageVolume(BaseResource):
    """
    Representation of a :term:`storage volume`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.StorageVolumeManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.StorageVolumeManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, StorageVolumeManager), \
            "StorageVolume init: Expected manager type %s, got %s" % \
            (StorageVolumeManager, type(manager))
        super(StorageVolume, self).__init__(manager, uri, name, properties)

    @property
    def oid(self):
        """
        :term `unicode string`: The object ID of this storage volume.
        The object ID is unique within the parent storage group.

        Note that for storage volumes, the 'name' property is not unique and
        therefore cannot be used to identify a storage volume. Therefore,
        storage volumes provide easy access to the object ID, as a means to
        identify the storage volume in CLIs and other string-based tooling.
        """
        m = re.match(r'^/api/storage-groups/[^/]*/storage-volumes/([^/]*)$',
                     self.uri)
        oid = m.group(1)
        return oid

    @logged_api_call
    def delete(self, email_to_addresses=None, email_cc_addresses=None,
               email_insert=None):
        """
        Delete this storage volume on the HMC, and optionally send emails to
        storage administrators requesting deletion of the storage volume on the
        storage subsystem and cleanup of any resources related to the storage
        volume (e.g. LUN mask definitions on a storage subsystem).

        This method performs the "Modify Storage Group Properties" operation,
        requesting deletion of the volume.

        Authorization requirements:

        * Object-access permission to the storage group owning this storage
          volume.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          email_to_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrator to be notified.
            If `None` or empty, no email will be sent.

          email_cc_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrator to be copied
            on the notification email.
            If `None` or empty, nobody will be copied on the email.
            Must be `None` or empty if `email_to_addresses` is `None` or empty.

          email_insert (:term:`string`): Additional text to be inserted in the
            notification email.
            The text can include HTML formatting tags.
            If `None`, no additional text will be inserted.
            Must be `None` or empty if `email_to_addresses` is `None` or empty.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        req_properties = {
            'operation': 'delete',
            'element-uri': self.uri,
        }
        body = {
            'storage-volumes': req_properties,
        }
        if email_to_addresses:
            body['email-to-addresses'] = email_to_addresses
            if email_cc_addresses:
                body['email-cc-addresses'] = email_cc_addresses
            if email_insert:
                body['email-insert'] = email_insert
        else:
            if email_cc_addresses:
                raise ValueError("email_cc_addresses must not be specified if "
                                 "there is no email_to_addresses: %r" %
                                 email_cc_addresses)
            if email_insert:
                raise ValueError("email_insert must not be specified if "
                                 "there is no email_to_addresses: %r" %
                                 email_insert)

        self.session.post(
            self.storage_group.uri + '/operations/modify',
            body=body)

        self.manager._name_uri_cache.delete(
            self.properties.get(self.manager._name_prop, None))

    @logged_api_call
    def update_properties(self, properties, email_to_addresses=None,
                          email_cc_addresses=None, email_insert=None):
        """
        Update writeable properties of this storage volume on the HMC, and
        optionally send emails to storage administrators requesting
        modification of the storage volume on the storage subsystem and of any
        resources related to the storage volume.

        This method performs the "Modify Storage Group Properties" operation,
        requesting modification of the volume.

        Authorization requirements:

        * Object-access permission to the storage group owning this storage
          volume.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): New property values for the volume.
            Allowable properties are the fields defined in the
            "storage-volume-request-info" nested object for the "modify"
            operation. That nested object is described in section "Request body
            contents" for operation "Modify Storage Group Properties" in the
            :term:`HMC API` book.

            The properties provided in this parameter will be copied and then
            amended with the `operation="modify"` and `element-uri` properties,
            and then used as a single array item for the `storage-volumes`
            field in the request body of the "Modify Storage Group Properties"
            operation.

          email_to_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrator to be notified.
            If `None` or empty, no email will be sent.

          email_cc_addresses (:term:`iterable` of :term:`string`): Email
            addresses of one or more storage administrator to be copied
            on the notification email.
            If `None` or empty, nobody will be copied on the email.
            Must be `None` or empty if `email_to_addresses` is `None` or empty.

          email_insert (:term:`string`): Additional text to be inserted in the
            notification email.
            The text can include HTML formatting tags.
            If `None`, no additional text will be inserted.
            Must be `None` or empty if `email_to_addresses` is `None` or empty.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        req_properties = copy.deepcopy(properties)
        req_properties['operation'] = 'modify'
        req_properties['element-uri'] = self.uri
        body = {
            'storage-volumes': req_properties,
        }
        if email_to_addresses:
            body['email-to-addresses'] = email_to_addresses
            if email_cc_addresses:
                body['email-cc-addresses'] = email_cc_addresses
            if email_insert:
                body['email-insert'] = email_insert
        else:
            if email_cc_addresses:
                raise ValueError("email_cc_addresses must not be specified if "
                                 "there is no email_to_addresses: %r" %
                                 email_cc_addresses)
            if email_insert:
                raise ValueError("email_insert must not be specified if "
                                 "there is no email_to_addresses: %r" %
                                 email_insert)

        self.session.post(
            self.storage_group.uri + '/operations/modify',
            body=body)

        self.properties.update(copy.deepcopy(properties))

    @logged_api_call
    def indicate_fulfillment_ficon(self, control_unit, unit_address):
        """
        TODO: Add ControlUnit objects etc for FICON support.

        Indicate completion of :term:`fulfillment` for this ECKD (=FICON)
        storage volume and provide identifying information (control unit
        and unit address) about the actual storage volume on the storage
        subsystem.

        Manually indicating fulfillment is required for all ECKD volumes,
        because they are not auto-discovered by the CPC.

        This method performs the "Fulfill FICON Storage Volume" HMC operation.

        Upon successful completion of this operation, the "fulfillment-state"
        property of this storage volume object will have been set to
        "complete". That is necessary for the CPC to be able to address and
        connect to the volume.

        If the "fulfillment-state" properties of all storage volumes in the
        owning storage group are "complete", the owning storage group's
        "fulfillment-state" property will also be set to "complete".

        Parameters:

          control_unit (:class:`~zhmcclient.ControlUnit`):
            Logical control unit (LCU) in which the backing ECKD volume is
            defined.

          unit_address (:term:`string`):
            Unit address of the backing ECKD volume within its logical control
            unit,
            as a hexadecimal number of up to 2 characters in any lexical case.

        Authorization requirements:

        * Object-access permission to the storage group owning this storage
          volume.
        * Task permission to the "Configure Storage - Storage Administrator"
          task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        # The operation requires exactly 2 characters in lower case
        unit_address_2 = format(int(unit_address, 16), '02x')

        body = {
            'control-unit-uri': control_unit.uri,
            'unit-address': unit_address_2,
        }
        self.manager.session.post(
            self.uri + '/operations/fulfill-ficon-storage-volume',
            body=body)

    @logged_api_call
    def indicate_fulfillment_fcp(self, wwpn, lun, host_port):
        """
        Indicate completion of :term:`fulfillment` for this FCP storage volume
        and provide identifying information (WWPN and LUN) about the actual
        storage volume on the storage subsystem.

        Manually indicating fulfillment is required for storage volumes that
        will be used as boot devices for a partition. The specified host
        port will be used to access the storage volume during boot of the
        partition.

        Because the CPC discovers storage volumes automatically, the
        fulfillment of non-boot volumes does not need to be manually indicated
        using this function (it may be indicated though before the CPC
        discovers a working communications path to the volume, but the role
        of the specified host port is not clear in this case).

        This method performs the "Fulfill FCP Storage Volume" HMC operation.

        Upon successful completion of this operation, the "fulfillment-state"
        property of this storage volume object will have been set to
        "complete". That is necessary for the CPC to be able to address and
        connect to the volume.

        If the "fulfillment-state" properties of all storage volumes in the
        owning storage group are "complete", the owning storage group's
        "fulfillment-state" property will also be set to "complete".

        Parameters:

          wwpn (:term:`string`):
            World wide port name (WWPN) of the FCP storage subsystem containing
            the storage volume,
            as a hexadecimal number of up to 16 characters in any lexical case.

          lun (:term:`string`):
            Logical Unit Number (LUN) of the storage volume within its FCP
            storage subsystem,
            as a hexadecimal number of up to 16 characters in any lexical case.

          host_port (:class:`~zhmcclient.Port`):
            Storage port on the CPC that will be used to boot from.

        Authorization requirements:

        * Object-access permission to the storage group owning this storage
          volume.
        * Task permission to the "Configure Storage - Storage Administrator"
          task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        # The operation requires exactly 16 characters in lower case
        wwpn_16 = format(int(wwpn, 16), '016x')
        lun_16 = format(int(lun, 16), '016x')

        body = {
            'world-wide-port-name': wwpn_16,
            'logical-unit-number': lun_16,
            'adapter-port-uri': host_port.uri,
        }
        self.manager.session.post(
            self.uri + '/operations/fulfill-fcp-storage-volume',
            body=body)
