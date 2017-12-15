"""Verify that warnings are issued for global statements following use."""
from test.support import run_unittest, check_syntax_error, check_warnings
import unittest
import warnings


class GlobalTests(unittest.TestCase):

    def setUp(self):
        self._warnings_manager = check_warnings()
        self._warnings_manager.__enter__()
        warnings.filterwarnings('error', module='<test string>')

    def tearDown(self):
        self._warnings_manager.__exit__(None, None, None)

    def test1(self):
        prog_text_1 = (
            'def wrong1():\n    a = 1\n    b = 2\n    global a\n    global b\n'
            )
        check_syntax_error(self, prog_text_1, lineno=4, offset=4)

    def test2(self):
        prog_text_2 = 'def wrong2():\n    print(x)\n    global x\n'
        check_syntax_error(self, prog_text_2, lineno=3, offset=4)

    def test3(self):
        prog_text_3 = 'def wrong3():\n    print(x)\n    x = 2\n    global x\n'
        check_syntax_error(self, prog_text_3, lineno=4, offset=4)

    def test4(self):
        prog_text_4 = 'global x\nx = 2\n'
        compile(prog_text_4, '<test string>', 'exec')


def test_main():
    with warnings.catch_warnings():
        warnings.filterwarnings('error', module='<test string>')
        run_unittest(GlobalTests)


if __name__ == '__main__':
    test_main()
