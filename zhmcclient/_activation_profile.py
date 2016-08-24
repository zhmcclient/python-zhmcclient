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
**Activation profiles** are required for CPC (processor)
and CPC image (partition) activation. They are used to tailor the operation
of a CPC and are stored in the Support Element associated with the CPC.

There are types of activation profiles:

1. Reset:
   Every CPC in the processor cluster requires a reset profile to determine
   the mode in which the CPC licensed internal code will be loaded and
   how much central storage and expanded storage will be used.

2. Image:
   If LPAR mode is selected in the reset profile, each partition
   can have an image profile. The image profile determines the number of CPs
   that the image will use and whether these CPs will be dedicated
   to the partition or shared. It also allows you to assign the amount of
   central storage and expanded storage that will be used by each partition.

3. Load:
   A load profile is needed to define the channel address of the device that
   the operating system will be loaded from.

Activation Profiles are not provided when the CPC is enabled for DPM.
"""

from __future__ import absolute_import

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import _log_call


__all__ = ['ActivationProfileManager', 'ActivationProfile']


class ActivationProfileManager(BaseManager):
    """
    Manager object for Activation Profiles.
    This manager object is scoped to the Activation Profiles of a particular
    CPC.

    Derived from :class:`~zhmcclient.BaseManager`; see there for common methods
    and attributes.
    """

    def __init__(self, cpc, profile_type):
        """
        Parameters:

          cpc (:class:`~zhmcclient.Cpc`):
            CPC defining the scope for this manager object.

          profile_type (string):
            Controls which type of Activation Profiles
            this manager returns.

            * If `reset`, this manager returns Reset Activation Profiles.
            * If `image`, this manager returns Image Activation Profiles.
            * If `load`, this manager returns Load Activation Profiles.
        """
        super(ActivationProfileManager, self).__init__(cpc)
        self._profile_type = profile_type

    @property
    def cpc(self):
        """
        :class:`~zhmcclient.Cpc`: Parent object (CPC) defining the scope for
        this manager object.
        """
        return self._parent

    @property
    def profile_type(self):
        """
        Returns type of Activation Profiles:
          * If `reset`, this manager returns Reset Activation Profiles.
          * If `image`, this manager returns Image Activation Profiles.
          * If `load`, this manager returns Load Activation Profiles.
        """
        return self._profile_type

    @_log_call
    def list(self, full_properties=False):
        """
        List the Activation Profiles in scope of this manager object.

        Parameters:

          full_properties (bool):
            Controls whether the full set of resource properties should be
            retrieved, vs. only the short set as returned by the list
            operation.

        Returns:

          : A list of :class:`~zhmcclient.ActivationProfile` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        cpc_uri = self.cpc.get_property('object-uri')
        activation_profile = self._profile_type + '-activation-profiles'
        profiles_res = self.session.get(cpc_uri + '/' + activation_profile)
        profile_list = []
        if profiles_res:
            profile_items = profiles_res[self._profile_type +
                                         '-activation-profiles']
            for profile_props in profile_items:
                profile = ActivationProfile(self, profile_props['element-uri'],
                                            profile_props)
                if full_properties:
                    profile.pull_full_properties()
                profile_list.append(profile)
        return profile_list


class ActivationProfile(BaseResource):
    """
    Representation of an Activation Profile.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.
    """

    def __init__(self, manager, uri, properties):
        """
        Parameters:

          manager (:class:`~zhmcclient.ActivationProfileManager`):
            Manager object for this resource.

          uri (string):
            Canonical URI path of the Activation Profile object.

          properties (dict):
            Properties to be set for this resource object.
            See initialization of :class:`~zhmcclient.BaseResource` for
            details.
        """
        assert isinstance(manager, ActivationProfileManager)
        super(ActivationProfile, self).__init__(manager, uri, properties)

    def update_properties(self, properties):
        """
        Updates one or more of the writable properties of
        an activation profile with the specified resource properties.

        Parameters:

          properties (dict): Updated properties for the activation profile.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        profile_uri = self.get_property('element-uri')
        self.manager.session.post(profile_uri, body=properties)
