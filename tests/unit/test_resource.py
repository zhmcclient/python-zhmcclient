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
Unit tests for _resource module.
"""

from __future__ import absolute_import, print_function

import unittest
import time

from zhmcclient import BaseResource, BaseManager


class MyResource(BaseResource):
    """
    A derived resource for testing the (abstract) BaseResource class.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, manager, uri, properties):
        super(MyResource, self).__init__(manager, uri, properties,
                                         uri_prop='fake-uri-prop',
                                         name_prop='fake-name-prop')


class MyManager(BaseManager):
    """
    A derived resource manager for testing purposes.

    It is only needed because BaseResource needs it; it is not subject
    of test in this unit test module.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, parent=None):
        super(MyManager, self).__init__(MyResource, parent)

    def list(self, full_properties=False):
        pass  # to avoid warning about unimplemented abstract method.


class ResourceTestCase(unittest.TestCase):
    """
    Base class for all tests in this file.
    """

    def setUp(self):
        self.mgr = MyManager()
        self.uri = "/api/resource/deadbeef-beef-beef-beef-deadbeefbeef"
        self.uri_prop = 'fake-uri-prop'
        self.name_prop = 'fake-name-prop'

    def assert_properties(self, resource, exp_props):
        """
        Assert that the properties of a resource object are as expected.
        """

        # Check that the properties member is a dict
        self.assertTrue(isinstance(resource.properties, dict))

        # Verify that the resource properties are as expected
        self.assertEqual(len(resource.properties), len(exp_props))
        for key, value in exp_props.items():
            self.assertEqual(resource.properties[key], value)


class InitTests(ResourceTestCase):
    """Test BaseResource initialization."""

    def test_empty(self):
        """Test with an empty set of input properties."""
        init_props = {}
        res_props = {
            self.uri_prop: self.uri,
        }

        res = MyResource(self.mgr, self.uri, init_props)

        self.assertTrue(res.manager is self.mgr)
        self.assertEqual(res.uri, self.uri)
        self.assert_properties(res, res_props)
        self.assertTrue(int(time.time()) - res.properties_timestamp <= 1)
        self.assertEqual(res.full_properties, False)
        self.assertTrue(repr(res).startswith(res.__class__.__name__ + '('))

    def test_simple(self):
        """Test with a simple set of input properties."""
        init_props = {
            'prop1': 'abc',
            'prop2': 100042
        }
        res_props = {
            self.uri_prop: self.uri,
            'prop1': 'abc',
            'prop2': 100042
        }

        res = MyResource(self.mgr, self.uri, init_props)

        self.assertTrue(res.manager is self.mgr)
        self.assertEqual(res.uri, self.uri)
        self.assert_properties(res, res_props)
        self.assertTrue(int(time.time()) - res.properties_timestamp <= 1)
        self.assertEqual(res.full_properties, False)

    def test_prop_case(self):
        """Test case sensitivity for the input properties."""
        init_props = {
            'prop1': 'abc',
            'Prop1': 100042,
        }
        res_props = {
            self.uri_prop: self.uri,
            'prop1': 'abc',
            'Prop1': 100042,
        }

        res = MyResource(self.mgr, self.uri, init_props)

        self.assertTrue(res.manager is self.mgr)
        self.assertEqual(res.uri, self.uri)
        self.assert_properties(res, res_props)
        self.assertTrue(int(time.time()) - res.properties_timestamp <= 1)
        self.assertEqual(res.full_properties, False)

    def test_invalid_type(self):
        """Test that input properties with an invalid type fail."""
        init_props = 42
        try:

            MyResource(self.mgr, self.uri, init_props)

        except TypeError:
            pass
        else:
            self.fail("TypeError was not raised when initializing resource "
                      "with invalid properties: %r" % init_props)


class PropertySetTests(ResourceTestCase):
    """Test BaseResource by setting properties."""

    def test_add_to_empty(self):
        """Test setting a property in a resource object with no properties."""
        init_props = {}
        set_props = {
            'prop1': 'abc',
            'prop2': 100042,
        }
        res_props = {
            self.uri_prop: self.uri,
            'prop1': 'abc',
            'prop2': 100042,
        }

        res = MyResource(self.mgr, self.uri, init_props)

        for key, value in set_props.items():
            res.properties[key] = value

        self.assert_properties(res, res_props)

    def test_replace_one_add_one(self):
        """Test replacing and adding a property in a resource object."""
        init_props = {
            'prop1': 42,
        }
        set_props = {
            'prop1': 'abc',
            'prop2': 100042,
        }
        res_props = {
            self.uri_prop: self.uri,
            'prop1': 'abc',
            'prop2': 100042,
        }

        res = MyResource(self.mgr, self.uri, init_props)

        for key, value in set_props.items():
            res.properties[key] = value

        self.assert_properties(res, res_props)


class PropertyDelTests(ResourceTestCase):
    """Test BaseResource by deleting properties."""

    def test_del_one(self):
        """Test deleting a property in a resource object."""
        init_props = {
            'prop1': 'abc',
            'prop2': 100042,
        }
        del_keys = ('prop1',)
        res_props = {
            self.uri_prop: self.uri,
            'prop2': 100042,
        }

        res = MyResource(self.mgr, self.uri, init_props)

        for key in del_keys:
            del res.properties[key]

        self.assert_properties(res, res_props)

    def test_del_all_input(self):
        """Test deleting all input properties in a resource object."""
        init_props = {
            'prop1': 'abc',
            'prop2': 100042,
        }
        del_keys = ('prop1', 'prop2')
        res_props = {
            self.uri_prop: self.uri,
        }

        res = MyResource(self.mgr, self.uri, init_props)

        for key in del_keys:
            del res.properties[key]

        self.assert_properties(res, res_props)

    def test_del_invalid(self):
        """Test deleting an invalid property in a resource object."""
        init_props = {
            'prop1': 'abc',
            'prop2': 100042,
        }
        org_init_props = dict(init_props)

        res = MyResource(self.mgr, self.uri, init_props)

        invalid_key = 'inv1'
        try:

            del res.properties[invalid_key]

        except KeyError:
            pass
        else:
            self.fail("KeyError was not raised when deleting invalid key %r "
                      "in resource properties %r" %
                      (invalid_key, org_init_props))

    def test_clear(self):
        """Test clearing the properties in a resource object."""
        init_props = {
            'prop1': 'abc',
            'prop2': 100042,
        }

        res = MyResource(self.mgr, self.uri, init_props)

        res.properties.clear()

        self.assertEqual(len(res.properties), 0)


if __name__ == '__main__':
    unittest.main()
