"""Test SearchDialog class in idlelib.search.py"""
from test.support import requires
requires('gui')
import unittest
import tkinter as tk
from tkinter import BooleanVar
import idlelib.searchengine as se
import idlelib.search as sd


class SearchDialogTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        del cls.root

    def setUp(self):
        self.engine = se.SearchEngine(self.root)
        self.dialog = sd.SearchDialog(self.root, self.engine)
        self.dialog.bell = lambda : None
        self.text = tk.Text(self.root)
        self.text.insert('1.0', 'Hello World!')

    def test_find_again(self):
        text = self.text
        self.engine.setpat('')
        self.assertFalse(self.dialog.find_again(text))
        self.dialog.bell = lambda : None
        self.engine.setpat('Hello')
        self.assertTrue(self.dialog.find_again(text))
        self.engine.setpat('Goodbye')
        self.assertFalse(self.dialog.find_again(text))
        self.engine.setpat('World!')
        self.assertTrue(self.dialog.find_again(text))
        self.engine.setpat('Hello World!')
        self.assertTrue(self.dialog.find_again(text))
        self.engine.revar = BooleanVar(self.root, True)
        self.engine.setpat('W[aeiouy]r')
        self.assertTrue(self.dialog.find_again(text))

    def test_find_selection(self):
        text = self.text
        self.text.insert('2.0', 'Hello World!')
        text.tag_add('sel', '1.0', '1.4')
        self.assertTrue(self.dialog.find_selection(text))
        text.tag_remove('sel', '1.0', 'end')
        text.tag_add('sel', '1.6', '1.11')
        self.assertTrue(self.dialog.find_selection(text))
        text.tag_remove('sel', '1.0', 'end')
        text.tag_add('sel', '1.0', '1.11')
        self.assertTrue(self.dialog.find_selection(text))
        text.delete('2.0', 'end')


if __name__ == '__main__':
    unittest.main(verbosity=2, exit=2)
