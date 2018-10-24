# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Unit tests for _hmc module of the zhmcclient_mock package.
"""

from __future__ import absolute_import, print_function

import re
from datetime import datetime
import pytest

from zhmcclient_mock._hmc import FakedHmc, \
    FakedBaseManager, FakedBaseResource, \
    FakedActivationProfileManager, FakedActivationProfile, \
    FakedAdapterManager, FakedAdapter, \
    FakedCpcManager, FakedCpc, \
    FakedHbaManager, FakedHba, \
    FakedLparManager, FakedLpar, \
    FakedNicManager, FakedNic, \
    FakedPartitionManager, FakedPartition, \
    FakedPortManager, FakedPort, \
    FakedVirtualFunctionManager, FakedVirtualFunction, \
    FakedVirtualSwitchManager, FakedVirtualSwitch, \
    FakedMetricsContextManager, FakedMetricsContext, \
    FakedMetricGroupDefinition, FakedMetricObjectValues


class TestFakedHmc(object):
    """All tests for the zhmcclient_mock.FakedHmc class."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')

    def test_repr(self):
        """Test FakedHmc.__repr__()."""
        hmc = self.hmc

        repr_str = repr(hmc)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=hmc.__class__.__name__, id=id(hmc)),
                        repr_str)

    def test_hmc(self):
        assert self.hmc.hmc_name == 'fake-hmc'
        assert self.hmc.hmc_version == '2.13.1'
        assert self.hmc.api_version == '1.8'
        assert isinstance(self.hmc.cpcs, FakedCpcManager)

        # the function to be tested:
        cpcs = self.hmc.cpcs.list()

        assert len(cpcs) == 0

    def test_hmc_1_cpc(self):
        cpc1_in_props = {'name': 'cpc1'}

        # the function to be tested:
        cpc1 = self.hmc.cpcs.add(cpc1_in_props)

        cpc1_out_props = cpc1_in_props.copy()
        cpc1_out_props.update({
            'object-id': cpc1.oid,
            'object-uri': cpc1.uri,
            'class': 'cpc',
            'parent': None,
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'status': 'operating',
        })

        # the function to be tested:
        cpcs = self.hmc.cpcs.list()

        assert len(cpcs) == 1
        assert cpcs[0] == cpc1

        assert isinstance(cpc1, FakedCpc)
        assert cpc1.properties == cpc1_out_props
        assert cpc1.manager == self.hmc.cpcs

    def test_hmc_2_cpcs(self):
        cpc1_in_props = {'name': 'cpc1'}

        # the function to be tested:
        cpc1 = self.hmc.cpcs.add(cpc1_in_props)

        cpc1_out_props = cpc1_in_props.copy()
        cpc1_out_props.update({
            'object-id': cpc1.oid,
            'object-uri': cpc1.uri,
            'class': 'cpc',
            'parent': None,
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'status': 'operating',
        })

        cpc2_in_props = {'name': 'cpc2'}

        # the function to be tested:
        cpc2 = self.hmc.cpcs.add(cpc2_in_props)

        cpc2_out_props = cpc2_in_props.copy()
        cpc2_out_props.update({
            'object-id': cpc2.oid,
            'object-uri': cpc2.uri,
            'class': 'cpc',
            'parent': None,
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'status': 'operating',
        })

        # the function to be tested:
        cpcs = self.hmc.cpcs.list()

        assert len(cpcs) == 2
        # We expect the order of addition to be maintained:
        assert cpcs[0] == cpc1
        assert cpcs[1] == cpc2

        assert isinstance(cpc1, FakedCpc)
        assert cpc1.properties == cpc1_out_props
        assert cpc1.manager == self.hmc.cpcs

        assert isinstance(cpc2, FakedCpc)
        assert cpc2.properties == cpc2_out_props
        assert cpc2.manager == self.hmc.cpcs

    def test_res_dict(self):
        cpc1_in_props = {'name': 'cpc1'}
        adapter1_in_props = {'name': 'osa1', 'adapter-family': 'hipersockets'}
        port1_in_props = {'name': 'osa1_1'}

        rd = {
            'cpcs': [
                {
                    'properties': cpc1_in_props,
                    'adapters': [
                        {
                            'properties': adapter1_in_props,
                            'ports': [
                                {'properties': port1_in_props},
                            ],
                        },
                    ],
                },
            ]
        }

        # the function to be tested:
        self.hmc.add_resources(rd)

        cpcs = self.hmc.cpcs.list()

        assert len(cpcs) == 1

        cpc1 = cpcs[0]
        cpc1_out_props = cpc1_in_props.copy()
        cpc1_out_props.update({
            'object-id': cpc1.oid,
            'object-uri': cpc1.uri,
            'class': 'cpc',
            'parent': None,
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'status': 'operating',
        })
        assert isinstance(cpc1, FakedCpc)
        assert cpc1.properties == cpc1_out_props
        assert cpc1.manager == self.hmc.cpcs

        cpc1_adapters = cpc1.adapters.list()

        assert len(cpc1_adapters) == 1
        adapter1 = cpc1_adapters[0]

        adapter1_ports = adapter1.ports.list()

        assert len(adapter1_ports) == 1
        port1 = adapter1_ports[0]

        adapter1_out_props = adapter1_in_props.copy()
        adapter1_out_props.update({
            'object-id': adapter1.oid,
            'object-uri': adapter1.uri,
            'class': 'adapter',
            'parent': cpc1.uri,
            'status': 'active',
            'network-port-uris': [port1.uri],
        })
        assert isinstance(adapter1, FakedAdapter)
        assert adapter1.properties == adapter1_out_props
        assert adapter1.manager == cpc1.adapters

        port1_out_props = port1_in_props.copy()
        port1_out_props.update({
            'element-id': port1.oid,
            'element-uri': port1.uri,
            'class': 'network-port',
            'parent': adapter1.uri,
        })
        assert isinstance(port1, FakedPort)
        assert port1.properties == port1_out_props
        assert port1.manager == adapter1.ports


class TestFakedBase(object):
    """All tests for the FakedBaseManager and FakedBaseResource classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')

        self.cpc1_oid = '42-abc-543'
        self.cpc1_uri = '/api/cpcs/%s' % self.cpc1_oid

        self.cpc1_in_props = {
            # All properties that are otherwise defaulted (but with non-default
            # values), plus 'name'.
            'object-id': self.cpc1_oid,
            'object-uri': self.cpc1_uri,
            'class': 'cpc',
            'parent': None,
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'status': 'service',
            'name': 'cpc1',
        }
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                },
            ]
        }
        self.hmc.add_resources(rd)
        self.cpc_manager = self.hmc.cpcs
        self.cpc_resource = self.hmc.cpcs.list()[0]
        self.cpc1_out_props = self.cpc1_in_props.copy()

    def test_resource_repr(self):
        """Test FakedBaseResource.__repr__()."""
        resource = self.cpc_resource

        repr_str = repr(resource)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=resource.__class__.__name__,
                               id=id(resource)),
                        repr_str)

    def test_manager_repr(self):
        """Test FakedBaseManager.__repr__()."""
        manager = self.cpc_manager

        repr_str = repr(manager)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=manager.__class__.__name__,
                               id=id(manager)),
                        repr_str)

    def test_manager_attr(self):
        """Test FakedBaseManager attributes."""

        assert isinstance(self.cpc_manager, FakedBaseManager)

        assert self.cpc_manager.hmc == self.hmc
        assert self.cpc_manager.parent == self.hmc
        assert self.cpc_manager.resource_class == FakedCpc
        assert self.cpc_manager.base_uri == '/api/cpcs'
        assert self.cpc_manager.oid_prop == 'object-id'
        assert self.cpc_manager.uri_prop == 'object-uri'

    def test_resource_attr(self):
        """Test FakedBaseResource attributes."""

        assert isinstance(self.cpc_resource, FakedBaseResource)

        assert self.cpc_resource.manager == self.cpc_manager
        assert self.cpc_resource.properties == self.cpc1_out_props
        assert self.cpc_resource.oid == self.cpc1_out_props['object-id']
        assert self.cpc_resource.uri == self.cpc1_out_props['object-uri']


class TestFakedActivationProfile(object):
    """All tests for the FakedActivationProfileManager and
    FakedActivationProfile classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1_in_props = {'name': 'cpc1'}
        self.resetprofile1_in_props = {'name': 'resetprofile1'}
        self.imageprofile1_in_props = {'name': 'imageprofile1'}
        self.loadprofile1_in_props = {'name': 'loadprofile1'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'reset_activation_profiles': [
                        {'properties': self.resetprofile1_in_props},
                    ],
                    'image_activation_profiles': [
                        {'properties': self.imageprofile1_in_props},
                    ],
                    'load_activation_profiles': [
                        {'properties': self.loadprofile1_in_props},
                    ],
                },
            ]
        }
        # This already uses add() of FakedActivationProfileManager:
        self.hmc.add_resources(rd)

    def test_profiles_attr(self):
        """Test CPC '*_activation_profiles' attributes."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        # Test reset activation profiles

        assert isinstance(cpc1.reset_activation_profiles,
                          FakedActivationProfileManager)
        assert cpc1.reset_activation_profiles.profile_type == 'reset'
        assert re.match(r'/api/cpcs/[^/]+/reset-activation-profiles',
                        cpc1.reset_activation_profiles.base_uri)

        # Test image activation profiles

        assert isinstance(cpc1.image_activation_profiles,
                          FakedActivationProfileManager)
        assert cpc1.image_activation_profiles.profile_type == 'image'
        assert re.match(r'/api/cpcs/[^/]+/image-activation-profiles',
                        cpc1.image_activation_profiles.base_uri)

        # Test load activation profiles

        assert isinstance(cpc1.load_activation_profiles,
                          FakedActivationProfileManager)
        assert cpc1.load_activation_profiles.profile_type == 'load'
        assert re.match(r'/api/cpcs/[^/]+/load-activation-profiles',
                        cpc1.load_activation_profiles.base_uri)

    def test_profiles_list(self):
        """Test list() of FakedActivationProfileManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        # Test reset activation profiles

        resetprofiles = cpc1.reset_activation_profiles.list()

        assert len(resetprofiles) == 1
        resetprofile1 = resetprofiles[0]
        resetprofile1_out_props = self.resetprofile1_in_props.copy()
        resetprofile1_out_props.update({
            'name': resetprofile1.oid,
            'element-uri': resetprofile1.uri,
            'class': 'reset-activation-profile',
            'parent': cpc1.uri,
        })
        assert isinstance(resetprofile1, FakedActivationProfile)
        assert resetprofile1.properties == resetprofile1_out_props
        assert resetprofile1.manager == cpc1.reset_activation_profiles

        # Test image activation profiles

        imageprofiles = cpc1.image_activation_profiles.list()

        assert len(imageprofiles) == 1
        imageprofile1 = imageprofiles[0]
        imageprofile1_out_props = self.imageprofile1_in_props.copy()
        imageprofile1_out_props.update({
            'name': imageprofile1.oid,
            'element-uri': imageprofile1.uri,
            'class': 'image-activation-profile',
            'parent': cpc1.uri,
        })
        assert isinstance(imageprofile1, FakedActivationProfile)
        assert imageprofile1.properties == imageprofile1_out_props
        assert imageprofile1.manager == cpc1.image_activation_profiles

        # Test load activation profiles

        loadprofiles = cpc1.load_activation_profiles.list()

        assert len(loadprofiles) == 1
        loadprofile1 = loadprofiles[0]
        loadprofile1_out_props = self.loadprofile1_in_props.copy()
        loadprofile1_out_props.update({
            'name': loadprofile1.oid,
            'element-uri': loadprofile1.uri,
            'class': 'load-activation-profile',
            'parent': cpc1.uri,
        })
        assert isinstance(loadprofile1, FakedActivationProfile)
        assert loadprofile1.properties == loadprofile1_out_props
        assert loadprofile1.manager == cpc1.load_activation_profiles

    def test_profiles_add(self):
        """Test add() of FakedActivationProfileManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        resetprofiles = cpc1.reset_activation_profiles.list()
        assert len(resetprofiles) == 1

        resetprofile2_in_props = {'name': 'resetprofile2'}

        # the function to be tested:
        new_resetprofile = cpc1.reset_activation_profiles.add(
            resetprofile2_in_props)

        resetprofiles = cpc1.reset_activation_profiles.list()
        assert len(resetprofiles) == 2

        resetprofile2 = [p for p in resetprofiles
                         if p.properties['name'] ==  # noqa: W504
                         resetprofile2_in_props['name']][0]

        assert new_resetprofile.properties == resetprofile2.properties
        assert new_resetprofile.manager == resetprofile2.manager

        resetprofile2_out_props = resetprofile2_in_props.copy()
        resetprofile2_out_props.update({
            'name': resetprofile2.oid,
            'element-uri': resetprofile2.uri,
            'class': 'reset-activation-profile',
            'parent': cpc1.uri,
        })
        assert isinstance(resetprofile2, FakedActivationProfile)
        assert resetprofile2.properties == resetprofile2_out_props
        assert resetprofile2.manager == cpc1.reset_activation_profiles

        # Because we know that the image and load profile managers are of the
        # same class, we don't need to test them.

    def test_profiles_remove(self):
        """Test remove() of FakedActivationProfileManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        resetprofiles = cpc1.reset_activation_profiles.list()
        resetprofile1 = resetprofiles[0]
        assert len(resetprofiles) == 1

        # the function to be tested:
        cpc1.reset_activation_profiles.remove(resetprofile1.oid)

        resetprofiles = cpc1.reset_activation_profiles.list()
        assert len(resetprofiles) == 0

        # Because we know that the image and load profile managers are of the
        # same class, we don't need to test them.


class TestFakedAdapter(object):
    """All tests for the FakedAdapterManager and FakedAdapter classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1_in_props = {'name': 'cpc1'}
        self.adapter1_in_props = {'name': 'adapter1', 'type': 'roce'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'adapters': [
                        {'properties': self.adapter1_in_props},
                    ],
                },
            ]
        }
        # This already uses add() of FakedAdapterManager:
        self.hmc.add_resources(rd)

    def test_adapter_repr(self):
        """Test FakedAdapter.__repr__()."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        adapters = cpc1.adapters.list()
        adapter = adapters[0]

        repr_str = repr(adapter)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=adapter.__class__.__name__,
                               id=id(adapter)),
                        repr_str)

    def test_adapters_attr(self):
        """Test CPC 'adapters' attribute."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        assert isinstance(cpc1.adapters, FakedAdapterManager)
        assert re.match(r'/api/adapters', cpc1.adapters.base_uri)

    def test_adapters_list(self):
        """Test list() of FakedAdapterManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        # the function to be tested:
        adapters = cpc1.adapters.list()

        assert len(adapters) == 1
        adapter1 = adapters[0]
        adapter1_out_props = self.adapter1_in_props.copy()
        adapter1_out_props.update({
            'object-id': adapter1.oid,
            'object-uri': adapter1.uri,
            'class': 'adapter',
            'parent': cpc1.uri,
            'status': 'active',
            'adapter-family': 'roce',
            'network-port-uris': [],
        })
        assert isinstance(adapter1, FakedAdapter)
        assert adapter1.properties == adapter1_out_props
        assert adapter1.manager == cpc1.adapters

        # Quick check of child resources:
        assert isinstance(adapter1.ports, FakedPortManager)

    def test_adapters_add(self):
        """Test add() of FakedAdapterManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        adapters = cpc1.adapters.list()
        assert len(adapters) == 1

        adapter2_in_props = {'name': 'adapter2', 'adapter-family': 'ficon'}

        # the function to be tested:
        new_adapter = cpc1.adapters.add(
            adapter2_in_props)

        adapters = cpc1.adapters.list()
        assert len(adapters) == 2

        adapter2 = [a for a in adapters
                    if a.properties['name'] == adapter2_in_props['name']][0]

        assert new_adapter.properties == adapter2.properties
        assert new_adapter.manager == adapter2.manager

        adapter2_out_props = adapter2_in_props.copy()
        adapter2_out_props.update({
            'object-id': adapter2.oid,
            'object-uri': adapter2.uri,
            'class': 'adapter',
            'parent': cpc1.uri,
            'status': 'active',
            'storage-port-uris': [],
        })
        assert isinstance(adapter2, FakedAdapter)
        assert adapter2.properties == adapter2_out_props
        assert adapter2.manager == cpc1.adapters

    def test_adapters_remove(self):
        """Test remove() of FakedAdapterManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        adapters = cpc1.adapters.list()
        adapter1 = adapters[0]
        assert len(adapters) == 1

        # the function to be tested:
        cpc1.adapters.remove(adapter1.oid)

        adapters = cpc1.adapters.list()
        assert len(adapters) == 0


class TestFakedCpc(object):
    """All tests for the FakedCpcManager and FakedCpc classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1_in_props = {'name': 'cpc1'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                },
            ]
        }
        # This already uses add() of FakedCpcManager:
        self.hmc.add_resources(rd)

    def test_cpc_repr(self):
        """Test FakedCpc.__repr__()."""
        cpcs = self.hmc.cpcs.list()
        cpc = cpcs[0]

        repr_str = repr(cpc)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=cpc.__class__.__name__, id=id(cpc)),
                        repr_str)

    def test_cpcs_attr(self):
        """Test HMC 'cpcs' attribute."""
        assert isinstance(self.hmc.cpcs, FakedCpcManager)
        assert re.match(r'/api/cpcs', self.hmc.cpcs.base_uri)

    def test_cpcs_list(self):
        """Test list() of FakedCpcManager."""

        # the function to be tested:
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        cpc1_out_props = self.cpc1_in_props.copy()
        cpc1_out_props.update({
            'object-id': cpc1.oid,
            'object-uri': cpc1.uri,
            'class': 'cpc',
            'parent': None,
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'status': 'operating',
        })
        assert isinstance(cpc1, FakedCpc)
        assert cpc1.properties == cpc1_out_props
        assert cpc1.manager == self.hmc.cpcs

        # Quick check of child resources:
        assert isinstance(cpc1.lpars, FakedLparManager)
        assert isinstance(cpc1.partitions, FakedPartitionManager)
        assert isinstance(cpc1.adapters, FakedAdapterManager)
        assert isinstance(cpc1.virtual_switches, FakedVirtualSwitchManager)
        assert isinstance(cpc1.reset_activation_profiles,
                          FakedActivationProfileManager)
        assert isinstance(cpc1.image_activation_profiles,
                          FakedActivationProfileManager)
        assert isinstance(cpc1.load_activation_profiles,
                          FakedActivationProfileManager)

    def test_cpcs_add(self):
        """Test add() of FakedCpcManager."""
        cpcs = self.hmc.cpcs.list()
        assert len(cpcs) == 1

        cpc2_in_props = {'name': 'cpc2'}

        # the function to be tested:
        new_cpc = self.hmc.cpcs.add(cpc2_in_props)

        cpcs = self.hmc.cpcs.list()
        assert len(cpcs) == 2

        cpc2 = [cpc for cpc in cpcs
                if cpc.properties['name'] == cpc2_in_props['name']][0]

        assert new_cpc.properties == cpc2.properties
        assert new_cpc.manager == cpc2.manager

        cpc2_out_props = cpc2_in_props.copy()
        cpc2_out_props.update({
            'object-id': cpc2.oid,
            'object-uri': cpc2.uri,
            'class': 'cpc',
            'parent': None,
            'dpm-enabled': False,
            'is-ensemble-member': False,
            'status': 'operating',
        })
        assert isinstance(cpc2, FakedCpc)
        assert cpc2.properties == cpc2_out_props
        assert cpc2.manager == self.hmc.cpcs

    def test_cpcs_remove(self):
        """Test remove() of FakedCpcManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        assert len(cpcs) == 1

        # the function to be tested:
        self.hmc.cpcs.remove(cpc1.oid)

        cpcs = self.hmc.cpcs.list()
        assert len(cpcs) == 0


class TestFakedHba(object):
    """All tests for the FakedHbaManager and FakedHba classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')

        self.adapter1_oid = '747-abc-12345'
        self.adapter1_uri = '/api/adapters/%s' % self.adapter1_oid
        self.port1_oid = '23'
        self.port1_uri = '/api/adapters/%s/storage-ports/%s' % \
            (self.adapter1_oid, self.port1_oid)
        self.hba1_oid = '999-123-xyz'

        self.cpc1_in_props = {'name': 'cpc1'}
        self.partition1_in_props = {'name': 'partition1'}
        self.adapter1_in_props = {
            'object-id': self.adapter1_oid,
            'name': 'fcp1',
            'type': 'fcp',
        }
        self.port1_in_props = {
            'element-id': self.port1_oid,
            'name': 'port1',
        }
        self.hba1_in_props = {
            'element-id': self.hba1_oid,
            'name': 'hba1',
            'adapter-port-uri': self.port1_uri,
        }
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'partitions': [
                        {
                            'properties': self.partition1_in_props,
                            'hbas': [
                                {'properties': self.hba1_in_props},
                            ],
                        },
                    ],
                    'adapters': [
                        {
                            'properties': self.adapter1_in_props,
                            'ports': [
                                {'properties': self.port1_in_props},
                            ],
                        },
                    ],
                },
            ]
        }
        # This already uses add() of FakedHbaManager:
        self.hmc.add_resources(rd)

    def test_hbas_attr(self):
        """Test Partition 'hbas' attribute."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]

        assert isinstance(partition1.hbas, FakedHbaManager)
        assert re.match(r'/api/partitions/[^/]+/hbas',
                        partition1.hbas.base_uri)

    def test_hbas_list(self):
        """Test list() of FakedHbaManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]

        # the function to be tested:
        hbas = partition1.hbas.list()

        assert len(hbas) == 1
        hba1 = hbas[0]
        hba1_out_props = self.hba1_in_props.copy()
        hba1_out_props.update({
            'element-id': self.hba1_oid,
            'element-uri': hba1.uri,
            'class': 'hba',
            'parent': partition1.uri,
            'device-number': hba1.properties['device-number'],
            'wwpn': hba1.properties['wwpn'],
        })
        assert isinstance(hba1, FakedHba)
        assert hba1.properties == hba1_out_props
        assert hba1.manager == partition1.hbas

    def test_hbas_add(self):
        """Test add() of FakedHbaManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]
        hbas = partition1.hbas.list()
        assert len(hbas) == 1

        hba2_oid = '22-55-xy'
        port_uri = '/api/adapters/abc-123/storage-ports/42'

        hba2_in_props = {
            'element-id': hba2_oid,
            'name': 'hba2',
            'adapter-port-uri': port_uri,
            'device-number': '8001',
            'wwpn': 'AFFEAFFE00008001',
        }

        # the function to be tested:
        new_hba = partition1.hbas.add(
            hba2_in_props)

        hbas = partition1.hbas.list()
        assert len(hbas) == 2

        hba2 = [hba for hba in hbas
                if hba.properties['name'] == hba2_in_props['name']][0]

        assert new_hba.properties == hba2.properties
        assert new_hba.manager == hba2.manager

        hba2_out_props = hba2_in_props.copy()
        hba2_out_props.update({
            'element-id': hba2_oid,
            'element-uri': hba2.uri,
            'class': 'hba',
            'parent': partition1.uri,
        })
        assert isinstance(hba2, FakedHba)
        assert hba2.properties == hba2_out_props
        assert hba2.manager == partition1.hbas

    def test_hbas_remove(self):
        """Test remove() of FakedHbaManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]
        hbas = partition1.hbas.list()
        hba1 = hbas[0]
        assert len(hbas) == 1

        # the function to be tested:
        partition1.hbas.remove(hba1.oid)

        hbas = partition1.hbas.list()
        assert len(hbas) == 0

    # TODO: Add testcases for updating 'hba-uris' parent property


class TestFakedLpar(object):
    """All tests for the FakedLparManager and FakedLpar classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1_in_props = {'name': 'cpc1'}
        self.lpar1_in_props = {'name': 'lpar1'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'lpars': [
                        {'properties': self.lpar1_in_props},
                    ],
                },
            ]
        }
        # This already uses add() of FakedLparManager:
        self.hmc.add_resources(rd)

    def test_lpars_attr(self):
        """Test CPC 'lpars' attribute."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        assert isinstance(cpc1.lpars, FakedLparManager)
        assert re.match(r'/api/logical-partitions', cpc1.lpars.base_uri)

    def test_lpars_list(self):
        """Test list() of FakedLparManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        # the function to be tested:
        lpars = cpc1.lpars.list()

        assert len(lpars) == 1
        lpar1 = lpars[0]
        lpar1_out_props = self.lpar1_in_props.copy()
        lpar1_out_props.update({
            'object-id': lpar1.oid,
            'object-uri': lpar1.uri,
            'class': 'logical-partition',
            'parent': cpc1.uri,
            'status': 'not-activated',
        })
        assert isinstance(lpar1, FakedLpar)
        assert lpar1.properties == lpar1_out_props
        assert lpar1.manager == cpc1.lpars

    def test_lpars_add(self):
        """Test add() of FakedLparManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        lpars = cpc1.lpars.list()
        assert len(lpars) == 1

        lpar2_in_props = {'name': 'lpar2'}

        # the function to be tested:
        new_lpar = cpc1.lpars.add(
            lpar2_in_props)

        lpars = cpc1.lpars.list()
        assert len(lpars) == 2

        lpar2 = [p for p in lpars
                 if p.properties['name'] == lpar2_in_props['name']][0]

        assert new_lpar.properties == lpar2.properties
        assert new_lpar.manager == lpar2.manager

        lpar2_out_props = lpar2_in_props.copy()
        lpar2_out_props.update({
            'object-id': lpar2.oid,
            'object-uri': lpar2.uri,
            'class': 'logical-partition',
            'parent': cpc1.uri,
            'status': 'not-activated',
        })
        assert isinstance(lpar2, FakedLpar)
        assert lpar2.properties == lpar2_out_props
        assert lpar2.manager == cpc1.lpars

    def test_lpars_remove(self):
        """Test remove() of FakedLparManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        lpars = cpc1.lpars.list()
        lpar1 = lpars[0]
        assert len(lpars) == 1

        # the function to be tested:
        cpc1.lpars.remove(lpar1.oid)

        lpars = cpc1.lpars.list()
        assert len(lpars) == 0


class TestFakedNic(object):
    """All tests for the FakedNicManager and FakedNic classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')

        self.adapter1_oid = '380-xyz-12345'
        self.adapter1_uri = '/api/adapters/%s' % self.adapter1_oid
        self.port1_oid = '32'
        self.port1_uri = '/api/adapters/%s/network-ports/%s' % \
            (self.adapter1_oid, self.port1_oid)
        self.nic1_oid = 'ddd-999-123'

        self.cpc1_in_props = {'name': 'cpc1'}
        self.partition1_in_props = {'name': 'partition1'}
        self.nic1_in_props = {
            'element-id': self.nic1_oid,
            'name': 'nic1',
            'network-adapter-port-uri': self.port1_uri,
        }
        self.adapter1_in_props = {
            'object-id': self.adapter1_oid,
            'name': 'roce1',
            'type': 'roce',
        }
        self.port1_in_props = {
            'element-id': self.port1_oid,
            'name': 'port1',
        }
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'partitions': [
                        {
                            'properties': self.partition1_in_props,
                            'nics': [
                                {'properties': self.nic1_in_props},
                            ],
                        },
                    ],
                    'adapters': [
                        {
                            'properties': self.adapter1_in_props,
                            'ports': [
                                {'properties': self.port1_in_props},
                            ],
                        },
                    ],
                },
            ]
        }
        # This already uses add() of FakedNicManager:
        self.hmc.add_resources(rd)

    def test_nics_attr(self):
        """Test Partition 'nics' attribute."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]

        assert isinstance(partition1.nics, FakedNicManager)
        assert re.match(r'/api/partitions/[^/]+/nics',
                        partition1.nics.base_uri)

    def test_nics_list(self):
        """Test list() of FakedNicManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]

        # the function to be tested:
        nics = partition1.nics.list()

        assert len(nics) == 1
        nic1 = nics[0]
        nic1_out_props = self.nic1_in_props.copy()
        nic1_out_props.update({
            'element-id': self.nic1_oid,
            'element-uri': nic1.uri,
            'class': 'nic',
            'parent': partition1.uri,
            'device-number': nic1.properties['device-number'],
        })
        assert isinstance(nic1, FakedNic)
        assert nic1.properties == nic1_out_props
        assert nic1.manager == partition1.nics

    def test_nics_add(self):
        """Test add() of FakedNicManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]
        nics = partition1.nics.list()
        assert len(nics) == 1

        nic2_oid = '77-55-ab'
        port_uri = '/api/adapters/abc-123/network-ports/42'

        nic2_in_props = {
            'element-id': nic2_oid,
            'name': 'nic2',
            'network-adapter-port-uri': port_uri,
        }

        # the function to be tested:
        new_nic = partition1.nics.add(
            nic2_in_props)

        nics = partition1.nics.list()
        assert len(nics) == 2

        nic2 = [nic for nic in nics
                if nic.properties['name'] == nic2_in_props['name']][0]

        assert new_nic.properties == nic2.properties
        assert new_nic.manager == nic2.manager

        nic2_out_props = nic2_in_props.copy()
        nic2_out_props.update({
            'element-id': nic2_oid,
            'element-uri': nic2.uri,
            'class': 'nic',
            'parent': partition1.uri,
            'device-number': nic2.properties['device-number'],
        })
        assert isinstance(nic2, FakedNic)
        assert nic2.properties == nic2_out_props
        assert nic2.manager == partition1.nics

    def test_nics_remove(self):
        """Test remove() of FakedNicManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]
        nics = partition1.nics.list()
        nic1 = nics[0]
        assert len(nics) == 1

        # the function to be tested:
        partition1.nics.remove(nic1.oid)

        nics = partition1.nics.list()
        assert len(nics) == 0

    # TODO: Add testcases for updating 'nic-uris' parent property


class TestFakedPartition(object):
    """All tests for the FakedPartitionManager and FakedPartition classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1_in_props = {'name': 'cpc1'}
        self.partition1_in_props = {'name': 'partition1'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'partitions': [
                        {'properties': self.partition1_in_props},
                    ],
                },
            ]
        }
        # This already uses add() of FakedPartitionManager:
        self.hmc.add_resources(rd)

    def test_partition_repr(self):
        """Test FakedPartition.__repr__()."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition = partitions[0]

        repr_str = repr(partition)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=partition.__class__.__name__,
                               id=id(partition)),
                        repr_str)

    def test_partitions_attr(self):
        """Test CPC 'partitions' attribute."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        assert isinstance(cpc1.partitions, FakedPartitionManager)
        assert re.match(r'/api/partitions', cpc1.partitions.base_uri)

    def test_partitions_list(self):
        """Test list() of FakedPartitionManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        # the function to be tested:
        partitions = cpc1.partitions.list()

        assert len(partitions) == 1
        partition1 = partitions[0]
        partition1_out_props = self.partition1_in_props.copy()
        partition1_out_props.update({
            'object-id': partition1.oid,
            'object-uri': partition1.uri,
            'class': 'partition',
            'parent': cpc1.uri,
            'status': 'stopped',
            'hba-uris': [],
            'nic-uris': [],
            'virtual-function-uris': [],
        })
        assert isinstance(partition1, FakedPartition)
        assert partition1.properties == partition1_out_props
        assert partition1.manager == cpc1.partitions

    def test_partitions_add(self):
        """Test add() of FakedPartitionManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        assert len(partitions) == 1

        partition2_in_props = {'name': 'partition2'}

        # the function to be tested:
        new_partition = cpc1.partitions.add(
            partition2_in_props)

        partitions = cpc1.partitions.list()
        assert len(partitions) == 2

        partition2 = [p for p in partitions
                      if p.properties['name'] ==  # noqa: W504
                      partition2_in_props['name']][0]

        assert new_partition.properties == partition2.properties
        assert new_partition.manager == partition2.manager

        partition2_out_props = partition2_in_props.copy()
        partition2_out_props.update({
            'object-id': partition2.oid,
            'object-uri': partition2.uri,
            'class': 'partition',
            'parent': cpc1.uri,
            'status': 'stopped',
            'hba-uris': [],
            'nic-uris': [],
            'virtual-function-uris': [],
        })
        assert isinstance(partition2, FakedPartition)
        assert partition2.properties == partition2_out_props
        assert partition2.manager == cpc1.partitions

    def test_partitions_remove(self):
        """Test remove() of FakedPartitionManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]
        assert len(partitions) == 1

        # the function to be tested:
        cpc1.partitions.remove(partition1.oid)

        partitions = cpc1.partitions.list()
        assert len(partitions) == 0


class TestFakedPort(object):
    """All tests for the FakedPortManager and FakedPort classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1_in_props = {'name': 'cpc1'}
        self.adapter1_in_props = {'name': 'adapter1', 'adapter-family': 'osa'}
        self.port1_in_props = {'name': 'port1'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'adapters': [
                        {
                            'properties': self.adapter1_in_props,
                            'ports': [
                                {'properties': self.port1_in_props},
                            ],
                        },
                    ],
                },
            ]
        }
        # This already uses add() of FakedPortManager:
        self.hmc.add_resources(rd)

    def test_ports_attr(self):
        """Test Adapter 'ports' attribute."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        adapters = cpc1.adapters.list()
        adapter1 = adapters[0]

        assert isinstance(adapter1.ports, FakedPortManager)
        assert re.match(r'/api/adapters/[^/]+/network-ports',
                        adapter1.ports.base_uri)

    def test_ports_list(self):
        """Test list() of FakedPortManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        adapters = cpc1.adapters.list()
        adapter1 = adapters[0]

        # the function to be tested:
        ports = adapter1.ports.list()

        assert len(ports) == 1
        port1 = ports[0]
        port1_out_props = self.port1_in_props.copy()
        port1_out_props.update({
            'element-id': port1.oid,
            'element-uri': port1.uri,
            'class': 'network-port',
            'parent': adapter1.uri,
        })
        assert isinstance(port1, FakedPort)
        assert port1.properties == port1_out_props
        assert port1.manager == adapter1.ports

    def test_ports_add(self):
        """Test add() of FakedPortManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        adapters = cpc1.adapters.list()
        adapter1 = adapters[0]
        ports = adapter1.ports.list()
        assert len(ports) == 1

        port2_in_props = {'name': 'port2'}

        # the function to be tested:
        new_port = adapter1.ports.add(
            port2_in_props)

        ports = adapter1.ports.list()
        assert len(ports) == 2

        port2 = [p for p in ports
                 if p.properties['name'] == port2_in_props['name']][0]

        assert new_port.properties == port2.properties
        assert new_port.manager == port2.manager

        port2_out_props = port2_in_props.copy()
        port2_out_props.update({
            'element-id': port2.oid,
            'element-uri': port2.uri,
            'class': 'network-port',
            'parent': adapter1.uri,
        })
        assert isinstance(port2, FakedPort)
        assert port2.properties == port2_out_props
        assert port2.manager == adapter1.ports

    def test_ports_remove(self):
        """Test remove() of FakedPortManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        adapters = cpc1.adapters.list()
        adapter1 = adapters[0]
        ports = adapter1.ports.list()
        port1 = ports[0]
        assert len(ports) == 1

        # the function to be tested:
        adapter1.ports.remove(port1.oid)

        ports = adapter1.ports.list()
        assert len(ports) == 0

    # TODO: Add testcases for updating 'network-port-uris' and
    #       'storage-port-uris' parent properties


class TestFakedVirtualFunction(object):
    """All tests for the FakedVirtualFunctionManager and FakedVirtualFunction
    classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1_in_props = {'name': 'cpc1'}
        self.partition1_in_props = {'name': 'partition1'}
        self.virtual_function1_in_props = {'name': 'virtual_function1'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'partitions': [
                        {
                            'properties': self.partition1_in_props,
                            'virtual_functions': [
                                {'properties':
                                 self.virtual_function1_in_props},
                            ],
                        },
                    ],
                },
            ]
        }
        # This already uses add() of FakedVirtualFunctionManager:
        self.hmc.add_resources(rd)

    def test_virtual_functions_attr(self):
        """Test CPC 'virtual_functions' attribute."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]

        assert isinstance(partition1.virtual_functions,
                          FakedVirtualFunctionManager)
        assert re.match(r'/api/partitions/[^/]+/virtual-functions',
                        partition1.virtual_functions.base_uri)

    def test_virtual_functions_list(self):
        """Test list() of FakedVirtualFunctionManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]

        # the function to be tested:
        virtual_functions = partition1.virtual_functions.list()

        assert len(virtual_functions) == 1
        virtual_function1 = virtual_functions[0]
        virtual_function1_out_props = self.virtual_function1_in_props.copy()
        virtual_function1_out_props.update({
            'element-id': virtual_function1.oid,
            'element-uri': virtual_function1.uri,
            'class': 'virtual-function',
            'parent': partition1.uri,
            'device-number': virtual_function1.properties['device-number'],
        })
        assert isinstance(virtual_function1, FakedVirtualFunction)
        assert virtual_function1.properties == virtual_function1_out_props
        assert virtual_function1.manager == partition1.virtual_functions

    def test_virtual_functions_add(self):
        """Test add() of FakedVirtualFunctionManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]
        virtual_functions = partition1.virtual_functions.list()
        assert len(virtual_functions) == 1

        virtual_function2_in_props = {'name': 'virtual_function2'}

        # the function to be tested:
        new_virtual_function = partition1.virtual_functions.add(
            virtual_function2_in_props)

        virtual_functions = partition1.virtual_functions.list()
        assert len(virtual_functions) == 2

        virtual_function2 = [vf for vf in virtual_functions
                             if vf.properties['name'] ==  # noqa: W504
                             virtual_function2_in_props['name']][0]

        assert new_virtual_function.properties == virtual_function2.properties
        assert new_virtual_function.manager == virtual_function2.manager

        virtual_function2_out_props = virtual_function2_in_props.copy()
        virtual_function2_out_props.update({
            'element-id': virtual_function2.oid,
            'element-uri': virtual_function2.uri,
            'class': 'virtual-function',
            'parent': partition1.uri,
            'device-number': virtual_function2.properties['device-number'],
        })
        assert isinstance(virtual_function2, FakedVirtualFunction)
        assert virtual_function2.properties == virtual_function2_out_props
        assert virtual_function2.manager == partition1.virtual_functions

    def test_virtual_functions_remove(self):
        """Test remove() of FakedVirtualFunctionManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        partitions = cpc1.partitions.list()
        partition1 = partitions[0]
        virtual_functions = partition1.virtual_functions.list()
        virtual_function1 = virtual_functions[0]
        assert len(virtual_functions) == 1

        # the function to be tested:
        partition1.virtual_functions.remove(virtual_function1.oid)

        virtual_functions = partition1.virtual_functions.list()
        assert len(virtual_functions) == 0

    # TODO: Add testcases for updating 'virtual-function-uris' parent property


class TestFakedVirtualSwitch(object):
    """All tests for the FakedVirtualSwitchManager and FakedVirtualSwitch
    classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1_in_props = {'name': 'cpc1'}
        self.virtual_switch1_in_props = {'name': 'virtual_switch1'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'virtual_switches': [
                        {'properties': self.virtual_switch1_in_props},
                    ],
                },
            ]
        }
        # This already uses add() of FakedVirtualSwitchManager:
        self.hmc.add_resources(rd)

    def test_virtual_switches_attr(self):
        """Test CPC 'virtual_switches' attribute."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        assert isinstance(cpc1.virtual_switches, FakedVirtualSwitchManager)
        assert re.match(r'/api/virtual-switches',
                        cpc1.virtual_switches.base_uri)

    def test_virtual_switches_list(self):
        """Test list() of FakedVirtualSwitchManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        # the function to be tested:
        virtual_switches = cpc1.virtual_switches.list()

        assert len(virtual_switches) == 1
        virtual_switch1 = virtual_switches[0]
        virtual_switch1_out_props = self.virtual_switch1_in_props.copy()
        virtual_switch1_out_props.update({
            'object-id': virtual_switch1.oid,
            'object-uri': virtual_switch1.uri,
            'class': 'virtual-switch',
            'parent': cpc1.uri,
            'connected-vnic-uris': [],
        })
        assert isinstance(virtual_switch1, FakedVirtualSwitch)
        assert virtual_switch1.properties == virtual_switch1_out_props
        assert virtual_switch1.manager == cpc1.virtual_switches

    def test_virtual_switches_add(self):
        """Test add() of FakedVirtualSwitchManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        virtual_switches = cpc1.virtual_switches.list()
        assert len(virtual_switches) == 1

        virtual_switch2_in_props = {'name': 'virtual_switch2'}

        # the function to be tested:
        new_virtual_switch = cpc1.virtual_switches.add(
            virtual_switch2_in_props)

        virtual_switches = cpc1.virtual_switches.list()
        assert len(virtual_switches) == 2

        virtual_switch2 = [p for p in virtual_switches
                           if p.properties['name'] ==  # noqa: W504
                           virtual_switch2_in_props['name']][0]

        assert new_virtual_switch.properties == virtual_switch2.properties
        assert new_virtual_switch.manager == virtual_switch2.manager

        virtual_switch2_out_props = virtual_switch2_in_props.copy()
        virtual_switch2_out_props.update({
            'object-id': virtual_switch2.oid,
            'object-uri': virtual_switch2.uri,
            'class': 'virtual-switch',
            'parent': cpc1.uri,
            'connected-vnic-uris': [],
        })
        assert isinstance(virtual_switch2, FakedVirtualSwitch)
        assert virtual_switch2.properties == virtual_switch2_out_props
        assert virtual_switch2.manager == cpc1.virtual_switches

    def test_virtual_switches_remove(self):
        """Test remove() of FakedVirtualSwitchManager."""
        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        virtual_switches = cpc1.virtual_switches.list()
        virtual_switch1 = virtual_switches[0]
        assert len(virtual_switches) == 1

        # the function to be tested:
        cpc1.virtual_switches.remove(virtual_switch1.oid)

        virtual_switches = cpc1.virtual_switches.list()
        assert len(virtual_switches) == 0


class TestFakedMetricsContext(object):
    """All tests for the FakedMetricsContextManager and FakedMetricsContext
    classes."""

    def setup_method(self):
        self.hmc = FakedHmc('fake-hmc', '2.13.1', '1.8')
        self.cpc1_in_props = {'name': 'cpc1'}
        self.partition1_in_props = {'name': 'partition1'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'partitions': [
                        {
                            'properties': self.partition1_in_props,
                        },
                    ],
                },
            ]
        }
        self.hmc.add_resources(rd)

    def test_metrics_contexts_attr(self):
        """Test faked HMC 'metrics_contexts' attribute."""
        faked_hmc = self.hmc

        assert isinstance(faked_hmc.metrics_contexts,
                          FakedMetricsContextManager)
        assert re.match(r'/api/services/metrics/context',
                        faked_hmc.metrics_contexts.base_uri)

    def test_metrics_contexts_add(self):
        """Test add() of FakedMetricsContextManager."""
        faked_hmc = self.hmc

        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            'metric-groups': ['partition-usage'],
        }

        # the function to be tested:
        mc = faked_hmc.metrics_contexts.add(mc_in_props)

        assert isinstance(mc, FakedMetricsContext)
        assert re.match(r'/api/services/metrics/context/[^/]+', mc.uri)
        assert mc.manager is faked_hmc.metrics_contexts
        mc_props = mc_in_props.copy()
        mc_props.update({
            'fake-id': mc.oid,
            'fake-uri': mc.uri,
            'parent': None,
        })
        assert mc.properties == mc_props

    def test_metrics_contexts_add_get_mg_def(self):
        """Test add_metric_group_definition(), get_metric_group_definition(),
        and get_metric_group_definition_names() of
        FakedMetricsContextManager."""

        faked_hmc = self.hmc
        mc_mgr = faked_hmc.metrics_contexts

        mg_name = 'partition-usage'
        mg_def_input = FakedMetricGroupDefinition(
            name=mg_name,
            types={
                'metric-1': 'string-metric',
                'metric-2': 'integer-metric',
            })

        # Verify the initial M.G.Def names
        mg_def_names = mc_mgr.get_metric_group_definition_names()
        assert list(mg_def_names) == []

        # Verify that a M.G.Def can be added
        mc_mgr.add_metric_group_definition(mg_def_input)

        # Verify the M.G.Def names after having added one
        mg_def_names = mc_mgr.get_metric_group_definition_names()
        assert list(mg_def_names) == [mg_name]

        # Verify that it can be retrieved
        mg_def = mc_mgr.get_metric_group_definition(mg_name)
        assert mg_def == mg_def_input

        # Verify that retrieving a non-existing M.G.Def fails
        with pytest.raises(ValueError) as exc_info:
            mc_mgr.get_metric_group_definition('foo')
        exc = exc_info.value
        assert re.match(r"^A metric group definition with this name does "
                        r"not exist:.*", str(exc))

        # Verify that adding an M.G.Def with an existing name fails
        with pytest.raises(ValueError) as exc_info:
            mc_mgr.add_metric_group_definition(mg_def_input)
        exc = exc_info.value
        assert re.match(r"^A metric group definition with this name already "
                        r"exists:.*", str(exc))

        # Verify that the M.G.Def names have not changed in these fails
        mg_def_names = mc_mgr.get_metric_group_definition_names()
        assert list(mg_def_names) == [mg_name]

    def test_metrics_contexts_add_get_metric_values(self):
        """Test add_metric_values(), get_metric_values(), and
        get_metric_values_group_names() of FakedMetricsContextManager."""

        faked_hmc = self.hmc
        mc_mgr = faked_hmc.metrics_contexts

        mg_name = 'partition-usage'
        mo_val_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=datetime.now(),
            values=[
                ('metric-1', "a"),
                ('metric-2', 5),
            ])
        mo_val2_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid2',
            timestamp=datetime.now(),
            values=[
                ('metric-1', "b"),
                ('metric-2', 7),
            ])

        # Verify the initial M.O.Val group names
        mo_val_group_names = mc_mgr.get_metric_values_group_names()
        assert list(mo_val_group_names) == []

        # Verify that a first M.O.Val can be added
        mc_mgr.add_metric_values(mo_val_input)

        # Verify the M.O.Val group names after having added one
        mo_val_group_names = mc_mgr.get_metric_values_group_names()
        assert list(mo_val_group_names) == [mg_name]

        # Verify that the M.O.Vals can be retrieved and contain the first one
        mo_vals = mc_mgr.get_metric_values(mg_name)
        assert list(mo_vals) == [mo_val_input]

        # Verify that retrieving a non-existing M.O.Val fails
        with pytest.raises(ValueError) as exc_info:
            mc_mgr.get_metric_values('foo')
        exc = exc_info.value
        assert re.match(r"^Metric values for this group name do not "
                        r"exist:.*", str(exc))

        # Verify that a second M.O.Val can be added for the same group name
        mc_mgr.add_metric_values(mo_val2_input)

        # Verify the M.O.Val group names after having added a second M.O.Val
        # for the same group name -> still just one group name
        mo_val_group_names = mc_mgr.get_metric_values_group_names()
        assert list(mo_val_group_names) == [mg_name]

        # Verify that the M.O.Vals can be retrieved and contain both
        mo_vals = mc_mgr.get_metric_values(mg_name)
        assert list(mo_vals) == [mo_val_input, mo_val2_input]

    def test_metrics_context_get_mg_defs(self):
        """Test get_metric_group_definitions() of FakedMetricsContext."""

        faked_hmc = self.hmc
        mc_mgr = faked_hmc.metrics_contexts

        mg_name = 'partition-usage'
        mg_def = FakedMetricGroupDefinition(
            name=mg_name,
            types=[
                ('metric-1', 'string-metric'),
                ('metric-2', 'integer-metric'),
            ])
        mc_mgr.add_metric_group_definition(mg_def)

        mg_name2 = 'cpc-usage'
        mg_def2 = FakedMetricGroupDefinition(
            name=mg_name2,
            types=[
                ('metric-3', 'string-metric'),
                ('metric-4', 'integer-metric'),
            ])
        mc_mgr.add_metric_group_definition(mg_def2)

        # Test case where only one M.G.Def is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            'metric-groups': [mg_name],
        }
        mc = faked_hmc.metrics_contexts.add(mc_in_props)
        exp_mg_defs = [mg_def]

        # the function to be tested:
        mg_defs = mc.get_metric_group_definitions()

        # Verify the returned M.G.Defs
        assert list(mg_defs) == exp_mg_defs

        # Test case where the default for M.G.Defs is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            # 'metric-groups' not specified -> default: return all
        }
        mc = faked_hmc.metrics_contexts.add(mc_in_props)
        exp_mg_defs = [mg_def, mg_def2]

        # the function to be tested:
        mg_defs = mc.get_metric_group_definitions()

        # Verify the returned M.G.Defs
        assert list(mg_defs) == exp_mg_defs

    def test_metrics_context_get_mg_infos(self):
        """Test get_metric_group_infos() of FakedMetricsContext."""

        faked_hmc = self.hmc
        mc_mgr = faked_hmc.metrics_contexts

        mg_name = 'partition-usage'
        mg_def = FakedMetricGroupDefinition(
            name=mg_name,
            types=[
                ('metric-1', 'string-metric'),
                ('metric-2', 'integer-metric'),
            ])
        mg_info = {
            'group-name': mg_name,
            'metric-infos': [
                {
                    'metric-name': 'metric-1',
                    'metric-type': 'string-metric',
                },
                {
                    'metric-name': 'metric-2',
                    'metric-type': 'integer-metric',
                },
            ],
        }
        mc_mgr.add_metric_group_definition(mg_def)

        mg_name2 = 'cpc-usage'
        mg_def2 = FakedMetricGroupDefinition(
            name=mg_name2,
            types=[
                ('metric-3', 'string-metric'),
                ('metric-4', 'integer-metric'),
            ])
        mg_info2 = {
            'group-name': mg_name2,
            'metric-infos': [
                {
                    'metric-name': 'metric-3',
                    'metric-type': 'string-metric',
                },
                {
                    'metric-name': 'metric-4',
                    'metric-type': 'integer-metric',
                },
            ],
        }
        mc_mgr.add_metric_group_definition(mg_def2)

        # Test case where only one M.G.Def is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            'metric-groups': [mg_name],
        }
        mc = faked_hmc.metrics_contexts.add(mc_in_props)
        exp_mg_infos = [mg_info]

        # the function to be tested:
        mg_infos = mc.get_metric_group_infos()

        # Verify the returned M.G.Defs
        assert list(mg_infos) == exp_mg_infos

        # Test case where the default for M.G.Defs is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            # 'metric-groups' not specified -> default: return all
        }
        mc = faked_hmc.metrics_contexts.add(mc_in_props)
        exp_mg_infos = [mg_info, mg_info2]

        # the function to be tested:
        mg_infos = mc.get_metric_group_infos()

        # Verify the returned M.G.Defs
        assert list(mg_infos) == exp_mg_infos

    def test_metrics_context_get_m_values(self):
        """Test get_metric_values() of FakedMetricsContext."""

        faked_hmc = self.hmc
        mc_mgr = faked_hmc.metrics_contexts

        mg_name = 'partition-usage'
        mg_def = FakedMetricGroupDefinition(
            name=mg_name,
            types=[
                ('metric-1', 'string-metric'),
                ('metric-2', 'integer-metric'),
            ])
        mc_mgr.add_metric_group_definition(mg_def)

        mo_val_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=datetime.now(),
            values=[
                ('metric-1', "a"),
                ('metric-2', 5),
            ])
        mc_mgr.add_metric_values(mo_val_input)
        mo_val2_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid2',
            timestamp=datetime.now(),
            values=[
                ('metric-1', "b"),
                ('metric-2', 7),
            ])
        mc_mgr.add_metric_values(mo_val2_input)
        exp_mo_vals = mc_mgr.get_metric_values(mg_name)

        # Test case where only one M.G.Def is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            'metric-groups': [mg_name],
        }
        mc = mc_mgr.add(mc_in_props)

        # the function to be tested:
        mv_list = mc.get_metric_values()

        assert len(mv_list) == 1
        mv = mv_list[0]
        assert mv[0] == mg_name
        assert mv[1] == exp_mo_vals

    def test_metrics_context_get_m_values_response(self):
        """Test get_metric_values_response() of FakedMetricsContext."""

        faked_hmc = self.hmc
        mc_mgr = faked_hmc.metrics_contexts

        mg_name = 'partition-usage'
        mg_def = FakedMetricGroupDefinition(
            name=mg_name,
            types=[
                ('metric-1', 'string-metric'),
                ('metric-2', 'integer-metric'),
                ('metric-3', 'double-metric'),
            ])
        mc_mgr.add_metric_group_definition(mg_def)

        mo_val_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=datetime(2017, 9, 5, 12, 13, 10, 0),
            values=[
                ('metric-1', "a"),
                ('metric-2', -5),
                ('metric-3', 3.1),
            ])
        mc_mgr.add_metric_values(mo_val_input)
        mo_val2_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=datetime(2017, 9, 5, 12, 13, 20, 0),
            values=[
                ('metric-1', "0"),
                ('metric-2', 7),
                ('metric-3', -4.2),
            ])
        mc_mgr.add_metric_values(mo_val2_input)

        mg_name2 = 'cpc-usage'
        mg_def2 = FakedMetricGroupDefinition(
            name=mg_name2,
            types=[
                ('metric-4', 'double-metric'),
            ])
        mc_mgr.add_metric_group_definition(mg_def2)

        mo_val3_input = FakedMetricObjectValues(
            group_name=mg_name2,
            resource_uri='/api/cpcs/fake-oid',
            timestamp=datetime(2017, 9, 5, 12, 13, 10, 0),
            values=[
                ('metric-4', 7.0),
            ])
        mc_mgr.add_metric_values(mo_val3_input)

        exp_mv_resp = '''"partition-usage"
"/api/partitions/fake-oid"
1504613590000
"a",-5,3.1

"/api/partitions/fake-oid"
1504613600000
"0",7,-4.2


"cpc-usage"
"/api/cpcs/fake-oid"
1504613590000
7.0



'''

        # Test case where only one M.G.Def is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            'metric-groups': [mg_name, mg_name2],
        }
        mc = mc_mgr.add(mc_in_props)

        # the function to be tested:
        mv_resp = mc.get_metric_values_response()

        assert mv_resp == exp_mv_resp, \
            "Actual response string:\n{!r}\n" \
            "Expected response string:\n{!r}\n". \
            format(mv_resp, exp_mv_resp)


class TestFakedMetricGroupDefinition(object):
    """All tests for the FakedMetricGroupDefinition class."""

    def test_metric_group_definition_attr(self):
        """Test attributes of a FakedMetricGroupDefinition object."""

        in_kwargs = {
            'name': 'partition-usage',
            'types': [
                ('metric-1', 'string-metric'),
                ('metric-2', 'integer-metric'),
            ]
        }

        # the function to be tested:
        new_mgd = FakedMetricGroupDefinition(**in_kwargs)

        assert new_mgd.name == in_kwargs['name']
        assert new_mgd.types == in_kwargs['types']
        assert new_mgd.types is not in_kwargs['types']  # was copied


class TestFakedMetricObjectValues(object):
    """All tests for the FakedMetricObjectValues class."""

    def test_metric_object_values_attr(self):
        """Test attributes of a FakedMetricObjectValues object."""

        in_kwargs = {
            'group_name': 'partition-usage',
            'resource_uri': '/api/partitions/fake-oid',
            'timestamp': datetime.now(),
            'values': [
                ('metric-1', "a"),
                ('metric-2', 5),
            ]
        }

        # the function to be tested:
        new_mov = FakedMetricObjectValues(**in_kwargs)

        assert new_mov.group_name == in_kwargs['group_name']
        assert new_mov.resource_uri == in_kwargs['resource_uri']
        assert new_mov.timestamp == in_kwargs['timestamp']
        assert new_mov.values == in_kwargs['values']
        assert new_mov.values is not in_kwargs['values']  # was copied
