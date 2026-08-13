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
Unit tests for the _storage_subsystem module.
"""


import copy
import pytest

from zhmcclient import Client, StorageSubsystem, StorageSubsystemManager, \
    HTTPError, NotFound
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources


# ---------------------------------------------------------------------------
# Object IDs / URIs for faked resources used across the test class
# ---------------------------------------------------------------------------

CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'

SSITE1_OID = 'ss1-oid'
SSITE1_URI = f'/api/storage-sites/{SSITE1_OID}'
SSITE1_NAME = 'Primary Site'

SSITE2_OID = 'ss2-oid'
SSITE2_URI = f'/api/storage-sites/{SSITE2_OID}'
SSITE2_NAME = 'Alternate Site'

SSWITCH1_OID = 'sw1-oid'
SSWITCH1_URI = f'/api/storage-switches/{SSWITCH1_OID}'
SSWITCH1_NAME = 'Storage Switch 11'

SUBSYS1_OID = 'subsys1-oid'
SUBSYS1_NAME = 'DS8886 A'

SUBSYS2_OID = 'subsys2-oid'
SUBSYS2_NAME = 'DS8886 B'


class TestStorageSubsystem:
    """All tests for StorageSubsystem and StorageSubsystemManager classes."""

    def setup_method(self):
        """
        Setup called by pytest before each test method.

        Sets up a faked session with a faked CPC (DPM mode), a faked console,
        two faked storage sites, and one faked storage switch.
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
                {'name': 'dpm-storage-management', 'state': True},
            ],
        })
        assert self.faked_cpc.uri == CPC_URI

        # Add a faked console
        self.faked_console = self.session.hmc.consoles.add({
            'name': 'fake-console-name',
            'description': 'The HMC',
        })
        self.console = self.client.consoles.console

        # Add two faked storage sites
        self.faked_site1 = self.faked_console.storage_sites.add({
            'object-id': SSITE1_OID,
            'name': SSITE1_NAME,
            'description': 'Primary storage site',
            'cpc-uris': [CPC_URI],
            'storage-subsystem-uris': [],
        })
        assert self.faked_site1.uri == SSITE1_URI

        self.faked_site2 = self.faked_console.storage_sites.add({
            'object-id': SSITE2_OID,
            'name': SSITE2_NAME,
            'description': 'Alternate storage site',
            'cpc-uris': [CPC_URI],
            'storage-subsystem-uris': [],
        })
        assert self.faked_site2.uri == SSITE2_URI

        # Add a faked storage switch (used as connection endpoint)
        self.faked_switch1 = self.faked_console.storage_switches.add({
            'object-id': SSWITCH1_OID,
            'name': SSWITCH1_NAME,
            'domain-id': '11',
            'storage-fabric-uri': '/api/storage-fabrics/fabric1-oid',
            'storage-site-uri': SSITE1_URI,
        })
        assert self.faked_switch1.uri == SSWITCH1_URI

    def add_subsystem1(self):
        """Add first faked storage subsystem to site1."""
        faked_ss = self.faked_console.storage_subsystems.add({
            'object-id': SUBSYS1_OID,
            'name': SUBSYS1_NAME,
            'description': 'Storage subsystem DS8886 A',
            'storage-site-uri': SSITE1_URI,
            'parent': '/api/console',
        })
        return faked_ss

    def add_subsystem2(self):
        """Add second faked storage subsystem to site1."""
        faked_ss = self.faked_console.storage_subsystems.add({
            'object-id': SUBSYS2_OID,
            'name': SUBSYS2_NAME,
            'description': 'Storage subsystem DS8886 B',
            'storage-site-uri': SSITE1_URI,
            'parent': '/api/console',
        })
        return faked_ss

    # -----------------------------------------------------------------------
    # Manager attribute tests
    # -----------------------------------------------------------------------

    def test_ssm_initial_attrs(self):
        """Test initial attributes of StorageSubsystemManager."""

        ssm = self.console.storage_subsystems

        assert ssm.resource_class == StorageSubsystem
        assert ssm.class_name == 'storage-subsystem'
        assert ssm.session == self.session
        assert ssm.parent == self.console
        assert ssm.console == self.console

    # -----------------------------------------------------------------------
    # List tests
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            ({'full_properties': False},
             ['object-uri', 'name', 'storage-site-uri']),
            ({'full_properties': True},
             ['object-uri', 'name', 'storage-site-uri', 'description']),
            ({},  # default for full_properties is False
             ['object-uri', 'name', 'storage-site-uri']),
        ]
    )
    @pytest.mark.parametrize(
        "filter_args, exp_names", [
            (None, [SUBSYS1_NAME, SUBSYS2_NAME]),
            ({}, [SUBSYS1_NAME, SUBSYS2_NAME]),
            ({'name': SUBSYS1_NAME}, [SUBSYS1_NAME]),
            ({'name': [SUBSYS1_NAME, SUBSYS2_NAME]},
             [SUBSYS1_NAME, SUBSYS2_NAME]),
        ]
    )
    def test_ssm_list(self, filter_args, exp_names,
                      full_properties_kwargs, prop_names):
        """Test StorageSubsystemManager.list()."""

        faked_ss1 = self.add_subsystem1()
        faked_ss2 = self.add_subsystem2()
        faked_subsystems = [faked_ss1, faked_ss2]
        exp_faked = [s for s in faked_subsystems if s.name in exp_names]

        ssm = self.console.storage_subsystems

        # Execute the code to be tested
        subsystems = ssm.list(filter_args=filter_args,
                              **full_properties_kwargs)

        assert_resources(subsystems, exp_faked, prop_names)

    def test_ssm_list_empty(self):
        """Test listing an empty set of storage subsystems."""

        ssm = self.console.storage_subsystems
        subsystems = ssm.list()
        assert subsystems == []

    def test_ssm_list_two(self):
        """Test listing two storage subsystems."""

        self.add_subsystem1()
        self.add_subsystem2()

        ssm = self.console.storage_subsystems
        subsystems = ssm.list()

        assert len(subsystems) == 2
        names = {ss.name for ss in subsystems}
        assert names == {SUBSYS1_NAME, SUBSYS2_NAME}

    def test_ssm_list_filter_by_site_uri(self):
        """Test filtering subsystems by storage-site-uri."""

        self.add_subsystem1()
        self.add_subsystem2()

        ssm = self.console.storage_subsystems
        subsystems = ssm.list(filter_args={'storage-site-uri': SSITE1_URI})
        assert len(subsystems) == 2

    # -----------------------------------------------------------------------
    # find / findall
    # -----------------------------------------------------------------------

    def test_ssm_resource_object(self):
        """Test that find() returns a valid StorageSubsystem object."""

        self.add_subsystem1()

        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        assert isinstance(ss, StorageSubsystem)
        assert ss.name == SUBSYS1_NAME
        assert isinstance(ss.manager, StorageSubsystemManager)

    def test_ssm_find_not_found(self):
        """Test that find() raises NotFound for unknown name."""

        ssm = self.console.storage_subsystems

        with pytest.raises(NotFound):
            ssm.find(name='nonexistent-subsystem')

    # -----------------------------------------------------------------------
    # repr
    # -----------------------------------------------------------------------

    def test_ss_repr(self):
        """Test repr() of StorageSubsystem objects."""

        faked_ss = self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=faked_ss.name)
        ss.pull_full_properties()

        repr_str = repr(ss)
        assert 'StorageSubsystem' in repr_str

    # -----------------------------------------------------------------------
    # update_properties tests
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "update_props", [
            {},
            {'description': 'Updated description'},
            {'name': SUBSYS2_NAME, 'description': 'Renamed subsystem'},
        ]
    )
    def test_ss_update_properties(self, update_props):
        """Test StorageSubsystem.update_properties()."""

        faked_ss = self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=faked_ss.name)
        ss.pull_full_properties()
        saved_props = copy.deepcopy(ss.properties)

        # Execute the code to be tested
        ss.update_properties(properties=update_props)
        ss.pull_full_properties()

        for prop_name in saved_props:
            if prop_name in update_props:
                exp_value = update_props[prop_name]
            else:
                exp_value = saved_props[prop_name]
            assert ss.properties[prop_name] == exp_value, (
                f"Unexpected value for property {prop_name!r}")

    def test_ss_update_name(self):
        """Test that renaming a subsystem updates the name-URI cache."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        new_name = 'DS8886 A Renamed'
        ss.update_properties({'name': new_name})

        # Old name should be gone from cache
        with pytest.raises(NotFound):
            ssm.find(name=SUBSYS1_NAME)

        # New name should be findable
        renamed_ss = ssm.find(name=new_name)
        assert renamed_ss.name == new_name

    # -----------------------------------------------------------------------
    # move_to_storage_site tests
    # -----------------------------------------------------------------------

    def test_ss_move_to_storage_site(self):
        """Test StorageSubsystem.move_to_storage_site()."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        # Execute the code to be tested
        ss.move_to_storage_site(SSITE2_URI)

        ss.pull_full_properties()
        assert ss.properties['storage-site-uri'] == SSITE2_URI

    def test_ss_move_updates_site_uris(self):
        """Test that move_to_storage_site() updates storage-subsystem-uris."""

        faked_ss = self.add_subsystem1()
        ss_uri = faked_ss.uri

        # Set up old site with the subsystem
        self.faked_site1.update({'storage-subsystem-uris': [ss_uri]})

        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        # Execute the code to be tested
        ss.move_to_storage_site(SSITE2_URI)

        # Verify old site no longer lists this subsystem
        old_site_props = self.faked_site1.properties
        assert ss_uri not in old_site_props.get('storage-subsystem-uris', [])

        # Verify new site now lists this subsystem
        new_site_props = self.faked_site2.properties
        assert ss_uri in new_site_props.get('storage-subsystem-uris', [])

    def test_ss_move_to_site_not_found(self):
        """Test move_to_storage_site() with unknown subsystem raises 404."""

        # Construct a subsystem object with a non-existent URI
        ssm = self.console.storage_subsystems
        fake_ss = StorageSubsystem(
            ssm, '/api/storage-subsystems/nonexistent-oid',
            'Nonexistent',
            {'object-uri': '/api/storage-subsystems/nonexistent-oid'})

        with pytest.raises(HTTPError) as exc_info:
            fake_ss.move_to_storage_site(SSITE2_URI)
        assert exc_info.value.http_status == 404

    def test_ss_move_to_site_conflict(self):
        """Test move_to_storage_site() when already on target site gives 409."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        with pytest.raises(HTTPError) as exc_info:
            ss.move_to_storage_site(SSITE1_URI)  # already on site1
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 450

    def test_ss_move_to_site_unknown_target(self):
        """Test move_to_storage_site() with unknown target site returns 404."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        with pytest.raises(HTTPError) as exc_info:
            ss.move_to_storage_site('/api/storage-sites/nonexistent-site')
        assert exc_info.value.http_status == 404

    # -----------------------------------------------------------------------
    # add_connection_endpoint tests
    # -----------------------------------------------------------------------

    def test_ss_add_connection_endpoint(self):
        """Test StorageSubsystem.add_connection_endpoint()."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        # Execute the code to be tested
        ss.add_connection_endpoint(
            endpoint_uri=SSWITCH1_URI,
            port_id='00',
        )

        ss.pull_full_properties()
        endpoints = ss.properties.get('connection-endpoints', [])
        assert len(endpoints) == 1
        assert endpoints[0]['endpoint-uri'] == SSWITCH1_URI
        assert endpoints[0]['port-id'] == '00'
        assert endpoints[0]['endpoint-class'] == 'storage-switch'

    def test_ss_add_connection_endpoint_no_port(self):
        """Test adding an adapter endpoint (no port-id)."""

        # Add a faked adapter resource under the faked CPC
        faked_adapter = self.faked_cpc.adapters.add({
            'object-id': 'adapter1-oid',
            'name': 'TestAdapter',
            'type': 'fc',
            'status': 'active',
        })
        adapter_uri = faked_adapter.uri

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        # Execute the code to be tested
        ss.add_connection_endpoint(endpoint_uri=adapter_uri)

        ss.pull_full_properties()
        endpoints = ss.properties.get('connection-endpoints', [])
        assert len(endpoints) == 1
        assert endpoints[0]['endpoint-uri'] == adapter_uri
        assert endpoints[0]['endpoint-class'] == 'adapter'
        assert 'port-id' not in endpoints[0]

    def test_ss_add_endpoint_duplicate(self):
        """Test that adding a duplicate endpoint returns 409."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        ss.add_connection_endpoint(endpoint_uri=SSWITCH1_URI, port_id='00')

        with pytest.raises(HTTPError) as exc_info:
            ss.add_connection_endpoint(endpoint_uri=SSWITCH1_URI, port_id='00')
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 443

    def test_ss_add_endpoint_missing_field(self):
        """Test that missing endpoint-uri returns 400."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        # Bypass the Python method and call the session directly to test
        # handler validation (missing required field)
        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                ss.uri + '/operations/add-connection-endpoint',
                body={},  # missing 'endpoint-uri'
            )
        assert exc_info.value.http_status == 400

    def test_ss_add_endpoint_unknown(self):
        """Test that add with unknown endpoint URI returns 404."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        with pytest.raises(HTTPError) as exc_info:
            ss.add_connection_endpoint(
                endpoint_uri='/api/storage-switches/nonexistent-switch',
                port_id='00',
            )
        assert exc_info.value.http_status == 404

    def test_ss_add_endpoint_subsys_not_found(self):
        """Test that add endpoint with unknown subsystem URI returns 404."""

        ssm = self.console.storage_subsystems
        fake_ss = StorageSubsystem(
            ssm, '/api/storage-subsystems/nonexistent-oid',
            'Nonexistent',
            {'object-uri': '/api/storage-subsystems/nonexistent-oid'})

        with pytest.raises(HTTPError) as exc_info:
            fake_ss.add_connection_endpoint(
                endpoint_uri=SSWITCH1_URI, port_id='00')
        assert exc_info.value.http_status == 404

    # -----------------------------------------------------------------------
    # remove_connection_endpoint tests
    # -----------------------------------------------------------------------

    def test_ss_remove_connection_endpoint(self):
        """Test StorageSubsystem.remove_connection_endpoint()."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        # First add an endpoint
        ss.add_connection_endpoint(endpoint_uri=SSWITCH1_URI, port_id='00')
        ss.pull_full_properties()
        assert len(ss.properties['connection-endpoints']) == 1

        # Execute the code to be tested
        ss.remove_connection_endpoint(
            endpoint_uri=SSWITCH1_URI, port_id='00')

        ss.pull_full_properties()
        assert len(ss.properties['connection-endpoints']) == 0

    def test_ss_remove_endpoint_not_found(self):
        """Test that removing a non-existent endpoint returns 409."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        with pytest.raises(HTTPError) as exc_info:
            ss.remove_connection_endpoint(
                endpoint_uri=SSWITCH1_URI, port_id='00')
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 444

    def test_ss_remove_endpoint_subsys_not_found(self):
        """Test that remove endpoint with unknown subsystem URI returns 404."""

        ssm = self.console.storage_subsystems
        fake_ss = StorageSubsystem(
            ssm, '/api/storage-subsystems/nonexistent-oid',
            'Nonexistent',
            {'object-uri': '/api/storage-subsystems/nonexistent-oid'})

        with pytest.raises(HTTPError) as exc_info:
            fake_ss.remove_connection_endpoint(
                endpoint_uri=SSWITCH1_URI, port_id='00')
        assert exc_info.value.http_status == 404

    def test_ss_remove_endpoint_unknown(self):
        """Test that remove with unknown endpoint URI returns 404."""

        self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)

        with pytest.raises(HTTPError) as exc_info:
            ss.remove_connection_endpoint(
                endpoint_uri='/api/storage-switches/nonexistent-switch',
                port_id='00',
            )
        assert exc_info.value.http_status == 404

    # -----------------------------------------------------------------------
    # Default property tests
    # -----------------------------------------------------------------------

    def test_ss_default_properties(self):
        """Test that faked subsystem gets correct default property values."""

        faked_ss = self.faked_console.storage_subsystems.add({
            'name': SUBSYS1_NAME,
            'storage-site-uri': SSITE1_URI,
        })

        assert faked_ss.properties.get('description') == ''
        assert faked_ss.properties.get('connection-endpoints') == []
        assert faked_ss.properties.get('storage-control-unit-uris') == []
        assert faked_ss.properties.get('class') == 'storage-subsystem'
        assert faked_ss.properties.get('name') == SUBSYS1_NAME

    def test_ss_class_property(self):
        """Test that class property is 'storage-subsystem'."""

        faked_ss = self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=faked_ss.name)
        ss.pull_full_properties()

        assert ss.properties.get('class') == 'storage-subsystem'

    # -----------------------------------------------------------------------
    # dump() test
    # -----------------------------------------------------------------------

    def test_ss_dump(self):
        """Test StorageSubsystem.dump()."""

        faked_ss = self.add_subsystem1()
        ssm = self.console.storage_subsystems
        ss = ssm.find(name=faked_ss.name)
        ss.pull_full_properties()

        resource_dict = ss.dump()

        assert isinstance(resource_dict, dict)
        assert 'properties' in resource_dict
        assert resource_dict['properties']['name'] == SUBSYS1_NAME

    # -----------------------------------------------------------------------
    # URI handler tests — direct session calls
    # -----------------------------------------------------------------------

    def test_get_subsystem_properties(self):
        """Test GET /api/storage-subsystems/{id}."""

        faked_ss = self.add_subsystem1()
        ss_uri = faked_ss.uri

        result = self.session.get(ss_uri)

        assert result['name'] == SUBSYS1_NAME
        assert result['class'] == 'storage-subsystem'

    def test_get_subsystem_properties_not_found(self):
        """Test GET /api/storage-subsystems/{id} for unknown ID raises 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.get('/api/storage-subsystems/nonexistent-id')
        assert exc_info.value.http_status == 404

    def test_list_subsystems_global(self):
        """Test GET /api/storage-subsystems returns all subsystems."""

        self.add_subsystem1()
        self.add_subsystem2()

        result = self.session.get('/api/storage-subsystems')

        assert 'storage-subsystems' in result
        names = {ss['name'] for ss in result['storage-subsystems']}
        assert names == {SUBSYS1_NAME, SUBSYS2_NAME}

    def test_list_subsystems_global_filter_name(self):
        """Test GET /api/storage-subsystems?name=... filtering."""

        self.add_subsystem1()
        self.add_subsystem2()

        result = self.session.get(
            f'/api/storage-subsystems?name={SUBSYS1_NAME}')

        assert 'storage-subsystems' in result
        names = [ss['name'] for ss in result['storage-subsystems']]
        assert SUBSYS1_NAME in names
        assert SUBSYS2_NAME not in names

    def test_update_subsystem_properties_handler(self):
        """Test POST /api/storage-subsystems/{id} (Update Properties)."""

        faked_ss = self.add_subsystem1()
        ss_uri = faked_ss.uri

        self.session.post(ss_uri, body={'description': 'Updated'})

        result = self.session.get(ss_uri)
        assert result['description'] == 'Updated'

    def test_list_subsystems_by_site(self):
        """Test GET /api/storage-sites/{id}/storage-subsystems."""

        faked_ss1 = self.add_subsystem1()
        faked_ss2 = self.add_subsystem2()

        result = self.session.get(
            f'/api/storage-sites/{SSITE1_OID}/storage-subsystems')

        assert 'storage-subsystems' in result
        uris = {ss['object-uri'] for ss in result['storage-subsystems']}
        assert faked_ss1.uri in uris
        assert faked_ss2.uri in uris

    def test_list_subsystems_by_site_not_found(self):
        """Test GET /api/storage-sites/{id}/storage-subsystems for bad site."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.get(
                '/api/storage-sites/nonexistent-site/storage-subsystems')
        assert exc_info.value.http_status == 404

    def test_move_site_handler(self):
        """Test POST …/operations/move-storage-site."""

        faked_ss = self.add_subsystem1()
        ss_oid = faked_ss.oid

        self.session.post(
            f'/api/storage-subsystems/{ss_oid}/operations/move-storage-site',
            body={'storage-site-uri': SSITE2_URI},
        )

        result = self.session.get(faked_ss.uri)
        assert result['storage-site-uri'] == SSITE2_URI

    def test_move_site_handler_not_found(self):
        """Test that move-storage-site with bad subsystem ID returns 404."""

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                '/api/storage-subsystems/nonexistent-id/operations/'
                'move-storage-site',
                body={'storage-site-uri': SSITE2_URI},
            )
        assert exc_info.value.http_status == 404

    def test_add_endpoint_handler(self):
        """Test POST …/operations/add-connection-endpoint."""

        faked_ss = self.add_subsystem1()
        ss_oid = faked_ss.oid

        self.session.post(
            f'/api/storage-subsystems/{ss_oid}/operations/'
            'add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '01'},
        )

        result = self.session.get(faked_ss.uri)
        endpoints = result.get('connection-endpoints', [])
        assert len(endpoints) == 1
        assert endpoints[0]['endpoint-uri'] == SSWITCH1_URI

    def test_remove_endpoint_handler(self):
        """Test POST …/operations/remove-connection-endpoint."""

        faked_ss = self.add_subsystem1()
        ss_oid = faked_ss.oid

        # First add an endpoint
        self.session.post(
            f'/api/storage-subsystems/{ss_oid}/operations/'
            'add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '01'},
        )

        # Then remove it
        self.session.post(
            f'/api/storage-subsystems/{ss_oid}/operations/'
            'remove-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '01'},
        )

        result = self.session.get(faked_ss.uri)
        endpoints = result.get('connection-endpoints', [])
        assert len(endpoints) == 0

    def test_add_endpoint_handler_missing_field(self):
        """Test add-connection-endpoint missing endpoint-uri returns 400."""

        faked_ss = self.add_subsystem1()
        ss_oid = faked_ss.oid

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                f'/api/storage-subsystems/{ss_oid}/operations/'
                'add-connection-endpoint',
                body={},
            )
        assert exc_info.value.http_status == 400

    # -----------------------------------------------------------------------
    # Dependency regression tests
    # -----------------------------------------------------------------------

    # --- Gap 1 + 2: storage-site ↔ storage-subsystem bi-directional linkage --

    def test_ssm_add_registers_site_uris(self):
        """Adding a subsystem populates the site's storage-subsystem-uris."""

        faked_ss = self.add_subsystem1()

        site_props = self.faked_site1.properties
        assert faked_ss.uri in site_props.get('storage-subsystem-uris', []), (
            "subsystem URI not registered in parent site's "
            "storage-subsystem-uris after add()")

    def test_site_default_subsystem_uris(self):
        """FakedStorageSite.add() initialises storage-subsystem-uris to []."""

        faked_site = self.faked_console.storage_sites.add({
            'object-id': 'new-site-oid',
            'name': 'New Site',
        })

        assert 'storage-subsystem-uris' in faked_site.properties, (
            "storage-subsystem-uris not defaulted on FakedStorageSite")
        assert faked_site.properties['storage-subsystem-uris'] == []

    def test_ssm_add_two_both_in_site_uris(self):
        """Two subsystems on the same site both appear in subsystem-uris."""

        faked_ss1 = self.add_subsystem1()
        faked_ss2 = self.add_subsystem2()

        site_uris = self.faked_site1.properties.get(
            'storage-subsystem-uris', [])
        assert faked_ss1.uri in site_uris
        assert faked_ss2.uri in site_uris

    def test_ss_move_site_updates_both_sites(self):
        """move_to_storage_site() removes URI from old site, adds to new."""

        faked_ss = self.add_subsystem1()
        ss_uri = faked_ss.uri

        # Confirm it starts registered in site1
        assert ss_uri in self.faked_site1.properties.get(
            'storage-subsystem-uris', [])

        ssm = self.console.storage_subsystems
        ss = ssm.find(name=SUBSYS1_NAME)
        ss.move_to_storage_site(SSITE2_URI)

        # After move: must be gone from site1, present in site2
        assert ss_uri not in self.faked_site1.properties.get(
            'storage-subsystem-uris', [])
        assert ss_uri in self.faked_site2.properties.get(
            'storage-subsystem-uris', [])

    def test_ssm_add_uri_resolvable_from_site(self):
        """The site's storage-subsystem-uris resolves back to the subsystem."""

        faked_ss = self.add_subsystem1()

        site = self.session.hmc.consoles.console.storage_sites.lookup_by_oid(
            SSITE1_OID)
        site_ss_uris = site.properties.get('storage-subsystem-uris', [])
        assert faked_ss.uri in site_ss_uris

        # Verify the URI resolves to the subsystem
        resolved = self.session.hmc.lookup_by_uri(faked_ss.uri)
        assert resolved.properties['name'] == SUBSYS1_NAME

    # --- Gap 3: undefining a switch clears subsystem connection-endpoints ---

    def test_sw_undefine_clears_endpoints(self):
        """Undefining a switch clears it from subsystem connection-endpoints."""

        faked_ss = self.add_subsystem1()
        ss_oid = faked_ss.oid

        # Add the switch as a connection endpoint on the subsystem
        self.session.post(
            f'/api/storage-subsystems/{ss_oid}/operations/'
            'add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '00'},
        )

        # Confirm endpoint is present
        result = self.session.get(faked_ss.uri)
        assert len(result['connection-endpoints']) == 1

        # Now undefine the storage switch
        self.session.post(
            f'{SSWITCH1_URI}/operations/undefine',
            body=None,
        )

        # The endpoint must have been removed from the subsystem
        result = self.session.get(faked_ss.uri)
        assert len(result['connection-endpoints']) == 0, (
            "connection-endpoints not cleared after storage switch undefine")

    def test_sw_undefine_clears_all_endpoints(self):
        """Undefine a switch clears endpoints on all referencing subsystems."""

        faked_ss1 = self.add_subsystem1()
        faked_ss2 = self.add_subsystem2()

        for faked_ss in (faked_ss1, faked_ss2):
            self.session.post(
                f'{faked_ss.uri}/operations/add-connection-endpoint',
                body={'endpoint-uri': SSWITCH1_URI, 'port-id': '00'},
            )

        # Undefine the switch
        self.session.post(f'{SSWITCH1_URI}/operations/undefine', body=None)

        for faked_ss in (faked_ss1, faked_ss2):
            result = self.session.get(faked_ss.uri)
            assert result['connection-endpoints'] == [], (
                f"connection-endpoints not cleared on {faked_ss.uri} "
                "after switch undefine")

    def test_sw_undefine_leaves_other_endpoints(self):
        """Undefining a switch only removes that switch's endpoints."""

        # Add a second switch to use as an unaffected endpoint
        faked_switch2 = self.faked_console.storage_switches.add({
            'object-id': 'sw2-oid',
            'name': 'Storage Switch 22',
            'domain-id': '22',
            'storage-fabric-uri': '/api/storage-fabrics/fabric1-oid',
            'storage-site-uri': SSITE1_URI,
        })

        faked_ss = self.add_subsystem1()

        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '00'},
        )
        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': faked_switch2.uri, 'port-id': '01'},
        )

        # Undefine only switch1
        self.session.post(f'{SSWITCH1_URI}/operations/undefine', body=None)

        result = self.session.get(faked_ss.uri)
        endpoints = result['connection-endpoints']
        assert len(endpoints) == 1, (
            "Expected exactly 1 endpoint (switch2) to remain")
        assert endpoints[0]['endpoint-uri'] == faked_switch2.uri

    # --- Gap 4: port-id required for switch endpoints (add) ---

    def test_ss_add_sw_endpoint_no_port_id(self):
        """Adding a switch endpoint without port-id must return 400 reason 5."""

        faked_ss = self.add_subsystem1()

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                f'{faked_ss.uri}/operations/add-connection-endpoint',
                body={'endpoint-uri': SSWITCH1_URI},  # port-id missing
            )
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 5

    def test_ss_add_adapter_ep_with_port_id(self):
        """Adding an adapter endpoint WITH port-id must return 400 reason 15."""

        faked_adapter = self.faked_cpc.adapters.add({
            'object-id': 'adapter2-oid',
            'name': 'TestAdapter2',
            'type': 'fc',
            'status': 'active',
        })
        faked_ss = self.add_subsystem1()

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                f'{faked_ss.uri}/operations/add-connection-endpoint',
                body={
                    'endpoint-uri': faked_adapter.uri,
                    'port-id': '00',  # prohibited for adapters
                },
            )
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 15

    def test_ss_add_adapter_endpoint_no_port_id(self):
        """Adding an adapter endpoint without port-id succeeds."""

        faked_adapter = self.faked_cpc.adapters.add({
            'object-id': 'adapter3-oid',
            'name': 'TestAdapter3',
            'type': 'fc',
            'status': 'active',
        })
        faked_ss = self.add_subsystem1()

        # Must succeed with no exception
        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': faked_adapter.uri},
        )

        result = self.session.get(faked_ss.uri)
        endpoints = result['connection-endpoints']
        assert len(endpoints) == 1
        assert endpoints[0]['endpoint-class'] == 'adapter'
        assert 'port-id' not in endpoints[0]

    def test_ss_add_sw_endpoint_with_port_id(self):
        """Adding a switch endpoint with port-id succeeds."""

        faked_ss = self.add_subsystem1()

        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '0a'},
        )

        result = self.session.get(faked_ss.uri)
        endpoints = result['connection-endpoints']
        assert len(endpoints) == 1
        assert endpoints[0]['port-id'] == '0a'
        assert endpoints[0]['endpoint-class'] == 'storage-switch'

    # --- Gap 5: port-id required for switch endpoints (remove) ---

    def test_ss_remove_sw_endpoint_no_port_id(self):
        """Removing a switch endpoint without port-id returns 400 reason 5."""

        faked_ss = self.add_subsystem1()

        # First add a valid endpoint so we have something to remove
        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '00'},
        )

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                f'{faked_ss.uri}/operations/remove-connection-endpoint',
                body={'endpoint-uri': SSWITCH1_URI},  # port-id missing
            )
        assert exc_info.value.http_status == 400
        assert exc_info.value.reason == 5

    def test_ss_remove_sw_endpoint_wrong_port_id(self):
        """Removing a switch endpoint with wrong port-id returns 409/444."""

        faked_ss = self.add_subsystem1()

        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '00'},
        )

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                f'{faked_ss.uri}/operations/remove-connection-endpoint',
                body={'endpoint-uri': SSWITCH1_URI, 'port-id': 'ff'},
            )
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 444

    def test_ss_remove_adapter_ep_no_port_id(self):
        """Removing an adapter endpoint without port-id succeeds."""

        faked_adapter = self.faked_cpc.adapters.add({
            'object-id': 'adapter4-oid',
            'name': 'TestAdapter4',
            'type': 'fc',
            'status': 'active',
        })
        faked_ss = self.add_subsystem1()

        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': faked_adapter.uri},
        )

        # Remove without port-id — must succeed for adapters
        self.session.post(
            f'{faked_ss.uri}/operations/remove-connection-endpoint',
            body={'endpoint-uri': faked_adapter.uri},
        )

        result = self.session.get(faked_ss.uri)
        assert result['connection-endpoints'] == []

    # --- Duplicate-endpoint check uses port-id correctly ---

    def test_ss_add_sw_endpoint_diff_ports_ok(self):
        """Adding the same switch with two different port-ids is allowed."""

        faked_ss = self.add_subsystem1()

        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '00'},
        )
        # Same switch, different port — should succeed
        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '01'},
        )

        result = self.session.get(faked_ss.uri)
        assert len(result['connection-endpoints']) == 2

    def test_ss_add_sw_ep_dup_port_conflict(self):
        """Adding exactly the same switch+port twice returns 409 reason 443."""

        faked_ss = self.add_subsystem1()

        self.session.post(
            f'{faked_ss.uri}/operations/add-connection-endpoint',
            body={'endpoint-uri': SSWITCH1_URI, 'port-id': '00'},
        )

        with pytest.raises(HTTPError) as exc_info:
            self.session.post(
                f'{faked_ss.uri}/operations/add-connection-endpoint',
                body={'endpoint-uri': SSWITCH1_URI, 'port-id': '00'},
            )
        assert exc_info.value.http_status == 409
        assert exc_info.value.reason == 443

    # ── Inventory ──────────────────────────────────────────────────────────

    def test_inventory_storage_subsystem_empty(self):
        """get_inventory(['storage-subsystem']) returns empty when none
        exist."""
        result = self.client.get_inventory(['storage-subsystem'])
        names = [r['name'] for r in result
                 if r.get('class') == 'storage-subsystem']
        assert names == []

    def test_inventory_storage_subsystem_two(self):
        """get_inventory(['storage-subsystem']) returns both subsystems."""
        self.add_subsystem1()
        self.add_subsystem2()
        result = self.client.get_inventory(['storage-subsystem'])
        names = {r['name'] for r in result
                 if r.get('class') == 'storage-subsystem'}
        assert names == {SUBSYS1_NAME, SUBSYS2_NAME}

    def test_inventory_dpm_resources_includes_subsystem(self):  # pylint: disable=invalid-name
        """get_inventory(['dpm-resources']) includes storage-subsystem
        entries."""
        self.add_subsystem1()
        result = self.client.get_inventory(['dpm-resources'])
        classes = {r.get('class') for r in result}
        assert 'storage-subsystem' in classes
