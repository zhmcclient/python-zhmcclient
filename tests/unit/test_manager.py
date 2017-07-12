#!/usr/bin/env python
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
Unit tests for _manager module.
"""

from __future__ import absolute_import, print_function

import unittest
from datetime import datetime
import time
import warnings

from zhmcclient import BaseResource, BaseManager, Session, NotFound, \
    NoUniqueMatch
from zhmcclient._manager import _NameUriCache


class MyResource(BaseResource):
    """
    A derived resource for testing purposes.

    It is only needed because BaseManager needs it; it is not subject
    of test in this unit test module.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, manager, uri, name=None, properties=None):
        super(MyResource, self).__init__(manager, uri, name, properties)


class MyManager(BaseManager):
    """
    A derived resource manager for testing the (abstract) BaseManager class.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, session):
        super(MyManager, self).__init__(
            resource_class=MyResource,
            class_name='myresource',
            session=session,
            parent=None,  # a top-level resource
            base_uri='/api/myresources/',
            oid_prop='fake_object_id',
            uri_prop='fake_uri_prop',
            name_prop='fake_name_prop',
            query_props=[])
        self._list_resources = []  # resources to return in list()
        self._list_called = 0  # number of calls to list()

    def list(self, full_properties=False, filter_args=None):
        # This mocked implementation does its work based upon the
        # _list_resources instance variable, and then applies client-side
        # filtering on top of it.
        result_list = []
        for res in self._list_resources:
            if not filter_args or self._matches_filters(res, filter_args):
                result_list.append(res)
        self._list_called += 1
        return result_list


class Manager1Tests(unittest.TestCase):
    """
    Tests for the BaseManager class with one resource.
    """

    def setUp(self):
        self.session = Session(host='fake-host', userid='fake-user',
                               password='fake-pw')
        self.manager = MyManager(self.session)
        self.resource_uri = "/api/fake-uri-1"
        self.resource_name = "fake-name-1"
        self.resource = MyResource(
            self.manager, uri=self.resource_uri,
            properties={
                self.manager._name_prop: self.resource_name,
                "other": "fake-other-1",
            })
        self.manager._list_resources = [self.resource]

    def test_repr(self):
        """Test BaseManager.__repr__()."""
        manager = self.manager

        repr_str = repr(manager)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        self.assertRegexpMatches(
            repr_str,
            r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.format(
                classname=manager.__class__.__name__,
                id=id(manager)))

    def test_init_properties(self):
        """Test BaseManager properties after initialization."""

        self.assertEqual(self.manager.resource_class, MyResource)
        self.assertEqual(self.manager.session, self.session)
        self.assertEqual(self.manager.parent, None)

    def test_invalidate_cache(self):
        """Test invalidate_cache()."""
        filter_args = {self.manager._name_prop: self.resource_name}

        # Populate the cache by finding a resource by name.
        self.manager.find(**filter_args)
        self.assertEqual(self.manager._list_called, 1)

        # Check that on the second find by name, list() is not called again.
        self.manager.find(**filter_args)
        self.assertEqual(self.manager._list_called, 1)

        # Invalidate the cache via invalidate_cache().
        self.manager.invalidate_cache()

        # Check that on the third find by name, list() is called again, because
        # the cache had been invalidated.
        self.manager.find(**filter_args)
        self.assertEqual(self.manager._list_called, 2)

    def test_flush(self):
        """Test flush() and verify that it raises a DeprecationWarning."""
        filter_args = {self.manager._name_prop: self.resource_name}

        # Populate the cache by finding a resource by name.
        self.manager.find(**filter_args)
        self.assertEqual(self.manager._list_called, 1)

        # Check that on the second find by name, list() is not called again.
        self.manager.find(**filter_args)
        self.assertEqual(self.manager._list_called, 1)

        # Invalidate the cache via flush().
        with warnings.catch_warnings(record=True) as wngs:
            warnings.simplefilter("always")
            self.manager.flush()
        self.assertEqual(len(wngs), 1)
        wng = wngs[0]
        self.assertTrue(issubclass(wng.category, DeprecationWarning),
                        "Unexpected warnings class: %s" % wng.category)

        # Check that on the third find by name, list() is called again, because
        # the cache had been invalidated.
        self.manager.find(**filter_args)
        self.assertEqual(self.manager._list_called, 2)

    def test_list_not_implemented(self):
        """Test that BaseManager.list() raises NotImplementedError."""
        manager = BaseManager(
            resource_class=MyResource,
            class_name='myresource',
            session=self.session,
            parent=None,  # a top-level resource
            base_uri='/api/myresources/',
            oid_prop='fake_object_id',
            uri_prop='fake_uri_prop',
            name_prop='fake_name_prop',
            query_props=[])

        with self.assertRaises(NotImplementedError):
            manager.list()


class Manager2Tests(unittest.TestCase):
    """
    Tests for the BaseManager class with two resources.
    """

    def setUp(self):
        self.session = Session(host='fake-host', userid='fake-user',
                               password='fake-pw')
        self.manager = MyManager(self.session)
        self.resource1 = MyResource(
            self.manager,
            uri="/api/fake-uri-1",
            properties={
                self.manager._name_prop: "fake-name-1",
                "other": "fake-other-1",
                "same": "fake-same",
                "int_other": 23,
                "int_same": 42,
            })
        self.resource2 = MyResource(
            self.manager,
            uri="/api/fake-uri-2",
            properties={
                self.manager._name_prop: "fake-name-2",
                "other": "fake-other-2",
                "same": "fake-same",
                "int_other": 24,
                "int_same": 42,
            })
        self.manager._list_resources = [self.resource1, self.resource2]

    def test_findall_name_none(self):
        """Test BaseManager.findall() with no resource matching by the name
        resource property."""
        filter_args = {self.manager._name_prop: "not-exists"}

        resources = self.manager.findall(**filter_args)

        self.assertEqual(len(resources), 0)

    def test_findall_name_one(self):
        """Test BaseManager.findall() with one resource matching by the name
        resource property."""
        filter_args = {self.manager._name_prop: self.resource2.name}

        resources = self.manager.findall(**filter_args)

        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].uri, self.resource2.uri)
        self.assertEqual(resources[0].name, self.resource2.name)

    def test_findall_str_none(self):
        """Test BaseManager.findall() with no resource matching by a
        string-typed (non-name) resource property."""

        resources = self.manager.findall(other="not-exists")

        self.assertEqual(len(resources), 0)

    def test_findall_str_one(self):
        """Test BaseManager.findall() with one resource matching by a
        string-typed (non-name) resource property."""

        resources = self.manager.findall(other="fake-other-2")

        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].uri, self.resource2.uri)
        self.assertEqual(resources[0].name, self.resource2.name)

    def test_findall_str_one_and(self):
        """Test BaseManager.findall() with one resource matching by two
        string-typed (non-name) resource properties (which get ANDed)."""

        resources = self.manager.findall(same="fake-same",
                                         other="fake-other-2")

        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].uri, self.resource2.uri)
        self.assertEqual(resources[0].name, self.resource2.name)

    def test_findall_str_two(self):
        """Test BaseManager.findall() with two resources matching by a
        string-typed (non-name) resource property."""

        resources = self.manager.findall(same="fake-same")

        self.assertEqual(len(resources), 2)
        self.assertEqual(set([res.uri for res in resources]),
                         set([self.resource1.uri, self.resource2.uri]))

    def test_findall_str_two_or(self):
        """Test BaseManager.findall() with two resources matching by a
        list of string-typed (non-name) resource properties (which get
        ORed)."""

        resources = self.manager.findall(other=["fake-other-1",
                                                "fake-other-2"])

        self.assertEqual(len(resources), 2)
        self.assertEqual(set([res.uri for res in resources]),
                         set([self.resource1.uri, self.resource2.uri]))

    def test_findall_int_none(self):
        """Test BaseManager.findall() with no resource matching by a
        integer-typed resource property."""

        resources = self.manager.findall(int_other=815)

        self.assertEqual(len(resources), 0)

    def test_findall_int_one(self):
        """Test BaseManager.findall() with one resource matching by a
        integer-typed resource property."""

        resources = self.manager.findall(int_other=24)

        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].uri, self.resource2.uri)
        self.assertEqual(resources[0].name, self.resource2.name)

    def test_findall_int_two(self):
        """Test BaseManager.findall() with two resources matching by a
        integer-typed resource property."""

        resources = self.manager.findall(int_same=42)

        self.assertEqual(len(resources), 2)
        self.assertEqual(set([res.uri for res in resources]),
                         set([self.resource1.uri, self.resource2.uri]))

    def test_find_name_none(self):
        """Test BaseManager.find() with no resource matching by the name
        resource property."""
        filter_args = {self.manager._name_prop: "not-exists"}

        with self.assertRaises(NotFound):
            self.manager.find(**filter_args)

    def test_find_name_one(self):
        """Test BaseManager.find() with one resource matching by the name
        resource property."""
        filter_args = {self.manager._name_prop: self.resource2.name}

        resource = self.manager.find(**filter_args)

        self.assertEqual(resource.uri, self.resource2.uri)
        self.assertEqual(resource.name, self.resource2.name)

    def test_find_str_none(self):
        """Test BaseManager.find() with no resource matching by a
        string-typed (non-name) resource property."""
        with self.assertRaises(NotFound):

            self.manager.find(other="not-exists")

    def test_find_str_one(self):
        """Test BaseManager.find() with one resource matching by a
        string-typed (non-name) resource property."""

        resource = self.manager.find(other="fake-other-2")

        self.assertEqual(resource.uri, self.resource2.uri)
        self.assertEqual(resource.name, self.resource2.name)

    def test_find_str_two(self):
        """Test BaseManager.find() with two resources matching by a
        string-typed (non-name) resource property."""
        with self.assertRaises(NoUniqueMatch):

            self.manager.find(same="fake-same")

    def test_find_int_none(self):
        """Test BaseManager.find() with no resource matching by a
        string-typed (non-name) resource property."""
        with self.assertRaises(NotFound):

            self.manager.find(int_other=815)

    def test_find_int_one(self):
        """Test BaseManager.find() with one resource matching by a
        string-typed (non-name) resource property."""

        resource = self.manager.find(int_other=24)

        self.assertEqual(resource.uri, self.resource2.uri)
        self.assertEqual(resource.name, self.resource2.name)

    def test_find_int_two(self):
        """Test BaseManager.find() with two resources matching by a
        string-typed (non-name) resource property."""
        with self.assertRaises(NoUniqueMatch):

            self.manager.find(int_same=42)

    def test_find_by_name_none(self):
        """Test BaseManager.find_by_name() with no resource matching by the
        name resource property."""

        with self.assertRaises(NotFound):
            self.manager.find_by_name("not-exists")

    def test_find_by_name_one(self):
        """Test BaseManager.find_by_name() with one resource matching by the
        name resource property."""

        resource = self.manager.find_by_name(self.resource2.name)

        self.assertEqual(resource.uri, self.resource2.uri)
        self.assertEqual(resource.name, self.resource2.name)


class NameUriCacheTests(unittest.TestCase):
    """All tests for the _NameUriCache class."""

    def assertDatetimeNear(self, dt1, dt2, max_delta=0.1):
        delta = abs(dt2 - dt1).total_seconds()
        if delta > max_delta:
            self.fail(
                "Datetime values are %s s apart, maximum is %s s" %
                (delta, max_delta))

    def setUp(self):
        self.session = Session(host='fake-host', userid='fake-user',
                               password='fake-pw')
        self.manager = MyManager(self.session)
        self.resource1_uri = "/api/fake-uri-1"
        self.resource1_name = "fake-name-1"
        self.resource1 = MyResource(
            self.manager, uri=self.resource1_uri,
            properties={
                self.manager._name_prop: self.resource1_name,
                "other": "fake-other-1"
            })
        self.resource2_uri = "/api/fake-uri-2"
        self.resource2_name = "fake-name-2"
        self.resource2 = MyResource(
            self.manager, uri=self.resource2_uri,
            properties={
                self.manager._name_prop: self.resource2_name,
                "other": "fake-other-2"
            })
        self.all_names = {self.resource1_name, self.resource2_name}
        self.manager._list_resources = [self.resource1, self.resource2]

        self.timetolive = 1.0  # seconds
        self.cache = _NameUriCache(self.manager, self.timetolive)
        self.created = datetime.now()

    def test_initial(self):
        """Test initial cache state."""

        self.assertEqual(self.cache._manager, self.manager)
        self.assertEqual(self.cache._timetolive, self.timetolive)
        self.assertEqual(self.cache._uris, {})
        self.assertDatetimeNear(self.cache._invalidated, self.created)

    def test_get_no_invalidate(self):
        """Tests for get() without auto-invalidating the cache."""

        # Check that accessing an existing resource name that is not yet in the
        # cache brings all resources into the cache and causes list() to be
        # called once.
        resource1_uri = self.cache.get(self.resource1_name)
        self.assertEqual(resource1_uri, self.resource1.uri)
        self.assertEqual(set(self.cache._uris.keys()), self.all_names)
        self.assertEqual(self.manager._list_called, 1)

        # Check that on the second access of the same name, list() is not
        # called again.
        resource1_uri = self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)

    def test_get_non_existing(self):
        """Tests for get() of a non-existing entry."""

        # Check that accessing a non-existing resource name raises an
        # exception, but has populated the cache.
        with self.assertRaises(NotFound):
            self.cache.get('non-existing')
        self.assertEqual(set(self.cache._uris.keys()), self.all_names)
        self.assertEqual(self.manager._list_called, 1)

    def test_get_auto_invalidate(self):
        """Tests for get() with auto-invalidating the cache."""

        # Populate the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertDatetimeNear(self.cache._invalidated, self.created)

        # Check that on the second access of the same name, list() is not
        # called again.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)

        # Wait until the time-to-live has safely passed.
        time.sleep(self.timetolive + 0.2)

        # Check that on the third access of the same name, list() is called
        # again, because the cache now has auto-invalidated.
        self.cache.get(self.resource1_name)
        invalidated = datetime.now()
        self.assertEqual(self.manager._list_called, 2)
        self.assertDatetimeNear(self.cache._invalidated, invalidated)

    def test_get_manual_invalidate(self):
        """Tests for get() and manual invalidate()."""

        # Populate the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertDatetimeNear(self.cache._invalidated, self.created)

        # Check that on the second access of the same name, list() is not
        # called again.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)

        # Manually invalidate the cache.
        self.cache.invalidate()
        invalidated = datetime.now()
        self.assertDatetimeNear(self.cache._invalidated, invalidated)
        self.assertEqual(self.cache._uris, {})

        # Check that on the third access of the same name, list() is called
        # again, because the cache has been invalidated.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 2)
        self.assertEqual(set(self.cache._uris.keys()), self.all_names)

    def test_refresh_empty(self):
        """Test refresh() on an empty cache."""

        # Refresh the cache and check that this invalidates it and
        # re-populates it.
        self.cache.refresh()
        refreshed = datetime.now()
        self.assertDatetimeNear(self.cache._invalidated, refreshed)
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(set(self.cache._uris.keys()), self.all_names)

    def test_refresh_populated(self):
        """Test refresh() on a fully populated cache."""

        # Populate the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertDatetimeNear(self.cache._invalidated, self.created)

        # Refresh the cache and check that this invalidates it and
        # re-populates it.
        self.cache.refresh()
        refreshed = datetime.now()
        self.assertDatetimeNear(self.cache._invalidated, refreshed)
        self.assertEqual(self.manager._list_called, 2)
        self.assertEqual(set(self.cache._uris.keys()), self.all_names)

    def test_delete_existing(self):
        """Test delete() of an existing cache entry, and re-accessing it."""

        # Populate the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertDatetimeNear(self.cache._invalidated, self.created)

        # Delete an existing cache entry and check that the entry is now gone.
        self.cache.delete(self.resource1_name)
        self.assertEqual(set(self.cache._uris.keys()), {self.resource2_name})

        # Re-access the deleted entry, and check that list() is called again
        # to get that entry into the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 2)
        self.assertEqual(set(self.cache._uris.keys()), self.all_names)

    def test_delete_non_existing(self):
        """Test delete() of a non-existing cache entry."""

        # Populate the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertDatetimeNear(self.cache._invalidated, self.created)

        # Delete a non-existing cache entry and check that no exception is
        # raised and that the cache still contains the same entries.
        self.cache.delete('non-existing')
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(set(self.cache._uris.keys()), self.all_names)

    def test_delete_none(self):
        """Test delete() of `None`."""

        # Populate the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertDatetimeNear(self.cache._invalidated, self.created)

        # Delete `None` and check that no exception is raised and that the
        # cache still contains the same entries.
        self.cache.delete(None)
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(set(self.cache._uris.keys()), self.all_names)

    def test_update_from_empty(self):
        """Test update_from() on an empty cache."""

        resource3_uri = "/api/fake-uri-3"
        resource3_name = "fake-name-3"
        resource3 = MyResource(
            self.manager, uri=resource3_uri,
            properties={
                self.manager._name_prop: resource3_name,
            })
        resource4_uri = "/api/fake-uri-4"
        resource4_name = "fake-name-4"
        resource4 = MyResource(
            self.manager, uri=resource4_uri,
            properties={
                self.manager._name_prop: resource4_name,
            })

        # Update the cache from these two resources check that they are now in
        # the cache (and that list() has not been called)
        self.cache.update_from([resource3, resource4])
        self.assertEqual(self.manager._list_called, 0)
        self.assertEqual(set(self.cache._uris.keys()),
                         {resource3_name, resource4_name})

    def test_update_from_populated_modify_name(self):
        """Test update_from() on a populated cache and modify the URI of one
        existing entry."""

        resource3_uri = "/api/fake-uri-3"
        resource3_name = "fake-name-3"
        resource3 = MyResource(
            self.manager, uri=resource3_uri,
            properties={
                self.manager._name_prop: resource3_name,
            })
        resource2_new_uri = "/api/fake-new-uri-2"
        resource2_new = MyResource(
            self.manager, uri=resource2_new_uri,
            properties={
                self.manager._name_prop: self.resource2_name,
            })

        # Populate the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(set(self.cache._uris.keys()),
                         {self.resource1_name, self.resource2_name})

        # Update the cache from these two resources check that they are now in
        # the cache (and that list() has not been called again).
        self.cache.update_from([resource3, resource2_new])
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(
            set(self.cache._uris.keys()),
            {self.resource1_name, self.resource2_name, resource3_name})

        # Access the modified entry, and check that the entry has changed
        # (and that list() has not been called again).
        resource2_uri = self.cache.get(self.resource2_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(resource2_uri, resource2_new_uri)

    def test_update_empty(self):
        """Test update() on an empty cache."""

        resource3_uri = "/api/fake-uri-3"
        resource3_name = "fake-name-3"

        # Update the cache, to get the entry added.
        self.cache.update(resource3_name, resource3_uri)
        self.assertEqual(self.manager._list_called, 0)

        # Access the new entry, and check the entry (and that list() has not
        # been called).
        act_resource3_uri = self.cache.get(resource3_name)
        self.assertEqual(self.manager._list_called, 0)
        self.assertEqual(act_resource3_uri, resource3_uri)

    def test_update_empty_empty(self):
        """Test update() on an empty cache with an empty resource name."""

        resource3_uri = "/api/fake-uri-3"
        resource3_name = ""

        # Update the cache with the empty resource name, and check that no
        # exception is raised and that the cache is still empty.
        self.cache.update(resource3_name, resource3_uri)
        self.assertEqual(self.cache._uris, {})
        self.assertEqual(self.manager._list_called, 0)

    def test_update_empty_none(self):
        """Test update() on an empty cache with a `None` resource name."""

        resource3_uri = "/api/fake-uri-3"
        resource3_name = None

        # Update the cache with the empty resource name, and check that no
        # exception is raised and that the cache is still empty.
        self.cache.update(resource3_name, resource3_uri)
        self.assertEqual(self.cache._uris, {})
        self.assertEqual(self.manager._list_called, 0)

    def test_update_populated_new(self):
        """Test update() on a populated cache with a new entry."""

        resource3_uri = "/api/fake-uri-3"
        resource3_name = "fake-name-3"

        # Populate the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(set(self.cache._uris.keys()),
                         {self.resource1_name, self.resource2_name})

        # Update the cache, to get the new entry added.
        self.cache.update(resource3_name, resource3_uri)
        self.assertEqual(self.manager._list_called, 1)

        # Access the new entry, and check the entry (and that list() has not
        # been called).
        act_resource3_uri = self.cache.get(resource3_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(act_resource3_uri, resource3_uri)

    def test_update_populated_modify(self):
        """Test update() on a populated cache by modifying an existing
        entry."""

        resource2_new_uri = "/api/fake-new-uri-2"

        # Populate the cache.
        self.cache.get(self.resource1_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(set(self.cache._uris.keys()),
                         {self.resource1_name, self.resource2_name})

        # Update the cache, to get the existing entry modified.
        self.cache.update(self.resource2_name, resource2_new_uri)
        self.assertEqual(self.manager._list_called, 1)

        # Access the new entry, and check the entry (and that list() has not
        # been called again).
        act_resource2_uri = self.cache.get(self.resource2_name)
        self.assertEqual(self.manager._list_called, 1)
        self.assertEqual(act_resource2_uri, resource2_new_uri)
