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
End2end tests for Storage Switches (on CPCs in DPM mode).

These tests create, modify, and delete test Storage Switches, and exercise
the move-to-site and move-to-fabric operations.
"""

import pytest
from requests.packages import urllib3

import zhmcclient

from .utils import skip_warn, pick_test_resources, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic StorageSwitch objects (e.g. find_by_name())
SSWITCH_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in StorageSwitch objects returned by list() without full props
SSWITCH_LIST_PROPS = ['object-uri', 'name', 'domain-id', 'storage-fabric-uri']

# Properties whose values can change between retrievals
SSWITCH_VOLATILE_PROPS = []


def test_sswitch_find_list(hmc_session):
    """
    Test list(), find(), findall() for Storage Switches.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    switch_list = console.storage_switches.list()
    if not switch_list:
        skip_warn(f"No Storage Switches defined on HMC {hd.host}")

    switch_list = pick_test_resources(switch_list)

    for switch in switch_list:
        print(f"Testing with Storage Switch {switch.name!r}")
        runtest_find_list(
            hmc_session, console.storage_switches, switch.name,
            'name', 'object-uri', SSWITCH_VOLATILE_PROPS,
            SSWITCH_MINIMAL_PROPS, SSWITCH_LIST_PROPS)


def test_sswitch_property(hmc_session):
    """
    Test property related methods for Storage Switches.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    switch_list = console.storage_switches.list()
    if not switch_list:
        skip_warn(f"No Storage Switches defined on HMC {hd.host}")

    switch_list = pick_test_resources(switch_list)

    for switch in switch_list:
        print(f"Testing with Storage Switch {switch.name!r}")

        # 'class' is not returned by list(), so use it as the non_list_prop
        non_list_prop = 'class'

        runtest_get_properties(switch.manager, non_list_prop)


def test_sswitch_full_properties(hmc_session):
    """
    Test that pull_full_properties() fills in all expected properties.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    switch_list = console.storage_switches.list()
    if not switch_list:
        skip_warn(f"No Storage Switches defined on HMC {hd.host}")

    switch_list = pick_test_resources(switch_list)

    for switch in switch_list:
        print(f"Testing with Storage Switch {switch.name!r}")

        switch.pull_full_properties()

        # Mandatory properties from the data model
        for prop in ('object-uri', 'object-id', 'class', 'parent',
                     'name', 'domain-id',
                     'storage-fabric-uri', 'storage-site-uri'):
            assert prop in switch.properties, (
                f"Expected property {prop!r} missing from "
                f"Storage Switch {switch.name!r}")

        assert switch.properties['class'] == 'storage-switch'
        assert isinstance(switch.properties['domain-id'], str)


def test_sswitch_list_filter_name(hmc_session):
    """
    Test list() with name filter for Storage Switches.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    switch_list = console.storage_switches.list()
    if not switch_list:
        skip_warn(f"No Storage Switches defined on HMC {hd.host}")

    switch = switch_list[0]
    switch_name = switch.name

    filtered = console.storage_switches.list(
        filter_args={'name': switch_name})

    assert len(filtered) >= 1
    names = [s.name for s in filtered]
    assert switch_name in names
    print(f"name filter returned {len(filtered)} switch(es) "
          f"for name {switch_name!r}")


def test_sswitch_list_filter_domain_id(hmc_session):
    """
    Test list() with domain-id filter for Storage Switches.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    switch_list = console.storage_switches.list()
    if not switch_list:
        skip_warn(f"No Storage Switches defined on HMC {hd.host}")

    switch = switch_list[0]
    switch.pull_full_properties()
    domain_id = switch.properties.get('domain-id')
    if not domain_id:
        skip_warn(
            f"Storage Switch {switch.name!r} has no domain-id property")

    filtered = console.storage_switches.list(
        filter_args={'domain-id': domain_id})

    assert len(filtered) >= 1
    for s in filtered:
        s.pull_full_properties()
        assert s.properties['domain-id'] == domain_id
    print(f"domain-id filter returned {len(filtered)} switch(es) "
          f"for domain-id {domain_id!r}")


def test_sswitch_list_by_fabric(hmc_session):
    """
    Test listing storage switches associated with a storage fabric.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    switch_list = console.storage_switches.list()
    if not switch_list:
        skip_warn(f"No Storage Switches defined on HMC {hd.host}")

    # Pull full properties to find a fabric URI
    switch = switch_list[0]
    switch.pull_full_properties()
    fabric_uri = switch.properties.get('storage-fabric-uri')
    if not fabric_uri:
        skip_warn(
            f"Storage Switch {switch.name!r} has no storage-fabric-uri")

    fabric_id = fabric_uri.split('/')[-1]

    result = hmc_session.get(
        f'/api/storage-fabrics/{fabric_id}/storage-switches')

    assert 'storage-switches' in result
    returned_uris = {s['object-uri'] for s in result['storage-switches']}
    assert switch.uri in returned_uris
    print(f"Fabric {fabric_uri!r} has "
          f"{len(result['storage-switches'])} switch(es)")


def test_sswitch_crud(hmc_session):
    """
    Test define, update properties, and undefine operations for Storage
    Switches.

    Requires at least one Storage Fabric and one Storage Site to be defined.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Need a fabric
    fabric_list = console.storage_fabrics.list()
    if not fabric_list:
        skip_warn(f"No Storage Fabrics defined on HMC {hd.host}")
    fabric = fabric_list[0]
    fabric.pull_full_properties()
    fabric_uri = fabric.uri

    # Need a site
    site_list = console.storage_sites.list()
    if not site_list:
        skip_warn(f"No Storage Sites defined on HMC {hd.host}")
    site = site_list[0]
    site_uri = site.uri

    switch_name = 'zhmcclient-e2e-storage-switch'
    switch_props = {
        'name': switch_name,
        'domain-id': '99',
        'storage-fabric-uri': fabric_uri,
        'storage-site-uri': site_uri,
        'description': 'Test storage switch for end-to-end testing',
    }

    # Clean up any leftover from a previous run
    try:
        existing = console.storage_switches.find(name=switch_name)
        existing.undefine()
        print(f"Cleaned up leftover Storage Switch {switch_name!r}")
    except zhmcclient.NotFound:
        pass

    # The code to be tested: Define
    switch = console.storage_switches.define(switch_props)

    try:
        assert switch.properties['name'] == switch_name
        assert switch.properties['storage-fabric-uri'] == fabric_uri
        print(f"Defined Storage Switch {switch.name!r}")

        # Pull full properties and verify
        switch.pull_full_properties()
        assert switch.properties['class'] == 'storage-switch'
        assert switch.properties['domain-id'] == '99'
        assert switch.properties['storage-site-uri'] == site_uri

        # The code to be tested: Update description
        new_desc = 'Updated description for e2e storage switch test'
        switch.update_properties({'description': new_desc})

        assert switch.properties['description'] == new_desc
        switch.pull_full_properties()
        assert switch.properties['description'] == new_desc
        print(f"Updated Storage Switch {switch.name!r} description")

        # The code to be tested: Rename
        renamed = switch_name + '-renamed'
        switch.update_properties({'name': renamed})
        switch.pull_full_properties()

        assert switch.properties['name'] == renamed
        with pytest.raises(zhmcclient.NotFound):
            console.storage_switches.find(name=switch_name)
        print(f"Renamed Storage Switch to {renamed!r}")

    finally:
        # Clean up: undefine the test switch
        try:
            switch.undefine()
            print("Undefined test Storage Switch")
        except zhmcclient.NotFound:
            pass


def test_sswitch_move_to_fabric(hmc_session):
    """
    Test the move-to-storage-fabric operation for a Storage Switch.

    Requires at least two Storage Fabrics and one Storage Site.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    fabric_list = console.storage_fabrics.list()
    if len(fabric_list) < 2:
        skip_warn(
            f"Need at least 2 Storage Fabrics on HMC {hd.host} "
            f"(found {len(fabric_list)})")

    site_list = console.storage_sites.list()
    if not site_list:
        skip_warn(f"No Storage Sites defined on HMC {hd.host}")

    fabric1 = fabric_list[0]
    fabric2 = fabric_list[1]
    site = site_list[0]

    switch_name = 'zhmcclient-e2e-storage-switch-move-fabric'

    # Clean up leftover
    try:
        existing = console.storage_switches.find(name=switch_name)
        existing.undefine()
    except zhmcclient.NotFound:
        pass

    switch = console.storage_switches.define({
        'name': switch_name,
        'domain-id': '98',
        'storage-fabric-uri': fabric1.uri,
        'storage-site-uri': site.uri,
    })

    try:
        switch.pull_full_properties()
        assert switch.properties['storage-fabric-uri'] == fabric1.uri

        # The code to be tested: Move to fabric2
        switch.move_to_storage_fabric(fabric2.uri)

        switch.pull_full_properties()
        assert switch.properties['storage-fabric-uri'] == fabric2.uri
        print(f"Moved Storage Switch {switch.name!r} "
              f"from {fabric1.name!r} to {fabric2.name!r}")

    finally:
        try:
            switch.undefine()
        except zhmcclient.NotFound:
            pass


def test_sswitch_move_to_site(hmc_session):
    """
    Test the move-to-storage-site operation for a Storage Switch.

    Requires at least one Storage Fabric and two Storage Sites.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    fabric_list = console.storage_fabrics.list()
    if not fabric_list:
        skip_warn(f"No Storage Fabrics defined on HMC {hd.host}")

    site_list = console.storage_sites.list()
    if len(site_list) < 2:
        skip_warn(
            f"Need at least 2 Storage Sites on HMC {hd.host} "
            f"(found {len(site_list)})")

    fabric = fabric_list[0]
    site1 = site_list[0]
    site2 = site_list[1]

    switch_name = 'zhmcclient-e2e-storage-switch-move-site'

    # Clean up leftover
    try:
        existing = console.storage_switches.find(name=switch_name)
        existing.undefine()
    except zhmcclient.NotFound:
        pass

    switch = console.storage_switches.define({
        'name': switch_name,
        'domain-id': '97',
        'storage-fabric-uri': fabric.uri,
        'storage-site-uri': site1.uri,
    })

    try:
        switch.pull_full_properties()
        assert switch.properties['storage-site-uri'] == site1.uri

        # The code to be tested: Move to site2
        switch.move_to_storage_site(site2.uri)

        switch.pull_full_properties()
        assert switch.properties['storage-site-uri'] == site2.uri
        print(f"Moved Storage Switch {switch.name!r} "
              f"from {site1.name!r} to {site2.name!r}")

    finally:
        try:
            switch.undefine()
        except zhmcclient.NotFound:
            pass
