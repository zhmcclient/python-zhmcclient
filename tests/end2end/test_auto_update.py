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

"""
End2end tests for auto-updated resources (on CPCs in DPM mode).

These tests use partitions to test the auto-updating of resources. They do not
change any existing partitions, but create, modify and delete test partitions.
"""


import uuid
from time import sleep
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import
from zhmcclient_mock import FakedSession

from .utils import TEST_PREFIX, standard_partition_props, skip_warn

urllib3.disable_warnings()


def test_autoupdate_prop(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test auto-updated partitions when updating a property.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        if isinstance(cpc.manager.client.session, FakedSession):
            pytest.skip("Auto-update test requires notifications which are "
                        "not supported by zhmcclient_mock")

        print(f"Testing on CPC {cpc.name}")

        part_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"

        # Create the partition
        part_input_props = standard_partition_props(cpc, part_name)
        part = cpc.partitions.create(part_input_props)

        try:

            # Get a second zhmcclient object for the same partition, which will
            # be auto-updated
            part_auto = cpc.partitions.find(name=part_name)

            # Enable auto-update for the second partition
            part_auto.enable_auto_update()

            # Save some properties
            org_desc = part_auto.get_property('description')
            org_name = part_auto.name
            org_uri = part_auto.uri

            # Change the 'description' property through the first partition
            # object
            new_desc = org_desc + ' new'
            part.update_properties({'description': new_desc})

            # Test that the property change auto-updates the second partition
            # object.
            # We allow for some delay here, but in actual tests, the JMS message
            # about the change arrived faster than the operation response:
            #   07:20:59,817 Request Update Partition Properties
            #   07:21:00,529 JMS message for property change notification
            #   07:21:00,530 Response Update Partition Properties
            attempts = 20
            delay = 0.1  # seconds
            for _ in range(attempts):
                desc_auto = part_auto.properties['description']
                if desc_auto == new_desc:
                    break
                sleep(delay)
            assert desc_auto == new_desc, (
                f"Property did not auto-update after {attempts * delay} "
                "seconds")

            # Delete the partition through the first partition object
            part.delete()

            # Test that the second partition object is in ceased-existence
            # state.
            # We allow for some delay here, but in actual tests, the JMS message
            # about the change arrived faster than the operation response:
            #   07:21:00,532 Request Delete Partition
            #   07:21:02,735 JMS message for inventory change notification
            #   07:21:02,809 Response Delete Partition
            attempts = 20
            delay = 0.1  # seconds
            for _ in range(attempts):
                ceased = part_auto.ceased_existence
                if ceased:
                    break
                sleep(delay)
            assert ceased, (
                "Ceased-existence state did not auto-update after "
                f"{attempts * delay} seconds")

            # Test that accessing certain properties/methods on the
            # second (auto-updated) partition raises CeasedExistence

            with pytest.raises(zhmcclient.CeasedExistence) as exc_info:
                _ = part_auto.get_property('description')
            exc = exc_info.value
            assert exc.resource_uri == part.uri

            with pytest.raises(zhmcclient.CeasedExistence) as exc_info:
                _ = part_auto.prop('description')
            exc = exc_info.value
            assert exc.resource_uri == part.uri

            with pytest.raises(zhmcclient.CeasedExistence) as exc_info:
                part_auto.pull_full_properties()
            exc = exc_info.value
            assert exc.resource_uri == part.uri

            with pytest.raises(zhmcclient.CeasedExistence) as exc_info:
                _ = part_auto.dump()
            exc = exc_info.value
            assert exc.resource_uri == part.uri

            # Test that accessing certain properties/methods on the
            # second (auto-updated) partition does not raise CeasedExistence

            uri = part_auto.uri
            assert uri == org_uri

            name = part_auto.name
            assert name == org_name

            desc = part_auto.properties['description']
            assert desc == new_desc

            _ = part_auto.manager

            _ = part_auto.full_properties

            _ = part_auto.properties_timestamp

            ce = part_auto.ceased_existence
            assert ce is True

            _ = str(part_auto)

            _ = repr(part_auto)

            # Test that accessing properties of the first partition also
            # raises CeasedExistence (the ceased-existence state is set by
            # the delete() method).

            ce = part.ceased_existence
            assert ce is True

            with pytest.raises(zhmcclient.CeasedExistence) as exc_info:
                _ = part.get_property('description')
            exc = exc_info.value
            assert exc.resource_uri == part.uri

            with pytest.raises(zhmcclient.CeasedExistence) as exc_info:
                _ = part.prop('description')
            exc = exc_info.value
            assert exc.resource_uri == part.uri

            with pytest.raises(zhmcclient.CeasedExistence) as exc_info:
                part.pull_full_properties()
            exc = exc_info.value
            assert exc.resource_uri == part.uri

            with pytest.raises(zhmcclient.CeasedExistence) as exc_info:
                _ = part.dump()
            exc = exc_info.value
            assert exc.resource_uri == part.uri

        finally:
            # We want to make sure the test partition gets cleaned up after
            # the test, e.g. if the test is interrupted with Ctrl-C.
            try:
                part.delete()
            except zhmcclient.HTTPError as exc:
                # Since it normally will have been deleted already, we need to
                # allow for "not found".
                if exc.http_status == 404 and exc.reason == 1:
                    pass
                else:
                    raise


def test_autoupdate_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list() with auto-updated Partition manager.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        if isinstance(cpc.manager.client.session, FakedSession):
            pytest.skip("Auto-update test requires notifications which are "
                        "not supported by zhmcclient_mock")

        session = cpc.manager.session
        hd = session.hmc_definition

        new_part_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"

        # Get the initial set of partitions, for later comparison
        initial_part_list = cpc.partitions.list()
        if not initial_part_list:
            skip_warn(
                f"No partitions on CPC {cpc.name} managed by HMC {hd.host}")
        initial_part_names = {p.name for p in initial_part_list}

        # Enable auto-updating on partition manager and check partition list
        cpc.partitions.enable_auto_update()
        part_list = cpc.partitions.list()
        part_names = {p.name for p in part_list}
        assert part_names == initial_part_names

        try:

            # Create a partition and check partition list
            new_part_input_props = standard_partition_props(cpc, new_part_name)
            new_part = cpc.partitions.create(new_part_input_props)
            part_list = cpc.partitions.list()
            part_names = {p.name for p in part_list}
            exp_part_names = initial_part_names | {new_part.name}
            assert part_names == exp_part_names

            # Delete the partition and check partition list
            new_part.delete()
            part_list = cpc.partitions.list()
            part_names = {p.name for p in part_list}
            assert part_names == initial_part_names

            # Disable auto-updating on partition manager and check part. list
            cpc.partitions.disable_auto_update()
            part_list = cpc.partitions.list()
            part_names = {p.name for p in part_list}
            assert part_names == initial_part_names

            # Create a partition and check partition list
            new_part_input_props = standard_partition_props(cpc, new_part_name)
            new_part = cpc.partitions.create(new_part_input_props)
            part_list = cpc.partitions.list()
            part_names = {p.name for p in part_list}
            exp_part_names = initial_part_names | {new_part.name}
            assert part_names == exp_part_names

            # Delete the partition and check partition list
            new_part.delete()
            part_list = cpc.partitions.list()
            part_names = {p.name for p in part_list}
            assert part_names == initial_part_names

        finally:
            # We want to make sure the test partition gets cleaned up after
            # the test, e.g. if the test is interrupted with Ctrl-C.
            try:
                new_part.delete()
            except zhmcclient.HTTPError as exc:
                # Since it normally will have been deleted already, we need to
                # allow for "not found".
                if exc.http_status == 404 and exc.reason == 1:
                    pass
                else:
                    raise
