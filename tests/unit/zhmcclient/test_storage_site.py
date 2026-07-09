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
Unit tests for _storage_site module.
"""


import copy
import pytest

from zhmcclient import Client, StorageSite, HTTPError, NotFound
from zhmcclient.mock import FakedSession
from tests.common.utils import assert_resources

# Object names and IDs for our faked storage sites:
SS1_NAME = 'Primary Site'
SS2_NAME = 'Alternate Site'
CPC_OID = 'fake-cpc1-oid'
CPC_URI = f'/api/cpcs/{CPC_OID}'


class TestStorageSite:
    """All tests for the StorageSite and StorageSiteManager classes."""

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Sets up a faked session with a faked Console and a faked CPC.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.14.0', '1.8')
        self.client = Client(self.session)
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
                dict(name='dpm-storage-management', state=True),
            ],
        })
        assert self.faked_cpc.uri == CPC_URI

        self.faked_console = self.session.hmc.consoles.add({
            'object-id': None,
            # object-uri will be automatically set
            'parent': None,
            'class': 'console',
            'name': 'fake-console1',
            'description': 'Console #1',
        })
        self.console = self.client.consoles.find(name=self.faked_console.name)

    def add_storage_site(self, name, cpc_uris=None):
        """Add a faked storage site to the faked console."""
        if cpc_uris is None:
            cpc_uris = [CPC_URI]
        faked_storage_site = self.faked_console.storage_sites.add({
            'object-uri': f'/api/storage-sites/{name}',
            'parent': self.faked_console.uri,
            'class': 'storage-site',
            'name': name,
            'description': f'Storage site {name}',
            'cpc-uris': cpc_uris,
        })
        return faked_storage_site

    def test_storage_site_mgr_initial_attrs(self):
        """Test initial attributes of StorageSiteManager."""

        ss_mgr = self.console.storage_sites

        # Verify all public properties of the manager object
        assert ss_mgr.resource_class == StorageSite
        assert ss_mgr.class_name == 'storage-site'
        assert ss_mgr.session == self.session
        assert ss_mgr.parent == self.console
        assert ss_mgr.console == self.console

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(full_properties=False),
             ['object-uri', 'name', 'cpc-uris']),
            (dict(full_properties=True),
             ['object-uri', 'name', 'cpc-uris', 'description']),
            ({},  # test default for full_properties (False)
             ['object-uri', 'name', 'cpc-uris']),
        ]
    )
    @pytest.mark.parametrize(
        "filter_args, exp_name", [
            (None, [SS1_NAME, SS2_NAME]),
            ({}, [SS1_NAME, SS2_NAME]),
            ({'name': SS1_NAME}, [SS1_NAME]),
            ({'name': [SS1_NAME, SS2_NAME]}, [SS1_NAME, SS2_NAME]),
        ]
    )
    def test_storage_site_mgr_list(
            self, filter_args, exp_name, full_properties_kwargs, prop_names):
        """Test StorageSiteManager.list()."""

        faked_ss1 = self.add_storage_site(name=SS1_NAME)
        faked_ss2 = self.add_storage_site(name=SS2_NAME)
        faked_sites = [faked_ss1, faked_ss2]
        exp_faked_sites = [s for s in faked_sites if s.name in exp_name]
        ss_mgr = self.console.storage_sites

        # Execute the code to be tested
        sites = ss_mgr.list(filter_args=filter_args, **full_properties_kwargs)

        assert_resources(sites, exp_faked_sites, prop_names)

    @pytest.mark.parametrize(
        "input_props, exp_exc", [
            ({'name': SS2_NAME},
             None),
            ({'name': SS2_NAME, 'description': 'Alternate site'},
             None),
            ({},  # missing required 'name'
             HTTPError({'http-status': 400, 'reason': 5})),
        ]
    )
    def test_storage_site_mgr_create(self, input_props, exp_exc):
        """Test StorageSiteManager.create()."""

        ss_mgr = self.console.storage_sites

        if exp_exc is not None:
            with pytest.raises(exp_exc.__class__) as exc_info:
                # Execute the code to be tested
                ss_mgr.create(input_props)
            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason
        else:
            # Execute the code to be tested
            ss = ss_mgr.create(input_props)

            assert isinstance(ss, StorageSite)
            # Verify the site can be found
            found_ss = ss_mgr.find(name=input_props['name'])
            assert found_ss.name == input_props['name']

    @pytest.mark.parametrize(
        "input_props, exp_exc", [
            ({'name': SS2_NAME}, None),
        ]
    )
    def test_storage_site_delete(self, input_props, exp_exc):
        """Test StorageSite.delete()."""

        faked_ss = self.add_storage_site(name=input_props['name'])

        ss_mgr = self.console.storage_sites
        ss = ss_mgr.find(name=faked_ss.name)

        if exp_exc is not None:
            with pytest.raises(exp_exc.__class__) as exc_info:
                # Execute the code to be tested
                ss.delete()
            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason
            # Check that the storage site still exists
            ss_mgr.find(name=faked_ss.name)
        else:
            # Execute the code to be tested
            ss.delete()

            # Check that the storage site no longer exists
            with pytest.raises(NotFound):
                ss_mgr.find(name=ss.name)

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'name': SS2_NAME},
            {'description': 'Updated alternate site description'},
        ]
    )
    def test_storage_site_update_properties(self, input_props):
        """Test StorageSite.update_properties()."""

        site_name = SS2_NAME

        # Add the storage site to be tested
        self.add_storage_site(name=site_name)

        ss_mgr = self.console.storage_sites
        ss = ss_mgr.find(name=site_name)

        ss.pull_full_properties()
        saved_properties = copy.deepcopy(ss.properties)

        # Execute the code to be tested
        ss.update_properties(properties=input_props)
        ss.pull_full_properties()

        # Verify that the resource object already reflects the property updates
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in ss.properties
            prop_value = ss.properties[prop_name]
            assert prop_value == exp_prop_value, \
                f"Unexpected value for property {prop_name!r}"

        # Refresh the resource object and verify it still reflects updates
        ss.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in ss.properties
            prop_value = ss.properties[prop_name]
            assert prop_value == exp_prop_value

    def test_storage_site_default_properties(self):
        """Test that faked storage site gets correct default property values."""

        faked_ss = self.faked_console.storage_sites.add({
            'name': SS1_NAME,
        })

        # Verify default properties are set
        assert faked_ss.properties.get('description') == ''
        assert faked_ss.properties.get('cpc-uris') == []
        assert faked_ss.properties.get('class') == 'storage-site'
        assert faked_ss.properties.get('name') == SS1_NAME

    def test_storage_site_dump(self):
        """Test StorageSite.dump()."""

        faked_ss = self.add_storage_site(name=SS1_NAME)

        ss_mgr = self.console.storage_sites
        ss = ss_mgr.find(name=faked_ss.name)
        ss.pull_full_properties()

        # Execute the code to be tested
        resource_dict = ss.dump()

        assert isinstance(resource_dict, dict)
        assert 'properties' in resource_dict
        assert resource_dict['properties']['name'] == SS1_NAME

    def test_storage_site_list_empty(self):
        """Test that listing an empty set of storage sites works."""

        ss_mgr = self.console.storage_sites
        sites = ss_mgr.list()
        assert sites == []

    def test_storage_site_list_cpc_uri_filter(self):
        """Test listing storage sites filtered by cpc-uris."""

        faked_ss1 = self.add_storage_site(name=SS1_NAME, cpc_uris=[CPC_URI])
        self.add_storage_site(name=SS2_NAME, cpc_uris=['/api/cpcs/other-cpc'])

        ss_mgr = self.console.storage_sites

        # List all sites
        all_sites = ss_mgr.list()
        assert len(all_sites) == 2

        # Find the site for our CPC by filtering
        cpc_sites = ss_mgr.list(filter_args={'name': SS1_NAME})
        assert len(cpc_sites) == 1
        assert cpc_sites[0].name == faked_ss1.name
