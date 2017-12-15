import unittest
from test import support
import binascii
import pickle
import random
import sys
from test.support import bigmemtest, _1G, _4G
zlib = support.import_module('zlib')
requires_Compress_copy = unittest.skipUnless(hasattr(zlib.compressobj(),
    'copy'), 'requires Compress.copy()')
requires_Decompress_copy = unittest.skipUnless(hasattr(zlib.decompressobj(),
    'copy'), 'requires Decompress.copy()')


class VersionTestCase(unittest.TestCase):

    def test_library_version(self):
        self.assertEqual(zlib.ZLIB_RUNTIME_VERSION[0], zlib.ZLIB_VERSION[0])


class ChecksumTestCase(unittest.TestCase):

    def test_crc32start(self):
        self.assertEqual(zlib.crc32(b''), zlib.crc32(b'', 0))
        self.assertTrue(zlib.crc32(b'abc', 4294967295))

    def test_crc32empty(self):
        self.assertEqual(zlib.crc32(b'', 0), 0)
        self.assertEqual(zlib.crc32(b'', 1), 1)
        self.assertEqual(zlib.crc32(b'', 432), 432)

    def test_adler32start(self):
        self.assertEqual(zlib.adler32(b''), zlib.adler32(b'', 1))
        self.assertTrue(zlib.adler32(b'abc', 4294967295))

    def test_adler32empty(self):
        self.assertEqual(zlib.adler32(b'', 0), 0)
        self.assertEqual(zlib.adler32(b'', 1), 1)
        self.assertEqual(zlib.adler32(b'', 432), 432)

    def test_penguins(self):
        self.assertEqual(zlib.crc32(b'penguin', 0), 3854672160)
        self.assertEqual(zlib.crc32(b'penguin', 1), 1136044692)
        self.assertEqual(zlib.adler32(b'penguin', 0), 198116086)
        self.assertEqual(zlib.adler32(b'penguin', 1), 198574839)
        self.assertEqual(zlib.crc32(b'penguin'), zlib.crc32(b'penguin', 0))
        self.assertEqual(zlib.adler32(b'penguin'), zlib.adler32(b'penguin', 1))

    def test_crc32_adler32_unsigned(self):
        foo = b'abcdefghijklmnop'
        self.assertEqual(zlib.crc32(foo), 2486878355)
        self.assertEqual(zlib.crc32(b'spam'), 1138425661)
        self.assertEqual(zlib.adler32(foo + foo), 3573550353)
        self.assertEqual(zlib.adler32(b'spam'), 72286642)

    def test_same_as_binascii_crc32(self):
        foo = b'abcdefghijklmnop'
        crc = 2486878355
        self.assertEqual(binascii.crc32(foo), crc)
        self.assertEqual(zlib.crc32(foo), crc)
        self.assertEqual(binascii.crc32(b'spam'), zlib.crc32(b'spam'))


class ChecksumBigBufferTestCase(unittest.TestCase):

    @bigmemtest(size=_4G + 4, memuse=1, dry_run=False)
    def test_big_buffer(self, size):
        data = b'nyan' * (_1G + 1)
        self.assertEqual(zlib.crc32(data), 1044521549)
        self.assertEqual(zlib.adler32(data), 2256789997)


class ExceptionTestCase(unittest.TestCase):

    def test_badlevel(self):
        self.assertRaises(zlib.error, zlib.compress, b'ERROR', 10)

    def test_badargs(self):
        self.assertRaises(TypeError, zlib.adler32)
        self.assertRaises(TypeError, zlib.crc32)
        self.assertRaises(TypeError, zlib.compress)
        self.assertRaises(TypeError, zlib.decompress)
        for arg in (42, None, '', 'abc', (), []):
            self.assertRaises(TypeError, zlib.adler32, arg)
            self.assertRaises(TypeError, zlib.crc32, arg)
            self.assertRaises(TypeError, zlib.compress, arg)
            self.assertRaises(TypeError, zlib.decompress, arg)

    def test_badcompressobj(self):
        self.assertRaises(ValueError, zlib.compressobj, 1, zlib.DEFLATED, 0)
        self.assertRaises(ValueError, zlib.compressobj, 1, zlib.DEFLATED, 
            zlib.MAX_WBITS + 1)

    def test_baddecompressobj(self):
        self.assertRaises(ValueError, zlib.decompressobj, -1)

    def test_decompressobj_badflush(self):
        self.assertRaises(ValueError, zlib.decompressobj().flush, 0)
        self.assertRaises(ValueError, zlib.decompressobj().flush, -1)

    @support.cpython_only
    def test_overflow(self):
        with self.assertRaisesRegex(OverflowError, 'int too large'):
            zlib.decompress(b'', 15, sys.maxsize + 1)
        with self.assertRaisesRegex(OverflowError, 'int too large'):
            zlib.decompressobj().decompress(b'', sys.maxsize + 1)
        with self.assertRaisesRegex(OverflowError, 'int too large'):
            zlib.decompressobj().flush(sys.maxsize + 1)


class BaseCompressTestCase(object):

    def check_big_compress_buffer(self, size, compress_func):
        _1M = 1024 * 1024
        data = b''.join([random.getrandbits(8 * _1M).to_bytes(_1M, 'little'
            ) for i in range(10)])
        data = data * (size // len(data) + 1)
        try:
            compress_func(data)
        finally:
            data = None

    def check_big_decompress_buffer(self, size, decompress_func):
        data = b'x' * size
        try:
            compressed = zlib.compress(data, 1)
        finally:
            data = None
        data = decompress_func(compressed)
        try:
            self.assertEqual(len(data), size)
            self.assertEqual(len(data.strip(b'x')), 0)
        finally:
            data = None


class CompressTestCase(BaseCompressTestCase, unittest.TestCase):

    def test_speech(self):
        x = zlib.compress(HAMLET_SCENE)
        self.assertEqual(zlib.decompress(x), HAMLET_SCENE)

    def test_keywords(self):
        x = zlib.compress(HAMLET_SCENE, level=3)
        self.assertEqual(zlib.decompress(x), HAMLET_SCENE)
        with self.assertRaises(TypeError):
            zlib.compress(data=HAMLET_SCENE, level=3)
        self.assertEqual(zlib.decompress(x, wbits=zlib.MAX_WBITS, bufsize=
            zlib.DEF_BUF_SIZE), HAMLET_SCENE)

    def test_speech128(self):
        data = HAMLET_SCENE * 128
        x = zlib.compress(data)
        self.assertEqual(zlib.compress(bytearray(data)), x)
        for ob in (x, bytearray(x)):
            self.assertEqual(zlib.decompress(ob), data)

    def test_incomplete_stream(self):
        x = zlib.compress(HAMLET_SCENE)
        self.assertRaisesRegex(zlib.error,
            'Error -5 while decompressing data: incomplete or truncated stream'
            , zlib.decompress, x[:-1])

    @bigmemtest(size=_1G + 1024 * 1024, memuse=3)
    def test_big_compress_buffer(self, size):
        compress = lambda s: zlib.compress(s, 1)
        self.check_big_compress_buffer(size, compress)

    @bigmemtest(size=_1G + 1024 * 1024, memuse=2)
    def test_big_decompress_buffer(self, size):
        self.check_big_decompress_buffer(size, zlib.decompress)

    @bigmemtest(size=_4G, memuse=1)
    def test_large_bufsize(self, size):
        data = HAMLET_SCENE * 10
        compressed = zlib.compress(data, 1)
        self.assertEqual(zlib.decompress(compressed, 15, size), data)

    def test_custom_bufsize(self):
        data = HAMLET_SCENE * 10
        compressed = zlib.compress(data, 1)
        self.assertEqual(zlib.decompress(compressed, 15, CustomInt()), data)

    @unittest.skipUnless(sys.maxsize > 2 ** 32, 'requires 64bit platform')
    @bigmemtest(size=_4G + 100, memuse=4)
    def test_64bit_compress(self, size):
        data = b'x' * size
        try:
            comp = zlib.compress(data, 0)
            self.assertEqual(zlib.decompress(comp), data)
        finally:
            comp = data = None


class CompressObjectTestCase(BaseCompressTestCase, unittest.TestCase):

    def test_pair(self):
        datasrc = HAMLET_SCENE * 128
        datazip = zlib.compress(datasrc)
        for data in (datasrc, bytearray(datasrc)):
            co = zlib.compressobj()
            x1 = co.compress(data)
            x2 = co.flush()
            self.assertRaises(zlib.error, co.flush)
            self.assertEqual(x1 + x2, datazip)
        for v1, v2 in ((x1, x2), (bytearray(x1), bytearray(x2))):
            dco = zlib.decompressobj()
            y1 = dco.decompress(v1 + v2)
            y2 = dco.flush()
            self.assertEqual(data, y1 + y2)
            self.assertIsInstance(dco.unconsumed_tail, bytes)
            self.assertIsInstance(dco.unused_data, bytes)

    def test_keywords(self):
        level = 2
        method = zlib.DEFLATED
        wbits = -12
        memLevel = 9
        strategy = zlib.Z_FILTERED
        co = zlib.compressobj(level=level, method=method, wbits=wbits,
            memLevel=memLevel, strategy=strategy, zdict=b'')
        do = zlib.decompressobj(wbits=wbits, zdict=b'')
        with self.assertRaises(TypeError):
            co.compress(data=HAMLET_SCENE)
        with self.assertRaises(TypeError):
            do.decompress(data=zlib.compress(HAMLET_SCENE))
        x = co.compress(HAMLET_SCENE) + co.flush()
        y = do.decompress(x, max_length=len(HAMLET_SCENE)) + do.flush()
        self.assertEqual(HAMLET_SCENE, y)

    def test_compressoptions(self):
        level = 2
        method = zlib.DEFLATED
        wbits = -12
        memLevel = 9
        strategy = zlib.Z_FILTERED
        co = zlib.compressobj(level, method, wbits, memLevel, strategy)
        x1 = co.compress(HAMLET_SCENE)
        x2 = co.flush()
        dco = zlib.decompressobj(wbits)
        y1 = dco.decompress(x1 + x2)
        y2 = dco.flush()
        self.assertEqual(HAMLET_SCENE, y1 + y2)

    def test_compressincremental(self):
        data = HAMLET_SCENE * 128
        co = zlib.compressobj()
        bufs = []
        for i in range(0, len(data), 256):
            bufs.append(co.compress(data[i:i + 256]))
        bufs.append(co.flush())
        combuf = b''.join(bufs)
        dco = zlib.decompressobj()
        y1 = dco.decompress(b''.join(bufs))
        y2 = dco.flush()
        self.assertEqual(data, y1 + y2)

    def test_decompinc(self, flush=False, source=None, cx=256, dcx=64):
        source = source or HAMLET_SCENE
        data = source * 128
        co = zlib.compressobj()
        bufs = []
        for i in range(0, len(data), cx):
            bufs.append(co.compress(data[i:i + cx]))
        bufs.append(co.flush())
        combuf = b''.join(bufs)
        decombuf = zlib.decompress(combuf)
        self.assertIsInstance(decombuf, bytes)
        self.assertEqual(data, decombuf)
        dco = zlib.decompressobj()
        bufs = []
        for i in range(0, len(combuf), dcx):
            bufs.append(dco.decompress(combuf[i:i + dcx]))
            self.assertEqual(b'', dco.unconsumed_tail, 
                "(A) uct should be b'': not %d long" % len(dco.unconsumed_tail)
                )
            self.assertEqual(b'', dco.unused_data)
        if flush:
            bufs.append(dco.flush())
        else:
            while True:
                chunk = dco.decompress(b'')
                if chunk:
                    bufs.append(chunk)
                else:
                    break
        self.assertEqual(b'', dco.unconsumed_tail, 
            "(B) uct should be b'': not %d long" % len(dco.unconsumed_tail))
        self.assertEqual(b'', dco.unused_data)
        self.assertEqual(data, b''.join(bufs))

    def test_decompincflush(self):
        self.test_decompinc(flush=True)

    def test_decompimax(self, source=None, cx=256, dcx=64):
        source = source or HAMLET_SCENE
        data = source * 128
        co = zlib.compressobj()
        bufs = []
        for i in range(0, len(data), cx):
            bufs.append(co.compress(data[i:i + cx]))
        bufs.append(co.flush())
        combuf = b''.join(bufs)
        self.assertEqual(data, zlib.decompress(combuf),
            'compressed data failure')
        dco = zlib.decompressobj()
        bufs = []
        cb = combuf
        while cb:
            chunk = dco.decompress(cb, dcx)
            self.assertFalse(len(chunk) > dcx, 'chunk too big (%d>%d)' % (
                len(chunk), dcx))
            bufs.append(chunk)
            cb = dco.unconsumed_tail
        bufs.append(dco.flush())
        self.assertEqual(data, b''.join(bufs), 'Wrong data retrieved')

    def test_decompressmaxlen(self, flush=False):
        data = HAMLET_SCENE * 128
        co = zlib.compressobj()
        bufs = []
        for i in range(0, len(data), 256):
            bufs.append(co.compress(data[i:i + 256]))
        bufs.append(co.flush())
        combuf = b''.join(bufs)
        self.assertEqual(data, zlib.decompress(combuf),
            'compressed data failure')
        dco = zlib.decompressobj()
        bufs = []
        cb = combuf
        while cb:
            max_length = 1 + len(cb) // 10
            chunk = dco.decompress(cb, max_length)
            self.assertFalse(len(chunk) > max_length, 
                'chunk too big (%d>%d)' % (len(chunk), max_length))
            bufs.append(chunk)
            cb = dco.unconsumed_tail
        if flush:
            bufs.append(dco.flush())
        else:
            while chunk:
                chunk = dco.decompress(b'', max_length)
                self.assertFalse(len(chunk) > max_length, 
                    'chunk too big (%d>%d)' % (len(chunk), max_length))
                bufs.append(chunk)
        self.assertEqual(data, b''.join(bufs), 'Wrong data retrieved')

    def test_decompressmaxlenflush(self):
        self.test_decompressmaxlen(flush=True)

    def test_maxlenmisc(self):
        dco = zlib.decompressobj()
        self.assertRaises(ValueError, dco.decompress, b'', -1)
        self.assertEqual(b'', dco.unconsumed_tail)

    def test_maxlen_large(self):
        data = HAMLET_SCENE * 10
        self.assertGreater(len(data), zlib.DEF_BUF_SIZE)
        compressed = zlib.compress(data, 1)
        dco = zlib.decompressobj()
        self.assertEqual(dco.decompress(compressed, sys.maxsize), data)

    def test_maxlen_custom(self):
        data = HAMLET_SCENE * 10
        compressed = zlib.compress(data, 1)
        dco = zlib.decompressobj()
        self.assertEqual(dco.decompress(compressed, CustomInt()), data[:100])

    def test_clear_unconsumed_tail(self):
        cdata = b'x\x9cKLJ\x06\x00\x02M\x01'
        dco = zlib.decompressobj()
        ddata = dco.decompress(cdata, 1)
        ddata += dco.decompress(dco.unconsumed_tail)
        self.assertEqual(dco.unconsumed_tail, b'')

    def test_flushes(self):
        sync_opt = ['Z_NO_FLUSH', 'Z_SYNC_FLUSH', 'Z_FULL_FLUSH']
        sync_opt = [getattr(zlib, opt) for opt in sync_opt if hasattr(zlib,
            opt)]
        data = HAMLET_SCENE * 8
        for sync in sync_opt:
            for level in range(10):
                obj = zlib.compressobj(level)
                a = obj.compress(data[:3000])
                b = obj.flush(sync)
                c = obj.compress(data[3000:])
                d = obj.flush()
                self.assertEqual(zlib.decompress(b''.join([a, b, c, d])),
                    data, 'Decompress failed: flush mode=%i, level=%i' % (
                    sync, level))
                del obj

    @unittest.skipUnless(hasattr(zlib, 'Z_SYNC_FLUSH'),
        'requires zlib.Z_SYNC_FLUSH')
    def test_odd_flush(self):
        import random
        co = zlib.compressobj(zlib.Z_BEST_COMPRESSION)
        dco = zlib.decompressobj()
        try:
            gen = random.WichmannHill()
        except AttributeError:
            try:
                gen = random.Random()
            except AttributeError:
                gen = random
        gen.seed(1)
        data = genblock(1, 17 * 1024, generator=gen)
        first = co.compress(data)
        second = co.flush(zlib.Z_SYNC_FLUSH)
        expanded = dco.decompress(first + second)
        self.assertEqual(expanded, data, "17K random source doesn't match")

    def test_empty_flush(self):
        co = zlib.compressobj(zlib.Z_BEST_COMPRESSION)
        self.assertTrue(co.flush())
        dco = zlib.decompressobj()
        self.assertEqual(dco.flush(), b'')

    def test_dictionary(self):
        h = HAMLET_SCENE
        words = h.split()
        random.shuffle(words)
        zdict = b''.join(words)
        co = zlib.compressobj(zdict=zdict)
        cd = co.compress(h) + co.flush()
        dco = zlib.decompressobj(zdict=zdict)
        self.assertEqual(dco.decompress(cd) + dco.flush(), h)
        dco = zlib.decompressobj()
        self.assertRaises(zlib.error, dco.decompress, cd)

    def test_dictionary_streaming(self):
        co = zlib.compressobj(zdict=HAMLET_SCENE)
        do = zlib.decompressobj(zdict=HAMLET_SCENE)
        piece = HAMLET_SCENE[1000:1500]
        d0 = co.compress(piece) + co.flush(zlib.Z_SYNC_FLUSH)
        d1 = co.compress(piece[100:]) + co.flush(zlib.Z_SYNC_FLUSH)
        d2 = co.compress(piece[:-100]) + co.flush(zlib.Z_SYNC_FLUSH)
        self.assertEqual(do.decompress(d0), piece)
        self.assertEqual(do.decompress(d1), piece[100:])
        self.assertEqual(do.decompress(d2), piece[:-100])

    def test_decompress_incomplete_stream(self):
        x = b'x\x9cK\xcb\xcf\x07\x00\x02\x82\x01E'
        self.assertEqual(zlib.decompress(x), b'foo')
        self.assertRaises(zlib.error, zlib.decompress, x[:-5])
        dco = zlib.decompressobj()
        y = dco.decompress(x[:-5])
        y += dco.flush()
        self.assertEqual(y, b'foo')

    def test_decompress_eof(self):
        x = b'x\x9cK\xcb\xcf\x07\x00\x02\x82\x01E'
        dco = zlib.decompressobj()
        self.assertFalse(dco.eof)
        dco.decompress(x[:-5])
        self.assertFalse(dco.eof)
        dco.decompress(x[-5:])
        self.assertTrue(dco.eof)
        dco.flush()
        self.assertTrue(dco.eof)

    def test_decompress_eof_incomplete_stream(self):
        x = b'x\x9cK\xcb\xcf\x07\x00\x02\x82\x01E'
        dco = zlib.decompressobj()
        self.assertFalse(dco.eof)
        dco.decompress(x[:-5])
        self.assertFalse(dco.eof)
        dco.flush()
        self.assertFalse(dco.eof)

    def test_decompress_unused_data(self):
        source = b'abcdefghijklmnopqrstuvwxyz'
        remainder = b'0123456789'
        y = zlib.compress(source)
        x = y + remainder
        for maxlen in (0, 1000):
            for step in (1, 2, len(y), len(x)):
                dco = zlib.decompressobj()
                data = b''
                for i in range(0, len(x), step):
                    if i < len(y):
                        self.assertEqual(dco.unused_data, b'')
                    if maxlen == 0:
                        data += dco.decompress(x[i:i + step])
                        self.assertEqual(dco.unconsumed_tail, b'')
                    else:
                        data += dco.decompress(dco.unconsumed_tail + x[i:i +
                            step], maxlen)
                data += dco.flush()
                self.assertTrue(dco.eof)
                self.assertEqual(data, source)
                self.assertEqual(dco.unconsumed_tail, b'')
                self.assertEqual(dco.unused_data, remainder)

    def test_decompress_raw_with_dictionary(self):
        zdict = b'abcdefghijklmnopqrstuvwxyz'
        co = zlib.compressobj(wbits=-zlib.MAX_WBITS, zdict=zdict)
        comp = co.compress(zdict) + co.flush()
        dco = zlib.decompressobj(wbits=-zlib.MAX_WBITS, zdict=zdict)
        uncomp = dco.decompress(comp) + dco.flush()
        self.assertEqual(zdict, uncomp)

    def test_flush_with_freed_input(self):
        input1 = b'abcdefghijklmnopqrstuvwxyz'
        input2 = b'QWERTYUIOPASDFGHJKLZXCVBNM'
        data = zlib.compress(input1)
        dco = zlib.decompressobj()
        dco.decompress(data, 1)
        del data
        data = zlib.compress(input2)
        self.assertEqual(dco.flush(), input1[1:])

    @bigmemtest(size=_4G, memuse=1)
    def test_flush_large_length(self, size):
        input = HAMLET_SCENE * 10
        data = zlib.compress(input, 1)
        dco = zlib.decompressobj()
        dco.decompress(data, 1)
        self.assertEqual(dco.flush(size), input[1:])

    def test_flush_custom_length(self):
        input = HAMLET_SCENE * 10
        data = zlib.compress(input, 1)
        dco = zlib.decompressobj()
        dco.decompress(data, 1)
        self.assertEqual(dco.flush(CustomInt()), input[1:])

    @requires_Compress_copy
    def test_compresscopy(self):
        data0 = HAMLET_SCENE
        data1 = bytes(str(HAMLET_SCENE, 'ascii').swapcase(), 'ascii')
        c0 = zlib.compressobj(zlib.Z_BEST_COMPRESSION)
        bufs0 = []
        bufs0.append(c0.compress(data0))
        c1 = c0.copy()
        bufs1 = bufs0[:]
        bufs0.append(c0.compress(data0))
        bufs0.append(c0.flush())
        s0 = b''.join(bufs0)
        bufs1.append(c1.compress(data1))
        bufs1.append(c1.flush())
        s1 = b''.join(bufs1)
        self.assertEqual(zlib.decompress(s0), data0 + data0)
        self.assertEqual(zlib.decompress(s1), data0 + data1)

    @requires_Compress_copy
    def test_badcompresscopy(self):
        c = zlib.compressobj()
        c.compress(HAMLET_SCENE)
        c.flush()
        self.assertRaises(ValueError, c.copy)

    @requires_Decompress_copy
    def test_decompresscopy(self):
        data = HAMLET_SCENE
        comp = zlib.compress(data)
        self.assertIsInstance(comp, bytes)
        d0 = zlib.decompressobj()
        bufs0 = []
        bufs0.append(d0.decompress(comp[:32]))
        d1 = d0.copy()
        bufs1 = bufs0[:]
        bufs0.append(d0.decompress(comp[32:]))
        s0 = b''.join(bufs0)
        bufs1.append(d1.decompress(comp[32:]))
        s1 = b''.join(bufs1)
        self.assertEqual(s0, s1)
        self.assertEqual(s0, data)

    @requires_Decompress_copy
    def test_baddecompresscopy(self):
        data = zlib.compress(HAMLET_SCENE)
        d = zlib.decompressobj()
        d.decompress(data)
        d.flush()
        self.assertRaises(ValueError, d.copy)

    def test_compresspickle(self):
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.assertRaises((TypeError, pickle.PicklingError)):
                pickle.dumps(zlib.compressobj(zlib.Z_BEST_COMPRESSION), proto)

    def test_decompresspickle(self):
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.assertRaises((TypeError, pickle.PicklingError)):
                pickle.dumps(zlib.decompressobj(), proto)

    @bigmemtest(size=_1G + 1024 * 1024, memuse=3)
    def test_big_compress_buffer(self, size):
        c = zlib.compressobj(1)
        compress = lambda s: c.compress(s) + c.flush()
        self.check_big_compress_buffer(size, compress)

    @bigmemtest(size=_1G + 1024 * 1024, memuse=2)
    def test_big_decompress_buffer(self, size):
        d = zlib.decompressobj()
        decompress = lambda s: d.decompress(s) + d.flush()
        self.check_big_decompress_buffer(size, decompress)

    @unittest.skipUnless(sys.maxsize > 2 ** 32, 'requires 64bit platform')
    @bigmemtest(size=_4G + 100, memuse=4)
    def test_64bit_compress(self, size):
        data = b'x' * size
        co = zlib.compressobj(0)
        do = zlib.decompressobj()
        try:
            comp = co.compress(data) + co.flush()
            uncomp = do.decompress(comp) + do.flush()
            self.assertEqual(uncomp, data)
        finally:
            comp = uncomp = data = None

    @unittest.skipUnless(sys.maxsize > 2 ** 32, 'requires 64bit platform')
    @bigmemtest(size=_4G + 100, memuse=3)
    def test_large_unused_data(self, size):
        data = b'abcdefghijklmnop'
        unused = b'x' * size
        comp = zlib.compress(data) + unused
        do = zlib.decompressobj()
        try:
            uncomp = do.decompress(comp) + do.flush()
            self.assertEqual(unused, do.unused_data)
            self.assertEqual(uncomp, data)
        finally:
            unused = comp = do = None

    @unittest.skipUnless(sys.maxsize > 2 ** 32, 'requires 64bit platform')
    @bigmemtest(size=_4G + 100, memuse=5)
    def test_large_unconsumed_tail(self, size):
        data = b'x' * size
        do = zlib.decompressobj()
        try:
            comp = zlib.compress(data, 0)
            uncomp = do.decompress(comp, 1) + do.flush()
            self.assertEqual(uncomp, data)
            self.assertEqual(do.unconsumed_tail, b'')
        finally:
            comp = uncomp = data = None

    def test_wbits(self):
        v = (zlib.ZLIB_RUNTIME_VERSION + '.0').split('.', 4)
        supports_wbits_0 = int(v[0]) > 1 or int(v[0]) == 1 and (int(v[1]) >
            2 or int(v[1]) == 2 and (int(v[2]) > 3 or int(v[2]) == 3 and 
            int(v[3]) >= 5))
        co = zlib.compressobj(level=1, wbits=15)
        zlib15 = co.compress(HAMLET_SCENE) + co.flush()
        self.assertEqual(zlib.decompress(zlib15, 15), HAMLET_SCENE)
        if supports_wbits_0:
            self.assertEqual(zlib.decompress(zlib15, 0), HAMLET_SCENE)
        self.assertEqual(zlib.decompress(zlib15, 32 + 15), HAMLET_SCENE)
        with self.assertRaisesRegex(zlib.error, 'invalid window size'):
            zlib.decompress(zlib15, 14)
        dco = zlib.decompressobj(wbits=32 + 15)
        self.assertEqual(dco.decompress(zlib15), HAMLET_SCENE)
        dco = zlib.decompressobj(wbits=14)
        with self.assertRaisesRegex(zlib.error, 'invalid window size'):
            dco.decompress(zlib15)
        co = zlib.compressobj(level=1, wbits=9)
        zlib9 = co.compress(HAMLET_SCENE) + co.flush()
        self.assertEqual(zlib.decompress(zlib9, 9), HAMLET_SCENE)
        self.assertEqual(zlib.decompress(zlib9, 15), HAMLET_SCENE)
        if supports_wbits_0:
            self.assertEqual(zlib.decompress(zlib9, 0), HAMLET_SCENE)
        self.assertEqual(zlib.decompress(zlib9, 32 + 9), HAMLET_SCENE)
        dco = zlib.decompressobj(wbits=32 + 9)
        self.assertEqual(dco.decompress(zlib9), HAMLET_SCENE)
        co = zlib.compressobj(level=1, wbits=-15)
        deflate15 = co.compress(HAMLET_SCENE) + co.flush()
        self.assertEqual(zlib.decompress(deflate15, -15), HAMLET_SCENE)
        dco = zlib.decompressobj(wbits=-15)
        self.assertEqual(dco.decompress(deflate15), HAMLET_SCENE)
        co = zlib.compressobj(level=1, wbits=-9)
        deflate9 = co.compress(HAMLET_SCENE) + co.flush()
        self.assertEqual(zlib.decompress(deflate9, -9), HAMLET_SCENE)
        self.assertEqual(zlib.decompress(deflate9, -15), HAMLET_SCENE)
        dco = zlib.decompressobj(wbits=-9)
        self.assertEqual(dco.decompress(deflate9), HAMLET_SCENE)
        co = zlib.compressobj(level=1, wbits=16 + 15)
        gzip = co.compress(HAMLET_SCENE) + co.flush()
        self.assertEqual(zlib.decompress(gzip, 16 + 15), HAMLET_SCENE)
        self.assertEqual(zlib.decompress(gzip, 32 + 15), HAMLET_SCENE)
        dco = zlib.decompressobj(32 + 15)
        self.assertEqual(dco.decompress(gzip), HAMLET_SCENE)


def genblock(seed, length, step=1024, generator=random):
    """length-byte stream of random data from a seed (in step-byte blocks)."""
    if seed is not None:
        generator.seed(seed)
    randint = generator.randint
    if length < step or step < 2:
        step = length
    blocks = bytes()
    for i in range(0, length, step):
        blocks += bytes(randint(0, 255) for x in range(step))
    return blocks


def choose_lines(source, number, seed=None, generator=random):
    """Return a list of number lines randomly chosen from the source"""
    if seed is not None:
        generator.seed(seed)
    sources = source.split('\n')
    return [generator.choice(sources) for n in range(number)]


HAMLET_SCENE = (
    b"\nLAERTES\n\n       O, fear me not.\n       I stay too long: but here my father comes.\n\n       Enter POLONIUS\n\n       A double blessing is a double grace,\n       Occasion smiles upon a second leave.\n\nLORD POLONIUS\n\n       Yet here, Laertes! aboard, aboard, for shame!\n       The wind sits in the shoulder of your sail,\n       And you are stay'd for. There; my blessing with thee!\n       And these few precepts in thy memory\n       See thou character. Give thy thoughts no tongue,\n       Nor any unproportioned thought his act.\n       Be thou familiar, but by no means vulgar.\n       Those friends thou hast, and their adoption tried,\n       Grapple them to thy soul with hoops of steel;\n       But do not dull thy palm with entertainment\n       Of each new-hatch'd, unfledged comrade. Beware\n       Of entrance to a quarrel, but being in,\n       Bear't that the opposed may beware of thee.\n       Give every man thy ear, but few thy voice;\n       Take each man's censure, but reserve thy judgment.\n       Costly thy habit as thy purse can buy,\n       But not express'd in fancy; rich, not gaudy;\n       For the apparel oft proclaims the man,\n       And they in France of the best rank and station\n       Are of a most select and generous chief in that.\n       Neither a borrower nor a lender be;\n       For loan oft loses both itself and friend,\n       And borrowing dulls the edge of husbandry.\n       This above all: to thine ownself be true,\n       And it must follow, as the night the day,\n       Thou canst not then be false to any man.\n       Farewell: my blessing season this in thee!\n\nLAERTES\n\n       Most humbly do I take my leave, my lord.\n\nLORD POLONIUS\n\n       The time invites you; go; your servants tend.\n\nLAERTES\n\n       Farewell, Ophelia; and remember well\n       What I have said to you.\n\nOPHELIA\n\n       'Tis in my memory lock'd,\n       And you yourself shall keep the key of it.\n\nLAERTES\n\n       Farewell.\n"
    )


class CustomInt:

    def __int__(self):
        return 100


if __name__ == '__main__':
    unittest.main()
