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
End2end tests for Storage Fabrics (on CPCs in DPM mode).

These tests create, modify, and delete test Storage Fabrics.
"""

import pytest
from requests.packages import urllib3

import zhmcclient

from .utils import skip_warn, pick_test_resources, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Storage Fabric objects (e.g. find_by_name())
SFABRIC_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Storage Fabric objects returned by list() without full props
SFABRIC_LIST_PROPS = ['object-uri', 'name', 'cpc-uri']

# Properties whose values can change between retrievals
SFABRIC_VOLATILE_PROPS = []


def test_sfabric_find_list(hmc_session):
    """
    Test list(), find(), findall() for Storage Fabrics.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    fabric_list = console.storage_fabrics.list()
    if not fabric_list:
        skip_warn(f"No Storage Fabrics defined on HMC {hd.host}")

    fabric_list = pick_test_resources(fabric_list)

    for fabric in fabric_list:
        print(f"Testing with Storage Fabric {fabric.name!r}")
        runtest_find_list(
            hmc_session, console.storage_fabrics, fabric.name,
            'name', 'object-uri', SFABRIC_VOLATILE_PROPS,
            SFABRIC_MINIMAL_PROPS, SFABRIC_LIST_PROPS)


def test_sfabric_property(hmc_session):
    """
    Test property related methods for Storage Fabrics.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    fabric_list = console.storage_fabrics.list()
    if not fabric_list:
        skip_warn(f"No Storage Fabrics defined on HMC {hd.host}")

    fabric_list = pick_test_resources(fabric_list)

    for fabric in fabric_list:
        print(f"Testing with Storage Fabric {fabric.name!r}")

        # 'class' is not returned by list(), so use it as the non_list_prop
        non_list_prop = 'class'

        runtest_get_properties(fabric.manager, non_list_prop)


def test_sfabric_crud(hmc_session):
    """
    Test create, update, and delete operations for Storage Fabrics.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick a CPC to associate the fabric with
    cpc_list = client.cpcs.list()
    if not cpc_list:
        skip_warn(f"No CPCs defined on HMC {hd.host}")
    cpc = cpc_list[0]

    print(f"Testing with CPC {cpc.name!r}")

    fabric_name = 'zhmcclient-e2e-storage-fabric'
    fabric_props = {
        'name': fabric_name,
        'cpc-uri': cpc.uri,
        'description': 'Test storage fabric for end-to-end testing',
        'high-integrity': False,
    }

    # Clean up any leftover from a previous run
    try:
        existing = console.storage_fabrics.find(name=fabric_name)
        existing.delete()
        print(f"Cleaned up leftover Storage Fabric {fabric_name!r}")
    except zhmcclient.NotFound:
        pass

    # The code to be tested: Create
    fabric = console.storage_fabrics.create(fabric_props)

    try:
        assert fabric.properties['name'] == fabric_name
        assert fabric.properties['cpc-uri'] == cpc.uri
        print(f"Created Storage Fabric {fabric.name!r}")

        # Pull full properties and verify defaults
        fabric.pull_full_properties()
        assert fabric.properties['class'] == 'storage-fabric'
        assert isinstance(fabric.properties['storage-switch-uris'], list)
        assert fabric.properties['high-integrity'] is False

        # The code to be tested: Update description
        new_desc = 'Updated description for e2e storage fabric test'
        fabric.update_properties({'description': new_desc})

        assert fabric.properties['description'] == new_desc
        fabric.pull_full_properties()
        assert fabric.properties['description'] == new_desc
        print(f"Updated Storage Fabric {fabric.name!r} description")

        # The code to be tested: Rename
        renamed = fabric_name + '-renamed'
        fabric.update_properties({'name': renamed})
        fabric.pull_full_properties()

        assert fabric.properties['name'] == renamed
        with pytest.raises(zhmcclient.NotFound):
            console.storage_fabrics.find(name=fabric_name)
        print(f"Renamed Storage Fabric to {renamed!r}")

    finally:
        # Clean up: delete the test fabric
        try:
            fabric.delete()
            print(f"Deleted test Storage Fabric {fabric.name!r}")
        except zhmcclient.NotFound:
            pass


def test_sfabric_list_filter_cpc_uri(hmc_session):
    """
    Test list() with cpc-uri filter for Storage Fabrics.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    fabric_list = console.storage_fabrics.list()
    if not fabric_list:
        skip_warn(f"No Storage Fabrics defined on HMC {hd.host}")

    # Pull full properties on the first fabric to get its cpc-uri
    fabric = fabric_list[0]
    fabric.pull_full_properties()
    cpc_uri = fabric.properties.get('cpc-uri')
    if not cpc_uri:
        skip_warn(
            f"Storage Fabric {fabric.name!r} has no cpc-uri property")

    # Filter by cpc-uri
    filtered = console.storage_fabrics.list(
        filter_args={'cpc-uri': cpc_uri})

    # All returned fabrics must have the matching cpc-uri
    for f in filtered:
        f.pull_full_properties()
        assert f.properties['cpc-uri'] == cpc_uri, (
            f"Fabric {f.name!r} cpc-uri {f.properties['cpc-uri']!r} "
            f"does not match filter {cpc_uri!r}"
        )
    print(f"cpc-uri filter returned {len(filtered)} fabric(s) "
          f"for cpc-uri {cpc_uri!r}")


def test_sfabric_full_properties(hmc_session):
    """
    Test that pull_full_properties() fills in all expected properties.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    fabric_list = console.storage_fabrics.list()
    if not fabric_list:
        skip_warn(f"No Storage Fabrics defined on HMC {hd.host}")

    fabric_list = pick_test_resources(fabric_list)

    for fabric in fabric_list:
        print(f"Testing with Storage Fabric {fabric.name!r}")

        fabric.pull_full_properties()

        # Mandatory properties from the data model
        for prop in ('object-uri', 'object-id', 'class', 'parent',
                     'name', 'cpc-uri', 'storage-switch-uris',
                     'high-integrity'):
            assert prop in fabric.properties, (
                f"Expected property {prop!r} missing from "
                f"Storage Fabric {fabric.name!r}")

        assert fabric.properties['class'] == 'storage-fabric'
        assert isinstance(fabric.properties['storage-switch-uris'], list)
        assert isinstance(fabric.properties['high-integrity'], bool)
