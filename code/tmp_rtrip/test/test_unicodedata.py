""" Test script for the unicodedata module.

    Written by Marc-Andre Lemburg (mal@lemburg.com).

    (c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""
import sys
import unittest
import hashlib
from test.support import script_helper
encoding = 'utf-8'
errors = 'surrogatepass'


class UnicodeMethodsTest(unittest.TestCase):
    expectedchecksum = 'c1fa98674a683aa8a8d8dee0c84494f8d36346e6'

    def test_method_checksum(self):
        h = hashlib.sha1()
        for i in range(65536):
            char = chr(i)
            data = ['01'[char.isalnum()], '01'[char.isalpha()], '01'[char.
                isdecimal()], '01'[char.isdigit()], '01'[char.islower()],
                '01'[char.isnumeric()], '01'[char.isspace()], '01'[char.
                istitle()], '01'[char.isupper()], '01'[(char + 'abc').
                isalnum()], '01'[(char + 'abc').isalpha()], '01'[(char +
                '123').isdecimal()], '01'[(char + '123').isdigit()], '01'[(
                char + 'abc').islower()], '01'[(char + '123').isnumeric()],
                '01'[(char + ' \t').isspace()], '01'[(char + 'abc').istitle
                ()], '01'[(char + 'ABC').isupper()], char.lower(), char.
                upper(), char.title(), (char + 'abc').lower(), (char +
                'ABC').upper(), (char + 'abc').title(), (char + 'ABC').title()]
            h.update(''.join(data).encode(encoding, errors))
        result = h.hexdigest()
        self.assertEqual(result, self.expectedchecksum)


class UnicodeDatabaseTest(unittest.TestCase):

    def setUp(self):
        import unicodedata
        self.db = unicodedata

    def tearDown(self):
        del self.db


class UnicodeFunctionsTest(UnicodeDatabaseTest):
    expectedchecksum = 'f891b1e6430c712531b9bc935a38e22d78ba1bf3'

    def test_function_checksum(self):
        data = []
        h = hashlib.sha1()
        for i in range(65536):
            char = chr(i)
            data = [format(self.db.digit(char, -1), '.12g'), format(self.db
                .numeric(char, -1), '.12g'), format(self.db.decimal(char, -
                1), '.12g'), self.db.category(char), self.db.bidirectional(
                char), self.db.decomposition(char), str(self.db.mirrored(
                char)), str(self.db.combining(char))]
            h.update(''.join(data).encode('ascii'))
        result = h.hexdigest()
        self.assertEqual(result, self.expectedchecksum)

    def test_digit(self):
        self.assertEqual(self.db.digit('A', None), None)
        self.assertEqual(self.db.digit('9'), 9)
        self.assertEqual(self.db.digit('⅛', None), None)
        self.assertEqual(self.db.digit('⑨'), 9)
        self.assertEqual(self.db.digit('𠀀', None), None)
        self.assertEqual(self.db.digit('𝟽'), 7)
        self.assertRaises(TypeError, self.db.digit)
        self.assertRaises(TypeError, self.db.digit, 'xx')
        self.assertRaises(ValueError, self.db.digit, 'x')

    def test_numeric(self):
        self.assertEqual(self.db.numeric('A', None), None)
        self.assertEqual(self.db.numeric('9'), 9)
        self.assertEqual(self.db.numeric('⅛'), 0.125)
        self.assertEqual(self.db.numeric('⑨'), 9.0)
        self.assertEqual(self.db.numeric('꘧'), 7.0)
        self.assertEqual(self.db.numeric('𠀀', None), None)
        self.assertEqual(self.db.numeric('𐄪'), 9000)
        self.assertRaises(TypeError, self.db.numeric)
        self.assertRaises(TypeError, self.db.numeric, 'xx')
        self.assertRaises(ValueError, self.db.numeric, 'x')

    def test_decimal(self):
        self.assertEqual(self.db.decimal('A', None), None)
        self.assertEqual(self.db.decimal('9'), 9)
        self.assertEqual(self.db.decimal('⅛', None), None)
        self.assertEqual(self.db.decimal('⑨', None), None)
        self.assertEqual(self.db.decimal('𠀀', None), None)
        self.assertEqual(self.db.decimal('𝟽'), 7)
        self.assertRaises(TypeError, self.db.decimal)
        self.assertRaises(TypeError, self.db.decimal, 'xx')
        self.assertRaises(ValueError, self.db.decimal, 'x')

    def test_category(self):
        self.assertEqual(self.db.category('\ufffe'), 'Cn')
        self.assertEqual(self.db.category('a'), 'Ll')
        self.assertEqual(self.db.category('A'), 'Lu')
        self.assertEqual(self.db.category('𠀀'), 'Lo')
        self.assertEqual(self.db.category('𐄪'), 'No')
        self.assertRaises(TypeError, self.db.category)
        self.assertRaises(TypeError, self.db.category, 'xx')

    def test_bidirectional(self):
        self.assertEqual(self.db.bidirectional('\ufffe'), '')
        self.assertEqual(self.db.bidirectional(' '), 'WS')
        self.assertEqual(self.db.bidirectional('A'), 'L')
        self.assertEqual(self.db.bidirectional('𠀀'), 'L')
        self.assertRaises(TypeError, self.db.bidirectional)
        self.assertRaises(TypeError, self.db.bidirectional, 'xx')

    def test_decomposition(self):
        self.assertEqual(self.db.decomposition('\ufffe'), '')
        self.assertEqual(self.db.decomposition('¼'),
            '<fraction> 0031 2044 0034')
        self.assertRaises(TypeError, self.db.decomposition)
        self.assertRaises(TypeError, self.db.decomposition, 'xx')

    def test_mirrored(self):
        self.assertEqual(self.db.mirrored('\ufffe'), 0)
        self.assertEqual(self.db.mirrored('a'), 0)
        self.assertEqual(self.db.mirrored('∁'), 1)
        self.assertEqual(self.db.mirrored('𠀀'), 0)
        self.assertRaises(TypeError, self.db.mirrored)
        self.assertRaises(TypeError, self.db.mirrored, 'xx')

    def test_combining(self):
        self.assertEqual(self.db.combining('\ufffe'), 0)
        self.assertEqual(self.db.combining('a'), 0)
        self.assertEqual(self.db.combining('⃡'), 230)
        self.assertEqual(self.db.combining('𠀀'), 0)
        self.assertRaises(TypeError, self.db.combining)
        self.assertRaises(TypeError, self.db.combining, 'xx')

    def test_normalize(self):
        self.assertRaises(TypeError, self.db.normalize)
        self.assertRaises(ValueError, self.db.normalize, 'unknown', 'xx')
        self.assertEqual(self.db.normalize('NFKC', ''), '')

    def test_pr29(self):
        composed = ('େ̀ା', 'ᄀ̀ᅡ', 'Li̍t-sṳ́', 'मार्क ज़' + 'ुकेरबर्ग', 
            'किर्गिज़' + 'स्तान')
        for text in composed:
            self.assertEqual(self.db.normalize('NFC', text), text)

    def test_issue10254(self):
        a = 'C̸' * 20 + 'Ç'
        b = 'C̸' * 20 + 'Ç'
        self.assertEqual(self.db.normalize('NFC', a), b)

    def test_east_asian_width(self):
        eaw = self.db.east_asian_width
        self.assertRaises(TypeError, eaw, b'a')
        self.assertRaises(TypeError, eaw, bytearray())
        self.assertRaises(TypeError, eaw, '')
        self.assertRaises(TypeError, eaw, 'ra')
        self.assertEqual(eaw('\x1e'), 'N')
        self.assertEqual(eaw(' '), 'Na')
        self.assertEqual(eaw('좔'), 'W')
        self.assertEqual(eaw('ｦ'), 'H')
        self.assertEqual(eaw('？'), 'F')
        self.assertEqual(eaw('‐'), 'A')
        self.assertEqual(eaw('𠀀'), 'W')

    def test_east_asian_width_9_0_changes(self):
        self.assertEqual(self.db.ucd_3_2_0.east_asian_width('⌚'), 'N')
        self.assertEqual(self.db.east_asian_width('⌚'), 'W')


class UnicodeMiscTest(UnicodeDatabaseTest):

    def test_failed_import_during_compiling(self):
        code = (
            'import sys;sys.modules[\'unicodedata\'] = None;eval("\'\\\\N{SOFT HYPHEN}\'")'
            )
        result = script_helper.assert_python_failure('-c', code)
        error = (
            "SyntaxError: (unicode error) \\N escapes not supported (can't load unicodedata module)"
            )
        self.assertIn(error, result.err.decode('ascii'))

    def test_decimal_numeric_consistent(self):
        count = 0
        for i in range(65536):
            c = chr(i)
            dec = self.db.decimal(c, -1)
            if dec != -1:
                self.assertEqual(dec, self.db.numeric(c))
                count += 1
        self.assertTrue(count >= 10)

    def test_digit_numeric_consistent(self):
        count = 0
        for i in range(65536):
            c = chr(i)
            dec = self.db.digit(c, -1)
            if dec != -1:
                self.assertEqual(dec, self.db.numeric(c))
                count += 1
        self.assertTrue(count >= 10)

    def test_bug_1704793(self):
        self.assertEqual(self.db.lookup('GOTHIC LETTER FAIHU'), '𐍆')

    def test_ucd_510(self):
        import unicodedata
        self.assertTrue(unicodedata.mirrored('༺'))
        self.assertTrue(not unicodedata.ucd_3_2_0.mirrored('༺'))
        self.assertTrue('a'.upper() == 'A')
        self.assertTrue('ᵹ'.upper() == 'Ᵹ')
        self.assertTrue('.'.upper() == '.')

    def test_bug_5828(self):
        self.assertEqual('ᵹ'.lower(), 'ᵹ')
        self.assertEqual([c for c in range(sys.maxunicode + 1) if '\x00' in
            chr(c).lower() + chr(c).upper() + chr(c).title()], [0])

    def test_bug_4971(self):
        self.assertEqual('Ǆ'.title(), 'ǅ')
        self.assertEqual('ǅ'.title(), 'ǅ')
        self.assertEqual('ǆ'.title(), 'ǅ')

    def test_linebreak_7643(self):
        for i in range(65536):
            lines = (chr(i) + 'A').splitlines()
            if i in (10, 11, 12, 13, 133, 28, 29, 30, 8232, 8233):
                self.assertEqual(len(lines), 2, 
                    '\\u%.4x should be a linebreak' % i)
            else:
                self.assertEqual(len(lines), 1, 
                    '\\u%.4x should not be a linebreak' % i)


if __name__ == '__main__':
    unittest.main()
