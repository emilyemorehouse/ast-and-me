from test import support
support.import_module('_tkinter')
support.requires('gui')
from tkinter.test import runtktests


def test_main():
    support.run_unittest(*runtktests.get_tests(text=False, packages=[
        'test_tkinter']))


if __name__ == '__main__':
    test_main()
