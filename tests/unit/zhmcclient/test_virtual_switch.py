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
Unit tests for _virtual_switch module.
"""


import re
# FIXME: Migrate requests_mock to zhmcclient_mock.
import requests_mock

from zhmcclient import Session, Client, Nic


class TestVirtualSwitch:
    """All tests for VirtualSwitch and VirtualSwitchManager classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = Session('vswitch-dpm-host', 'vswitch-user',
                               'vswitch-pwd')
        self.client = Client(self.session)
        with requests_mock.mock() as m:
            # Because logon is deferred until needed, we perform it
            # explicitly in order to keep mocking in the actual test simple.
            m.post(
                '/api/sessions', json={
                    'api-session': 'test-session-id',
                    'notification-topic': 'test-obj-topic.1',
                    'job-notification-topic': 'test-job-topic.1',
                    'session-credential':
                        'un8bu462g37aw9j0o8pltontz3szt35jh4b1qe2toxt6fkhl4',
                })
            m.get(
                '/api/version', json={
                    'api-major-version': 4,
                    'api-minor-version': 10,
                })
            self.session.logon()

        self.cpc_mgr = self.client.cpcs
        with requests_mock.mock() as m:
            result = {
                'cpcs': [
                    {
                        'object-uri': '/api/cpcs/vswitch-cpc-id-1',
                        'name': 'CPC',
                        'status': 'service-required',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)

            cpcs = self.cpc_mgr.list()
            self.cpc = cpcs[0]

    def teardown_method(self):
        """
        Teardown that is called by pytest after each test method.
        """
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)
            self.session.logoff()

    def test_init(self):
        """Test __init__() on VirtualSwitchManager instance in CPC."""
        vswitch_mgr = self.cpc.virtual_switches
        assert vswitch_mgr.cpc == self.cpc

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties
        on VirtualSwitchManager instance in CPC.
        """
        vswitch_mgr = self.cpc.virtual_switches
        with requests_mock.mock() as m:
            result = {
                'virtual-switches': [
                    {
                        'name': 'VSWITCH1',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id1',
                        'type': 'osd'
                    },
                    {
                        'name': 'VSWITCH2',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id2',
                        'type': 'hpersockets'
                    }
                ]
            }

            m.get('/api/cpcs/vswitch-cpc-id-1/virtual-switches', json=result)

            vswitches = vswitch_mgr.list(full_properties=False)

            assert len(vswitches) == len(result['virtual-switches'])
            for idx, vswitch in enumerate(vswitches):
                assert vswitch.properties == \
                    result['virtual-switches'][idx]
                assert vswitch.uri == \
                    result['virtual-switches'][idx]['object-uri']
                assert not vswitch.full_properties
                assert vswitch.manager == vswitch_mgr

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on
        VirtualSwitchManager instance in CPC.
        """
        vswitch_mgr = self.cpc.virtual_switches
        with requests_mock.mock() as m:
            result = {
                'virtual-switches': [
                    {
                        'name': 'VSWITCH1',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id1',
                        'type': 'osd'
                    },
                    {
                        'name': 'VSWITCH2',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id2',
                        'type': 'hipersockets'
                    }
                ]
            }

            m.get('/api/cpcs/vswitch-cpc-id-1/virtual-switches', json=result)

            mock_result_get_bulk = [
                {
                    'id': '1',
                    'status': 200,
                    'body': {
                        'name': 'VSWITCH1',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id1',
                        'type': 'osd',
                        'class': 'virtual-switch',
                        'description': 'Test VirtualSwitch',
                        'more_properties': 'bliblablub'
                    }
                },
                {
                    'id': '2',
                    'status': 200,
                    'body': {
                        'name': 'VSWITCH2',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id2',
                        'type': 'hipersockets',
                        'class': 'virtual-switch',
                        'description': 'Test VirtualSwitch',
                        'more_properties': 'bliblablub'
                    }
                }
            ]
            m.post('/api/services/aggregation/submit',
                   json=mock_result_get_bulk)

            vswitches = vswitch_mgr.list(full_properties=True)

            assert len(vswitches) == len(result['virtual-switches'])
            for idx, vswitch in enumerate(vswitches):
                assert vswitch.properties['name'] == \
                    result['virtual-switches'][idx]['name']
                assert vswitch.uri == \
                    result['virtual-switches'][idx]['object-uri']
                assert vswitch.full_properties
                assert vswitch.manager == vswitch_mgr

    def test_list_add_props(self):
        """
        Test successful list() with additional_properties.
        """
        vswitch_mgr = self.cpc.virtual_switches
        with requests_mock.mock() as m:
            result = {
                'virtual-switches': [
                    {
                        'name': 'VSWITCH1',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id1',
                        'type': 'osd',
                        'port': 1,
                    },
                    {
                        'name': 'VSWITCH2',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id2',
                        'type': 'hipersockets',
                        'port': 0,
                    }
                ]
            }

            m.get('/api/cpcs/vswitch-cpc-id-1/virtual-switches', json=result)

            vswitches = vswitch_mgr.list(additional_properties=['port'])

            assert len(vswitches) == len(result['virtual-switches'])
            for idx, vswitch in enumerate(vswitches):
                assert vswitch.properties['name'] == \
                    result['virtual-switches'][idx]['name']
                assert vswitch.uri == \
                    result['virtual-switches'][idx]['object-uri']
                assert 'port' in vswitch.properties
                assert vswitch.properties['port'] == \
                    result['virtual-switches'][idx]['port']
                assert vswitch.manager == vswitch_mgr

    def test_update_properties(self):
        """
        This tests the 'Update VirtualSwitch Properties' operation.
        """
        vswitch_mgr = self.cpc.virtual_switches
        with requests_mock.mock() as m:
            result = {
                'virtual-switches': [
                    {
                        'name': 'VSWITCH1',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id1',
                        'type': 'osd'
                    },
                    {
                        'name': 'VSWITCH2',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id2',
                        'type': 'hpersockets'
                    }
                ]
            }
            m.get('/api/cpcs/vswitch-cpc-id-1/virtual-switches', json=result)

            vswitches = vswitch_mgr.list(full_properties=False)
            vswitch = vswitches[0]
            m.post("/api/virtual-switches/fake-vswitch-id1", status_code=204)
            vswitch.update_properties(properties={})

    def test_get_connected_nics(self):
        """
        This tests the `get_connected_nics()` method.
        """
        vswitch_mgr = self.cpc.virtual_switches
        with requests_mock.mock() as m:
            result = {
                'virtual-switches': [
                    {
                        'name': 'VSWITCH1',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id1',
                        'type': 'osd'
                    },
                    {
                        'name': 'VSWITCH2',
                        'object-uri': '/api/virtual-switches/fake-vswitch-id2',
                        'type': 'hpersockets'
                    }
                ]
            }
            m.get('/api/cpcs/vswitch-cpc-id-1/virtual-switches', json=result)

            vswitches = vswitch_mgr.list(full_properties=False)
            vswitch = vswitches[0]
            result = {
                'connected-vnic-uris': [
                    '/api/partitions/fake-part-id1/nics/fake-nic-id1',
                    '/api/partitions/fake-part-id1/nics/fake-nic-id2',
                    '/api/partitions/fake-part-id1/nics/fake-nic-id3'
                ]
            }

            m.get(
                "/api/virtual-switches/fake-vswitch-id1/"
                "operations/get-connected-vnics",
                json=result)

            nics = vswitch.get_connected_nics()

            assert isinstance(nics, list)
            for i, nic in enumerate(nics):
                assert isinstance(nic, Nic)
                nic_uri = result['connected-vnic-uris'][i]
                assert nic.uri == nic_uri
                assert nic.properties['element-uri'] == nic_uri
                m = re.match(r"^/api/partitions/([^/]+)/nics/([^/]+)/?$",
                             nic_uri)
                nic_id = m.group(2)
                assert nic.properties['element-id'] == nic_id
