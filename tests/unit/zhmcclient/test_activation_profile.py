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
Unit tests for _activation_profile module.
"""


import copy
import re
import logging
import pytest

from zhmcclient import Client, ActivationProfile
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources, assert_blanked_in_message


class TestActivationProfile:
    """
    All tests for the ActivationProfile and ActivationProfileManager classes.
    """

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Set up a faked session, and add a faked CPC in classic mode,
        and add two faked activation profiles of each type.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'fake-cpc1-oid',
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (classic mode)',
            'status': 'active',
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'iml-mode': 'lpar',
        })
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

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
            'ipl-address': '0010',
        })
        self.faked_image_ap_2 = self.faked_cpc.image_activation_profiles.add({
            # element-uri is set up automatically
            'name': 'iap_2',
            'parent': self.faked_cpc.uri,
            'class': 'image-activation-profile',
            'description': 'IAP #2',
            'ipl-address': '0010',
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
    def test_profilemanager_initial_attrs(self, profile_type):
        """Test initial attributes of ActivationProfileManager."""

        mgr_attr = profile_type + '_activation_profiles'
        profile_mgr = getattr(self.cpc, mgr_attr)

        # Verify all public properties of the manager object
        assert profile_mgr.resource_class == ActivationProfile
        assert profile_mgr.session == self.session
        assert profile_mgr.parent == self.cpc
        assert profile_mgr.cpc == self.cpc
        assert profile_mgr.profile_type == profile_type

    # TODO: Test for ActivationProfileManager.__repr__()

    @pytest.mark.parametrize(
        "profile_type", ['reset', 'image', 'load']
    )
    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            ({},
             ['name', 'element-uri']),
            (dict(full_properties=False),
             ['name', 'element-uri']),
            (dict(full_properties=True),
             None),
        ]
    )
    def test_profilemanager_list_full_properties(
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
    def test_profilemanager_list_filter_args(
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

    @pytest.mark.parametrize(
        "list_kwargs, prop_names", [
            ({},
             ['element-uri', 'name']),
            (dict(additional_properties=[]),
             ['element-uri', 'name']),
            (dict(additional_properties=['description']),
             ['element-uri', 'name', 'description']),
            (dict(additional_properties=['description', 'ipl-address']),
             ['element-uri', 'name', 'description', 'ipl-address']),
            (dict(additional_properties=['ssc-host-name']),
             ['element-uri', 'name', 'ssc-host-name']
             # ssc-host-name is not on every image profile
             ),
        ]
    )
    def test_profilemanager_list_add_props(
            self, list_kwargs, prop_names):
        """
        Test ActivationProfileManager.list() for image profiles with
        additional_properties.
        """
        mgr_attr = 'image_activation_profiles'
        profile_mgr = getattr(self.cpc, mgr_attr)

        # Execute the code to be tested
        profiles = profile_mgr.list(**list_kwargs)

        exp_faked_profiles = [self.faked_image_ap_1, self.faked_image_ap_2]

        assert_resources(profiles, exp_faked_profiles, prop_names)

    # TODO: Test for initial ActivationProfile attributes

    def test_profile_repr(self):
        """Test ActivationProfile.__repr__()."""

        # We test __repr__() just for reset activation profiles, because the
        # ActivationProfile class is the same for all profile types and we know
        # that __repr__() does not depend on the profile type.
        profile_mgr = self.cpc.reset_activation_profiles
        reset_ap = profile_mgr.find(name='rap_1')

        # Execute the code to be tested
        repr_str = repr(reset_ap)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf'^{reset_ap.__class__.__name__}\s+at\s+'
            rf'0x{id(reset_ap):08x}\s+\(\\n.*',
            repr_str)

    @pytest.mark.parametrize(
        "profile_type", ['reset', 'image', 'load']
    )
    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New profile description'},
            {'description': ''},
            {'ssc-network-info': {
                'chpid': '1a',
                'port': 0,
                'ipaddr-type': 'dhcp',
                'vlan-id': None,
                'static-ip-info': None,
            }},
            {'group-profile-uri': None},
            {'zaware-gateway-info': None},
            {'ssc-master-pw': 'bla', 'zaware-master-pw': 'bla'},
        ]
    )
    def test_profile_update_properties(self, caplog, input_props, profile_type):
        """Test ActivationProfile.update_properties()."""

        logger_name = "zhmcclient.api"
        caplog.set_level(logging.DEBUG, logger=logger_name)

        mgr_attr = profile_type + '_activation_profiles'
        profile_mgr = getattr(self.cpc, mgr_attr)

        profile = profile_mgr.list()[0]

        profile.pull_full_properties()
        saved_properties = copy.deepcopy(profile.properties)

        # Execute the code to be tested
        profile.update_properties(properties=input_props)

        # Get its API call log record
        call_record = caplog.records[-2]

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in profile.properties
            prop_value = profile.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        profile.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in profile.properties
            prop_value = profile.properties[prop_name]
            assert prop_value == exp_prop_value

        # Verify the API call log record for blanked-out properties.
        assert_blanked_in_message(
            call_record.message, input_props,
            ['ssc-master-pw', 'zaware-master-pw'])
