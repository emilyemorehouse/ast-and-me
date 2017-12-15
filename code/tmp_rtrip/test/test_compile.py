import math
import os
import unittest
import sys
import _ast
import tempfile
import types
from test import support
from test.support import script_helper


class TestSpecifics(unittest.TestCase):

    def compile_single(self, source):
        compile(source, '<single>', 'single')

    def assertInvalidSingle(self, source):
        self.assertRaises(SyntaxError, self.compile_single, source)

    def test_no_ending_newline(self):
        compile('hi', '<test>', 'exec')
        compile('hi\r', '<test>', 'exec')

    def test_empty(self):
        compile('', '<test>', 'exec')

    def test_other_newlines(self):
        compile('\r\n', '<test>', 'exec')
        compile('\r', '<test>', 'exec')
        compile('hi\r\nstuff\r\ndef f():\n    pass\r', '<test>', 'exec')
        compile('this_is\rreally_old_mac\rdef f():\n    pass', '<test>', 'exec'
            )

    def test_debug_assignment(self):
        self.assertRaises(SyntaxError, compile, '__debug__ = 1', '?', 'single')
        import builtins
        prev = builtins.__debug__
        setattr(builtins, '__debug__', 'sure')
        setattr(builtins, '__debug__', prev)

    def test_argument_handling(self):
        self.assertRaises(SyntaxError, eval, 'lambda a,a:0')
        self.assertRaises(SyntaxError, eval, 'lambda a,a=1:0')
        self.assertRaises(SyntaxError, eval, 'lambda a=1,a=1:0')
        self.assertRaises(SyntaxError, exec, 'def f(a, a): pass')
        self.assertRaises(SyntaxError, exec, 'def f(a = 0, a = 1): pass')
        self.assertRaises(SyntaxError, exec, 'def f(a): global a; a = 1')

    def test_syntax_error(self):
        self.assertRaises(SyntaxError, compile, '1+*3', 'filename', 'exec')

    def test_none_keyword_arg(self):
        self.assertRaises(SyntaxError, compile, 'f(None=1)', '<string>', 'exec'
            )

    def test_duplicate_global_local(self):
        self.assertRaises(SyntaxError, exec, 'def f(a): global a; a = 1')

    def test_exec_with_general_mapping_for_locals(self):


        class M:
            """Test mapping interface versus possible calls from eval()."""

            def __getitem__(self, key):
                if key == 'a':
                    return 12
                raise KeyError

            def __setitem__(self, key, value):
                self.results = key, value

            def keys(self):
                return list('xyz')
        m = M()
        g = globals()
        exec('z = a', g, m)
        self.assertEqual(m.results, ('z', 12))
        try:
            exec('z = b', g, m)
        except NameError:
            pass
        else:
            self.fail('Did not detect a KeyError')
        exec('z = dir()', g, m)
        self.assertEqual(m.results, ('z', list('xyz')))
        exec('z = globals()', g, m)
        self.assertEqual(m.results, ('z', g))
        exec('z = locals()', g, m)
        self.assertEqual(m.results, ('z', m))
        self.assertRaises(TypeError, exec, 'z = b', m)


        class A:
            """Non-mapping"""
            pass
        m = A()
        self.assertRaises(TypeError, exec, 'z = a', g, m)


        class D(dict):

            def __getitem__(self, key):
                if key == 'a':
                    return 12
                return dict.__getitem__(self, key)
        d = D()
        exec('z = a', g, d)
        self.assertEqual(d['z'], 12)

    def test_extended_arg(self):
        longexpr = 'x = x or ' + '-x' * 2500
        g = {}
        code = (
            """
def f(x):
    %s
    %s
    %s
    %s
    %s
    %s
    %s
    %s
    %s
    %s
    # the expressions above have no effect, x == argument
    while x:
        x -= 1
        # EXTENDED_ARG/JUMP_ABSOLUTE here
    return x
"""
             % ((longexpr,) * 10))
        exec(code, g)
        self.assertEqual(g['f'](5), 0)

    def test_argument_order(self):
        self.assertRaises(SyntaxError, exec, 'def f(a=1, b): pass')

    def test_float_literals(self):
        self.assertRaises(SyntaxError, eval, '2e')
        self.assertRaises(SyntaxError, eval, '2.0e+')
        self.assertRaises(SyntaxError, eval, '1e-')
        self.assertRaises(SyntaxError, eval, '3-4e/21')

    def test_indentation(self):
        s = '\nif 1:\n    if 2:\n        pass'
        compile(s, '<string>', 'exec')

    def test_leading_newlines(self):
        s256 = ''.join(['\n'] * 256 + ['spam'])
        co = compile(s256, 'fn', 'exec')
        self.assertEqual(co.co_firstlineno, 257)
        self.assertEqual(co.co_lnotab, bytes())

    def test_literals_with_leading_zeroes(self):
        for arg in ['077787', '0xj', '0x.', '0e', '090000000000000',
            '080000000000000', '000000000000009', '000000000000008', '0b42',
            '0BADCAFE', '0o123456789', '0b1.1', '0o4.2', '0b101j2',
            '0o153j2', '0b100e1', '0o777e1', '0777', '000777',
            '000000000000007']:
            self.assertRaises(SyntaxError, eval, arg)
        self.assertEqual(eval('0xff'), 255)
        self.assertEqual(eval('0777.'), 777)
        self.assertEqual(eval('0777.0'), 777)
        self.assertEqual(eval(
            '000000000000000000000000000000000000000000000000000777e0'), 777)
        self.assertEqual(eval('0777e1'), 7770)
        self.assertEqual(eval('0e0'), 0)
        self.assertEqual(eval('0000e-012'), 0)
        self.assertEqual(eval('09.5'), 9.5)
        self.assertEqual(eval('0777j'), 777j)
        self.assertEqual(eval('000'), 0)
        self.assertEqual(eval('00j'), 0j)
        self.assertEqual(eval('00.0'), 0)
        self.assertEqual(eval('0e3'), 0)
        self.assertEqual(eval('090000000000000.'), 90000000000000.0)
        self.assertEqual(eval('090000000000000.0000000000000000000000'), 
            90000000000000.0)
        self.assertEqual(eval('090000000000000e0'), 90000000000000.0)
        self.assertEqual(eval('090000000000000e-0'), 90000000000000.0)
        self.assertEqual(eval('090000000000000j'), 90000000000000j)
        self.assertEqual(eval('000000000000008.'), 8.0)
        self.assertEqual(eval('000000000000009.'), 9.0)
        self.assertEqual(eval('0b101010'), 42)
        self.assertEqual(eval('-0b000000000010'), -2)
        self.assertEqual(eval('0o777'), 511)
        self.assertEqual(eval('-0o0000010'), -8)

    def test_unary_minus(self):
        if sys.maxsize == 2147483647:
            all_one_bits = '0xffffffff'
            self.assertEqual(eval(all_one_bits), 4294967295)
            self.assertEqual(eval('-' + all_one_bits), -4294967295)
        elif sys.maxsize == 9223372036854775807:
            all_one_bits = '0xffffffffffffffff'
            self.assertEqual(eval(all_one_bits), 18446744073709551615)
            self.assertEqual(eval('-' + all_one_bits), -18446744073709551615)
        else:
            self.fail('How many bits *does* this machine have???')
        self.assertIsInstance(eval('%s' % (-sys.maxsize - 1)), int)
        self.assertIsInstance(eval('%s' % (-sys.maxsize - 2)), int)
    if sys.maxsize == 9223372036854775807:

        def test_32_63_bit_values(self):
            a = +4294967296
            b = -4294967296
            c = +281474976710656
            d = -281474976710656
            e = +4611686018427387904
            f = -4611686018427387904
            g = +9223372036854775807
            h = -9223372036854775807
            for variable in self.test_32_63_bit_values.__code__.co_consts:
                if variable is not None:
                    self.assertIsInstance(variable, int)

    def test_sequence_unpacking_error(self):
        i, j = (1, -1) or (-1, 1)
        self.assertEqual(i, 1)
        self.assertEqual(j, -1)

    def test_none_assignment(self):
        stmts = ['None = 0', 'None += 0', '__builtins__.None = 0',
            'def None(): pass', 'class None: pass', '(a, None) = 0, 0',
            'for None in range(10): pass', 'def f(None): pass',
            'import None', 'import x as None', 'from x import None',
            'from x import y as None']
        for stmt in stmts:
            stmt += '\n'
            self.assertRaises(SyntaxError, compile, stmt, 'tmp', 'single')
            self.assertRaises(SyntaxError, compile, stmt, 'tmp', 'exec')

    def test_import(self):
        succeed = ['import sys', 'import os, sys', 'import os as bar',
            'import os.path as bar',
            'from __future__ import nested_scopes, generators',
            """from __future__ import (nested_scopes,
generators)""",
            """from __future__ import (nested_scopes,
generators,)""",
            'from sys import stdin, stderr, stdout',
            """from sys import (stdin, stderr,
stdout)""",
            """from sys import (stdin, stderr,
stdout,)""",
            """from sys import (stdin
, stderr, stdout)""",
            """from sys import (stdin
, stderr, stdout,)""",
            'from sys import stdin as si, stdout as so, stderr as se',
            'from sys import (stdin as si, stdout as so, stderr as se)',
            'from sys import (stdin as si, stdout as so, stderr as se,)']
        fail = ['import (os, sys)', 'import (os), (sys)',
            'import ((os), (sys))', 'import (sys', 'import sys)',
            'import (os,)', 'import os As bar', 'import os.path a bar',
            'from sys import stdin As stdout',
            'from sys import stdin a stdout', 'from (sys) import stdin',
            'from __future__ import (nested_scopes',
            'from __future__ import nested_scopes)',
            """from __future__ import nested_scopes,
generators""",
            'from sys import (stdin', 'from sys import stdin)',
            """from sys import stdin, stdout,
stderr""",
            'from sys import stdin si',
            'from sys import stdin,from sys import (*)',
            'from sys import (stdin,, stdout, stderr)',
            'from sys import (stdin, stdout),']
        for stmt in succeed:
            compile(stmt, 'tmp', 'exec')
        for stmt in fail:
            self.assertRaises(SyntaxError, compile, stmt, 'tmp', 'exec')

    def test_for_distinct_code_objects(self):

        def f():
            f1 = lambda x=1: x
            f2 = lambda x=2: x
            return f1, f2
        f1, f2 = f()
        self.assertNotEqual(id(f1.__code__), id(f2.__code__))

    def test_lambda_doc(self):
        l = lambda : 'foo'
        self.assertIsNone(l.__doc__)

    def test_encoding(self):
        code = b'# -*- coding: badencoding -*-\npass\n'
        self.assertRaises(SyntaxError, compile, code, 'tmp', 'exec')
        code = '# -*- coding: badencoding -*-\n"Â¤"\n'
        compile(code, 'tmp', 'exec')
        self.assertEqual(eval(code), 'Â¤')
        code = '"Â¤"\n'
        self.assertEqual(eval(code), 'Â¤')
        code = b'"\xc2\xa4"\n'
        self.assertEqual(eval(code), '¤')
        code = b'# -*- coding: latin1 -*-\n"\xc2\xa4"\n'
        self.assertEqual(eval(code), 'Â¤')
        code = b'# -*- coding: utf-8 -*-\n"\xc2\xa4"\n'
        self.assertEqual(eval(code), '¤')
        code = b'# -*- coding: iso8859-15 -*-\n"\xc2\xa4"\n'
        self.assertEqual(eval(code), 'Â€')
        code = '"""\\\n# -*- coding: iso8859-15 -*-\nÂ¤"""\n'
        self.assertEqual(eval(code), '# -*- coding: iso8859-15 -*-\nÂ¤')
        code = b'"""\\\n# -*- coding: iso8859-15 -*-\n\xc2\xa4"""\n'
        self.assertEqual(eval(code), '# -*- coding: iso8859-15 -*-\n¤')

    def test_subscripts(self):


        class str_map(object):

            def __init__(self):
                self.data = {}

            def __getitem__(self, key):
                return self.data[str(key)]

            def __setitem__(self, key, value):
                self.data[str(key)] = value

            def __delitem__(self, key):
                del self.data[str(key)]

            def __contains__(self, key):
                return str(key) in self.data
        d = str_map()
        d[1] = 1
        self.assertEqual(d[1], 1)
        d[1] += 1
        self.assertEqual(d[1], 2)
        del d[1]
        self.assertNotIn(1, d)
        d[1, 1] = 1
        self.assertEqual(d[1, 1], 1)
        d[1, 1] += 1
        self.assertEqual(d[1, 1], 2)
        del d[1, 1]
        self.assertNotIn((1, 1), d)
        d[1:2] = 1
        self.assertEqual(d[1:2], 1)
        d[1:2] += 1
        self.assertEqual(d[1:2], 2)
        del d[1:2]
        self.assertNotIn(slice(1, 2), d)
        d[1:2, 1:2] = 1
        self.assertEqual(d[1:2, 1:2], 1)
        d[1:2, 1:2] += 1
        self.assertEqual(d[1:2, 1:2], 2)
        del d[1:2, 1:2]
        self.assertNotIn((slice(1, 2), slice(1, 2)), d)
        d[1:2:3] = 1
        self.assertEqual(d[1:2:3], 1)
        d[1:2:3] += 1
        self.assertEqual(d[1:2:3], 2)
        del d[1:2:3]
        self.assertNotIn(slice(1, 2, 3), d)
        d[1:2:3, 1:2:3] = 1
        self.assertEqual(d[1:2:3, 1:2:3], 1)
        d[1:2:3, 1:2:3] += 1
        self.assertEqual(d[1:2:3, 1:2:3], 2)
        del d[1:2:3, 1:2:3]
        self.assertNotIn((slice(1, 2, 3), slice(1, 2, 3)), d)
        d[...] = 1
        self.assertEqual(d[...], 1)
        d[...] += 1
        self.assertEqual(d[...], 2)
        del d[...]
        self.assertNotIn(Ellipsis, d)
        d[..., ...] = 1
        self.assertEqual(d[..., ...], 1)
        d[..., ...] += 1
        self.assertEqual(d[..., ...], 2)
        del d[..., ...]
        self.assertNotIn((Ellipsis, Ellipsis), d)

    def test_annotation_limit(self):
        s = 'def f(%s): pass'
        s %= ', '.join('a%d:%d' % (i, i) for i in range(256))
        self.assertRaises(SyntaxError, compile, s, '?', 'exec')
        s = 'def f(%s): pass'
        s %= ', '.join('a%d:%d' % (i, i) for i in range(255))
        compile(s, '?', 'exec')

    def test_mangling(self):


        class A:

            def f():
                __mangled = 1
                __not_mangled__ = 2
                import __mangled_mod
                import __package__.module
        self.assertIn('_A__mangled', A.f.__code__.co_varnames)
        self.assertIn('__not_mangled__', A.f.__code__.co_varnames)
        self.assertIn('_A__mangled_mod', A.f.__code__.co_varnames)
        self.assertIn('__package__', A.f.__code__.co_varnames)

    def test_compile_ast(self):
        fname = __file__
        if fname.lower().endswith('pyc'):
            fname = fname[:-1]
        with open(fname, 'r') as f:
            fcontents = f.read()
        sample_code = [['<assign>', 'x = 5'], ['<ifblock>',
            'if True:\n    pass\n'], ['<forblock>',
            """for n in [1, 2, 3]:
    print(n)
"""], ['<deffunc>',
            """def foo():
    pass
foo()
"""], [fname, fcontents]]
        for fname, code in sample_code:
            co1 = compile(code, '%s1' % fname, 'exec')
            ast = compile(code, '%s2' % fname, 'exec', _ast.PyCF_ONLY_AST)
            self.assertTrue(type(ast) == _ast.Module)
            co2 = compile(ast, '%s3' % fname, 'exec')
            self.assertEqual(co1, co2)
            self.assertEqual(co2.co_filename, '%s3' % fname)
        co1 = compile('print(1)', '<string>', 'exec', _ast.PyCF_ONLY_AST)
        self.assertRaises(TypeError, compile, co1, '<ast>', 'eval')
        self.assertRaises(TypeError, compile, _ast.If(), '<ast>', 'exec')
        ast = _ast.Module()
        ast.body = [_ast.BoolOp()]
        self.assertRaises(TypeError, compile, ast, '<ast>', 'exec')

    def test_dict_evaluation_order(self):
        i = 0

        def f():
            nonlocal i
            i += 1
            return i
        d = {f(): f(), f(): f()}
        self.assertEqual(d, {(1): 2, (3): 4})

    def test_compile_filename(self):
        for filename in ('file.py', b'file.py'):
            code = compile('pass', filename, 'exec')
            self.assertEqual(code.co_filename, 'file.py')
        for filename in (bytearray(b'file.py'), memoryview(b'file.py')):
            with self.assertWarns(DeprecationWarning):
                code = compile('pass', filename, 'exec')
            self.assertEqual(code.co_filename, 'file.py')
        self.assertRaises(TypeError, compile, 'pass', list(b'file.py'), 'exec')

    @support.cpython_only
    def test_same_filename_used(self):
        s = 'def f(): pass\ndef g(): pass'
        c = compile(s, 'myfile', 'exec')
        for obj in c.co_consts:
            if isinstance(obj, types.CodeType):
                self.assertIs(obj.co_filename, c.co_filename)

    def test_single_statement(self):
        self.compile_single('1 + 2')
        self.compile_single('\n1 + 2')
        self.compile_single('1 + 2\n')
        self.compile_single('1 + 2\n\n')
        self.compile_single('1 + 2\t\t\n')
        self.compile_single('1 + 2\t\t\n        ')
        self.compile_single('1 + 2 # one plus two')
        self.compile_single('1; 2')
        self.compile_single('import sys; sys')
        self.compile_single('def f():\n   pass')
        self.compile_single('while False:\n   pass')
        self.compile_single('if x:\n   f(x)')
        self.compile_single('if x:\n   f(x)\nelse:\n   g(x)')
        self.compile_single('class T:\n   pass')

    def test_bad_single_statement(self):
        self.assertInvalidSingle('1\n2')
        self.assertInvalidSingle('def f(): pass')
        self.assertInvalidSingle('a = 13\nb = 187')
        self.assertInvalidSingle('del x\ndel y')
        self.assertInvalidSingle('f()\ng()')
        self.assertInvalidSingle('f()\n# blah\nblah()')
        self.assertInvalidSingle('f()\nxy # blah\nblah()')
        self.assertInvalidSingle('x = 5 # comment\nx = 6\n')

    def test_particularly_evil_undecodable(self):
        src = b'0000\x00\n00000000000\n\x00\n\x9e\n'
        with tempfile.TemporaryDirectory() as tmpd:
            fn = os.path.join(tmpd, 'bad.py')
            with open(fn, 'wb') as fp:
                fp.write(src)
            res = script_helper.run_python_until_end(fn)[0]
        self.assertIn(b'Non-UTF-8', res.err)

    def test_yet_more_evil_still_undecodable(self):
        src = b'#\x00\n#\xfd\n'
        with tempfile.TemporaryDirectory() as tmpd:
            fn = os.path.join(tmpd, 'bad.py')
            with open(fn, 'wb') as fp:
                fp.write(src)
            res = script_helper.run_python_until_end(fn)[0]
        self.assertIn(b'Non-UTF-8', res.err)

    @support.cpython_only
    def test_compiler_recursion_limit(self):
        fail_depth = sys.getrecursionlimit() * 3
        success_depth = int(fail_depth * 0.75)

        def check_limit(prefix, repeated):
            expect_ok = prefix + repeated * success_depth
            self.compile_single(expect_ok)
            broken = prefix + repeated * fail_depth
            details = 'Compiling ({!r} + {!r} * {})'.format(prefix,
                repeated, fail_depth)
            with self.assertRaises(RecursionError, msg=details):
                self.compile_single(broken)
        check_limit('a', '()')
        check_limit('a', '.b')
        check_limit('a', '[0]')
        check_limit('a', '*a')

    def test_null_terminated(self):
        with self.assertRaisesRegex(ValueError, 'cannot contain null'):
            compile('123\x00', '<dummy>', 'eval')
        with self.assertRaisesRegex(ValueError, 'cannot contain null'):
            compile(memoryview(b'123\x00'), '<dummy>', 'eval')
        code = compile(memoryview(b'123\x00')[1:-1], '<dummy>', 'eval')
        self.assertEqual(eval(code), 23)
        code = compile(memoryview(b'1234')[1:-1], '<dummy>', 'eval')
        self.assertEqual(eval(code), 23)
        code = compile(memoryview(b'$23$')[1:-1], '<dummy>', 'eval')
        self.assertEqual(eval(code), 23)
        self.assertEqual(eval(memoryview(b'1234')[1:-1]), 23)
        namespace = dict()
        exec(memoryview(b'ax = 123')[1:-1], namespace)
        self.assertEqual(namespace['x'], 12)

    def check_constant(self, func, expected):
        for const in func.__code__.co_consts:
            if repr(const) == repr(expected):
                break
        else:
            self.fail('unable to find constant %r in %r' % (expected, func.
                __code__.co_consts))

    @support.cpython_only
    def test_merge_constants(self):

        def check_same_constant(const):
            ns = {}
            code = 'f1, f2 = lambda: %r, lambda: %r' % (const, const)
            exec(code, ns)
            f1 = ns['f1']
            f2 = ns['f2']
            self.assertIs(f1.__code__, f2.__code__)
            self.check_constant(f1, const)
            self.assertEqual(repr(f1()), repr(const))
        check_same_constant(None)
        check_same_constant(0)
        check_same_constant(0.0)
        check_same_constant(b'abc')
        check_same_constant('abc')
        f1, f2 = lambda : ..., lambda : ...
        self.assertIs(f1.__code__, f2.__code__)
        self.check_constant(f1, Ellipsis)
        self.assertEqual(repr(f1()), repr(Ellipsis))
        f1, f2 = lambda x: x in {0}, lambda x: x in {0}
        self.assertIs(f1.__code__, f2.__code__)
        self.check_constant(f1, frozenset({0}))
        self.assertTrue(f1(0))

    def test_dont_merge_constants(self):

        def check_different_constants(const1, const2):
            ns = {}
            exec('f1, f2 = lambda: %r, lambda: %r' % (const1, const2), ns)
            f1 = ns['f1']
            f2 = ns['f2']
            self.assertIsNot(f1.__code__, f2.__code__)
            self.assertNotEqual(f1.__code__, f2.__code__)
            self.check_constant(f1, const1)
            self.check_constant(f2, const2)
            self.assertEqual(repr(f1()), repr(const1))
            self.assertEqual(repr(f2()), repr(const2))
        check_different_constants(0, 0.0)
        check_different_constants(+0.0, -0.0)
        check_different_constants((0,), (0.0,))
        check_different_constants('a', b'a')
        check_different_constants(('a',), (b'a',))
        f1, f2 = lambda : +0j, lambda : -0j
        self.assertIsNot(f1.__code__, f2.__code__)
        self.check_constant(f1, +0j)
        self.check_constant(f2, -0j)
        self.assertEqual(repr(f1()), repr(+0j))
        self.assertEqual(repr(f2()), repr(-0j))
        f1, f2 = lambda x: x in {0}, lambda x: x in {0.0}
        self.assertIsNot(f1.__code__, f2.__code__)
        self.check_constant(f1, frozenset({0}))
        self.check_constant(f2, frozenset({0.0}))
        self.assertTrue(f1(0))
        self.assertTrue(f2(0.0))

    def test_path_like_objects(self):


        class PathLike:

            def __init__(self, path):
                self._path = path

            def __fspath__(self):
                return self._path
        compile('42', PathLike('test_compile_pathlike'), 'single')


class TestStackSize(unittest.TestCase):
    N = 100

    def check_stack_size(self, code):
        if isinstance(code, str):
            code = compile(code, '<foo>', 'single')
        max_size = math.ceil(math.log(len(code.co_code)))
        self.assertLessEqual(code.co_stacksize, max_size)

    def test_and(self):
        self.check_stack_size('x and ' * self.N + 'x')

    def test_or(self):
        self.check_stack_size('x or ' * self.N + 'x')

    def test_and_or(self):
        self.check_stack_size('x and x or ' * self.N + 'x')

    def test_chained_comparison(self):
        self.check_stack_size('x < ' * self.N + 'x')

    def test_if_else(self):
        self.check_stack_size('x if x else ' * self.N + 'x')

    def test_binop(self):
        self.check_stack_size('x + ' * self.N + 'x')

    def test_func_and(self):
        code = 'def f(x):\n'
        code += '   x and x\n' * self.N
        self.check_stack_size(code)


if __name__ == '__main__':
    unittest.main()
