# Copyright 2025 IBM Corp. All Rights Reserved.
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
End2end tests for AI Accelerator Functions (on CPCs in DPM mode).

These tests do not change any existing partitions or AI Accelerator Functions,
but create, modify, and delete test resources as needed.

Requirements:
  - A CPC in DPM mode with the "ai-adapter" firmware feature enabled.
  - At least one adapter of type "ai" visible to the test user.

The tests skip gracefully when the firmware feature or suitable adapters
are not found.
"""


import warnings
import pytest
from requests.packages import urllib3

import zhmcclient

from .utils import skip_log, pick_test_resources, TEST_PREFIX, \
    standard_partition_props

urllib3.disable_warnings()

# Properties in minimalistic AiAcceleratorFunction objects (from find_by_name)
AI_FUNC_MINIMAL_PROPS = ['element-uri', 'name']

# Properties in AiAcceleratorFunction objects returned by list() without full
# properties (listed from the parent partition's ai-accelerator-function-uris)
AI_FUNC_LIST_PROPS = ['element-uri']

# Properties whose values can change between retrievals
AI_FUNC_VOLATILE_PROPS = []


def _skip_if_no_ai_feature(logger, cpc):
    """Skip the test if the 'ai-adapter' firmware feature is not enabled."""
    if not cpc.firmware_feature_enabled('ai-adapter'):
        skip_log(logger,
                 f"Firmware feature 'ai-adapter' not enabled on CPC {cpc.name}")


def _find_ai_adapter(cpc):
    """
    Find and return the first adapter of type 'ai' on the CPC, or None.
    """
    adapters = cpc.adapters.list(filter_args={'type': 'ai'})
    if not adapters:
        return None
    return adapters[0]


def test_ai_func_list(zhmc_logger, dpm_mode_cpcs):
    """
    Test list() for AI Accelerator Functions on an existing partition that
    already has AI Accelerator Functions assigned.
    """
    if not dpm_mode_cpcs:
        skip_log(zhmc_logger,
                 "HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        _skip_if_no_ai_feature(zhmc_logger, cpc)

        # Collect (partition, ai-func) pairs from all partitions on this CPC
        part_func_tuples = []
        for part in cpc.partitions.list():
            for ai_func in part.ai_accelerator_functions.list():
                part_func_tuples.append((part, ai_func))

        if not part_func_tuples:
            skip_log(zhmc_logger,
                     f"No partitions with AI Accelerator Functions on CPC "
                     f"{cpc.name} managed by HMC {hd.host}")

        part_func_tuples = pick_test_resources(part_func_tuples)

        for part, ai_func in part_func_tuples:
            print(f"Testing on CPC {cpc.name} with AI Accelerator Function "
                  f"{ai_func.name!r} of partition {part.name!r}")

            # Verify that list() returns the resource with its URI
            funcs = part.ai_accelerator_functions.list()
            uris = [f.uri for f in funcs]
            assert ai_func.uri in uris, (
                f"Expected AI Accelerator Function URI {ai_func.uri!r} to be "
                f"in the list result URIs: {uris!r}")


def test_ai_func_get_properties(zhmc_logger, dpm_mode_cpcs):
    """
    Test get_properties() / pull_full_properties() for an existing AI
    Accelerator Function.
    """
    if not dpm_mode_cpcs:
        skip_log(zhmc_logger,
                 "HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        session = cpc.manager.session
        hd = session.hmc_definition

        _skip_if_no_ai_feature(zhmc_logger, cpc)

        # Find a partition with at least one AI Accelerator Function
        part_func_tuples = []
        for part in cpc.partitions.list():
            for ai_func in part.ai_accelerator_functions.list():
                part_func_tuples.append((part, ai_func))

        if not part_func_tuples:
            skip_log(zhmc_logger,
                     f"No partitions with AI Accelerator Functions on CPC "
                     f"{cpc.name} managed by HMC {hd.host}")

        part_func_tuples = pick_test_resources(part_func_tuples)

        for part, ai_func in part_func_tuples:
            print(f"Testing on CPC {cpc.name} with AI Accelerator Function "
                  f"{ai_func.name!r} of partition {part.name!r}")

            # Test get_properties()
            props = ai_func.get_properties()

            assert isinstance(props, dict)
            assert 'element-uri' in props
            assert 'class' in props
            assert props['class'] == 'ai-accelerator-function'
            assert 'adapter-uri' in props
            assert 'is-physical-function' in props

            # Test pull_full_properties() gives the same result
            ai_func.pull_full_properties()
            assert ai_func.full_properties is True
            assert ai_func.properties['element-uri'] == props['element-uri']
            assert ai_func.properties['class'] == 'ai-accelerator-function'


def test_ai_func_crud(zhmc_logger, dpm_mode_cpcs):
    """
    Test create, read, update, and delete of AI Accelerator Functions.

    This test:
      1. Creates a test partition.
      2. Creates AI Accelerator Functions for the partition.
      3. Reads (get_properties) each created function and checks its props.
      4. Updates a writable property (description) on one function.
      5. Deletes all created AI Accelerator Functions.
      6. Deletes the test partition.
    """
    if not dpm_mode_cpcs:
        skip_log(zhmc_logger,
                 "HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        assert cpc.dpm_enabled

        _skip_if_no_ai_feature(zhmc_logger, cpc)

        ai_adapter = _find_ai_adapter(cpc)
        if ai_adapter is None:
            skip_log(zhmc_logger,
                     f"No adapter of type 'ai' found on CPC {cpc.name}")

        print(f"Testing on CPC {cpc.name} with AI adapter {ai_adapter.name!r}")

        part_name = TEST_PREFIX + ' test_ai_func_crud part1'
        vf_name = 'ai-vf-1'
        vf_name_new = vf_name + '-updated'
        new_description = 'Updated description for AI VF test'

        # Ensure a clean starting point
        try:
            part = cpc.partitions.find(name=part_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                f"Deleting test partition from previous run: {part_name!r} on "
                f"CPC {cpc.name}", UserWarning)
            if part.get_property('status') != 'stopped':
                part.stop()
            part.delete()

        part = None
        ai_funcs = None
        try:
            # --- Create a test partition ---
            part_props = standard_partition_props(cpc, part_name)
            part = cpc.partitions.create(part_props)
            print(f"Created partition {part_name!r}")

            # --- Create AI Accelerator Functions (one virtual function) ---
            ai_funcs = part.ai_accelerator_functions.create(
                adapter_uri=ai_adapter.uri,
                ai_accelerator_functions=[
                    {
                        'name': vf_name,
                        'description': 'Test VF for AI accelerator crud test',
                        'is-physical-function': False,
                    }
                ])

            assert len(ai_funcs) == 1, \
                f"Expected 1 created function, got {len(ai_funcs)}"
            ai_func = ai_funcs[0]
            assert isinstance(ai_func, zhmcclient.AiAcceleratorFunction)
            print(f"Created AI Accelerator Function URI: {ai_func.uri!r}")

            # Verify the URI is listed by the partition
            listed_uris = [
                f.uri for f in part.ai_accelerator_functions.list()]
            assert ai_func.uri in listed_uris, (
                f"Created function URI {ai_func.uri!r} not found in listed "
                f"URIs: {listed_uris!r}")

            # --- Read the function properties ---
            props = ai_func.get_properties()
            assert props.get('name') == vf_name, \
                f"Expected name {vf_name!r}, got {props.get('name')!r}"
            assert props.get('is-physical-function') is False
            assert props.get('adapter-uri') == ai_adapter.uri

            # --- Update a writable property (description) ---
            ai_func.update_properties({'description': new_description})

            # Verify local update
            assert ai_func.properties['description'] == new_description

            # Verify server-side update
            ai_func.pull_full_properties()
            assert ai_func.properties['description'] == new_description

            # --- Update name ---
            ai_func.update_properties({'name': vf_name_new})
            assert ai_func.properties['name'] == vf_name_new
            ai_func.pull_full_properties()
            assert ai_func.properties['name'] == vf_name_new

            # Old name should not be findable
            with pytest.raises(zhmcclient.NotFound):
                part.ai_accelerator_functions.find(name=vf_name)

            # New name is findable
            found = part.ai_accelerator_functions.find(name=vf_name_new)
            assert found.uri == ai_func.uri

            # --- Delete the AI Accelerator Functions ---
            func_uris = [f.uri for f in part.ai_accelerator_functions.list()]
            assert len(func_uris) >= 1

            part.ai_accelerator_functions.delete_functions(func_uris)

            # Verify they are gone
            remaining = part.ai_accelerator_functions.list()
            assert remaining == [], \
                f"Expected no AI functions after delete, got: {remaining!r}"

            ai_funcs = None  # already deleted, no need to clean up in finally

        finally:
            # Best-effort cleanup
            if ai_funcs:
                try:
                    func_uris = [f.uri for f in
                                 part.ai_accelerator_functions.list()]
                    if func_uris:
                        part.ai_accelerator_functions.delete_functions(
                            func_uris)
                except Exception:  # noqa: S110 # pylint: disable=broad-except
                    pass
            if part:
                try:
                    if part.get_property('status') != 'stopped':
                        part.stop()
                    part.delete()
                except Exception:  # noqa: S110 # pylint: disable=broad-except
                    pass


def test_ai_func_zzz_cleanup(zhmc_logger, dpm_mode_cpcs):
    """
    Cleanup leftover test partitions from previous runs.

    This test function is named with 'zzz_' so that pytest collects it last.
    It removes any partition with the test prefix that was left over from a
    previous, failed test run.
    """
    if not dpm_mode_cpcs:
        skip_log(zhmc_logger,
                 "HMC definition does not include any CPCs in DPM mode")

    for cpc in dpm_mode_cpcs:
        if not cpc.dpm_enabled:
            continue
        part_name = TEST_PREFIX + ' test_ai_func_crud part1'
        try:
            part = cpc.partitions.find(name=part_name)
        except zhmcclient.NotFound:
            pass
        else:
            warnings.warn(
                f"Cleaning up leftover test partition {part_name!r} on CPC "
                f"{cpc.name}", UserWarning)
            try:
                func_uris = [
                    f.uri for f in part.ai_accelerator_functions.list()]
                if func_uris:
                    part.ai_accelerator_functions.delete_functions(func_uris)
            except Exception:  # noqa: S110 # pylint: disable=broad-except
                pass
            try:
                if part.get_property('status') != 'stopped':
                    part.stop()
                part.delete()
            except Exception:  # noqa: S110 # pylint: disable=broad-except
                pass
