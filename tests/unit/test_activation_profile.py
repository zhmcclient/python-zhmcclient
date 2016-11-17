#!/usr/bin/env python
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
Unit tests for _activation_profile module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client


class ActivationProfileTests(unittest.TestCase):
    """All tests for ActivationProfile and ActvationProfileManager classes."""

    def setUp(self):
        self.session = Session('ap-test-host', 'ap-test-user', 'ap-test-id')
        self.client = Client(self.session)
        with requests_mock.mock() as m:
            # Because logon is deferred until needed, we perform it
            # explicitly in order to keep mocking in the actual test simple.
            m.post('/api/sessions', json={'api-session': 'ap-test-session-id'})
            self.session.logon()

        self.cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/ap-test-cpc-id-1',
                        'name': 'APCPC1',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)
            cpcs = self.cpc_mgr.list()
            self.cpc = cpcs[0]

    def tearDown(self):
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)
            self.session.logoff()

    def test_init(self):
        """Test __init__() on ActivationManager instance in CPC."""
        reset_ap_mgr = self.cpc.reset_activation_profiles
        self.assertEqual(reset_ap_mgr.cpc, self.cpc)
        self.assertEqual(reset_ap_mgr.profile_type, "reset")

        image_ap_mgr = self.cpc.image_activation_profiles
        self.assertEqual(image_ap_mgr.cpc, self.cpc)
        self.assertEqual(image_ap_mgr.profile_type, "image")

        load_ap_mgr = self.cpc.load_activation_profiles
        self.assertEqual(load_ap_mgr.cpc, self.cpc)
        self.assertEqual(load_ap_mgr.profile_type, "load")

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties
        on ActivationProfileManager instance in CPC.
        """
        image_mgr = self.cpc.image_activation_profiles
        with requests_mock.mock() as m:
            result = {
                'image-activation-profiles': [
                    {
                        'name': 'LPAR1',
                        'element-uri': '/api/cpcs/fake-element-uri-id-1/'
                                       'image-activation-profiles/LPAR1'
                    },
                    {
                        'name': 'LPAR2',
                        'element-uri': '/api/cpcs/fake-element-uri-id-2/'
                                       'image-activation-profiles/LPAR2'
                    }
                ]
            }

            m.get('/api/cpcs/ap-test-cpc-id-1/image-activation-profiles',
                  json=result)

            profiles = image_mgr.list(full_properties=False)

            self.assertEqual(len(profiles),
                             len(result['image-activation-profiles']))
            for idx, profile in enumerate(profiles):
                self.assertEqual(
                    profile.properties,
                    result['image-activation-profiles'][idx])
                self.assertEqual(
                    profile.uri,
                    result['image-activation-profiles'][idx]['element-uri'])
                self.assertFalse(profile.full_properties)
                self.assertEqual(profile.manager, image_mgr)

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties
        on ActivationProfileManager instance in CPC.
        """
        image_mgr = self.cpc.image_activation_profiles
        with requests_mock.mock() as m:
            result = {
                'image-activation-profiles': [
                    {
                        'name': 'LPAR1',
                        'element-uri': '/api/cpcs/fake-element-uri-id-1/'
                                       'image-activation-profiles/LPAR1'
                    },
                    {
                        'name': 'LPAR2',
                        'element-uri': '/api/cpcs/fake-element-uri-id-2/'
                                       'image-activation-profiles/LPAR2'
                    }
                ]
            }

            m.get('/api/cpcs/ap-test-cpc-id-1/image-activation-profiles',
                  json=result)

            mock_result_part1 = {
                'element-uri': '/api/cpcs/fake-element-uri-id-1/'
                               'image-activation-profiles/LPAR1',
                'name': 'LPAR1',
                'description': 'Image Activation Profile',
                'more_properties': 'bliblablub'
            }
            m.get('/api/cpcs/fake-element-uri-id-1/image-activation-profiles/'
                  'LPAR1',
                  json=mock_result_part1)
            mock_result_part2 = {
                'element-uri': '/api/cpcs/fake-element-uri-id-2/'
                               'image-activation-profiles/LPAR2',
                'name': 'LPAR2',
                'description': 'Image Activation Profile',
                'more_properties': 'bliblablub'
            }
            m.get('/api/cpcs/fake-element-uri-id-2/image-activation-profiles/'
                  'LPAR2',
                  json=mock_result_part2)

            profiles = image_mgr.list(full_properties=True)

            self.assertEqual(len(profiles),
                             len(result['image-activation-profiles']))
            for idx, profile in enumerate(profiles):
                self.assertEqual(
                    profile.properties['name'],
                    result['image-activation-profiles'][idx]['name'])
                self.assertEqual(
                    profile.uri,
                    result['image-activation-profiles'][idx]['element-uri'])
                self.assertTrue(profile.full_properties)
                self.assertEqual(profile.manager, image_mgr)

    def test_update_properties(self):
        """
        This tests the 'Update Activation Profile Properties' operation.
        """
        image_mgr = self.cpc.image_activation_profiles
        with requests_mock.mock() as m:
            result = {
                'image-activation-profiles': [
                    {
                        'name': 'LPAR1',
                        'element-uri': '/api/cpcs/fake-element-uri-id-1/'
                                       'image-activation-profiles/LPAR1'
                    },
                    {
                        'name': 'LPAR2',
                        'element-uri': '/api/cpcs/fake-element-uri-id-2/'
                                       'image-activation-profiles/LPAR2'
                    }
                ]
            }

            m.get('/api/cpcs/ap-test-cpc-id-1/image-activation-profiles',
                  json=result)
            profiles = image_mgr.list(full_properties=False)
            profile = profiles[0]
            m.post(
                '/api/cpcs/fake-element-uri-id-1/image-activation-profiles/'
                'LPAR1',
                json=result)
            status = profile.update_properties(properties={})
            self.assertEqual(status, None)


if __name__ == '__main__':
    unittest.main()
