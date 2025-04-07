# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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

# pylint: disable=protected-access

"""
Unit tests for _resource module.
"""


import time
import re
import random
import threading
from immutable_views import DictView
import pytest

from zhmcclient import BaseResource, BaseManager, Session, Client, \
    CeasedExistence
from zhmcclient._utils import divide_filter_args
from zhmcclient_mock import FakedSession


class MyResource(BaseResource):
    """
    A derived resource for testing the (abstract) BaseResource class.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, manager, uri, name, properties):
        # pylint: disable=useless-super-delegation
        super().__init__(manager, uri, name, properties)


class MyManager(BaseManager):
    """
    A derived resource manager for testing purposes.

    It is only needed because BaseResource needs it; it is not subject
    of test in this unit test module.
    """

    # This init method is not part of the external API, so this testcase may
    # need to be updated if the API changes.
    def __init__(self, session):
        super().__init__(
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


class ResourceTestCase:
    """
    Base class for all tests in this file.
    """

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = Session(host='fake-host')
        self.mgr = MyManager(self.session)
        self.uri = self.mgr._base_uri + '/deadbeef-beef-beef-beef-deadbeefbeef'
        self.name = "fake-name"
        self.uri_prop = 'fake-uri-prop'  # same as in MyManager
        self.name_prop = 'fake-name-prop'  # same as in MyManager

    @staticmethod
    def assert_properties(resource, exp_props):
        """
        Assert that the properties of a resource object are as expected.
        """

        # Check the properties member type
        assert isinstance(resource.properties, DictView)

        # Verify that the resource properties are as expected
        assert len(resource.properties) == len(exp_props), (
            "Set of properties does not match. "
            f"Expected {resource.properties.keys()!r}, "
            f"got {exp_props.keys()!r}")

        for name, exp_value in exp_props.items():
            act_value = resource.properties[name]
            assert act_value == exp_value, (
                f"Property {name!r} does not match. "
                f"Expected {exp_value!r}, got {act_value!r}")


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
            raise AssertionError(
                "TypeError was not raised when initializing resource "
                f"with invalid properties: {init_props!r}")

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
        assert re.match(rf'^{resource.__class__.__name__}\s*\(.*',
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
        assert re.match(
            rf'^{resource.__class__.__name__}\s+at\s+'
            rf'0x{id(resource):08x}\s+\(\\n.*',
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
        }

        res = MyResource(self.mgr, self.uri, None, init_props)

        for key, value in set_props.items():
            # Since zhmcclient 0.31.0, the 'properties' attribute has type
            # DictView which prevents modifications to the dictionary.
            with pytest.raises(TypeError):
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
            'prop1': 42,
        }

        res = MyResource(self.mgr, self.uri, None, init_props)

        for key, value in set_props.items():
            # Since zhmcclient 0.31.0, the 'properties' attribute has type
            # DictView which prevents modifications to the dictionary.
            with pytest.raises(TypeError):
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
            'prop1': 'abc',
            'prop2': 100042,
        }

        res = MyResource(self.mgr, self.uri, None, init_props)

        for key in del_keys:
            # Since zhmcclient 0.31.0, the 'properties' attribute has type
            # DictView which prevents modifications to the dictionary.
            with pytest.raises(TypeError):
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
            'prop1': 'abc',
            'prop2': 100042,
        }

        res = MyResource(self.mgr, self.uri, None, init_props)

        for key in del_keys:
            # Since zhmcclient 0.31.0, the 'properties' attribute has type
            # DictView which prevents modifications to the dictionary.
            with pytest.raises(TypeError):
                del res.properties[key]

        self.assert_properties(res, res_props)

    def test_del_invalid(self):
        """Test deleting an invalid property in a resource object."""
        init_props = {
            'prop1': 'abc',
            'prop2': 100042,
        }
        res_props = {
            self.uri_prop: self.uri,
            'prop1': 'abc',
            'prop2': 100042,
        }

        res = MyResource(self.mgr, self.uri, None, init_props)

        invalid_key = 'inv1'
        # Rejection of deletion is checked byfore invalid key is checked.
        with pytest.raises(TypeError):
            del res.properties[invalid_key]

        self.assert_properties(res, res_props)

    def test_clear(self):
        """Test clearing the properties in a resource object."""
        init_props = {
            'prop1': 'abc',
            'prop2': 100042,
        }
        res_props = {
            self.uri_prop: self.uri,
            'prop1': 'abc',
            'prop2': 100042,
        }

        res = MyResource(self.mgr, self.uri, None, init_props)

        # Since zhmcclient 0.31.0, the 'properties' attribute has type
        # DictView which prevents modifications to the dictionary.
        with pytest.raises(AttributeError):
            res.properties.clear()

        self.assert_properties(res, res_props)


class TestManagerDivideFilter(ResourceTestCase):
    """
    Test the divide_filter_args() utils method (previously in BaseManager).
    """

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

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == []
        assert cf_args == {}

    def test_empty(self):
        """Test with an empty set of filter arguments."""
        filter_args = {}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == []
        assert cf_args == {}

    def test_one_string_qp(self):
        """Test with one string filter argument that is a query parm."""
        filter_args = {'qp1': 'bar'}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == ['qp1=bar']
        assert cf_args == {}

    def test_one_string_cf(self):
        """Test with one string filter argument that is a client filter."""
        filter_args = {'foo': 'bar'}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == []
        assert cf_args == {'foo': 'bar'}

    def test_one_integer_qp(self):
        """Test with one integer filter argument that is a query parm."""
        filter_args = {'qp2': 42}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == ['qp2=42']
        assert cf_args == {}

    def test_one_integer_cf(self):
        """Test with one integer filter argument that is a client filter."""
        filter_args = {'foo': 42}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == []
        assert cf_args == {'foo': 42}

    def test_one_str_reserved_val_qp(self):
        """Test with one string filter argument with reserved URI chars in
        its value that is a query parm."""
        char_str = '_'.join(self.reserved_chars)
        escape_str = '_'.join(self.reserved_escapes)
        filter_args = {'qp1': char_str}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == [f'qp1={escape_str}']
        assert cf_args == {}

    def test_one_str_reserved_val_cf(self):
        """Test with one string filter argument with reserved URI chars in
        its value that is a client filter."""
        char_str = '_'.join(self.reserved_chars)
        filter_args = {'foo': char_str}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == []
        assert cf_args == {'foo': char_str}

    def test_one_str_dash_name_qp(self):
        """Test with one string filter argument with a dash in its name that is
        a query parm."""
        filter_args = {'foo-boo': 'bar'}
        self.mgr._query_props.append('foo-boo')

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == ['foo-boo=bar']
        assert cf_args == {}

    def test_one_str_reserved_name_qp(self):
        """Test with one string filter argument with reserved URI chars in
        its name that is a query parm."""
        char_str = '_'.join(self.reserved_chars)
        escape_str = '_'.join(self.reserved_escapes)
        filter_args = {char_str: 'bar'}
        self.mgr._query_props.append(char_str)

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == [f'{escape_str}=bar']
        assert cf_args == {}

    def test_two_qp(self):
        """Test with two filter arguments that are query parms."""
        filter_args = {'qp1': 'bar', 'qp2': 42}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == ['qp1=bar', 'qp2=42']
        assert cf_args == {}

    def test_two_qp_cf(self):
        """Test with two filter arguments where one is a query parm and one is
        a client filter."""
        filter_args = {'qp1': 'bar', 'foo': 42}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == ['qp1=bar']
        assert cf_args == {'foo': 42}

    def test_two_cf_qp(self):
        """Test with two filter arguments where one is a client filter and one
        is a query parm."""
        filter_args = {'foo': 'bar', 'qp1': 42}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == ['qp1=42']
        assert cf_args == {'foo': 'bar'}

    def test_two_two_qp(self):
        """Test with two filter arguments, one of which is a list of two, and
        both are query parms."""
        filter_args = {'qp1': 'bar', 'qp2': [42, 7]}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == ['qp1=bar', 'qp2=42', 'qp2=7']
        assert cf_args == {}

    def test_two_str_reserved_val_qp(self):
        """Test with two filter arguments, one of which is a list of two, and
        has reserved URI chars, and both are query parms."""
        char_str = '_'.join(self.reserved_chars)
        escape_str = '_'.join(self.reserved_escapes)
        filter_args = {'qp1': 'bar', 'qp2': [42, char_str]}

        parm_str, cf_args = divide_filter_args(
            self.mgr._query_props, filter_args)

        assert parm_str == ['qp1=bar', 'qp2=42', f'qp2={escape_str}']
        assert cf_args == {}


class TestThreadingSerialization(ResourceTestCase):
    """
    Test serialization of resource property update/access.
    """

    def test_serialization_1(self):
        """
        Test serialization of resource property update/access.
        """

        resource = MyResource(self.mgr, self.uri, 'res1', dict(p1=1, p2=1))

        def update():
            for _ in range(0, 10000):
                value = random.randint(1, 100)
                props = dict(p1=value, p2=value)
                resource.update_properties_local(props)

        def get_assert():
            for _ in range(0, 10000):
                value1, value2 = resource.get_properties_local(['p1', 'p2'])
                assert value1 == value2

        threads = []
        for _ in range(0, 10):

            thread = threading.Thread(target=update)
            thread.start()
            threads.append(thread)

            thread = threading.Thread(target=get_assert)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    TESTCASES_GET_PROPERTIES_LOCAL = [
        # Testcases for test_get_properties_local().
        # Each list item is a tuple defining a testcase in the following format:
        # - desc: Testcase description
        # - create_properties: Initial properties for test resource
        # - get_properties: properties parm for tested function
        # - default: default parm for tested function
        # - exp_values: Expected properties returned by tested function
        (
            "Get two properties that exist",
            {
                'p1': 'v1',
                'p2': 'v2',
            },
            ['p1', 'p2'],
            'vd',
            ['v1', 'v2'],
        ),
        (
            "Get two properties that do not exist, using single default value",
            {},
            ['p1', 'p2'],
            'vd',
            ['vd', 'vd'],
        ),
        (
            "Get two properties that do not exist, using two default values",
            {},
            ['p1', 'p2'],
            ['vd1', 'vd2'],
            ['vd1', 'vd2'],
        ),
    ]

    @pytest.mark.parametrize(
        "desc, create_properties, get_properties, default, exp_values",
        TESTCASES_GET_PROPERTIES_LOCAL)
    def test_get_properties_local(
            self, desc, create_properties, get_properties, default, exp_values):
        # pylint: disable=unused-argument
        """
        Test get_properties_local().
        """

        resource = MyResource(self.mgr, self.uri, 'res1', create_properties)

        values = resource.get_properties_local(get_properties, default)

        for i, name in enumerate(get_properties):
            value = values[i]
            exp_value = exp_values[i]

            assert value == exp_value, \
                f"Unexpected property value for '{name}'"


class TestPropertyMethodsMocked:
    """
    All tests of property methods that need mocked resources.
    """

    RESOURCE_OID = 'res-oid'
    RESOURCE_NAME = 'res-name'
    RESOURCE_DESC = 'Resource Description'

    def setup_method(self):
        """
        Setup that is called by pytest before each test method.

        Set up a faked session, and add a faked CPC in DPM mode without any
        child resources.
        """
        # pylint: disable=attribute-defined-outside-init

        self.session = FakedSession('fake-host', 'fake-hmc', '2.13.1', '1.8')
        self.client = Client(self.session)

        self.faked_cpc = self.session.hmc.cpcs.add({
            'object-id': 'fake-cpc1-oid',
            # object-uri is set up automatically
            'parent': None,
            'class': 'cpc',
            'name': 'fake-cpc1-name',
            'description': 'CPC #1 (DPM mode)',
            'status': 'active',
            'dpm-enabled': True,
            'is-ensemble-member': False,
            'iml-mode': 'dpm',
            'machine-type': '2964',  # z13
            'machine-model': 'N10',
        })
        self.cpc = self.client.cpcs.find(name='fake-cpc1-name')

    def add_standard_hipersocket(self):
        """
        Add a standard Hipersocket adapter with one port to the faked HMC.

        Adapter resources do not support the 'properties' query parameter.
        """

        # Adapter properties that will be auto-set:
        # - object-uri
        # - adapter-family
        # - network-port-uris (to empty array)
        faked_hs = self.faked_cpc.adapters.add({
            'object-id': self.RESOURCE_OID,
            'parent': self.faked_cpc.uri,
            'class': 'adapter',
            'name': self.RESOURCE_NAME,
            'description': self.RESOURCE_DESC,
            'status': 'active',
            'type': 'hipersockets',
            'adapter-id': '123',
            'detected-card-type': 'hipersockets',
            'port-count': 1,
            'network-port-uris': [],
            'state': 'online',
            'configured-capacity': 32,
            'used-capacity': 0,
            'allowed-capacity': 32,
            'maximum-total-capacity': 32,
            'physical-channel-status': 'operating',
            'maximum-transmission-unit-size': 56,
        })

        # Port properties that will be auto-set:
        # - element-uri
        # Properties in parent adapter that will be auto-set:
        # - network-port-uris
        faked_hs.ports.add({
            'element-id': 'fake-port1-oid',
            'parent': faked_hs.uri,
            'class': 'network-port',
            'index': 0,
            'name': 'fake-port1-name',
            'description': 'Hipersocket #1 Port #1',
        })
        return faked_hs

    def add_standard_partition(self):
        """
        Add a standard partition.

        Partition resources support the 'properties' query parameter.
        """

        # Partition properties that will be auto-set:
        # - object-uri
        faked_part = self.faked_cpc.partitions.add({
            'object-id': self.RESOURCE_OID,
            'parent': self.faked_cpc.uri,
            'class': 'partition',
            'name': self.RESOURCE_NAME,
            'description': self.RESOURCE_DESC,
            'status': 'stopped',
        })
        return faked_part

    @pytest.mark.parametrize(
        # Indicates whether to delete the resource before test
        "delete", [False, True])
    def test_pull_full_properties(self, delete):
        """
        Test BaseResource.pull_full_properties().
        """
        faked_res = self.add_standard_hipersocket()
        res_mgr = self.cpc.adapters
        resource = res_mgr.find(name=faked_res.name)
        propnames_find = set(resource.properties.keys())
        assert resource.full_properties is False

        if delete:
            # Delete the resource on the HMC, without affecting the state of
            # the local zhmcclient resource object. This simulates some other
            # user who has deleted the resource on the HMC while we have it
            # here as a zhmcclient resource object.
            resource.manager.session.delete(resource.uri)

            with pytest.raises(CeasedExistence):

                # The code to be tested
                resource.pull_full_properties()

        else:

            # The code to be tested
            resource.pull_full_properties()

            assert resource.full_properties is True
            propnames_pull = set(resource.properties.keys())
            assert propnames_pull.issuperset(propnames_find)
            assert dict(resource.properties) == faked_res.properties

    TESTCASES_PULL_PROPERTIES = [
        # Testcases for test_pull_properties().
        # Each list item is a tuple defining a testcase in the following format:
        # - desc: Testcase description
        # - input_kwargs: keyword input parameters for the function
        # - delete: Indicates whether to delete the resource before test
        # - supports_properties: Resource supports 'properties' query parm
        # - exp_propnames: Expected property names in resource after test
        # - exp_full_props: Expected value for full_properties attribute
        # - exp_exc_type: Expected type of exception, or None for success

        (
            "No properties requested (None); "
            "resource exists and does not support 'properties' query parm",
            dict(properties=None),
            False,
            False,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "No properties requested (None); "
            "resource exists and supports 'properties' query parm",
            dict(properties=None),
            False,
            True,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "No properties requested (None); "
            "resource is deleted and does not support 'properties' query parm",
            dict(properties=None),
            True,
            False,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "No properties requested (None); "
            "resource is deleted and supports 'properties' query parm",
            dict(properties=None),
            True,
            True,
            {'name', 'object-uri'},
            False,
            None,
        ),

        (
            "No properties requested (empty list); "
            "resource exists and does not support 'properties' query parm",
            dict(properties=[]),
            False,
            False,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "No properties requested (empty list); "
            "resource exists and supports 'properties' query parm",
            dict(properties=[]),
            False,
            True,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "No properties requested (empty list); "
            "resource is deleted and does not support 'properties' query parm",
            dict(properties=[]),
            True,
            False,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "No properties requested (empty list); "
            "resource is deleted and supports 'properties' query parm",
            dict(properties=[]),
            True,
            True,
            {'name', 'object-uri'},
            False,
            None,
        ),

        (
            "One valid property requested; "
            "resource exists and does not support 'properties' query parm",
            dict(properties=['object-id']),
            False,
            False,
            {'name', 'object-uri', 'object-id'},
            True,
            None,
        ),
        (
            "One valid property requested; "
            "resource exists and supports 'properties' query parm",
            dict(properties=['object-id']),
            False,
            True,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "One valid property requested; "
            "resource is deleted and does not support 'properties' query parm",
            dict(properties=['object-id']),
            True,
            False,
            None,
            None,
            CeasedExistence,
        ),
        (
            "One valid property requested; "
            "resource is deleted and supports 'properties' query parm",
            dict(properties=['object-id']),
            True,
            True,
            None,
            None,
            CeasedExistence,
        ),

        (
            "One invalid property requested; "
            "resource exists and does not support 'properties' query parm",
            dict(properties=['invalid-property']),
            False,
            False,
            {'name', 'object-uri', 'object-id'},
            True,
            None,
        ),
        (
            "One invalid property requested; "
            "resource exists and supports 'properties' query parm",
            dict(properties=['invalid-property']),
            False,
            True,
            {'name', 'object-uri', 'object-id'},
            True,
            None,
        ),
        (
            "One invalid property requested; "
            "resource is deleted and does not support 'properties' query parm",
            dict(properties=['invalid-property']),
            True,
            False,
            None,
            None,
            CeasedExistence,
        ),
        (
            "One invalid property requested; "
            "resource is deleted and supports 'properties' query parm",
            dict(properties=['invalid-property']),
            True,
            True,
            None,
            None,
            CeasedExistence,
        ),
    ]

    @pytest.mark.parametrize(
        "desc, input_kwargs, delete, supports_properties, exp_propnames, "
        "exp_full_props, exp_exc_type",
        TESTCASES_PULL_PROPERTIES)
    def test_pull_properties(
            self, desc, input_kwargs, delete, supports_properties,
            exp_propnames, exp_full_props, exp_exc_type):
        # pylint: disable=unused-argument
        """
        Test BaseResource.pull_properties().
        """
        if supports_properties:
            # Partitions support the properties query parm
            faked_res = self.add_standard_partition()
            res_mgr = self.cpc.partitions
        else:
            # Adapters do not support the properties query parm
            faked_res = self.add_standard_hipersocket()
            res_mgr = self.cpc.adapters
        assert res_mgr.supports_properties == supports_properties

        resource = res_mgr.find(name=faked_res.name)
        assert resource.full_properties is False

        if delete:
            # Delete the resource on the HMC, without affecting the state of
            # the local zhmcclient resource object. This simulates some other
            # user who has deleted the resource on the HMC while we have it
            # here as a zhmcclient resource object.
            resource.manager.session.delete(resource.uri)

        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The code to be tested
                resource.pull_properties(**input_kwargs)

            exc = exc_info.value
            assert isinstance(exc, exp_exc_type)
        else:

            # The code to be tested
            resource.pull_properties(**input_kwargs)

            propnames = set(resource.properties.keys())
            assert propnames.issuperset(exp_propnames)

            assert resource.full_properties == exp_full_props

    TESTCASES_GET_PROPERTY = [
        # Testcases for test_get_property().
        # Each list item is a tuple defining a testcase in the following format:
        # - desc: Testcase description
        # - input_kwargs: keyword input parameters for the function
        # - delete: Indicates whether to delete the resource before test
        # - supports_properties: Resource supports 'properties' query parm
        # - exp_value: Expected return value of the function
        # - exp_propnames: Expected property names in resource after test
        # - exp_full_props: Expected value for full_properties attribute
        # - exp_exc_type: Expected type of exception, or None for success

        (
            "Valid locally existing property requested; "
            "resource exists and does not support 'properties' query parm",
            dict(name='name'),
            False,
            False,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "Valid locally existing property requested; "
            "resource exists and supports 'properties' query parm",
            dict(name='name'),
            False,
            True,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "Valid locally existing property requested; "
            "resource is deleted and does not support 'properties' query parm",
            dict(name='name'),
            True,
            False,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "Valid locally existing property requested; "
            "resource is deleted and supports 'properties' query parm",
            dict(name='name'),
            True,
            True,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),

        (
            "Valid not locally existing property requested; "
            "resource exists and does not support 'properties' query parm",
            dict(name='object-id'),
            False,
            False,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "Valid not locally existing property requested; "
            "resource exists and supports 'properties' query parm",
            dict(name='object-id'),
            False,
            True,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "Valid not locally existing property requested; "
            "resource is deleted and does not support 'properties' query parm",
            dict(name='object-id'),
            True,
            False,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "Valid not locally existing property requested; "
            "resource is deleted and supports 'properties' query parm",
            dict(name='object-id'),
            True,
            True,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),

        (
            "Invalid property requested; "
            "resource exists and does not support 'properties' query parm",
            dict(name='invalid-property'),
            False,
            False,
            None,
            None,
            None,
            KeyError,
        ),
        (
            "Invalid property requested; "
            "resource exists and supports 'properties' query parm",
            dict(name='invalid-property'),
            False,
            True,
            None,
            None,
            None,
            KeyError,
        ),
        (
            "Invalid property requested; "
            "resource is deleted and does not support 'properties' query parm",
            dict(name='invalid-property'),
            True,
            False,
            None,
            None,
            None,
            CeasedExistence,
        ),
        (
            "Invalid property requested; "
            "resource is deleted and supports 'properties' query parm",
            dict(name='invalid-property'),
            True,
            True,
            None,
            None,
            None,
            CeasedExistence,
        ),
    ]

    @pytest.mark.parametrize(
        "desc, input_kwargs, delete, supports_properties, exp_value, "
        "exp_propnames, exp_full_props, exp_exc_type",
        TESTCASES_GET_PROPERTY)
    def test_get_property(
            self, desc, input_kwargs, delete, supports_properties, exp_value,
            exp_propnames, exp_full_props, exp_exc_type):
        # pylint: disable=unused-argument
        """
        Test BaseResource.get_property().
        """
        if supports_properties:
            # Partitions support the properties query parm
            faked_res = self.add_standard_partition()
            res_mgr = self.cpc.partitions
        else:
            # Adapters do not support the properties query parm
            faked_res = self.add_standard_hipersocket()
            res_mgr = self.cpc.adapters
        assert res_mgr.supports_properties == supports_properties

        resource = res_mgr.find(name=faked_res.name)
        assert resource.full_properties is False

        if delete:
            # Delete the resource on the HMC, without affecting the state of
            # the local zhmcclient resource object. This simulates some other
            # user who has deleted the resource on the HMC while we have it
            # here as a zhmcclient resource object.
            resource.manager.session.delete(resource.uri)

        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The code to be tested
                resource.get_property(**input_kwargs)

            exc = exc_info.value
            assert isinstance(exc, exp_exc_type)
        else:

            # The code to be tested
            value = resource.get_property(**input_kwargs)

            assert value == exp_value

            propnames = set(resource.properties.keys())
            assert propnames.issuperset(exp_propnames)

            assert resource.full_properties == exp_full_props

    TESTCASES_PROP = [
        # Testcases for test_prop().
        # Each list item is a tuple defining a testcase in the following format:
        # - desc: Testcase description
        # - input_kwargs: keyword input parameters for the function
        # - delete: Indicates whether to delete the resource before test
        # - supports_properties: Resource supports 'properties' query parm
        # - exp_value: Expected return value of the function
        # - exp_propnames: Expected property names in resource after test
        # - exp_full_props: Expected value for full_properties attribute
        # - exp_exc_type: Expected type of exception, or None for success

        (
            "Valid locally existing property requested without default; "
            "resource exists and does not support 'properties' query parm",
            dict(name='name'),
            False,
            False,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "Valid locally existing property requested without default; "
            "resource exists and supports 'properties' query parm",
            dict(name='name'),
            False,
            True,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "Valid locally existing property requested without default; "
            "resource is deleted and does not support 'properties' query parm",
            dict(name='name'),
            True,
            False,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "Valid locally existing property requested without default; "
            "resource is deleted and supports 'properties' query parm",
            dict(name='name'),
            True,
            True,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),

        (
            "Valid locally existing property requested with default; "
            "resource exists and does not support 'properties' query parm",
            dict(name='name', default='foo'),
            False,
            False,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "Valid locally existing property requested with default; "
            "resource exists and supports 'properties' query parm",
            dict(name='name', default='foo'),
            False,
            True,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "Valid locally existing property requested with default; "
            "resource is deleted and does not support 'properties' query parm",
            dict(name='name', default='foo'),
            True,
            False,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),
        (
            "Valid locally existing property requested with default; "
            "resource is deleted and supports 'properties' query parm",
            dict(name='name', default='foo'),
            True,
            True,
            RESOURCE_NAME,
            {'name', 'object-uri'},
            False,
            None,
        ),

        (
            "Valid not locally existing property requested without default; "
            "resource exists and does not support 'properties' query parm",
            dict(name='object-id'),
            False,
            False,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "Valid not locally existing property requested without default; "
            "resource exists and supports 'properties' query parm",
            dict(name='object-id'),
            False,
            True,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "Valid not locally existing property requested without default; "
            "resource is deleted and does not support 'properties' query parm",
            dict(name='object-id'),
            True,
            False,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "Valid not locally existing property requested without default; "
            "resource is deleted and supports 'properties' query parm",
            dict(name='object-id'),
            True,
            True,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),

        (
            "Valid not locally existing property requested with default; "
            "resource exists and does not support 'properties' query parm",
            dict(name='object-id', default='foo'),
            False,
            False,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "Valid not locally existing property requested with default; "
            "resource exists and supports 'properties' query parm",
            dict(name='object-id', default='foo'),
            False,
            True,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "Valid not locally existing property requested with default; "
            "resource is deleted and does not support 'properties' query parm",
            dict(name='object-id', default='foo'),
            True,
            False,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),
        (
            "Valid not locally existing property requested with default; "
            "resource is deleted and supports 'properties' query parm",
            dict(name='object-id', default='foo'),
            True,
            True,
            RESOURCE_OID,
            {'name', 'object-uri', 'object-id'},
            False,
            None,
        ),

        (
            "Invalid property requested without default; "
            "resource exists and does not support 'properties' query parm",
            dict(name='invalid-property'),
            False,
            False,
            None,
            {'name', 'object-uri', 'invalid-property'},
            True,
            None,
        ),
        (
            "Invalid property requested without default; "
            "resource exists and supports 'properties' query parm",
            dict(name='invalid-property'),
            False,
            True,
            None,
            {'name', 'object-uri', 'invalid-property'},
            True,
            None,
        ),
        (
            "Invalid property requested without default; "
            "resource is deleted and does not support 'properties' query parm",
            dict(name='invalid-property'),
            True,
            False,
            None,
            None,
            None,
            CeasedExistence,
        ),
        (
            "Invalid property requested without default; "
            "resource is deleted and supports 'properties' query parm",
            dict(name='invalid-property'),
            True,
            True,
            None,
            None,
            None,
            CeasedExistence,
        ),

        (
            "Invalid property requested with default; "
            "resource exists and does not support 'properties' query parm",
            dict(name='invalid-property', default='foo'),
            False,
            False,
            'foo',
            {'name', 'object-uri', 'invalid-property'},
            True,
            None,
        ),
        (
            "Invalid property requested with default; "
            "resource exists and supports 'properties' query parm",
            dict(name='invalid-property', default='foo'),
            False,
            True,
            'foo',
            {'name', 'object-uri', 'invalid-property'},
            True,
            None,
        ),
        (
            "Invalid property requested with default; "
            "resource is deleted and does not support 'properties' query parm",
            dict(name='invalid-property', default='foo'),
            True,
            False,
            None,
            None,
            None,
            CeasedExistence,
        ),
        (
            "Invalid property requested with default; "
            "resource is deleted and supports 'properties' query parm",
            dict(name='invalid-property', default='foo'),
            True,
            True,
            None,
            None,
            None,
            CeasedExistence,
        ),
    ]

    @pytest.mark.parametrize(
        "desc, input_kwargs, delete, supports_properties, exp_value, "
        "exp_propnames, exp_full_props, exp_exc_type",
        TESTCASES_PROP)
    def test_prop(
            self, desc, input_kwargs, delete, supports_properties, exp_value,
            exp_propnames, exp_full_props, exp_exc_type):
        # pylint: disable=unused-argument
        """
        Test BaseResource.prop().
        """
        if supports_properties:
            # Partitions support the properties query parm
            faked_res = self.add_standard_partition()
            res_mgr = self.cpc.partitions
        else:
            # Adapters do not support the properties query parm
            faked_res = self.add_standard_hipersocket()
            res_mgr = self.cpc.adapters
        assert res_mgr.supports_properties == supports_properties

        resource = res_mgr.find(name=faked_res.name)
        assert resource.full_properties is False

        if delete:
            # Delete the resource on the HMC, without affecting the state of
            # the local zhmcclient resource object. This simulates some other
            # user who has deleted the resource on the HMC while we have it
            # here as a zhmcclient resource object.
            resource.manager.session.delete(resource.uri)

        if exp_exc_type:
            with pytest.raises(exp_exc_type) as exc_info:

                # The code to be tested
                resource.prop(**input_kwargs)

            exc = exc_info.value
            assert isinstance(exc, exp_exc_type)
        else:

            # The code to be tested
            value = resource.prop(**input_kwargs)

            assert value == exp_value

            propnames = set(resource.properties.keys())
            # prop() always adds the requested property
            if 'name' in input_kwargs:
                propnames.add(input_kwargs['name'])
            assert propnames.issuperset(exp_propnames)

            assert resource.full_properties == exp_full_props

    # TODO: Add test function for get_properties_pulled()
