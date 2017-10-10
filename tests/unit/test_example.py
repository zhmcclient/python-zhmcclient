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
Example unit test for a user of the zhmcclient package.
"""

from __future__ import absolute_import, print_function

import requests.packages.urllib3

import zhmcclient
import zhmcclient_mock

requests.packages.urllib3.disable_warnings()


class TestMy(object):

    @staticmethod
    def create_session_1():
        """
        Demonstrate how to populate a faked session with resources defined
        in a resource dictionary.
        """
        session = zhmcclient_mock.FakedSession('fake-host', 'fake-hmc',
                                               '2.13.1', '1.8')
        session.hmc.add_resources({
            'cpcs': [
                {
                    'properties': {
                        # object-id is auto-generated
                        # object-uri is auto-generated
                        'name': 'cpc_1',
                        'dpm-enabled': False,
                        'description': 'CPC #1',
                    },
                    'lpars': [
                        {
                            'properties': {
                                # object-id is auto-generated
                                # object-uri is auto-generated
                                'name': 'lpar_1',
                                'description': 'LPAR #1 in CPC #1',
                            },
                        },
                    ],
                },
                {
                    'properties': {
                        # object-id is auto-generated
                        # object-uri is auto-generated
                        'name': 'cpc_2',
                        'dpm-enabled': True,
                        'description': 'CPC #2',
                    },
                    'partitions': [
                        {
                            'properties': {
                                # object-id is auto-generated
                                # object-uri is auto-generated
                                'name': 'partition_1',
                                'description': 'Partition #1 in CPC #2',
                            },
                        },
                    ],
                    'adapters': [
                        {
                            'properties': {
                                # object-id is auto-generated
                                # object-uri is auto-generated
                                'name': 'osa_1',
                                'description': 'OSA #1 in CPC #2',
                                'type': 'osd',
                            },
                            'ports': [
                                {
                                    'properties': {
                                        # element-id is auto-generated
                                        # element-uri is auto-generated
                                        'name': 'osa_1_port_1',
                                        'description': 'Port #1 of OSA #1',
                                    },
                                },
                            ],
                        },
                    ],
                },
            ],
        })
        return session

    @staticmethod
    def create_session_2():
        """
        Demonstrate how to populate a faked session with resources one by one.
        """
        session = zhmcclient_mock.FakedSession('fake-host', 'fake-hmc',
                                               '2.13.1', '1.8')
        cpc1 = session.hmc.cpcs.add({
            # object-id is auto-generated
            # object-uri is auto-generated
            'name': 'cpc_1',
            'dpm-enabled': False,
            'description': 'CPC #1',
        })
        cpc1.lpars.add({
            # object-id is auto-generated
            # object-uri is auto-generated
            'name': 'lpar_1',
            'description': 'LPAR #1 in CPC #1',
        })
        cpc2 = session.hmc.cpcs.add({
            # object-id is auto-generated
            # object-uri is auto-generated
            'name': 'cpc_2',
            'dpm-enabled': True,
            'description': 'CPC #2',
        })
        cpc2.partitions.add({
            # object-id is auto-generated
            # object-uri is auto-generated
            'name': 'partition_1',
            'description': 'Partition #1 in CPC #2',
        })
        adapter1 = cpc2.adapters.add({
            # object-id is auto-generated
            # object-uri is auto-generated
            'name': 'osa_1',
            'description': 'OSA #1 in CPC #2',
            'type': 'osd',
        })
        adapter1.ports.add({
            # element-id is auto-generated
            # element-uri is auto-generated
            'name': 'osa_1_port_1',
            'description': 'Port #1 of OSA #1',
        })
        return session

    def check(self):
        """
        Check the faked session and its faked HMC.
        """

        assert self.session.host == 'fake-host'

        assert self.client.version_info() == (1, 8)

        cpcs = self.client.cpcs.list()
        assert len(cpcs) == 2

        cpc1 = cpcs[0]  # a CPC in classic mode
        assert cpc1.get_property('name') == 'cpc_1'
        assert not cpc1.dpm_enabled

        lpars = cpc1.lpars.list()
        assert len(lpars) == 1
        lpar1 = lpars[0]
        assert lpar1.get_property('name') == 'lpar_1'

        cpc2 = cpcs[1]  # a CPC in DPM mode
        assert cpc2.get_property('name') == 'cpc_2'
        assert cpc2.dpm_enabled

        partitions = cpc2.partitions.list()
        assert len(partitions) == 1
        partition1 = partitions[0]
        assert partition1.get_property('name') == 'partition_1'

        adapters = cpc2.adapters.list()
        assert len(adapters) == 1
        adapter1 = adapters[0]
        assert adapter1.get_property('name') == 'osa_1'

        ports = adapter1.ports.list()
        assert len(ports) == 1
        port1 = ports[0]
        assert port1.get_property('name') == 'osa_1_port_1'

    def test_session_1(self):
        self.session = self.create_session_1()
        self.client = zhmcclient.Client(self.session)
        self.check()

    def test_session_2(self):
        self.session = self.create_session_2()
        self.client = zhmcclient.Client(self.session)
        self.check()
