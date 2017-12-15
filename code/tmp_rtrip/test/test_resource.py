import contextlib
import sys
import os
import unittest
from test import support
import time
resource = support.import_module('resource')


class ResourceTest(unittest.TestCase):

    def test_args(self):
        self.assertRaises(TypeError, resource.getrlimit)
        self.assertRaises(TypeError, resource.getrlimit, 42, 42)
        self.assertRaises(TypeError, resource.setrlimit)
        self.assertRaises(TypeError, resource.setrlimit, 42, 42, 42)

    def test_fsize_ismax(self):
        try:
            cur, max = resource.getrlimit(resource.RLIMIT_FSIZE)
        except AttributeError:
            pass
        else:
            self.assertEqual(resource.RLIM_INFINITY, max)
            resource.setrlimit(resource.RLIMIT_FSIZE, (cur, max))

    def test_fsize_enforced(self):
        try:
            cur, max = resource.getrlimit(resource.RLIMIT_FSIZE)
        except AttributeError:
            pass
        else:
            try:
                try:
                    resource.setrlimit(resource.RLIMIT_FSIZE, (1024, max))
                    limit_set = True
                except ValueError:
                    limit_set = False
                f = open(support.TESTFN, 'wb')
                try:
                    f.write(b'X' * 1024)
                    try:
                        f.write(b'Y')
                        f.flush()
                        for i in range(5):
                            time.sleep(0.1)
                            f.flush()
                    except OSError:
                        if not limit_set:
                            raise
                    if limit_set:
                        resource.setrlimit(resource.RLIMIT_FSIZE, (cur, max))
                finally:
                    f.close()
            finally:
                if limit_set:
                    resource.setrlimit(resource.RLIMIT_FSIZE, (cur, max))
                support.unlink(support.TESTFN)

    def test_fsize_toobig(self):
        too_big = 10 ** 50
        try:
            cur, max = resource.getrlimit(resource.RLIMIT_FSIZE)
        except AttributeError:
            pass
        else:
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE, (too_big, max))
            except (OverflowError, ValueError):
                pass
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE, (max, too_big))
            except (OverflowError, ValueError):
                pass

    def test_getrusage(self):
        self.assertRaises(TypeError, resource.getrusage)
        self.assertRaises(TypeError, resource.getrusage, 42, 42)
        usageself = resource.getrusage(resource.RUSAGE_SELF)
        usagechildren = resource.getrusage(resource.RUSAGE_CHILDREN)
        try:
            usageboth = resource.getrusage(resource.RUSAGE_BOTH)
        except (ValueError, AttributeError):
            pass
        try:
            usage_thread = resource.getrusage(resource.RUSAGE_THREAD)
        except (ValueError, AttributeError):
            pass

    def test_setrusage_refcount(self):
        try:
            limits = resource.getrlimit(resource.RLIMIT_CPU)
        except AttributeError:
            pass
        else:


            class BadSequence:

                def __len__(self):
                    return 2

                def __getitem__(self, key):
                    if key in (0, 1):
                        return len(tuple(range(1000000)))
                    raise IndexError
            resource.setrlimit(resource.RLIMIT_CPU, BadSequence())

    def test_pagesize(self):
        pagesize = resource.getpagesize()
        self.assertIsInstance(pagesize, int)
        self.assertGreaterEqual(pagesize, 0)

    @unittest.skipUnless(sys.platform == 'linux', 'test requires Linux')
    def test_linux_constants(self):
        for attr in ['MSGQUEUE', 'NICE', 'RTPRIO', 'RTTIME', 'SIGPENDING']:
            with contextlib.suppress(AttributeError):
                self.assertIsInstance(getattr(resource, 'RLIMIT_' + attr), int)

    @support.requires_freebsd_version(9)
    def test_freebsd_contants(self):
        for attr in ['SWAP', 'SBSIZE', 'NPTS']:
            with contextlib.suppress(AttributeError):
                self.assertIsInstance(getattr(resource, 'RLIMIT_' + attr), int)

    @unittest.skipUnless(hasattr(resource, 'prlimit'), 'no prlimit')
    @support.requires_linux_version(2, 6, 36)
    def test_prlimit(self):
        self.assertRaises(TypeError, resource.prlimit)
        if os.geteuid() != 0:
            self.assertRaises(PermissionError, resource.prlimit, 1,
                resource.RLIMIT_AS)
        self.assertRaises(ProcessLookupError, resource.prlimit, -1,
            resource.RLIMIT_AS)
        limit = resource.getrlimit(resource.RLIMIT_AS)
        self.assertEqual(resource.prlimit(0, resource.RLIMIT_AS), limit)
        self.assertEqual(resource.prlimit(0, resource.RLIMIT_AS, limit), limit)

    @unittest.skipUnless(hasattr(resource, 'prlimit'), 'no prlimit')
    @support.requires_linux_version(2, 6, 36)
    def test_prlimit_refcount(self):


        class BadSeq:

            def __len__(self):
                return 2

            def __getitem__(self, key):
                return limits[key] - 1
        limits = resource.getrlimit(resource.RLIMIT_AS)
        self.assertEqual(resource.prlimit(0, resource.RLIMIT_AS, BadSeq()),
            limits)


def test_main(verbose=None):
    support.run_unittest(ResourceTest)


if __name__ == '__main__':
    test_main()
