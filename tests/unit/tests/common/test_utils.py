# Copyright 2017 IBM Corp. All Rights Reserved.
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
Unit test cases for the tests/common/utils.py module.
"""

from __future__ import absolute_import, print_function

import pytest

from zhmcclient import Client
from zhmcclient_mock import FakedSession

from tests.common.utils import assert_resources


class TestUtilsAssertResources(object):
    """All tests for utils.assert_resources()."""

    def setup_method(self):
        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

    def add_cpcs(self):
        faked_cpc1 = self.session.hmc.cpcs.add({
            'object-id': 'fake-cpc1-oid',
            # object-uri is auto-generated
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
        })
        faked_cpc2 = self.session.hmc.cpcs.add({
            'object-id': 'fake-cpc2-oid',
            # object-uri is auto-generated
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc2-name',
            'description': 'CPC #2',
            'status': 'active',
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'iml-mode': 'lpar',
        })
        return [faked_cpc1, faked_cpc2]

    @pytest.mark.parametrize(
        "reverse", [False, True]
    )
    @pytest.mark.parametrize(
        "props", ['all', 'some', 'empty', 'none']
    )
    def test_assert_resources_success(self, props, reverse):
        """Test assert_resources() with successful parameters."""

        faked_cpcs = self.add_cpcs()
        cpcs = self.client.cpcs.list(full_properties=True)

        resources = cpcs
        exp_resources = faked_cpcs
        if reverse:
            exp_resources = list(reversed(exp_resources))

        if props == 'all':
            prop_names = exp_resources[0].properties.keys()
        if props == 'some':
            prop_names = ['name', 'status']
            # We change a property that is not being checked:
            exp_resources[0].properties['description'] = 'changed description'
        elif props == 'empty':
            prop_names = []
            # No properties are checked, we change a property:
            exp_resources[0].properties['description'] = 'changed description'
        elif props == 'none':
            # All properties are checked.
            prop_names = None

        # Execute the code to be tested
        assert_resources(resources, exp_resources, prop_names)

        # If it comes back, our test is successful.

    @pytest.mark.parametrize(
        "reverse", [False, True]
    )
    @pytest.mark.parametrize(
        "props", ['all', 'some', 'none']
    )
    def test_assert_resources_error_props(self, props, reverse):
        """Test assert_resources() with failing property checks."""

        faked_cpcs = self.add_cpcs()
        cpcs = self.client.cpcs.list(full_properties=True)

        resources = cpcs
        exp_resources = faked_cpcs
        if reverse:
            exp_resources = list(reversed(exp_resources))

        if props == 'all':
            prop_names = exp_resources[0].properties.keys()
            # We change a property that is being checked:
            exp_resources[0].properties['description'] = 'changed description'
        if props == 'some':
            prop_names = ['name', 'status']
            # We change a property that is being checked:
            exp_resources[0].properties['status'] = 'not-operating'
        elif props == 'none':
            # All properties are checked.
            prop_names = None
            # We change a property that is being checked:
            exp_resources[0].properties['description'] = 'changed description'

        # Execute the code to be tested
        with pytest.raises(AssertionError):
            assert_resources(resources, exp_resources, prop_names)

    @pytest.mark.parametrize(
        "reverse", [False, True]
    )
    def test_assert_resources_error_res(self, reverse):
        """Test assert_resources() with failing resource list checks."""

        faked_cpcs = self.add_cpcs()
        cpcs = self.client.cpcs.list(full_properties=True)

        resources = cpcs[0:1]   # trigger non-matching resource list
        exp_resources = faked_cpcs
        if reverse:
            exp_resources = list(reversed(exp_resources))

        prop_names = exp_resources[0].properties.keys()

        # Execute the code to be tested
        with pytest.raises(AssertionError):
            assert_resources(resources, exp_resources, prop_names)
