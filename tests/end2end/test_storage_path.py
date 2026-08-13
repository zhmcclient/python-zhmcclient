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
End2end tests for Storage Paths (on CPCs in DPM mode).

These tests exercise the list, get-properties, update-properties, create, and
delete operations on StoragePath element resources nested inside Storage Control
Units.  They do not permanently modify any existing resources.
"""


from requests.packages import urllib3

import zhmcclient

from .utils import skip_warn, pick_test_resources

urllib3.disable_warnings()

# Properties in minimalistic StoragePath objects returned by list()
PATH_MINIMAL_PROPS = ['element-uri']

# Properties expected on a fully-retrieved StoragePath
PATH_FULL_PROPS = [
    'element-uri',
    'element-id',
    'class',
    'parent',
    'adapter-port-uri',
]

# Properties that legitimately change between two retrievals
PATH_VOLATILE_PROPS = []


def _first_cu_with_paths(hmc_session, min_paths=1):
    """
    Return *(console, cu, path_list)* for the first Storage Control Unit that
    has at least *min_paths* storage paths, or ``None`` if none is found.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    cu_list = console.storage_control_units.list()
    for cu in cu_list:
        cu.pull_full_properties()
        path_list = cu.storage_paths.list(full_properties=True)
        if len(path_list) >= min_paths:
            return console, cu, path_list
    return None


# ── list() ────────────────────────────────────────────────────────────────────

def test_path_list(hmc_session):
    """
    Test StoragePathManager.list() returns StoragePath objects.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    for cu in pick_test_resources(cu_list):
        path_list = cu.storage_paths.list()
        print(f"CU {cu.name!r}: {len(path_list)} path(s) from list()")
        for path in path_list:
            assert isinstance(path, zhmcclient.StoragePath), (
                f"Expected StoragePath, got {type(path)!r}")


def test_path_list_full_properties(hmc_session):
    """
    Test StoragePathManager.list(full_properties=True) returns paths with all
    expected properties.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    for cu in pick_test_resources(cu_list):
        path_list = cu.storage_paths.list(full_properties=True)
        for path in path_list:
            for prop in PATH_FULL_PROPS:
                assert prop in path.properties, (
                    f"Expected property {prop!r} missing from storage path "
                    f"{path.uri!r} on CU {cu.name!r}")
            assert path.properties['class'] == 'storage-path', (
                f"Unexpected class {path.properties['class']!r} for "
                f"storage path {path.uri!r}")


# ── pull_full_properties() ────────────────────────────────────────────────────

def test_path_pull_full_properties(hmc_session):
    """
    Test StoragePath.pull_full_properties() populates all expected properties.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    found_path = False
    for cu in pick_test_resources(cu_list):
        path_list = cu.storage_paths.list()
        if not path_list:
            continue
        found_path = True
        path = path_list[0]
        path.pull_full_properties()
        for prop in PATH_FULL_PROPS:
            assert prop in path.properties, (
                f"Expected property {prop!r} missing after "
                f"pull_full_properties on path {path.uri!r} "
                f"of CU {cu.name!r}")
        break

    if not found_path:
        skip_warn(
            f"No Storage Control Unit on HMC {hd.host} has any storage paths")


# ── class and parent properties ───────────────────────────────────────────────

def test_path_class_property(hmc_session):
    """
    Test that the 'class' property of a StoragePath is 'storage-path'.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    found_path = False
    for cu in pick_test_resources(cu_list):
        path_list = cu.storage_paths.list(full_properties=True)
        if not path_list:
            continue
        found_path = True
        for path in path_list:
            assert path.properties.get('class') == 'storage-path', (
                f"Unexpected class {path.properties.get('class')!r} for "
                f"storage path {path.uri!r}")
        break

    if not found_path:
        skip_warn(
            f"No Storage Control Unit on HMC {hd.host} has any storage paths")


def test_path_parent_property(hmc_session):
    """
    Test that the 'parent' property of a StoragePath points to its CU URI.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    found_path = False
    for cu in pick_test_resources(cu_list):
        path_list = cu.storage_paths.list(full_properties=True)
        if not path_list:
            continue
        found_path = True
        for path in path_list:
            assert path.properties.get('parent') == cu.uri, (
                f"Expected parent {cu.uri!r}, got "
                f"{path.properties.get('parent')!r} for path {path.uri!r}")
        break

    if not found_path:
        skip_warn(
            f"No Storage Control Unit on HMC {hd.host} has any storage paths")


# ── adapter-port-uri ──────────────────────────────────────────────────────────

def test_path_adapter_port_uri(hmc_session):
    """
    Test that 'adapter-port-uri' is present and points to a valid adapter port.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    found_path = False
    for cu in pick_test_resources(cu_list):
        path_list = cu.storage_paths.list(full_properties=True)
        if not path_list:
            continue
        found_path = True
        for path in path_list:
            port_uri = path.properties.get('adapter-port-uri')
            assert port_uri, (
                f"Missing 'adapter-port-uri' on storage path {path.uri!r} "
                f"of CU {cu.name!r}")
            assert port_uri.startswith('/api/'), (
                f"Unexpected adapter-port-uri format {port_uri!r}")
        break

    if not found_path:
        skip_warn(
            f"No Storage Control Unit on HMC {hd.host} has any storage paths")


# ── Consistency: storage-path-uris on parent CU ───────────────────────────────

def test_path_uris_consistent_with_cu(hmc_session):
    """
    Test that the URIs returned by storage_paths.list() match the parent CU's
    storage-path-uris property.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    for cu in pick_test_resources(cu_list):
        cu.pull_full_properties()
        expected_uris = set(cu.properties.get('storage-path-uris', []))
        listed_paths = cu.storage_paths.list()
        listed_uris = {p.uri for p in listed_paths}
        assert listed_uris == expected_uris, (
            f"Mismatch between storage-path-uris ({expected_uris!r}) and "
            f"storage_paths.list() URIs ({listed_uris!r}) for CU {cu.name!r}")


# ── update_properties() ───────────────────────────────────────────────────────

def test_path_update_properties(hmc_session):
    """
    Test StoragePath.update_properties() - update a writeable property and
    verify the change is persisted, then restore the original value.

    Uses the first path found that has an 'exit-switch-uri' set, so we can
    toggle 'exit-port'.  If no paths have a switch, the test is skipped.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    target_path = None
    target_cu = None
    for cu in pick_test_resources(cu_list):
        path_list = cu.storage_paths.list(full_properties=True)
        for path in path_list:
            if path.properties.get('exit-switch-uri'):
                target_path = path
                target_cu = cu
                break
        if target_path:
            break

    if target_path is None:
        skip_warn(
            f"No storage path with an exit-switch-uri found on HMC {hd.host}; "
            "skipping update test")

    original_port = target_path.properties.get('exit-port', '')
    # Use a different port value that is unlikely to conflict
    new_port = 'ff' if original_port != 'ff' else 'fe'

    try:
        target_path.update_properties({'exit-port': new_port})
        assert target_path.properties['exit-port'] == new_port, (
            "Local property not updated by update_properties()")

        target_path.pull_full_properties()
        assert target_path.properties['exit-port'] == new_port, (
            f"HMC property not updated for path {target_path.uri!r} "
            f"of CU {target_cu.name!r}")
        print(f"Updated exit-port of path {target_path.uri!r} on "
              f"CU {target_cu.name!r}")

    finally:
        try:
            target_path.update_properties({'exit-port': original_port})
            print(f"Restored exit-port of path {target_path.uri!r}")
        except zhmcclient.HTTPError as exc:
            print(f"Failed to restore exit-port: {exc}")


# ── create() and delete() ─────────────────────────────────────────────────────

def test_path_create_and_delete(hmc_session):
    """
    Test creating a new StoragePath and then deleting it.

    The test looks for a CU that already has at least one path, picks the
    adapter-port-uri from that path, then creates a second path on a different
    adapter port (if available).  If no suitable resources exist the test is
    skipped.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    # Find a CU with at least one existing path (so we know the adapter-port
    # URI pattern) and that has fewer than 8 paths (so we can add one more).
    target_cu = None
    ref_port_uri = None
    for cu in pick_test_resources(cu_list):
        cu.pull_full_properties()
        path_list = cu.storage_paths.list(full_properties=True)
        if not path_list:
            continue
        if len(path_list) >= 8:
            continue  # Cannot add more paths
        # Use the same adapter-port-uri for simplicity — will fail if it
        # results in a duplicate; that is caught and skipped below.
        ref_port_uri = path_list[0].properties.get('adapter-port-uri')
        target_cu = cu
        break

    if target_cu is None:
        skip_warn(
            f"No suitable Storage Control Unit found on HMC {hd.host} for "
            "create/delete test (need < 8 existing paths and at least 1)")

    new_path = None
    try:
        try:
            new_path = target_cu.storage_paths.create({
                'adapter-port-uri': ref_port_uri,
            })
        except zhmcclient.HTTPError as exc:
            if exc.http_status == 400 and exc.reason == 8:
                skip_warn(
                    f"Duplicate path rejected by HMC {hd.host}; "
                    "skipping create/delete test")
            raise

        assert isinstance(new_path, zhmcclient.StoragePath), (
            f"create() did not return a StoragePath, got {type(new_path)!r}")
        assert new_path.uri.startswith(target_cu.uri + '/storage-paths/'), (
            f"Unexpected path URI {new_path.uri!r}")

        # Verify the new path appears in list()
        path_list_after = target_cu.storage_paths.list()
        uris = {p.uri for p in path_list_after}
        assert new_path.uri in uris, (
            f"Newly created path {new_path.uri!r} not found in list() result")

        # Verify the path URI appears in the parent CU's storage-path-uris
        target_cu.pull_full_properties()
        assert new_path.uri in target_cu.properties['storage-path-uris'], (
            f"Newly created path {new_path.uri!r} not in "
            f"CU storage-path-uris")

        print(f"Created path {new_path.uri!r} on CU {target_cu.name!r}")

    finally:
        if new_path is not None:
            try:
                new_path.delete()
                print(f"Deleted path {new_path.uri!r} on CU {target_cu.name!r}")
            except zhmcclient.HTTPError as exc:
                print(f"Failed to delete test path {new_path.uri!r}: {exc}")


def test_path_delete_removes_from_cu_uris(hmc_session):
    """
    Test that deleting a StoragePath removes its URI from the parent CU's
    storage-path-uris property.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    cu_list = console.storage_control_units.list()
    if not cu_list:
        skip_warn(f"No Storage Control Units defined on HMC {hd.host}")

    target_cu = None
    ref_port_uri = None
    for cu in pick_test_resources(cu_list):
        cu.pull_full_properties()
        path_list = cu.storage_paths.list(full_properties=True)
        if not path_list or len(path_list) >= 8:
            continue
        ref_port_uri = path_list[0].properties.get('adapter-port-uri')
        target_cu = cu
        break

    if target_cu is None:
        skip_warn(
            f"No suitable Storage Control Unit on HMC {hd.host} for "
            "delete consistency test")

    new_path = None
    try:
        try:
            new_path = target_cu.storage_paths.create({
                'adapter-port-uri': ref_port_uri,
            })
        except zhmcclient.HTTPError as exc:
            if exc.http_status == 400 and exc.reason == 8:
                skip_warn(
                    f"Duplicate path rejected on HMC {hd.host}; skipping test")
            raise

        path_uri = new_path.uri
        new_path.delete()
        new_path = None  # do not attempt cleanup again in finally

        target_cu.pull_full_properties()
        assert path_uri not in target_cu.properties['storage-path-uris'], (
            f"Deleted path {path_uri!r} still present in "
            f"CU storage-path-uris after delete")
        print(f"Verified deletion of {path_uri!r} from CU {target_cu.name!r}")

    finally:
        if new_path is not None:
            try:
                new_path.delete()
            except zhmcclient.HTTPError as exc:
                print(f"Failed to cleanup test path {new_path.uri!r}: {exc}")
