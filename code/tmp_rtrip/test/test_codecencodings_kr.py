from test import multibytecodec_support
import unittest


class Test_CP949(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'cp949'
    tstring = multibytecodec_support.load_teststring('cp949')
    codectests = (b'abc\x80\x80\xc1\xc4', 'strict', None), (b'abc\xc8',
        'strict', None), (b'abc\x80\x80\xc1\xc4', 'replace', 'abc��좔'), (
        b'abc\x80\x80\xc1\xc4\xc8', 'replace', 'abc��좔�'), (
        b'abc\x80\x80\xc1\xc4', 'ignore', 'abc좔')


class Test_EUCKR(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'euc_kr'
    tstring = multibytecodec_support.load_teststring('euc_kr')
    codectests = (b'abc\x80\x80\xc1\xc4', 'strict', None), (b'abc\xc8',
        'strict', None), (b'abc\x80\x80\xc1\xc4', 'replace', 'abc��좔'), (
        b'abc\x80\x80\xc1\xc4\xc8', 'replace', 'abc��좔�'), (
        b'abc\x80\x80\xc1\xc4', 'ignore', 'abc좔'), (b'\xa4\xd4', 'strict', None
        ), (b'\xa4\xd4\xa4', 'strict', None), (b'\xa4\xd4\xa4\xb6',
        'strict', None), (b'\xa4\xd4\xa4\xb6\xa4', 'strict', None), (
        b'\xa4\xd4\xa4\xb6\xa4\xd0', 'strict', None), (
        b'\xa4\xd4\xa4\xb6\xa4\xd0\xa4', 'strict', None), (
        b'\xa4\xd4\xa4\xb6\xa4\xd0\xa4\xd4', 'strict', '쓔'), (
        b'\xa4\xd4\xa4\xb6\xa4\xd0\xa4\xd4x', 'strict', '쓔x'), (
        b'a\xa4\xd4\xa4\xb6\xa4', 'replace', 'a�'), (
        b'\xa4\xd4\xa3\xb6\xa4\xd0\xa4\xd4', 'strict', None), (
        b'\xa4\xd4\xa4\xb6\xa3\xd0\xa4\xd4', 'strict', None), (
        b'\xa4\xd4\xa4\xb6\xa4\xd0\xa3\xd4', 'strict', None), (
        b'\xa4\xd4\xa4\xff\xa4\xd0\xa4\xd4', 'replace', '�渡�ㅠ�'), (
        b'\xa4\xd4\xa4\xb6\xa4\xff\xa4\xd4', 'replace', '�渡땄��'), (
        b'\xa4\xd4\xa4\xb6\xa4\xd0\xa4\xff', 'replace', '�渡땄圭�'), (
        b'\xa4\xd4\xff\xa4\xd4\xa4\xb6\xa4\xd0\xa4\xd4', 'replace', '���쓔'), (
        b'\xc1\xc4', 'strict', '좔')


class Test_JOHAB(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'johab'
    tstring = multibytecodec_support.load_teststring('johab')
    codectests = (b'abc\x80\x80\xc1\xc4', 'strict', None), (b'abc\xc8',
        'strict', None), (b'abc\x80\x80\xc1\xc4', 'replace', 'abc��촧'), (
        b'abc\x80\x80\xc1\xc4\xc8', 'replace', 'abc��촧�'), (
        b'abc\x80\x80\xc1\xc4', 'ignore', 'abc촧'), (b'\xd8abc', 'replace',
        '�abc'), (b'\xd8\xffabc', 'replace', '��abc'), (b'\x84bxy',
        'replace', '�bxy'), (b'\x8cBxy', 'replace', '�Bxy')


if __name__ == '__main__':
    unittest.main()
