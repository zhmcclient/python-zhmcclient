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
Unit tests for _partition_link module.

Focus: managing attachment of partitions to partition links for SMC-D and
HiperSockets (hipersockets) typed partition links.
"""


import re
import pytest

from zhmcclient import Client, PartitionLink, PartitionLinkManager, \
    HTTPError, NotFound
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked resources:
CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'

PLINK1_OID = 'pl1-oid'
PLINK1_NAME = 'smcd link 1'

PLINK2_OID = 'pl2-oid'
PLINK2_NAME = 'hs link 2'

PART1_OID = 'part1-oid'
PART1_NAME = 'partition-1'
PART1_URI = f'/api/partitions/{PART1_OID}'

PART2_OID = 'part2-oid'
PART2_NAME = 'partition-2'
PART2_URI = f'/api/partitions/{PART2_OID}'

PART3_OID = 'part3-oid'
PART3_NAME = 'partition-3'
PART3_URI = f'/api/partitions/{PART3_OID}'


class TestPartitionLink:
    """All tests for the PartitionLink and PartitionLinkManager classes."""

    def setup_method(self):
        """
        Setup called by pytest before each test method.

        Sets up a faked session with a faked Console, CPC, and partitions.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.16.0', '4.10')
        self.client = Client(self.session)

        # Add a faked CPC in DPM mode
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': CPC_OID,
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
            'available-features-list': [
                {'name': 'dpm-smcd-partition-link-management', 'state': True},
                {'name': 'dpm-hipersockets-partition-link-management',
                 'state': True},
            ],
        })
        assert self.faked_cpc.uri == CPC_URI
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

        # Add a faked console
        self.faked_console = self.session.hmc.consoles.add({
            # object-id, object-uri, parent, class set automatically
            'name': 'fake-console-name',
            'description': 'The HMC',
        })
        self.console = self.client.consoles.console

        # Add faked partitions
        self.faked_part1 = self.faked_cpc.partitions.add({
            'object-id': PART1_OID,
            # object-uri is set up automatically
            'parent': CPC_URI,
            'class': 'partition',
            'name': PART1_NAME,
            'description': 'Partition 1',
            'status': 'stopped',
        })
        self.faked_part2 = self.faked_cpc.partitions.add({
            'object-id': PART2_OID,
            'parent': CPC_URI,
            'class': 'partition',
            'name': PART2_NAME,
            'description': 'Partition 2',
            'status': 'stopped',
        })
        self.faked_part3 = self.faked_cpc.partitions.add({
            'object-id': PART3_OID,
            'parent': CPC_URI,
            'class': 'partition',
            'name': PART3_NAME,
            'description': 'Partition 3',
            'status': 'stopped',
        })
        self.part1 = self.cpc.partitions.find(name=PART1_NAME)
        self.part2 = self.cpc.partitions.find(name=PART2_NAME)
        self.part3 = self.cpc.partitions.find(name=PART3_NAME)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def add_smcd_plink(self):
        """Add an SMC-D partition link (no partitions attached)."""
        faked = self.faked_console.partition_links.add({
            'object-id': PLINK1_OID,
            # object-uri set automatically
            'parent': self.faked_console.uri,
            'class': 'partition-link',
            'name': PLINK1_NAME,
            'description': 'SMC-D Partition Link #1',
            'type': 'smc-d',
            'cpc-uri': CPC_URI,
            'cpc-name': 'fake-cpc1-name',
            'state': 'incomplete',
            'bus-connections': [],
            'pending-operations': [],
            'starting-fid': 4096,
        })
        return faked

    def add_hs_plink(self):
        """Add a HiperSockets partition link (no partitions attached)."""
        faked = self.faked_console.partition_links.add({
            'object-id': PLINK2_OID,
            # object-uri set automatically
            'parent': self.faked_console.uri,
            'class': 'partition-link',
            'name': PLINK2_NAME,
            'description': 'HiperSockets Partition Link #2',
            'type': 'hipersockets',
            'cpc-uri': CPC_URI,
            'cpc-name': 'fake-cpc1-name',
            'state': 'incomplete',
            'bus-connections': [],
            'pending-operations': [],
            'maximum-transmission-unit-size': 8,
        })
        return faked

    # -----------------------------------------------------------------------
    # Manager attribute tests
    # -----------------------------------------------------------------------

    def test_plm_initial_attrs(self):
        """Test initial attributes of PartitionLinkManager."""

        plm = self.console.partition_links

        assert isinstance(plm, PartitionLinkManager)
        assert plm.resource_class == PartitionLink
        assert plm.class_name == 'partition-link'
        assert plm.session == self.session
        assert plm.parent == self.console
        assert plm.console == self.console

    # -----------------------------------------------------------------------
    # List tests
    # -----------------------------------------------------------------------

    testcases_plm_list_full_properties = (
        "full_properties_kwargs, prop_names", [
            ({},
             ['object-uri', 'cpc-uri', 'name', 'state', 'type']),
            ({'full_properties': False},
             ['object-uri', 'cpc-uri', 'name', 'state', 'type']),
        ]
    )

    @pytest.mark.parametrize(*testcases_plm_list_full_properties)
    def test_plm_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test PartitionLinkManager.list() with full_properties."""

        faked_pl1 = self.add_smcd_plink()
        faked_pl2 = self.add_hs_plink()

        plm = self.console.partition_links

        plinks = plm.list(**full_properties_kwargs)

        assert_resources(plinks, [faked_pl1, faked_pl2], prop_names)

    testcases_plm_list_filter_args = (
        "filter_args, exp_names", [
            ({'name': PLINK1_NAME},
             [PLINK1_NAME]),
            ({'name': PLINK2_NAME},
             [PLINK2_NAME]),
            ({'name': [PLINK1_NAME, PLINK2_NAME]},
             [PLINK1_NAME, PLINK2_NAME]),
            ({'name': PLINK1_NAME + 'foo'},
             []),
            ({'name': '.+'},
             [PLINK1_NAME, PLINK2_NAME]),
            ({'cpc-uri': CPC_URI},
             [PLINK1_NAME, PLINK2_NAME]),
            ({'cpc-uri': '/api/cpcs/other'},
             []),
        ]
    )

    @pytest.mark.parametrize(*testcases_plm_list_filter_args)
    def test_plm_list_filter_args(self, filter_args, exp_names):
        """Test PartitionLinkManager.list() with filter_args."""

        self.add_smcd_plink()
        self.add_hs_plink()

        plm = self.console.partition_links
        plinks = plm.list(filter_args=filter_args)

        assert len(plinks) == len(exp_names)
        if exp_names:
            names = [pl.properties['name'] for pl in plinks]
            assert set(names) == set(exp_names)

    # -----------------------------------------------------------------------
    # Create tests
    # -----------------------------------------------------------------------

    testcases_plm_create = (
        "input_props, exp_prop_names, exp_exc", [
            # Missing required fields → 400 Bad Request
            ({},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'x'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'x', 'cpc-uri': CPC_URI},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            # Minimal valid SMC-D partition link
            ({'name': 'mylink', 'type': 'smc-d', 'cpc-uri': CPC_URI},
             ['object-uri', 'name', 'type', 'cpc-uri'],
             None),
            # Minimal valid HiperSockets partition link
            ({'name': 'mylink-hs', 'type': 'hipersockets', 'cpc-uri': CPC_URI},
             ['object-uri', 'name', 'type', 'cpc-uri'],
             None),
        ]
    )

    @pytest.mark.parametrize(*testcases_plm_create)
    def test_plm_create(self, input_props, exp_prop_names, exp_exc):
        """Test PartitionLinkManager.create()."""

        plm = self.console.partition_links

        if exp_exc is not None:
            with pytest.raises(exp_exc.__class__) as exc_info:
                plm.create(properties=input_props)
            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason
        else:
            plink = plm.create(properties=input_props)

            assert isinstance(plink, PartitionLink)
            assert plink.name == input_props['name']
            assert plink.uri == plink.properties['object-uri']

            for prop_name in exp_prop_names:
                assert prop_name in plink.properties
                if prop_name in input_props:
                    assert plink.properties[prop_name] == input_props[prop_name]

    # -----------------------------------------------------------------------
    # Delete tests
    # -----------------------------------------------------------------------

    def test_pl_delete(self):
        """Test PartitionLink.delete()."""

        faked_pl = self.add_smcd_plink()
        self.add_hs_plink()

        plm = self.console.partition_links
        plink = plm.find(name=faked_pl.name)

        plink.delete()

        with pytest.raises(NotFound):
            plm.find(name=faked_pl.name)

    def test_pl_delete_create_same_name(self):
        """Test PartitionLink.delete() followed by create() with same name."""

        faked_pl = self.add_smcd_plink()
        plink_name = faked_pl.name

        plm = self.console.partition_links
        plink = plm.find(name=plink_name)
        plink.delete()

        with pytest.raises(NotFound):
            plm.find(name=plink_name)

        # Re-create with the same name
        new_pl = plm.create({
            'name': plink_name,
            'type': 'smc-d',
            'cpc-uri': CPC_URI,
            'description': 'Recreated',
        })
        assert new_pl.name == plink_name

    # -----------------------------------------------------------------------
    # update_properties (rename) tests
    # -----------------------------------------------------------------------

    def test_pl_update_name(self):
        """Test PartitionLink.update_properties() with a name change."""

        faked_pl = self.add_smcd_plink()
        plink_name = faked_pl.name

        plm = self.console.partition_links
        plink = plm.find(name=plink_name)
        new_name = 'renamed-' + plink_name

        plink.update_properties({'name': new_name})

        # Old name gone
        with pytest.raises(NotFound):
            plm.find(name=plink_name)

        # New name found
        found = plm.find(name=new_name)
        assert found.properties['name'] == new_name

    # -----------------------------------------------------------------------
    # Attach/detach tests — SMC-D
    # -----------------------------------------------------------------------

    def test_attach_smcd_single_partition(self):
        """
        Test Partition.attach_network_link() for an SMC-D partition link:
        attach one partition; link should be 'incomplete'.
        """
        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        part_uris = [bc['partition-uri'] for bc in bus_connections]
        assert PART1_URI in part_uris
        assert plink.get_property('state') == 'incomplete'

    def test_attach_smcd_two_partitions_complete(self):
        """
        Test Partition.attach_network_link() for an SMC-D partition link:
        attach two partitions; link should be 'complete'.
        """
        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)
        self.part2.attach_network_link(plink, number_of_nics=2)

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        part_uris = [bc['partition-uri'] for bc in bus_connections]
        assert PART1_URI in part_uris
        assert PART2_URI in part_uris
        assert plink.get_property('state') == 'complete'

    def test_detach_smcd_partition(self):
        """
        Test Partition.detach_network_link() for an SMC-D partition link:
        attach two partitions then detach one; link becomes 'incomplete'.
        """
        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)
        self.part2.attach_network_link(plink, number_of_nics=1)

        # Detach part1
        self.part1.detach_network_link(plink)

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        part_uris = [bc['partition-uri'] for bc in bus_connections]
        assert PART1_URI not in part_uris
        assert PART2_URI in part_uris
        assert plink.get_property('state') == 'incomplete'

    def test_detach_smcd_both_partitions(self):
        """
        Detach both partitions from an SMC-D link; state becomes 'incomplete'.
        """
        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)
        self.part2.attach_network_link(plink, number_of_nics=1)

        self.part1.detach_network_link(plink)
        self.part2.detach_network_link(plink)

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        assert bus_connections == []
        assert plink.get_property('state') == 'incomplete'

    def test_attach_smcd_with_nic_properties(self):
        """
        Test Partition.attach_network_link() passing explicit NIC properties
        for an SMC-D partition link.
        """
        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)

        self.part1.attach_network_link(
            plink,
            number_of_nics=1,
            nic_property_list=[
                {'device-number': '0010', 'fid': 100},
            ])

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        assert len(bus_connections) == 1
        bc = bus_connections[0]
        assert bc['partition-uri'] == PART1_URI
        # The NIC should carry through the supplied properties
        nics = bc.get('nics', [])
        assert len(nics) == 1
        nic = nics[0]
        assert nic.get('device-numbers') == ['0010']
        assert nic.get('fid') == 100

    def test_attach_smcd_multiple_nics(self):
        """
        Attach an SMC-D partition link with multiple NICs for a partition.
        """
        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)

        self.part1.attach_network_link(plink, number_of_nics=3)

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        bc = next(b for b in bus_connections if b['partition-uri'] == PART1_URI)
        assert len(bc.get('nics', [])) == 3

    # -----------------------------------------------------------------------
    # Attach/detach tests — HiperSockets
    # -----------------------------------------------------------------------

    def test_attach_hs_single_partition(self):
        """
        Test Partition.attach_network_link() for a HiperSockets partition link:
        attach one partition; link should be 'incomplete'.
        """
        self.add_hs_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK2_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        part_uris = [bc['partition-uri'] for bc in bus_connections]
        assert PART1_URI in part_uris
        assert plink.get_property('state') == 'incomplete'

    def test_attach_hs_two_partitions_complete(self):
        """
        Test Partition.attach_network_link() for a HiperSockets partition link:
        attach two partitions; link should be 'complete'.
        """
        self.add_hs_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK2_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)
        self.part2.attach_network_link(plink, number_of_nics=1)

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        part_uris = [bc['partition-uri'] for bc in bus_connections]
        assert PART1_URI in part_uris
        assert PART2_URI in part_uris
        assert plink.get_property('state') == 'complete'

    def test_attach_hs_three_partitions_complete(self):
        """
        Test attaching three partitions to a HiperSockets partition link.
        """
        self.add_hs_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK2_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)
        self.part2.attach_network_link(plink, number_of_nics=1)
        self.part3.attach_network_link(plink, number_of_nics=1)

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        part_uris = [bc['partition-uri'] for bc in bus_connections]
        assert PART1_URI in part_uris
        assert PART2_URI in part_uris
        assert PART3_URI in part_uris
        assert plink.get_property('state') == 'complete'

    def test_detach_hs_partition(self):
        """
        Test Partition.detach_network_link() for a HiperSockets partition link.
        """
        self.add_hs_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK2_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)
        self.part2.attach_network_link(plink, number_of_nics=1)

        self.part2.detach_network_link(plink)

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        part_uris = [bc['partition-uri'] for bc in bus_connections]
        assert PART1_URI in part_uris
        assert PART2_URI not in part_uris
        assert plink.get_property('state') == 'incomplete'

    def test_attach_hs_with_nic_properties(self):
        """
        Test attach with explicit NIC properties (device-number, vlan-id) for
        a HiperSockets partition link.
        """
        self.add_hs_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK2_NAME)

        self.part1.attach_network_link(
            plink,
            number_of_nics=1,
            nic_property_list=[
                {'device-number': '1a00', 'vlan-id': 100},
            ])

        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        bc = next(b for b in bus_connections if b['partition-uri'] == PART1_URI)
        nics = bc.get('nics', [])
        assert len(nics) == 1
        nic = nics[0]
        assert nic.get('device-numbers') == ['1a00']
        assert nic.get('vlan-id') == 100

    # -----------------------------------------------------------------------
    # list_attached_partitions tests
    # -----------------------------------------------------------------------

    def test_list_attached_partitions_empty(self):
        """Test PartitionLink.list_attached_partitions() on unattached link."""

        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)
        plink.pull_full_properties()

        parts = plink.list_attached_partitions()
        assert parts == []

    def test_list_attached_partitions_smcd(self):
        """Test PartitionLink.list_attached_partitions() for SMC-D link."""

        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)
        self.part2.attach_network_link(plink, number_of_nics=1)

        plink.pull_full_properties()
        parts = plink.list_attached_partitions()
        part_uris = [p.uri for p in parts]

        assert PART1_URI in part_uris
        assert PART2_URI in part_uris

    def test_list_attached_partitions_hs(self):
        """Test PartitionLink.list_attached_partitions() for HS link."""

        self.add_hs_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK2_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)

        plink.pull_full_properties()
        parts = plink.list_attached_partitions()
        part_uris = [p.uri for p in parts]

        assert PART1_URI in part_uris
        assert len(parts) == 1

    def test_list_attached_partitions_by_name(self):
        """Test PartitionLink.list_attached_partitions() with name filter."""

        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)

        self.part1.attach_network_link(plink, number_of_nics=1)
        self.part2.attach_network_link(plink, number_of_nics=1)

        plink.pull_full_properties()
        parts = plink.list_attached_partitions(name=PART1_NAME)
        part_uris = [p.uri for p in parts]

        assert PART1_URI in part_uris
        assert PART2_URI not in part_uris

    # -----------------------------------------------------------------------
    # PartitionLink.cpc property
    # -----------------------------------------------------------------------

    def test_pl_cpc_property(self):
        """Test PartitionLink.cpc returns the associated CPC."""

        self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=PLINK1_NAME)
        plink.pull_full_properties()

        cpc = plink.cpc
        assert cpc.uri == CPC_URI

    # -----------------------------------------------------------------------
    # Repr test
    # -----------------------------------------------------------------------

    def test_pl_repr(self):
        """Test PartitionLink.__repr__()."""

        faked_pl = self.add_smcd_plink()
        plm = self.console.partition_links
        plink = plm.find(name=faked_pl.name)

        repr_str = repr(plink)
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(
            rf'^{plink.__class__.__name__}\s+at\s+'
            rf'0x{id(plink):08x}\s+\(\\n.*',
            repr_str)

    # -----------------------------------------------------------------------
    # create() with initial bus-connections
    # -----------------------------------------------------------------------

    def test_plm_create_with_bus_connections_smc(self):
        """
        Test PartitionLinkManager.create() with initial bus-connections for
        an SMC-D partition link.
        """
        plm = self.console.partition_links
        plink = plm.create({
            'name': 'newlink',
            'type': 'smc-d',
            'cpc-uri': CPC_URI,
            'bus-connections': [
                {'partition-uri': PART1_URI, 'number-of-nics': 1},
                {'partition-uri': PART2_URI, 'number-of-nics': 2},
            ],
        })

        assert isinstance(plink, PartitionLink)
        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        part_uris = [bc['partition-uri'] for bc in bus_connections]
        assert PART1_URI in part_uris
        assert PART2_URI in part_uris

    def test_plm_create_with_bus_connections_hs(self):
        """
        Test PartitionLinkManager.create() with initial bus-connections for
        a HiperSockets partition link.
        """
        plm = self.console.partition_links
        plink = plm.create({
            'name': 'newlink-hs',
            'type': 'hipersockets',
            'cpc-uri': CPC_URI,
            'bus-connections': [
                {'partition-uri': PART1_URI, 'number-of-nics': 1},
            ],
        })

        assert isinstance(plink, PartitionLink)
        plink.pull_full_properties()
        bus_connections = plink.get_property('bus-connections')
        part_uris = [bc['partition-uri'] for bc in bus_connections]
        assert PART1_URI in part_uris
