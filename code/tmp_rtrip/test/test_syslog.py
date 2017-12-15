from test import support
syslog = support.import_module('syslog')
import unittest


class Test(unittest.TestCase):

    def test_openlog(self):
        syslog.openlog('python')
        self.assertRaises(UnicodeEncodeError, syslog.openlog, '\ud800')

    def test_syslog(self):
        syslog.openlog('python')
        syslog.syslog('test message from python test_syslog')
        syslog.syslog(syslog.LOG_ERR, 'test error from python test_syslog')

    def test_closelog(self):
        syslog.openlog('python')
        syslog.closelog()

    def test_setlogmask(self):
        syslog.setlogmask(syslog.LOG_DEBUG)

    def test_log_mask(self):
        syslog.LOG_MASK(syslog.LOG_INFO)

    def test_log_upto(self):
        syslog.LOG_UPTO(syslog.LOG_INFO)

    def test_openlog_noargs(self):
        syslog.openlog()
        syslog.syslog('test message from python test_syslog')


if __name__ == '__main__':
    unittest.main()
