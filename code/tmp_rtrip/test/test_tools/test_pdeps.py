"""Tests for the pdeps script in the Tools directory."""
import os
import unittest
import tempfile
from test.test_tools import skip_if_missing, import_tool
skip_if_missing()


class PdepsTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.pdeps = import_tool('pdeps')

    def test_process_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fn = os.path.join(tmpdir, 'foo')
            with open(fn, 'w') as stream:
                stream.write('#!/this/will/fail')
            self.pdeps.process(fn, {})

    def test_inverse_attribute_error(self):
        self.pdeps.inverse({'a': []})


if __name__ == '__main__':
    unittest.main()
