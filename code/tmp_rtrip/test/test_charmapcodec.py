""" Python character mapping codec test

This uses the test codec in testcodec.py and thus also tests the
encodings package lookup scheme.

Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright 2000 Guido van Rossum.

"""
import unittest
import codecs


def codec_search_function(encoding):
    if encoding == 'testcodec':
        from test import testcodec
        return tuple(testcodec.getregentry())
    return None


codecs.register(codec_search_function)
codecname = 'testcodec'


class CharmapCodecTest(unittest.TestCase):

    def test_constructorx(self):
        self.assertEqual(str(b'abc', codecname), 'abc')
        self.assertEqual(str(b'xdef', codecname), 'abcdef')
        self.assertEqual(str(b'defx', codecname), 'defabc')
        self.assertEqual(str(b'dxf', codecname), 'dabcf')
        self.assertEqual(str(b'dxfx', codecname), 'dabcfabc')

    def test_encodex(self):
        self.assertEqual('abc'.encode(codecname), b'abc')
        self.assertEqual('xdef'.encode(codecname), b'abcdef')
        self.assertEqual('defx'.encode(codecname), b'defabc')
        self.assertEqual('dxf'.encode(codecname), b'dabcf')
        self.assertEqual('dxfx'.encode(codecname), b'dabcfabc')

    def test_constructory(self):
        self.assertEqual(str(b'ydef', codecname), 'def')
        self.assertEqual(str(b'defy', codecname), 'def')
        self.assertEqual(str(b'dyf', codecname), 'df')
        self.assertEqual(str(b'dyfy', codecname), 'df')

    def test_maptoundefined(self):
        self.assertRaises(UnicodeError, str, b'abc\x01', codecname)


if __name__ == '__main__':
    unittest.main()
