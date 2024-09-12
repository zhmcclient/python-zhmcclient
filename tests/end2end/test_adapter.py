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
End2end tests for adapters (on CPCs in DPM mode).

These tests do not change any existing adapters, but create, modify
and delete Hipersocket adapters.
"""


import uuid
import warnings
import pdb
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs, all_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    standard_partition_props, runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Adapter objects (e.g. find_by_name())
ADAPTER_MINIMAL_PROPS = ['object-uri', 'name']

# Properties in Adapter objects returned by list() without full props
ADAPTER_LIST_PROPS = ['object-uri', 'name', 'adapter-id', 'adapter-family',
                      'type', 'status']

# Properties in Adapter objects for list(additional_properties)
ADAPTER_ADDITIONAL_PROPS = ['description', 'detected-card-type']

# Properties whose values can change between retrievals of Adapter objects
ADAPTER_VOLATILE_PROPS = []


def test_adapter_find_list(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test list(), find(), findall().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the adapters to test with
        adapter_list = cpc.adapters.list()
        if not adapter_list:
            skip_warn(f"No adapters on CPC {cpc.name} managed by HMC {hd.host}")
        adapter_list = pick_test_resources(adapter_list)

        for adapter in adapter_list:
            print(f"Testing on CPC {cpc.name} with adapter {adapter.name!r}")
            runtest_find_list(
                session, cpc.adapters, adapter.name, 'name', 'object-uri',
                ADAPTER_VOLATILE_PROPS, ADAPTER_MINIMAL_PROPS,
                ADAPTER_LIST_PROPS, ADAPTER_ADDITIONAL_PROPS)


def test_adapter_property(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test property related methods
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        # Pick the adapters to test with
        adapter_list = cpc.adapters.list()
        if not adapter_list:
            skip_warn(f"No adapters on CPC {cpc.name} managed by HMC {hd.host}")
        adapter_list = pick_test_resources(adapter_list)

        for adapter in adapter_list:
            print(f"Testing on CPC {cpc.name} with adapter {adapter.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(adapter.manager, non_list_prop)


def test_adapter_hs_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a Hipersocket adapter.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print(f"Testing on CPC {cpc.name}")

        adapter_name = TEST_PREFIX + ' test_adapter_crud adapter1'
        adapter_name_new = adapter_name + ' new'

        # Ensure a clean starting point for this test
        try:
            adapter = cpc.adapters.find(name=adapter_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test Hipersocket adapter from previous run: "
                f"{adapter_name!r} on CPC {cpc.name}", UserWarning)
            adapter.delete()
        try:
            adapter = cpc.adapters.find(name=adapter_name_new)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test Hipersocket adapter from previous run: "
                f"{adapter_name_new!r} on CPC {cpc.name}", UserWarning)
            adapter.delete()

        # Create a Hipersocket adapter
        adapter_input_props = {
            'name': adapter_name,
            'description': 'Test adapter for zhmcclient end2end tests',
        }
        adapter_auto_props = {
            'type': 'hipersockets',
        }

        # The code to be tested
        adapter = cpc.adapters.create_hipersocket(adapter_input_props)

        for pn, exp_value in adapter_input_props.items():
            assert adapter.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"
        adapter.pull_full_properties()
        for pn, exp_value in adapter_input_props.items():
            assert adapter.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"
        for pn, exp_value in adapter_auto_props.items():
            assert adapter.properties[pn] == exp_value, \
                f"Unexpected value for property {pn!r}"

        # Test updating a property of the adapter

        new_desc = "Updated adapter description."

        # The code to be tested
        adapter.update_properties(dict(description=new_desc))

        assert adapter.properties['description'] == new_desc
        adapter.pull_full_properties()
        assert adapter.properties['description'] == new_desc

        # Test renaming the adapter

        # The code to be tested
        adapter.update_properties(dict(name=adapter_name_new))

        assert adapter.properties['name'] == adapter_name_new
        adapter.pull_full_properties()
        assert adapter.properties['name'] == adapter_name_new
        with pytest.raises(zhmcclient.NotFound):
            cpc.adapters.find(name=adapter_name)

        # Test deleting the adapter

        # The code to be tested
        adapter.delete()

        with pytest.raises(zhmcclient.NotFound):
            cpc.adapters.find(name=adapter_name_new)


def test_adapter_list_assigned_part(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test Adapter.list_assigned_partitions().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        required_families = [
            'hipersockets',
            'osa',
            'roce',
            'cna',
            'ficon',
            'accelerator',
            'crypto',
            'nvme',
            'coupling',
            'ism',
            'zhyperlink',
        ]
        family_adapters = {}
        for family in required_families:
            family_adapters[family] = []

        # List all adapters on the CPC and group by family
        adapter_list = cpc.adapters.list()
        for adapter in adapter_list:
            family = adapter.get_property('adapter-family')
            if family not in family_adapters:
                warnings.warn(
                    f"Ignoring adapter {adapter.name!r} on CPC {cpc.name} with "
                    f"an unknown family: '{family}'", UserWarning)
                continue
            if adapter.get_property('type') == 'osm':
                # Skip OSM adapters since they cannot be assigned to partitions
                continue
            family_adapters[family].append(adapter)

        tmp_part = None
        try:

            # Create a temporary partition for test purposes
            part_name = f"{TEST_PREFIX}_{uuid.uuid4().hex}"
            part_props = standard_partition_props(cpc, part_name)
            tmp_part = cpc.partitions.create(part_props)

            for family, all_adapters in family_adapters.items():
                if not all_adapters:
                    warnings.warn(
                        f"CPC {cpc.name} has no adapters of family '{family}'",
                        UserWarning)
                    continue

                if family in ('hipersockets', 'osa'):

                    test_adapters = pick_test_resources(all_adapters)
                    for test_adapter in test_adapters:
                        print(f"Testing on CPC {cpc.name} with adapter "
                              f"{test_adapter.name!r} (family '{family}')")

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        # Find the virtual switch for the test adapter
                        filter_args = {'backing-adapter-uri': test_adapter.uri}
                        vswitches = cpc.virtual_switches.list(
                            filter_args=filter_args)
                        assert len(vswitches) >= 1
                        vswitch = vswitches[0]

                        # Create a NIC in the temporary partition
                        nic_name = f"{family}_{uuid.uuid4().hex}"
                        nic_props = {
                            'name': nic_name,
                            'virtual-switch-uri': vswitch.uri,
                        }
                        tmp_part.nics.create(nic_props)

                        # The method to be tested
                        after_parts = test_adapter.list_assigned_partitions()

                        before_uris = [p.uri for p in before_parts]
                        new_parts = []
                        for part in after_parts:
                            if part.uri not in before_uris:
                                new_parts.append(part)

                        assert len(new_parts) == 1
                        new_part = new_parts[0]
                        assert new_part.uri == tmp_part.uri

                elif family in ('roce', 'cna'):

                    test_adapters = pick_test_resources(all_adapters)
                    for test_adapter in test_adapters:
                        print(f"Testing on CPC {cpc.name} with adapter "
                              f"{test_adapter.name!r} (family '{family}')")

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        test_port = test_adapter.ports.list()[0]

                        # Create a NIC in the temporary partition
                        nic_name = f"{family}_{uuid.uuid4().hex}"
                        nic_props = {
                            'name': nic_name,
                            'network-adapter-port-uri': test_port.uri,
                        }
                        tmp_part.nics.create(nic_props)

                        # The method to be tested
                        after_parts = test_adapter.list_assigned_partitions()

                        before_uris = [p.uri for p in before_parts]
                        new_parts = []
                        for part in after_parts:
                            if part.uri not in before_uris:
                                new_parts.append(part)

                        assert len(new_parts) == 1
                        new_part = new_parts[0]
                        assert new_part.uri == tmp_part.uri

                elif family == 'ficon':

                    # Assigning storage adapters to partitions is complex,
                    # so we search for a storage adapter that is already
                    # assigned to a partition.

                    found_test_adapter = False
                    for test_adapter in all_adapters:

                        if test_adapter.get_property('type') != 'fcp':
                            # This test works only for FCP adapters
                            continue

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        if len(before_parts) == 0:
                            continue

                        found_test_adapter = True
                        print(f"Testing on CPC {cpc.name} with FCP adapter "
                              f"{test_adapter.name!r} (family '{family}')")

                        found_adapters = []
                        for part in before_parts:
                            sgroups = part.list_attached_storage_groups()
                            for sg in sgroups:
                                if sg.get_property('type') != 'fcp':
                                    # This test works only for FCP stogrps
                                    continue
                                vsrs = sg.virtual_storage_resources.list()
                                for vsr in vsrs:
                                    port = vsr.adapter_port
                                    adapter = port.manager.parent
                                    if adapter.uri == test_adapter.uri:
                                        found_adapters.append(adapter)

                        assert len(found_adapters) >= 1
                        break

                    if not found_test_adapter:
                        warnings.warn(
                            f"CPC {cpc.name} has no FCP adapter with that is "
                            "assigned to any partition - cannot test FCP "
                            "adapters", UserWarning)

                elif family == 'accelerator':

                    test_adapters = pick_test_resources(all_adapters)
                    for test_adapter in test_adapters:
                        print(f"Testing on CPC {cpc.name} with adapter "
                              f"{test_adapter.name!r} (family '{family}')")

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        # Create a VF in the temporary partition
                        vf_name = f"{family}_{uuid.uuid4().hex}"
                        vf_props = {
                            'name': vf_name,
                            'adapter-uri': test_adapter.uri,
                        }
                        tmp_part.virtual_functions.create(vf_props)

                        # The method to be tested
                        after_parts = test_adapter.list_assigned_partitions()

                        before_uris = [p.uri for p in before_parts]
                        new_parts = []
                        for part in after_parts:
                            if part.uri not in before_uris:
                                new_parts.append(part)

                        assert len(new_parts) == 1
                        new_part = new_parts[0]
                        assert new_part.uri == tmp_part.uri

                elif family == 'crypto':

                    # Assigning crypto adapters to partitions is complex,
                    # so we search for a crypto adapter that is already
                    # assigned to a partition.

                    found_test_adapter = False
                    for test_adapter in all_adapters:

                        # The method to be tested
                        before_parts = test_adapter.list_assigned_partitions()

                        if len(before_parts) == 0:
                            continue

                        found_test_adapter = True
                        print(f"Testing on CPC {cpc.name} with adapter "
                              f"{test_adapter.name!r} (family '{family}')")

                        found_adapter_uris = []
                        for part in before_parts:
                            crypto_config = part.get_property(
                                'crypto-configuration')
                            if crypto_config is None:
                                continue
                            adapter_uris = crypto_config['crypto-adapter-uris']
                            for adapter_uri in adapter_uris:
                                if adapter_uri == test_adapter.uri:
                                    found_adapter_uris.append(adapter_uri)

                        assert len(found_adapter_uris) >= 1
                        break

                    if not found_test_adapter:
                        warnings.warn(
                            f"CPC {cpc.name} has no Crypto adapter that is "
                            "assigned to any partition - cannot test Crypto "
                            "adapters", UserWarning)

                elif family == 'nvme':
                    print(f"TODO: Implement test for family {family}")

                elif family == 'coupling':
                    print(f"TODO: Implement test for family {family}")

                elif family == 'ism':
                    print(f"TODO: Implement test for family {family}")

                elif family == 'zhyperlink':
                    print(f"TODO: Implement test for family {family}")

        finally:
            # Cleanup
            if tmp_part:
                tmp_part.delete()


def base_adapter_id(adapter_id, family):
    """
    Return the base adapter_id of an adapter_id.
    Both are in hex.
    """

    # Adapter families that have no physical adapter card
    virtual_families = [
        'hipersockets',
        'coupling',  # Internal Coupling Facility
        'ism',  # Internal Shared Memory
    ]

    pchid = int(adapter_id, 16)

    if family in virtual_families:

        # Make sure the virtual card detection based on the PCHID range in
        # Adapter.list_sibling_adapters() holds true
        assert pchid >= int('7c0', 16)

        # Virtual adapters have only 1 PCHID
        base_pchid = pchid

    else:

        # Make sure the physical card detection based on the PCHID range in
        # Adapter.list_sibling_adapters() holds true
        assert pchid < int('7c0', 16)

        # Physical adapters have 4 PCHIDs reeserved for the slot.
        # Calculate the base PCHID for the slot.
        base_pchid = pchid // 4 * 4

    return f'{base_pchid:03x}'


def test_adapter_list_sibling_adapters(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test Adapter.list_sibling_adapters().
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        # Adapter families that have more than one Adapter object (=PCHID) on a
        # physical adapter card
        sibling_families = [
            'ficon',
            'crypto',
        ]

        adapters = cpc.adapters.list()

        # Determine the sibling adapters on the CPC, grouped by base PCHID
        adapters_by_base = {}  # key: base PCHID
        for adapter in adapters:
            adapter_id = adapter.get_property('adapter-id')
            family = adapter.get_property('adapter-family')
            if family in sibling_families:
                base_id = base_adapter_id(adapter_id, family)
                if base_id not in adapters_by_base:
                    adapters_by_base[base_id] = []
                adapters_by_base[base_id].append(adapter)

        # Test all adapters for their siblings
        for adapter in adapters:
            adapter_id = adapter.get_property('adapter-id')
            family = adapter.get_property('adapter-family')
            base_id = base_adapter_id(adapter_id, family)

            # The code to be tested
            sibling_adapters = adapter.list_sibling_adapters()

            assert isinstance(sibling_adapters, list)

            sibling_ids = {a.get_property('adapter-id')
                           for a in sibling_adapters}
            sibling_names = [a.name for a in sibling_adapters]
            if base_id not in adapters_by_base:
                exp_ids = set()
                exp_names = []
            else:
                exp_ids = {a.get_property('adapter-id')
                           for a in adapters_by_base[base_id]}
                exp_ids.remove(adapter_id)
                exp_names = [a.name for a in adapters_by_base[base_id]]
                exp_names.remove(adapter.name)

            assert sibling_ids == exp_ids, (
                f"Adapter '{adapter.name}' has unexpected siblings: got: "
                f"{sibling_names}, expected: {exp_names}")


# Properties in returned adapters, where each list item is a
# tuple(prop name, minimum CPC version).

# Default properties when no full/additional properties are requested:
DEFAULT_PROPS_LIST_PERMITTED_ADAPTERS = [
    ('object-uri', [2, 13, 1]),
    ('name', [2, 13, 1]),
    ('adapter-id', [2, 13, 1]),
    ('adapter-family', [2, 13, 1]),
    ('type', [2, 13, 1]),
    ('status', [2, 13, 1]),
    # The 'firmware-update-pending' property requires the
    # LI_1580_CRYPTO_AUTO_TOGGLE feature to be enabled:
    ('firmware-update-pending', [2, 16, 0]),
    ('cpc-name', [2, 13, 1]),
    ('cpc-object-uri', [2, 13, 1]),
    ('se-version', [2, 13, 1]),
    ('dpm-enabled', [2, 13, 1]),
]

# Full set of properties that are common on all types of adapters:
COMMON_FULL_PROPS_ADAPTERS = DEFAULT_PROPS_LIST_PERMITTED_ADAPTERS + [
    ('object-id', [2, 13, 1]),
    ('class', [2, 13, 1]),
    ('parent', [2, 13, 1]),
    ('description', [2, 13, 1]),
    ('detected-card-type', [2, 13, 1]),
    ('state', [2, 13, 1]),
    ('physical-channel-status', [2, 13, 1]),
]

LIST_PERMITTED_ADAPTERS_TESTCASES = [
    # The list items are tuples with the following items:
    # - desc (string): description of the testcase.
    # - input_kwargs (dict): Input parameters for the function.
    # - exp_props (list): List of expected properties in the result. Each list
    #     item is a tuple(prop name, minimum CPC version).
    # - exp_exc_type (class): Expected exception type, or None for success.
    # - run (bool or 'pdb'): Whether to run the test or call the debugger.

    (
        "Default parameters",
        dict(),
        DEFAULT_PROPS_LIST_PERMITTED_ADAPTERS,
        None,
        True,
    ),
    (
        "full_properties",
        dict(
            full_properties=True,
        ),
        COMMON_FULL_PROPS_ADAPTERS,
        None,
        True,
    ),
    (
        "'detected-card-type' in additional_properties",
        dict(
            additional_properties=['detected-card-type'],
        ),
        DEFAULT_PROPS_LIST_PERMITTED_ADAPTERS + [
            ('detected-card-type', [2, 13, 1]),
        ],
        None,
        True,
    ),
]


@pytest.mark.parametrize(
    "desc, input_kwargs, exp_props, exp_exc_type, run",
    LIST_PERMITTED_ADAPTERS_TESTCASES)
def test_adapter_list_permitted(
        desc, input_kwargs, exp_props, exp_exc_type, run,
        all_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name, unused-argument
    """
    Test Console.list_permitted_adapters() without filtering, but with
    different variations of returned properties.
    """
    if not all_cpcs:
        pytest.skip("HMC definition does not include any CPCs")

    console = all_cpcs[0].manager.console
    session = console.manager.session
    client = console.manager.client
    hd = session.hmc_definition

    if hd.mock_file:
        skip_warn("zhmcclient mock does not support 'List Permitted Adapters' "
                  "operation")

    if run == 'pdb':
        # pylint: disable=forgotten-debug-statement
        pdb.set_trace()

    if not run:
        skip_warn("Testcase is disabled in testcase definition")

    if exp_exc_type:

        with pytest.raises(exp_exc_type) as exc_info:

            # Exercise the code to be tested
            _ = console.list_permitted_adapters(**input_kwargs)

        _ = exc_info.value
    else:

        # Exercise the code to be tested
        adapters = console.list_permitted_adapters(**input_kwargs)

        # Verify the result
        returned_cpc_names = set()
        for adapter in adapters:
            cpc = adapter.manager.parent
            returned_cpc_names.add(cpc.name)
            cpc_version = list(map(int, cpc.prop('se-version').split('.')))
            assert isinstance(adapter, zhmcclient.Adapter)
            for pname, min_cpc_version in exp_props:
                if cpc_version >= min_cpc_version:
                    # The property is supposed to be in the result
                    actual_pnames = list(adapter.properties.keys())
                    if pname == 'firmware-update-pending' \
                            and pname not in actual_pnames:
                        warnings.warn(
                            "The 'firmware-update-pending' property is not "
                            f"returned for adapters on CPC {cpc.name!r} (SE "
                            f"version {cpc.prop('se-version')}). Check on the "
                            "SE 'Manage Firmware Features' task whether "
                            "feature LI_1580_CRYPTO_AUTO_TOGGLE is enabled.")
                    else:
                        assert pname in actual_pnames, \
                            f"Actual adapter: {adapter!r}"

        # Verify that adapters are returned:
        # * For all DPM-mode CPCs (of any version)
        # * For all classic-mode CPCs of z15 or higher
        # The logic below assumes that each CPC has at least one adapter.
        expected_cpc_names = set()
        for cpc in client.cpcs.list():
            cpc_version = list(map(int, cpc.prop('se-version').split('.')))
            if cpc.dpm_enabled or cpc_version >= (2, 15):
                expected_cpc_names.add(cpc.name)
        assert returned_cpc_names == expected_cpc_names, (
            "Invalid set of CPCs of returned adapters:\n"
            f"Returned CPCs: {','.join(returned_cpc_names)}"
            f"Expected CPCs: {','.join(expected_cpc_names)}")
