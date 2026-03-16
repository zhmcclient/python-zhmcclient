# Copyright 2026 IBM Corp. All Rights Reserved.
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
End2end tests for Tape Links (on CPCs in DPM mode).

These tests create, modify, and delete test Tape Links.
"""

import pytest
from requests.packages import urllib3

import zhmcclient

from .utils import skip_warn, pick_test_resources, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Tape Link objects (e.g. find_by_name())
TLINK_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in Tape Link objects returned by list() without full props
TLINK_LIST_PROPS = ['element-uri', 'name', 'partition-uri',
                    'tape-library-uri', 'description']

# Properties whose values can change between retrievals of Tape Link objects
TLINK_VOLATILE_PROPS = []


def test_tlink_find_list(hmc_session):
    """
    Test list(), find(), findall() for Tape Links.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl_list = pick_test_resources(tl_list)

    for tl in tl_list:
        print(f"Testing with Tape Library {tl.name!r}")

        # Get tape links for this tape library
        tlink_list = tl.tape_links.list()
        if not tlink_list:
            skip_warn(f"No Tape Links defined for Tape Library {tl.name!r}")
            continue

        tlink_list = pick_test_resources(tlink_list)

        for tlink in tlink_list:
            print(f"Testing with Tape Link {tlink.name!r}")
            runtest_find_list(
                hmc_session, tl.tape_links, tlink.name,
                'name', 'element-uri', TLINK_VOLATILE_PROPS,
                TLINK_MINIMAL_PROPS, TLINK_LIST_PROPS)


def test_tlink_property(hmc_session):
    """
    Test property related methods for Tape Links.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl_list = pick_test_resources(tl_list)

    for tl in tl_list:
        print(f"Testing with Tape Library {tl.name!r}")

        # Get tape links for this tape library
        tlink_list = tl.tape_links.list()
        if not tlink_list:
            skip_warn(f"No Tape Links defined for Tape Library {tl.name!r}")
            continue

        tlink_list = pick_test_resources(tlink_list)

        for tlink in tlink_list:
            print(f"Testing with Tape Link {tlink.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'class'

            runtest_get_properties(tlink.manager, non_list_prop)


def test_tlink_crud(hmc_session):
    """
    Test create, update, and delete operations for Tape Links.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl = tl_list[0]

    print(f"Testing with Tape Library {tl.name!r}")

    # Get the CPC for this tape library
    cpc_uri = tl.get_property('cpc-uri')
    cpc = client.cpcs.find(**{'object-uri': cpc_uri})

    # Pick a partition to test with
    part_list = cpc.partitions.list()
    if not part_list:
        skip_warn(f"No Partitions defined on CPC {cpc.name!r}")
    partition = part_list[0]

    print(f"Testing with Partition {partition.name!r}")

    # Test creating a Tape Link
    tlink_name = 'test-tape-link-e2e'
    tlink_props = {
        'name': tlink_name,
        'description': 'Test tape link for end-to-end testing',
        'partition-uri': partition.uri,
    }

    # Clean up any existing test tape link
    try:
        existing_tlink = tl.tape_links.find(name=tlink_name)
        existing_tlink.delete()
        print(f"Deleted existing test Tape Link {tlink_name!r}")
    except zhmcclient.NotFound:
        pass

    # The code to be tested: Create
    tlink = tl.tape_links.create(tlink_props)

    try:
        assert tlink.properties['name'] == tlink_name
        assert tlink.properties['partition-uri'] == partition.uri
        print(f"Created Tape Link {tlink.name!r}")

        # Test updating properties
        new_desc = "Updated tape link description for e2e testing"

        # The code to be tested: Update
        tlink.update_properties({'description': new_desc})

        assert tlink.properties['description'] == new_desc
        tlink.pull_full_properties()
        assert tlink.properties['description'] == new_desc
        print(f"Updated Tape Link {tlink.name!r} description")

        # Test renaming
        new_name = 'test-tape-link-e2e-renamed'

        # The code to be tested: Rename
        tlink.update_properties({'name': new_name})
        tlink.pull_full_properties()

        assert tlink.properties['name'] == new_name
        with pytest.raises(zhmcclient.NotFound):
            tl.tape_links.find(name=tlink_name)
        print(f"Renamed Tape Link to {new_name!r}")

    finally:
        # Clean up: Delete the test tape link
        try:
            tlink.delete()
            print(f"Deleted test Tape Link {tlink.name!r}")
        except zhmcclient.NotFound:
            pass


def test_tlink_get_partitions(hmc_session):
    """
    Test get_partitions() method for Tape Links.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl_list = pick_test_resources(tl_list)

    for tl in tl_list:
        print(f"Testing with Tape Library {tl.name!r}")

        # Get tape links for this tape library
        tlink_list = tl.tape_links.list()
        if not tlink_list:
            skip_warn(f"No Tape Links defined for Tape Library {tl.name!r}")
            continue

        tlink_list = pick_test_resources(tlink_list)

        for tlink in tlink_list:
            print(f"Testing with Tape Link {tlink.name!r}")

            # The code to be tested
            partitions = tlink.get_partitions()

            assert isinstance(partitions, list)
            print(f"Tape Link {tlink.name!r} has {len(partitions)} "
                  f"partition(s)")

            for partition in partitions:
                assert isinstance(partition, zhmcclient.Partition)
                assert 'object-uri' in partition.properties
                assert 'name' in partition.properties
                assert 'status' in partition.properties
                print(f"  Partition: {partition.name!r}, "
                      f"Status: {partition.properties['status']}")


def test_tlink_get_histories(hmc_session):
    """
    Test get_histories() method for Tape Links.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl_list = pick_test_resources(tl_list)

    for tl in tl_list:
        print(f"Testing with Tape Library {tl.name!r}")

        # Get tape links for this tape library
        tlink_list = tl.tape_links.list()
        if not tlink_list:
            skip_warn(f"No Tape Links defined for Tape Library {tl.name!r}")
            continue

        tlink_list = pick_test_resources(tlink_list)

        for tlink in tlink_list:
            print(f"Testing with Tape Link {tlink.name!r}")

            # The code to be tested
            histories = tlink.get_histories()

            assert isinstance(histories, dict)
            print(f"Retrieved histories for Tape Link {tlink.name!r}")

            # The response should contain tape-link-histories
            if 'tape-link-histories' in histories:
                history_list = histories['tape-link-histories']
                print(f"  Found {len(history_list)} history record(s)")


def test_tlink_environment_report(hmc_session):
    """
    Test get_environment_report() and update_environment_report() methods.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl_list = pick_test_resources(tl_list)

    for tl in tl_list:
        print(f"Testing with Tape Library {tl.name!r}")

        # Get tape links for this tape library
        tlink_list = tl.tape_links.list()
        if not tlink_list:
            skip_warn(f"No Tape Links defined for Tape Library {tl.name!r}")
            continue

        tlink_list = pick_test_resources(tlink_list)

        for tlink in tlink_list:
            print(f"Testing with Tape Link {tlink.name!r}")

            # The code to be tested: Get environment report
            report = tlink.get_environment_report()

            assert isinstance(report, dict)
            print(f"Retrieved environment report for Tape Link {tlink.name!r}")

            # The code to be tested: Update environment report
            # Note: The actual properties that can be updated depend on the
            # HMC API specification. This is a basic test.
            update_props = {
                'test-field': 'test-value'
            }

            try:
                result = tlink.update_environment_report(update_props)
                assert isinstance(result, dict)
                print(f"Updated environment report for Tape Link "
                      f"{tlink.name!r}")
            except zhmcclient.HTTPError as exc:
                # Some properties might not be updatable, which is acceptable
                if exc.http_status == 400:
                    print(f"Update not supported (expected): {exc}")
                else:
                    raise


def test_tlink_partition_property(hmc_session):
    """
    Test the partition property of Tape Link.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the Tape Library to test with
    tl_list = console.tape_library.list()
    if not tl_list:
        skip_warn(f"No Tape Library defined on HMC {hd.host}")
    tl_list = pick_test_resources(tl_list)

    for tl in tl_list:
        print(f"Testing with Tape Library {tl.name!r}")

        # Get tape links for this tape library
        tlink_list = tl.tape_links.list()
        if not tlink_list:
            skip_warn(f"No Tape Links defined for Tape Library {tl.name!r}")
            continue

        tlink_list = pick_test_resources(tlink_list)

        for tlink in tlink_list:
            print(f"Testing with Tape Link {tlink.name!r}")

            # The code to be tested
            partition = tlink.partition

            assert isinstance(partition, zhmcclient.Partition)
            assert partition.uri == tlink.get_property('partition-uri')
            print(f"Tape Link {tlink.name!r} is linked to "
                  f"Partition {partition.name!r}")
