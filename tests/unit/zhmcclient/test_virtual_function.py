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
Unit tests for _virtual_function module.
"""


# FIXME: Migrate requests_mock to zhmcclient_mock.
import requests_mock

from zhmcclient import Session, Client, VirtualFunction


class TestVirtualFunction:
    """
    All tests for VirtualFunction and VirtualFunctionManager classes.
    """

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = Session('test-dpm-host', 'test-user', 'test-id')
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
                        'object-uri': '/api/cpcs/fake-cpc-id-1',
                        'name': 'CPC1',
                        'status': '',
                    }
                ]
            }
            m.get('/api/cpcs', json=result)
#            self.cpc = self.cpc_mgr.find(name="CPC1", full_properties=False)
            cpcs = self.cpc_mgr.list()
            self.cpc = cpcs[0]

        partition_mgr = self.cpc.partitions
        with requests_mock.mock() as m:
            result = {
                'partitions': [
                    {
                        'status': 'active',
                        'object-uri': '/api/partitions/fake-part-id-1',
                        'name': 'PART1'
                    },
                    {
                        'status': 'stopped',
                        'object-uri': '/api/partitions/fake-part-id-2',
                        'name': 'PART2'
                    }
                ]
            }

            m.get('/api/cpcs/fake-cpc-id-1/partitions', json=result)

            mock_result_get_bulk = [
                {
                    'id': '1',
                    'status': 200,
                    'body': {
                        'status': 'active',
                        'object-uri': '/api/partitions/fake-part-id-1',
                        'name': 'PART1',
                        'description': 'Test Partition',
                        'more_properties': 'bliblablub',
                        'virtual-function-uris': [
                            '/api/partitions/fake-part-id-1/virtual-functions/'
                            'fake-vf-id-1',
                            '/api/partitions/fake-part-id-1/virtual-functions/'
                            'fake-vf-id-2'
                        ]
                    },
                },
                {
                    'id': '2',
                    'status': 200,
                    'body': {
                        'status': 'stopped',
                        'object-uri': '/api/partitions/fake-part-id-2',
                        'name': 'PART2',
                        'description': 'Test Partition',
                        'more_properties': 'bliblablub',
                        'virtual-function-uris': [
                            '/api/partitions/fake-part-id-2/virtual-functions/'
                            'fake-vf-id-1',
                            '/api/partitions/fake-part-id-2/virtual-functions/'
                            'fake-vf-id-2'
                        ]
                    }
                }
            ]
            m.post('/api/services/aggregation/submit',
                   json=mock_result_get_bulk)

            partitions = partition_mgr.list(full_properties=True)
            self.partition = partitions[0]

    def teardown_method(self):
        """
        Teardown that is called by pytest after each test method.
        """
        with requests_mock.mock() as m:
            m.delete('/api/sessions/this-session', status_code=204)
            self.session.logoff()

    def test_init(self):
        """Test __init__() on VirtualFunctionManager instance in Partition."""
        vf_mgr = self.partition.virtual_functions
        assert vf_mgr.partition == self.partition

    def test_list_short_ok(self):
        """
        Test successful list() with short set of properties on
        VirtualFunctionManager instance in partition.
        """
        vf_mgr = self.partition.virtual_functions
        vfs = vf_mgr.list(full_properties=False)

        assert len(vfs) == \
            len(self.partition.properties['virtual-function-uris'])
        for idx, vf in enumerate(vfs):
            assert vf.properties['element-uri'] == \
                self.partition.properties['virtual-function-uris'][idx]
            assert vf.uri == \
                self.partition.properties['virtual-function-uris'][idx]
            assert not vf.full_properties
            assert vf.manager == vf_mgr

    def test_list_full_ok(self):
        """
        Test successful list() with full set of properties on
        VirtualFunctionManager instance in partition.
        """
        vf_mgr = self.partition.virtual_functions

        with requests_mock.mock() as m:

            mock_result_vf1 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'vf1',
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-1',
                'class': 'virtual-function',
                'element-id': 'fake-vf-id-1',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/virtual-functions/'
                  'fake-vf-id-1',
                  json=mock_result_vf1)
            mock_result_vf2 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'vf2',
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-2',
                'class': 'virtual-function',
                'element-id': 'fake-vf-id-2',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/virtual-functions/'
                  'fake-vf-id-2',
                  json=mock_result_vf2)

            vfs = vf_mgr.list(full_properties=True)

            assert len(vfs) == \
                len(self.partition.properties['virtual-function-uris'])
            for idx, vf in enumerate(vfs):
                assert vf.properties['element-uri'] == \
                    self.partition.properties['virtual-function-uris'][idx]
                assert vf.uri == \
                    self.partition.properties['virtual-function-uris'][idx]
                assert vf.full_properties
                assert vf.manager == vf_mgr

    def test_list_filter_name_ok(self):
        """
        Test successful list() with filter arguments using the 'name' property
        on a VirtualFunctionManager instance in a partition.
        """
        vf_mgr = self.partition.virtual_functions

        with requests_mock.mock() as m:

            mock_result_vf1 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'vf1',
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-1',
                'class': 'virtual-function',
                'element-id': 'fake-vf-id-1',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/virtual-functions/'
                  'fake-vf-id-1',
                  json=mock_result_vf1)
            mock_result_vf2 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'vf2',
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-2',
                'class': 'virtual-function',
                'element-id': 'fake-vf-id-2',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/virtual-functions/'
                  'fake-vf-id-2',
                  json=mock_result_vf2)

            filter_args = {'name': 'vf2'}
            vfs = vf_mgr.list(filter_args=filter_args)

            assert len(vfs) == 1
            vf = vfs[0]
            assert vf.name == 'vf2'
            assert vf.uri == \
                '/api/partitions/fake-part-id-1/virtual-functions/' \
                'fake-vf-id-2'
            assert vf.properties['name'] == 'vf2'
            assert vf.properties['element-id'] == 'fake-vf-id-2'
            assert vf.manager == vf_mgr

    def test_list_filter_elementid_ok(self):
        """
        Test successful list() with filter arguments using the 'element-id'
        property on a VirtualFunctionManager instance in a partition.
        """
        vf_mgr = self.partition.virtual_functions

        with requests_mock.mock() as m:

            mock_result_vf1 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'vf1',
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-1',
                'class': 'virtual-function',
                'element-id': 'fake-vf-id-1',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/virtual-functions/'
                  'fake-vf-id-1',
                  json=mock_result_vf1)
            mock_result_vf2 = {
                'parent': '/api/partitions/fake-part-id-1',
                'name': 'vf2',
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-2',
                'class': 'virtual-function',
                'element-id': 'fake-vf-id-2',
                'description': '',
                'more_properties': 'bliblablub'
            }
            m.get('/api/partitions/fake-part-id-1/virtual-functions/'
                  'fake-vf-id-2',
                  json=mock_result_vf2)

            filter_args = {'element-id': 'fake-vf-id-2'}
            vfs = vf_mgr.list(filter_args=filter_args)

            assert len(vfs) == 1
            vf = vfs[0]
            assert vf.name == 'vf2'
            assert vf.uri == \
                '/api/partitions/fake-part-id-1/virtual-functions/' \
                'fake-vf-id-2'
            assert vf.properties['name'] == 'vf2'
            assert vf.properties['element-id'] == 'fake-vf-id-2'
            assert vf.manager == vf_mgr

    def test_create(self):
        """
        This tests the 'Create Virtual Function' operation.
        """
        vf_mgr = self.partition.virtual_functions
        with requests_mock.mock() as m:
            result = {
                'element-uri':
                    '/api/partitions/fake-part-id-1/virtual-functions/'
                    'fake-vf-id-1'
            }
            m.post('/api/partitions/fake-part-id-1/virtual-functions',
                   json=result)

            vf = vf_mgr.create(properties={})

            assert isinstance(vf, VirtualFunction)
            assert vf.properties == result
            assert vf.uri == result['element-uri']

    def test_delete(self):
        """
        This tests the 'Delete Virtual Function' operation.
        """
        vf_mgr = self.partition.virtual_functions
        vfs = vf_mgr.list(full_properties=False)
        vf = vfs[0]
        with requests_mock.mock() as m:
            m.delete('/api/partitions/fake-part-id-1/virtual-functions/'
                     'fake-vf-id-1', status_code=204)
            vf.delete()

    def test_update_properties(self):
        """
        This tests the 'Update Virtual Function Properties' operation.
        """
        vf_mgr = self.partition.virtual_functions
        vfs = vf_mgr.list(full_properties=False)
        vf = vfs[0]
        with requests_mock.mock() as m:
            m.post('/api/partitions/fake-part-id-1/virtual-functions/'
                   'fake-vf-id-1', status_code=204)
            vf.update_properties(properties={})
