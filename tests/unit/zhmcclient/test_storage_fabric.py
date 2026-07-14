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
Unit tests for _storage_fabric module.
"""


import re
import copy
import pytest

from zhmcclient import Client, StorageFabric, StorageFabricManager, \
    HTTPError, NotFound
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked resources:
CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'
SFABRIC1_OID = 'sf1-oid'
SFABRIC1_NAME = 'Fabric A'
SFABRIC2_OID = 'sf2-oid'
SFABRIC2_NAME = 'Fabric B'


class TestStorageFabric:
    """All tests for the StorageFabric and StorageFabricManager classes."""

    def setup_method(self):
        """
        Setup called by pytest before each test method.

        Creates a faked session with a faked CPC (DPM mode) and a faked
        console.
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
            'description': 'CPC #1 (DPM mode, storage mgmt feature enabled)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
            'available-features-list': [
                dict(name='dpm-storage-management', state=True),
            ],
        })
        assert self.faked_cpc.uri == CPC_URI
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

        # Add a faked console
        self.faked_console = self.session.hmc.consoles.add({
            # object-id is set up automatically
            # object-uri is set up automatically
            # parent will be automatically set
            # class will be automatically set
            'name': 'fake-console-name',
            'description': 'The HMC',
        })
        self.console = self.client.consoles.console

    def add_fabric1(self):
        """Add storage fabric 1 to the faked console."""
        return self.faked_console.storage_fabrics.add({
            'object-id': SFABRIC1_OID,
            # object-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'cpc-uri': CPC_URI,
            'name': SFABRIC1_NAME,
            'description': 'Storage Fabric #1',
            'high-integrity': False,
        })

    def add_fabric2(self):
        """Add storage fabric 2 to the faked console."""
        return self.faked_console.storage_fabrics.add({
            'object-id': SFABRIC2_OID,
            # object-uri will be automatically set
            # parent will be automatically set
            # class will be automatically set
            'cpc-uri': CPC_URI,
            'name': SFABRIC2_NAME,
            'description': 'Storage Fabric #2',
            'high-integrity': True,
        })

    # -------------------------------------------------------------------------
    # StorageFabricManager tests
    # -------------------------------------------------------------------------

    def test_sfm_initial_attrs(self):
        """Test initial attributes of StorageFabricManager."""

        fabric_mgr = self.console.storage_fabrics

        assert isinstance(fabric_mgr, StorageFabricManager)
        assert fabric_mgr.resource_class == StorageFabric
        assert fabric_mgr.session == self.session
        assert fabric_mgr.parent == self.console
        assert fabric_mgr.console == self.console

    testcases_sfm_list_full_properties = (
        "full_properties_kwargs, prop_names", [
            ({},
             ['object-uri', 'cpc-uri', 'name']),
            (dict(full_properties=False),
             ['object-uri', 'cpc-uri', 'name']),
        ]
    )

    @pytest.mark.parametrize(*testcases_sfm_list_full_properties)
    def test_sfm_list_full_properties(self, full_properties_kwargs, prop_names):
        """Test StorageFabricManager.list() with full_properties."""

        faked_fabric1 = self.add_fabric1()
        faked_fabric2 = self.add_fabric2()
        exp_faked_fabrics = [faked_fabric1, faked_fabric2]

        fabric_mgr = self.console.storage_fabrics

        # Execute the code to be tested
        fabrics = fabric_mgr.list(**full_properties_kwargs)

        assert_resources(fabrics, exp_faked_fabrics, prop_names)

    testcases_sfm_list_filter_args = (
        "filter_args, exp_names", [
            ({'object-id': SFABRIC1_OID},
             [SFABRIC1_NAME]),
            ({'object-id': SFABRIC2_OID},
             [SFABRIC2_NAME]),
            ({'object-id': [SFABRIC1_OID, SFABRIC2_OID]},
             [SFABRIC1_NAME, SFABRIC2_NAME]),
            ({'object-id': [SFABRIC1_OID, SFABRIC1_OID]},
             [SFABRIC1_NAME]),
            ({'object-id': SFABRIC1_OID + 'foo'},
             []),
            ({'object-id': [SFABRIC1_OID, SFABRIC2_OID + 'foo']},
             [SFABRIC1_NAME]),
            ({'object-id': [SFABRIC2_OID + 'foo', SFABRIC1_OID]},
             [SFABRIC1_NAME]),
            ({'name': SFABRIC1_NAME},
             [SFABRIC1_NAME]),
            ({'name': SFABRIC2_NAME},
             [SFABRIC2_NAME]),
            ({'name': [SFABRIC1_NAME, SFABRIC2_NAME]},
             [SFABRIC1_NAME, SFABRIC2_NAME]),
            ({'name': SFABRIC1_NAME + 'foo'},
             []),
            ({'name': [SFABRIC1_NAME, SFABRIC2_NAME + 'foo']},
             [SFABRIC1_NAME]),
            ({'name': 'Fabric .*'},
             [SFABRIC1_NAME, SFABRIC2_NAME]),
            ({'name': 'Fabric A'},
             [SFABRIC1_NAME]),
            ({'name': SFABRIC1_NAME,
              'object-id': SFABRIC1_OID},
             [SFABRIC1_NAME]),
            ({'name': SFABRIC1_NAME,
              'object-id': SFABRIC1_OID + 'foo'},
             []),
            ({'name': SFABRIC1_NAME + 'foo',
              'object-id': SFABRIC1_OID},
             []),
        ]
    )

    @pytest.mark.parametrize(*testcases_sfm_list_filter_args)
    def test_sfm_list_filter_args(self, filter_args, exp_names):
        """Test StorageFabricManager.list() with filter_args."""

        self.add_fabric1()
        self.add_fabric2()

        fabric_mgr = self.console.storage_fabrics

        # Execute the code to be tested
        fabrics = fabric_mgr.list(filter_args=filter_args)

        assert len(fabrics) == len(exp_names)
        if exp_names:
            names = [f.properties['name'] for f in fabrics]
            assert set(names) == set(exp_names)

    testcases_sfm_create = (
        "input_props, exp_prop_names, exp_exc", [
            # Missing required fields → 400
            ({},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            # name only — missing cpc-uri → 400
            ({'name': 'fake-fabric-x'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            # cpc-uri only — missing name → 400
            ({'cpc-uri': CPC_URI},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            # Both required fields → success
            ({'name': 'fake-fabric-x',
              'cpc-uri': CPC_URI},
             ['object-uri', 'name', 'cpc-uri'],
             None),
            # All fields → success
            ({'name': 'fake-fabric-y',
              'cpc-uri': CPC_URI,
              'description': 'Fabric Y description',
              'high-integrity': True},
             ['object-uri', 'name', 'cpc-uri', 'description'],
             None),
        ]
    )

    @pytest.mark.parametrize(*testcases_sfm_create)
    def test_sfm_create(self, input_props, exp_prop_names, exp_exc):
        """Test StorageFabricManager.create()."""

        fabric_mgr = self.console.storage_fabrics

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:
                # Execute the code to be tested
                fabric_mgr.create(properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            # StorageFabric.create() returns the object with input
            # properties plus 'object-uri'.
            fabric = fabric_mgr.create(properties=input_props)

            # Check the resource for internal consistency
            assert isinstance(fabric, StorageFabric)
            assert fabric.name == fabric.properties['name']
            assert fabric.uri == fabric.properties['object-uri']

            # Check that expected property names are present
            for prop_name in exp_prop_names:
                assert prop_name in fabric.properties
                if prop_name in input_props:
                    assert fabric.properties[prop_name] == input_props[prop_name]

    def test_sfm_resource_object(self):
        """Test StorageFabricManager.resource_object()."""

        faked_fabric = self.add_fabric1()
        fabric_oid = faked_fabric.oid

        fabric_mgr = self.console.storage_fabrics

        # Execute the code to be tested
        fabric = fabric_mgr.resource_object(fabric_oid)

        expected_uri = f'/api/storage-fabrics/{fabric_oid}'

        assert isinstance(fabric, StorageFabric)
        assert fabric.properties['object-uri'] == expected_uri
        assert fabric.properties['object-id'] == fabric_oid
        assert fabric.properties['class'] == 'storage-fabric'
        assert fabric.properties['parent'] == self.console.uri

    # -------------------------------------------------------------------------
    # StorageFabric resource tests
    # -------------------------------------------------------------------------

    def test_sf_repr(self):
        """Test StorageFabric.__repr__()."""

        faked_fabric = self.add_fabric1()

        fabric_mgr = self.console.storage_fabrics
        fabric = fabric_mgr.find(name=faked_fabric.name)

        # Execute the code to be tested
        repr_str = repr(fabric)

        repr_str = repr_str.replace('\n', '\\n')
        assert re.match(
            rf'^{fabric.__class__.__name__}\s+at\s+'
            rf'0x{id(fabric):08x}\s+\(\\n.*',
            repr_str)

    def test_sf_delete(self):
        """Test StorageFabric.delete()."""

        faked_fabric = self.add_fabric1()
        self.add_fabric2()

        fabric_mgr = self.console.storage_fabrics
        fabric = fabric_mgr.find(name=faked_fabric.name)

        # Execute the code to be tested
        fabric.delete()

        # Verify the fabric no longer exists
        with pytest.raises(NotFound):
            fabric_mgr.find(name=faked_fabric.name)

    def test_sf_delete_create_same(self):
        """Test StorageFabric.delete() followed by create() with same name."""

        faked_fabric = self.add_fabric1()
        fabric_name = faked_fabric.name
        self.add_fabric2()

        # Build properties for a re-created fabric with the same name
        recreate_props = copy.deepcopy(faked_fabric.properties)
        recreate_props['description'] = 'Re-created fabric'

        fabric_mgr = self.console.storage_fabrics
        fabric = fabric_mgr.find(name=fabric_name)

        # Delete
        fabric.delete()

        with pytest.raises(NotFound):
            fabric_mgr.find(name=fabric_name)

        # Re-create with same name
        fabric_mgr.create(recreate_props)

        # Verify it exists again
        fabric3 = fabric_mgr.find(name=fabric_name)
        assert fabric3.get_property('description') == 'Re-created fabric'

    # Parameterised update_properties tests
    testcases_sf_update_properties_fabrics = (
        "fabric_name", [SFABRIC1_NAME, SFABRIC2_NAME]
    )

    testcases_sf_update_properties_props = (
        "input_props", [
            {},
            {'description': 'Updated description'},
            {'description': 'Updated description', 'high-integrity': True},
        ]
    )

    @pytest.mark.parametrize(*testcases_sf_update_properties_fabrics)
    @pytest.mark.parametrize(*testcases_sf_update_properties_props)
    def test_sf_update_properties(self, input_props, fabric_name):
        """Test StorageFabric.update_properties()."""

        self.add_fabric1()
        self.add_fabric2()

        fabric_mgr = self.console.storage_fabrics
        fabric = fabric_mgr.find(name=fabric_name)

        fabric.pull_full_properties()
        saved_properties = copy.deepcopy(fabric.properties)

        # Execute the code to be tested
        fabric.update_properties(properties=input_props)

        # Resource object should immediately reflect updates
        for prop_name in saved_properties:
            exp_value = (input_props[prop_name]
                         if prop_name in input_props
                         else saved_properties[prop_name])
            assert prop_name in fabric.properties
            assert fabric.properties[prop_name] == exp_value

        # Verify updates survive a full-properties refresh
        fabric.pull_full_properties()
        for prop_name in saved_properties:
            exp_value = (input_props[prop_name]
                         if prop_name in input_props
                         else saved_properties[prop_name])
            assert prop_name in fabric.properties
            assert fabric.properties[prop_name] == exp_value

    def test_sf_update_name(self):
        """Test StorageFabric.update_properties() with 'name' property."""

        faked_fabric = self.add_fabric1()
        fabric_name = faked_fabric.name

        fabric_mgr = self.console.storage_fabrics
        fabric = fabric_mgr.find(name=fabric_name)

        new_name = 'renamed-' + fabric_name

        # Execute the code to be tested
        fabric.update_properties(properties={'name': new_name})

        # Old name: list() should return no results
        fabrics_old = fabric_mgr.list(filter_args=dict(name=fabric_name))
        assert len(fabrics_old) == 0

        # Old name: find() must raise NotFound
        with pytest.raises(NotFound):
            fabric_mgr.find(name=fabric_name)

        # Resource object should already reflect the new name
        assert fabric.properties['name'] == new_name

        # After a full-properties pull the new name is still there
        fabric.pull_full_properties()
        assert fabric.properties['name'] == new_name

        # New name: find() must succeed
        fabric_found = fabric_mgr.find(name=new_name)
        assert fabric_found.properties['name'] == new_name

        # New name: list() must return exactly one result
        fabrics_new = fabric_mgr.list(filter_args=dict(name=new_name))
        assert len(fabrics_new) == 1
        assert fabrics_new[0].properties['name'] == new_name

    def test_sf_default_properties(self):
        """Test that FakedStorageFabric has correct default property values."""

        # Create a fabric without optional properties
        faked_fabric = self.faked_console.storage_fabrics.add({
            'object-id': 'sf-defaults-oid',
            'cpc-uri': CPC_URI,
            'name': 'Fabric Defaults',
        })

        fabric_mgr = self.console.storage_fabrics
        fabric = fabric_mgr.find(name='Fabric Defaults')
        fabric.pull_full_properties()

        # Verify the defaults set by FakedStorageFabricManager.add()
        assert fabric.properties['description'] == ''
        assert fabric.properties['storage-switch-uris'] == []
        assert fabric.properties['high-integrity'] is False

        # Clean up
        faked_fabric.manager.remove(faked_fabric.oid)

    def test_sf_cpc_uri_property(self):
        """Test that cpc-uri is set and accessible."""

        faked_fabric = self.add_fabric1()

        fabric_mgr = self.console.storage_fabrics
        fabric = fabric_mgr.find(name=faked_fabric.name)
        fabric.pull_full_properties()

        assert fabric.properties['cpc-uri'] == CPC_URI

    def test_sf_high_integrity_property(self):
        """Test that high-integrity property is correctly stored."""

        # Fabric 1: high-integrity = False
        self.add_fabric1()
        # Fabric 2: high-integrity = True
        self.add_fabric2()

        fabric_mgr = self.console.storage_fabrics

        fabric1 = fabric_mgr.find(name=SFABRIC1_NAME)
        fabric1.pull_full_properties()
        assert fabric1.properties['high-integrity'] is False

        fabric2 = fabric_mgr.find(name=SFABRIC2_NAME)
        fabric2.pull_full_properties()
        assert fabric2.properties['high-integrity'] is True

    def test_sf_list_empty(self):
        """Test StorageFabricManager.list() with no fabrics defined."""

        fabric_mgr = self.console.storage_fabrics

        fabrics = fabric_mgr.list()

        assert fabrics == []

    def test_sf_list_two(self):
        """Test StorageFabricManager.list() with two fabrics defined."""

        self.add_fabric1()
        self.add_fabric2()

        fabric_mgr = self.console.storage_fabrics

        fabrics = fabric_mgr.list()

        assert len(fabrics) == 2
        names = {f.properties['name'] for f in fabrics}
        assert names == {SFABRIC1_NAME, SFABRIC2_NAME}

    def test_sf_storage_switch_uris_default(self):
        """Test that storage-switch-uris defaults to empty list."""

        self.add_fabric1()

        fabric_mgr = self.console.storage_fabrics
        fabric = fabric_mgr.find(name=SFABRIC1_NAME)
        fabric.pull_full_properties()

        assert fabric.properties['storage-switch-uris'] == []

    def test_sf_class_property(self):
        """Test that the class property is correctly set to 'storage-fabric'."""

        self.add_fabric1()

        fabric_mgr = self.console.storage_fabrics
        fabric = fabric_mgr.find(name=SFABRIC1_NAME)
        fabric.pull_full_properties()

        assert fabric.properties['class'] == 'storage-fabric'
