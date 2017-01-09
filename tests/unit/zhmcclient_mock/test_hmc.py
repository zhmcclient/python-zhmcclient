#!/usr/bin/env python
# Copyright 2016 IBM Corp. All Rights Reserved.
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
Unit tests for _hmc module of the zhmcclient_mock package.
"""

from __future__ import absolute_import, print_function

import unittest

from zhmcclient_mock._hmc import Hmc, CpcManager, Cpc, Adapter, Port


class HmcTests(unittest.TestCase):
    """All tests for the zhmcclient_mock._hmc.Hmc class."""

    def test_hmc(self):

        # the function to be tested:
        hmc = Hmc('fake-host', '2.13.1')

        self.assertEqual(hmc.host, 'fake-host')
        self.assertEqual(hmc.api_version, '2.13.1')
        self.assertIsInstance(hmc.cpcs, CpcManager)

        # the function to be tested:
        cpcs = hmc.cpcs.list()

        self.assertEqual(len(cpcs), 0)

    def test_hmc_1_cpc(self):
        hmc = Hmc('fake-host', '2.13.1')

        cpc1_in_props = {'name': 'cpc1'}

        # the function to be tested:
        cpc1 = hmc.cpcs.add({'name': 'cpc1'})

        cpc1_out_props = cpc1_in_props.copy()
        cpc1_out_props.update({
            'object-id': cpc1.oid,
            'object-uri': cpc1.uri,
        })

        # the function to be tested:
        cpcs = hmc.cpcs.list()

        self.assertEqual(len(cpcs), 1)
        self.assertEqual(cpcs[0], cpc1)

        self.assertIsInstance(cpc1, Cpc)
        self.assertEqual(cpc1.properties, cpc1_out_props)
        self.assertEqual(cpc1.manager, hmc.cpcs)

    def test_hmc_2_cpcs(self):
        hmc = Hmc('fake-host', '2.13.1')

        cpc1_in_props = {'name': 'cpc1'}

        # the function to be tested:
        cpc1 = hmc.cpcs.add(cpc1_in_props)

        cpc1_out_props = cpc1_in_props.copy()
        cpc1_out_props.update({
            'object-id': cpc1.oid,
            'object-uri': cpc1.uri,
        })

        cpc2_in_props = {'name': 'cpc2'}

        # the function to be tested:
        cpc2 = hmc.cpcs.add(cpc2_in_props)

        cpc2_out_props = cpc2_in_props.copy()
        cpc2_out_props.update({
            'object-id': cpc2.oid,
            'object-uri': cpc2.uri,
        })

        # the function to be tested:
        cpcs = hmc.cpcs.list()

        self.assertEqual(len(cpcs), 2)
        # We expect the order of addition to be maintained:
        self.assertEqual(cpcs[0], cpc1)
        self.assertEqual(cpcs[1], cpc2)

        self.assertIsInstance(cpc1, Cpc)
        self.assertEqual(cpc1.properties, cpc1_out_props)
        self.assertEqual(cpc1.manager, hmc.cpcs)

        self.assertIsInstance(cpc2, Cpc)
        self.assertEqual(cpc2.properties, cpc2_out_props)
        self.assertEqual(cpc2.manager, hmc.cpcs)

    # TODO: Add test cases for:
    #    osa1 = cpc1.adapters.add({'adapter-family': 'osa'})
    #    osa1_1 = osa1.ports.add({'name': 'fake-osa1-port1'})
    #    manager.remove() for all types
    #    manager attributes for all types

    def test_res_dict(self):
        hmc = Hmc('fake-host', '2.13.1')

        cpc1_in_props = {'name': 'cpc1'}
        adapter1_in_props = {'name': 'osa1'}
        port1_in_props = {'name': 'osa1_1'}

        rd = {
            'cpcs': [
                {
                    'properties': cpc1_in_props,
                    'adapters': [
                        {
                            'properties': adapter1_in_props,
                            'ports': [
                                {'properties': port1_in_props},
                            ],
                        },
                    ],
                },
            ]
        }

        # the function to be tested:
        hmc.add_resources(rd)

        cpcs = hmc.cpcs.list()

        self.assertEqual(len(cpcs), 1)

        cpc1 = cpcs[0]
        cpc1_out_props = cpc1_in_props.copy()
        cpc1_out_props.update({
            'object-id': cpc1.oid,
            'object-uri': cpc1.uri,
        })
        self.assertIsInstance(cpc1, Cpc)
        self.assertEqual(cpc1.properties, cpc1_out_props)
        self.assertEqual(cpc1.manager, hmc.cpcs)

        cpc1_adapters = cpc1.adapters.list()

        self.assertEqual(len(cpc1_adapters), 1)

        adapter1 = cpc1_adapters[0]
        adapter1_out_props = adapter1_in_props.copy()
        adapter1_out_props.update({
            'object-id': adapter1.oid,
            'object-uri': adapter1.uri,
        })
        self.assertIsInstance(adapter1, Adapter)
        self.assertEqual(adapter1.properties, adapter1_out_props)
        self.assertEqual(adapter1.manager, cpc1.adapters)

        adapter1_ports = adapter1.ports.list()

        self.assertEqual(len(adapter1_ports), 1)

        port1 = adapter1_ports[0]
        port1_out_props = port1_in_props.copy()
        port1_out_props.update({
            'element-id': port1.oid,
            'element-uri': port1.uri,
        })
        self.assertIsInstance(port1, Port)
        self.assertEqual(port1.properties, port1_out_props)
        self.assertEqual(port1.manager, adapter1.ports)


if __name__ == '__main__':
    unittest.main()
