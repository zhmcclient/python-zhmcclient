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
Function tests for partition lifecycle.
"""

from __future__ import absolute_import, print_function

import pytest
import requests.packages.urllib3

import zhmcclient
from tests.common.utils import HmcCredentials, info, setup_cpc, setup_logging

requests.packages.urllib3.disable_warnings()


class TestPartitionLifecycle(object):
    """Test partition lifecycle."""

    # Prefix for any names of HMC resources that are being created
    NAME_PREFIX = 'zhmcclient.TestPartitionLifecycle.'

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
            })
        setup_logging()

    def test_crud(self, capsys):
        """Create, read, update and delete a partition."""

        cpc_name, session, client, cpc, faked_cpc = \
            setup_cpc(capsys, self.hmc_creds, self.fake_data)

        part_name = self.NAME_PREFIX + 'test_crud.part1'

        # Ensure a clean starting point for this test
        try:
            part = cpc.partitions.find(name=part_name)
        except zhmcclient.NotFound:
            pass
        else:
            info(capsys, "Cleaning up partition from previous run: {!r}".
                 format(part))
            status = part.get_property('status')
            if status != 'stopped':
                part.stop()
            part.delete()

        # Test creating the partition

        part_input_props = {
            'name': part_name,
            'description': 'Dummy partition description.',
            'ifl-processors': 2,
            'initial-memory': 1024,
            'maximum-memory': 2048,
            'processor-mode': 'shared',  # used for filtering
            'type': 'linux',  # used for filtering
        }
        part_auto_props = {
            'status': 'stopped',
        }

        part = cpc.partitions.create(part_input_props)

        for pn in part_input_props:
            exp_value = part_input_props[pn]
            assert part.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        part.pull_full_properties()
        for pn in part_input_props:
            exp_value = part_input_props[pn]
            assert part.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)
        for pn in part_auto_props:
            exp_value = part_auto_props[pn]
            assert part.properties[pn] == exp_value, \
                "Unexpected value for property {!r}".format(pn)

        # Test finding the partition based on its (cached) name

        p = cpc.partitions.find(name=part_name)

        assert p.name == part_name

        # Test finding the partition based on a server-side filtered prop

        parts = cpc.partitions.findall(type='linux')

        assert part_name in [p.name for p in parts]  # noqa: F812

        # Test finding the partition based on a client-side filtered prop

        parts = cpc.partitions.findall(**{'processor-mode': 'shared'})

        assert part_name in [p.name for p in parts]  # noqa: F812

        # Test updating a property of the partition

        new_desc = "Updated partition description."

        part.update_properties(dict(description=new_desc))

        assert part.properties['description'] == new_desc
        part.pull_full_properties()
        assert part.properties['description'] == new_desc

        # Test deleting the partition

        part.delete()

        with pytest.raises(zhmcclient.NotFound):
            cpc.partitions.find(name=part_name)

        # Cleanup
        session.logoff()
