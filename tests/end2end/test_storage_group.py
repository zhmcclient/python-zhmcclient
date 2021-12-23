# Copyright 2017-2021 IBM Corp. All Rights Reserved.
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

# pylint: disable=attribute-defined-outside-init

"""
End2end tests for storage groups and their child resources.

Only tested on CPCs in DPM mode, and skipped otherwise.
"""

from __future__ import absolute_import, print_function

import pytest
from requests.packages import urllib3

import zhmcclient
# pylint: disable=line-too-long,unused-import
from zhmcclient.testutils.hmc_definition_fixtures import hmc_definition, hmc_session  # noqa: F401, E501
# pylint: disable=unused-import

urllib3.disable_warnings()


def dpm_storage_management_enabled(cpc):
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


def test_stogrp_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a storage group.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for cpc_name in hd.cpcs:
        cpc = client.cpcs.find_by_name(cpc_name)
        if not cpc.get_property('dpm-enabled'):
            pytest.skip("CPC {} is not in DPM mode".format(cpc_name))
        if not dpm_storage_management_enabled(cpc):
            pytest.skip("DPM Storage feature not enabled or not supported "
                        "on CPC {}".format(cpc_name))

        console = client.consoles.console
        stogrp_name = 'test_stogrp_crud.stogrp1'

        # Ensure clean starting point
        try:
            stogrp = console.storage_groups.find(name=stogrp_name)
        except zhmcclient.NotFound:
            pass
        else:
            stogrp.delete()

        # Test creating the storage group

        stogrp_input_props = {
            'cpc-uri': cpc.uri,
            'name': stogrp_name,
            'description': 'Dummy storage group description.',
            'type': 'fcp',
        }
        stogrp_auto_props = {
            'shared': True,
            'fulfillment-state': 'pending',
        }

        stogrp = console.storage_groups.create(stogrp_input_props)

        for pn, exp_value in stogrp_input_props.items():
            assert stogrp.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage group:\n" \
                "{!r}".format(pn, sorted(stogrp.properties))
        stogrp.pull_full_properties()
        for pn, exp_value in stogrp_input_props.items():
            assert stogrp.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage group:\n" \
                "{!r}".format(pn, sorted(stogrp.properties))
        for pn, exp_value in stogrp_auto_props.items():
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

        stogrps = console.storage_groups.findall(shared=True)

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


def test_stovol_crud(hmc_session):  # noqa: F811
    # pylint: disable=redefined-outer-name
    """
    Test create, read, update and delete a storage volume in a storage group.
    """
    client = zhmcclient.Client(hmc_session)
    hd = hmc_session.hmc_definition
    for cpc_name in hd.cpcs:
        cpc = client.cpcs.find_by_name(cpc_name)
        if not cpc.get_property('dpm-enabled'):
            pytest.skip("CPC {} is not in DPM mode".format(cpc_name))
        if not dpm_storage_management_enabled(cpc):
            pytest.skip("DPM Storage feature not enabled or not supported "
                        "on CPC {}".format(cpc_name))

        console = client.consoles.console

        stogrp_name = 'test_stovol_crud.stogrp1'
        stovol_name = 'test_stovol_crud.stovol1'

        # Ensure clean starting point
        try:
            stogrp = console.storage_groups.find(name=stogrp_name)
        except zhmcclient.NotFound:
            pass
        else:
            stogrp.delete()

        # Create a storage group for the volume
        stogrp_input_props = {
            'cpc-uri': cpc.uri,
            'name': stogrp_name,
            'description': 'Dummy storage group description.',
            'type': 'fcp',
        }
        stogrp = console.storage_groups.create(stogrp_input_props)

        # Test creating a volume

        stovol_input_props = {
            'name': stovol_name,
            'description': 'Dummy storage volume description.',
            'size': 100,  # MB
        }
        stovol_auto_props = {
            'fulfillment-state': 'pending',
            'usage': 'data',
        }

        stovol = stogrp.storage_volumes.create(stovol_input_props)

        for pn, exp_value in stovol_input_props.items():
            assert stovol.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage volume:\n" \
                "{!r}".format(pn, sorted(stovol.properties))
        stovol.pull_full_properties()
        for pn, exp_value in stovol_input_props.items():
            assert stovol.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage volume:\n" \
                "{!r}".format(pn, sorted(stovol.properties))
        for pn, exp_value in stovol_auto_props.items():
            assert stovol.properties[pn] == exp_value, \
                "Unexpected value for property {!r} of storage volume:\n" \
                "{!r}".format(pn, sorted(stovol.properties))

        # Test finding the storage volume based on its (cached) name

        sv = stogrp.storage_volumes.find(name=stovol_name)

        assert sv.name == stovol_name

        # Test finding the storage volume based on a server-side filtered prop

        stovols = stogrp.storage_volumes.findall(usage='data')
        assert stovol_name in [sv.name for sv in stovols]  # noqa: F812

        # Test finding the storage group based on a client-side filtered prop

        stovols = stogrp.storage_volumes.findall(size=100)
        assert stovol_name in [sv.name for sv in stovols]

        # Test updating a property of the storage volume

        new_desc = "Updated storage volume description."

        stovol.update_properties(dict(description=new_desc))

        assert stovol.properties['description'] == new_desc
        stovol.pull_full_properties()
        assert stovol.properties['description'] == new_desc

        # Test deleting the storage volume

        stovol.delete()

        with pytest.raises(zhmcclient.NotFound):
            stogrp.storage_volumes.find(name=stovol_name)

        # Cleanup
        stogrp.delete()
