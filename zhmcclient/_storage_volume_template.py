# Copyright 2019,2021 IBM Corp. All Rights Reserved.
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
A :class:`~zhmcclient.StorageVolumeTemplate` object represents a
:term:`storage volume template` for FCP or FICON (ECKD) that is defined in a
:term:`storage group template`.

Storage volume template objects can be created, updated and deleted.

Storage volume templates are contained in
:term:`storage group templates <storage group template>`.

You can create as many storage volume templates as you want in a storage group
template. When creating a storage group from the storage group template, each
storage volume template will cause a storage volume to be created in the new
storage group.

Storage group templates and storage volume templates only can be defined in
CPCs that are in DPM mode and have SE version >= 2.14.1.
"""


import copy
# from requests.utils import quote

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_STORAGE_TEMPLATE_VOLUME

__all__ = ['StorageVolumeTemplateManager', 'StorageVolumeTemplate']


class StorageVolumeTemplateManager(BaseManager):
    """
    Manager providing access to the
    :term:`storage volume templates <storage volume template>`
    in a particular :term:`storage group template`.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable of a
    :class:`~zhmcclient.StorageGroupTemplate` object:

    * :attr:`~zhmcclient.StorageGroupTemplate.storage_volume_templates`

    HMC/SE version requirements:

    * SE version >= 2.14.1
    """

    def __init__(self, storage_group_template):
        # This function should not go into the docs.
        # Parameters:
        #   storage_group_template (:class:`~zhmcclient.StorageGroupTemplate`):
        #     Storage group template defining the scope for this manager.

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name',
            'maximum-size',
            'minimum-size',
            'usage',
        ]

        super().__init__(
            resource_class=StorageVolumeTemplate,
            class_name=RC_STORAGE_TEMPLATE_VOLUME,
            session=storage_group_template.manager.session,
            parent=storage_group_template,
            base_uri=f'{storage_group_template.uri}/storage-template-volumes',
            oid_prop='element-id',
            uri_prop='element-uri',
            name_prop='name',
            query_props=query_props)

    @property
    def storage_group_template(self):
        """
        :class:`~zhmcclient.StorageGroupTemplate`:
        :term:`Storage group template` defining the scope for this manager.
        """
        return self._parent

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the storage volume templates in this storage group template.

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

        * SE version >= 2.14.1

        Authorization requirements:

        * Object-access permission to this storage group template.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            storage volume template is being retrieved, vs. only the following
            short set: "element-uri", "name", "size", and "usage".

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen, i.e. all resources are
            returned.

        Returns:

          : A list of :class:`~zhmcclient.StorageVolumeTemplate` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = 'storage-template-volumes'
        list_uri = f'{self.storage_group_template.uri}/storage-template-volumes'
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args, None)

    @logged_api_call
    def create(self, properties):
        """
        Create a :term:`storage volume template` in this storage group template
        on the HMC.

        This method performs the "Modify Storage Template Properties"
        operation, requesting creation of the volume.

        HMC/SE version requirements:

        * SE version >= 2.14.1

        Authorization requirements:

        * Object-access permission to this storage group template.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): Initial property values for the new volume
            template.

            Allowable properties are the fields defined in the
            "storage-template-volume-request-info" nested object described for
            operation "Modify Storage Template Properties" in the
            :term:`HMC API` book.
            The valid fields are those for the "create" operation. The
            `operation` field must not be provided; it is set automatically
            to the value "create".

            The properties provided in this parameter will be copied and then
            amended with the `operation="create"` field, and then used as a
            single array item for the `storage-template-volumes` field in the
            request body of the "Modify Storage Template Properties" operation.

        Returns:

          StorageVolumeTemplate:
            The resource object for the new storage volume template.
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

            stovol1 = fcp_stogrp.storage_volume_templates.create(
                properties=dict(
                    name='vol1',
                    size=30,  # GiB
            ))
        """
        volreq_obj = copy.deepcopy(properties)
        volreq_obj['operation'] = 'create'
        body = {
            'storage-template-volumes': [volreq_obj],
        }
        result = self.session.post(
            self.storage_group_template.uri + '/operations/modify',
            body=body)
        uri = result['element-uris'][0]
        storage_volume_template = self.resource_object(uri, properties)
        # The 'name' property is unique within the parent object. However, it
        # is not returned by this operation, so we don't set the name-to-uri
        # cache. It will be set lazily, upon first use.
        return storage_volume_template


class StorageVolumeTemplate(BaseResource):
    """
    Representation of a :term:`storage volume template`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.StorageVolumeTemplateManager`).

    HMC/SE version requirements:

    * SE version >= 2.14.1
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.StorageVolumeTemplateManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, StorageVolumeTemplateManager), (
            "StorageVolumeTemplate init: Expected manager type "
            f"{StorageVolumeTemplateManager}, got {type(manager)}")
        super().__init__(
            manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this storage volume template on the HMC.

        This method performs the "Modify Storage Template Properties"
        operation, requesting deletion of the volume template.

        HMC/SE version requirements:

        * SE version >= 2.14.1

        Authorization requirements:

        * Object-access permission to the storage group template owning this
          storage volume template.
        * Task permission to the "Configure Storage - System Programmer" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        volreq_obj = {
            'operation': 'delete',
            'element-uri': self.uri,
        }
        body = {
            'storage-template-volumes': [
                volreq_obj
            ],
        }
        self.manager.session.post(
            self.manager.storage_group_template.uri + '/operations/modify',
            resource=self, body=body)

        # pylint: disable=protected-access
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))

        parent_sv_uris = self.manager.parent.get_properties_local(
            'storage-volume-uris')
        if parent_sv_uris:
            try:
                parent_sv_uris.remove(self._uri)
            except ValueError:
                pass

        self.cease_existence_local()

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this storage volume template on the HMC.

        This method performs the "Modify Storage Template Properties"
        operation, requesting modification of the volume.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements:

        * SE version >= 2.14.1

        Authorization requirements:

        * Object-access permission to the storage group template owning this
          storage volume template.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): New property values for the volume.
            Allowable properties are the fields defined in the
            "storage-template-volume-request-info" nested object for the
            "modify" operation. That nested object is described in operation
            "Modify Storage Template Properties" in the :term:`HMC API` book.

            The properties provided in this parameter will be copied and then
            amended with the `operation="modify"` and `element-uri` properties,
            and then used as a single array item for the
            `storage-template-volumes` field in the request body of the
            "Modify Storage Template Properties" operation.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        volreq_obj = copy.deepcopy(properties)
        volreq_obj['operation'] = 'modify'
        volreq_obj['element-uri'] = self.uri
        body = {
            'storage-template-volumes': [volreq_obj],
        }
        self.manager.session.post(
            self.manager.storage_group_template.uri + '/operations/modify',
            resource=self, body=body)
        self.update_properties_local(copy.deepcopy(properties))
