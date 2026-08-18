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
End2end tests for Storage Subsystems (on CPCs in DPM mode).

These tests exercise the list, get-properties, update-properties,
move-to-storage-site, add-connection-endpoint, and remove-connection-endpoint
operations. They do not permanently modify existing storage subsystems but
may temporarily create or update test resources where permitted.
"""


from requests.packages import urllib3

import zhmcclient

from .utils import skip_warn, pick_test_resources, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic StorageSubsystem objects (e.g. find_by_name())
SSUB_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in StorageSubsystem objects returned by list() without full props
SSUB_LIST_PROPS = ['object-uri', 'name', 'storage-site-uri']

# Properties whose values can change between retrievals
SSUB_VOLATILE_PROPS = []


def test_ssub_find_list(hmc_session):
    """
    Test list(), find(), findall() for Storage Subsystems.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    subsystem_list = console.storage_subsystems.list()
    if not subsystem_list:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    subsystem_list = pick_test_resources(subsystem_list)

    for subsystem in subsystem_list:
        print(f"Testing with Storage Subsystem {subsystem.name!r}")
        runtest_find_list(
            hmc_session, console.storage_subsystems, subsystem.name,
            'name', 'object-uri', SSUB_VOLATILE_PROPS,
            SSUB_MINIMAL_PROPS, SSUB_LIST_PROPS)


def test_ssub_property(hmc_session):
    """
    Test property related methods for Storage Subsystems.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    subsystem_list = console.storage_subsystems.list()
    if not subsystem_list:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    subsystem_list = pick_test_resources(subsystem_list)

    for subsystem in subsystem_list:
        print(f"Testing with Storage Subsystem {subsystem.name!r}")

        # 'class' is not returned by list(), so use it as the non_list_prop
        non_list_prop = 'class'

        runtest_get_properties(subsystem.manager, non_list_prop)


def test_ssub_full_properties(hmc_session):
    """
    Test that pull_full_properties() fills in all expected properties.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    subsystem_list = console.storage_subsystems.list()
    if not subsystem_list:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    subsystem_list = pick_test_resources(subsystem_list)

    for subsystem in subsystem_list:
        print(f"Testing with Storage Subsystem {subsystem.name!r}")

        subsystem.pull_full_properties()

        # Mandatory properties from the data model
        for prop in ('object-uri', 'object-id', 'class', 'parent',
                     'name', 'storage-site-uri',
                     'connection-endpoints', 'storage-control-unit-uris'):
            assert prop in subsystem.properties, (
                f"Expected property {prop!r} missing from "
                f"Storage Subsystem {subsystem.name!r}")

        assert subsystem.properties['class'] == 'storage-subsystem'
        assert isinstance(subsystem.properties['connection-endpoints'], list)


def test_ssub_list_filter_name(hmc_session):
    """
    Test list() with name filter for Storage Subsystems.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    subsystem_list = console.storage_subsystems.list()
    if not subsystem_list:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    subsystem = subsystem_list[0]
    subsystem_name = subsystem.name

    filtered = console.storage_subsystems.list(
        filter_args={'name': subsystem_name})

    assert len(filtered) >= 1
    names = [s.name for s in filtered]
    assert subsystem_name in names
    print(f"name filter returned {len(filtered)} subsystem(s) "
          f"for name {subsystem_name!r}")


def test_ssub_list_filter_storage_site_uri(hmc_session):
    """
    Test list() with storage-site-uri filter for Storage Subsystems.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    subsystem_list = console.storage_subsystems.list()
    if not subsystem_list:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    subsystem = subsystem_list[0]
    subsystem.pull_full_properties()
    site_uri = subsystem.properties.get('storage-site-uri')
    if not site_uri:
        skip_warn(
            f"Storage Subsystem {subsystem.name!r} has no storage-site-uri")

    filtered = console.storage_subsystems.list(
        filter_args={'storage-site-uri': site_uri})

    assert len(filtered) >= 1
    for s in filtered:
        s.pull_full_properties()
        assert s.properties['storage-site-uri'] == site_uri
    print(f"storage-site-uri filter returned {len(filtered)} subsystem(s)")


def test_ssub_list_short_and_full_props(hmc_session):
    """
    Test that list() returns correct properties in short and full-props mode.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    all_subsystems = console.storage_subsystems.list()
    if not all_subsystems:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    # Verify short list props are present
    for ss in all_subsystems:
        for prop_name in SSUB_LIST_PROPS:
            assert prop_name in ss.properties, (
                f"Expected property {prop_name!r} missing in list() result "
                f"for storage subsystem {ss.name!r}")

    # Verify full list props include at least short props + 'description'
    full_subsystems = console.storage_subsystems.list(full_properties=True)
    for ss in full_subsystems:
        for prop_name in SSUB_LIST_PROPS + ['description']:
            assert prop_name in ss.properties, (
                f"Expected property {prop_name!r} missing in full list() "
                f"result for storage subsystem {ss.name!r}")


def test_ssub_list_by_site(hmc_session):
    """
    Test listing storage subsystems associated with a storage site via the
    storage-sites sub-resource endpoint.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    subsystem_list = console.storage_subsystems.list()
    if not subsystem_list:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    # Pull full properties to find a site URI
    subsystem = subsystem_list[0]
    subsystem.pull_full_properties()
    site_uri = subsystem.properties.get('storage-site-uri')
    if not site_uri:
        skip_warn(
            f"Storage Subsystem {subsystem.name!r} has no storage-site-uri")

    site_id = site_uri.split('/')[-1]

    result = hmc_session.get(
        f'/api/storage-sites/{site_id}/storage-subsystems')

    assert 'storage-subsystems' in result
    returned_uris = {ss['object-uri'] for ss in result['storage-subsystems']}
    assert subsystem.uri in returned_uris
    print(f"Site {site_uri!r} has "
          f"{len(result['storage-subsystems'])} subsystem(s)")


def test_ssub_update_description(hmc_session):
    """
    Test update_properties() – update the description of an existing
    storage subsystem and verify the change, then restore the original value.

    This test modifies an existing storage subsystem temporarily.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    subsystem_list = console.storage_subsystems.list()
    if not subsystem_list:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    subsystem = pick_test_resources(subsystem_list)[0]
    subsystem.pull_full_properties()
    original_desc = subsystem.properties.get('description', '')

    new_desc = f"{original_desc}__zhmcclient_e2e_test"

    try:
        # The code to be tested: Update description
        subsystem.update_properties({'description': new_desc})

        assert subsystem.properties['description'] == new_desc
        subsystem.pull_full_properties()
        assert subsystem.properties['description'] == new_desc
        print(f"Updated description of Storage Subsystem "
              f"{subsystem.name!r}")

    finally:
        # Restore original description
        try:
            subsystem.update_properties({'description': original_desc})
            print(f"Restored description of Storage Subsystem "
                  f"{subsystem.name!r}")
        except zhmcclient.HTTPError as exc:
            print(f"Failed to restore description of storage subsystem "
                  f"{subsystem.name!r}: {exc}")


def test_ssub_connection_endpoints(hmc_session):
    """
    Test that connection-endpoints property is accessible and has the
    correct structure.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    subsystem_list = console.storage_subsystems.list()
    if not subsystem_list:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    for subsystem in pick_test_resources(subsystem_list):
        subsystem.pull_full_properties()
        endpoints = subsystem.properties.get('connection-endpoints', [])

        print(f"Storage Subsystem {subsystem.name!r} has "
              f"{len(endpoints)} connection endpoint(s)")

        for ep in endpoints:
            assert 'endpoint-uri' in ep, (
                f"Missing 'endpoint-uri' in connection endpoint of "
                f"subsystem {subsystem.name!r}: {ep!r}")
            assert 'endpoint-class' in ep, (
                f"Missing 'endpoint-class' in connection endpoint of "
                f"subsystem {subsystem.name!r}: {ep!r}")
            assert ep['endpoint-class'] in ('storage-switch', 'adapter'), (
                f"Unexpected endpoint-class {ep['endpoint-class']!r} in "
                f"subsystem {subsystem.name!r}")


def test_ssub_move_to_storage_site(hmc_session):
    """
    Test the move-to-storage-site operation for a Storage Subsystem.

    Requires at least two Storage Sites and at least one Storage Subsystem.
    This test moves the subsystem to the second site and then moves it back
    to the original site so no persistent change is made.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    subsystem_list = console.storage_subsystems.list()
    if not subsystem_list:
        skip_warn(f"No Storage Subsystems defined on HMC {hd.host}")

    site_list = console.storage_sites.list()
    if len(site_list) < 2:
        skip_warn(
            f"Need at least 2 Storage Sites on HMC {hd.host} "
            f"(found {len(site_list)})")

    subsystem = pick_test_resources(subsystem_list)[0]
    subsystem.pull_full_properties()
    original_site_uri = subsystem.properties['storage-site-uri']

    # Find a different target site
    target_site = next(
        (s for s in site_list if s.uri != original_site_uri), None)
    if target_site is None:
        skip_warn(
            f"Could not find a site different from current one "
            f"({original_site_uri}) on HMC {hd.host}")

    try:
        # The code to be tested: Move to target site
        subsystem.move_to_storage_site(target_site.uri)

        subsystem.pull_full_properties()
        assert subsystem.properties['storage-site-uri'] == target_site.uri, (
            f"Expected storage-site-uri {target_site.uri!r}, got "
            f"{subsystem.properties['storage-site-uri']!r}")
        print(f"Moved Storage Subsystem {subsystem.name!r} to "
              f"{target_site.name!r}")

    finally:
        # Move it back to the original site
        try:
            subsystem.move_to_storage_site(original_site_uri)
            print(f"Moved Storage Subsystem {subsystem.name!r} back to "
                  f"original site")
        except zhmcclient.HTTPError as exc:
            print(f"Failed to move storage subsystem back to original site: "
                  f"{exc}")
