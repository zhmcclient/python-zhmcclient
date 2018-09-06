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
Function tests for storage groups and their child resources.
"""

from __future__ import absolute_import, print_function

import pytest
import requests.packages.urllib3

import zhmcclient
from tests.common.utils import HmcCredentials, info, setup_cpc

requests.packages.urllib3.disable_warnings()


@pytest.mark.skip('TODO: Enable and fix issues')
class TestStorageGroups(object):
    """Test storage groups and their child resources."""

    # Prefix for any names of HMC resources that are being created
    NAME_PREFIX = 'zhmcclient.TestStorageGroups.'

    def setup_method(self):
        """
        Set up HMC data, Session to that HMC, Client, and Cpc object.
        """
        self.hmc_creds = HmcCredentials()
        self.fake_data = dict(
            hmc_host='fake-host', hmc_name='fake-hmc',
            hmc_version='2.13.1', api_version='1.8',
            cpc_properties={
                'object-id': 'fake-cpc1-oid',
                # object-uri is set up automatically
                'parent': None,
                'class': 'cpc',
                'name': 'fake-cpc1',
                'description': 'Fake CPC #1 (DPM mode)',
                'status': 'active',
                'dpm-enabled': True,
                'is-ensemble-member': False,
                'iml-mode': 'dpm',
                'available-features-list': [
                    dict(name='dpm-storage-management', state=True),
                ],
            })
        # setup_logging()

    @classmethod
    def dpm_storage_management_enabled(self, cpc):
        """
        Return boolean indicating whether the "DPM Storage Management" feature
        is enabled for the specified CPC.

        If the machine is not even aware of firmware features, it is considered
        disabled.
        """
        try:
            dpm_sm = cpc.feature_enabled('dpm-storage-management')
        except ValueError:
            dpm_sm = False
        return dpm_sm

    def test_stogrp_crud(self, capsys):
        """Create, read, update and delete a storage group."""

        cpc_name, session, client, cpc, faked_cpc = \
            setup_cpc(capsys, self.hmc_creds, self.fake_data)

        if not self.dpm_storage_management_enabled(cpc):
            info(capsys, "DPM Storage feature not enabled or not supported; "
                 "Skipping test_stogrp_crud() test case")
            return

        console = client.consoles.console
        stogrp_name = self.NAME_PREFIX + 'test_stogrp_crud.stogrp1'

        # Ensure clean starting point
        try:
            stogrp = console.storage_groups.find(name=stogrp_name)
        except zhmcclient.NotFound:
            pass
        else:
            info(capsys, "Cleaning up storage group from previous run: {!r}".
                 format(stogrp))
            stogrp.delete()

        # Test creating the storage group

        stogrp_input_props = {
            'name': stogrp_name,
            'description': 'Dummy storage group description.',
            'type': 'fcp',
        }
        stogrp_auto_props = {
            'shared': False,
            'active': False,
            'fulfillment-state': 'creating',
            'adapter-count': 1,
        }

        stogrp = console.storage_groups.create(stogrp_input_props)

        for pn in stogrp_input_props:
            exp_value = stogrp_input_props[pn]
            assert stogrp.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage group:\n" \
                "{!r}".format(pn, sorted(stogrp.properties))
        stogrp.pull_full_properties()
        for pn in stogrp_input_props:
            exp_value = stogrp_input_props[pn]
            assert stogrp.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage group:\n" \
                "{!r}".format(pn, sorted(stogrp.properties))
        if not faked_cpc:
            for pn in stogrp_auto_props:
                exp_value = stogrp_auto_props[pn]
                assert stogrp.properties[pn] == exp_value, \
                    "Unexpected value for property {!r} of storage group:\n" \
                    "{!r}".format(pn, sorted(stogrp.properties))

        # Test finding the storage group based on its (cached) name

        sg = console.storage_groups.find(name=stogrp_name)

        assert sg.name == stogrp_name

        # Test finding the storage group based on a server-side filtered prop

        stogrps = console.storage_groups.findall(type='fcp')

        assert stogrp_name in [sg.name for sg in stogrps]  # noqa: F812

        # Test finding the storage group based on a client-side filtered prop

        stogrps = console.storage_groups.findall(active=False)

        assert stogrp_name in [sg.name for sg in stogrps]

        # Test updating a property of the storage group

        new_desc = "Updated storage group description."

        stogrp.update_properties(dict(description=new_desc))

        assert stogrp.properties['description'] == new_desc
        stogrp.pull_full_properties()
        assert stogrp.properties['description'] == new_desc

        # Test deleting the storage group

        stogrp.delete()

        with pytest.raises(zhmcclient.NotFound):
            console.storage_groups.find(name=stogrp_name)

        # Cleanup
        session.logoff()

    def test_stovol_crud(self, capsys):
        """Create, read, update and delete a storage volume in a sto.grp."""

        cpc_name, session, client, cpc, faked_cpc = \
            setup_cpc(capsys, self.hmc_creds, self.fake_data)

        if not self.dpm_storage_management_enabled(cpc):
            info(capsys, "DPM Storage feature not enabled or not supported; "
                 "Skipping test_stovol_crud() test case")
            return

        console = client.consoles.console

        stogrp_name = self.NAME_PREFIX + 'test_stovol_crud.stogrp1'
        stovol_name = self.NAME_PREFIX + 'test_stovol_crud.stovol1'

        # Ensure clean starting point
        try:
            stogrp = console.storage_groups.find(name=stogrp_name)
        except zhmcclient.NotFound:
            pass
        else:
            info(capsys, "Cleaning up storage group from previous run: {!r}".
                 format(stogrp))
            stogrp.delete()

        # Create a storage group for the volume
        stogrp = console.storage_groups.create(
            dict(name=stogrp_name, type='fcp'))

        # Test creating a volume

        stovol_input_props = {
            'name': stovol_name,
            'description': 'Dummy storage volume description.',
            'size': 100,  # MB
        }
        stovol_auto_props = {
            'fulfillment-state': 'creating',
            'usage': 'data',
        }

        # TODO: Remove this tempfix when fixed:
        if True:
            info(capsys, "Tempfix: Volume does not support 'cpc-uri' "
                 "property; Omitting it in Create Volume.")
        else:
            stovol_input_props['cpc-uri'] = cpc.uri

        stovol = stogrp.storage_volumes.create(stovol_input_props)

        for pn in stovol_input_props:
            exp_value = stovol_input_props[pn]
            assert stovol.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage volume:\n" \
                "{!r}".format(pn, sorted(stovol.properties))
        stovol.pull_full_properties()
        for pn in stovol_input_props:
            # TODO: Remove this tempfix when fixed:
            if pn == 'name':
                info(capsys, "Tempfix: Create Volume does not honor name; "
                     "Skipping assertion of name:\n"
                     "  provided name: %r\n"
                     "  created name:  %r" %
                     (stovol_input_props[pn], stovol.properties[pn]))
                continue
            exp_value = stovol_input_props[pn]
            assert stovol.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage volume:\n" \
                "{!r}".format(pn, sorted(stovol.properties))
        if not faked_cpc:
            for pn in stovol_auto_props:
                exp_value = stovol_auto_props[pn]
                assert stovol.properties[pn] == exp_value, \
                    "Unexpected value for property {!r} of storage volume:\n" \
                    "{!r}".format(pn, sorted(stovol.properties))

        # Test finding the storage volume based on its (cached) name

        sv = stogrp.storage_volumes.find(name=stovol_name)

        assert sv.name == stovol_name

        # Test finding the storage volume based on a server-side filtered prop

        # TODO: Remove this tempfix when fixed:
        try:
            stovols = stogrp.storage_volumes.find(usage='data')
        except zhmcclient.HTTPError as exc:
            if exc.http_status == 500:
                info(capsys, "Tempfix: List Volumes filtered by usage raises "
                     "%s,%s %r; Skipping this test." %
                     (exc.http_status, exc.reason, exc.message))
        else:
            assert stovol_name in [sv.name for sv in stovols]  # noqa: F812

        # Test finding the storage group based on a client-side filtered prop

        # TODO: Remove this tempfix when fixed:
        try:
            stovols = stogrp.storage_volumes.findall(active=False)
        except zhmcclient.HTTPError as exc:
            if exc.http_status == 500:
                info(capsys, "Tempfix: List Volumes raises "
                     "%s,%s %r; Skipping this test." %
                     (exc.http_status, exc.reason, exc.message))
        else:
            assert stovol_name in [sv.name for sv in stovols]

        # Test updating a property of the storage volume

        new_desc = "Updated storage volume description."

        stovol.update_properties(dict(description=new_desc))

        assert stovol.properties['description'] == new_desc
        stovol.pull_full_properties()
        assert stovol.properties['description'] == new_desc

        # Test deleting the storage volume

        # TODO: Remove this tempfix when fixed:
        try:
            stovol.delete()
        except zhmcclient.HTTPError as exc:
            if exc.http_status == 500:
                info(capsys, "Tempfix: Delete Volume raises "
                     "%s,%s %r; Skipping this test." %
                     (exc.http_status, exc.reason, exc.message))
        else:
            with pytest.raises(zhmcclient.NotFound):
                stogrp.storage_volumes.find(name=stovol_name)

        # Cleanup
        stogrp.delete()
        session.logoff()
