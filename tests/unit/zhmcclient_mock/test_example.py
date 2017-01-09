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
Example unit test for a user of the zhmcclient package.
"""

from __future__ import absolute_import, print_function

import requests.packages.urllib3
import unittest
import zhmcclient
import zhmcclient_mock


class MyTests(unittest.TestCase):

    def setUp(self):

        self.session = zhmcclient_mock.Session('fake-host', '2.13.1')
        self.session.hmc.add_resources({
            'cpcs': [
                {
                    'properties': {
                        # object-id is auto-generated
                        # object-uri is auto-generated
                        'name': 'cpc_1',
                        'description': 'CPC #1',
                    },
                },
                {
                    'properties': {
                        # object-id is auto-generated
                        # object-uri is auto-generated
                        'name': 'cpc_2',
                        'description': 'CPC #2',
                    },
                },
            ]
        })
        self.client = zhmcclient.Client(self.session)

    def test_initial(self):

        self.assertEqual(self.session.host, 'fake-host')
        #self.assertEqual(self.client.version_info(), (2, 13))

    def test_list(self):

        # the function to be tested:
        cpcs = self.client.cpcs.list()

        self.assertEqual(len(cpcs), 2)

        self.assertEqual(cpcs[0].uri, '/api/cpcs/%s' % cpcs[0]['object-id'])
        self.assertEqual(cpcs[0].name, 'cpc_1')
        self.assertEqual(cpcs[0].get_property('name'), 'cpc_1')
        self.assertEqual(cpcs[0].get_property('description'), 'CPC #1')

        self.assertEqual(cpcs[1].uri, '/api/cpcs/%s' % cpcs[1]['object-id'])
        self.assertEqual(cpcs[1].name, 'cpc_2')
        self.assertEqual(cpcs[1].get_property('name'), 'cpc_2')
        self.assertEqual(cpcs[1].get_property('description'), 'CPC #2')

if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    unittest.main()
