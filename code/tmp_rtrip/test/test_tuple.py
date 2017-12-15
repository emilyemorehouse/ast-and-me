from test import support, seq_tests
import unittest
import gc
import pickle


class TupleTest(seq_tests.CommonTest):
    type2test = tuple

    def test_getitem_error(self):
        msg = 'tuple indices must be integers or slices'
        with self.assertRaisesRegex(TypeError, msg):
            ()['a']

    def test_constructors(self):
        super().test_constructors()
        self.assertEqual(tuple(), ())
        t0_3 = 0, 1, 2, 3
        t0_3_bis = tuple(t0_3)
        self.assertTrue(t0_3 is t0_3_bis)
        self.assertEqual(tuple([]), ())
        self.assertEqual(tuple([0, 1, 2, 3]), (0, 1, 2, 3))
        self.assertEqual(tuple(''), ())
        self.assertEqual(tuple('spam'), ('s', 'p', 'a', 'm'))

    def test_truth(self):
        super().test_truth()
        self.assertTrue(not ())
        self.assertTrue((42,))

    def test_len(self):
        super().test_len()
        self.assertEqual(len(()), 0)
        self.assertEqual(len((0,)), 1)
        self.assertEqual(len((0, 1, 2)), 3)

    def test_iadd(self):
        super().test_iadd()
        u = 0, 1
        u2 = u
        u += 2, 3
        self.assertTrue(u is not u2)

    def test_imul(self):
        super().test_imul()
        u = 0, 1
        u2 = u
        u *= 3
        self.assertTrue(u is not u2)

    def test_tupleresizebug(self):

        def f():
            for i in range(1000):
                yield i
        self.assertEqual(list(tuple(f())), list(range(1000)))

    def test_hash(self):
        N = 50
        base = list(range(N))
        xp = [(i, j) for i in base for j in base]
        inps = base + [(i, j) for i in base for j in xp] + [(i, j) for i in
            xp for j in base] + xp + list(zip(base))
        collisions = len(inps) - len(set(map(hash, inps)))
        self.assertTrue(collisions <= 15)

    def test_repr(self):
        l0 = tuple()
        l2 = 0, 1, 2
        a0 = self.type2test(l0)
        a2 = self.type2test(l2)
        self.assertEqual(str(a0), repr(l0))
        self.assertEqual(str(a2), repr(l2))
        self.assertEqual(repr(a0), '()')
        self.assertEqual(repr(a2), '(0, 1, 2)')

    def _not_tracked(self, t):
        gc.collect()
        gc.collect()
        self.assertFalse(gc.is_tracked(t), t)

    def _tracked(self, t):
        self.assertTrue(gc.is_tracked(t), t)
        gc.collect()
        gc.collect()
        self.assertTrue(gc.is_tracked(t), t)

    @support.cpython_only
    def test_track_literals(self):
        x, y, z = 1.5, 'a', []
        self._not_tracked(())
        self._not_tracked((1,))
        self._not_tracked((1, 2))
        self._not_tracked((1, 2, 'a'))
        self._not_tracked((1, 2, (None, True, False, ()), int))
        self._not_tracked((object(),))
        self._not_tracked(((1, x), y, (2, 3)))
        self._tracked(([],))
        self._tracked(([1],))
        self._tracked(({},))
        self._tracked((set(),))
        self._tracked((x, y, z))

    def check_track_dynamic(self, tp, always_track):
        x, y, z = 1.5, 'a', []
        check = self._tracked if always_track else self._not_tracked
        check(tp())
        check(tp([]))
        check(tp(set()))
        check(tp([1, x, y]))
        check(tp(obj for obj in [1, x, y]))
        check(tp(set([1, x, y])))
        check(tp(tuple([obj]) for obj in [1, x, y]))
        check(tuple(tp([obj]) for obj in [1, x, y]))
        self._tracked(tp([z]))
        self._tracked(tp([[x, y]]))
        self._tracked(tp([{x: y}]))
        self._tracked(tp(obj for obj in [x, y, z]))
        self._tracked(tp(tuple([obj]) for obj in [x, y, z]))
        self._tracked(tuple(tp([obj]) for obj in [x, y, z]))

    @support.cpython_only
    def test_track_dynamic(self):
        self.check_track_dynamic(tuple, False)

    @support.cpython_only
    def test_track_subtypes(self):


        class MyTuple(tuple):
            pass
        self.check_track_dynamic(MyTuple, True)

    @support.cpython_only
    def test_bug7466(self):
        self._not_tracked(tuple(gc.collect() for i in range(101)))

    def test_repr_large(self):

        def check(n):
            l = (0,) * n
            s = repr(l)
            self.assertEqual(s, '(' + ', '.join(['0'] * n) + ')')
        check(10)
        check(1000000)

    def test_iterator_pickle(self):
        data = self.type2test([4, 5, 6, 7])
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            itorg = iter(data)
            d = pickle.dumps(itorg, proto)
            it = pickle.loads(d)
            self.assertEqual(type(itorg), type(it))
            self.assertEqual(self.type2test(it), self.type2test(data))
            it = pickle.loads(d)
            next(it)
            d = pickle.dumps(it, proto)
            self.assertEqual(self.type2test(it), self.type2test(data)[1:])

    def test_reversed_pickle(self):
        data = self.type2test([4, 5, 6, 7])
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            itorg = reversed(data)
            d = pickle.dumps(itorg, proto)
            it = pickle.loads(d)
            self.assertEqual(type(itorg), type(it))
            self.assertEqual(self.type2test(it), self.type2test(reversed(data))
                )
            it = pickle.loads(d)
            next(it)
            d = pickle.dumps(it, proto)
            self.assertEqual(self.type2test(it), self.type2test(reversed(
                data))[1:])

    def test_no_comdat_folding(self):


        class T(tuple):
            pass
        with self.assertRaises(TypeError):
            [3] + T((1, 2))

    def test_lexicographic_ordering(self):
        a = self.type2test([1, 2])
        b = self.type2test([1, 2, 0])
        c = self.type2test([1, 3])
        self.assertLess(a, b)
        self.assertLess(b, c)


if __name__ == '__main__':
    unittest.main()
