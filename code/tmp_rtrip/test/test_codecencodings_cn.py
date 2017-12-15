from test import multibytecodec_support
import unittest


class Test_GB2312(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'gb2312'
    tstring = multibytecodec_support.load_teststring('gb2312')
    codectests = (b'abc\x81\x81\xc1\xc4', 'strict', None), (b'abc\xc8',
        'strict', None), (b'abc\x81\x81\xc1\xc4', 'replace', 'abc��聊'), (
        b'abc\x81\x81\xc1\xc4\xc8', 'replace', 'abc��聊�'), (
        b'abc\x81\x81\xc1\xc4', 'ignore', 'abc聊'), (b'\xc1d', 'strict', None)


class Test_GBK(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'gbk'
    tstring = multibytecodec_support.load_teststring('gbk')
    codectests = (b'abc\x80\x80\xc1\xc4', 'strict', None), (b'abc\xc8',
        'strict', None), (b'abc\x80\x80\xc1\xc4', 'replace', 'abc��聊'), (
        b'abc\x80\x80\xc1\xc4\xc8', 'replace', 'abc��聊�'), (
        b'abc\x80\x80\xc1\xc4', 'ignore', 'abc聊'), (b'\x834\x831', 'strict',
        None), ('・', 'strict', None)


class Test_GB18030(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'gb18030'
    tstring = multibytecodec_support.load_teststring('gb18030')
    codectests = (b'abc\x80\x80\xc1\xc4', 'strict', None), (b'abc\xc8',
        'strict', None), (b'abc\x80\x80\xc1\xc4', 'replace', 'abc��聊'), (
        b'abc\x80\x80\xc1\xc4\xc8', 'replace', 'abc��聊�'), (
        b'abc\x80\x80\xc1\xc4', 'ignore', 'abc聊'), (b'abc\x849\x849\xc1\xc4',
        'replace', 'abc�9�9聊'), ('・', 'strict', b'\x819\xa79'), (
        b'abc\x842\x80\x80def', 'replace', 'abc�2��def'), (b'abc\x810\x810def',
        'strict', 'abc\x80def'), (b'abc\x860\x810def', 'replace', 'abc�0�0def'
        ), (b'\xff0\x810', 'strict', None), (b'\x810\xff0', 'strict', None), (
        b'abc\x819\xff9\xc1\xc4', 'replace', 'abc�9�9聊'), (b'abc\xab6\xff0def',
        'replace', 'abc�6�0def'), (b'abc\xbf8\xff2\xc1\xc4', 'ignore', 'abc82聊'
        )
    has_iso10646 = True


class Test_HZ(multibytecodec_support.TestBase, unittest.TestCase):
    encoding = 'hz'
    tstring = multibytecodec_support.load_teststring('hz')
    codectests = (
        b'This sentence is in ASCII.\nThe next sentence is in GB.~{<:Ky2;S{#,~}~\n~{NpJ)l6HK!#~}Bye.\n'
        , 'strict',
        """This sentence is in ASCII.
The next sentence is in GB.己所不欲，勿施於人。Bye.
"""
        ), (
        b'This sentence is in ASCII.\nThe next sentence is in GB.~\n~{<:Ky2;S{#,NpJ)l6HK!#~}~\nBye.\n'
        , 'strict',
        """This sentence is in ASCII.
The next sentence is in GB.己所不欲，勿施於人。Bye.
"""
        ), (b'ab~cd', 'replace', 'ab�cd'), (b'ab\xffcd', 'replace', 'ab�cd'), (
        b'ab~{\x81\x81AD~}cd', 'replace', 'ab��聊cd'), (b'ab~{AD~}cd',
        'replace', 'ab聊cd'), (b'ab~{yyAD~}cd', 'replace', 'ab��聊cd'), ('ab~cd',
        'strict', b'ab~~cd'), (b'~{Dc~~:C~}', 'strict', None), (b'~{Dc~\n:C~}',
        'strict', None)


if __name__ == '__main__':
    unittest.main()
