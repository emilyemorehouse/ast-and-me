import ast
import builtins
import collections
import decimal
import fractions
import io
import locale
import os
import pickle
import platform
import random
import re
import sys
import traceback
import types
import unittest
import warnings
from operator import neg
from test.support import TESTFN, unlink, run_unittest, check_warnings
from test.support.script_helper import assert_python_ok
try:
    import pty, signal
except ImportError:
    pty = signal = None


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
            n += 1
        return self.sofar[i]


class StrSquares:

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
            self.sofar.append(str(n * n))
            n += 1
        return self.sofar[i]


class BitBucket:

    def write(self, line):
        pass


test_conv_no_sign = [('0', 0), ('1', 1), ('9', 9), ('10', 10), ('99', 99),
    ('100', 100), ('314', 314), (' 314', 314), ('314 ', 314), (
    '  \t\t  314  \t\t  ', 314), (repr(sys.maxsize), sys.maxsize), ('  1x',
    ValueError), ('  1  ', 1), ('  1\x02  ', ValueError), ('', ValueError),
    (' ', ValueError), ('  \t\t  ', ValueError), (str(
    b'\\u0663\\u0661\\u0664 ', 'raw-unicode-escape'), 314), (chr(512),
    ValueError)]
test_conv_sign = [('0', 0), ('1', 1), ('9', 9), ('10', 10), ('99', 99), (
    '100', 100), ('314', 314), (' 314', ValueError), ('314 ', 314), (
    '  \t\t  314  \t\t  ', ValueError), (repr(sys.maxsize), sys.maxsize), (
    '  1x', ValueError), ('  1  ', ValueError), ('  1\x02  ', ValueError),
    ('', ValueError), (' ', ValueError), ('  \t\t  ', ValueError), (str(
    b'\\u0663\\u0661\\u0664 ', 'raw-unicode-escape'), 314), (chr(512),
    ValueError)]


class TestFailingBool:

    def __bool__(self):
        raise RuntimeError


class TestFailingIter:

    def __iter__(self):
        raise RuntimeError


def filter_char(arg):
    return ord(arg) > ord('d')


def map_char(arg):
    return chr(ord(arg) + 1)


class BuiltinTest(unittest.TestCase):

    def check_iter_pickle(self, it, seq, proto):
        itorg = it
        d = pickle.dumps(it, proto)
        it = pickle.loads(d)
        self.assertEqual(type(itorg), type(it))
        self.assertEqual(list(it), seq)
        it = pickle.loads(d)
        try:
            next(it)
        except StopIteration:
            return
        d = pickle.dumps(it, proto)
        it = pickle.loads(d)
        self.assertEqual(list(it), seq[1:])

    def test_import(self):
        __import__('sys')
        __import__('time')
        __import__('string')
        __import__(name='sys')
        __import__(name='time', level=0)
        self.assertRaises(ImportError, __import__, 'spamspam')
        self.assertRaises(TypeError, __import__, 1, 2, 3, 4)
        self.assertRaises(ValueError, __import__, '')
        self.assertRaises(TypeError, __import__, 'sys', name='sys')

    def test_abs(self):
        self.assertEqual(abs(0), 0)
        self.assertEqual(abs(1234), 1234)
        self.assertEqual(abs(-1234), 1234)
        self.assertTrue(abs(-sys.maxsize - 1) > 0)
        self.assertEqual(abs(0.0), 0.0)
        self.assertEqual(abs(3.14), 3.14)
        self.assertEqual(abs(-3.14), 3.14)
        self.assertRaises(TypeError, abs, 'a')
        self.assertEqual(abs(True), 1)
        self.assertEqual(abs(False), 0)
        self.assertRaises(TypeError, abs)
        self.assertRaises(TypeError, abs, None)


        class AbsClass(object):

            def __abs__(self):
                return -5
        self.assertEqual(abs(AbsClass()), -5)

    def test_all(self):
        self.assertEqual(all([2, 4, 6]), True)
        self.assertEqual(all([2, None, 6]), False)
        self.assertRaises(RuntimeError, all, [2, TestFailingBool(), 6])
        self.assertRaises(RuntimeError, all, TestFailingIter())
        self.assertRaises(TypeError, all, 10)
        self.assertRaises(TypeError, all)
        self.assertRaises(TypeError, all, [2, 4, 6], [])
        self.assertEqual(all([]), True)
        self.assertEqual(all([0, TestFailingBool()]), False)
        S = [50, 60]
        self.assertEqual(all(x > 42 for x in S), True)
        S = [50, 40, 60]
        self.assertEqual(all(x > 42 for x in S), False)

    def test_any(self):
        self.assertEqual(any([None, None, None]), False)
        self.assertEqual(any([None, 4, None]), True)
        self.assertRaises(RuntimeError, any, [None, TestFailingBool(), 6])
        self.assertRaises(RuntimeError, any, TestFailingIter())
        self.assertRaises(TypeError, any, 10)
        self.assertRaises(TypeError, any)
        self.assertRaises(TypeError, any, [2, 4, 6], [])
        self.assertEqual(any([]), False)
        self.assertEqual(any([1, TestFailingBool()]), True)
        S = [40, 60, 30]
        self.assertEqual(any(x > 42 for x in S), True)
        S = [10, 20, 30]
        self.assertEqual(any(x > 42 for x in S), False)

    def test_ascii(self):
        self.assertEqual(ascii(''), "''")
        self.assertEqual(ascii(0), '0')
        self.assertEqual(ascii(()), '()')
        self.assertEqual(ascii([]), '[]')
        self.assertEqual(ascii({}), '{}')
        a = []
        a.append(a)
        self.assertEqual(ascii(a), '[[...]]')
        a = {}
        a[0] = a
        self.assertEqual(ascii(a), '{0: {...}}')

        def _check_uni(s):
            self.assertEqual(ascii(s), repr(s))
        _check_uni("'")
        _check_uni('"')
        _check_uni('"\'')
        _check_uni('\x00')
        _check_uni('\r\n\t .')
        _check_uni('\x85')
        _check_uni('\u1fff')
        _check_uni('\U00012fff')
        _check_uni('\ud800')
        _check_uni('\udfff')
        self.assertEqual(ascii('𝄡'), "'\\U0001d121'")
        s = '\'\x00"\n\r\t abcd\x85é\U00012fff\ud800𝄡xxx.'
        self.assertEqual(ascii(s),
            '\'\\\'\\x00"\\n\\r\\t abcd\\x85\\xe9\\U00012fff\\ud800\\U0001d121xxx.\''
            )

    def test_neg(self):
        x = -sys.maxsize - 1
        self.assertTrue(isinstance(x, int))
        self.assertEqual(-x, sys.maxsize + 1)

    def test_callable(self):
        self.assertTrue(callable(len))
        self.assertFalse(callable('a'))
        self.assertTrue(callable(callable))
        self.assertTrue(callable(lambda x, y: x + y))
        self.assertFalse(callable(__builtins__))

        def f():
            pass
        self.assertTrue(callable(f))


        class C1:

            def meth(self):
                pass
        self.assertTrue(callable(C1))
        c = C1()
        self.assertTrue(callable(c.meth))
        self.assertFalse(callable(c))
        c.__call__ = None
        self.assertFalse(callable(c))
        c.__call__ = lambda self: 0
        self.assertFalse(callable(c))
        del c.__call__
        self.assertFalse(callable(c))


        class C2(object):

            def __call__(self):
                pass
        c2 = C2()
        self.assertTrue(callable(c2))
        c2.__call__ = None
        self.assertTrue(callable(c2))


        class C3(C2):
            pass
        c3 = C3()
        self.assertTrue(callable(c3))

    def test_chr(self):
        self.assertEqual(chr(32), ' ')
        self.assertEqual(chr(65), 'A')
        self.assertEqual(chr(97), 'a')
        self.assertEqual(chr(255), 'ÿ')
        self.assertRaises(ValueError, chr, 1 << 24)
        self.assertEqual(chr(sys.maxunicode), str('\\U0010ffff'.encode(
            'ascii'), 'unicode-escape'))
        self.assertRaises(TypeError, chr)
        self.assertEqual(chr(65535), '\uffff')
        self.assertEqual(chr(65536), '𐀀')
        self.assertEqual(chr(65537), '𐀁')
        self.assertEqual(chr(1048574), '\U000ffffe')
        self.assertEqual(chr(1048575), '\U000fffff')
        self.assertEqual(chr(1048576), '\U00100000')
        self.assertEqual(chr(1048577), '\U00100001')
        self.assertEqual(chr(1114110), '\U0010fffe')
        self.assertEqual(chr(1114111), '\U0010ffff')
        self.assertRaises(ValueError, chr, -1)
        self.assertRaises(ValueError, chr, 1114112)
        self.assertRaises((OverflowError, ValueError), chr, 2 ** 32)

    def test_cmp(self):
        self.assertTrue(not hasattr(builtins, 'cmp'))

    def test_compile(self):
        compile('print(1)\n', '', 'exec')
        bom = b'\xef\xbb\xbf'
        compile(bom + b'print(1)\n', '', 'exec')
        compile(source='pass', filename='?', mode='exec')
        compile(dont_inherit=0, filename='tmp', source='0', mode='eval')
        compile('pass', '?', dont_inherit=1, mode='exec')
        compile(memoryview(b'text'), 'name', 'exec')
        self.assertRaises(TypeError, compile)
        self.assertRaises(ValueError, compile, 'print(42)\n', '<string>',
            'badmode')
        self.assertRaises(ValueError, compile, 'print(42)\n', '<string>',
            'single', 255)
        self.assertRaises(ValueError, compile, chr(0), 'f', 'exec')
        self.assertRaises(TypeError, compile, 'pass', '?', 'exec', mode=
            'eval', source='0', filename='tmp')
        compile('print("å")\n', '', 'exec')
        self.assertRaises(ValueError, compile, chr(0), 'f', 'exec')
        self.assertRaises(ValueError, compile, str('a = 1'), 'f', 'bad')
        codestr = """def f():
        ""\"doc""\"
        try:
            assert False
        except AssertionError:
            return (True, f.__doc__)
        else:
            return (False, f.__doc__)
        """

        def f():
            """doc"""
        values = [(-1, __debug__, f.__doc__), (0, True, 'doc'), (1, False,
            'doc'), (2, False, None)]
        for optval, debugval, docstring in values:
            codeobjs = []
            codeobjs.append(compile(codestr, '<test>', 'exec', optimize=optval)
                )
            tree = ast.parse(codestr)
            codeobjs.append(compile(tree, '<test>', 'exec', optimize=optval))
            for code in codeobjs:
                ns = {}
                exec(code, ns)
                rv = ns['f']()
                self.assertEqual(rv, (debugval, docstring))

    def test_delattr(self):
        sys.spam = 1
        delattr(sys, 'spam')
        self.assertRaises(TypeError, delattr)

    def test_dir(self):
        self.assertRaises(TypeError, dir, 42, 42)
        local_var = 1
        self.assertIn('local_var', dir())
        self.assertIn('exit', dir(sys))


        class Foo(types.ModuleType):
            __dict__ = 8
        f = Foo('foo')
        self.assertRaises(TypeError, dir, f)
        self.assertIn('strip', dir(str))
        self.assertNotIn('__mro__', dir(str))


        class Foo(object):

            def __init__(self):
                self.x = 7
                self.y = 8
                self.z = 9
        f = Foo()
        self.assertIn('y', dir(f))


        class Foo(object):
            __slots__ = []
        f = Foo()
        self.assertIn('__repr__', dir(f))


        class Foo(object):
            __slots__ = ['__class__', '__dict__']

            def __init__(self):
                self.bar = 'wow'
        f = Foo()
        self.assertNotIn('__repr__', dir(f))
        self.assertIn('bar', dir(f))


        class Foo(object):

            def __dir__(self):
                return ['kan', 'ga', 'roo']
        f = Foo()
        self.assertTrue(dir(f) == ['ga', 'kan', 'roo'])


        class Foo(object):

            def __dir__(self):
                return 'b', 'c', 'a'
        res = dir(Foo())
        self.assertIsInstance(res, list)
        self.assertTrue(res == ['a', 'b', 'c'])


        class Foo(object):

            def __dir__(self):
                return 7
        f = Foo()
        self.assertRaises(TypeError, dir, f)
        try:
            raise IndexError
        except:
            self.assertEqual(len(dir(sys.exc_info()[2])), 4)
        self.assertEqual(sorted([].__dir__()), dir([]))

    def test_divmod(self):
        self.assertEqual(divmod(12, 7), (1, 5))
        self.assertEqual(divmod(-12, 7), (-2, 2))
        self.assertEqual(divmod(12, -7), (-2, -2))
        self.assertEqual(divmod(-12, -7), (1, -5))
        self.assertEqual(divmod(-sys.maxsize - 1, -1), (sys.maxsize + 1, 0))
        for num, denom, exp_result in [(3.25, 1.0, (3.0, 0.25)), (-3.25, 
            1.0, (-4.0, 0.75)), (3.25, -1.0, (-4.0, -0.75)), (-3.25, -1.0,
            (3.0, -0.25))]:
            result = divmod(num, denom)
            self.assertAlmostEqual(result[0], exp_result[0])
            self.assertAlmostEqual(result[1], exp_result[1])
        self.assertRaises(TypeError, divmod)

    def test_eval(self):
        self.assertEqual(eval('1+1'), 2)
        self.assertEqual(eval(' 1+1\n'), 2)
        globals = {'a': 1, 'b': 2}
        locals = {'b': 200, 'c': 300}
        self.assertEqual(eval('a', globals), 1)
        self.assertEqual(eval('a', globals, locals), 1)
        self.assertEqual(eval('b', globals, locals), 200)
        self.assertEqual(eval('c', globals, locals), 300)
        globals = {'a': 1, 'b': 2}
        locals = {'b': 200, 'c': 300}
        bom = b'\xef\xbb\xbf'
        self.assertEqual(eval(bom + b'a', globals, locals), 1)
        self.assertEqual(eval('"å"', globals), 'å')
        self.assertRaises(TypeError, eval)
        self.assertRaises(TypeError, eval, ())
        self.assertRaises(SyntaxError, eval, bom[:2] + b'a')


        class X:

            def __getitem__(self, key):
                raise ValueError
        self.assertRaises(ValueError, eval, 'foo', {}, X())

    def test_general_eval(self):


        class M:
            """Test mapping interface versus possible calls from eval()."""

            def __getitem__(self, key):
                if key == 'a':
                    return 12
                raise KeyError

            def keys(self):
                return list('xyz')
        m = M()
        g = globals()
        self.assertEqual(eval('a', g, m), 12)
        self.assertRaises(NameError, eval, 'b', g, m)
        self.assertEqual(eval('dir()', g, m), list('xyz'))
        self.assertEqual(eval('globals()', g, m), g)
        self.assertEqual(eval('locals()', g, m), m)
        self.assertRaises(TypeError, eval, 'a', m)


        class A:
            """Non-mapping"""
            pass
        m = A()
        self.assertRaises(TypeError, eval, 'a', g, m)


        class D(dict):

            def __getitem__(self, key):
                if key == 'a':
                    return 12
                return dict.__getitem__(self, key)

            def keys(self):
                return list('xyz')
        d = D()
        self.assertEqual(eval('a', g, d), 12)
        self.assertRaises(NameError, eval, 'b', g, d)
        self.assertEqual(eval('dir()', g, d), list('xyz'))
        self.assertEqual(eval('globals()', g, d), g)
        self.assertEqual(eval('locals()', g, d), d)
        eval('[locals() for i in (2,3)]', g, d)
        eval('[locals() for i in (2,3)]', g, collections.UserDict())


        class SpreadSheet:
            """Sample application showing nested, calculated lookups."""
            _cells = {}

            def __setitem__(self, key, formula):
                self._cells[key] = formula

            def __getitem__(self, key):
                return eval(self._cells[key], globals(), self)
        ss = SpreadSheet()
        ss['a1'] = '5'
        ss['a2'] = 'a1*6'
        ss['a3'] = 'a2*7'
        self.assertEqual(ss['a3'], 210)


        class C:

            def __getitem__(self, item):
                raise KeyError(item)

            def keys(self):
                return 1
        self.assertRaises(TypeError, eval, 'dir()', globals(), C())

    def test_exec(self):
        g = {}
        exec('z = 1', g)
        if '__builtins__' in g:
            del g['__builtins__']
        self.assertEqual(g, {'z': 1})
        exec('z = 1+1', g)
        if '__builtins__' in g:
            del g['__builtins__']
        self.assertEqual(g, {'z': 2})
        g = {}
        l = {}
        with check_warnings():
            warnings.filterwarnings('ignore', 'global statement', module=
                '<string>')
            exec('global a; a = 1; b = 2', g, l)
        if '__builtins__' in g:
            del g['__builtins__']
        if '__builtins__' in l:
            del l['__builtins__']
        self.assertEqual((g, l), ({'a': 1}, {'b': 2}))

    def test_exec_globals(self):
        code = compile("print('Hello World!')", '', 'exec')
        self.assertRaisesRegex(NameError, "name 'print' is not defined",
            exec, code, {'__builtins__': {}})
        self.assertRaises(TypeError, exec, code, {'__builtins__': 123})
        code = compile('class A: pass', '', 'exec')
        self.assertRaisesRegex(NameError, '__build_class__ not found', exec,
            code, {'__builtins__': {}})


        class frozendict_error(Exception):
            pass


        class frozendict(dict):

            def __setitem__(self, key, value):
                raise frozendict_error('frozendict is readonly')
        if isinstance(__builtins__, types.ModuleType):
            frozen_builtins = frozendict(__builtins__.__dict__)
        else:
            frozen_builtins = frozendict(__builtins__)
        code = compile("__builtins__['superglobal']=2; print(superglobal)",
            'test', 'exec')
        self.assertRaises(frozendict_error, exec, code, {'__builtins__':
            frozen_builtins})
        namespace = frozendict({})
        code = compile('x=1', 'test', 'exec')
        self.assertRaises(frozendict_error, exec, code, namespace)

    def test_exec_redirected(self):
        savestdout = sys.stdout
        sys.stdout = None
        try:
            exec('a')
        except NameError:
            pass
        finally:
            sys.stdout = savestdout

    def test_filter(self):
        self.assertEqual(list(filter(lambda c: 'a' <= c <= 'z',
            'Hello World')), list('elloorld'))
        self.assertEqual(list(filter(None, [1, 'hello', [], [3], '', None, 
            9, 0])), [1, 'hello', [3], 9])
        self.assertEqual(list(filter(lambda x: x > 0, [1, -3, 9, 0, 2])), [
            1, 9, 2])
        self.assertEqual(list(filter(None, Squares(10))), [1, 4, 9, 16, 25,
            36, 49, 64, 81])
        self.assertEqual(list(filter(lambda x: x % 2, Squares(10))), [1, 9,
            25, 49, 81])

        def identity(item):
            return 1
        filter(identity, Squares(5))
        self.assertRaises(TypeError, filter)


        class BadSeq(object):

            def __getitem__(self, index):
                if index < 4:
                    return 42
                raise ValueError
        self.assertRaises(ValueError, list, filter(lambda x: x, BadSeq()))

        def badfunc():
            pass
        self.assertRaises(TypeError, list, filter(badfunc, range(5)))
        self.assertEqual(list(filter(None, (1, 2))), [1, 2])
        self.assertEqual(list(filter(lambda x: x >= 3, (1, 2, 3, 4))), [3, 4])
        self.assertRaises(TypeError, list, filter(42, (1, 2)))

    def test_filter_pickle(self):
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            f1 = filter(filter_char, 'abcdeabcde')
            f2 = filter(filter_char, 'abcdeabcde')
            self.check_iter_pickle(f1, list(f2), proto)

    def test_getattr(self):
        self.assertTrue(getattr(sys, 'stdout') is sys.stdout)
        self.assertRaises(TypeError, getattr, sys, 1)
        self.assertRaises(TypeError, getattr, sys, 1, 'foo')
        self.assertRaises(TypeError, getattr)
        self.assertRaises(AttributeError, getattr, sys, chr(sys.maxunicode))
        self.assertRaises(AttributeError, getattr, 1, '\udad1픞')

    def test_hasattr(self):
        self.assertTrue(hasattr(sys, 'stdout'))
        self.assertRaises(TypeError, hasattr, sys, 1)
        self.assertRaises(TypeError, hasattr)
        self.assertEqual(False, hasattr(sys, chr(sys.maxunicode)))


        class A:

            def __getattr__(self, what):
                raise SystemExit
        self.assertRaises(SystemExit, hasattr, A(), 'b')


        class B:

            def __getattr__(self, what):
                raise ValueError
        self.assertRaises(ValueError, hasattr, B(), 'b')

    def test_hash(self):
        hash(None)
        self.assertEqual(hash(1), hash(1))
        self.assertEqual(hash(1), hash(1.0))
        hash('spam')
        self.assertEqual(hash('spam'), hash(b'spam'))
        hash((0, 1, 2, 3))

        def f():
            pass
        self.assertRaises(TypeError, hash, [])
        self.assertRaises(TypeError, hash, {})


        class X:

            def __hash__(self):
                return 2 ** 100
        self.assertEqual(type(hash(X())), int)


        class Z(int):

            def __hash__(self):
                return self
        self.assertEqual(hash(Z(42)), hash(42))

    def test_hex(self):
        self.assertEqual(hex(16), '0x10')
        self.assertEqual(hex(-16), '-0x10')
        self.assertRaises(TypeError, hex, {})

    def test_id(self):
        id(None)
        id(1)
        id(1.0)
        id('spam')
        id((0, 1, 2, 3))
        id([0, 1, 2, 3])
        id({'spam': 1, 'eggs': 2, 'ham': 3})

    def test_iter(self):
        self.assertRaises(TypeError, iter)
        self.assertRaises(TypeError, iter, 42, 42)
        lists = [('1', '2'), ['1', '2'], '12']
        for l in lists:
            i = iter(l)
            self.assertEqual(next(i), '1')
            self.assertEqual(next(i), '2')
            self.assertRaises(StopIteration, next, i)

    def test_isinstance(self):


        class C:
            pass


        class D(C):
            pass


        class E:
            pass
        c = C()
        d = D()
        e = E()
        self.assertTrue(isinstance(c, C))
        self.assertTrue(isinstance(d, C))
        self.assertTrue(not isinstance(e, C))
        self.assertTrue(not isinstance(c, D))
        self.assertTrue(not isinstance('foo', E))
        self.assertRaises(TypeError, isinstance, E, 'foo')
        self.assertRaises(TypeError, isinstance)

    def test_issubclass(self):


        class C:
            pass


        class D(C):
            pass


        class E:
            pass
        c = C()
        d = D()
        e = E()
        self.assertTrue(issubclass(D, C))
        self.assertTrue(issubclass(C, C))
        self.assertTrue(not issubclass(C, D))
        self.assertRaises(TypeError, issubclass, 'foo', E)
        self.assertRaises(TypeError, issubclass, E, 'foo')
        self.assertRaises(TypeError, issubclass)

    def test_len(self):
        self.assertEqual(len('123'), 3)
        self.assertEqual(len(()), 0)
        self.assertEqual(len((1, 2, 3, 4)), 4)
        self.assertEqual(len([1, 2, 3, 4]), 4)
        self.assertEqual(len({}), 0)
        self.assertEqual(len({'a': 1, 'b': 2}), 2)


        class BadSeq:

            def __len__(self):
                raise ValueError
        self.assertRaises(ValueError, len, BadSeq())


        class InvalidLen:

            def __len__(self):
                return None
        self.assertRaises(TypeError, len, InvalidLen())


        class FloatLen:

            def __len__(self):
                return 4.5
        self.assertRaises(TypeError, len, FloatLen())


        class HugeLen:

            def __len__(self):
                return sys.maxsize + 1
        self.assertRaises(OverflowError, len, HugeLen())


        class NoLenMethod(object):
            pass
        self.assertRaises(TypeError, len, NoLenMethod())

    def test_map(self):
        self.assertEqual(list(map(lambda x: x * x, range(1, 4))), [1, 4, 9])
        try:
            from math import sqrt
        except ImportError:

            def sqrt(x):
                return pow(x, 0.5)
        self.assertEqual(list(map(lambda x: list(map(sqrt, x)), [[16, 4], [
            81, 9]])), [[4.0, 2.0], [9.0, 3.0]])
        self.assertEqual(list(map(lambda x, y: x + y, [1, 3, 2], [9, 1, 4])
            ), [10, 4, 6])

        def plus(*v):
            accu = 0
            for i in v:
                accu = accu + i
            return accu
        self.assertEqual(list(map(plus, [1, 3, 7])), [1, 3, 7])
        self.assertEqual(list(map(plus, [1, 3, 7], [4, 9, 2])), [1 + 4, 3 +
            9, 7 + 2])
        self.assertEqual(list(map(plus, [1, 3, 7], [4, 9, 2], [1, 1, 0])),
            [1 + 4 + 1, 3 + 9 + 1, 7 + 2 + 0])
        self.assertEqual(list(map(int, Squares(10))), [0, 1, 4, 9, 16, 25, 
            36, 49, 64, 81])

        def Max(a, b):
            if a is None:
                return b
            if b is None:
                return a
            return max(a, b)
        self.assertEqual(list(map(Max, Squares(3), Squares(2))), [0, 1])
        self.assertRaises(TypeError, map)
        self.assertRaises(TypeError, map, lambda x: x, 42)


        class BadSeq:

            def __iter__(self):
                raise ValueError
                yield None
        self.assertRaises(ValueError, list, map(lambda x: x, BadSeq()))

        def badfunc(x):
            raise RuntimeError
        self.assertRaises(RuntimeError, list, map(badfunc, range(5)))

    def test_map_pickle(self):
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            m1 = map(map_char, 'Is this the real life?')
            m2 = map(map_char, 'Is this the real life?')
            self.check_iter_pickle(m1, list(m2), proto)

    def test_max(self):
        self.assertEqual(max('123123'), '3')
        self.assertEqual(max(1, 2, 3), 3)
        self.assertEqual(max((1, 2, 3, 1, 2, 3)), 3)
        self.assertEqual(max([1, 2, 3, 1, 2, 3]), 3)
        self.assertEqual(max(1, 2, 3.0), 3.0)
        self.assertEqual(max(1, 2.0, 3), 3)
        self.assertEqual(max(1.0, 2, 3), 3)
        self.assertRaises(TypeError, max)
        self.assertRaises(TypeError, max, 42)
        self.assertRaises(ValueError, max, ())


        class BadSeq:

            def __getitem__(self, index):
                raise ValueError
        self.assertRaises(ValueError, max, BadSeq())
        for stmt in ('max(key=int)', 'max(default=None)',
            'max(1, 2, default=None)', 'max(default=None, key=int)',
            'max(1, key=int)', 'max(1, 2, keystone=int)',
            'max(1, 2, key=int, abc=int)', 'max(1, 2, key=1)'):
            try:
                exec(stmt, globals())
            except TypeError:
                pass
            else:
                self.fail(stmt)
        self.assertEqual(max((1,), key=neg), 1)
        self.assertEqual(max((1, 2), key=neg), 1)
        self.assertEqual(max(1, 2, key=neg), 1)
        self.assertEqual(max((), default=None), None)
        self.assertEqual(max((1,), default=None), 1)
        self.assertEqual(max((1, 2), default=None), 2)
        self.assertEqual(max((), default=1, key=neg), 1)
        self.assertEqual(max((1, 2), default=3, key=neg), 1)
        data = [random.randrange(200) for i in range(100)]
        keys = dict((elem, random.randrange(50)) for elem in data)
        f = keys.__getitem__
        self.assertEqual(max(data, key=f), sorted(reversed(data), key=f)[-1])

    def test_min(self):
        self.assertEqual(min('123123'), '1')
        self.assertEqual(min(1, 2, 3), 1)
        self.assertEqual(min((1, 2, 3, 1, 2, 3)), 1)
        self.assertEqual(min([1, 2, 3, 1, 2, 3]), 1)
        self.assertEqual(min(1, 2, 3.0), 1)
        self.assertEqual(min(1, 2.0, 3), 1)
        self.assertEqual(min(1.0, 2, 3), 1.0)
        self.assertRaises(TypeError, min)
        self.assertRaises(TypeError, min, 42)
        self.assertRaises(ValueError, min, ())


        class BadSeq:

            def __getitem__(self, index):
                raise ValueError
        self.assertRaises(ValueError, min, BadSeq())
        for stmt in ('min(key=int)', 'min(default=None)',
            'min(1, 2, default=None)', 'min(default=None, key=int)',
            'min(1, key=int)', 'min(1, 2, keystone=int)',
            'min(1, 2, key=int, abc=int)', 'min(1, 2, key=1)'):
            try:
                exec(stmt, globals())
            except TypeError:
                pass
            else:
                self.fail(stmt)
        self.assertEqual(min((1,), key=neg), 1)
        self.assertEqual(min((1, 2), key=neg), 2)
        self.assertEqual(min(1, 2, key=neg), 2)
        self.assertEqual(min((), default=None), None)
        self.assertEqual(min((1,), default=None), 1)
        self.assertEqual(min((1, 2), default=None), 1)
        self.assertEqual(min((), default=1, key=neg), 1)
        self.assertEqual(min((1, 2), default=1, key=neg), 2)
        data = [random.randrange(200) for i in range(100)]
        keys = dict((elem, random.randrange(50)) for elem in data)
        f = keys.__getitem__
        self.assertEqual(min(data, key=f), sorted(data, key=f)[0])

    def test_next(self):
        it = iter(range(2))
        self.assertEqual(next(it), 0)
        self.assertEqual(next(it), 1)
        self.assertRaises(StopIteration, next, it)
        self.assertRaises(StopIteration, next, it)
        self.assertEqual(next(it, 42), 42)


        class Iter(object):

            def __iter__(self):
                return self

            def __next__(self):
                raise StopIteration
        it = iter(Iter())
        self.assertEqual(next(it, 42), 42)
        self.assertRaises(StopIteration, next, it)

        def gen():
            yield 1
            return
        it = gen()
        self.assertEqual(next(it), 1)
        self.assertRaises(StopIteration, next, it)
        self.assertEqual(next(it, 42), 42)

    def test_oct(self):
        self.assertEqual(oct(100), '0o144')
        self.assertEqual(oct(-100), '-0o144')
        self.assertRaises(TypeError, oct, ())

    def write_testfile(self):
        fp = open(TESTFN, 'w')
        self.addCleanup(unlink, TESTFN)
        with fp:
            fp.write('1+1\n')
            fp.write('The quick brown fox jumps over the lazy dog')
            fp.write('.\n')
            fp.write('Dear John\n')
            fp.write('XXX' * 100)
            fp.write('YYY' * 100)

    def test_open(self):
        self.write_testfile()
        fp = open(TESTFN, 'r')
        with fp:
            self.assertEqual(fp.readline(4), '1+1\n')
            self.assertEqual(fp.readline(),
                'The quick brown fox jumps over the lazy dog.\n')
            self.assertEqual(fp.readline(4), 'Dear')
            self.assertEqual(fp.readline(100), ' John\n')
            self.assertEqual(fp.read(300), 'XXX' * 100)
            self.assertEqual(fp.read(1000), 'YYY' * 100)

    def test_open_default_encoding(self):
        old_environ = dict(os.environ)
        try:
            for key in ('LC_ALL', 'LANG', 'LC_CTYPE'):
                if key in os.environ:
                    del os.environ[key]
            self.write_testfile()
            current_locale_encoding = locale.getpreferredencoding(False)
            fp = open(TESTFN, 'w')
            with fp:
                self.assertEqual(fp.encoding, current_locale_encoding)
        finally:
            os.environ.clear()
            os.environ.update(old_environ)

    def test_open_non_inheritable(self):
        fileobj = open(__file__)
        with fileobj:
            self.assertFalse(os.get_inheritable(fileobj.fileno()))

    def test_ord(self):
        self.assertEqual(ord(' '), 32)
        self.assertEqual(ord('A'), 65)
        self.assertEqual(ord('a'), 97)
        self.assertEqual(ord('\x80'), 128)
        self.assertEqual(ord('ÿ'), 255)
        self.assertEqual(ord(b' '), 32)
        self.assertEqual(ord(b'A'), 65)
        self.assertEqual(ord(b'a'), 97)
        self.assertEqual(ord(b'\x80'), 128)
        self.assertEqual(ord(b'\xff'), 255)
        self.assertEqual(ord(chr(sys.maxunicode)), sys.maxunicode)
        self.assertRaises(TypeError, ord, 42)
        self.assertEqual(ord(chr(1114111)), 1114111)
        self.assertEqual(ord('\uffff'), 65535)
        self.assertEqual(ord('𐀀'), 65536)
        self.assertEqual(ord('𐀁'), 65537)
        self.assertEqual(ord('\U000ffffe'), 1048574)
        self.assertEqual(ord('\U000fffff'), 1048575)
        self.assertEqual(ord('\U00100000'), 1048576)
        self.assertEqual(ord('\U00100001'), 1048577)
        self.assertEqual(ord('\U0010fffe'), 1114110)
        self.assertEqual(ord('\U0010ffff'), 1114111)

    def test_pow(self):
        self.assertEqual(pow(0, 0), 1)
        self.assertEqual(pow(0, 1), 0)
        self.assertEqual(pow(1, 0), 1)
        self.assertEqual(pow(1, 1), 1)
        self.assertEqual(pow(2, 0), 1)
        self.assertEqual(pow(2, 10), 1024)
        self.assertEqual(pow(2, 20), 1024 * 1024)
        self.assertEqual(pow(2, 30), 1024 * 1024 * 1024)
        self.assertEqual(pow(-2, 0), 1)
        self.assertEqual(pow(-2, 1), -2)
        self.assertEqual(pow(-2, 2), 4)
        self.assertEqual(pow(-2, 3), -8)
        self.assertAlmostEqual(pow(0.0, 0), 1.0)
        self.assertAlmostEqual(pow(0.0, 1), 0.0)
        self.assertAlmostEqual(pow(1.0, 0), 1.0)
        self.assertAlmostEqual(pow(1.0, 1), 1.0)
        self.assertAlmostEqual(pow(2.0, 0), 1.0)
        self.assertAlmostEqual(pow(2.0, 10), 1024.0)
        self.assertAlmostEqual(pow(2.0, 20), 1024.0 * 1024.0)
        self.assertAlmostEqual(pow(2.0, 30), 1024.0 * 1024.0 * 1024.0)
        self.assertAlmostEqual(pow(-2.0, 0), 1.0)
        self.assertAlmostEqual(pow(-2.0, 1), -2.0)
        self.assertAlmostEqual(pow(-2.0, 2), 4.0)
        self.assertAlmostEqual(pow(-2.0, 3), -8.0)
        for x in (2, 2.0):
            for y in (10, 10.0):
                for z in (1000, 1000.0):
                    if isinstance(x, float) or isinstance(y, float
                        ) or isinstance(z, float):
                        self.assertRaises(TypeError, pow, x, y, z)
                    else:
                        self.assertAlmostEqual(pow(x, y, z), 24.0)
        self.assertAlmostEqual(pow(-1, 0.5), 1j)
        self.assertAlmostEqual(pow(-1, 1 / 3), 0.5 + 0.8660254037844386j)
        self.assertRaises(ValueError, pow, -1, -2, 3)
        self.assertRaises(ValueError, pow, 1, 2, 0)
        self.assertRaises(TypeError, pow)

    def test_input(self):
        self.write_testfile()
        fp = open(TESTFN, 'r')
        savestdin = sys.stdin
        savestdout = sys.stdout
        try:
            sys.stdin = fp
            sys.stdout = BitBucket()
            self.assertEqual(input(), '1+1')
            self.assertEqual(input(),
                'The quick brown fox jumps over the lazy dog.')
            self.assertEqual(input('testing\n'), 'Dear John')
            sys.stdout = savestdout
            sys.stdin.close()
            self.assertRaises(ValueError, input)
            sys.stdout = BitBucket()
            sys.stdin = io.StringIO('NULL\x00')
            self.assertRaises(TypeError, input, 42, 42)
            sys.stdin = io.StringIO("    'whitespace'")
            self.assertEqual(input(), "    'whitespace'")
            sys.stdin = io.StringIO()
            self.assertRaises(EOFError, input)
            del sys.stdout
            self.assertRaises(RuntimeError, input, 'prompt')
            del sys.stdin
            self.assertRaises(RuntimeError, input, 'prompt')
        finally:
            sys.stdin = savestdin
            sys.stdout = savestdout
            fp.close()

    def test_repr(self):
        self.assertEqual(repr(''), "''")
        self.assertEqual(repr(0), '0')
        self.assertEqual(repr(()), '()')
        self.assertEqual(repr([]), '[]')
        self.assertEqual(repr({}), '{}')
        a = []
        a.append(a)
        self.assertEqual(repr(a), '[[...]]')
        a = {}
        a[0] = a
        self.assertEqual(repr(a), '{0: {...}}')

    def test_round(self):
        self.assertEqual(round(0.0), 0.0)
        self.assertEqual(type(round(0.0)), int)
        self.assertEqual(round(1.0), 1.0)
        self.assertEqual(round(10.0), 10.0)
        self.assertEqual(round(1000000000.0), 1000000000.0)
        self.assertEqual(round(1e+20), 1e+20)
        self.assertEqual(round(-1.0), -1.0)
        self.assertEqual(round(-10.0), -10.0)
        self.assertEqual(round(-1000000000.0), -1000000000.0)
        self.assertEqual(round(-1e+20), -1e+20)
        self.assertEqual(round(0.1), 0.0)
        self.assertEqual(round(1.1), 1.0)
        self.assertEqual(round(10.1), 10.0)
        self.assertEqual(round(1000000000.1), 1000000000.0)
        self.assertEqual(round(-1.1), -1.0)
        self.assertEqual(round(-10.1), -10.0)
        self.assertEqual(round(-1000000000.1), -1000000000.0)
        self.assertEqual(round(0.9), 1.0)
        self.assertEqual(round(9.9), 10.0)
        self.assertEqual(round(999999999.9), 1000000000.0)
        self.assertEqual(round(-0.9), -1.0)
        self.assertEqual(round(-9.9), -10.0)
        self.assertEqual(round(-999999999.9), -1000000000.0)
        self.assertEqual(round(-8.0, -1), -10.0)
        self.assertEqual(type(round(-8.0, -1)), float)
        self.assertEqual(type(round(-8.0, 0)), float)
        self.assertEqual(type(round(-8.0, 1)), float)
        self.assertEqual(round(5.5), 6)
        self.assertEqual(round(6.5), 6)
        self.assertEqual(round(-5.5), -6)
        self.assertEqual(round(-6.5), -6)
        self.assertEqual(round(0), 0)
        self.assertEqual(round(8), 8)
        self.assertEqual(round(-8), -8)
        self.assertEqual(type(round(0)), int)
        self.assertEqual(type(round(-8, -1)), int)
        self.assertEqual(type(round(-8, 0)), int)
        self.assertEqual(type(round(-8, 1)), int)
        self.assertEqual(round(number=-8.0, ndigits=-1), -10.0)
        self.assertRaises(TypeError, round)


        class TestRound:

            def __round__(self):
                return 23


        class TestNoRound:
            pass
        self.assertEqual(round(TestRound()), 23)
        self.assertRaises(TypeError, round, 1, 2, 3)
        self.assertRaises(TypeError, round, TestNoRound())
        t = TestNoRound()
        t.__round__ = lambda *args: args
        self.assertRaises(TypeError, round, t)
        self.assertRaises(TypeError, round, t, 0)
    linux_alpha = platform.system().startswith('Linux') and platform.machine(
        ).startswith('alpha')
    system_round_bug = round(5000000000000000.0 + 1) != 5000000000000000.0 + 1

    @unittest.skipIf(linux_alpha and system_round_bug,
        'test will fail;  failure is probably due to a buggy system round function'
        )
    def test_round_large(self):
        self.assertEqual(round(5000000000000000.0 - 1), 5000000000000000.0 - 1)
        self.assertEqual(round(5000000000000000.0), 5000000000000000.0)
        self.assertEqual(round(5000000000000000.0 + 1), 5000000000000000.0 + 1)
        self.assertEqual(round(5000000000000000.0 + 2), 5000000000000000.0 + 2)
        self.assertEqual(round(5000000000000000.0 + 3), 5000000000000000.0 + 3)

    def test_bug_27936(self):
        for x in [1234, 1234.56, decimal.Decimal('1234.56'), fractions.
            Fraction(123456, 100)]:
            self.assertEqual(round(x, None), round(x))
            self.assertEqual(type(round(x, None)), type(round(x)))

    def test_setattr(self):
        setattr(sys, 'spam', 1)
        self.assertEqual(sys.spam, 1)
        self.assertRaises(TypeError, setattr, sys, 1, 'spam')
        self.assertRaises(TypeError, setattr)

    def test_sum(self):
        self.assertEqual(sum([]), 0)
        self.assertEqual(sum(list(range(2, 8))), 27)
        self.assertEqual(sum(iter(list(range(2, 8)))), 27)
        self.assertEqual(sum(Squares(10)), 285)
        self.assertEqual(sum(iter(Squares(10))), 285)
        self.assertEqual(sum([[1], [2], [3]], []), [1, 2, 3])
        self.assertRaises(TypeError, sum)
        self.assertRaises(TypeError, sum, 42)
        self.assertRaises(TypeError, sum, ['a', 'b', 'c'])
        self.assertRaises(TypeError, sum, ['a', 'b', 'c'], '')
        self.assertRaises(TypeError, sum, [b'a', b'c'], b'')
        values = [bytearray(b'a'), bytearray(b'b')]
        self.assertRaises(TypeError, sum, values, bytearray(b''))
        self.assertRaises(TypeError, sum, [[1], [2], [3]])
        self.assertRaises(TypeError, sum, [{(2): 3}])
        self.assertRaises(TypeError, sum, [{(2): 3}] * 2, {(2): 3})


        class BadSeq:

            def __getitem__(self, index):
                raise ValueError
        self.assertRaises(ValueError, sum, BadSeq())
        empty = []
        sum(([x] for x in range(10)), empty)
        self.assertEqual(empty, [])

    def test_type(self):
        self.assertEqual(type(''), type('123'))
        self.assertNotEqual(type(''), type(()))

    @staticmethod
    def get_vars_f0():
        return vars()

    @staticmethod
    def get_vars_f2():
        BuiltinTest.get_vars_f0()
        a = 1
        b = 2
        return vars()


    class C_get_vars(object):

        def getDict(self):
            return {'a': 2}
        __dict__ = property(fget=getDict)

    def test_vars(self):
        self.assertEqual(set(vars()), set(dir()))
        self.assertEqual(set(vars(sys)), set(dir(sys)))
        self.assertEqual(self.get_vars_f0(), {})
        self.assertEqual(self.get_vars_f2(), {'a': 1, 'b': 2})
        self.assertRaises(TypeError, vars, 42, 42)
        self.assertRaises(TypeError, vars, 42)
        self.assertEqual(vars(self.C_get_vars()), {'a': 2})

    def test_zip(self):
        a = 1, 2, 3
        b = 4, 5, 6
        t = [(1, 4), (2, 5), (3, 6)]
        self.assertEqual(list(zip(a, b)), t)
        b = [4, 5, 6]
        self.assertEqual(list(zip(a, b)), t)
        b = 4, 5, 6, 7
        self.assertEqual(list(zip(a, b)), t)


        class I:

            def __getitem__(self, i):
                if i < 0 or i > 2:
                    raise IndexError
                return i + 4
        self.assertEqual(list(zip(a, I())), t)
        self.assertEqual(list(zip()), [])
        self.assertEqual(list(zip(*[])), [])
        self.assertRaises(TypeError, zip, None)


        class G:
            pass
        self.assertRaises(TypeError, zip, a, G())
        self.assertRaises(RuntimeError, zip, a, TestFailingIter())


        class SequenceWithoutALength:

            def __getitem__(self, i):
                if i == 5:
                    raise IndexError
                else:
                    return i
        self.assertEqual(list(zip(SequenceWithoutALength(), range(2 ** 30))
            ), list(enumerate(range(5))))


        class BadSeq:

            def __getitem__(self, i):
                if i == 5:
                    raise ValueError
                else:
                    return i
        self.assertRaises(ValueError, list, zip(BadSeq(), BadSeq()))

    def test_zip_pickle(self):
        a = 1, 2, 3
        b = 4, 5, 6
        t = [(1, 4), (2, 5), (3, 6)]
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z1 = zip(a, b)
            self.check_iter_pickle(z1, t, proto)

    def test_format(self):
        self.assertEqual(format(3, ''), '3')

        def classes_new():


            class A(object):

                def __init__(self, x):
                    self.x = x

                def __format__(self, format_spec):
                    return str(self.x) + format_spec


            class DerivedFromA(A):
                pass


            class Simple(object):
                pass


            class DerivedFromSimple(Simple):

                def __init__(self, x):
                    self.x = x

                def __format__(self, format_spec):
                    return str(self.x) + format_spec


            class DerivedFromSimple2(DerivedFromSimple):
                pass
            return A, DerivedFromA, DerivedFromSimple, DerivedFromSimple2

        def class_test(A, DerivedFromA, DerivedFromSimple, DerivedFromSimple2):
            self.assertEqual(format(A(3), 'spec'), '3spec')
            self.assertEqual(format(DerivedFromA(4), 'spec'), '4spec')
            self.assertEqual(format(DerivedFromSimple(5), 'abc'), '5abc')
            self.assertEqual(format(DerivedFromSimple2(10), 'abcdef'),
                '10abcdef')
        class_test(*classes_new())

        def empty_format_spec(value):
            self.assertEqual(format(value, ''), str(value))
            self.assertEqual(format(value), str(value))
        empty_format_spec(17 ** 13)
        empty_format_spec(1.0)
        empty_format_spec(3.1415e+104)
        empty_format_spec(-3.1415e+104)
        empty_format_spec(3.1415e-104)
        empty_format_spec(-3.1415e-104)
        empty_format_spec(object)
        empty_format_spec(None)


        class BadFormatResult:

            def __format__(self, format_spec):
                return 1.0
        self.assertRaises(TypeError, format, BadFormatResult(), '')
        self.assertRaises(TypeError, format, object(), 4)
        self.assertRaises(TypeError, format, object(), object())
        x = object().__format__('')
        self.assertTrue(x.startswith('<object object at'))
        self.assertRaises(TypeError, object().__format__, 3)
        self.assertRaises(TypeError, object().__format__, object())
        self.assertRaises(TypeError, object().__format__, None)


        class A:

            def __format__(self, fmt_str):
                return format('', fmt_str)
        self.assertEqual(format(A()), '')
        self.assertEqual(format(A(), ''), '')
        self.assertEqual(format(A(), 's'), '')


        class B:
            pass


        class C(object):
            pass
        for cls in [object, B, C]:
            obj = cls()
            self.assertEqual(format(obj), str(obj))
            self.assertEqual(format(obj, ''), str(obj))
            with self.assertRaisesRegex(TypeError, '\\b%s\\b' % re.escape(
                cls.__name__)):
                format(obj, 's')


        class DerivedFromStr(str):
            pass
        self.assertEqual(format(0, DerivedFromStr('10')), '         0')

    def test_bin(self):
        self.assertEqual(bin(0), '0b0')
        self.assertEqual(bin(1), '0b1')
        self.assertEqual(bin(-1), '-0b1')
        self.assertEqual(bin(2 ** 65), '0b1' + '0' * 65)
        self.assertEqual(bin(2 ** 65 - 1), '0b' + '1' * 65)
        self.assertEqual(bin(-2 ** 65), '-0b1' + '0' * 65)
        self.assertEqual(bin(-(2 ** 65 - 1)), '-0b' + '1' * 65)

    def test_bytearray_translate(self):
        x = bytearray(b'abc')
        self.assertRaises(ValueError, x.translate, b'1', 1)
        self.assertRaises(TypeError, x.translate, b'1' * 256, 1)

    def test_construct_singletons(self):
        for const in (None, Ellipsis, NotImplemented):
            tp = type(const)
            self.assertIs(tp(), const)
            self.assertRaises(TypeError, tp, 1, 2)
            self.assertRaises(TypeError, tp, a=1, b=2)


@unittest.skipUnless(pty, 'the pty and signal modules must be available')
class PtyTests(unittest.TestCase):
    """Tests that use a pseudo terminal to guarantee stdin and stdout are
    terminals in the test environment"""

    def run_child(self, child, terminal_input):
        r, w = os.pipe()
        try:
            pid, fd = pty.fork()
        except (OSError, AttributeError) as e:
            os.close(r)
            os.close(w)
            self.skipTest('pty.fork() raised {}'.format(e))
            raise
        if pid == 0:
            try:
                signal.alarm(2)
                os.close(r)
                with open(w, 'w') as wpipe:
                    child(wpipe)
            except:
                traceback.print_exc()
            finally:
                os._exit(0)
        os.close(w)
        os.write(fd, terminal_input)
        with open(r, 'r') as rpipe:
            lines = []
            while True:
                line = rpipe.readline().strip()
                if line == '':
                    break
                lines.append(line)
        if len(lines) != 2:
            child_output = bytearray()
            while True:
                try:
                    chunk = os.read(fd, 3000)
                except OSError:
                    break
                if not chunk:
                    break
                child_output.extend(chunk)
            os.close(fd)
            child_output = child_output.decode('ascii', 'ignore')
            self.fail(
                'got %d lines in pipe but expected 2, child output was:\n%s' %
                (len(lines), child_output))
        os.close(fd)
        return lines

    def check_input_tty(self, prompt, terminal_input, stdio_encoding=None):
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            self.skipTest('stdin and stdout must be ttys')

        def child(wpipe):
            if stdio_encoding:
                sys.stdin = io.TextIOWrapper(sys.stdin.detach(), encoding=
                    stdio_encoding, errors='surrogateescape')
                sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding
                    =stdio_encoding, errors='replace')
            print('tty =', sys.stdin.isatty() and sys.stdout.isatty(), file
                =wpipe)
            print(ascii(input(prompt)), file=wpipe)
        lines = self.run_child(child, terminal_input + b'\r\n')
        self.assertIn(lines[0], {'tty = True', 'tty = False'})
        if lines[0] != 'tty = True':
            self.skipTest('standard IO in should have been a tty')
        input_result = eval(lines[1])
        if stdio_encoding:
            expected = terminal_input.decode(stdio_encoding, 'surrogateescape')
        else:
            expected = terminal_input.decode(sys.stdin.encoding)
        self.assertEqual(input_result, expected)

    def test_input_tty(self):
        self.check_input_tty('prompt', b'quux')

    def test_input_tty_non_ascii(self):
        self.check_input_tty('prompté', b'quux\xe9', 'utf-8')

    def test_input_tty_non_ascii_unicode_errors(self):
        self.check_input_tty('prompté', b'quux\xe9', 'ascii')

    def test_input_no_stdout_fileno(self):

        def child(wpipe):
            print('stdin.isatty():', sys.stdin.isatty(), file=wpipe)
            sys.stdout = io.StringIO()
            input('prompt')
            print('captured:', ascii(sys.stdout.getvalue()), file=wpipe)
        lines = self.run_child(child, b'quux\r')
        expected = 'stdin.isatty(): True', "captured: 'prompt'"
        self.assertSequenceEqual(lines, expected)


class TestSorted(unittest.TestCase):

    def test_basic(self):
        data = list(range(100))
        copy = data[:]
        random.shuffle(copy)
        self.assertEqual(data, sorted(copy))
        self.assertNotEqual(data, copy)
        data.reverse()
        random.shuffle(copy)
        self.assertEqual(data, sorted(copy, key=lambda x: -x))
        self.assertNotEqual(data, copy)
        random.shuffle(copy)
        self.assertEqual(data, sorted(copy, reverse=1))
        self.assertNotEqual(data, copy)

    def test_bad_arguments(self):
        sorted([])
        with self.assertRaises(TypeError):
            sorted(iterable=[])
        sorted([], key=None)
        with self.assertRaises(TypeError):
            sorted([], None)

    def test_inputtypes(self):
        s = 'abracadabra'
        types = [list, tuple, str]
        for T in types:
            self.assertEqual(sorted(s), sorted(T(s)))
        s = ''.join(set(s))
        types = [str, set, frozenset, list, tuple, dict.fromkeys]
        for T in types:
            self.assertEqual(sorted(s), sorted(T(s)))

    def test_baddecorator(self):
        data = 'The quick Brown fox Jumped over The lazy Dog'.split()
        self.assertRaises(TypeError, sorted, data, None, lambda x, y: 0)


class ShutdownTest(unittest.TestCase):

    def test_cleanup(self):
        code = """if 1:
            import builtins
            import sys

            class C:
                def __del__(self):
                    print("before")
                    # Check that builtins still exist
                    len(())
                    print("after")

            c = C()
            # Make this module survive until builtins and sys are cleaned
            builtins.here = sys.modules[__name__]
            sys.here = sys.modules[__name__]
            # Create a reference loop so that this module needs to go
            # through a GC phase.
            here = sys.modules[__name__]
            """
        rc, out, err = assert_python_ok('-c', code, PYTHONIOENCODING='ascii')
        self.assertEqual(['before', 'after'], out.decode().splitlines())


class TestType(unittest.TestCase):

    def test_new_type(self):
        A = type('A', (), {})
        self.assertEqual(A.__name__, 'A')
        self.assertEqual(A.__qualname__, 'A')
        self.assertEqual(A.__module__, __name__)
        self.assertEqual(A.__bases__, (object,))
        self.assertIs(A.__base__, object)
        x = A()
        self.assertIs(type(x), A)
        self.assertIs(x.__class__, A)


        class B:

            def ham(self):
                return 'ham%d' % self
        C = type('C', (B, int), {'spam': lambda self: 'spam%s' % self})
        self.assertEqual(C.__name__, 'C')
        self.assertEqual(C.__qualname__, 'C')
        self.assertEqual(C.__module__, __name__)
        self.assertEqual(C.__bases__, (B, int))
        self.assertIs(C.__base__, int)
        self.assertIn('spam', C.__dict__)
        self.assertNotIn('ham', C.__dict__)
        x = C(42)
        self.assertEqual(x, 42)
        self.assertIs(type(x), C)
        self.assertIs(x.__class__, C)
        self.assertEqual(x.ham(), 'ham42')
        self.assertEqual(x.spam(), 'spam42')
        self.assertEqual(x.to_bytes(2, 'little'), b'*\x00')

    def test_type_nokwargs(self):
        with self.assertRaises(TypeError):
            type('a', (), {}, x=5)
        with self.assertRaises(TypeError):
            type('a', (), dict={})

    def test_type_name(self):
        for name in ('A', 'Ä', '🐍', 'B.A', '42', ''):
            with self.subTest(name=name):
                A = type(name, (), {})
                self.assertEqual(A.__name__, name)
                self.assertEqual(A.__qualname__, name)
                self.assertEqual(A.__module__, __name__)
        with self.assertRaises(ValueError):
            type('A\x00B', (), {})
        with self.assertRaises(ValueError):
            type('A\udcdcB', (), {})
        with self.assertRaises(TypeError):
            type(b'A', (), {})
        C = type('C', (), {})
        for name in ('A', 'Ä', '🐍', 'B.A', '42', ''):
            with self.subTest(name=name):
                C.__name__ = name
                self.assertEqual(C.__name__, name)
                self.assertEqual(C.__qualname__, 'C')
                self.assertEqual(C.__module__, __name__)
        A = type('C', (), {})
        with self.assertRaises(ValueError):
            A.__name__ = 'A\x00B'
        self.assertEqual(A.__name__, 'C')
        with self.assertRaises(ValueError):
            A.__name__ = 'A\udcdcB'
        self.assertEqual(A.__name__, 'C')
        with self.assertRaises(TypeError):
            A.__name__ = b'A'
        self.assertEqual(A.__name__, 'C')

    def test_type_qualname(self):
        A = type('A', (), {'__qualname__': 'B.C'})
        self.assertEqual(A.__name__, 'A')
        self.assertEqual(A.__qualname__, 'B.C')
        self.assertEqual(A.__module__, __name__)
        with self.assertRaises(TypeError):
            type('A', (), {'__qualname__': b'B'})
        self.assertEqual(A.__qualname__, 'B.C')
        A.__qualname__ = 'D.E'
        self.assertEqual(A.__name__, 'A')
        self.assertEqual(A.__qualname__, 'D.E')
        with self.assertRaises(TypeError):
            A.__qualname__ = b'B'
        self.assertEqual(A.__qualname__, 'D.E')

    def test_type_doc(self):
        for doc in ('x', 'Ä', '🐍', 'x\x00y', b'x', 42, None):
            A = type('A', (), {'__doc__': doc})
            self.assertEqual(A.__doc__, doc)
        with self.assertRaises(UnicodeEncodeError):
            type('A', (), {'__doc__': 'x\udcdcy'})
        A = type('A', (), {})
        self.assertEqual(A.__doc__, None)
        for doc in ('x', 'Ä', '🐍', 'x\x00y', 'x\udcdcy', b'x', 42, None):
            A.__doc__ = doc
            self.assertEqual(A.__doc__, doc)

    def test_bad_args(self):
        with self.assertRaises(TypeError):
            type()
        with self.assertRaises(TypeError):
            type('A', ())
        with self.assertRaises(TypeError):
            type('A', (), {}, ())
        with self.assertRaises(TypeError):
            type('A', (), dict={})
        with self.assertRaises(TypeError):
            type('A', [], {})
        with self.assertRaises(TypeError):
            type('A', (), types.MappingProxyType({}))
        with self.assertRaises(TypeError):
            type('A', (None,), {})
        with self.assertRaises(TypeError):
            type('A', (bool,), {})
        with self.assertRaises(TypeError):
            type('A', (int, str), {})

    def test_bad_slots(self):
        with self.assertRaises(TypeError):
            type('A', (), {'__slots__': b'x'})
        with self.assertRaises(TypeError):
            type('A', (int,), {'__slots__': 'x'})
        with self.assertRaises(TypeError):
            type('A', (), {'__slots__': ''})
        with self.assertRaises(TypeError):
            type('A', (), {'__slots__': '42'})
        with self.assertRaises(TypeError):
            type('A', (), {'__slots__': 'x\x00y'})
        with self.assertRaises(ValueError):
            type('A', (), {'__slots__': 'x', 'x': 0})
        with self.assertRaises(TypeError):
            type('A', (), {'__slots__': ('__dict__', '__dict__')})
        with self.assertRaises(TypeError):
            type('A', (), {'__slots__': ('__weakref__', '__weakref__')})


        class B:
            pass
        with self.assertRaises(TypeError):
            type('A', (B,), {'__slots__': '__dict__'})
        with self.assertRaises(TypeError):
            type('A', (B,), {'__slots__': '__weakref__'})


def load_tests(loader, tests, pattern):
    from doctest import DocTestSuite
    tests.addTest(DocTestSuite(builtins))
    return tests


if __name__ == '__main__':
    unittest.main()
