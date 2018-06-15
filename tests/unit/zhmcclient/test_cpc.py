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
import re
import copy

from zhmcclient import Client, Cpc, HTTPError
from zhmcclient_mock import FakedSession
from tests.common.utils import assert_resources


# Object IDs and names of our faked CPCs:
CPC1_NAME = 'cpc 1'  # z13s in DPM mode
CPC1_OID = 'cpc1-oid'
CPC1_MAX_CRYPTO_DOMAINS = 40  # Crypto Express5S on a z13s
CPC2_NAME = 'cpc 2'  # z13s in classic mode
CPC2_OID = 'cpc2-oid'
CPC3_NAME = 'cpc 3'  # zEC12
CPC3_OID = 'cpc3-oid'
CPC4_NAME = 'cpc 4'  # z14-ZR1 in DPM mode
CPC4_OID = 'cpc4-oid'

HTTPError_404_1 = HTTPError({'http-status': 404, 'reason': 1})
HTTPError_409_5 = HTTPError({'http-status': 409, 'reason': 5})
HTTPError_409_4 = HTTPError({'http-status': 409, 'reason': 4})
HTTPError_400_7 = HTTPError({'http-status': 400, 'reason': 7})

# Names of our faked crypto adapters:
CRYPTO1_NAME = 'crypto 1'
CRYPTO2_NAME = 'crypto 2'

CPC1_UNUSED_CRYPTO_DOMAINS = list(range(4, CPC1_MAX_CRYPTO_DOMAINS))

GET_FREE_CRYPTO_DOMAINS_ENVIRONMENTS = {
    'env0-example': {
        'desc': "The example from the description of method "
        "Cpc.get_free_crypto_domains()",
        'cpc_name': CPC1_NAME,
        'adapter_names': [
            CRYPTO1_NAME,
            CRYPTO2_NAME,
        ],
        'partitions': [
            {
                'name': 'part-A',
                'adapter_names': [
                    CRYPTO1_NAME,
                ],
                'domain_configs': [
                    {'domain-index': 0, 'access-mode': 'control-usage'},
                    {'domain-index': 1, 'access-mode': 'control'},
                    # We leave domain index 4 and higher untouched
                ],
            },
            {
                'name': 'part-B',
                'adapter_names': [
                    CRYPTO2_NAME,
                ],
                'domain_configs': [
                    {'domain-index': 0, 'access-mode': 'control'},
                    {'domain-index': 1, 'access-mode': 'control-usage'},
                    {'domain-index': 2, 'access-mode': 'control-usage'},
                    # We leave domain index 4 and higher untouched
                ],
            },
            {
                'name': 'part-C',
                'adapter_names': [
                    CRYPTO1_NAME,
                    CRYPTO2_NAME,
                ],
                'domain_configs': [
                    {'domain-index': 0, 'access-mode': 'control'},
                    {'domain-index': 1, 'access-mode': 'control'},
                    {'domain-index': 3, 'access-mode': 'control-usage'},
                    # We leave domain index 4 and higher untouched
                ],
            },
        ]
    },
    'env1-ocdu': {
        'desc': "Overlapped control of domains, but disjoint usage "
        "on all adapters",
        'cpc_name': CPC1_NAME,
        'adapter_names': [
            CRYPTO1_NAME,
            CRYPTO2_NAME,
        ],
        'partitions': [
            {
                'name': 'part-0',
                'adapter_names': [
                    CRYPTO1_NAME,
                    CRYPTO2_NAME,
                ],
                'domain_configs': [
                    {'domain-index': 0, 'access-mode': 'control-usage'},
                    {'domain-index': 1, 'access-mode': 'control'},
                    {'domain-index': 2, 'access-mode': 'control'},
                    {'domain-index': 3, 'access-mode': 'control'},
                    # We leave domain index 4 and higher untouched
                ],
            },
            {
                'name': 'part-1',
                'adapter_names': [
                    CRYPTO1_NAME,
                    CRYPTO2_NAME,
                ],
                'domain_configs': [
                    {'domain-index': 1, 'access-mode': 'control-usage'},
                    # We leave domain index 4 and higher untouched
                ],
            },
        ]
    },
    'env2-dcdu': {
        'desc': "Disjoint control and usage of domains on all adapters",
        'cpc_name': CPC1_NAME,
        'adapter_names': [
            CRYPTO1_NAME,
            CRYPTO2_NAME,
        ],
        'partitions': [
            {
                'name': 'part-0',
                'adapter_names': [
                    CRYPTO1_NAME,
                    CRYPTO2_NAME,
                ],
                'domain_configs': [
                    {'domain-index': 0, 'access-mode': 'control-usage'},
                    {'domain-index': 1, 'access-mode': 'control'},
                    # We leave domain index 4 and higher untouched
                ],
            },
            {
                'name': 'part-2',
                'adapter_names': [
                    CRYPTO1_NAME,
                    CRYPTO2_NAME,
                ],
                'domain_configs': [
                    {'domain-index': 2, 'access-mode': 'control-usage'},
                    {'domain-index': 3, 'access-mode': 'control'},
                    # We leave domain index 4 and higher untouched
                ],
            },
        ]
    },
    'env3-dcou': {
        'desc': "Disjoint control of domains, but overlapping usage on all "
        "adapters (this prevents activating the partitions at the same time)",
        'cpc_name': CPC1_NAME,
        'adapter_names': [
            CRYPTO1_NAME,
            CRYPTO2_NAME,
        ],
        'partitions': [
            {
                'name': 'part-1',
                'adapter_names': [
                    CRYPTO1_NAME,
                    CRYPTO2_NAME,
                ],
                'domain_configs': [
                    {'domain-index': 1, 'access-mode': 'control-usage'},
                    {'domain-index': 2, 'access-mode': 'control'},
                    # We leave domain index 4 and higher untouched
                ],
            },
            {
                'name': 'part-2',
                'adapter_names': [
                    CRYPTO1_NAME,
                    CRYPTO2_NAME,
                ],
                'domain_configs': [
                    {'domain-index': 1, 'access-mode': 'control-usage'},
                    {'domain-index': 3, 'access-mode': 'control'},
                    # We leave domain index 4 and higher untouched
                ],
            },
        ]
    },
}

GET_FREE_CRYPTO_DOMAINS_SUCCESS_TESTCASES = [
    # (env_name, parm_adapter_names, exp_free_domains)

    # test cases for environment 'env0-example':
    (
        'env0-example',
        [],
        None,
    ),
    (
        'env0-example',
        [CRYPTO1_NAME],
        [1, 2] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env0-example',
        [CRYPTO2_NAME],
        [0] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env0-example',
        [CRYPTO1_NAME, CRYPTO2_NAME],
        [] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env0-example',
        None,
        [] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),

    # test cases for environment 'env1-ocdu':
    (
        'env1-ocdu',
        [],
        None,
    ),
    (
        'env1-ocdu',
        [CRYPTO1_NAME],
        [2, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env1-ocdu',
        [CRYPTO2_NAME],
        [2, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env1-ocdu',
        [CRYPTO1_NAME, CRYPTO2_NAME],
        [2, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env1-ocdu',
        None,
        [2, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),

    # test cases for environment 'env2-dcdu':
    (
        'env2-dcdu',
        [],
        None,
    ),
    (
        'env2-dcdu',
        [CRYPTO1_NAME],
        [1, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env2-dcdu',
        [CRYPTO2_NAME],
        [1, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env2-dcdu',
        [CRYPTO1_NAME, CRYPTO2_NAME],
        [1, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env2-dcdu',
        None,
        [1, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),

    # test cases for environment 'env3-dcou':
    (
        'env3-dcou',
        [],
        None,
    ),
    (
        'env3-dcou',
        [CRYPTO1_NAME],
        [0, 2, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env3-dcou',
        [CRYPTO2_NAME],
        [0, 2, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env3-dcou',
        [CRYPTO1_NAME, CRYPTO2_NAME],
        [0, 2, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
    (
        'env3-dcou',
        None,
        [0, 2, 3] + CPC1_UNUSED_CRYPTO_DOMAINS,
    ),
]


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
                'description': 'CPC #1 (z13s in DPM mode)',
                'status': 'active',
                'dpm-enabled': True,
                'is-ensemble-member': False,
                'iml-mode': 'dpm',
                'machine-type': '2965',
            })
        elif cpc_name == CPC2_NAME:
            faked_cpc = self.session.hmc.cpcs.add({
                'object-id': CPC2_OID,
                # object-uri is set up automatically
                'parent': None,
                'class': 'cpc',
                'name': CPC2_NAME,
                'description': 'CPC #2 (z13s in classic mode)',
                'status': 'operating',
                'dpm-enabled': False,
                'is-ensemble-member': False,
                'iml-mode': 'lpar',
                'machine-type': '2965',
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
        elif cpc_name == CPC4_NAME:
            faked_cpc = self.session.hmc.cpcs.add({
                'object-id': CPC4_OID,
                # object-uri is set up automatically
                'parent': None,
                'class': 'cpc',
                'name': CPC4_NAME,
                'description': 'CPC #4 (z14-ZR1 in DPM mode)',
                'status': 'active',
                'dpm-enabled': True,
                'is-ensemble-member': False,
                'iml-mode': 'dpm',
                'machine-type': '3607',
                'available-features-list': [],
            })
        else:
            raise ValueError("Invalid value for cpc_name: %s" % cpc_name)
        return faked_cpc

    def add_crypto_adapter(self, faked_cpc, adapter_name):
        """Add a faked crypto adapter to a faked CPC."""

        if adapter_name == CRYPTO1_NAME:
            faked_crypto_adapter = faked_cpc.adapters.add({
                'object-id': adapter_name + '-oid',
                # object-uri is automatically set
                'parent': faked_cpc.uri,
                'class': 'adapter',
                'name': adapter_name,
                'status': 'active',
                'type': 'crypto',
                'adapter-family': 'crypto',
                'detected-card-type': 'crypto-express-5s',
                'crypto-type': 'ep11-coprocessor',
                'crypto-number': 1,
                'adapter-id': '12C',
            })
        elif adapter_name == CRYPTO2_NAME:
            faked_crypto_adapter = faked_cpc.adapters.add({
                'object-id': adapter_name + '-oid',
                # object-uri is automatically set
                'parent': faked_cpc.uri,
                'class': 'adapter',
                'name': adapter_name,
                'status': 'active',
                'type': 'crypto',
                'adapter-family': 'crypto',
                'detected-card-type': 'crypto-express-5s',
                'crypto-type': 'cca-coprocessor',
                'crypto-number': 2,
                'adapter-id': '12D',
            })
        else:
            raise ValueError("Invalid value for crypto_name: %s" %
                             adapter_name)
        return faked_crypto_adapter

    def add_partition(self, faked_cpc, part_name):
        """Add a faked partition to a faked CPC, with standard properties."""

        faked_partition = faked_cpc.partitions.add({
            'object-id': part_name + '-oid',
            # object-uri is automatically set
            'parent': faked_cpc.uri,
            'class': 'partition',
            'name': part_name,
            'status': 'active',
            'ifl-processors': 2,
            'initial-memory': 1024,
            'maximum-memory': 1024,
        })
        return faked_partition

    def test_cpcmanager_initial_attrs(self):
        """Test initial attributes of CpcManager."""

        cpc_mgr = self.client.cpcs

        # Verify all public properties of the manager object
        assert cpc_mgr.resource_class is Cpc
        assert cpc_mgr.session is self.session
        assert cpc_mgr.parent is None
        assert cpc_mgr.client is self.client

    # TODO: Test for CpcManager.__repr__()

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
    def test_cpcmanager_list_full_properties(
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
    def test_cpcmanager_list_filter_args(self, filter_args, exp_names):
        """Test CpcManager.list() with filter_args."""

        # Add two faked CPCs
        self.add_cpc(CPC1_NAME)
        self.add_cpc(CPC2_NAME)

        cpc_mgr = self.client.cpcs

        # Execute the code to be tested
        cpcs = cpc_mgr.list(filter_args=filter_args)

        assert len(cpcs) == len(exp_names)
        if exp_names:
            names = [ad.properties['name'] for ad in cpcs]
            assert set(names) == set(exp_names)

    # TODO: Test for initial Cpc attributes (lpars, partitions, adapters,
    #       virtual_switches, reset_activation_profiles,
    #       image_activation_profiles, load_activation_profiles, )

    def test_cpc_repr(self):
        """Test Cpc.__repr__()."""

        # Add a faked CPC
        faked_cpc = self.add_cpc(CPC1_NAME)

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=faked_cpc.name)

        # Execute the code to be tested
        repr_str = repr(cpc)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=cpc.__class__.__name__,
                               id=id(cpc)),
                        repr_str)

    @pytest.mark.parametrize(
        "cpc_name, exp_dpm_enabled", [
            (CPC1_NAME, True),
            (CPC2_NAME, False),
            (CPC3_NAME, False),
        ]
    )
    def test_cpc_dpm_enabled(self, cpc_name, exp_dpm_enabled):
        """Test Cpc.dpm_enabled."""

        # Add a faked CPC
        self.add_cpc(cpc_name)

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)

        # Execute the code to be tested
        dpm_enabled = cpc.dpm_enabled

        assert dpm_enabled == exp_dpm_enabled

    # TODO: Test for Cpc.maximum_active_partitions

    @pytest.mark.parametrize(
        "desc, cpc_name, available_features, feature_name, "
        "exp_feature_enabled, exp_exc", [
            (
                "No feature support on the CPC",
                CPC1_NAME,
                None,
                'fake-feature1', None, ValueError()
            ),
            (
                "Feature not available on the CPC (empty feature list)",
                CPC4_NAME,
                [],
                'fake-feature1', None, ValueError()
            ),
            (
                "Feature not available on the CPC (one other feature avail)",
                CPC4_NAME,
                [
                    dict(name='fake-feature-foo', state=True),
                ],
                'fake-feature1', None, ValueError()
            ),
            (
                "Feature disabled (the only feature available)",
                CPC4_NAME,
                [
                    dict(name='fake-feature1', state=False),
                ],
                'fake-feature1', False, None
            ),
            (
                "Feature enabled (the only feature available)",
                CPC4_NAME,
                [
                    dict(name='fake-feature1', state=True),
                ],
                'fake-feature1', True, None
            ),
        ]
    )
    def test_cpc_feature_enabled(
            self, desc, cpc_name, available_features, feature_name,
            exp_feature_enabled, exp_exc):
        """Test Cpc.feature_enabled()."""

        # Add a faked CPC
        faked_cpc = self.add_cpc(cpc_name)

        # Set up the firmware feature list
        if available_features is not None:
            faked_cpc.properties['available-features-list'] = \
                available_features

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)

        if exp_exc:
            with pytest.raises(exp_exc.__class__):

                # Execute the code to be tested
                cpc.feature_enabled(feature_name)

        else:

            # Execute the code to be tested
            act_feature_enabled = cpc.feature_enabled(feature_name)

            assert act_feature_enabled == exp_feature_enabled

    @pytest.mark.parametrize(
        "desc, cpc_name, available_features, exp_exc", [
            (
                "No feature support on the CPC",
                CPC1_NAME,
                None,
                ValueError()
            ),
            (
                "Feature not available on the CPC (empty feature list)",
                CPC4_NAME,
                [],
                None
            ),
            (
                "Feature not available on the CPC (one other feature avail)",
                CPC4_NAME,
                [
                    dict(name='fake-feature-foo', state=True),
                ],
                None
            ),
            (
                "Feature disabled (the only feature available)",
                CPC4_NAME,
                [
                    dict(name='fake-feature1', state=False),
                ],
                None
            ),
            (
                "Feature enabled (the only feature available)",
                CPC4_NAME,
                [
                    dict(name='fake-feature1', state=True),
                ],
                None
            ),
        ]
    )
    def test_cpc_feature_info(
            self, desc, cpc_name, available_features, exp_exc):
        """Test Cpc.feature_info()."""

        # Add a faked CPC
        faked_cpc = self.add_cpc(cpc_name)

        # Set up the firmware feature list
        if available_features is not None:
            faked_cpc.properties['available-features-list'] = \
                available_features

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)

        if exp_exc:
            with pytest.raises(exp_exc.__class__):

                # Execute the code to be tested
                cpc.feature_info()

        else:

            # Execute the code to be tested
            act_features = cpc.feature_info()

            assert act_features == available_features

    @pytest.mark.parametrize(
        "input_props", [
            {},
            {'description': 'New CPC description'},
            {'acceptable-status': ['active', 'degraded'],
             'description': 'New CPC description'},
        ]
    )
    def test_cpc_update_properties(self, input_props):
        """Test Cpc.update_properties()."""

        # Add a faked CPC
        faked_cpc = self.add_cpc(CPC1_NAME)

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=faked_cpc.name)

        cpc.pull_full_properties()
        saved_properties = copy.deepcopy(cpc.properties)

        # Execute the code to be tested
        cpc.update_properties(properties=input_props)

        # Verify that the resource object already reflects the property
        # updates.
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in cpc.properties
            prop_value = cpc.properties[prop_name]
            assert prop_value == exp_prop_value

        # Refresh the resource object and verify that the resource object
        # still reflects the property updates.
        cpc.pull_full_properties()
        for prop_name in saved_properties:
            if prop_name in input_props:
                exp_prop_value = input_props[prop_name]
            else:
                exp_prop_value = saved_properties[prop_name]
            assert prop_name in cpc.properties
            prop_value = cpc.properties[prop_name]
            assert prop_value == exp_prop_value

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
    def test_cpc_start(self, cpc_name, initial_status, exp_status, exp_error,
                       wait_for_completion):
        """Test Cpc.start()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        faked_cpc = self.add_cpc(cpc_name)

        # Set initial status of the CPC for this test
        faked_cpc.properties['status'] = initial_status

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)

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
    def test_cpc_stop(self, cpc_name, initial_status, exp_status, exp_error,
                      wait_for_completion):
        """Test Cpc.stop()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        faked_cpc = self.add_cpc(cpc_name)

        # Set initial status of the CPC for this test
        faked_cpc.properties['status'] = initial_status

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)

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
    def test_cpc_import_profiles(self, cpc_name, exp_error,
                                 wait_for_completion):
        """Test Cpc.import_profiles()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        self.add_cpc(cpc_name)

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)
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
    def test_cpc_export_profiles(self, cpc_name, exp_error,
                                 wait_for_completion):
        """Test Cpc.export_profiles()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        self.add_cpc(cpc_name)

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)
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
    def test_cpc_get_wwpns(self, cpc_name, exp_error):
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

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)
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

    @pytest.mark.parametrize(
        "env_name, parm_adapter_names, exp_free_domains",
        GET_FREE_CRYPTO_DOMAINS_SUCCESS_TESTCASES)
    def test_cpc_get_free_crypto_domains(self, env_name, parm_adapter_names,
                                         exp_free_domains):
        """Test Cpc.get_free_crypto_domains()."""

        env = GET_FREE_CRYPTO_DOMAINS_ENVIRONMENTS[env_name]

        cpc_name = env['cpc_name']

        # Add the faked CPC
        faked_cpc = self.add_cpc(cpc_name)

        # Add the faked crypto adapters
        faked_adapters = {}  # faked crypto adapters by name
        for adapter_name in env['adapter_names']:
            faked_adapter = self.add_crypto_adapter(faked_cpc, adapter_name)
            faked_adapters[adapter_name] = faked_adapter

        # Add the faked partitions
        for part in env['partitions']:
            faked_part = self.add_partition(faked_cpc, part['name'])

            part_adapter_uris = [faked_adapters[name].uri
                                 for name in part['adapter_names']]
            part_domain_configs = part['domain_configs']
            crypto_config = {
                'crypto-adapter-uris': part_adapter_uris,
                'crypto-domain-configurations': part_domain_configs,
            }
            faked_part.properties['crypto-configuration'] = crypto_config

        # Set up input parameters
        cpc = self.client.cpcs.find(name=cpc_name)
        if parm_adapter_names is None:
            parm_adapters = None
        else:
            parm_adapters = [cpc.adapters.find(name=name)
                             for name in parm_adapter_names]

        # Execute the code to be tested
        act_free_domains = cpc.get_free_crypto_domains(parm_adapters)

        # Verify the result
        assert act_free_domains == exp_free_domains

    @pytest.mark.parametrize(
        "wait_for_completion", [True]
    )
    @pytest.mark.parametrize(
        "cpc_name, power_saving, exp_error", [
            (CPC1_NAME, 'high-performance', None),
            (CPC1_NAME, 'low-power', None),
            (CPC1_NAME, 'custom', None),
            (CPC1_NAME, None, HTTPError_400_7),
            (CPC1_NAME, 'invalid', HTTPError_400_7),
        ]
    )
    def test_cpc_set_power_save(self, cpc_name, power_saving, exp_error,
                                wait_for_completion):
        """Test Cpc.set_power_save()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        self.add_cpc(cpc_name)

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)

        if exp_error:
            with pytest.raises(HTTPError) as exc_info:

                # Execute the code to be tested
                result = cpc.set_power_save(
                    power_saving, wait_for_completion=wait_for_completion)

            exc = exc_info.value
            assert exc.http_status == exp_error.http_status
            assert exc.reason == exp_error.reason
        else:

            # Execute the code to be tested
            result = cpc.set_power_save(
                power_saving, wait_for_completion=wait_for_completion)

            if wait_for_completion:
                assert result is None
            else:
                raise NotImplemented

            cpc.pull_full_properties()

            assert cpc.properties['cpc-power-saving'] == power_saving
            assert cpc.properties['cpc-power-saving-state'] == power_saving
            assert cpc.properties['zcpc-power-saving'] == power_saving
            assert cpc.properties['zcpc-power-saving-state'] == power_saving

    @pytest.mark.parametrize(
        "wait_for_completion", [True]
    )
    @pytest.mark.parametrize(
        "cpc_name, power_capping_state, power_cap, exp_error", [
            (CPC1_NAME, 'disabled', None, None),
            (CPC1_NAME, 'enabled', 20000, None),
            (CPC1_NAME, 'enabled', None, HTTPError_400_7),
            (CPC1_NAME, None, None, HTTPError_400_7),
            (CPC1_NAME, 'invalid', None, HTTPError_400_7),
        ]
    )
    def test_cpc_set_power_capping(self, cpc_name, power_capping_state,
                                   power_cap, exp_error, wait_for_completion):
        """Test Cpc.set_power_capping()."""

        # wait_for_completion=False not implemented in mock support:
        assert wait_for_completion is True

        # Add a faked CPC
        self.add_cpc(cpc_name)

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)

        if exp_error:
            with pytest.raises(HTTPError) as exc_info:

                # Execute the code to be tested
                result = cpc.set_power_capping(
                    power_capping_state, power_cap,
                    wait_for_completion=wait_for_completion)

            exc = exc_info.value
            assert exc.http_status == exp_error.http_status
            assert exc.reason == exp_error.reason
        else:

            # Execute the code to be tested
            result = cpc.set_power_capping(
                power_capping_state, power_cap,
                wait_for_completion=wait_for_completion)

            if wait_for_completion:
                assert result is None
            else:
                raise NotImplemented

            cpc.pull_full_properties()

            assert cpc.properties['cpc-power-capping-state'] == \
                power_capping_state
            assert cpc.properties['cpc-power-cap-current'] == power_cap
            assert cpc.properties['zcpc-power-capping-state'] == \
                power_capping_state
            assert cpc.properties['zcpc-power-cap-current'] == power_cap

    @pytest.mark.parametrize(
        "cpc_name, energy_props", [
            (CPC1_NAME, {
                'cpc-power-consumption': 14423,
                'cpc-power-rating': 28000,
                'cpc-power-save-allowed': 'allowed',
                'cpc-power-saving': 'high-performance',
                'cpc-power-saving-state': 'high-performance',
                'zcpc-ambient-temperature': 26.7,
                'zcpc-dew-point': 8.4,
                'zcpc-exhaust-temperature': 29.0,
                'zcpc-heat-load': 49246,
                'zcpc-heat-load-forced-air': 10370,
                'zcpc-heat-load-water': 38877,
                'zcpc-humidity': 31,
                'zcpc-maximum-potential-heat-load': 57922,
                'zcpc-maximum-potential-power': 16964,
                'zcpc-power-consumption': 14423,
                'zcpc-power-rating': 28000,
                'zcpc-power-save-allowed': 'under-group-control',
                'zcpc-power-saving': 'high-performance',
                'zcpc-power-saving-state': 'high-performance',
            }),
        ]
    )
    def test_cpc_get_energy_management_properties(
            self, cpc_name, energy_props):
        """Test Cpc.get_energy_management_properties()."""

        # Add a faked CPC
        faked_cpc = self.add_cpc(cpc_name)
        faked_cpc.properties.update(energy_props)

        cpc_mgr = self.client.cpcs
        cpc = cpc_mgr.find(name=cpc_name)

        # Execute the code to be tested
        act_energy_props = cpc.get_energy_management_properties()

        assert isinstance(act_energy_props, dict)
        cpc.pull_full_properties()

        for p in energy_props:
            exp_value = energy_props[p]

            # Verify returned energy properties
            assert p in act_energy_props
            assert act_energy_props[p] == exp_value

            # Verify consistency of returned energy properties with CPC props
            assert p in cpc.properties
            assert cpc.properties[p] == exp_value
