from test import mapping_tests
import unittest
import collections
d0 = {}
d1 = {'one': 1}
d2 = {'one': 1, 'two': 2}
d3 = {'one': 1, 'two': 3, 'three': 5}
d4 = {'one': None, 'two': None}
d5 = {'one': 1, 'two': 1}


class UserDictTest(mapping_tests.TestHashMappingProtocol):
    type2test = collections.UserDict

    def test_all(self):
        u = collections.UserDict()
        u0 = collections.UserDict(d0)
        u1 = collections.UserDict(d1)
        u2 = collections.UserDict(d2)
        uu = collections.UserDict(u)
        uu0 = collections.UserDict(u0)
        uu1 = collections.UserDict(u1)
        uu2 = collections.UserDict(u2)
        self.assertEqual(collections.UserDict(one=1, two=2), d2)
        self.assertEqual(collections.UserDict([('one', 1), ('two', 2)]), d2)
        with self.assertWarnsRegex(DeprecationWarning, "'dict'"):
            self.assertEqual(collections.UserDict(dict=[('one', 1), ('two',
                2)]), d2)
        self.assertEqual(collections.UserDict([('one', 1), ('two', 2)], two
            =3, three=5), d3)
        self.assertEqual(collections.UserDict.fromkeys('one two'.split()), d4)
        self.assertEqual(collections.UserDict().fromkeys('one two'.split()), d4
            )
        self.assertEqual(collections.UserDict.fromkeys('one two'.split(), 1
            ), d5)
        self.assertEqual(collections.UserDict().fromkeys('one two'.split(),
            1), d5)
        self.assertTrue(u1.fromkeys('one two'.split()) is not u1)
        self.assertIsInstance(u1.fromkeys('one two'.split()), collections.
            UserDict)
        self.assertIsInstance(u2.fromkeys('one two'.split()), collections.
            UserDict)
        self.assertEqual(str(u0), str(d0))
        self.assertEqual(repr(u1), repr(d1))
        self.assertIn(repr(u2), ("{'one': 1, 'two': 2}",
            "{'two': 2, 'one': 1}"))
        all = [d0, d1, d2, u, u0, u1, u2, uu, uu0, uu1, uu2]
        for a in all:
            for b in all:
                self.assertEqual(a == b, len(a) == len(b))
        self.assertEqual(u2['one'], 1)
        self.assertRaises(KeyError, u1.__getitem__, 'two')
        u3 = collections.UserDict(u2)
        u3['two'] = 2
        u3['three'] = 3
        del u3['three']
        self.assertRaises(KeyError, u3.__delitem__, 'three')
        u3.clear()
        self.assertEqual(u3, {})
        u2a = u2.copy()
        self.assertEqual(u2a, u2)
        u2b = collections.UserDict(x=42, y=23)
        u2c = u2b.copy()
        self.assertEqual(u2b, u2c)


        class MyUserDict(collections.UserDict):

            def display(self):
                print(self)
        m2 = MyUserDict(u2)
        m2a = m2.copy()
        self.assertEqual(m2a, m2)
        m2['foo'] = 'bar'
        self.assertNotEqual(m2a, m2)
        self.assertEqual(sorted(u2.keys()), sorted(d2.keys()))
        self.assertEqual(sorted(u2.items()), sorted(d2.items()))
        self.assertEqual(sorted(u2.values()), sorted(d2.values()))
        for i in u2.keys():
            self.assertIn(i, u2)
            self.assertEqual(i in u1, i in d1)
            self.assertEqual(i in u0, i in d0)
        t = collections.UserDict()
        t.update(u2)
        self.assertEqual(t, u2)
        for i in u2.keys():
            self.assertEqual(u2.get(i), u2[i])
            self.assertEqual(u1.get(i), d1.get(i))
            self.assertEqual(u0.get(i), d0.get(i))
        for i in range(20):
            u2[i] = str(i)
        ikeys = []
        for k in u2:
            ikeys.append(k)
        keys = u2.keys()
        self.assertEqual(set(ikeys), set(keys))
        t = collections.UserDict()
        self.assertEqual(t.setdefault('x', 42), 42)
        self.assertIn('x', t)
        self.assertEqual(t.setdefault('x', 23), 42)
        t = collections.UserDict(x=42)
        self.assertEqual(t.pop('x'), 42)
        self.assertRaises(KeyError, t.pop, 'x')
        self.assertEqual(t.pop('x', 1), 1)
        t['x'] = 42
        self.assertEqual(t.pop('x', 1), 42)
        t = collections.UserDict(x=42)
        self.assertEqual(t.popitem(), ('x', 42))
        self.assertRaises(KeyError, t.popitem)

    def test_init(self):
        for kw in ('self', 'other', 'iterable'):
            self.assertEqual(list(collections.UserDict(**{kw: 42}).items()),
                [(kw, 42)])
        self.assertEqual(list(collections.UserDict({}, dict=42).items()), [
            ('dict', 42)])
        self.assertEqual(list(collections.UserDict({}, dict=None).items()),
            [('dict', None)])
        with self.assertWarnsRegex(DeprecationWarning, "'dict'"):
            self.assertEqual(list(collections.UserDict(dict={'a': 42}).
                items()), [('a', 42)])
        self.assertRaises(TypeError, collections.UserDict, 42)
        self.assertRaises(TypeError, collections.UserDict, (), ())
        self.assertRaises(TypeError, collections.UserDict.__init__)

    def test_update(self):
        for kw in ('self', 'dict', 'other', 'iterable'):
            d = collections.UserDict()
            d.update(**{kw: 42})
            self.assertEqual(list(d.items()), [(kw, 42)])
        self.assertRaises(TypeError, collections.UserDict().update, 42)
        self.assertRaises(TypeError, collections.UserDict().update, {}, {})
        self.assertRaises(TypeError, collections.UserDict.update)

    def test_missing(self):
        self.assertEqual(hasattr(collections.UserDict, '__missing__'), False)


        class D(collections.UserDict):

            def __missing__(self, key):
                return 42
        d = D({(1): 2, (3): 4})
        self.assertEqual(d[1], 2)
        self.assertEqual(d[3], 4)
        self.assertNotIn(2, d)
        self.assertNotIn(2, d.keys())
        self.assertEqual(d[2], 42)


        class E(collections.UserDict):

            def __missing__(self, key):
                raise RuntimeError(key)
        e = E()
        try:
            e[42]
        except RuntimeError as err:
            self.assertEqual(err.args, (42,))
        else:
            self.fail("e[42] didn't raise RuntimeError")


        class F(collections.UserDict):

            def __init__(self):
                self.__missing__ = lambda key: None
                collections.UserDict.__init__(self)
        f = F()
        try:
            f[42]
        except KeyError as err:
            self.assertEqual(err.args, (42,))
        else:
            self.fail("f[42] didn't raise KeyError")


        class G(collections.UserDict):
            pass
        g = G()
        try:
            g[42]
        except KeyError as err:
            self.assertEqual(err.args, (42,))
        else:
            self.fail("g[42] didn't raise KeyError")


if __name__ == '__main__':
    unittest.main()
