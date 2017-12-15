"""
Tests for uu module.
Nick Mathewson
"""
import unittest
from test import support
import sys, os
import uu
import io
plaintext = b'The smooth-scaled python crept over the sleeping dog\n'
encodedtext = (
    b'M5&AE(\'-M;V]T:"US8V%L960@<\'ET:&]N(&-R97!T(&]V97(@=&AE(\'-L965P\n(:6YG(&1O9PH '
    )


class FakeIO(io.TextIOWrapper):
    """Text I/O implementation using an in-memory buffer.

    Can be a used as a drop-in replacement for sys.stdin and sys.stdout.
    """

    def __init__(self, initial_value='', encoding='utf-8', errors='strict',
        newline='\n'):
        super(FakeIO, self).__init__(io.BytesIO(), encoding=encoding,
            errors=errors, newline=newline)
        self._encoding = encoding
        self._errors = errors
        if initial_value:
            if not isinstance(initial_value, str):
                initial_value = str(initial_value)
            self.write(initial_value)
            self.seek(0)

    def getvalue(self):
        self.flush()
        return self.buffer.getvalue().decode(self._encoding, self._errors)


def encodedtextwrapped(mode, filename):
    return bytes('begin %03o %s\n' % (mode, filename), 'ascii'
        ) + encodedtext + b'\n \nend\n'


class UUTest(unittest.TestCase):

    def test_encode(self):
        inp = io.BytesIO(plaintext)
        out = io.BytesIO()
        uu.encode(inp, out, 't1')
        self.assertEqual(out.getvalue(), encodedtextwrapped(438, 't1'))
        inp = io.BytesIO(plaintext)
        out = io.BytesIO()
        uu.encode(inp, out, 't1', 420)
        self.assertEqual(out.getvalue(), encodedtextwrapped(420, 't1'))

    def test_decode(self):
        inp = io.BytesIO(encodedtextwrapped(438, 't1'))
        out = io.BytesIO()
        uu.decode(inp, out)
        self.assertEqual(out.getvalue(), plaintext)
        inp = io.BytesIO(b'UUencoded files may contain many lines,\n' +
            b"even some that have 'begin' in them.\n" + encodedtextwrapped(
            438, 't1'))
        out = io.BytesIO()
        uu.decode(inp, out)
        self.assertEqual(out.getvalue(), plaintext)

    def test_truncatedinput(self):
        inp = io.BytesIO(b'begin 644 t1\n' + encodedtext)
        out = io.BytesIO()
        try:
            uu.decode(inp, out)
            self.fail('No exception raised')
        except uu.Error as e:
            self.assertEqual(str(e), 'Truncated input file')

    def test_missingbegin(self):
        inp = io.BytesIO(b'')
        out = io.BytesIO()
        try:
            uu.decode(inp, out)
            self.fail('No exception raised')
        except uu.Error as e:
            self.assertEqual(str(e), 'No valid begin line found in input file')

    def test_garbage_padding(self):
        encodedtext = b'begin 644 file\n!,___\n \nend\n'
        plaintext = b'3'
        with self.subTest('uu.decode()'):
            inp = io.BytesIO(encodedtext)
            out = io.BytesIO()
            uu.decode(inp, out, quiet=True)
            self.assertEqual(out.getvalue(), plaintext)
        with self.subTest('uu_codec'):
            import codecs
            decoded = codecs.decode(encodedtext, 'uu_codec')
            self.assertEqual(decoded, plaintext)


class UUStdIOTest(unittest.TestCase):

    def setUp(self):
        self.stdin = sys.stdin
        self.stdout = sys.stdout

    def tearDown(self):
        sys.stdin = self.stdin
        sys.stdout = self.stdout

    def test_encode(self):
        sys.stdin = FakeIO(plaintext.decode('ascii'))
        sys.stdout = FakeIO()
        uu.encode('-', '-', 't1', 438)
        self.assertEqual(sys.stdout.getvalue(), encodedtextwrapped(438,
            't1').decode('ascii'))

    def test_decode(self):
        sys.stdin = FakeIO(encodedtextwrapped(438, 't1').decode('ascii'))
        sys.stdout = FakeIO()
        uu.decode('-', '-')
        stdout = sys.stdout
        sys.stdout = self.stdout
        sys.stdin = self.stdin
        self.assertEqual(stdout.getvalue(), plaintext.decode('ascii'))


class UUFileTest(unittest.TestCase):

    def _kill(self, f):
        if f is None:
            return
        try:
            f.close()
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            pass
        try:
            os.unlink(f.name)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            pass

    def setUp(self):
        self.tmpin = support.TESTFN + 'i'
        self.tmpout = support.TESTFN + 'o'

    def tearDown(self):
        del self.tmpin
        del self.tmpout

    def test_encode(self):
        fin = fout = None
        try:
            support.unlink(self.tmpin)
            fin = open(self.tmpin, 'wb')
            fin.write(plaintext)
            fin.close()
            fin = open(self.tmpin, 'rb')
            fout = open(self.tmpout, 'wb')
            uu.encode(fin, fout, self.tmpin, mode=420)
            fin.close()
            fout.close()
            fout = open(self.tmpout, 'rb')
            s = fout.read()
            fout.close()
            self.assertEqual(s, encodedtextwrapped(420, self.tmpin))
            uu.encode(self.tmpin, self.tmpout, self.tmpin, mode=420)
            fout = open(self.tmpout, 'rb')
            s = fout.read()
            fout.close()
            self.assertEqual(s, encodedtextwrapped(420, self.tmpin))
        finally:
            self._kill(fin)
            self._kill(fout)

    def test_decode(self):
        f = None
        try:
            support.unlink(self.tmpin)
            f = open(self.tmpin, 'wb')
            f.write(encodedtextwrapped(420, self.tmpout))
            f.close()
            f = open(self.tmpin, 'rb')
            uu.decode(f)
            f.close()
            f = open(self.tmpout, 'rb')
            s = f.read()
            f.close()
            self.assertEqual(s, plaintext)
        finally:
            self._kill(f)

    def test_decode_filename(self):
        f = None
        try:
            support.unlink(self.tmpin)
            f = open(self.tmpin, 'wb')
            f.write(encodedtextwrapped(420, self.tmpout))
            f.close()
            uu.decode(self.tmpin)
            f = open(self.tmpout, 'rb')
            s = f.read()
            f.close()
            self.assertEqual(s, plaintext)
        finally:
            self._kill(f)

    def test_decodetwice(self):
        f = None
        try:
            f = io.BytesIO(encodedtextwrapped(420, self.tmpout))
            f = open(self.tmpin, 'rb')
            uu.decode(f)
            f.close()
            f = open(self.tmpin, 'rb')
            self.assertRaises(uu.Error, uu.decode, f)
            f.close()
        finally:
            self._kill(f)


def test_main():
    support.run_unittest(UUTest, UUStdIOTest, UUFileTest)


if __name__ == '__main__':
    test_main()
