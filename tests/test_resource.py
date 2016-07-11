#!/usr/bin/env python
#
# Unit tests for _resource module.
#

from __future__ import absolute_import

import unittest
import warnings
import six

from zhmcclient._resource import BaseResource
from zhmcclient._manager import BaseManager


class MyResource(BaseResource):
    """
    A derived resource for testing the BaseResource class.
    """

    def __init__(self, *args, **kwargs):
        super(MyResource, self).__init__(*args, **kwargs)


class MyManager(BaseManager):
    """
    A derived resource manager for testing purposes.

    It is only needed because BaseResource needs it; it is not subject
    of test in this unit test module.
    """

    def __init__(self, *args, **kwargs):
        super(MyManager, self).__init__(*args, **kwargs)


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.mgr = MyManager()

    def assert_properties(self, resource, properties, invalid_keys=None):
        """
        Perform a number of read-only checks on a resource object,
        given its input properties and some invalid keys.
        """

        # Check properties dict size
        self.assertEqual(len(resource), len(properties))

        # Various tests with valid keys and values
        for key, value in properties.items():

            # Check access by key
            self.assertEqual(resource[key], value)

            # Check 'get()' method without default
            self.assertEqual(resource.get(key), value)

            # Check 'get()' method with default
            self.assertEqual(resource.get(key, 'xxx'), value)

            # Check 'in' operator
            self.assertTrue(key in resource,
                            "Key %r is not in resource %r, " \
                            "using 'in' operator" % (key, resource))

            # Check 'has_key()' method
            self.assertTrue(resource.has_key(key),
                            "Key %r is not in resource %r, " \
                            "using has_key() method" % (key, resource))

        # Check 'keys()' method
        for key in resource.keys():
            self.assertTrue(key in properties.keys(),
                            "Resource property key %r is not in input " \
                            "properties %r, using keys() method" % \
                            (key, properties))
        for key in properties.keys():
            self.assertTrue(key in resource.keys(),
                            "Input property key %r is not in resource " \
                            "properties %r, using keys() method" % \
                            (key, resource))

        # Check 'values()' method
        for value in resource.values():
            self.assertTrue(value in properties.values(),
                            "Resource property value %r is not in input " \
                            "properties %r, using values() method" % \
                            (value, properties))
        for value in properties.values():
            self.assertTrue(value in resource.values(),
                            "Input property value %r is not in resource " \
                            "properties %r, using values() method" % \
                            (value, resource))

        # Check 'items()' method
        for key, value in resource.items():
            self.assertTrue((key, value) in properties.items(),
                            "Resource property key/value tuple (%r, %r) is " \
                            "not in input properties %r, " \
                            "using items() method" % \
                            (key, value, properties))
        for key, value in properties.items():
            self.assertTrue((key, value) in resource.items(),
                            "Input property key/value tuple (%r, %r) is " \
                            "not in resource properties %r, " \
                            "using items() method" % \
                            (key, value, resource))

        # Check 'iterkeys()' method
        for key in six.iterkeys(resource):
            self.assertTrue(key in properties.keys(),
                            "Resource property key %r is not in input " \
                            "properties %r, using iterkeys() method" % \
                            (key, properties))
        for key in six.iterkeys(properties):
            self.assertTrue(key in resource.keys(),
                            "Input property key %r is not in resource " \
                            "properties %r, using iterkeys() method" % \
                            (key, resource))

        # Check 'itervalues()' method
        for value in six.itervalues(resource):
            self.assertTrue(value in properties.values(),
                            "Resource property value %r is not in input " \
                            "properties %r, using itervalues() method" % \
                            (value, properties))
        for value in six.itervalues(properties):
            self.assertTrue(value in resource.values(),
                            "Input property value %r is not in resource " \
                            "properties %r, using itervalues() method" % \
                            (value, resource))

        # Check 'iteritems()' method
        for key, value in six.iteritems(resource):
            self.assertTrue((key, value) in properties.items(),
                            "Resource property key/value tuple (%r, %r) is " \
                            "not in input properties %r, " \
                            "using iteritems() method" % \
                            (key, value, properties))
        for key, value in six.iteritems(properties):
            self.assertTrue((key, value) in resource.items(),
                            "Input property key/value tuple (%r, %r) is " \
                            "not in resource properties %r, " \
                            "using iteritems() method" % \
                            (key, value, resource))

        # Various checks with invalid keys
        if invalid_keys is not None:
            for key in invalid_keys:

                # Ensure that the testcase is correct, i.e. specifies an
                # invalid key
                assert key not in properties

                # Check 'get()' method without default
                self.assertEqual(resource.get(key), None)

                # Check 'get()' method with default
                self.assertEqual(resource.get(key, 'xxx'), 'xxx')

                # Check 'in' operation
                self.assertTrue(not key in resource,
                                "Key %r is in resource %r, " \
                                "using 'in' operator" % (key, resource))

                # Check 'has_key()' method
                self.assertTrue(not resource.has_key(key),
                                "Key %r is in resource %r, " \
                                "using has_key() method" % (key, resource))

                # Check 'keys()' method
                self.assertTrue(not key in resource.keys(),
                                "Key %r is not in resource %r, " \
                                "using keys() method" % (key, resource))

                # Check that accessing invalid keys raise KeyError
                try:
                    x = resource[key]
                except KeyError:
                    pass
                else:
                    self.fail("KeyError was not raised when accessing " \
                              "invalid key %r in resource %r" % \
                              (key, resource))


class TestInit(BaseTest):
    """Test BaseResource initialization and read-only operations."""

    def test_empty(self):
        properties = {}
        invalid_keys = ('inv1', '', 99)
        res = MyResource(self.mgr, properties)
        self.assertTrue(res.manager is self.mgr)
        self.assert_properties(res, properties, invalid_keys)

    def test_simple(self):
        properties = {
            'prop1': 'abc',
            'prop2': 100042
        }
        invalid_keys = ('inv1', '', 99)
        res = MyResource(self.mgr, properties)
        self.assertTrue(res.manager is self.mgr)
        self.assert_properties(res, properties, invalid_keys)

    def test_prop_case(self):
        properties = {
            'prop1': 'abc',
            'Prop1': 100042
        }
        invalid_keys = ('proP1', '', 99)
        res = MyResource(self.mgr, properties)
        self.assertTrue(res.manager is self.mgr)
        self.assert_properties(res, properties, invalid_keys)

    def test_invalid_type(self):
        init_props = 42
        try:
            res = MyResource(self.mgr, init_props)
        except TypeError:
            pass
        else:
            self.fail("TypeError was not raised when initializing resource " \
                      "with invalid properties: %r" % init_props)


class TestSet(BaseTest):
    """Test BaseResource by setting single properties."""

    def test_add_to_empty(self):
        init_properties = {}
        set_properties = {
            'prop1': 'abc',
            'prop2': 100042
        }
        res_properties = dict(init_properties)
        res_properties.update(set_properties)
        res = MyResource(self.mgr, init_properties)
        for key, value in set_properties.items():
            res[key] = value
        self.assert_properties(res, res_properties)

    def test_replace_one_add_one(self):
        init_properties = {
            'prop1': 42,
        }
        set_properties = {
            'prop1': 'abc',
            'prop2': 100042
        }
        res_properties = dict(init_properties)
        res_properties.update(set_properties)
        res = MyResource(self.mgr, init_properties)
        for key, value in set_properties.items():
            res[key] = value
        self.assert_properties(res, res_properties)


class TestDel(BaseTest):
    """Test BaseResource by deleting single properties."""

    def test_del_one(self):
        init_properties = {
            'prop1': 'abc',
            'prop2': 100042
        }
        del_keys = ('prop1',)
        res_properties = {
            'prop2': 100042
        }
        res = MyResource(self.mgr, init_properties)
        for key in del_keys:
            del res[key]
        self.assert_properties(res, res_properties)

    def test_del_all(self):
        init_properties = {
            'prop1': 'abc',
            'prop2': 100042
        }
        del_keys = ('prop1', 'prop2')
        res_properties = {}
        res = MyResource(self.mgr, init_properties)
        for key in del_keys:
            del res[key]
        self.assert_properties(res, res_properties)

    def test_del_invalid(self):
        init_properties = {
            'prop1': 'abc',
            'prop2': 100042
        }
        org_init_properties = dict(init_properties)
        res = MyResource(self.mgr, init_properties)
        invalid_key = 'inv1'
        try:
            del res[invalid_key]
        except KeyError:
            pass
        else:
            self.fail("KeyError was not raised when deleting invalid key %r " \
                      "in resource properties %r" % \
                      (invalid_key, org_init_properties))

class xTestClear(object):

    def test_all(self):
        self.dic.clear()
        self.assertTrue(len(self.dic) == 0)

class xTestUpdate(object):

    def test_all(self):
        self.dic.clear()
        self.dic.update({'Chicken': 'Ham'})
        self.assertTrue(self.dic.keys() == ['Chicken'])
        self.assertTrue(self.dic.values() == ['Ham'])
        self.dic.clear()
        self.dic.update({'Chicken': 'Ham'}, {'Dog': 'Cat'})
        keys = self.dic.keys()
        vals = self.dic.values()
        keys = list(keys)
        vals = list(vals)
        keys.sort()
        vals.sort()
        self.assertTrue(keys == ['Chicken', 'Dog'])
        self.assertTrue(vals == ['Cat', 'Ham'])
        self.dic.update([('Chicken', 'Egg')], {'Fish': 'Eel'})
        self.assertTrue(self.dic['chicken'] == 'Egg')
        self.assertTrue(self.dic['fish'] == 'Eel')
        self.dic.update({'Fish': 'Salmon'}, Cow='Beef')
        self.assertTrue(self.dic['fish'] == 'Salmon')
        self.assertTrue(self.dic['Cow'] == 'Beef')
        self.assertTrue(self.dic['COW'] == 'Beef')
        self.assertTrue(self.dic['cow'] == 'Beef')

class xTestCopy(object):

    def test_all(self):
        cp = self.dic.copy()
        self.assertEqual(cp, self.dic)
        self.assertTrue(isinstance(cp, BaseResource))
        cp['Dog'] = 'Kitten'
        self.assertTrue(self.dic['Dog'] == 'Cat')
        self.assertTrue(cp['Dog'] == 'Kitten')

class xTestSetDefault(object):

    def test_all(self):
        self.dic.setdefault('Dog', 'Kitten')
        self.assertTrue(self.dic['Dog'] == 'Cat')
        self.dic.setdefault('Ningaui', 'Chicken')
        self.assertTrue(self.dic['Ningaui'] == 'Chicken')

class xTestEqual(object):

    def assertDictEqual(self, dic1, dic2, msg):

        self.assertTrue(dic1 == dic2, msg)
        self.assertFalse(dic1 != dic2, msg)

        self.assertTrue(dic2 == dic1, msg)
        self.assertFalse(dic2 != dic1, msg)

    def assertDictNotEqual(self, dic1, dic2, msg):

        self.assertTrue(dic1 != dic2, msg)
        self.assertFalse(dic1 == dic2, msg)

        self.assertTrue(dic2 != dic1, msg)
        self.assertFalse(dic2 == dic1, msg)

    def run_test_dicts(self, base_dict, test_dicts):

        for test_dict, relation, comment in test_dicts:
            if relation == 'eq':
                self.assertDictEqual(test_dict, base_dict,
                                "Expected test_dict == base_dict:\n" \
                                "  test case: %s\n" \
                                "  test_dict: %r\n" \
                                "  base_dict: %r" % \
                                (comment, test_dict, base_dict))
            elif relation == 'ne':
                self.assertDictNotEqual(test_dict, base_dict,
                                "Expected test_dict != base_dict:\n" \
                                "  test case: %s\n" \
                                "  test_dict: %r\n" \
                                "  base_dict: %r" % \
                                (comment, test_dict, base_dict))
            else:
                raise AssertionError("Internal Error: Invalid relation %s" \
                                     "specified in testcase: %s" % \
                                     (relation, comment))

    def test_all(self):

        # The base dictionary that is used for all comparisons
        base_dict = dict({'Budgie': 'Fish', 'Dog': 'Cat'})

        # Test dictionaries to test against the base dict, as a list of
        # tuple(dict, relation, comment), with relation being the expected
        # comparison relation, and one of ('eq', 'ne').
        test_dicts = [

            (dict({'Budgie': 'Fish', 'Dog': 'Cat'}),
             'eq',
             'Same'),

            (dict({'Budgie': 'Fish'}),
             'ne',
             'Higher key missing, shorter size'),

            (dict({'Dog': 'Cat'}),
             'ne',
             'Lower key missing, shorter size'),

            (dict({'Budgie': 'Fish', 'Curly': 'Snake', 'Cozy': 'Dog'}),
             'ne',
             'First non-matching key is less. But longer size!'),

            (dict({'Alf': 'F', 'Anton': 'S', 'Aussie': 'D'}),
             'ne',
             'Only non-matching keys that are less. But longer size!'),

            (dict({'Budgio': 'Fish'}),
             'ne',
             'First non-matching key is greater. But shorter size!'),

            (dict({'Zoe': 'F'}),
             'ne',
             'Only non-matching keys that are greater. But shorter size!'),

            (dict({'Budgie': 'Fish', 'Curly': 'Snake'}),
             'ne',
             'Same size. First non-matching key is less'),

            (dict({'Alf': 'F', 'Anton': 'S'}),
             'ne',
             'Same size. Only non-matching keys that are less'),

            (dict({'Zoe': 'F', 'Zulu': 'S'}),
             'ne',
             'Same size. Only non-matching keys that are greater'),

            (dict({'Budgie': 'Fish', 'Dog': 'Car'}),
             'ne',
             'Same size, only matching keys. First non-matching value is less'),

            (dict({'Budgie': 'Fish', 'Dog': 'Caz'}),
             'ne',
             'Same size, only matching keys. First non-matching value is grt.'),
        ]

        # First, run these tests against a standard dictionary to verify
        # that the test case definitions conform to that
        self.run_test_dicts(base_dict, test_dicts)

        # Then, transform these tests to NocaseDict and run them again
        TEST_CASE_INSENSITIVITY = True
        base_ncdict = MyResource(base_dict)
        test_ncdicts = []
        for test_dict, relation, comment in test_dicts:
            test_ncdict = MyResource()
            for key in test_dict:
                if TEST_CASE_INSENSITIVITY:
                    nc_key = swapcase2(key)
                else:
                    nc_key = key
                test_ncdict[nc_key] = test_dict[key]
            test_ncdicts.append((test_ncdict, relation, comment))
        self.run_test_dicts(base_ncdict, test_ncdicts)

class xTestOrdering(object):
    """Verify that ordering comparisons between NocaseDict instances
    issue a deprecation warning, and for Python 3, in addition the usual
    "TypeError: unorderable types" for standard dicts."""

    def assertWarning(self, comp_str):
        with warnings.catch_warnings(record=True) as wlist:
            warnings.simplefilter("always")
            if six.PY2:
                eval(comp_str)
            else:
                try:
                    eval(comp_str)
                except TypeError as exc:
                    assert "unorderable types" in str(exc)
                else:
                    self.fail("Ordering a dictionary in Python 3 did not "
                              "raise TypeError")
            assert len(wlist) >= 1
            assert issubclass(wlist[-1].category, DeprecationWarning)
            assert "deprecated" in str(wlist[-1].message)

    def test_all(self):
        self.assertWarning("self.dic < self.dic")
        self.assertWarning("self.dic <= self.dic")
        self.assertWarning("self.dic > self.dic")
        self.assertWarning("self.dic >= self.dic")


if __name__ == '__main__':
    unittest.main()
