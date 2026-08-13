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
End2end tests for Storage Site (on CPCs in DPM mode).

These tests do not change any existing primary Storage Site, but create,
modify, and delete alternate test Storage Sites.

A primary site (with default name "Primary Site") exists by default and cannot
be deleted. Alternate sites can be created and deleted.
"""


import uuid
import pytest
from requests.packages import urllib3

import zhmcclient

from .utils import skip_log, pick_test_resources, TEST_PREFIX, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic StorageSite objects (e.g. find_by_name())
SS_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in StorageSite objects returned by list() without full props
SS_LIST_PROPS = ['object-uri', 'name', 'cpc-uris']

# Properties whose values can change between retrievals of StorageSite objs
SS_VOLATILE_PROPS = []


def test_ss_find_list(zhmc_logger, hmc_session):
    """
    Test list(), find(), findall() on existing storage sites.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the storage sites to test with
    ss_list = console.storage_sites.list()
    if not ss_list:
        skip_log(zhmc_logger,
                 f"No storage sites defined on HMC {hd.host}")
    ss_list = pick_test_resources(ss_list)

    for ss in ss_list:
        print(f"Testing with Storage Site {ss.name!r}")
        runtest_find_list(
            hmc_session, console.storage_sites, ss.name,
            'name', 'object-uri', SS_VOLATILE_PROPS,
            SS_MINIMAL_PROPS, SS_LIST_PROPS)


def test_ss_property(zhmc_logger, hmc_session):
    """
    Test property-related methods (pull_full_properties, get_property, etc.)
    on existing storage sites.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Pick the storage sites to test with
    ss_list = console.storage_sites.list()
    if not ss_list:
        skip_log(zhmc_logger,
                 f"No storage sites defined on HMC {hd.host}")
    ss_list = pick_test_resources(ss_list)

    for ss in ss_list:
        print(f"Testing with Storage Site {ss.name!r}")

        # Select a property that is not returned by list()
        non_list_prop = 'description'

        runtest_get_properties(ss.manager, non_list_prop)


def test_ss_list_filter_by_name(zhmc_logger, hmc_session):
    """
    Test list() with a name filter argument.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Get all storage sites
    all_sites = console.storage_sites.list()
    if not all_sites:
        skip_log(zhmc_logger,
                 f"No storage sites defined on HMC {hd.host}")

    # Pick one site to filter by
    target_site = all_sites[0]
    target_name = target_site.name

    # The code to be tested: list() with name filter
    filtered_sites = console.storage_sites.list(
        filter_args={'name': target_name})

    assert len(filtered_sites) >= 1, (
        f"Expected at least 1 site with name {target_name!r}, got 0")
    names = [s.name for s in filtered_sites]
    assert target_name in names, (
        f"Expected site {target_name!r} in filtered list {names!r}")


def test_ss_list_short_and_full_props(zhmc_logger, hmc_session):
    """
    Test list() returns correct properties in short and full-properties mode.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    all_sites = console.storage_sites.list()
    if not all_sites:
        skip_log(zhmc_logger,
                 f"No storage sites defined on HMC {hd.host}")

    # Verify that list() (short props) includes the expected properties
    for ss in all_sites:
        for prop_name in SS_LIST_PROPS:
            assert prop_name in ss.properties, (
                f"Expected property {prop_name!r} missing in list() result "
                f"for storage site {ss.name!r}")

    # Verify that list(full_properties=True) includes at least all short props
    # plus 'description'
    full_sites = console.storage_sites.list(full_properties=True)
    for ss in full_sites:
        for prop_name in SS_LIST_PROPS + ['description']:
            assert prop_name in ss.properties, (
                f"Expected property {prop_name!r} missing in full list() "
                f"result for storage site {ss.name!r}")


def test_ss_crud(zhmc_logger, hmc_session):
    """
    Test create, read, update and delete an alternate storage site.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    ss_name = f"{TEST_PREFIX}_crud_{uuid.uuid4().hex}"
    ss_name_new = ss_name + '_renamed'

    # Find a DPM-mode CPC on this HMC to use as the cpc-uri
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        skip_log(zhmc_logger,
                 f"No DPM-mode CPC on HMC {hd.host} for storage site test")
    cpc = cpcs[0]

    ss_input_props = {
        'name': ss_name,
        'description': 'Test storage site for zhmcclient end2end tests',
        'cpc-uris': [cpc.uri],
    }

    ss = None
    try:
        # Test creating a storage site
        print(f"Creating storage site {ss_name!r}")

        # The code to be tested
        ss = console.storage_sites.create(ss_input_props)

        assert isinstance(ss, zhmcclient.StorageSite), (
            f"Expected StorageSite, got {type(ss)}")

        # Verify the initial properties match what was specified
        for pn, exp_value in ss_input_props.items():
            assert ss.properties[pn] == exp_value, (
                f"Unexpected value for property {pn!r} of storage site:\n"
                f"{ss.properties!r}")

        # Verify after pulling full properties
        ss.pull_full_properties()
        for pn, exp_value in ss_input_props.items():
            assert ss.properties[pn] == exp_value, (
                f"Unexpected value for property {pn!r} after pull:\n"
                f"{ss.properties!r}")

        # Test that the storage site can be found by name
        found_ss = console.storage_sites.find(name=ss_name)
        assert found_ss.name == ss_name

        # Test updating the description
        new_desc = 'Updated storage site description for zhmcclient tests'
        print(f"Updating description of storage site {ss_name!r}")

        # The code to be tested
        ss.update_properties({'description': new_desc})

        assert ss.properties['description'] == new_desc
        ss.pull_full_properties()
        assert ss.properties['description'] == new_desc

        # Test renaming the storage site
        print(f"Renaming storage site {ss_name!r} to {ss_name_new!r}")

        # The code to be tested
        ss.update_properties({'name': ss_name_new})

        assert ss.properties['name'] == ss_name_new
        ss.pull_full_properties()
        assert ss.properties['name'] == ss_name_new

        # Verify the old name is gone
        with pytest.raises(zhmcclient.NotFound):
            console.storage_sites.find(name=ss_name)

        # Verify the new name can be found
        found_ss = console.storage_sites.find(name=ss_name_new)
        assert found_ss.name == ss_name_new

    finally:
        # Test deleting the storage site
        if ss:
            print(f"Deleting storage site {ss.name!r}")

            # The code to be tested
            ss.delete()

            with pytest.raises(zhmcclient.NotFound):
                console.storage_sites.find(name=ss_name_new)


SS_CREATE_DELETE_TESTCASES = [
    # Testcases for test_ss_create_delete().
    # Each item is a tuple:
    # - desc (string): Description of the testcase.
    # - input_props (dict): Input properties for create(), excluding 'name'
    #   and 'cpc-uris' which are added by the test function.
    # - exp_props (dict): Expected properties in the created storage site,
    #   beyond what was specified as input (i.e. server-set defaults).
    #   'name' and 'cpc-uris' are checked separately.
    # - exp_exc_type (class or None): Exception type expected from create(),
    #   or None if no exception is expected.
    (
        "Minimal input properties (name + cpc-uris only)",
        {},
        {
            'description': '',  # default empty string
            'class': 'storage-site',
        },
        None,
    ),
    (
        "With description",
        {
            'description': 'Alternate site with description',
        },
        {
            'description': 'Alternate site with description',
            'class': 'storage-site',
        },
        None,
    ),
]


@pytest.mark.parametrize(
    "desc, input_props, exp_props, exp_exc_type",
    SS_CREATE_DELETE_TESTCASES)
def test_ss_create_delete(
        zhmc_logger, hmc_session,
        desc, input_props, exp_props, exp_exc_type):
    # pylint: disable=unused-argument
    """
    Test creation of a storage site with various property combinations,
    and verify properties, then delete it.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Find a DPM-mode CPC to reference
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        skip_log(zhmc_logger,
                 f"No DPM-mode CPC on HMC {hd.host} for storage site test")
    cpc = cpcs[0]

    ss_name = f"{TEST_PREFIX}_cre_del_{uuid.uuid4().hex}"

    ss_input_props = {
        'name': ss_name,
        'cpc-uris': [cpc.uri],
    }
    ss_input_props.update(input_props)

    ss = None
    try:
        if exp_exc_type:
            with pytest.raises(exp_exc_type):
                # The code to be tested
                ss = console.storage_sites.create(ss_input_props)
        else:
            # The code to be tested
            ss = console.storage_sites.create(ss_input_props)

            assert isinstance(ss, zhmcclient.StorageSite)

            ss.pull_full_properties()

            # Verify specified input properties
            for pn, exp_value in ss_input_props.items():
                assert ss.properties[pn] == exp_value, (
                    f"Property {pn!r}: expected {exp_value!r}, "
                    f"got {ss.properties.get(pn)!r}")

            # Verify expected server-side properties
            for pn, exp_value in exp_props.items():
                assert pn in ss.properties, (
                    f"Expected property {pn!r} not found in created site")
                assert ss.properties[pn] == exp_value, (
                    f"Property {pn!r}: expected {exp_value!r}, "
                    f"got {ss.properties[pn]!r}")

    finally:
        if ss:
            ss.delete()
            with pytest.raises(zhmcclient.NotFound):
                console.storage_sites.find(name=ss_name)


def test_ss_update_properties(zhmc_logger, hmc_session):
    """
    Test update_properties() on an alternate storage site.
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Find a DPM-mode CPC to reference
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        skip_log(zhmc_logger,
                 f"No DPM-mode CPC on HMC {hd.host} for storage site test")
    cpc = cpcs[0]

    ss_name = f"{TEST_PREFIX}_upd_{uuid.uuid4().hex}"

    ss = None
    try:
        ss = console.storage_sites.create({
            'name': ss_name,
            'description': 'Original description',
            'cpc-uris': [cpc.uri],
        })

        # Test updating description
        new_desc = 'Updated description for end2end test'
        ss.update_properties({'description': new_desc})
        assert ss.properties['description'] == new_desc
        ss.pull_full_properties()
        assert ss.properties['description'] == new_desc

        # Test updating to empty description
        ss.update_properties({'description': ''})
        assert ss.properties['description'] == ''
        ss.pull_full_properties()
        assert ss.properties['description'] == ''

    finally:
        if ss:
            ss.delete()


def test_ss_delete_nonexistent(zhmc_logger, hmc_session):
    """
    Test that deleting a storage site that was already deleted raises NotFound
    on a subsequent find().
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console
    hd = hmc_session.hmc_definition

    # Find a DPM-mode CPC to reference
    cpcs = client.cpcs.list(filter_args={'dpm-enabled': True})
    if not cpcs:
        skip_log(zhmc_logger,
                 f"No DPM-mode CPC on HMC {hd.host} for storage site test")
    cpc = cpcs[0]

    ss_name = f"{TEST_PREFIX}_del2_{uuid.uuid4().hex}"

    ss = console.storage_sites.create({
        'name': ss_name,
        'cpc-uris': [cpc.uri],
    })

    # Delete it once — should succeed
    ss.delete()

    # Verify it is gone
    with pytest.raises(zhmcclient.NotFound):
        console.storage_sites.find(name=ss_name)


def test_ss_zzz_cleanup(zhmc_logger, hmc_session):
    # pylint: disable=unused-argument
    """
    Cleanup any test storage sites that may have been left over from prior
    test runs (e.g. due to test failures).
    """
    client = zhmcclient.Client(hmc_session)
    console = client.consoles.console

    name_pattern = fr'{TEST_PREFIX}.*'
    sites = console.storage_sites.findall(name=name_pattern)
    for ss in sites:

        print("Deleting leftover test storage site from a prior run: "
              f"{ss.name!r} - please open a zhmcclient issue for that")

        try:
            ss.delete()
        except zhmcclient.HTTPError as exc:
            print(f"HTTPError during StorageSite.delete(): {exc}")
