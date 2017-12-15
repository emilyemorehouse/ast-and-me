""" Test script for the Unicode implementation.

Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""
import _string
import codecs
import itertools
import operator
import struct
import string
import sys
import unittest
import warnings
from test import support, string_tests


def search_function(encoding):

    def decode1(input, errors='strict'):
        return 42

    def encode1(input, errors='strict'):
        return 42

    def encode2(input, errors='strict'):
        return 42, 42

    def decode2(input, errors='strict'):
        return 42, 42
    if encoding == 'test.unicode1':
        return encode1, decode1, None, None
    elif encoding == 'test.unicode2':
        return encode2, decode2, None, None
    else:
        return None


codecs.register(search_function)


def duplicate_string(text):
    """
    Try to get a fresh clone of the specified text:
    new object with a reference count of 1.

    This is a best-effort: latin1 single letters and the empty
    string ('') are singletons and cannot be cloned.
    """
    return text.encode().decode()


class StrSubclass(str):
    pass


class UnicodeTest(string_tests.CommonTest, string_tests.
    MixinStrUnicodeUserStringTest, string_tests.MixinStrUnicodeTest,
    unittest.TestCase):
    type2test = str

    def checkequalnofix(self, result, object, methodname, *args):
        method = getattr(object, methodname)
        realresult = method(*args)
        self.assertEqual(realresult, result)
        self.assertTrue(type(realresult) is type(result))
        if realresult is object:


            class usub(str):

                def __repr__(self):
                    return 'usub(%r)' % str.__repr__(self)
            object = usub(object)
            method = getattr(object, methodname)
            realresult = method(*args)
            self.assertEqual(realresult, result)
            self.assertTrue(object is not realresult)

    def test_literals(self):
        self.assertEqual('ÿ', 'ÿ')
        self.assertEqual('\uffff', '\uffff')
        self.assertRaises(SyntaxError, eval, "'\\Ufffffffe'")
        self.assertRaises(SyntaxError, eval, "'\\Uffffffff'")
        self.assertRaises(SyntaxError, eval, "'\\U%08x'" % 1114112)
        self.assertNotEqual('\\u0020', ' ')

    def test_ascii(self):
        if not sys.platform.startswith('java'):
            self.assertEqual(ascii('abc'), "'abc'")
            self.assertEqual(ascii('ab\\c'), "'ab\\\\c'")
            self.assertEqual(ascii('ab\\'), "'ab\\\\'")
            self.assertEqual(ascii('\\c'), "'\\\\c'")
            self.assertEqual(ascii('\\'), "'\\\\'")
            self.assertEqual(ascii('\n'), "'\\n'")
            self.assertEqual(ascii('\r'), "'\\r'")
            self.assertEqual(ascii('\t'), "'\\t'")
            self.assertEqual(ascii('\x08'), "'\\x08'")
            self.assertEqual(ascii('\'"'), '\'\\\'"\'')
            self.assertEqual(ascii('\'"'), '\'\\\'"\'')
            self.assertEqual(ascii("'"), '"\'"')
            self.assertEqual(ascii('"'), '\'"\'')
            latin1repr = (
                '\'\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&\\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\\x7f\\x80\\x81\\x82\\x83\\x84\\x85\\x86\\x87\\x88\\x89\\x8a\\x8b\\x8c\\x8d\\x8e\\x8f\\x90\\x91\\x92\\x93\\x94\\x95\\x96\\x97\\x98\\x99\\x9a\\x9b\\x9c\\x9d\\x9e\\x9f\\xa0\\xa1\\xa2\\xa3\\xa4\\xa5\\xa6\\xa7\\xa8\\xa9\\xaa\\xab\\xac\\xad\\xae\\xaf\\xb0\\xb1\\xb2\\xb3\\xb4\\xb5\\xb6\\xb7\\xb8\\xb9\\xba\\xbb\\xbc\\xbd\\xbe\\xbf\\xc0\\xc1\\xc2\\xc3\\xc4\\xc5\\xc6\\xc7\\xc8\\xc9\\xca\\xcb\\xcc\\xcd\\xce\\xcf\\xd0\\xd1\\xd2\\xd3\\xd4\\xd5\\xd6\\xd7\\xd8\\xd9\\xda\\xdb\\xdc\\xdd\\xde\\xdf\\xe0\\xe1\\xe2\\xe3\\xe4\\xe5\\xe6\\xe7\\xe8\\xe9\\xea\\xeb\\xec\\xed\\xee\\xef\\xf0\\xf1\\xf2\\xf3\\xf4\\xf5\\xf6\\xf7\\xf8\\xf9\\xfa\\xfb\\xfc\\xfd\\xfe\\xff\''
                )
            testrepr = ascii(''.join(map(chr, range(256))))
            self.assertEqual(testrepr, latin1repr)
            self.assertEqual(ascii('𐀀' * 39 + '\uffff' * 4096), ascii('𐀀' *
                39 + '\uffff' * 4096))


            class WrongRepr:

                def __repr__(self):
                    return b'byte-repr'
            self.assertRaises(TypeError, ascii, WrongRepr())

    def test_repr(self):
        if not sys.platform.startswith('java'):
            self.assertEqual(repr('abc'), "'abc'")
            self.assertEqual(repr('ab\\c'), "'ab\\\\c'")
            self.assertEqual(repr('ab\\'), "'ab\\\\'")
            self.assertEqual(repr('\\c'), "'\\\\c'")
            self.assertEqual(repr('\\'), "'\\\\'")
            self.assertEqual(repr('\n'), "'\\n'")
            self.assertEqual(repr('\r'), "'\\r'")
            self.assertEqual(repr('\t'), "'\\t'")
            self.assertEqual(repr('\x08'), "'\\x08'")
            self.assertEqual(repr('\'"'), '\'\\\'"\'')
            self.assertEqual(repr('\'"'), '\'\\\'"\'')
            self.assertEqual(repr("'"), '"\'"')
            self.assertEqual(repr('"'), '\'"\'')
            latin1repr = (
                '\'\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&\\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\\x7f\\x80\\x81\\x82\\x83\\x84\\x85\\x86\\x87\\x88\\x89\\x8a\\x8b\\x8c\\x8d\\x8e\\x8f\\x90\\x91\\x92\\x93\\x94\\x95\\x96\\x97\\x98\\x99\\x9a\\x9b\\x9c\\x9d\\x9e\\x9f\\xa0¡¢£¤¥¦§¨©ª«¬\\xad®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ\''
                )
            testrepr = repr(''.join(map(chr, range(256))))
            self.assertEqual(testrepr, latin1repr)
            self.assertEqual(repr('𐀀' * 39 + '\uffff' * 4096), repr('𐀀' * 
                39 + '\uffff' * 4096))


            class WrongRepr:

                def __repr__(self):
                    return b'byte-repr'
            self.assertRaises(TypeError, repr, WrongRepr())

    def test_iterators(self):
        it = 'ᄑ∢㌳'.__iter__()
        self.assertEqual(next(it), 'ᄑ')
        self.assertEqual(next(it), '∢')
        self.assertEqual(next(it), '㌳')
        self.assertRaises(StopIteration, next, it)

    def test_count(self):
        string_tests.CommonTest.test_count(self)
        self.checkequalnofix(3, 'aaa', 'count', 'a')
        self.checkequalnofix(0, 'aaa', 'count', 'b')
        self.checkequalnofix(3, 'aaa', 'count', 'a')
        self.checkequalnofix(0, 'aaa', 'count', 'b')
        self.checkequalnofix(0, 'aaa', 'count', 'b')
        self.checkequalnofix(1, 'aaa', 'count', 'a', -1)
        self.checkequalnofix(3, 'aaa', 'count', 'a', -10)
        self.checkequalnofix(2, 'aaa', 'count', 'a', 0, -1)
        self.checkequalnofix(0, 'aaa', 'count', 'a', 0, -10)
        self.checkequal(10, 'Ă' + 'a' * 10, 'count', 'a')
        self.checkequal(10, '\U00100304' + 'a' * 10, 'count', 'a')
        self.checkequal(10, '\U00100304' + 'Ă' * 10, 'count', 'Ă')
        self.checkequal(0, 'a' * 10, 'count', 'Ă')
        self.checkequal(0, 'a' * 10, 'count', '\U00100304')
        self.checkequal(0, 'Ă' * 10, 'count', '\U00100304')
        self.checkequal(10, 'Ă' + 'a_' * 10, 'count', 'a_')
        self.checkequal(10, '\U00100304' + 'a_' * 10, 'count', 'a_')
        self.checkequal(10, '\U00100304' + 'Ă_' * 10, 'count', 'Ă_')
        self.checkequal(0, 'a' * 10, 'count', 'aĂ')
        self.checkequal(0, 'a' * 10, 'count', 'a\U00100304')
        self.checkequal(0, 'Ă' * 10, 'count', 'Ă\U00100304')

    def test_find(self):
        string_tests.CommonTest.test_find(self)
        self.checkequal(100, 'a' * 100 + 'Ă', 'find', 'Ă')
        self.checkequal(-1, 'a' * 100 + 'Ă', 'find', 'ȁ')
        self.checkequal(-1, 'a' * 100 + 'Ă', 'find', 'Ġ')
        self.checkequal(-1, 'a' * 100 + 'Ă', 'find', 'Ƞ')
        self.checkequal(100, 'a' * 100 + '\U00100304', 'find', '\U00100304')
        self.checkequal(-1, 'a' * 100 + '\U00100304', 'find', '\U00100204')
        self.checkequal(-1, 'a' * 100 + '\U00100304', 'find', '\U00102004')
        self.checkequalnofix(0, 'abcdefghiabc', 'find', 'abc')
        self.checkequalnofix(9, 'abcdefghiabc', 'find', 'abc', 1)
        self.checkequalnofix(-1, 'abcdefghiabc', 'find', 'def', 4)
        self.assertRaises(TypeError, 'hello'.find)
        self.assertRaises(TypeError, 'hello'.find, 42)
        self.checkequal(100, 'Ă' * 100 + 'a', 'find', 'a')
        self.checkequal(100, '\U00100304' * 100 + 'a', 'find', 'a')
        self.checkequal(100, '\U00100304' * 100 + 'Ă', 'find', 'Ă')
        self.checkequal(-1, 'a' * 100, 'find', 'Ă')
        self.checkequal(-1, 'a' * 100, 'find', '\U00100304')
        self.checkequal(-1, 'Ă' * 100, 'find', '\U00100304')
        self.checkequal(100, 'Ă' * 100 + 'a_', 'find', 'a_')
        self.checkequal(100, '\U00100304' * 100 + 'a_', 'find', 'a_')
        self.checkequal(100, '\U00100304' * 100 + 'Ă_', 'find', 'Ă_')
        self.checkequal(-1, 'a' * 100, 'find', 'aĂ')
        self.checkequal(-1, 'a' * 100, 'find', 'a\U00100304')
        self.checkequal(-1, 'Ă' * 100, 'find', 'Ă\U00100304')

    def test_rfind(self):
        string_tests.CommonTest.test_rfind(self)
        self.checkequal(0, 'Ă' + 'a' * 100, 'rfind', 'Ă')
        self.checkequal(-1, 'Ă' + 'a' * 100, 'rfind', 'ȁ')
        self.checkequal(-1, 'Ă' + 'a' * 100, 'rfind', 'Ġ')
        self.checkequal(-1, 'Ă' + 'a' * 100, 'rfind', 'Ƞ')
        self.checkequal(0, '\U00100304' + 'a' * 100, 'rfind', '\U00100304')
        self.checkequal(-1, '\U00100304' + 'a' * 100, 'rfind', '\U00100204')
        self.checkequal(-1, '\U00100304' + 'a' * 100, 'rfind', '\U00102004')
        self.checkequalnofix(9, 'abcdefghiabc', 'rfind', 'abc')
        self.checkequalnofix(12, 'abcdefghiabc', 'rfind', '')
        self.checkequalnofix(12, 'abcdefghiabc', 'rfind', '')
        self.checkequal(0, 'a' + 'Ă' * 100, 'rfind', 'a')
        self.checkequal(0, 'a' + '\U00100304' * 100, 'rfind', 'a')
        self.checkequal(0, 'Ă' + '\U00100304' * 100, 'rfind', 'Ă')
        self.checkequal(-1, 'a' * 100, 'rfind', 'Ă')
        self.checkequal(-1, 'a' * 100, 'rfind', '\U00100304')
        self.checkequal(-1, 'Ă' * 100, 'rfind', '\U00100304')
        self.checkequal(0, '_a' + 'Ă' * 100, 'rfind', '_a')
        self.checkequal(0, '_a' + '\U00100304' * 100, 'rfind', '_a')
        self.checkequal(0, '_Ă' + '\U00100304' * 100, 'rfind', '_Ă')
        self.checkequal(-1, 'a' * 100, 'rfind', 'Ăa')
        self.checkequal(-1, 'a' * 100, 'rfind', '\U00100304a')
        self.checkequal(-1, 'Ă' * 100, 'rfind', '\U00100304Ă')

    def test_index(self):
        string_tests.CommonTest.test_index(self)
        self.checkequalnofix(0, 'abcdefghiabc', 'index', '')
        self.checkequalnofix(3, 'abcdefghiabc', 'index', 'def')
        self.checkequalnofix(0, 'abcdefghiabc', 'index', 'abc')
        self.checkequalnofix(9, 'abcdefghiabc', 'index', 'abc', 1)
        self.assertRaises(ValueError, 'abcdefghiabc'.index, 'hib')
        self.assertRaises(ValueError, 'abcdefghiab'.index, 'abc', 1)
        self.assertRaises(ValueError, 'abcdefghi'.index, 'ghi', 8)
        self.assertRaises(ValueError, 'abcdefghi'.index, 'ghi', -1)
        self.checkequal(100, 'Ă' * 100 + 'a', 'index', 'a')
        self.checkequal(100, '\U00100304' * 100 + 'a', 'index', 'a')
        self.checkequal(100, '\U00100304' * 100 + 'Ă', 'index', 'Ă')
        self.assertRaises(ValueError, ('a' * 100).index, 'Ă')
        self.assertRaises(ValueError, ('a' * 100).index, '\U00100304')
        self.assertRaises(ValueError, ('Ă' * 100).index, '\U00100304')
        self.checkequal(100, 'Ă' * 100 + 'a_', 'index', 'a_')
        self.checkequal(100, '\U00100304' * 100 + 'a_', 'index', 'a_')
        self.checkequal(100, '\U00100304' * 100 + 'Ă_', 'index', 'Ă_')
        self.assertRaises(ValueError, ('a' * 100).index, 'aĂ')
        self.assertRaises(ValueError, ('a' * 100).index, 'a\U00100304')
        self.assertRaises(ValueError, ('Ă' * 100).index, 'Ă\U00100304')

    def test_rindex(self):
        string_tests.CommonTest.test_rindex(self)
        self.checkequalnofix(12, 'abcdefghiabc', 'rindex', '')
        self.checkequalnofix(3, 'abcdefghiabc', 'rindex', 'def')
        self.checkequalnofix(9, 'abcdefghiabc', 'rindex', 'abc')
        self.checkequalnofix(0, 'abcdefghiabc', 'rindex', 'abc', 0, -1)
        self.assertRaises(ValueError, 'abcdefghiabc'.rindex, 'hib')
        self.assertRaises(ValueError, 'defghiabc'.rindex, 'def', 1)
        self.assertRaises(ValueError, 'defghiabc'.rindex, 'abc', 0, -1)
        self.assertRaises(ValueError, 'abcdefghi'.rindex, 'ghi', 0, 8)
        self.assertRaises(ValueError, 'abcdefghi'.rindex, 'ghi', 0, -1)
        self.checkequal(0, 'a' + 'Ă' * 100, 'rindex', 'a')
        self.checkequal(0, 'a' + '\U00100304' * 100, 'rindex', 'a')
        self.checkequal(0, 'Ă' + '\U00100304' * 100, 'rindex', 'Ă')
        self.assertRaises(ValueError, ('a' * 100).rindex, 'Ă')
        self.assertRaises(ValueError, ('a' * 100).rindex, '\U00100304')
        self.assertRaises(ValueError, ('Ă' * 100).rindex, '\U00100304')
        self.checkequal(0, '_a' + 'Ă' * 100, 'rindex', '_a')
        self.checkequal(0, '_a' + '\U00100304' * 100, 'rindex', '_a')
        self.checkequal(0, '_Ă' + '\U00100304' * 100, 'rindex', '_Ă')
        self.assertRaises(ValueError, ('a' * 100).rindex, 'Ăa')
        self.assertRaises(ValueError, ('a' * 100).rindex, '\U00100304a')
        self.assertRaises(ValueError, ('Ă' * 100).rindex, '\U00100304Ă')

    def test_maketrans_translate(self):
        self.checkequalnofix('bbbc', 'abababc', 'translate', {ord('a'): None})
        self.checkequalnofix('iiic', 'abababc', 'translate', {ord('a'):
            None, ord('b'): ord('i')})
        self.checkequalnofix('iiix', 'abababc', 'translate', {ord('a'):
            None, ord('b'): ord('i'), ord('c'): 'x'})
        self.checkequalnofix('c', 'abababc', 'translate', {ord('a'): None,
            ord('b'): ''})
        self.checkequalnofix('xyyx', 'xzx', 'translate', {ord('z'): 'yy'})
        self.checkequalnofix('abababc', 'abababc', 'translate', {'b': '<i>'})
        tbl = self.type2test.maketrans({'a': None, 'b': '<i>'})
        self.checkequalnofix('<i><i><i>c', 'abababc', 'translate', tbl)
        tbl = self.type2test.maketrans('abc', 'xyz', 'd')
        self.checkequalnofix('xyzzy', 'abdcdcbdddd', 'translate', tbl)
        self.assertEqual('[a]'.translate(str.maketrans('a', 'X')), '[X]')
        self.assertEqual('[a]'.translate(str.maketrans({'a': 'X'})), '[X]')
        self.assertEqual('[a]'.translate(str.maketrans({'a': None})), '[]')
        self.assertEqual('[a]'.translate(str.maketrans({'a': 'XXX'})), '[XXX]')
        self.assertEqual('[a]'.translate(str.maketrans({'a': 'é'})), '[é]')
        self.assertEqual('axb'.translate(str.maketrans({'a': None, 'b':
            '123'})), 'x123')
        self.assertEqual('axb'.translate(str.maketrans({'a': None, 'b': 'é'
            })), 'xé')
        self.assertEqual('[a]'.translate(str.maketrans({'a': '<é>'})), '[<é>]')
        self.assertEqual('[é]'.translate(str.maketrans({'é': 'a'})), '[a]')
        self.assertEqual('[é]'.translate(str.maketrans({'é': None})), '[]')
        self.assertEqual('[é]'.translate(str.maketrans({'é': '123'})), '[123]')
        self.assertEqual('[aé]'.translate(str.maketrans({'a': '<€>'})),
            '[<€>é]')
        invalid_char = 1114111 + 1
        for before in 'aé€\U0010ffff':
            mapping = str.maketrans({before: invalid_char})
            text = '[%s]' % before
            self.assertRaises(ValueError, text.translate, mapping)
        self.assertRaises(TypeError, self.type2test.maketrans)
        self.assertRaises(ValueError, self.type2test.maketrans, 'abc', 'defg')
        self.assertRaises(TypeError, self.type2test.maketrans, 2, 'def')
        self.assertRaises(TypeError, self.type2test.maketrans, 'abc', 2)
        self.assertRaises(TypeError, self.type2test.maketrans, 'abc', 'def', 2)
        self.assertRaises(ValueError, self.type2test.maketrans, {'xy': 2})
        self.assertRaises(TypeError, self.type2test.maketrans, {(1,): 2})
        self.assertRaises(TypeError, 'hello'.translate)
        self.assertRaises(TypeError, 'abababc'.translate, 'abc', 'xyz')

    def test_split(self):
        string_tests.CommonTest.test_split(self)
        for left, right in ('ba', 'āĀ', '𐌁𐌀'):
            left *= 9
            right *= 9
            for delim in ('c', 'Ă', '𐌂'):
                self.checkequal([left + right], left + right, 'split', delim)
                self.checkequal([left, right], left + delim + right,
                    'split', delim)
                self.checkequal([left + right], left + right, 'split', 
                    delim * 2)
                self.checkequal([left, right], left + delim * 2 + right,
                    'split', delim * 2)

    def test_rsplit(self):
        string_tests.CommonTest.test_rsplit(self)
        for left, right in ('ba', 'āĀ', '𐌁𐌀'):
            left *= 9
            right *= 9
            for delim in ('c', 'Ă', '𐌂'):
                self.checkequal([left + right], left + right, 'rsplit', delim)
                self.checkequal([left, right], left + delim + right,
                    'rsplit', delim)
                self.checkequal([left + right], left + right, 'rsplit', 
                    delim * 2)
                self.checkequal([left, right], left + delim * 2 + right,
                    'rsplit', delim * 2)

    def test_partition(self):
        string_tests.MixinStrUnicodeUserStringTest.test_partition(self)
        self.checkequal(('ABCDEFGH', '', ''), 'ABCDEFGH', 'partition', '䈀')
        for left, right in ('ba', 'āĀ', '𐌁𐌀'):
            left *= 9
            right *= 9
            for delim in ('c', 'Ă', '𐌂'):
                self.checkequal((left + right, '', ''), left + right,
                    'partition', delim)
                self.checkequal((left, delim, right), left + delim + right,
                    'partition', delim)
                self.checkequal((left + right, '', ''), left + right,
                    'partition', delim * 2)
                self.checkequal((left, delim * 2, right), left + delim * 2 +
                    right, 'partition', delim * 2)

    def test_rpartition(self):
        string_tests.MixinStrUnicodeUserStringTest.test_rpartition(self)
        self.checkequal(('', '', 'ABCDEFGH'), 'ABCDEFGH', 'rpartition', '䈀')
        for left, right in ('ba', 'āĀ', '𐌁𐌀'):
            left *= 9
            right *= 9
            for delim in ('c', 'Ă', '𐌂'):
                self.checkequal(('', '', left + right), left + right,
                    'rpartition', delim)
                self.checkequal((left, delim, right), left + delim + right,
                    'rpartition', delim)
                self.checkequal(('', '', left + right), left + right,
                    'rpartition', delim * 2)
                self.checkequal((left, delim * 2, right), left + delim * 2 +
                    right, 'rpartition', delim * 2)

    def test_join(self):
        string_tests.MixinStrUnicodeUserStringTest.test_join(self)


        class MyWrapper:

            def __init__(self, sval):
                self.sval = sval

            def __str__(self):
                return self.sval
        self.checkequalnofix('a b c d', ' ', 'join', ['a', 'b', 'c', 'd'])
        self.checkequalnofix('abcd', '', 'join', ('a', 'b', 'c', 'd'))
        self.checkequalnofix('w x y z', ' ', 'join', string_tests.Sequence(
            'wxyz'))
        self.checkequalnofix('a b c d', ' ', 'join', ['a', 'b', 'c', 'd'])
        self.checkequalnofix('a b c d', ' ', 'join', ['a', 'b', 'c', 'd'])
        self.checkequalnofix('abcd', '', 'join', ('a', 'b', 'c', 'd'))
        self.checkequalnofix('w x y z', ' ', 'join', string_tests.Sequence(
            'wxyz'))
        self.checkraises(TypeError, ' ', 'join', ['1', '2', MyWrapper('foo')])
        self.checkraises(TypeError, ' ', 'join', ['1', '2', '3', bytes()])
        self.checkraises(TypeError, ' ', 'join', [1, 2, 3])
        self.checkraises(TypeError, ' ', 'join', ['1', '2', 3])

    @unittest.skipIf(sys.maxsize > 2 ** 32,
        'needs too much memory on a 64-bit platform')
    def test_join_overflow(self):
        size = int(sys.maxsize ** 0.5) + 1
        seq = ('A' * size,) * size
        self.assertRaises(OverflowError, ''.join, seq)

    def test_replace(self):
        string_tests.CommonTest.test_replace(self)
        self.checkequalnofix('one@two!three!', 'one!two!three!', 'replace',
            '!', '@', 1)
        self.assertRaises(TypeError, 'replace'.replace, 'r', 42)
        for left, right in ('ba', 'āĀ', '𐌁𐌀'):
            left *= 9
            right *= 9
            for delim in ('c', 'Ă', '𐌂'):
                for repl in ('d', 'ă', '𐌃'):
                    self.checkequal(left + right, left + right, 'replace',
                        delim, repl)
                    self.checkequal(left + repl + right, left + delim +
                        right, 'replace', delim, repl)
                    self.checkequal(left + right, left + right, 'replace', 
                        delim * 2, repl)
                    self.checkequal(left + repl + right, left + delim * 2 +
                        right, 'replace', delim * 2, repl)

    @support.cpython_only
    def test_replace_id(self):
        pattern = 'abc'
        text = 'abc def'
        self.assertIs(text.replace(pattern, pattern), text)

    def test_bytes_comparison(self):
        with support.check_warnings():
            warnings.simplefilter('ignore', BytesWarning)
            self.assertEqual('abc' == b'abc', False)
            self.assertEqual('abc' != b'abc', True)
            self.assertEqual('abc' == bytearray(b'abc'), False)
            self.assertEqual('abc' != bytearray(b'abc'), True)

    def test_comparison(self):
        self.assertEqual('abc', 'abc')
        self.assertTrue('abcd' > 'abc')
        self.assertTrue('abc' < 'abcd')
        if 0:
            self.assertTrue('a' < '€')
            self.assertTrue('a' < '\ud800\udc02')

            def test_lecmp(s, s2):
                self.assertTrue(s < s2)

            def test_fixup(s):
                s2 = '\ud800\udc01'
                test_lecmp(s, s2)
                s2 = '\ud900\udc01'
                test_lecmp(s, s2)
                s2 = '\uda00\udc01'
                test_lecmp(s, s2)
                s2 = '\udb00\udc01'
                test_lecmp(s, s2)
                s2 = '\ud800\udd01'
                test_lecmp(s, s2)
                s2 = '\ud900\udd01'
                test_lecmp(s, s2)
                s2 = '\uda00\udd01'
                test_lecmp(s, s2)
                s2 = '\udb00\udd01'
                test_lecmp(s, s2)
                s2 = '\ud800\ude01'
                test_lecmp(s, s2)
                s2 = '\ud900\ude01'
                test_lecmp(s, s2)
                s2 = '\uda00\ude01'
                test_lecmp(s, s2)
                s2 = '\udb00\ude01'
                test_lecmp(s, s2)
                s2 = '\ud800\udfff'
                test_lecmp(s, s2)
                s2 = '\ud900\udfff'
                test_lecmp(s, s2)
                s2 = '\uda00\udfff'
                test_lecmp(s, s2)
                s2 = '\udb00\udfff'
                test_lecmp(s, s2)
                test_fixup('\ue000')
                test_fixup('｡')
        self.assertTrue('\ud800\udc02' < '\ud84d\udc56')

    def test_islower(self):
        super().test_islower()
        self.checkequalnofix(False, 'ῼ', 'islower')
        self.assertFalse('Ⅷ'.islower())
        self.assertTrue('ⅷ'.islower())
        self.assertFalse('𐐁'.islower())
        self.assertFalse('𐐧'.islower())
        self.assertTrue('𐐩'.islower())
        self.assertTrue('𐑎'.islower())
        self.assertFalse('🐍'.islower())
        self.assertFalse('👯'.islower())

    def test_isupper(self):
        super().test_isupper()
        if not sys.platform.startswith('java'):
            self.checkequalnofix(False, 'ῼ', 'isupper')
        self.assertTrue('Ⅷ'.isupper())
        self.assertFalse('ⅷ'.isupper())
        self.assertTrue('𐐁'.isupper())
        self.assertTrue('𐐧'.isupper())
        self.assertFalse('𐐩'.isupper())
        self.assertFalse('𐑎'.isupper())
        self.assertFalse('🐍'.isupper())
        self.assertFalse('👯'.isupper())

    def test_istitle(self):
        super().test_istitle()
        self.checkequalnofix(True, 'ῼ', 'istitle')
        self.checkequalnofix(True, 'Greek ῼitlecases ...', 'istitle')
        self.assertTrue('𐐁𐐩'.istitle())
        self.assertTrue('𐐧𐑎'.istitle())
        for ch in ['𐐩', '𐑎', '🐍', '👯']:
            self.assertFalse(ch.istitle(), '{!a} is not title'.format(ch))

    def test_isspace(self):
        super().test_isspace()
        self.checkequalnofix(True, '\u2000', 'isspace')
        self.checkequalnofix(True, '\u200a', 'isspace')
        self.checkequalnofix(False, '—', 'isspace')
        for ch in ['𐐁', '𐐧', '𐐩', '𐑎', '🐍', '👯']:
            self.assertFalse(ch.isspace(), '{!a} is not space.'.format(ch))

    def test_isalnum(self):
        super().test_isalnum()
        for ch in ['𐐁', '𐐧', '𐐩', '𐑎', '𝟶', '𑁦', '𐒠', '🄇']:
            self.assertTrue(ch.isalnum(), '{!a} is alnum.'.format(ch))

    def test_isalpha(self):
        super().test_isalpha()
        self.checkequalnofix(True, 'ῼ', 'isalpha')
        self.assertTrue('𐐁'.isalpha())
        self.assertTrue('𐐧'.isalpha())
        self.assertTrue('𐐩'.isalpha())
        self.assertTrue('𐑎'.isalpha())
        self.assertFalse('🐍'.isalpha())
        self.assertFalse('👯'.isalpha())

    def test_isdecimal(self):
        self.checkequalnofix(False, '', 'isdecimal')
        self.checkequalnofix(False, 'a', 'isdecimal')
        self.checkequalnofix(True, '0', 'isdecimal')
        self.checkequalnofix(False, '①', 'isdecimal')
        self.checkequalnofix(False, '¼', 'isdecimal')
        self.checkequalnofix(True, '٠', 'isdecimal')
        self.checkequalnofix(True, '0123456789', 'isdecimal')
        self.checkequalnofix(False, '0123456789a', 'isdecimal')
        self.checkraises(TypeError, 'abc', 'isdecimal', 42)
        for ch in ['𐐁', '𐐧', '𐐩', '𐑎', '🐍', '👯', '𑁥', '🄇']:
            self.assertFalse(ch.isdecimal(), '{!a} is not decimal.'.format(ch))
        for ch in ['𝟶', '𑁦', '𐒠']:
            self.assertTrue(ch.isdecimal(), '{!a} is decimal.'.format(ch))

    def test_isdigit(self):
        super().test_isdigit()
        self.checkequalnofix(True, '①', 'isdigit')
        self.checkequalnofix(False, '¼', 'isdigit')
        self.checkequalnofix(True, '٠', 'isdigit')
        for ch in ['𐐁', '𐐧', '𐐩', '𐑎', '🐍', '👯', '𑁥']:
            self.assertFalse(ch.isdigit(), '{!a} is not a digit.'.format(ch))
        for ch in ['𝟶', '𑁦', '𐒠', '🄇']:
            self.assertTrue(ch.isdigit(), '{!a} is a digit.'.format(ch))

    def test_isnumeric(self):
        self.checkequalnofix(False, '', 'isnumeric')
        self.checkequalnofix(False, 'a', 'isnumeric')
        self.checkequalnofix(True, '0', 'isnumeric')
        self.checkequalnofix(True, '①', 'isnumeric')
        self.checkequalnofix(True, '¼', 'isnumeric')
        self.checkequalnofix(True, '٠', 'isnumeric')
        self.checkequalnofix(True, '0123456789', 'isnumeric')
        self.checkequalnofix(False, '0123456789a', 'isnumeric')
        self.assertRaises(TypeError, 'abc'.isnumeric, 42)
        for ch in ['𐐁', '𐐧', '𐐩', '𐑎', '🐍', '👯']:
            self.assertFalse(ch.isnumeric(), '{!a} is not numeric.'.format(ch))
        for ch in ['𑁥', '𝟶', '𑁦', '𐒠', '🄇']:
            self.assertTrue(ch.isnumeric(), '{!a} is numeric.'.format(ch))

    def test_isidentifier(self):
        self.assertTrue('a'.isidentifier())
        self.assertTrue('Z'.isidentifier())
        self.assertTrue('_'.isidentifier())
        self.assertTrue('b0'.isidentifier())
        self.assertTrue('bc'.isidentifier())
        self.assertTrue('b_'.isidentifier())
        self.assertTrue('µ'.isidentifier())
        self.assertTrue('𝔘𝔫𝔦𝔠𝔬𝔡𝔢'.isidentifier())
        self.assertFalse(' '.isidentifier())
        self.assertFalse('['.isidentifier())
        self.assertFalse('©'.isidentifier())
        self.assertFalse('0'.isidentifier())

    def test_isprintable(self):
        self.assertTrue(''.isprintable())
        self.assertTrue(' '.isprintable())
        self.assertTrue('abcdefg'.isprintable())
        self.assertFalse('abcdefg\n'.isprintable())
        self.assertTrue('ʹ'.isprintable())
        self.assertFalse('\u0378'.isprintable())
        self.assertFalse('\ud800'.isprintable())
        self.assertTrue('👯'.isprintable())
        self.assertFalse('\U000e0020'.isprintable())

    def test_surrogates(self):
        for s in ('a\ud800b\udfff', 'a\udfffb\ud800', 'a\ud800b\udfffa',
            'a\udfffb\ud800a'):
            self.assertTrue(s.islower())
            self.assertFalse(s.isupper())
            self.assertFalse(s.istitle())
        for s in ('A\ud800B\udfff', 'A\udfffB\ud800', 'A\ud800B\udfffA',
            'A\udfffB\ud800A'):
            self.assertFalse(s.islower())
            self.assertTrue(s.isupper())
            self.assertTrue(s.istitle())
        for meth_name in ('islower', 'isupper', 'istitle'):
            meth = getattr(str, meth_name)
            for s in ('\ud800', '\udfff', '\ud800\ud800', '\udfff\udfff'):
                self.assertFalse(meth(s), '%a.%s() is False' % (s, meth_name))
        for meth_name in ('isalpha', 'isalnum', 'isdigit', 'isspace',
            'isdecimal', 'isnumeric', 'isidentifier', 'isprintable'):
            meth = getattr(str, meth_name)
            for s in ('\ud800', '\udfff', '\ud800\ud800', '\udfff\udfff',
                'a\ud800b\udfff', 'a\udfffb\ud800', 'a\ud800b\udfffa',
                'a\udfffb\ud800a'):
                self.assertFalse(meth(s), '%a.%s() is False' % (s, meth_name))

    def test_lower(self):
        string_tests.CommonTest.test_lower(self)
        self.assertEqual('𐐧'.lower(), '𐑏')
        self.assertEqual('𐐧𐐧'.lower(), '𐑏𐑏')
        self.assertEqual('𐐧𐑏'.lower(), '𐑏𐑏')
        self.assertEqual('X𐐧x𐑏'.lower(), 'x𐑏x𐑏')
        self.assertEqual('ﬁ'.lower(), 'ﬁ')
        self.assertEqual('İ'.lower(), 'i̇')
        self.assertEqual('Σ'.lower(), 'σ')
        self.assertEqual('ͅΣ'.lower(), 'ͅσ')
        self.assertEqual('AͅΣ'.lower(), 'aͅς')
        self.assertEqual('AͅΣa'.lower(), 'aͅσa')
        self.assertEqual('AͅΣ'.lower(), 'aͅς')
        self.assertEqual('AΣͅ'.lower(), 'aςͅ')
        self.assertEqual('Σͅ '.lower(), 'σͅ ')
        self.assertEqual('\U0008fffe'.lower(), '\U0008fffe')
        self.assertEqual('ⅷ'.lower(), 'ⅷ')

    def test_casefold(self):
        self.assertEqual('hello'.casefold(), 'hello')
        self.assertEqual('hELlo'.casefold(), 'hello')
        self.assertEqual('ß'.casefold(), 'ss')
        self.assertEqual('ﬁ'.casefold(), 'fi')
        self.assertEqual('Σ'.casefold(), 'σ')
        self.assertEqual('AͅΣ'.casefold(), 'aισ')
        self.assertEqual('µ'.casefold(), 'μ')

    def test_upper(self):
        string_tests.CommonTest.test_upper(self)
        self.assertEqual('𐑏'.upper(), '𐐧')
        self.assertEqual('𐑏𐑏'.upper(), '𐐧𐐧')
        self.assertEqual('𐐧𐑏'.upper(), '𐐧𐐧')
        self.assertEqual('X𐐧x𐑏'.upper(), 'X𐐧X𐐧')
        self.assertEqual('ﬁ'.upper(), 'FI')
        self.assertEqual('İ'.upper(), 'İ')
        self.assertEqual('Σ'.upper(), 'Σ')
        self.assertEqual('ß'.upper(), 'SS')
        self.assertEqual('ῒ'.upper(), 'Ϊ̀')
        self.assertEqual('\U0008fffe'.upper(), '\U0008fffe')
        self.assertEqual('ⅷ'.upper(), 'Ⅷ')

    def test_capitalize(self):
        string_tests.CommonTest.test_capitalize(self)
        self.assertEqual('𐑏'.capitalize(), '𐐧')
        self.assertEqual('𐑏𐑏'.capitalize(), '𐐧𐑏')
        self.assertEqual('𐐧𐑏'.capitalize(), '𐐧𐑏')
        self.assertEqual('𐑏𐐧'.capitalize(), '𐐧𐑏')
        self.assertEqual('X𐐧x𐑏'.capitalize(), 'X𐑏x𐑏')
        self.assertEqual('hİ'.capitalize(), 'Hi̇')
        exp = 'Ϊ̀i̇'
        self.assertEqual('ῒİ'.capitalize(), exp)
        self.assertEqual('ﬁnnish'.capitalize(), 'FInnish')
        self.assertEqual('AͅΣ'.capitalize(), 'Aͅς')

    def test_title(self):
        super().test_title()
        self.assertEqual('𐑏'.title(), '𐐧')
        self.assertEqual('𐑏𐑏'.title(), '𐐧𐑏')
        self.assertEqual('𐑏𐑏 𐑏𐑏'.title(), '𐐧𐑏 𐐧𐑏')
        self.assertEqual('𐐧𐑏 𐐧𐑏'.title(), '𐐧𐑏 𐐧𐑏')
        self.assertEqual('𐑏𐐧 𐑏𐐧'.title(), '𐐧𐑏 𐐧𐑏')
        self.assertEqual('X𐐧x𐑏 X𐐧x𐑏'.title(), 'X𐑏x𐑏 X𐑏x𐑏')
        self.assertEqual('ﬁNNISH'.title(), 'Finnish')
        self.assertEqual('AΣ ᾡxy'.title(), 'Aς ᾩxy')
        self.assertEqual('AΣA'.title(), 'Aσa')

    def test_swapcase(self):
        string_tests.CommonTest.test_swapcase(self)
        self.assertEqual('𐑏'.swapcase(), '𐐧')
        self.assertEqual('𐐧'.swapcase(), '𐑏')
        self.assertEqual('𐑏𐑏'.swapcase(), '𐐧𐐧')
        self.assertEqual('𐐧𐑏'.swapcase(), '𐑏𐐧')
        self.assertEqual('𐑏𐐧'.swapcase(), '𐐧𐑏')
        self.assertEqual('X𐐧x𐑏'.swapcase(), 'x𐑏X𐐧')
        self.assertEqual('ﬁ'.swapcase(), 'FI')
        self.assertEqual('İ'.swapcase(), 'i̇')
        self.assertEqual('Σ'.swapcase(), 'σ')
        self.assertEqual('ͅΣ'.swapcase(), 'Ισ')
        self.assertEqual('AͅΣ'.swapcase(), 'aΙς')
        self.assertEqual('AͅΣa'.swapcase(), 'aΙσA')
        self.assertEqual('AͅΣ'.swapcase(), 'aΙς')
        self.assertEqual('AΣͅ'.swapcase(), 'aςΙ')
        self.assertEqual('Σͅ '.swapcase(), 'σΙ ')
        self.assertEqual('Σ'.swapcase(), 'σ')
        self.assertEqual('ß'.swapcase(), 'SS')
        self.assertEqual('ῒ'.swapcase(), 'Ϊ̀')

    def test_center(self):
        string_tests.CommonTest.test_center(self)
        self.assertEqual('x'.center(2, '\U0010ffff'), 'x\U0010ffff')
        self.assertEqual('x'.center(3, '\U0010ffff'), '\U0010ffffx\U0010ffff')
        self.assertEqual('x'.center(4, '\U0010ffff'),
            '\U0010ffffx\U0010ffff\U0010ffff')

    @unittest.skipUnless(sys.maxsize == 2 ** 31 - 1, 'requires 32-bit system')
    @support.cpython_only
    def test_case_operation_overflow(self):
        size = 2 ** 32 // 12 + 1
        try:
            s = 'ü' * size
        except MemoryError:
            self.skipTest('no enough memory (%.0f MiB required)' % (size / 
                2 ** 20))
        try:
            self.assertRaises(OverflowError, s.upper)
        finally:
            del s

    def test_contains(self):
        self.assertIn('a', 'abdb')
        self.assertIn('a', 'bdab')
        self.assertIn('a', 'bdaba')
        self.assertIn('a', 'bdba')
        self.assertNotIn('a', 'bdb')
        self.assertIn('a', 'bdba')
        self.assertIn('a', ('a', 1, None))
        self.assertIn('a', (1, None, 'a'))
        self.assertIn('a', ('a', 1, None))
        self.assertIn('a', (1, None, 'a'))
        self.assertNotIn('a', ('x', 1, 'y'))
        self.assertNotIn('a', ('x', 1, None))
        self.assertNotIn('abcd', 'abcxxxx')
        self.assertIn('ab', 'abcd')
        self.assertIn('ab', 'abc')
        self.assertIn('ab', (1, None, 'ab'))
        self.assertIn('', 'abc')
        self.assertIn('', '')
        self.assertIn('', 'abc')
        self.assertNotIn('\x00', 'abc')
        self.assertIn('\x00', '\x00abc')
        self.assertIn('\x00', 'abc\x00')
        self.assertIn('a', '\x00abc')
        self.assertIn('asdf', 'asdf')
        self.assertNotIn('asdf', 'asd')
        self.assertNotIn('asdf', '')
        self.assertRaises(TypeError, 'abc'.__contains__)
        for fill in ('a', 'Ā', '𐌀'):
            fill *= 9
            for delim in ('c', 'Ă', '𐌂'):
                self.assertNotIn(delim, fill)
                self.assertIn(delim, fill + delim)
                self.assertNotIn(delim * 2, fill)
                self.assertIn(delim * 2, fill + delim * 2)

    def test_issue18183(self):
        """𐀀􀀀""".lower()
        """𐀀􀀀""".casefold()
        """𐀀􀀀""".upper()
        """𐀀􀀀""".capitalize()
        """𐀀􀀀""".title()
        """𐀀􀀀""".swapcase()
        """􀀀""".center(3, '𐀀')
        """􀀀""".ljust(3, '𐀀')
        """􀀀""".rjust(3, '𐀀')

    def test_format(self):
        self.assertEqual(''.format(), '')
        self.assertEqual('a'.format(), 'a')
        self.assertEqual('ab'.format(), 'ab')
        self.assertEqual('a{{'.format(), 'a{')
        self.assertEqual('a}}'.format(), 'a}')
        self.assertEqual('{{b'.format(), '{b')
        self.assertEqual('}}b'.format(), '}b')
        self.assertEqual('a{{b'.format(), 'a{b')
        import datetime
        self.assertEqual('My name is {0}'.format('Fred'), 'My name is Fred')
        self.assertEqual('My name is {0[name]}'.format(dict(name='Fred')),
            'My name is Fred')
        self.assertEqual('My name is {0} :-{{}}'.format('Fred'),
            'My name is Fred :-{}')
        d = datetime.date(2007, 8, 18)
        self.assertEqual('The year is {0.year}'.format(d), 'The year is 2007')


        class C:

            def __init__(self, x=100):
                self._x = x

            def __format__(self, spec):
                return spec


        class D:

            def __init__(self, x):
                self.x = x

            def __format__(self, spec):
                return str(self.x)


        class E:

            def __init__(self, x):
                self.x = x

            def __str__(self):
                return 'E(' + self.x + ')'


        class F:

            def __init__(self, x):
                self.x = x

            def __repr__(self):
                return 'F(' + self.x + ')'


        class G:

            def __init__(self, x):
                self.x = x

            def __str__(self):
                return 'string is ' + self.x

            def __format__(self, format_spec):
                if format_spec == 'd':
                    return 'G(' + self.x + ')'
                return object.__format__(self, format_spec)


        class I(datetime.date):

            def __format__(self, format_spec):
                return self.strftime(format_spec)


        class J(int):

            def __format__(self, format_spec):
                return int.__format__(self * 2, format_spec)


        class M:

            def __init__(self, x):
                self.x = x

            def __repr__(self):
                return 'M(' + self.x + ')'
            __str__ = None


        class N:

            def __init__(self, x):
                self.x = x

            def __repr__(self):
                return 'N(' + self.x + ')'
            __format__ = None
        self.assertEqual(''.format(), '')
        self.assertEqual('abc'.format(), 'abc')
        self.assertEqual('{0}'.format('abc'), 'abc')
        self.assertEqual('{0:}'.format('abc'), 'abc')
        self.assertEqual('X{0}'.format('abc'), 'Xabc')
        self.assertEqual('{0}X'.format('abc'), 'abcX')
        self.assertEqual('X{0}Y'.format('abc'), 'XabcY')
        self.assertEqual('{1}'.format(1, 'abc'), 'abc')
        self.assertEqual('X{1}'.format(1, 'abc'), 'Xabc')
        self.assertEqual('{1}X'.format(1, 'abc'), 'abcX')
        self.assertEqual('X{1}Y'.format(1, 'abc'), 'XabcY')
        self.assertEqual('{0}'.format(-15), '-15')
        self.assertEqual('{0}{1}'.format(-15, 'abc'), '-15abc')
        self.assertEqual('{0}X{1}'.format(-15, 'abc'), '-15Xabc')
        self.assertEqual('{{'.format(), '{')
        self.assertEqual('}}'.format(), '}')
        self.assertEqual('{{}}'.format(), '{}')
        self.assertEqual('{{x}}'.format(), '{x}')
        self.assertEqual('{{{0}}}'.format(123), '{123}')
        self.assertEqual('{{{{0}}}}'.format(), '{{0}}')
        self.assertEqual('}}{{'.format(), '}{')
        self.assertEqual('}}x{{'.format(), '}x{')
        self.assertEqual('{0[foo-bar]}'.format({'foo-bar': 'baz'}), 'baz')
        self.assertEqual('{0[foo bar]}'.format({'foo bar': 'baz'}), 'baz')
        self.assertEqual('{0[ ]}'.format({' ': 3}), '3')
        self.assertEqual('{foo._x}'.format(foo=C(20)), '20')
        self.assertEqual('{1}{0}'.format(D(10), D(20)), '2010')
        self.assertEqual('{0._x.x}'.format(C(D('abc'))), 'abc')
        self.assertEqual('{0[0]}'.format(['abc', 'def']), 'abc')
        self.assertEqual('{0[1]}'.format(['abc', 'def']), 'def')
        self.assertEqual('{0[1][0]}'.format(['abc', ['def']]), 'def')
        self.assertEqual('{0[1][0].x}'.format(['abc', [D('def')]]), 'def')
        self.assertEqual('{0:.3s}'.format('abc'), 'abc')
        self.assertEqual('{0:.3s}'.format('ab'), 'ab')
        self.assertEqual('{0:.3s}'.format('abcdef'), 'abc')
        self.assertEqual('{0:.0s}'.format('abcdef'), '')
        self.assertEqual('{0:3.3s}'.format('abc'), 'abc')
        self.assertEqual('{0:2.3s}'.format('abc'), 'abc')
        self.assertEqual('{0:2.2s}'.format('abc'), 'ab')
        self.assertEqual('{0:3.2s}'.format('abc'), 'ab ')
        self.assertEqual('{0:x<0s}'.format('result'), 'result')
        self.assertEqual('{0:x<5s}'.format('result'), 'result')
        self.assertEqual('{0:x<6s}'.format('result'), 'result')
        self.assertEqual('{0:x<7s}'.format('result'), 'resultx')
        self.assertEqual('{0:x<8s}'.format('result'), 'resultxx')
        self.assertEqual('{0: <7s}'.format('result'), 'result ')
        self.assertEqual('{0:<7s}'.format('result'), 'result ')
        self.assertEqual('{0:>7s}'.format('result'), ' result')
        self.assertEqual('{0:>8s}'.format('result'), '  result')
        self.assertEqual('{0:^8s}'.format('result'), ' result ')
        self.assertEqual('{0:^9s}'.format('result'), ' result  ')
        self.assertEqual('{0:^10s}'.format('result'), '  result  ')
        self.assertEqual('{0:10000}'.format('a'), 'a' + ' ' * 9999)
        self.assertEqual('{0:10000}'.format(''), ' ' * 10000)
        self.assertEqual('{0:10000000}'.format(''), ' ' * 10000000)
        self.assertEqual('{0:\x00<6s}'.format('foo'), 'foo\x00\x00\x00')
        self.assertEqual('{0:\x01<6s}'.format('foo'), 'foo\x01\x01\x01')
        self.assertEqual('{0:\x00^6s}'.format('foo'), '\x00foo\x00\x00')
        self.assertEqual('{0:^6s}'.format('foo'), ' foo  ')
        self.assertEqual('{0:\x00<6}'.format(3), '3\x00\x00\x00\x00\x00')
        self.assertEqual('{0:\x01<6}'.format(3), '3\x01\x01\x01\x01\x01')
        self.assertEqual('{0:\x00^6}'.format(3), '\x00\x003\x00\x00\x00')
        self.assertEqual('{0:<6}'.format(3), '3     ')
        self.assertEqual('{0:\x00<6}'.format(3.14), '3.14\x00\x00')
        self.assertEqual('{0:\x01<6}'.format(3.14), '3.14\x01\x01')
        self.assertEqual('{0:\x00^6}'.format(3.14), '\x003.14\x00')
        self.assertEqual('{0:^6}'.format(3.14), ' 3.14 ')
        self.assertEqual('{0:\x00<12}'.format(3 + 2j),
            '(3+2j)\x00\x00\x00\x00\x00\x00')
        self.assertEqual('{0:\x01<12}'.format(3 + 2j),
            '(3+2j)\x01\x01\x01\x01\x01\x01')
        self.assertEqual('{0:\x00^12}'.format(3 + 2j),
            '\x00\x00\x00(3+2j)\x00\x00\x00')
        self.assertEqual('{0:^12}'.format(3 + 2j), '   (3+2j)   ')
        self.assertEqual('{0:abc}'.format(C()), 'abc')
        self.assertEqual('{0!s}'.format('Hello'), 'Hello')
        self.assertEqual('{0!s:}'.format('Hello'), 'Hello')
        self.assertEqual('{0!s:15}'.format('Hello'), 'Hello          ')
        self.assertEqual('{0!s:15s}'.format('Hello'), 'Hello          ')
        self.assertEqual('{0!r}'.format('Hello'), "'Hello'")
        self.assertEqual('{0!r:}'.format('Hello'), "'Hello'")
        self.assertEqual('{0!r}'.format(F('Hello')), 'F(Hello)')
        self.assertEqual('{0!r}'.format('\u0378'), "'\\u0378'")
        self.assertEqual('{0!r}'.format('ʹ'), "'ʹ'")
        self.assertEqual('{0!r}'.format(F('ʹ')), 'F(ʹ)')
        self.assertEqual('{0!a}'.format('Hello'), "'Hello'")
        self.assertEqual('{0!a}'.format('\u0378'), "'\\u0378'")
        self.assertEqual('{0!a}'.format('ʹ'), "'\\u0374'")
        self.assertEqual('{0!a:}'.format('Hello'), "'Hello'")
        self.assertEqual('{0!a}'.format(F('Hello')), 'F(Hello)')
        self.assertEqual('{0!a}'.format(F('ʹ')), 'F(\\u0374)')
        self.assertEqual('{0}'.format({}), '{}')
        self.assertEqual('{0}'.format([]), '[]')
        self.assertEqual('{0}'.format([1]), '[1]')
        self.assertEqual('{0:d}'.format(G('data')), 'G(data)')
        self.assertEqual('{0!s}'.format(G('data')), 'string is data')
        self.assertRaises(TypeError, '{0:^10}'.format, E('data'))
        self.assertRaises(TypeError, '{0:^10s}'.format, E('data'))
        self.assertRaises(TypeError, '{0:>15s}'.format, G('data'))
        self.assertEqual('{0:date: %Y-%m-%d}'.format(I(year=2007, month=8,
            day=27)), 'date: 2007-08-27')
        self.assertEqual('{0}'.format(J(10)), '20')
        self.assertEqual('{0:}'.format('a'), 'a')
        self.assertEqual('{0:.{1}}'.format('hello world', 5), 'hello')
        self.assertEqual('{0:.{1}s}'.format('hello world', 5), 'hello')
        self.assertEqual('{0:.{precision}s}'.format('hello world',
            precision=5), 'hello')
        self.assertEqual('{0:{width}.{precision}s}'.format('hello world',
            width=10, precision=5), 'hello     ')
        self.assertEqual('{0:{width}.{precision}s}'.format('hello world',
            width='10', precision='5'), 'hello     ')
        self.assertRaises(ValueError, '{'.format)
        self.assertRaises(ValueError, '}'.format)
        self.assertRaises(ValueError, 'a{'.format)
        self.assertRaises(ValueError, 'a}'.format)
        self.assertRaises(ValueError, '{a'.format)
        self.assertRaises(ValueError, '}a'.format)
        self.assertRaises(IndexError, '{0}'.format)
        self.assertRaises(IndexError, '{1}'.format, 'abc')
        self.assertRaises(KeyError, '{x}'.format)
        self.assertRaises(ValueError, '}{'.format)
        self.assertRaises(ValueError, 'abc{0:{}'.format)
        self.assertRaises(ValueError, '{0'.format)
        self.assertRaises(IndexError, '{0.}'.format)
        self.assertRaises(ValueError, '{0.}'.format, 0)
        self.assertRaises(ValueError, '{0[}'.format)
        self.assertRaises(ValueError, '{0[}'.format, [])
        self.assertRaises(KeyError, '{0]}'.format)
        self.assertRaises(ValueError, '{0.[]}'.format, 0)
        self.assertRaises(ValueError, '{0..foo}'.format, 0)
        self.assertRaises(ValueError, '{0[0}'.format, 0)
        self.assertRaises(ValueError, '{0[0:foo}'.format, 0)
        self.assertRaises(KeyError, '{c]}'.format)
        self.assertRaises(ValueError, '{{ {{{0}}'.format, 0)
        self.assertRaises(ValueError, '{0}}'.format, 0)
        self.assertRaises(KeyError, '{foo}'.format, bar=3)
        self.assertRaises(ValueError, '{0!x}'.format, 3)
        self.assertRaises(ValueError, '{0!}'.format, 0)
        self.assertRaises(ValueError, '{0!rs}'.format, 0)
        self.assertRaises(ValueError, '{!}'.format)
        self.assertRaises(IndexError, '{:}'.format)
        self.assertRaises(IndexError, '{:s}'.format)
        self.assertRaises(IndexError, '{}'.format)
        big = '23098475029384702983476098230754973209482573'
        self.assertRaises(ValueError, ('{' + big + '}').format)
        self.assertRaises(ValueError, ('{[' + big + ']}').format, [0])
        self.assertRaises(ValueError, '{0[0]x}'.format, [None])
        self.assertRaises(ValueError, '{0[0](10)}'.format, [None])
        self.assertRaises(TypeError, '{0[{1}]}'.format, 'abcdefg', 4)
        self.assertRaises(ValueError, '{0:{1:{2}}}'.format, 'abc', 's', '')
        self.assertRaises(ValueError, '{0:{1:{2:{3:{4:{5:{6}}}}}}}'.format,
            0, 1, 2, 3, 4, 5, 6, 7)
        self.assertRaises(ValueError, '{0:-s}'.format, '')
        self.assertRaises(ValueError, format, '', '-')
        self.assertRaises(ValueError, '{0:=s}'.format, '')
        self.assertRaises(ValueError, format, '', '#')
        self.assertRaises(ValueError, format, '', '#20')
        self.assertEqual('{0:s}{1:s}'.format('ABC', 'АБВ'), 'ABCАБВ')
        self.assertEqual('{0:.3s}'.format('ABCАБВ'), 'ABC')
        self.assertEqual('{0:.0s}'.format('ABCАБВ'), '')
        self.assertEqual('{[{}]}'.format({'{}': 5}), '5')
        self.assertEqual('{[{}]}'.format({'{}': 'a'}), 'a')
        self.assertEqual('{[{]}'.format({'{': 'a'}), 'a')
        self.assertEqual('{[}]}'.format({'}': 'a'}), 'a')
        self.assertEqual('{[[]}'.format({'[': 'a'}), 'a')
        self.assertEqual('{[!]}'.format({'!': 'a'}), 'a')
        self.assertRaises(ValueError, '{a{}b}'.format, 42)
        self.assertRaises(ValueError, '{a{b}'.format, 42)
        self.assertRaises(ValueError, '{[}'.format, 42)
        self.assertEqual('0x{:0{:d}X}'.format(0, 16), '0x0000000000000000')
        m = M('data')
        self.assertEqual('{!r}'.format(m), 'M(data)')
        self.assertRaises(TypeError, '{!s}'.format, m)
        self.assertRaises(TypeError, '{}'.format, m)
        n = N('data')
        self.assertEqual('{!r}'.format(n), 'N(data)')
        self.assertEqual('{!s}'.format(n), 'N(data)')
        self.assertRaises(TypeError, '{}'.format, n)

    def test_format_map(self):
        self.assertEqual(''.format_map({}), '')
        self.assertEqual('a'.format_map({}), 'a')
        self.assertEqual('ab'.format_map({}), 'ab')
        self.assertEqual('a{{'.format_map({}), 'a{')
        self.assertEqual('a}}'.format_map({}), 'a}')
        self.assertEqual('{{b'.format_map({}), '{b')
        self.assertEqual('}}b'.format_map({}), '}b')
        self.assertEqual('a{{b'.format_map({}), 'a{b')


        class Mapping(dict):

            def __missing__(self, key):
                return key
        self.assertEqual('{hello}'.format_map(Mapping()), 'hello')
        self.assertEqual('{a} {world}'.format_map(Mapping(a='hello')),
            'hello world')


        class InternalMapping:

            def __init__(self):
                self.mapping = {'a': 'hello'}

            def __getitem__(self, key):
                return self.mapping[key]
        self.assertEqual('{a}'.format_map(InternalMapping()), 'hello')


        class C:

            def __init__(self, x=100):
                self._x = x

            def __format__(self, spec):
                return spec
        self.assertEqual('{foo._x}'.format_map({'foo': C(20)}), '20')
        self.assertRaises(TypeError, ''.format_map)
        self.assertRaises(TypeError, 'a'.format_map)
        self.assertRaises(ValueError, '{'.format_map, {})
        self.assertRaises(ValueError, '}'.format_map, {})
        self.assertRaises(ValueError, 'a{'.format_map, {})
        self.assertRaises(ValueError, 'a}'.format_map, {})
        self.assertRaises(ValueError, '{a'.format_map, {})
        self.assertRaises(ValueError, '}a'.format_map, {})
        self.assertRaises(ValueError, '{}'.format_map, {'a': 2})
        self.assertRaises(ValueError, '{}'.format_map, 'a')
        self.assertRaises(ValueError, '{a} {}'.format_map, {'a': 2, 'b': 1})

    def test_format_huge_precision(self):
        format_string = '.{}f'.format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format(2.34, format_string)

    def test_format_huge_width(self):
        format_string = '{}f'.format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format(2.34, format_string)

    def test_format_huge_item_number(self):
        format_string = '{{{}:.6f}}'.format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format_string.format(2.34)

    def test_format_auto_numbering(self):


        class C:

            def __init__(self, x=100):
                self._x = x

            def __format__(self, spec):
                return spec
        self.assertEqual('{}'.format(10), '10')
        self.assertEqual('{:5}'.format('s'), 's    ')
        self.assertEqual('{!r}'.format('s'), "'s'")
        self.assertEqual('{._x}'.format(C(10)), '10')
        self.assertEqual('{[1]}'.format([1, 2]), '2')
        self.assertEqual('{[a]}'.format({'a': 4, 'b': 2}), '4')
        self.assertEqual('a{}b{}c'.format(0, 1), 'a0b1c')
        self.assertEqual('a{:{}}b'.format('x', '^10'), 'a    x     b')
        self.assertEqual('a{:{}x}b'.format(20, '#'), 'a0x14b')
        self.assertRaises(ValueError, '{}{1}'.format, 1, 2)
        self.assertRaises(ValueError, '{1}{}'.format, 1, 2)
        self.assertRaises(ValueError, '{:{1}}'.format, 1, 2)
        self.assertRaises(ValueError, '{0:{}}'.format, 1, 2)
        self.assertEqual('{f}{}'.format(4, f='test'), 'test4')
        self.assertEqual('{}{f}'.format(4, f='test'), '4test')
        self.assertEqual('{:{f}}{g}{}'.format(1, 3, g='g', f=2), ' 1g3')
        self.assertEqual('{f:{}}{}{g}'.format(2, 4, f=1, g='g'), ' 14g')

    def test_formatting(self):
        string_tests.MixinStrUnicodeUserStringTest.test_formatting(self)
        self.assertEqual('%s, %s' % ('abc', 'abc'), 'abc, abc')
        self.assertEqual('%s, %s, %i, %f, %5.2f' % ('abc', 'abc', 1, 2, 3),
            'abc, abc, 1, 2.000000,  3.00')
        self.assertEqual('%s, %s, %i, %f, %5.2f' % ('abc', 'abc', 1, -2, 3),
            'abc, abc, 1, -2.000000,  3.00')
        self.assertEqual('%s, %s, %i, %f, %5.2f' % ('abc', 'abc', -1, -2, 
            3.5), 'abc, abc, -1, -2.000000,  3.50')
        self.assertEqual('%s, %s, %i, %f, %5.2f' % ('abc', 'abc', -1, -2, 
            3.57), 'abc, abc, -1, -2.000000,  3.57')
        self.assertEqual('%s, %s, %i, %f, %5.2f' % ('abc', 'abc', -1, -2, 
            1003.57), 'abc, abc, -1, -2.000000, 1003.57')
        if not sys.platform.startswith('java'):
            self.assertEqual('%r, %r' % (b'abc', 'abc'), "b'abc', 'abc'")
            self.assertEqual('%r' % ('ሴ',), "'ሴ'")
            self.assertEqual('%a' % ('ሴ',), "'\\u1234'")
        self.assertEqual('%(x)s, %(y)s' % {'x': 'abc', 'y': 'def'}, 'abc, def')
        self.assertEqual('%(x)s, %(ü)s' % {'x': 'abc', 'ü': 'def'}, 'abc, def')
        self.assertEqual('%c' % 4660, 'ሴ')
        self.assertEqual('%c' % 136323, '𡒃')
        self.assertRaises(OverflowError, '%c'.__mod__, (1114112,))
        self.assertEqual('%c' % '𡒃', '𡒃')
        self.assertRaises(TypeError, '%c'.__mod__, 'aa')
        self.assertRaises(ValueError, '%.1ဲf'.__mod__, 1.0 / 3)
        self.assertRaises(TypeError, '%i'.__mod__, 'aa')
        self.assertEqual('...%(foo)s...' % {'foo': 'abc'}, '...abc...')
        self.assertEqual('...%(foo)s...' % {'foo': 'abc'}, '...abc...')
        self.assertEqual('...%(foo)s...' % {'foo': 'abc'}, '...abc...')
        self.assertEqual('...%(foo)s...' % {'foo': 'abc'}, '...abc...')
        self.assertEqual('...%(foo)s...' % {'foo': 'abc', 'def': 123},
            '...abc...')
        self.assertEqual('...%(foo)s...' % {'foo': 'abc', 'def': 123},
            '...abc...')
        self.assertEqual('...%s...%s...%s...%s...' % (1, 2, 3, 'abc'),
            '...1...2...3...abc...')
        self.assertEqual('...%%...%%s...%s...%s...%s...%s...' % (1, 2, 3,
            'abc'), '...%...%s...1...2...3...abc...')
        self.assertEqual('...%s...' % 'abc', '...abc...')
        self.assertEqual('%*s' % (5, 'abc'), '  abc')
        self.assertEqual('%*s' % (-5, 'abc'), 'abc  ')
        self.assertEqual('%*.*s' % (5, 2, 'abc'), '   ab')
        self.assertEqual('%*.*s' % (5, 3, 'abc'), '  abc')
        self.assertEqual('%i %*.*s' % (10, 5, 3, 'abc'), '10   abc')
        self.assertEqual('%i%s %*.*s' % (10, 3, 5, 3, 'abc'), '103   abc')
        self.assertEqual('%c' % 'a', 'a')


        class Wrapper:

            def __str__(self):
                return 'ሴ'
        self.assertEqual('%s' % Wrapper(), 'ሴ')
        NAN = float('nan')
        INF = float('inf')
        self.assertEqual('%f' % NAN, 'nan')
        self.assertEqual('%F' % NAN, 'NAN')
        self.assertEqual('%f' % INF, 'inf')
        self.assertEqual('%F' % INF, 'INF')
        self.assertEqual('%.1s' % 'aé€', 'a')
        self.assertEqual('%.2s' % 'aé€', 'aé')


        class PseudoInt:

            def __init__(self, value):
                self.value = int(value)

            def __int__(self):
                return self.value

            def __index__(self):
                return self.value


        class PseudoFloat:

            def __init__(self, value):
                self.value = float(value)

            def __int__(self):
                return int(self.value)
        pi = PseudoFloat(3.1415)
        letter_m = PseudoInt(109)
        self.assertEqual('%x' % 42, '2a')
        self.assertEqual('%X' % 15, 'F')
        self.assertEqual('%o' % 9, '11')
        self.assertEqual('%c' % 109, 'm')
        self.assertEqual('%x' % letter_m, '6d')
        self.assertEqual('%X' % letter_m, '6D')
        self.assertEqual('%o' % letter_m, '155')
        self.assertEqual('%c' % letter_m, 'm')
        self.assertRaisesRegex(TypeError,
            '%x format: an integer is required, not float', operator.mod,
            '%x', 3.14),
        self.assertRaisesRegex(TypeError,
            '%X format: an integer is required, not float', operator.mod,
            '%X', 2.11),
        self.assertRaisesRegex(TypeError,
            '%o format: an integer is required, not float', operator.mod,
            '%o', 1.79),
        self.assertRaisesRegex(TypeError,
            '%x format: an integer is required, not PseudoFloat', operator.
            mod, '%x', pi),
        self.assertRaises(TypeError, operator.mod, '%c', pi),

    def test_formatting_with_enum(self):
        import enum


        class Float(float, enum.Enum):
            PI = 3.1415926


        class Int(enum.IntEnum):
            IDES = 15


        class Str(str, enum.Enum):
            ABC = 'abc'
        self.assertEqual('%s, %s' % (Str.ABC, Str.ABC), 'Str.ABC, Str.ABC')
        self.assertEqual('%s, %s, %d, %i, %u, %f, %5.2f' % (Str.ABC, Str.
            ABC, Int.IDES, Int.IDES, Int.IDES, Float.PI, Float.PI),
            'Str.ABC, Str.ABC, 15, 15, 15, 3.141593,  3.14')
        self.assertEqual('...%(foo)s...' % {'foo': Str.ABC}, '...Str.ABC...')
        self.assertEqual('...%(foo)s...' % {'foo': Int.IDES}, '...Int.IDES...')
        self.assertEqual('...%(foo)i...' % {'foo': Int.IDES}, '...15...')
        self.assertEqual('...%(foo)d...' % {'foo': Int.IDES}, '...15...')
        self.assertEqual('...%(foo)u...' % {'foo': Int.IDES, 'def': Float.
            PI}, '...15...')
        self.assertEqual('...%(foo)f...' % {'foo': Float.PI, 'def': 123},
            '...3.141593...')

    def test_formatting_huge_precision(self):
        format_string = '%.{}f'.format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format_string % 2.34

    def test_issue28598_strsubclass_rhs(self):


        class SubclassedStr(str):

            def __rmod__(self, other):
                return 'Success, self.__rmod__({!r}) was called'.format(other)
        self.assertEqual('lhs %% %r' % SubclassedStr('rhs'),
            "Success, self.__rmod__('lhs %% %r') was called")

    @support.cpython_only
    def test_formatting_huge_precision_c_limits(self):
        from _testcapi import INT_MAX
        format_string = '%.{}f'.format(INT_MAX + 1)
        with self.assertRaises(ValueError):
            result = format_string % 2.34

    def test_formatting_huge_width(self):
        format_string = '%{}f'.format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format_string % 2.34

    def test_startswith_endswith_errors(self):
        for meth in ('foo'.startswith, 'foo'.endswith):
            with self.assertRaises(TypeError) as cm:
                meth(['f'])
            exc = str(cm.exception)
            self.assertIn('str', exc)
            self.assertIn('tuple', exc)

    @support.run_with_locale('LC_ALL', 'de_DE', 'fr_FR')
    def test_format_float(self):
        self.assertEqual('1.0', '%.1f' % 1.0)

    def test_constructor(self):
        self.assertEqual(str('unicode remains unicode'),
            'unicode remains unicode')
        for text in ('ascii', 'é', '€', '\U0010ffff'):
            subclass = StrSubclass(text)
            self.assertEqual(str(subclass), text)
            self.assertEqual(len(subclass), len(text))
            if text == 'ascii':
                self.assertEqual(subclass.encode('ascii'), b'ascii')
                self.assertEqual(subclass.encode('utf-8'), b'ascii')
        self.assertEqual(str('strings are converted to unicode'),
            'strings are converted to unicode')


        class StringCompat:

            def __init__(self, x):
                self.x = x

            def __str__(self):
                return self.x
        self.assertEqual(str(StringCompat(
            '__str__ compatible objects are recognized')),
            '__str__ compatible objects are recognized')
        o = StringCompat('unicode(obj) is compatible to str()')
        self.assertEqual(str(o), 'unicode(obj) is compatible to str()')
        self.assertEqual(str(o), 'unicode(obj) is compatible to str()')
        for obj in (123, 123.45, 123):
            self.assertEqual(str(obj), str(str(obj)))
        if not sys.platform.startswith('java'):
            self.assertRaises(TypeError, str,
                'decoding unicode is not supported', 'utf-8', 'strict')
        self.assertEqual(str(b'strings are decoded to unicode', 'utf-8',
            'strict'), 'strings are decoded to unicode')
        if not sys.platform.startswith('java'):
            self.assertEqual(str(memoryview(
                b'character buffers are decoded to unicode'), 'utf-8',
                'strict'), 'character buffers are decoded to unicode')
        self.assertRaises(TypeError, str, 42, 42, 42)

    def test_constructor_keyword_args(self):
        """Pass various keyword argument combinations to the constructor."""
        self.assertEqual(str(object='foo'), 'foo')
        self.assertEqual(str(object=b'foo', encoding='utf-8'), 'foo')
        self.assertEqual(str(b'foo', errors='strict'), 'foo')
        self.assertEqual(str(object=b'foo', errors='strict'), 'foo')

    def test_constructor_defaults(self):
        """Check the constructor argument defaults."""
        self.assertEqual(str(), '')
        self.assertEqual(str(errors='strict'), '')
        utf8_cent = '¢'.encode('utf-8')
        self.assertEqual(str(utf8_cent, errors='strict'), '¢')
        self.assertRaises(UnicodeDecodeError, str, utf8_cent, encoding='ascii')

    def test_codecs_utf7(self):
        utfTests = [('A≢Α.', b'A+ImIDkQ.'), ('Hi Mom -☺-!',
            b'Hi Mom -+Jjo--!'), ('日本語', b'+ZeVnLIqe-'), ('Item 3 is £1.',
            b'Item 3 is +AKM-1.'), ('+', b'+-'), ('+-', b'+--'), ('+?',
            b'+-?'), ('\\?', b'+AFw?'), ('+?', b'+-?'), ('\\\\?',
            b'+AFwAXA?'), ('\\\\\\?', b'+AFwAXABc?'), ('++--', b'+-+---'),
            ('\U000abcde', b'+2m/c3g-'), ('/', b'/')]
        for x, y in utfTests:
            self.assertEqual(x.encode('utf-7'), y)
        self.assertEqual('\ud801'.encode('utf-7'), b'+2AE-')
        self.assertEqual('\ud801x'.encode('utf-7'), b'+2AE-x')
        self.assertEqual('\udc01'.encode('utf-7'), b'+3AE-')
        self.assertEqual('\udc01x'.encode('utf-7'), b'+3AE-x')
        self.assertEqual(b'+2AE-'.decode('utf-7'), '\ud801')
        self.assertEqual(b'+2AE-x'.decode('utf-7'), '\ud801x')
        self.assertEqual(b'+3AE-'.decode('utf-7'), '\udc01')
        self.assertEqual(b'+3AE-x'.decode('utf-7'), '\udc01x')
        self.assertEqual('\ud801\U000abcde'.encode('utf-7'), b'+2AHab9ze-')
        self.assertEqual(b'+2AHab9ze-'.decode('utf-7'), '\ud801\U000abcde')
        self.assertEqual(b'+\xc1'.decode('utf-7', 'ignore'), '')
        set_d = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'(),-./:?"
            )
        set_o = '!"#$%&*;<=>@[]^_`{|}'
        for c in set_d:
            self.assertEqual(c.encode('utf7'), c.encode('ascii'))
            self.assertEqual(c.encode('ascii').decode('utf7'), c)
        for c in set_o:
            self.assertEqual(c.encode('ascii').decode('utf7'), c)

    def test_codecs_utf8(self):
        self.assertEqual(''.encode('utf-8'), b'')
        self.assertEqual('€'.encode('utf-8'), b'\xe2\x82\xac')
        self.assertEqual('𐀂'.encode('utf-8'), b'\xf0\x90\x80\x82')
        self.assertEqual('𣑖'.encode('utf-8'), b'\xf0\xa3\x91\x96')
        self.assertEqual('\ud800'.encode('utf-8', 'surrogatepass'),
            b'\xed\xa0\x80')
        self.assertEqual('\udc00'.encode('utf-8', 'surrogatepass'),
            b'\xed\xb0\x80')
        self.assertEqual(('𐀂' * 10).encode('utf-8'), b'\xf0\x90\x80\x82' * 10)
        self.assertEqual(
            '正確に言うと翻訳はされていません。一部はドイツ語ですが、あとはでたらめです。実際には「Wenn ist das Nunstuck git und'
            .encode('utf-8'),
            b'\xe6\xad\xa3\xe7\xa2\xba\xe3\x81\xab\xe8\xa8\x80\xe3\x81\x86\xe3\x81\xa8\xe7\xbf\xbb\xe8\xa8\xb3\xe3\x81\xaf\xe3\x81\x95\xe3\x82\x8c\xe3\x81\xa6\xe3\x81\x84\xe3\x81\xbe\xe3\x81\x9b\xe3\x82\x93\xe3\x80\x82\xe4\xb8\x80\xe9\x83\xa8\xe3\x81\xaf\xe3\x83\x89\xe3\x82\xa4\xe3\x83\x84\xe8\xaa\x9e\xe3\x81\xa7\xe3\x81\x99\xe3\x81\x8c\xe3\x80\x81\xe3\x81\x82\xe3\x81\xa8\xe3\x81\xaf\xe3\x81\xa7\xe3\x81\x9f\xe3\x82\x89\xe3\x82\x81\xe3\x81\xa7\xe3\x81\x99\xe3\x80\x82\xe5\xae\x9f\xe9\x9a\x9b\xe3\x81\xab\xe3\x81\xaf\xe3\x80\x8cWenn ist das Nunstuck git und'
            )
        self.assertEqual(str(b'\xf0\xa3\x91\x96', 'utf-8'), '𣑖')
        self.assertEqual(str(b'\xf0\x90\x80\x82', 'utf-8'), '𐀂')
        self.assertEqual(str(b'\xe2\x82\xac', 'utf-8'), '€')

    def test_utf8_decode_valid_sequences(self):
        sequences = [(b'\x00', '\x00'), (b'a', 'a'), (b'\x7f', '\x7f'), (
            b'\xc2\x80', '\x80'), (b'\xdf\xbf', '\u07ff'), (b'\xe0\xa0\x80',
            'ࠀ'), (b'\xed\x9f\xbf', '\ud7ff'), (b'\xee\x80\x80', '\ue000'),
            (b'\xef\xbf\xbf', '\uffff'), (b'\xf0\x90\x80\x80', '𐀀'), (
            b'\xf4\x8f\xbf\xbf', '\U0010ffff')]
        for seq, res in sequences:
            self.assertEqual(seq.decode('utf-8'), res)

    def test_utf8_decode_invalid_sequences(self):
        continuation_bytes = [bytes([x]) for x in range(128, 192)]
        invalid_2B_seq_start_bytes = [bytes([x]) for x in range(192, 194)]
        invalid_4B_seq_start_bytes = [bytes([x]) for x in range(245, 248)]
        invalid_start_bytes = (continuation_bytes +
            invalid_2B_seq_start_bytes + invalid_4B_seq_start_bytes + [
            bytes([x]) for x in range(247, 256)])
        for byte in invalid_start_bytes:
            self.assertRaises(UnicodeDecodeError, byte.decode, 'utf-8')
        for sb in invalid_2B_seq_start_bytes:
            for cb in continuation_bytes:
                self.assertRaises(UnicodeDecodeError, (sb + cb).decode, 'utf-8'
                    )
        for sb in invalid_4B_seq_start_bytes:
            for cb1 in continuation_bytes[:3]:
                for cb3 in continuation_bytes[:3]:
                    self.assertRaises(UnicodeDecodeError, (sb + cb1 +
                        b'\x80' + cb3).decode, 'utf-8')
        for cb in [bytes([x]) for x in range(128, 160)]:
            self.assertRaises(UnicodeDecodeError, (b'\xe0' + cb + b'\x80').
                decode, 'utf-8')
            self.assertRaises(UnicodeDecodeError, (b'\xe0' + cb + b'\xbf').
                decode, 'utf-8')
        for cb in [bytes([x]) for x in range(160, 192)]:
            self.assertRaises(UnicodeDecodeError, (b'\xed' + cb + b'\x80').
                decode, 'utf-8')
            self.assertRaises(UnicodeDecodeError, (b'\xed' + cb + b'\xbf').
                decode, 'utf-8')
        for cb in [bytes([x]) for x in range(128, 144)]:
            self.assertRaises(UnicodeDecodeError, (b'\xf0' + cb +
                b'\x80\x80').decode, 'utf-8')
            self.assertRaises(UnicodeDecodeError, (b'\xf0' + cb +
                b'\xbf\xbf').decode, 'utf-8')
        for cb in [bytes([x]) for x in range(144, 192)]:
            self.assertRaises(UnicodeDecodeError, (b'\xf4' + cb +
                b'\x80\x80').decode, 'utf-8')
            self.assertRaises(UnicodeDecodeError, (b'\xf4' + cb +
                b'\xbf\xbf').decode, 'utf-8')

    def test_issue8271(self):
        FFFD = '�'
        sequences = [(b'\x80', FFFD), (b'\x80\x80', FFFD * 2), (b'\xc0',
            FFFD), (b'\xc0\xc0', FFFD * 2), (b'\xc1', FFFD), (b'\xc1\xc0', 
            FFFD * 2), (b'\xc0\xc1', FFFD * 2), (b'\xc2', FFFD), (
            b'\xc2\xc2', FFFD * 2), (b'\xc2\xc2\xc2', FFFD * 3), (b'\xc2A',
            FFFD + 'A'), (b'\xe1', FFFD), (b'\xe1\xe1', FFFD * 2), (
            b'\xe1\xe1\xe1', FFFD * 3), (b'\xe1\xe1\xe1\xe1', FFFD * 4), (
            b'\xe1\x80', FFFD), (b'\xe1A', FFFD + 'A'), (b'\xe1A\x80', FFFD +
            'A' + FFFD), (b'\xe1AA', FFFD + 'AA'), (b'\xe1\x80A', FFFD +
            'A'), (b'\xe1\x80\xe1A', FFFD * 2 + 'A'), (b'\xe1A\xe1\x80', 
            FFFD + 'A' + FFFD), (b'\xf1', FFFD), (b'\xf1\xf1', FFFD * 2), (
            b'\xf1\xf1\xf1', FFFD * 3), (b'\xf1\xf1\xf1\xf1', FFFD * 4), (
            b'\xf1\xf1\xf1\xf1\xf1', FFFD * 5), (b'\xf1\x80', FFFD), (
            b'\xf1\x80\x80', FFFD), (b'\xf1\x80A', FFFD + 'A'), (
            b'\xf1\x80AA', FFFD + 'AA'), (b'\xf1\x80\x80A', FFFD + 'A'), (
            b'\xf1A\x80', FFFD + 'A' + FFFD), (b'\xf1A\x80\x80', FFFD + 'A' +
            FFFD * 2), (b'\xf1A\x80A', FFFD + 'A' + FFFD + 'A'), (
            b'\xf1AA\x80', FFFD + 'AA' + FFFD), (b'\xf1A\xf1\x80', FFFD +
            'A' + FFFD), (b'\xf1A\x80\xf1', FFFD + 'A' + FFFD * 2), (
            b'\xf1\xf1\x80A', FFFD * 2 + 'A'), (b'\xf1A\xf1\xf1', FFFD +
            'A' + FFFD * 2), (b'\xf5', FFFD), (b'\xf5\xf5', FFFD * 2), (
            b'\xf5\x80', FFFD * 2), (b'\xf5\x80\x80', FFFD * 3), (
            b'\xf5\x80\x80\x80', FFFD * 4), (b'\xf5\x80A', FFFD * 2 + 'A'),
            (b'\xf5\x80A\xf5', FFFD * 2 + 'A' + FFFD), (b'\xf5A\x80\x80A', 
            FFFD + 'A' + FFFD * 2 + 'A'), (b'\xf8', FFFD), (b'\xf8\xf8', 
            FFFD * 2), (b'\xf8\x80', FFFD * 2), (b'\xf8\x80A', FFFD * 2 +
            'A'), (b'\xf8\x80\x80\x80\x80', FFFD * 5), (b'\xfc', FFFD), (
            b'\xfc\xfc', FFFD * 2), (b'\xfc\x80\x80', FFFD * 3), (
            b'\xfc\x80\x80\x80\x80\x80', FFFD * 6), (b'\xfe', FFFD), (
            b'\xfe\x80\x80', FFFD * 3), (b'\xf1\x80ABC', '�ABC'), (
            b'\xf1\x80\xffBC', '��BC'), (b'\xf1\x80\xc2\x81C', '�\x81C'), (
            b'a\xf1\x80\x80\xe1\x80\xc2b\x80c\x80\xbfd', 'a���b�c��d')]
        for n, (seq, res) in enumerate(sequences):
            self.assertRaises(UnicodeDecodeError, seq.decode, 'utf-8', 'strict'
                )
            self.assertEqual(seq.decode('utf-8', 'replace'), res)
            self.assertEqual((seq + b'b').decode('utf-8', 'replace'), res + 'b'
                )
            self.assertEqual(seq.decode('utf-8', 'ignore'), res.replace('�',
                ''))

    def to_bytestring(self, seq):
        return bytes(int(c, 16) for c in seq.split())

    def assertCorrectUTF8Decoding(self, seq, res, err):
        """
        Check that an invalid UTF-8 sequence raises a UnicodeDecodeError when
        'strict' is used, returns res when 'replace' is used, and that doesn't
        return anything when 'ignore' is used.
        """
        with self.assertRaises(UnicodeDecodeError) as cm:
            seq.decode('utf-8')
        exc = cm.exception
        self.assertIn(err, str(exc))
        self.assertEqual(seq.decode('utf-8', 'replace'), res)
        self.assertEqual((b'aaaa' + seq + b'bbbb').decode('utf-8',
            'replace'), 'aaaa' + res + 'bbbb')
        res = res.replace('�', '')
        self.assertEqual(seq.decode('utf-8', 'ignore'), res)
        self.assertEqual((b'aaaa' + seq + b'bbbb').decode('utf-8', 'ignore'
            ), 'aaaa' + res + 'bbbb')

    def test_invalid_start_byte(self):
        """
        Test that an 'invalid start byte' error is raised when the first byte
        is not in the ASCII range or is not a valid start byte of a 2-, 3-, or
        4-bytes sequence. The invalid start byte is replaced with a single
        U+FFFD when errors='replace'.
        E.g. <80> is a continuation byte and can appear only after a start byte.
        """
        FFFD = '�'
        for byte in b'\x80\xa0\x9f\xbf\xc0\xc1\xf5\xff':
            self.assertCorrectUTF8Decoding(bytes([byte]), '�',
                'invalid start byte')

    def test_unexpected_end_of_data(self):
        """
        Test that an 'unexpected end of data' error is raised when the string
        ends after a start byte of a 2-, 3-, or 4-bytes sequence without having
        enough continuation bytes.  The incomplete sequence is replaced with a
        single U+FFFD when errors='replace'.
        E.g. in the sequence <F3 80 80>, F3 is the start byte of a 4-bytes
        sequence, but it's followed by only 2 valid continuation bytes and the
        last continuation bytes is missing.
        Note: the continuation bytes must be all valid, if one of them is
        invalid another error will be raised.
        """
        sequences = ['C2', 'DF', 'E0 A0', 'E0 BF', 'E1 80', 'E1 BF',
            'EC 80', 'EC BF', 'ED 80', 'ED 9F', 'EE 80', 'EE BF', 'EF 80',
            'EF BF', 'F0 90', 'F0 BF', 'F0 90 80', 'F0 90 BF', 'F0 BF 80',
            'F0 BF BF', 'F1 80', 'F1 BF', 'F1 80 80', 'F1 80 BF',
            'F1 BF 80', 'F1 BF BF', 'F3 80', 'F3 BF', 'F3 80 80',
            'F3 80 BF', 'F3 BF 80', 'F3 BF BF', 'F4 80', 'F4 8F',
            'F4 80 80', 'F4 80 BF', 'F4 8F 80', 'F4 8F BF']
        FFFD = '�'
        for seq in sequences:
            self.assertCorrectUTF8Decoding(self.to_bytestring(seq), '�',
                'unexpected end of data')

    def test_invalid_cb_for_2bytes_seq(self):
        """
        Test that an 'invalid continuation byte' error is raised when the
        continuation byte of a 2-bytes sequence is invalid.  The start byte
        is replaced by a single U+FFFD and the second byte is handled
        separately when errors='replace'.
        E.g. in the sequence <C2 41>, C2 is the start byte of a 2-bytes
        sequence, but 41 is not a valid continuation byte because it's the
        ASCII letter 'A'.
        """
        FFFD = '�'
        FFFDx2 = FFFD * 2
        sequences = [('C2 00', FFFD + '\x00'), ('C2 7F', FFFD + '\x7f'), (
            'C2 C0', FFFDx2), ('C2 FF', FFFDx2), ('DF 00', FFFD + '\x00'),
            ('DF 7F', FFFD + '\x7f'), ('DF C0', FFFDx2), ('DF FF', FFFDx2)]
        for seq, res in sequences:
            self.assertCorrectUTF8Decoding(self.to_bytestring(seq), res,
                'invalid continuation byte')

    def test_invalid_cb_for_3bytes_seq(self):
        """
        Test that an 'invalid continuation byte' error is raised when the
        continuation byte(s) of a 3-bytes sequence are invalid.  When
        errors='replace', if the first continuation byte is valid, the first
        two bytes (start byte + 1st cb) are replaced by a single U+FFFD and the
        third byte is handled separately, otherwise only the start byte is
        replaced with a U+FFFD and the other continuation bytes are handled
        separately.
        E.g. in the sequence <E1 80 41>, E1 is the start byte of a 3-bytes
        sequence, 80 is a valid continuation byte, but 41 is not a valid cb
        because it's the ASCII letter 'A'.
        Note: when the start byte is E0 or ED, the valid ranges for the first
        continuation byte are limited to A0..BF and 80..9F respectively.
        Python 2 used to consider all the bytes in range 80..BF valid when the
        start byte was ED.  This is fixed in Python 3.
        """
        FFFD = '�'
        FFFDx2 = FFFD * 2
        sequences = [('E0 00', FFFD + '\x00'), ('E0 7F', FFFD + '\x7f'), (
            'E0 80', FFFDx2), ('E0 9F', FFFDx2), ('E0 C0', FFFDx2), (
            'E0 FF', FFFDx2), ('E0 A0 00', FFFD + '\x00'), ('E0 A0 7F', 
            FFFD + '\x7f'), ('E0 A0 C0', FFFDx2), ('E0 A0 FF', FFFDx2), (
            'E0 BF 00', FFFD + '\x00'), ('E0 BF 7F', FFFD + '\x7f'), (
            'E0 BF C0', FFFDx2), ('E0 BF FF', FFFDx2), ('E1 00', FFFD +
            '\x00'), ('E1 7F', FFFD + '\x7f'), ('E1 C0', FFFDx2), ('E1 FF',
            FFFDx2), ('E1 80 00', FFFD + '\x00'), ('E1 80 7F', FFFD +
            '\x7f'), ('E1 80 C0', FFFDx2), ('E1 80 FF', FFFDx2), (
            'E1 BF 00', FFFD + '\x00'), ('E1 BF 7F', FFFD + '\x7f'), (
            'E1 BF C0', FFFDx2), ('E1 BF FF', FFFDx2), ('EC 00', FFFD +
            '\x00'), ('EC 7F', FFFD + '\x7f'), ('EC C0', FFFDx2), ('EC FF',
            FFFDx2), ('EC 80 00', FFFD + '\x00'), ('EC 80 7F', FFFD +
            '\x7f'), ('EC 80 C0', FFFDx2), ('EC 80 FF', FFFDx2), (
            'EC BF 00', FFFD + '\x00'), ('EC BF 7F', FFFD + '\x7f'), (
            'EC BF C0', FFFDx2), ('EC BF FF', FFFDx2), ('ED 00', FFFD +
            '\x00'), ('ED 7F', FFFD + '\x7f'), ('ED A0', FFFDx2), ('ED BF',
            FFFDx2), ('ED C0', FFFDx2), ('ED FF', FFFDx2), ('ED 80 00', 
            FFFD + '\x00'), ('ED 80 7F', FFFD + '\x7f'), ('ED 80 C0',
            FFFDx2), ('ED 80 FF', FFFDx2), ('ED 9F 00', FFFD + '\x00'), (
            'ED 9F 7F', FFFD + '\x7f'), ('ED 9F C0', FFFDx2), ('ED 9F FF',
            FFFDx2), ('EE 00', FFFD + '\x00'), ('EE 7F', FFFD + '\x7f'), (
            'EE C0', FFFDx2), ('EE FF', FFFDx2), ('EE 80 00', FFFD + '\x00'
            ), ('EE 80 7F', FFFD + '\x7f'), ('EE 80 C0', FFFDx2), (
            'EE 80 FF', FFFDx2), ('EE BF 00', FFFD + '\x00'), ('EE BF 7F', 
            FFFD + '\x7f'), ('EE BF C0', FFFDx2), ('EE BF FF', FFFDx2), (
            'EF 00', FFFD + '\x00'), ('EF 7F', FFFD + '\x7f'), ('EF C0',
            FFFDx2), ('EF FF', FFFDx2), ('EF 80 00', FFFD + '\x00'), (
            'EF 80 7F', FFFD + '\x7f'), ('EF 80 C0', FFFDx2), ('EF 80 FF',
            FFFDx2), ('EF BF 00', FFFD + '\x00'), ('EF BF 7F', FFFD +
            '\x7f'), ('EF BF C0', FFFDx2), ('EF BF FF', FFFDx2)]
        for seq, res in sequences:
            self.assertCorrectUTF8Decoding(self.to_bytestring(seq), res,
                'invalid continuation byte')

    def test_invalid_cb_for_4bytes_seq(self):
        """
        Test that an 'invalid continuation byte' error is raised when the
        continuation byte(s) of a 4-bytes sequence are invalid.  When
        errors='replace',the start byte and all the following valid
        continuation bytes are replaced with a single U+FFFD, and all the bytes
        starting from the first invalid continuation bytes (included) are
        handled separately.
        E.g. in the sequence <E1 80 41>, E1 is the start byte of a 3-bytes
        sequence, 80 is a valid continuation byte, but 41 is not a valid cb
        because it's the ASCII letter 'A'.
        Note: when the start byte is E0 or ED, the valid ranges for the first
        continuation byte are limited to A0..BF and 80..9F respectively.
        However, when the start byte is ED, Python 2 considers all the bytes
        in range 80..BF valid.  This is fixed in Python 3.
        """
        FFFD = '�'
        FFFDx2 = FFFD * 2
        sequences = [('F0 00', FFFD + '\x00'), ('F0 7F', FFFD + '\x7f'), (
            'F0 80', FFFDx2), ('F0 8F', FFFDx2), ('F0 C0', FFFDx2), (
            'F0 FF', FFFDx2), ('F0 90 00', FFFD + '\x00'), ('F0 90 7F', 
            FFFD + '\x7f'), ('F0 90 C0', FFFDx2), ('F0 90 FF', FFFDx2), (
            'F0 BF 00', FFFD + '\x00'), ('F0 BF 7F', FFFD + '\x7f'), (
            'F0 BF C0', FFFDx2), ('F0 BF FF', FFFDx2), ('F0 90 80 00', FFFD +
            '\x00'), ('F0 90 80 7F', FFFD + '\x7f'), ('F0 90 80 C0', FFFDx2
            ), ('F0 90 80 FF', FFFDx2), ('F0 90 BF 00', FFFD + '\x00'), (
            'F0 90 BF 7F', FFFD + '\x7f'), ('F0 90 BF C0', FFFDx2), (
            'F0 90 BF FF', FFFDx2), ('F0 BF 80 00', FFFD + '\x00'), (
            'F0 BF 80 7F', FFFD + '\x7f'), ('F0 BF 80 C0', FFFDx2), (
            'F0 BF 80 FF', FFFDx2), ('F0 BF BF 00', FFFD + '\x00'), (
            'F0 BF BF 7F', FFFD + '\x7f'), ('F0 BF BF C0', FFFDx2), (
            'F0 BF BF FF', FFFDx2), ('F1 00', FFFD + '\x00'), ('F1 7F', 
            FFFD + '\x7f'), ('F1 C0', FFFDx2), ('F1 FF', FFFDx2), (
            'F1 80 00', FFFD + '\x00'), ('F1 80 7F', FFFD + '\x7f'), (
            'F1 80 C0', FFFDx2), ('F1 80 FF', FFFDx2), ('F1 BF 00', FFFD +
            '\x00'), ('F1 BF 7F', FFFD + '\x7f'), ('F1 BF C0', FFFDx2), (
            'F1 BF FF', FFFDx2), ('F1 80 80 00', FFFD + '\x00'), (
            'F1 80 80 7F', FFFD + '\x7f'), ('F1 80 80 C0', FFFDx2), (
            'F1 80 80 FF', FFFDx2), ('F1 80 BF 00', FFFD + '\x00'), (
            'F1 80 BF 7F', FFFD + '\x7f'), ('F1 80 BF C0', FFFDx2), (
            'F1 80 BF FF', FFFDx2), ('F1 BF 80 00', FFFD + '\x00'), (
            'F1 BF 80 7F', FFFD + '\x7f'), ('F1 BF 80 C0', FFFDx2), (
            'F1 BF 80 FF', FFFDx2), ('F1 BF BF 00', FFFD + '\x00'), (
            'F1 BF BF 7F', FFFD + '\x7f'), ('F1 BF BF C0', FFFDx2), (
            'F1 BF BF FF', FFFDx2), ('F3 00', FFFD + '\x00'), ('F3 7F', 
            FFFD + '\x7f'), ('F3 C0', FFFDx2), ('F3 FF', FFFDx2), (
            'F3 80 00', FFFD + '\x00'), ('F3 80 7F', FFFD + '\x7f'), (
            'F3 80 C0', FFFDx2), ('F3 80 FF', FFFDx2), ('F3 BF 00', FFFD +
            '\x00'), ('F3 BF 7F', FFFD + '\x7f'), ('F3 BF C0', FFFDx2), (
            'F3 BF FF', FFFDx2), ('F3 80 80 00', FFFD + '\x00'), (
            'F3 80 80 7F', FFFD + '\x7f'), ('F3 80 80 C0', FFFDx2), (
            'F3 80 80 FF', FFFDx2), ('F3 80 BF 00', FFFD + '\x00'), (
            'F3 80 BF 7F', FFFD + '\x7f'), ('F3 80 BF C0', FFFDx2), (
            'F3 80 BF FF', FFFDx2), ('F3 BF 80 00', FFFD + '\x00'), (
            'F3 BF 80 7F', FFFD + '\x7f'), ('F3 BF 80 C0', FFFDx2), (
            'F3 BF 80 FF', FFFDx2), ('F3 BF BF 00', FFFD + '\x00'), (
            'F3 BF BF 7F', FFFD + '\x7f'), ('F3 BF BF C0', FFFDx2), (
            'F3 BF BF FF', FFFDx2), ('F4 00', FFFD + '\x00'), ('F4 7F', 
            FFFD + '\x7f'), ('F4 90', FFFDx2), ('F4 BF', FFFDx2), ('F4 C0',
            FFFDx2), ('F4 FF', FFFDx2), ('F4 80 00', FFFD + '\x00'), (
            'F4 80 7F', FFFD + '\x7f'), ('F4 80 C0', FFFDx2), ('F4 80 FF',
            FFFDx2), ('F4 8F 00', FFFD + '\x00'), ('F4 8F 7F', FFFD +
            '\x7f'), ('F4 8F C0', FFFDx2), ('F4 8F FF', FFFDx2), (
            'F4 80 80 00', FFFD + '\x00'), ('F4 80 80 7F', FFFD + '\x7f'),
            ('F4 80 80 C0', FFFDx2), ('F4 80 80 FF', FFFDx2), (
            'F4 80 BF 00', FFFD + '\x00'), ('F4 80 BF 7F', FFFD + '\x7f'),
            ('F4 80 BF C0', FFFDx2), ('F4 80 BF FF', FFFDx2), (
            'F4 8F 80 00', FFFD + '\x00'), ('F4 8F 80 7F', FFFD + '\x7f'),
            ('F4 8F 80 C0', FFFDx2), ('F4 8F 80 FF', FFFDx2), (
            'F4 8F BF 00', FFFD + '\x00'), ('F4 8F BF 7F', FFFD + '\x7f'),
            ('F4 8F BF C0', FFFDx2), ('F4 8F BF FF', FFFDx2)]
        for seq, res in sequences:
            self.assertCorrectUTF8Decoding(self.to_bytestring(seq), res,
                'invalid continuation byte')

    def test_codecs_idna(self):
        self.assertEqual('www.python.org.'.encode('idna'), b'www.python.org.')

    def test_codecs_errors(self):
        self.assertRaises(UnicodeError, 'Andr\x82 x'.encode, 'ascii')
        self.assertRaises(UnicodeError, 'Andr\x82 x'.encode, 'ascii', 'strict')
        self.assertEqual('Andr\x82 x'.encode('ascii', 'ignore'), b'Andr x')
        self.assertEqual('Andr\x82 x'.encode('ascii', 'replace'), b'Andr? x')
        self.assertEqual('Andr\x82 x'.encode('ascii', 'replace'),
            'Andr\x82 x'.encode('ascii', errors='replace'))
        self.assertEqual('Andr\x82 x'.encode('ascii', 'ignore'),
            'Andr\x82 x'.encode(encoding='ascii', errors='ignore'))
        self.assertRaises(UnicodeError, str, b'Andr\x82 x', 'ascii')
        self.assertRaises(UnicodeError, str, b'Andr\x82 x', 'ascii', 'strict')
        self.assertEqual(str(b'Andr\x82 x', 'ascii', 'ignore'), 'Andr x')
        self.assertEqual(str(b'Andr\x82 x', 'ascii', 'replace'), 'Andr� x')
        self.assertEqual(str(b'\x82 x', 'ascii', 'replace'), '� x')
        self.assertEqual(b'\\N{foo}xx'.decode('unicode-escape', 'ignore'), 'xx'
            )
        self.assertRaises(UnicodeError, b'\\'.decode, 'unicode-escape')
        self.assertRaises(TypeError, b'hello'.decode, 'test.unicode1')
        self.assertRaises(TypeError, str, b'hello', 'test.unicode2')
        self.assertRaises(TypeError, 'hello'.encode, 'test.unicode1')
        self.assertRaises(TypeError, 'hello'.encode, 'test.unicode2')
        self.assertRaises(TypeError, 'hello'.encode, 42, 42, 42)
        self.assertRaises(UnicodeError, float, '\ud800')
        self.assertRaises(UnicodeError, float, '\udf00')
        self.assertRaises(UnicodeError, complex, '\ud800')
        self.assertRaises(UnicodeError, complex, '\udf00')

    def test_codecs(self):
        self.assertEqual('hello'.encode('ascii'), b'hello')
        self.assertEqual('hello'.encode('utf-7'), b'hello')
        self.assertEqual('hello'.encode('utf-8'), b'hello')
        self.assertEqual('hello'.encode('utf-8'), b'hello')
        self.assertEqual('hello'.encode('utf-16-le'),
            b'h\x00e\x00l\x00l\x00o\x00')
        self.assertEqual('hello'.encode('utf-16-be'),
            b'\x00h\x00e\x00l\x00l\x00o')
        self.assertEqual('hello'.encode('latin-1'), b'hello')
        self.assertEqual('☃'.encode(), b'\xe2\x98\x83')
        for c in range(1024):
            u = chr(c)
            for encoding in ('utf-7', 'utf-8', 'utf-16', 'utf-16-le',
                'utf-16-be', 'raw_unicode_escape', 'unicode_escape',
                'unicode_internal'):
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', DeprecationWarning)
                    self.assertEqual(str(u.encode(encoding), encoding), u)
        for c in range(256):
            u = chr(c)
            for encoding in ('latin-1',):
                self.assertEqual(str(u.encode(encoding), encoding), u)
        for c in range(128):
            u = chr(c)
            for encoding in ('ascii',):
                self.assertEqual(str(u.encode(encoding), encoding), u)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            u = '𐀁𠀂\U00030003\U00040004\U00050005'
            for encoding in ('utf-8', 'utf-16', 'utf-16-le', 'utf-16-be',
                'raw_unicode_escape', 'unicode_escape', 'unicode_internal'):
                self.assertEqual(str(u.encode(encoding), encoding), u)
        u = ''.join(map(chr, list(range(0, 55296)) + list(range(57344, 
            1114112))))
        for encoding in ('utf-8',):
            self.assertEqual(str(u.encode(encoding), encoding), u)

    def test_codecs_charmap(self):
        s = bytes(range(128))
        for encoding in ('cp037', 'cp1026', 'cp273', 'cp437', 'cp500',
            'cp720', 'cp737', 'cp775', 'cp850', 'cp852', 'cp855', 'cp858',
            'cp860', 'cp861', 'cp862', 'cp863', 'cp865', 'cp866', 'cp1125',
            'iso8859_10', 'iso8859_13', 'iso8859_14', 'iso8859_15',
            'iso8859_2', 'iso8859_3', 'iso8859_4', 'iso8859_5', 'iso8859_6',
            'iso8859_7', 'iso8859_9', 'koi8_r', 'koi8_t', 'koi8_u',
            'kz1048', 'latin_1', 'mac_cyrillic', 'mac_latin2', 'cp1250',
            'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256',
            'cp1257', 'cp1258', 'cp856', 'cp857', 'cp864', 'cp869', 'cp874',
            'mac_greek', 'mac_iceland', 'mac_roman', 'mac_turkish',
            'cp1006', 'iso8859_8'):
            self.assertEqual(str(s, encoding).encode(encoding), s)
        s = bytes(range(128, 256))
        for encoding in ('cp037', 'cp1026', 'cp273', 'cp437', 'cp500',
            'cp720', 'cp737', 'cp775', 'cp850', 'cp852', 'cp855', 'cp858',
            'cp860', 'cp861', 'cp862', 'cp863', 'cp865', 'cp866', 'cp1125',
            'iso8859_10', 'iso8859_13', 'iso8859_14', 'iso8859_15',
            'iso8859_2', 'iso8859_4', 'iso8859_5', 'iso8859_9', 'koi8_r',
            'koi8_u', 'latin_1', 'mac_cyrillic', 'mac_latin2'):
            self.assertEqual(str(s, encoding).encode(encoding), s)

    def test_concatenation(self):
        self.assertEqual('abcdef', 'abcdef')
        self.assertEqual('abcdef', 'abcdef')
        self.assertEqual('abcdef', 'abcdef')
        self.assertEqual('abcdefghi', 'abcdefghi')
        self.assertEqual('abcdefghi', 'abcdefghi')

    def test_printing(self):


        class BitBucket:

            def write(self, text):
                pass
        out = BitBucket()
        print('abc', file=out)
        print('abc', 'def', file=out)
        print('abc', 'def', file=out)
        print('abc', 'def', file=out)
        print('abc\n', file=out)
        print('abc\n', end=' ', file=out)
        print('abc\n', end=' ', file=out)
        print('def\n', file=out)
        print('def\n', file=out)

    def test_ucs4(self):
        x = '\U00100000'
        y = x.encode('raw-unicode-escape').decode('raw-unicode-escape')
        self.assertEqual(x, y)
        y = b'\\U00100000'
        x = y.decode('raw-unicode-escape').encode('raw-unicode-escape')
        self.assertEqual(x, y)
        y = b'\\U00010000'
        x = y.decode('raw-unicode-escape').encode('raw-unicode-escape')
        self.assertEqual(x, y)
        try:
            b'\\U11111111'.decode('raw-unicode-escape')
        except UnicodeDecodeError as e:
            self.assertEqual(e.start, 0)
            self.assertEqual(e.end, 10)
        else:
            self.fail('Should have raised UnicodeDecodeError')

    def test_conversion(self):


        class ObjectToStr:

            def __str__(self):
                return 'foo'


        class StrSubclassToStr(str):

            def __str__(self):
                return 'foo'


        class StrSubclassToStrSubclass(str):

            def __new__(cls, content=''):
                return str.__new__(cls, 2 * content)

            def __str__(self):
                return self
        self.assertEqual(str(ObjectToStr()), 'foo')
        self.assertEqual(str(StrSubclassToStr('bar')), 'foo')
        s = str(StrSubclassToStrSubclass('foo'))
        self.assertEqual(s, 'foofoo')
        self.assertIs(type(s), StrSubclassToStrSubclass)
        s = StrSubclass(StrSubclassToStrSubclass('foo'))
        self.assertEqual(s, 'foofoo')
        self.assertIs(type(s), StrSubclass)

    def test_unicode_repr(self):


        class s1:

            def __repr__(self):
                return '\\n'


        class s2:

            def __repr__(self):
                return '\\n'
        self.assertEqual(repr(s1()), '\\n')
        self.assertEqual(repr(s2()), '\\n')

    def test_printable_repr(self):
        self.assertEqual(repr('𐀀'), "'%c'" % (65536,))
        self.assertEqual(repr('\U00014000'), "'\\U00014000'")

    @unittest.skipIf(sys.maxsize > 1 << 32 or struct.calcsize('P') != 4,
        'only applies to 32-bit platforms')
    def test_expandtabs_overflows_gracefully(self):
        self.assertRaises(OverflowError, 't\tt\t'.expandtabs, sys.maxsize)

    @support.cpython_only
    def test_expandtabs_optimization(self):
        s = 'abc'
        self.assertIs(s.expandtabs(), s)

    def test_raiseMemError(self):
        if struct.calcsize('P') == 8:
            ascii_struct_size = 48
            compact_struct_size = 72
        else:
            ascii_struct_size = 24
            compact_struct_size = 36
        for char in ('a', 'é', '€', '\U0010ffff'):
            code = ord(char)
            if code < 256:
                char_size = 1
                struct_size = ascii_struct_size
            elif code < 65536:
                char_size = 2
                struct_size = compact_struct_size
            else:
                char_size = 4
                struct_size = compact_struct_size
            maxlen = (sys.maxsize - struct_size) // char_size
            alloc = lambda : char * maxlen
            self.assertRaises(MemoryError, alloc)
            self.assertRaises(MemoryError, alloc)

    def test_format_subclass(self):


        class S(str):

            def __str__(self):
                return '__str__ overridden'
        s = S('xxx')
        self.assertEqual('%s' % s, '__str__ overridden')
        self.assertEqual('{}'.format(s), '__str__ overridden')

    def test_subclass_add(self):


        class S(str):

            def __add__(self, o):
                return '3'
        self.assertEqual(S('4') + S('5'), '3')


        class S(str):

            def __iadd__(self, o):
                return '3'
        s = S('1')
        s += '4'
        self.assertEqual(s, '3')

    def test_getnewargs(self):
        text = 'abc'
        args = text.__getnewargs__()
        self.assertIsNot(args[0], text)
        self.assertEqual(args[0], text)
        self.assertEqual(len(args), 1)

    def test_resize(self):
        for length in range(1, 100, 7):
            text = 'a' * length + 'b'
            with support.check_warnings((
                'unicode_internal codec has been deprecated',
                DeprecationWarning)):
                abc = text.encode('unicode_internal')
                self.assertEqual(abc.decode('unicode_internal'), text)
                text += 'c'
                abcdef = text.encode('unicode_internal')
                self.assertNotEqual(abc, abcdef)
                self.assertEqual(abcdef.decode('unicode_internal'), text)

    def test_compare(self):
        N = 10
        ascii = 'a' * N
        ascii2 = 'z' * N
        latin = '\x80' * N
        latin2 = 'ÿ' * N
        bmp = 'Ā' * N
        bmp2 = '\uffff' * N
        astral = '\U00100000' * N
        astral2 = '\U0010ffff' * N
        strings = ascii, ascii2, latin, latin2, bmp, bmp2, astral, astral2
        for text1, text2 in itertools.combinations(strings, 2):
            equal = text1 is text2
            self.assertEqual(text1 == text2, equal)
            self.assertEqual(text1 != text2, not equal)
            if equal:
                self.assertTrue(text1 <= text2)
                self.assertTrue(text1 >= text2)
                copy1 = duplicate_string(text1)
                copy2 = duplicate_string(text2)
                self.assertIsNot(copy1, copy2)
                self.assertTrue(copy1 == copy2)
                self.assertFalse(copy1 != copy2)
                self.assertTrue(copy1 <= copy2)
                self.assertTrue(copy2 >= copy2)
        self.assertTrue(ascii < ascii2)
        self.assertTrue(ascii < latin)
        self.assertTrue(ascii < bmp)
        self.assertTrue(ascii < astral)
        self.assertFalse(ascii >= ascii2)
        self.assertFalse(ascii >= latin)
        self.assertFalse(ascii >= bmp)
        self.assertFalse(ascii >= astral)
        self.assertFalse(latin < ascii)
        self.assertTrue(latin < latin2)
        self.assertTrue(latin < bmp)
        self.assertTrue(latin < astral)
        self.assertTrue(latin >= ascii)
        self.assertFalse(latin >= latin2)
        self.assertFalse(latin >= bmp)
        self.assertFalse(latin >= astral)
        self.assertFalse(bmp < ascii)
        self.assertFalse(bmp < latin)
        self.assertTrue(bmp < bmp2)
        self.assertTrue(bmp < astral)
        self.assertTrue(bmp >= ascii)
        self.assertTrue(bmp >= latin)
        self.assertFalse(bmp >= bmp2)
        self.assertFalse(bmp >= astral)
        self.assertFalse(astral < ascii)
        self.assertFalse(astral < latin)
        self.assertFalse(astral < bmp2)
        self.assertTrue(astral < astral2)
        self.assertTrue(astral >= ascii)
        self.assertTrue(astral >= latin)
        self.assertTrue(astral >= bmp2)
        self.assertFalse(astral >= astral2)

    def test_free_after_iterating(self):
        support.check_free_after_iterating(self, iter, str)
        support.check_free_after_iterating(self, reversed, str)


class CAPITest(unittest.TestCase):

    def test_from_format(self):
        support.import_module('ctypes')
        from ctypes import pythonapi, py_object, sizeof, c_int, c_long, c_longlong, c_ssize_t, c_uint, c_ulong, c_ulonglong, c_size_t, c_void_p
        name = 'PyUnicode_FromFormat'
        _PyUnicode_FromFormat = getattr(pythonapi, name)
        _PyUnicode_FromFormat.restype = py_object

        def PyUnicode_FromFormat(format, *args):
            cargs = tuple(py_object(arg) if isinstance(arg, str) else arg for
                arg in args)
            return _PyUnicode_FromFormat(format, *cargs)

        def check_format(expected, format, *args):
            text = PyUnicode_FromFormat(format, *args)
            self.assertEqual(expected, text)
        check_format('ascii\x7f=unicodeé', b'ascii\x7f=%U', 'unicodeé')
        self.assertRaisesRegex(ValueError,
            '^PyUnicode_FromFormatV\\(\\) expects an ASCII-encoded format string, got a non-ASCII byte: 0xe9$'
            , PyUnicode_FromFormat, b'unicode\xe9=%s', 'ascii')
        check_format('ꯍ', b'%c', c_int(43981))
        check_format('\U0010ffff', b'%c', c_int(1114111))
        with self.assertRaises(OverflowError):
            PyUnicode_FromFormat(b'%c', c_int(1114112))
        check_format('𐀀\U00100000', b'%c%c', c_int(65536), c_int(1048576))
        check_format('%', b'%')
        check_format('%', b'%%')
        check_format('%s', b'%%s')
        check_format('[%]', b'[%%]')
        check_format('%abc', b'%%%s', b'abc')
        check_format('abc', b'%.3s', b'abcdef')
        check_format('abc[�', b'%.5s', 'abc[€]'.encode('utf8'))
        check_format("'\\u20acABC'", b'%A', '€ABC')
        check_format("'\\u20", b'%.5A', '€ABCDEF')
        check_format("'€ABC'", b'%R', '€ABC')
        check_format("'€A", b'%.3R', '€ABCDEF')
        check_format('€AB', b'%.3S', '€ABCDEF')
        check_format('€AB', b'%.3U', '€ABCDEF')
        check_format('€AB', b'%.3V', '€ABCDEF', None)
        check_format('abc[�', b'%.5V', None, 'abc[€]'.encode('utf8'))
        check_format('repr=  abc', b'repr=%5S', 'abc')
        check_format('repr=ab', b'repr=%.2S', 'abc')
        check_format('repr=   ab', b'repr=%5.2S', 'abc')
        check_format("repr=   'abc'", b'repr=%8R', 'abc')
        check_format("repr='ab", b'repr=%.3R', 'abc')
        check_format("repr=  'ab", b'repr=%5.3R', 'abc')
        check_format("repr=   'abc'", b'repr=%8A', 'abc')
        check_format("repr='ab", b'repr=%.3A', 'abc')
        check_format("repr=  'ab", b'repr=%5.3A', 'abc')
        check_format('repr=  abc', b'repr=%5s', b'abc')
        check_format('repr=ab', b'repr=%.2s', b'abc')
        check_format('repr=   ab', b'repr=%5.2s', b'abc')
        check_format('repr=  abc', b'repr=%5U', 'abc')
        check_format('repr=ab', b'repr=%.2U', 'abc')
        check_format('repr=   ab', b'repr=%5.2U', 'abc')
        check_format('repr=  abc', b'repr=%5V', 'abc', b'123')
        check_format('repr=ab', b'repr=%.2V', 'abc', b'123')
        check_format('repr=   ab', b'repr=%5.2V', 'abc', b'123')
        check_format('repr=  123', b'repr=%5V', None, b'123')
        check_format('repr=12', b'repr=%.2V', None, b'123')
        check_format('repr=   12', b'repr=%5.2V', None, b'123')
        check_format('010', b'%03i', c_int(10))
        check_format('0010', b'%0.4i', c_int(10))
        check_format('-123', b'%i', c_int(-123))
        check_format('-123', b'%li', c_long(-123))
        check_format('-123', b'%lli', c_longlong(-123))
        check_format('-123', b'%zi', c_ssize_t(-123))
        check_format('-123', b'%d', c_int(-123))
        check_format('-123', b'%ld', c_long(-123))
        check_format('-123', b'%lld', c_longlong(-123))
        check_format('-123', b'%zd', c_ssize_t(-123))
        check_format('123', b'%u', c_uint(123))
        check_format('123', b'%lu', c_ulong(123))
        check_format('123', b'%llu', c_ulonglong(123))
        check_format('123', b'%zu', c_size_t(123))
        min_longlong = -2 ** (8 * sizeof(c_longlong) - 1)
        max_longlong = -min_longlong - 1
        check_format(str(min_longlong), b'%lld', c_longlong(min_longlong))
        check_format(str(max_longlong), b'%lld', c_longlong(max_longlong))
        max_ulonglong = 2 ** (8 * sizeof(c_ulonglong)) - 1
        check_format(str(max_ulonglong), b'%llu', c_ulonglong(max_ulonglong))
        PyUnicode_FromFormat(b'%p', c_void_p(-1))
        check_format('123'.rjust(10, '0'), b'%010i', c_int(123))
        check_format('123'.rjust(100), b'%100i', c_int(123))
        check_format('123'.rjust(100, '0'), b'%.100i', c_int(123))
        check_format('123'.rjust(80, '0').rjust(100), b'%100.80i', c_int(123))
        check_format('123'.rjust(10, '0'), b'%010u', c_uint(123))
        check_format('123'.rjust(100), b'%100u', c_uint(123))
        check_format('123'.rjust(100, '0'), b'%.100u', c_uint(123))
        check_format('123'.rjust(80, '0').rjust(100), b'%100.80u', c_uint(123))
        check_format('123'.rjust(10, '0'), b'%010x', c_int(291))
        check_format('123'.rjust(100), b'%100x', c_int(291))
        check_format('123'.rjust(100, '0'), b'%.100x', c_int(291))
        check_format('123'.rjust(80, '0').rjust(100), b'%100.80x', c_int(291))
        check_format("%A:'abc\\xe9\\uabcd\\U0010ffff'", b'%%A:%A',
            'abcéꯍ\U0010ffff')
        check_format('repr=abc', b'repr=%V', 'abc', b'xyz')
        check_format('repr=人民', b'repr=%V', None, b'\xe4\xba\xba\xe6\xb0\x91')
        check_format('repr=abc�', b'repr=%V', None, b'abc\xff')
        check_format('%s', b'%1%s', b'abc')
        check_format('%1abc', b'%1abc')
        check_format('%+i', b'%+i', c_int(10))
        check_format('%.%s', b'%.%s', b'abc')

    @support.cpython_only
    def test_aswidechar(self):
        from _testcapi import unicode_aswidechar
        support.import_module('ctypes')
        from ctypes import c_wchar, sizeof
        wchar, size = unicode_aswidechar('abcdef', 2)
        self.assertEqual(size, 2)
        self.assertEqual(wchar, 'ab')
        wchar, size = unicode_aswidechar('abc', 3)
        self.assertEqual(size, 3)
        self.assertEqual(wchar, 'abc')
        wchar, size = unicode_aswidechar('abc', 4)
        self.assertEqual(size, 3)
        self.assertEqual(wchar, 'abc\x00')
        wchar, size = unicode_aswidechar('abc', 10)
        self.assertEqual(size, 3)
        self.assertEqual(wchar, 'abc\x00')
        wchar, size = unicode_aswidechar('abc\x00def', 20)
        self.assertEqual(size, 7)
        self.assertEqual(wchar, 'abc\x00def\x00')
        nonbmp = chr(1114111)
        if sizeof(c_wchar) == 2:
            buflen = 3
            nchar = 2
        else:
            buflen = 2
            nchar = 1
        wchar, size = unicode_aswidechar(nonbmp, buflen)
        self.assertEqual(size, nchar)
        self.assertEqual(wchar, nonbmp + '\x00')

    @support.cpython_only
    def test_aswidecharstring(self):
        from _testcapi import unicode_aswidecharstring
        support.import_module('ctypes')
        from ctypes import c_wchar, sizeof
        wchar, size = unicode_aswidecharstring('abc')
        self.assertEqual(size, 3)
        self.assertEqual(wchar, 'abc\x00')
        wchar, size = unicode_aswidecharstring('abc\x00def')
        self.assertEqual(size, 7)
        self.assertEqual(wchar, 'abc\x00def\x00')
        nonbmp = chr(1114111)
        if sizeof(c_wchar) == 2:
            nchar = 2
        else:
            nchar = 1
        wchar, size = unicode_aswidecharstring(nonbmp)
        self.assertEqual(size, nchar)
        self.assertEqual(wchar, nonbmp + '\x00')

    @support.cpython_only
    def test_asucs4(self):
        from _testcapi import unicode_asucs4
        for s in ['abc', '¡¢', '你好', 'a😀', 'a\ud800b\udfffc', '\ud834\udd1e']:
            l = len(s)
            self.assertEqual(unicode_asucs4(s, l, 1), s + '\x00')
            self.assertEqual(unicode_asucs4(s, l, 0), s + '\uffff')
            self.assertEqual(unicode_asucs4(s, l + 1, 1), s + '\x00\uffff')
            self.assertEqual(unicode_asucs4(s, l + 1, 0), s + '\x00\uffff')
            self.assertRaises(SystemError, unicode_asucs4, s, l - 1, 1)
            self.assertRaises(SystemError, unicode_asucs4, s, l - 2, 0)
            s = '\x00'.join([s, s])
            self.assertEqual(unicode_asucs4(s, len(s), 1), s + '\x00')
            self.assertEqual(unicode_asucs4(s, len(s), 0), s + '\uffff')

    @support.cpython_only
    def test_copycharacters(self):
        from _testcapi import unicode_copycharacters
        strings = ['abcde', '¡¢£¤¥', '你好世界！', '😀😁😂😃😄']
        for idx, from_ in enumerate(strings):
            for to in strings[:idx]:
                self.assertRaises(SystemError, unicode_copycharacters, to, 
                    0, from_, 0, 5)
            for from_start in range(5):
                self.assertEqual(unicode_copycharacters(from_, 0, from_,
                    from_start, 5), (from_[from_start:from_start + 5].ljust
                    (5, '\x00'), 5 - from_start))
            for to_start in range(5):
                self.assertEqual(unicode_copycharacters(from_, to_start,
                    from_, to_start, 5), (from_[to_start:to_start + 5].
                    rjust(5, '\x00'), 5 - to_start))
        s = strings[0]
        self.assertRaises(IndexError, unicode_copycharacters, s, 6, s, 0, 5)
        self.assertRaises(IndexError, unicode_copycharacters, s, -1, s, 0, 5)
        self.assertRaises(IndexError, unicode_copycharacters, s, 0, s, 6, 5)
        self.assertRaises(IndexError, unicode_copycharacters, s, 0, s, -1, 5)
        self.assertRaises(SystemError, unicode_copycharacters, s, 1, s, 0, 5)
        self.assertRaises(SystemError, unicode_copycharacters, s, 0, s, 0, -1)
        self.assertRaises(SystemError, unicode_copycharacters, s, 0, b'', 0, 0)

    @support.cpython_only
    def test_encode_decimal(self):
        from _testcapi import unicode_encodedecimal
        self.assertEqual(unicode_encodedecimal('123'), b'123')
        self.assertEqual(unicode_encodedecimal('٣.١٤'), b'3.14')
        self.assertEqual(unicode_encodedecimal('\u20033.14\u2002'), b' 3.14 ')
        self.assertRaises(UnicodeEncodeError, unicode_encodedecimal, '123€',
            'strict')
        self.assertRaisesRegex(ValueError,
            "^'decimal' codec can't encode character",
            unicode_encodedecimal, '123€', 'replace')

    @support.cpython_only
    def test_transform_decimal(self):
        from _testcapi import unicode_transformdecimaltoascii as transform_decimal
        self.assertEqual(transform_decimal('123'), '123')
        self.assertEqual(transform_decimal('٣.١٤'), '3.14')
        self.assertEqual(transform_decimal('\u20033.14\u2002'),
            '\u20033.14\u2002')
        self.assertEqual(transform_decimal('123€'), '123€')

    @support.cpython_only
    def test_pep393_utf8_caching_bug(self):
        from _testcapi import getargs_s_hash
        for k in (36, 164, 8364, 128013):
            s = ''
            for i in range(5):
                s += chr(k)
                self.assertEqual(getargs_s_hash(s), chr(k).encode() * (i + 1))
                self.assertEqual(getargs_s_hash(s), chr(k).encode() * (i + 1))


class StringModuleTest(unittest.TestCase):

    def test_formatter_parser(self):

        def parse(format):
            return list(_string.formatter_parser(format))
        formatter = parse('prefix {2!s}xxx{0:^+10.3f}{obj.attr!s} {z[0]!s:10}')
        self.assertEqual(formatter, [('prefix ', '2', '', 's'), ('xxx', '0',
            '^+10.3f', None), ('', 'obj.attr', '', 's'), (' ', 'z[0]', '10',
            's')])
        formatter = parse('prefix {} suffix')
        self.assertEqual(formatter, [('prefix ', '', '', None), (' suffix',
            None, None, None)])
        formatter = parse('str')
        self.assertEqual(formatter, [('str', None, None, None)])
        formatter = parse('')
        self.assertEqual(formatter, [])
        formatter = parse('{0}')
        self.assertEqual(formatter, [('', '0', '', None)])
        self.assertRaises(TypeError, _string.formatter_parser, 1)

    def test_formatter_field_name_split(self):

        def split(name):
            items = list(_string.formatter_field_name_split(name))
            items[1] = list(items[1])
            return items
        self.assertEqual(split('obj'), ['obj', []])
        self.assertEqual(split('obj.arg'), ['obj', [(True, 'arg')]])
        self.assertEqual(split('obj[key]'), ['obj', [(False, 'key')]])
        self.assertEqual(split('obj.arg[key1][key2]'), ['obj', [(True,
            'arg'), (False, 'key1'), (False, 'key2')]])
        self.assertRaises(TypeError, _string.formatter_field_name_split, 1)


if __name__ == '__main__':
    unittest.main()
