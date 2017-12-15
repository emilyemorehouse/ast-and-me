import unittest
from test import support
import os
import sys
from os import path
startfile = support.get_attribute(os, 'startfile')


class TestCase(unittest.TestCase):

    def test_nonexisting(self):
        self.assertRaises(OSError, startfile, 'nonexisting.vbs')

    def test_empty(self):
        with support.change_cwd(path.dirname(sys.executable)):
            empty = path.join(path.dirname(__file__), 'empty.vbs')
            startfile(empty)
            startfile(empty, 'open')


if __name__ == '__main__':
    unittest.main()
