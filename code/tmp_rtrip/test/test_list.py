import sys
from test import list_tests
import pickle
import unittest


class ListTest(list_tests.CommonTest):
    type2test = list

    def test_basic(self):
        self.assertEqual(list([]), [])
        l0_3 = [0, 1, 2, 3]
        l0_3_bis = list(l0_3)
        self.assertEqual(l0_3, l0_3_bis)
        self.assertTrue(l0_3 is not l0_3_bis)
        self.assertEqual(list(()), [])
        self.assertEqual(list((0, 1, 2, 3)), [0, 1, 2, 3])
        self.assertEqual(list(''), [])
        self.assertEqual(list('spam'), ['s', 'p', 'a', 'm'])
        if sys.maxsize == 2147483647:
            self.assertRaises(MemoryError, list, range(sys.maxsize // 2))
        x = []
        x.extend(-y for y in x)
        self.assertEqual(x, [])

    def test_truth(self):
        super().test_truth()
        self.assertTrue(not [])
        self.assertTrue([42])

    def test_identity(self):
        self.assertTrue([] is not [])

    def test_len(self):
        super().test_len()
        self.assertEqual(len([]), 0)
        self.assertEqual(len([0]), 1)
        self.assertEqual(len([0, 1, 2]), 3)

    def test_overflow(self):
        lst = [4, 5, 6, 7]
        n = int((sys.maxsize * 2 + 2) // len(lst))

        def mul(a, b):
            return a * b

        def imul(a, b):
            a *= b
        self.assertRaises((MemoryError, OverflowError), mul, lst, n)
        self.assertRaises((MemoryError, OverflowError), imul, lst, n)

    def test_repr_large(self):

        def check(n):
            l = [0] * n
            s = repr(l)
            self.assertEqual(s, '[' + ', '.join(['0'] * n) + ']')
        check(10)
        check(1000000)

    def test_iterator_pickle(self):
        orig = self.type2test([4, 5, 6, 7])
        data = [10, 11, 12, 13, 14, 15]
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            itorig = iter(orig)
            d = pickle.dumps((itorig, orig), proto)
            it, a = pickle.loads(d)
            a[:] = data
            self.assertEqual(type(it), type(itorig))
            self.assertEqual(list(it), data)
            next(itorig)
            d = pickle.dumps((itorig, orig), proto)
            it, a = pickle.loads(d)
            a[:] = data
            self.assertEqual(type(it), type(itorig))
            self.assertEqual(list(it), data[1:])
            for i in range(1, len(orig)):
                next(itorig)
            d = pickle.dumps((itorig, orig), proto)
            it, a = pickle.loads(d)
            a[:] = data
            self.assertEqual(type(it), type(itorig))
            self.assertEqual(list(it), data[len(orig):])
            self.assertRaises(StopIteration, next, itorig)
            d = pickle.dumps((itorig, orig), proto)
            it, a = pickle.loads(d)
            a[:] = data
            self.assertEqual(list(it), [])

    def test_reversed_pickle(self):
        orig = self.type2test([4, 5, 6, 7])
        data = [10, 11, 12, 13, 14, 15]
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            itorig = reversed(orig)
            d = pickle.dumps((itorig, orig), proto)
            it, a = pickle.loads(d)
            a[:] = data
            self.assertEqual(type(it), type(itorig))
            self.assertEqual(list(it), data[len(orig) - 1::-1])
            next(itorig)
            d = pickle.dumps((itorig, orig), proto)
            it, a = pickle.loads(d)
            a[:] = data
            self.assertEqual(type(it), type(itorig))
            self.assertEqual(list(it), data[len(orig) - 2::-1])
            for i in range(1, len(orig)):
                next(itorig)
            d = pickle.dumps((itorig, orig), proto)
            it, a = pickle.loads(d)
            a[:] = data
            self.assertEqual(type(it), type(itorig))
            self.assertEqual(list(it), [])
            self.assertRaises(StopIteration, next, itorig)
            d = pickle.dumps((itorig, orig), proto)
            it, a = pickle.loads(d)
            a[:] = data
            self.assertEqual(list(it), [])

    def test_no_comdat_folding(self):


        class L(list):
            pass
        with self.assertRaises(TypeError):
            (3,) + L([1, 2])


if __name__ == '__main__':
    unittest.main()
