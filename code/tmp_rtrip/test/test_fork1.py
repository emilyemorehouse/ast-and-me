"""This test checks for correct fork() behavior.
"""
import _imp as imp
import os
import signal
import sys
import time
import unittest
from test.fork_wait import ForkWait
from test.support import reap_children, get_attribute, import_module, verbose
threading = import_module('threading')
get_attribute(os, 'fork')


class ForkTest(ForkWait):

    def wait_impl(self, cpid):
        deadline = time.monotonic() + 10.0
        while time.monotonic() <= deadline:
            spid, status = os.waitpid(cpid, os.WNOHANG)
            if spid == cpid:
                break
            time.sleep(0.1)
        self.assertEqual(spid, cpid)
        self.assertEqual(status, 0, 'cause = %d, exit = %d' % (status & 255,
            status >> 8))

    def test_threaded_import_lock_fork(self):
        """Check fork() in main thread works while a subthread is doing an import"""
        import_started = threading.Event()
        fake_module_name = 'fake test module'
        partial_module = 'partial'
        complete_module = 'complete'

        def importer():
            imp.acquire_lock()
            sys.modules[fake_module_name] = partial_module
            import_started.set()
            time.sleep(0.01)
            sys.modules[fake_module_name] = complete_module
            imp.release_lock()
        t = threading.Thread(target=importer)
        t.start()
        import_started.wait()
        pid = os.fork()
        try:
            if not pid:
                m = __import__(fake_module_name)
                if m == complete_module:
                    os._exit(0)
                else:
                    if verbose > 1:
                        print('Child encountered partial module')
                    os._exit(1)
            else:
                t.join()
                self.wait_impl(pid)
        finally:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

    def test_nested_import_lock_fork(self):
        """Check fork() in main thread works while the main thread is doing an import"""

        def fork_with_import_lock(level):
            release = 0
            in_child = False
            try:
                try:
                    for i in range(level):
                        imp.acquire_lock()
                        release += 1
                    pid = os.fork()
                    in_child = not pid
                finally:
                    for i in range(release):
                        imp.release_lock()
            except RuntimeError:
                if in_child:
                    if verbose > 1:
                        print('RuntimeError in child')
                    os._exit(1)
                raise
            if in_child:
                os._exit(0)
            self.wait_impl(pid)
        for level in range(5):
            fork_with_import_lock(level)


def tearDownModule():
    reap_children()


if __name__ == '__main__':
    unittest.main()
