from test import multibytecodec_support
import unittest


class TestCP949Map(multibytecodec_support.TestBase_Mapping, unittest.TestCase):
    encoding = 'cp949'
    mapfileurl = 'http://www.pythontest.net/unicode/CP949.TXT'


class TestEUCKRMap(multibytecodec_support.TestBase_Mapping, unittest.TestCase):
    encoding = 'euc_kr'
    mapfileurl = 'http://www.pythontest.net/unicode/EUC-KR.TXT'
    pass_enctest = [(b'\xa4\xd4', 'ㅤ')]
    pass_dectest = [(b'\xa4\xd4', 'ㅤ')]


class TestJOHABMap(multibytecodec_support.TestBase_Mapping, unittest.TestCase):
    encoding = 'johab'
    mapfileurl = 'http://www.pythontest.net/unicode/JOHAB.TXT'
    pass_enctest = [(b'\\', '₩')]
    pass_dectest = [(b'\\', '₩')]


if __name__ == '__main__':
    unittest.main()
