from test.support import run_unittest, verbose, requires_IEEE_754
from test import support
import unittest
import math
import os
import platform
import struct
import sys
import sysconfig
eps = 1e-05
NAN = float('nan')
INF = float('inf')
NINF = float('-inf')
FLOAT_MAX = sys.float_info.max
x, y = 1e+16, 2.9999
HAVE_DOUBLE_ROUNDING = x + y == 1e+16 + 4
if __name__ == '__main__':
    file = sys.argv[0]
else:
    file = __file__
test_dir = os.path.dirname(file) or os.curdir
math_testcases = os.path.join(test_dir, 'math_testcases.txt')
test_file = os.path.join(test_dir, 'cmath_testcases.txt')


def to_ulps(x):
    """Convert a non-NaN float x to an integer, in such a way that
    adjacent floats are converted to adjacent integers.  Then
    abs(ulps(x) - ulps(y)) gives the difference in ulps between two
    floats.

    The results from this function will only make sense on platforms
    where native doubles are represented in IEEE 754 binary64 format.

    Note: 0.0 and -0.0 are converted to 0 and -1, respectively.
    """
    n = struct.unpack('<q', struct.pack('<d', x))[0]
    if n < 0:
        n = ~(n + 2 ** 63)
    return n


def ulp(x):
    """Return the value of the least significant bit of a
    float x, such that the first float bigger than x is x+ulp(x).
    Then, given an expected result x and a tolerance of n ulps,
    the result y should be such that abs(y-x) <= n * ulp(x).
    The results from this function will only make sense on platforms
    where native doubles are represented in IEEE 754 binary64 format.
    """
    x = abs(float(x))
    if math.isnan(x) or math.isinf(x):
        return x
    n = struct.unpack('<q', struct.pack('<d', x))[0]
    x_next = struct.unpack('<d', struct.pack('<q', n + 1))[0]
    if math.isinf(x_next):
        x_prev = struct.unpack('<d', struct.pack('<q', n - 1))[0]
        return x - x_prev
    else:
        return x_next - x


def count_set_bits(n):
    """Number of '1' bits in binary expansion of a nonnnegative integer."""
    return 1 + count_set_bits(n & n - 1) if n else 0


def partial_product(start, stop):
    """Product of integers in range(start, stop, 2), computed recursively.
    start and stop should both be odd, with start <= stop.

    """
    numfactors = stop - start >> 1
    if not numfactors:
        return 1
    elif numfactors == 1:
        return start
    else:
        mid = start + numfactors | 1
        return partial_product(start, mid) * partial_product(mid, stop)


def py_factorial(n):
    """Factorial of nonnegative integer n, via "Binary Split Factorial Formula"
    described at http://www.luschny.de/math/factorial/binarysplitfact.html

    """
    inner = outer = 1
    for i in reversed(range(n.bit_length())):
        inner *= partial_product((n >> i + 1) + 1 | 1, (n >> i) + 1 | 1)
        outer *= inner
    return outer << n - count_set_bits(n)


def ulp_abs_check(expected, got, ulp_tol, abs_tol):
    """Given finite floats `expected` and `got`, check that they're
    approximately equal to within the given number of ulps or the
    given absolute tolerance, whichever is bigger.

    Returns None on success and an error message on failure.
    """
    ulp_error = abs(to_ulps(expected) - to_ulps(got))
    abs_error = abs(expected - got)
    if abs_error <= abs_tol or ulp_error <= ulp_tol:
        return None
    else:
        fmt = (
            'error = {:.3g} ({:d} ulps); permitted error = {:.3g} or {:d} ulps'
            )
        return fmt.format(abs_error, ulp_error, abs_tol, ulp_tol)


def parse_mtestfile(fname):
    """Parse a file with test values

    -- starts a comment
    blank lines, or lines containing only a comment, are ignored
    other lines are expected to have the form
      id fn arg -> expected [flag]*

    """
    with open(fname) as fp:
        for line in fp:
            if '--' in line:
                line = line[:line.index('--')]
            if not line.strip():
                continue
            lhs, rhs = line.split('->')
            id, fn, arg = lhs.split()
            rhs_pieces = rhs.split()
            exp = rhs_pieces[0]
            flags = rhs_pieces[1:]
            yield id, fn, float(arg), float(exp), flags


def parse_testfile(fname):
    """Parse a file with test values

    Empty lines or lines starting with -- are ignored
    yields id, fn, arg_real, arg_imag, exp_real, exp_imag
    """
    with open(fname) as fp:
        for line in fp:
            if line.startswith('--') or not line.strip():
                continue
            lhs, rhs = line.split('->')
            id, fn, arg_real, arg_imag = lhs.split()
            rhs_pieces = rhs.split()
            exp_real, exp_imag = rhs_pieces[0], rhs_pieces[1]
            flags = rhs_pieces[2:]
            yield id, fn, float(arg_real), float(arg_imag), float(exp_real
                ), float(exp_imag), flags


def result_check(expected, got, ulp_tol=5, abs_tol=0.0):
    """Compare arguments expected and got, as floats, if either
    is a float, using a tolerance expressed in multiples of
    ulp(expected) or absolutely (if given and greater).

    As a convenience, when neither argument is a float, and for
    non-finite floats, exact equality is demanded. Also, nan==nan
    as far as this function is concerned.

    Returns None on success and an error message on failure.
    """
    if got == expected:
        return None
    failure = 'not equal'
    if isinstance(expected, float) and isinstance(got, int):
        got = float(got)
    elif isinstance(got, float) and isinstance(expected, int):
        expected = float(expected)
    if isinstance(expected, float) and isinstance(got, float):
        if math.isnan(expected) and math.isnan(got):
            failure = None
        elif math.isinf(expected) or math.isinf(got):
            pass
        else:
            failure = ulp_abs_check(expected, got, ulp_tol, abs_tol)
    if failure is not None:
        fail_fmt = 'expected {!r}, got {!r}'
        fail_msg = fail_fmt.format(expected, got)
        fail_msg += ' ({})'.format(failure)
        return fail_msg
    else:
        return None


class MyIndexable(object):

    def __init__(self, value):
        self.value = value

    def __index__(self):
        return self.value


class MathTests(unittest.TestCase):

    def ftest(self, name, got, expected, ulp_tol=5, abs_tol=0.0):
        """Compare arguments expected and got, as floats, if either
        is a float, using a tolerance expressed in multiples of
        ulp(expected) or absolutely, whichever is greater.

        As a convenience, when neither argument is a float, and for
        non-finite floats, exact equality is demanded. Also, nan==nan
        in this function.
        """
        failure = result_check(expected, got, ulp_tol, abs_tol)
        if failure is not None:
            self.fail('{}: {}'.format(name, failure))

    def testConstants(self):
        self.ftest('pi', math.pi, 3.141592653589793)
        self.ftest('e', math.e, 2.718281828459045)
        self.assertEqual(math.tau, 2 * math.pi)

    def testAcos(self):
        self.assertRaises(TypeError, math.acos)
        self.ftest('acos(-1)', math.acos(-1), math.pi)
        self.ftest('acos(0)', math.acos(0), math.pi / 2)
        self.ftest('acos(1)', math.acos(1), 0)
        self.assertRaises(ValueError, math.acos, INF)
        self.assertRaises(ValueError, math.acos, NINF)
        self.assertRaises(ValueError, math.acos, 1 + eps)
        self.assertRaises(ValueError, math.acos, -1 - eps)
        self.assertTrue(math.isnan(math.acos(NAN)))

    def testAcosh(self):
        self.assertRaises(TypeError, math.acosh)
        self.ftest('acosh(1)', math.acosh(1), 0)
        self.ftest('acosh(2)', math.acosh(2), 1.3169578969248168)
        self.assertRaises(ValueError, math.acosh, 0)
        self.assertRaises(ValueError, math.acosh, -1)
        self.assertEqual(math.acosh(INF), INF)
        self.assertRaises(ValueError, math.acosh, NINF)
        self.assertTrue(math.isnan(math.acosh(NAN)))

    def testAsin(self):
        self.assertRaises(TypeError, math.asin)
        self.ftest('asin(-1)', math.asin(-1), -math.pi / 2)
        self.ftest('asin(0)', math.asin(0), 0)
        self.ftest('asin(1)', math.asin(1), math.pi / 2)
        self.assertRaises(ValueError, math.asin, INF)
        self.assertRaises(ValueError, math.asin, NINF)
        self.assertRaises(ValueError, math.asin, 1 + eps)
        self.assertRaises(ValueError, math.asin, -1 - eps)
        self.assertTrue(math.isnan(math.asin(NAN)))

    def testAsinh(self):
        self.assertRaises(TypeError, math.asinh)
        self.ftest('asinh(0)', math.asinh(0), 0)
        self.ftest('asinh(1)', math.asinh(1), 0.881373587019543)
        self.ftest('asinh(-1)', math.asinh(-1), -0.881373587019543)
        self.assertEqual(math.asinh(INF), INF)
        self.assertEqual(math.asinh(NINF), NINF)
        self.assertTrue(math.isnan(math.asinh(NAN)))

    def testAtan(self):
        self.assertRaises(TypeError, math.atan)
        self.ftest('atan(-1)', math.atan(-1), -math.pi / 4)
        self.ftest('atan(0)', math.atan(0), 0)
        self.ftest('atan(1)', math.atan(1), math.pi / 4)
        self.ftest('atan(inf)', math.atan(INF), math.pi / 2)
        self.ftest('atan(-inf)', math.atan(NINF), -math.pi / 2)
        self.assertTrue(math.isnan(math.atan(NAN)))

    def testAtanh(self):
        self.assertRaises(TypeError, math.atan)
        self.ftest('atanh(0)', math.atanh(0), 0)
        self.ftest('atanh(0.5)', math.atanh(0.5), 0.5493061443340549)
        self.ftest('atanh(-0.5)', math.atanh(-0.5), -0.5493061443340549)
        self.assertRaises(ValueError, math.atanh, 1)
        self.assertRaises(ValueError, math.atanh, -1)
        self.assertRaises(ValueError, math.atanh, INF)
        self.assertRaises(ValueError, math.atanh, NINF)
        self.assertTrue(math.isnan(math.atanh(NAN)))

    def testAtan2(self):
        self.assertRaises(TypeError, math.atan2)
        self.ftest('atan2(-1, 0)', math.atan2(-1, 0), -math.pi / 2)
        self.ftest('atan2(-1, 1)', math.atan2(-1, 1), -math.pi / 4)
        self.ftest('atan2(0, 1)', math.atan2(0, 1), 0)
        self.ftest('atan2(1, 1)', math.atan2(1, 1), math.pi / 4)
        self.ftest('atan2(1, 0)', math.atan2(1, 0), math.pi / 2)
        self.ftest('atan2(0., -inf)', math.atan2(0.0, NINF), math.pi)
        self.ftest('atan2(0., -2.3)', math.atan2(0.0, -2.3), math.pi)
        self.ftest('atan2(0., -0.)', math.atan2(0.0, -0.0), math.pi)
        self.assertEqual(math.atan2(0.0, 0.0), 0.0)
        self.assertEqual(math.atan2(0.0, 2.3), 0.0)
        self.assertEqual(math.atan2(0.0, INF), 0.0)
        self.assertTrue(math.isnan(math.atan2(0.0, NAN)))
        self.ftest('atan2(-0., -inf)', math.atan2(-0.0, NINF), -math.pi)
        self.ftest('atan2(-0., -2.3)', math.atan2(-0.0, -2.3), -math.pi)
        self.ftest('atan2(-0., -0.)', math.atan2(-0.0, -0.0), -math.pi)
        self.assertEqual(math.atan2(-0.0, 0.0), -0.0)
        self.assertEqual(math.atan2(-0.0, 2.3), -0.0)
        self.assertEqual(math.atan2(-0.0, INF), -0.0)
        self.assertTrue(math.isnan(math.atan2(-0.0, NAN)))
        self.ftest('atan2(inf, -inf)', math.atan2(INF, NINF), math.pi * 3 / 4)
        self.ftest('atan2(inf, -2.3)', math.atan2(INF, -2.3), math.pi / 2)
        self.ftest('atan2(inf, -0.)', math.atan2(INF, -0.0), math.pi / 2)
        self.ftest('atan2(inf, 0.)', math.atan2(INF, 0.0), math.pi / 2)
        self.ftest('atan2(inf, 2.3)', math.atan2(INF, 2.3), math.pi / 2)
        self.ftest('atan2(inf, inf)', math.atan2(INF, INF), math.pi / 4)
        self.assertTrue(math.isnan(math.atan2(INF, NAN)))
        self.ftest('atan2(-inf, -inf)', math.atan2(NINF, NINF), -math.pi * 
            3 / 4)
        self.ftest('atan2(-inf, -2.3)', math.atan2(NINF, -2.3), -math.pi / 2)
        self.ftest('atan2(-inf, -0.)', math.atan2(NINF, -0.0), -math.pi / 2)
        self.ftest('atan2(-inf, 0.)', math.atan2(NINF, 0.0), -math.pi / 2)
        self.ftest('atan2(-inf, 2.3)', math.atan2(NINF, 2.3), -math.pi / 2)
        self.ftest('atan2(-inf, inf)', math.atan2(NINF, INF), -math.pi / 4)
        self.assertTrue(math.isnan(math.atan2(NINF, NAN)))
        self.ftest('atan2(2.3, -inf)', math.atan2(2.3, NINF), math.pi)
        self.ftest('atan2(2.3, -0.)', math.atan2(2.3, -0.0), math.pi / 2)
        self.ftest('atan2(2.3, 0.)', math.atan2(2.3, 0.0), math.pi / 2)
        self.assertEqual(math.atan2(2.3, INF), 0.0)
        self.assertTrue(math.isnan(math.atan2(2.3, NAN)))
        self.ftest('atan2(-2.3, -inf)', math.atan2(-2.3, NINF), -math.pi)
        self.ftest('atan2(-2.3, -0.)', math.atan2(-2.3, -0.0), -math.pi / 2)
        self.ftest('atan2(-2.3, 0.)', math.atan2(-2.3, 0.0), -math.pi / 2)
        self.assertEqual(math.atan2(-2.3, INF), -0.0)
        self.assertTrue(math.isnan(math.atan2(-2.3, NAN)))
        self.assertTrue(math.isnan(math.atan2(NAN, NINF)))
        self.assertTrue(math.isnan(math.atan2(NAN, -2.3)))
        self.assertTrue(math.isnan(math.atan2(NAN, -0.0)))
        self.assertTrue(math.isnan(math.atan2(NAN, 0.0)))
        self.assertTrue(math.isnan(math.atan2(NAN, 2.3)))
        self.assertTrue(math.isnan(math.atan2(NAN, INF)))
        self.assertTrue(math.isnan(math.atan2(NAN, NAN)))

    def testCeil(self):
        self.assertRaises(TypeError, math.ceil)
        self.assertEqual(int, type(math.ceil(0.5)))
        self.ftest('ceil(0.5)', math.ceil(0.5), 1)
        self.ftest('ceil(1.0)', math.ceil(1.0), 1)
        self.ftest('ceil(1.5)', math.ceil(1.5), 2)
        self.ftest('ceil(-0.5)', math.ceil(-0.5), 0)
        self.ftest('ceil(-1.0)', math.ceil(-1.0), -1)
        self.ftest('ceil(-1.5)', math.ceil(-1.5), -1)


        class TestCeil:

            def __ceil__(self):
                return 42


        class TestNoCeil:
            pass
        self.ftest('ceil(TestCeil())', math.ceil(TestCeil()), 42)
        self.assertRaises(TypeError, math.ceil, TestNoCeil())
        t = TestNoCeil()
        t.__ceil__ = lambda *args: args
        self.assertRaises(TypeError, math.ceil, t)
        self.assertRaises(TypeError, math.ceil, t, 0)

    @requires_IEEE_754
    def testCopysign(self):
        self.assertEqual(math.copysign(1, 42), 1.0)
        self.assertEqual(math.copysign(0.0, 42), 0.0)
        self.assertEqual(math.copysign(1.0, -42), -1.0)
        self.assertEqual(math.copysign(3, 0.0), 3.0)
        self.assertEqual(math.copysign(4.0, -0.0), -4.0)
        self.assertRaises(TypeError, math.copysign)
        self.assertEqual(math.copysign(1.0, 0.0), 1.0)
        self.assertEqual(math.copysign(1.0, -0.0), -1.0)
        self.assertEqual(math.copysign(INF, 0.0), INF)
        self.assertEqual(math.copysign(INF, -0.0), NINF)
        self.assertEqual(math.copysign(NINF, 0.0), INF)
        self.assertEqual(math.copysign(NINF, -0.0), NINF)
        self.assertEqual(math.copysign(1.0, INF), 1.0)
        self.assertEqual(math.copysign(1.0, NINF), -1.0)
        self.assertEqual(math.copysign(INF, INF), INF)
        self.assertEqual(math.copysign(INF, NINF), NINF)
        self.assertEqual(math.copysign(NINF, INF), INF)
        self.assertEqual(math.copysign(NINF, NINF), NINF)
        self.assertTrue(math.isnan(math.copysign(NAN, 1.0)))
        self.assertTrue(math.isnan(math.copysign(NAN, INF)))
        self.assertTrue(math.isnan(math.copysign(NAN, NINF)))
        self.assertTrue(math.isnan(math.copysign(NAN, NAN)))
        self.assertTrue(math.isinf(math.copysign(INF, NAN)))
        self.assertEqual(abs(math.copysign(2.0, NAN)), 2.0)

    def testCos(self):
        self.assertRaises(TypeError, math.cos)
        self.ftest('cos(-pi/2)', math.cos(-math.pi / 2), 0, abs_tol=ulp(1))
        self.ftest('cos(0)', math.cos(0), 1)
        self.ftest('cos(pi/2)', math.cos(math.pi / 2), 0, abs_tol=ulp(1))
        self.ftest('cos(pi)', math.cos(math.pi), -1)
        try:
            self.assertTrue(math.isnan(math.cos(INF)))
            self.assertTrue(math.isnan(math.cos(NINF)))
        except ValueError:
            self.assertRaises(ValueError, math.cos, INF)
            self.assertRaises(ValueError, math.cos, NINF)
        self.assertTrue(math.isnan(math.cos(NAN)))

    def testCosh(self):
        self.assertRaises(TypeError, math.cosh)
        self.ftest('cosh(0)', math.cosh(0), 1)
        self.ftest('cosh(2)-2*cosh(1)**2', math.cosh(2) - 2 * math.cosh(1) **
            2, -1)
        self.assertEqual(math.cosh(INF), INF)
        self.assertEqual(math.cosh(NINF), INF)
        self.assertTrue(math.isnan(math.cosh(NAN)))

    def testDegrees(self):
        self.assertRaises(TypeError, math.degrees)
        self.ftest('degrees(pi)', math.degrees(math.pi), 180.0)
        self.ftest('degrees(pi/2)', math.degrees(math.pi / 2), 90.0)
        self.ftest('degrees(-pi/4)', math.degrees(-math.pi / 4), -45.0)
        self.ftest('degrees(0)', math.degrees(0), 0)

    def testExp(self):
        self.assertRaises(TypeError, math.exp)
        self.ftest('exp(-1)', math.exp(-1), 1 / math.e)
        self.ftest('exp(0)', math.exp(0), 1)
        self.ftest('exp(1)', math.exp(1), math.e)
        self.assertEqual(math.exp(INF), INF)
        self.assertEqual(math.exp(NINF), 0.0)
        self.assertTrue(math.isnan(math.exp(NAN)))
        self.assertRaises(OverflowError, math.exp, 1000000)

    def testFabs(self):
        self.assertRaises(TypeError, math.fabs)
        self.ftest('fabs(-1)', math.fabs(-1), 1)
        self.ftest('fabs(0)', math.fabs(0), 0)
        self.ftest('fabs(1)', math.fabs(1), 1)

    def testFactorial(self):
        self.assertEqual(math.factorial(0), 1)
        self.assertEqual(math.factorial(0.0), 1)
        total = 1
        for i in range(1, 1000):
            total *= i
            self.assertEqual(math.factorial(i), total)
            self.assertEqual(math.factorial(float(i)), total)
            self.assertEqual(math.factorial(i), py_factorial(i))
        self.assertRaises(ValueError, math.factorial, -1)
        self.assertRaises(ValueError, math.factorial, -1.0)
        self.assertRaises(ValueError, math.factorial, -10 ** 100)
        self.assertRaises(ValueError, math.factorial, -1e+100)
        self.assertRaises(ValueError, math.factorial, math.pi)

    @support.cpython_only
    def testFactorialHugeInputs(self):
        self.assertRaises(OverflowError, math.factorial, 10 ** 100)
        self.assertRaises(OverflowError, math.factorial, 1e+100)

    def testFloor(self):
        self.assertRaises(TypeError, math.floor)
        self.assertEqual(int, type(math.floor(0.5)))
        self.ftest('floor(0.5)', math.floor(0.5), 0)
        self.ftest('floor(1.0)', math.floor(1.0), 1)
        self.ftest('floor(1.5)', math.floor(1.5), 1)
        self.ftest('floor(-0.5)', math.floor(-0.5), -1)
        self.ftest('floor(-1.0)', math.floor(-1.0), -1)
        self.ftest('floor(-1.5)', math.floor(-1.5), -2)
        self.ftest('floor(1.23e167)', math.floor(1.23e+167), 1.23e+167)
        self.ftest('floor(-1.23e167)', math.floor(-1.23e+167), -1.23e+167)


        class TestFloor:

            def __floor__(self):
                return 42


        class TestNoFloor:
            pass
        self.ftest('floor(TestFloor())', math.floor(TestFloor()), 42)
        self.assertRaises(TypeError, math.floor, TestNoFloor())
        t = TestNoFloor()
        t.__floor__ = lambda *args: args
        self.assertRaises(TypeError, math.floor, t)
        self.assertRaises(TypeError, math.floor, t, 0)

    def testFmod(self):
        self.assertRaises(TypeError, math.fmod)
        self.ftest('fmod(10, 1)', math.fmod(10, 1), 0.0)
        self.ftest('fmod(10, 0.5)', math.fmod(10, 0.5), 0.0)
        self.ftest('fmod(10, 1.5)', math.fmod(10, 1.5), 1.0)
        self.ftest('fmod(-10, 1)', math.fmod(-10, 1), -0.0)
        self.ftest('fmod(-10, 0.5)', math.fmod(-10, 0.5), -0.0)
        self.ftest('fmod(-10, 1.5)', math.fmod(-10, 1.5), -1.0)
        self.assertTrue(math.isnan(math.fmod(NAN, 1.0)))
        self.assertTrue(math.isnan(math.fmod(1.0, NAN)))
        self.assertTrue(math.isnan(math.fmod(NAN, NAN)))
        self.assertRaises(ValueError, math.fmod, 1.0, 0.0)
        self.assertRaises(ValueError, math.fmod, INF, 1.0)
        self.assertRaises(ValueError, math.fmod, NINF, 1.0)
        self.assertRaises(ValueError, math.fmod, INF, 0.0)
        self.assertEqual(math.fmod(3.0, INF), 3.0)
        self.assertEqual(math.fmod(-3.0, INF), -3.0)
        self.assertEqual(math.fmod(3.0, NINF), 3.0)
        self.assertEqual(math.fmod(-3.0, NINF), -3.0)
        self.assertEqual(math.fmod(0.0, 3.0), 0.0)
        self.assertEqual(math.fmod(0.0, NINF), 0.0)

    def testFrexp(self):
        self.assertRaises(TypeError, math.frexp)

        def testfrexp(name, result, expected):
            (mant, exp), (emant, eexp) = result, expected
            if abs(mant - emant) > eps or exp != eexp:
                self.fail('%s returned %r, expected %r' % (name, result,
                    expected))
        testfrexp('frexp(-1)', math.frexp(-1), (-0.5, 1))
        testfrexp('frexp(0)', math.frexp(0), (0, 0))
        testfrexp('frexp(1)', math.frexp(1), (0.5, 1))
        testfrexp('frexp(2)', math.frexp(2), (0.5, 2))
        self.assertEqual(math.frexp(INF)[0], INF)
        self.assertEqual(math.frexp(NINF)[0], NINF)
        self.assertTrue(math.isnan(math.frexp(NAN)[0]))

    @requires_IEEE_754
    @unittest.skipIf(HAVE_DOUBLE_ROUNDING,
        'fsum is not exact on machines with double rounding')
    def testFsum(self):
        from sys import float_info
        mant_dig = float_info.mant_dig
        etiny = float_info.min_exp - mant_dig

        def msum(iterable):
            """Full precision summation.  Compute sum(iterable) without any
            intermediate accumulation of error.  Based on the 'lsum' function
            at http://code.activestate.com/recipes/393090/

            """
            tmant, texp = 0, 0
            for x in iterable:
                mant, exp = math.frexp(x)
                mant, exp = int(math.ldexp(mant, mant_dig)), exp - mant_dig
                if texp > exp:
                    tmant <<= texp - exp
                    texp = exp
                else:
                    mant <<= exp - texp
                tmant += mant
            tail = max(len(bin(abs(tmant))) - 2 - mant_dig, etiny - texp)
            if tail > 0:
                h = 1 << tail - 1
                tmant = tmant // (2 * h) + bool(tmant & h and tmant & 3 * h - 1
                    )
                texp += tail
            return math.ldexp(tmant, texp)
        test_values = [([], 0.0), ([0.0], 0.0), ([1e+100, 1.0, -1e+100, 
            1e-100, 1e+50, -1.0, -1e+50], 1e-100), ([2.0 ** 53, -0.5, -2.0 **
            -54], 2.0 ** 53 - 1.0), ([2.0 ** 53, 1.0, 2.0 ** -100], 2.0 ** 
            53 + 2.0), ([2.0 ** 53 + 10.0, 1.0, 2.0 ** -100], 2.0 ** 53 + 
            12.0), ([2.0 ** 53 - 4.0, 0.5, 2.0 ** -54], 2.0 ** 53 - 3.0), (
            [(1.0 / n) for n in range(1, 1001)], float.fromhex(
            '0x1.df11f45f4e61ap+2')), ([((-1.0) ** n / n) for n in range(1,
            1001)], float.fromhex('-0x1.62a2af1bd3624p-1')), ([(1.7 ** (i +
            1) - 1.7 ** i) for i in range(1000)] + [-1.7 ** 1000], -1.0), (
            [1e+16, 1.0, 1e-16], 1.0000000000000002e+16), ([1e+16 - 2.0, 
            1.0 - 2.0 ** -53, -(1e+16 - 2.0), -(1.0 - 2.0 ** -53)], 0.0), (
            [(2.0 ** n - 2.0 ** (n + 50) + 2.0 ** (n + 52)) for n in range(
            -1074, 972, 2)] + [-2.0 ** 1022], float.fromhex(
            '0x1.5555555555555p+970'))]
        for i, (vals, expected) in enumerate(test_values):
            try:
                actual = math.fsum(vals)
            except OverflowError:
                self.fail(
                    'test %d failed: got OverflowError, expected %r for math.fsum(%.100r)'
                     % (i, expected, vals))
            except ValueError:
                self.fail(
                    'test %d failed: got ValueError, expected %r for math.fsum(%.100r)'
                     % (i, expected, vals))
            self.assertEqual(actual, expected)
        from random import random, gauss, shuffle
        for j in range(1000):
            vals = [7, 1e+100, -7, -1e+100, -9e-20, 8e-20] * 10
            s = 0
            for i in range(200):
                v = gauss(0, random()) ** 7 - s
                s += v
                vals.append(v)
            shuffle(vals)
            s = msum(vals)
            self.assertEqual(msum(vals), math.fsum(vals))

    def testGcd(self):
        gcd = math.gcd
        self.assertEqual(gcd(0, 0), 0)
        self.assertEqual(gcd(1, 0), 1)
        self.assertEqual(gcd(-1, 0), 1)
        self.assertEqual(gcd(0, 1), 1)
        self.assertEqual(gcd(0, -1), 1)
        self.assertEqual(gcd(7, 1), 1)
        self.assertEqual(gcd(7, -1), 1)
        self.assertEqual(gcd(-23, 15), 1)
        self.assertEqual(gcd(120, 84), 12)
        self.assertEqual(gcd(84, -120), 12)
        self.assertEqual(gcd(1216342683557601535506311712, 
            436522681849110124616458784), 32)
        c = 652560
        x = 434610456570399902378880679233098819019853229470286994367836600566
        y = 1064502245825115327754847244914921553977
        a = x * c
        b = y * c
        self.assertEqual(gcd(a, b), c)
        self.assertEqual(gcd(b, a), c)
        self.assertEqual(gcd(-a, b), c)
        self.assertEqual(gcd(b, -a), c)
        self.assertEqual(gcd(a, -b), c)
        self.assertEqual(gcd(-b, a), c)
        self.assertEqual(gcd(-a, -b), c)
        self.assertEqual(gcd(-b, -a), c)
        c = 576559230871654959816130551884856912003141446781646602790216406874
        a = x * c
        b = y * c
        self.assertEqual(gcd(a, b), c)
        self.assertEqual(gcd(b, a), c)
        self.assertEqual(gcd(-a, b), c)
        self.assertEqual(gcd(b, -a), c)
        self.assertEqual(gcd(a, -b), c)
        self.assertEqual(gcd(-b, a), c)
        self.assertEqual(gcd(-a, -b), c)
        self.assertEqual(gcd(-b, -a), c)
        self.assertRaises(TypeError, gcd, 120.0, 84)
        self.assertRaises(TypeError, gcd, 120, 84.0)
        self.assertEqual(gcd(MyIndexable(120), MyIndexable(84)), 12)

    def testHypot(self):
        self.assertRaises(TypeError, math.hypot)
        self.ftest('hypot(0,0)', math.hypot(0, 0), 0)
        self.ftest('hypot(3,4)', math.hypot(3, 4), 5)
        self.assertEqual(math.hypot(NAN, INF), INF)
        self.assertEqual(math.hypot(INF, NAN), INF)
        self.assertEqual(math.hypot(NAN, NINF), INF)
        self.assertEqual(math.hypot(NINF, NAN), INF)
        self.assertRaises(OverflowError, math.hypot, FLOAT_MAX, FLOAT_MAX)
        self.assertTrue(math.isnan(math.hypot(1.0, NAN)))
        self.assertTrue(math.isnan(math.hypot(NAN, -2.0)))

    def testLdexp(self):
        self.assertRaises(TypeError, math.ldexp)
        self.ftest('ldexp(0,1)', math.ldexp(0, 1), 0)
        self.ftest('ldexp(1,1)', math.ldexp(1, 1), 2)
        self.ftest('ldexp(1,-1)', math.ldexp(1, -1), 0.5)
        self.ftest('ldexp(-1,1)', math.ldexp(-1, 1), -2)
        self.assertRaises(OverflowError, math.ldexp, 1.0, 1000000)
        self.assertRaises(OverflowError, math.ldexp, -1.0, 1000000)
        self.assertEqual(math.ldexp(1.0, -1000000), 0.0)
        self.assertEqual(math.ldexp(-1.0, -1000000), -0.0)
        self.assertEqual(math.ldexp(INF, 30), INF)
        self.assertEqual(math.ldexp(NINF, -213), NINF)
        self.assertTrue(math.isnan(math.ldexp(NAN, 0)))
        for n in [10 ** 5, 10 ** 10, 10 ** 20, 10 ** 40]:
            self.assertEqual(math.ldexp(INF, -n), INF)
            self.assertEqual(math.ldexp(NINF, -n), NINF)
            self.assertEqual(math.ldexp(1.0, -n), 0.0)
            self.assertEqual(math.ldexp(-1.0, -n), -0.0)
            self.assertEqual(math.ldexp(0.0, -n), 0.0)
            self.assertEqual(math.ldexp(-0.0, -n), -0.0)
            self.assertTrue(math.isnan(math.ldexp(NAN, -n)))
            self.assertRaises(OverflowError, math.ldexp, 1.0, n)
            self.assertRaises(OverflowError, math.ldexp, -1.0, n)
            self.assertEqual(math.ldexp(0.0, n), 0.0)
            self.assertEqual(math.ldexp(-0.0, n), -0.0)
            self.assertEqual(math.ldexp(INF, n), INF)
            self.assertEqual(math.ldexp(NINF, n), NINF)
            self.assertTrue(math.isnan(math.ldexp(NAN, n)))

    def testLog(self):
        self.assertRaises(TypeError, math.log)
        self.ftest('log(1/e)', math.log(1 / math.e), -1)
        self.ftest('log(1)', math.log(1), 0)
        self.ftest('log(e)', math.log(math.e), 1)
        self.ftest('log(32,2)', math.log(32, 2), 5)
        self.ftest('log(10**40, 10)', math.log(10 ** 40, 10), 40)
        self.ftest('log(10**40, 10**20)', math.log(10 ** 40, 10 ** 20), 2)
        self.ftest('log(10**1000)', math.log(10 ** 1000), 2302.5850929940457)
        self.assertRaises(ValueError, math.log, -1.5)
        self.assertRaises(ValueError, math.log, -10 ** 1000)
        self.assertRaises(ValueError, math.log, NINF)
        self.assertEqual(math.log(INF), INF)
        self.assertTrue(math.isnan(math.log(NAN)))

    def testLog1p(self):
        self.assertRaises(TypeError, math.log1p)
        for n in [2, 2 ** 90, 2 ** 300]:
            self.assertAlmostEqual(math.log1p(n), math.log1p(float(n)))
        self.assertRaises(ValueError, math.log1p, -1)
        self.assertEqual(math.log1p(INF), INF)

    @requires_IEEE_754
    def testLog2(self):
        self.assertRaises(TypeError, math.log2)
        self.assertEqual(math.log2(1), 0.0)
        self.assertEqual(math.log2(2), 1.0)
        self.assertEqual(math.log2(4), 2.0)
        self.assertEqual(math.log2(2 ** 1023), 1023.0)
        self.assertEqual(math.log2(2 ** 1024), 1024.0)
        self.assertEqual(math.log2(2 ** 2000), 2000.0)
        self.assertRaises(ValueError, math.log2, -1.5)
        self.assertRaises(ValueError, math.log2, NINF)
        self.assertTrue(math.isnan(math.log2(NAN)))

    @requires_IEEE_754
    @support.requires_mac_ver(10, 5)
    def testLog2Exact(self):
        actual = [math.log2(math.ldexp(1.0, n)) for n in range(-1074, 1024)]
        expected = [float(n) for n in range(-1074, 1024)]
        self.assertEqual(actual, expected)

    def testLog10(self):
        self.assertRaises(TypeError, math.log10)
        self.ftest('log10(0.1)', math.log10(0.1), -1)
        self.ftest('log10(1)', math.log10(1), 0)
        self.ftest('log10(10)', math.log10(10), 1)
        self.ftest('log10(10**1000)', math.log10(10 ** 1000), 1000.0)
        self.assertRaises(ValueError, math.log10, -1.5)
        self.assertRaises(ValueError, math.log10, -10 ** 1000)
        self.assertRaises(ValueError, math.log10, NINF)
        self.assertEqual(math.log(INF), INF)
        self.assertTrue(math.isnan(math.log10(NAN)))

    def testModf(self):
        self.assertRaises(TypeError, math.modf)

        def testmodf(name, result, expected):
            (v1, v2), (e1, e2) = result, expected
            if abs(v1 - e1) > eps or abs(v2 - e2):
                self.fail('%s returned %r, expected %r' % (name, result,
                    expected))
        testmodf('modf(1.5)', math.modf(1.5), (0.5, 1.0))
        testmodf('modf(-1.5)', math.modf(-1.5), (-0.5, -1.0))
        self.assertEqual(math.modf(INF), (0.0, INF))
        self.assertEqual(math.modf(NINF), (-0.0, NINF))
        modf_nan = math.modf(NAN)
        self.assertTrue(math.isnan(modf_nan[0]))
        self.assertTrue(math.isnan(modf_nan[1]))

    def testPow(self):
        self.assertRaises(TypeError, math.pow)
        self.ftest('pow(0,1)', math.pow(0, 1), 0)
        self.ftest('pow(1,0)', math.pow(1, 0), 1)
        self.ftest('pow(2,1)', math.pow(2, 1), 2)
        self.ftest('pow(2,-1)', math.pow(2, -1), 0.5)
        self.assertEqual(math.pow(INF, 1), INF)
        self.assertEqual(math.pow(NINF, 1), NINF)
        self.assertEqual(math.pow(1, INF), 1.0)
        self.assertEqual(math.pow(1, NINF), 1.0)
        self.assertTrue(math.isnan(math.pow(NAN, 1)))
        self.assertTrue(math.isnan(math.pow(2, NAN)))
        self.assertTrue(math.isnan(math.pow(0, NAN)))
        self.assertEqual(math.pow(1, NAN), 1)
        self.assertEqual(math.pow(0.0, INF), 0.0)
        self.assertEqual(math.pow(0.0, 3.0), 0.0)
        self.assertEqual(math.pow(0.0, 2.3), 0.0)
        self.assertEqual(math.pow(0.0, 2.0), 0.0)
        self.assertEqual(math.pow(0.0, 0.0), 1.0)
        self.assertEqual(math.pow(0.0, -0.0), 1.0)
        self.assertRaises(ValueError, math.pow, 0.0, -2.0)
        self.assertRaises(ValueError, math.pow, 0.0, -2.3)
        self.assertRaises(ValueError, math.pow, 0.0, -3.0)
        self.assertRaises(ValueError, math.pow, 0.0, NINF)
        self.assertTrue(math.isnan(math.pow(0.0, NAN)))
        self.assertEqual(math.pow(INF, INF), INF)
        self.assertEqual(math.pow(INF, 3.0), INF)
        self.assertEqual(math.pow(INF, 2.3), INF)
        self.assertEqual(math.pow(INF, 2.0), INF)
        self.assertEqual(math.pow(INF, 0.0), 1.0)
        self.assertEqual(math.pow(INF, -0.0), 1.0)
        self.assertEqual(math.pow(INF, -2.0), 0.0)
        self.assertEqual(math.pow(INF, -2.3), 0.0)
        self.assertEqual(math.pow(INF, -3.0), 0.0)
        self.assertEqual(math.pow(INF, NINF), 0.0)
        self.assertTrue(math.isnan(math.pow(INF, NAN)))
        self.assertEqual(math.pow(-0.0, INF), 0.0)
        self.assertEqual(math.pow(-0.0, 3.0), -0.0)
        self.assertEqual(math.pow(-0.0, 2.3), 0.0)
        self.assertEqual(math.pow(-0.0, 2.0), 0.0)
        self.assertEqual(math.pow(-0.0, 0.0), 1.0)
        self.assertEqual(math.pow(-0.0, -0.0), 1.0)
        self.assertRaises(ValueError, math.pow, -0.0, -2.0)
        self.assertRaises(ValueError, math.pow, -0.0, -2.3)
        self.assertRaises(ValueError, math.pow, -0.0, -3.0)
        self.assertRaises(ValueError, math.pow, -0.0, NINF)
        self.assertTrue(math.isnan(math.pow(-0.0, NAN)))
        self.assertEqual(math.pow(NINF, INF), INF)
        self.assertEqual(math.pow(NINF, 3.0), NINF)
        self.assertEqual(math.pow(NINF, 2.3), INF)
        self.assertEqual(math.pow(NINF, 2.0), INF)
        self.assertEqual(math.pow(NINF, 0.0), 1.0)
        self.assertEqual(math.pow(NINF, -0.0), 1.0)
        self.assertEqual(math.pow(NINF, -2.0), 0.0)
        self.assertEqual(math.pow(NINF, -2.3), 0.0)
        self.assertEqual(math.pow(NINF, -3.0), -0.0)
        self.assertEqual(math.pow(NINF, NINF), 0.0)
        self.assertTrue(math.isnan(math.pow(NINF, NAN)))
        self.assertEqual(math.pow(-1.0, INF), 1.0)
        self.assertEqual(math.pow(-1.0, 3.0), -1.0)
        self.assertRaises(ValueError, math.pow, -1.0, 2.3)
        self.assertEqual(math.pow(-1.0, 2.0), 1.0)
        self.assertEqual(math.pow(-1.0, 0.0), 1.0)
        self.assertEqual(math.pow(-1.0, -0.0), 1.0)
        self.assertEqual(math.pow(-1.0, -2.0), 1.0)
        self.assertRaises(ValueError, math.pow, -1.0, -2.3)
        self.assertEqual(math.pow(-1.0, -3.0), -1.0)
        self.assertEqual(math.pow(-1.0, NINF), 1.0)
        self.assertTrue(math.isnan(math.pow(-1.0, NAN)))
        self.assertEqual(math.pow(1.0, INF), 1.0)
        self.assertEqual(math.pow(1.0, 3.0), 1.0)
        self.assertEqual(math.pow(1.0, 2.3), 1.0)
        self.assertEqual(math.pow(1.0, 2.0), 1.0)
        self.assertEqual(math.pow(1.0, 0.0), 1.0)
        self.assertEqual(math.pow(1.0, -0.0), 1.0)
        self.assertEqual(math.pow(1.0, -2.0), 1.0)
        self.assertEqual(math.pow(1.0, -2.3), 1.0)
        self.assertEqual(math.pow(1.0, -3.0), 1.0)
        self.assertEqual(math.pow(1.0, NINF), 1.0)
        self.assertEqual(math.pow(1.0, NAN), 1.0)
        self.assertEqual(math.pow(2.3, 0.0), 1.0)
        self.assertEqual(math.pow(-2.3, 0.0), 1.0)
        self.assertEqual(math.pow(NAN, 0.0), 1.0)
        self.assertEqual(math.pow(2.3, -0.0), 1.0)
        self.assertEqual(math.pow(-2.3, -0.0), 1.0)
        self.assertEqual(math.pow(NAN, -0.0), 1.0)
        self.assertRaises(ValueError, math.pow, -1.0, 2.3)
        self.assertRaises(ValueError, math.pow, -15.0, -3.1)
        self.assertEqual(math.pow(1.9, NINF), 0.0)
        self.assertEqual(math.pow(1.1, NINF), 0.0)
        self.assertEqual(math.pow(0.9, NINF), INF)
        self.assertEqual(math.pow(0.1, NINF), INF)
        self.assertEqual(math.pow(-0.1, NINF), INF)
        self.assertEqual(math.pow(-0.9, NINF), INF)
        self.assertEqual(math.pow(-1.1, NINF), 0.0)
        self.assertEqual(math.pow(-1.9, NINF), 0.0)
        self.assertEqual(math.pow(1.9, INF), INF)
        self.assertEqual(math.pow(1.1, INF), INF)
        self.assertEqual(math.pow(0.9, INF), 0.0)
        self.assertEqual(math.pow(0.1, INF), 0.0)
        self.assertEqual(math.pow(-0.1, INF), 0.0)
        self.assertEqual(math.pow(-0.9, INF), 0.0)
        self.assertEqual(math.pow(-1.1, INF), INF)
        self.assertEqual(math.pow(-1.9, INF), INF)
        self.ftest('(-2.)**3.', math.pow(-2.0, 3.0), -8.0)
        self.ftest('(-2.)**2.', math.pow(-2.0, 2.0), 4.0)
        self.ftest('(-2.)**1.', math.pow(-2.0, 1.0), -2.0)
        self.ftest('(-2.)**0.', math.pow(-2.0, 0.0), 1.0)
        self.ftest('(-2.)**-0.', math.pow(-2.0, -0.0), 1.0)
        self.ftest('(-2.)**-1.', math.pow(-2.0, -1.0), -0.5)
        self.ftest('(-2.)**-2.', math.pow(-2.0, -2.0), 0.25)
        self.ftest('(-2.)**-3.', math.pow(-2.0, -3.0), -0.125)
        self.assertRaises(ValueError, math.pow, -2.0, -0.5)
        self.assertRaises(ValueError, math.pow, -2.0, 0.5)

    def testRadians(self):
        self.assertRaises(TypeError, math.radians)
        self.ftest('radians(180)', math.radians(180), math.pi)
        self.ftest('radians(90)', math.radians(90), math.pi / 2)
        self.ftest('radians(-45)', math.radians(-45), -math.pi / 4)
        self.ftest('radians(0)', math.radians(0), 0)

    def testSin(self):
        self.assertRaises(TypeError, math.sin)
        self.ftest('sin(0)', math.sin(0), 0)
        self.ftest('sin(pi/2)', math.sin(math.pi / 2), 1)
        self.ftest('sin(-pi/2)', math.sin(-math.pi / 2), -1)
        try:
            self.assertTrue(math.isnan(math.sin(INF)))
            self.assertTrue(math.isnan(math.sin(NINF)))
        except ValueError:
            self.assertRaises(ValueError, math.sin, INF)
            self.assertRaises(ValueError, math.sin, NINF)
        self.assertTrue(math.isnan(math.sin(NAN)))

    def testSinh(self):
        self.assertRaises(TypeError, math.sinh)
        self.ftest('sinh(0)', math.sinh(0), 0)
        self.ftest('sinh(1)**2-cosh(1)**2', math.sinh(1) ** 2 - math.cosh(1
            ) ** 2, -1)
        self.ftest('sinh(1)+sinh(-1)', math.sinh(1) + math.sinh(-1), 0)
        self.assertEqual(math.sinh(INF), INF)
        self.assertEqual(math.sinh(NINF), NINF)
        self.assertTrue(math.isnan(math.sinh(NAN)))

    def testSqrt(self):
        self.assertRaises(TypeError, math.sqrt)
        self.ftest('sqrt(0)', math.sqrt(0), 0)
        self.ftest('sqrt(1)', math.sqrt(1), 1)
        self.ftest('sqrt(4)', math.sqrt(4), 2)
        self.assertEqual(math.sqrt(INF), INF)
        self.assertRaises(ValueError, math.sqrt, -1)
        self.assertRaises(ValueError, math.sqrt, NINF)
        self.assertTrue(math.isnan(math.sqrt(NAN)))

    def testTan(self):
        self.assertRaises(TypeError, math.tan)
        self.ftest('tan(0)', math.tan(0), 0)
        self.ftest('tan(pi/4)', math.tan(math.pi / 4), 1)
        self.ftest('tan(-pi/4)', math.tan(-math.pi / 4), -1)
        try:
            self.assertTrue(math.isnan(math.tan(INF)))
            self.assertTrue(math.isnan(math.tan(NINF)))
        except:
            self.assertRaises(ValueError, math.tan, INF)
            self.assertRaises(ValueError, math.tan, NINF)
        self.assertTrue(math.isnan(math.tan(NAN)))

    def testTanh(self):
        self.assertRaises(TypeError, math.tanh)
        self.ftest('tanh(0)', math.tanh(0), 0)
        self.ftest('tanh(1)+tanh(-1)', math.tanh(1) + math.tanh(-1), 0,
            abs_tol=ulp(1))
        self.ftest('tanh(inf)', math.tanh(INF), 1)
        self.ftest('tanh(-inf)', math.tanh(NINF), -1)
        self.assertTrue(math.isnan(math.tanh(NAN)))

    @requires_IEEE_754
    @unittest.skipIf(sysconfig.get_config_var('TANH_PRESERVES_ZERO_SIGN') ==
        0, "system tanh() function doesn't copy the sign")
    def testTanhSign(self):
        self.assertEqual(math.tanh(-0.0), -0.0)
        self.assertEqual(math.copysign(1.0, math.tanh(-0.0)), math.copysign
            (1.0, -0.0))

    def test_trunc(self):
        self.assertEqual(math.trunc(1), 1)
        self.assertEqual(math.trunc(-1), -1)
        self.assertEqual(type(math.trunc(1)), int)
        self.assertEqual(type(math.trunc(1.5)), int)
        self.assertEqual(math.trunc(1.5), 1)
        self.assertEqual(math.trunc(-1.5), -1)
        self.assertEqual(math.trunc(1.999999), 1)
        self.assertEqual(math.trunc(-1.999999), -1)
        self.assertEqual(math.trunc(-0.999999), -0)
        self.assertEqual(math.trunc(-100.999), -100)


        class TestTrunc(object):

            def __trunc__(self):
                return 23


        class TestNoTrunc(object):
            pass
        self.assertEqual(math.trunc(TestTrunc()), 23)
        self.assertRaises(TypeError, math.trunc)
        self.assertRaises(TypeError, math.trunc, 1, 2)
        self.assertRaises(TypeError, math.trunc, TestNoTrunc())

    def testIsfinite(self):
        self.assertTrue(math.isfinite(0.0))
        self.assertTrue(math.isfinite(-0.0))
        self.assertTrue(math.isfinite(1.0))
        self.assertTrue(math.isfinite(-1.0))
        self.assertFalse(math.isfinite(float('nan')))
        self.assertFalse(math.isfinite(float('inf')))
        self.assertFalse(math.isfinite(float('-inf')))

    def testIsnan(self):
        self.assertTrue(math.isnan(float('nan')))
        self.assertTrue(math.isnan(float('-nan')))
        self.assertTrue(math.isnan(float('inf') * 0.0))
        self.assertFalse(math.isnan(float('inf')))
        self.assertFalse(math.isnan(0.0))
        self.assertFalse(math.isnan(1.0))

    def testIsinf(self):
        self.assertTrue(math.isinf(float('inf')))
        self.assertTrue(math.isinf(float('-inf')))
        self.assertTrue(math.isinf(1e1000))
        self.assertTrue(math.isinf(-1e1000))
        self.assertFalse(math.isinf(float('nan')))
        self.assertFalse(math.isinf(0.0))
        self.assertFalse(math.isinf(1.0))

    @requires_IEEE_754
    def test_nan_constant(self):
        self.assertTrue(math.isnan(math.nan))

    @requires_IEEE_754
    def test_inf_constant(self):
        self.assertTrue(math.isinf(math.inf))
        self.assertGreater(math.inf, 0.0)
        self.assertEqual(math.inf, float('inf'))
        self.assertEqual(-math.inf, float('-inf'))

    @unittest.skipUnless(verbose, 'requires verbose mode')
    def test_exceptions(self):
        try:
            x = math.exp(-1000000000)
        except:
            self.fail('underflowing exp() should not have raised an exception')
        if x != 0:
            self.fail('underflowing exp() should have returned 0')
        try:
            x = math.exp(1000000000)
        except OverflowError:
            pass
        else:
            self.fail("overflowing exp() didn't trigger OverflowError")
        try:
            x = math.sqrt(-1.0)
        except ValueError:
            pass
        else:
            self.fail("sqrt(-1) didn't raise ValueError")

    @requires_IEEE_754
    def test_testfile(self):
        SKIP_ON_TIGER = {'tan0064'}
        osx_version = None
        if sys.platform == 'darwin':
            version_txt = platform.mac_ver()[0]
            try:
                osx_version = tuple(map(int, version_txt.split('.')))
            except ValueError:
                pass
        fail_fmt = '{}: {}({!r}): {}'
        failures = []
        for id, fn, ar, ai, er, ei, flags in parse_testfile(test_file):
            if ai != 0.0 or ei != 0.0:
                continue
            if fn in ['rect', 'polar']:
                continue
            if osx_version is not None and osx_version < (10, 5):
                if id in SKIP_ON_TIGER:
                    continue
            func = getattr(math, fn)
            if 'invalid' in flags or 'divide-by-zero' in flags:
                er = 'ValueError'
            elif 'overflow' in flags:
                er = 'OverflowError'
            try:
                result = func(ar)
            except ValueError:
                result = 'ValueError'
            except OverflowError:
                result = 'OverflowError'
            ulp_tol, abs_tol = 5, 0.0
            failure = result_check(er, result, ulp_tol, abs_tol)
            if failure is None:
                continue
            msg = fail_fmt.format(id, fn, ar, failure)
            failures.append(msg)
        if failures:
            self.fail('Failures in test_testfile:\n  ' + '\n  '.join(failures))

    @requires_IEEE_754
    def test_mtestfile(self):
        fail_fmt = '{}: {}({!r}): {}'
        failures = []
        for id, fn, arg, expected, flags in parse_mtestfile(math_testcases):
            func = getattr(math, fn)
            if 'invalid' in flags or 'divide-by-zero' in flags:
                expected = 'ValueError'
            elif 'overflow' in flags:
                expected = 'OverflowError'
            try:
                got = func(arg)
            except ValueError:
                got = 'ValueError'
            except OverflowError:
                got = 'OverflowError'
            ulp_tol, abs_tol = 5, 0.0
            if fn == 'gamma':
                ulp_tol = 20
            elif fn == 'lgamma':
                abs_tol = 1e-15
            elif fn == 'erfc' and arg >= 0.0:
                if arg < 1.0:
                    ulp_tol = 10
                elif arg < 10.0:
                    ulp_tol = 100
                else:
                    ulp_tol = 1000
            failure = result_check(expected, got, ulp_tol, abs_tol)
            if failure is None:
                continue
            msg = fail_fmt.format(id, fn, arg, failure)
            failures.append(msg)
        if failures:
            self.fail('Failures in test_mtestfile:\n  ' + '\n  '.join(failures)
                )


class IsCloseTests(unittest.TestCase):
    isclose = math.isclose

    def assertIsClose(self, a, b, *args, **kwargs):
        self.assertTrue(self.isclose(a, b, *args, **kwargs), msg=
            '%s and %s should be close!' % (a, b))

    def assertIsNotClose(self, a, b, *args, **kwargs):
        self.assertFalse(self.isclose(a, b, *args, **kwargs), msg=
            '%s and %s should not be close!' % (a, b))

    def assertAllClose(self, examples, *args, **kwargs):
        for a, b in examples:
            self.assertIsClose(a, b, *args, **kwargs)

    def assertAllNotClose(self, examples, *args, **kwargs):
        for a, b in examples:
            self.assertIsNotClose(a, b, *args, **kwargs)

    def test_negative_tolerances(self):
        with self.assertRaises(ValueError):
            self.assertIsClose(1, 1, rel_tol=-1e-100)
        with self.assertRaises(ValueError):
            self.assertIsClose(1, 1, rel_tol=1e-100, abs_tol=-10000000000.0)

    def test_identical(self):
        identical_examples = [(2.0, 2.0), (1e+199, 1e+199), (1.123e-300, 
            1.123e-300), (12345, 12345.0), (0.0, -0.0), (345678, 345678)]
        self.assertAllClose(identical_examples, rel_tol=0.0, abs_tol=0.0)

    def test_eight_decimal_places(self):
        eight_decimal_places_examples = [(100000000.0, 100000000.0 + 1), (-
            1e-08, -1.000000009e-08), (1.12345678, 1.12345679)]
        self.assertAllClose(eight_decimal_places_examples, rel_tol=1e-08)
        self.assertAllNotClose(eight_decimal_places_examples, rel_tol=1e-09)

    def test_near_zero(self):
        near_zero_examples = [(1e-09, 0.0), (-1e-09, 0.0), (-1e-150, 0.0)]
        self.assertAllNotClose(near_zero_examples, rel_tol=0.9)
        self.assertAllClose(near_zero_examples, abs_tol=1e-08)

    def test_identical_infinite(self):
        self.assertIsClose(INF, INF)
        self.assertIsClose(INF, INF, abs_tol=0.0)
        self.assertIsClose(NINF, NINF)
        self.assertIsClose(NINF, NINF, abs_tol=0.0)

    def test_inf_ninf_nan(self):
        not_close_examples = [(NAN, NAN), (NAN, 1e-100), (1e-100, NAN), (
            INF, NAN), (NAN, INF), (INF, NINF), (INF, 1.0), (1.0, INF), (
            INF, 1e+308), (1e+308, INF)]
        self.assertAllNotClose(not_close_examples, abs_tol=0.999999999999999)

    def test_zero_tolerance(self):
        zero_tolerance_close_examples = [(1.0, 1.0), (-3.4, -3.4), (-1e-300,
            -1e-300)]
        self.assertAllClose(zero_tolerance_close_examples, rel_tol=0.0)
        zero_tolerance_not_close_examples = [(1.0, 1.000000000000001), (
            0.99999999999999, 1.0), (1e+200, 9.99999999999999e+199)]
        self.assertAllNotClose(zero_tolerance_not_close_examples, rel_tol=0.0)

    def test_asymmetry(self):
        self.assertAllClose([(9, 10), (10, 9)], rel_tol=0.1)

    def test_integers(self):
        integer_examples = [(100000001, 100000000), (123456789, 123456788)]
        self.assertAllClose(integer_examples, rel_tol=1e-08)
        self.assertAllNotClose(integer_examples, rel_tol=1e-09)

    def test_decimals(self):
        from decimal import Decimal
        decimal_examples = [(Decimal('1.00000001'), Decimal('1.0')), (
            Decimal('1.00000001e-20'), Decimal('1.0e-20')), (Decimal(
            '1.00000001e-100'), Decimal('1.0e-100')), (Decimal(
            '1.00000001e20'), Decimal('1.0e20'))]
        self.assertAllClose(decimal_examples, rel_tol=1e-08)
        self.assertAllNotClose(decimal_examples, rel_tol=1e-09)

    def test_fractions(self):
        from fractions import Fraction
        fraction_examples = [(Fraction(1, 100000000) + 1, Fraction(1)), (
            Fraction(100000001), Fraction(100000000)), (Fraction(10 ** 8 + 
            1, 10 ** 28), Fraction(1, 10 ** 20))]
        self.assertAllClose(fraction_examples, rel_tol=1e-08)
        self.assertAllNotClose(fraction_examples, rel_tol=1e-09)


def test_main():
    from doctest import DocFileSuite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MathTests))
    suite.addTest(unittest.makeSuite(IsCloseTests))
    suite.addTest(DocFileSuite('ieee754.txt'))
    run_unittest(suite)


if __name__ == '__main__':
    test_main()
