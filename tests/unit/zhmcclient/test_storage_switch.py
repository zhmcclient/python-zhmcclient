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
Unit tests for _storage_switch module.
"""

import re
import copy
import pytest

from zhmcclient import Client, StorageSwitch, StorageSwitchManager, \
    HTTPError, NotFound
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources


# ---------------------------------------------------------------------------
# Object IDs and URIs of faked resources used across the test class
# ---------------------------------------------------------------------------

CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'

SFABRIC1_OID = 'sf1-oid'
SFABRIC1_URI = f'/api/storage-fabrics/{SFABRIC1_OID}'
SFABRIC1_NAME = 'Fabric A'

SFABRIC2_OID = 'sf2-oid'
SFABRIC2_URI = f'/api/storage-fabrics/{SFABRIC2_OID}'
SFABRIC2_NAME = 'Fabric B'

SSITE1_OID = 'ss1-oid'
SSITE1_URI = f'/api/storage-sites/{SSITE1_OID}'
SSITE1_NAME = 'Primary Site'

SSITE2_OID = 'ss2-oid'
SSITE2_URI = f'/api/storage-sites/{SSITE2_OID}'
SSITE2_NAME = 'Alternate Site'

SSWITCH1_OID = 'sw1-oid'
SSWITCH1_NAME = 'Storage switch 11'
SSWITCH1_DOMAIN_ID = '11'

SSWITCH2_OID = 'sw2-oid'
SSWITCH2_NAME = 'Storage switch 21'
SSWITCH2_DOMAIN_ID = '21'


class TestStorageSwitch:
    """All tests for the StorageSwitch and StorageSwitchManager classes."""

    def setup_method(self):
        """
        Setup called by pytest before each test method.

        Creates a faked session with a faked CPC (DPM mode), a faked console,
        two faked storage fabrics, and two faked storage sites.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.16.0', '4.10')
        self.client = Client(self.session)

        # Add a faked CPC in DPM mode
        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': CPC_OID,
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
            'available-features-list': [
                dict(name='dpm-storage-management', state=True),
            ],
        })
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

        # Add a faked console
        self.faked_console = self.session.hmc.consoles.add({
            'name': 'fake-console-name',
            'description': 'The HMC',
        })
        self.console = self.client.consoles.console

        # Add two faked storage fabrics
        self.faked_fabric1 = self.faked_console.storage_fabrics.add({
            'object-id': SFABRIC1_OID,
            'cpc-uri': CPC_URI,
            'name': SFABRIC1_NAME,
            'description': 'Fabric A',
            'high-integrity': False,
        })
        self.faked_fabric2 = self.faked_console.storage_fabrics.add({
            'object-id': SFABRIC2_OID,
            'cpc-uri': CPC_URI,
            'name': SFABRIC2_NAME,
            'description': 'Fabric B',
            'high-integrity': False,
        })

        # Add two faked storage sites
        self.faked_site1 = self.faked_console.storage_sites.add({
            'object-id': SSITE1_OID,
            'name': SSITE1_NAME,
            'description': 'Primary storage site',
            'cpc-uris': [CPC_URI],
        })
        self.faked_site2 = self.faked_console.storage_sites.add({
            'object-id': SSITE2_OID,
            'name': SSITE2_NAME,
            'description': 'Alternate storage site',
            'cpc-uris': [CPC_URI],
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def add_switch1(self):
        """Add storage switch 1 directly to the faked console."""
        return self.faked_console.storage_switches.add({
            'object-id': SSWITCH1_OID,
            'name': SSWITCH1_NAME,
            'domain-id': SSWITCH1_DOMAIN_ID,
            'storage-fabric-uri': SFABRIC1_URI,
            'storage-site-uri': SSITE1_URI,
            'description': 'Storage switch 11',
        })

    def add_switch2(self):
        """Add storage switch 2 directly to the faked console."""
        return self.faked_console.storage_switches.add({
            'object-id': SSWITCH2_OID,
            'name': SSWITCH2_NAME,
            'domain-id': SSWITCH2_DOMAIN_ID,
            'storage-fabric-uri': SFABRIC2_URI,
            'storage-site-uri': SSITE1_URI,
            'description': 'Storage switch 21',
        })

    # ==================================================================
    # StorageSwitchManager tests
    # ==================================================================

    def test_sswm_initial_attrs(self):
        """Test initial attributes of StorageSwitchManager."""

        sw_mgr = self.console.storage_switches

        assert isinstance(sw_mgr, StorageSwitchManager)
        assert sw_mgr.resource_class == StorageSwitch
        assert sw_mgr.session == self.session
        assert sw_mgr.parent == self.console
        assert sw_mgr.console == self.console

    # ------------------------------------------------------------------
    # list() — full_properties
    # ------------------------------------------------------------------

    testcases_sswm_list_full_properties = (
        "full_properties_kwargs, prop_names", [
            ({},
             ['object-uri', 'name', 'domain-id', 'storage-fabric-uri']),
            (dict(full_properties=False),
             ['object-uri', 'name', 'domain-id', 'storage-fabric-uri']),
        ]
    )

    @pytest.mark.parametrize(*testcases_sswm_list_full_properties)
    def test_sswm_list_full_props(self, full_properties_kwargs, prop_names):
        """Test StorageSwitchManager.list() short-props vs full_properties."""

        faked_sw1 = self.add_switch1()
        faked_sw2 = self.add_switch2()
        exp_faked_switches = [faked_sw1, faked_sw2]

        sw_mgr = self.console.storage_switches

        switches = sw_mgr.list(**full_properties_kwargs)

        assert_resources(switches, exp_faked_switches, prop_names)

    # ------------------------------------------------------------------
    # list() — filter_args
    # ------------------------------------------------------------------

    testcases_sswm_list_filter_args = (
        "filter_args, exp_names", [
            ({'object-id': SSWITCH1_OID},
             [SSWITCH1_NAME]),
            ({'object-id': SSWITCH2_OID},
             [SSWITCH2_NAME]),
            ({'object-id': [SSWITCH1_OID, SSWITCH2_OID]},
             [SSWITCH1_NAME, SSWITCH2_NAME]),
            ({'object-id': SSWITCH1_OID + 'foo'},
             []),
            ({'name': SSWITCH1_NAME},
             [SSWITCH1_NAME]),
            ({'name': SSWITCH2_NAME},
             [SSWITCH2_NAME]),
            ({'name': [SSWITCH1_NAME, SSWITCH2_NAME]},
             [SSWITCH1_NAME, SSWITCH2_NAME]),
            ({'name': SSWITCH1_NAME + 'foo'},
             []),
            ({'name': 'Storage switch .*'},
             [SSWITCH1_NAME, SSWITCH2_NAME]),
            ({'domain-id': SSWITCH1_DOMAIN_ID},
             [SSWITCH1_NAME]),
            ({'domain-id': SSWITCH2_DOMAIN_ID},
             [SSWITCH2_NAME]),
            ({'domain-id': '99'},
             []),
            ({'name': SSWITCH1_NAME, 'domain-id': SSWITCH1_DOMAIN_ID},
             [SSWITCH1_NAME]),
            ({'name': SSWITCH1_NAME, 'domain-id': SSWITCH2_DOMAIN_ID},
             []),
            ({'storage-fabric-uri': SFABRIC1_URI},
             [SSWITCH1_NAME]),
            ({'storage-fabric-uri': SFABRIC2_URI},
             [SSWITCH2_NAME]),
        ]
    )

    @pytest.mark.parametrize(*testcases_sswm_list_filter_args)
    def test_sswm_list_filter_args(self, filter_args, exp_names):
        """Test StorageSwitchManager.list() with filter_args."""

        self.add_switch1()
        self.add_switch2()

        sw_mgr = self.console.storage_switches

        switches = sw_mgr.list(filter_args=filter_args)

        assert len(switches) == len(exp_names)
        if exp_names:
            names = [s.properties['name'] for s in switches]
            assert set(names) == set(exp_names)

    # ------------------------------------------------------------------
    # list() — empty / two
    # ------------------------------------------------------------------

    def test_sswm_list_empty(self):
        """Test StorageSwitchManager.list() with no switches defined."""

        switches = self.console.storage_switches.list()

        assert switches == []

    def test_sswm_list_two(self):
        """Test StorageSwitchManager.list() with two switches defined."""

        self.add_switch1()
        self.add_switch2()

        switches = self.console.storage_switches.list()

        assert len(switches) == 2
        names = {s.properties['name'] for s in switches}
        assert names == {SSWITCH1_NAME, SSWITCH2_NAME}

    # ------------------------------------------------------------------
    # resource_object()
    # ------------------------------------------------------------------

    def test_sswm_resource_object(self):
        """Test StorageSwitchManager.resource_object()."""

        faked_sw = self.add_switch1()
        sw_oid = faked_sw.oid

        sw_mgr = self.console.storage_switches
        sw = sw_mgr.resource_object(sw_oid)

        expected_uri = f'/api/storage-switches/{sw_oid}'
        assert isinstance(sw, StorageSwitch)
        assert sw.properties['object-uri'] == expected_uri
        assert sw.properties['object-id'] == sw_oid
        assert sw.properties['class'] == 'storage-switch'
        assert sw.properties['parent'] == self.console.uri

    # ==================================================================
    # StorageSwitch resource tests
    # ==================================================================

    def test_ssw_repr(self):
        """Test StorageSwitch.__repr__()."""

        faked_sw = self.add_switch1()
        sw = self.console.storage_switches.find(name=faked_sw.name)

        repr_str = repr(sw)
        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(
            rf'^{sw.__class__.__name__}\s+at\s+'
            rf'0x{id(sw):08x}\s+\(\\n.*',
            repr_str)

    # ------------------------------------------------------------------
    # undefine()
    # ------------------------------------------------------------------

    def test_ssw_undefine(self):
        """Test StorageSwitch.undefine() removes the switch."""

        faked_sw = self.add_switch1()
        self.add_switch2()

        sw_mgr = self.console.storage_switches
        sw = sw_mgr.find(name=faked_sw.name)

        sw.undefine()

        with pytest.raises(NotFound):
            sw_mgr.find(name=faked_sw.name)

    def test_ssw_undefine_updates_fabric_uris(self):
        """Test that undefine() removes the switch URI from the fabric."""

        faked_sw = self.add_switch1()
        sw_uri = faked_sw.uri

        # Manually set the switch URI on the fabric's storage-switch-uris
        fabric1 = self.session.hmc.lookup_by_uri(SFABRIC1_URI)
        fabric1.update({'storage-switch-uris': [sw_uri]})

        sw = self.console.storage_switches.find(name=faked_sw.name)
        sw.undefine()

        fabric1 = self.session.hmc.lookup_by_uri(SFABRIC1_URI)
        assert sw_uri not in fabric1.properties.get('storage-switch-uris', [])

    def test_ssw_undefine_create_same(self):
        """Test undefine() followed by re-adding with the same name."""

        faked_sw = self.add_switch1()
        sw_name = faked_sw.name

        sw_mgr = self.console.storage_switches
        sw = sw_mgr.find(name=sw_name)
        sw.undefine()

        with pytest.raises(NotFound):
            sw_mgr.find(name=sw_name)

        # Re-add with same name
        self.faked_console.storage_switches.add({
            'object-id': 'sw1-new-oid',
            'name': sw_name,
            'domain-id': SSWITCH1_DOMAIN_ID,
            'storage-fabric-uri': SFABRIC1_URI,
            'storage-site-uri': SSITE1_URI,
            'description': 'Re-added switch',
        })

        sw_found = sw_mgr.find(name=sw_name)
        assert sw_found.get_property('description') == 'Re-added switch'

    # ------------------------------------------------------------------
    # update_properties()
    # ------------------------------------------------------------------

    testcases_ssw_update_props = (
        "input_props", [
            {},
            {'description': 'Updated description'},
            {'description': 'Updated description', 'domain-id': '99'},
        ]
    )

    @pytest.mark.parametrize(*testcases_ssw_update_props)
    def test_ssw_update_properties(self, input_props):
        """Test StorageSwitch.update_properties()."""

        self.add_switch1()

        sw_mgr = self.console.storage_switches
        sw = sw_mgr.find(name=SSWITCH1_NAME)
        sw.pull_full_properties()
        saved = copy.deepcopy(sw.properties)

        sw.update_properties(properties=input_props)

        for prop_name in saved:
            exp_value = (input_props[prop_name]
                         if prop_name in input_props
                         else saved[prop_name])
            assert prop_name in sw.properties
            assert sw.properties[prop_name] == exp_value

        sw.pull_full_properties()
        for prop_name in saved:
            exp_value = (input_props[prop_name]
                         if prop_name in input_props
                         else saved[prop_name])
            assert sw.properties[prop_name] == exp_value

    def test_ssw_update_name(self):
        """Test StorageSwitch.update_properties() with 'name' property."""

        faked_sw = self.add_switch1()
        old_name = faked_sw.name

        sw_mgr = self.console.storage_switches
        sw = sw_mgr.find(name=old_name)
        new_name = 'renamed-' + old_name

        sw.update_properties(properties={'name': new_name})

        assert len(sw_mgr.list(filter_args={'name': old_name})) == 0

        with pytest.raises(NotFound):
            sw_mgr.find(name=old_name)

        assert sw.properties['name'] == new_name

        sw.pull_full_properties()
        assert sw.properties['name'] == new_name

        sw_found = sw_mgr.find(name=new_name)
        assert sw_found.properties['name'] == new_name

        assert len(sw_mgr.list(filter_args={'name': new_name})) == 1

    # ------------------------------------------------------------------
    # move_to_storage_site()
    # ------------------------------------------------------------------

    def test_ssw_move_to_site(self):
        """Test StorageSwitch.move_to_storage_site() updates site URI."""

        self.add_switch1()

        sw_mgr = self.console.storage_switches
        sw = sw_mgr.find(name=SSWITCH1_NAME)
        sw.pull_full_properties()

        # Move to site2 (already registered in the faked HMC)
        sw.move_to_storage_site(SSITE2_URI)

        assert sw.properties['storage-site-uri'] == SSITE2_URI

        sw.pull_full_properties()
        assert sw.properties['storage-site-uri'] == SSITE2_URI

    def test_ssw_move_to_storage_site_not_found(self):
        """Test move_to_storage_site() raises 404 for unknown site URI."""

        self.add_switch1()
        sw = self.console.storage_switches.find(name=SSWITCH1_NAME)

        with pytest.raises(HTTPError) as exc_info:
            sw.move_to_storage_site('/api/storage-sites/nonexistent')

        assert exc_info.value.http_status == 404

    # ------------------------------------------------------------------
    # move_to_storage_fabric()
    # ------------------------------------------------------------------

    def test_ssw_move_to_storage_fabric(self):
        """Test StorageSwitch.move_to_storage_fabric() updates fabric URI."""

        faked_sw = self.add_switch1()
        sw_uri = faked_sw.uri

        # Pre-populate storage-switch-uris on fabric1
        fabric1 = self.session.hmc.lookup_by_uri(SFABRIC1_URI)
        fabric1.update({'storage-switch-uris': [sw_uri]})

        sw = self.console.storage_switches.find(name=SSWITCH1_NAME)

        sw.move_to_storage_fabric(SFABRIC2_URI)

        assert sw.properties['storage-fabric-uri'] == SFABRIC2_URI

        sw.pull_full_properties()
        assert sw.properties['storage-fabric-uri'] == SFABRIC2_URI

    def test_ssw_move_to_fabric_not_found(self):
        """Test move_to_storage_fabric() raises 404 for unknown fabric URI."""

        self.add_switch1()
        sw = self.console.storage_switches.find(name=SSWITCH1_NAME)

        with pytest.raises(HTTPError) as exc_info:
            sw.move_to_storage_fabric('/api/storage-fabrics/nonexistent')

        assert exc_info.value.http_status == 404

    # ------------------------------------------------------------------
    # Default properties
    # ------------------------------------------------------------------

    def test_ssw_default_properties(self):
        """Test that FakedStorageSwitch has correct default property values."""

        faked_sw = self.faked_console.storage_switches.add({
            'object-id': 'sw-defaults-oid',
            'name': 'Switch Defaults',
            'domain-id': '50',
            'storage-fabric-uri': SFABRIC1_URI,
            'storage-site-uri': SSITE1_URI,
        })

        sw = self.console.storage_switches.find(name='Switch Defaults')
        sw.pull_full_properties()

        assert sw.properties['description'] == ''
        assert sw.properties['port-count'] == 256

        faked_sw.manager.remove(faked_sw.oid)

    def test_ssw_class_property(self):
        """Test that the class property is set to 'storage-switch'."""

        self.add_switch1()
        sw = self.console.storage_switches.find(name=SSWITCH1_NAME)
        sw.pull_full_properties()

        assert sw.properties['class'] == 'storage-switch'

    def test_ssw_domain_id_property(self):
        """Test that domain-id is correctly stored and accessible."""

        self.add_switch1()
        self.add_switch2()

        sw_mgr = self.console.storage_switches

        sw1 = sw_mgr.find(name=SSWITCH1_NAME)
        sw1.pull_full_properties()
        assert sw1.properties['domain-id'] == SSWITCH1_DOMAIN_ID

        sw2 = sw_mgr.find(name=SSWITCH2_NAME)
        sw2.pull_full_properties()
        assert sw2.properties['domain-id'] == SSWITCH2_DOMAIN_ID

    def test_ssw_storage_fabric_uri_property(self):
        """Test that storage-fabric-uri is correctly stored."""

        self.add_switch1()
        self.add_switch2()

        sw_mgr = self.console.storage_switches

        sw1 = sw_mgr.find(name=SSWITCH1_NAME)
        sw1.pull_full_properties()
        assert sw1.properties['storage-fabric-uri'] == SFABRIC1_URI

        sw2 = sw_mgr.find(name=SSWITCH2_NAME)
        sw2.pull_full_properties()
        assert sw2.properties['storage-fabric-uri'] == SFABRIC2_URI

    # ------------------------------------------------------------------
    # URI handler — List by Storage Fabric
    # ------------------------------------------------------------------

    def test_list_switches_by_fabric(self):
        """Test GET /api/storage-fabrics/{id}/storage-switches."""

        self.add_switch1()
        self.add_switch2()

        result = self.session.get(
            f'/api/storage-fabrics/{SFABRIC1_OID}/storage-switches')

        assert 'storage-switches' in result
        names = [s['name'] for s in result['storage-switches']]
        assert SSWITCH1_NAME in names
        assert SSWITCH2_NAME not in names

    def test_list_switches_by_fabric_empty(self):
        """Test GET /api/storage-fabrics/{id}/storage-switches returns empty."""

        result = self.session.get(
            f'/api/storage-fabrics/{SFABRIC1_OID}/storage-switches')

        assert result == {'storage-switches': []}

    def test_list_switches_by_fabric_not_found(self):
        """Test GET on unknown fabric raises 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.get(
                '/api/storage-fabrics/nonexistent/storage-switches')

        assert exc_info.value.http_status == 404

    # ------------------------------------------------------------------
    # URI handler — List by Storage Site
    # ------------------------------------------------------------------

    def test_list_switches_by_site(self):
        """Test GET /api/storage-sites/{id}/storage-switches."""

        self.add_switch1()
        self.add_switch2()

        result = self.session.get(
            f'/api/storage-sites/{SSITE1_OID}/storage-switches')

        assert 'storage-switches' in result
        # Both switches belong to SSITE1
        names = {s['name'] for s in result['storage-switches']}
        assert names == {SSWITCH1_NAME, SSWITCH2_NAME}

    def test_list_switches_by_site_not_found(self):
        """Test GET on unknown site raises 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.get(
                '/api/storage-sites/nonexistent/storage-switches')

        assert exc_info.value.http_status == 404

    # ------------------------------------------------------------------
    # URI handler — Global list
    # ------------------------------------------------------------------

    def test_list_switches_global(self):
        """Test GET /api/storage-switches lists all switches."""

        self.add_switch1()
        self.add_switch2()

        result = self.session.get('/api/storage-switches')

        assert 'storage-switches' in result
        names = {s['name'] for s in result['storage-switches']}
        assert names == {SSWITCH1_NAME, SSWITCH2_NAME}

    def test_list_switches_global_filter_name(self):
        """Test GET /api/storage-switches?name=... filters correctly."""

        self.add_switch1()
        self.add_switch2()

        result = self.session.get(
            f'/api/storage-switches?name={SSWITCH1_NAME}')

        names = [s['name'] for s in result['storage-switches']]
        assert names == [SSWITCH1_NAME]

    # ------------------------------------------------------------------
    # URI handler — Get Properties
    # ------------------------------------------------------------------

    def test_get_switch_properties(self):
        """Test GET /api/storage-switches/{id} returns full properties."""

        faked_sw = self.add_switch1()

        result = self.session.get(f'/api/storage-switches/{faked_sw.oid}')

        assert result['name'] == SSWITCH1_NAME
        assert result['domain-id'] == SSWITCH1_DOMAIN_ID
        assert result['storage-fabric-uri'] == SFABRIC1_URI
        assert result['class'] == 'storage-switch'

    def test_get_switch_properties_not_found(self):
        """Test GET /api/storage-switches/{id} with unknown ID raises 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.get('/api/storage-switches/nonexistent-oid')

        assert exc_info.value.http_status == 404

    # ------------------------------------------------------------------
    # URI handler — Update Properties
    # ------------------------------------------------------------------

    def test_update_switch_properties_handler(self):
        """Test POST /api/storage-switches/{id} updates properties."""

        faked_sw = self.add_switch1()

        self.session.post(
            f'/api/storage-switches/{faked_sw.oid}',
            body={'description': 'Updated via handler'})

        result = self.session.get(f'/api/storage-switches/{faked_sw.oid}')
        assert result['description'] == 'Updated via handler'

    # ------------------------------------------------------------------
    # URI handler — Undefine
    # ------------------------------------------------------------------

    def test_undefine_handler(self):
        """Test POST /api/storage-switches/{id}/operations/undefine."""

        faked_sw = self.add_switch1()
        sw_oid = faked_sw.oid

        self.session.post(
            f'/api/storage-switches/{sw_oid}/operations/undefine',
            body=None)

        with pytest.raises(HTTPError) as exc_info:
            self.session.get(f'/api/storage-switches/{sw_oid}')
        assert exc_info.value.http_status == 404

    def test_undefine_handler_not_found(self):
        """Test undefine on unknown switch raises 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/storage-switches/nonexistent/operations/undefine',
                body=None)

        assert exc_info.value.http_status == 404

    # ------------------------------------------------------------------
    # URI handler — Define Storage Switch
    # ------------------------------------------------------------------

    def test_define_switch_handler(self):
        """Test POST /api/console/operations/define-storage-switch."""

        result = self.session.post(
            '/api/console/operations/define-storage-switch',
            body={
                'name': 'New Switch',
                'domain-id': '42',
                'storage-fabric-uri': SFABRIC1_URI,
                'storage-site-uri': SSITE1_URI,
            })

        assert 'object-uri' in result
        sw_uri = result['object-uri']
        assert sw_uri.startswith('/api/storage-switches/')

        # Verify the switch is retrievable
        props = self.session.get(sw_uri)
        assert props['name'] == 'New Switch'
        assert props['domain-id'] == '42'

        # Verify fabric storage-switch-uris updated
        fabric1 = self.session.hmc.lookup_by_uri(SFABRIC1_URI)
        assert sw_uri in fabric1.properties.get('storage-switch-uris', [])

    def test_define_switch_missing_req_field(self):
        """Test define with missing required fields raises 400."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/console/operations/define-storage-switch',
                body={
                    # Missing domain-id and storage-site-uri
                    'storage-fabric-uri': SFABRIC1_URI,
                })

        assert exc_info.value.http_status == 400

    def test_define_switch_unknown_fabric(self):
        """Test define with unknown storage-fabric-uri raises 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/console/operations/define-storage-switch',
                body={
                    'domain-id': '10',
                    'storage-fabric-uri': '/api/storage-fabrics/nonexistent',
                    'storage-site-uri': SSITE1_URI,
                })

        assert exc_info.value.http_status == 404

    def test_define_switch_unknown_site(self):
        """Test define with unknown storage-site-uri raises 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/console/operations/define-storage-switch',
                body={
                    'domain-id': '10',
                    'storage-fabric-uri': SFABRIC1_URI,
                    'storage-site-uri': '/api/storage-sites/nonexistent',
                })

        assert exc_info.value.http_status == 404

    # ------------------------------------------------------------------
    # URI handler — Move Storage Switch to Storage Site
    # ------------------------------------------------------------------

    def test_move_site_handler(self):
        """Test POST .../move-storage-site."""

        faked_sw = self.add_switch1()

        self.session.post(
            f'/api/storage-switches/{faked_sw.oid}/'
            'operations/move-storage-site',
            body={'storage-site-uri': SSITE2_URI})

        props = self.session.get(
            f'/api/storage-switches/{faked_sw.oid}')
        assert props['storage-site-uri'] == SSITE2_URI

    def test_move_site_handler_not_found(self):
        """Test move-storage-site on unknown switch raises 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/storage-switches/nonexistent/'
                'operations/move-storage-site',
                body={'storage-site-uri': SSITE2_URI})

        assert exc_info.value.http_status == 404

    # ------------------------------------------------------------------
    # URI handler — Move Storage Switch to Storage Fabric
    # ------------------------------------------------------------------

    def test_move_fabric_handler(self):
        """Test POST .../move-storage-fabric."""

        faked_sw = self.add_switch1()
        sw_uri = faked_sw.uri

        # Pre-populate fabric1 storage-switch-uris
        fabric1 = self.session.hmc.lookup_by_uri(SFABRIC1_URI)
        fabric1.update({'storage-switch-uris': [sw_uri]})

        self.session.post(
            f'/api/storage-switches/{faked_sw.oid}/'
            'operations/move-storage-fabric',
            body={'storage-fabric-uri': SFABRIC2_URI})

        props = self.session.get(f'/api/storage-switches/{faked_sw.oid}')
        assert props['storage-fabric-uri'] == SFABRIC2_URI

        # sw removed from fabric1 and added to fabric2
        fabric1 = self.session.hmc.lookup_by_uri(SFABRIC1_URI)
        sw_uris1 = fabric1.properties.get('storage-switch-uris', [])
        assert sw_uri not in sw_uris1

        fabric2 = self.session.hmc.lookup_by_uri(SFABRIC2_URI)
        sw_uris2 = fabric2.properties.get('storage-switch-uris', [])
        assert sw_uri in sw_uris2

    def test_move_fabric_handler_not_found(self):
        """Test move-storage-fabric on unknown switch raises 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/storage-switches/nonexistent/'
                'operations/move-storage-fabric',
                body={'storage-fabric-uri': SFABRIC2_URI})

        assert exc_info.value.http_status == 404
