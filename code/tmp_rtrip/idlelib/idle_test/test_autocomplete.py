""" Test autocomplete and autocomple_w

Coverage of autocomple: 56%
"""
import unittest
from test.support import requires
from tkinter import Tk, Text
import idlelib.autocomplete as ac
import idlelib.autocomplete_w as acw
from idlelib.idle_test.mock_idle import Func
from idlelib.idle_test.mock_tk import Event


class AutoCompleteWindow:

    def complete():
        return


class DummyEditwin:

    def __init__(self, root, text):
        self.root = root
        self.text = text
        self.indentwidth = 8
        self.tabwidth = 8
        self.context_use_ps1 = True


class AutoCompleteTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.text = Text(cls.root)
        cls.editor = DummyEditwin(cls.root, cls.text)

    @classmethod
    def tearDownClass(cls):
        del cls.editor, cls.text
        cls.root.destroy()
        del cls.root

    def setUp(self):
        self.editor.text.delete('1.0', 'end')
        self.autocomplete = ac.AutoComplete(self.editor)

    def test_init(self):
        self.assertEqual(self.autocomplete.editwin, self.editor)

    def test_make_autocomplete_window(self):
        testwin = self.autocomplete._make_autocomplete_window()
        self.assertIsInstance(testwin, acw.AutoCompleteWindow)

    def test_remove_autocomplete_window(self):
        self.autocomplete.autocompletewindow = (self.autocomplete.
            _make_autocomplete_window())
        self.autocomplete._remove_autocomplete_window()
        self.assertIsNone(self.autocomplete.autocompletewindow)

    def test_force_open_completions_event(self):
        o_cs = Func()
        self.autocomplete.open_completions = o_cs
        self.autocomplete.force_open_completions_event('event')
        self.assertEqual(o_cs.args, (True, False, True))

    def test_try_open_completions_event(self):
        Equal = self.assertEqual
        autocomplete = self.autocomplete
        trycompletions = self.autocomplete.try_open_completions_event
        o_c_l = Func()
        autocomplete._open_completions_later = o_c_l
        trycompletions('event')
        Equal(o_c_l.args, None)
        self.text.insert('1.0', 're.')
        trycompletions('event')
        Equal(o_c_l.args, (False, False, False, 1))
        self.text.delete('1.0', 'end')
        self.text.insert('1.0', '"./Lib/')
        trycompletions('event')
        Equal(o_c_l.args, (False, False, False, 2))

    def test_autocomplete_event(self):
        Equal = self.assertEqual
        autocomplete = self.autocomplete
        ev = Event(mc_state=True)
        self.assertIsNone(autocomplete.autocomplete_event(ev))
        del ev.mc_state
        self.text.insert('1.0', '        """Docstring.\n    ')
        self.assertIsNone(autocomplete.autocomplete_event(ev))
        self.text.delete('1.0', 'end')
        self.text.insert('1.0', 're.')
        Equal(self.autocomplete.autocomplete_event(ev), 'break')
        autocomplete._remove_autocomplete_window()
        o_cs = Func()
        autocomplete.open_completions = o_cs
        Equal(self.autocomplete.autocomplete_event(ev), None)
        Equal(o_cs.args, (False, True, True))
        o_cs.result = True
        Equal(self.autocomplete.autocomplete_event(ev), 'break')
        Equal(o_cs.args, (False, True, True))

    def test_open_completions_later(self):
        pass

    def test_delayed_open_completions(self):
        pass

    def test_open_completions(self):
        pass

    def test_fetch_completions(self):
        pass

    def test_get_entity(self):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
