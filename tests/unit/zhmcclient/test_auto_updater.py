# Copyright 2021 IBM Corp. All Rights Reserved.
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
Unit tests for _auto_updater module.
"""


import time
import re
import logging
from unittest.mock import patch
import pytest

from zhmcclient import Client
from zhmcclient_mock import FakedSession

from .test_notification import MockedStompConnection

# Test resources that are the basis, in FakedHMC.add_resources() format
TEST_RESOURCES_BASE = {
    'cpcs': [
        {
            'properties': {
                'object-uri': '/api/cpcs/fake-cpc1',
                'object-id': 'fake-cpc1',
                'name': 'fake-cpc1',  # pc (but ro)
                'dpm-enabled': True,  # pc
                'description': 'description1',  # pc if DPM
                'acceptable-status': ['active'],  # pc
                'degraded-status': [],  # pc
                'status': 'active',  # sc
                'additional-status': 'addstatus',  # sc (not in data model)
                'has-unacceptable-status': False,  # sc
            },
            'partitions': [
                {
                    'properties': {
                        'object-uri': '/api/partitions/fake-part1',
                        'object-id': 'fake-part1',
                        'name': 'fake-part1',  # pc
                        'description': 'description1',  # pc
                        'acceptable-status': ['active'],  # pc
                        'status': 'active',  # sc
                        'additional-status': 'addstatus',  # sc (not in model)
                        'has-unacceptable-status': False,  # sc
                    },
                    'nics': [
                        {
                            'properties': {
                                'element-uri':
                                '/api/partitions/fake-part1/nics/fake-nic1',
                                'element-id': 'fake-nic1',
                                'name': 'fake-nic1',  # pc
                                'description': 'description1',  # pc
                            },
                        },
                    ],
                },
            ],
        },
    ],
    'consoles': [
        {
            'properties': {
                'object-uri': '/api/console',
                'name': 'fake-hmc1',
                'description': 'fake-hmc1',
                'version': '2.15.0',
            },
            'unmanaged_cpcs': [],
        },
    ],
}

# Test partition 2 that gets added, in FakedPartitionManager.add() format
TEST_PARTITION_2 = {
    'object-uri': '/api/partitions/fake-part2',
    'object-id': 'fake-part2',
    'name': 'fake-part2',  # pc
    'description': 'description2',  # pc
    'acceptable-status': ['active'],  # pc
    'status': 'active',  # sc
    'additional-status': 'addstatus',  # sc (not in model)
    'has-unacceptable-status': False,  # sc
}

# Test CPC 2 that gets added, in FakedCpcManager.add() format
TEST_CPC_2 = {
    'object-uri': '/api/cpcs/fake-cpc2',
    'object-id': 'fake-cpc2',
    'name': 'fake-cpc2',  # pc (but ro)
    'dpm-enabled': True,  # pc
    'description': 'description2',  # pc if DPM
    'acceptable-status': ['active'],  # pc
    'degraded-status': [],  # pc
    'status': 'inactive',  # sc
    'additional-status': 'addstatus',  # sc (not in data model)
    'has-unacceptable-status': True,  # sc
}


# Testcases for test_auto_updater_all()
TESTCASES_AUTO_UPDATER_ALL = [
    # Each list item is a separate testcase for which test_auto_updater_all()
    # is called.
    # A testcase item is a tuple with these members:
    # * string: testcase description
    # * dict: testcase data, with the following dict items:
    #   - initial_resources: Initial mock resources to be set up before the
    #     test, in FakedBaseResource.add_resources() format.
    #   - auto_updated_uris: List of canonical resource or manager URIs to
    #     enable for auto-updating before the test. The format for manager
    #     URIs must follow the implementation in BaseManager.uri.
    #   - added_resources: List of tuple(parent_uri, resources) for
    #     resources to be added to trigger inventory add notifications.
    #     child_resources is in FakedBaseResource.add_resources() format.
    #   - removed_resources: List of resource_uri for resources to be removed
    #     to trigger inventory remove notifications.
    #   - updated_resources: List of tuple(resource_uri, properties) for
    #     resources to be updated to trigger property change or status change
    #     notifications.
    #   - notifications: List of tuple(header, message) for JMS notifications
    #     that are triggered. header and message are Python objects that can be
    #     dumped to JSON.
    #   - exp_lists: List of tuple(mgr_uri, res_uris, local_res_uris) for the
    #     expected resources and local resources in a manager after the changes.
    #   - exp_resources: List of tuple(uri, properties) for expected resource
    #     properties after the changes.
    #   - exp_log_entries: List of tuple(logger_name, level, message_pattern)
    #     for expected log entries. Only these are verified, any additional
    #     log entries are tolerated.

    (
        "no auto-updated resources, no changes, no notifications",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[],
            added_resources=[],
            removed_resources=[],
            updated_resources=[],
            notifications=[],
            exp_lists=[],
            exp_resources=[],
            exp_log_entries=[],
        ),
    ),
    (
        "property change notification for an auto-updated CPC "
        "(top-level object)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/api/cpcs/fake-cpc1',
            ],
            added_resources=[],
            removed_resources=[],
            updated_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'description': 'desc_new',
                    },
                ),
            ],
            notifications=[
                (
                    {
                        'notification-type': 'property-change',
                        'object-uri': '/api/cpcs/fake-cpc1',
                    },
                    {
                        'change-reports': [
                            {
                                'property-name': 'description',
                                'old-value': 'description1',
                                'new-value': 'desc_new',
                            },
                        ],
                    },
                ),
            ],
            exp_lists=[
                (
                    '/#cpc',
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                ),
            ],
            exp_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'description': 'desc_new',
                    },
                ),
            ],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.DEBUG,
                 "JMS message for property change notification .*"
                 "resource /api/cpcs/fake-cpc1 .*"
                 "u?'property-name': u?'description'"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "property change notification for a non auto-updated CPC",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[],  # Not auto-updated
            added_resources=[],
            removed_resources=[],
            updated_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'description': 'description1',  # Old value
                    },
                ),
            ],
            notifications=[
                (
                    {
                        'notification-type': 'property-change',
                        'object-uri': '/api/cpcs/fake-cpc1',
                    },
                    {
                        'change-reports': [
                            {
                                'property-name': 'description',
                                'old-value': 'description1',
                                'new-value': 'desc_new',
                            },
                        ],
                    },
                ),
            ],
            exp_lists=[
                (
                    '/#cpc',
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                ),
            ],
            exp_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'description': 'description1',
                    },
                ),
            ],
            exp_log_entries=[],
        ),
    ),
    (
        "property change notification with two changes",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/api/cpcs/fake-cpc1',
            ],
            added_resources=[],
            removed_resources=[],
            updated_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'description': 'desc_new',
                        'degraded-status': ['memory'],
                    },
                ),
            ],
            notifications=[
                (
                    {
                        'notification-type': 'property-change',
                        'object-uri': '/api/cpcs/fake-cpc1',
                    },
                    {
                        'change-reports': [
                            {
                                'property-name': 'description',
                                'old-value': 'description1',
                                'new-value': 'desc_new',
                            },
                            {
                                'property-name': 'degraded-status',
                                'old-value': [],
                                'new-value': ['memory'],
                            },
                        ],
                    },
                ),
            ],
            exp_lists=[
                (
                    '/#cpc',
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                ),
            ],
            exp_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'description': 'desc_new',
                        'degraded-status': ['memory'],
                    },
                ),
            ],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.DEBUG,
                 "JMS message for property change notification .*"
                 "resource /api/cpcs/fake-cpc1 .*"
                 "u?'property-name': u?'description'.*"
                 "u?'property-name': u?'degraded-status'"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "property change notification on an auto-updated NIC "
        "(element resource)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/api/partitions/fake-part1/nics/fake-nic1',
            ],
            added_resources=[],
            removed_resources=[],
            updated_resources=[
                (
                    '/api/partitions/fake-part1/nics/fake-nic1',
                    {
                        'description': 'desc_new',
                    },
                ),
            ],
            notifications=[
                (
                    {
                        'notification-type': 'property-change',
                        'element-uri':
                        '/api/partitions/fake-part1/nics/fake-nic1',
                    },
                    {
                        'change-reports': [
                            {
                                'property-name': 'description',
                                'old-value': 'description1',
                                'new-value': 'desc_new',
                            },
                        ]
                    },
                ),
            ],
            exp_lists=[
                (
                    '/api/partitions/fake-part1#nic',
                    [
                        '/api/partitions/fake-part1/nics/fake-nic1',
                    ],
                    [
                        '/api/partitions/fake-part1/nics/fake-nic1',
                    ],
                ),
            ],
            exp_resources=[
                (
                    '/api/partitions/fake-part1/nics/fake-nic1',
                    {
                        'description': 'desc_new',
                    },
                ),
            ],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.DEBUG,
                 "JMS message for property change notification .*"
                 "resource /api/partitions/fake-part1/nics/fake-nic1 .*"
                 "u?'property-name': u?'description'"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "status change notification on an auto-updated CPC "
        "(top-level resource)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/api/cpcs/fake-cpc1',
            ],
            added_resources=[],
            removed_resources=[],
            updated_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'status': 'inactive',
                        'additional-status': 'addstatus_new',
                        'has-unacceptable-status': True,
                    },
                ),
            ],
            notifications=[
                (
                    {
                        'notification-type': 'status-change',
                        'object-uri': '/api/cpcs/fake-cpc1',
                    },
                    {
                        'change-reports': [
                            {
                                'old-status': 'active',
                                'old-additional-status': 'addstatus',
                                'new-status': 'inactive',
                                'new-additional-status': 'addstatus_new',
                                'has-unacceptable-status': True,
                            },
                        ]
                    },
                ),
            ],
            exp_lists=[
                (
                    '/#cpc',
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                ),
            ],
            exp_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'status': 'inactive',
                        'additional-status': 'addstatus_new',
                        'has-unacceptable-status': True,
                    },
                ),
            ],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.DEBUG,
                 "JMS message for status change notification"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "inventory change notification for removing a partition from an "
        "auto-updated partition manager (object resource)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/api/cpcs/fake-cpc1#partition',
            ],
            added_resources=[],
            removed_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    'partitions',
                    'fake-part1',
                ),
            ],
            updated_resources=[],
            notifications=[
                (
                    {
                        'notification-type': 'inventory-change',
                        'object-uri': '/api/partitions/fake-part1',
                        'object-id': 'fake-part1',
                        'class': 'partition',
                        'action': 'remove',
                    },
                    None,
                ),
            ],
            exp_lists=[
                (
                    '/api/cpcs/fake-cpc1#partition',
                    [],
                    [],
                ),
            ],
            exp_resources=[],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.DEBUG,
                 "JMS message for inventory change notification .*"
                 "resource /api/partitions/fake-part1 .*"
                 "action: u?'remove'"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "inventory change notification for adding a partition to an "
        "auto-updated partition manager (object resource)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/api/cpcs/fake-cpc1#partition',
            ],
            added_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'partitions': [
                            {
                                'properties': TEST_PARTITION_2,
                            },
                        ],
                    },
                ),
            ],
            removed_resources=[],
            updated_resources=[],
            notifications=[
                (
                    {
                        'notification-type': 'inventory-change',
                        'object-uri': TEST_PARTITION_2['object-uri'],
                        'object-id': TEST_PARTITION_2['object-id'],
                        'class': 'partition',
                        'action': 'add',
                    },
                    None,
                ),
            ],
            exp_lists=[
                (
                    '/api/cpcs/fake-cpc1#partition',
                    [
                        '/api/partitions/fake-part1',
                        TEST_PARTITION_2['object-uri'],
                    ],
                    [
                        '/api/partitions/fake-part1',
                        TEST_PARTITION_2['object-uri'],
                    ],
                ),
            ],
            exp_resources=[
                (
                    TEST_PARTITION_2['object-uri'],
                    TEST_PARTITION_2,
                ),
            ],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.DEBUG,
                 "JMS message for inventory change notification .*"
                 "resource /api/partitions/fake-part2 .*"
                 "action: u?'add'"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "inventory change notification for removing a CPC from an "
        "auto-updated CPC manager (top-level resource)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/#cpc',
            ],
            added_resources=[],
            removed_resources=[
                (
                    None,
                    'cpcs',
                    'fake-cpc1',
                ),
            ],
            updated_resources=[],
            notifications=[
                (
                    {
                        'notification-type': 'inventory-change',
                        'object-uri': '/api/cpcs/fake-cpc1',
                        'object-id': 'fake-cpc1',
                        'class': 'cpc',
                        'action': 'remove',
                    },
                    None,
                ),
            ],
            exp_lists=[
                (
                    '/#cpc',
                    [],
                    [],
                ),
            ],
            exp_resources=[],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.DEBUG,
                 "JMS message for inventory change notification .*"
                 "resource /api/cpcs/fake-cpc1 .*"
                 "action: u?'remove'"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "inventory change notification for adding a CPC to an "
        "auto-updated CPC manager ((top-level resource)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/#cpc',
            ],
            added_resources=[
                (
                    None,
                    {
                        'cpcs': [
                            {
                                'properties': TEST_CPC_2,
                            },
                        ],
                    },
                ),
            ],
            removed_resources=[],
            updated_resources=[],
            notifications=[
                (
                    {
                        'notification-type': 'inventory-change',
                        'object-uri': TEST_CPC_2['object-uri'],
                        'object-id': TEST_CPC_2['object-id'],
                        'class': 'cpc',
                        'action': 'add',
                    },
                    None,
                ),
            ],
            exp_lists=[
                (
                    '/#cpc',
                    [
                        '/api/cpcs/fake-cpc1',
                        TEST_CPC_2['object-uri'],
                    ],
                    [
                        '/api/cpcs/fake-cpc1',
                        TEST_CPC_2['object-uri'],
                    ],
                ),
            ],
            exp_resources=[
                (
                    TEST_CPC_2['object-uri'],
                    TEST_CPC_2,
                ),
            ],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.DEBUG,
                 "JMS message for inventory change notification .*"
                 "resource /api/cpcs/fake-cpc2 .*"
                 "action: u?'add'"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "inventory change notification with invalid action "
        "(that would be an HMC error or a future extension)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/api/cpcs/fake-cpc1#partition',
            ],
            added_resources=[],
            removed_resources=[],
            updated_resources=[],
            notifications=[
                (
                    {
                        'notification-type': 'inventory-change',
                        'object-uri': '/api/partitions/fake-part1',
                        'object-id': 'fake-part1',
                        'class': 'partition',
                        'action': 'xyz',  # invalid action
                    },
                    None,
                ),
            ],
            exp_lists=[
                (
                    '/api/cpcs/fake-cpc1#partition',
                    [
                        '/api/partitions/fake-part1',
                    ],
                    [
                        '/api/partitions/fake-part1',
                    ],
                ),
            ],
            exp_resources=[],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.DEBUG,
                 "JMS message for inventory change notification .*"
                 "resource /api/partitions/fake-part1 .*"
                 "action: u?'xyz'"),
                ('zhmcclient.jms', logging.ERROR,
                 "JMS message for inventory change notification .*"
                 "unknown action 'xyz'"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "property change notification that misses both object-uri and "
        "element-uri (that would be an HMC error)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/api/cpcs/fake-cpc1',
            ],
            added_resources=[],
            removed_resources=[],
            updated_resources=[],
            notifications=[
                (
                    {
                        'notification-type': 'property-change',
                        # missing element-uri and object-uri
                    },
                    {
                        'change-reports': [
                            {
                                'property-name': 'description',
                                'old-value': 'description1',
                                'new-value': 'desc_new',
                            },
                        ]
                    },
                ),
            ],
            exp_lists=[
                (
                    '/#cpc',
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                    [
                        '/api/cpcs/fake-cpc1',
                    ],
                ),
            ],
            exp_resources=[
                (
                    '/api/cpcs/fake-cpc1',
                    {
                        'description': 'description1',
                    },
                ),
            ],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.ERROR,
                 "JMS message for object notification .*"
                 "no 'element-uri' .*no 'object-uri'"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
    (
        "valid notification unrelated to auto-updating (should be ignored)",
        dict(
            initial_resources=TEST_RESOURCES_BASE,
            auto_updated_uris=[
                '/api/cpcs/fake-cpc1',
            ],
            added_resources=[],
            removed_resources=[],
            updated_resources=[],
            notifications=[
                (
                    {
                        'notification-type': 'job-completion',  # unrelated
                        'job-uri': 'bla',
                    },
                    None,
                ),
            ],
            exp_lists=[],
            exp_resources=[],
            exp_log_entries=[
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* established"),
                ('zhmcclient.jms', logging.WARNING,
                 "JMS message for notification of type job-completion .*"
                 "is ignored"),
                ('zhmcclient.jms', logging.INFO,
                 "JMS session .* disconnected"),
            ],
        ),
    ),
]


@pytest.mark.parametrize(
    "desc, testcase",
    TESTCASES_AUTO_UPDATER_ALL)
@patch(target='stomp.Connection', new=MockedStompConnection)
def test_auto_updater_all(desc, testcase, caplog):
    # pylint: disable=unused-argument
    """
    Test function for an overall use of AutoUpdater with auto-updated
    resources.
    """

    # In this function, the variables for faked zhmcclient objects are named
    # 'faked_*'.

    initial_resources = testcase['initial_resources']
    auto_updated_uris = testcase['auto_updated_uris']
    added_resources = testcase['added_resources']
    removed_resources = testcase['removed_resources']
    updated_resources = testcase['updated_resources']
    notifications = testcase['notifications']
    exp_lists = testcase['exp_lists']
    exp_resources = testcase['exp_resources']
    exp_log_entries = testcase['exp_log_entries']

    caplog.set_level(logging.DEBUG, logger="zhmcclient.jms")

    # Create a zhmcclient mock environment
    faked_session = FakedSession(
        'fake-hmc', 'fake-hmc', 'fake-version', 'fake-version')
    client = Client(faked_session)

    # Add the initial resources for the testcase to the mock enviroment.
    # They will be retrieved in order to enable auto-updating for them.
    faked_session.hmc.add_resources(initial_resources)

    # List the resources and managerss
    managers = {}  # key: manager URI, value: zhmcclient manager object
    resource_objs = []  # zhmcclient resource objects
    cpcs = client.cpcs.list()
    resource_objs.extend(cpcs)
    managers[client.cpcs.uri] = client.cpcs
    for cpc in cpcs:
        partitions = cpc.partitions.list()
        resource_objs.extend(partitions)
        managers[cpc.partitions.uri] = cpc.partitions
        for partition in partitions:
            nics = partition.nics.list()
            resource_objs.extend(nics)
            managers[partition.nics.uri] = partition.nics

    # Enable the desired resource and manager objects for auto-updating.
    # This causes them to be registered with the auto updater.
    enabled_res_objs = []
    enabled_mgr_objs = []
    for res_obj in resource_objs:
        if res_obj.uri in auto_updated_uris:
            enabled_res_objs.append(res_obj)
    for mgr_uri, mgr_obj in managers.items():
        if mgr_uri in auto_updated_uris:
            enabled_mgr_objs.append(mgr_obj)
    for res_obj in enabled_res_objs:
        res_obj.enable_auto_update()
        assert res_obj.auto_update_enabled()
    for mgr_obj in enabled_mgr_objs:
        mgr_obj.enable_auto_update()
        assert mgr_obj.auto_update_enabled()

    # pylint: disable=protected-access
    updater = faked_session._auto_updater
    if not auto_updated_uris:
        assert not updater.is_open()
        return

    assert updater.is_open()
    assert updater.has_objects()
    assert faked_session.auto_update_subscribed()

    for res_obj in enabled_res_objs:
        registered_objs = list(updater.registered_objects(res_obj.uri))
        assert res_obj in registered_objs

    # Simulate the desired changes in the mock enviroment
    for parent_uri, resources in added_resources:
        if parent_uri is None:
            faked_parent_obj = faked_session.hmc
        else:
            faked_parent_obj = faked_session.hmc.lookup_by_uri(parent_uri)
        faked_parent_obj.add_resources(resources)
    for parent_uri, mgr_attr, res_oid in removed_resources:
        if parent_uri is None:
            faked_parent_obj = faked_session.hmc
        else:
            faked_parent_obj = faked_session.hmc.lookup_by_uri(parent_uri)
        faked_mgr_obj = getattr(faked_parent_obj, mgr_attr)
        faked_mgr_obj.remove(res_oid)
    for res_uri, props in updated_resources:
        faked_res_obj = faked_session.hmc.lookup_by_uri(res_uri)
        faked_res_obj.properties.update(props)

    # Queue the notifications to be sent for the desired changes
    stomp_conn = updater._conn  # pylint: disable=protected-access
    for headers, message in notifications:
        # pylint: disable=no-member
        stomp_conn.mock_add_message(headers, message)

    # Send the notifications to the auto updater
    stomp_conn.mock_start()  # pylint: disable=no-member

    # Wait for notifications to be received and processed.
    time.sleep(0.5)

    # Verify the log entries.
    # The expected log entries must appear in the specified order, but
    # additional log entries are tolerated.
    caplog_records = list(caplog.records)
    next_aix = 0
    for eix, exp_log_entry in enumerate(exp_log_entries):
        exp_logger_name, exp_level, exp_message_pattern = exp_log_entry
        for aix, act_record in enumerate(caplog_records[next_aix:]):
            if act_record.name == exp_logger_name \
                    and act_record.levelno == exp_level \
                    and re.match(exp_message_pattern, act_record.message):
                # Found the next matching expected log entry
                next_aix += 1 + aix
                break
        else:
            exp_messages = [item[2] for item in exp_log_entries]
            caplog_messages = [item.message for item in caplog_records]
            exp_msg_str = '\n'.join(exp_messages)
            caplog_msg_str = '\n'.join(caplog_messages)
            raise AssertionError(
                f"Did not find expected log message pattern at index {eix} "
                f"in captured log records starting at index {next_aix}.\n"
                "\nExpected log record message patterns:\n"
                f"{exp_msg_str}\n"
                "\nCaptured log record messages:\n"
                f"{caplog_msg_str}")

    # Verify the list() results and the local resources in the manager object
    for mgr_uri, exp_res_uris, exp_local_res_uris in exp_lists:
        mgr_obj = managers[mgr_uri]

        # Verify the list() results
        res_objs = mgr_obj.list()
        res_uris = [_obj.uri for _obj in res_objs]
        assert set(res_uris) == set(exp_res_uris)

        # Verify the local resources in the manager object
        local_res_objs = mgr_obj.list_resources_local()
        local_res_uris = [_obj.uri for _obj in local_res_objs]
        assert set(local_res_uris) == set(exp_local_res_uris)

    # Verify the properties of updated resource objects
    for res_uri, exp_props in exp_resources:
        faked_res_obj = faked_session.hmc.lookup_by_uri(res_uri)
        for name, value in faked_res_obj.properties.items():
            try:
                exp_value = exp_props[name]
            except KeyError:
                exp_value = None
            if exp_value is not None:
                assert value == exp_value, (
                    f"Unexpected value for property {name} of resource "
                    f"{faked_res_obj.uri}")

    # Disable the resource and manager objects for auto-updating.
    # This causes them to be unregistered from the auto updater.
    for res_obj in enabled_res_objs:
        res_obj.disable_auto_update()
        assert not res_obj.auto_update_enabled()
    for mgr_obj in enabled_mgr_objs:
        mgr_obj.disable_auto_update()
        assert not mgr_obj.auto_update_enabled()

    # There is always the initial CPC manager object in the UpdateListener
    # class enabled for auto-updating:
    assert updater.has_objects()
    assert updater.is_open()
    assert faked_session.auto_update_subscribed()
