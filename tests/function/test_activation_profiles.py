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
Function tests for activation profile handling.
"""

from __future__ import absolute_import, print_function

import pytest
import requests.packages.urllib3

import zhmcclient
from tests.common.utils import HmcCredentials, setup_cpc, setup_logging

requests.packages.urllib3.disable_warnings()


class TestActivationProfiles(object):
    """Test activation profile handling."""

    # Prefix for any names of HMC resources that are being created
    NAME_PREFIX = 'zhmcclient.TestActivationProfiles.'

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
                'name': 'CPC1',
                'description': 'Fake CPC #1 (classic mode)',
                'status': 'active',
                'dpm-enabled': False,
                'is-ensemble-member': False,
                'iml-mode': 'lpar',
            })
        self.faked_cpc_resources = {
            'lpars': [
                {
                    'properties': {
                        'partition-number': 0x41,
                        'partition-identifier': 0x41,
                        'name': 'LPAR1',
                        'status': 'operating',
                        'activation-mode': 'linux',
                        'next-activation-profile-name': 'LPAR1',
                        'last-used-activation-profile': 'LPAR1',
                    },
                },
                {
                    'properties': {
                        'partition-number': 0x42,
                        'partition-identifier': 0x42,
                        'name': 'LPAR2',
                        'status': 'not-activated',
                        'activation-mode': 'not-set',
                        'next-activation-profile-name': 'LPAR2',
                        'last-used-activation-profile': 'LPAR2',
                    },
                },
            ],
            'reset_activation_profiles': [
                {
                    'properties': {
                        'name': 'CPC1',
                        'iocds-name': 'ABC',
                    },
                },
            ],
            'load_activation_profiles': [
                {
                    'properties': {
                        'name': 'LPAR1',
                        'ipl-type': 'ipltype-standard',
                        'ipl-address': '189AB',
                    },
                },
                {
                    'properties': {
                        'name': 'LPAR2',
                        'ipl-type': 'ipltype-scsi',
                        'worldwide-port-name': '1234',
                        'logical-unit-number': '1234',
                        'boot-record-lba': '1234',
                        'disk-partition-id': 0,
                    },
                },
            ],
            'image_activation_profiles': [
                {
                    'properties': {
                        'name': 'LPAR1',
                        # TODO: Add more properties
                    },
                },
                {
                    'properties': {
                        'name': 'LPAR2',
                        # TODO: Add more properties
                    },
                },
            ],
        }
        setup_logging()

    @pytest.mark.parametrize(
        "profile_type", ['reset', 'image', 'load']
    )
    def test_ap_lf(self, capsys, profile_type):
        """List and find activation profiles."""

        cpc_name, session, client, cpc, faked_cpc = \
            setup_cpc(capsys, self.hmc_creds, self.fake_data)

        if faked_cpc:
            faked_cpc.add_resources(self.faked_cpc_resources)

        ap_mgr_attr = profile_type + '_activation_profiles'
        ap_class = profile_type + '-activation-profile'

        ap_mgr = getattr(cpc, ap_mgr_attr)

        # Test listing activation profiles

        ap_list = ap_mgr.list()

        assert len(ap_list) >= 1
        for ap in ap_list:
            assert isinstance(ap, zhmcclient.ActivationProfile)

        # Pick the last one returned
        ap = ap_list[-1]
        ap_name = ap.name

        # Test finding the activation profile based on its (cached) name

        ap_found = ap_mgr.find(name=ap_name)

        assert ap_found.name == ap_name

        # There are no other server-side filtered props besides name

        # Test finding the partition based on a client-side filtered prop

        aps_found = ap_mgr.findall(**{'class': ap_class})

        assert ap_name in [ap.name for ap in aps_found]  # noqa: F812

        # Cleanup
        session.logoff()
