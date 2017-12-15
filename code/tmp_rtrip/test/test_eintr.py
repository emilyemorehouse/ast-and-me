import os
import signal
import unittest
from test import support
from test.support import script_helper


@unittest.skipUnless(os.name == 'posix', 'only supported on Unix')
class EINTRTests(unittest.TestCase):

    @unittest.skipUnless(hasattr(signal, 'setitimer'), 'requires setitimer()')
    def test_all(self):
        tester = support.findfile('eintr_tester.py', subdir='eintrdata')
        script_helper.assert_python_ok('-u', tester)


if __name__ == '__main__':
    unittest.main()
