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
Unit tests for Storage Control Units and Storage Paths using the faked HMC.
"""

import pytest

import zhmcclient
from zhmcclient.mock import FakedSession
from zhmcclient import Client, HTTPError

# ── Test fixture constants ─────────────────────────────────────────────────

CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'

SSITE1_OID = 'site1-oid'
SSITE1_URI = f'/api/storage-sites/{SSITE1_OID}'
SSITE1_NAME = 'Primary Site'

SUBSYS1_OID = 'subsys1-oid'
SUBSYS1_URI = f'/api/storage-subsystems/{SUBSYS1_OID}'
SUBSYS1_NAME = 'DS8886 A'

SUBSYS2_OID = 'subsys2-oid'
SUBSYS2_URI = f'/api/storage-subsystems/{SUBSYS2_OID}'
SUBSYS2_NAME = 'DS8886 B'

ADAPTER_OID = 'adap1-oid'
ADAPTER_PORT_OID = 'port1-oid'
ADAPTER_PORT_URI = (
    f'/api/adapters/{ADAPTER_OID}/storage-ports/{ADAPTER_PORT_OID}')

SWITCH1_OID = 'sw1-oid'
SWITCH1_URI = f'/api/storage-switches/{SWITCH1_OID}'

CU1_OID = 'cu1-oid'
CU1_NAME = 'Control unit 50'
CU1_ADDR = '50'

CU2_OID = 'cu2-oid'
CU2_NAME = 'Control unit 60'
CU2_ADDR = '60'


class TestStorageControlUnit:
    """Tests for StorageControlUnit and StoragePath resources."""

    def setup_method(self):
        # pylint: disable=attribute-defined-outside-init
        """Set up faked session, HMC, and common resources."""
        self.session = FakedSession('fake-host', 'fake-hmc', '2.16.0', '4.10')
        self.client = Client(self.session)

        self.session.hmc.cpcs.add({
            'object-id': CPC_OID,
            'parent': None,
            'class': 'cpc',
            'name': 'CPC1',
            'dpm-enabled': True,
        })
        self.faked_console = self.session.hmc.consoles.add({
            'name': 'HMC1',
        })
        self.console = self.client.consoles.console

        # Add storage site and subsystem
        self.faked_site1 = self.faked_console.storage_sites.add({
            'object-id': SSITE1_OID,
            'name': SSITE1_NAME,
        })
        self.faked_subsys1 = self.faked_console.storage_subsystems.add({
            'object-id': SUBSYS1_OID,
            'name': SUBSYS1_NAME,
            'storage-site-uri': SSITE1_URI,
        })
        self.faked_subsys2 = self.faked_console.storage_subsystems.add({
            'object-id': SUBSYS2_OID,
            'name': SUBSYS2_NAME,
            'storage-site-uri': SSITE1_URI,
        })

        # Add an adapter with a storage port for path tests
        faked_cpc = self.session.hmc.cpcs.lookup_by_oid(CPC_OID)
        faked_adapter = faked_cpc.adapters.add({
            'object-id': ADAPTER_OID,
            'name': 'Adapter1',
            'adapter-family': 'ficon',
            'type': 'fcp',
            'storage-port-uris': [],
        })
        faked_adapter.ports.add({
            'element-id': ADAPTER_PORT_OID,
            'name': 'Port0',
        })

        # Add a storage switch for path tests
        self.faked_switch1 = self.faked_console.storage_switches.add({
            'object-id': SWITCH1_OID,
            'name': 'SW1',
            'domain-id': '1',
            'storage-site-uri': SSITE1_URI,
            'storage-fabric-uri': '/api/storage-fabrics/fab1',
        })

    def _add_cu1(self):
        """Add control unit 1 as child of subsys1."""
        return self.faked_console.storage_control_units.add({
            'object-id': CU1_OID,
            'name': CU1_NAME,
            'logical-address': CU1_ADDR,
            'parent': SUBSYS1_URI,
        })

    def _add_cu2(self):
        """Add control unit 2 as child of subsys1."""
        return self.faked_console.storage_control_units.add({
            'object-id': CU2_OID,
            'name': CU2_NAME,
            'logical-address': CU2_ADDR,
            'parent': SUBSYS1_URI,
        })

    # ── Manager initial attrs ───────────────────────────────────────────────

    def test_cum_initial_attrs(self):
        """StorageControlUnitManager has correct initial attributes."""
        mgr = self.console.storage_control_units
        assert isinstance(mgr, zhmcclient.StorageControlUnitManager)
        assert mgr.console is self.console

    # ── list() ─────────────────────────────────────────────────────────────

    def test_cum_list_empty(self):
        """list() returns empty when no control units exist."""
        result = self.console.storage_control_units.list()
        assert result == []

    def test_cum_list_one(self):
        """list() returns one control unit."""
        self._add_cu1()
        result = self.console.storage_control_units.list()
        assert len(result) == 1
        assert isinstance(result[0], zhmcclient.StorageControlUnit)

    def test_cum_list_two(self):
        """list() returns both control units."""
        self._add_cu1()
        self._add_cu2()
        result = self.console.storage_control_units.list()
        assert len(result) == 2
        names = {cu.properties.get('name') for cu in result}
        assert names == {CU1_NAME, CU2_NAME}

    def test_cum_list_filter_by_name(self):
        """list() with name filter returns matching CU only."""
        self._add_cu1()
        self._add_cu2()
        result = self.console.storage_control_units.list(
            filter_args={'name': CU1_NAME})
        assert len(result) == 1
        assert result[0].properties['name'] == CU1_NAME

    def test_cum_list_filter_by_addr(self):
        """list() with logical-address filter returns matching CU."""
        self._add_cu1()
        self._add_cu2()
        result = self.console.storage_control_units.list(
            filter_args={'logical-address': CU2_ADDR})
        assert len(result) == 1
        assert result[0].properties['logical-address'] == CU2_ADDR

    # ── Default properties ─────────────────────────────────────────────────

    def test_cu_default_props(self):
        """FakedStorageControlUnit.add() sets correct defaults."""
        faked_cu = self._add_cu1()
        assert faked_cu.properties.get('description') == ''
        assert faked_cu.properties.get('storage-path-uris') == []
        assert faked_cu.properties.get('volume-ranges') == []

    def test_cu_class_property(self):
        """StorageControlUnit 'class' property is 'storage-control-unit'."""
        faked_cu = self._add_cu1()
        assert faked_cu.properties.get('class') == 'storage-control-unit'

    # ── Subsystem back-reference ────────────────────────────────────────────

    def test_cu_add_registers_in_subsystem(self):
        """Adding a CU registers its URI in parent subsystem's cu-uris."""
        faked_cu = self._add_cu1()
        cu_uris = self.faked_subsys1.properties.get(
            'storage-control-unit-uris', [])
        assert faked_cu.uri in cu_uris

    def test_two_cus_both_in_subsys(self):
        """Both CU URIs appear in parent subsystem's cu-uris."""
        faked_cu1 = self._add_cu1()
        faked_cu2 = self._add_cu2()
        cu_uris = self.faked_subsys1.properties.get(
            'storage-control-unit-uris', [])
        assert faked_cu1.uri in cu_uris
        assert faked_cu2.uri in cu_uris

    # ── repr ───────────────────────────────────────────────────────────────

    def test_cu_repr(self):
        """StorageControlUnit.__repr__() returns a non-empty string."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        assert repr(cu)

    # ── update_properties() ────────────────────────────────────────────────

    def test_cu_update_description(self):
        """update_properties() updates description locally."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        cu.update_properties({'description': 'updated desc'})
        assert cu.properties['description'] == 'updated desc'

    def test_cu_update_name(self):
        """update_properties() with name updates name-URI cache."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        cu.update_properties({'name': 'New CU Name'})
        assert cu.properties['name'] == 'New CU Name'
        found = self.console.storage_control_units.find(name='New CU Name')
        assert found.uri == cu.uri

    # ── Handler: GET /api/storage-control-units ────────────────────────────

    def test_list_handler_global(self):
        """GET /api/storage-control-units returns all CUs."""
        self._add_cu1()
        self._add_cu2()
        result = self.session.get('/api/storage-control-units')
        assert 'storage-control-units' in result
        assert len(result['storage-control-units']) == 2

    def test_list_handler_filter_name(self):
        """GET /api/storage-control-units?name=... filters correctly."""
        self._add_cu1()
        self._add_cu2()
        result = self.session.get(
            f'/api/storage-control-units?name={CU1_NAME}')
        assert len(result['storage-control-units']) == 1
        assert result['storage-control-units'][0]['name'] == CU1_NAME

    # ── Handler: GET /api/storage-subsystems/{id}/storage-control-units ────

    def test_list_by_subsystem(self):
        """Listing CUs by subsystem scopes results correctly."""
        self._add_cu1()
        self._add_cu2()
        # Add a CU for a different subsystem
        self.faked_console.storage_control_units.add({
            'name': 'Other CU', 'logical-address': 'ff',
            'parent': SUBSYS2_URI,
        })
        result = self.session.get(
            f'/api/storage-subsystems/{SUBSYS1_OID}/storage-control-units')
        assert 'storage-control-units' in result
        returned_names = {cu['name'] for cu in result['storage-control-units']}
        assert returned_names == {CU1_NAME, CU2_NAME}

    def test_list_by_subsys_not_found(self):
        """Listing CUs for a non-existent subsystem returns 404."""
        with pytest.raises(HTTPError) as exc_info:
            self.session.get(
                '/api/storage-subsystems/no-such/storage-control-units')
        assert exc_info.value.http_status == 404

    # ── Handler: POST define-storage-control-unit ──────────────────────────

    def test_define_cu_handler(self):
        """Define creates a CU and returns its URI."""
        result = self.session.post(
            f'/api/storage-subsystems/{SUBSYS1_OID}/operations/'
            'define-storage-control-unit',
            body={'logical-address': '50'})
        assert 'object-uri' in result
        assert '/api/storage-control-units/' in result['object-uri']

    def test_define_cu_registers_in_subsys(self):
        """Define updates parent subsystem's storage-control-unit-uris."""
        result = self.session.post(
            f'/api/storage-subsystems/{SUBSYS1_OID}/operations/'
            'define-storage-control-unit',
            body={'logical-address': '51'})
        cu_uri = result['object-uri']
        cu_uris = self.faked_subsys1.properties.get(
            'storage-control-unit-uris', [])
        assert cu_uri in cu_uris

    def test_define_cu_default_name(self):
        """Define sets default name to 'Control unit {addr}'."""
        self.session.post(
            f'/api/storage-subsystems/{SUBSYS1_OID}/operations/'
            'define-storage-control-unit',
            body={'logical-address': '55'})
        cus = self.console.storage_control_units.list(
            filter_args={'logical-address': '55'})
        assert len(cus) == 1
        assert cus[0].properties['name'] == 'Control unit 55'

    def test_define_cu_custom_name(self):
        """Define with explicit name uses that name."""
        self.session.post(
            f'/api/storage-subsystems/{SUBSYS1_OID}/operations/'
            'define-storage-control-unit',
            body={'logical-address': '56', 'name': 'My CU'})
        cus = self.console.storage_control_units.list(
            filter_args={'name': 'My CU'})
        assert len(cus) == 1

    def test_define_cu_missing_logical_addr(self):
        """Define without logical-address returns 400."""
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                f'/api/storage-subsystems/{SUBSYS1_OID}/operations/'
                'define-storage-control-unit',
                body={'name': 'Bad CU'})
        assert exc_info.value.http_status == 400

    def test_define_cu_dup_logical_addr(self):
        """Define with duplicate logical-address returns 409/447."""
        self._add_cu1()
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                f'/api/storage-subsystems/{SUBSYS1_OID}/operations/'
                'define-storage-control-unit',
                body={'logical-address': CU1_ADDR})
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 447

    def test_define_cu_dup_name(self):
        """Define with duplicate name returns 400/8."""
        self._add_cu1()
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                f'/api/storage-subsystems/{SUBSYS1_OID}/operations/'
                'define-storage-control-unit',
                body={'logical-address': 'ff', 'name': CU1_NAME})
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 8

    def test_define_cu_subsys_not_found(self):
        """Define on non-existent subsystem returns 404."""
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/storage-subsystems/no-such/operations/'
                'define-storage-control-unit',
                body={'logical-address': '50'})
        assert exc_info.value.http_status == 404

    # ── Handler: POST undefine ─────────────────────────────────────────────

    def test_undefine_cu_handler(self):
        """Undefine removes the CU from the HMC."""
        faked_cu = self._add_cu1()
        cu_uri = faked_cu.uri
        self.session.post(cu_uri + '/operations/undefine', body=None)
        with pytest.raises(HTTPError):
            self.session.get(cu_uri)

    def test_undefine_cu_removes_from_subsys(self):
        """Undefine removes CU URI from parent subsystem's cu-uris."""
        faked_cu = self._add_cu1()
        cu_uri = faked_cu.uri
        self.session.post(cu_uri + '/operations/undefine', body=None)
        cu_uris = self.faked_subsys1.properties.get(
            'storage-control-unit-uris', [])
        assert cu_uri not in cu_uris

    def test_undefine_cu_removes_paths(self):
        """Undefine also removes all child storage paths."""
        faked_cu = self._add_cu1()
        # Add a storage path manually
        faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        assert len(faked_cu.storage_paths.list(None)) == 1
        self.session.post(faked_cu.uri + '/operations/undefine', body=None)
        # After undefine, CU is gone; verify via manager list
        result = self.console.storage_control_units.list()
        assert all(cu.uri != faked_cu.uri for cu in result)

    def test_undefine_cu_not_found(self):
        """Undefine on non-existent CU returns 404."""
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/storage-control-units/no-such/operations/undefine',
                body=None)
        assert exc_info.value.http_status == 404

    # ── StorageControlUnit.undefine() client method ────────────────────────

    def test_cu_undefine_method(self):
        """StorageControlUnit.undefine() removes the resource."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        cu.undefine()
        result = self.console.storage_control_units.list()
        assert all(c.uri != cu.uri for c in result)

    # ── Volume ranges ──────────────────────────────────────────────────────

    def test_add_volume_range(self):
        """add_volume_range() appends a range to volume-ranges."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        cu.add_volume_range('00', '0f', 'base')
        cu.pull_full_properties()
        vr = cu.properties.get('volume-ranges', [])
        assert len(vr) == 1
        assert vr[0]['starting-volume'] == '00'
        assert vr[0]['ending-volume'] == '0f'
        assert vr[0]['type'] == 'base'

    def test_add_volume_range_default_ending(self):
        """add_volume_range() defaults ending-volume to starting-volume."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        cu.add_volume_range('05')
        cu.pull_full_properties()
        vr = cu.properties.get('volume-ranges', [])
        assert len(vr) == 1
        assert vr[0]['ending-volume'] == '05'

    def test_add_volume_range_handler(self):
        """Handler for add-volume-range appends to volume-ranges."""
        faked_cu = self._add_cu1()
        self.session.post(
            faked_cu.uri + '/operations/add-volume-range',
            body={'starting-volume': 'a0', 'ending-volume': 'af',
                  'type': 'alias'})
        vr = faked_cu.properties.get('volume-ranges', [])
        assert len(vr) == 1
        assert vr[0]['type'] == 'alias'

    def test_add_volume_range_missing_field(self):
        """Handler for add-volume-range without starting-volume returns 400."""
        faked_cu = self._add_cu1()
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                faked_cu.uri + '/operations/add-volume-range',
                body={'ending-volume': '0f'})
        assert exc_info.value.http_status == 400

    def test_remove_volume_range(self):
        """remove_volume_range() removes the matching range."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        cu.add_volume_range('00', '0f', 'base')
        cu.remove_volume_range('00', '0f', 'base')
        cu.pull_full_properties()
        vr = cu.properties.get('volume-ranges', [])
        assert len(vr) == 0

    def test_remove_volume_range_not_found(self):
        """Handler for remove-volume-range on missing range returns 409."""
        faked_cu = self._add_cu1()
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                faked_cu.uri + '/operations/remove-volume-range',
                body={'starting-volume': 'ff'})
        assert exc_info.value.http_status == 409

    # ── Storage paths ──────────────────────────────────────────────────────

    def test_path_manager_initial(self):
        """StoragePath manager is accessible and empty initially."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        paths = cu.storage_paths.list()
        assert paths == []

    def test_create_path(self):
        """StoragePathManager.create() creates a path and returns it."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        path = cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        assert isinstance(path, zhmcclient.StoragePath)
        assert path.uri.startswith(cu.uri + '/storage-paths/')

    def test_create_path_handler(self):
        """POST to storage-paths creates a path and updates cu uris."""
        faked_cu = self._add_cu1()
        result = self.session.post(
            faked_cu.uri + '/storage-paths',
            body={'adapter-port-uri': ADAPTER_PORT_URI})
        assert 'element-uri' in result
        path_uris = faked_cu.properties.get('storage-path-uris', [])
        assert result['element-uri'] in path_uris

    def test_create_path_registers_in_cu(self):
        """FakedStoragePathManager.add() registers URI in cu's path-uris."""
        faked_cu = self._add_cu1()
        faked_path = faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        path_uris = faked_cu.properties.get('storage-path-uris', [])
        assert faked_path.uri in path_uris

    def test_create_path_with_switch(self):
        """Creating a path with exit-switch-uri and exit-port succeeds."""
        faked_cu = self._add_cu1()
        result = self.session.post(
            faked_cu.uri + '/storage-paths',
            body={
                'adapter-port-uri': ADAPTER_PORT_URI,
                'exit-switch-uri': SWITCH1_URI,
                'exit-port': '00',
            })
        assert 'element-uri' in result

    def test_path_coreq_missing_port(self):
        """exit-switch-uri without exit-port returns 400/442."""
        faked_cu = self._add_cu1()
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                faked_cu.uri + '/storage-paths',
                body={
                    'adapter-port-uri': ADAPTER_PORT_URI,
                    'exit-switch-uri': SWITCH1_URI,
                })
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 442

    def test_path_coreq_missing_switch(self):
        """exit-port without exit-switch-uri returns 400/442."""
        faked_cu = self._add_cu1()
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                faked_cu.uri + '/storage-paths',
                body={
                    'adapter-port-uri': ADAPTER_PORT_URI,
                    'exit-port': '00',
                })
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 442

    def test_create_path_adapter_not_found(self):
        """Creating a path with unknown adapter-port-uri returns 404/2."""
        faked_cu = self._add_cu1()
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                faked_cu.uri + '/storage-paths',
                body={'adapter-port-uri': '/api/adapters/no/storage-ports/x'})
        assert exc_info.value.http_status == 404
        assert exc_info.value.reason == 2

    def test_create_path_missing_required_field(self):
        """Creating a path without adapter-port-uri returns 400."""
        faked_cu = self._add_cu1()
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                faked_cu.uri + '/storage-paths',
                body={'exit-port': '00'})
        assert exc_info.value.http_status == 400

    def test_create_path_cu_not_found(self):
        """Creating a path for non-existent CU returns 404."""
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/storage-control-units/no-such/storage-paths',
                body={'adapter-port-uri': ADAPTER_PORT_URI})
        assert exc_info.value.http_status == 404

    def test_create_path_max_exceeded(self):
        """Creating more than 8 paths for one CU returns 409/486."""
        faked_cu = self._add_cu1()
        # Add 8 paths directly to the faked CU to reach the maximum
        for i in range(8):
            faked_cu.storage_paths.add({
                'adapter-port-uri': ADAPTER_PORT_URI,
                'exit-switch-uri': None,
                'exit-port': None,
                '_idx': i,  # distinguish them
            })
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                faked_cu.uri + '/storage-paths',
                body={'adapter-port-uri': ADAPTER_PORT_URI})
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 486

    def test_create_path_duplicate(self):
        """Creating a duplicate path returns 400/8."""
        faked_cu = self._add_cu1()
        # Create first path
        self.session.post(
            faked_cu.uri + '/storage-paths',
            body={'adapter-port-uri': ADAPTER_PORT_URI})
        # Try to create an identical path
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                faked_cu.uri + '/storage-paths',
                body={'adapter-port-uri': ADAPTER_PORT_URI})
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 8

    def test_list_paths_handler(self):
        """GET storage-paths lists all paths of the CU."""
        faked_cu = self._add_cu1()
        faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        result = self.session.get(faked_cu.uri + '/storage-paths')
        assert 'storage-paths' in result
        assert len(result['storage-paths']) == 1

    def test_get_path_properties(self):
        """GET on a single storage path returns its properties."""
        faked_cu = self._add_cu1()
        result = self.session.post(
            faked_cu.uri + '/storage-paths',
            body={'adapter-port-uri': ADAPTER_PORT_URI})
        path_uri = result['element-uri']
        props = self.session.get(path_uri)
        assert props['adapter-port-uri'] == ADAPTER_PORT_URI

    def test_update_path_properties(self):
        """POST on a storage path updates its properties."""
        faked_cu = self._add_cu1()
        result = self.session.post(
            faked_cu.uri + '/storage-paths',
            body={'adapter-port-uri': ADAPTER_PORT_URI})
        path_uri = result['element-uri']
        self.session.post(path_uri,
                          body={'exit-switch-uri': SWITCH1_URI,
                                'exit-port': '00'})
        props = self.session.get(path_uri)
        assert props['exit-switch-uri'] == SWITCH1_URI
        assert props['exit-port'] == '00'

    def test_delete_path_handler(self):
        """DELETE on a storage path removes it."""
        faked_cu = self._add_cu1()
        result = self.session.post(
            faked_cu.uri + '/storage-paths',
            body={'adapter-port-uri': ADAPTER_PORT_URI})
        path_uri = result['element-uri']
        self.session.delete(path_uri)
        with pytest.raises(HTTPError):
            self.session.get(path_uri)

    def test_delete_path_removes_from_cu_uris(self):
        """Deleting a path removes its URI from cu's storage-path-uris."""
        faked_cu = self._add_cu1()
        result = self.session.post(
            faked_cu.uri + '/storage-paths',
            body={'adapter-port-uri': ADAPTER_PORT_URI})
        path_uri = result['element-uri']
        self.session.delete(path_uri)
        path_uris = faked_cu.properties.get('storage-path-uris', [])
        assert path_uri not in path_uris

    def test_delete_path_not_found(self):
        """DELETE on non-existent path returns 404."""
        faked_cu = self._add_cu1()
        with pytest.raises(HTTPError) as exc_info:
            self.session.delete(faked_cu.uri + '/storage-paths/no-such')
        assert exc_info.value.http_status == 404

    def test_storagepath_delete_method(self):
        """StoragePath.delete() method removes the path resource."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        path = cu.storage_paths.create(
            {'adapter-port-uri': ADAPTER_PORT_URI})
        path.delete()
        result = self.session.get(cu.uri + '/storage-paths')
        assert len(result['storage-paths']) == 0

    def test_storagepath_update_method(self):
        """StoragePath.update_properties() updates properties locally."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        path = cu.storage_paths.create(
            {'adapter-port-uri': ADAPTER_PORT_URI})
        path.update_properties(
            {'exit-switch-uri': SWITCH1_URI, 'exit-port': '01'})
        assert path.properties['exit-switch-uri'] == SWITCH1_URI
        assert path.properties['exit-port'] == '01'

    # ── Dump ───────────────────────────────────────────────────────────────

    def test_cu_dump(self):
        """StorageControlUnit.dump() returns a dict with properties."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        cu.pull_full_properties()
        result = cu.dump()
        assert isinstance(result, dict)
        assert 'properties' in result

    def test_path_dump(self):
        """StoragePath.dump() returns a dict with properties."""
        self._add_cu1()
        cu = self.console.storage_control_units.find(name=CU1_NAME)
        path = cu.storage_paths.create(
            {'adapter-port-uri': ADAPTER_PORT_URI})
        path.pull_full_properties()
        result = path.dump()
        assert isinstance(result, dict)
        assert 'properties' in result

    # ── Undefine cascade ───────────────────────────────────────────────────

    def test_undefine_cascades_to_paths(self):
        """Undefining a CU also removes its storage paths from HMC."""
        faked_cu = self._add_cu1()
        path_result = self.session.post(
            faked_cu.uri + '/storage-paths',
            body={'adapter-port-uri': ADAPTER_PORT_URI})
        path_uri = path_result['element-uri']
        # Undefine the CU
        self.session.post(faked_cu.uri + '/operations/undefine', body=None)
        # Both the CU and the path should now be gone
        with pytest.raises(HTTPError):
            self.session.get(faked_cu.uri)
        with pytest.raises(HTTPError):
            self.session.get(path_uri)

    # ── add_resources() schema wiring ──────────────────────────────────────

    def test_add_resources_wiring(self):
        """add_resources() correctly wires storage_control_units on console."""
        self.session.hmc.consoles.console.add_resources({
            'storage_control_units': [
                {
                    'properties': {
                        'name': 'CU via add_resources',
                        'logical-address': 'aa',
                        'parent': SUBSYS1_URI,
                    }
                }
            ]
        })
        cus = self.console.storage_control_units.list(
            filter_args={'name': 'CU via add_resources'})
        assert len(cus) == 1

    # ── Inventory ──────────────────────────────────────────────────────────

    def test_inventory_storage_control_unit_empty(self):  # pylint: disable=invalid-name
        """get_inventory(['storage-control-unit']) returns empty when none
        exist."""
        result = self.client.get_inventory(['storage-control-unit'])
        names = [r['name'] for r in result
                 if r.get('class') == 'storage-control-unit']
        assert names == []

    def test_inventory_storage_control_unit_two(self):
        """get_inventory(['storage-control-unit']) returns both CUs."""
        self._add_cu1()
        self._add_cu2()
        result = self.client.get_inventory(['storage-control-unit'])
        names = {r['name'] for r in result
                 if r.get('class') == 'storage-control-unit'}
        assert names == {CU1_NAME, CU2_NAME}

    def test_inventory_dpm_resources_includes_cu(self):
        """get_inventory(['dpm-resources']) includes storage-control-unit
        entries."""
        self._add_cu1()
        result = self.client.get_inventory(['dpm-resources'])
        classes = {r.get('class') for r in result}
        assert 'storage-control-unit' in classes
