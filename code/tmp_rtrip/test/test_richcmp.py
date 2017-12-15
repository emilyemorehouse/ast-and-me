import unittest
from test import support
import operator


class Number:

    def __init__(self, x):
        self.x = x

    def __lt__(self, other):
        return self.x < other

    def __le__(self, other):
        return self.x <= other

    def __eq__(self, other):
        return self.x == other

    def __ne__(self, other):
        return self.x != other

    def __gt__(self, other):
        return self.x > other

    def __ge__(self, other):
        return self.x >= other

    def __cmp__(self, other):
        raise support.TestFailed('Number.__cmp__() should not be called')

    def __repr__(self):
        return 'Number(%r)' % (self.x,)


class Vector:

    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        return self.data[i]

    def __setitem__(self, i, v):
        self.data[i] = v
    __hash__ = None

    def __bool__(self):
        raise TypeError('Vectors cannot be used in Boolean contexts')

    def __cmp__(self, other):
        raise support.TestFailed('Vector.__cmp__() should not be called')

    def __repr__(self):
        return 'Vector(%r)' % (self.data,)

    def __lt__(self, other):
        return Vector([(a < b) for a, b in zip(self.data, self.__cast(other))])

    def __le__(self, other):
        return Vector([(a <= b) for a, b in zip(self.data, self.__cast(other))]
            )

    def __eq__(self, other):
        return Vector([(a == b) for a, b in zip(self.data, self.__cast(other))]
            )

    def __ne__(self, other):
        return Vector([(a != b) for a, b in zip(self.data, self.__cast(other))]
            )

    def __gt__(self, other):
        return Vector([(a > b) for a, b in zip(self.data, self.__cast(other))])

    def __ge__(self, other):
        return Vector([(a >= b) for a, b in zip(self.data, self.__cast(other))]
            )

    def __cast(self, other):
        if isinstance(other, Vector):
            other = other.data
        if len(self.data) != len(other):
            raise ValueError('Cannot compare vectors of different length')
        return other


opmap = {'lt': (lambda a, b: a < b, operator.lt, operator.__lt__), 'le': (
    lambda a, b: a <= b, operator.le, operator.__le__), 'eq': (lambda a, b:
    a == b, operator.eq, operator.__eq__), 'ne': (lambda a, b: a != b,
    operator.ne, operator.__ne__), 'gt': (lambda a, b: a > b, operator.gt,
    operator.__gt__), 'ge': (lambda a, b: a >= b, operator.ge, operator.__ge__)
    }


class VectorTest(unittest.TestCase):

    def checkfail(self, error, opname, *args):
        for op in opmap[opname]:
            self.assertRaises(error, op, *args)

    def checkequal(self, opname, a, b, expres):
        for op in opmap[opname]:
            realres = op(a, b)
            self.assertEqual(len(realres), len(expres))
            for i in range(len(realres)):
                self.assertTrue(realres[i] is expres[i])

    def test_mixed(self):
        a = Vector(range(2))
        b = Vector(range(3))
        for opname in opmap:
            self.checkfail(ValueError, opname, a, b)
        a = list(range(5))
        b = 5 * [2]
        args = [(a, Vector(b)), (Vector(a), b), (Vector(a), Vector(b))]
        for a, b in args:
            self.checkequal('lt', a, b, [True, True, False, False, False])
            self.checkequal('le', a, b, [True, True, True, False, False])
            self.checkequal('eq', a, b, [False, False, True, False, False])
            self.checkequal('ne', a, b, [True, True, False, True, True])
            self.checkequal('gt', a, b, [False, False, False, True, True])
            self.checkequal('ge', a, b, [False, False, True, True, True])
            for ops in opmap.values():
                for op in ops:
                    self.assertRaises(TypeError, bool, op(a, b))


class NumberTest(unittest.TestCase):

    def test_basic(self):
        for a in range(3):
            for b in range(3):
                for typea in (int, Number):
                    for typeb in (int, Number):
                        if typea == typeb == int:
                            continue
                        ta = typea(a)
                        tb = typeb(b)
                        for ops in opmap.values():
                            for op in ops:
                                realoutcome = op(a, b)
                                testoutcome = op(ta, tb)
                                self.assertEqual(realoutcome, testoutcome)

    def checkvalue(self, opname, a, b, expres):
        for typea in (int, Number):
            for typeb in (int, Number):
                ta = typea(a)
                tb = typeb(b)
                for op in opmap[opname]:
                    realres = op(ta, tb)
                    realres = getattr(realres, 'x', realres)
                    self.assertTrue(realres is expres)

    def test_values(self):
        self.checkvalue('lt', 0, 0, False)
        self.checkvalue('le', 0, 0, True)
        self.checkvalue('eq', 0, 0, True)
        self.checkvalue('ne', 0, 0, False)
        self.checkvalue('gt', 0, 0, False)
        self.checkvalue('ge', 0, 0, True)
        self.checkvalue('lt', 0, 1, True)
        self.checkvalue('le', 0, 1, True)
        self.checkvalue('eq', 0, 1, False)
        self.checkvalue('ne', 0, 1, True)
        self.checkvalue('gt', 0, 1, False)
        self.checkvalue('ge', 0, 1, False)
        self.checkvalue('lt', 1, 0, False)
        self.checkvalue('le', 1, 0, False)
        self.checkvalue('eq', 1, 0, False)
        self.checkvalue('ne', 1, 0, True)
        self.checkvalue('gt', 1, 0, True)
        self.checkvalue('ge', 1, 0, True)


class MiscTest(unittest.TestCase):

    def test_misbehavin(self):


        class Misb:

            def __lt__(self_, other):
                return 0

            def __gt__(self_, other):
                return 0

            def __eq__(self_, other):
                return 0

            def __le__(self_, other):
                self.fail("This shouldn't happen")

            def __ge__(self_, other):
                self.fail("This shouldn't happen")

            def __ne__(self_, other):
                self.fail("This shouldn't happen")
        a = Misb()
        b = Misb()
        self.assertEqual(a < b, 0)
        self.assertEqual(a == b, 0)
        self.assertEqual(a > b, 0)

    def test_not(self):
        import operator


        class Exc(Exception):
            pass


        class Bad:

            def __bool__(self):
                raise Exc

        def do(bad):
            not bad
        for func in (do, operator.not_):
            self.assertRaises(Exc, func, Bad())

    @support.no_tracing
    def test_recursion(self):
        from collections import UserList
        a = UserList()
        b = UserList()
        a.append(b)
        b.append(a)
        self.assertRaises(RecursionError, operator.eq, a, b)
        self.assertRaises(RecursionError, operator.ne, a, b)
        self.assertRaises(RecursionError, operator.lt, a, b)
        self.assertRaises(RecursionError, operator.le, a, b)
        self.assertRaises(RecursionError, operator.gt, a, b)
        self.assertRaises(RecursionError, operator.ge, a, b)
        b.append(17)
        self.assertTrue(not a == b)
        self.assertTrue(a != b)
        self.assertRaises(RecursionError, operator.lt, a, b)
        self.assertRaises(RecursionError, operator.le, a, b)
        self.assertRaises(RecursionError, operator.gt, a, b)
        self.assertRaises(RecursionError, operator.ge, a, b)
        a.append(17)
        self.assertRaises(RecursionError, operator.eq, a, b)
        self.assertRaises(RecursionError, operator.ne, a, b)
        a.insert(0, 11)
        b.insert(0, 12)
        self.assertTrue(not a == b)
        self.assertTrue(a != b)
        self.assertTrue(a < b)

    def test_exception_message(self):


        class Spam:
            pass
        tests = [(lambda : 42 < None, "'<' .* of 'int' and 'NoneType'"), (
            lambda : None < 42, "'<' .* of 'NoneType' and 'int'"), (lambda :
            42 > None, "'>' .* of 'int' and 'NoneType'"), (lambda : 'foo' <
            None, "'<' .* of 'str' and 'NoneType'"), (lambda : 'foo' >= 666,
            "'>=' .* of 'str' and 'int'"), (lambda : 42 <= None,
            "'<=' .* of 'int' and 'NoneType'"), (lambda : 42 >= None,
            "'>=' .* of 'int' and 'NoneType'"), (lambda : 42 < [],
            "'<' .* of 'int' and 'list'"), (lambda : () > [],
            "'>' .* of 'tuple' and 'list'"), (lambda : None >= None,
            "'>=' .* of 'NoneType' and 'NoneType'"), (lambda : Spam() < 42,
            "'<' .* of 'Spam' and 'int'"), (lambda : 42 < Spam(),
            "'<' .* of 'int' and 'Spam'"), (lambda : Spam() <= Spam(),
            "'<=' .* of 'Spam' and 'Spam'")]
        for i, test in enumerate(tests):
            with self.subTest(test=i):
                with self.assertRaisesRegex(TypeError, test[1]):
                    test[0]()


class DictTest(unittest.TestCase):

    def test_dicts(self):
        import random
        imag1a = {}
        for i in range(50):
            imag1a[random.randrange(100) * 1j] = random.randrange(100) * 1j
        items = list(imag1a.items())
        random.shuffle(items)
        imag1b = {}
        for k, v in items:
            imag1b[k] = v
        imag2 = imag1b.copy()
        imag2[k] = v + 1.0
        self.assertEqual(imag1a, imag1a)
        self.assertEqual(imag1a, imag1b)
        self.assertEqual(imag2, imag2)
        self.assertTrue(imag1a != imag2)
        for opname in ('lt', 'le', 'gt', 'ge'):
            for op in opmap[opname]:
                self.assertRaises(TypeError, op, imag1a, imag2)


class ListTest(unittest.TestCase):

    def test_coverage(self):
        x = [42]
        self.assertIs(x < x, False)
        self.assertIs(x <= x, True)
        self.assertIs(x == x, True)
        self.assertIs(x != x, False)
        self.assertIs(x > x, False)
        self.assertIs(x >= x, True)
        y = [42, 42]
        self.assertIs(x < y, True)
        self.assertIs(x <= y, True)
        self.assertIs(x == y, False)
        self.assertIs(x != y, True)
        self.assertIs(x > y, False)
        self.assertIs(x >= y, False)

    def test_badentry(self):


        class Exc(Exception):
            pass


        class Bad:

            def __eq__(self, other):
                raise Exc
        x = [Bad()]
        y = [Bad()]
        for op in opmap['eq']:
            self.assertRaises(Exc, op, x, y)

    def test_goodentry(self):


        class Good:

            def __lt__(self, other):
                return True
        x = [Good()]
        y = [Good()]
        for op in opmap['lt']:
            self.assertIs(op(x, y), True)


if __name__ == '__main__':
    unittest.main()
