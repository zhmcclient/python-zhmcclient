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
Unit tests for _manager module.
"""

from __future__ import absolute_import, print_function

import unittest

from zhmcclient._manager import BaseManager
from zhmcclient._resource import BaseResource


class MyResource(BaseResource):
    def __init__(self, manager, uri, name=None, properties=None):
        super(MyResource, self).__init__(manager, uri, name, properties)


class MyManager(BaseManager):
    def __init__(self, parent=None):
        super(MyManager, self).__init__(
            resource_class=MyResource,
            parent=parent,
            uri_prop='object-uri',
            name_prop='name',
            query_props=[])
        self._list_items = []

    def list(self, full_properties=False, filter_args=None):
        # We need to have a quick way to mock this method. This mocked
        # implementation basically uses the _list_items instance variable,
        # and then applies the client-side filtering on top of it.
        result_list = []
        for obj in self._list_items:
            if not filter_args or self._matches_filters(obj, filter_args):
                result_list.append(obj)
        return result_list


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = MyManager()

        self.resource = MyResource(self.manager, "foo-uri",
                                   properties={"name": "foo-name",
                                               "other": "foo-other"})
        self.manager._list_items = [self.resource]

    def test_findall_attribute(self):
        items = self.manager.findall(other="foo-other")
        self.assertIn(self.resource, items)

    def test_findall_attribute_no_result(self):
        items = self.manager.findall(other="not-exists")
        self.assertEqual([], items)

    def test_findall_name(self):
        items = self.manager.findall(name="foo-name")
        self.assertEqual(1, len(items))
        item = items[0]
        self.assertEqual("foo-name", item.properties['name'])
        self.assertEqual("foo-uri", item.properties['object-uri'])

    def test_findall_name_no_result(self):
        items = self.manager.findall(name="not-exists")
        self.assertEqual([], items)
