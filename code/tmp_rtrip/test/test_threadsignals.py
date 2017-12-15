"""PyUnit testing that threads honor our signal semantics"""
import unittest
import signal
import os
import sys
from test.support import run_unittest, import_module
thread = import_module('_thread')
import time
if sys.platform[:3] == 'win':
    raise unittest.SkipTest("Can't test signal on %s" % sys.platform)
process_pid = os.getpid()
signalled_all = thread.allocate_lock()
USING_PTHREAD_COND = (sys.thread_info.name == 'pthread' and sys.thread_info
    .lock == 'mutex+cond')


def registerSignals(for_usr1, for_usr2, for_alrm):
    usr1 = signal.signal(signal.SIGUSR1, for_usr1)
    usr2 = signal.signal(signal.SIGUSR2, for_usr2)
    alrm = signal.signal(signal.SIGALRM, for_alrm)
    return usr1, usr2, alrm


def handle_signals(sig, frame):
    signal_blackboard[sig]['tripped'] += 1
    signal_blackboard[sig]['tripped_by'] = thread.get_ident()


def send_signals():
    os.kill(process_pid, signal.SIGUSR1)
    os.kill(process_pid, signal.SIGUSR2)
    signalled_all.release()


class ThreadSignals(unittest.TestCase):

    def test_signals(self):
        signalled_all.acquire()
        self.spawnSignallingThread()
        signalled_all.acquire()
        if signal_blackboard[signal.SIGUSR1]['tripped'
            ] == 0 or signal_blackboard[signal.SIGUSR2]['tripped'] == 0:
            signal.alarm(1)
            signal.pause()
            signal.alarm(0)
        self.assertEqual(signal_blackboard[signal.SIGUSR1]['tripped'], 1)
        self.assertEqual(signal_blackboard[signal.SIGUSR1]['tripped_by'],
            thread.get_ident())
        self.assertEqual(signal_blackboard[signal.SIGUSR2]['tripped'], 1)
        self.assertEqual(signal_blackboard[signal.SIGUSR2]['tripped_by'],
            thread.get_ident())
        signalled_all.release()

    def spawnSignallingThread(self):
        thread.start_new_thread(send_signals, ())

    def alarm_interrupt(self, sig, frame):
        raise KeyboardInterrupt

    @unittest.skipIf(USING_PTHREAD_COND,
        'POSIX condition variables cannot be interrupted')
    @unittest.skipIf(sys.platform.startswith('openbsd'),
        'lock cannot be interrupted on OpenBSD')
    def test_lock_acquire_interruption(self):
        oldalrm = signal.signal(signal.SIGALRM, self.alarm_interrupt)
        try:
            lock = thread.allocate_lock()
            lock.acquire()
            signal.alarm(1)
            t1 = time.time()
            self.assertRaises(KeyboardInterrupt, lock.acquire, timeout=5)
            dt = time.time() - t1
            self.assertLess(dt, 3.0)
        finally:
            signal.signal(signal.SIGALRM, oldalrm)

    @unittest.skipIf(USING_PTHREAD_COND,
        'POSIX condition variables cannot be interrupted')
    @unittest.skipIf(sys.platform.startswith('openbsd'),
        'lock cannot be interrupted on OpenBSD')
    def test_rlock_acquire_interruption(self):
        oldalrm = signal.signal(signal.SIGALRM, self.alarm_interrupt)
        try:
            rlock = thread.RLock()

            def other_thread():
                rlock.acquire()
            thread.start_new_thread(other_thread, ())
            while rlock.acquire(blocking=False):
                rlock.release()
                time.sleep(0.01)
            signal.alarm(1)
            t1 = time.time()
            self.assertRaises(KeyboardInterrupt, rlock.acquire, timeout=5)
            dt = time.time() - t1
            self.assertLess(dt, 3.0)
        finally:
            signal.signal(signal.SIGALRM, oldalrm)

    def acquire_retries_on_intr(self, lock):
        self.sig_recvd = False

        def my_handler(signal, frame):
            self.sig_recvd = True
        old_handler = signal.signal(signal.SIGUSR1, my_handler)
        try:

            def other_thread():
                lock.acquire()
                time.sleep(0.5)
                os.kill(process_pid, signal.SIGUSR1)
                time.sleep(0.5)
                lock.release()
            thread.start_new_thread(other_thread, ())
            while lock.acquire(blocking=False):
                lock.release()
                time.sleep(0.01)
            result = lock.acquire()
            self.assertTrue(self.sig_recvd)
            self.assertTrue(result)
        finally:
            signal.signal(signal.SIGUSR1, old_handler)

    def test_lock_acquire_retries_on_intr(self):
        self.acquire_retries_on_intr(thread.allocate_lock())

    def test_rlock_acquire_retries_on_intr(self):
        self.acquire_retries_on_intr(thread.RLock())

    def test_interrupted_timed_acquire(self):
        self.start = None
        self.end = None
        self.sigs_recvd = 0
        done = thread.allocate_lock()
        done.acquire()
        lock = thread.allocate_lock()
        lock.acquire()

        def my_handler(signum, frame):
            self.sigs_recvd += 1
        old_handler = signal.signal(signal.SIGUSR1, my_handler)
        try:

            def timed_acquire():
                self.start = time.time()
                lock.acquire(timeout=0.5)
                self.end = time.time()

            def send_signals():
                for _ in range(40):
                    time.sleep(0.02)
                    os.kill(process_pid, signal.SIGUSR1)
                done.release()
            thread.start_new_thread(send_signals, ())
            timed_acquire()
            done.acquire()
            self.assertLess(self.end - self.start, 2.0)
            self.assertGreater(self.end - self.start, 0.3)
            self.assertGreater(self.sigs_recvd, 0)
        finally:
            signal.signal(signal.SIGUSR1, old_handler)


def test_main():
    global signal_blackboard
    signal_blackboard = {signal.SIGUSR1: {'tripped': 0, 'tripped_by': 0},
        signal.SIGUSR2: {'tripped': 0, 'tripped_by': 0}, signal.SIGALRM: {
        'tripped': 0, 'tripped_by': 0}}
    oldsigs = registerSignals(handle_signals, handle_signals, handle_signals)
    try:
        run_unittest(ThreadSignals)
    finally:
        registerSignals(*oldsigs)


if __name__ == '__main__':
    test_main()
