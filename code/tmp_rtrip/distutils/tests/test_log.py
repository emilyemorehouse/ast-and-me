"""Tests for distutils.log"""
import sys
import unittest
from tempfile import NamedTemporaryFile
from test.support import run_unittest
from distutils import log


class TestLog(unittest.TestCase):

    def test_non_ascii(self):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_threshold = log.set_threshold(log.DEBUG)
        try:
            with NamedTemporaryFile(mode='w+', encoding='ascii'
                ) as stdout, NamedTemporaryFile(mode='w+', encoding='ascii'
                ) as stderr:
                sys.stdout = stdout
                sys.stderr = stderr
                log.debug('debug:é')
                log.fatal('fatal:é')
                stdout.seek(0)
                self.assertEqual(stdout.read().rstrip(), 'debug:\\xe9')
                stderr.seek(0)
                self.assertEqual(stderr.read().rstrip(), 'fatal:\\xe9')
        finally:
            log.set_threshold(old_threshold)
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def test_suite():
    return unittest.makeSuite(TestLog)


if __name__ == '__main__':
    run_unittest(test_suite())
