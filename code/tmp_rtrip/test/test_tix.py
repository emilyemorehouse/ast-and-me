import unittest
from test import support
import sys
_tkinter = support.import_module('_tkinter')
support.requires('gui')
from tkinter import tix, TclError


class TestTix(unittest.TestCase):

    def setUp(self):
        try:
            self.root = tix.Tk()
        except TclError:
            if sys.platform.startswith('win'):
                self.fail('Tix should always be available on Windows')
            self.skipTest('Tix not available')
        else:
            self.addCleanup(self.root.destroy)

    def test_tix_available(self):
        pass


if __name__ == '__main__':
    unittest.main()
