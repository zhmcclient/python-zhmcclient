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
Unit tests for _client module.
"""

from __future__ import absolute_import, print_function

import unittest
import requests_mock

from zhmcclient import Session, Client


class ClientTests(unittest.TestCase):
    """All tests for Client classes."""

    def setUp(self):
        self.session = Session('fake-host')
        self.client = Client(self.session)
        with requests_mock.mock() as m:
            # Because logon is deferred until needed, we perform it
            # explicitly in order to keep mocking in the actual test simple.
            m.post('/api/sessions', json={'api-session': 'fake-session-id'})

    def tearDown(self):
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)

    def test_init(self):
        """Test Initialization of Client class."""
        self.assertTrue(self.client.session is self.session)

    def test_version_info_ok(self):
        """
        Test successful version_info().
        """
        with requests_mock.mock() as m:
            result = {
                'hmc-name': 'FAKEHMC1',
                'hmc-version': '2.13.1',
                'api-minor-version': 7,
                'api-features': ['internal-get-files-from-se'],
                'api-major-version': 1
            }
            m.get('/api/version', json=result)

            vi = self.client.version_info()
            self.assertEqual(vi[0], result['api-major-version'])
            self.assertEqual(vi[1], result['api-minor-version'])

    def test_query_api_version_ok(self):
        """
        Test successful query_api_version().
        """
        with requests_mock.mock() as m:
            result = {
                'hmc-name': 'FAKEHMC1',
                'hmc-version': '2.13.1',
                'api-minor-version': 7,
                'api-features': ['internal-get-files-from-se'],
                'api-major-version': 1
            }
            m.get('/api/version', json=result)

            api_version = self.client.query_api_version()
            vi = self.client.version_info()
            self.assertEqual(vi[0], api_version['api-major-version'])
            self.assertEqual(vi[1], api_version['api-minor-version'])


if __name__ == '__main__':
    unittest.main()
