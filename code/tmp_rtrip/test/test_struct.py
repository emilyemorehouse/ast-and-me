from collections import abc
import array
import math
import operator
import unittest
import struct
import sys
from test import support
ISBIGENDIAN = sys.byteorder == 'big'
integer_codes = 'b', 'B', 'h', 'H', 'i', 'I', 'l', 'L', 'q', 'Q', 'n', 'N'
byteorders = '', '@', '=', '<', '>', '!'


def iter_integer_formats(byteorders=byteorders):
    for code in integer_codes:
        for byteorder in byteorders:
            if byteorder not in ('', '@') and code in ('n', 'N'):
                continue
            yield code, byteorder


def string_reverse(s):
    return s[::-1]


def bigendian_to_native(value):
    if ISBIGENDIAN:
        return value
    else:
        return string_reverse(value)


class StructTest(unittest.TestCase):

    def test_isbigendian(self):
        self.assertEqual(struct.pack('=i', 1)[0] == 0, ISBIGENDIAN)

    def test_consistence(self):
        self.assertRaises(struct.error, struct.calcsize, 'Z')
        sz = struct.calcsize('i')
        self.assertEqual(sz * 3, struct.calcsize('iii'))
        fmt = 'cbxxxxxxhhhhiillffd?'
        fmt3 = '3c3b18x12h6i6l6f3d3?'
        sz = struct.calcsize(fmt)
        sz3 = struct.calcsize(fmt3)
        self.assertEqual(sz * 3, sz3)
        self.assertRaises(struct.error, struct.pack, 'iii', 3)
        self.assertRaises(struct.error, struct.pack, 'i', 3, 3, 3)
        self.assertRaises((TypeError, struct.error), struct.pack, 'i', 'foo')
        self.assertRaises((TypeError, struct.error), struct.pack, 'P', 'foo')
        self.assertRaises(struct.error, struct.unpack, 'd', b'flap')
        s = struct.pack('ii', 1, 2)
        self.assertRaises(struct.error, struct.unpack, 'iii', s)
        self.assertRaises(struct.error, struct.unpack, 'i', s)

    def test_transitiveness(self):
        c = b'a'
        b = 1
        h = 255
        i = 65535
        l = 65536
        f = 3.1415
        d = 3.1415
        t = True
        for prefix in ('', '@', '<', '>', '=', '!'):
            for format in ('xcbhilfd?', 'xcBHILfd?'):
                format = prefix + format
                s = struct.pack(format, c, b, h, i, l, f, d, t)
                cp, bp, hp, ip, lp, fp, dp, tp = struct.unpack(format, s)
                self.assertEqual(cp, c)
                self.assertEqual(bp, b)
                self.assertEqual(hp, h)
                self.assertEqual(ip, i)
                self.assertEqual(lp, l)
                self.assertEqual(int(100 * fp), int(100 * f))
                self.assertEqual(int(100 * dp), int(100 * d))
                self.assertEqual(tp, t)

    def test_new_features(self):
        tests = [('c', b'a', b'a', b'a', 0), ('xc', b'a', b'\x00a',
            b'\x00a', 0), ('cx', b'a', b'a\x00', b'a\x00', 0), ('s', b'a',
            b'a', b'a', 0), ('0s', b'helloworld', b'', b'', 1), ('1s',
            b'helloworld', b'h', b'h', 1), ('9s', b'helloworld',
            b'helloworl', b'helloworl', 1), ('10s', b'helloworld',
            b'helloworld', b'helloworld', 0), ('11s', b'helloworld',
            b'helloworld\x00', b'helloworld\x00', 1), ('20s', b'helloworld',
            b'helloworld' + 10 * b'\x00', b'helloworld' + 10 * b'\x00', 1),
            ('b', 7, b'\x07', b'\x07', 0), ('b', -7, b'\xf9', b'\xf9', 0),
            ('B', 7, b'\x07', b'\x07', 0), ('B', 249, b'\xf9', b'\xf9', 0),
            ('h', 700, b'\x02\xbc', b'\xbc\x02', 0), ('h', -700, b'\xfdD',
            b'D\xfd', 0), ('H', 700, b'\x02\xbc', b'\xbc\x02', 0), ('H', 
            65536 - 700, b'\xfdD', b'D\xfd', 0), ('i', 70000000,
            b'\x04,\x1d\x80', b'\x80\x1d,\x04', 0), ('i', -70000000,
            b'\xfb\xd3\xe2\x80', b'\x80\xe2\xd3\xfb', 0), ('I', 70000000,
            b'\x04,\x1d\x80', b'\x80\x1d,\x04', 0), ('I', 4294967296 - 
            70000000, b'\xfb\xd3\xe2\x80', b'\x80\xe2\xd3\xfb', 0), ('l', 
            70000000, b'\x04,\x1d\x80', b'\x80\x1d,\x04', 0), ('l', -
            70000000, b'\xfb\xd3\xe2\x80', b'\x80\xe2\xd3\xfb', 0), ('L', 
            70000000, b'\x04,\x1d\x80', b'\x80\x1d,\x04', 0), ('L', 
            4294967296 - 70000000, b'\xfb\xd3\xe2\x80', b'\x80\xe2\xd3\xfb',
            0), ('f', 2.0, b'@\x00\x00\x00', b'\x00\x00\x00@', 0), ('d', 
            2.0, b'@\x00\x00\x00\x00\x00\x00\x00',
            b'\x00\x00\x00\x00\x00\x00\x00@', 0), ('f', -2.0,
            b'\xc0\x00\x00\x00', b'\x00\x00\x00\xc0', 0), ('d', -2.0,
            b'\xc0\x00\x00\x00\x00\x00\x00\x00',
            b'\x00\x00\x00\x00\x00\x00\x00\xc0', 0), ('?', 0, b'\x00',
            b'\x00', 0), ('?', 3, b'\x01', b'\x01', 1), ('?', True, b'\x01',
            b'\x01', 0), ('?', [], b'\x00', b'\x00', 1), ('?', (1,),
            b'\x01', b'\x01', 1)]
        for fmt, arg, big, lil, asy in tests:
            for xfmt, exp in [('>' + fmt, big), ('!' + fmt, big), ('<' +
                fmt, lil), ('=' + fmt, ISBIGENDIAN and big or lil)]:
                res = struct.pack(xfmt, arg)
                self.assertEqual(res, exp)
                self.assertEqual(struct.calcsize(xfmt), len(res))
                rev = struct.unpack(xfmt, res)[0]
                if rev != arg:
                    self.assertTrue(asy)

    def test_calcsize(self):
        expected_size = {'b': 1, 'B': 1, 'h': 2, 'H': 2, 'i': 4, 'I': 4,
            'l': 4, 'L': 4, 'q': 8, 'Q': 8}
        for code, byteorder in iter_integer_formats(('=', '<', '>', '!')):
            format = byteorder + code
            size = struct.calcsize(format)
            self.assertEqual(size, expected_size[code])
        native_pairs = 'bB', 'hH', 'iI', 'lL', 'nN', 'qQ'
        for format_pair in native_pairs:
            for byteorder in ('', '@'):
                signed_size = struct.calcsize(byteorder + format_pair[0])
                unsigned_size = struct.calcsize(byteorder + format_pair[1])
                self.assertEqual(signed_size, unsigned_size)
        self.assertEqual(struct.calcsize('b'), 1)
        self.assertLessEqual(2, struct.calcsize('h'))
        self.assertLessEqual(4, struct.calcsize('l'))
        self.assertLessEqual(struct.calcsize('h'), struct.calcsize('i'))
        self.assertLessEqual(struct.calcsize('i'), struct.calcsize('l'))
        self.assertLessEqual(8, struct.calcsize('q'))
        self.assertLessEqual(struct.calcsize('l'), struct.calcsize('q'))
        self.assertGreaterEqual(struct.calcsize('n'), struct.calcsize('i'))
        self.assertGreaterEqual(struct.calcsize('n'), struct.calcsize('P'))

    def test_integers(self):
        import binascii


        class IntTester(unittest.TestCase):

            def __init__(self, format):
                super(IntTester, self).__init__(methodName='test_one')
                self.format = format
                self.code = format[-1]
                self.byteorder = format[:-1]
                if not self.byteorder in byteorders:
                    raise ValueError('unrecognized packing byteorder: %s' %
                        self.byteorder)
                self.bytesize = struct.calcsize(format)
                self.bitsize = self.bytesize * 8
                if self.code in tuple('bhilqn'):
                    self.signed = True
                    self.min_value = -2 ** (self.bitsize - 1)
                    self.max_value = 2 ** (self.bitsize - 1) - 1
                elif self.code in tuple('BHILQN'):
                    self.signed = False
                    self.min_value = 0
                    self.max_value = 2 ** self.bitsize - 1
                else:
                    raise ValueError('unrecognized format code: %s' % self.code
                        )

            def test_one(self, x, pack=struct.pack, unpack=struct.unpack,
                unhexlify=binascii.unhexlify):
                format = self.format
                if self.min_value <= x <= self.max_value:
                    expected = x
                    if self.signed and x < 0:
                        expected += 1 << self.bitsize
                    self.assertGreaterEqual(expected, 0)
                    expected = '%x' % expected
                    if len(expected) & 1:
                        expected = '0' + expected
                    expected = expected.encode('ascii')
                    expected = unhexlify(expected)
                    expected = b'\x00' * (self.bytesize - len(expected)
                        ) + expected
                    if self.byteorder == '<' or self.byteorder in ('', '@', '='
                        ) and not ISBIGENDIAN:
                        expected = string_reverse(expected)
                    self.assertEqual(len(expected), self.bytesize)
                    got = pack(format, x)
                    self.assertEqual(got, expected)
                    retrieved = unpack(format, got)[0]
                    self.assertEqual(x, retrieved)
                    self.assertRaises((struct.error, TypeError), unpack,
                        format, b'\x01' + got)
                else:
                    self.assertRaises((OverflowError, ValueError, struct.
                        error), pack, format, x)

            def run(self):
                from random import randrange
                values = []
                for exp in range(self.bitsize + 3):
                    values.append(1 << exp)
                for i in range(self.bitsize):
                    val = 0
                    for j in range(self.bytesize):
                        val = val << 8 | randrange(256)
                    values.append(val)
                values.extend([300, 700000, sys.maxsize * 4])
                for base in values:
                    for val in (-base, base):
                        for incr in (-1, 0, 1):
                            x = val + incr
                            self.test_one(x)


                class NotAnInt:

                    def __int__(self):
                        return 42


                class Indexable(object):

                    def __init__(self, value):
                        self._value = value

                    def __index__(self):
                        return self._value


                class BadIndex(object):

                    def __index__(self):
                        raise TypeError

                    def __int__(self):
                        return 42
                self.assertRaises((TypeError, struct.error), struct.pack,
                    self.format, 'a string')
                self.assertRaises((TypeError, struct.error), struct.pack,
                    self.format, randrange)
                self.assertRaises((TypeError, struct.error), struct.pack,
                    self.format, 3 + 42j)
                self.assertRaises((TypeError, struct.error), struct.pack,
                    self.format, NotAnInt())
                self.assertRaises((TypeError, struct.error), struct.pack,
                    self.format, BadIndex())
                for obj in (Indexable(0), Indexable(10), Indexable(17),
                    Indexable(42), Indexable(100), Indexable(127)):
                    try:
                        struct.pack(format, obj)
                    except:
                        self.fail(
                            "integer code pack failed on object with '__index__' method"
                            )
                for obj in (Indexable(b'a'), Indexable('b'), Indexable(None
                    ), Indexable({'a': 1}), Indexable([1, 2, 3])):
                    self.assertRaises((TypeError, struct.error), struct.
                        pack, self.format, obj)
        for code, byteorder in iter_integer_formats():
            format = byteorder + code
            t = IntTester(format)
            t.run()

    def test_nN_code(self):

        def assertStructError(func, *args, **kwargs):
            with self.assertRaises(struct.error) as cm:
                func(*args, **kwargs)
            self.assertIn('bad char in struct format', str(cm.exception))
        for code in 'nN':
            for byteorder in ('=', '<', '>', '!'):
                format = byteorder + code
                assertStructError(struct.calcsize, format)
                assertStructError(struct.pack, format, 0)
                assertStructError(struct.unpack, format, b'')

    def test_p_code(self):
        for code, input, expected, expectedback in [('p', b'abc', b'\x00',
            b''), ('1p', b'abc', b'\x00', b''), ('2p', b'abc', b'\x01a',
            b'a'), ('3p', b'abc', b'\x02ab', b'ab'), ('4p', b'abc',
            b'\x03abc', b'abc'), ('5p', b'abc', b'\x03abc\x00', b'abc'), (
            '6p', b'abc', b'\x03abc\x00\x00', b'abc'), ('1000p', b'x' * 
            1000, b'\xff' + b'x' * 999, b'x' * 255)]:
            got = struct.pack(code, input)
            self.assertEqual(got, expected)
            got, = struct.unpack(code, got)
            self.assertEqual(got, expectedback)

    def test_705836(self):
        for base in range(1, 33):
            delta = 0.5
            while base - delta / 2.0 != base:
                delta /= 2.0
            smaller = base - delta
            packed = struct.pack('<f', smaller)
            unpacked = struct.unpack('<f', packed)[0]
            self.assertEqual(base, unpacked)
            bigpacked = struct.pack('>f', smaller)
            self.assertEqual(bigpacked, string_reverse(packed))
            unpacked = struct.unpack('>f', bigpacked)[0]
            self.assertEqual(base, unpacked)
        big = (1 << 24) - 1
        big = math.ldexp(big, 127 - 23)
        packed = struct.pack('>f', big)
        unpacked = struct.unpack('>f', packed)[0]
        self.assertEqual(big, unpacked)
        big = (1 << 25) - 1
        big = math.ldexp(big, 127 - 24)
        self.assertRaises(OverflowError, struct.pack, '>f', big)

    def test_1530559(self):
        for code, byteorder in iter_integer_formats():
            format = byteorder + code
            self.assertRaises(struct.error, struct.pack, format, 1.0)
            self.assertRaises(struct.error, struct.pack, format, 1.5)
        self.assertRaises(struct.error, struct.pack, 'P', 1.0)
        self.assertRaises(struct.error, struct.pack, 'P', 1.5)

    def test_unpack_from(self):
        test_string = b'abcd01234'
        fmt = '4s'
        s = struct.Struct(fmt)
        for cls in (bytes, bytearray):
            data = cls(test_string)
            self.assertEqual(s.unpack_from(data), (b'abcd',))
            self.assertEqual(s.unpack_from(data, 2), (b'cd01',))
            self.assertEqual(s.unpack_from(data, 4), (b'0123',))
            for i in range(6):
                self.assertEqual(s.unpack_from(data, i), (data[i:i + 4],))
            for i in range(6, len(test_string) + 1):
                self.assertRaises(struct.error, s.unpack_from, data, i)
        for cls in (bytes, bytearray):
            data = cls(test_string)
            self.assertEqual(struct.unpack_from(fmt, data), (b'abcd',))
            self.assertEqual(struct.unpack_from(fmt, data, 2), (b'cd01',))
            self.assertEqual(struct.unpack_from(fmt, data, 4), (b'0123',))
            for i in range(6):
                self.assertEqual(struct.unpack_from(fmt, data, i), (data[i:
                    i + 4],))
            for i in range(6, len(test_string) + 1):
                self.assertRaises(struct.error, struct.unpack_from, fmt,
                    data, i)
        self.assertEqual(s.unpack_from(buffer=test_string, offset=2), (
            b'cd01',))

    def test_pack_into(self):
        test_string = b'Reykjavik rocks, eow!'
        writable_buf = array.array('b', b' ' * 100)
        fmt = '21s'
        s = struct.Struct(fmt)
        s.pack_into(writable_buf, 0, test_string)
        from_buf = writable_buf.tobytes()[:len(test_string)]
        self.assertEqual(from_buf, test_string)
        s.pack_into(writable_buf, 10, test_string)
        from_buf = writable_buf.tobytes()[:len(test_string) + 10]
        self.assertEqual(from_buf, test_string[:10] + test_string)
        small_buf = array.array('b', b' ' * 10)
        self.assertRaises((ValueError, struct.error), s.pack_into,
            small_buf, 0, test_string)
        self.assertRaises((ValueError, struct.error), s.pack_into,
            small_buf, 2, test_string)
        sb = small_buf
        self.assertRaises((TypeError, struct.error), struct.pack_into, b'',
            sb, None)

    def test_pack_into_fn(self):
        test_string = b'Reykjavik rocks, eow!'
        writable_buf = array.array('b', b' ' * 100)
        fmt = '21s'
        pack_into = lambda *args: struct.pack_into(fmt, *args)
        pack_into(writable_buf, 0, test_string)
        from_buf = writable_buf.tobytes()[:len(test_string)]
        self.assertEqual(from_buf, test_string)
        pack_into(writable_buf, 10, test_string)
        from_buf = writable_buf.tobytes()[:len(test_string) + 10]
        self.assertEqual(from_buf, test_string[:10] + test_string)
        small_buf = array.array('b', b' ' * 10)
        self.assertRaises((ValueError, struct.error), pack_into, small_buf,
            0, test_string)
        self.assertRaises((ValueError, struct.error), pack_into, small_buf,
            2, test_string)

    def test_unpack_with_buffer(self):
        data1 = array.array('B', b'\x124Vx')
        data2 = memoryview(b'\x124Vx')
        for data in [data1, data2]:
            value, = struct.unpack('>I', data)
            self.assertEqual(value, 305419896)

    def test_bool(self):


        class ExplodingBool(object):

            def __bool__(self):
                raise OSError
        for prefix in (tuple('<>!=') + ('',)):
            false = (), [], [], '', 0
            true = [1], 'test', 5, -1, 4294967295 + 1, 4294967295 / 2
            falseFormat = prefix + '?' * len(false)
            packedFalse = struct.pack(falseFormat, *false)
            unpackedFalse = struct.unpack(falseFormat, packedFalse)
            trueFormat = prefix + '?' * len(true)
            packedTrue = struct.pack(trueFormat, *true)
            unpackedTrue = struct.unpack(trueFormat, packedTrue)
            self.assertEqual(len(true), len(unpackedTrue))
            self.assertEqual(len(false), len(unpackedFalse))
            for t in unpackedFalse:
                self.assertFalse(t)
            for t in unpackedTrue:
                self.assertTrue(t)
            packed = struct.pack(prefix + '?', 1)
            self.assertEqual(len(packed), struct.calcsize(prefix + '?'))
            if len(packed) != 1:
                self.assertFalse(prefix, msg=
                    'encoded bool is not one byte: %r' % packed)
            try:
                struct.pack(prefix + '?', ExplodingBool())
            except OSError:
                pass
            else:
                self.fail(
                    'Expected OSError: struct.pack(%r, ExplodingBool())' %
                    (prefix + '?'))
        for c in [b'\x01', b'\x7f', b'\xff', b'\x0f', b'\xf0']:
            self.assertTrue(struct.unpack('>?', c)[0])

    def test_count_overflow(self):
        hugecount = '{}b'.format(sys.maxsize + 1)
        self.assertRaises(struct.error, struct.calcsize, hugecount)
        hugecount2 = '{}b{}H'.format(sys.maxsize // 2, sys.maxsize // 2)
        self.assertRaises(struct.error, struct.calcsize, hugecount2)

    def test_trailing_counter(self):
        store = array.array('b', b' ' * 100)
        self.assertRaises(struct.error, struct.pack, '12345')
        self.assertRaises(struct.error, struct.unpack, '12345', '')
        self.assertRaises(struct.error, struct.pack_into, '12345', store, 0)
        self.assertRaises(struct.error, struct.unpack_from, '12345', store, 0)
        self.assertRaises(struct.error, struct.pack, 'c12345', 'x')
        self.assertRaises(struct.error, struct.unpack, 'c12345', 'x')
        self.assertRaises(struct.error, struct.pack_into, 'c12345', store, 
            0, 'x')
        self.assertRaises(struct.error, struct.unpack_from, 'c12345', store, 0)
        self.assertRaises(struct.error, struct.pack, '14s42', 'spam and eggs')
        self.assertRaises(struct.error, struct.unpack, '14s42', 'spam and eggs'
            )
        self.assertRaises(struct.error, struct.pack_into, '14s42', store, 0,
            'spam and eggs')
        self.assertRaises(struct.error, struct.unpack_from, '14s42', store, 0)

    def test_Struct_reinitialization(self):
        s = struct.Struct('i')
        s.__init__('ii')

    def check_sizeof(self, format_str, number_of_codes):
        totalsize = support.calcobjsize('2n3P')
        totalsize += struct.calcsize('P3n0P') * (number_of_codes + 1)
        support.check_sizeof(self, struct.Struct(format_str), totalsize)

    @support.cpython_only
    def test__sizeof__(self):
        for code in integer_codes:
            self.check_sizeof(code, 1)
        self.check_sizeof('BHILfdspP', 9)
        self.check_sizeof('B' * 1234, 1234)
        self.check_sizeof('fd', 2)
        self.check_sizeof('xxxxxxxxxxxxxx', 0)
        self.check_sizeof('100H', 1)
        self.check_sizeof('187s', 1)
        self.check_sizeof('20p', 1)
        self.check_sizeof('0s', 1)
        self.check_sizeof('0c', 0)


class UnpackIteratorTest(unittest.TestCase):
    """
    Tests for iterative unpacking (struct.Struct.iter_unpack).
    """

    def test_construct(self):

        def _check_iterator(it):
            self.assertIsInstance(it, abc.Iterator)
            self.assertIsInstance(it, abc.Iterable)
        s = struct.Struct('>ibcp')
        it = s.iter_unpack(b'')
        _check_iterator(it)
        it = s.iter_unpack(b'1234567')
        _check_iterator(it)
        with self.assertRaises(struct.error):
            s.iter_unpack(b'123456')
        with self.assertRaises(struct.error):
            s.iter_unpack(b'12345678')
        s = struct.Struct('>')
        with self.assertRaises(struct.error):
            s.iter_unpack(b'')
        with self.assertRaises(struct.error):
            s.iter_unpack(b'12')

    def test_iterate(self):
        s = struct.Struct('>IB')
        b = bytes(range(1, 16))
        it = s.iter_unpack(b)
        self.assertEqual(next(it), (16909060, 5))
        self.assertEqual(next(it), (101124105, 10))
        self.assertEqual(next(it), (185339150, 15))
        self.assertRaises(StopIteration, next, it)
        self.assertRaises(StopIteration, next, it)

    def test_arbitrary_buffer(self):
        s = struct.Struct('>IB')
        b = bytes(range(1, 11))
        it = s.iter_unpack(memoryview(b))
        self.assertEqual(next(it), (16909060, 5))
        self.assertEqual(next(it), (101124105, 10))
        self.assertRaises(StopIteration, next, it)
        self.assertRaises(StopIteration, next, it)

    def test_length_hint(self):
        lh = operator.length_hint
        s = struct.Struct('>IB')
        b = bytes(range(1, 16))
        it = s.iter_unpack(b)
        self.assertEqual(lh(it), 3)
        next(it)
        self.assertEqual(lh(it), 2)
        next(it)
        self.assertEqual(lh(it), 1)
        next(it)
        self.assertEqual(lh(it), 0)
        self.assertRaises(StopIteration, next, it)
        self.assertEqual(lh(it), 0)

    def test_module_func(self):
        it = struct.iter_unpack('>IB', bytes(range(1, 11)))
        self.assertEqual(next(it), (16909060, 5))
        self.assertEqual(next(it), (101124105, 10))
        self.assertRaises(StopIteration, next, it)
        self.assertRaises(StopIteration, next, it)

    def test_half_float(self):
        format_bits_float__cleanRoundtrip_list = [(b'\x00<', 1.0), (
            b'\x00\xc0', -2.0), (b'\xff{', 65504.0), (b'\x00\x04', 2 ** -14
            ), (b'\x01\x00', 2 ** -24), (b'\x00\x00', 0.0), (b'\x00\x80', -
            0.0), (b'\x00|', float('+inf')), (b'\x00\xfc', float('-inf')),
            (b'U5', 0.333251953125)]
        for le_bits, f in format_bits_float__cleanRoundtrip_list:
            be_bits = le_bits[::-1]
            self.assertEqual(f, struct.unpack('<e', le_bits)[0])
            self.assertEqual(le_bits, struct.pack('<e', f))
            self.assertEqual(f, struct.unpack('>e', be_bits)[0])
            self.assertEqual(be_bits, struct.pack('>e', f))
            if sys.byteorder == 'little':
                self.assertEqual(f, struct.unpack('e', le_bits)[0])
                self.assertEqual(le_bits, struct.pack('e', f))
            else:
                self.assertEqual(f, struct.unpack('e', be_bits)[0])
                self.assertEqual(be_bits, struct.pack('e', f))
        format_bits__nan_list = [('<e', b'\x01\xfc'), ('<e', b'\x00\xfe'),
            ('<e', b'\xff\xff'), ('<e', b'\x01|'), ('<e', b'\x00~'), ('<e',
            b'\xff\x7f')]
        for formatcode, bits in format_bits__nan_list:
            self.assertTrue(math.isnan(struct.unpack('<e', bits)[0]))
            self.assertTrue(math.isnan(struct.unpack('>e', bits[::-1])[0]))
        packed = struct.pack('<e', math.nan)
        self.assertEqual(packed[1] & 126, 126)
        packed = struct.pack('<e', -math.nan)
        self.assertEqual(packed[1] & 126, 126)
        format_bits_float__rounding_list = [('>e', b'\x00\x01', 2.0 ** -25 +
            2.0 ** -35), ('>e', b'\x00\x00', 2.0 ** -25), ('>e',
            b'\x00\x00', 2.0 ** -26), ('>e', b'\x03\xff', 2.0 ** -14 - 2.0 **
            -24), ('>e', b'\x03\xff', 2.0 ** -14 - 2.0 ** -25 - 2.0 ** -65),
            ('>e', b'\x04\x00', 2.0 ** -14 - 2.0 ** -25), ('>e',
            b'\x04\x00', 2.0 ** -14), ('>e', b'<\x01', 1.0 + 2.0 ** -11 + 
            2.0 ** -16), ('>e', b'<\x00', 1.0 + 2.0 ** -11), ('>e',
            b'<\x00', 1.0 + 2.0 ** -12), ('>e', b'{\xff', 65504), ('>e',
            b'{\xff', 65519), ('>e', b'\x80\x01', -2.0 ** -25 - 2.0 ** -35),
            ('>e', b'\x80\x00', -2.0 ** -25), ('>e', b'\x80\x00', -2.0 ** -
            26), ('>e', b'\xbc\x01', -1.0 - 2.0 ** -11 - 2.0 ** -16), ('>e',
            b'\xbc\x00', -1.0 - 2.0 ** -11), ('>e', b'\xbc\x00', -1.0 - 2.0 **
            -12), ('>e', b'\xfb\xff', -65519)]
        for formatcode, bits, f in format_bits_float__rounding_list:
            self.assertEqual(bits, struct.pack(formatcode, f))
        format_bits_float__roundingError_list = [('>e', 65520.0), ('>e', 
            65536.0), ('>e', 1e+300), ('>e', -65520.0), ('>e', -65536.0), (
            '>e', -1e+300), ('<e', 65520.0), ('<e', 65536.0), ('<e', 1e+300
            ), ('<e', -65520.0), ('<e', -65536.0), ('<e', -1e+300)]
        for formatcode, f in format_bits_float__roundingError_list:
            self.assertRaises(OverflowError, struct.pack, formatcode, f)
        format_bits_float__doubleRoundingError_list = [('>e', b'g\xff', 
            137405399039 * 2 ** -26)]
        for formatcode, bits, f in format_bits_float__doubleRoundingError_list:
            self.assertEqual(bits, struct.pack(formatcode, f))


if __name__ == '__main__':
    unittest.main()
