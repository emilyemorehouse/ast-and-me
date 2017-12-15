import codecs
from collections import OrderedDict
from test.test_json import PyTest, CTest


class TestUnicode:

    def test_encoding3(self):
        u = 'αΩ'
        j = self.dumps(u)
        self.assertEqual(j, '"\\u03b1\\u03a9"')

    def test_encoding4(self):
        u = 'αΩ'
        j = self.dumps([u])
        self.assertEqual(j, '["\\u03b1\\u03a9"]')

    def test_encoding5(self):
        u = 'αΩ'
        j = self.dumps(u, ensure_ascii=False)
        self.assertEqual(j, '"{0}"'.format(u))

    def test_encoding6(self):
        u = 'αΩ'
        j = self.dumps([u], ensure_ascii=False)
        self.assertEqual(j, '["{0}"]'.format(u))

    def test_big_unicode_encode(self):
        u = '𝄠'
        self.assertEqual(self.dumps(u), '"\\ud834\\udd20"')
        self.assertEqual(self.dumps(u, ensure_ascii=False), '"𝄠"')

    def test_big_unicode_decode(self):
        u = 'z𝄠x'
        self.assertEqual(self.loads('"' + u + '"'), u)
        self.assertEqual(self.loads('"z\\ud834\\udd20x"'), u)

    def test_unicode_decode(self):
        for i in range(0, 55295):
            u = chr(i)
            s = '"\\u{0:04x}"'.format(i)
            self.assertEqual(self.loads(s), u)

    def test_unicode_preservation(self):
        self.assertEqual(type(self.loads('""')), str)
        self.assertEqual(type(self.loads('"a"')), str)
        self.assertEqual(type(self.loads('["a"]')[0]), str)

    def test_bytes_encode(self):
        self.assertRaises(TypeError, self.dumps, b'hi')
        self.assertRaises(TypeError, self.dumps, [b'hi'])

    def test_bytes_decode(self):
        for encoding, bom in [('utf-8', codecs.BOM_UTF8), ('utf-16be',
            codecs.BOM_UTF16_BE), ('utf-16le', codecs.BOM_UTF16_LE), (
            'utf-32be', codecs.BOM_UTF32_BE), ('utf-32le', codecs.BOM_UTF32_LE)
            ]:
            data = ['aµ€𝄠']
            encoded = self.dumps(data).encode(encoding)
            self.assertEqual(self.loads(bom + encoded), data)
            self.assertEqual(self.loads(encoded), data)
        self.assertRaises(UnicodeDecodeError, self.loads, b'["\x80"]')
        self.assertEqual(self.loads('"☀"'.encode('utf-16-le')), '☀')
        self.assertEqual(self.loads(b'5\x00'), 5)
        self.assertEqual(self.loads(b'\x007'), 7)
        self.assertEqual(self.loads(b'57'), 57)

    def test_object_pairs_hook_with_unicode(self):
        s = '{"xkd":1, "kcw":2, "art":3, "hxm":4, "qrt":5, "pad":6, "hoy":7}'
        p = [('xkd', 1), ('kcw', 2), ('art', 3), ('hxm', 4), ('qrt', 5), (
            'pad', 6), ('hoy', 7)]
        self.assertEqual(self.loads(s), eval(s))
        self.assertEqual(self.loads(s, object_pairs_hook=lambda x: x), p)
        od = self.loads(s, object_pairs_hook=OrderedDict)
        self.assertEqual(od, OrderedDict(p))
        self.assertEqual(type(od), OrderedDict)
        self.assertEqual(self.loads(s, object_pairs_hook=OrderedDict,
            object_hook=lambda x: None), OrderedDict(p))


class TestPyUnicode(TestUnicode, PyTest):
    pass


class TestCUnicode(TestUnicode, CTest):
    pass
