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
End2end tests for NICs (on CPCs in DPM mode).

These tests do not change any existing partitions or NICs, but create, modify
and delete test partitions with NICs.
"""


import warnings
import random
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
from .utils import logger  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    standard_partition_props, runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Nic objects (e.g. find_by_name())
NIC_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in Nic objects returned by list() without full props
NIC_LIST_PROPS = ['element-uri', 'name', 'description', 'type']

# Properties whose values can change between retrievals of Nic objects
NIC_VOLATILE_PROPS = []


def test_nic_find_list(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the NICs to test with
        part_nic_tuples = []
        part_list = cpc.partitions.list()
        for part in part_list:
            nic_list = part.nics.list()
            for nic in nic_list:
                part_nic_tuples.append((part, nic))
        if not part_nic_tuples:
            skip_warn(
                f"No partitions with NICs on CPC {cpc.name} managed by HMC "
                f"{hd.host}")
        part_nic_tuples = pick_test_resources(part_nic_tuples)

        for part, nic in part_nic_tuples:
            print(f"Testing on CPC {cpc.name} with NIC {nic.name!r} of "
                  f"partition {part.name!r}")
            runtest_find_list(
                session, part.nics, nic.name, 'name', 'type',
                NIC_VOLATILE_PROPS, NIC_MINIMAL_PROPS, NIC_LIST_PROPS)


def test_nic_property(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the NICs to test with
        part_nic_tuples = []
        part_list = cpc.partitions.list()
        for part in part_list:
            nic_list = part.nics.list()
            for nic in nic_list:
                part_nic_tuples.append((part, nic))
        if not part_nic_tuples:
            skip_warn(f"No partitions with NICs on CPC {cpc.name} managed by "
                      f"HMC {hd.host}")
        part_nic_tuples = pick_test_resources(part_nic_tuples)

        for part, nic in part_nic_tuples:
            print(f"Testing on CPC {cpc.name} with NIC {nic.name!r} of "
                  f"partition {part.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(nic.manager, non_list_prop)


def test_nic_crud(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a NIC (and a partition).
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print(f"Testing on CPC {cpc.name}")

        hs_adapter_name = TEST_PREFIX + ' test_nic_crud adapter1'
        part_name = TEST_PREFIX + ' test_nic_crud part1'
        nic_name = 'nic1'
        nic_name_new = nic_name + ' new'

        # Ensure a clean starting point for this test
        try:
            part = cpc.partitions.find(name=part_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                f"Deleting test partition from previous run: {part_name!r} on "
                f"CPC {cpc.name}", UserWarning)
            status = part.get_property('status')
            if status != 'stopped':
                part.stop()
            part.delete()
        try:
            adapter = cpc.adapters.find(name=hs_adapter_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                "Deleting test Hipersocket adapter from previous run: "
                f"{hs_adapter_name!r} on CPC {cpc.name}", UserWarning)
            adapter.delete()

        part = None
        adapter = None
        try:

            # Create a partition that will lateron contain the NIC
            part_props = standard_partition_props(cpc, part_name)
            part = cpc.partitions.create(part_props)

            # Create a Hipersocket adapter backing the NIC
            adapter_input_props = {
                'name': hs_adapter_name,
                'description': 'Test adapter for zhmcclient end2end tests',
            }
            adapter = cpc.adapters.create_hipersocket(adapter_input_props)

            # Find the vswitch backed by the Hipersockets adapter
            vswitches = cpc.virtual_switches.findall(
                **{'backing-adapter-uri': adapter.uri})
            vswitch = vswitches[0]

            # Test creating a NIC

            nic_input_props = {
                'name': nic_name,
                'description': 'Dummy NIC description.',
                'virtual-switch-uri': vswitch.uri,
                'device-number': '0100',
            }
            nic_auto_props = {
                'type': 'iqd',
                'ssc-management-nic': False,
            }

            # The code to be tested
            nic = part.nics.create(nic_input_props)

            for pn, exp_value in nic_input_props.items():
                assert nic.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r}"
            nic.pull_full_properties()
            for pn, exp_value in nic_input_props.items():
                assert nic.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r}"
            for pn, exp_value in nic_auto_props.items():
                assert nic.properties[pn] == exp_value, \
                    f"Unexpected value for property {pn!r}"

            # Test updating a property of the NIC

            new_desc = "Updated NIC description."

            # The code to be tested
            nic.update_properties(dict(description=new_desc))

            assert nic.properties['description'] == new_desc
            nic.pull_full_properties()
            assert nic.properties['description'] == new_desc

            # Test renaming the NIC

            # The code to be tested
            nic.update_properties(dict(name=nic_name_new))

            assert nic.properties['name'] == nic_name_new
            nic.pull_full_properties()
            assert nic.properties['name'] == nic_name_new
            with pytest.raises(zhmcclient.NotFound):
                part.nics.find(name=nic_name)

            # Test deleting the NIC

            # The code to be tested
            nic.delete()

            with pytest.raises(zhmcclient.NotFound):
                part.nics.find(name=nic_name_new)

        finally:
            # Cleanup
            if part:
                part.delete()
            if adapter:
                adapter.delete()


def test_nic_backing_port_port_based(logger, dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test Nic.backing_port() for port-based NICs (e.g. RoCE, CNA).
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    cpc = random.choice(dpm_mode_cpcs)
    logger.debug("Testing with CPC %s", cpc.name)
    client = cpc.manager.client

    port_nics = []
    partitions = cpc.partitions.list()
    for partition in random.sample(partitions, k=len(partitions)):
        for nic in partition.nics.list():
            try:
                _ = nic.get_property('virtual-switch-uri')
            except KeyError:
                # port-based NIC (e.g. RoCE, CNA)
                logger.debug("Found port-based NIC %s", nic.name)
                port_nics.append(nic)
            else:
                # vswitch-based NIC (e.g. OSA, HS)
                pass
        if len(port_nics) >= 5:
            break

    if not port_nics:
        pytest.skip(f"CPC {cpc.name} does not have any partitions with "
                    "port-based NICs")

    # Pick the port-based NIC to test with
    nic = random.choice(port_nics)
    partition = nic.manager.parent
    logger.debug("Testing with NIC %r in partition %r",
                 nic.name, partition.name)

    port_uri = nic.get_property('network-adapter-port-uri')
    port_props = client.session.get(port_uri)
    adapter_uri = port_props['parent']
    adapter = cpc.adapters.resource_object(adapter_uri)
    port = adapter.ports.resource_object(port_uri)

    logger.debug("Calling Nic.backing_port()")

    # The code to be tested
    result_port = nic.backing_port()

    logger.debug("Returned from Nic.backing_port()")

    assert isinstance(result_port, zhmcclient.Port)
    assert result_port.uri == port.uri

    result_adapter = result_port.manager.parent
    assert result_adapter.uri == adapter.uri

    result_cpc = result_adapter.manager.parent
    assert result_cpc.uri == cpc.uri


def test_nic_backing_port_vswitch_based(logger, dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test Nic.backing_port() for vswitch-based NICs (e.g. OSA, HS).
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    cpc = random.choice(dpm_mode_cpcs)
    logger.debug("Testing with CPC %s", cpc.name)
    client = cpc.manager.client

    vswitch_nics = []
    partitions = cpc.partitions.list()
    for partition in random.sample(partitions, k=len(partitions)):
        for nic in partition.nics.list():
            try:
                _ = nic.get_property('virtual-switch-uri')
            except KeyError:
                # port-based NIC (e.g. RoCE, CNA)
                pass
            else:
                # vswitch-based NIC (e.g. OSA, HS)
                logger.debug("Found vswitch-based NIC %s", nic.name)
                vswitch_nics.append(nic)
        if len(vswitch_nics) >= 5:
            break

    if not vswitch_nics:
        pytest.skip(f"CPC {cpc.name} does not have any partitions with "
                    "vswitch-based NICs")

    # Pick the port-based NIC to test with
    nic = random.choice(vswitch_nics)
    partition = nic.manager.parent
    logger.debug("Testing with NIC %r in partition %r",
                 nic.name, partition.name)

    vswitch_uri = nic.get_property('virtual-switch-uri')
    vswitch_props = client.session.get(vswitch_uri)
    adapter_uri = vswitch_props['backing-adapter-uri']
    port_index = vswitch_props['port']
    adapter = cpc.adapters.resource_object(adapter_uri)
    port_uris = adapter.get_property('network-port-uris')
    for port_uri in port_uris:
        port = adapter.ports.resource_object(port_uri)
        port_index_ = port.get_property('index')
        if port_index_ == port_index:
            break
    else:
        raise AssertionError  # Would be an HMC inconsistency

    logger.debug("Calling Nic.backing_port()")

    # The code to be tested
    result_port = nic.backing_port()

    logger.debug("Returned from Nic.backing_port()")

    assert isinstance(result_port, zhmcclient.Port)
    assert result_port.uri == port.uri

    result_adapter = result_port.manager.parent
    assert result_adapter.uri == adapter.uri

    result_cpc = result_adapter.manager.parent
    assert result_cpc.uri == cpc.uri
