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
Unit tests for _resource_updater module.
"""

from __future__ import absolute_import, print_function

import time
import pytest
from mock import patch

from zhmcclient import BaseResource, BaseManager, Client
from zhmcclient_mock import FakedSession

from .test_notification import MockedStompConnection


class MyResource(BaseResource):
    """
    A simple resource for testing the ResourceUpdater class.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, manager, uri, name, properties):
        # pylint: disable=useless-super-delegation
        super(MyResource, self).__init__(manager, uri, name, properties)


class MyManager(BaseManager):
    """
    A simple resource manager for testing the ResourceUpdater class.

    It is only needed because BaseResource needs it; it is not subject
    of any test.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, session):
        super(MyManager, self).__init__(
            resource_class=MyResource,
            class_name='myresource',
            session=session,
            parent=None,  # a top-level resource
            base_uri='/api/myresources',
            oid_prop='fake-oid-prop',
            uri_prop='fake-uri-prop',
            name_prop='fake-name-prop',
            query_props=['qp1', 'qp2'])

    def list(self, full_properties=False, filter_args=None):
        # We have this method here just to avoid the warning about
        # an unimplemented abstract method. It is not being used in this
        # set of testcases.
        raise NotImplementedError


@pytest.fixture(params=[
    (
        # no object notifications
    ),
    (
        # one property change notification on a CPC with one property
        dict(
            headers={
                'notification-type': 'property-change',
                'object-uri': '/api/cpcs/fake-cpc1',
            },
            message={
                'change-reports': [
                    {
                        'property-name': 'description',
                        'old-value': 'desc1',
                        'new-value': 'desc_new',
                    },
                ]
            },
        ),
    ),
    (
        # one property change notification on a CPC with two properties
        dict(
            headers={
                'notification-type': 'property-change',
                'object-uri': '/api/cpcs/fake-cpc1',
            },
            message={
                'change-reports': [
                    {
                        'property-name': 'description',
                        'old-value': 'desc1',
                        'new-value': 'desc_new',
                    },
                    {
                        'property-name': 'title',
                        'old-value': 'title1',
                        'new-value': 'title_new',
                    },
                ]
            },
        ),
    ),
    (
        # one property change notification on a NIC with one property
        # (for testing a resource that has element-uri instead of object-uri)
        dict(
            headers={
                'notification-type': 'property-change',
                'element-uri': '/api/partitions/fake-part1/nics/fake-nic1',
            },
            message={
                'change-reports': [
                    {
                        'property-name': 'description',
                        'old-value': 'desc1',
                        'new-value': 'desc_new',
                    },
                ]
            },
        ),
    ),
    (
        # one status change notification on a CPC
        dict(
            headers={
                'notification-type': 'status-change',
                'object-uri': '/api/cpcs/fake-cpc1',
            },
            message={
                'change-reports': [
                    {
                        'old-status': 'status1',
                        'old-additional-status': 'addstatus1',
                        'new-status': 'status_new',
                        'new-additional-status': 'addstatus_new',
                        'has-unacceptable-status': True,
                    },
                ]
            },
        ),
    ),
    (
        # one property change notification that misses both object-uri and
        # element-uri (that would be an HMC error)
        dict(
            headers={
                'notification-type': 'property-change',
                'action': 'remove',
            },
            message={
                'change-reports': [
                    {
                        'property-name': 'description',
                        'old-value': 'desc1',
                        'new-value': 'desc_new',
                    },
                ]
            },
        ),
    ),
    (
        # one inventory change notification (will be ignored)
        dict(
            headers={
                'notification-type': 'inventory-change',
                'object-uri': '/api/cpcs/fake-cpc1',
                'action': 'remove',
            },
            message=None,
        ),
    ),
    (
        # one property change notification with invalid JSON
        dict(
            headers={
                'notification-type': 'property-change',
                'object-uri': '/api/cpcs/fake-cpc1',
                'action': 'remove',
            },
            message='{ prop: a}',
        ),
    ),
], scope='module')
def notifications(request):
    """Fixture for test notifications for ResourceUpdater"""
    return request.param


@pytest.fixture(params=[
    (
        # no resources
        {},
        [],
    ),
    (
        # one CPC resource with one partition that has one NIC
        {
            'cpcs': [
                {
                    'properties': {
                        'object-uri': '/api/cpcs/fake-cpc1',
                        'object-id': 'fake-cpc1',
                        'name': 'fake-cpc1',
                        'description': 'description1',
                        'status': 'status1',
                        'additional-status': 'addstatus1',
                        'has-unacceptable-status': False,
                    },
                    'partitions': [
                        {
                            'properties': {
                                'object-uri': '/api/partitions/fake-part1',
                                'object-id': 'fake-part1',
                                'name': 'fake-part1',
                                'description': 'description1',
                                'status': 'status1',
                                'additional-status': 'addstatus1',
                                'has-unacceptable-status': False,
                            },
                            'nics': [
                                {
                                    'properties': {
                                        'element-uri':
                                        '/api/partitions/fake-part1/'
                                        'nics/fake-nic1',
                                        'element-id': 'fake-nic1',
                                        'name': 'fake-nic1',
                                        'description': 'description1',
                                    },
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        # resources enabled for auto-update
        [
            '/api/cpcs/fake-cpc1',
            '/api/partitions/fake-part1',
            '/api/partitions/fake-part1/nics/fake-nic1',
        ],
    ),
], scope='module')
def resources(request):
    """
    Fixture for test resources for ResourceUpdater,
    in FakedHMC.add_resources() format.
    """
    return request.param


class TestResourceUpdater(object):
    """
    Test the ResourceUpdater class.
    """

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

        # The session has the ResourceUpdater object that is tested.
        self.session = FakedSession(
            'fake-hmc', 'fake-hmc', 'fake-version', 'fake-version')
        self.mgr = MyManager(self.session)

        # pylint: enable=attribute-defined-outside-init

    @patch(target='stomp.Connection', new=MockedStompConnection)
    def test_resource_updater(self, notifications, resources):
        # pylint: disable=redefined-outer-name
        """
        Test function for all methods of ResourceUpdater.
        """

        faked_resources, enabled_uris = resources

        # Build the faked resources.
        # We need to set up faked resources because the enabling for auto-update
        # will retrieve them. We set up all test resources as CPCs, since they
        # are top-level objects and it does not really matter for this test.
        self.session.hmc.add_resources(faked_resources)

        # List the CPC resources from the faked session
        client = Client(self.session)
        cpcs = client.cpcs.list()
        partitions = []
        for cpc in cpcs:
            partitions.extend(cpc.partitions.list())
        nics = []
        for partition in partitions:
            nics.extend(partition.nics.list())
        resource_objs = cpcs + partitions + nics

        # Enable the resource objects for auto-update. This causes them to be
        # registered with the resource updater.
        enabled_resource_objs = [obj for obj in resource_objs
                                 if obj.uri in enabled_uris]
        for res_obj in enabled_resource_objs:
            res_obj.enable_auto_update()
            assert res_obj.auto_update_enabled()

        # pylint: disable=protected-access
        updater = self.session._resource_updater
        if not enabled_uris:
            assert updater is None
            return

        assert updater is not None
        stomp_conn = updater._conn  # pylint: disable=protected-access

        assert updater.has_objects()
        assert self.session.auto_update_subscribed()

        for res_obj in enabled_resource_objs:
            registered_objs = list(updater.registered_objects(res_obj.uri))
            assert res_obj in registered_objs

        # Queue object notifications to be sent
        for noti in notifications:
            # pylint: disable=no-member
            stomp_conn.mock_add_message(noti['headers'], noti['message'])

        # Send the object notifications to the resource updater
        stomp_conn.mock_start()  # pylint: disable=no-member

        # Wait for notifications to be received and processed.
        time.sleep(1)

        # Build the expected changed resources from the notifications, for
        # easier access by assertions
        changed_resources = {}  # changed property dict by uri
        for noti in notifications:
            if not isinstance(noti['message'], dict):
                continue
            changed_props = {}
            if noti['headers']['notification-type'] == 'property-change':
                for cr in noti['message']['change-reports']:
                    changed_props[cr['property-name']] = cr['new-value']
            if noti['headers']['notification-type'] == 'status-change':
                for cr in noti['message']['change-reports']:
                    changed_props['status'] = cr['new-status']
                    changed_props['additional-status'] = \
                        cr['new-additional-status']
                    changed_props['has-unacceptable-status'] = \
                        cr['has-unacceptable-status']
            if 'object-uri' in noti['headers']:
                uri = noti['headers']['object-uri']
            elif 'element-uri' in noti['headers']:
                uri = noti['headers']['element-uri']
            else:
                uri = None
            if uri:
                changed_resources[uri] = changed_props

        # Verify the updated resource objects
        for res_obj in enabled_resource_objs:
            for name, value in res_obj.properties.items():
                try:
                    exp_value = changed_resources[res_obj.uri][name]
                except KeyError:  # for both
                    exp_value = None
                if exp_value is not None:
                    assert value == exp_value, \
                        "Unexpected value for property {} of resource {}". \
                        format(name, res_obj.uri)

        # Disable the resource objects for auto-update. This causes them to be
        # unregistered from the resource updater.
        for res_obj in enabled_resource_objs:
            res_obj.disable_auto_update()
            assert not res_obj.auto_update_enabled()

        assert not updater.has_objects()
        assert not self.session.auto_update_subscribed()
