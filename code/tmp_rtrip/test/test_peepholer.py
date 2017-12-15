import dis
import re
import sys
import textwrap
import unittest
from test.bytecode_helper import BytecodeTestCase


class TestTranforms(BytecodeTestCase):

    def test_unot(self):

        def unot(x):
            if not x == 2:
                del x
        self.assertNotInBytecode(unot, 'UNARY_NOT')
        self.assertNotInBytecode(unot, 'POP_JUMP_IF_FALSE')
        self.assertInBytecode(unot, 'POP_JUMP_IF_TRUE')

    def test_elim_inversion_of_is_or_in(self):
        for line, cmp_op in (('not a is b', 'is not'), ('not a in b',
            'not in'), ('not a is not b', 'is'), ('not a not in b', 'in')):
            code = compile(line, '', 'single')
            self.assertInBytecode(code, 'COMPARE_OP', cmp_op)

    def test_global_as_constant(self):

        def f():
            x = None
            x = None
            return x

        def g():
            x = True
            return x

        def h():
            x = False
            return x
        for func, elem in ((f, None), (g, True), (h, False)):
            self.assertNotInBytecode(func, 'LOAD_GLOBAL')
            self.assertInBytecode(func, 'LOAD_CONST', elem)

        def f():
            """Adding a docstring made this test fail in Py2.5.0"""
            return None
        self.assertNotInBytecode(f, 'LOAD_GLOBAL')
        self.assertInBytecode(f, 'LOAD_CONST', None)

    def test_while_one(self):

        def f():
            while 1:
                pass
            return list
        for elem in ('LOAD_CONST', 'POP_JUMP_IF_FALSE'):
            self.assertNotInBytecode(f, elem)
        for elem in ('JUMP_ABSOLUTE',):
            self.assertInBytecode(f, elem)

    def test_pack_unpack(self):
        for line, elem in (('a, = a,', 'LOAD_CONST'), ('a, b = a, b',
            'ROT_TWO'), ('a, b, c = a, b, c', 'ROT_THREE')):
            code = compile(line, '', 'single')
            self.assertInBytecode(code, elem)
            self.assertNotInBytecode(code, 'BUILD_TUPLE')
            self.assertNotInBytecode(code, 'UNPACK_TUPLE')

    def test_folding_of_tuples_of_constants(self):
        for line, elem in (('a = 1,2,3', (1, 2, 3)), ('("a","b","c")', ('a',
            'b', 'c')), ('a,b,c = 1,2,3', (1, 2, 3)), ('(None, 1, None)', (
            None, 1, None)), ('((1, 2), 3, 4)', ((1, 2), 3, 4))):
            code = compile(line, '', 'single')
            self.assertInBytecode(code, 'LOAD_CONST', elem)
            self.assertNotInBytecode(code, 'BUILD_TUPLE')
        code = compile(repr(tuple(range(10000))), '', 'single')
        self.assertNotInBytecode(code, 'BUILD_TUPLE')
        load_consts = [instr for instr in dis.get_instructions(code) if 
            instr.opname == 'LOAD_CONST']
        self.assertEqual(len(load_consts), 2)

        def crater():
            ~[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0,
                1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0,
                1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0,
                1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0,
                1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],

    def test_folding_of_lists_of_constants(self):
        for line, elem in (('a in [1,2,3]', (1, 2, 3)), (
            'a not in ["a","b","c"]', ('a', 'b', 'c')), (
            'a in [None, 1, None]', (None, 1, None)), (
            'a not in [(1, 2), 3, 4]', ((1, 2), 3, 4))):
            code = compile(line, '', 'single')
            self.assertInBytecode(code, 'LOAD_CONST', elem)
            self.assertNotInBytecode(code, 'BUILD_LIST')

    def test_folding_of_sets_of_constants(self):
        for line, elem in (('a in {1,2,3}', frozenset({1, 2, 3})), (
            'a not in {"a","b","c"}', frozenset({'a', 'c', 'b'})), (
            'a in {None, 1, None}', frozenset({1, None})), (
            'a not in {(1, 2), 3, 4}', frozenset({(1, 2), 3, 4})), (
            'a in {1, 2, 3, 3, 2, 1}', frozenset({1, 2, 3}))):
            code = compile(line, '', 'single')
            self.assertNotInBytecode(code, 'BUILD_SET')
            self.assertInBytecode(code, 'LOAD_CONST', elem)

        def f(a):
            return a in {1, 2, 3}

        def g(a):
            return a not in {1, 2, 3}
        self.assertTrue(f(3))
        self.assertTrue(not f(4))
        self.assertTrue(not g(3))
        self.assertTrue(g(4))

    def test_folding_of_binops_on_constants(self):
        for line, elem in (('a = 2+3+4', 9), ('"@"*4', '@@@@'), (
            'a="abc" + "def"', 'abcdef'), ('a = 3**4', 81), ('a = 3*4', 12),
            ('a = 13//4', 3), ('a = 14%4', 2), ('a = 2+3', 5), ('a = 13-4',
            9), ('a = (12,13)[1]', 13), ('a = 13 << 2', 52), ('a = 13 >> 2',
            3), ('a = 13 & 7', 5), ('a = 13 ^ 7', 10), ('a = 13 | 7', 15)):
            code = compile(line, '', 'single')
            self.assertInBytecode(code, 'LOAD_CONST', elem)
            for instr in dis.get_instructions(code):
                self.assertFalse(instr.opname.startswith('BINARY_'))
        code = compile('a=2+"b"', '', 'single')
        self.assertInBytecode(code, 'LOAD_CONST', 2)
        self.assertInBytecode(code, 'LOAD_CONST', 'b')
        code = compile('a="x"*1000', '', 'single')
        self.assertInBytecode(code, 'LOAD_CONST', 1000)

    def test_binary_subscr_on_unicode(self):
        code = compile('"foo"[0]', '', 'single')
        self.assertInBytecode(code, 'LOAD_CONST', 'f')
        self.assertNotInBytecode(code, 'BINARY_SUBSCR')
        code = compile('"a\uffff"[1]', '', 'single')
        self.assertInBytecode(code, 'LOAD_CONST', '\uffff')
        self.assertNotInBytecode(code, 'BINARY_SUBSCR')
        code = compile('"𒍅"[0]', '', 'single')
        self.assertInBytecode(code, 'LOAD_CONST', '𒍅')
        self.assertNotInBytecode(code, 'BINARY_SUBSCR')
        code = compile('"fuu"[10]', '', 'single')
        self.assertInBytecode(code, 'BINARY_SUBSCR')

    def test_folding_of_unaryops_on_constants(self):
        for line, elem in (('-0.5', -0.5), ('-0.0', -0.0), ('-(1.0-1.0)', -
            0.0), ('-0', 0), ('~-2', 1), ('+1', 1)):
            code = compile(line, '', 'single')
            self.assertInBytecode(code, 'LOAD_CONST', elem)
            for instr in dis.get_instructions(code):
                self.assertFalse(instr.opname.startswith('UNARY_'))

        def negzero():
            return -(1.0 - 1.0)
        for instr in dis.get_instructions(code):
            self.assertFalse(instr.opname.startswith('UNARY_'))
        for line, elem, opname in (('-"abc"', 'abc', 'UNARY_NEGATIVE'), (
            '~"abc"', 'abc', 'UNARY_INVERT')):
            code = compile(line, '', 'single')
            self.assertInBytecode(code, 'LOAD_CONST', elem)
            self.assertInBytecode(code, opname)

    def test_elim_extra_return(self):

        def f(x):
            return x
        self.assertNotInBytecode(f, 'LOAD_CONST', None)
        returns = [instr for instr in dis.get_instructions(f) if instr.
            opname == 'RETURN_VALUE']
        self.assertEqual(len(returns), 1)

    def test_elim_jump_to_return(self):

        def f(cond, true_value, false_value):
            return true_value if cond else false_value
        self.assertNotInBytecode(f, 'JUMP_FORWARD')
        self.assertNotInBytecode(f, 'JUMP_ABSOLUTE')
        returns = [instr for instr in dis.get_instructions(f) if instr.
            opname == 'RETURN_VALUE']
        self.assertEqual(len(returns), 2)

    def test_elim_jump_after_return1(self):

        def f(cond1, cond2):
            if cond1:
                return 1
            if cond2:
                return 2
            while 1:
                return 3
            while 1:
                if cond1:
                    return 4
                return 5
            return 6
        self.assertNotInBytecode(f, 'JUMP_FORWARD')
        self.assertNotInBytecode(f, 'JUMP_ABSOLUTE')
        returns = [instr for instr in dis.get_instructions(f) if instr.
            opname == 'RETURN_VALUE']
        self.assertEqual(len(returns), 6)

    def test_elim_jump_after_return2(self):

        def f(cond1, cond2):
            while 1:
                if cond1:
                    return 4
        self.assertNotInBytecode(f, 'JUMP_FORWARD')
        returns = [instr for instr in dis.get_instructions(f) if instr.
            opname == 'JUMP_ABSOLUTE']
        self.assertEqual(len(returns), 1)
        returns = [instr for instr in dis.get_instructions(f) if instr.
            opname == 'RETURN_VALUE']
        self.assertEqual(len(returns), 2)

    def test_make_function_doesnt_bail(self):

        def f():

            def g() ->(1 + 1):
                pass
            return g
        self.assertNotInBytecode(f, 'BINARY_ADD')

    def test_constant_folding(self):
        exprs = ['3 * -5', '-3 * 5', '2 * (3 * 4)', '(2 * 3) * 4',
            '(-1, 2, 3)', '(1, -2, 3)', '(1, 2, -3)', '(1, 2, -3) * 6',
            'lambda x: x in {(3 * -5) + (-1 - 6), (1, -2, 3) * 2, None}']
        for e in exprs:
            code = compile(e, '', 'single')
            for instr in dis.get_instructions(code):
                self.assertFalse(instr.opname.startswith('UNARY_'))
                self.assertFalse(instr.opname.startswith('BINARY_'))
                self.assertFalse(instr.opname.startswith('BUILD_'))


class TestBuglets(unittest.TestCase):

    def test_bug_11510(self):

        def f():
            x, y = {1, 1}
            return x, y
        with self.assertRaises(ValueError):
            f()


if __name__ == '__main__':
    unittest.main()
