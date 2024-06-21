# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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

# pylint: disable=protected-access,attribute-defined-outside-init

"""
Unit tests for _hmc module of the zhmcclient_mock package.
"""


import re
from datetime import datetime
from dateutil import tz
import pytz
import pytest

from zhmcclient_mock._session import FakedSession
from zhmcclient_mock._hmc import \
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
    FakedCapacityGroupManager, FakedCapacityGroup, \
    FakedMetricsContextManager, FakedMetricsContext, \
    FakedMetricGroupDefinition, FakedMetricObjectValues

from tests.common.utils import timestamp_aware


class TestFakedHmc:
    """All tests for the zhmcclient_mock.FakedHmc class."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC with attributes set but no child resourcs.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc

    def test_hmc_repr(self):
        """Test FakedHmc.__repr__()."""

        hmc = self.hmc

        # the function to be tested:
        repr_str = repr(hmc)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf"^{hmc.__class__.__name__}\s+at\s+"
            rf"0x{id(hmc):08x}\s+\(\\n.*", repr_str)

    def test_hmc_attrs(self):
        """Test FakedHmc attributes."""

        assert self.hmc.hmc_name == 'fake-hmc'
        assert self.hmc.hmc_version == '2.13.1'
        assert self.hmc.api_version == '1.8'
        assert isinstance(self.hmc.cpcs, FakedCpcManager)

        cpcs = self.hmc.cpcs.list()
        assert len(cpcs) == 0

    def test_hmc_1_cpc(self):
        """Test FakedHmc, adding and listing one CPC."""

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
        """Test FakedHmc, adding and listing two CPCs."""

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

    def test_hmc_add_resources(self):
        """Test FakedHmc.add_resources()."""

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

    def test_hmc_session_id(self):
        """Test FakedHmc.validate/add/remove_session_id()."""

        hmc = self.hmc

        session_id = 'valid_id'

        hmc.add_session_id(session_id)

        result = hmc.validate_session_id(session_id)
        assert result is True

        # Adding an already valid ID fails
        with pytest.raises(ValueError):
            hmc.add_session_id(session_id)

        hmc.remove_session_id(session_id)

        result = hmc.validate_session_id(session_id)
        assert result is False

        # Removing an invalid ID fails
        with pytest.raises(ValueError):
            hmc.remove_session_id(session_id)


class TestFakedBase:
    """All tests for the FakedBaseManager and FakedBaseResource classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has one managed CPC.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc

        self.cpc1_oid = '42-abc-543'
        self.cpc1_uri = f'/api/cpcs/{self.cpc1_oid}'

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
        assert re.match(
            rf"^{resource.__class__.__name__}\s+at\s+"
            rf"0x{id(resource):08x}\s+\(\\n.*", repr_str)

    def test_manager_repr(self):
        """Test FakedBaseManager.__repr__()."""

        manager = self.cpc_manager

        repr_str = repr(manager)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(
            rf"^{manager.__class__.__name__}\s+at\s+"
            rf"0x{id(manager):08x}\s+\(\\n.*", repr_str)

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


class TestFakedActivationProfile:
    """All tests for the FakedActivationProfileManager and
    FakedActivationProfile classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC in classic mode with some
        activation profiles.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
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


class TestFakedAdapter:
    """All tests for the FakedAdapterManager and FakedAdapter classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with one ROCE adapter.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
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
        assert re.match(
            rf"^{adapter.__class__.__name__}\s+at\s+"
            rf"0x{id(adapter):08x}\s+\(\\n.*", repr_str)

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


class TestFakedCpc:
    """All tests for the FakedCpcManager and FakedCpc classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
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
        assert re.match(
            rf"^{cpc.__class__.__name__}\s+at\s+"
            rf"0x{id(cpc):08x}\s+\(\\n.*", repr_str)

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
        assert isinstance(cpc1.capacity_groups, FakedCapacityGroupManager)
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


class TestFakedHba:
    """All tests for the FakedHbaManager and FakedHba classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with an FCP adapter, and a partition
        that has an HBA.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc

        self.adapter1_oid = '747-abc-12345'
        self.adapter1_uri = f'/api/adapters/{self.adapter1_oid}'
        self.port1_oid = '23'
        self.port1_uri = (f'/api/adapters/{self.adapter1_oid}/storage-ports/'
                          f'{self.port1_oid}')
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


# TODO: Add unit tests for FakedCapacityGroup/Manager.


class TestFakedLpar:
    """All tests for the FakedLparManager and FakedLpar classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with an LPAR.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
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


class TestFakedNic:
    """All tests for the FakedNicManager and FakedNic classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with a ROCE adapter and one
        partition that has a NIC.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc

        self.adapter1_oid = '380-xyz-12345'
        self.adapter1_uri = f'/api/adapters/{self.adapter1_oid}'
        self.port1_oid = '32'
        self.port1_uri = (f'/api/adapters/{self.adapter1_oid}/'
                          f'network-ports/{self.port1_oid}')
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
            'ssc-management-nic': False,
            'type': 'iqd',
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
            'ssc-management-nic': False,
            'type': 'iqd',
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


class TestFakedPartition:
    """All tests for the FakedPartitionManager and FakedPartition classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with a partition.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
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
        assert re.match(
            rf"^{partition.__class__.__name__}\s+at\s+"
            rf"0x{id(partition):08x}\s+\(\\n.*", repr_str)

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
            'partition-link-uris': [],
            'storage-group-uris': [],
            'tape-link-uris': [],
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
            'partition-link-uris': [],
            'storage-group-uris': [],
            'tape-link-uris': [],
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


class TestFakedPort:
    """All tests for the FakedPortManager and FakedPort classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with an OSA adapter with one Port.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
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


class TestFakedVirtualFunction:
    """All tests for the FakedVirtualFunctionManager and FakedVirtualFunction
    classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with a partition that has a virtual
        function.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
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
        """Test Partition 'virtual_functions' attribute."""

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


class TestFakedVirtualSwitch:
    """All tests for the FakedVirtualSwitchManager and FakedVirtualSwitch
    classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with a virtual switch.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
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


class TestFakedCapacityGroup:
    """All tests for the FakedCapacityGroupManager and FakedCapacityGroup
    classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with a capacity group.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
        self.cpc1_in_props = {'name': 'cpc1'}
        self.capacity_group1_in_props = {'name': 'capacity_group1'}
        rd = {
            'cpcs': [
                {
                    'properties': self.cpc1_in_props,
                    'capacity_groups': [
                        {'properties': self.capacity_group1_in_props},
                    ],
                },
            ]
        }
        # This already uses add() of FakedCapacityGroupManager:
        self.hmc.add_resources(rd)

    def test_capacity_groups_attr(self):
        """Test CPC 'capacity_groups' attribute."""

        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        assert isinstance(cpc1.capacity_groups, FakedCapacityGroupManager)
        assert re.match(cpc1.uri + '/capacity-groups',
                        cpc1.capacity_groups.base_uri)

    def test_capacity_groups_list(self):
        """Test list() of FakedCapacityGroupManager."""

        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]

        # the function to be tested:
        capacity_groups = cpc1.capacity_groups.list()

        assert len(capacity_groups) == 1
        capacity_group1 = capacity_groups[0]
        capacity_group1_out_props = self.capacity_group1_in_props.copy()
        capacity_group1_out_props.update({
            'element-id': capacity_group1.oid,
            'element-uri': capacity_group1.uri,
            'class': 'capacity-group',
            'parent': cpc1.uri,
            'partition-uris': [],
            'capping-enabled': True,
        })
        assert isinstance(capacity_group1, FakedCapacityGroup)
        assert capacity_group1.properties == capacity_group1_out_props
        assert capacity_group1.manager == cpc1.capacity_groups

    def test_capacity_groups_add(self):
        """Test add() of FakedCapacityGroupManager."""

        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        capacity_groups = cpc1.capacity_groups.list()
        assert len(capacity_groups) == 1

        capacity_group2_in_props = {'name': 'capacity_group2'}

        # the function to be tested:
        new_capacity_group = cpc1.capacity_groups.add(
            capacity_group2_in_props)

        capacity_groups = cpc1.capacity_groups.list()
        assert len(capacity_groups) == 2

        capacity_group2 = [p for p in capacity_groups
                           if p.properties['name'] ==  # noqa: W504
                           capacity_group2_in_props['name']][0]

        assert new_capacity_group.properties == capacity_group2.properties
        assert new_capacity_group.manager == capacity_group2.manager

        capacity_group2_out_props = capacity_group2_in_props.copy()
        capacity_group2_out_props.update({
            'element-id': capacity_group2.oid,
            'element-uri': capacity_group2.uri,
            'class': 'capacity-group',
            'parent': cpc1.uri,
            'partition-uris': [],
            'capping-enabled': True,
        })
        assert isinstance(capacity_group2, FakedCapacityGroup)
        assert capacity_group2.properties == capacity_group2_out_props
        assert capacity_group2.manager == cpc1.capacity_groups

    def test_capacity_groups_remove(self):
        """Test remove() of FakedCapacityGroupManager."""

        cpcs = self.hmc.cpcs.list()
        cpc1 = cpcs[0]
        capacity_groups = cpc1.capacity_groups.list()
        capacity_group1 = capacity_groups[0]
        assert len(capacity_groups) == 1

        # the function to be tested:
        cpc1.capacity_groups.remove(capacity_group1.oid)

        capacity_groups = cpc1.capacity_groups.list()
        assert len(capacity_groups) == 0


class TestFakedMetricsContext:
    """All tests for the FakedMetricsContextManager and FakedMetricsContext
    classes."""

    def setup_method(self):
        """
        Called by pytest before each test method.

        Creates a faked HMC that has a CPC with a partition.
        """
        session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.hmc = session.hmc
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

    def test_mcm_attr(self):
        """Test faked HMC 'metrics_contexts' attribute."""

        faked_hmc = self.hmc

        assert isinstance(faked_hmc.metrics_contexts,
                          FakedMetricsContextManager)
        assert re.match(r'/api/services/metrics/context',
                        faked_hmc.metrics_contexts.base_uri)

    def test_mcm_add(self):
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

    def test_mcm_add_get_metric_values(self):
        """
        Test add_metric_values() of FakedMetricsContextManager.
        """

        faked_hmc = self.hmc

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
        mo_val_group_names = faked_hmc.metric_values.keys()
        assert list(mo_val_group_names) == []

        # Verify that a first M.O.Val can be added
        faked_hmc.add_metric_values(mo_val_input)

        # Verify the M.O.Val group names after having added one
        mo_val_group_names = faked_hmc.metric_values.keys()
        assert list(mo_val_group_names) == [mg_name]

        # Verify that the M.O.Vals can be retrieved and contain the first one
        mo_vals = faked_hmc.metric_values[mg_name]
        assert list(mo_vals) == [mo_val_input]

        # Verify that a second M.O.Val can be added for the same group name
        faked_hmc.add_metric_values(mo_val2_input)

        # Verify the M.O.Val group names after having added a second M.O.Val
        # for the same group name -> still just one group name
        mo_val_group_names = faked_hmc.metric_values.keys()
        assert list(mo_val_group_names) == [mg_name]

        # Verify that the M.O.Vals can be retrieved and contain both
        mo_vals = faked_hmc.metric_values[mg_name]
        assert list(mo_vals) == [mo_val_input, mo_val2_input]

    def test_mc_get_mg_defs(self):
        """Test get_metric_group_definitions() of FakedMetricsContext."""

        faked_hmc = self.hmc

        mg_name = 'partition-usage'
        mg_def = faked_hmc.metric_groups[mg_name]
        mg_name2 = 'dpm-system-usage-overview'
        mg_def2 = faked_hmc.metric_groups[mg_name2]

        # Test case where only one M.G.Def is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            'metric-groups': [mg_name],
        }
        mc = faked_hmc.metrics_contexts.add(mc_in_props)

        # the function to be tested:
        mg_defs = mc.get_metric_group_definitions()

        # Verify the returned M.G.Defs
        assert list(mg_defs) == [mg_def]

        # Test case where the default for M.G.Defs is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            # 'metric-groups' not specified -> default: return all
        }
        mc = faked_hmc.metrics_contexts.add(mc_in_props)

        # the function to be tested:
        mg_defs = mc.get_metric_group_definitions()

        # Verify a subset of the returned M.G.Defs
        assert mg_def in mg_defs
        assert mg_def2 in mg_defs

    def test_mc_get_mg_infos(self):
        """Test get_metric_group_infos() of FakedMetricsContext."""

        faked_hmc = self.hmc

        mg_name = 'partition-usage'
        mg_def = faked_hmc.metric_groups[mg_name]
        mg_info = {
            'group-name': mg_name,
            'metric-infos': [
                {'metric-name': t[0], 'metric-type': t[1]}
                for t in mg_def.types
            ],
        }

        mg_name2 = 'dpm-system-usage-overview'
        mg_def2 = faked_hmc.metric_groups[mg_name2]
        mg_info2 = {
            'group-name': mg_name2,
            'metric-infos': [
                {'metric-name': t[0], 'metric-type': t[1]}
                for t in mg_def2.types
            ],
        }

        # Test case where only one M.G.Def is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            'metric-groups': [mg_name],
        }
        mc = faked_hmc.metrics_contexts.add(mc_in_props)

        # the function to be tested:
        mg_infos = mc.get_metric_group_infos()

        # Verify the returned M.G.Defs
        assert list(mg_infos) == [mg_info]

        # Test case where the default for M.G.Defs is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            # 'metric-groups' not specified -> default: return all
        }
        mc = faked_hmc.metrics_contexts.add(mc_in_props)

        # the function to be tested:
        mg_infos = mc.get_metric_group_infos()

        # Verify a subset of the returned M.G.Defs
        assert mg_info in mg_infos
        assert mg_info2 in mg_infos

    def test_mc_get_m_values(self):
        """Test get_metric_values() of FakedMetricsContext."""

        faked_hmc = self.hmc
        mc_mgr = faked_hmc.metrics_contexts

        mg_name = 'partition-usage'
        mo_val_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=datetime.now(),
            values=[
                ('processor-usage', 10),
                ('network-usage', 5),
            ])
        faked_hmc.add_metric_values(mo_val_input)
        mo_val2_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid2',
            timestamp=datetime.now(),
            values=[
                ('processor-usage', 12),
                ('network-usage', 3),
            ])
        faked_hmc.add_metric_values(mo_val2_input)

        exp_mo_vals = faked_hmc.metric_values[mg_name]

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

    def test_mc_get_m_values_response(self):
        """Test get_metric_values_response() of FakedMetricsContext."""

        faked_hmc = self.hmc
        mc_mgr = faked_hmc.metrics_contexts

        mg_name = 'partition-usage'

        ts1_input = datetime(2017, 9, 5, 12, 13, 10, 0, pytz.utc)
        ts1_exp = 1504613590000
        mo_val_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=ts1_input,
            values=[
                ('processor-usage', 12),
                ('network-usage', 3),
            ])
        faked_hmc.add_metric_values(mo_val_input)

        ts2_tz = pytz.timezone('CET')
        ts2_input = datetime(2017, 9, 5, 12, 13, 20, 0, ts2_tz)
        ts2_offset = int(ts2_tz.utcoffset(ts2_input).total_seconds())
        ts2_exp = 1504613600000 - 1000 * ts2_offset
        mo_val2_input = FakedMetricObjectValues(
            group_name=mg_name,
            resource_uri='/api/partitions/fake-oid',
            timestamp=ts2_input,
            values=[
                ('processor-usage', 10),
                ('network-usage', 5),
            ])
        faked_hmc.add_metric_values(mo_val2_input)

        mg_name2 = 'dpm-system-usage-overview'

        ts3_input = datetime(2017, 9, 5, 12, 13, 30, 0)  # timezone-naive
        ts3_offset = int(tz.tzlocal().utcoffset(ts3_input).total_seconds())
        ts3_exp = 1504613610000 - 1000 * ts3_offset
        mo_val3_input = FakedMetricObjectValues(
            group_name=mg_name2,
            resource_uri='/api/cpcs/fake-oid',
            timestamp=ts3_input,
            values=[
                ('processor-usage', 50),
                ('network-usage', 20),
            ])
        faked_hmc.add_metric_values(mo_val3_input)

        exp_mv_resp = f'''"partition-usage"
"/api/partitions/fake-oid"
{ts1_exp}
12,3

"/api/partitions/fake-oid"
{ts2_exp}
10,5


"dpm-system-usage-overview"
"/api/cpcs/fake-oid"
{ts3_exp}
50,20



'''

        # Test case where only one M.G.Def is tested
        mc_in_props = {
            'anticipated-frequency-seconds': 1,
            'metric-groups': [mg_name, mg_name2],
        }
        mc = mc_mgr.add(mc_in_props)

        # the function to be tested:
        mv_resp = mc.get_metric_values_response()

        assert mv_resp == exp_mv_resp, (
            f"Actual response string:\n{mv_resp!r}\n"
            f"Expected response string:\n{exp_mv_resp!r}\n")


def test_mgd_attr():
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


def test_mov_attr():
    """Test attributes of a FakedMetricObjectValues object."""

    in_timestamp = datetime.now()  # timezone-naive
    in_kwargs = {
        'group_name': 'partition-usage',
        'resource_uri': '/api/partitions/fake-oid',
        'timestamp': in_timestamp,
        'values': [
            ('metric-1', "a"),
            ('metric-2', 5),
        ]
    }
    exp_timestamp = timestamp_aware(in_timestamp)

    # the function to be tested:
    new_mov = FakedMetricObjectValues(**in_kwargs)

    assert new_mov.group_name == in_kwargs['group_name']
    assert new_mov.resource_uri == in_kwargs['resource_uri']
    assert new_mov.timestamp == exp_timestamp
    assert new_mov.values == in_kwargs['values']
    assert new_mov.values is not in_kwargs['values']  # was copied
