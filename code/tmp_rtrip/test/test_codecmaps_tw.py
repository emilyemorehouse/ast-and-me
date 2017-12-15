from test import multibytecodec_support
import unittest


class TestBIG5Map(multibytecodec_support.TestBase_Mapping, unittest.TestCase):
    encoding = 'big5'
    mapfileurl = 'http://www.pythontest.net/unicode/BIG5.TXT'


class TestCP950Map(multibytecodec_support.TestBase_Mapping, unittest.TestCase):
    encoding = 'cp950'
    mapfileurl = 'http://www.pythontest.net/unicode/CP950.TXT'
    pass_enctest = [(b'\xa2\xcc', '十'), (b'\xa2\xce', '卅')]
    codectests = (b'\xffxy', 'replace', '�xy'),


if __name__ == '__main__':
    unittest.main()
