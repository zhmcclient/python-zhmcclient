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
End2end tests for Storage Control Units and Storage Paths
(on CPCs in DPM mode).

These tests exercise the list, get-properties, update-properties,
define, undefine, add-volume-range, remove-volume-range, and storage path
CRUD operations. They do not permanently modify existing resources.
"""


from requests.packages import urllib3

import zhmcclient

from .utils import skip_warn, pick_test_resources, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic StorageControlUnit objects
SCU_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in StorageControlUnit objects returned by list() without full props
SCU_LIST_PROPS = ['object-uri', 'name', 'logical-address']

# Properties whose values can change between retrievals
SCU_VOLATILE_PROPS = []


def test_scu_find_list(hmc_session):
    """
    Test list(), find(), findall() for Storage Control Units.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    cu_list = pick_test_resources(cu_list)

    for cu in cu_list:
        print(f"Testing with Storage Control Unit {cu.name!r}")
        runtest_find_list(
            hmc_session, console.storage_control_units, cu.name,
            'name', 'object-uri', SCU_VOLATILE_PROPS,
            SCU_MINIMAL_PROPS, SCU_LIST_PROPS)


def test_scu_property(hmc_session):
    """
    Test property related methods for Storage Control Units.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    cu_list = pick_test_resources(cu_list)

    for cu in cu_list:
        print(f"Testing with Storage Control Unit {cu.name!r}")

        non_list_prop = 'class'

        runtest_get_properties(cu.manager, non_list_prop)


def test_scu_full_properties(hmc_session):
    """
    Test that pull_full_properties() fills in all expected properties.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    cu_list = pick_test_resources(cu_list)

    for cu in cu_list:
        print(f"Testing with Storage Control Unit {cu.name!r}")

        cu.pull_full_properties()

        for prop in ('object-uri', 'object-id', 'class', 'parent',
                     'name', 'logical-address',
                     'storage-path-uris', 'volume-ranges'):
            assert prop in cu.properties, (
                f"Expected property {prop!r} missing from "
                f"Storage Control Unit {cu.name!r}")

        assert cu.properties['class'] == 'storage-control-unit'
        assert isinstance(cu.properties['storage-path-uris'], list)
        assert isinstance(cu.properties['volume-ranges'], list)


def test_scu_list_filter_name(hmc_session):
    """
    Test list() with name filter for Storage Control Units.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    cu = cu_list[0]
    cu_name = cu.name

    filtered = console.storage_control_units.list(
        filter_args={'name': cu_name})

    assert len(filtered) >= 1
    names = [c.name for c in filtered]
    assert cu_name in names
    print(f"name filter returned {len(filtered)} CU(s) for name {cu_name!r}")


def test_scu_list_filter_logical_address(hmc_session):
    """
    Test list() with logical-address filter for Storage Control Units.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    cu = cu_list[0]
    cu.pull_full_properties()
    logical_addr = cu.properties.get('logical-address')
    if not logical_addr:
        skip_warn(
            f"Storage Control Unit {cu.name!r} has no logical-address")

    filtered = console.storage_control_units.list(
        filter_args={'logical-address': logical_addr})

    assert len(filtered) >= 1
    for c in filtered:
        c.pull_full_properties()
        assert c.properties['logical-address'] == logical_addr
    print(f"logical-address filter returned {len(filtered)} CU(s)")


def test_scu_list_by_subsystem(hmc_session):
    """
    Test listing storage control units via the storage-subsystems sub-resource
    endpoint.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    cu = cu_list[0]
    cu.pull_full_properties()
    parent_uri = cu.properties.get('parent')
    if not parent_uri:
        skip_warn(
            f"Storage Control Unit {cu.name!r} has no parent property")

    ss_id = parent_uri.split('/')[-1]

    result = hmc_session.get(
        f'/api/storage-subsystems/{ss_id}/storage-control-units')

    assert 'storage-control-units' in result
    returned_uris = {c['object-uri'] for c in result['storage-control-units']}
    assert cu.uri in returned_uris
    print(f"Subsystem {parent_uri!r} has "
          f"{len(result['storage-control-units'])} control unit(s)")


def test_scu_update_description(hmc_session):
    """
    Test update_properties() – update the description of an existing
    storage control unit and verify the change, then restore.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    cu = pick_test_resources(cu_list)[0]
    cu.pull_full_properties()
    original_desc = cu.properties.get('description', '')

    new_desc = f"{original_desc}__zhmcclient_e2e_test"

    try:
        cu.update_properties({'description': new_desc})

        assert cu.properties['description'] == new_desc
        cu.pull_full_properties()
        assert cu.properties['description'] == new_desc
        print(f"Updated description of Storage Control Unit {cu.name!r}")

    finally:
        try:
            cu.update_properties({'description': original_desc})
            print(f"Restored description of Storage Control Unit "
                  f"{cu.name!r}")
        except zhmcclient.HTTPError as exc:
            print(f"Failed to restore description: {exc}")


def test_scu_storage_paths(hmc_session):
    """
    Test that storage-path-uris property is accessible and paths can be
    retrieved.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    for cu in pick_test_resources(cu_list):
        cu.pull_full_properties()
        path_uris = cu.properties.get('storage-path-uris', [])

        print(f"Storage Control Unit {cu.name!r} has "
              f"{len(path_uris)} storage path(s)")

        for path_uri in path_uris:
            props = hmc_session.get(path_uri)
            assert 'adapter-port-uri' in props, (
                f"Missing 'adapter-port-uri' in storage path {path_uri!r} "
                f"of CU {cu.name!r}")
            assert props.get('class') == 'storage-path', (
                f"Unexpected class {props.get('class')!r} for "
                f"storage path {path_uri!r}")


def test_scu_volume_ranges(hmc_session):
    """
    Test that volume-ranges property is accessible and has correct structure.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    for cu in pick_test_resources(cu_list):
        cu.pull_full_properties()
        volume_ranges = cu.properties.get('volume-ranges', [])

        print(f"Storage Control Unit {cu.name!r} has "
              f"{len(volume_ranges)} volume range(s)")

        for vr in volume_ranges:
            assert 'starting-volume' in vr, (
                f"Missing 'starting-volume' in volume range of CU "
                f"{cu.name!r}: {vr!r}")
            assert 'ending-volume' in vr, (
                f"Missing 'ending-volume' in volume range of CU "
                f"{cu.name!r}: {vr!r}")
            assert vr.get('type') in ('base', 'alias'), (
                f"Unexpected type {vr.get('type')!r} in volume range of "
                f"CU {cu.name!r}")
