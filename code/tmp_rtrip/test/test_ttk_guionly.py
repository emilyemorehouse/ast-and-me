import unittest
from test import support
support.import_module('_tkinter')
support.requires('gui')
import tkinter
from _tkinter import TclError
from tkinter import ttk
from tkinter.test import runtktests
root = None
try:
    root = tkinter.Tk()
    button = ttk.Button(root)
    button.destroy()
    del button
except TclError as msg:
    raise unittest.SkipTest('ttk not available: %s' % msg)
finally:
    if root is not None:
        root.destroy()
    del root


def test_main():
    support.run_unittest(*runtktests.get_tests(text=False, packages=[
        'test_ttk']))


if __name__ == '__main__':
    test_main()
