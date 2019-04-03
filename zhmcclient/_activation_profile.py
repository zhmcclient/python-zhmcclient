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
An :term:`Activation Profile` controls the activation of a :term:`CPC`
or :term:`LPAR`. They are used to tailor the operation of a CPC and are
stored in the Support Element associated with the CPC.

Activation Profile resources are contained in CPC resources.

Activation Profile resources only exist in CPCs that are not in DPM mode.

TODO: If Reset Activation Profiles are used to determine the CPC mode,
      should they not exist in all CPC modes?

There are three types of Activation Profiles:

1. Reset:
   The Reset Activation Profile defines for a CPC the mode in which the CPC
   licensed internal code will be loaded (e.g. DPM mode or classic mode) and
   how much central storage and expanded storage will be used.

2. Image:
   For CPCs in classic mode, each LPAR can have an Image Activation Profile.
   The Image Activation Profile determines the number of CPs that the LPAR will
   use and whether these CPs will be dedicated to the LPAR or shared. It also
   allows assigning the amount of central storage and expanded storage that
   will be used by each LPAR.

3. Load:
   For CPCs in classic mode, each LPAR can have a Load Activation Profile.
   The Load Activation Profile defines the channel address of the device that
   the operating system for that LPAR will be loaded (booted) from.
"""

from __future__ import absolute_import

import copy

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call

__all__ = ['ActivationProfileManager', 'ActivationProfile']


class ActivationProfileManager(BaseManager):
    """
    Manager providing access to the
    :term:`Activation Profiles <Activation Profile>` of a particular type in
    a particular :term:`CPC` (the scoping CPC).

    Possible types of activation profiles are:

    * Reset Activation Profile
    * Image Activation Profile
    * Load Activation Profile

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.

    Objects of this class are not directly created by the user; they are
    accessible via the following instance variables of a
    :class:`~zhmcclient.Cpc` object (in classic mode or ensemble mode):

    * :attr:`~zhmcclient.Cpc.reset_activation_profiles`
    * :attr:`~zhmcclient.Cpc.image_activation_profiles`
    * :attr:`~zhmcclient.Cpc.load_activation_profiles`
    """

    def __init__(self, cpc, profile_type):
        # This function should not go into the docs.
        # Parameters:
        #   cpc (:class:`~zhmcclient.Cpc`):
        #     CPC defining the scope for this manager.
        #   profile_type (string):
        #     Type of Activation Profiles:
        #     * `reset`: Reset Activation Profiles
        #     * `image`: Image Activation Profiles
        #     * `load`: Load Activation Profiles

        # Resource properties that are supported as filter query parameters.
        # If the support for a resource property changes within the set of HMC
        # versions that support this type of resource, this list must be set up
        # for the version of the HMC this session is connected to.
        query_props = [
            'name',
        ]

        super(ActivationProfileManager, self).__init__(
            resource_class=ActivationProfile,
            class_name='{}-activation-profile'.format(profile_type),
            session=cpc.manager.session,
            parent=cpc,
            base_uri='{}/{}-activation-profiles'.format(cpc.uri, profile_type),
            oid_prop='name',  # This is an exception!
            uri_prop='element-uri',
            name_prop='name',
            query_props=query_props)

        self._profile_type = profile_type

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: :term:`CPC` defining the scope for this
        manager.
        """
        return self._parent

    @property
    def profile_type(self):
        """
        :term:`string`: Type of the Activation Profiles managed by this object:

        * ``'reset'`` - Reset Activation Profiles
        * ``'image'`` - Image Activation Profiles
        * ``'load'`` - Load Activation Profiles
        """
        return self._profile_type

    @logged_api_call
    def list(self, full_properties=False, filter_args=None):
        """
        List the Activation Profiles of this CPC, of the profile type
        managed by this object.

        Authorization requirements:

        * Object-access permission to this CPC.

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

          : A list of :class:`~zhmcclient.ActivationProfile` objects.

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

            resources_name = self._profile_type + '-activation-profiles'
            uri = '{}/{}{}'.format(self.cpc.uri, resources_name, query_parms)

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


class ActivationProfile(BaseResource):
    """
    Representation of an :term:`Activation Profile` of a particular type.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.ActivationProfileManager`).
    """

    def __init__(self, manager, uri, name=None, properties=None):
        # This function should not go into the docs.
        #   manager (:class:`~zhmcclient.ActivationProfileManager`):
        #     Manager object for this resource object.
        #   uri (string):
        #     Canonical URI path of the resource.
        #   name (string):
        #     Name of the resource.
        #   properties (dict):
        #     Properties to be set for this resource object. May be `None` or
        #     empty.
        assert isinstance(manager, ActivationProfileManager), \
            "ActivationProfile init: Expected manager type %s, got %s" % \
            (ActivationProfileManager, type(manager))
        super(ActivationProfile, self).__init__(manager, uri, name, properties)

    @logged_api_call
    def update_properties(self, properties):
        """
        Update writeable properties of this Activation Profile.

        Authorization requirements:

        * Object-access permission to the CPC of this Activation Profile.
        * Task permission for the "Customize/Delete Activation Profiles" task.

        Parameters:

          properties (dict): New values for the properties to be updated.
            Properties not to be updated are omitted.
            Allowable properties are the properties with qualifier (w) in
            section 'Data model' in section
            '<profile_type> activation profile' in the :term:`HMC API` book,
            where <profile_type> is the profile type of this object
            (e.g. Reset, Load, Image).

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        self.manager.session.post(self.uri, body=properties)
        # Attempts to change the 'name' property will be rejected by the HMC,
        # so we don't need to update the name-to-URI cache.
        assert self.manager._name_prop not in properties
        self.properties.update(copy.deepcopy(properties))
