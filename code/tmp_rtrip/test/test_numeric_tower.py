import unittest
import random
import math
import sys
import operator
from decimal import Decimal as D
from fractions import Fraction as F
_PyHASH_MODULUS = sys.hash_info.modulus
_PyHASH_INF = sys.hash_info.inf


class HashTest(unittest.TestCase):

    def check_equal_hash(self, x, y):
        self.assertEqual(hash(x), hash(y),
            'got different hashes for {!r} and {!r}'.format(x, y))
        self.assertEqual(x, y)

    def test_bools(self):
        self.check_equal_hash(False, 0)
        self.check_equal_hash(True, 1)

    def test_integers(self):
        for i in range(-1000, 1000):
            self.check_equal_hash(i, float(i))
            self.check_equal_hash(i, D(i))
            self.check_equal_hash(i, F(i))
        for i in range(100):
            n = 2 ** i - 1
            if n == int(float(n)):
                self.check_equal_hash(n, float(n))
                self.check_equal_hash(-n, -float(n))
            self.check_equal_hash(n, D(n))
            self.check_equal_hash(n, F(n))
            self.check_equal_hash(-n, D(-n))
            self.check_equal_hash(-n, F(-n))
            n = 2 ** i
            self.check_equal_hash(n, float(n))
            self.check_equal_hash(-n, -float(n))
            self.check_equal_hash(n, D(n))
            self.check_equal_hash(n, F(n))
            self.check_equal_hash(-n, D(-n))
            self.check_equal_hash(-n, F(-n))
        for _ in range(1000):
            e = random.randrange(300)
            n = random.randrange(-10 ** e, 10 ** e)
            self.check_equal_hash(n, D(n))
            self.check_equal_hash(n, F(n))
            if n == int(float(n)):
                self.check_equal_hash(n, float(n))

    def test_binary_floats(self):
        self.check_equal_hash(0.0, -0.0)
        self.check_equal_hash(0.0, D(0))
        self.check_equal_hash(-0.0, D(0))
        self.check_equal_hash(-0.0, D('-0.0'))
        self.check_equal_hash(0.0, F(0))
        self.check_equal_hash(float('inf'), D('inf'))
        self.check_equal_hash(float('-inf'), D('-inf'))
        for _ in range(1000):
            x = random.random() * math.exp(random.random() * 200.0 - 100.0)
            self.check_equal_hash(x, D.from_float(x))
            self.check_equal_hash(x, F.from_float(x))

    def test_complex(self):
        test_values = [0.0, -0.0, 1.0, -1.0, 0.40625, -5136.5, float('inf'),
            float('-inf')]
        for zero in (-0.0, 0.0):
            for value in test_values:
                self.check_equal_hash(value, complex(value, zero))

    def test_decimals(self):
        zeros = ['0', '-0', '0.0', '-0.0e10', '000e-10']
        for zero in zeros:
            self.check_equal_hash(D(zero), D(0))
        self.check_equal_hash(D('1.00'), D(1))
        self.check_equal_hash(D('1.00000'), D(1))
        self.check_equal_hash(D('-1.00'), D(-1))
        self.check_equal_hash(D('-1.00000'), D(-1))
        self.check_equal_hash(D('123e2'), D(12300))
        self.check_equal_hash(D('1230e1'), D(12300))
        self.check_equal_hash(D('12300'), D(12300))
        self.check_equal_hash(D('12300.0'), D(12300))
        self.check_equal_hash(D('12300.00'), D(12300))
        self.check_equal_hash(D('12300.000'), D(12300))

    def test_fractions(self):
        self.assertEqual(hash(F(1, _PyHASH_MODULUS)), _PyHASH_INF)
        self.assertEqual(hash(F(-1, 3 * _PyHASH_MODULUS)), -_PyHASH_INF)
        self.assertEqual(hash(F(7 * _PyHASH_MODULUS, 1)), 0)
        self.assertEqual(hash(F(-_PyHASH_MODULUS, 1)), 0)

    def test_hash_normalization(self):


        class HalibutProxy:

            def __hash__(self):
                return hash('halibut')

            def __eq__(self, other):
                return other == 'halibut'
        x = {'halibut', HalibutProxy()}
        self.assertEqual(len(x), 1)


class ComparisonTest(unittest.TestCase):

    def test_mixed_comparisons(self):
        test_values = [float('-inf'), D('-1e425000000'), -1e+308, F(-22, 7),
            -3.14, -2, 0.0, 1e-320, True, F('1.2'), D('1.3'), float('1.4'),
            F(275807, 195025), D('1.414213562373095048801688724'), F(114243,
            80782), F(473596569, 84615), 7e+200, D('infinity')]
        for i, first in enumerate(test_values):
            for second in test_values[i + 1:]:
                self.assertLess(first, second)
                self.assertLessEqual(first, second)
                self.assertGreater(second, first)
                self.assertGreaterEqual(second, first)

    def test_complex(self):
        z = 1.0 + 0j
        w = -3.14 + 2.7j
        for v in (1, 1.0, F(1), D(1), complex(1)):
            self.assertEqual(z, v)
            self.assertEqual(v, z)
        for v in (2, 2.0, F(2), D(2), complex(2)):
            self.assertNotEqual(z, v)
            self.assertNotEqual(v, z)
            self.assertNotEqual(w, v)
            self.assertNotEqual(v, w)
        for v in (1, 1.0, F(1), D(1), complex(1), 2, 2.0, F(2), D(2),
            complex(2), w):
            for op in (operator.le, operator.lt, operator.ge, operator.gt):
                self.assertRaises(TypeError, op, z, v)
                self.assertRaises(TypeError, op, v, z)


if __name__ == '__main__':
    unittest.main()
