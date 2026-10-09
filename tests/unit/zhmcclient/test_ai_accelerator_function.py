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
Unit tests for _ai_accelerator_function module.
"""


import re
import copy
import pytest

from zhmcclient import Client, AiAcceleratorFunction, \
    AiAcceleratorFunctionManager, HTTPError, NotFound
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked AI Accelerator Functions:
AIFUNC1_OID = 'ai-func-1-oid'
AIFUNC1_NAME = 'ai-func-1'
AIFUNC2_OID = 'ai-func-2-oid'
AIFUNC2_NAME = 'ai-func-2'

# Fake adapter of type "ai"
AI_ADAPTER_OID = 'fake-ai-adapter-oid'
AI_ADAPTER_URI = f'/api/adapters/{AI_ADAPTER_OID}'


class TestAiAcceleratorFunction:
    """All tests for AiAcceleratorFunction and AiAcceleratorFunctionManager."""

    def setup_method(self):
        """
        Setup called by pytest before each test method.

        Sets up a faked session with a CPC in DPM mode and one partition
        with no AI Accelerator Functions initially.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.16.0', '4.10')
        self.client = Client(self.session)

        # Add a CPC in DPM mode
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'fake-cpc1-oid',
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
        })
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

        # Add a partition to the CPC
        self.faked_partition = self.faked_cpc.partitions.add({
            'element-id': 'fake-part1-oid',
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': 'fake-part1-name',
            'description': 'Partition #1',
            'status': 'active',
            'initial-memory': 1024,
            'maximum-memory': 2048,
        })
        self.partition = self.cpc.partitions.find(name='fake-part1-name')

        # Add a fake AI adapter to the CPC
        self.faked_ai_adapter = self.faked_cpc.adapters.add({
            'object-id': AI_ADAPTER_OID,
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': 'fake-ai-adapter',
            'description': 'AI Adapter #1',
            'status': 'active',
            'type': 'ai',
            'adapter-id': '007',
            'state': 'online',
        })
        assert AI_ADAPTER_URI == self.faked_ai_adapter.uri

    # -----------------------------------------------------------------------
    # Helper methods
    # -----------------------------------------------------------------------

    def add_aifunc1(self):
        """Add faked AI Accelerator Function 1 (virtual function)."""
        return self.faked_partition.ai_accelerator_functions.add({
            'element-id': AIFUNC1_OID,
            'parent': self.faked_partition.uri,
            'class': 'ai-accelerator-function',
            'name': AIFUNC1_NAME,
            'description': 'AI function ' + AIFUNC1_NAME,
            'adapter-uri': AI_ADAPTER_URI,
            'is-physical-function': False,
            'device-number': '0001',
        })

    def add_aifunc2(self):
        """Add faked AI Accelerator Function 2 (physical function)."""
        return self.faked_partition.ai_accelerator_functions.add({
            'element-id': AIFUNC2_OID,
            'parent': self.faked_partition.uri,
            'class': 'ai-accelerator-function',
            'name': AIFUNC2_NAME,
            'description': 'AI function ' + AIFUNC2_NAME,
            'adapter-uri': AI_ADAPTER_URI,
            'is-physical-function': True,
            'device-number': '0002',
        })

    def add_mgmt_partition(self):
        """Add a separate management partition with a PF to satisfy
        Reason 121."""
        mgmt_part = self.faked_cpc.partitions.add({
            'element-id': 'fake-part-mgmt-oid',
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': 'fake-part-mgmt-name',
            'type': 'ssc',
            'status': 'active',
        })
        mgmt_part.ai_accelerator_functions.add({
            'element-id': 'fake-pf-oid',
            'name': 'fake-pf-name',
            'is-physical-function': True,
            'adapter-uri': AI_ADAPTER_URI,
        })
        return mgmt_part

    # -----------------------------------------------------------------------
    # Manager attribute tests
    # -----------------------------------------------------------------------

    def test_manager_initial_attrs(self):
        """Test initial attributes of AiAcceleratorFunctionManager."""
        mgr = self.partition.ai_accelerator_functions

        assert isinstance(mgr, AiAcceleratorFunctionManager)
        assert mgr.resource_class == AiAcceleratorFunction
        assert mgr.session == self.session
        assert mgr.parent == self.partition
        assert mgr.partition == self.partition

    # -----------------------------------------------------------------------
    # list() tests
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            ({},
             ['element-uri']),
            ({'full_properties': False},
             ['element-uri']),
            ({'full_properties': True},
             None),
        ]
    )
    def test_manager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test AiAcceleratorFunctionManager.list() with full_properties."""
        faked_func1 = self.add_aifunc1()
        faked_func2 = self.add_aifunc2()

        exp_faked_funcs = [faked_func1, faked_func2]
        mgr = self.partition.ai_accelerator_functions

        funcs = mgr.list(**full_properties_kwargs)

        assert_resources(funcs, exp_faked_funcs, prop_names)

    @pytest.mark.parametrize(
        "filter_args, exp_oids", [
            ({'element-id': AIFUNC1_OID},
             [AIFUNC1_OID]),
            ({'element-id': AIFUNC2_OID},
             [AIFUNC2_OID]),
            ({'element-id': [AIFUNC1_OID, AIFUNC2_OID]},
             [AIFUNC1_OID, AIFUNC2_OID]),
            ({'element-id': AIFUNC1_OID + 'x'},
             []),
            ({'name': AIFUNC1_NAME},
             [AIFUNC1_OID]),
            ({'name': AIFUNC2_NAME},
             [AIFUNC2_OID]),
            ({'name': [AIFUNC1_NAME, AIFUNC2_NAME]},
             [AIFUNC1_OID, AIFUNC2_OID]),
            ({'name': AIFUNC1_NAME + 'x'},
             []),
            ({'name': 'ai-func-.'},
             [AIFUNC1_OID, AIFUNC2_OID]),
        ]
    )
    def test_manager_list_filter_args(self, filter_args, exp_oids):
        """Test AiAcceleratorFunctionManager.list() with filter_args."""
        self.add_aifunc1()
        self.add_aifunc2()

        mgr = self.partition.ai_accelerator_functions

        funcs = mgr.list(filter_args=filter_args)

        assert len(funcs) == len(exp_oids)
        if exp_oids:
            oids = [f.properties['element-id'] for f in funcs]
            assert set(oids) == set(exp_oids)

    def test_manager_list_empty(self):
        """Test AiAcceleratorFunctionManager.list() when partition has none."""
        mgr = self.partition.ai_accelerator_functions
        funcs = mgr.list()
        assert funcs == []

    # -----------------------------------------------------------------------
    # create() tests
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "initial_partition_status, exp_status_exc", [
            ('stopped', None),
            ('active', None),
            ('starting', HTTPError({'http-status': 409, 'reason': 1})),
            ('stopping', HTTPError({'http-status': 409, 'reason': 1})),
            ('degraded', None),
        ]
    )
    def test_manager_create_partition_status(
            self, initial_partition_status, exp_status_exc):
        """Test that create() respects partition status constraints."""
        self.add_mgmt_partition()
        self.faked_partition.properties['status'] = initial_partition_status
        mgr = self.partition.ai_accelerator_functions

        if exp_status_exc:
            with pytest.raises(exp_status_exc.__class__) as exc_info:
                mgr.create(adapter_uri=AI_ADAPTER_URI)
            exc = exc_info.value
            assert exc.http_status == exp_status_exc.http_status
            assert exc.reason == exp_status_exc.reason
        else:
            funcs = mgr.create(adapter_uri=AI_ADAPTER_URI)
            assert len(funcs) == 1
            assert isinstance(funcs[0], AiAcceleratorFunction)

    def test_manager_create_single_default(self):
        """Test create() with one default (virtual) function via empty list."""
        self.add_mgmt_partition()
        mgr = self.partition.ai_accelerator_functions

        funcs = mgr.create(adapter_uri=AI_ADAPTER_URI)

        assert len(funcs) == 1
        func = funcs[0]
        assert isinstance(func, AiAcceleratorFunction)
        assert func.uri is not None
        assert func.uri.startswith(
            self.partition.uri + '/ai-accelerator-functions/')

        # Verify the URI is now in the partition's list
        part_uris = self.faked_partition.properties[
            'ai-accelerator-function-uris']
        assert func.uri in part_uris

    def test_manager_create_two_with_props(self):
        """Test create() with explicit physical and virtual function props."""
        self.faked_partition.properties['type'] = 'ssc'
        mgr = self.partition.ai_accelerator_functions

        ai_funcs = [
            {
                'name': 'pf-func',
                'description': 'Physical function',
                'device-number': '0010',
                'is-physical-function': True,
            },
            {
                'name': 'vf-func',
                'description': 'Virtual function',
                'device-number': '0011',
                'is-physical-function': False,
            },
        ]

        funcs = mgr.create(
            adapter_uri=AI_ADAPTER_URI,
            ai_accelerator_functions=ai_funcs)

        assert len(funcs) == 2
        for func in funcs:
            assert isinstance(func, AiAcceleratorFunction)

        part_uris = self.faked_partition.properties[
            'ai-accelerator-function-uris']
        for func in funcs:
            assert func.uri in part_uris

    def test_create_constr_dup_name(self):
        """Test that create() raises HTTPError on duplicate name within
        partition."""
        self.add_mgmt_partition()
        self.add_aifunc1()  # adds AIFUNC1_NAME
        mgr = self.partition.ai_accelerator_functions
        with pytest.raises(HTTPError) as exc_info:
            mgr.create(adapter_uri=AI_ADAPTER_URI,
                       ai_accelerator_functions=[{'name': AIFUNC1_NAME}])
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 8

    def test_create_constr_dup_devno(self):
        """Test that create() raises HTTPError on duplicate device-number
        within partition."""
        self.add_mgmt_partition()
        self.add_aifunc1()  # uses device-number '0001'
        mgr = self.partition.ai_accelerator_functions
        with pytest.raises(HTTPError) as exc_info:
            mgr.create(adapter_uri=AI_ADAPTER_URI,
                       ai_accelerator_functions=[
                           {'name': 'new-func', 'device-number': '0001'}])
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 8

    def test_create_constr_consumer_limit(self):
        """Test that consumer partition only allows at most 1 AI Accelerator
        Function."""
        self.add_mgmt_partition()
        mgr = self.partition.ai_accelerator_functions
        # Try to create 2 functions on consumer partition
        with pytest.raises(HTTPError) as exc_info:
            mgr.create(adapter_uri=AI_ADAPTER_URI,
                       ai_accelerator_functions=[
                           {'name': 'f1'}, {'name': 'f2'}])
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 7

    def test_create_constr_consumer_pf(self):
        """Test that physical function is not allowed on a consumer
        partition."""
        self.add_mgmt_partition()
        mgr = self.partition.ai_accelerator_functions
        with pytest.raises(HTTPError) as exc_info:
            mgr.create(adapter_uri=AI_ADAPTER_URI,
                       ai_accelerator_functions=[
                           {'name': 'f1', 'is-physical-function': True}])
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 24

    def test_create_constr_no_mgmt_part(self):
        """Test that creating a consumer function raises HTTPError
        (reason 121) when no management partition is defined."""
        # Do not call self.add_mgmt_partition()
        mgr = self.partition.ai_accelerator_functions
        with pytest.raises(HTTPError) as exc_info:
            mgr.create(adapter_uri=AI_ADAPTER_URI)
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 121

    def test_create_constr_multi_mgmt(self):
        """Test that creating a management partition when one already exists
        raises HTTPError (reason 120)."""
        self.add_mgmt_partition()  # defines a management partition
        # Try to create another management partition on self.partition
        self.faked_partition.properties['type'] = 'ssc'
        mgr = self.partition.ai_accelerator_functions
        with pytest.raises(HTTPError) as exc_info:
            mgr.create(adapter_uri=AI_ADAPTER_URI,
                       ai_accelerator_functions=[
                           {'name': 'pf', 'is-physical-function': True}])
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 120

    def test_update_constr_dup_name(self):
        """Test that update_properties() raises HTTPError on duplicate name."""
        self.add_mgmt_partition()
        self.add_aifunc1()  # name AIFUNC1_NAME
        self.add_aifunc2()  # name AIFUNC2_NAME
        funcs = self.partition.ai_accelerator_functions.list()
        f1 = next(f for f in funcs if f.name == AIFUNC1_NAME)
        with pytest.raises(HTTPError) as exc_info:
            f1.update_properties({'name': AIFUNC2_NAME})
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 8

    def test_manager_create_no_adapter_raises(self):
        """Test create() without required adapter-uri raises HTTPError."""
        # Manually POST with no body fields via the session
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                self.partition.uri +
                '/operations/create-ai-accelerator-functions',
                body={})
        exc = exc_info.value
        assert exc.http_status == 400

    # -----------------------------------------------------------------------
    # delete_functions() tests
    # -----------------------------------------------------------------------

    def test_manager_delete_functions_ok(self):
        """Test delete_functions() removes the specified functions."""
        faked_func1 = self.add_aifunc1()
        faked_func2 = self.add_aifunc2()
        mgr = self.partition.ai_accelerator_functions

        # Both exist
        funcs = mgr.list()
        assert len(funcs) == 2

        # Delete one
        mgr.delete_functions([faked_func1.uri])

        funcs = mgr.list()
        assert len(funcs) == 1
        assert funcs[0].uri == faked_func2.uri

        part_uris = self.faked_partition.properties[
            'ai-accelerator-function-uris']
        assert faked_func1.uri not in part_uris
        assert faked_func2.uri in part_uris

    def test_manager_delete_functions_both(self):
        """Test delete_functions() with both URIs removes both functions."""
        faked_func1 = self.add_aifunc1()
        faked_func2 = self.add_aifunc2()
        mgr = self.partition.ai_accelerator_functions

        mgr.delete_functions([faked_func1.uri, faked_func2.uri])

        funcs = mgr.list()
        assert funcs == []
        part_uris = self.faked_partition.properties[
            'ai-accelerator-function-uris']
        assert part_uris == []

    @pytest.mark.parametrize(
        "initial_partition_status, exp_status_exc", [
            ('stopped', None),
            ('active', None),
            ('starting', HTTPError({'http-status': 409, 'reason': 1})),
            ('stopping', HTTPError({'http-status': 409, 'reason': 1})),
        ]
    )
    def test_manager_delete_part_status(
            self, initial_partition_status, exp_status_exc):
        """Test delete_functions() partition status constraints."""
        faked_func = self.add_aifunc1()
        self.faked_partition.properties['status'] = initial_partition_status
        mgr = self.partition.ai_accelerator_functions

        if exp_status_exc:
            with pytest.raises(exp_status_exc.__class__) as exc_info:
                mgr.delete_functions([faked_func.uri])
            exc = exc_info.value
            assert exc.http_status == exp_status_exc.http_status
            assert exc.reason == exp_status_exc.reason
        else:
            mgr.delete_functions([faked_func.uri])
            assert mgr.list() == []

    # -----------------------------------------------------------------------
    # AiAcceleratorFunction resource tests
    # -----------------------------------------------------------------------

    def test_function_repr(self):
        """Test AiAcceleratorFunction.__repr__()."""
        faked_func = self.add_aifunc1()
        mgr = self.partition.ai_accelerator_functions
        func = mgr.find(name=faked_func.name)

        repr_str = repr(func)
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(
            rf'^{func.__class__.__name__}\s+at\s+0x{id(func):08x}\s+\(\\n.*',
            repr_str)

    def test_function_get_properties(self):
        """Test AiAcceleratorFunction.get_properties()."""
        faked_func = self.add_aifunc1()
        mgr = self.partition.ai_accelerator_functions
        func = mgr.find(name=faked_func.name)

        result = func.get_properties()

        assert isinstance(result, dict)
        assert result['element-uri'] == faked_func.uri
        assert result['name'] == AIFUNC1_NAME
        assert result['adapter-uri'] == AI_ADAPTER_URI
        assert result['is-physical-function'] is False
        # Properties are also stored locally
        assert func.properties['name'] == AIFUNC1_NAME

    @pytest.mark.parametrize(
        "update_props", [
            {},
            {'description': 'New description'},
            {'device-number': 'FEDC'},
            {'name': 'new-func-name', 'description': 'Renamed'},
        ]
    )
    def test_function_update_properties(self, update_props):
        """Test AiAcceleratorFunction.update_properties()."""
        faked_func = self.add_aifunc1()
        mgr = self.partition.ai_accelerator_functions
        func = mgr.find(name=faked_func.name)
        func.pull_full_properties()
        saved_props = copy.deepcopy(func.properties)

        func.update_properties(update_props)

        # Local properties reflect update immediately
        for prop_name, exp_value in update_props.items():
            assert func.properties[prop_name] == exp_value

        # Properties not in update are unchanged
        for prop_name in saved_props:
            if prop_name not in update_props:
                assert func.properties[prop_name] == saved_props[prop_name]

        # After refresh, updates are still reflected
        func.pull_full_properties()
        for prop_name, exp_value in update_props.items():
            assert func.properties[prop_name] == exp_value

    def test_function_update_name_cache(self):
        """Test AiAcceleratorFunction.update_properties() updates name cache."""
        faked_func = self.add_aifunc1()
        old_name = faked_func.name
        new_name = 'renamed-ai-func'

        mgr = self.partition.ai_accelerator_functions
        func = mgr.find(name=old_name)

        func.update_properties({'name': new_name})

        # Old name no longer findable
        with pytest.raises(NotFound):
            mgr.find(name=old_name)

        # New name is findable
        renamed = mgr.find(name=new_name)
        assert renamed.properties['name'] == new_name

    def test_manager_resource_object(self):
        """Test AiAcceleratorFunctionManager.resource_object()."""
        mgr = self.partition.ai_accelerator_functions
        func_oid = 'fake-ai-func-id0711'

        func = mgr.resource_object(func_oid)

        expected_uri = (
            self.partition.uri + '/ai-accelerator-functions/' + func_oid)

        assert isinstance(func, AiAcceleratorFunction)
        assert func.uri == expected_uri
        assert func.properties['element-uri'] == expected_uri
        assert func.properties['element-id'] == func_oid
        assert func.properties['class'] == 'ai-accelerator-function'
        assert func.properties['parent'] == self.partition.uri
