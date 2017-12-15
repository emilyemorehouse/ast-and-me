from test.support import run_unittest, check_syntax_error
import unittest
import sys
from sys import *


class TokenTests(unittest.TestCase):

    def testBackslash(self):
        x = 1 + 1
        self.assertEquals(x, 2, 'backslash for line continuation')
        x = 0
        self.assertEquals(x, 0, 'backslash ending comment')

    def testPlainIntegers(self):
        self.assertEquals(type(0), type(0))
        self.assertEquals(255, 255)
        self.assertEquals(255, 255)
        self.assertEquals(2147483647, 2147483647)
        self.assertEquals(9, 9)
        self.assertRaises(SyntaxError, eval, '0x')
        from sys import maxsize
        if maxsize == 2147483647:
            self.assertEquals(-2147483647 - 1, -2147483648)
            self.assert_(4294967295 > 0)
            self.assert_(4294967295 > 0)
            self.assert_(2147483647 > 0)
            for s in ('2147483648', '0o40000000000', '0x100000000',
                '0b10000000000000000000000000000000'):
                try:
                    x = eval(s)
                except OverflowError:
                    self.fail('OverflowError on huge integer literal %r' % s)
        elif maxsize == 9223372036854775807:
            self.assertEquals(-9223372036854775807 - 1, -9223372036854775808)
            self.assert_(18446744073709551615 > 0)
            self.assert_(18446744073709551615 > 0)
            self.assert_(4611686018427387903 > 0)
            for s in ('9223372036854775808', '0o2000000000000000000000',
                '0x10000000000000000',
                '0b100000000000000000000000000000000000000000000000000000000000000'
                ):
                try:
                    x = eval(s)
                except OverflowError:
                    self.fail('OverflowError on huge integer literal %r' % s)
        else:
            self.fail('Weird maxsize value %r' % maxsize)

    def testLongIntegers(self):
        x = 0
        x = 18446744073709551615
        x = 18446744073709551615
        x = 2251799813685247
        x = 2251799813685247
        x = 123456789012345678901234567890
        x = 295147905179352825856
        x = 590295810358705651711

    def testUnderscoresInNumbers(self):
        x = 10
        x = 123456789
        x = 2881561413
        x = 11256099
        x = 13
        x = 13
        x = 2423
        x = 2423
        x = 31.4
        x = 31.4
        x = 31.0
        x = 0.31
        x = 3.14
        x = 3.14
        x = 300000000000000.0
        x = 3.1e+42
        x = 3.1e-40

    def testFloats(self):
        x = 3.14
        x = 314.0
        x = 0.314
        x = 0.314
        x = 300000000000000.0
        x = 300000000000000.0
        x = 3e-14
        x = 300000000000000.0
        x = 300000000000000.0
        x = 30000000000000.0
        x = 31000.0

    def testStringLiterals(self):
        x = ''
        y = ''
        self.assert_(len(x) == 0 and x == y)
        x = "'"
        y = "'"
        self.assert_(len(x) == 1 and x == y and ord(x) == 39)
        x = '"'
        y = '"'
        self.assert_(len(x) == 1 and x == y and ord(x) == 34)
        x = 'doesn\'t "shrink" does it'
        y = 'doesn\'t "shrink" does it'
        self.assert_(len(x) == 24 and x == y)
        x = 'does "shrink" doesn\'t it'
        y = 'does "shrink" doesn\'t it'
        self.assert_(len(x) == 24 and x == y)
        x = '\nThe "quick"\nbrown fox\njumps over\nthe \'lazy\' dog.\n'
        y = '\nThe "quick"\nbrown fox\njumps over\nthe \'lazy\' dog.\n'
        self.assertEquals(x, y)
        y = '\nThe "quick"\nbrown fox\njumps over\nthe \'lazy\' dog.\n'
        self.assertEquals(x, y)
        y = '\nThe "quick"\nbrown fox\njumps over\nthe \'lazy\' dog.\n'
        self.assertEquals(x, y)
        y = '\nThe "quick"\nbrown fox\njumps over\nthe \'lazy\' dog.\n'
        self.assertEquals(x, y)

    def testEllipsis(self):
        x = ...
        self.assert_(x is Ellipsis)
        self.assertRaises(SyntaxError, eval, '.. .')


class GrammarTests(unittest.TestCase):

    def testEvalInput(self):
        x = eval('1, 0 or 1')

    def testFuncdef(self):

        def f1():
            pass
        f1()
        f1(*())
        f1(*(), **{})

        def f2(one_argument):
            pass

        def f3(two, arguments):
            pass
        self.assertEquals(f2.__code__.co_varnames, ('one_argument',))
        self.assertEquals(f3.__code__.co_varnames, ('two', 'arguments'))

        def a1(one_arg):
            pass

        def a2(two, args):
            pass

        def v0(*rest):
            pass

        def v1(a, *rest):
            pass

        def v2(a, b, *rest):
            pass
        f1()
        f2(1)
        f2(1)
        f3(1, 2)
        f3(1, 2)
        v0()
        v0(1)
        v0(1)
        v0(1, 2)
        v0(1, 2, 3, 4, 5, 6, 7, 8, 9, 0)
        v1(1)
        v1(1)
        v1(1, 2)
        v1(1, 2, 3)
        v1(1, 2, 3, 4, 5, 6, 7, 8, 9, 0)
        v2(1, 2)
        v2(1, 2, 3)
        v2(1, 2, 3, 4)
        v2(1, 2, 3, 4, 5, 6, 7, 8, 9, 0)

        def d01(a=1):
            pass
        d01()
        d01(1)
        d01(*(1,))
        d01(**{'a': 2})

        def d11(a, b=1):
            pass
        d11(1)
        d11(1, 2)
        d11(1, **{'b': 2})

        def d21(a, b, c=1):
            pass
        d21(1, 2)
        d21(1, 2, 3)
        d21(*(1, 2, 3))
        d21(1, *(2, 3))
        d21(1, 2, *(3,))
        d21(1, 2, **{'c': 3})

        def d02(a=1, b=2):
            pass
        d02()
        d02(1)
        d02(1, 2)
        d02(*(1, 2))
        d02(1, *(2,))
        d02(1, **{'b': 2})
        d02(**{'a': 1, 'b': 2})

        def d12(a, b=1, c=2):
            pass
        d12(1)
        d12(1, 2)
        d12(1, 2, 3)

        def d22(a, b, c=1, d=2):
            pass
        d22(1, 2)
        d22(1, 2, 3)
        d22(1, 2, 3, 4)

        def d01v(a=1, *rest):
            pass
        d01v()
        d01v(1)
        d01v(1, 2)
        d01v(*(1, 2, 3, 4))
        d01v(*(1,))
        d01v(**{'a': 2})

        def d11v(a, b=1, *rest):
            pass
        d11v(1)
        d11v(1, 2)
        d11v(1, 2, 3)

        def d21v(a, b, c=1, *rest):
            pass
        d21v(1, 2)
        d21v(1, 2, 3)
        d21v(1, 2, 3, 4)
        d21v(*(1, 2, 3, 4))
        d21v(1, 2, **{'c': 3})

        def d02v(a=1, b=2, *rest):
            pass
        d02v()
        d02v(1)
        d02v(1, 2)
        d02v(1, 2, 3)
        d02v(1, *(2, 3, 4))
        d02v(**{'a': 1, 'b': 2})

        def d12v(a, b=1, c=2, *rest):
            pass
        d12v(1)
        d12v(1, 2)
        d12v(1, 2, 3)
        d12v(1, 2, 3, 4)
        d12v(*(1, 2, 3, 4))
        d12v(1, 2, *(3, 4, 5))
        d12v(1, *(2,), **{'c': 3})

        def d22v(a, b, c=1, d=2, *rest):
            pass
        d22v(1, 2)
        d22v(1, 2, 3)
        d22v(1, 2, 3, 4)
        d22v(1, 2, 3, 4, 5)
        d22v(*(1, 2, 3, 4))
        d22v(1, 2, *(3, 4, 5))
        d22v(1, *(2, 3), **{'d': 4})
        try:
            str('x', **{b'foo': 1})
        except TypeError:
            pass
        else:
            self.fail('Bytes should not work as keyword argument names')

        def pos0key1(*, key):
            return key
        pos0key1(key=100)

        def pos2key2(p1, p2, *, k1, k2=100):
            return p1, p2, k1, k2
        pos2key2(1, 2, k1=100)
        pos2key2(1, 2, k1=100, k2=200)
        pos2key2(1, 2, k2=100, k1=200)

        def pos2key2dict(p1, p2, *, k1=100, k2, **kwarg):
            return p1, p2, k1, k2, kwarg
        pos2key2dict(1, 2, k2=100, tokwarg1=100, tokwarg2=200)
        pos2key2dict(1, 2, tokwarg1=100, tokwarg2=200, k2=100)

        def f(*args, **kwargs):
            return args, kwargs
        self.assertEquals(f(1, *[3, 4], x=2, y=5), ((1, 3, 4), {'x': 2, 'y':
            5}))
        self.assertRaises(SyntaxError, eval, 'f(1, *(2,3), 4)')
        self.assertRaises(SyntaxError, eval, 'f(1, x=2, *(3,4), x=5)')

        def f(x) ->list:
            pass
        self.assertEquals(f.__annotations__, {'return': list})

        def f(x: int):
            pass
        self.assertEquals(f.__annotations__, {'x': int})

        def f(*x: str):
            pass
        self.assertEquals(f.__annotations__, {'x': str})

        def f(**x: float):
            pass
        self.assertEquals(f.__annotations__, {'x': float})

        def f(x, y: (1 + 2)):
            pass
        self.assertEquals(f.__annotations__, {'y': 3})

        def f(a, b: (1), c: (2), d):
            pass
        self.assertEquals(f.__annotations__, {'b': 1, 'c': 2})

        def f(a, b: (1), c: (2), d, e: (3)=4, f=5, *g: (6)):
            pass
        self.assertEquals(f.__annotations__, {'b': 1, 'c': 2, 'e': 3, 'g': 6})

        def f(a, b: (1), c: (2), d, e: (3)=4, f=5, *g: (6), h: (7), i=8, j:
            (9)=10, **k: (11)) ->(12):
            pass
        self.assertEquals(f.__annotations__, {'b': 1, 'c': 2, 'e': 3, 'g': 
            6, 'h': 7, 'j': 9, 'k': 11, 'return': 12})

        def null(x):
            return x

        @null
        def f(x) ->list:
            pass
        self.assertEquals(f.__annotations__, {'return': list})
        closure = 1

        def f():
            return closure

        def f(x=1):
            return closure

        def f(*, k=1):
            return closure

        def f() ->int:
            return closure
        check_syntax_error(self, 'f(*g(1=2))')
        check_syntax_error(self, 'f(**g(1=2))')

    def testLambdef(self):
        l1 = lambda : 0
        self.assertEquals(l1(), 0)
        l2 = lambda : a[d]
        l3 = lambda : [(2 < x) for x in [-1, 3, 0]]
        self.assertEquals(l3(), [0, 1, 0])
        l4 = lambda x=lambda y=lambda z=1: z: y(): x()
        self.assertEquals(l4(), 1)
        l5 = lambda x, y, z=2: x + y + z
        self.assertEquals(l5(1, 2), 5)
        self.assertEquals(l5(1, 2, 3), 6)
        check_syntax_error(self, 'lambda x: x = 2')
        check_syntax_error(self, 'lambda (None,): None')
        l6 = lambda x, y, *, k=20: x + y + k
        self.assertEquals(l6(1, 2), 1 + 2 + 20)
        self.assertEquals(l6(1, 2, k=10), 1 + 2 + 10)

    def testSimpleStmt(self):
        x = 1
        pass
        del x

        def foo():
            x = 1
            pass
            del x
        foo()

    def testExprStmt(self):
        1
        1, 2, 3
        x = 1
        x = 1, 2, 3
        x = y = z = 1, 2, 3
        x, y, z = 1, 2, 3
        abc = a, b, c = x, y, z = xyz = 1, 2, (3, 4)
        check_syntax_error(self, 'x + 1 = 1')
        check_syntax_error(self, 'a + 1 = b + 2')

    def testDelStmt(self):
        abc = [1, 2, 3]
        x, y, z = abc
        xyz = x, y, z
        del abc
        del x, y, (z, xyz)

    def testPassStmt(self):
        pass

    def testBreakStmt(self):
        while 1:
            break

    def testContinueStmt(self):
        i = 1
        while i:
            i = 0
            continue
        msg = ''
        while not msg:
            msg = 'ok'
            try:
                continue
                msg = 'continue failed to continue inside try'
            except:
                msg = 'continue inside try called except block'
        if msg != 'ok':
            self.fail(msg)
        msg = ''
        while not msg:
            msg = 'finally block not called'
            try:
                continue
            finally:
                msg = 'ok'
        if msg != 'ok':
            self.fail(msg)

    def test_break_continue_loop(self):

        def test_inner(extra_burning_oil=1, count=0):
            big_hippo = 2
            while big_hippo:
                count += 1
                try:
                    if extra_burning_oil and big_hippo == 1:
                        extra_burning_oil -= 1
                        break
                    big_hippo -= 1
                    continue
                except:
                    raise
            if count > 2 or big_hippo != 1:
                self.fail('continue then break in try/except in loop broken!')
        test_inner()

    def testReturn(self):

        def g1():
            return

        def g2():
            return 1
        g1()
        x = g2()
        check_syntax_error(self, 'class foo:return 1')

    def testYield(self):
        check_syntax_error(self, 'class foo:yield 1')

    def testRaise(self):
        try:
            raise RuntimeError('just testing')
        except RuntimeError:
            pass
        try:
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass

    def testImport(self):
        import sys
        import time, sys
        from time import time
        from time import time
        from sys import path, argv
        from sys import path, argv
        from sys import path, argv

    def testGlobal(self):
        global a
        global a, b
        global one, two, three, four, five, six, seven, eight, nine, ten

    def testNonlocal(self):
        x = 0
        y = 0

        def f():
            nonlocal x
            nonlocal x, y

    def testAssert(self):
        assert 1
        assert 1, 1
        assert lambda x: x
        assert 1, lambda x: x + 1
        try:
            assert 0, 'msg'
        except AssertionError as e:
            self.assertEquals(e.args[0], 'msg')
        else:
            if __debug__:
                self.fail('AssertionError not raised by assert 0')

    def testIf(self):
        if 1:
            pass
        if 1:
            pass
        else:
            pass
        if 0:
            pass
        elif 0:
            pass
        if 0:
            pass
        elif 0:
            pass
        elif 0:
            pass
        elif 0:
            pass
        else:
            pass

    def testWhile(self):
        while 0:
            pass
        while 0:
            pass
        else:
            pass
        x = 0
        while 0:
            x = 1
        else:
            x = 2
        self.assertEquals(x, 2)

    def testFor(self):
        for i in (1, 2, 3):
            pass
        for i, j, k in ():
            pass
        else:
            pass


        class Squares:

            def __init__(self, max):
                self.max = max
                self.sofar = []

            def __len__(self):
                return len(self.sofar)

            def __getitem__(self, i):
                if not 0 <= i < self.max:
                    raise IndexError
                n = len(self.sofar)
                while n <= i:
                    self.sofar.append(n * n)
                    n = n + 1
                return self.sofar[i]
        n = 0
        for x in Squares(10):
            n = n + x
        if n != 285:
            self.fail('for over growing sequence')
        result = []
        for x, in [(1,), (2,), (3,)]:
            result.append(x)
        self.assertEqual(result, [1, 2, 3])

    def testTry(self):
        try:
            1 / 0
        except ZeroDivisionError:
            pass
        else:
            pass
        try:
            1 / 0
        except EOFError:
            pass
        except TypeError as msg:
            pass
        except RuntimeError as msg:
            pass
        except:
            pass
        else:
            pass
        try:
            1 / 0
        except (EOFError, TypeError, ZeroDivisionError):
            pass
        try:
            1 / 0
        except (EOFError, TypeError, ZeroDivisionError) as msg:
            pass
        try:
            pass
        finally:
            pass

    def testSuite(self):
        if 1:
            pass
        if 1:
            pass
        if 1:
            pass
            pass
            pass

    def testTest(self):
        if not 1:
            pass
        if 1 and 1:
            pass
        if 1 or 1:
            pass
        if not not not 1:
            pass
        if not 1 and 1 and 1:
            pass
        if 1 and 1 or 1 and 1 and 1 or not 1 and 1:
            pass

    def testComparison(self):
        if 1:
            pass
        x = 1 == 1
        if 1 == 1:
            pass
        if 1 != 1:
            pass
        if 1 < 1:
            pass
        if 1 > 1:
            pass
        if 1 <= 1:
            pass
        if 1 >= 1:
            pass
        if 1 is 1:
            pass
        if 1 is not 1:
            pass
        if 1 in ():
            pass
        if 1 not in ():
            pass
        if 1 < 1 > 1 == 1 >= 1 <= 1 != 1 in 1 not in 1 is 1 is not 1:
            pass

    def testBinaryMaskOps(self):
        x = 1 & 1
        x = 1 ^ 1
        x = 1 | 1

    def testShiftOps(self):
        x = 1 << 1
        x = 1 >> 1
        x = 1 << 1 >> 1

    def testAdditiveOps(self):
        x = 1
        x = 1 + 1
        x = 1 - 1 - 1
        x = 1 - 1 + 1 - 1 + 1

    def testMultiplicativeOps(self):
        x = 1 * 1
        x = 1 / 1
        x = 1 % 1
        x = 1 / 1 * 1 % 1

    def testUnaryOps(self):
        x = +1
        x = -1
        x = ~1
        x = ~1 ^ 1 & 1 | 1 & 1 ^ -1
        x = -1 * 1 / 1 + 1 * 1 - ---1 * 1

    def testSelectors(self):
        import sys, time
        c = sys.path[0]
        x = time.time()
        x = sys.modules['time'].time()
        a = '01234'
        c = a[0]
        c = a[-1]
        s = a[0:5]
        s = a[:5]
        s = a[0:]
        s = a[:]
        s = a[-5:]
        s = a[:-1]
        s = a[-4:-3]
        d = {}
        d[1] = 1
        d[1,] = 2
        d[1, 2] = 3
        d[1, 2, 3] = 4
        L = list(d)
        L.sort(key=lambda x: x if isinstance(x, tuple) else ())
        self.assertEquals(str(L), '[1, (1,), (1, 2), (1, 2, 3)]')

    def testAtoms(self):
        x = 1
        x = 1 or 2 or 3
        x = 1 or 2 or 3, 2, 3
        x = []
        x = [1]
        x = [1 or 2 or 3]
        x = [1 or 2 or 3, 2, 3]
        x = []
        x = {}
        x = {'one': 1}
        x = {'one': 1}
        x = {('one' or 'two'): 1 or 2}
        x = {'one': 1, 'two': 2}
        x = {'one': 1, 'two': 2}
        x = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}
        x = {'one'}
        x = {'one', 1}
        x = {'one', 'two', 'three'}
        x = {2, 3, 4}
        x = x
        x = 'x'
        x = 123

    def testClassdef(self):


        class B:
            pass


        class B2:
            pass


        class C1(B):
            pass


        class C2(B):
            pass


        class D(C1, C2, B):
            pass


        class C:

            def meth1(self):
                pass

            def meth2(self, arg):
                pass

            def meth3(self, a1, a2):
                pass

        def class_decorator(x):
            return x


        @class_decorator
        class G:
            pass

    def testDictcomps(self):
        nums = [1, 2, 3]
        self.assertEqual({i: (i + 1) for i in nums}, {(1): 2, (2): 3, (3): 4})

    def testListcomps(self):
        nums = [1, 2, 3, 4, 5]
        strs = ['Apple', 'Banana', 'Coconut']
        spcs = ['  Apple', ' Banana ', 'Coco  nut  ']
        self.assertEqual([s.strip() for s in spcs], ['Apple', 'Banana',
            'Coco  nut'])
        self.assertEqual([(3 * x) for x in nums], [3, 6, 9, 12, 15])
        self.assertEqual([x for x in nums if x > 2], [3, 4, 5])
        self.assertEqual([(i, s) for i in nums for s in strs], [(1, 'Apple'
            ), (1, 'Banana'), (1, 'Coconut'), (2, 'Apple'), (2, 'Banana'),
            (2, 'Coconut'), (3, 'Apple'), (3, 'Banana'), (3, 'Coconut'), (4,
            'Apple'), (4, 'Banana'), (4, 'Coconut'), (5, 'Apple'), (5,
            'Banana'), (5, 'Coconut')])
        self.assertEqual([(i, s) for i in nums for s in [f for f in strs if
            'n' in f]], [(1, 'Banana'), (1, 'Coconut'), (2, 'Banana'), (2,
            'Coconut'), (3, 'Banana'), (3, 'Coconut'), (4, 'Banana'), (4,
            'Coconut'), (5, 'Banana'), (5, 'Coconut')])
        self.assertEqual([(lambda a: [(a ** i) for i in range(a + 1)])(j) for
            j in range(5)], [[1], [1, 1], [1, 2, 4], [1, 3, 9, 27], [1, 4, 
            16, 64, 256]])

        def test_in_func(l):
            return [(0 < x < 3) for x in l if x > 2]
        self.assertEqual(test_in_func(nums), [False, False, False])

        def test_nested_front():
            self.assertEqual([[y for y in [x, x + 1]] for x in [1, 3, 5]],
                [[1, 2], [3, 4], [5, 6]])
        test_nested_front()
        check_syntax_error(self, '[i, s for i in nums for s in strs]')
        check_syntax_error(self, '[x if y]')
        suppliers = [(1, 'Boeing'), (2, 'Ford'), (3, 'Macdonalds')]
        parts = [(10, 'Airliner'), (20, 'Engine'), (30, 'Cheeseburger')]
        suppart = [(1, 10), (1, 20), (2, 20), (3, 30)]
        x = [(sname, pname) for sno, sname in suppliers for pno, pname in
            parts for sp_sno, sp_pno in suppart if sno == sp_sno and pno ==
            sp_pno]
        self.assertEqual(x, [('Boeing', 'Airliner'), ('Boeing', 'Engine'),
            ('Ford', 'Engine'), ('Macdonalds', 'Cheeseburger')])

    def testGenexps(self):
        g = ([x for x in range(10)] for x in range(1))
        self.assertEqual(next(g), [x for x in range(10)])
        try:
            next(g)
            self.fail('should produce StopIteration exception')
        except StopIteration:
            pass
        a = 1
        try:
            g = (a for d in a)
            next(g)
            self.fail('should produce TypeError')
        except TypeError:
            pass
        self.assertEqual(list((x, y) for x in 'abcd' for y in 'abcd'), [(x,
            y) for x in 'abcd' for y in 'abcd'])
        self.assertEqual(list((x, y) for x in 'ab' for y in 'xy'), [(x, y) for
            x in 'ab' for y in 'xy'])
        a = [x for x in range(10)]
        b = (x for x in (y for y in a))
        self.assertEqual(sum(b), sum([x for x in range(10)]))
        self.assertEqual(sum(x ** 2 for x in range(10)), sum([(x ** 2) for
            x in range(10)]))
        self.assertEqual(sum(x * x for x in range(10) if x % 2), sum([(x *
            x) for x in range(10) if x % 2]))
        self.assertEqual(sum(x for x in (y for y in range(10))), sum([x for
            x in range(10)]))
        self.assertEqual(sum(x for x in (y for y in (z for z in range(10)))
            ), sum([x for x in range(10)]))
        self.assertEqual(sum(x for x in [y for y in (z for z in range(10))]
            ), sum([x for x in range(10)]))
        self.assertEqual(sum(x for x in (y for y in (z for z in range(10) if
            True)) if True), sum([x for x in range(10)]))
        self.assertEqual(sum(x for x in (y for y in (z for z in range(10) if
            True) if False) if True), 0)
        check_syntax_error(self, 'foo(x for x in range(10), 100)')
        check_syntax_error(self, 'foo(100, x for x in range(10))')

    def testComprehensionSpecials(self):
        x = 10
        g = (i for i in range(x))
        x = 5
        self.assertEqual(len(list(g)), 10)
        x = 10
        t = False
        g = ((i, j) for i in range(x) if t for j in range(x))
        x = 5
        t = True
        self.assertEqual([(i, j) for i in range(10) for j in range(5)], list(g)
            )
        self.assertEqual([x for x in range(10) if x % 2 if x % 3], [1, 5, 7])
        self.assertEqual(list(x for x in range(10) if x % 2 if x % 3), [1, 
            5, 7])
        self.assertEqual([x for x, in [(4,), (5,), (6,)]], [4, 5, 6])
        self.assertEqual(list(x for x, in [(7,), (8,), (9,)]), [7, 8, 9])

    def test_with_statement(self):


        class manager(object):

            def __enter__(self):
                return 1, 2

            def __exit__(self, *args):
                pass
        with manager():
            pass
        with manager() as x:
            pass
        with manager() as (x, y):
            pass
        with manager(), manager():
            pass
        with manager() as x, manager() as y:
            pass
        with manager() as x, manager():
            pass

    def testIfElseExpr(self):

        def _checkeval(msg, ret):
            """helper to check that evaluation of expressions is done correctly"""
            print(x)
            return ret
        self.assertEqual([x() for x in (lambda : True, lambda : False) if x
            ()], [True])
        self.assertEqual([x(False) for x in (lambda x: False if x else True,
            lambda x: True if x else False) if x(False)], [True])
        self.assertEqual(5 if 1 else _checkeval('check 1', 0), 5)
        self.assertEqual(_checkeval('check 2', 0) if 0 else 5, 5)
        self.assertEqual(5 and 6 if 0 else 1, 1)
        self.assertEqual(5 and 6 if 0 else 1, 1)
        self.assertEqual(5 and (6 if 1 else 1), 6)
        self.assertEqual(0 or _checkeval('check 3', 2) if 0 else 3, 3)
        self.assertEqual(1 or _checkeval('check 4', 2) if 1 else _checkeval
            ('check 5', 3), 1)
        self.assertEqual(0 or 5 if 1 else _checkeval('check 6', 3), 5)
        self.assertEqual(not 5 if 1 else 1, False)
        self.assertEqual(not 5 if 0 else 1, 1)
        self.assertEqual(6 + 1 if 1 else 2, 7)
        self.assertEqual(6 - 1 if 1 else 2, 5)
        self.assertEqual(6 * 2 if 1 else 4, 12)
        self.assertEqual(6 / 2 if 1 else 3, 3)
        self.assertEqual(6 < 4 if 0 else 2, 2)


def test_main():
    run_unittest(TokenTests, GrammarTests)


if __name__ == '__main__':
    test_main()
