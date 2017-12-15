import os
import signal
import sys
import threading
import warnings
import _multiprocessing
from . import spawn
from . import util
__all__ = ['ensure_running', 'register', 'unregister']


class SemaphoreTracker(object):

    def __init__(self):
        self._lock = threading.Lock()
        self._fd = None

    def getfd(self):
        self.ensure_running()
        return self._fd

    def ensure_running(self):
        """Make sure that semaphore tracker process is running.

        This can be run from any process.  Usually a child process will use
        the semaphore created by its parent."""
        with self._lock:
            if self._fd is not None:
                return
            fds_to_pass = []
            try:
                fds_to_pass.append(sys.stderr.fileno())
            except Exception:
                pass
            cmd = 'from multiprocessing.semaphore_tracker import main;main(%d)'
            r, w = os.pipe()
            try:
                fds_to_pass.append(r)
                exe = spawn.get_executable()
                args = [exe] + util._args_from_interpreter_flags()
                args += ['-c', cmd % r]
                util.spawnv_passfds(exe, args, fds_to_pass)
            except:
                os.close(w)
                raise
            else:
                self._fd = w
            finally:
                os.close(r)

    def register(self, name):
        """Register name of semaphore with semaphore tracker."""
        self._send('REGISTER', name)

    def unregister(self, name):
        """Unregister name of semaphore with semaphore tracker."""
        self._send('UNREGISTER', name)

    def _send(self, cmd, name):
        self.ensure_running()
        msg = '{0}:{1}\n'.format(cmd, name).encode('ascii')
        if len(name) > 512:
            raise ValueError('name too long')
        nbytes = os.write(self._fd, msg)
        assert nbytes == len(msg)


_semaphore_tracker = SemaphoreTracker()
ensure_running = _semaphore_tracker.ensure_running
register = _semaphore_tracker.register
unregister = _semaphore_tracker.unregister
getfd = _semaphore_tracker.getfd


def main(fd):
    """Run semaphore tracker."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    for f in (sys.stdin, sys.stdout):
        try:
            f.close()
        except Exception:
            pass
    cache = set()
    try:
        with open(fd, 'rb') as f:
            for line in f:
                try:
                    cmd, name = line.strip().split(b':')
                    if cmd == b'REGISTER':
                        cache.add(name)
                    elif cmd == b'UNREGISTER':
                        cache.remove(name)
                    else:
                        raise RuntimeError('unrecognized command %r' % cmd)
                except Exception:
                    try:
                        sys.excepthook(*sys.exc_info())
                    except:
                        pass
    finally:
        if cache:
            try:
                warnings.warn(
                    'semaphore_tracker: There appear to be %d leaked semaphores to clean up at shutdown'
                     % len(cache))
            except Exception:
                pass
        for name in cache:
            try:
                name = name.decode('ascii')
                try:
                    _multiprocessing.sem_unlink(name)
                except Exception as e:
                    warnings.warn('semaphore_tracker: %r: %s' % (name, e))
            finally:
                pass
