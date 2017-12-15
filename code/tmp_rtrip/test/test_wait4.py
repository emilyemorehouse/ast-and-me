"""This test checks for correct wait4() behavior.
"""
import os
import time
import sys
import unittest
from test.fork_wait import ForkWait
from test.support import reap_children, get_attribute
get_attribute(os, 'fork')
get_attribute(os, 'wait4')


class Wait4Test(ForkWait):

    def wait_impl(self, cpid):
        option = os.WNOHANG
        if sys.platform.startswith('aix'):
            option = 0
        deadline = time.monotonic() + 10.0
        while time.monotonic() <= deadline:
            spid, status, rusage = os.wait4(cpid, option)
            if spid == cpid:
                break
            time.sleep(0.1)
        self.assertEqual(spid, cpid)
        self.assertEqual(status, 0, 'cause = %d, exit = %d' % (status & 255,
            status >> 8))
        self.assertTrue(rusage)


def tearDownModule():
    reap_children()


if __name__ == '__main__':
    unittest.main()
