from test.support import verbose, run_unittest, gc_collect, bigmemtest, _2G, cpython_only, captured_stdout
import io
import locale
import re
import sre_compile
import string
import sys
import traceback
import unittest
import warnings
from re import Scanner
from weakref import proxy


class S(str):

    def __getitem__(self, index):
        return S(super().__getitem__(index))


class B(bytes):

    def __getitem__(self, index):
        return B(super().__getitem__(index))


class ReTests(unittest.TestCase):

    def assertTypedEqual(self, actual, expect, msg=None):
        self.assertEqual(actual, expect, msg)

        def recurse(actual, expect):
            if isinstance(expect, (tuple, list)):
                for x, y in zip(actual, expect):
                    recurse(x, y)
            else:
                self.assertIs(type(actual), type(expect), msg)
        recurse(actual, expect)

    def checkPatternError(self, pattern, errmsg, pos=None):
        with self.assertRaises(re.error) as cm:
            re.compile(pattern)
        with self.subTest(pattern=pattern):
            err = cm.exception
            self.assertEqual(err.msg, errmsg)
            if pos is not None:
                self.assertEqual(err.pos, pos)

    def checkTemplateError(self, pattern, repl, string, errmsg, pos=None):
        with self.assertRaises(re.error) as cm:
            re.sub(pattern, repl, string)
        with self.subTest(pattern=pattern, repl=repl):
            err = cm.exception
            self.assertEqual(err.msg, errmsg)
            if pos is not None:
                self.assertEqual(err.pos, pos)

    def test_keep_buffer(self):
        b = bytearray(b'x')
        it = re.finditer(b'a', b)
        with self.assertRaises(BufferError):
            b.extend(b'x' * 400)
        list(it)
        del it
        gc_collect()
        b.extend(b'x' * 400)

    def test_weakref(self):
        s = 'QabbbcR'
        x = re.compile('ab+c')
        y = proxy(x)
        self.assertEqual(x.findall('QabbbcR'), y.findall('QabbbcR'))

    def test_search_star_plus(self):
        self.assertEqual(re.search('x*', 'axx').span(0), (0, 0))
        self.assertEqual(re.search('x*', 'axx').span(), (0, 0))
        self.assertEqual(re.search('x+', 'axx').span(0), (1, 3))
        self.assertEqual(re.search('x+', 'axx').span(), (1, 3))
        self.assertIsNone(re.search('x', 'aaa'))
        self.assertEqual(re.match('a*', 'xxx').span(0), (0, 0))
        self.assertEqual(re.match('a*', 'xxx').span(), (0, 0))
        self.assertEqual(re.match('x*', 'xxxa').span(0), (0, 3))
        self.assertEqual(re.match('x*', 'xxxa').span(), (0, 3))
        self.assertIsNone(re.match('a+', 'xxx'))

    def bump_num(self, matchobj):
        int_value = int(matchobj.group(0))
        return str(int_value + 1)

    def test_basic_re_sub(self):
        self.assertTypedEqual(re.sub('y', 'a', 'xyz'), 'xaz')
        self.assertTypedEqual(re.sub('y', S('a'), S('xyz')), 'xaz')
        self.assertTypedEqual(re.sub(b'y', b'a', b'xyz'), b'xaz')
        self.assertTypedEqual(re.sub(b'y', B(b'a'), B(b'xyz')), b'xaz')
        self.assertTypedEqual(re.sub(b'y', bytearray(b'a'), bytearray(
            b'xyz')), b'xaz')
        self.assertTypedEqual(re.sub(b'y', memoryview(b'a'), memoryview(
            b'xyz')), b'xaz')
        for y in ('à', 'а', '𝒜'):
            self.assertEqual(re.sub(y, 'a', 'x%sz' % y), 'xaz')
        self.assertEqual(re.sub('(?i)b+', 'x', 'bbbb BBBB'), 'x x')
        self.assertEqual(re.sub('\\d+', self.bump_num, '08.2 -2 23x99y'),
            '9.3 -3 24x100y')
        self.assertEqual(re.sub('\\d+', self.bump_num, '08.2 -2 23x99y', 3),
            '9.3 -3 23x99y')
        self.assertEqual(re.sub('\\d+', self.bump_num, '08.2 -2 23x99y',
            count=3), '9.3 -3 23x99y')
        self.assertEqual(re.sub('.', lambda m: '\\n', 'x'), '\\n')
        self.assertEqual(re.sub('.', '\\n', 'x'), '\n')
        s = '\\1\\1'
        self.assertEqual(re.sub('(.)', s, 'x'), 'xx')
        self.assertEqual(re.sub('(.)', re.escape(s), 'x'), s)
        self.assertEqual(re.sub('(.)', lambda m: s, 'x'), s)
        self.assertEqual(re.sub('(?P<a>x)', '\\g<a>\\g<a>', 'xx'), 'xxxx')
        self.assertEqual(re.sub('(?P<a>x)', '\\g<a>\\g<1>', 'xx'), 'xxxx')
        self.assertEqual(re.sub('(?P<unk>x)', '\\g<unk>\\g<unk>', 'xx'), 'xxxx'
            )
        self.assertEqual(re.sub('(?P<unk>x)', '\\g<1>\\g<1>', 'xx'), 'xxxx')
        self.assertEqual(re.sub('a', '\\t\\n\\v\\r\\f\\a\\b', 'a'),
            '\t\n\x0b\r\x0c\x07\x08')
        self.assertEqual(re.sub('a', '\t\n\x0b\r\x0c\x07\x08', 'a'),
            '\t\n\x0b\r\x0c\x07\x08')
        self.assertEqual(re.sub('a', '\t\n\x0b\r\x0c\x07\x08', 'a'), chr(9) +
            chr(10) + chr(11) + chr(13) + chr(12) + chr(7) + chr(8))
        for c in 'cdehijklmopqsuwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
            with self.subTest(c):
                with self.assertWarns(DeprecationWarning):
                    self.assertEqual(re.sub('a', '\\' + c, 'a'), '\\' + c)
        self.assertEqual(re.sub('^\\s*', 'X', 'test'), 'Xtest')

    def test_bug_449964(self):
        self.assertEqual(re.sub('(?P<unk>x)', '\\g<1>\\g<1>\\b', 'xx'),
            'xx\x08xx\x08')

    def test_bug_449000(self):
        self.assertEqual(re.sub('\\r\\n', '\\n', 'abc\r\ndef\r\n'),
            'abc\ndef\n')
        self.assertEqual(re.sub('\r\n', '\\n', 'abc\r\ndef\r\n'), 'abc\ndef\n')
        self.assertEqual(re.sub('\\r\\n', '\n', 'abc\r\ndef\r\n'), 'abc\ndef\n'
            )
        self.assertEqual(re.sub('\r\n', '\n', 'abc\r\ndef\r\n'), 'abc\ndef\n')

    def test_bug_1661(self):
        pattern = re.compile('.')
        self.assertRaises(ValueError, re.match, pattern, 'A', re.I)
        self.assertRaises(ValueError, re.search, pattern, 'A', re.I)
        self.assertRaises(ValueError, re.findall, pattern, 'A', re.I)
        self.assertRaises(ValueError, re.compile, pattern, re.I)

    def test_bug_3629(self):
        re.compile('(?P<quote>)(?(quote))')

    def test_sub_template_numeric_escape(self):
        self.assertEqual(re.sub('x', '\\0', 'x'), '\x00')
        self.assertEqual(re.sub('x', '\\000', 'x'), '\x00')
        self.assertEqual(re.sub('x', '\\001', 'x'), '\x01')
        self.assertEqual(re.sub('x', '\\008', 'x'), '\x00' + '8')
        self.assertEqual(re.sub('x', '\\009', 'x'), '\x00' + '9')
        self.assertEqual(re.sub('x', '\\111', 'x'), 'I')
        self.assertEqual(re.sub('x', '\\117', 'x'), 'O')
        self.assertEqual(re.sub('x', '\\377', 'x'), 'ÿ')
        self.assertEqual(re.sub('x', '\\1111', 'x'), 'I1')
        self.assertEqual(re.sub('x', '\\1111', 'x'), 'I' + '1')
        self.assertEqual(re.sub('x', '\\00', 'x'), '\x00')
        self.assertEqual(re.sub('x', '\\07', 'x'), '\x07')
        self.assertEqual(re.sub('x', '\\08', 'x'), '\x00' + '8')
        self.assertEqual(re.sub('x', '\\09', 'x'), '\x00' + '9')
        self.assertEqual(re.sub('x', '\\0a', 'x'), '\x00' + 'a')
        self.checkTemplateError('x', '\\400', 'x',
            'octal escape value \\400 outside of range 0-0o377', 0)
        self.checkTemplateError('x', '\\777', 'x',
            'octal escape value \\777 outside of range 0-0o377', 0)
        self.checkTemplateError('x', '\\1', 'x', 'invalid group reference 1', 1
            )
        self.checkTemplateError('x', '\\8', 'x', 'invalid group reference 8', 1
            )
        self.checkTemplateError('x', '\\9', 'x', 'invalid group reference 9', 1
            )
        self.checkTemplateError('x', '\\11', 'x',
            'invalid group reference 11', 1)
        self.checkTemplateError('x', '\\18', 'x',
            'invalid group reference 18', 1)
        self.checkTemplateError('x', '\\1a', 'x',
            'invalid group reference 1', 1)
        self.checkTemplateError('x', '\\90', 'x',
            'invalid group reference 90', 1)
        self.checkTemplateError('x', '\\99', 'x',
            'invalid group reference 99', 1)
        self.checkTemplateError('x', '\\118', 'x',
            'invalid group reference 11', 1)
        self.checkTemplateError('x', '\\11a', 'x',
            'invalid group reference 11', 1)
        self.checkTemplateError('x', '\\181', 'x',
            'invalid group reference 18', 1)
        self.checkTemplateError('x', '\\800', 'x',
            'invalid group reference 80', 1)
        self.checkTemplateError('x', '\\8', '', 'invalid group reference 8', 1)
        self.assertEqual(re.sub('(((((((((((x)))))))))))', '\\11', 'x'), 'x')
        self.assertEqual(re.sub('((((((((((y))))))))))(.)', '\\118', 'xyz'),
            'xz8')
        self.assertEqual(re.sub('((((((((((y))))))))))(.)', '\\11a', 'xyz'),
            'xza')

    def test_qualified_re_sub(self):
        self.assertEqual(re.sub('a', 'b', 'aaaaa'), 'bbbbb')
        self.assertEqual(re.sub('a', 'b', 'aaaaa', 1), 'baaaa')
        self.assertEqual(re.sub('a', 'b', 'aaaaa', count=1), 'baaaa')

    def test_bug_114660(self):
        self.assertEqual(re.sub('(\\S)\\s+(\\S)', '\\1 \\2', 'hello  there'
            ), 'hello there')

    def test_bug_462270(self):
        self.assertEqual(re.sub('x*', '-', 'abxd'), '-a-b-d-')
        self.assertEqual(re.sub('x+', '-', 'abxd'), 'ab-d')

    def test_symbolic_groups(self):
        re.compile('(?P<a>x)(?P=a)(?(a)y)')
        re.compile('(?P<a1>x)(?P=a1)(?(a1)y)')
        re.compile('(?P<a1>x)\\1(?(1)y)')
        self.checkPatternError('(?P<a>)(?P<a>)',
            "redefinition of group name 'a' as group 2; was group 1")
        self.checkPatternError('(?P<a>(?P=a))',
            'cannot refer to an open group', 10)
        self.checkPatternError('(?Pxy)', 'unknown extension ?Px')
        self.checkPatternError('(?P<a>)(?P=a',
            'missing ), unterminated name', 11)
        self.checkPatternError('(?P=', 'missing group name', 4)
        self.checkPatternError('(?P=)', 'missing group name', 4)
        self.checkPatternError('(?P=1)', "bad character in group name '1'", 4)
        self.checkPatternError('(?P=a)', "unknown group name 'a'")
        self.checkPatternError('(?P=a1)', "unknown group name 'a1'")
        self.checkPatternError('(?P=a.)', "bad character in group name 'a.'", 4
            )
        self.checkPatternError('(?P<)', 'missing >, unterminated name', 4)
        self.checkPatternError('(?P<a', 'missing >, unterminated name', 4)
        self.checkPatternError('(?P<', 'missing group name', 4)
        self.checkPatternError('(?P<>)', 'missing group name', 4)
        self.checkPatternError('(?P<1>)', "bad character in group name '1'", 4)
        self.checkPatternError('(?P<a.>)',
            "bad character in group name 'a.'", 4)
        self.checkPatternError('(?(', 'missing group name', 3)
        self.checkPatternError('(?())', 'missing group name', 3)
        self.checkPatternError('(?(a))', "unknown group name 'a'", 3)
        self.checkPatternError('(?(-1))', "bad character in group name '-1'", 3
            )
        self.checkPatternError('(?(1a))', "bad character in group name '1a'", 3
            )
        self.checkPatternError('(?(a.))', "bad character in group name 'a.'", 3
            )
        re.compile('(?P<µ>x)(?P=µ)(?(µ)y)')
        re.compile('(?P<𝔘𝔫𝔦𝔠𝔬𝔡𝔢>x)(?P=𝔘𝔫𝔦𝔠𝔬𝔡𝔢)(?(𝔘𝔫𝔦𝔠𝔬𝔡𝔢)y)')
        self.checkPatternError('(?P<©>x)', "bad character in group name '©'", 4
            )
        pat = '|'.join('x(?P<a%d>%x)y' % (i, i) for i in range(1, 200 + 1))
        pat = '(?:%s)(?(200)z|t)' % pat
        self.assertEqual(re.match(pat, 'xc8yz').span(), (0, 5))

    def test_symbolic_refs(self):
        self.checkTemplateError('(?P<a>x)', '\\g<a', 'xx',
            'missing >, unterminated name', 3)
        self.checkTemplateError('(?P<a>x)', '\\g<', 'xx',
            'missing group name', 3)
        self.checkTemplateError('(?P<a>x)', '\\g', 'xx', 'missing <', 2)
        self.checkTemplateError('(?P<a>x)', '\\g<a a>', 'xx',
            "bad character in group name 'a a'", 3)
        self.checkTemplateError('(?P<a>x)', '\\g<>', 'xx',
            'missing group name', 3)
        self.checkTemplateError('(?P<a>x)', '\\g<1a1>', 'xx',
            "bad character in group name '1a1'", 3)
        self.checkTemplateError('(?P<a>x)', '\\g<2>', 'xx',
            'invalid group reference 2', 3)
        self.checkTemplateError('(?P<a>x)', '\\2', 'xx',
            'invalid group reference 2', 1)
        with self.assertRaisesRegex(IndexError, "unknown group name 'ab'"):
            re.sub('(?P<a>x)', '\\g<ab>', 'xx')
        self.assertEqual(re.sub('(?P<a>x)|(?P<b>y)', '\\g<b>', 'xx'), '')
        self.assertEqual(re.sub('(?P<a>x)|(?P<b>y)', '\\2', 'xx'), '')
        self.checkTemplateError('(?P<a>x)', '\\g<-1>', 'xx',
            "bad character in group name '-1'", 3)
        self.assertEqual(re.sub('(?P<µ>x)', '\\g<µ>', 'xx'), 'xx')
        self.assertEqual(re.sub('(?P<𝔘𝔫𝔦𝔠𝔬𝔡𝔢>x)', '\\g<𝔘𝔫𝔦𝔠𝔬𝔡𝔢>', 'xx'), 'xx')
        self.checkTemplateError('(?P<a>x)', '\\g<©>', 'xx',
            "bad character in group name '©'", 3)
        pat = '|'.join('x(?P<a%d>%x)y' % (i, i) for i in range(1, 200 + 1))
        self.assertEqual(re.sub(pat, '\\g<200>', 'xc8yzxc8y'), 'c8zc8')

    def test_re_subn(self):
        self.assertEqual(re.subn('(?i)b+', 'x', 'bbbb BBBB'), ('x x', 2))
        self.assertEqual(re.subn('b+', 'x', 'bbbb BBBB'), ('x BBBB', 1))
        self.assertEqual(re.subn('b+', 'x', 'xyz'), ('xyz', 0))
        self.assertEqual(re.subn('b*', 'x', 'xyz'), ('xxxyxzx', 4))
        self.assertEqual(re.subn('b*', 'x', 'xyz', 2), ('xxxyz', 2))
        self.assertEqual(re.subn('b*', 'x', 'xyz', count=2), ('xxxyz', 2))

    def test_re_split(self):
        for string in (':a:b::c', S(':a:b::c')):
            self.assertTypedEqual(re.split(':', string), ['', 'a', 'b', '',
                'c'])
            self.assertTypedEqual(re.split(':+', string), ['', 'a', 'b', 'c'])
            self.assertTypedEqual(re.split('(:+)', string), ['', ':', 'a',
                ':', 'b', '::', 'c'])
        for string in (b':a:b::c', B(b':a:b::c'), bytearray(b':a:b::c'),
            memoryview(b':a:b::c')):
            self.assertTypedEqual(re.split(b':', string), [b'', b'a', b'b',
                b'', b'c'])
            self.assertTypedEqual(re.split(b':+', string), [b'', b'a', b'b',
                b'c'])
            self.assertTypedEqual(re.split(b'(:+)', string), [b'', b':',
                b'a', b':', b'b', b'::', b'c'])
        for a, b, c in ('àßç', 'абв', '𝒜𝒞𝒵'):
            string = ':%s:%s::%s' % (a, b, c)
            self.assertEqual(re.split(':', string), ['', a, b, '', c])
            self.assertEqual(re.split(':+', string), ['', a, b, c])
            self.assertEqual(re.split('(:+)', string), ['', ':', a, ':', b,
                '::', c])
        self.assertEqual(re.split('(?::+)', ':a:b::c'), ['', 'a', 'b', 'c'])
        self.assertEqual(re.split('(:)+', ':a:b::c'), ['', ':', 'a', ':',
            'b', ':', 'c'])
        self.assertEqual(re.split('([b:]+)', ':a:b::c'), ['', ':', 'a',
            ':b::', 'c'])
        self.assertEqual(re.split('(b)|(:+)', ':a:b::c'), ['', None, ':',
            'a', None, ':', '', 'b', None, '', None, '::', 'c'])
        self.assertEqual(re.split('(?:b)|(?::+)', ':a:b::c'), ['', 'a', '',
            '', 'c'])
        for sep, expected in [(':*', ['', 'a', 'b', 'c']), ('(?::*)', ['',
            'a', 'b', 'c']), ('(:*)', ['', ':', 'a', ':', 'b', '::', 'c']),
            ('(:)*', ['', ':', 'a', ':', 'b', ':', 'c'])]:
            with self.subTest(sep=sep), self.assertWarns(FutureWarning):
                self.assertTypedEqual(re.split(sep, ':a:b::c'), expected)
        for sep, expected in [('', [':a:b::c']), ('\\b', [':a:b::c']), (
            '(?=:)', [':a:b::c']), ('(?<=:)', [':a:b::c'])]:
            with self.subTest(sep=sep), self.assertRaises(ValueError):
                self.assertTypedEqual(re.split(sep, ':a:b::c'), expected)

    def test_qualified_re_split(self):
        self.assertEqual(re.split(':', ':a:b::c', 2), ['', 'a', 'b::c'])
        self.assertEqual(re.split(':', ':a:b::c', maxsplit=2), ['', 'a',
            'b::c'])
        self.assertEqual(re.split(':', 'a:b:c:d', maxsplit=2), ['a', 'b',
            'c:d'])
        self.assertEqual(re.split('(:)', ':a:b::c', maxsplit=2), ['', ':',
            'a', ':', 'b::c'])
        self.assertEqual(re.split('(:+)', ':a:b::c', maxsplit=2), ['', ':',
            'a', ':', 'b::c'])
        with self.assertWarns(FutureWarning):
            self.assertEqual(re.split('(:*)', ':a:b::c', maxsplit=2), ['',
                ':', 'a', ':', 'b::c'])

    def test_re_findall(self):
        self.assertEqual(re.findall(':+', 'abc'), [])
        for string in ('a:b::c:::d', S('a:b::c:::d')):
            self.assertTypedEqual(re.findall(':+', string), [':', '::', ':::'])
            self.assertTypedEqual(re.findall('(:+)', string), [':', '::',
                ':::'])
            self.assertTypedEqual(re.findall('(:)(:*)', string), [(':', ''),
                (':', ':'), (':', '::')])
        for string in (b'a:b::c:::d', B(b'a:b::c:::d'), bytearray(
            b'a:b::c:::d'), memoryview(b'a:b::c:::d')):
            self.assertTypedEqual(re.findall(b':+', string), [b':', b'::',
                b':::'])
            self.assertTypedEqual(re.findall(b'(:+)', string), [b':', b'::',
                b':::'])
            self.assertTypedEqual(re.findall(b'(:)(:*)', string), [(b':',
                b''), (b':', b':'), (b':', b'::')])
        for x in ('à', 'а', '𝒜'):
            xx = x * 2
            xxx = x * 3
            string = 'a%sb%sc%sd' % (x, xx, xxx)
            self.assertEqual(re.findall('%s+' % x, string), [x, xx, xxx])
            self.assertEqual(re.findall('(%s+)' % x, string), [x, xx, xxx])
            self.assertEqual(re.findall('(%s)(%s*)' % (x, x), string), [(x,
                ''), (x, x), (x, xx)])

    def test_bug_117612(self):
        self.assertEqual(re.findall('(a|(b))', 'aba'), [('a', ''), ('b',
            'b'), ('a', '')])

    def test_re_match(self):
        for string in ('a', S('a')):
            self.assertEqual(re.match('a', string).groups(), ())
            self.assertEqual(re.match('(a)', string).groups(), ('a',))
            self.assertEqual(re.match('(a)', string).group(0), 'a')
            self.assertEqual(re.match('(a)', string).group(1), 'a')
            self.assertEqual(re.match('(a)', string).group(1, 1), ('a', 'a'))
        for string in (b'a', B(b'a'), bytearray(b'a'), memoryview(b'a')):
            self.assertEqual(re.match(b'a', string).groups(), ())
            self.assertEqual(re.match(b'(a)', string).groups(), (b'a',))
            self.assertEqual(re.match(b'(a)', string).group(0), b'a')
            self.assertEqual(re.match(b'(a)', string).group(1), b'a')
            self.assertEqual(re.match(b'(a)', string).group(1, 1), (b'a', b'a')
                )
        for a in ('à', 'а', '𝒜'):
            self.assertEqual(re.match(a, a).groups(), ())
            self.assertEqual(re.match('(%s)' % a, a).groups(), (a,))
            self.assertEqual(re.match('(%s)' % a, a).group(0), a)
            self.assertEqual(re.match('(%s)' % a, a).group(1), a)
            self.assertEqual(re.match('(%s)' % a, a).group(1, 1), (a, a))
        pat = re.compile('((a)|(b))(c)?')
        self.assertEqual(pat.match('a').groups(), ('a', 'a', None, None))
        self.assertEqual(pat.match('b').groups(), ('b', None, 'b', None))
        self.assertEqual(pat.match('ac').groups(), ('a', 'a', None, 'c'))
        self.assertEqual(pat.match('bc').groups(), ('b', None, 'b', 'c'))
        self.assertEqual(pat.match('bc').groups(''), ('b', '', 'b', 'c'))
        pat = re.compile('(?:(?P<a1>a)|(?P<b2>b))(?P<c3>c)?')
        self.assertEqual(pat.match('a').group(1, 2, 3), ('a', None, None))
        self.assertEqual(pat.match('b').group('a1', 'b2', 'c3'), (None, 'b',
            None))
        self.assertEqual(pat.match('ac').group(1, 'b2', 3), ('a', None, 'c'))

    def test_group(self):


        class Index:

            def __init__(self, value):
                self.value = value

            def __index__(self):
                return self.value
        m = re.match('(a)(b)', 'ab')
        self.assertEqual(m.group(), 'ab')
        self.assertEqual(m.group(0), 'ab')
        self.assertEqual(m.group(1), 'a')
        self.assertEqual(m.group(Index(1)), 'a')
        self.assertRaises(IndexError, m.group, -1)
        self.assertRaises(IndexError, m.group, 3)
        self.assertRaises(IndexError, m.group, 1 << 1000)
        self.assertRaises(IndexError, m.group, Index(1 << 1000))
        self.assertRaises(IndexError, m.group, 'x')
        self.assertEqual(m.group(2, 1), ('b', 'a'))
        self.assertEqual(m.group(Index(2), Index(1)), ('b', 'a'))

    def test_match_getitem(self):
        pat = re.compile('(?:(?P<a1>a)|(?P<b2>b))(?P<c3>c)?')
        m = pat.match('a')
        self.assertEqual(m['a1'], 'a')
        self.assertEqual(m['b2'], None)
        self.assertEqual(m['c3'], None)
        self.assertEqual('a1={a1} b2={b2} c3={c3}'.format_map(m),
            'a1=a b2=None c3=None')
        self.assertEqual(m[0], 'a')
        self.assertEqual(m[1], 'a')
        self.assertEqual(m[2], None)
        self.assertEqual(m[3], None)
        with self.assertRaisesRegex(IndexError, 'no such group'):
            m['X']
        with self.assertRaisesRegex(IndexError, 'no such group'):
            m[-1]
        with self.assertRaisesRegex(IndexError, 'no such group'):
            m[4]
        with self.assertRaisesRegex(IndexError, 'no such group'):
            m[0, 1]
        with self.assertRaisesRegex(IndexError, 'no such group'):
            m[0,]
        with self.assertRaisesRegex(IndexError, 'no such group'):
            m[0, 1]
        with self.assertRaisesRegex(KeyError, 'a2'):
            """a1={a2}""".format_map(m)
        m = pat.match('ac')
        self.assertEqual(m['a1'], 'a')
        self.assertEqual(m['b2'], None)
        self.assertEqual(m['c3'], 'c')
        self.assertEqual('a1={a1} b2={b2} c3={c3}'.format_map(m),
            'a1=a b2=None c3=c')
        self.assertEqual(m[0], 'ac')
        self.assertEqual(m[1], 'a')
        self.assertEqual(m[2], None)
        self.assertEqual(m[3], 'c')
        with self.assertRaises(TypeError):
            m[0] = 1
        self.assertRaises(TypeError, len, m)

    def test_re_fullmatch(self):
        self.assertEqual(re.fullmatch('a', 'a').span(), (0, 1))
        for string in ('ab', S('ab')):
            self.assertEqual(re.fullmatch('a|ab', string).span(), (0, 2))
        for string in (b'ab', B(b'ab'), bytearray(b'ab'), memoryview(b'ab')):
            self.assertEqual(re.fullmatch(b'a|ab', string).span(), (0, 2))
        for a, b in ('àß', 'аб', '𝒜𝒞'):
            r = '%s|%s' % (a, a + b)
            self.assertEqual(re.fullmatch(r, a + b).span(), (0, 2))
        self.assertEqual(re.fullmatch('.*?$', 'abc').span(), (0, 3))
        self.assertEqual(re.fullmatch('.*?', 'abc').span(), (0, 3))
        self.assertEqual(re.fullmatch('a.*?b', 'ab').span(), (0, 2))
        self.assertEqual(re.fullmatch('a.*?b', 'abb').span(), (0, 3))
        self.assertEqual(re.fullmatch('a.*?b', 'axxb').span(), (0, 4))
        self.assertIsNone(re.fullmatch('a+', 'ab'))
        self.assertIsNone(re.fullmatch('abc$', 'abc\n'))
        self.assertIsNone(re.fullmatch('abc\\Z', 'abc\n'))
        self.assertIsNone(re.fullmatch('(?m)abc$', 'abc\n'))
        self.assertEqual(re.fullmatch('ab(?=c)cd', 'abcd').span(), (0, 4))
        self.assertEqual(re.fullmatch('ab(?<=b)cd', 'abcd').span(), (0, 4))
        self.assertEqual(re.fullmatch('(?=a|ab)ab', 'ab').span(), (0, 2))
        self.assertEqual(re.compile('bc').fullmatch('abcd', pos=1, endpos=3
            ).span(), (1, 3))
        self.assertEqual(re.compile('.*?$').fullmatch('abcd', pos=1, endpos
            =3).span(), (1, 3))
        self.assertEqual(re.compile('.*?').fullmatch('abcd', pos=1, endpos=
            3).span(), (1, 3))

    def test_re_groupref_exists(self):
        self.assertEqual(re.match('^(\\()?([^()]+)(?(1)\\))$', '(a)').
            groups(), ('(', 'a'))
        self.assertEqual(re.match('^(\\()?([^()]+)(?(1)\\))$', 'a').groups(
            ), (None, 'a'))
        self.assertIsNone(re.match('^(\\()?([^()]+)(?(1)\\))$', 'a)'))
        self.assertIsNone(re.match('^(\\()?([^()]+)(?(1)\\))$', '(a'))
        self.assertEqual(re.match('^(?:(a)|c)((?(1)b|d))$', 'ab').groups(),
            ('a', 'b'))
        self.assertEqual(re.match('^(?:(a)|c)((?(1)b|d))$', 'cd').groups(),
            (None, 'd'))
        self.assertEqual(re.match('^(?:(a)|c)((?(1)|d))$', 'cd').groups(),
            (None, 'd'))
        self.assertEqual(re.match('^(?:(a)|c)((?(1)|d))$', 'a').groups(), (
            'a', ''))
        p = re.compile('(?P<g1>a)(?P<g2>b)?((?(g2)c|d))')
        self.assertEqual(p.match('abc').groups(), ('a', 'b', 'c'))
        self.assertEqual(p.match('ad').groups(), ('a', None, 'd'))
        self.assertIsNone(p.match('abd'))
        self.assertIsNone(p.match('ac'))
        pat = '|'.join('x(?P<a%d>%x)y' % (i, i) for i in range(1, 200 + 1))
        pat = '(?:%s)(?(200)z)' % pat
        self.assertEqual(re.match(pat, 'xc8yz').span(), (0, 5))
        self.checkPatternError('(?P<a>)(?(0))', 'bad group number', 10)
        self.checkPatternError('()(?(1)a|b',
            'missing ), unterminated subpattern', 2)
        self.checkPatternError('()(?(1)a|b|c)',
            'conditional backref with more than two branches', 10)

    def test_re_groupref_overflow(self):
        from sre_constants import MAXGROUPS
        self.checkTemplateError('()', '\\g<%s>' % MAXGROUPS, 'xx', 
            'invalid group reference %d' % MAXGROUPS, 3)
        self.checkPatternError('(?P<a>)(?(%d))' % MAXGROUPS, 
            'invalid group reference %d' % MAXGROUPS, 10)

    def test_re_groupref(self):
        self.assertEqual(re.match('^(\\|)?([^()]+)\\1$', '|a|').groups(), (
            '|', 'a'))
        self.assertEqual(re.match('^(\\|)?([^()]+)\\1?$', 'a').groups(), (
            None, 'a'))
        self.assertIsNone(re.match('^(\\|)?([^()]+)\\1$', 'a|'))
        self.assertIsNone(re.match('^(\\|)?([^()]+)\\1$', '|a'))
        self.assertEqual(re.match('^(?:(a)|c)(\\1)$', 'aa').groups(), ('a',
            'a'))
        self.assertEqual(re.match('^(?:(a)|c)(\\1)?$', 'c').groups(), (None,
            None))
        self.checkPatternError('(abc\\1)', 'cannot refer to an open group', 4)

    def test_groupdict(self):
        self.assertEqual(re.match('(?P<first>first) (?P<second>second)',
            'first second').groupdict(), {'first': 'first', 'second': 'second'}
            )

    def test_expand(self):
        self.assertEqual(re.match('(?P<first>first) (?P<second>second)',
            'first second').expand('\\2 \\1 \\g<second> \\g<first>'),
            'second first second first')
        self.assertEqual(re.match('(?P<first>first)|(?P<second>second)',
            'first').expand('\\2 \\g<second>'), ' ')

    def test_repeat_minmax(self):
        self.assertIsNone(re.match('^(\\w){1}$', 'abc'))
        self.assertIsNone(re.match('^(\\w){1}?$', 'abc'))
        self.assertIsNone(re.match('^(\\w){1,2}$', 'abc'))
        self.assertIsNone(re.match('^(\\w){1,2}?$', 'abc'))
        self.assertEqual(re.match('^(\\w){3}$', 'abc').group(1), 'c')
        self.assertEqual(re.match('^(\\w){1,3}$', 'abc').group(1), 'c')
        self.assertEqual(re.match('^(\\w){1,4}$', 'abc').group(1), 'c')
        self.assertEqual(re.match('^(\\w){3,4}?$', 'abc').group(1), 'c')
        self.assertEqual(re.match('^(\\w){3}?$', 'abc').group(1), 'c')
        self.assertEqual(re.match('^(\\w){1,3}?$', 'abc').group(1), 'c')
        self.assertEqual(re.match('^(\\w){1,4}?$', 'abc').group(1), 'c')
        self.assertEqual(re.match('^(\\w){3,4}?$', 'abc').group(1), 'c')
        self.assertIsNone(re.match('^x{1}$', 'xxx'))
        self.assertIsNone(re.match('^x{1}?$', 'xxx'))
        self.assertIsNone(re.match('^x{1,2}$', 'xxx'))
        self.assertIsNone(re.match('^x{1,2}?$', 'xxx'))
        self.assertTrue(re.match('^x{3}$', 'xxx'))
        self.assertTrue(re.match('^x{1,3}$', 'xxx'))
        self.assertTrue(re.match('^x{3,3}$', 'xxx'))
        self.assertTrue(re.match('^x{1,4}$', 'xxx'))
        self.assertTrue(re.match('^x{3,4}?$', 'xxx'))
        self.assertTrue(re.match('^x{3}?$', 'xxx'))
        self.assertTrue(re.match('^x{1,3}?$', 'xxx'))
        self.assertTrue(re.match('^x{1,4}?$', 'xxx'))
        self.assertTrue(re.match('^x{3,4}?$', 'xxx'))
        self.assertIsNone(re.match('^x{}$', 'xxx'))
        self.assertTrue(re.match('^x{}$', 'x{}'))
        self.checkPatternError('x{2,1}',
            'min repeat greater than max repeat', 2)

    def test_getattr(self):
        self.assertEqual(re.compile('(?i)(a)(b)').pattern, '(?i)(a)(b)')
        self.assertEqual(re.compile('(?i)(a)(b)').flags, re.I | re.U)
        self.assertEqual(re.compile('(?i)(a)(b)').groups, 2)
        self.assertEqual(re.compile('(?i)(a)(b)').groupindex, {})
        self.assertEqual(re.compile('(?i)(?P<first>a)(?P<other>b)').
            groupindex, {'first': 1, 'other': 2})
        self.assertEqual(re.match('(a)', 'a').pos, 0)
        self.assertEqual(re.match('(a)', 'a').endpos, 1)
        self.assertEqual(re.match('(a)', 'a').string, 'a')
        self.assertEqual(re.match('(a)', 'a').regs, ((0, 1), (0, 1)))
        self.assertTrue(re.match('(a)', 'a').re)
        p = re.compile('(?i)(?P<first>a)(?P<other>b)')
        self.assertEqual(sorted(p.groupindex), ['first', 'other'])
        self.assertEqual(p.groupindex['other'], 2)
        with self.assertRaises(TypeError):
            p.groupindex['other'] = 0
        self.assertEqual(p.groupindex['other'], 2)

    def test_special_escapes(self):
        self.assertEqual(re.search('\\b(b.)\\b', 'abcd abc bcd bx').group(1
            ), 'bx')
        self.assertEqual(re.search('\\B(b.)\\B', 'abc bcd bc abxd').group(1
            ), 'bx')
        self.assertEqual(re.search('\\b(b.)\\b', 'abcd abc bcd bx', re.
            ASCII).group(1), 'bx')
        self.assertEqual(re.search('\\B(b.)\\B', 'abc bcd bc abxd', re.
            ASCII).group(1), 'bx')
        self.assertEqual(re.search('^abc$', '\nabc\n', re.M).group(0), 'abc')
        self.assertEqual(re.search('^\\Aabc\\Z$', 'abc', re.M).group(0), 'abc')
        self.assertIsNone(re.search('^\\Aabc\\Z$', '\nabc\n', re.M))
        self.assertEqual(re.search(b'\\b(b.)\\b', b'abcd abc bcd bx').group
            (1), b'bx')
        self.assertEqual(re.search(b'\\B(b.)\\B', b'abc bcd bc abxd').group
            (1), b'bx')
        self.assertEqual(re.search(b'\\b(b.)\\b', b'abcd abc bcd bx', re.
            LOCALE).group(1), b'bx')
        self.assertEqual(re.search(b'\\B(b.)\\B', b'abc bcd bc abxd', re.
            LOCALE).group(1), b'bx')
        self.assertEqual(re.search(b'^abc$', b'\nabc\n', re.M).group(0), b'abc'
            )
        self.assertEqual(re.search(b'^\\Aabc\\Z$', b'abc', re.M).group(0),
            b'abc')
        self.assertIsNone(re.search(b'^\\Aabc\\Z$', b'\nabc\n', re.M))
        self.assertEqual(re.search('\\d\\D\\w\\W\\s\\S', '1aa! a').group(0),
            '1aa! a')
        self.assertEqual(re.search(b'\\d\\D\\w\\W\\s\\S', b'1aa! a').group(
            0), b'1aa! a')
        self.assertEqual(re.search('\\d\\D\\w\\W\\s\\S', '1aa! a', re.ASCII
            ).group(0), '1aa! a')
        self.assertEqual(re.search(b'\\d\\D\\w\\W\\s\\S', b'1aa! a', re.
            LOCALE).group(0), b'1aa! a')

    def test_other_escapes(self):
        self.checkPatternError('\\', 'bad escape (end of pattern)', 0)
        self.assertEqual(re.match('\\(', '(').group(), '(')
        self.assertIsNone(re.match('\\(', ')'))
        self.assertEqual(re.match('\\\\', '\\').group(), '\\')
        self.assertEqual(re.match('[\\]]', ']').group(), ']')
        self.assertIsNone(re.match('[\\]]', '['))
        self.assertEqual(re.match('[a\\-c]', '-').group(), '-')
        self.assertIsNone(re.match('[a\\-c]', 'b'))
        self.assertEqual(re.match('[\\^a]+', 'a^').group(), 'a^')
        self.assertIsNone(re.match('[\\^a]+', 'b'))
        re.purge()
        for c in 'ceghijklmopqyzCEFGHIJKLMNOPQRTVXY':
            with self.subTest(c):
                self.assertRaises(re.error, re.compile, '\\%c' % c)
        for c in 'ceghijklmopqyzABCEFGHIJKLMNOPQRTVXYZ':
            with self.subTest(c):
                self.assertRaises(re.error, re.compile, '[\\%c]' % c)

    def test_string_boundaries(self):
        self.assertEqual(re.search('\\b(abc)\\b', 'abc').group(1), 'abc')
        self.assertTrue(re.match('\\b', 'abc'))
        self.assertTrue(re.search('\\B', 'abc'))
        self.assertFalse(re.match('\\B', 'abc'))
        self.assertIsNone(re.search('\\B', ''))
        self.assertIsNone(re.search('\\b', ''))
        self.assertEqual(len(re.findall('\\b', 'a')), 2)
        self.assertEqual(len(re.findall('\\B', 'a')), 0)
        self.assertEqual(len(re.findall('\\b', ' ')), 0)
        self.assertEqual(len(re.findall('\\b', '   ')), 0)
        self.assertEqual(len(re.findall('\\B', ' ')), 2)

    def test_bigcharset(self):
        self.assertEqual(re.match('([∢∣])', '∢').group(1), '∢')
        r = '[%s]' % ''.join(map(chr, range(256, 2 ** 16, 255)))
        self.assertEqual(re.match(r, '！').group(), '！')

    def test_big_codesize(self):
        r = re.compile('|'.join('%d' % x for x in range(10000)))
        self.assertTrue(r.match('1000'))
        self.assertTrue(r.match('9999'))

    def test_anyall(self):
        self.assertEqual(re.match('a.b', 'a\nb', re.DOTALL).group(0), 'a\nb')
        self.assertEqual(re.match('a.*b', 'a\n\nb', re.DOTALL).group(0),
            'a\n\nb')

    def test_lookahead(self):
        self.assertEqual(re.match('(a(?=\\s[^a]))', 'a b').group(1), 'a')
        self.assertEqual(re.match('(a(?=\\s[^a]*))', 'a b').group(1), 'a')
        self.assertEqual(re.match('(a(?=\\s[abc]))', 'a b').group(1), 'a')
        self.assertEqual(re.match('(a(?=\\s[abc]*))', 'a bc').group(1), 'a')
        self.assertEqual(re.match('(a)(?=\\s\\1)', 'a a').group(1), 'a')
        self.assertEqual(re.match('(a)(?=\\s\\1*)', 'a aa').group(1), 'a')
        self.assertEqual(re.match('(a)(?=\\s(abc|a))', 'a a').group(1), 'a')
        self.assertEqual(re.match('(a(?!\\s[^a]))', 'a a').group(1), 'a')
        self.assertEqual(re.match('(a(?!\\s[abc]))', 'a d').group(1), 'a')
        self.assertEqual(re.match('(a)(?!\\s\\1)', 'a b').group(1), 'a')
        self.assertEqual(re.match('(a)(?!\\s(abc|a))', 'a b').group(1), 'a')
        self.assertTrue(re.match('(a)b(?=\\1)a', 'aba'))
        self.assertIsNone(re.match('(a)b(?=\\1)c', 'abac'))
        self.assertTrue(re.match('(?:(a)|(x))b(?=(?(2)x|c))c', 'abc'))
        self.assertIsNone(re.match('(?:(a)|(x))b(?=(?(2)c|x))c', 'abc'))
        self.assertTrue(re.match('(?:(a)|(x))b(?=(?(2)x|c))c', 'abc'))
        self.assertIsNone(re.match('(?:(a)|(x))b(?=(?(1)b|x))c', 'abc'))
        self.assertTrue(re.match('(?:(a)|(x))b(?=(?(1)c|x))c', 'abc'))
        self.assertTrue(re.match('(a)b(?=(?(2)x|c))(c)', 'abc'))
        self.assertIsNone(re.match('(a)b(?=(?(2)b|x))(c)', 'abc'))
        self.assertTrue(re.match('(a)b(?=(?(1)c|x))(c)', 'abc'))

    def test_lookbehind(self):
        self.assertTrue(re.match('ab(?<=b)c', 'abc'))
        self.assertIsNone(re.match('ab(?<=c)c', 'abc'))
        self.assertIsNone(re.match('ab(?<!b)c', 'abc'))
        self.assertTrue(re.match('ab(?<!c)c', 'abc'))
        self.assertTrue(re.match('(a)a(?<=\\1)c', 'aac'))
        self.assertIsNone(re.match('(a)b(?<=\\1)a', 'abaa'))
        self.assertIsNone(re.match('(a)a(?<!\\1)c', 'aac'))
        self.assertTrue(re.match('(a)b(?<!\\1)a', 'abaa'))
        self.assertIsNone(re.match('(?:(a)|(x))b(?<=(?(2)x|c))c', 'abc'))
        self.assertIsNone(re.match('(?:(a)|(x))b(?<=(?(2)b|x))c', 'abc'))
        self.assertTrue(re.match('(?:(a)|(x))b(?<=(?(2)x|b))c', 'abc'))
        self.assertIsNone(re.match('(?:(a)|(x))b(?<=(?(1)c|x))c', 'abc'))
        self.assertTrue(re.match('(?:(a)|(x))b(?<=(?(1)b|x))c', 'abc'))
        self.assertRaises(re.error, re.compile, '(a)b(?<=(?(2)b|x))(c)')
        self.assertIsNone(re.match('(a)b(?<=(?(1)c|x))(c)', 'abc'))
        self.assertTrue(re.match('(a)b(?<=(?(1)b|x))(c)', 'abc'))
        self.assertRaises(re.error, re.compile, '(a)b(?<=(.)\\2)(c)')
        self.assertRaises(re.error, re.compile, '(a)b(?<=(?P<a>.)(?P=a))(c)')
        self.assertRaises(re.error, re.compile, '(a)b(?<=(a)(?(2)b|x))(c)')
        self.assertRaises(re.error, re.compile, '(a)b(?<=(.)(?<=\\2))(c)')

    def test_ignore_case(self):
        self.assertEqual(re.match('abc', 'ABC', re.I).group(0), 'ABC')
        self.assertEqual(re.match(b'abc', b'ABC', re.I).group(0), b'ABC')
        self.assertEqual(re.match('(a\\s[^a])', 'a b', re.I).group(1), 'a b')
        self.assertEqual(re.match('(a\\s[^a]*)', 'a bb', re.I).group(1), 'a bb'
            )
        self.assertEqual(re.match('(a\\s[abc])', 'a b', re.I).group(1), 'a b')
        self.assertEqual(re.match('(a\\s[abc]*)', 'a bb', re.I).group(1),
            'a bb')
        self.assertEqual(re.match('((a)\\s\\2)', 'a a', re.I).group(1), 'a a')
        self.assertEqual(re.match('((a)\\s\\2*)', 'a aa', re.I).group(1),
            'a aa')
        self.assertEqual(re.match('((a)\\s(abc|a))', 'a a', re.I).group(1),
            'a a')
        self.assertEqual(re.match('((a)\\s(abc|a)*)', 'a aa', re.I).group(1
            ), 'a aa')
        assert 'K'.lower() == 'k'
        self.assertTrue(re.match('K', 'K', re.I))
        self.assertTrue(re.match('k', 'K', re.I))
        self.assertTrue(re.match('\\u212a', 'K', re.I))
        self.assertTrue(re.match('\\u212a', 'k', re.I))
        assert 'ſ'.upper() == 'S'
        self.assertTrue(re.match('S', 'ſ', re.I))
        self.assertTrue(re.match('s', 'ſ', re.I))
        self.assertTrue(re.match('\\u017f', 'S', re.I))
        self.assertTrue(re.match('\\u017f', 's', re.I))
        assert 'ﬅ'.upper() == 'ﬆ'.upper() == 'ST'
        self.assertTrue(re.match('\\ufb05', 'ﬆ', re.I))
        self.assertTrue(re.match('\\ufb06', 'ﬅ', re.I))

    def test_ignore_case_set(self):
        self.assertTrue(re.match('[19A]', 'A', re.I))
        self.assertTrue(re.match('[19a]', 'a', re.I))
        self.assertTrue(re.match('[19a]', 'A', re.I))
        self.assertTrue(re.match('[19A]', 'a', re.I))
        self.assertTrue(re.match(b'[19A]', b'A', re.I))
        self.assertTrue(re.match(b'[19a]', b'a', re.I))
        self.assertTrue(re.match(b'[19a]', b'A', re.I))
        self.assertTrue(re.match(b'[19A]', b'a', re.I))
        assert 'K'.lower() == 'k'
        self.assertTrue(re.match('[19K]', 'K', re.I))
        self.assertTrue(re.match('[19k]', 'K', re.I))
        self.assertTrue(re.match('[19\\u212a]', 'K', re.I))
        self.assertTrue(re.match('[19\\u212a]', 'k', re.I))
        assert 'ſ'.upper() == 'S'
        self.assertTrue(re.match('[19S]', 'ſ', re.I))
        self.assertTrue(re.match('[19s]', 'ſ', re.I))
        self.assertTrue(re.match('[19\\u017f]', 'S', re.I))
        self.assertTrue(re.match('[19\\u017f]', 's', re.I))
        assert 'ﬅ'.upper() == 'ﬆ'.upper() == 'ST'
        self.assertTrue(re.match('[19\\ufb05]', 'ﬆ', re.I))
        self.assertTrue(re.match('[19\\ufb06]', 'ﬅ', re.I))

    def test_ignore_case_range(self):
        self.assertTrue(re.match('[9-a]', '_', re.I))
        self.assertIsNone(re.match('[9-A]', '_', re.I))
        self.assertTrue(re.match(b'[9-a]', b'_', re.I))
        self.assertIsNone(re.match(b'[9-A]', b'_', re.I))
        self.assertTrue(re.match('[\\xc0-\\xde]', '×', re.I))
        self.assertIsNone(re.match('[\\xc0-\\xde]', '÷', re.I))
        self.assertTrue(re.match('[\\xe0-\\xfe]', '÷', re.I))
        self.assertIsNone(re.match('[\\xe0-\\xfe]', '×', re.I))
        self.assertTrue(re.match('[\\u0430-\\u045f]', 'ѐ', re.I))
        self.assertTrue(re.match('[\\u0430-\\u045f]', 'Ѐ', re.I))
        self.assertTrue(re.match('[\\u0400-\\u042f]', 'ѐ', re.I))
        self.assertTrue(re.match('[\\u0400-\\u042f]', 'Ѐ', re.I))
        self.assertTrue(re.match('[\\U00010428-\\U0001044f]', '𐐨', re.I))
        self.assertTrue(re.match('[\\U00010428-\\U0001044f]', '𐐀', re.I))
        self.assertTrue(re.match('[\\U00010400-\\U00010427]', '𐐨', re.I))
        self.assertTrue(re.match('[\\U00010400-\\U00010427]', '𐐀', re.I))
        assert 'K'.lower() == 'k'
        self.assertTrue(re.match('[J-M]', 'K', re.I))
        self.assertTrue(re.match('[j-m]', 'K', re.I))
        self.assertTrue(re.match('[\\u2129-\\u212b]', 'K', re.I))
        self.assertTrue(re.match('[\\u2129-\\u212b]', 'k', re.I))
        assert 'ſ'.upper() == 'S'
        self.assertTrue(re.match('[R-T]', 'ſ', re.I))
        self.assertTrue(re.match('[r-t]', 'ſ', re.I))
        self.assertTrue(re.match('[\\u017e-\\u0180]', 'S', re.I))
        self.assertTrue(re.match('[\\u017e-\\u0180]', 's', re.I))
        assert 'ﬅ'.upper() == 'ﬆ'.upper() == 'ST'
        self.assertTrue(re.match('[\\ufb04-\\ufb05]', 'ﬆ', re.I))
        self.assertTrue(re.match('[\\ufb06-\\ufb07]', 'ﬅ', re.I))

    def test_category(self):
        self.assertEqual(re.match('(\\s)', ' ').group(1), ' ')

    def test_getlower(self):
        import _sre
        self.assertEqual(_sre.getlower(ord('A'), 0), ord('a'))
        self.assertEqual(_sre.getlower(ord('A'), re.LOCALE), ord('a'))
        self.assertEqual(_sre.getlower(ord('A'), re.UNICODE), ord('a'))
        self.assertEqual(_sre.getlower(ord('A'), re.ASCII), ord('a'))
        self.assertEqual(re.match('abc', 'ABC', re.I).group(0), 'ABC')
        self.assertEqual(re.match(b'abc', b'ABC', re.I).group(0), b'ABC')
        self.assertEqual(re.match('abc', 'ABC', re.I | re.A).group(0), 'ABC')
        self.assertEqual(re.match(b'abc', b'ABC', re.I | re.L).group(0), b'ABC'
            )

    def test_not_literal(self):
        self.assertEqual(re.search('\\s([^a])', ' b').group(1), 'b')
        self.assertEqual(re.search('\\s([^a]*)', ' bb').group(1), 'bb')

    def test_search_coverage(self):
        self.assertEqual(re.search('\\s(b)', ' b').group(1), 'b')
        self.assertEqual(re.search('a\\s', 'a ').group(0), 'a ')

    def assertMatch(self, pattern, text, match=None, span=None, matcher=re.
        match):
        if match is None and span is None:
            match = text
            span = 0, len(text)
        elif match is None or span is None:
            raise ValueError(
                'If match is not None, span should be specified (and vice versa).'
                )
        m = matcher(pattern, text)
        self.assertTrue(m)
        self.assertEqual(m.group(), match)
        self.assertEqual(m.span(), span)

    def test_re_escape(self):
        alnum_chars = string.ascii_letters + string.digits + '_'
        p = ''.join(chr(i) for i in range(256))
        for c in p:
            if c in alnum_chars:
                self.assertEqual(re.escape(c), c)
            elif c == '\x00':
                self.assertEqual(re.escape(c), '\\000')
            else:
                self.assertEqual(re.escape(c), '\\' + c)
            self.assertMatch(re.escape(c), c)
        self.assertMatch(re.escape(p), p)

    def test_re_escape_byte(self):
        alnum_chars = (string.ascii_letters + string.digits + '_').encode(
            'ascii')
        p = bytes(range(256))
        for i in p:
            b = bytes([i])
            if b in alnum_chars:
                self.assertEqual(re.escape(b), b)
            elif i == 0:
                self.assertEqual(re.escape(b), b'\\000')
            else:
                self.assertEqual(re.escape(b), b'\\' + b)
            self.assertMatch(re.escape(b), b)
        self.assertMatch(re.escape(p), p)

    def test_re_escape_non_ascii(self):
        s = 'xxx☠☠☠xxx'
        s_escaped = re.escape(s)
        self.assertEqual(s_escaped, 'xxx\\☠\\☠\\☠xxx')
        self.assertMatch(s_escaped, s)
        self.assertMatch('.%s+.' % re.escape('☠'), s, 'x☠☠☠x', (2, 7), re.
            search)

    def test_re_escape_non_ascii_bytes(self):
        b = 'y☠y☠y'.encode('utf-8')
        b_escaped = re.escape(b)
        self.assertEqual(b_escaped, b'y\\\xe2\\\x98\\\xa0y\\\xe2\\\x98\\\xa0y')
        self.assertMatch(b_escaped, b)
        res = re.findall(re.escape('☠'.encode('utf-8')), b)
        self.assertEqual(len(res), 2)

    def test_pickling(self):
        import pickle
        oldpat = re.compile('a(?:b|(c|e){1,2}?|d)+?(.)', re.UNICODE)
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            pickled = pickle.dumps(oldpat, proto)
            newpat = pickle.loads(pickled)
            self.assertEqual(newpat, oldpat)
        from re import _compile

    def test_constants(self):
        self.assertEqual(re.I, re.IGNORECASE)
        self.assertEqual(re.L, re.LOCALE)
        self.assertEqual(re.M, re.MULTILINE)
        self.assertEqual(re.S, re.DOTALL)
        self.assertEqual(re.X, re.VERBOSE)

    def test_flags(self):
        for flag in [re.I, re.M, re.X, re.S, re.A, re.U]:
            self.assertTrue(re.compile('^pattern$', flag))
        for flag in [re.I, re.M, re.X, re.S, re.A, re.L]:
            self.assertTrue(re.compile(b'^pattern$', flag))

    def test_sre_character_literals(self):
        for i in [0, 8, 16, 32, 64, 127, 128, 255, 256, 65535, 65536, 1114111]:
            if i < 256:
                self.assertTrue(re.match('\\%03o' % i, chr(i)))
                self.assertTrue(re.match('\\%03o0' % i, chr(i) + '0'))
                self.assertTrue(re.match('\\%03o8' % i, chr(i) + '8'))
                self.assertTrue(re.match('\\x%02x' % i, chr(i)))
                self.assertTrue(re.match('\\x%02x0' % i, chr(i) + '0'))
                self.assertTrue(re.match('\\x%02xz' % i, chr(i) + 'z'))
            if i < 65536:
                self.assertTrue(re.match('\\u%04x' % i, chr(i)))
                self.assertTrue(re.match('\\u%04x0' % i, chr(i) + '0'))
                self.assertTrue(re.match('\\u%04xz' % i, chr(i) + 'z'))
            self.assertTrue(re.match('\\U%08x' % i, chr(i)))
            self.assertTrue(re.match('\\U%08x0' % i, chr(i) + '0'))
            self.assertTrue(re.match('\\U%08xz' % i, chr(i) + 'z'))
        self.assertTrue(re.match('\\0', '\x00'))
        self.assertTrue(re.match('\\08', '\x008'))
        self.assertTrue(re.match('\\01', '\x01'))
        self.assertTrue(re.match('\\018', '\x018'))
        self.checkPatternError('\\567',
            'octal escape value \\567 outside of range 0-0o377', 0)
        self.checkPatternError('\\911', 'invalid group reference 91', 1)
        self.checkPatternError('\\x1', 'incomplete escape \\x1', 0)
        self.checkPatternError('\\x1z', 'incomplete escape \\x1', 0)
        self.checkPatternError('\\u123', 'incomplete escape \\u123', 0)
        self.checkPatternError('\\u123z', 'incomplete escape \\u123', 0)
        self.checkPatternError('\\U0001234', 'incomplete escape \\U0001234', 0)
        self.checkPatternError('\\U0001234z', 'incomplete escape \\U0001234', 0
            )
        self.checkPatternError('\\U00110000', 'bad escape \\U00110000', 0)

    def test_sre_character_class_literals(self):
        for i in [0, 8, 16, 32, 64, 127, 128, 255, 256, 65535, 65536, 1114111]:
            if i < 256:
                self.assertTrue(re.match('[\\%o]' % i, chr(i)))
                self.assertTrue(re.match('[\\%o8]' % i, chr(i)))
                self.assertTrue(re.match('[\\%03o]' % i, chr(i)))
                self.assertTrue(re.match('[\\%03o0]' % i, chr(i)))
                self.assertTrue(re.match('[\\%03o8]' % i, chr(i)))
                self.assertTrue(re.match('[\\x%02x]' % i, chr(i)))
                self.assertTrue(re.match('[\\x%02x0]' % i, chr(i)))
                self.assertTrue(re.match('[\\x%02xz]' % i, chr(i)))
            if i < 65536:
                self.assertTrue(re.match('[\\u%04x]' % i, chr(i)))
                self.assertTrue(re.match('[\\u%04x0]' % i, chr(i)))
                self.assertTrue(re.match('[\\u%04xz]' % i, chr(i)))
            self.assertTrue(re.match('[\\U%08x]' % i, chr(i)))
            self.assertTrue(re.match('[\\U%08x0]' % i, chr(i) + '0'))
            self.assertTrue(re.match('[\\U%08xz]' % i, chr(i) + 'z'))
        self.checkPatternError('[\\567]',
            'octal escape value \\567 outside of range 0-0o377', 1)
        self.checkPatternError('[\\911]', 'bad escape \\9', 1)
        self.checkPatternError('[\\x1z]', 'incomplete escape \\x1', 1)
        self.checkPatternError('[\\u123z]', 'incomplete escape \\u123', 1)
        self.checkPatternError('[\\U0001234z]',
            'incomplete escape \\U0001234', 1)
        self.checkPatternError('[\\U00110000]', 'bad escape \\U00110000', 1)
        self.assertTrue(re.match('[\\U0001d49c-\\U0001d4b5]', '𝒞'))

    def test_sre_byte_literals(self):
        for i in [0, 8, 16, 32, 64, 127, 128, 255]:
            self.assertTrue(re.match(('\\%03o' % i).encode(), bytes([i])))
            self.assertTrue(re.match(('\\%03o0' % i).encode(), bytes([i]) +
                b'0'))
            self.assertTrue(re.match(('\\%03o8' % i).encode(), bytes([i]) +
                b'8'))
            self.assertTrue(re.match(('\\x%02x' % i).encode(), bytes([i])))
            self.assertTrue(re.match(('\\x%02x0' % i).encode(), bytes([i]) +
                b'0'))
            self.assertTrue(re.match(('\\x%02xz' % i).encode(), bytes([i]) +
                b'z'))
        self.assertRaises(re.error, re.compile, b'\\u1234')
        self.assertRaises(re.error, re.compile, b'\\U00012345')
        self.assertTrue(re.match(b'\\0', b'\x00'))
        self.assertTrue(re.match(b'\\08', b'\x008'))
        self.assertTrue(re.match(b'\\01', b'\x01'))
        self.assertTrue(re.match(b'\\018', b'\x018'))
        self.checkPatternError(b'\\567',
            'octal escape value \\567 outside of range 0-0o377', 0)
        self.checkPatternError(b'\\911', 'invalid group reference 91', 1)
        self.checkPatternError(b'\\x1', 'incomplete escape \\x1', 0)
        self.checkPatternError(b'\\x1z', 'incomplete escape \\x1', 0)

    def test_sre_byte_class_literals(self):
        for i in [0, 8, 16, 32, 64, 127, 128, 255]:
            self.assertTrue(re.match(('[\\%o]' % i).encode(), bytes([i])))
            self.assertTrue(re.match(('[\\%o8]' % i).encode(), bytes([i])))
            self.assertTrue(re.match(('[\\%03o]' % i).encode(), bytes([i])))
            self.assertTrue(re.match(('[\\%03o0]' % i).encode(), bytes([i])))
            self.assertTrue(re.match(('[\\%03o8]' % i).encode(), bytes([i])))
            self.assertTrue(re.match(('[\\x%02x]' % i).encode(), bytes([i])))
            self.assertTrue(re.match(('[\\x%02x0]' % i).encode(), bytes([i])))
            self.assertTrue(re.match(('[\\x%02xz]' % i).encode(), bytes([i])))
        self.assertRaises(re.error, re.compile, b'[\\u1234]')
        self.assertRaises(re.error, re.compile, b'[\\U00012345]')
        self.checkPatternError(b'[\\567]',
            'octal escape value \\567 outside of range 0-0o377', 1)
        self.checkPatternError(b'[\\911]', 'bad escape \\9', 1)
        self.checkPatternError(b'[\\x1z]', 'incomplete escape \\x1', 1)

    def test_character_set_errors(self):
        self.checkPatternError('[', 'unterminated character set', 0)
        self.checkPatternError('[^', 'unterminated character set', 0)
        self.checkPatternError('[a', 'unterminated character set', 0)
        self.checkPatternError('[a-', 'unterminated character set', 0)
        self.checkPatternError('[\\w-b]', 'bad character range \\w-b', 1)
        self.checkPatternError('[a-\\w]', 'bad character range a-\\w', 1)
        self.checkPatternError('[b-a]', 'bad character range b-a', 1)

    def test_bug_113254(self):
        self.assertEqual(re.match('(a)|(b)', 'b').start(1), -1)
        self.assertEqual(re.match('(a)|(b)', 'b').end(1), -1)
        self.assertEqual(re.match('(a)|(b)', 'b').span(1), (-1, -1))

    def test_bug_527371(self):
        self.assertIsNone(re.match('(a)?a', 'a').lastindex)
        self.assertEqual(re.match('(a)(b)?b', 'ab').lastindex, 1)
        self.assertEqual(re.match('(?P<a>a)(?P<b>b)?b', 'ab').lastgroup, 'a')
        self.assertEqual(re.match('(?P<a>a(b))', 'ab').lastgroup, 'a')
        self.assertEqual(re.match('((a))', 'a').lastindex, 1)

    def test_bug_418626(self):
        self.assertEqual(re.match('.*?c', 10000 * 'ab' + 'cd').end(0), 20001)
        self.assertEqual(re.match('.*?cd', 5000 * 'ab' + 'c' + 5000 * 'ab' +
            'cde').end(0), 20003)
        self.assertEqual(re.match('.*?cd', 20000 * 'abc' + 'de').end(0), 60001)
        self.assertEqual(re.search('(a|b)*?c', 10000 * 'ab' + 'cd').end(0),
            20001)

    def test_bug_612074(self):
        pat = '[' + re.escape('‹') + ']'
        self.assertEqual(re.compile(pat) and 1, 1)

    def test_stack_overflow(self):
        self.assertEqual(re.match('(x)*', 50000 * 'x').group(1), 'x')
        self.assertEqual(re.match('(x)*y', 50000 * 'x' + 'y').group(1), 'x')
        self.assertEqual(re.match('(x)*?y', 50000 * 'x' + 'y').group(1), 'x')

    def test_nothing_to_repeat(self):
        for reps in ('*', '+', '?', '{1,2}'):
            for mod in ('', '?'):
                self.checkPatternError('%s%s' % (reps, mod),
                    'nothing to repeat', 0)
                self.checkPatternError('(?:%s%s)' % (reps, mod),
                    'nothing to repeat', 3)

    def test_multiple_repeat(self):
        for outer_reps in ('*', '+', '{1,2}'):
            for outer_mod in ('', '?'):
                outer_op = outer_reps + outer_mod
                for inner_reps in ('*', '+', '?', '{1,2}'):
                    for inner_mod in ('', '?'):
                        inner_op = inner_reps + inner_mod
                        self.checkPatternError('x%s%s' % (inner_op,
                            outer_op), 'multiple repeat', 1 + len(inner_op))

    def test_unlimited_zero_width_repeat(self):
        self.assertIsNone(re.match('(?:a?)*y', 'z'))
        self.assertIsNone(re.match('(?:a?)+y', 'z'))
        self.assertIsNone(re.match('(?:a?){2,}y', 'z'))
        self.assertIsNone(re.match('(?:a?)*?y', 'z'))
        self.assertIsNone(re.match('(?:a?)+?y', 'z'))
        self.assertIsNone(re.match('(?:a?){2,}?y', 'z'))

    def test_scanner(self):

        def s_ident(scanner, token):
            return token

        def s_operator(scanner, token):
            return 'op%s' % token

        def s_float(scanner, token):
            return float(token)

        def s_int(scanner, token):
            return int(token)
        scanner = Scanner([('[a-zA-Z_]\\w*', s_ident), ('\\d+\\.\\d*',
            s_float), ('\\d+', s_int), ('=|\\+|-|\\*|/', s_operator), (
            '\\s+', None)])
        self.assertTrue(scanner.scanner.scanner('').pattern)
        self.assertEqual(scanner.scan('sum = 3*foo + 312.50 + bar'), ([
            'sum', 'op=', 3, 'op*', 'foo', 'op+', 312.5, 'op+', 'bar'], ''))

    def test_bug_448951(self):
        for op in ('', '?', '*'):
            self.assertEqual(re.match('((.%s):)?z' % op, 'z').groups(), (
                None, None))
            self.assertEqual(re.match('((.%s):)?z' % op, 'a:z').groups(), (
                'a:', 'a'))

    def test_bug_725106(self):
        self.assertEqual(re.match('^((a)|b)*', 'abc').groups(), ('b', 'a'))
        self.assertEqual(re.match('^(([ab])|c)*', 'abc').groups(), ('c', 'b'))
        self.assertEqual(re.match('^((d)|[ab])*', 'abc').groups(), ('b', None))
        self.assertEqual(re.match('^((a)c|[ab])*', 'abc').groups(), ('b', None)
            )
        self.assertEqual(re.match('^((a)|b)*?c', 'abc').groups(), ('b', 'a'))
        self.assertEqual(re.match('^(([ab])|c)*?d', 'abcd').groups(), ('c',
            'b'))
        self.assertEqual(re.match('^((d)|[ab])*?c', 'abc').groups(), ('b',
            None))
        self.assertEqual(re.match('^((a)c|[ab])*?c', 'abc').groups(), ('b',
            None))

    def test_bug_725149(self):
        self.assertEqual(re.match('(a)(?:(?=(b)*)c)*', 'abb').groups(), (
            'a', None))
        self.assertEqual(re.match('(a)((?!(b)*))*', 'abb').groups(), ('a',
            None, None))

    def test_bug_764548(self):


        class my_unicode(str):
            pass
        pat = re.compile(my_unicode('abc'))
        self.assertIsNone(pat.match('xyz'))

    def test_finditer(self):
        iter = re.finditer(':+', 'a:b::c:::d')
        self.assertEqual([item.group(0) for item in iter], [':', '::', ':::'])
        pat = re.compile(':+')
        iter = pat.finditer('a:b::c:::d', 1, 10)
        self.assertEqual([item.group(0) for item in iter], [':', '::', ':::'])
        pat = re.compile(':+')
        iter = pat.finditer('a:b::c:::d', pos=1, endpos=10)
        self.assertEqual([item.group(0) for item in iter], [':', '::', ':::'])
        pat = re.compile(':+')
        iter = pat.finditer('a:b::c:::d', endpos=10, pos=1)
        self.assertEqual([item.group(0) for item in iter], [':', '::', ':::'])
        pat = re.compile(':+')
        iter = pat.finditer('a:b::c:::d', pos=3, endpos=8)
        self.assertEqual([item.group(0) for item in iter], ['::', '::'])

    def test_bug_926075(self):
        self.assertIsNot(re.compile('bug_926075'), re.compile(b'bug_926075'))

    def test_bug_931848(self):
        pattern = '[.。．｡]'
        self.assertEqual(re.compile(pattern).split('a.b.c'), ['a', 'b', 'c'])

    def test_bug_581080(self):
        iter = re.finditer('\\s', 'a b')
        self.assertEqual(next(iter).span(), (1, 2))
        self.assertRaises(StopIteration, next, iter)
        scanner = re.compile('\\s').scanner('a b')
        self.assertEqual(scanner.search().span(), (1, 2))
        self.assertIsNone(scanner.search())

    def test_bug_817234(self):
        iter = re.finditer('.*', 'asdf')
        self.assertEqual(next(iter).span(), (0, 4))
        self.assertEqual(next(iter).span(), (4, 4))
        self.assertRaises(StopIteration, next, iter)

    def test_bug_6561(self):
        decimal_digits = ['7', '๘', '０']
        for x in decimal_digits:
            self.assertEqual(re.match('^\\d$', x).group(0), x)
        not_decimal_digits = ['Ⅵ', '〹', '₂', '㊴']
        for x in not_decimal_digits:
            self.assertIsNone(re.match('^\\d$', x))

    def test_empty_array(self):
        import array
        for typecode in 'bBuhHiIlLfd':
            a = array.array(typecode)
            self.assertIsNone(re.compile(b'bla').match(a))
            self.assertEqual(re.compile(b'').match(a).groups(), ())

    def test_inline_flags(self):
        upper_char = 'Ạ'
        lower_char = 'ạ'
        p = re.compile('.' + upper_char, re.I | re.S)
        q = p.match('\n' + lower_char)
        self.assertTrue(q)
        p = re.compile('.' + lower_char, re.I | re.S)
        q = p.match('\n' + upper_char)
        self.assertTrue(q)
        p = re.compile('(?i).' + upper_char, re.S)
        q = p.match('\n' + lower_char)
        self.assertTrue(q)
        p = re.compile('(?i).' + lower_char, re.S)
        q = p.match('\n' + upper_char)
        self.assertTrue(q)
        p = re.compile('(?is).' + upper_char)
        q = p.match('\n' + lower_char)
        self.assertTrue(q)
        p = re.compile('(?is).' + lower_char)
        q = p.match('\n' + upper_char)
        self.assertTrue(q)
        p = re.compile('(?s)(?i).' + upper_char)
        q = p.match('\n' + lower_char)
        self.assertTrue(q)
        p = re.compile('(?s)(?i).' + lower_char)
        q = p.match('\n' + upper_char)
        self.assertTrue(q)
        self.assertTrue(re.match('(?ix) ' + upper_char, lower_char))
        self.assertTrue(re.match('(?ix) ' + lower_char, upper_char))
        self.assertTrue(re.match(' (?i) ' + upper_char, lower_char, re.X))
        self.assertTrue(re.match('(?x) (?i) ' + upper_char, lower_char))
        self.assertTrue(re.match(' (?x) (?i) ' + upper_char, lower_char, re.X))
        p = upper_char + '(?i)'
        with self.assertWarns(DeprecationWarning) as warns:
            self.assertTrue(re.match(p, lower_char))
        self.assertEqual(str(warns.warnings[0].message), 
            'Flags not at the start of the expression %r' % p)
        self.assertEqual(warns.warnings[0].filename, __file__)
        p = upper_char + '(?i)%s' % ('.?' * 100)
        with self.assertWarns(DeprecationWarning) as warns:
            self.assertTrue(re.match(p, lower_char))
        self.assertEqual(str(warns.warnings[0].message), 
            'Flags not at the start of the expression %r (truncated)' % p[:20])
        self.assertEqual(warns.warnings[0].filename, __file__)
        with warnings.catch_warnings():
            warnings.simplefilter('error', BytesWarning)
            p = b'A(?i)'
            with self.assertWarns(DeprecationWarning) as warns:
                self.assertTrue(re.match(p, b'a'))
            self.assertEqual(str(warns.warnings[0].message), 
                'Flags not at the start of the expression %r' % p)
            self.assertEqual(warns.warnings[0].filename, __file__)
        with self.assertWarns(DeprecationWarning):
            self.assertTrue(re.match('(?s).(?i)' + upper_char, '\n' +
                lower_char))
        with self.assertWarns(DeprecationWarning):
            self.assertTrue(re.match('(?i) ' + upper_char + ' (?x)',
                lower_char))
        with self.assertWarns(DeprecationWarning):
            self.assertTrue(re.match(' (?x) (?i) ' + upper_char, lower_char))
        with self.assertWarns(DeprecationWarning):
            self.assertTrue(re.match('^(?i)' + upper_char, lower_char))
        with self.assertWarns(DeprecationWarning):
            self.assertTrue(re.match('$|(?i)' + upper_char, lower_char))
        with self.assertWarns(DeprecationWarning) as warns:
            self.assertTrue(re.match('(?:(?i)' + upper_char + ')', lower_char))
        self.assertRegex(str(warns.warnings[0].message),
            'Flags not at the start')
        self.assertEqual(warns.warnings[0].filename, __file__)
        with self.assertWarns(DeprecationWarning) as warns:
            self.assertTrue(re.fullmatch('(^)?(?(1)(?i)' + upper_char + ')',
                lower_char))
        self.assertRegex(str(warns.warnings[0].message),
            'Flags not at the start')
        self.assertEqual(warns.warnings[0].filename, __file__)
        with self.assertWarns(DeprecationWarning) as warns:
            self.assertTrue(re.fullmatch('($)?(?(1)|(?i)' + upper_char +
                ')', lower_char))
        self.assertRegex(str(warns.warnings[0].message),
            'Flags not at the start')
        self.assertEqual(warns.warnings[0].filename, __file__)

    def test_dollar_matches_twice(self):
        """$ matches the end of string, and just before the terminating 
"""
        pattern = re.compile('$')
        self.assertEqual(pattern.sub('#', 'a\nb\n'), 'a\nb#\n#')
        self.assertEqual(pattern.sub('#', 'a\nb\nc'), 'a\nb\nc#')
        self.assertEqual(pattern.sub('#', '\n'), '#\n#')
        pattern = re.compile('$', re.MULTILINE)
        self.assertEqual(pattern.sub('#', 'a\nb\n'), 'a#\nb#\n#')
        self.assertEqual(pattern.sub('#', 'a\nb\nc'), 'a#\nb#\nc#')
        self.assertEqual(pattern.sub('#', '\n'), '#\n#')

    def test_bytes_str_mixing(self):
        pat = re.compile('.')
        bpat = re.compile(b'.')
        self.assertRaises(TypeError, pat.match, b'b')
        self.assertRaises(TypeError, bpat.match, 'b')
        self.assertRaises(TypeError, pat.sub, b'b', 'c')
        self.assertRaises(TypeError, pat.sub, 'b', b'c')
        self.assertRaises(TypeError, pat.sub, b'b', b'c')
        self.assertRaises(TypeError, bpat.sub, b'b', 'c')
        self.assertRaises(TypeError, bpat.sub, 'b', b'c')
        self.assertRaises(TypeError, bpat.sub, 'b', 'c')

    def test_ascii_and_unicode_flag(self):
        for flags in (0, re.UNICODE):
            pat = re.compile('À', flags | re.IGNORECASE)
            self.assertTrue(pat.match('à'))
            pat = re.compile('\\w', flags)
            self.assertTrue(pat.match('à'))
        pat = re.compile('À', re.ASCII | re.IGNORECASE)
        self.assertIsNone(pat.match('à'))
        pat = re.compile('(?a)À', re.IGNORECASE)
        self.assertIsNone(pat.match('à'))
        pat = re.compile('\\w', re.ASCII)
        self.assertIsNone(pat.match('à'))
        pat = re.compile('(?a)\\w')
        self.assertIsNone(pat.match('à'))
        for flags in (0, re.ASCII):
            pat = re.compile(b'\xc0', flags | re.IGNORECASE)
            self.assertIsNone(pat.match(b'\xe0'))
            pat = re.compile(b'\\w', flags)
            self.assertIsNone(pat.match(b'\xe0'))
        self.assertRaises(ValueError, re.compile, b'\\w', re.UNICODE)
        self.assertRaises(ValueError, re.compile, b'(?u)\\w')
        self.assertRaises(ValueError, re.compile, '\\w', re.UNICODE | re.ASCII)
        self.assertRaises(ValueError, re.compile, '(?u)\\w', re.ASCII)
        self.assertRaises(ValueError, re.compile, '(?a)\\w', re.UNICODE)
        self.assertRaises(ValueError, re.compile, '(?au)\\w')

    def test_locale_flag(self):
        import locale
        _, enc = locale.getlocale(locale.LC_CTYPE)
        for i in range(128, 256):
            try:
                c = bytes([i]).decode(enc)
                sletter = c.lower()
                if sletter == c:
                    continue
                bletter = sletter.encode(enc)
                if len(bletter) != 1:
                    continue
                if bletter.decode(enc) != sletter:
                    continue
                bpat = re.escape(bytes([i]))
                break
            except (UnicodeError, TypeError):
                pass
        else:
            bletter = None
            bpat = b'A'
        pat = re.compile(bpat, re.LOCALE | re.IGNORECASE)
        if bletter:
            self.assertTrue(pat.match(bletter))
        pat = re.compile(b'(?L)' + bpat, re.IGNORECASE)
        if bletter:
            self.assertTrue(pat.match(bletter))
        pat = re.compile(bpat, re.IGNORECASE)
        if bletter:
            self.assertIsNone(pat.match(bletter))
        pat = re.compile(b'\\w', re.LOCALE)
        if bletter:
            self.assertTrue(pat.match(bletter))
        pat = re.compile(b'(?L)\\w')
        if bletter:
            self.assertTrue(pat.match(bletter))
        pat = re.compile(b'\\w')
        if bletter:
            self.assertIsNone(pat.match(bletter))
        self.assertRaises(ValueError, re.compile, '', re.LOCALE)
        self.assertRaises(ValueError, re.compile, '(?L)')
        self.assertRaises(ValueError, re.compile, b'', re.LOCALE | re.ASCII)
        self.assertRaises(ValueError, re.compile, b'(?L)', re.ASCII)
        self.assertRaises(ValueError, re.compile, b'(?a)', re.LOCALE)
        self.assertRaises(ValueError, re.compile, b'(?aL)')

    def test_scoped_flags(self):
        self.assertTrue(re.match('(?i:a)b', 'Ab'))
        self.assertIsNone(re.match('(?i:a)b', 'aB'))
        self.assertIsNone(re.match('(?-i:a)b', 'Ab', re.IGNORECASE))
        self.assertTrue(re.match('(?-i:a)b', 'aB', re.IGNORECASE))
        self.assertIsNone(re.match('(?i:(?-i:a)b)', 'Ab'))
        self.assertTrue(re.match('(?i:(?-i:a)b)', 'aB'))
        self.assertTrue(re.match('(?x: a) b', 'a b'))
        self.assertIsNone(re.match('(?x: a) b', ' a b'))
        self.assertTrue(re.match('(?-x: a) b', ' ab', re.VERBOSE))
        self.assertIsNone(re.match('(?-x: a) b', 'ab', re.VERBOSE))
        self.checkPatternError('(?a:\\w)',
            'bad inline flags: cannot turn on global flag', 3)
        self.checkPatternError('(?a)(?-a:\\w)',
            'bad inline flags: cannot turn off global flag', 8)
        self.checkPatternError('(?i-i:a)',
            'bad inline flags: flag turned on and off', 5)
        self.checkPatternError('(?-', 'missing flag', 3)
        self.checkPatternError('(?-+', 'missing flag', 3)
        self.checkPatternError('(?-z', 'unknown flag', 3)
        self.checkPatternError('(?-i', 'missing :', 4)
        self.checkPatternError('(?-i)', 'missing :', 4)
        self.checkPatternError('(?-i+', 'missing :', 4)
        self.checkPatternError('(?-iz', 'unknown flag', 4)
        self.checkPatternError('(?i:', 'missing ), unterminated subpattern', 0)
        self.checkPatternError('(?i', 'missing -, : or )', 3)
        self.checkPatternError('(?i+', 'missing -, : or )', 3)
        self.checkPatternError('(?iz', 'unknown flag', 3)

    def test_bug_6509(self):
        pat = re.compile('a(\\w)')
        self.assertEqual(pat.sub('b\\1', 'ac'), 'bc')
        pat = re.compile('a(.)')
        self.assertEqual(pat.sub('b\\1', 'aሴ'), 'bሴ')
        pat = re.compile('..')
        self.assertEqual(pat.sub(lambda m: 'str', 'a5'), 'str')
        pat = re.compile(b'a(\\w)')
        self.assertEqual(pat.sub(b'b\\1', b'ac'), b'bc')
        pat = re.compile(b'a(.)')
        self.assertEqual(pat.sub(b'b\\1', b'a\xcd'), b'b\xcd')
        pat = re.compile(b'..')
        self.assertEqual(pat.sub(lambda m: b'bytes', b'a5'), b'bytes')

    def test_dealloc(self):
        import _sre
        long_overflow = 2 ** 128
        self.assertRaises(TypeError, re.finditer, 'a', {})
        with self.assertRaises(OverflowError):
            _sre.compile('abc', 0, [long_overflow], 0, [], [])
        with self.assertRaises(TypeError):
            _sre.compile({}, 0, [], 0, [], [])

    def test_search_dot_unicode(self):
        self.assertTrue(re.search('123.*-', '123abc-'))
        self.assertTrue(re.search('123.*-', '123é-'))
        self.assertTrue(re.search('123.*-', '123€-'))
        self.assertTrue(re.search('123.*-', '123\U0010ffff-'))
        self.assertTrue(re.search('123.*-', '123é€\U0010ffff-'))

    def test_compile(self):
        pattern = re.compile('random pattern')
        self.assertIsInstance(pattern, re._pattern_type)
        same_pattern = re.compile(pattern)
        self.assertIsInstance(same_pattern, re._pattern_type)
        self.assertIs(same_pattern, pattern)
        self.assertRaises(TypeError, re.compile, 0)

    @bigmemtest(size=_2G, memuse=1)
    def test_large_search(self, size):
        s = 'a' * size
        m = re.search('$', s)
        self.assertIsNotNone(m)
        self.assertEqual(m.start(), size)
        self.assertEqual(m.end(), size)

    @bigmemtest(size=_2G, memuse=16 + 2)
    def test_large_subn(self, size):
        s = 'a' * size
        r, n = re.subn('', '', s)
        self.assertEqual(r, s)
        self.assertEqual(n, size + 1)

    def test_bug_16688(self):
        self.assertEqual(re.findall('(?i)(a)\\1', 'aa Ā'), ['a'])
        self.assertEqual(re.match('(?s).{1,3}', 'ĀĀ').span(), (0, 2))

    def test_repeat_minmax_overflow(self):
        string = 'x' * 100000
        self.assertEqual(re.match('.{65535}', string).span(), (0, 65535))
        self.assertEqual(re.match('.{,65535}', string).span(), (0, 65535))
        self.assertEqual(re.match('.{65535,}?', string).span(), (0, 65535))
        self.assertEqual(re.match('.{65536}', string).span(), (0, 65536))
        self.assertEqual(re.match('.{,65536}', string).span(), (0, 65536))
        self.assertEqual(re.match('.{65536,}?', string).span(), (0, 65536))
        self.assertRaises(OverflowError, re.compile, '.{%d}' % 2 ** 128)
        self.assertRaises(OverflowError, re.compile, '.{,%d}' % 2 ** 128)
        self.assertRaises(OverflowError, re.compile, '.{%d,}?' % 2 ** 128)
        self.assertRaises(OverflowError, re.compile, '.{%d,%d}' % (2 ** 129,
            2 ** 128))

    @cpython_only
    def test_repeat_minmax_overflow_maxrepeat(self):
        try:
            from _sre import MAXREPEAT
        except ImportError:
            self.skipTest('requires _sre.MAXREPEAT constant')
        string = 'x' * 100000
        self.assertIsNone(re.match('.{%d}' % (MAXREPEAT - 1), string))
        self.assertEqual(re.match('.{,%d}' % (MAXREPEAT - 1), string).span(
            ), (0, 100000))
        self.assertIsNone(re.match('.{%d,}?' % (MAXREPEAT - 1), string))
        self.assertRaises(OverflowError, re.compile, '.{%d}' % MAXREPEAT)
        self.assertRaises(OverflowError, re.compile, '.{,%d}' % MAXREPEAT)
        self.assertRaises(OverflowError, re.compile, '.{%d,}?' % MAXREPEAT)

    def test_backref_group_name_in_exception(self):
        self.checkPatternError('(?P=<foo>)',
            "bad character in group name '<foo>'", 4)

    def test_group_name_in_exception(self):
        self.checkPatternError('(?P<?foo>)',
            "bad character in group name '?foo'", 4)

    def test_issue17998(self):
        for reps in ('*', '+', '?', '{1}'):
            for mod in ('', '?'):
                pattern = '.' + reps + mod + 'yz'
                self.assertEqual(re.compile(pattern, re.S).findall('xyz'),
                    ['xyz'], msg=pattern)
                pattern = pattern.encode()
                self.assertEqual(re.compile(pattern, re.S).findall(b'xyz'),
                    [b'xyz'], msg=pattern)

    def test_match_repr(self):
        for string in ('[abracadabra]', S('[abracadabra]')):
            m = re.search('(.+)(.*?)\\1', string)
            self.assertEqual(repr(m), 
                "<%s.%s object; span=(1, 12), match='abracadabra'>" % (type
                (m).__module__, type(m).__qualname__))
        for string in (b'[abracadabra]', B(b'[abracadabra]'), bytearray(
            b'[abracadabra]'), memoryview(b'[abracadabra]')):
            m = re.search(b'(.+)(.*?)\\1', string)
            self.assertEqual(repr(m), 
                "<%s.%s object; span=(1, 12), match=b'abracadabra'>" % (
                type(m).__module__, type(m).__qualname__))
        first, second = list(re.finditer('(aa)|(bb)', 'aa bb'))
        self.assertEqual(repr(first), 
            "<%s.%s object; span=(0, 2), match='aa'>" % (type(second).
            __module__, type(first).__qualname__))
        self.assertEqual(repr(second), 
            "<%s.%s object; span=(3, 5), match='bb'>" % (type(second).
            __module__, type(second).__qualname__))

    def test_bug_2537(self):
        for outer_op in ('{0,}', '*', '+', '{1,187}'):
            for inner_op in ('{0,}', '*', '?'):
                r = re.compile('^((x|y)%s)%s' % (inner_op, outer_op))
                m = r.match('xyyzy')
                self.assertEqual(m.group(0), 'xyy')
                self.assertEqual(m.group(1), '')
                self.assertEqual(m.group(2), 'y')

    def test_debug_flag(self):
        pat = '(\\.)(?:[ch]|py)(?(1)$|: )'
        with captured_stdout() as out:
            re.compile(pat, re.DEBUG)
        dump = """SUBPATTERN 1 0 0
  LITERAL 46
SUBPATTERN None 0 0
  BRANCH
    IN
      LITERAL 99
      LITERAL 104
  OR
    LITERAL 112
    LITERAL 121
SUBPATTERN None 0 0
  GROUPREF_EXISTS 1
    AT AT_END
  ELSE
    LITERAL 58
    LITERAL 32
"""
        self.assertEqual(out.getvalue(), dump)
        with captured_stdout() as out:
            re.compile(pat, re.DEBUG)
        self.assertEqual(out.getvalue(), dump)

    def test_keyword_parameters(self):
        pat = re.compile('(ab)')
        self.assertEqual(pat.match(string='abracadabra', pos=7, endpos=10).
            span(), (7, 9))
        self.assertEqual(pat.fullmatch(string='abracadabra', pos=7, endpos=
            9).span(), (7, 9))
        self.assertEqual(pat.search(string='abracadabra', pos=3, endpos=10)
            .span(), (7, 9))
        self.assertEqual(pat.findall(string='abracadabra', pos=3, endpos=10
            ), ['ab'])
        self.assertEqual(pat.split(string='abracadabra', maxsplit=1), ['',
            'ab', 'racadabra'])
        self.assertEqual(pat.scanner(string='abracadabra', pos=3, endpos=10
            ).search().span(), (7, 9))

    def test_bug_20998(self):
        self.assertEqual(re.fullmatch('[a-c]+', 'ABC', re.I).span(), (0, 3))

    def test_locale_caching(self):
        oldlocale = locale.setlocale(locale.LC_CTYPE)
        self.addCleanup(locale.setlocale, locale.LC_CTYPE, oldlocale)
        for loc in ('en_US.iso88591', 'en_US.utf8'):
            try:
                locale.setlocale(locale.LC_CTYPE, loc)
            except locale.Error:
                self.skipTest('test needs %s locale' % loc)
        re.purge()
        self.check_en_US_iso88591()
        self.check_en_US_utf8()
        re.purge()
        self.check_en_US_utf8()
        self.check_en_US_iso88591()

    def check_en_US_iso88591(self):
        locale.setlocale(locale.LC_CTYPE, 'en_US.iso88591')
        self.assertTrue(re.match(b'\xc5\xe5', b'\xc5\xe5', re.L | re.I))
        self.assertTrue(re.match(b'\xc5', b'\xe5', re.L | re.I))
        self.assertTrue(re.match(b'\xe5', b'\xc5', re.L | re.I))
        self.assertTrue(re.match(b'(?Li)\xc5\xe5', b'\xc5\xe5'))
        self.assertTrue(re.match(b'(?Li)\xc5', b'\xe5'))
        self.assertTrue(re.match(b'(?Li)\xe5', b'\xc5'))

    def check_en_US_utf8(self):
        locale.setlocale(locale.LC_CTYPE, 'en_US.utf8')
        self.assertTrue(re.match(b'\xc5\xe5', b'\xc5\xe5', re.L | re.I))
        self.assertIsNone(re.match(b'\xc5', b'\xe5', re.L | re.I))
        self.assertIsNone(re.match(b'\xe5', b'\xc5', re.L | re.I))
        self.assertTrue(re.match(b'(?Li)\xc5\xe5', b'\xc5\xe5'))
        self.assertIsNone(re.match(b'(?Li)\xc5', b'\xe5'))
        self.assertIsNone(re.match(b'(?Li)\xe5', b'\xc5'))

    def test_error(self):
        with self.assertRaises(re.error) as cm:
            re.compile('(€))')
        err = cm.exception
        self.assertIsInstance(err.pattern, str)
        self.assertEqual(err.pattern, '(€))')
        self.assertEqual(err.pos, 3)
        self.assertEqual(err.lineno, 1)
        self.assertEqual(err.colno, 4)
        self.assertIn(err.msg, str(err))
        self.assertIn(' at position 3', str(err))
        self.assertNotIn(' at position 3', err.msg)
        with self.assertRaises(re.error) as cm:
            re.compile(b'(\xa4))')
        err = cm.exception
        self.assertIsInstance(err.pattern, bytes)
        self.assertEqual(err.pattern, b'(\xa4))')
        self.assertEqual(err.pos, 3)
        with self.assertRaises(re.error) as cm:
            re.compile(
                """
                (
                    abc
                )
                )
                (
                """
                , re.VERBOSE)
        err = cm.exception
        self.assertEqual(err.pos, 77)
        self.assertEqual(err.lineno, 5)
        self.assertEqual(err.colno, 17)
        self.assertIn(err.msg, str(err))
        self.assertIn(' at position 77', str(err))
        self.assertIn('(line 5, column 17)', str(err))

    def test_misc_errors(self):
        self.checkPatternError('(', 'missing ), unterminated subpattern', 0)
        self.checkPatternError('((a|b)',
            'missing ), unterminated subpattern', 0)
        self.checkPatternError('(a|b))', 'unbalanced parenthesis', 5)
        self.checkPatternError('(?P', 'unexpected end of pattern', 3)
        self.checkPatternError('(?z)', 'unknown extension ?z', 1)
        self.checkPatternError('(?iz)', 'unknown flag', 3)
        self.checkPatternError('(?i', 'missing -, : or )', 3)
        self.checkPatternError('(?#abc', 'missing ), unterminated comment', 0)
        self.checkPatternError('(?<', 'unexpected end of pattern', 3)
        self.checkPatternError('(?<>)', 'unknown extension ?<>', 1)
        self.checkPatternError('(?', 'unexpected end of pattern', 2)

    def test_enum(self):
        self.assertIn('ASCII', str(re.A))
        self.assertIn('DOTALL', str(re.S))

    def test_pattern_compare(self):
        pattern1 = re.compile('abc', re.IGNORECASE)
        self.assertEqual(pattern1, pattern1)
        self.assertFalse(pattern1 != pattern1)
        re.purge()
        pattern2 = re.compile('abc', re.IGNORECASE)
        self.assertEqual(hash(pattern2), hash(pattern1))
        self.assertEqual(pattern2, pattern1)
        re.purge()
        pattern3 = re.compile('XYZ', re.IGNORECASE)
        self.assertNotEqual(pattern3, pattern1)
        re.purge()
        pattern4 = re.compile('abc')
        self.assertNotEqual(pattern4, pattern1)
        with self.assertRaises(TypeError):
            pattern1 < pattern2

    def test_pattern_compare_bytes(self):
        pattern1 = re.compile(b'abc')
        re.purge()
        pattern2 = re.compile(b'abc')
        self.assertEqual(hash(pattern2), hash(pattern1))
        self.assertEqual(pattern2, pattern1)
        re.purge()
        pattern3 = re.compile('abc')
        with warnings.catch_warnings():
            warnings.simplefilter('error', BytesWarning)
            self.assertNotEqual(pattern3, pattern1)

    def test_bug_29444(self):
        s = bytearray(b'abcdefgh')
        m = re.search(b'[a-h]+', s)
        m2 = re.search(b'[e-h]+', s)
        self.assertEqual(m.group(), b'abcdefgh')
        self.assertEqual(m2.group(), b'efgh')
        s[:] = b'xyz'
        self.assertEqual(m.group(), b'xyz')
        self.assertEqual(m2.group(), b'')


class PatternReprTests(unittest.TestCase):

    def check(self, pattern, expected):
        self.assertEqual(repr(re.compile(pattern)), expected)

    def check_flags(self, pattern, flags, expected):
        self.assertEqual(repr(re.compile(pattern, flags)), expected)

    def test_without_flags(self):
        self.check('random pattern', "re.compile('random pattern')")

    def test_single_flag(self):
        self.check_flags('random pattern', re.IGNORECASE,
            "re.compile('random pattern', re.IGNORECASE)")

    def test_multiple_flags(self):
        self.check_flags('random pattern', re.I | re.S | re.X,
            "re.compile('random pattern', re.IGNORECASE|re.DOTALL|re.VERBOSE)")

    def test_unicode_flag(self):
        self.check_flags('random pattern', re.U, "re.compile('random pattern')"
            )
        self.check_flags('random pattern', re.I | re.S | re.U,
            "re.compile('random pattern', re.IGNORECASE|re.DOTALL)")

    def test_inline_flags(self):
        self.check('(?i)pattern', "re.compile('(?i)pattern', re.IGNORECASE)")

    def test_unknown_flags(self):
        self.check_flags('random pattern', 1191936,
            "re.compile('random pattern', 0x123000)")
        self.check_flags('random pattern', 1191936 | re.I,
            "re.compile('random pattern', re.IGNORECASE|0x123000)")

    def test_bytes(self):
        self.check(b'bytes pattern', "re.compile(b'bytes pattern')")
        self.check_flags(b'bytes pattern', re.A,
            "re.compile(b'bytes pattern', re.ASCII)")

    def test_locale(self):
        self.check_flags(b'bytes pattern', re.L,
            "re.compile(b'bytes pattern', re.LOCALE)")

    def test_quotes(self):
        self.check('random "double quoted" pattern',
            're.compile(\'random "double quoted" pattern\')')
        self.check("random 'single quoted' pattern",
            're.compile("random \'single quoted\' pattern")')
        self.check('both \'single\' and "double" quotes',
            're.compile(\'both \\\'single\\\' and "double" quotes\')')

    def test_long_pattern(self):
        pattern = 'Very %spattern' % ('long ' * 1000)
        r = repr(re.compile(pattern))
        self.assertLess(len(r), 300)
        self.assertEqual(r[:30], "re.compile('Very long long lon")
        r = repr(re.compile(pattern, re.I))
        self.assertLess(len(r), 300)
        self.assertEqual(r[:30], "re.compile('Very long long lon")
        self.assertEqual(r[-16:], ', re.IGNORECASE)')


class ImplementationTest(unittest.TestCase):
    """
    Test implementation details of the re module.
    """

    def test_overlap_table(self):
        f = sre_compile._generate_overlap_table
        self.assertEqual(f(''), [])
        self.assertEqual(f('a'), [0])
        self.assertEqual(f('abcd'), [0, 0, 0, 0])
        self.assertEqual(f('aaaa'), [0, 1, 2, 3])
        self.assertEqual(f('ababba'), [0, 0, 1, 2, 0, 1])
        self.assertEqual(f('abcabdac'), [0, 0, 0, 1, 2, 0, 1, 0])


class ExternalTests(unittest.TestCase):

    def test_re_benchmarks(self):
        """re_tests benchmarks"""
        from test.re_tests import benchmarks
        for pattern, s in benchmarks:
            with self.subTest(pattern=pattern, string=s):
                p = re.compile(pattern)
                self.assertTrue(p.search(s))
                self.assertTrue(p.match(s))
                self.assertTrue(p.fullmatch(s))
                s2 = ' ' * 10000 + s + ' ' * 10000
                self.assertTrue(p.search(s2))
                self.assertTrue(p.match(s2, 10000))
                self.assertTrue(p.match(s2, 10000, 10000 + len(s)))
                self.assertTrue(p.fullmatch(s2, 10000, 10000 + len(s)))

    def test_re_tests(self):
        """re_tests test suite"""
        from test.re_tests import tests, SUCCEED, FAIL, SYNTAX_ERROR
        for t in tests:
            pattern = s = outcome = repl = expected = None
            if len(t) == 5:
                pattern, s, outcome, repl, expected = t
            elif len(t) == 3:
                pattern, s, outcome = t
            else:
                raise ValueError('Test tuples should have 3 or 5 fields', t)
            with self.subTest(pattern=pattern, string=s):
                if outcome == SYNTAX_ERROR:
                    with self.assertRaises(re.error):
                        re.compile(pattern)
                    continue
                obj = re.compile(pattern)
                result = obj.search(s)
                if outcome == FAIL:
                    self.assertIsNone(result, 'Succeeded incorrectly')
                    continue
                with self.subTest():
                    self.assertTrue(result, 'Failed incorrectly')
                    start, end = result.span(0)
                    vardict = {'found': result.group(0), 'groups': result.
                        group(), 'flags': result.re.flags}
                    for i in range(1, 100):
                        try:
                            gi = result.group(i)
                            if gi is None:
                                gi = 'None'
                        except IndexError:
                            gi = 'Error'
                        vardict['g%d' % i] = gi
                    for i in result.re.groupindex.keys():
                        try:
                            gi = result.group(i)
                            if gi is None:
                                gi = 'None'
                        except IndexError:
                            gi = 'Error'
                        vardict[i] = gi
                    self.assertEqual(eval(repl, vardict), expected,
                        'grouping error')
                try:
                    bpat = bytes(pattern, 'ascii')
                    bs = bytes(s, 'ascii')
                except UnicodeEncodeError:
                    pass
                else:
                    with self.subTest('bytes pattern match'):
                        obj = re.compile(bpat)
                        self.assertTrue(obj.search(bs))
                    with self.subTest('locale-sensitive match'):
                        obj = re.compile(bpat, re.LOCALE)
                        result = obj.search(bs)
                        if result is None:
                            print('=== Fails on locale-sensitive match', t)
                if pattern[:2] != '\\B' and pattern[-2:
                    ] != '\\B' and result is not None:
                    with self.subTest('range-limited match'):
                        obj = re.compile(pattern)
                        self.assertTrue(obj.search(s, start, end + 1))
                with self.subTest('case-insensitive match'):
                    obj = re.compile(pattern, re.IGNORECASE)
                    self.assertTrue(obj.search(s))
                with self.subTest('unicode-sensitive match'):
                    obj = re.compile(pattern, re.UNICODE)
                    self.assertTrue(obj.search(s))


if __name__ == '__main__':
    unittest.main()
