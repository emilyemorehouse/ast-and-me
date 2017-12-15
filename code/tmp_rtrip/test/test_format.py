from test.support import verbose, TestFailed
import locale
import sys
import test.support as support
import unittest
maxsize = support.MAX_Py_ssize_t


def testformat(formatstr, args, output=None, limit=None, overflowok=False):
    if verbose:
        if output:
            print('{!a} % {!a} =? {!a} ...'.format(formatstr, args, output),
                end=' ')
        else:
            print('{!a} % {!a} works? ...'.format(formatstr, args), end=' ')
    try:
        result = formatstr % args
    except OverflowError:
        if not overflowok:
            raise
        if verbose:
            print('overflow (this is fine)')
    else:
        if output and limit is None and result != output:
            if verbose:
                print('no')
            raise AssertionError('%r %% %r == %r != %r' % (formatstr, args,
                result, output))
        elif output and limit is not None and (len(result) != len(output) or
            result[:limit] != output[:limit]):
            if verbose:
                print('no')
            print('%s %% %s == %s != %s' % (repr(formatstr), repr(args),
                repr(result), repr(output)))
        elif verbose:
            print('yes')


def testcommon(formatstr, args, output=None, limit=None, overflowok=False):
    if isinstance(formatstr, str):
        testformat(formatstr, args, output, limit, overflowok)
        b_format = formatstr.encode('ascii')
    else:
        b_format = formatstr
    ba_format = bytearray(b_format)
    b_args = []
    if not isinstance(args, tuple):
        args = args,
    b_args = tuple(args)
    if output is None:
        b_output = ba_output = None
    else:
        if isinstance(output, str):
            b_output = output.encode('ascii')
        else:
            b_output = output
        ba_output = bytearray(b_output)
    testformat(b_format, b_args, b_output, limit, overflowok)
    testformat(ba_format, b_args, ba_output, limit, overflowok)


class FormatTest(unittest.TestCase):

    def test_common_format(self):
        testcommon('%.1d', (1,), '1')
        testcommon('%.*d', (sys.maxsize, 1), overflowok=True)
        testcommon('%.100d', (1,),
            '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001'
            , overflowok=True)
        testcommon('%#.117x', (1,),
            '0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001'
            , overflowok=True)
        testcommon('%#.118x', (1,),
            '0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001'
            , overflowok=True)
        testcommon('%f', (1.0,), '1.000000')
        testcommon('%#.*g', (109, -1e+49 / 3.0))
        testcommon('%#.*g', (110, -1e+49 / 3.0))
        testcommon('%#.*g', (110, -1e+100 / 3.0))
        testcommon('%12.*f', (123456, 1.0))
        testcommon('%#.*g', (110, -1e+100 / 3.0))
        testcommon('%#.*G', (110, -1e+100 / 3.0))
        testcommon('%#.*f', (110, -1e+100 / 3.0))
        testcommon('%#.*F', (110, -1e+100 / 3.0))
        testcommon('%x', 10, 'a')
        testcommon('%x', 100000000000, '174876e800')
        testcommon('%o', 10, '12')
        testcommon('%o', 100000000000, '1351035564000')
        testcommon('%d', 10, '10')
        testcommon('%d', 100000000000, '100000000000')
        big = 123456789012345678901234567890
        testcommon('%d', big, '123456789012345678901234567890')
        testcommon('%d', -big, '-123456789012345678901234567890')
        testcommon('%5d', -big, '-123456789012345678901234567890')
        testcommon('%31d', -big, '-123456789012345678901234567890')
        testcommon('%32d', -big, ' -123456789012345678901234567890')
        testcommon('%-32d', -big, '-123456789012345678901234567890 ')
        testcommon('%032d', -big, '-0123456789012345678901234567890')
        testcommon('%-032d', -big, '-123456789012345678901234567890 ')
        testcommon('%034d', -big, '-000123456789012345678901234567890')
        testcommon('%034d', big, '0000123456789012345678901234567890')
        testcommon('%0+34d', big, '+000123456789012345678901234567890')
        testcommon('%+34d', big, '   +123456789012345678901234567890')
        testcommon('%34d', big, '    123456789012345678901234567890')
        testcommon('%.2d', big, '123456789012345678901234567890')
        testcommon('%.30d', big, '123456789012345678901234567890')
        testcommon('%.31d', big, '0123456789012345678901234567890')
        testcommon('%32.31d', big, ' 0123456789012345678901234567890')
        testcommon('%d', float(big), '123456________________________', 6)
        big = 1375488932362216742658885
        testcommon('%x', big, '1234567890abcdef12345')
        testcommon('%x', -big, '-1234567890abcdef12345')
        testcommon('%5x', -big, '-1234567890abcdef12345')
        testcommon('%22x', -big, '-1234567890abcdef12345')
        testcommon('%23x', -big, ' -1234567890abcdef12345')
        testcommon('%-23x', -big, '-1234567890abcdef12345 ')
        testcommon('%023x', -big, '-01234567890abcdef12345')
        testcommon('%-023x', -big, '-1234567890abcdef12345 ')
        testcommon('%025x', -big, '-0001234567890abcdef12345')
        testcommon('%025x', big, '00001234567890abcdef12345')
        testcommon('%0+25x', big, '+0001234567890abcdef12345')
        testcommon('%+25x', big, '   +1234567890abcdef12345')
        testcommon('%25x', big, '    1234567890abcdef12345')
        testcommon('%.2x', big, '1234567890abcdef12345')
        testcommon('%.21x', big, '1234567890abcdef12345')
        testcommon('%.22x', big, '01234567890abcdef12345')
        testcommon('%23.22x', big, ' 01234567890abcdef12345')
        testcommon('%-23.22x', big, '01234567890abcdef12345 ')
        testcommon('%X', big, '1234567890ABCDEF12345')
        testcommon('%#X', big, '0X1234567890ABCDEF12345')
        testcommon('%#x', big, '0x1234567890abcdef12345')
        testcommon('%#x', -big, '-0x1234567890abcdef12345')
        testcommon('%#27x', big, '    0x1234567890abcdef12345')
        testcommon('%#-27x', big, '0x1234567890abcdef12345    ')
        testcommon('%#027x', big, '0x00001234567890abcdef12345')
        testcommon('%#.23x', big, '0x001234567890abcdef12345')
        testcommon('%#.23x', -big, '-0x001234567890abcdef12345')
        testcommon('%#27.23x', big, '  0x001234567890abcdef12345')
        testcommon('%#-27.23x', big, '0x001234567890abcdef12345  ')
        testcommon('%#027.23x', big, '0x00001234567890abcdef12345')
        testcommon('%#+.23x', big, '+0x001234567890abcdef12345')
        testcommon('%# .23x', big, ' 0x001234567890abcdef12345')
        testcommon('%#+.23X', big, '+0X001234567890ABCDEF12345')
        testcommon('%#+027.23X', big, '+0X0001234567890ABCDEF12345')
        testcommon('%# 027.23X', big, ' 0X0001234567890ABCDEF12345')
        testcommon('%#+27.23X', big, ' +0X001234567890ABCDEF12345')
        testcommon('%#-+27.23x', big, '+0x001234567890abcdef12345 ')
        testcommon('%#- 27.23x', big, ' 0x001234567890abcdef12345 ')
        big = 12935167030485801517351291832
        testcommon('%o', big, '12345670123456701234567012345670')
        testcommon('%o', -big, '-12345670123456701234567012345670')
        testcommon('%5o', -big, '-12345670123456701234567012345670')
        testcommon('%33o', -big, '-12345670123456701234567012345670')
        testcommon('%34o', -big, ' -12345670123456701234567012345670')
        testcommon('%-34o', -big, '-12345670123456701234567012345670 ')
        testcommon('%034o', -big, '-012345670123456701234567012345670')
        testcommon('%-034o', -big, '-12345670123456701234567012345670 ')
        testcommon('%036o', -big, '-00012345670123456701234567012345670')
        testcommon('%036o', big, '000012345670123456701234567012345670')
        testcommon('%0+36o', big, '+00012345670123456701234567012345670')
        testcommon('%+36o', big, '   +12345670123456701234567012345670')
        testcommon('%36o', big, '    12345670123456701234567012345670')
        testcommon('%.2o', big, '12345670123456701234567012345670')
        testcommon('%.32o', big, '12345670123456701234567012345670')
        testcommon('%.33o', big, '012345670123456701234567012345670')
        testcommon('%34.33o', big, ' 012345670123456701234567012345670')
        testcommon('%-34.33o', big, '012345670123456701234567012345670 ')
        testcommon('%o', big, '12345670123456701234567012345670')
        testcommon('%#o', big, '0o12345670123456701234567012345670')
        testcommon('%#o', -big, '-0o12345670123456701234567012345670')
        testcommon('%#38o', big, '    0o12345670123456701234567012345670')
        testcommon('%#-38o', big, '0o12345670123456701234567012345670    ')
        testcommon('%#038o', big, '0o000012345670123456701234567012345670')
        testcommon('%#.34o', big, '0o0012345670123456701234567012345670')
        testcommon('%#.34o', -big, '-0o0012345670123456701234567012345670')
        testcommon('%#38.34o', big, '  0o0012345670123456701234567012345670')
        testcommon('%#-38.34o', big, '0o0012345670123456701234567012345670  ')
        testcommon('%#038.34o', big, '0o000012345670123456701234567012345670')
        testcommon('%#+.34o', big, '+0o0012345670123456701234567012345670')
        testcommon('%# .34o', big, ' 0o0012345670123456701234567012345670')
        testcommon('%#+38.34o', big, ' +0o0012345670123456701234567012345670')
        testcommon('%#-+38.34o', big, '+0o0012345670123456701234567012345670 ')
        testcommon('%#- 38.34o', big, ' 0o0012345670123456701234567012345670 ')
        testcommon('%#+038.34o', big, '+0o00012345670123456701234567012345670')
        testcommon('%# 038.34o', big, ' 0o00012345670123456701234567012345670')
        testcommon('%.33o', big, '012345670123456701234567012345670')
        testcommon('%#.33o', big, '0o012345670123456701234567012345670')
        testcommon('%#.32o', big, '0o12345670123456701234567012345670')
        testcommon('%035.33o', big, '00012345670123456701234567012345670')
        testcommon('%0#35.33o', big, '0o012345670123456701234567012345670')
        testcommon('%d', 42, '42')
        testcommon('%d', -42, '-42')
        testcommon('%d', 42.0, '42')
        testcommon('%#x', 1, '0x1')
        testcommon('%#X', 1, '0X1')
        testcommon('%#o', 1, '0o1')
        testcommon('%#o', 0, '0o0')
        testcommon('%o', 0, '0')
        testcommon('%d', 0, '0')
        testcommon('%#x', 0, '0x0')
        testcommon('%#X', 0, '0X0')
        testcommon('%x', 66, '42')
        testcommon('%x', -66, '-42')
        testcommon('%o', 34, '42')
        testcommon('%o', -34, '-42')
        testcommon('%g', 1.1, '1.1')
        testcommon('%#g', 1.1, '1.10000')

    def test_str_format(self):
        testformat('%r', '\u0378', "'\\u0378'")
        testformat('%a', '\u0378', "'\\u0378'")
        testformat('%r', 'ʹ', "'ʹ'")
        testformat('%a', 'ʹ', "'\\u0374'")
        if verbose:
            print('Testing exceptions')

        def test_exc(formatstr, args, exception, excmsg):
            try:
                testformat(formatstr, args)
            except exception as exc:
                if str(exc) == excmsg:
                    if verbose:
                        print('yes')
                else:
                    if verbose:
                        print('no')
                    print('Unexpected ', exception, ':', repr(str(exc)))
            except:
                if verbose:
                    print('no')
                print('Unexpected exception')
                raise
            else:
                raise TestFailed('did not get expected exception: %s' % excmsg)
        test_exc('abc %b', 1, ValueError,
            "unsupported format character 'b' (0x62) at index 5")
        test_exc('%d', '1', TypeError,
            '%d format: a number is required, not str')
        test_exc('%x', '1', TypeError,
            '%x format: an integer is required, not str')
        test_exc('%x', 3.14, TypeError,
            '%x format: an integer is required, not float')
        test_exc('%g', '1', TypeError, 'must be real number, not str')
        test_exc('no format', '1', TypeError,
            'not all arguments converted during string formatting')
        test_exc('%c', -1, OverflowError, '%c arg not in range(0x110000)')
        test_exc('%c', sys.maxunicode + 1, OverflowError,
            '%c arg not in range(0x110000)')
        test_exc('%c', 3.14, TypeError, '%c requires int or char')
        test_exc('%c', 'ab', TypeError, '%c requires int or char')
        test_exc('%c', b'x', TypeError, '%c requires int or char')
        if maxsize == 2 ** 31 - 1:
            try:
                '%*d' % (maxsize, -127)
            except MemoryError:
                pass
            else:
                raise TestFailed('"%*d"%(maxsize, -127) should fail')

    def test_bytes_and_bytearray_format(self):
        testcommon(b'%c', 7, b'\x07')
        testcommon(b'%c', b'Z', b'Z')
        testcommon(b'%c', bytearray(b'Z'), b'Z')
        testcommon(b'%5c', 65, b'    A')
        testcommon(b'%-5c', 65, b'A    ')


        class FakeBytes(object):

            def __bytes__(self):
                return b'123'
        fb = FakeBytes()
        testcommon(b'%b', b'abc', b'abc')
        testcommon(b'%b', bytearray(b'def'), b'def')
        testcommon(b'%b', fb, b'123')
        testcommon(b'%b', memoryview(b'abc'), b'abc')
        testcommon(b'%s', b'abc', b'abc')
        testcommon(b'%s', bytearray(b'def'), b'def')
        testcommon(b'%s', fb, b'123')
        testcommon(b'%s', memoryview(b'abc'), b'abc')
        testcommon(b'%a', 3.14, b'3.14')
        testcommon(b'%a', b'ghi', b"b'ghi'")
        testcommon(b'%a', 'jkl', b"'jkl'")
        testcommon(b'%a', 'Մ', b"'\\u0544'")
        testcommon(b'%r', 3.14, b'3.14')
        testcommon(b'%r', b'ghi', b"b'ghi'")
        testcommon(b'%r', 'jkl', b"'jkl'")
        testcommon(b'%r', 'Մ', b"'\\u0544'")
        if verbose:
            print('Testing exceptions')

        def test_exc(formatstr, args, exception, excmsg):
            try:
                testformat(formatstr, args)
            except exception as exc:
                if str(exc) == excmsg:
                    if verbose:
                        print('yes')
                else:
                    if verbose:
                        print('no')
                    print('Unexpected ', exception, ':', repr(str(exc)))
            except:
                if verbose:
                    print('no')
                print('Unexpected exception')
                raise
            else:
                raise TestFailed('did not get expected exception: %s' % excmsg)
        test_exc(b'%d', '1', TypeError,
            '%d format: a number is required, not str')
        test_exc(b'%d', b'1', TypeError,
            '%d format: a number is required, not bytes')
        test_exc(b'%x', 3.14, TypeError,
            '%x format: an integer is required, not float')
        test_exc(b'%g', '1', TypeError, 'float argument required, not str')
        test_exc(b'%g', b'1', TypeError, 'float argument required, not bytes')
        test_exc(b'no format', 7, TypeError,
            'not all arguments converted during bytes formatting')
        test_exc(b'no format', b'1', TypeError,
            'not all arguments converted during bytes formatting')
        test_exc(b'no format', bytearray(b'1'), TypeError,
            'not all arguments converted during bytes formatting')
        test_exc(b'%c', -1, OverflowError, '%c arg not in range(256)')
        test_exc(b'%c', 256, OverflowError, '%c arg not in range(256)')
        test_exc(b'%c', 2 ** 128, OverflowError, '%c arg not in range(256)')
        test_exc(b'%c', b'Za', TypeError,
            '%c requires an integer in range(256) or a single byte')
        test_exc(b'%c', 'Y', TypeError,
            '%c requires an integer in range(256) or a single byte')
        test_exc(b'%c', 3.14, TypeError,
            '%c requires an integer in range(256) or a single byte')
        test_exc(b'%b', 'Xc', TypeError,
            "%b requires a bytes-like object, or an object that implements __bytes__, not 'str'"
            )
        test_exc(b'%s', 'Wd', TypeError,
            "%b requires a bytes-like object, or an object that implements __bytes__, not 'str'"
            )
        if maxsize == 2 ** 31 - 1:
            try:
                '%*d' % (maxsize, -127)
            except MemoryError:
                pass
            else:
                raise TestFailed('"%*d"%(maxsize, -127) should fail')

    def test_nul(self):
        testcommon('a\x00b', (), 'a\x00b')
        testcommon('a%cb', (0,), 'a\x00b')
        testformat('a%sb', ('c\x00d',), 'ac\x00db')
        testcommon(b'a%sb', (b'c\x00d',), b'ac\x00db')

    def test_non_ascii(self):
        testformat('€=%f', (1.0,), '€=1.000000')
        self.assertEqual(format('abc', '\u2007<5'), 'abc\u2007\u2007')
        self.assertEqual(format(123, '\u2007<5'), '123\u2007\u2007')
        self.assertEqual(format(12.3, '\u2007<6'), '12.3\u2007\u2007')
        self.assertEqual(format(0j, '\u2007<4'), '0j\u2007\u2007')
        self.assertEqual(format(1 + 2j, '\u2007<8'), '(1+2j)\u2007\u2007')
        self.assertEqual(format('abc', '\u2007>5'), '\u2007\u2007abc')
        self.assertEqual(format(123, '\u2007>5'), '\u2007\u2007123')
        self.assertEqual(format(12.3, '\u2007>6'), '\u2007\u200712.3')
        self.assertEqual(format(1 + 2j, '\u2007>8'), '\u2007\u2007(1+2j)')
        self.assertEqual(format(0j, '\u2007>4'), '\u2007\u20070j')
        self.assertEqual(format('abc', '\u2007^5'), '\u2007abc\u2007')
        self.assertEqual(format(123, '\u2007^5'), '\u2007123\u2007')
        self.assertEqual(format(12.3, '\u2007^6'), '\u200712.3\u2007')
        self.assertEqual(format(1 + 2j, '\u2007^8'), '\u2007(1+2j)\u2007')
        self.assertEqual(format(0j, '\u2007^4'), '\u20070j\u2007')

    def test_locale(self):
        try:
            oldloc = locale.setlocale(locale.LC_ALL)
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error as err:
            self.skipTest('Cannot set locale: {}'.format(err))
        try:
            localeconv = locale.localeconv()
            sep = localeconv['thousands_sep']
            point = localeconv['decimal_point']
            text = format(123456789, 'n')
            self.assertIn(sep, text)
            self.assertEqual(text.replace(sep, ''), '123456789')
            text = format(1234.5, 'n')
            self.assertIn(sep, text)
            self.assertIn(point, text)
            self.assertEqual(text.replace(sep, ''), '1234' + point + '5')
        finally:
            locale.setlocale(locale.LC_ALL, oldloc)

    @support.cpython_only
    def test_optimisations(self):
        text = 'abcde'
        self.assertIs('%s' % text, text)
        self.assertIs('%.5s' % text, text)
        self.assertIs('%.10s' % text, text)
        self.assertIs('%1s' % text, text)
        self.assertIs('%5s' % text, text)
        self.assertIs('{0}'.format(text), text)
        self.assertIs('{0:s}'.format(text), text)
        self.assertIs('{0:.5s}'.format(text), text)
        self.assertIs('{0:.10s}'.format(text), text)
        self.assertIs('{0:1s}'.format(text), text)
        self.assertIs('{0:5s}'.format(text), text)
        self.assertIs(text % (), text)
        self.assertIs(text.format(), text)

    def test_precision(self):
        f = 1.2
        self.assertEqual(format(f, '.0f'), '1')
        self.assertEqual(format(f, '.3f'), '1.200')
        with self.assertRaises(ValueError) as cm:
            format(f, '.%sf' % (sys.maxsize + 1))
        c = complex(f)
        self.assertEqual(format(c, '.0f'), '1+0j')
        self.assertEqual(format(c, '.3f'), '1.200+0.000j')
        with self.assertRaises(ValueError) as cm:
            format(c, '.%sf' % (sys.maxsize + 1))

    @support.cpython_only
    def test_precision_c_limits(self):
        from _testcapi import INT_MAX
        f = 1.2
        with self.assertRaises(ValueError) as cm:
            format(f, '.%sf' % (INT_MAX + 1))
        c = complex(f)
        with self.assertRaises(ValueError) as cm:
            format(c, '.%sf' % (INT_MAX + 1))


if __name__ == '__main__':
    unittest.main()
