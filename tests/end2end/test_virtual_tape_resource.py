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
End2end tests for Virtual Tape Resources (on CPCs in DPM mode).

These tests list, retrieve properties, and update Virtual Tape Resources.
"""

from requests.packages import urllib3

import zhmcclient

from .utils import skip_warn, pick_test_resources, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Virtual Tape Resource objects (e.g. find_by_name())
VTR_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in Virtual Tape Resource objects returned by list()
# without full props
VTR_LIST_PROPS = ['element-uri', 'name', 'device-number',
                  'adapter-port-uri', 'partition-uri']

# Properties whose values can change between retrievals of Virtual
# Tape Resource objects
VTR_VOLATILE_PROPS = []


def test_vtr_find_list(hmc_session):
    """
    Test list(), find(), findall() for Virtual Tape Resources.
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

            # Get virtual tape resources for this tape link
            vtr_list = tlink.virtual_tape_resources.list()
            if not vtr_list:
                skip_warn(f"No Virtual Tape Resources defined for "
                          f"Tape Link {tlink.name!r}")
                continue

            vtr_list = pick_test_resources(vtr_list)

            for vtr in vtr_list:
                print(f"Testing with Virtual Tape Resource "
                      f"{vtr.name!r}")
                runtest_find_list(
                    hmc_session, tlink.virtual_tape_resources, vtr.name,
                    'name', 'element-uri', VTR_VOLATILE_PROPS,
                    VTR_MINIMAL_PROPS, VTR_LIST_PROPS)


def test_vtr_property(hmc_session):
    """
    Test property related methods for Virtual Tape Resources.
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

            # Get virtual tape resources for this tape link
            vtr_list = tlink.virtual_tape_resources.list()
            if not vtr_list:
                skip_warn(f"No Virtual Tape Resources defined for "
                          f"Tape Link {tlink.name!r}")
                continue

            vtr_list = pick_test_resources(vtr_list)

            for vtr in vtr_list:
                print(f"Testing with Virtual Tape Resource "
                      f"{vtr.name!r}")

                # Select a property that is not returned by list()
                non_list_prop = 'class'

                runtest_get_properties(vtr.manager, non_list_prop)


def test_vtr_update_properties(hmc_session):
    """
    Test update_properties() for Virtual Tape Resources.
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

            # Get virtual tape resources for this tape link
            vtr_list = tlink.virtual_tape_resources.list()
            if not vtr_list:
                skip_warn(f"No Virtual Tape Resources defined for "
                          f"Tape Link {tlink.name!r}")
                continue

            vtr_list = pick_test_resources(vtr_list)

            for vtr in vtr_list:
                print(f"Testing with Virtual Tape Resource "
                      f"{vtr.name!r}")

                # Get current properties
                vtr.pull_full_properties()
                original_desc = vtr.get_property('description')

                # Update description
                new_desc = 'Updated by end2end test'
                print(f"Updating description to: {new_desc!r}")
                vtr.update_properties({'description': new_desc})

                # Verify the update
                vtr.pull_full_properties()
                updated_desc = vtr.get_property('description')
                assert updated_desc == new_desc, \
                    f"Description was not updated correctly: {updated_desc!r}"

                # Restore original description
                print(f"Restoring description to: {original_desc!r}")
                vtr.update_properties({'description': original_desc})

                # Verify restoration
                vtr.pull_full_properties()
                restored_desc = vtr.get_property('description')
                assert restored_desc == original_desc, \
                    f"Description was not restored correctly: {restored_desc!r}"

                print(f"Successfully tested update_properties() for "
                      f"Virtual Tape Resource {vtr.name!r}")


def test_vtr_attached_partition(hmc_session):
    """
    Test attached_partition property for Virtual Tape Resources.
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

            # Get virtual tape resources for this tape link
            vtr_list = tlink.virtual_tape_resources.list()
            if not vtr_list:
                skip_warn(f"No Virtual Tape Resources defined for "
                          f"Tape Link {tlink.name!r}")
                continue

            vtr_list = pick_test_resources(vtr_list)

            for vtr in vtr_list:
                print(f"Testing with Virtual Tape Resource "
                      f"{vtr.name!r}")

                # Get the attached partition
                partition = vtr.attached_partition
                assert partition is not None, \
                    f"VTR {vtr.name!r} has no attached partition"

                # Verify partition URI matches
                vtr.pull_full_properties()
                partition_uri = vtr.get_property('partition-uri')
                assert partition.uri == partition_uri, \
                    f"Partition URI mismatch for VTR {vtr.name!r}"


def test_vtr_adapter_port(hmc_session):
    """
    Test adapter_port property for Virtual Tape Resources.
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

            # Get virtual tape resources for this tape link
            vtr_list = tlink.virtual_tape_resources.list()
            if not vtr_list:
                skip_warn(f"No Virtual Tape Resources defined for "
                          f"Tape Link {tlink.name!r}")
                continue

            vtr_list = pick_test_resources(vtr_list)

            for vtr in vtr_list:
                print(f"Testing with Virtual Tape Resource "
                      f"{vtr.name!r}")

                # Get full properties to ensure adapter-port-uri is available
                vtr.pull_full_properties()
                adapter_port_uri = vtr.get_property('adapter-port-uri')

                if adapter_port_uri is None:
                    print(f"Skipping VTR {vtr.name!r} - no adapter port URI")
                    continue

                # Get the adapter port
                adapter_port = vtr.adapter_port
                assert adapter_port is not None, \
                    f"Virtual Tape Resource {vtr.name!r} has no adapter port"

                # Verify adapter port URI matches
                assert adapter_port.uri == adapter_port_uri, \
                    f"Adapter port URI mismatch for VTR {vtr.name!r}"


def test_vtr_filter_by_device_number(hmc_session):
    """
    Test filtering Virtual Tape Resources by device number.
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

            # Get all virtual tape resources for this tape link
            all_vtrs = tlink.virtual_tape_resources.list()
            if not all_vtrs:
                skip_warn(f"No Virtual Tape Resources defined for "
                          f"Tape Link {tlink.name!r}")
                continue

            # Pick one to test filtering
            test_vtr = all_vtrs[0]
            device_number = test_vtr.get_property('device-number')

            print(f"Testing filter by device-number: {device_number!r}")

            # Filter by device number
            filtered_vtrs = tlink.virtual_tape_resources.list(
                filter_args={'device-number': device_number})

            assert len(filtered_vtrs) >= 1, \
                f"No VTRs found with device-number {device_number!r}"

            # Verify all returned resources have the correct device number
            for vtr in filtered_vtrs:
                assert (vtr.get_property('device-number') ==
                        device_number)


def test_vtr_filter_by_partition(hmc_session):
    """
    Test filtering Virtual Tape Resources by partition URI.
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

            # Get all virtual tape resources for this tape link
            all_vtrs = tlink.virtual_tape_resources.list()
            if not all_vtrs:
                skip_warn(f"No Virtual Tape Resources defined for "
                          f"Tape Link {tlink.name!r}")
                continue

            # Pick one to test filtering
            test_vtr = all_vtrs[0]
            partition_uri = test_vtr.get_property('partition-uri')

            print(f"Testing filter by partition-uri: {partition_uri!r}")

            # Filter by partition URI
            filtered_vtrs = tlink.virtual_tape_resources.list(
                filter_args={'partition-uri': partition_uri})

            assert len(filtered_vtrs) >= 1, \
                f"No VTRs found with partition-uri {partition_uri!r}"

            # Verify all returned resources have the correct partition URI
            for vtr in filtered_vtrs:
                assert (vtr.get_property('partition-uri') ==
                        partition_uri)
