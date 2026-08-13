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
Unit tests for the StoragePath and StoragePathManager classes using the
faked HMC.
"""

import pytest

import zhmcclient
from zhmcclient.mock import FakedSession
from zhmcclient import Client, HTTPError

# ── Fixture constants ─────────────────────────────────────────────────────────

CPC_OID = 'fake-cpc1-oid'

SSITE1_OID = 'site1-oid'
SSITE1_URI = f'/api/storage-sites/{SSITE1_OID}'

SUBSYS1_OID = 'subsys1-oid'
SUBSYS1_URI = f'/api/storage-subsystems/{SUBSYS1_OID}'
SUBSYS1_NAME = 'DS8886 A'

ADAPTER_OID = 'adap1-oid'
ADAPTER_PORT_OID = 'port1-oid'
ADAPTER_PORT_URI = (
    f'/api/adapters/{ADAPTER_OID}/storage-ports/{ADAPTER_PORT_OID}')

ADAPTER2_OID = 'adap2-oid'
ADAPTER2_PORT_OID = 'port2-oid'
ADAPTER2_PORT_URI = (
    f'/api/adapters/{ADAPTER2_OID}/storage-ports/{ADAPTER2_PORT_OID}')

SWITCH1_OID = 'sw1-oid'
SWITCH1_URI = f'/api/storage-switches/{SWITCH1_OID}'

CU1_OID = 'cu1-oid'
CU1_NAME = 'Control unit 50'
CU1_ADDR = '50'


class TestStoragePath:
    """Unit tests for StoragePath and StoragePathManager."""

    def setup_method(self):
        # pylint: disable=attribute-defined-outside-init
        """Set up faked session, HMC resources, and a single control unit."""
        self.session = FakedSession('fake-host', 'fake-hmc', '2.16.0', '4.10')
        self.client = Client(self.session)

        # CPC
        self.session.hmc.cpcs.add({
            'object-id': CPC_OID,
            'parent': None,
            'class': 'cpc',
            'name': 'CPC1',
            'dpm-enabled': True,
        })

        # Console
        self.faked_console = self.session.hmc.consoles.add({'name': 'HMC1'})
        self.console = self.client.consoles.console

        # Storage infrastructure
        self.faked_console.storage_sites.add({
            'object-id': SSITE1_OID,
            'name': 'Primary Site',
        })
        self.faked_console.storage_subsystems.add({
            'object-id': SUBSYS1_OID,
            'name': SUBSYS1_NAME,
            'storage-site-uri': SSITE1_URI,
        })

        # Primary adapter with one storage port
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

        # Second adapter/port for multi-path tests
        faked_adapter2 = faked_cpc.adapters.add({
            'object-id': ADAPTER2_OID,
            'name': 'Adapter2',
            'adapter-family': 'ficon',
            'type': 'fcp',
            'storage-port-uris': [],
        })
        faked_adapter2.ports.add({
            'element-id': ADAPTER2_PORT_OID,
            'name': 'Port0',
        })

        # Storage switch
        self.faked_console.storage_switches.add({
            'object-id': SWITCH1_OID,
            'name': 'SW1',
            'domain-id': '1',
            'storage-site-uri': SSITE1_URI,
            'storage-fabric-uri': '/api/storage-fabrics/fab1',
        })

        # Control unit
        self.faked_cu = self.faked_console.storage_control_units.add({
            'object-id': CU1_OID,
            'name': CU1_NAME,
            'logical-address': CU1_ADDR,
            'parent': SUBSYS1_URI,
        })

        self.cu = self.console.storage_control_units.find(name=CU1_NAME)

    # ── StoragePathManager attributes ─────────────────────────────────────────

    def test_manager_type(self):
        """storage_paths attribute returns a StoragePathManager."""
        assert isinstance(self.cu.storage_paths,
                          zhmcclient.StoragePathManager)

    def test_manager_storage_control_unit(self):
        """StoragePathManager.storage_control_unit points to the parent CU."""
        assert self.cu.storage_paths.storage_control_unit is self.cu

    def test_manager_session(self):
        """StoragePathManager.session is the same session used by the client."""
        assert self.cu.storage_paths.session is self.session

    # ── list() ────────────────────────────────────────────────────────────────

    def test_list_empty(self):
        """list() returns [] when no paths exist."""
        assert self.cu.storage_paths.list() == []

    def test_list_one(self):
        """list() returns one StoragePath after creating one."""
        self.faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        result = self.cu.storage_paths.list()
        assert len(result) == 1
        assert isinstance(result[0], zhmcclient.StoragePath)

    def test_list_two(self):
        """list() returns both paths after adding two."""
        self.faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        self.faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER2_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        result = self.cu.storage_paths.list()
        assert len(result) == 2

    def test_list_full_properties(self):
        """list(full_properties=True) returns paths with all properties."""
        self.faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        result = self.cu.storage_paths.list(full_properties=True)
        assert len(result) == 1
        assert 'adapter-port-uri' in result[0].properties

    # ── create() ──────────────────────────────────────────────────────────────

    def test_create_returns_storage_path(self):
        """create() returns a StoragePath object."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        assert isinstance(path, zhmcclient.StoragePath)

    def test_create_uri_is_under_cu(self):
        """Created path URI is prefixed with the CU URI."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        assert path.uri.startswith(self.cu.uri + '/storage-paths/')

    def test_create_registers_in_cu_path_uris(self):
        """create() causes path URI to appear in parent CU's
        storage-path-uris."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        self.cu.pull_full_properties()
        assert path.uri in self.cu.properties['storage-path-uris']

    def test_create_with_switch(self):
        """create() with exit-switch-uri and exit-port succeeds."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': SWITCH1_URI,
            'exit-port': '00',
        })
        assert isinstance(path, zhmcclient.StoragePath)

    def test_create_two_paths_different_ports(self):
        """Two paths with different adapter-port-uris can coexist."""
        p1 = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        p2 = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER2_PORT_URI,
        })
        assert p1.uri != p2.uri
        assert len(self.cu.storage_paths.list()) == 2

    def test_create_missing_required_field_raises(self):  # pylint: disable=invalid-name
        """create() without adapter-port-uri raises HTTPError 400."""
        with pytest.raises(HTTPError) as exc_info:
            self.cu.storage_paths.create({'exit-port': '00'})
        assert exc_info.value.http_status == 400

    def test_create_unknown_adapter_port_raises(self):
        """create() with unknown adapter-port-uri raises HTTPError 404."""
        with pytest.raises(HTTPError) as exc_info:
            self.cu.storage_paths.create({
                'adapter-port-uri': '/api/adapters/no/storage-ports/x',
            })
        assert exc_info.value.http_status == 404
        assert exc_info.value.reason == 2

    def test_create_switch_without_port_raises(self):
        """exit-switch-uri without exit-port raises HTTPError 400/442."""
        with pytest.raises(HTTPError) as exc_info:
            self.cu.storage_paths.create({
                'adapter-port-uri': ADAPTER_PORT_URI,
                'exit-switch-uri': SWITCH1_URI,
            })
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 442

    def test_create_port_without_switch_raises(self):
        """exit-port without exit-switch-uri raises HTTPError 400/442."""
        with pytest.raises(HTTPError) as exc_info:
            self.cu.storage_paths.create({
                'adapter-port-uri': ADAPTER_PORT_URI,
                'exit-port': '00',
            })
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 442

    def test_create_duplicate_path_raises(self):
        """Creating an identical path twice raises HTTPError 400/8."""
        self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        with pytest.raises(HTTPError) as exc_info:
            self.cu.storage_paths.create({
                'adapter-port-uri': ADAPTER_PORT_URI,
            })
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 8

    def test_create_max_paths_exceeded_raises(self):
        """Creating a 9th path raises HTTPError 409/486."""
        for i in range(8):
            self.faked_cu.storage_paths.add({
                'adapter-port-uri': ADAPTER_PORT_URI,
                'exit-switch-uri': None,
                'exit-port': None,
                '_idx': i,
            })
        with pytest.raises(HTTPError) as exc_info:
            self.cu.storage_paths.create({
                'adapter-port-uri': ADAPTER_PORT_URI,
            })
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 486

    # ── StoragePathManager.delete() ───────────────────────────────────────────

    def test_manager_delete(self):
        """StoragePathManager.delete() removes the path by element-id."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        element_id = path.uri.split('/')[-1]
        self.cu.storage_paths.delete(element_id)
        assert self.cu.storage_paths.list() == []

    def test_manager_delete_removes_from_path_uris(self):  # pylint: disable=invalid-name
        """StoragePathManager.delete() deregisters URI from parent CU."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        element_id = path.uri.split('/')[-1]
        self.cu.storage_paths.delete(element_id)
        self.cu.pull_full_properties()
        assert path.uri not in self.cu.properties['storage-path-uris']

    def test_manager_delete_not_found_raises(self):
        """StoragePathManager.delete() with non-existent id raises
        HTTPError 404."""
        with pytest.raises(HTTPError) as exc_info:
            self.cu.storage_paths.delete('no-such-element-id')
        assert exc_info.value.http_status == 404

    # ── StoragePath.update_properties() ──────────────────────────────────────

    def test_update_properties(self):
        """update_properties() changes properties on the HMC and locally."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        path.update_properties({
            'exit-switch-uri': SWITCH1_URI,
            'exit-port': '01',
        })
        assert path.properties['exit-switch-uri'] == SWITCH1_URI
        assert path.properties['exit-port'] == '01'
        # Verify persisted on the HMC
        path.pull_full_properties()
        assert path.properties['exit-switch-uri'] == SWITCH1_URI
        assert path.properties['exit-port'] == '01'

    def test_update_properties_adapter_port_uri(self):
        """update_properties() can change adapter-port-uri."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        path.update_properties({'adapter-port-uri': ADAPTER2_PORT_URI})
        assert path.properties['adapter-port-uri'] == ADAPTER2_PORT_URI

    # ── StoragePath.delete() ──────────────────────────────────────────────────

    def test_delete(self):
        """StoragePath.delete() removes the resource and it is no longer
        listed."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        path.delete()
        assert self.cu.storage_paths.list() == []

    def test_delete_removes_from_cu_path_uris(self):
        """StoragePath.delete() deregisters path URI from parent CU."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        path_uri = path.uri
        path.delete()
        self.cu.pull_full_properties()
        assert path_uri not in self.cu.properties['storage-path-uris']

    def test_delete_not_found_raises(self):
        """DELETE on a non-existent path URI raises HTTPError 404."""
        with pytest.raises(HTTPError) as exc_info:
            self.session.delete(self.cu.uri + '/storage-paths/no-such')
        assert exc_info.value.http_status == 404

    # ── StoragePath.pull_full_properties() ───────────────────────────────────

    def test_pull_full_properties(self):
        """pull_full_properties() populates all known path properties."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        path.pull_full_properties()
        assert 'adapter-port-uri' in path.properties
        assert 'element-uri' in path.properties
        assert 'class' in path.properties

    def test_class_property_value(self):
        """Path 'class' property is 'storage-path'."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        path.pull_full_properties()
        assert path.properties['class'] == 'storage-path'

    # ── StoragePath.dump() ───────────────────────────────────────────────────

    def test_dump_returns_dict_with_properties(self):
        """dump() returns a dict containing a 'properties' key."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        path.pull_full_properties()
        result = path.dump()
        assert isinstance(result, dict)
        assert 'properties' in result

    def test_dump_properties_contain_adapter_port_uri(self):  # pylint: disable=invalid-name
        """dump() properties include adapter-port-uri."""
        path = self.cu.storage_paths.create({
            'adapter-port-uri': ADAPTER_PORT_URI,
        })
        path.pull_full_properties()
        result = path.dump()
        assert result['properties'].get('adapter-port-uri') == ADAPTER_PORT_URI

    # ── Faked-layer direct add/remove ─────────────────────────────────────────

    def test_faked_add_registers_uri_in_cu(self):
        """FakedStoragePathManager.add() registers path URI in parent CU."""
        faked_path = self.faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        path_uris = self.faked_cu.properties.get('storage-path-uris', [])
        assert faked_path.uri in path_uris

    def test_faked_remove_deregisters_uri_from_cu(self):  # pylint: disable=invalid-name
        """FakedStoragePathManager.remove() deregisters path URI from
        parent CU."""
        faked_path = self.faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        path_uri = faked_path.uri
        self.faked_cu.storage_paths.remove(faked_path.oid)
        path_uris = self.faked_cu.properties.get('storage-path-uris', [])
        assert path_uri not in path_uris

    # ── GET handler ──────────────────────────────────────────────────────────

    def test_get_path_properties_via_session(self):
        """GET on a single path URI returns its properties."""
        result = self.session.post(
            self.faked_cu.uri + '/storage-paths',
            body={'adapter-port-uri': ADAPTER_PORT_URI})
        path_uri = result['element-uri']
        props = self.session.get(path_uri)
        assert props['adapter-port-uri'] == ADAPTER_PORT_URI

    def test_list_handler_returns_element_uris(self):
        """GET /storage-paths returns list with element-uri entries."""
        self.faked_cu.storage_paths.add({
            'adapter-port-uri': ADAPTER_PORT_URI,
            'exit-switch-uri': None,
            'exit-port': None,
        })
        result = self.session.get(self.faked_cu.uri + '/storage-paths')
        assert 'storage-paths' in result
        assert len(result['storage-paths']) == 1
        assert 'element-uri' in result['storage-paths'][0]

    def test_list_handler_cu_not_found_raises(self):
        """GET /storage-paths for non-existent CU raises HTTPError 404."""
        with pytest.raises(HTTPError) as exc_info:
            self.session.get(
                '/api/storage-control-units/no-such/storage-paths')
        assert exc_info.value.http_status == 404

    # ── add_resources() schema wiring ─────────────────────────────────────────

    def test_add_resources_with_storage_paths(self):
        """add_resources() accepts storage_paths as children of a CU."""
        self.faked_console.add_resources({
            'storage_control_units': [
                {
                    'properties': {
                        'name': 'CU via add_resources',
                        'logical-address': 'aa',
                        'parent': SUBSYS1_URI,
                    },
                    'storage_paths': [
                        {
                            'properties': {
                                'adapter-port-uri': ADAPTER_PORT_URI,
                                'exit-switch-uri': None,
                                'exit-port': None,
                            }
                        }
                    ],
                }
            ]
        })
        cu = self.console.storage_control_units.find(
            name='CU via add_resources')
        paths = cu.storage_paths.list()
        assert len(paths) == 1

    def test_add_resources_path_registered_in_cu(self):
        """add_resources() wired path URI appears in CU's storage-path-uris."""
        self.faked_console.add_resources({
            'storage_control_units': [
                {
                    'properties': {
                        'name': 'CU wiring test',
                        'logical-address': 'bb',
                        'parent': SUBSYS1_URI,
                    },
                    'storage_paths': [
                        {
                            'properties': {
                                'adapter-port-uri': ADAPTER_PORT_URI,
                                'exit-switch-uri': None,
                                'exit-port': None,
                            }
                        }
                    ],
                }
            ]
        })
        cu = self.console.storage_control_units.find(name='CU wiring test')
        cu.pull_full_properties()
        path_uris = cu.properties.get('storage-path-uris', [])
        assert len(path_uris) == 1
        paths = cu.storage_paths.list(full_properties=True)
        assert paths[0].uri == path_uris[0]
