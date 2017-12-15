"""Basic tests for os.popen()

  Particularly useful for platforms that fake popen.
"""
import unittest
from test import support
import os, sys
python = sys.executable
if ' ' in python:
    python = '"' + python + '"'


class PopenTest(unittest.TestCase):

    def _do_test_commandline(self, cmdline, expected):
        cmd = '%s -c "import sys; print(sys.argv)" %s'
        cmd = cmd % (python, cmdline)
        with os.popen(cmd) as p:
            data = p.read()
        got = eval(data)[1:]
        self.assertEqual(got, expected)

    def test_popen(self):
        self.assertRaises(TypeError, os.popen)
        self._do_test_commandline('foo bar', ['foo', 'bar'])
        self._do_test_commandline('foo "spam and eggs" "silly walk"', [
            'foo', 'spam and eggs', 'silly walk'])
        self._do_test_commandline('foo "a \\"quoted\\" arg" bar', ['foo',
            'a "quoted" arg', 'bar'])
        support.reap_children()

    def test_return_code(self):
        self.assertEqual(os.popen('exit 0').close(), None)
        if os.name == 'nt':
            self.assertEqual(os.popen('exit 42').close(), 42)
        else:
            self.assertEqual(os.popen('exit 42').close(), 42 << 8)

    def test_contextmanager(self):
        with os.popen('echo hello') as f:
            self.assertEqual(f.read(), 'hello\n')

    def test_iterating(self):
        with os.popen('echo hello') as f:
            self.assertEqual(list(f), ['hello\n'])

    def test_keywords(self):
        with os.popen(cmd='exit 0', mode='w', buffering=-1):
            pass


if __name__ == '__main__':
    unittest.main()
