"""
Tests for the threading module.
"""
import test.support
from test.support import verbose, import_module, cpython_only, requires_type_collecting
from test.support.script_helper import assert_python_ok, assert_python_failure
import random
import sys
_thread = import_module('_thread')
threading = import_module('threading')
import time
import unittest
import weakref
import os
import subprocess
from test import lock_tests
from test import support
platforms_to_skip = 'freebsd4', 'freebsd5', 'freebsd6', 'netbsd5', 'hp-ux11'


class Counter(object):

    def __init__(self):
        self.value = 0

    def inc(self):
        self.value += 1

    def dec(self):
        self.value -= 1

    def get(self):
        return self.value


class TestThread(threading.Thread):

    def __init__(self, name, testcase, sema, mutex, nrunning):
        threading.Thread.__init__(self, name=name)
        self.testcase = testcase
        self.sema = sema
        self.mutex = mutex
        self.nrunning = nrunning

    def run(self):
        delay = random.random() / 10000.0
        if verbose:
            print('task %s will run for %.1f usec' % (self.name, delay * 
                1000000.0))
        with self.sema:
            with self.mutex:
                self.nrunning.inc()
                if verbose:
                    print(self.nrunning.get(), 'tasks are running')
                self.testcase.assertLessEqual(self.nrunning.get(), 3)
            time.sleep(delay)
            if verbose:
                print('task', self.name, 'done')
            with self.mutex:
                self.nrunning.dec()
                self.testcase.assertGreaterEqual(self.nrunning.get(), 0)
                if verbose:
                    print('%s is finished. %d tasks are running' % (self.
                        name, self.nrunning.get()))


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self._threads = test.support.threading_setup()

    def tearDown(self):
        test.support.threading_cleanup(*self._threads)
        test.support.reap_children()


class ThreadTests(BaseTestCase):

    def test_various_ops(self):
        NUMTASKS = 10
        sema = threading.BoundedSemaphore(value=3)
        mutex = threading.RLock()
        numrunning = Counter()
        threads = []
        for i in range(NUMTASKS):
            t = TestThread('<thread %d>' % i, self, sema, mutex, numrunning)
            threads.append(t)
            self.assertIsNone(t.ident)
            self.assertRegex(repr(t), '^<TestThread\\(.*, initial\\)>$')
            t.start()
        if verbose:
            print('waiting for all tasks to complete')
        for t in threads:
            t.join()
            self.assertFalse(t.is_alive())
            self.assertNotEqual(t.ident, 0)
            self.assertIsNotNone(t.ident)
            self.assertRegex(repr(t), '^<TestThread\\(.*, stopped -?\\d+\\)>$')
        if verbose:
            print('all tasks done')
        self.assertEqual(numrunning.get(), 0)

    def test_ident_of_no_threading_threads(self):
        self.assertIsNotNone(threading.currentThread().ident)

        def f():
            ident.append(threading.currentThread().ident)
            done.set()
        done = threading.Event()
        ident = []
        _thread.start_new_thread(f, ())
        done.wait()
        self.assertIsNotNone(ident[0])
        del threading._active[ident[0]]

    def test_various_ops_small_stack(self):
        if verbose:
            print('with 256kB thread stack size...')
        try:
            threading.stack_size(262144)
        except _thread.error:
            raise unittest.SkipTest(
                'platform does not support changing thread stack size')
        self.test_various_ops()
        threading.stack_size(0)

    def test_various_ops_large_stack(self):
        if verbose:
            print('with 1MB thread stack size...')
        try:
            threading.stack_size(1048576)
        except _thread.error:
            raise unittest.SkipTest(
                'platform does not support changing thread stack size')
        self.test_various_ops()
        threading.stack_size(0)

    def test_foreign_thread(self):

        def f(mutex):
            threading.current_thread()
            mutex.release()
        mutex = threading.Lock()
        mutex.acquire()
        tid = _thread.start_new_thread(f, (mutex,))
        mutex.acquire()
        self.assertIn(tid, threading._active)
        self.assertIsInstance(threading._active[tid], threading._DummyThread)
        self.assertTrue(threading._active[tid].is_alive())
        self.assertRegex(repr(threading._active[tid]), '_DummyThread')
        del threading._active[tid]

    def test_PyThreadState_SetAsyncExc(self):
        ctypes = import_module('ctypes')
        set_async_exc = ctypes.pythonapi.PyThreadState_SetAsyncExc


        class AsyncExc(Exception):
            pass
        exception = ctypes.py_object(AsyncExc)
        tid = threading.get_ident()
        try:
            result = set_async_exc(ctypes.c_long(tid), exception)
            while True:
                pass
        except AsyncExc:
            pass
        else:
            self.fail('AsyncExc not raised')
        try:
            self.assertEqual(result, 1)
        except UnboundLocalError:
            pass
        worker_started = threading.Event()
        worker_saw_exception = threading.Event()


        class Worker(threading.Thread):

            def run(self):
                self.id = threading.get_ident()
                self.finished = False
                try:
                    while True:
                        worker_started.set()
                        time.sleep(0.1)
                except AsyncExc:
                    self.finished = True
                    worker_saw_exception.set()
        t = Worker()
        t.daemon = True
        t.start()
        if verbose:
            print('    started worker thread')
        if verbose:
            print('    trying nonsensical thread id')
        result = set_async_exc(ctypes.c_long(-1), exception)
        self.assertEqual(result, 0)
        if verbose:
            print('    waiting for worker thread to get started')
        ret = worker_started.wait()
        self.assertTrue(ret)
        if verbose:
            print("    verifying worker hasn't exited")
        self.assertFalse(t.finished)
        if verbose:
            print('    attempting to raise asynch exception in worker')
        result = set_async_exc(ctypes.c_long(t.id), exception)
        self.assertEqual(result, 1)
        if verbose:
            print('    waiting for worker to say it caught the exception')
        worker_saw_exception.wait(timeout=10)
        self.assertTrue(t.finished)
        if verbose:
            print('    all OK -- joining worker')
        if t.finished:
            t.join()

    def test_limbo_cleanup(self):

        def fail_new_thread(*args):
            raise threading.ThreadError()
        _start_new_thread = threading._start_new_thread
        threading._start_new_thread = fail_new_thread
        try:
            t = threading.Thread(target=lambda : None)
            self.assertRaises(threading.ThreadError, t.start)
            self.assertFalse(t in threading._limbo,
                'Failed to cleanup _limbo map on failure of Thread.start().')
        finally:
            threading._start_new_thread = _start_new_thread

    def test_finalize_runnning_thread(self):
        import_module('ctypes')
        rc, out, err = assert_python_failure('-c',
            """if 1:
            import ctypes, sys, time, _thread

            # This lock is used as a simple event variable.
            ready = _thread.allocate_lock()
            ready.acquire()

            # Module globals are cleared before __del__ is run
            # So we save the functions in class dict
            class C:
                ensure = ctypes.pythonapi.PyGILState_Ensure
                release = ctypes.pythonapi.PyGILState_Release
                def __del__(self):
                    state = self.ensure()
                    self.release(state)

            def waitingThread():
                x = C()
                ready.release()
                time.sleep(100)

            _thread.start_new_thread(waitingThread, ())
            ready.acquire()  # Be sure the other thread is waiting.
            sys.exit(42)
            """
            )
        self.assertEqual(rc, 42)

    def test_finalize_with_trace(self):
        assert_python_ok('-c',
            """if 1:
            import sys, threading

            # A deadlock-killer, to prevent the
            # testsuite to hang forever
            def killer():
                import os, time
                time.sleep(2)
                print('program blocked; aborting')
                os._exit(2)
            t = threading.Thread(target=killer)
            t.daemon = True
            t.start()

            # This is the trace function
            def func(frame, event, arg):
                threading.current_thread()
                return func

            sys.settrace(func)
            """
            )

    def test_join_nondaemon_on_shutdown(self):
        rc, out, err = assert_python_ok('-c',
            """if 1:
                import threading
                from time import sleep

                def child():
                    sleep(1)
                    # As a non-daemon thread we SHOULD wake up and nothing
                    # should be torn down yet
                    print("Woke up, sleep function is:", sleep)

                threading.Thread(target=child).start()
                raise SystemExit
            """
            )
        self.assertEqual(out.strip(),
            b'Woke up, sleep function is: <built-in function sleep>')
        self.assertEqual(err, b'')

    def test_enumerate_after_join(self):
        enum = threading.enumerate
        old_interval = sys.getswitchinterval()
        try:
            for i in range(1, 100):
                sys.setswitchinterval(i * 0.0002)
                t = threading.Thread(target=lambda : None)
                t.start()
                t.join()
                l = enum()
                self.assertNotIn(t, l, 
                    '#1703448 triggered after %d trials: %s' % (i, l))
        finally:
            sys.setswitchinterval(old_interval)

    def test_no_refcycle_through_target(self):


        class RunSelfFunction(object):

            def __init__(self, should_raise):
                self.should_raise = should_raise
                self.thread = threading.Thread(target=self._run, args=(self
                    ,), kwargs={'yet_another': self})
                self.thread.start()

            def _run(self, other_ref, yet_another):
                if self.should_raise:
                    raise SystemExit
        cyclic_object = RunSelfFunction(should_raise=False)
        weak_cyclic_object = weakref.ref(cyclic_object)
        cyclic_object.thread.join()
        del cyclic_object
        self.assertIsNone(weak_cyclic_object(), msg=
            '%d references still around' % sys.getrefcount(
            weak_cyclic_object()))
        raising_cyclic_object = RunSelfFunction(should_raise=True)
        weak_raising_cyclic_object = weakref.ref(raising_cyclic_object)
        raising_cyclic_object.thread.join()
        del raising_cyclic_object
        self.assertIsNone(weak_raising_cyclic_object(), msg=
            '%d references still around' % sys.getrefcount(
            weak_raising_cyclic_object()))

    def test_old_threading_api(self):
        t = threading.Thread()
        t.isDaemon()
        t.setDaemon(True)
        t.getName()
        t.setName('name')
        t.isAlive()
        e = threading.Event()
        e.isSet()
        threading.activeCount()

    def test_repr_daemon(self):
        t = threading.Thread()
        self.assertNotIn('daemon', repr(t))
        t.daemon = True
        self.assertIn('daemon', repr(t))

    def test_deamon_param(self):
        t = threading.Thread()
        self.assertFalse(t.daemon)
        t = threading.Thread(daemon=False)
        self.assertFalse(t.daemon)
        t = threading.Thread(daemon=True)
        self.assertTrue(t.daemon)

    @unittest.skipUnless(hasattr(os, 'fork'), 'test needs fork()')
    def test_dummy_thread_after_fork(self):
        code = """if 1:
            import _thread, threading, os, time

            def background_thread(evt):
                # Creates and registers the _DummyThread instance
                threading.current_thread()
                evt.set()
                time.sleep(10)

            evt = threading.Event()
            _thread.start_new_thread(background_thread, (evt,))
            evt.wait()
            assert threading.active_count() == 2, threading.active_count()
            if os.fork() == 0:
                assert threading.active_count() == 1, threading.active_count()
                os._exit(0)
            else:
                os.wait()
        """
        _, out, err = assert_python_ok('-c', code)
        self.assertEqual(out, b'')
        self.assertEqual(err, b'')

    @unittest.skipUnless(hasattr(os, 'fork'), 'needs os.fork()')
    def test_is_alive_after_fork(self):
        old_interval = sys.getswitchinterval()
        self.addCleanup(sys.setswitchinterval, old_interval)
        test.support.setswitchinterval(1e-06)
        for i in range(20):
            t = threading.Thread(target=lambda : None)
            t.start()
            pid = os.fork()
            if pid == 0:
                os._exit(11 if t.is_alive() else 10)
            else:
                t.join()
                pid, status = os.waitpid(pid, 0)
                self.assertTrue(os.WIFEXITED(status))
                self.assertEqual(10, os.WEXITSTATUS(status))

    def test_main_thread(self):
        main = threading.main_thread()
        self.assertEqual(main.name, 'MainThread')
        self.assertEqual(main.ident, threading.current_thread().ident)
        self.assertEqual(main.ident, threading.get_ident())

        def f():
            self.assertNotEqual(threading.main_thread().ident, threading.
                current_thread().ident)
        th = threading.Thread(target=f)
        th.start()
        th.join()

    @unittest.skipUnless(hasattr(os, 'fork'), 'test needs os.fork()')
    @unittest.skipUnless(hasattr(os, 'waitpid'), 'test needs os.waitpid()')
    def test_main_thread_after_fork(self):
        code = """if 1:
            import os, threading

            pid = os.fork()
            if pid == 0:
                main = threading.main_thread()
                print(main.name)
                print(main.ident == threading.current_thread().ident)
                print(main.ident == threading.get_ident())
            else:
                os.waitpid(pid, 0)
        """
        _, out, err = assert_python_ok('-c', code)
        data = out.decode().replace('\r', '')
        self.assertEqual(err, b'')
        self.assertEqual(data, 'MainThread\nTrue\nTrue\n')

    @unittest.skipIf(sys.platform in platforms_to_skip, 'due to known OS bug')
    @unittest.skipUnless(hasattr(os, 'fork'), 'test needs os.fork()')
    @unittest.skipUnless(hasattr(os, 'waitpid'), 'test needs os.waitpid()')
    def test_main_thread_after_fork_from_nonmain_thread(self):
        code = """if 1:
            import os, threading, sys

            def f():
                pid = os.fork()
                if pid == 0:
                    main = threading.main_thread()
                    print(main.name)
                    print(main.ident == threading.current_thread().ident)
                    print(main.ident == threading.get_ident())
                    # stdout is fully buffered because not a tty,
                    # we have to flush before exit.
                    sys.stdout.flush()
                else:
                    os.waitpid(pid, 0)

            th = threading.Thread(target=f)
            th.start()
            th.join()
        """
        _, out, err = assert_python_ok('-c', code)
        data = out.decode().replace('\r', '')
        self.assertEqual(err, b'')
        self.assertEqual(data, 'Thread-1\nTrue\nTrue\n')

    def test_tstate_lock(self):
        started = _thread.allocate_lock()
        finish = _thread.allocate_lock()
        started.acquire()
        finish.acquire()

        def f():
            started.release()
            finish.acquire()
            time.sleep(0.01)
        t = threading.Thread(target=f)
        self.assertIs(t._tstate_lock, None)
        t.start()
        started.acquire()
        self.assertTrue(t.is_alive())
        tstate_lock = t._tstate_lock
        self.assertFalse(tstate_lock.acquire(timeout=0), False)
        finish.release()
        self.assertTrue(tstate_lock.acquire(timeout=5), False)
        self.assertTrue(t.is_alive())
        tstate_lock.release()
        self.assertFalse(t.is_alive())
        self.assertIsNone(t._tstate_lock)

    def test_repr_stopped(self):
        started = _thread.allocate_lock()
        finish = _thread.allocate_lock()
        started.acquire()
        finish.acquire()

        def f():
            started.release()
            finish.acquire()
        t = threading.Thread(target=f)
        t.start()
        started.acquire()
        self.assertIn('started', repr(t))
        finish.release()
        LOOKING_FOR = 'stopped'
        for i in range(500):
            if LOOKING_FOR in repr(t):
                break
            time.sleep(0.01)
        self.assertIn(LOOKING_FOR, repr(t))

    def test_BoundedSemaphore_limit(self):
        for limit in range(1, 10):
            bs = threading.BoundedSemaphore(limit)
            threads = [threading.Thread(target=bs.acquire) for _ in range(
                limit)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            threads = [threading.Thread(target=bs.release) for _ in range(
                limit)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            self.assertRaises(ValueError, bs.release)

    @cpython_only
    def test_frame_tstate_tracing(self):

        def noop_trace(frame, event, arg):
            return noop_trace

        def generator():
            while 1:
                yield 'generator'

        def callback():
            if callback.gen is None:
                callback.gen = generator()
            return next(callback.gen)
        callback.gen = None
        old_trace = sys.gettrace()
        sys.settrace(noop_trace)
        try:
            threading.settrace(noop_trace)
            import _testcapi
            _testcapi.call_in_temporary_c_thread(callback)
            for test in range(3):
                callback()
        finally:
            sys.settrace(old_trace)


class ThreadJoinOnShutdown(BaseTestCase):

    def _run_and_join(self, script):
        script = (
            """if 1:
            import sys, os, time, threading

            # a thread, which waits for the main program to terminate
            def joiningfunc(mainthread):
                mainthread.join()
                print('end of thread')
                # stdout is fully buffered because not a tty, we have to flush
                # before exit.
                sys.stdout.flush()
        
"""
             + script)
        rc, out, err = assert_python_ok('-c', script)
        data = out.decode().replace('\r', '')
        self.assertEqual(data, 'end of main\nend of thread\n')

    def test_1_join_on_shutdown(self):
        script = """if 1:
            import os
            t = threading.Thread(target=joiningfunc,
                                 args=(threading.current_thread(),))
            t.start()
            time.sleep(0.1)
            print('end of main')
            """
        self._run_and_join(script)

    @unittest.skipUnless(hasattr(os, 'fork'), 'needs os.fork()')
    @unittest.skipIf(sys.platform in platforms_to_skip, 'due to known OS bug')
    def test_2_join_in_forked_process(self):
        script = """if 1:
            childpid = os.fork()
            if childpid != 0:
                os.waitpid(childpid, 0)
                sys.exit(0)

            t = threading.Thread(target=joiningfunc,
                                 args=(threading.current_thread(),))
            t.start()
            print('end of main')
            """
        self._run_and_join(script)

    @unittest.skipUnless(hasattr(os, 'fork'), 'needs os.fork()')
    @unittest.skipIf(sys.platform in platforms_to_skip, 'due to known OS bug')
    def test_3_join_in_forked_from_thread(self):
        script = """if 1:
            main_thread = threading.current_thread()
            def worker():
                childpid = os.fork()
                if childpid != 0:
                    os.waitpid(childpid, 0)
                    sys.exit(0)

                t = threading.Thread(target=joiningfunc,
                                     args=(main_thread,))
                print('end of main')
                t.start()
                t.join() # Should not block: main_thread is already stopped

            w = threading.Thread(target=worker)
            w.start()
            """
        self._run_and_join(script)

    @unittest.skipIf(sys.platform in platforms_to_skip, 'due to known OS bug')
    def test_4_daemon_threads(self):
        script = """if True:
            import os
            import random
            import sys
            import time
            import threading

            thread_has_run = set()

            def random_io():
                '''Loop for a while sleeping random tiny amounts and doing some I/O.'''
                while True:
                    in_f = open(os.__file__, 'rb')
                    stuff = in_f.read(200)
                    null_f = open(os.devnull, 'wb')
                    null_f.write(stuff)
                    time.sleep(random.random() / 1995)
                    null_f.close()
                    in_f.close()
                    thread_has_run.add(threading.current_thread())

            def main():
                count = 0
                for _ in range(40):
                    new_thread = threading.Thread(target=random_io)
                    new_thread.daemon = True
                    new_thread.start()
                    count += 1
                while len(thread_has_run) < count:
                    time.sleep(0.001)
                # Trigger process shutdown
                sys.exit(0)

            main()
            """
        rc, out, err = assert_python_ok('-c', script)
        self.assertFalse(err)

    @unittest.skipUnless(hasattr(os, 'fork'), 'needs os.fork()')
    @unittest.skipIf(sys.platform in platforms_to_skip, 'due to known OS bug')
    def test_reinit_tls_after_fork(self):

        def do_fork_and_wait():
            pid = os.fork()
            if pid > 0:
                os.waitpid(pid, 0)
            else:
                os._exit(0)
        threads = []
        for i in range(16):
            t = threading.Thread(target=do_fork_and_wait)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

    @unittest.skipUnless(hasattr(os, 'fork'), 'needs os.fork()')
    def test_clear_threads_states_after_fork(self):
        threads = []
        for i in range(16):
            t = threading.Thread(target=lambda : time.sleep(0.3))
            threads.append(t)
            t.start()
        pid = os.fork()
        if pid == 0:
            if len(sys._current_frames()) == 1:
                os._exit(0)
            else:
                os._exit(1)
        else:
            _, status = os.waitpid(pid, 0)
            self.assertEqual(0, status)
        for t in threads:
            t.join()


class SubinterpThreadingTests(BaseTestCase):

    def test_threads_join(self):
        r, w = os.pipe()
        self.addCleanup(os.close, r)
        self.addCleanup(os.close, w)
        code = (
            """if 1:
            import os
            import threading
            import time

            def f():
                # Sleep a bit so that the thread is still running when
                # Py_EndInterpreter is called.
                time.sleep(0.05)
                os.write(%d, b"x")
            threading.Thread(target=f).start()
            """
             % (w,))
        ret = test.support.run_in_subinterp(code)
        self.assertEqual(ret, 0)
        self.assertEqual(os.read(r, 1), b'x')

    def test_threads_join_2(self):
        r, w = os.pipe()
        self.addCleanup(os.close, r)
        self.addCleanup(os.close, w)
        code = (
            """if 1:
            import os
            import threading
            import time

            class Sleeper:
                def __del__(self):
                    time.sleep(0.05)

            tls = threading.local()

            def f():
                # Sleep a bit so that the thread is still running when
                # Py_EndInterpreter is called.
                time.sleep(0.05)
                tls.x = Sleeper()
                os.write(%d, b"x")
            threading.Thread(target=f).start()
            """
             % (w,))
        ret = test.support.run_in_subinterp(code)
        self.assertEqual(ret, 0)
        self.assertEqual(os.read(r, 1), b'x')

    @cpython_only
    def test_daemon_threads_fatal_error(self):
        subinterp_code = """if 1:
            import os
            import threading
            import time

            def f():
                # Make sure the daemon thread is still running when
                # Py_EndInterpreter is called.
                time.sleep(10)
            threading.Thread(target=f, daemon=True).start()
            """
        script = (
            """if 1:
            import _testcapi

            _testcapi.run_in_subinterp(%r)
            """
             % (subinterp_code,))
        with test.support.SuppressCrashReport():
            rc, out, err = assert_python_failure('-c', script)
        self.assertIn(
            'Fatal Python error: Py_EndInterpreter: not the last thread',
            err.decode())


class ThreadingExceptionTests(BaseTestCase):

    def test_start_thread_again(self):
        thread = threading.Thread()
        thread.start()
        self.assertRaises(RuntimeError, thread.start)

    def test_joining_current_thread(self):
        current_thread = threading.current_thread()
        self.assertRaises(RuntimeError, current_thread.join)

    def test_joining_inactive_thread(self):
        thread = threading.Thread()
        self.assertRaises(RuntimeError, thread.join)

    def test_daemonize_active_thread(self):
        thread = threading.Thread()
        thread.start()
        self.assertRaises(RuntimeError, setattr, thread, 'daemon', True)

    def test_releasing_unacquired_lock(self):
        lock = threading.Lock()
        self.assertRaises(RuntimeError, lock.release)

    @unittest.skipUnless(sys.platform == 'darwin' and test.support.
        python_is_optimized(), 'test macosx problem')
    def test_recursion_limit(self):
        script = """if True:
            import threading

            def recurse():
                return recurse()

            def outer():
                try:
                    recurse()
                except RecursionError:
                    pass

            w = threading.Thread(target=outer)
            w.start()
            w.join()
            print('end of main thread')
            """
        expected_output = 'end of main thread\n'
        p = subprocess.Popen([sys.executable, '-c', script], stdout=
            subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        data = stdout.decode().replace('\r', '')
        self.assertEqual(p.returncode, 0, 'Unexpected error: ' + stderr.
            decode())
        self.assertEqual(data, expected_output)

    def test_print_exception(self):
        script = """if True:
            import threading
            import time

            running = False
            def run():
                global running
                running = True
                while running:
                    time.sleep(0.01)
                1/0
            t = threading.Thread(target=run)
            t.start()
            while not running:
                time.sleep(0.01)
            running = False
            t.join()
            """
        rc, out, err = assert_python_ok('-c', script)
        self.assertEqual(out, b'')
        err = err.decode()
        self.assertIn('Exception in thread', err)
        self.assertIn('Traceback (most recent call last):', err)
        self.assertIn('ZeroDivisionError', err)
        self.assertNotIn('Unhandled exception', err)

    @requires_type_collecting
    def test_print_exception_stderr_is_none_1(self):
        script = """if True:
            import sys
            import threading
            import time

            running = False
            def run():
                global running
                running = True
                while running:
                    time.sleep(0.01)
                1/0
            t = threading.Thread(target=run)
            t.start()
            while not running:
                time.sleep(0.01)
            sys.stderr = None
            running = False
            t.join()
            """
        rc, out, err = assert_python_ok('-c', script)
        self.assertEqual(out, b'')
        err = err.decode()
        self.assertIn('Exception in thread', err)
        self.assertIn('Traceback (most recent call last):', err)
        self.assertIn('ZeroDivisionError', err)
        self.assertNotIn('Unhandled exception', err)

    def test_print_exception_stderr_is_none_2(self):
        script = """if True:
            import sys
            import threading
            import time

            running = False
            def run():
                global running
                running = True
                while running:
                    time.sleep(0.01)
                1/0
            sys.stderr = None
            t = threading.Thread(target=run)
            t.start()
            while not running:
                time.sleep(0.01)
            running = False
            t.join()
            """
        rc, out, err = assert_python_ok('-c', script)
        self.assertEqual(out, b'')
        self.assertNotIn('Unhandled exception', err.decode())

    def test_bare_raise_in_brand_new_thread(self):

        def bare_raise():
            raise


        class Issue27558(threading.Thread):
            exc = None

            def run(self):
                try:
                    bare_raise()
                except Exception as exc:
                    self.exc = exc
        thread = Issue27558()
        thread.start()
        thread.join()
        self.assertIsNotNone(thread.exc)
        self.assertIsInstance(thread.exc, RuntimeError)


class TimerTests(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)
        self.callback_args = []
        self.callback_event = threading.Event()

    def test_init_immutable_default_args(self):
        timer1 = threading.Timer(0.01, self._callback_spy)
        timer1.start()
        self.callback_event.wait()
        timer1.args.append('blah')
        timer1.kwargs['foo'] = 'bar'
        self.callback_event.clear()
        timer2 = threading.Timer(0.01, self._callback_spy)
        timer2.start()
        self.callback_event.wait()
        self.assertEqual(len(self.callback_args), 2)
        self.assertEqual(self.callback_args, [((), {}), ((), {})])

    def _callback_spy(self, *args, **kwargs):
        self.callback_args.append((args[:], kwargs.copy()))
        self.callback_event.set()


class LockTests(lock_tests.LockTests):
    locktype = staticmethod(threading.Lock)


class PyRLockTests(lock_tests.RLockTests):
    locktype = staticmethod(threading._PyRLock)


@unittest.skipIf(threading._CRLock is None, 'RLock not implemented in C')
class CRLockTests(lock_tests.RLockTests):
    locktype = staticmethod(threading._CRLock)


class EventTests(lock_tests.EventTests):
    eventtype = staticmethod(threading.Event)


class ConditionAsRLockTests(lock_tests.RLockTests):
    locktype = staticmethod(threading.Condition)


class ConditionTests(lock_tests.ConditionTests):
    condtype = staticmethod(threading.Condition)


class SemaphoreTests(lock_tests.SemaphoreTests):
    semtype = staticmethod(threading.Semaphore)


class BoundedSemaphoreTests(lock_tests.BoundedSemaphoreTests):
    semtype = staticmethod(threading.BoundedSemaphore)


class BarrierTests(lock_tests.BarrierTests):
    barriertype = staticmethod(threading.Barrier)


class MiscTestCase(unittest.TestCase):

    def test__all__(self):
        extra = {'ThreadError'}
        blacklist = {'currentThread', 'activeCount'}
        support.check__all__(self, threading, ('threading', '_thread'),
            extra=extra, blacklist=blacklist)


if __name__ == '__main__':
    unittest.main()
