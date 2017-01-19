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

        self.session = zhmcclient_mock.Session('fake-host', 'fake-hmc',
                                               '2.13.1', '1.8')
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
        self.assertEqual(self.client.version_info(), (1, 8))

    def test_list(self):

        # the function to be tested:
        cpcs = self.client.cpcs.list()

        self.assertEqual(len(cpcs), 2)

        cpc_1 = cpcs[0]
        cpc_1_oid = cpc_1.uri.split('/')[-1]
        self.assertEqual(cpc_1.uri, '/api/cpcs/%s' % cpc_1_oid)
        self.assertEqual(cpc_1.name, 'cpc_1')
        self.assertEqual(cpc_1.get_property('object-id'), cpc_1_oid)
        self.assertEqual(cpc_1.get_property('object-uri'), cpc_1.uri)
        self.assertEqual(cpc_1.get_property('name'), cpc_1.name)

        cpc_2 = cpcs[1]
        cpc_2_oid = cpc_2.uri.split('/')[-1]
        self.assertEqual(cpc_2.uri, '/api/cpcs/%s' % cpc_2_oid)
        self.assertEqual(cpc_2.name, 'cpc_2')
        self.assertEqual(cpc_2.get_property('object-id'), cpc_2_oid)
        self.assertEqual(cpc_2.get_property('object-uri'), cpc_2.uri)
        self.assertEqual(cpc_2.get_property('name'), cpc_2.name)

    def test_get_properties(self):
        cpcs = self.client.cpcs.list()
        cpc_1 = cpcs[0]

        # the function to be tested:
        cpc_1.pull_full_properties()

        cpc_1_uri = cpc_1.uri
        cpc_1_oid = cpc_1.uri.split('/')[-1]

        self.assertEqual(len(cpc_1.properties), 4)
        self.assertEqual(cpc_1.get_property('object-id'), cpc_1_oid)
        self.assertEqual(cpc_1.get_property('object-uri'), cpc_1_uri)
        self.assertEqual(cpc_1.get_property('name'), 'cpc_1')
        self.assertEqual(cpc_1.get_property('description'), 'CPC #1')


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    unittest.main()
