import audioop
import sys
import unittest


def pack(width, data):
    return b''.join(v.to_bytes(width, sys.byteorder, signed=True) for v in data
        )


def unpack(width, data):
    return [int.from_bytes(data[i:i + width], sys.byteorder, signed=True) for
        i in range(0, len(data), width)]


packs = {w: (lambda *data, width=w: pack(width, data)) for w in (1, 2, 3, 4)}
maxvalues = {w: ((1 << 8 * w - 1) - 1) for w in (1, 2, 3, 4)}
minvalues = {w: (-1 << 8 * w - 1) for w in (1, 2, 3, 4)}
datas = {(1): b'\x00\x12E\xbb\x7f\x80\xff', (2): packs[2](0, 4660, 17767, -
    17767, 32767, -32768, -1), (3): packs[3](0, 1193046, 4548489, -4548489,
    8388607, -8388608, -1), (4): packs[4](0, 305419896, 1164413355, -
    1164413355, 2147483647, -2147483648, -1)}
INVALID_DATA = [(b'abc', 0), (b'abc', 2), (b'ab', 3), (b'abc', 4)]


class TestAudioop(unittest.TestCase):

    def test_max(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.max(b'', w), 0)
            self.assertEqual(audioop.max(bytearray(), w), 0)
            self.assertEqual(audioop.max(memoryview(b''), w), 0)
            p = packs[w]
            self.assertEqual(audioop.max(p(5), w), 5)
            self.assertEqual(audioop.max(p(5, -8, -1), w), 8)
            self.assertEqual(audioop.max(p(maxvalues[w]), w), maxvalues[w])
            self.assertEqual(audioop.max(p(minvalues[w]), w), -minvalues[w])
            self.assertEqual(audioop.max(datas[w], w), -minvalues[w])

    def test_minmax(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.minmax(b'', w), (2147483647, -2147483648))
            self.assertEqual(audioop.minmax(bytearray(), w), (2147483647, -
                2147483648))
            self.assertEqual(audioop.minmax(memoryview(b''), w), (
                2147483647, -2147483648))
            p = packs[w]
            self.assertEqual(audioop.minmax(p(5), w), (5, 5))
            self.assertEqual(audioop.minmax(p(5, -8, -1), w), (-8, 5))
            self.assertEqual(audioop.minmax(p(maxvalues[w]), w), (maxvalues
                [w], maxvalues[w]))
            self.assertEqual(audioop.minmax(p(minvalues[w]), w), (minvalues
                [w], minvalues[w]))
            self.assertEqual(audioop.minmax(datas[w], w), (minvalues[w],
                maxvalues[w]))

    def test_maxpp(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.maxpp(b'', w), 0)
            self.assertEqual(audioop.maxpp(bytearray(), w), 0)
            self.assertEqual(audioop.maxpp(memoryview(b''), w), 0)
            self.assertEqual(audioop.maxpp(packs[w](*range(100)), w), 0)
            self.assertEqual(audioop.maxpp(packs[w](9, 10, 5, 5, 0, 1), w), 10)
            self.assertEqual(audioop.maxpp(datas[w], w), maxvalues[w] -
                minvalues[w])

    def test_avg(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.avg(b'', w), 0)
            self.assertEqual(audioop.avg(bytearray(), w), 0)
            self.assertEqual(audioop.avg(memoryview(b''), w), 0)
            p = packs[w]
            self.assertEqual(audioop.avg(p(5), w), 5)
            self.assertEqual(audioop.avg(p(5, 8), w), 6)
            self.assertEqual(audioop.avg(p(5, -8), w), -2)
            self.assertEqual(audioop.avg(p(maxvalues[w], maxvalues[w]), w),
                maxvalues[w])
            self.assertEqual(audioop.avg(p(minvalues[w], minvalues[w]), w),
                minvalues[w])
        self.assertEqual(audioop.avg(packs[4](1342177280, 1879048192), 4), 
            1610612736)
        self.assertEqual(audioop.avg(packs[4](-1342177280, -1879048192), 4),
            -1610612736)

    def test_avgpp(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.avgpp(b'', w), 0)
            self.assertEqual(audioop.avgpp(bytearray(), w), 0)
            self.assertEqual(audioop.avgpp(memoryview(b''), w), 0)
            self.assertEqual(audioop.avgpp(packs[w](*range(100)), w), 0)
            self.assertEqual(audioop.avgpp(packs[w](9, 10, 5, 5, 0, 1), w), 10)
        self.assertEqual(audioop.avgpp(datas[1], 1), 196)
        self.assertEqual(audioop.avgpp(datas[2], 2), 50534)
        self.assertEqual(audioop.avgpp(datas[3], 3), 12937096)
        self.assertEqual(audioop.avgpp(datas[4], 4), 3311897002)

    def test_rms(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.rms(b'', w), 0)
            self.assertEqual(audioop.rms(bytearray(), w), 0)
            self.assertEqual(audioop.rms(memoryview(b''), w), 0)
            p = packs[w]
            self.assertEqual(audioop.rms(p(*range(100)), w), 57)
            self.assertAlmostEqual(audioop.rms(p(maxvalues[w]) * 5, w),
                maxvalues[w], delta=1)
            self.assertAlmostEqual(audioop.rms(p(minvalues[w]) * 5, w), -
                minvalues[w], delta=1)
        self.assertEqual(audioop.rms(datas[1], 1), 77)
        self.assertEqual(audioop.rms(datas[2], 2), 20001)
        self.assertEqual(audioop.rms(datas[3], 3), 5120523)
        self.assertEqual(audioop.rms(datas[4], 4), 1310854152)

    def test_cross(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.cross(b'', w), -1)
            self.assertEqual(audioop.cross(bytearray(), w), -1)
            self.assertEqual(audioop.cross(memoryview(b''), w), -1)
            p = packs[w]
            self.assertEqual(audioop.cross(p(0, 1, 2), w), 0)
            self.assertEqual(audioop.cross(p(1, 2, -3, -4), w), 1)
            self.assertEqual(audioop.cross(p(-1, -2, 3, 4), w), 1)
            self.assertEqual(audioop.cross(p(0, minvalues[w]), w), 1)
            self.assertEqual(audioop.cross(p(minvalues[w], maxvalues[w]), w), 1
                )

    def test_add(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.add(b'', b'', w), b'')
            self.assertEqual(audioop.add(bytearray(), bytearray(), w), b'')
            self.assertEqual(audioop.add(memoryview(b''), memoryview(b''),
                w), b'')
            self.assertEqual(audioop.add(datas[w], b'\x00' * len(datas[w]),
                w), datas[w])
        self.assertEqual(audioop.add(datas[1], datas[1], 1),
            b'\x00$\x7f\x80\x7f\x80\xfe')
        self.assertEqual(audioop.add(datas[2], datas[2], 2), packs[2](0, 
            9320, 32767, -32768, 32767, -32768, -2))
        self.assertEqual(audioop.add(datas[3], datas[3], 3), packs[3](0, 
            2386092, 8388607, -8388608, 8388607, -8388608, -2))
        self.assertEqual(audioop.add(datas[4], datas[4], 4), packs[4](0, 
            610839792, 2147483647, -2147483648, 2147483647, -2147483648, -2))

    def test_bias(self):
        for w in (1, 2, 3, 4):
            for bias in (0, 1, -1, 127, -128, 2147483647, -2147483648):
                self.assertEqual(audioop.bias(b'', w, bias), b'')
                self.assertEqual(audioop.bias(bytearray(), w, bias), b'')
                self.assertEqual(audioop.bias(memoryview(b''), w, bias), b'')
        self.assertEqual(audioop.bias(datas[1], 1, 1),
            b'\x01\x13F\xbc\x80\x81\x00')
        self.assertEqual(audioop.bias(datas[1], 1, -1),
            b'\xff\x11D\xba~\x7f\xfe')
        self.assertEqual(audioop.bias(datas[1], 1, 2147483647),
            b'\xff\x11D\xba~\x7f\xfe')
        self.assertEqual(audioop.bias(datas[1], 1, -2147483648), datas[1])
        self.assertEqual(audioop.bias(datas[2], 2, 1), packs[2](1, 4661, 
            17768, -17766, -32768, -32767, 0))
        self.assertEqual(audioop.bias(datas[2], 2, -1), packs[2](-1, 4659, 
            17766, -17768, 32766, 32767, -2))
        self.assertEqual(audioop.bias(datas[2], 2, 2147483647), packs[2](-1,
            4659, 17766, -17768, 32766, 32767, -2))
        self.assertEqual(audioop.bias(datas[2], 2, -2147483648), datas[2])
        self.assertEqual(audioop.bias(datas[3], 3, 1), packs[3](1, 1193047,
            4548490, -4548488, -8388608, -8388607, 0))
        self.assertEqual(audioop.bias(datas[3], 3, -1), packs[3](-1, 
            1193045, 4548488, -4548490, 8388606, 8388607, -2))
        self.assertEqual(audioop.bias(datas[3], 3, 2147483647), packs[3](-1,
            1193045, 4548488, -4548490, 8388606, 8388607, -2))
        self.assertEqual(audioop.bias(datas[3], 3, -2147483648), datas[3])
        self.assertEqual(audioop.bias(datas[4], 4, 1), packs[4](1, 
            305419897, 1164413356, -1164413354, -2147483648, -2147483647, 0))
        self.assertEqual(audioop.bias(datas[4], 4, -1), packs[4](-1, 
            305419895, 1164413354, -1164413356, 2147483646, 2147483647, -2))
        self.assertEqual(audioop.bias(datas[4], 4, 2147483647), packs[4](
            2147483647, -1842063753, -983070294, 983070292, -2, -1, 2147483646)
            )
        self.assertEqual(audioop.bias(datas[4], 4, -2147483648), packs[4](-
            2147483648, -1842063752, -983070293, 983070293, -1, 0, 2147483647))

    def test_lin2lin(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.lin2lin(datas[w], w, w), datas[w])
            self.assertEqual(audioop.lin2lin(bytearray(datas[w]), w, w),
                datas[w])
            self.assertEqual(audioop.lin2lin(memoryview(datas[w]), w, w),
                datas[w])
        self.assertEqual(audioop.lin2lin(datas[1], 1, 2), packs[2](0, 4608,
            17664, -17664, 32512, -32768, -256))
        self.assertEqual(audioop.lin2lin(datas[1], 1, 3), packs[3](0, 
            1179648, 4521984, -4521984, 8323072, -8388608, -65536))
        self.assertEqual(audioop.lin2lin(datas[1], 1, 4), packs[4](0, 
            301989888, 1157627904, -1157627904, 2130706432, -2147483648, -
            16777216))
        self.assertEqual(audioop.lin2lin(datas[2], 2, 1),
            b'\x00\x12E\xba\x7f\x80\xff')
        self.assertEqual(audioop.lin2lin(datas[2], 2, 3), packs[3](0, 
            1192960, 4548352, -4548352, 8388352, -8388608, -256))
        self.assertEqual(audioop.lin2lin(datas[2], 2, 4), packs[4](0, 
            305397760, 1164378112, -1164378112, 2147418112, -2147483648, -
            65536))
        self.assertEqual(audioop.lin2lin(datas[3], 3, 1),
            b'\x00\x12E\xba\x7f\x80\xff')
        self.assertEqual(audioop.lin2lin(datas[3], 3, 2), packs[2](0, 4660,
            17767, -17768, 32767, -32768, -1))
        self.assertEqual(audioop.lin2lin(datas[3], 3, 4), packs[4](0, 
            305419776, 1164413184, -1164413184, 2147483392, -2147483648, -256))
        self.assertEqual(audioop.lin2lin(datas[4], 4, 1),
            b'\x00\x12E\xba\x7f\x80\xff')
        self.assertEqual(audioop.lin2lin(datas[4], 4, 2), packs[2](0, 4660,
            17767, -17768, 32767, -32768, -1))
        self.assertEqual(audioop.lin2lin(datas[4], 4, 3), packs[3](0, 
            1193046, 4548489, -4548490, 8388607, -8388608, -1))

    def test_adpcm2lin(self):
        self.assertEqual(audioop.adpcm2lin(b'\x07\x7f\x7f', 1, None), (
            b'\x00\x00\x00\xff\x00\xff', (-179, 40)))
        self.assertEqual(audioop.adpcm2lin(bytearray(b'\x07\x7f\x7f'), 1,
            None), (b'\x00\x00\x00\xff\x00\xff', (-179, 40)))
        self.assertEqual(audioop.adpcm2lin(memoryview(b'\x07\x7f\x7f'), 1,
            None), (b'\x00\x00\x00\xff\x00\xff', (-179, 40)))
        self.assertEqual(audioop.adpcm2lin(b'\x07\x7f\x7f', 2, None), (
            packs[2](0, 11, 41, -22, 114, -179), (-179, 40)))
        self.assertEqual(audioop.adpcm2lin(b'\x07\x7f\x7f', 3, None), (
            packs[3](0, 2816, 10496, -5632, 29184, -45824), (-179, 40)))
        self.assertEqual(audioop.adpcm2lin(b'\x07\x7f\x7f', 4, None), (
            packs[4](0, 720896, 2686976, -1441792, 7471104, -11730944), (-
            179, 40)))
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.adpcm2lin(b'\x00' * 5, w, None), (
                b'\x00' * w * 10, (0, 0)))

    def test_lin2adpcm(self):
        self.assertEqual(audioop.lin2adpcm(datas[1], 1, None), (
            b'\x07\x7f\x7f', (-221, 39)))
        self.assertEqual(audioop.lin2adpcm(bytearray(datas[1]), 1, None), (
            b'\x07\x7f\x7f', (-221, 39)))
        self.assertEqual(audioop.lin2adpcm(memoryview(datas[1]), 1, None),
            (b'\x07\x7f\x7f', (-221, 39)))
        for w in (2, 3, 4):
            self.assertEqual(audioop.lin2adpcm(datas[w], w, None), (
                b'\x07\x7f\x7f', (31, 39)))
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.lin2adpcm(b'\x00' * w * 10, w, None),
                (b'\x00' * 5, (0, 0)))

    def test_invalid_adpcm_state(self):
        self.assertRaises(TypeError, audioop.adpcm2lin, b'\x00', 1, 555)
        self.assertRaises(TypeError, audioop.lin2adpcm, b'\x00', 1, 555)
        self.assertRaises(ValueError, audioop.adpcm2lin, b'\x00', 1, (0, -1))
        self.assertRaises(ValueError, audioop.adpcm2lin, b'\x00', 1, (0, 89))
        self.assertRaises(ValueError, audioop.lin2adpcm, b'\x00', 1, (0, -1))
        self.assertRaises(ValueError, audioop.lin2adpcm, b'\x00', 1, (0, 89))
        self.assertRaises(ValueError, audioop.adpcm2lin, b'\x00', 1, (-
            32769, 0))
        self.assertRaises(ValueError, audioop.adpcm2lin, b'\x00', 1, (32768, 0)
            )
        self.assertRaises(ValueError, audioop.lin2adpcm, b'\x00', 1, (-
            32769, 0))
        self.assertRaises(ValueError, audioop.lin2adpcm, b'\x00', 1, (32768, 0)
            )

    def test_lin2alaw(self):
        self.assertEqual(audioop.lin2alaw(datas[1], 1), b'\xd5\x87\xa4$\xaa*Z')
        self.assertEqual(audioop.lin2alaw(bytearray(datas[1]), 1),
            b'\xd5\x87\xa4$\xaa*Z')
        self.assertEqual(audioop.lin2alaw(memoryview(datas[1]), 1),
            b'\xd5\x87\xa4$\xaa*Z')
        for w in (2, 3, 4):
            self.assertEqual(audioop.lin2alaw(datas[w], w),
                b'\xd5\x87\xa4$\xaa*U')

    def test_alaw2lin(self):
        encoded = (
            b'\x00\x03$*QTUXkq\x7f\x80\x83\xa4\xaa\xd1\xd4\xd5\xd8\xeb\xf1\xff'
            )
        src = [-688, -720, -2240, -4032, -9, -3, -1, -27, -244, -82, -106, 
            688, 720, 2240, 4032, 9, 3, 1, 27, 244, 82, 106]
        for w in (1, 2, 3, 4):
            decoded = packs[w](*(x << w * 8 >> 13 for x in src))
            self.assertEqual(audioop.alaw2lin(encoded, w), decoded)
            self.assertEqual(audioop.alaw2lin(bytearray(encoded), w), decoded)
            self.assertEqual(audioop.alaw2lin(memoryview(encoded), w), decoded)
        encoded = bytes(range(256))
        for w in (2, 3, 4):
            decoded = audioop.alaw2lin(encoded, w)
            self.assertEqual(audioop.lin2alaw(decoded, w), encoded)

    def test_lin2ulaw(self):
        self.assertEqual(audioop.lin2ulaw(datas[1], 1),
            b'\xff\xad\x8e\x0e\x80\x00g')
        self.assertEqual(audioop.lin2ulaw(bytearray(datas[1]), 1),
            b'\xff\xad\x8e\x0e\x80\x00g')
        self.assertEqual(audioop.lin2ulaw(memoryview(datas[1]), 1),
            b'\xff\xad\x8e\x0e\x80\x00g')
        for w in (2, 3, 4):
            self.assertEqual(audioop.lin2ulaw(datas[w], w),
                b'\xff\xad\x8e\x0e\x80\x00~')

    def test_ulaw2lin(self):
        encoded = (
            b'\x00\x0e(?Wjv|~\x7f\x80\x8e\xa8\xbf\xd7\xea\xf6\xfc\xfe\xff')
        src = [-8031, -4447, -1471, -495, -163, -53, -18, -6, -2, 0, 8031, 
            4447, 1471, 495, 163, 53, 18, 6, 2, 0]
        for w in (1, 2, 3, 4):
            decoded = packs[w](*(x << w * 8 >> 14 for x in src))
            self.assertEqual(audioop.ulaw2lin(encoded, w), decoded)
            self.assertEqual(audioop.ulaw2lin(bytearray(encoded), w), decoded)
            self.assertEqual(audioop.ulaw2lin(memoryview(encoded), w), decoded)
        encoded = bytes(range(127)) + bytes(range(128, 256))
        for w in (2, 3, 4):
            decoded = audioop.ulaw2lin(encoded, w)
            self.assertEqual(audioop.lin2ulaw(decoded, w), encoded)

    def test_mul(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.mul(b'', w, 2), b'')
            self.assertEqual(audioop.mul(bytearray(), w, 2), b'')
            self.assertEqual(audioop.mul(memoryview(b''), w, 2), b'')
            self.assertEqual(audioop.mul(datas[w], w, 0), b'\x00' * len(
                datas[w]))
            self.assertEqual(audioop.mul(datas[w], w, 1), datas[w])
        self.assertEqual(audioop.mul(datas[1], 1, 2),
            b'\x00$\x7f\x80\x7f\x80\xfe')
        self.assertEqual(audioop.mul(datas[2], 2, 2), packs[2](0, 9320, 
            32767, -32768, 32767, -32768, -2))
        self.assertEqual(audioop.mul(datas[3], 3, 2), packs[3](0, 2386092, 
            8388607, -8388608, 8388607, -8388608, -2))
        self.assertEqual(audioop.mul(datas[4], 4, 2), packs[4](0, 610839792,
            2147483647, -2147483648, 2147483647, -2147483648, -2))

    def test_ratecv(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.ratecv(b'', w, 1, 8000, 8000, None), (
                b'', (-1, ((0, 0),))))
            self.assertEqual(audioop.ratecv(bytearray(), w, 1, 8000, 8000,
                None), (b'', (-1, ((0, 0),))))
            self.assertEqual(audioop.ratecv(memoryview(b''), w, 1, 8000, 
                8000, None), (b'', (-1, ((0, 0),))))
            self.assertEqual(audioop.ratecv(b'', w, 5, 8000, 8000, None), (
                b'', (-1, ((0, 0),) * 5)))
            self.assertEqual(audioop.ratecv(b'', w, 1, 8000, 16000, None),
                (b'', (-2, ((0, 0),))))
            self.assertEqual(audioop.ratecv(datas[w], w, 1, 8000, 8000,
                None)[0], datas[w])
            self.assertEqual(audioop.ratecv(datas[w], w, 1, 8000, 8000,
                None, 1, 0)[0], datas[w])
        state = None
        d1, state = audioop.ratecv(b'\x00\x01\x02', 1, 1, 8000, 16000, state)
        d2, state = audioop.ratecv(b'\x00\x01\x02', 1, 1, 8000, 16000, state)
        self.assertEqual(d1 + d2,
            b'\x00\x00\x01\x01\x02\x01\x00\x00\x01\x01\x02')
        for w in (1, 2, 3, 4):
            d0, state0 = audioop.ratecv(datas[w], w, 1, 8000, 16000, None)
            d, state = b'', None
            for i in range(0, len(datas[w]), w):
                d1, state = audioop.ratecv(datas[w][i:i + w], w, 1, 8000, 
                    16000, state)
                d += d1
            self.assertEqual(d, d0)
            self.assertEqual(state, state0)
        expected = {(1): packs[1](0, 13, 55, -38, 85, -75, -20), (2): packs
            [2](0, 3495, 14199, -9776, 22131, -19044, -4762), (3): packs[3]
            (0, 894784, 3635062, -2502602, 5665804, -4875005, -1218752), (4
            ): packs[4](0, 229064922, 930576246, -640665954, 1450446246, -
            1248001174, -312000294)}
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.ratecv(datas[w], w, 1, 8000, 8000,
                None, 3, 1)[0], expected[w])
            self.assertEqual(audioop.ratecv(datas[w], w, 1, 8000, 8000,
                None, 30, 10)[0], expected[w])

    def test_reverse(self):
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.reverse(b'', w), b'')
            self.assertEqual(audioop.reverse(bytearray(), w), b'')
            self.assertEqual(audioop.reverse(memoryview(b''), w), b'')
            self.assertEqual(audioop.reverse(packs[w](0, 1, 2), w), packs[w
                ](2, 1, 0))

    def test_tomono(self):
        for w in (1, 2, 3, 4):
            data1 = datas[w]
            data2 = bytearray(2 * len(data1))
            for k in range(w):
                data2[k::2 * w] = data1[k::w]
            self.assertEqual(audioop.tomono(data2, w, 1, 0), data1)
            self.assertEqual(audioop.tomono(data2, w, 0, 1), b'\x00' * len(
                data1))
            for k in range(w):
                data2[k + w::2 * w] = data1[k::w]
            self.assertEqual(audioop.tomono(data2, w, 0.5, 0.5), data1)
            self.assertEqual(audioop.tomono(bytearray(data2), w, 0.5, 0.5),
                data1)
            self.assertEqual(audioop.tomono(memoryview(data2), w, 0.5, 0.5),
                data1)

    def test_tostereo(self):
        for w in (1, 2, 3, 4):
            data1 = datas[w]
            data2 = bytearray(2 * len(data1))
            for k in range(w):
                data2[k::2 * w] = data1[k::w]
            self.assertEqual(audioop.tostereo(data1, w, 1, 0), data2)
            self.assertEqual(audioop.tostereo(data1, w, 0, 0), b'\x00' *
                len(data2))
            for k in range(w):
                data2[k + w::2 * w] = data1[k::w]
            self.assertEqual(audioop.tostereo(data1, w, 1, 1), data2)
            self.assertEqual(audioop.tostereo(bytearray(data1), w, 1, 1), data2
                )
            self.assertEqual(audioop.tostereo(memoryview(data1), w, 1, 1),
                data2)

    def test_findfactor(self):
        self.assertEqual(audioop.findfactor(datas[2], datas[2]), 1.0)
        self.assertEqual(audioop.findfactor(bytearray(datas[2]), bytearray(
            datas[2])), 1.0)
        self.assertEqual(audioop.findfactor(memoryview(datas[2]),
            memoryview(datas[2])), 1.0)
        self.assertEqual(audioop.findfactor(b'\x00' * len(datas[2]), datas[
            2]), 0.0)

    def test_findfit(self):
        self.assertEqual(audioop.findfit(datas[2], datas[2]), (0, 1.0))
        self.assertEqual(audioop.findfit(bytearray(datas[2]), bytearray(
            datas[2])), (0, 1.0))
        self.assertEqual(audioop.findfit(memoryview(datas[2]), memoryview(
            datas[2])), (0, 1.0))
        self.assertEqual(audioop.findfit(datas[2], packs[2](1, 2, 0)), (1, 
            8038.8))
        self.assertEqual(audioop.findfit(datas[2][:-2] * 5 + datas[2],
            datas[2]), (30, 1.0))

    def test_findmax(self):
        self.assertEqual(audioop.findmax(datas[2], 1), 5)
        self.assertEqual(audioop.findmax(bytearray(datas[2]), 1), 5)
        self.assertEqual(audioop.findmax(memoryview(datas[2]), 1), 5)

    def test_getsample(self):
        for w in (1, 2, 3, 4):
            data = packs[w](0, 1, -1, maxvalues[w], minvalues[w])
            self.assertEqual(audioop.getsample(data, w, 0), 0)
            self.assertEqual(audioop.getsample(bytearray(data), w, 0), 0)
            self.assertEqual(audioop.getsample(memoryview(data), w, 0), 0)
            self.assertEqual(audioop.getsample(data, w, 1), 1)
            self.assertEqual(audioop.getsample(data, w, 2), -1)
            self.assertEqual(audioop.getsample(data, w, 3), maxvalues[w])
            self.assertEqual(audioop.getsample(data, w, 4), minvalues[w])

    def test_byteswap(self):
        swapped_datas = {(1): datas[1], (2): packs[2](0, 13330, 26437, -
            26182, -129, 128, -1), (3): packs[3](0, 5649426, -7772347, 
            7837882, -129, 128, -1), (4): packs[4](0, 2018915346, -
            1417058491, 1433835706, -129, 128, -1)}
        for w in (1, 2, 3, 4):
            self.assertEqual(audioop.byteswap(b'', w), b'')
            self.assertEqual(audioop.byteswap(datas[w], w), swapped_datas[w])
            self.assertEqual(audioop.byteswap(swapped_datas[w], w), datas[w])
            self.assertEqual(audioop.byteswap(bytearray(datas[w]), w),
                swapped_datas[w])
            self.assertEqual(audioop.byteswap(memoryview(datas[w]), w),
                swapped_datas[w])

    def test_negativelen(self):
        self.assertRaises(audioop.error, audioop.findmax, bytes(range(256)),
            -2392392)

    def test_issue7673(self):
        state = None
        for data, size in INVALID_DATA:
            size2 = size
            self.assertRaises(audioop.error, audioop.getsample, data, size, 0)
            self.assertRaises(audioop.error, audioop.max, data, size)
            self.assertRaises(audioop.error, audioop.minmax, data, size)
            self.assertRaises(audioop.error, audioop.avg, data, size)
            self.assertRaises(audioop.error, audioop.rms, data, size)
            self.assertRaises(audioop.error, audioop.avgpp, data, size)
            self.assertRaises(audioop.error, audioop.maxpp, data, size)
            self.assertRaises(audioop.error, audioop.cross, data, size)
            self.assertRaises(audioop.error, audioop.mul, data, size, 1.0)
            self.assertRaises(audioop.error, audioop.tomono, data, size, 
                0.5, 0.5)
            self.assertRaises(audioop.error, audioop.tostereo, data, size, 
                0.5, 0.5)
            self.assertRaises(audioop.error, audioop.add, data, data, size)
            self.assertRaises(audioop.error, audioop.bias, data, size, 0)
            self.assertRaises(audioop.error, audioop.reverse, data, size)
            self.assertRaises(audioop.error, audioop.lin2lin, data, size, size2
                )
            self.assertRaises(audioop.error, audioop.ratecv, data, size, 1,
                1, 1, state)
            self.assertRaises(audioop.error, audioop.lin2ulaw, data, size)
            self.assertRaises(audioop.error, audioop.lin2alaw, data, size)
            self.assertRaises(audioop.error, audioop.lin2adpcm, data, size,
                state)

    def test_string(self):
        data = 'abcd'
        size = 2
        self.assertRaises(TypeError, audioop.getsample, data, size, 0)
        self.assertRaises(TypeError, audioop.max, data, size)
        self.assertRaises(TypeError, audioop.minmax, data, size)
        self.assertRaises(TypeError, audioop.avg, data, size)
        self.assertRaises(TypeError, audioop.rms, data, size)
        self.assertRaises(TypeError, audioop.avgpp, data, size)
        self.assertRaises(TypeError, audioop.maxpp, data, size)
        self.assertRaises(TypeError, audioop.cross, data, size)
        self.assertRaises(TypeError, audioop.mul, data, size, 1.0)
        self.assertRaises(TypeError, audioop.tomono, data, size, 0.5, 0.5)
        self.assertRaises(TypeError, audioop.tostereo, data, size, 0.5, 0.5)
        self.assertRaises(TypeError, audioop.add, data, data, size)
        self.assertRaises(TypeError, audioop.bias, data, size, 0)
        self.assertRaises(TypeError, audioop.reverse, data, size)
        self.assertRaises(TypeError, audioop.lin2lin, data, size, size)
        self.assertRaises(TypeError, audioop.ratecv, data, size, 1, 1, 1, None)
        self.assertRaises(TypeError, audioop.lin2ulaw, data, size)
        self.assertRaises(TypeError, audioop.lin2alaw, data, size)
        self.assertRaises(TypeError, audioop.lin2adpcm, data, size, None)

    def test_wrongsize(self):
        data = b'abcdefgh'
        state = None
        for size in (-1, 0, 5, 1024):
            self.assertRaises(audioop.error, audioop.ulaw2lin, data, size)
            self.assertRaises(audioop.error, audioop.alaw2lin, data, size)
            self.assertRaises(audioop.error, audioop.adpcm2lin, data, size,
                state)


if __name__ == '__main__':
    unittest.main()
