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
Unit tests for `tests/function/_hmcinfo.py` module.
"""

import unittest
from datetime import datetime
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock
import requests_mock
import six
import pytz

from zhmcclient import Session, Client
from tests.function._hmcinfo import HMCInfo  # tests in zhmcclient


class HMCInfoTests(unittest.TestCase):
    """All tests for HMCInfo class."""

    def setUp(self):

        self.exp_hmc = "myhmc"
        self.exp_userid = "myuser"
        self.hmcinfo = HMCInfo(self.exp_hmc, self.exp_userid)

        self.session = Session('fake-host', 'fake-user', 'fake-id')
        self.client = Client(self.session)
        with requests_mock.mock() as m:
            # Because logon is deferred until needed, we perform it
            # explicitly in order to keep mocking in the actual test simple.
            m.post('/api/sessions', json={'api-session': 'fake-session-id'})
            self.session.logon()

    def test_init(self):
        """Test initialization of HMCInfo."""

        data = self.hmcinfo._data  # pylint: disable=protected-access

        hmc = data['hmc']
        assert hmc == self.exp_hmc

        userid = data['userid']
        assert userid == self.exp_userid

        created = data['created']
        assert isinstance(created, str) is True

        operations = data['operations']
        assert isinstance(operations, OrderedDict) is True
        assert len(operations) == 0

    def test_add_op_1(self):
        """Test HMCInfo.add_op() with sucessful GET operation."""

        method = 'GET'
        uri = '/api/version'
        error = None
        request_body = None
        response_body = {'api-minor-version': '1'}  # no need to be realistic

        self.hmcinfo.add_op(method, uri, error, request_body, response_body)

        key = 'get /api/version'
        data = self.hmcinfo._data  # pylint: disable=protected-access
        op = data['operations'][key]

        assert isinstance(op, OrderedDict) is True
        assert op['method'] == method
        assert op['uri'] == uri
        assert op['error'] == error
        assert op['request_body'] == request_body
        assert op['response_body'] == response_body

    def test_record_op_1(self):
        """Test HMCInfo.record_op() with sucessful GET operation."""

        method = 'GET'
        uri = '/api/cpcs'
        error = None
        request_body = None
        exp_response_body = {
            'cpcs': [
                {
                    'object-uri': '/api/cpcs/fake-cpc-id-1',
                    'name': 'P0ZHMP02',
                    'status': 'service-required',
                }
            ]
        }

        with requests_mock.mock() as m:
            m.get(uri, json=exp_response_body)
            self.hmcinfo.add_op = MagicMock(return_value=None)

            response_body = self.hmcinfo.record_op(self.session, method, uri,
                                                   request_body)

            self.hmcinfo.add_op.assert_called_with(method.lower(), uri, error,
                                                   None, exp_response_body)
            assert response_body == exp_response_body

    def test_record_get_1(self):
        """Test HMCInfo.record_get() with sucessful GET operation."""

        uri = '/api/cpcs'
        exp_response_body = {
            'cpcs': [
                {
                    'object-uri': '/api/cpcs/fake-cpc-id-1',
                    'name': 'P0ZHMP02',
                    'status': 'service-required',
                }
            ]
        }

        self.hmcinfo.record_op = MagicMock(return_value=exp_response_body)

        response_body = self.hmcinfo.record_get(self.session, uri)

        self.hmcinfo.record_op.assert_called_with(self.session, 'get', uri,
                                                  None)
        assert response_body == exp_response_body

    def test_get_op_1(self):
        """Test HMCInfo.get_op() with existing operation."""

        method = 'GET'
        uri = '/api/version'
        error = None
        request_body = None
        response_body = {'api-minor-version': '1'}  # no need to be realistic

        self.hmcinfo.add_op(method, uri, error, request_body, response_body)

        op = self.hmcinfo.get_op(method, uri)

        data = self.hmcinfo._data  # pylint: disable=protected-access
        key = 'get /api/version'
        assert op == data['operations'][key]

    def test_get_op_2(self):
        """Test HMCInfo.get_op() with non-existing operation."""

        method = 'GET'
        uri = '/api/version'
        error = None
        request_body = None
        response_body = {'api-minor-version': '1'}  # no need to be realistic

        self.hmcinfo.add_op(method, uri, error, request_body, response_body)

        op = self.hmcinfo.get_op(method, uri + 'XX')

        assert op is None

    def test_dump(self):
        """Test HMCInfo.dump() with two operations recorded."""

        self.hmcinfo.add_op(
            'GET', '/api/version', None, None,
            OrderedDict([
                ('api-minor-version', '1'),
            ])
        )
        self.hmcinfo.add_op(
            'GET', '/api/cpcs', None, None,
            OrderedDict([
                ('cpcs', [
                    OrderedDict([
                        ('status', 'service-required'),
                        ('object-uri', '/api/cpcs/fake-cpc-id-1'),
                        ('name', 'P0ZHMP02'),
                    ]),
                ])
            ])
        )

        data = self.hmcinfo._data  # pylint: disable=protected-access
        exp_dump = u"""{
  "hmc": "%s",
  "userid": "%s",
  "created": "%s",
  "operations": {
    "get /api/version": {
      "method": "GET",
      "uri": "/api/version",
      "error": null,
      "request_body": null,
      "response_body": {
        "api-minor-version": "1"
      }
    },
    "get /api/cpcs": {
      "method": "GET",
      "uri": "/api/cpcs",
      "error": null,
      "request_body": null,
      "response_body": {
        "cpcs": [
          {
            "status": "service-required",
            "object-uri": "/api/cpcs/fake-cpc-id-1",
            "name": "P0ZHMP02"
          }
        ]
      }
    }
  }
}""" % (data['hmc'], data['userid'], data['created'])

        fp = six.StringIO()

        self.hmcinfo.dump(fp)

        actual_dump = fp.getvalue()
        # Remove trailing blanks that are being produced:
        actual_dump = actual_dump.replace(" \n", "\n")
        assert actual_dump == exp_dump

    def test_load(self):
        """Test HMCInfo.load() with two operations recorded."""

        hmc = 'myhmc'
        userid = 'myuserid'
        created = datetime.now(pytz.utc).isoformat()

        load_str = u"""{
  "hmc": "%s",
  "userid": "%s",
  "created": "%s",
  "operations": {
    "get /api/version": {
      "method": "GET",
      "uri": "/api/version",
      "error": null,
      "request_body": null,
      "response_body": {
        "api-minor-version": "1"
      }
    },
    "get /api/cpcs": {
      "method": "GET",
      "uri": "/api/cpcs",
      "error": null,
      "request_body": null,
      "response_body": {
        "cpcs": [
          {
            "status": "service-required",
            "object-uri": "/api/cpcs/fake-cpc-id-1",
            "name": "P0ZHMP02"
          }
        ]
      }
    }
  }
}""" % (hmc, userid, created)

        load_input = six.StringIO(load_str)

        self.hmcinfo.load(load_input)

        data = self.hmcinfo._data  # pylint: disable=protected-access
        assert data['hmc'] == hmc
        assert data['userid'] == userid
        assert data['created'] == created

        ops = data['operations']
        assert len(ops) == 2

        op = ops["get /api/version"]
        assert op["method"] == 'GET'
        assert op["uri"] == '/api/version'
        assert op["error"] is None
        assert op["request_body"] is None
        assert op["response_body"] == OrderedDict([
            ('api-minor-version', '1'),
        ])

        op = ops["get /api/cpcs"]
        assert op["method"] == 'GET'
        assert op["uri"] == '/api/cpcs'
        assert op["error"] is None
        assert op["request_body"] is None
        assert op["response_body"] == OrderedDict([
            ('cpcs', [
                OrderedDict([
                    ('status', 'service-required'),
                    ('object-uri', '/api/cpcs/fake-cpc-id-1'),
                    ('name', 'P0ZHMP02'),
                ]),
            ])
        ])
