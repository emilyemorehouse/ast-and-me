from test import multibytecodec_support
import unittest
COMMON_CODEC_TESTS = (b'ab\xffcd', 'replace', 'ab�cd'), (b'ab\x1bdef',
    'replace', 'ab\x1bdef'), (b'ab\x1b$def', 'replace', 'ab�')


class Test_ISO2022_JP(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'iso2022_jp'
    tstring = multibytecodec_support.load_teststring('iso2022_jp')
    codectests = COMMON_CODEC_TESTS + ((b'ab\x1bNdef', 'replace',
        'ab\x1bNdef'),)


class Test_ISO2022_JP2(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'iso2022_jp_2'
    tstring = multibytecodec_support.load_teststring('iso2022_jp')
    codectests = COMMON_CODEC_TESTS + ((b'ab\x1bNdef', 'replace', 'abdef'),)


class Test_ISO2022_KR(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'iso2022_kr'
    tstring = multibytecodec_support.load_teststring('iso2022_kr')
    codectests = COMMON_CODEC_TESTS + ((b'ab\x1bNdef', 'replace',
        'ab\x1bNdef'),)

    @unittest.skip('iso2022_kr.txt cannot be used to test "chunk coding"')
    def test_chunkcoding(self):
        pass


if __name__ == '__main__':
    unittest.main()
