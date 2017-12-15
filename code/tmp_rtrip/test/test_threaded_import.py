import _imp as imp
import os
import importlib
import sys
import time
import shutil
import unittest
from test.support import verbose, import_module, run_unittest, TESTFN, reap_threads, forget, unlink, rmtree, start_threads
threading = import_module('threading')


def task(N, done, done_tasks, errors):
    try:
        if len(done_tasks) % 2:
            import modulefinder
            import random
        else:
            import random
            import modulefinder
        x = random.randrange(1, 3)
    except Exception as e:
        errors.append(e.with_traceback(None))
    finally:
        done_tasks.append(threading.get_ident())
        finished = len(done_tasks) == N
        if finished:
            done.set()


circular_imports_modules = {'A':
    """if 1:
        import time
        time.sleep(%(delay)s)
        x = 'a'
        import C
        """
    , 'B':
    """if 1:
        import time
        time.sleep(%(delay)s)
        x = 'b'
        import D
        """
    , 'C': 'import B', 'D': 'import A'}


class Finder:
    """A dummy finder to detect concurrent access to its find_spec()
    method."""

    def __init__(self):
        self.numcalls = 0
        self.x = 0
        self.lock = threading.Lock()

    def find_spec(self, name, path=None, target=None):
        assert imp.lock_held()
        with self.lock:
            self.numcalls += 1
        x = self.x
        time.sleep(0.01)
        self.x = x + 1


class FlushingFinder:
    """A dummy finder which flushes sys.path_importer_cache when it gets
    called."""

    def find_spec(self, name, path=None, target=None):
        sys.path_importer_cache.clear()


class ThreadedImportTests(unittest.TestCase):

    def setUp(self):
        self.old_random = sys.modules.pop('random', None)

    def tearDown(self):
        if self.old_random is not None:
            sys.modules['random'] = self.old_random

    def check_parallel_module_init(self):
        if imp.lock_held():
            raise unittest.SkipTest("can't run when import lock is held")
        done = threading.Event()
        for N in ((20, 50) * 3):
            if verbose:
                print('Trying', N, 'threads ...', end=' ')
            for modname in ['random', 'modulefinder']:
                try:
                    del sys.modules[modname]
                except KeyError:
                    pass
            errors = []
            done_tasks = []
            done.clear()
            t0 = time.monotonic()
            with start_threads(threading.Thread(target=task, args=(N, done,
                done_tasks, errors)) for i in range(N)):
                pass
            completed = done.wait(10 * 60)
            dt = time.monotonic() - t0
            if verbose:
                print('%.1f ms' % (dt * 1000.0), flush=True, end=' ')
            dbg_info = 'done: %s/%s' % (len(done_tasks), N)
            self.assertFalse(errors, dbg_info)
            self.assertTrue(completed, dbg_info)
            if verbose:
                print('OK.')

    def test_parallel_module_init(self):
        self.check_parallel_module_init()

    def test_parallel_meta_path(self):
        finder = Finder()
        sys.meta_path.insert(0, finder)
        try:
            self.check_parallel_module_init()
            self.assertGreater(finder.numcalls, 0)
            self.assertEqual(finder.x, finder.numcalls)
        finally:
            sys.meta_path.remove(finder)

    def test_parallel_path_hooks(self):
        finder = Finder()
        flushing_finder = FlushingFinder()

        def path_hook(path):
            finder.find_spec('')
            raise ImportError
        sys.path_hooks.insert(0, path_hook)
        sys.meta_path.append(flushing_finder)
        try:
            flushing_finder.find_spec('')
            numtests = self.check_parallel_module_init()
            self.assertGreater(finder.numcalls, 0)
            self.assertEqual(finder.x, finder.numcalls)
        finally:
            sys.meta_path.remove(flushing_finder)
            sys.path_hooks.remove(path_hook)

    def test_import_hangers(self):
        try:
            del sys.modules['test.threaded_import_hangers']
        except KeyError:
            pass
        import test.threaded_import_hangers
        self.assertFalse(test.threaded_import_hangers.errors)

    def test_circular_imports(self):
        delay = 0.5
        os.mkdir(TESTFN)
        self.addCleanup(shutil.rmtree, TESTFN)
        sys.path.insert(0, TESTFN)
        self.addCleanup(sys.path.remove, TESTFN)
        for name, contents in circular_imports_modules.items():
            contents = contents % {'delay': delay}
            with open(os.path.join(TESTFN, name + '.py'), 'wb') as f:
                f.write(contents.encode('utf-8'))
            self.addCleanup(forget, name)
        importlib.invalidate_caches()
        results = []

        def import_ab():
            import A
            results.append(getattr(A, 'x', None))

        def import_ba():
            import B
            results.append(getattr(B, 'x', None))
        t1 = threading.Thread(target=import_ab)
        t2 = threading.Thread(target=import_ba)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        self.assertEqual(set(results), {'a', 'b'})

    def test_side_effect_import(self):
        code = """if 1:
            import threading
            def target():
                import random
            t = threading.Thread(target=target)
            t.start()
            t.join()"""
        sys.path.insert(0, os.curdir)
        self.addCleanup(sys.path.remove, os.curdir)
        filename = TESTFN + '.py'
        with open(filename, 'wb') as f:
            f.write(code.encode('utf-8'))
        self.addCleanup(unlink, filename)
        self.addCleanup(forget, TESTFN)
        self.addCleanup(rmtree, '__pycache__')
        importlib.invalidate_caches()
        __import__(TESTFN)


@reap_threads
def test_main():
    old_switchinterval = None
    try:
        old_switchinterval = sys.getswitchinterval()
        sys.setswitchinterval(1e-05)
    except AttributeError:
        pass
    try:
        run_unittest(ThreadedImportTests)
    finally:
        if old_switchinterval is not None:
            sys.setswitchinterval(old_switchinterval)


if __name__ == '__main__':
    test_main()
