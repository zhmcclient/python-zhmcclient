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

import pytest
import copy
import re

from zhmcclient import Client, ActivationProfile
from zhmcclient_mock import FakedSession
from .utils import assert_resources


class TestActivationProfile(object):
    """
    All tests for the ActivationProfile and ActivationProfileManager classes.
    """

    def setup_method(self):
        """
        Set up a faked session, and add a faked CPC in classic mode,
        and add two faked activation profiles of each type.
        """
        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'faked-cpc1-oid',
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'faked-cpc1-name',
            'description': 'CPC #1 (classic mode)',
            'status': 'active',
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'iml-mode': 'lpar',
        })
        self.cpc = self.client.cpcs.list()[0]

        self.faked_reset_ap_1 = self.faked_cpc.reset_activation_profiles.add({
            # element-uri is set up automatically
            'name': 'rap_1',
            'parent': self.faked_cpc.uri,
            'class': 'reset-activation-profile',
            'description': 'RAP #1',
        })
        self.faked_reset_ap_2 = self.faked_cpc.reset_activation_profiles.add({
            # element-uri is set up automatically
            'name': 'rap_2',
            'parent': self.faked_cpc.uri,
            'class': 'reset-activation-profile',
            'description': 'RAP #2',
        })
        self.faked_image_ap_1 = self.faked_cpc.image_activation_profiles.add({
            # element-uri is set up automatically
            'name': 'iap_1',
            'parent': self.faked_cpc.uri,
            'class': 'image-activation-profile',
            'description': 'IAP #1',
        })
        self.faked_image_ap_2 = self.faked_cpc.image_activation_profiles.add({
            # element-uri is set up automatically
            'name': 'iap_2',
            'parent': self.faked_cpc.uri,
            'class': 'image-activation-profile',
            'description': 'IAP #2',
        })
        self.faked_load_ap_1 = self.faked_cpc.load_activation_profiles.add({
            # element-uri is set up automatically
            'name': 'lap_1',
            'parent': self.faked_cpc.uri,
            'class': 'load-activation-profile',
            'description': 'LAP #1',
        })
        self.faked_load_ap_2 = self.faked_cpc.load_activation_profiles.add({
            # element-uri is set up automatically
            'name': 'lap_2',
            'parent': self.faked_cpc.uri,
            'class': 'load-activation-profile',
            'description': 'LAP #2',
        })

    @pytest.mark.parametrize(
        "profile_type", ['reset', 'image', 'load']
    )
    def test_manager_initial_attrs(self, profile_type):
        """Test initial attributes of ActivationProfileManager."""

        mgr_attr = profile_type + '_activation_profiles'
        profile_mgr = getattr(self.cpc, mgr_attr)

        assert profile_mgr.resource_class == ActivationProfile
        assert profile_mgr.session == self.session
        assert profile_mgr.parent == self.cpc
        assert profile_mgr.cpc == self.cpc
        assert profile_mgr.profile_type == profile_type

    @pytest.mark.parametrize(
        "profile_type", ['reset', 'image', 'load']
    )
    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(),
             ['name', 'element-uri']),
            (dict(full_properties=False),
             ['name', 'element-uri']),
            (dict(full_properties=True),
             None),
        ]
    )
    def test_manager_list_full_properties(
            self, full_properties_kwargs, prop_names, profile_type):
        """Test ActivationProfileManager.list() with full_properties."""

        mgr_attr = profile_type + '_activation_profiles'
        faked_profile_mgr = getattr(self.faked_cpc, mgr_attr)
        exp_faked_profiles = faked_profile_mgr.list()
        profile_mgr = getattr(self.cpc, mgr_attr)

        # Execute the code to be tested
        profiles = profile_mgr.list(**full_properties_kwargs)

        assert_resources(profiles, exp_faked_profiles, prop_names)

    @pytest.mark.parametrize(
        "profile_type, filter_args, exp_names", [
            ('reset',
             {'name': 'rap_2'},
             ['rap_2']),
            ('reset',
             {'name': '.*rap_1'},
             ['rap_1']),
            ('reset',
             {'name': 'rap_1.*'},
             ['rap_1']),
            ('reset',
             {'name': 'rap_.'},
             ['rap_1', 'rap_2']),
            ('reset',
             {'name': '.ap_1'},
             ['rap_1']),
            ('reset',
             {'name': '.+'},
             ['rap_1', 'rap_2']),
            ('reset',
             {'name': 'rap_1.+'},
             []),
            ('reset',
             {'name': '.+rap_1'},
             []),
            ('image',
             {'name': 'iap_1'},
             ['iap_1']),
            ('image',
             {'name': '.*iap_1'},
             ['iap_1']),
            ('image',
             {'name': 'iap_1.*'},
             ['iap_1']),
            ('image',
             {'name': 'iap_.'},
             ['iap_1', 'iap_2']),
            ('image',
             {'name': '.ap_1'},
             ['iap_1']),
            ('image',
             {'name': '.+'},
             ['iap_1', 'iap_2']),
            ('image',
             {'name': 'iap_1.+'},
             []),
            ('image',
             {'name': '.+iap_1'},
             []),
            ('load',
             {'name': 'lap_2'},
             ['lap_2']),
            ('load',
             {'name': '.*lap_1'},
             ['lap_1']),
            ('load',
             {'name': 'lap_1.*'},
             ['lap_1']),
            ('load',
             {'name': 'lap_.'},
             ['lap_1', 'lap_2']),
            ('load',
             {'name': '.ap_1'},
             ['lap_1']),
            ('load',
             {'name': '.+'},
             ['lap_1', 'lap_2']),
            ('load',
             {'name': 'lap_1.+'},
             []),
            ('load',
             {'name': '.+lap_1'},
             []),
            ('reset',
             {'class': 'reset-activation-profile'},
             ['rap_1', 'rap_2']),
            ('image',
             {'class': 'image-activation-profile'},
             ['iap_1', 'iap_2']),
            ('load',
             {'class': 'load-activation-profile'},
             ['lap_1', 'lap_2']),
            ('reset',
             {'class': 'reset-activation-profile',
              'description': 'RAP #2'},
             ['rap_2']),
            ('image',
             {'class': 'image-activation-profile',
              'description': 'IAP #1'},
             ['iap_1']),
            ('load',
             {'class': 'load-activation-profile',
              'description': 'LAP #2'},
             ['lap_2']),
            ('reset',
             {'description': 'RAP #1'},
             ['rap_1']),
            ('image',
             {'description': 'IAP #2'},
             ['iap_2']),
            ('load',
             {'description': 'LAP #1'},
             ['lap_1']),
        ]
    )
    def test_manager_list_filter_args(
            self, profile_type, filter_args, exp_names):
        """Test ActivationProfileManager.list() with filter_args."""

        mgr_attr = profile_type + '_activation_profiles'
        profile_mgr = getattr(self.cpc, mgr_attr)

        # Execute the code to be tested
        profiles = profile_mgr.list(filter_args=filter_args)

        assert len(profiles) == len(exp_names)
        if exp_names:
            names = [ap.properties['name'] for ap in profiles]
            assert set(names) == set(exp_names)

    def test_resource_repr(self):
        """Test ActivationProfile.__repr__()."""

        # We test __repr__() just for reset activation profiles, because the
        # ActivationProfile class is the same for all profile types and we know
        # that __repr__() does not depend on the profile type.
        reset_ap = self.cpc.reset_activation_profiles.find(name='rap_1')

        # Execute the code to be tested
        repr_str = repr(reset_ap)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=reset_ap.__class__.__name__,
                               id=id(reset_ap)),
                        repr_str)

    def test_resource_update_nothing(self):
        """
        Test ActivationProfile.update_properties() with no properties.
        """

        profile_mgr = self.cpc.load_activation_profiles
        profiles = profile_mgr.list(filter_args={'name': 'lap_1'})
        assert len(profiles) == 1
        profile = profiles[0]

        saved_properties = copy.deepcopy(profile.properties)

        # Execute the code to be tested
        profile.update_properties(properties={})

        # Verify that the properties of the local resource object have not
        # changed
        assert profile.properties == saved_properties

    def test_resource_update_name(self):
        """
        Test ActivationProfile.update_properties() with 'name' property.
        """

        profile_mgr = self.cpc.load_activation_profiles
        profiles = profile_mgr.list(filter_args={'name': 'lap_1'})
        assert len(profiles) == 1
        profile = profiles[0]

        new_name = "new lap_1"

        # Execute the code to be tested
        profile.update_properties(properties={'name': new_name})

        # Verify that the local resource object reflects the update
        assert profile.properties['name'] == new_name

        # Update the properties of the resource object and verify that the
        # resource object reflects the update
        profile.pull_full_properties()
        assert profile.properties['name'] == new_name

        # List the resource by its new name and verify that it was found
        profiles = profile_mgr.list(filter_args={'name': new_name})
        assert len(profiles) == 1
        profile = profiles[0]
        assert profile.properties['name'] == new_name

    def test_resource_update_not_fetched(self):
        """
        Test ActivationProfile.update_properties() with an existing
        property that has not been fetched into the local resource object.
        """

        profile_mgr = self.cpc.load_activation_profiles
        profiles = profile_mgr.list(filter_args={'name': 'lap_1'})
        assert len(profiles) == 1
        profile = profiles[0]

        # A property that is not in the result of list():
        update_prop_name = 'description'
        update_prop_value = "new description for lap_1"

        # Execute the code to be tested
        profile.update_properties(
            properties={update_prop_name: update_prop_value})

        # Verify that the local resource object reflects the update
        assert profile.properties[update_prop_name] == update_prop_value

        # Update the properties of the resource object and verify that the
        # resource object reflects the update
        profile.pull_full_properties()
        assert profile.properties[update_prop_name] == update_prop_value
