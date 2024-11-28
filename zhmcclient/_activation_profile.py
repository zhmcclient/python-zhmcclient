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


import copy
import warnings

from ._manager import BaseManager
from ._resource import BaseResource
from ._logging import logged_api_call
from ._utils import RC_RESET_ACTIVATION_PROFILE, RC_IMAGE_ACTIVATION_PROFILE, \
    RC_LOAD_ACTIVATION_PROFILE

__all__ = ['ActivationProfileManager', 'ActivationProfile']

# Resource class names, by profile type:
ACTIVATION_PROFILE_CLASSES = {
    'reset': RC_RESET_ACTIVATION_PROFILE,
    'image': RC_IMAGE_ACTIVATION_PROFILE,
    'load': RC_LOAD_ACTIVATION_PROFILE,
}


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

    HMC/SE version requirements: None
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

        try:
            activation_profile_class = ACTIVATION_PROFILE_CLASSES[profile_type]
        except KeyError:
            raise ValueError(f"Unknown activation profile type: {profile_type}")

        super().__init__(
            resource_class=ActivationProfile,
            class_name=activation_profile_class,
            session=cpc.manager.session,
            parent=cpc,
            base_uri=f'{cpc.uri}/{profile_type}-activation-profiles',
            oid_prop='name',  # This is an exception!
            uri_prop='element-uri',
            name_prop='name',
            query_props=query_props,
            supports_properties=True)

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
    # pylint: disable=arguments-differ
    def list(self, full_properties=False, filter_args=None,
             additional_properties=None):
        """
        List the Activation Profiles of this CPC, of the profile type
        managed by this object.

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

        HMC/SE version requirements: None

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

          additional_properties (list of string):
            List of property names that are to be returned in addition to the
            default properties.

            This parameter requires HMC 2.16.0 or higher, and is supported
            only for image profiles.

        Returns:

          : A list of :class:`~zhmcclient.ActivationProfile` objects.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        result_prop = self._profile_type + '-activation-profiles'
        list_uri = f'{self.cpc.uri}/{result_prop}'
        if self._profile_type != 'image' and additional_properties is not None:
            raise TypeError(
                f"list() for {self._profile_type} profiles does not support "
                "'additional_properties' parameter")
        return self._list_with_operation(
            list_uri, result_prop, full_properties, filter_args,
            additional_properties)

    @logged_api_call(blanked_properties=['ssc-master-pw', 'zaware-master-pw'],
                     properties_pos=1)
    def create(self, properties):
        """
        Create and configure an Activation Profiles on this CPC, of the profile
        type managed by this object.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "create-delete-activation-profiles"

        Authorization requirements:

        * Object-access permission to this CPC.
        * Task permission to the "Customize/Delete Activation Profiles" task.

        Parameters:

          properties (dict): Initial property values.
            Allowable properties are defined in section 'Request body contents'
            in section 'Create Reset/Image/Load Activation Profile' in the
            :term:`HMC API` book.

            Note that the input profile name for creation must be provided in
            property 'profile-name', even though it shows up on the created
            resource in property 'name'. This applies to all three types of
            activation profiles.

        Returns:

          ActivationProfile:
            The resource object for the new Activation Profile.
            The object will have its 'element-uri' property set, and will also
            have the input properties set.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        ap_selector = self._profile_type + '-activation-profiles'
        uri = f'{self.cpc.uri}/{ap_selector}'

        result = self.session.post(uri, body=properties)

        # The "Create ... Activation Profile" operations do not return the
        # resource URI, so we construct it ourselves. Also, these operations
        # specify the profile name in input property 'profile-name'.
        if result is not None:
            warnings.warn(
                f"The Create {self._profile_type} Activation Profile operation "
                f"now has response data with properties: {result.keys()!r}",
                UserWarning)
        name = properties['profile-name']
        uri = f'{uri}/{name}'

        props = copy.deepcopy(properties)
        props[self._uri_prop] = uri
        profile = ActivationProfile(self, uri, name, props)
        self._name_uri_cache.update(name, uri)
        return profile


class ActivationProfile(BaseResource):
    """
    Representation of an :term:`Activation Profile` of a particular type.

    Derived from :class:`~zhmcclient.BaseResource`; see there for common
    methods and attributes.

    Objects of this class are not directly created by the user; they are
    returned from creation or list functions on their manager object
    (in this case, :class:`~zhmcclient.ActivationProfileManager`).

    HMC/SE version requirements: None
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
        assert isinstance(manager, ActivationProfileManager), (
            "ActivationProfile init: Expected manager type "
            f"{ActivationProfileManager}, got {type(manager)}")
        super().__init__(manager, uri, name, properties)

    @logged_api_call
    def delete(self):
        """
        Delete this Activation Profile.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "create-delete-activation-profiles"

        Authorization requirements:

        * Task permission to the "Customize/Delete Activation Profiles" task.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        # pylint: disable=protected-access
        self.manager.session.delete(self.uri, resource=self)
        self.manager._name_uri_cache.delete(
            self.get_properties_local(self.manager._name_prop, None))
        self.cease_existence_local()

    @logged_api_call(blanked_properties=['ssc-master-pw', 'zaware-master-pw'],
                     properties_pos=1)
    def update_properties(self, properties):
        """
        Update writeable properties of this Activation Profile.

        This method serializes with other methods that access or change
        properties on the same Python object.

        HMC/SE version requirements: None

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
        # pylint: disable=protected-access
        self.manager.session.post(self.uri, resource=self, body=properties)
        # Attempts to change the 'name' property will be rejected by the HMC,
        # so we don't need to update the name-to-URI cache.
        assert self.manager._name_prop not in properties
        self.update_properties_local(copy.deepcopy(properties))

    @logged_api_call
    def assign_certificate(self, certificate):
        """
        Assigns a :term:`Certificate` to this Image Activation Profile.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "secure-boot-with-certificates".

        Authorization requirements:

        * Object-access permission to this Activation Profile.
        * Object-access permission to the specified certificate.
        * Task permission to the "Assign Secure Boot Certificates" task.

        Parameters:

          certificate (:class:`~zhmcclient.Certificate`):
            Certificate to be assigned. The certificate must not currently
            be assigned to this LPAR.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'certificate-uri': certificate.uri}
        self.manager.session.post(
            self.uri + '/operations/assign-certificate', resource=self,
            body=body)

    @logged_api_call
    def unassign_certificate(self, certificate):
        """
        Unassign a :term:`Certificate` from this Image Activation Profile.

        HMC/SE version requirements:

        * :ref:`API feature <API features>` "secure-boot-with-certificates".

        Authorization requirements:

        * Object-access permission to this Image Activation Profile.
        * Object-access permission to the specified certificate.
        * Task permission to the "Assign Secure Boot Certificates" task.

        Parameters:

          certificate (:class:`~zhmcclient.Certificate`):
            Certificate to be unassigned. The certificate must currently be
            assigned to this LPAR.

        Raises:

          :exc:`~zhmcclient.HTTPError`
          :exc:`~zhmcclient.ParseError`
          :exc:`~zhmcclient.AuthError`
          :exc:`~zhmcclient.ConnectionError`
        """
        body = {'certificate-uri': certificate.uri}
        self.manager.session.post(
            self.uri + '/operations/unassign-certificate', resource=self,
            body=body)
