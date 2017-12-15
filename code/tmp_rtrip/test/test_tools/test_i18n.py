"""Tests to cover the Tools/i18n package"""
import os
import unittest
from test.support.script_helper import assert_python_ok
from test.test_tools import skip_if_missing, toolsdir
from test.support import temp_cwd
skip_if_missing()


class Test_pygettext(unittest.TestCase):
    """Tests for the pygettext.py tool"""
    script = os.path.join(toolsdir, 'i18n', 'pygettext.py')

    def get_header(self, data):
        """ utility: return the header of a .po file as a dictionary """
        headers = {}
        for line in data.split('\n'):
            if not line or line.startswith(('#', 'msgid', 'msgstr')):
                continue
            line = line.strip('"')
            key, val = line.split(':', 1)
            headers[key] = val.strip()
        return headers

    def test_header(self):
        """Make sure the required fields are in the header, according to:
           http://www.gnu.org/software/gettext/manual/gettext.html#Header-Entry
        """
        with temp_cwd(None) as cwd:
            assert_python_ok(self.script)
            with open('messages.pot') as fp:
                data = fp.read()
            header = self.get_header(data)
            self.assertIn('Project-Id-Version', header)
            self.assertIn('POT-Creation-Date', header)
            self.assertIn('PO-Revision-Date', header)
            self.assertIn('Last-Translator', header)
            self.assertIn('Language-Team', header)
            self.assertIn('MIME-Version', header)
            self.assertIn('Content-Type', header)
            self.assertIn('Content-Transfer-Encoding', header)
            self.assertIn('Generated-By', header)

    def test_POT_Creation_Date(self):
        """ Match the date format from xgettext for POT-Creation-Date """
        from datetime import datetime
        with temp_cwd(None) as cwd:
            assert_python_ok(self.script)
            with open('messages.pot') as fp:
                data = fp.read()
            header = self.get_header(data)
            creationDate = header['POT-Creation-Date']
            if creationDate.endswith('\\n'):
                creationDate = creationDate[:-len('\\n')]
            datetime.strptime(creationDate, '%Y-%m-%d %H:%M%z')
