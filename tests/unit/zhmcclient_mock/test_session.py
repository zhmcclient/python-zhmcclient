# Copyright 2022 IBM Corp. All Rights Reserved.
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

# pylint: disable=protected-access,attribute-defined-outside-init

"""
Unit tests for _session module of the zhmcclient_mock package.
"""


from datetime import datetime

from zhmcclient import Client
from zhmcclient_mock import FakedSession

from zhmcclient_mock._hmc import \
    FakedMetricGroupDefinition, FakedMetricObjectValues

from tests.common.utils import assert_equal_hmc


# The resource input for the test_hmc_dump_load() test function.
# Each type of resource should appear in this resource input.
HMC1_RESOURCES = {
    'consoles': [
        {
            'properties': {
                'name': 'hmc1',
                'version': '2.14.1',
            },
            'users': [
                {
                    'properties': {
                        'object-id': 'user1',
                        'name': 'User 1',
                        'type': 'standard',
                    },
                },
            ],
            'user_roles': [
                {
                    'properties': {
                        'object-id': 'userrole1',
                        'name': 'User role 1',
                    },
                },
            ],
            'user_patterns': [
                {
                    'properties': {
                        'element-id': 'userpattern1',
                        'name': 'User pattern 1',
                        'type': 'glob-like',
                    },
                },
            ],
            'password_rules': [
                {
                    'properties': {
                        'element-id': 'passwordrule1',
                        'name': 'Password rule 1',
                        'type': 'user-defined',
                    },
                },
            ],
            'tasks': [
                {
                    'properties': {
                        'element-id': 'task1',
                        'name': 'Task 1',
                    },
                },
            ],
            'ldap_server_definitions': [
                {
                    'properties': {
                        'element-id': 'lsd1',
                        'name': 'LDAP server definition 1',
                    },
                },
            ],
            'unmanaged_cpcs': [
                {
                    'properties': {
                        'object-id': 'cpc3',
                        'name': 'Unmanaged CPC 3',
                    },
                },
            ],
            'storage_groups': [
                {
                    'properties': {
                        'object-id': 'sg1',
                        'name': 'Storage group 1',
                        'type': 'shared',
                        'cpc-uri': '/api/cpcs/cpc1',
                        'fulfillment-state': 'complete',
                    },
                    'storage_volumes': [
                        {
                            'properties': {
                                'element-id': 'sv1',
                                'name': 'Storage volume 1',
                                'fulfillment-state': 'complete',
                                'size': '10',
                                'usage': 'boot',
                            },
                        },
                    ],
                },
            ],
        },
    ],
    'cpcs': [
        {
            'properties': {
                'object-id': 'cpc1',
                'name': 'CPC 1 (DPM mode)',
                'dpm-enabled': True,
                'se-version': '2.13',
                'status': 'operating',
            },
            'capacity_groups': [
                {
                    'properties': {
                        'object-id': 'cg1',
                        'name': 'Capacity group 1',
                    },
                },
            ],
            'partitions': [
                {
                    'properties': {
                        'object-id': 'part1',
                        'name': 'Partition 1',
                    },
                    'nics': [
                        {
                            'properties': {
                                'element-id': 'nic1',
                                'name': 'NIC 1',
                                'device-number': '0010',
                            },
                        },
                    ],
                    'hbas': [
                        {
                            'properties': {
                                'element-id': 'hba1',
                                'name': 'HBA 1',
                                'device-number': '0018',
                            },
                        },
                    ],
                    'virtual_functions': [
                        {
                            'properties': {
                                'element-id': 'vf1',
                                'name': 'Virtual function 1',
                                'device-number': '0020',
                            },
                        },
                    ],
                },
            ],
            'adapters': [
                {
                    'properties': {
                        'object-id': 'ad1',
                        'name': 'Adapter 1',
                        'adapter-family': 'hipersockets',
                    },
                    'ports': [
                        {
                            'properties': {
                                'element-id': '1',
                                'name': 'Port 1',
                            },
                        },
                    ],
                },
            ],
            'virtual_switches': [
                {
                    'properties': {
                        'object-id': 'vs1',
                        'name': 'Virtual switch 1',
                    },
                },
            ],
        },
        {
            'properties': {
                'object-id': 'cpc2',
                'name': 'CPC 2 (classic mode)',
                'dpm-enabled': False,
                'se-version': '2.13',
                'status': 'active',
            },
            'capacity_groups': [
                {
                    'properties': {
                        'object-id': 'cg1',
                        'name': 'Capacity group 1',
                    },
                },
            ],
            'lpars': [
                {
                    'properties': {
                        'object-id': 'lpar1',
                        'name': 'LPAR1',
                    },
                },
            ],
            'reset_activation_profiles': [
                {
                    'properties': {
                        'object-id': 'rap1',
                        'name': 'RAP1',
                    },
                },
            ],
            'image_activation_profiles': [
                {
                    'properties': {
                        'object-id': 'lpar1',
                        'name': 'LPAR1',
                    },
                },
            ],
            'load_activation_profiles': [
                {
                    'properties': {
                        'object-id': 'specialload',
                        'name': 'SPECIALLOAD',
                    },
                },
            ],
        },
    ]
}

# The metroc group definitions for the test_hmc_dump_load() test function.
HMC_DUMP_LOAD_METRIC_GROUP_DEFS = [
    FakedMetricGroupDefinition(
        name='partition-usage',
        types=[
            ('processor-usage', 'integer-metric'),
            ('network-usage', 'integer-metric'),
            ('storage-usage', 'integer-metric'),
            ('accelerator-usage', 'integer-metric'),
            ('crypto-usage', 'integer-metric'),
        ]
    ),
]


def test_session_to_from_yaml():
    """Test FakedSession.to_yaml() and from_yaml()"""

    debug_yamlfile = False  # Enable to get the HMC dump file created

    # Set up the faked session
    console_props = HMC1_RESOURCES['consoles'][0]['properties']
    host = 'testhmc'
    api_version = '2.20'
    hmc_name = console_props['name']
    hmc_version = console_props['version']

    session = FakedSession(host, hmc_name, hmc_version, api_version,
                           userid='fake-user', password='fake-password')
    client = Client(session)

    session.hmc.add_resources(HMC1_RESOURCES)

    cpc1 = session.hmc.cpcs.list(filter_args={'object-id': 'cpc1'})[0]
    part1 = cpc1.partitions.list(filter_args={'object-id': 'part1'})[0]
    session.hmc.add_metric_values(
        FakedMetricObjectValues(
            group_name='partition-usage',
            resource_uri=part1.uri,
            timestamp=datetime.now(),
            values=[
                ('processor-usage', 15),
                ('network-usage', 0),
                ('storage-usage', 1),
                ('accelerator-usage', 0),
                ('crypto-usage', 0),
            ]))
    session.hmc.add_metric_values(
        FakedMetricObjectValues(
            group_name='partition-usage',
            resource_uri=part1.uri,
            timestamp=datetime.now(),
            values=[
                ('processor-usage', 17),
                ('network-usage', 5),
                ('storage-usage', 2),
                ('accelerator-usage', 0),
                ('crypto-usage', 0),
            ]))
    session.logon()  # Sets session.host

    # The function to be tested:
    hmc_yaml = client.to_hmc_yaml()

    if debug_yamlfile:
        filename = 'tmp_hmcdef.yaml'
        print(f"Creating file with faked HMC definition: {filename}")
        # pylint: disable=unspecified-encoding
        with open(filename, 'w') as fp:
            fp.write(hmc_yaml)

    # The function to be tested:
    new_session = FakedSession.from_hmc_yaml(hmc_yaml)

    assert_equal_hmc(new_session.hmc, session.hmc)
