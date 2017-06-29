#!/usr/bin/env python
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
Unit tests for _activation_profile module.
"""

from __future__ import absolute_import, print_function

import unittest
import copy

from zhmcclient import Client, ActivationProfile
from zhmcclient_mock import FakedSession


class ActivationProfileTests(unittest.TestCase):
    """All tests for ActivationProfile and ActivationProfileManager classes."""

    def assertProfiles(self, profiles, exp_profiles, prop_names):
        self.assertEqual(set([profile.uri for profile in profiles]),
                         set([profile.uri for profile in exp_profiles]))
        for profile in profiles:
            uri = profile.uri
            for exp_profile in exp_profiles:
                if exp_profile.uri == uri:
                    break
            for prop_name in prop_names:
                self.assertEqual(profile.properties[prop_name],
                                 exp_profile.properties[prop_name])

    def setUp(self):
        """
        Set up a CPC with two of each type of activation profiles.

        Because activation profiles cannot be dynamically added, we work
        with a CPC that is initially set up and satisfies the need for all
        tests.
        """
        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'faked-cpc1',
            'parent': None,
            'class': 'cpc',
            'name': 'cpc_1',
            'description': 'CPC #1',
            'status': 'active',
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'iml-mode': 'TBD',
        })
        self.faked_reset_ap_1 = self.faked_cpc.reset_activation_profiles.add({
            'name': 'rap_1',
            'parent': self.faked_cpc.uri,
            'class': 'reset-activation-profile',
            'description': 'RAP #1',
        })
        self.faked_reset_ap_2 = self.faked_cpc.reset_activation_profiles.add({
            'name': 'rap_2',
            'parent': self.faked_cpc.uri,
            'class': 'reset-activation-profile',
            'description': 'RAP #2',
        })
        self.faked_image_ap_1 = self.faked_cpc.image_activation_profiles.add({
            'name': 'iap_1',
            'parent': self.faked_cpc.uri,
            'class': 'image-activation-profile',
            'description': 'IAP #1',
        })
        self.faked_image_ap_2 = self.faked_cpc.image_activation_profiles.add({
            'name': 'iap_2',
            'parent': self.faked_cpc.uri,
            'class': 'image-activation-profile',
            'description': 'IAP #2',
        })
        self.faked_load_ap_1 = self.faked_cpc.load_activation_profiles.add({
            'name': 'lap_1',
            'parent': self.faked_cpc.uri,
            'class': 'load-activation-profile',
            'description': 'LAP #1',
        })
        self.faked_load_ap_2 = self.faked_cpc.load_activation_profiles.add({
            'name': 'lap_2',
            'parent': self.faked_cpc.uri,
            'class': 'load-activation-profile',
            'description': 'LAP #2',
        })
        self.cpc = self.client.cpcs.list()[0]

    def test_resource_repr(self):
        """Test ActivationProfile.__repr__()."""
        # We test just for reset activation profiles, because the class is the
        # same for all profile types and we know that the __repr__() method
        # does not depend on the profile type either.

        reset_ap = ActivationProfile(
            self.cpc.reset_activation_profiles,
            uri=self.cpc.uri + '/reset-activation-profiles/rap-1',
            name='rap #1')

        repr_str = repr(reset_ap)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        self.assertRegexpMatches(
            repr_str,
            r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.format(
                classname=reset_ap.__class__.__name__,
                id=id(reset_ap)))

    def test_manager_initial_attrs(self):
        """Test initial attributes of ActivationProfileManager."""

        reset_ap_mgr = self.cpc.reset_activation_profiles
        self.assertEqual(reset_ap_mgr.cpc, self.cpc)
        self.assertEqual(reset_ap_mgr.profile_type, "reset")

        image_ap_mgr = self.cpc.image_activation_profiles
        self.assertEqual(image_ap_mgr.cpc, self.cpc)
        self.assertEqual(image_ap_mgr.profile_type, "image")

        load_ap_mgr = self.cpc.load_activation_profiles
        self.assertEqual(load_ap_mgr.cpc, self.cpc)
        self.assertEqual(load_ap_mgr.profile_type, "load")

    def test_manager_list_short(self):
        """
        Test ActivationProfileManager.list() with short set of properties.
        """
        # The faked resources are used to define the expected resources and
        # their properties.
        exp_profiles = [self.faked_image_ap_1, self.faked_image_ap_2]
        profile_mgr = self.cpc.image_activation_profiles

        profiles = profile_mgr.list(full_properties=False)

        self.assertProfiles(profiles, exp_profiles,
                            ['name', 'element-uri'])

    def test_manager_list_full(self):
        """
        Test ActivationProfileManager.list() with full set of properties.
        """
        # The faked resources are used to define the expected resources and
        # their properties.
        exp_profiles = [self.faked_reset_ap_1, self.faked_reset_ap_2]
        profile_mgr = self.cpc.reset_activation_profiles

        profiles = profile_mgr.list(full_properties=True)

        self.assertProfiles(profiles, exp_profiles,
                            ['name', 'element-uri', 'class', 'description'])

    def test_manager_list_filter_name(self):
        """
        Test ActivationProfileManager.list() with filtering by name.
        """
        # The faked resources are used to define the expected resources and
        # their properties.
        exp_profiles = [self.faked_reset_ap_2]
        profile_mgr = self.cpc.reset_activation_profiles

        profiles = profile_mgr.list(filter_args={'name': 'rap_2'})

        self.assertProfiles(profiles, exp_profiles,
                            ['name', 'element-uri'])

    def test_manager_list_filter_same(self):
        """
        Test ActivationProfileManager.list() with filtering by a property
        where more than one resource has the same value.
        """
        # The faked resources are used to define the expected resources and
        # their properties.
        exp_profiles = [self.faked_reset_ap_1, self.faked_reset_ap_2]
        profile_mgr = self.cpc.reset_activation_profiles

        profiles = profile_mgr.list(
            filter_args={'class': 'reset-activation-profile'})

        self.assertProfiles(profiles, exp_profiles,
                            ['name', 'element-uri'])

    def test_manager_list_filter_two(self):
        """
        Test ActivationProfileManager.list() with filtering by two properties.
        """
        # The faked resources are used to define the expected resources and
        # their properties.
        exp_profiles = [self.faked_reset_ap_2]
        profile_mgr = self.cpc.reset_activation_profiles

        profiles = profile_mgr.list(
            filter_args={'class': 'reset-activation-profile',
                         'description': 'RAP #2'})

        self.assertProfiles(profiles, exp_profiles,
                            ['name', 'element-uri'])

    def test_resource_update_nothing(self):
        """
        Test ActivationProfile.update_properties() with no properties.
        """
        profile_mgr = self.cpc.load_activation_profiles
        profiles = profile_mgr.list(filter_args={'name': 'lap_1'})
        self.assertEqual(len(profiles), 1)
        profile = profiles[0]

        saved_properties = copy.deepcopy(profile.properties)

        # Method to be tested
        profile.update_properties(properties={})

        # Verify that the properties of the local resource object have not
        # changed
        self.assertEqual(profile.properties, saved_properties)

    def test_resource_update_name(self):
        """
        Test ActivationProfile.update_properties() with 'name' property.
        """
        profile_mgr = self.cpc.load_activation_profiles
        profiles = profile_mgr.list(filter_args={'name': 'lap_1'})
        self.assertEqual(len(profiles), 1)
        profile = profiles[0]

        new_name = "new lap_1"

        # Method to be tested
        profile.update_properties(properties={'name': new_name})

        # Verify that the local resource object reflects the update
        self.assertEqual(profile.properties['name'], new_name)

        # Update the properties of the resource object and verify that the
        # resource object reflects the update
        profile.pull_full_properties()
        self.assertEqual(profile.properties['name'], new_name)

        # List the resource by its new name and verify that it was found
        profiles = profile_mgr.list(filter_args={'name': new_name})
        self.assertEqual(len(profiles), 1)
        profile = profiles[0]
        self.assertEqual(profile.properties['name'], new_name)

    def test_resource_update_not_fetched(self):
        """
        Test ActivationProfile.update_properties() with an existing
        property that has not been fetched into the local resource object.
        """
        profile_mgr = self.cpc.load_activation_profiles
        profiles = profile_mgr.list(filter_args={'name': 'lap_1'})
        self.assertEqual(len(profiles), 1)
        profile = profiles[0]

        # A property that is not in the result of list():
        update_prop_name = 'description'
        update_prop_value = "new description for lap_1"

        # Method to be tested
        profile.update_properties(
            properties={update_prop_name: update_prop_value})

        # Verify that the local resource object reflects the update
        self.assertEqual(profile.properties[update_prop_name],
                         update_prop_value)

        # Update the properties of the resource object and verify that the
        # resource object reflects the update
        profile.pull_full_properties()
        self.assertEqual(profile.properties[update_prop_name],
                         update_prop_value)


if __name__ == '__main__':
    unittest.main()
