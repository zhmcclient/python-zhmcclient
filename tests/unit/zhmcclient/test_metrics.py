# Copyright 2017-2018 IBM Corp. All Rights Reserved.
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
Unit tests for _metrics module.
"""

from __future__ import absolute_import, print_function

import pytest
import re

from zhmcclient import Client, MetricsContext, HTTPError, NotFound
from zhmcclient_mock import FakedSession, FakedMetricGroupDefinition
from tests.common.utils import assert_resources


# Object IDs of our faked metrics contexts:
MC1_OID = 'mc1-oid'
MC2_OID = 'mc2-oid'

# Names of our faked metric groups:
MG1_NAME = 'mg1-name'
MG2_NAME = 'mg2-name'

# Base URI for metrics contexts (Object ID will be added to get URI):
MC_BASE_URI = '/api/services/metrics/context/'


class TestMetricsContext(object):
    """All tests for the MetricsContext and MetricsContextManager classes."""

    def setup_method(self):
        """
        Set up a faked session, and add a faked CPC in DPM mode without any
        child resources.
        """

        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

    def add_metricgroupdefinition1(self):
        """Add metric group definition 1."""

        faked_metricgroupdefinition = FakedMetricGroupDefinition(
            name=MG1_NAME,
            types=[
                ('faked-metric11', 'integer-metric'),
                ('faked-metric12', 'string-metric'),
            ]
        )
        self.session.hmc.metrics_contexts.add_metric_group_definition(
            faked_metricgroupdefinition)
        return faked_metricgroupdefinition

    def add_metricgroupdefinition2(self):
        """Add metric group definition 2."""

        faked_metricgroupdefinition = FakedMetricGroupDefinition(
            name=MG2_NAME,
            types=[
                ('faked-metric21', 'boolean-metric'),
            ]
        )
        self.session.hmc.metrics_contexts.add_metric_group_definition(
            faked_metricgroupdefinition)
        return faked_metricgroupdefinition

    def add_metricscontext1(self):
        """Add faked metrics context 1."""

        faked_metricscontext = self.session.hmc.metrics_contexts.add({
            'fake-id': MC1_OID,
            'anticipated-frequency-seconds': 10,
            'metric-groups': [MG1_NAME, MG2_NAME],
        })
        return faked_metricscontext

    def add_metricscontext2(self):
        """Add faked metrics context 2."""

        faked_metricscontext = self.session.hmc.metrics_contexts.add({
            'fake-id': MC2_OID,
            'anticipated-frequency-seconds': 10,
            'metric-groups': [MG1_NAME],
        })
        return faked_metricscontext

    def create_metricscontext1(self):
        """create (non-faked) metrics context 1."""

        mc_props = {
            'anticipated-frequency-seconds': 10,
            'metric-groups': [MG1_NAME, MG2_NAME],
        }
        metricscontext = self.client.metrics_contexts.create(mc_props)
        return metricscontext

    def create_metricscontext2(self):
        """create (non-faked) metrics context 2."""

        mc_props = {
            'anticipated-frequency-seconds': 10,
            'metric-groups': [MG1_NAME],
        }
        metricscontext = self.client.metrics_contexts.create(mc_props)
        return metricscontext

    def test_metricscontextmanager_initial_attrs(self):
        """Test initial attributes of MetricsContextManager."""

        metricscontext_mgr = self.client.metrics_contexts

        # Verify all public properties of the manager object
        assert metricscontext_mgr.resource_class == MetricsContext
        assert metricscontext_mgr.session == self.session
        assert metricscontext_mgr.parent is None
        assert metricscontext_mgr.client == self.client

    # TODO: Test for MetricsContextManager.__repr__()

    @pytest.mark.parametrize(
        "full_properties_kwargs, prop_names", [
            (dict(),
             ['anticipated-frequency-seconds', 'metric-groups']),
            (dict(full_properties=False),
             ['anticipated-frequency-seconds', 'metric-groups']),
            (dict(full_properties=True),
             ['anticipated-frequency-seconds', 'metric-groups']),
        ]
    )
    def test_metricscontextmanager_list_full_properties(
            self, full_properties_kwargs, prop_names):
        """Test MetricsContextManager.list() with full_properties."""

        # Add faked metric groups
        self.add_metricgroupdefinition1()
        self.add_metricgroupdefinition2()

        # Create (non-faked) metrics contexts (list() will only return those)
        metricscontext1 = self.create_metricscontext1()
        metricscontext2 = self.create_metricscontext2()

        exp_metricscontexts = [metricscontext1, metricscontext2]
        metricscontext_mgr = self.client.metrics_contexts

        # Execute the code to be tested
        metricscontexts = metricscontext_mgr.list(**full_properties_kwargs)

        assert_resources(metricscontexts, exp_metricscontexts, prop_names)

    @pytest.mark.parametrize(
        "filter_args, exp_names", [
            ({'object-id': MC1_OID},
             [MG1_NAME]),
            ({'object-id': MC2_OID},
             [MG2_NAME]),
            ({'object-id': [MC1_OID, MC2_OID]},
             [MG1_NAME, MG2_NAME]),
            ({'object-id': [MC1_OID, MC1_OID]},
             [MG1_NAME]),
            ({'object-id': MC1_OID + 'foo'},
             []),
            ({'object-id': [MC1_OID, MC2_OID + 'foo']},
             [MG1_NAME]),
            ({'object-id': [MC2_OID + 'foo', MC1_OID]},
             [MG1_NAME]),
            ({'name': MG1_NAME},
             [MG1_NAME]),
            ({'name': MG2_NAME},
             [MG2_NAME]),
            ({'name': [MG1_NAME, MG2_NAME]},
             [MG1_NAME, MG2_NAME]),
            ({'name': MG1_NAME + 'foo'},
             []),
            ({'name': [MG1_NAME, MG2_NAME + 'foo']},
             [MG1_NAME]),
            ({'name': [MG2_NAME + 'foo', MG1_NAME]},
             [MG1_NAME]),
            ({'name': [MG1_NAME, MG1_NAME]},
             [MG1_NAME]),
            ({'name': '.*part 1'},
             [MG1_NAME]),
            ({'name': 'part 1.*'},
             [MG1_NAME]),
            ({'name': 'part .'},
             [MG1_NAME, MG2_NAME]),
            ({'name': '.art 1'},
             [MG1_NAME]),
            ({'name': '.+'},
             [MG1_NAME, MG2_NAME]),
            ({'name': 'part 1.+'},
             []),
            ({'name': '.+part 1'},
             []),
            ({'name': MG1_NAME,
              'object-id': MC1_OID},
             [MG1_NAME]),
            ({'name': MG1_NAME,
              'object-id': MC1_OID + 'foo'},
             []),
            ({'name': MG1_NAME + 'foo',
              'object-id': MC1_OID},
             []),
            ({'name': MG1_NAME + 'foo',
              'object-id': MC1_OID + 'foo'},
             []),
        ]
    )
    @pytest.mark.skip  # TODO: Test for MetricsContextManager.list() w/ filter
    def test_metricscontextmanager_list_filter_args(
            self, filter_args, exp_names):
        """Test MetricsContextManager.list() with filter_args."""

        # Add faked metric groups
        self.add_metricgroupdefinition1()
        self.add_metricgroupdefinition2()

        # Create (non-faked) metrics contexts (list() will only return those)
        self.create_metricscontext1()
        self.create_metricscontext2()

        metricscontext_mgr = self.client.metrics_contexts

        # Execute the code to be tested
        metricscontexts = metricscontext_mgr.list(filter_args=filter_args)

        names = [p.properties['name'] for p in metricscontexts]
        assert set(names) == set(exp_names)

    @pytest.mark.parametrize(
        "input_props, exp_prop_names, exp_exc", [
            ({},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'description': 'fake description X'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-part-x'},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-part-x',
              'initial-memory': 1024},
             None,
             HTTPError({'http-status': 400, 'reason': 5})),
            ({'name': 'fake-part-x',
              'initial-memory': 1024,
              'maximum-memory': 1024},
             ['object-uri', 'name', 'initial-memory', 'maximum-memory'],
             None),
            ({'name': 'fake-part-x',
              'initial-memory': 1024,
              'maximum-memory': 1024,
              'description': 'fake description X'},
             ['object-uri', 'name', 'initial-memory', 'maximum-memory',
              'description'],
             None),
        ]
    )
    @pytest.mark.skip  # TODO: Test for MetricsContextManager.create()
    def test_metricscontextmanager_create(
            self, input_props, exp_prop_names, exp_exc):
        """Test MetricsContextManager.create()."""

        metricscontext_mgr = self.client.metrics_contexts

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                metricscontext = metricscontext_mgr.create(
                    properties=input_props)

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

        else:

            # Execute the code to be tested.
            # Note: the MetricsContext object returned by
            # MetricsContext.create() has the input properties plus
            # 'object-uri'.
            metricscontext = metricscontext_mgr.create(properties=input_props)

            # Check the resource for consistency within itself
            assert isinstance(metricscontext, MetricsContext)
            metricscontext_name = metricscontext.name
            exp_metricscontext_name = metricscontext.properties['name']
            assert metricscontext_name == exp_metricscontext_name
            metricscontext_uri = metricscontext.uri
            exp_metricscontext_uri = metricscontext.properties['object-uri']
            assert metricscontext_uri == exp_metricscontext_uri

            # Check the properties against the expected names and values
            for prop_name in exp_prop_names:
                assert prop_name in metricscontext.properties
                if prop_name in input_props:
                    value = metricscontext.properties[prop_name]
                    exp_value = input_props[prop_name]
                    assert value == exp_value

    @pytest.mark.skip  # TODO: Test for MetricsContextManager.__repr__()
    def test_metricscontext_repr(self):
        """Test MetricsContext.__repr__()."""

        # Add a faked metrics context
        faked_metricscontext = self.add_metricscontext1()

        metricscontext_mgr = self.client.metrics_contexts
        metricscontext = metricscontext_mgr.find(
            name=faked_metricscontext.name)

        # Execute the code to be tested
        repr_str = repr(metricscontext)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=metricscontext.__class__.__name__,
                               id=id(metricscontext)),
                        repr_str)

    @pytest.mark.parametrize(
        "initial_status, exp_exc", [
            ('stopped', None),
            ('terminated', HTTPError({'http-status': 409, 'reason': 1})),
            ('starting', HTTPError({'http-status': 409, 'reason': 1})),
            ('active', HTTPError({'http-status': 409, 'reason': 1})),
            ('stopping', HTTPError({'http-status': 409, 'reason': 1})),
            ('degraded', HTTPError({'http-status': 409, 'reason': 1})),
            ('reservation-error',
             HTTPError({'http-status': 409, 'reason': 1})),
            ('paused', HTTPError({'http-status': 409, 'reason': 1})),
        ]
    )
    @pytest.mark.skip  # TODO: Test for MetricsContext.delete()
    def test_metricscontext_delete(self, initial_status, exp_exc):
        """Test MetricsContext.delete()."""

        # Add a faked metrics context
        faked_metricscontext = self.add_metricscontext1()

        # Set the initial status of the faked metrics context
        faked_metricscontext.properties['status'] = initial_status

        metricscontext_mgr = self.client.metrics_contexts

        metricscontext = metricscontext_mgr.find(
            name=faked_metricscontext.name)

        if exp_exc is not None:

            with pytest.raises(exp_exc.__class__) as exc_info:

                # Execute the code to be tested
                metricscontext.delete()

            exc = exc_info.value
            if isinstance(exp_exc, HTTPError):
                assert exc.http_status == exp_exc.http_status
                assert exc.reason == exp_exc.reason

            # Check that the metrics context still exists
            metricscontext_mgr.find(name=faked_metricscontext.name)

        else:

            # Execute the code to be tested.
            metricscontext.delete()

            # Check that the metrics context no longer exists
            with pytest.raises(NotFound) as exc_info:
                metricscontext_mgr.find(name=faked_metricscontext.name)
