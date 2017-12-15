import atexit
import faulthandler
import os
import signal
import sys
import unittest
from test import support
try:
    import gc
except ImportError:
    gc = None
from test.libregrtest.refleak import warm_caches


def setup_tests(ns):
    faulthandler.enable(all_threads=True)
    signals = []
    if hasattr(signal, 'SIGALRM'):
        signals.append(signal.SIGALRM)
    if hasattr(signal, 'SIGUSR1'):
        signals.append(signal.SIGUSR1)
    for signum in signals:
        faulthandler.register(signum, chain=True)
    replace_stdout()
    support.record_original_stdout(sys.stdout)
    if ns.testdir:
        sys.path.insert(0, os.path.abspath(ns.testdir))
    for module in sys.modules.values():
        if hasattr(module, '__path__'):
            for index, path in enumerate(module.__path__):
                module.__path__[index] = os.path.abspath(path)
        if hasattr(module, '__file__'):
            module.__file__ = os.path.abspath(module.__file__)
    if sys.platform == 'darwin':
        try:
            import resource
        except ImportError:
            pass
        else:
            soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
            newsoft = min(hard, max(soft, 1024 * 2048))
            resource.setrlimit(resource.RLIMIT_STACK, (newsoft, hard))
    if ns.huntrleaks:
        unittest.BaseTestSuite._cleanup = False
        warm_caches()
    if ns.memlimit is not None:
        support.set_memlimit(ns.memlimit)
    if ns.threshold is not None:
        gc.set_threshold(ns.threshold)
    try:
        import msvcrt
    except ImportError:
        pass
    else:
        msvcrt.SetErrorMode(msvcrt.SEM_FAILCRITICALERRORS | msvcrt.
            SEM_NOALIGNMENTFAULTEXCEPT | msvcrt.SEM_NOGPFAULTERRORBOX |
            msvcrt.SEM_NOOPENFILEERRORBOX)
        try:
            msvcrt.CrtSetReportMode
        except AttributeError:
            pass
        else:
            for m in [msvcrt.CRT_WARN, msvcrt.CRT_ERROR, msvcrt.CRT_ASSERT]:
                if ns.verbose and ns.verbose >= 2:
                    msvcrt.CrtSetReportMode(m, msvcrt.CRTDBG_MODE_FILE)
                    msvcrt.CrtSetReportFile(m, msvcrt.CRTDBG_FILE_STDERR)
                else:
                    msvcrt.CrtSetReportMode(m, 0)
    support.use_resources = ns.use_resources


def replace_stdout():
    """Set stdout encoder error handler to backslashreplace (as stderr error
    handler) to avoid UnicodeEncodeError when printing a traceback"""
    stdout = sys.stdout
    sys.stdout = open(stdout.fileno(), 'w', encoding=stdout.encoding,
        errors='backslashreplace', closefd=False, newline='\n')

    def restore_stdout():
        sys.stdout.close()
        sys.stdout = stdout
    atexit.register(restore_stdout)
