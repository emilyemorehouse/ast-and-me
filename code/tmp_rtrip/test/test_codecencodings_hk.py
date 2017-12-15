from test import multibytecodec_support
import unittest


class Test_Big5HKSCS(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'big5hkscs'
    tstring = multibytecodec_support.load_teststring('big5hkscs')
    codectests = (b'abc\x80\x80\xc1\xc4', 'strict', None), (b'abc\xc8',
        'strict', None), (b'abc\x80\x80\xc1\xc4', 'replace', 'abc��謐'), (
        b'abc\x80\x80\xc1\xc4\xc8', 'replace', 'abc��謐�'), (
        b'abc\x80\x80\xc1\xc4', 'ignore', 'abc謐')


if __name__ == '__main__':
    unittest.main()
