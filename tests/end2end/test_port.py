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
End2end tests for adapter ports (on CPCs in DPM mode).

These tests do not change any existing ports, but create and delete Hipersocket
adapters and modify their ports.
"""


import warnings
import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils import hmc_definition, hmc_session  # noqa: F401, E501
from zhmcclient.testutils import dpm_mode_cpcs  # noqa: F401, E501
# pylint: enable=line-too-long,unused-import

from .utils import skip_warn, pick_test_resources, TEST_PREFIX, \
    runtest_find_list, runtest_get_properties

urllib3.disable_warnings()

# Properties in minimalistic Port objects (e.g. find_by_name())
PORT_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in Port objects returned by list() without full props
PORT_LIST_PROPS = ['element-uri', 'name', 'description']

# Properties whose values can change between retrievals of Port objects
PORT_VOLATILE_PROPS = []


def test_port_find_list(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the ports to test with
        adapter_port_tuples = []
        adapter_list = cpc.adapters.list()
        for adapter in adapter_list:
            port_list = adapter.ports.list()
            for port in port_list:
                adapter_port_tuples.append((adapter, port))
        if not adapter_port_tuples:
            skip_warn(
                f"No adapters with ports on CPC {cpc.name} managed by HMC "
                f"{hd.host}")
        adapter_port_tuples = pick_test_resources(adapter_port_tuples)

        for adapter, port in adapter_port_tuples:
            print(f"Testing on CPC {cpc.name} with port {port.name!r} of "
                  f"adapter {adapter.name!r}")
            runtest_find_list(
                session, adapter.ports, port.name, 'name', 'element-uri',
                PORT_VOLATILE_PROPS, PORT_MINIMAL_PROPS, PORT_LIST_PROPS)


def test_port_property(dpm_mode_cpcs):  # noqa: F811
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

        # Pick the ports to test with
        adapter_port_tuples = []
        adapter_list = cpc.adapters.list()
        for adapter in adapter_list:
            port_list = adapter.ports.list()
            for port in port_list:
                adapter_port_tuples.append((adapter, port))
        if not adapter_port_tuples:
            skip_warn(
                f"No adapters with ports on CPC {cpc.name} managed by "
                f"HMC {hd.host}")
        adapter_port_tuples = pick_test_resources(adapter_port_tuples)

        for adapter, port in adapter_port_tuples:
            print(f"Testing on CPC {cpc.name} with port {port.name!r} of "
                  f"adapter {adapter.name!r}")

            # Select a property that is not returned by list()
            non_list_prop = 'description'

            runtest_get_properties(port.manager, non_list_prop)


def test_port_update(dpm_mode_cpcs):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test updating the port of a Hipersocket adapter.
    """
    if not dpm_mode_cpcs:
        pytest.skip("HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        print(f"Testing on CPC {cpc.name}")

        adapter_name = TEST_PREFIX + ' test_adapter_crud adapter1'

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

        adapter = None
        try:
            # Create a Hipersocket adapter
            adapter_input_props = {
                'name': adapter_name,
            }
            adapter = cpc.adapters.create_hipersocket(adapter_input_props)

            # Pick a port for the test
            port = adapter.ports.list()[0]

            port_name = port.name
            port_name_new = port_name + ' new'

            # Test updating a property of the port

            new_desc = "Updated port description."

            # The code to be tested
            port.update_properties(dict(description=new_desc))

            assert port.properties['description'] == new_desc
            port.pull_full_properties()
            assert port.properties['description'] == new_desc

            # Test that ports cannot be renamed

            with pytest.raises(zhmcclient.HTTPError) as exc_info:

                # The code to be tested
                port.update_properties(dict(name=port_name_new))

            exc = exc_info.value
            assert exc.http_status == 400
            assert exc.reason == 6

        finally:
            # Cleanup
            if adapter:
                adapter.delete()
