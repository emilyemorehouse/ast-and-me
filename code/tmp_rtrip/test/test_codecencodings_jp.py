from test import multibytecodec_support
import unittest


class Test_CP932(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'cp932'
    tstring = multibytecodec_support.load_teststring('shift_jis')
    codectests = (b'abc\x81\x00\x81\x00\x82\x84', 'strict', None), (b'abc\xf8',
        'strict', None), (b'abc\x81\x00\x82\x84', 'replace', 'abc�\x00ｄ'), (
        b'abc\x81\x00\x82\x84\x88', 'replace', 'abc�\x00ｄ�'), (
        b'abc\x81\x00\x82\x84', 'ignore', 'abc\x00ｄ'), (b'ab\xebxy',
        'replace', 'ab�xy'), (b'ab\xf09xy', 'replace', 'ab�9xy'), (
        b'ab\xea\xf0xy', 'replace', 'ab�\ue038y'), (b'\\~', 'replace', '\\~'
        ), (b'\x81_\x81a\x81|', 'replace', '＼∥－')


euc_commontests = (b'abc\x80\x80\xc1\xc4', 'strict', None), (
    b'abc\x80\x80\xc1\xc4', 'replace', 'abc��祖'), (b'abc\x80\x80\xc1\xc4\xc8',
    'replace', 'abc��祖�'), (b'abc\x80\x80\xc1\xc4', 'ignore', 'abc祖'), (
    b'abc\xc8', 'strict', None), (b'abc\x8f\x83\x83', 'replace', 'abc���'), (
    b'\x82\xfcxy', 'replace', '��xy'), (b'\xc1d', 'strict', None), (b'\xa1\xc0'
    , 'strict', '＼'), (b'\xa1\xc0\\', 'strict', '＼\\'), (b'\x8eXY',
    'replace', '�XY')


class Test_EUC_JIS_2004(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'euc_jis_2004'
    tstring = multibytecodec_support.load_teststring('euc_jisx0213')
    codectests = euc_commontests
    xmlcharnametest = ('«ℜ» = 〈ሴ〉',
        b'\xa9\xa8&real;\xa9\xb2 = &lang;&#4660;&rang;')


class Test_EUC_JISX0213(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'euc_jisx0213'
    tstring = multibytecodec_support.load_teststring('euc_jisx0213')
    codectests = euc_commontests
    xmlcharnametest = ('«ℜ» = 〈ሴ〉',
        b'\xa9\xa8&real;\xa9\xb2 = &lang;&#4660;&rang;')


class Test_EUC_JP_COMPAT(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'euc_jp'
    tstring = multibytecodec_support.load_teststring('euc_jp')
    codectests = euc_commontests + (('¥', 'strict', b'\\'), ('‾', 'strict',
        b'~'))


shiftjis_commonenctests = (b'abc\x80\x80\x82\x84', 'strict', None), (b'abc\xf8'
    , 'strict', None), (b'abc\x80\x80\x82\x84def', 'ignore', 'abcｄdef')


class Test_SJIS_COMPAT(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'shift_jis'
    tstring = multibytecodec_support.load_teststring('shift_jis')
    codectests = shiftjis_commonenctests + ((b'abc\x80\x80\x82\x84',
        'replace', 'abc��ｄ'), (b'abc\x80\x80\x82\x84\x88', 'replace',
        'abc��ｄ�'), (b'\\~', 'strict', '\\~'), (b'\x81_\x81a\x81|',
        'strict', '＼‖−'), (b'abc\x819', 'replace', 'abc�9'), (
        b'abc\xea\xfc', 'replace', 'abc��'), (b'abc\xffX', 'replace', 'abc�X'))


class Test_SJIS_2004(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'shift_jis_2004'
    tstring = multibytecodec_support.load_teststring('shift_jis')
    codectests = shiftjis_commonenctests + ((b'\\~', 'strict', '¥‾'), (
        b'\x81_\x81a\x81|', 'strict', '\\‖−'), (b'abc\xea\xfc', 'strict',
        'abc撿'), (b'\x819xy', 'replace', '�9xy'), (b'\xffXxy', 'replace',
        '�Xxy'), (b'\x80\x80\x82\x84xy', 'replace', '��ｄxy'), (
        b'\x80\x80\x82\x84\x88xy', 'replace', '��ｄ塤y'), (b'\xfc\xfbxy',
        'replace', '�閴y'))
    xmlcharnametest = '«ℜ» = 〈ሴ〉', b'\x85G&real;\x85Q = &lang;&#4660;&rang;'


class Test_SJISX0213(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'shift_jisx0213'
    tstring = multibytecodec_support.load_teststring('shift_jisx0213')
    codectests = shiftjis_commonenctests + ((b'abc\x80\x80\x82\x84',
        'replace', 'abc��ｄ'), (b'abc\x80\x80\x82\x84\x88', 'replace',
        'abc��ｄ�'), (b'\\~', 'replace', '¥‾'), (b'\x81_\x81a\x81|',
        'replace', '\\‖−'))
    xmlcharnametest = '«ℜ» = 〈ሴ〉', b'\x85G&real;\x85Q = &lang;&#4660;&rang;'


if __name__ == '__main__':
    unittest.main()
