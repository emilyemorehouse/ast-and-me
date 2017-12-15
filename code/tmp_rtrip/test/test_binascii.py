"""Test the binascii C module."""
import unittest
import binascii
import array
b2a_functions = ['b2a_base64', 'b2a_hex', 'b2a_hqx', 'b2a_qp', 'b2a_uu',
    'hexlify', 'rlecode_hqx']
a2b_functions = ['a2b_base64', 'a2b_hex', 'a2b_hqx', 'a2b_qp', 'a2b_uu',
    'unhexlify', 'rledecode_hqx']
all_functions = a2b_functions + b2a_functions + ['crc32', 'crc_hqx']


class BinASCIITest(unittest.TestCase):
    type2test = bytes
    rawdata = b'The quick brown fox jumps over the lazy dog.\r\n'
    rawdata += bytes(range(256))
    rawdata += b'\r\nHello world.\n'

    def setUp(self):
        self.data = self.type2test(self.rawdata)

    def test_exceptions(self):
        self.assertTrue(issubclass(binascii.Error, Exception))
        self.assertTrue(issubclass(binascii.Incomplete, Exception))

    def test_functions(self):
        for name in all_functions:
            self.assertTrue(hasattr(getattr(binascii, name), '__call__'))
            self.assertRaises(TypeError, getattr(binascii, name))

    def test_returned_value(self):
        MAX_ALL = 45
        raw = self.rawdata[:MAX_ALL]
        for fa, fb in zip(a2b_functions, b2a_functions):
            a2b = getattr(binascii, fa)
            b2a = getattr(binascii, fb)
            try:
                a = b2a(self.type2test(raw))
                res = a2b(self.type2test(a))
            except Exception as err:
                self.fail('{}/{} conversion raises {!r}'.format(fb, fa, err))
            if fb == 'b2a_hqx':
                res, _ = res
            self.assertEqual(res, raw, '{}/{} conversion: {!r} != {!r}'.
                format(fb, fa, res, raw))
            self.assertIsInstance(res, bytes)
            self.assertIsInstance(a, bytes)
            self.assertLess(max(a), 128)
        self.assertIsInstance(binascii.crc_hqx(raw, 0), int)
        self.assertIsInstance(binascii.crc32(raw), int)

    def test_base64valid(self):
        MAX_BASE64 = 57
        lines = []
        for i in range(0, len(self.rawdata), MAX_BASE64):
            b = self.type2test(self.rawdata[i:i + MAX_BASE64])
            a = binascii.b2a_base64(b)
            lines.append(a)
        res = bytes()
        for line in lines:
            a = self.type2test(line)
            b = binascii.a2b_base64(a)
            res += b
        self.assertEqual(res, self.rawdata)

    def test_base64invalid(self):
        MAX_BASE64 = 57
        lines = []
        for i in range(0, len(self.data), MAX_BASE64):
            b = self.type2test(self.rawdata[i:i + MAX_BASE64])
            a = binascii.b2a_base64(b)
            lines.append(a)
        fillers = bytearray()
        valid = (
            b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/'
            )
        for i in range(256):
            if i not in valid:
                fillers.append(i)

        def addnoise(line):
            noise = fillers
            ratio = len(line) // len(noise)
            res = bytearray()
            while line and noise:
                if len(line) // len(noise) > ratio:
                    c, line = line[0], line[1:]
                else:
                    c, noise = noise[0], noise[1:]
                res.append(c)
            return res + noise + line
        res = bytearray()
        for line in map(addnoise, lines):
            a = self.type2test(line)
            b = binascii.a2b_base64(a)
            res += b
        self.assertEqual(res, self.rawdata)
        self.assertEqual(binascii.a2b_base64(self.type2test(fillers)), b'')

    def test_uu(self):
        MAX_UU = 45
        lines = []
        for i in range(0, len(self.data), MAX_UU):
            b = self.type2test(self.rawdata[i:i + MAX_UU])
            a = binascii.b2a_uu(b)
            lines.append(a)
        res = bytes()
        for line in lines:
            a = self.type2test(line)
            b = binascii.a2b_uu(a)
            res += b
        self.assertEqual(res, self.rawdata)
        self.assertEqual(binascii.a2b_uu(b'\x7f'), b'\x00' * 31)
        self.assertEqual(binascii.a2b_uu(b'\x80'), b'\x00' * 32)
        self.assertEqual(binascii.a2b_uu(b'\xff'), b'\x00' * 31)
        self.assertRaises(binascii.Error, binascii.a2b_uu, b'\xff\x00')
        self.assertRaises(binascii.Error, binascii.a2b_uu, b'!!!!')
        self.assertRaises(binascii.Error, binascii.b2a_uu, 46 * b'!')
        self.assertEqual(binascii.b2a_uu(b'x'), b'!>   \n')

    def test_crc_hqx(self):
        crc = binascii.crc_hqx(self.type2test(b'Test the CRC-32 of'), 0)
        crc = binascii.crc_hqx(self.type2test(b' this string.'), crc)
        self.assertEqual(crc, 14290)
        self.assertRaises(TypeError, binascii.crc_hqx)
        self.assertRaises(TypeError, binascii.crc_hqx, self.type2test(b''))
        for crc in (0, 1, 4660, 74565, 305419896, -1):
            self.assertEqual(binascii.crc_hqx(self.type2test(b''), crc), 
                crc & 65535)

    def test_crc32(self):
        crc = binascii.crc32(self.type2test(b'Test the CRC-32 of'))
        crc = binascii.crc32(self.type2test(b' this string.'), crc)
        self.assertEqual(crc, 1571220330)
        self.assertRaises(TypeError, binascii.crc32)

    def test_hqx(self):
        rle = binascii.rlecode_hqx(self.data)
        a = binascii.b2a_hqx(self.type2test(rle))
        b, _ = binascii.a2b_hqx(self.type2test(a))
        res = binascii.rledecode_hqx(b)
        self.assertEqual(res, self.rawdata)

    def test_rle(self):
        data = b'a' * 100 + b'b' + b'c' * 300
        encoded = binascii.rlecode_hqx(data)
        self.assertEqual(encoded, b'a\x90dbc\x90\xffc\x90-')
        decoded = binascii.rledecode_hqx(encoded)
        self.assertEqual(decoded, data)

    def test_hex(self):
        s = (
            b'{s\x05\x00\x00\x00worldi\x02\x00\x00\x00s\x05\x00\x00\x00helloi\x01\x00\x00\x000'
            )
        t = binascii.b2a_hex(self.type2test(s))
        u = binascii.a2b_hex(self.type2test(t))
        self.assertEqual(s, u)
        self.assertRaises(binascii.Error, binascii.a2b_hex, t[:-1])
        self.assertRaises(binascii.Error, binascii.a2b_hex, t[:-1] + b'q')
        self.assertEqual(binascii.hexlify(self.type2test(s)), t)
        self.assertEqual(binascii.unhexlify(self.type2test(t)), u)

    def test_qp(self):
        type2test = self.type2test
        a2b_qp = binascii.a2b_qp
        b2a_qp = binascii.b2a_qp
        a2b_qp(data=b'', header=False)
        try:
            a2b_qp(b'', **{(1): 1})
        except TypeError:
            pass
        else:
            self.fail("binascii.a2b_qp(**{1:1}) didn't raise TypeError")
        self.assertEqual(a2b_qp(type2test(b'=')), b'')
        self.assertEqual(a2b_qp(type2test(b'= ')), b'= ')
        self.assertEqual(a2b_qp(type2test(b'==')), b'=')
        self.assertEqual(a2b_qp(type2test(b'=\nAB')), b'AB')
        self.assertEqual(a2b_qp(type2test(b'=\r\nAB')), b'AB')
        self.assertEqual(a2b_qp(type2test(b'=\rAB')), b'')
        self.assertEqual(a2b_qp(type2test(b'=\rAB\nCD')), b'CD')
        self.assertEqual(a2b_qp(type2test(b'=AB')), b'\xab')
        self.assertEqual(a2b_qp(type2test(b'=ab')), b'\xab')
        self.assertEqual(a2b_qp(type2test(b'=AX')), b'=AX')
        self.assertEqual(a2b_qp(type2test(b'=XA')), b'=XA')
        self.assertEqual(a2b_qp(type2test(b'=AB')[:-1]), b'=A')
        self.assertEqual(a2b_qp(type2test(b'_')), b'_')
        self.assertEqual(a2b_qp(type2test(b'_'), header=True), b' ')
        self.assertRaises(TypeError, b2a_qp, foo='bar')
        self.assertEqual(a2b_qp(type2test(b'=00\r\n=00')), b'\x00\r\n\x00')
        self.assertEqual(b2a_qp(type2test(b'\xff\r\n\xff\n\xff')),
            b'=FF\r\n=FF\r\n=FF')
        self.assertEqual(b2a_qp(type2test(b'0' * 75 +
            b'\xff\r\n\xff\r\n\xff')), b'0' * 75 + b'=\r\n=FF\r\n=FF\r\n=FF')
        self.assertEqual(b2a_qp(type2test(b'\x7f')), b'=7F')
        self.assertEqual(b2a_qp(type2test(b'=')), b'=3D')
        self.assertEqual(b2a_qp(type2test(b'_')), b'_')
        self.assertEqual(b2a_qp(type2test(b'_'), header=True), b'=5F')
        self.assertEqual(b2a_qp(type2test(b'x y'), header=True), b'x_y')
        self.assertEqual(b2a_qp(type2test(b'x '), header=True), b'x=20')
        self.assertEqual(b2a_qp(type2test(b'x y'), header=True, quotetabs=
            True), b'x=20y')
        self.assertEqual(b2a_qp(type2test(b'x\ty'), header=True), b'x\ty')
        self.assertEqual(b2a_qp(type2test(b' ')), b'=20')
        self.assertEqual(b2a_qp(type2test(b'\t')), b'=09')
        self.assertEqual(b2a_qp(type2test(b' x')), b' x')
        self.assertEqual(b2a_qp(type2test(b'\tx')), b'\tx')
        self.assertEqual(b2a_qp(type2test(b' x')[:-1]), b'=20')
        self.assertEqual(b2a_qp(type2test(b'\tx')[:-1]), b'=09')
        self.assertEqual(b2a_qp(type2test(b'\x00')), b'=00')
        self.assertEqual(b2a_qp(type2test(b'\x00\n')), b'=00\n')
        self.assertEqual(b2a_qp(type2test(b'\x00\n'), quotetabs=True), b'=00\n'
            )
        self.assertEqual(b2a_qp(type2test(b'x y\tz')), b'x y\tz')
        self.assertEqual(b2a_qp(type2test(b'x y\tz'), quotetabs=True),
            b'x=20y=09z')
        self.assertEqual(b2a_qp(type2test(b'x y\tz'), istext=False), b'x y\tz')
        self.assertEqual(b2a_qp(type2test(b'x \ny\t\n')), b'x=20\ny=09\n')
        self.assertEqual(b2a_qp(type2test(b'x \ny\t\n'), quotetabs=True),
            b'x=20\ny=09\n')
        self.assertEqual(b2a_qp(type2test(b'x \ny\t\n'), istext=False),
            b'x =0Ay\t=0A')
        self.assertEqual(b2a_qp(type2test(b'x \ry\t\r')), b'x \ry\t\r')
        self.assertEqual(b2a_qp(type2test(b'x \ry\t\r'), quotetabs=True),
            b'x=20\ry=09\r')
        self.assertEqual(b2a_qp(type2test(b'x \ry\t\r'), istext=False),
            b'x =0Dy\t=0D')
        self.assertEqual(b2a_qp(type2test(b'x \r\ny\t\r\n')),
            b'x=20\r\ny=09\r\n')
        self.assertEqual(b2a_qp(type2test(b'x \r\ny\t\r\n'), quotetabs=True
            ), b'x=20\r\ny=09\r\n')
        self.assertEqual(b2a_qp(type2test(b'x \r\ny\t\r\n'), istext=False),
            b'x =0D=0Ay\t=0D=0A')
        self.assertEqual(b2a_qp(type2test(b'x \r\n')[:-1]), b'x \r')
        self.assertEqual(b2a_qp(type2test(b'x\t\r\n')[:-1]), b'x\t\r')
        self.assertEqual(b2a_qp(type2test(b'x \r\n')[:-1], quotetabs=True),
            b'x=20\r')
        self.assertEqual(b2a_qp(type2test(b'x\t\r\n')[:-1], quotetabs=True),
            b'x=09\r')
        self.assertEqual(b2a_qp(type2test(b'x \r\n')[:-1], istext=False),
            b'x =0D')
        self.assertEqual(b2a_qp(type2test(b'x\t\r\n')[:-1], istext=False),
            b'x\t=0D')
        self.assertEqual(b2a_qp(type2test(b'.')), b'=2E')
        self.assertEqual(b2a_qp(type2test(b'.\n')), b'=2E\n')
        self.assertEqual(b2a_qp(type2test(b'.\r')), b'=2E\r')
        self.assertEqual(b2a_qp(type2test(b'.\x00')), b'=2E=00')
        self.assertEqual(b2a_qp(type2test(b'a.\n')), b'a.\n')
        self.assertEqual(b2a_qp(type2test(b'.a')[:-1]), b'=2E')

    def test_empty_string(self):
        empty = self.type2test(b'')
        for func in all_functions:
            if func == 'crc_hqx':
                binascii.crc_hqx(empty, 0)
                continue
            f = getattr(binascii, func)
            try:
                f(empty)
            except Exception as err:
                self.fail('{}({!r}) raises {!r}'.format(func, empty, err))

    def test_unicode_b2a(self):
        for func in (set(all_functions) - set(a2b_functions) | {
            'rledecode_hqx'}):
            try:
                self.assertRaises(TypeError, getattr(binascii, func), 'test')
            except Exception as err:
                self.fail('{}("test") raises {!r}'.format(func, err))
        self.assertRaises(TypeError, binascii.crc_hqx, 'test', 0)

    def test_unicode_a2b(self):
        MAX_ALL = 45
        raw = self.rawdata[:MAX_ALL]
        for fa, fb in zip(a2b_functions, b2a_functions):
            if fa == 'rledecode_hqx':
                continue
            a2b = getattr(binascii, fa)
            b2a = getattr(binascii, fb)
            try:
                a = b2a(self.type2test(raw))
                binary_res = a2b(a)
                a = a.decode('ascii')
                res = a2b(a)
            except Exception as err:
                self.fail('{}/{} conversion raises {!r}'.format(fb, fa, err))
            if fb == 'b2a_hqx':
                res, _ = res
                binary_res, _ = binary_res
            self.assertEqual(res, raw, '{}/{} conversion: {!r} != {!r}'.
                format(fb, fa, res, raw))
            self.assertEqual(res, binary_res)
            self.assertIsInstance(res, bytes)
            self.assertRaises(ValueError, a2b, '\x80')

    def test_b2a_base64_newline(self):
        b = self.type2test(b'hello')
        self.assertEqual(binascii.b2a_base64(b), b'aGVsbG8=\n')
        self.assertEqual(binascii.b2a_base64(b, newline=True), b'aGVsbG8=\n')
        self.assertEqual(binascii.b2a_base64(b, newline=False), b'aGVsbG8=')


class ArrayBinASCIITest(BinASCIITest):

    def type2test(self, s):
        return array.array('B', list(s))


class BytearrayBinASCIITest(BinASCIITest):
    type2test = bytearray


class MemoryviewBinASCIITest(BinASCIITest):
    type2test = memoryview


if __name__ == '__main__':
    unittest.main()
