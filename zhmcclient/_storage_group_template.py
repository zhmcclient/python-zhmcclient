# Copyright 2019 IBM Corp. All Rights Reserved.
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
A :class:`~zhmcclient.StorageGroupTemplate` object represents a
:term:`storage group template` object and can be used to create
:term:`storage group` objects with the properties of the template, including an
initial set of storage volumes, using the
:meth:`zhmcclient.StorageGroupTemplateManager.create` method.

Storage group template objects can be created, updated and deleted.

Storage group template objects can only be defined in CPCs that are in
DPM mode and that have the "dpm-storage-management" feature enabled.
"""

from __future__ import absolute_import

import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._storage_volume_template import StorageVolumeTemplateManager
from ._logging import logged_api_call

__all__ = ['StorageGroupTemplateManager', 'StorageGroupTemplate']


class StorageGroupTemplateManager(BaseManager):
    """
    Manager providing access to the
    :term:`storage group templates <storage group template>` of the HMC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variable:

    * :attr:`~zhmcclient.Console.storage_group_templates` of a
      :class:`~zhmcclient.Console` object.
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
            'cpc-uri',
            'name',
            'type',
        ]

        super(StorageGroupTemplateManager, self).__init__(
            resource_class=StorageGroupTemplate,
            class_name='storage-template',
            session=console.manager.session,
            parent=console,
            base_uri='/api/storage-templates',
            oid_prop='object-id',
            uri_prop='object-uri',
            name_prop='name',
            query_props=query_props)
        self._console = console

    @property
    def console(self):
        """
        :class:`~zhmcclient.Console`: The Console object representing the HMC.
        """
        return self._console

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the storage group templates defined in the HMC.

        Storage group templates for which the authenticated user does not have
        object-access permission are not included.

        Authorization requirements:

        * Object-access permission to any storage group templates to be
          included in the result.

        Parameters:

          full_properties (bool):
            Controls that the full set of resource properties for each returned
            storage group template is being retrieved, vs. only the following
            short set: "object-uri", "cpc-uri", "name", and "type".

          filter_args (dict):
            Filter arguments that narrow the list of returned resources to
            those that match the specified filter arguments. For details, see
            :ref:`Filtering`.

            `None` causes no filtering to happen.

        Returns:

          : A list of :class:`~zhmcclient.StorageGroupTemplate` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """

        resource_obj_list = []

        if filter_args is None:
            filter_args = {}

        resource_obj = self._try_optimized_lookup(filter_args)
        if resource_obj:
            resource_obj_list.append(resource_obj)
            # It already has full properties
        else:
            query_parms, client_filters = self._divide_filter_args(filter_args)
            uri = '{}{}'.format(self._base_uri, query_parms)

            result = self.session.get(uri)
            if result:
                props_list = result['storage-templates']
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
    def create(self, properties):
        """
        Create a storage group template.

        The new storage group will be associated with the CPC identified by the
        `cpc-uri` input property.

        Authorization requirements:

        * Object-access permission to the CPC that will be associated with
          the new storage group template.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Storage Template' in the :term:`HMC API` book.

            The 'cpc-uri' property identifies the CPC to which the new
            storage group template will be associated, and is required to be
            specified in this parameter.

        Returns:

          :class:`~zhmcclient.StorageGroupTemplate`:
            The resource object for the new storage group template.
            The object will have its 'object-uri' property set as returned by
            the HMC, and will also have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        if properties is None:
            properties = {}

        result = self.session.post(self._base_uri, body=properties)
        # There should not be overlaps, but just in case there are, the
        # returned props should overwrite the input props:
        props = copy.deepcopy(properties)
        props.update(result)
        name = props.get(self._name_prop, None)
        uri = props[self._uri_prop]
        storage_group_template = StorageGroupTemplate(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return storage_group_template


class StorageGroupTemplate(BaseResource):
    """
    Representation of a :term:`storage group template`.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.StorageGroupTemplateManager`).
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
        assert isinstance(manager, StorageGroupTemplateManager), \
            "StorageGroupTemplate init: Expected manager type %s, got %s" % \
            (StorageGroupTemplateManager, type(manager))
        super(StorageGroupTemplate, self).__init__(
            manager, uri, name, properties)
        # The manager objects for child resources (with lazy initialization):
        self._storage_volume_templates = None
        self._cpc = None

    @property
    def storage_volume_templates(self):
        """
        :class:`~zhmcclient.StorageVolumeManager`: Access to the
        :term:`storage volumes <storage volume>` in this storage group.
        """
        # We do here some lazy loading.
        if not self._storage_volume_templates:
            self._storage_volume_templates = StorageVolumeTemplateManager(self)
        return self._storage_volume_templates

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: The :term:`CPC` to which this storage group
        template is associated.

        The returned :class:`~zhmcclient.Cpc` has only a minimal set of
        properties populated.
        """
        # We do here some lazy loading.
        if not self._cpc:
            cpc_uri = self.get_property('cpc-uri')
            cpc_mgr = self.manager.console.manager.client.cpcs
            self._cpc = cpc_mgr.resource_object(cpc_uri)
        return self._cpc

    @logged_api_call
    def delete(self):
        """
        Delete this storage group template and its storage volume template
        resources on the HMC.

        Storage groups and their volumes that have been created from the
        template that is deleted, are not affected.

        Authorization requirements:

        * Object-access permission to this storage group template.
        * Task permission to the "Configure Storage - System Programmer" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.delete(uri=self.uri)
        self.manager._name_uri_cache.delete(
            self._properties.get(self.manager._name_prop, None))

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this storage group template.

        This includes the `storage-template-volumes` property which contains
        requests for creations, deletions and updates of
        :class:`~zhmcclient.StorageVolumeTemplate` resources of this storage
        group template.

        As an alternative to this bulk approach for managing storage volume
        templates, each :class:`~zhmcclient.StorageVolumeTemplate` resource
        can individually be created, deleted and updated using the respective
        methods on
        :attr:`~zhmcclient.StorageGroupTemplate.storage_volume_templates`.

        Authorization requirements:

        * Object-access permission to this storage group template.
        * Task permission to the "Configure Storage - System Programmer" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are listed for operation
            'Modify Storage Template Properties' in the :term:`HMC API` book.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        uri = '{}/operations/modify'.format(self.uri)
        self.manager.session.post(uri, body=properties)
        is_rename = self.manager._name_prop in properties
        if is_rename:
            # Delete the old name from the cache
            self.manager._name_uri_cache.delete(self.name)
        self._properties.update(copy.deepcopy(properties))
        if is_rename:
            # Add the new name to the cache
            self.manager._name_uri_cache.update(self.name, self.uri)
