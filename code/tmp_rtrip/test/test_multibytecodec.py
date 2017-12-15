from test import support
from test.support import TESTFN
import unittest, io, codecs, sys
import _multibytecodec
ALL_CJKENCODINGS = ['gb2312', 'gbk', 'gb18030', 'hz', 'big5hkscs', 'cp932',
    'shift_jis', 'euc_jp', 'euc_jisx0213', 'shift_jisx0213', 'euc_jis_2004',
    'shift_jis_2004', 'cp949', 'euc_kr', 'johab', 'big5', 'cp950',
    'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_2004',
    'iso2022_jp_3', 'iso2022_jp_ext', 'iso2022_kr']


class Test_MultibyteCodec(unittest.TestCase):

    def test_nullcoding(self):
        for enc in ALL_CJKENCODINGS:
            self.assertEqual(b''.decode(enc), '')
            self.assertEqual(str(b'', enc), '')
            self.assertEqual(''.encode(enc), b'')

    def test_str_decode(self):
        for enc in ALL_CJKENCODINGS:
            self.assertEqual('abcd'.encode(enc), b'abcd')

    def test_errorcallback_longindex(self):
        dec = codecs.getdecoder('euc-kr')
        myreplace = lambda exc: ('', sys.maxsize + 1)
        codecs.register_error('test.cjktest', myreplace)
        self.assertRaises(IndexError, dec, b'apple\x92ham\x93spam',
            'test.cjktest')

    def test_errorcallback_custom_ignore(self):
        data = 100 * '\udc00'
        codecs.register_error('test.ignore', codecs.ignore_errors)
        for enc in ALL_CJKENCODINGS:
            self.assertEqual(data.encode(enc, 'test.ignore'), b'')

    def test_codingspec(self):
        try:
            for enc in ALL_CJKENCODINGS:
                code = '# coding: {}\n'.format(enc)
                exec(code)
        finally:
            support.unlink(TESTFN)

    def test_init_segfault(self):
        self.assertRaises(AttributeError, _multibytecodec.
            MultibyteStreamReader, None)
        self.assertRaises(AttributeError, _multibytecodec.
            MultibyteStreamWriter, None)

    def test_decode_unicode(self):
        for enc in ALL_CJKENCODINGS:
            self.assertRaises(TypeError, codecs.getdecoder(enc), '')


class Test_IncrementalEncoder(unittest.TestCase):

    def test_stateless(self):
        encoder = codecs.getincrementalencoder('cp949')()
        self.assertEqual(encoder.encode('파이썬 마을'),
            b'\xc6\xc4\xc0\xcc\xbd\xe3 \xb8\xb6\xc0\xbb')
        self.assertEqual(encoder.reset(), None)
        self.assertEqual(encoder.encode('☆∼☆', True),
            b'\xa1\xd9\xa1\xad\xa1\xd9')
        self.assertEqual(encoder.reset(), None)
        self.assertEqual(encoder.encode('', True), b'')
        self.assertEqual(encoder.encode('', False), b'')
        self.assertEqual(encoder.reset(), None)

    def test_stateful(self):
        encoder = codecs.getincrementalencoder('jisx0213')()
        self.assertEqual(encoder.encode('æ̀'), b'\xab\xc4')
        self.assertEqual(encoder.encode('æ'), b'')
        self.assertEqual(encoder.encode('̀'), b'\xab\xc4')
        self.assertEqual(encoder.encode('æ', True), b'\xa9\xdc')
        self.assertEqual(encoder.reset(), None)
        self.assertEqual(encoder.encode('̀'), b'\xab\xdc')
        self.assertEqual(encoder.encode('æ'), b'')
        self.assertEqual(encoder.encode('', True), b'\xa9\xdc')
        self.assertEqual(encoder.encode('', True), b'')

    def test_stateful_keep_buffer(self):
        encoder = codecs.getincrementalencoder('jisx0213')()
        self.assertEqual(encoder.encode('æ'), b'')
        self.assertRaises(UnicodeEncodeError, encoder.encode, 'ģ')
        self.assertEqual(encoder.encode('̀æ'), b'\xab\xc4')
        self.assertRaises(UnicodeEncodeError, encoder.encode, 'ģ')
        self.assertEqual(encoder.reset(), None)
        self.assertEqual(encoder.encode('̀'), b'\xab\xdc')
        self.assertEqual(encoder.encode('æ'), b'')
        self.assertRaises(UnicodeEncodeError, encoder.encode, 'ģ')
        self.assertEqual(encoder.encode('', True), b'\xa9\xdc')

    def test_issue5640(self):
        encoder = codecs.getincrementalencoder('shift-jis')('backslashreplace')
        self.assertEqual(encoder.encode('ÿ'), b'\\xff')
        self.assertEqual(encoder.encode('\n'), b'\n')


class Test_IncrementalDecoder(unittest.TestCase):

    def test_dbcs(self):
        decoder = codecs.getincrementaldecoder('cp949')()
        self.assertEqual(decoder.decode(b'\xc6\xc4\xc0\xcc\xbd'), '파이')
        self.assertEqual(decoder.decode(b'\xe3 \xb8\xb6\xc0\xbb'), '썬 마을')
        self.assertEqual(decoder.decode(b''), '')

    def test_dbcs_keep_buffer(self):
        decoder = codecs.getincrementaldecoder('cp949')()
        self.assertEqual(decoder.decode(b'\xc6\xc4\xc0'), '파')
        self.assertRaises(UnicodeDecodeError, decoder.decode, b'', True)
        self.assertEqual(decoder.decode(b'\xcc'), '이')
        self.assertEqual(decoder.decode(b'\xc6\xc4\xc0'), '파')
        self.assertRaises(UnicodeDecodeError, decoder.decode, b'\xcc\xbd', True
            )
        self.assertEqual(decoder.decode(b'\xcc'), '이')

    def test_iso2022(self):
        decoder = codecs.getincrementaldecoder('iso2022-jp')()
        ESC = b'\x1b'
        self.assertEqual(decoder.decode(ESC + b'('), '')
        self.assertEqual(decoder.decode(b'B', True), '')
        self.assertEqual(decoder.decode(ESC + b'$'), '')
        self.assertEqual(decoder.decode(b'B@$'), '世')
        self.assertEqual(decoder.decode(b'@$@'), '世')
        self.assertEqual(decoder.decode(b'$', True), '世')
        self.assertEqual(decoder.reset(), None)
        self.assertEqual(decoder.decode(b'@$'), '@$')
        self.assertEqual(decoder.decode(ESC + b'$'), '')
        self.assertRaises(UnicodeDecodeError, decoder.decode, b'', True)
        self.assertEqual(decoder.decode(b'B@$'), '世')

    def test_decode_unicode(self):
        for enc in ALL_CJKENCODINGS:
            decoder = codecs.getincrementaldecoder(enc)()
            self.assertRaises(TypeError, decoder.decode, '')


class Test_StreamReader(unittest.TestCase):

    def test_bug1728403(self):
        try:
            f = open(TESTFN, 'wb')
            try:
                f.write(b'\xa1')
            finally:
                f.close()
            f = codecs.open(TESTFN, encoding='cp949')
            try:
                self.assertRaises(UnicodeDecodeError, f.read, 2)
            finally:
                f.close()
        finally:
            support.unlink(TESTFN)


class Test_StreamWriter(unittest.TestCase):

    def test_gb18030(self):
        s = io.BytesIO()
        c = codecs.getwriter('gb18030')(s)
        c.write('123')
        self.assertEqual(s.getvalue(), b'123')
        c.write('𒍅')
        self.assertEqual(s.getvalue(), b'123\x907\x959')
        c.write('가¬')
        self.assertEqual(s.getvalue(), b'123\x907\x959\x827\xcf5\x810\x851')

    def test_utf_8(self):
        s = io.BytesIO()
        c = codecs.getwriter('utf-8')(s)
        c.write('123')
        self.assertEqual(s.getvalue(), b'123')
        c.write('𒍅')
        self.assertEqual(s.getvalue(), b'123\xf0\x92\x8d\x85')
        c.write('가¬')
        self.assertEqual(s.getvalue(),
            b'123\xf0\x92\x8d\x85\xea\xb0\x80\xc2\xac')

    def test_streamwriter_strwrite(self):
        s = io.BytesIO()
        wr = codecs.getwriter('gb18030')(s)
        wr.write('abcd')
        self.assertEqual(s.getvalue(), b'abcd')


class Test_ISO2022(unittest.TestCase):

    def test_g2(self):
        iso2022jp2 = b'\x1b(B:hu4:unit\x1b.A\x1bNi de famille'
        uni = ':hu4:unité de famille'
        self.assertEqual(iso2022jp2.decode('iso2022-jp-2'), uni)

    def test_iso2022_jp_g0(self):
        self.assertNotIn(b'\x0e', '\xad'.encode('iso-2022-jp-2'))
        for encoding in ('iso-2022-jp-2004', 'iso-2022-jp-3'):
            e = '㐆'.encode(encoding)
            self.assertFalse(any(x > 128 for x in e))

    def test_bug1572832(self):
        for x in range(65536, 1114112):
            chr(x).encode('iso_2022_jp', 'ignore')


class TestStateful(unittest.TestCase):
    text = '世世'
    encoding = 'iso-2022-jp'
    expected = b'\x1b$B@$@$'
    reset = b'\x1b(B'
    expected_reset = expected + reset

    def test_encode(self):
        self.assertEqual(self.text.encode(self.encoding), self.expected_reset)

    def test_incrementalencoder(self):
        encoder = codecs.getincrementalencoder(self.encoding)()
        output = b''.join(encoder.encode(char) for char in self.text)
        self.assertEqual(output, self.expected)
        self.assertEqual(encoder.encode('', final=True), self.reset)
        self.assertEqual(encoder.encode('', final=True), b'')

    def test_incrementalencoder_final(self):
        encoder = codecs.getincrementalencoder(self.encoding)()
        last_index = len(self.text) - 1
        output = b''.join(encoder.encode(char, index == last_index) for 
            index, char in enumerate(self.text))
        self.assertEqual(output, self.expected_reset)
        self.assertEqual(encoder.encode('', final=True), b'')


class TestHZStateful(TestStateful):
    text = '聊聊'
    encoding = 'hz'
    expected = b'~{ADAD'
    reset = b'~}'
    expected_reset = expected + reset


def test_main():
    support.run_unittest(__name__)


if __name__ == '__main__':
    test_main()
