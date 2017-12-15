""" Test script for the Unicode implementation.

Written by Bill Tutt.
Modified for Python 2.0 by Fredrik Lundh (fredrik@pythonware.com)

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""
import unittest
import unicodedata
from test import support
from http.client import HTTPException
from test.test_normalization import check_version
try:
    from _testcapi import INT_MAX, PY_SSIZE_T_MAX, UINT_MAX
except ImportError:
    INT_MAX = PY_SSIZE_T_MAX = UINT_MAX = 2 ** 64 - 1


class UnicodeNamesTest(unittest.TestCase):

    def checkletter(self, name, code):
        res = eval('"\\N{%s}"' % name)
        self.assertEqual(res, code)
        return res

    def test_general(self):
        chars = ['LATIN CAPITAL LETTER T', 'LATIN SMALL LETTER H',
            'LATIN SMALL LETTER E', 'SPACE', 'LATIN SMALL LETTER R',
            'LATIN CAPITAL LETTER E', 'LATIN SMALL LETTER D', 'SPACE',
            'LATIN SMALL LETTER f', 'LATIN CAPITAL LeTtEr o',
            'LATIN SMaLl LETTER x', 'SPACE', 'LATIN SMALL LETTER A',
            'LATIN SMALL LETTER T', 'LATIN SMALL LETTER E', 'SPACE',
            'LATIN SMALL LETTER T', 'LATIN SMALL LETTER H',
            'LATIN SMALL LETTER E', 'SpAcE', 'LATIN SMALL LETTER S',
            'LATIN SMALL LETTER H', 'LATIN small LETTER e',
            'LATIN small LETTER e', 'LATIN SMALL LETTER P', 'FULL STOP']
        string = 'The rEd fOx ate the sheep.'
        self.assertEqual(''.join([self.checkletter(*args) for args in zip(
            chars, string)]), string)

    def test_ascii_letters(self):
        for char in ''.join(map(chr, range(ord('a'), ord('z')))):
            name = 'LATIN SMALL LETTER %s' % char.upper()
            code = unicodedata.lookup(name)
            self.assertEqual(unicodedata.name(code), name)

    def test_hangul_syllables(self):
        self.checkletter('HANGUL SYLLABLE GA', '가')
        self.checkletter('HANGUL SYLLABLE GGWEOSS', '꿨')
        self.checkletter('HANGUL SYLLABLE DOLS', '돐')
        self.checkletter('HANGUL SYLLABLE RYAN', '랸')
        self.checkletter('HANGUL SYLLABLE MWIK', '뮠')
        self.checkletter('HANGUL SYLLABLE BBWAEM', '뾈')
        self.checkletter('HANGUL SYLLABLE SSEOL', '썰')
        self.checkletter('HANGUL SYLLABLE YI', '의')
        self.checkletter('HANGUL SYLLABLE JJYOSS', '쭀')
        self.checkletter('HANGUL SYLLABLE KYEOLS', '켨')
        self.checkletter('HANGUL SYLLABLE PAN', '판')
        self.checkletter('HANGUL SYLLABLE HWEOK', '훸')
        self.checkletter('HANGUL SYLLABLE HIH', '힣')
        self.assertRaises(ValueError, unicodedata.name, '\ud7a4')

    def test_cjk_unified_ideographs(self):
        self.checkletter('CJK UNIFIED IDEOGRAPH-3400', '㐀')
        self.checkletter('CJK UNIFIED IDEOGRAPH-4DB5', '䶵')
        self.checkletter('CJK UNIFIED IDEOGRAPH-4E00', '一')
        self.checkletter('CJK UNIFIED IDEOGRAPH-9FCB', '鿋')
        self.checkletter('CJK UNIFIED IDEOGRAPH-20000', '𠀀')
        self.checkletter('CJK UNIFIED IDEOGRAPH-2A6D6', '𪛖')
        self.checkletter('CJK UNIFIED IDEOGRAPH-2A700', '𪜀')
        self.checkletter('CJK UNIFIED IDEOGRAPH-2B734', '𫜴')
        self.checkletter('CJK UNIFIED IDEOGRAPH-2B740', '𫝀')
        self.checkletter('CJK UNIFIED IDEOGRAPH-2B81D', '𫠝')

    def test_bmp_characters(self):
        for code in range(65536):
            char = chr(code)
            name = unicodedata.name(char, None)
            if name is not None:
                self.assertEqual(unicodedata.lookup(name), char)

    def test_misc_symbols(self):
        self.checkletter('PILCROW SIGN', '¶')
        self.checkletter('REPLACEMENT CHARACTER', '�')
        self.checkletter('HALFWIDTH KATAKANA SEMI-VOICED SOUND MARK', 'ﾟ')
        self.checkletter('FULLWIDTH LATIN SMALL LETTER A', 'ａ')

    def test_aliases(self):
        aliases = [('LATIN CAPITAL LETTER GHA', 418), (
            'LATIN SMALL LETTER GHA', 419), ('KANNADA LETTER LLLA', 3294),
            ('LAO LETTER FO FON', 3741), ('LAO LETTER FO FAY', 3743), (
            'LAO LETTER RO', 3747), ('LAO LETTER LO', 3749), (
            'TIBETAN MARK BKA- SHOG GI MGO RGYAN', 4048), (
            'YI SYLLABLE ITERATION MARK', 40981), (
            'PRESENTATION FORM FOR VERTICAL RIGHT WHITE LENTICULAR BRACKET',
            65048), ('BYZANTINE MUSICAL SYMBOL FTHORA SKLIRON CHROMA VASIS',
            118981)]
        for alias, codepoint in aliases:
            self.checkletter(alias, chr(codepoint))
            name = unicodedata.name(chr(codepoint))
            self.assertNotEqual(name, alias)
            self.assertEqual(unicodedata.lookup(alias), unicodedata.lookup(
                name))
            with self.assertRaises(KeyError):
                unicodedata.ucd_3_2_0.lookup(alias)

    def test_aliases_names_in_pua_range(self):
        for cp in range(983040, 983296):
            with self.assertRaises(ValueError) as cm:
                unicodedata.name(chr(cp))
            self.assertEqual(str(cm.exception), 'no such name')

    def test_named_sequences_names_in_pua_range(self):
        for cp in range(983296, 987135):
            with self.assertRaises(ValueError) as cm:
                unicodedata.name(chr(cp))
            self.assertEqual(str(cm.exception), 'no such name')

    def test_named_sequences_sample(self):
        sequences = [('LATIN SMALL LETTER R WITH TILDE', 'r̃'), (
            'TAMIL SYLLABLE SAI', 'ஸை'), ('TAMIL SYLLABLE MOO', 'மோ'), (
            'TAMIL SYLLABLE NNOO', 'ணோ'), ('TAMIL CONSONANT KSS', 'க்ஷ்')]
        for seqname, codepoints in sequences:
            self.assertEqual(unicodedata.lookup(seqname), codepoints)
            with self.assertRaises(SyntaxError):
                self.checkletter(seqname, None)
            with self.assertRaises(KeyError):
                unicodedata.ucd_3_2_0.lookup(seqname)

    def test_named_sequences_full(self):
        url = ('http://www.pythontest.net/unicode/%s/NamedSequences.txt' %
            unicodedata.unidata_version)
        try:
            testdata = support.open_urlresource(url, encoding='utf-8',
                check=check_version)
        except (OSError, HTTPException):
            self.skipTest('Could not retrieve ' + url)
        self.addCleanup(testdata.close)
        for line in testdata:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            seqname, codepoints = line.split(';')
            codepoints = ''.join(chr(int(cp, 16)) for cp in codepoints.split())
            self.assertEqual(unicodedata.lookup(seqname), codepoints)
            with self.assertRaises(SyntaxError):
                self.checkletter(seqname, None)
            with self.assertRaises(KeyError):
                unicodedata.ucd_3_2_0.lookup(seqname)

    def test_errors(self):
        self.assertRaises(TypeError, unicodedata.name)
        self.assertRaises(TypeError, unicodedata.name, 'xx')
        self.assertRaises(TypeError, unicodedata.lookup)
        self.assertRaises(KeyError, unicodedata.lookup, 'unknown')

    def test_strict_error_handling(self):
        self.assertRaises(UnicodeError, str, b'\\N{blah}', 'unicode-escape',
            'strict')
        self.assertRaises(UnicodeError, str, bytes('\\N{%s}' % ('x' * 
            100000), 'ascii'), 'unicode-escape', 'strict')
        self.assertRaises(UnicodeError, str, b'\\N{SPACE', 'unicode-escape',
            'strict')
        self.assertRaises(UnicodeError, str, b'\\NSPACE', 'unicode-escape',
            'strict')

    @support.cpython_only
    @unittest.skipUnless(INT_MAX < PY_SSIZE_T_MAX, 'needs UINT_MAX < SIZE_MAX')
    @support.bigmemtest(size=UINT_MAX + 1, memuse=2 + 1, dry_run=False)
    def test_issue16335(self, size):
        x = b'\\N{SPACE' + b'x' * (UINT_MAX + 1) + b'}'
        self.assertEqual(len(x), len(b'\\N{SPACE}') + (UINT_MAX + 1))
        self.assertRaisesRegex(UnicodeError,
            'unknown Unicode character name', x.decode, 'unicode-escape')


if __name__ == '__main__':
    unittest.main()
