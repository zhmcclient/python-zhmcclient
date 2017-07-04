# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Unit tests for _cpc module.
"""

from __future__ import absolute_import, print_function

import pytest

from zhmcclient import Client, Cpc, HTTPError
from zhmcclient_mock import FakedSession
from .utils import assert_resources


# Object IDs and names of our faked CPCs:
CPC1_OID = 'cpc1-oid'
CPC1_NAME = 'cpc 1'
CPC2_OID = 'cpc2-oid'
CPC2_NAME = 'cpc 2'
CPC3_OID = 'cpc3-oid'
CPC3_NAME = 'cpc 3'

HTTPError_404_1 = HTTPError({'http-status': 404, 'reason': 1})
HTTPError_409_5 = HTTPError({'http-status': 409, 'reason': 5})
HTTPError_409_4 = HTTPError({'http-status': 409, 'reason': 4})


class TestCpc(object):
    """All tests for the Cpc and CpcManager classes."""

    def setup_method(self):
        """
        Set up a faked session.
        """

        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

    def add_cpc(self, cpc_name):
        """Add a faked CPC."""

        if cpc_name == CPC1_NAME:
            faked_cpc = self.session.hmc.cpcs.add({
                'object-id': CPC1_OID,
                # object-uri is set up automatically
                'parent': None,
                'class': 'cpc',
                'name': CPC1_NAME,
                'description': 'CPC #1 (z13 in DPM mode)',
                'status': 'active',
                'dpm-enabled': True,
                'is-ensemble-member': False,
                'iml-mode': 'dpm',
                'machine-type': '2964',
            })
        elif cpc_name == CPC2_NAME:
            faked_cpc = self.session.hmc.cpcs.add({
                'object-id': CPC2_OID,
                # object-uri is set up automatically
                'parent': None,
                'class': 'cpc',
                'name': CPC2_NAME,
                'description': 'CPC #2 (z13 in classic mode)',
                'status': 'operating',
                'dpm-enabled': False,
                'is-ensemble-member': False,
                'iml-mode': 'lpar',
                'machine-type': '2964',
            })
        elif cpc_name == CPC3_NAME:
            faked_cpc = self.session.hmc.cpcs.add({
                'object-id': CPC3_OID,
                # object-uri is set up automatically
                'parent': None,
                'class': 'cpc',
                'name': CPC3_NAME,
                'description': 'CPC #3 (zEC12)',
                'status': 'operating',
                # zEC12 does not have a dpm-enabled property
                'is-ensemble-member': False,
                'iml-mode': 'lpar',
                'machine-type': '2827',
            })
        else:
            raise ValueError("Invalid value for cpc_name: %s" % cpc_name)
        return faked_cpc

    def test_manager_initial_attrs(self):
        """Test initial attributes of CpcManager."""

        manager = self.client.cpcs

        # Verify all public properties of the manager object
        assert manager.resource_class == Cpc
        assert manager.session == self.session
        assert manager.parent is None

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(),
             ['object-uri', 'name', 'status']),
            (dict(full_properties=False),
             ['object-uri', 'name', 'status']),
            (dict(full_properties=True),
             None),
        ]
    )
    def test_manager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test CpcManager.list() with full_properties."""

        # Add two faked CPCs
        faked_cpc1 = self.add_cpc(CPC1_NAME)
        faked_cpc2 = self.add_cpc(CPC2_NAME)

        exp_faked_cpcs = [faked_cpc1, faked_cpc2]
        cpc_mgr = self.client.cpcs

        # Execute the code to be tested
        cpcs = cpc_mgr.list(**full_properties_kwargs)

        assert_resources(cpcs, exp_faked_cpcs, prop_names)

    @pytest.mark.parametrize(
        "filter_args, exp_names", [
            ({'object-id': CPC1_OID},
             [CPC1_NAME]),
            ({'object-id': CPC2_OID},
             [CPC2_NAME]),
            ({'object-id': [CPC1_OID, CPC2_OID]},
             [CPC1_NAME, CPC2_NAME]),
            ({'object-id': [CPC1_OID, CPC1_OID]},
             [CPC1_NAME]),
            ({'object-id': CPC1_OID + 'foo'},
             []),
            ({'object-id': [CPC1_OID, CPC2_OID + 'foo']},
             [CPC1_NAME]),
            ({'object-id': [CPC2_OID + 'foo', CPC1_OID]},
             [CPC1_NAME]),
            ({'name': CPC1_NAME},
             [CPC1_NAME]),
            ({'name': CPC2_NAME},
             [CPC2_NAME]),
            ({'name': [CPC1_NAME, CPC2_NAME]},
             [CPC1_NAME, CPC2_NAME]),
            ({'name': CPC1_NAME + 'foo'},
             []),
            ({'name': [CPC1_NAME, CPC2_NAME + 'foo']},
             [CPC1_NAME]),
            ({'name': [CPC2_NAME + 'foo', CPC1_NAME]},
             [CPC1_NAME]),
            ({'name': [CPC1_NAME, CPC1_NAME]},
             [CPC1_NAME]),
            ({'name': '.*cpc 1'},
             [CPC1_NAME]),
            ({'name': 'cpc 1.*'},
             [CPC1_NAME]),
            ({'name': 'cpc .'},
             [CPC1_NAME, CPC2_NAME]),
            ({'name': '.pc 1'},
             [CPC1_NAME]),
            ({'name': '.+'},
             [CPC1_NAME, CPC2_NAME]),
            ({'name': 'cpc 1.+'},
             []),
            ({'name': '.+cpc 1'},
             []),
            ({'name': CPC1_NAME,
              'object-id': CPC1_OID},
             [CPC1_NAME]),
            ({'name': CPC1_NAME,
              'object-id': CPC1_OID + 'foo'},
             []),
            ({'name': CPC1_NAME + 'foo',
              'object-id': CPC1_OID},
             []),
            ({'name': CPC1_NAME + 'foo',
              'object-id': CPC1_OID + 'foo'},
             []),
        ]
    )
    def test_manager_list_filter_args(self, filter_args, exp_names):
        """Test CpcManager.list() with filter_args."""

        # Add two faked CPCs
        self.add_cpc(CPC1_NAME)
        self.add_cpc(CPC2_NAME)

        # Execute the code to be tested
        cpcs = self.client.cpcs.list(filter_args=filter_args)

        assert len(cpcs) == len(exp_names)
        if exp_names:
            names = [ad.properties['name'] for ad in cpcs]
            assert set(names) == set(exp_names)

    @pytest.mark.parametrize(
        "cpc_name, exp_dpm_enabled", [
            (CPC1_NAME, True),
            (CPC2_NAME, False),
            (CPC3_NAME, False),
        ]
    )
    def test_dpm_enabled(self, cpc_name, exp_dpm_enabled):
        """Test Cpc.dpm_enabled."""

        # Add the faked CPC
        self.add_cpc(cpc_name)

        cpc = self.client.cpcs.find(name=cpc_name)

        # Execute the code to be tested
        dpm_enabled = cpc.dpm_enabled

        assert dpm_enabled == exp_dpm_enabled

    @pytest.mark.parametrize(
        "wait_for_completion", [True]
    )
    @pytest.mark.parametrize(
        "cpc_name, initial_status, exp_status, exp_error", [
            (CPC1_NAME, 'not-operating', 'active', None),
            (CPC2_NAME, 'not-operating', None, HTTPError_409_5),
            (CPC3_NAME, 'not-operating', None, HTTPError_409_5),
        ]
    )
    def test_start(self, cpc_name, initial_status, exp_status, exp_error,
                   wait_for_completion):
        """Test Cpc.start()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        faked_cpc = self.add_cpc(cpc_name)

        # Set initial status of the CPC for this test
        faked_cpc.properties['status'] = initial_status

        cpc = self.client.cpcs.find(name=cpc_name)

        if exp_error:
            with pytest.raises(HTTPError) as exc_info:

                # Execute the code to be tested
                result = cpc.start(wait_for_completion=wait_for_completion)

            exc = exc_info.value
            assert exc.http_status == exp_error.http_status
            assert exc.reason == exp_error.reason
        else:

            # Execute the code to be tested
            result = cpc.start(wait_for_completion=wait_for_completion)

            if wait_for_completion:
                assert result is None
            else:
                raise NotImplemented

            cpc.pull_full_properties()
            status = cpc.properties['status']
            assert status == exp_status

    @pytest.mark.parametrize(
        "wait_for_completion", [True]
    )
    @pytest.mark.parametrize(
        "cpc_name, initial_status, exp_status, exp_error", [
            (CPC1_NAME, 'active', 'not-operating', None),
            (CPC2_NAME, 'operating', None, HTTPError_409_5),
            (CPC3_NAME, 'operating', None, HTTPError_409_5),
        ]
    )
    def test_stop(self, cpc_name, initial_status, exp_status, exp_error,
                  wait_for_completion):
        """Test Cpc.stop()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        faked_cpc = self.add_cpc(cpc_name)

        # Set initial status of the CPC for this test
        faked_cpc.properties['status'] = initial_status

        cpc = self.client.cpcs.find(name=cpc_name)

        if exp_error:
            with pytest.raises(HTTPError) as exc_info:

                # Execute the code to be tested
                result = cpc.stop(wait_for_completion=wait_for_completion)

            exc = exc_info.value
            assert exc.http_status == exp_error.http_status
            assert exc.reason == exp_error.reason
        else:

            # Execute the code to be tested
            result = cpc.stop(wait_for_completion=wait_for_completion)

            if wait_for_completion:
                assert result is None
            else:
                raise NotImplemented

            cpc.pull_full_properties()
            status = cpc.properties['status']
            assert status == exp_status

    @pytest.mark.parametrize(
        "wait_for_completion", [True]
    )
    @pytest.mark.parametrize(
        "cpc_name, exp_error", [
            (CPC1_NAME, HTTPError_409_4),
            (CPC2_NAME, None),
            (CPC3_NAME, None),
        ]
    )
    def test_import_profiles(self, cpc_name, exp_error, wait_for_completion):
        """Test Cpc.import_profiles()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        self.add_cpc(cpc_name)

        cpc = self.client.cpcs.find(name=cpc_name)
        profile_area = 1

        if exp_error:
            with pytest.raises(HTTPError) as exc_info:

                # Execute the code to be tested
                result = cpc.import_profiles(
                    profile_area, wait_for_completion=wait_for_completion)

            exc = exc_info.value
            assert exc.http_status == exp_error.http_status
            assert exc.reason == exp_error.reason
        else:

            # Execute the code to be tested
            result = cpc.import_profiles(
                profile_area, wait_for_completion=wait_for_completion)

            if wait_for_completion:
                assert result is None
            else:
                raise NotImplemented

    @pytest.mark.parametrize(
        "wait_for_completion", [True]
    )
    @pytest.mark.parametrize(
        "cpc_name, exp_error", [
            (CPC1_NAME, HTTPError_409_4),
            (CPC2_NAME, None),
            (CPC3_NAME, None),
        ]
    )
    def test_export_profiles(self, cpc_name, exp_error, wait_for_completion):
        """Test Cpc.export_profiles()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        self.add_cpc(cpc_name)

        cpc = self.client.cpcs.find(name=cpc_name)
        profile_area = 1

        if exp_error:
            with pytest.raises(HTTPError) as exc_info:

                # Execute the code to be tested
                result = cpc.export_profiles(
                    profile_area, wait_for_completion=wait_for_completion)

            exc = exc_info.value
            assert exc.http_status == exp_error.http_status
            assert exc.reason == exp_error.reason
        else:

            # Execute the code to be tested
            result = cpc.export_profiles(
                profile_area, wait_for_completion=wait_for_completion)

            if wait_for_completion:
                assert result is None
            else:
                raise NotImplemented

    @pytest.mark.parametrize(
        "cpc_name, exp_error", [
            (CPC1_NAME, None),
            (CPC2_NAME, HTTPError_409_5),
            (CPC3_NAME, HTTPError_409_5),
        ]
    )
    def test_get_wwpns(self, cpc_name, exp_error):
        """Test Cpc.get_wwpns()."""

        # Add a faked CPC
        faked_cpc = self.add_cpc(cpc_name)

        faked_fcp1 = faked_cpc.adapters.add({
            'object-id': 'fake-fcp1-oid',
            # object-uri is automatically set
            'parent': faked_cpc.uri,
            'class': 'adapter',
            'name': 'fake-fcp1-name',
            'description': 'FCP #1 in CPC #1',
            'status': 'active',
            'type': 'fcp',
            'port-count': 1,
            'adapter-id': '12F',
            # network-port-uris is automatically set when adding port
        })

        faked_port11 = faked_fcp1.ports.add({
            'element-id': 'fake-port11-oid',
            # element-uri is automatically set
            'parent': faked_fcp1.uri,
            'class': 'storage-port',
            'index': 0,
            'name': 'fake-port11-name',
            'description': 'FCP #1 Port #1',
        })

        faked_part1 = faked_cpc.partitions.add({
            'object-id': 'fake-part1-oid',
            # object-uri is automatically set
            'parent': faked_cpc.uri,
            'class': 'partition',
            'name': 'fake-part1-name',
            'description': 'Partition #1',
            'status': 'active',
        })

        faked_hba1 = faked_part1.hbas.add({
            'element-id': 'fake-hba1-oid',
            # element-uri is automatically set
            'parent': faked_part1.uri,
            'class': 'hba',
            'name': 'fake-hba1-name',
            'description': 'HBA #1 in Partition #1',
            'wwpn': 'AABBCCDDEC000082',
            'adapter-port-uri': faked_port11.uri,
            'device-number': '012F',
        })

        faked_part2 = faked_cpc.partitions.add({
            'object-id': 'fake-part2-oid',
            # object-uri is automatically set
            'parent': faked_cpc.uri,
            'class': 'partition',
            'name': 'fake-part2-name',
            'description': 'Partition #2',
            'status': 'active',
        })

        faked_hba2 = faked_part2.hbas.add({
            'element-id': 'fake-hba2-oid',
            # element-uri is automatically set
            'parent': faked_part2.uri,
            'class': 'hba',
            'name': 'fake-hba2-name',
            'description': 'HBA #2 in Partition #2',
            'wwpn': 'AABBCCDDEC000084',
            'adapter-port-uri': faked_port11.uri,
            'device-number': '012E',
        })

        cpc = self.client.cpcs.find(name=cpc_name)
        partitions = cpc.partitions.list()

        if exp_error:
            with pytest.raises(HTTPError) as exc_info:

                # Execute the code to be tested
                wwpn_list = cpc.get_wwpns(partitions)

            exc = exc_info.value
            assert exc.http_status == exp_error.http_status
            assert exc.reason == exp_error.reason
        else:

            # Execute the code to be tested
            wwpn_list = cpc.get_wwpns(partitions)

            exp_wwpn_list = [
                {'wwpn': faked_hba1.properties['wwpn'],
                 'partition-name': faked_part1.properties['name'],
                 'adapter-id': faked_fcp1.properties['adapter-id'],
                 'device-number': faked_hba1.properties['device-number']},
                {'wwpn': faked_hba2.properties['wwpn'],
                 'partition-name': faked_part2.properties['name'],
                 'adapter-id': faked_fcp1.properties['adapter-id'],
                 'device-number': faked_hba2.properties['device-number']},
            ]
            assert wwpn_list == exp_wwpn_list
