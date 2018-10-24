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
Unit tests for _resource module.
"""

from __future__ import absolute_import, print_function

import time
import re
from collections import OrderedDict

from zhmcclient import BaseResource, BaseManager, Session


class MyResource(BaseResource):
    """
    A derived resource for testing the (abstract) BaseResource class.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, manager, uri, name, properties):
        super(MyResource, self).__init__(manager, uri, name, properties)


class MyManager(BaseManager):
    """
    A derived resource manager for testing purposes.

    It is only needed because BaseResource needs it; it is not subject
    of test in this unit test module.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, session):
        super(MyManager, self).__init__(
            resource_class=MyResource,
            class_name='myresource',
            session=session,
            parent=None,  # a top-level resource
            base_uri='/api/myresources',
            oid_prop='fake-oid-prop',
            uri_prop='fake-uri-prop',
            name_prop='fake-name-prop',
            query_props=['qp1', 'qp2'])

    def list(self, full_properties=False, filter_args=None):
        # We have this method here just to avoid the warning about
        # an unimplemented abstract method. It is not being used in this
        # set of testcases.
        raise NotImplementedError


class ResourceTestCase(object):
    """
    Base class for all tests in this file.
    """

    def setup_method(self):
        self.session = Session(host='fake-host')
        self.mgr = MyManager(self.session)
        self.uri = self.mgr._base_uri + '/deadbeef-beef-beef-beef-deadbeefbeef'
        self.name = "fake-name"
        self.uri_prop = 'fake-uri-prop'  # same as in MyManager
        self.name_prop = 'fake-name-prop'  # same as in MyManager

    def assert_properties(self, resource, exp_props):
        """
        Assert that the properties of a resource object are as expected.
        """

        # Check that the properties member is a dict
        assert isinstance(resource.properties, dict)

        # Verify that the resource properties are as expected
        assert len(resource.properties) == len(exp_props), \
            "Set of properties does not match. Expected {!r}, got {!r}". \
            format(resource.properties.keys(), exp_props.keys())

        for name, exp_value in exp_props.items():
            act_value = resource.properties[name]
            assert act_value == exp_value, \
                "Property {!r} does not match. Expected {!r}, got {!r}". \
                format(name, exp_value, act_value)


class TestInit(ResourceTestCase):
    """Test BaseResource initialization."""

    def test_empty_name(self):
        """Test with an empty set of input properties, with 'name'."""
        init_props = {}
        res_props = {
            self.uri_prop: self.uri,
            self.name_prop: self.name,
        }

        res = MyResource(self.mgr, self.uri, self.name, init_props)

        assert res.manager is self.mgr
        assert res.uri == self.uri
        assert res.name == self.name
        self.assert_properties(res, res_props)
        assert int(time.time()) - res.properties_timestamp <= 1
        assert res.full_properties is False

    def test_empty_no_name(self):
        """Test with an empty set of input properties, without 'name'."""
        init_props = {}
        res_props = {
            self.uri_prop: self.uri,
        }

        res = MyResource(self.mgr, self.uri, None, init_props)

        assert res.manager is self.mgr
        assert res.uri == self.uri
        self.assert_properties(res, res_props)
        assert int(time.time()) - res.properties_timestamp <= 1
        assert res.full_properties is False

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

        res = MyResource(self.mgr, self.uri, None, init_props)

        assert res.manager is self.mgr
        assert res.uri == self.uri
        self.assert_properties(res, res_props)
        assert int(time.time()) - res.properties_timestamp <= 1
        assert res.full_properties is False

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

        res = MyResource(self.mgr, self.uri, None, init_props)

        assert res.manager is self.mgr
        assert res.uri == self.uri
        self.assert_properties(res, res_props)
        assert int(time.time()) - res.properties_timestamp <= 1
        assert res.full_properties is False

    def test_invalid_type(self):
        """Test that input properties with an invalid type fail."""
        init_props = 42
        try:

            MyResource(self.mgr, self.uri, None, init_props)

        except TypeError:
            pass
        else:
            self.fail("TypeError was not raised when initializing resource "
                      "with invalid properties: %r" % init_props)

    def test_str(self):
        """Test BaseResource.__str__()."""
        init_props = {
            'prop1': 'abc',
            'Prop1': 100042,
        }
        resource = MyResource(self.mgr, self.uri, None, init_props)

        str_str = str(resource)

        str_str = str_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s*\(.*'.
                        format(classname=resource.__class__.__name__),
                        str_str)

    def test_repr(self):
        """Test BaseResource.__repr__()."""
        init_props = {
            'prop1': 'abc',
            'Prop1': 100042,
        }
        resource = MyResource(self.mgr, self.uri, None, init_props)

        repr_str = repr(resource)

        repr_str = repr_str.replace('\n', '\\n')
        # We check just the begin of the string:
        assert re.match(r'^{classname}\s+at\s+0x{id:08x}\s+\(\\n.*'.
                        format(classname=resource.__class__.__name__,
                               id=id(resource)),
                        repr_str)


class TestPropertySet(ResourceTestCase):
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

        res = MyResource(self.mgr, self.uri, None, init_props)

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

        res = MyResource(self.mgr, self.uri, None, init_props)

        for key, value in set_props.items():
            res.properties[key] = value

        self.assert_properties(res, res_props)


class TestPropertyDel(ResourceTestCase):
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

        res = MyResource(self.mgr, self.uri, None, init_props)

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

        res = MyResource(self.mgr, self.uri, None, init_props)

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

        res = MyResource(self.mgr, self.uri, None, init_props)

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

        res = MyResource(self.mgr, self.uri, None, init_props)

        res.properties.clear()

        assert len(res.properties) == 0


class TestManagerDivideFilter(ResourceTestCase):
    """Test the _divide_filter_args() method of BaseManager."""

    # Reserved chars are defined in RFC 3986 as gen-delims and sub-delims.
    reserved_chars = [
        ':', '/', '?', '#', '[', ']', '@',  # gen-delims
        '!', '$', '&', "'", '(', ')', '*', '+', ',', ';', '='  # sub-delims
    ]

    # Percent-escapes for the reserved chars, in the same order.
    reserved_escapes = [
        '%3A', '%2F', '%3F', '%23', '%5B', '%5D', '%40',  # gen-delims
        '%21', '%24', '%26', '%27', '%28', '%29', '%2A',  # sub-delims
        '%2B', '%2C', '%3B', '%3D',  # sub-delims
    ]

    def test_none(self):
        """Test with None as filter arguments."""
        filter_args = None

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == ''
        assert cf_args == {}

    def test_empty(self):
        """Test with an empty set of filter arguments."""
        filter_args = {}

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == ''
        assert cf_args == {}

    def test_one_string_qp(self):
        """Test with one string filter argument that is a query parm."""
        filter_args = {'qp1': 'bar'}

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?qp1=bar'
        assert cf_args == {}

    def test_one_string_cf(self):
        """Test with one string filter argument that is a client filter."""
        filter_args = {'foo': 'bar'}

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == ''
        assert cf_args == {'foo': 'bar'}

    def test_one_integer_qp(self):
        """Test with one integer filter argument that is a query parm."""
        filter_args = {'qp2': 42}

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?qp2=42'
        assert cf_args == {}

    def test_one_integer_cf(self):
        """Test with one integer filter argument that is a client filter."""
        filter_args = {'foo': 42}

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == ''
        assert cf_args == {'foo': 42}

    def test_one_str_reserved_val_qp(self):
        """Test with one string filter argument with reserved URI chars in
        its value that is a query parm."""
        char_str = '_'.join(self.reserved_chars)
        escape_str = '_'.join(self.reserved_escapes)
        filter_args = {'qp1': char_str}

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?qp1={}'.format(escape_str)
        assert cf_args == {}

    def test_one_str_reserved_val_cf(self):
        """Test with one string filter argument with reserved URI chars in
        its value that is a client filter."""
        char_str = '_'.join(self.reserved_chars)
        filter_args = {'foo': char_str}

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == ''
        assert cf_args == {'foo': char_str}

    def test_one_str_dash_name_qp(self):
        """Test with one string filter argument with a dash in its name that is
        a query parm."""
        filter_args = {'foo-boo': 'bar'}
        self.mgr._query_props.append('foo-boo')

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?foo-boo=bar'
        assert cf_args == {}

    def test_one_str_reserved_name_qp(self):
        """Test with one string filter argument with reserved URI chars in
        its name that is a query parm."""
        char_str = '_'.join(self.reserved_chars)
        escape_str = '_'.join(self.reserved_escapes)
        filter_args = {char_str: 'bar'}
        self.mgr._query_props.append(char_str)

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?{}=bar'.format(escape_str)
        assert cf_args == {}

    def test_two_qp(self):
        """Test with two filter arguments that are query parms."""
        filter_args = OrderedDict([('qp1', 'bar'), ('qp2', 42)])

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?qp1=bar&qp2=42'
        assert cf_args == {}

    def test_two_qp_cf(self):
        """Test with two filter arguments where one is a query parm and one is
        a client filter."""
        filter_args = OrderedDict([('qp1', 'bar'), ('foo', 42)])

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?qp1=bar'
        assert cf_args == {'foo': 42}

    def test_two_cf_qp(self):
        """Test with two filter arguments where one is a client filter and one
        is a query parm."""
        filter_args = OrderedDict([('foo', 'bar'), ('qp1', 42)])

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?qp1=42'
        assert cf_args == {'foo': 'bar'}

    def test_two_two_qp(self):
        """Test with two filter arguments, one of which is a list of two, and
        both are query parms."""
        filter_args = OrderedDict([('qp1', 'bar'), ('qp2', [42, 7])])

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?qp1=bar&qp2=42&qp2=7'
        assert cf_args == {}

    def test_two_str_reserved_val_qp(self):
        """Test with two filter arguments, one of which is a list of two, and
        has reserved URI chars, and both are query parms."""
        char_str = '_'.join(self.reserved_chars)
        escape_str = '_'.join(self.reserved_escapes)
        filter_args = OrderedDict([('qp1', 'bar'), ('qp2', [42, char_str])])

        parm_str, cf_args = self.mgr._divide_filter_args(filter_args)

        assert parm_str == '?qp1=bar&qp2=42&qp2={}'.format(escape_str)
        assert cf_args == {}
