"""
Test implementation of the PEP 509: dictionary versionning.
"""
import unittest
from test import support
_testcapi = support.import_module('_testcapi')


class DictVersionTests(unittest.TestCase):
    type2test = dict

    def setUp(self):
        self.seen_versions = set()
        self.dict = None

    def check_version_unique(self, mydict):
        version = _testcapi.dict_get_version(mydict)
        self.assertNotIn(version, self.seen_versions)
        self.seen_versions.add(version)

    def check_version_changed(self, mydict, method, *args, **kw):
        result = method(*args, **kw)
        self.check_version_unique(mydict)
        return result

    def check_version_dont_change(self, mydict, method, *args, **kw):
        version1 = _testcapi.dict_get_version(mydict)
        self.seen_versions.add(version1)
        result = method(*args, **kw)
        version2 = _testcapi.dict_get_version(mydict)
        self.assertEqual(version2, version1, 'version changed')
        return result

    def new_dict(self, *args, **kw):
        d = self.type2test(*args, **kw)
        self.check_version_unique(d)
        return d

    def test_constructor(self):
        empty1 = self.new_dict()
        empty2 = self.new_dict()
        empty3 = self.new_dict()
        nonempty1 = self.new_dict(x='x')
        nonempty2 = self.new_dict(x='x', y='y')

    def test_copy(self):
        d = self.new_dict(a=1, b=2)
        d2 = self.check_version_dont_change(d, d.copy)
        self.check_version_unique(d2)

    def test_setitem(self):
        d = self.new_dict()
        self.check_version_changed(d, d.__setitem__, 'x', 'x')
        self.check_version_changed(d, d.__setitem__, 'y', 'y')
        self.check_version_changed(d, d.__setitem__, 'x', 1)
        self.check_version_changed(d, d.__setitem__, 'y', 2)

    def test_setitem_same_value(self):
        value = object()
        d = self.new_dict()
        self.check_version_changed(d, d.__setitem__, 'key', value)
        self.check_version_changed(d, d.__setitem__, 'key', value)
        self.check_version_changed(d, d.update, key=value)
        d2 = self.new_dict(key=value)
        self.check_version_changed(d, d.update, d2)

    def test_setitem_equal(self):


        class AlwaysEqual:

            def __eq__(self, other):
                return True
        value1 = AlwaysEqual()
        value2 = AlwaysEqual()
        self.assertTrue(value1 == value2)
        self.assertFalse(value1 != value2)
        d = self.new_dict()
        self.check_version_changed(d, d.__setitem__, 'key', value1)
        self.check_version_changed(d, d.__setitem__, 'key', value2)
        self.check_version_changed(d, d.update, key=value1)
        d2 = self.new_dict(key=value2)
        self.check_version_changed(d, d.update, d2)

    def test_setdefault(self):
        d = self.new_dict()
        self.check_version_changed(d, d.setdefault, 'key', 'value1')
        self.check_version_dont_change(d, d.setdefault, 'key', 'value2')

    def test_delitem(self):
        d = self.new_dict(key='value')
        self.check_version_changed(d, d.__delitem__, 'key')
        self.check_version_dont_change(d, self.assertRaises, KeyError, d.
            __delitem__, 'key')

    def test_pop(self):
        d = self.new_dict(key='value')
        self.check_version_changed(d, d.pop, 'key')
        self.check_version_dont_change(d, self.assertRaises, KeyError, d.
            pop, 'key')

    def test_popitem(self):
        d = self.new_dict(key='value')
        self.check_version_changed(d, d.popitem)
        self.check_version_dont_change(d, self.assertRaises, KeyError, d.
            popitem)

    def test_update(self):
        d = self.new_dict(key='value')
        self.check_version_dont_change(d, d.update)
        self.check_version_changed(d, d.update, key='new value')
        d2 = self.new_dict(key='value 3')
        self.check_version_changed(d, d.update, d2)

    def test_clear(self):
        d = self.new_dict(key='value')
        self.check_version_changed(d, d.clear)
        self.check_version_dont_change(d, d.clear)


class Dict(dict):
    pass


class DictSubtypeVersionTests(DictVersionTests):
    type2test = Dict


if __name__ == '__main__':
    unittest.main()
