import unittest
from unittest import mock
from test import support
import subprocess
import sys
import platform
import signal
import io
import os
import errno
import tempfile
import time
import selectors
import sysconfig
import select
import shutil
import gc
import textwrap
try:
    import ctypes
except ImportError:
    ctypes = None
try:
    import threading
except ImportError:
    threading = None
if support.PGO:
    raise unittest.SkipTest('test is not helpful for PGO')
mswindows = sys.platform == 'win32'
if mswindows:
    SETBINARY = (
        'import msvcrt; msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY);')
else:
    SETBINARY = ''


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        support.reap_children()

    def tearDown(self):
        for inst in subprocess._active:
            inst.wait()
        subprocess._cleanup()
        self.assertFalse(subprocess._active, 'subprocess._active not empty')

    def assertStderrEqual(self, stderr, expected, msg=None):
        actual = support.strip_python_stderr(stderr)
        expected = expected.strip()
        self.assertEqual(actual, expected, msg)


class PopenTestException(Exception):
    pass


class PopenExecuteChildRaises(subprocess.Popen):
    """Popen subclass for testing cleanup of subprocess.PIPE filehandles when
    _execute_child fails.
    """

    def _execute_child(self, *args, **kwargs):
        raise PopenTestException('Forced Exception for Test')


class ProcessTestCase(BaseTestCase):

    def test_io_buffered_by_default(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.exit(0)'], stdin=subprocess.PIPE, stdout=
            subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            self.assertIsInstance(p.stdin, io.BufferedIOBase)
            self.assertIsInstance(p.stdout, io.BufferedIOBase)
            self.assertIsInstance(p.stderr, io.BufferedIOBase)
        finally:
            p.stdin.close()
            p.stdout.close()
            p.stderr.close()
            p.wait()

    def test_io_unbuffered_works(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.exit(0)'], stdin=subprocess.PIPE, stdout=
            subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        try:
            self.assertIsInstance(p.stdin, io.RawIOBase)
            self.assertIsInstance(p.stdout, io.RawIOBase)
            self.assertIsInstance(p.stderr, io.RawIOBase)
        finally:
            p.stdin.close()
            p.stdout.close()
            p.stderr.close()
            p.wait()

    def test_call_seq(self):
        rc = subprocess.call([sys.executable, '-c', 'import sys; sys.exit(47)']
            )
        self.assertEqual(rc, 47)

    def test_call_timeout(self):
        self.assertRaises(subprocess.TimeoutExpired, subprocess.call, [sys.
            executable, '-c', 'while True: pass'], timeout=0.1)

    def test_check_call_zero(self):
        rc = subprocess.check_call([sys.executable, '-c',
            'import sys; sys.exit(0)'])
        self.assertEqual(rc, 0)

    def test_check_call_nonzero(self):
        with self.assertRaises(subprocess.CalledProcessError) as c:
            subprocess.check_call([sys.executable, '-c',
                'import sys; sys.exit(47)'])
        self.assertEqual(c.exception.returncode, 47)

    def test_check_output(self):
        output = subprocess.check_output([sys.executable, '-c',
            "print('BDFL')"])
        self.assertIn(b'BDFL', output)

    def test_check_output_nonzero(self):
        with self.assertRaises(subprocess.CalledProcessError) as c:
            subprocess.check_output([sys.executable, '-c',
                'import sys; sys.exit(5)'])
        self.assertEqual(c.exception.returncode, 5)

    def test_check_output_stderr(self):
        output = subprocess.check_output([sys.executable, '-c',
            "import sys; sys.stderr.write('BDFL')"], stderr=subprocess.STDOUT)
        self.assertIn(b'BDFL', output)

    def test_check_output_stdin_arg(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        tf.write(b'pear')
        tf.seek(0)
        output = subprocess.check_output([sys.executable, '-c',
            'import sys; sys.stdout.write(sys.stdin.read().upper())'], stdin=tf
            )
        self.assertIn(b'PEAR', output)

    def test_check_output_input_arg(self):
        output = subprocess.check_output([sys.executable, '-c',
            'import sys; sys.stdout.write(sys.stdin.read().upper())'],
            input=b'pear')
        self.assertIn(b'PEAR', output)

    def test_check_output_stdout_arg(self):
        with self.assertRaises(ValueError) as c:
            output = subprocess.check_output([sys.executable, '-c',
                "print('will not be run')"], stdout=sys.stdout)
            self.fail('Expected ValueError when stdout arg supplied.')
        self.assertIn('stdout', c.exception.args[0])

    def test_check_output_stdin_with_input_arg(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        tf.write(b'pear')
        tf.seek(0)
        with self.assertRaises(ValueError) as c:
            output = subprocess.check_output([sys.executable, '-c',
                "print('will not be run')"], stdin=tf, input=b'hare')
            self.fail('Expected ValueError when stdin and input args supplied.'
                )
        self.assertIn('stdin', c.exception.args[0])
        self.assertIn('input', c.exception.args[0])

    def test_check_output_timeout(self):
        with self.assertRaises(subprocess.TimeoutExpired) as c:
            output = subprocess.check_output([sys.executable, '-c',
                """import sys, time
sys.stdout.write('BDFL')
sys.stdout.flush()
time.sleep(3600)"""
                ], timeout=3)
            self.fail('Expected TimeoutExpired.')
        self.assertEqual(c.exception.output, b'BDFL')

    def test_call_kwargs(self):
        newenv = os.environ.copy()
        newenv['FRUIT'] = 'banana'
        rc = subprocess.call([sys.executable, '-c',
            'import sys, os;sys.exit(os.getenv("FRUIT")=="banana")'], env=
            newenv)
        self.assertEqual(rc, 1)

    def test_invalid_args(self):
        with support.captured_stderr() as s:
            self.assertRaises(TypeError, subprocess.Popen, invalid_arg_name=1)
            argcount = subprocess.Popen.__init__.__code__.co_argcount
            too_many_args = [0] * (argcount + 1)
            self.assertRaises(TypeError, subprocess.Popen, *too_many_args)
        self.assertEqual(s.getvalue(), '')

    def test_stdin_none(self):
        p = subprocess.Popen([sys.executable, '-c', 'print("banana")'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        p.wait()
        self.assertEqual(p.stdin, None)

    def test_stdout_none(self):
        code = (
            'import sys; from subprocess import Popen, PIPE;p = Popen([sys.executable, "-c", "print(\'test_stdout_none\')"],          stdin=PIPE, stderr=PIPE);p.wait(); assert p.stdout is None;'
            )
        p = subprocess.Popen([sys.executable, '-c', code], stdout=
            subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        out, err = p.communicate()
        self.assertEqual(p.returncode, 0, err)
        self.assertEqual(out.rstrip(), b'test_stdout_none')

    def test_stderr_none(self):
        p = subprocess.Popen([sys.executable, '-c', 'print("banana")'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stdin.close)
        p.wait()
        self.assertEqual(p.stderr, None)

    def _assert_python(self, pre_args, **kwargs):
        args = pre_args + ['import sys; sys.exit(47)']
        p = subprocess.Popen(args, **kwargs)
        p.wait()
        self.assertEqual(47, p.returncode)

    def test_executable(self):
        doesnotexist = os.path.join(os.path.dirname(sys.executable),
            'doesnotexist')
        self._assert_python([doesnotexist, '-c'], executable=sys.executable)

    def test_executable_takes_precedence(self):
        pre_args = [sys.executable, '-c']
        self._assert_python(pre_args)
        self.assertRaises((FileNotFoundError, PermissionError), self.
            _assert_python, pre_args, executable='doesnotexist')

    @unittest.skipIf(mswindows, 'executable argument replaces shell')
    def test_executable_replaces_shell(self):
        self._assert_python([], executable=sys.executable, shell=True)

    def _normalize_cwd(self, cwd):
        with support.change_cwd(cwd):
            return os.getcwd()

    def _split_python_path(self):
        python_path = os.path.realpath(sys.executable)
        return os.path.split(python_path)

    def _assert_cwd(self, expected_cwd, python_arg, **kwargs):
        p = subprocess.Popen([python_arg, '-c',
            'import os, sys; sys.stdout.write(os.getcwd()); sys.exit(47)'],
            stdout=subprocess.PIPE, **kwargs)
        self.addCleanup(p.stdout.close)
        p.wait()
        self.assertEqual(47, p.returncode)
        normcase = os.path.normcase
        self.assertEqual(normcase(expected_cwd), normcase(p.stdout.read().
            decode('utf-8')))

    def test_cwd(self):
        temp_dir = tempfile.gettempdir()
        temp_dir = self._normalize_cwd(temp_dir)
        self._assert_cwd(temp_dir, sys.executable, cwd=temp_dir)

    def test_cwd_with_pathlike(self):
        temp_dir = tempfile.gettempdir()
        temp_dir = self._normalize_cwd(temp_dir)


        class _PathLikeObj:

            def __fspath__(self):
                return temp_dir
        self._assert_cwd(temp_dir, sys.executable, cwd=_PathLikeObj())

    @unittest.skipIf(mswindows, 'pending resolution of issue #15533')
    def test_cwd_with_relative_arg(self):
        python_dir, python_base = self._split_python_path()
        rel_python = os.path.join(os.curdir, python_base)
        with support.temp_cwd() as wrong_dir:
            self.assertRaises(FileNotFoundError, subprocess.Popen, [rel_python]
                )
            self.assertRaises(FileNotFoundError, subprocess.Popen, [
                rel_python], cwd=wrong_dir)
            python_dir = self._normalize_cwd(python_dir)
            self._assert_cwd(python_dir, rel_python, cwd=python_dir)

    @unittest.skipIf(mswindows, 'pending resolution of issue #15533')
    def test_cwd_with_relative_executable(self):
        python_dir, python_base = self._split_python_path()
        rel_python = os.path.join(os.curdir, python_base)
        doesntexist = 'somethingyoudonthave'
        with support.temp_cwd() as wrong_dir:
            self.assertRaises(FileNotFoundError, subprocess.Popen, [
                doesntexist], executable=rel_python)
            self.assertRaises(FileNotFoundError, subprocess.Popen, [
                doesntexist], executable=rel_python, cwd=wrong_dir)
            python_dir = self._normalize_cwd(python_dir)
            self._assert_cwd(python_dir, doesntexist, executable=rel_python,
                cwd=python_dir)

    def test_cwd_with_absolute_arg(self):
        python_dir, python_base = self._split_python_path()
        abs_python = os.path.join(python_dir, python_base)
        rel_python = os.path.join(os.curdir, python_base)
        with support.temp_dir() as wrong_dir:
            self.assertRaises(FileNotFoundError, subprocess.Popen, [
                rel_python], cwd=wrong_dir)
            wrong_dir = self._normalize_cwd(wrong_dir)
            self._assert_cwd(wrong_dir, abs_python, cwd=wrong_dir)

    @unittest.skipIf(sys.base_prefix != sys.prefix,
        'Test is not venv-compatible')
    def test_executable_with_cwd(self):
        python_dir, python_base = self._split_python_path()
        python_dir = self._normalize_cwd(python_dir)
        self._assert_cwd(python_dir, 'somethingyoudonthave', executable=sys
            .executable, cwd=python_dir)

    @unittest.skipIf(sys.base_prefix != sys.prefix,
        'Test is not venv-compatible')
    @unittest.skipIf(sysconfig.is_python_build(),
        'need an installed Python. See #7774')
    def test_executable_without_cwd(self):
        self._assert_cwd(os.getcwd(), 'somethingyoudonthave', executable=
            sys.executable)

    def test_stdin_pipe(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.exit(sys.stdin.read() == "pear")'], stdin=
            subprocess.PIPE)
        p.stdin.write(b'pear')
        p.stdin.close()
        p.wait()
        self.assertEqual(p.returncode, 1)

    def test_stdin_filedes(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        d = tf.fileno()
        os.write(d, b'pear')
        os.lseek(d, 0, 0)
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.exit(sys.stdin.read() == "pear")'], stdin=d)
        p.wait()
        self.assertEqual(p.returncode, 1)

    def test_stdin_fileobj(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        tf.write(b'pear')
        tf.seek(0)
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.exit(sys.stdin.read() == "pear")'], stdin=tf)
        p.wait()
        self.assertEqual(p.returncode, 1)

    def test_stdout_pipe(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.stdout.write("orange")'], stdout=subprocess.PIPE)
        with p:
            self.assertEqual(p.stdout.read(), b'orange')

    def test_stdout_filedes(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        d = tf.fileno()
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.stdout.write("orange")'], stdout=d)
        p.wait()
        os.lseek(d, 0, 0)
        self.assertEqual(os.read(d, 1024), b'orange')

    def test_stdout_fileobj(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.stdout.write("orange")'], stdout=tf)
        p.wait()
        tf.seek(0)
        self.assertEqual(tf.read(), b'orange')

    def test_stderr_pipe(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.stderr.write("strawberry")'], stderr=
            subprocess.PIPE)
        with p:
            self.assertStderrEqual(p.stderr.read(), b'strawberry')

    def test_stderr_filedes(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        d = tf.fileno()
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.stderr.write("strawberry")'], stderr=d)
        p.wait()
        os.lseek(d, 0, 0)
        self.assertStderrEqual(os.read(d, 1024), b'strawberry')

    def test_stderr_fileobj(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.stderr.write("strawberry")'], stderr=tf)
        p.wait()
        tf.seek(0)
        self.assertStderrEqual(tf.read(), b'strawberry')

    def test_stderr_redirect_with_no_stdout_redirect(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys, subprocess;rc = subprocess.call([sys.executable, "-c",    "import sys;"    "sys.stderr.write(\'42\')"],    stderr=subprocess.STDOUT);sys.exit(rc)'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertStderrEqual(stdout, b'42')
        self.assertStderrEqual(stderr, b'')
        self.assertEqual(p.returncode, 0)

    def test_stdout_stderr_pipe(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys;sys.stdout.write("apple");sys.stdout.flush();sys.stderr.write("orange")'
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with p:
            self.assertStderrEqual(p.stdout.read(), b'appleorange')

    def test_stdout_stderr_file(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        p = subprocess.Popen([sys.executable, '-c',
            'import sys;sys.stdout.write("apple");sys.stdout.flush();sys.stderr.write("orange")'
            ], stdout=tf, stderr=tf)
        p.wait()
        tf.seek(0)
        self.assertStderrEqual(tf.read(), b'appleorange')

    def test_stdout_filedes_of_stdout(self):
        code = (
            'import sys, subprocess; rc = subprocess.call([sys.executable, "-c",     "import os, sys; sys.exit(os.write(sys.stdout.fileno(), b\'test with stdout=1\'))"], stdout=1); assert rc == 18'
            )
        p = subprocess.Popen([sys.executable, '-c', code], stdout=
            subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        out, err = p.communicate()
        self.assertEqual(p.returncode, 0, err)
        self.assertEqual(out.rstrip(), b'test with stdout=1')

    def test_stdout_devnull(self):
        p = subprocess.Popen([sys.executable, '-c',
            'for i in range(10240):print("x" * 1024)'], stdout=subprocess.
            DEVNULL)
        p.wait()
        self.assertEqual(p.stdout, None)

    def test_stderr_devnull(self):
        p = subprocess.Popen([sys.executable, '-c',
            """import sys
for i in range(10240):sys.stderr.write("x" * 1024)"""
            ], stderr=subprocess.DEVNULL)
        p.wait()
        self.assertEqual(p.stderr, None)

    def test_stdin_devnull(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys;sys.stdin.read(1)'], stdin=subprocess.DEVNULL)
        p.wait()
        self.assertEqual(p.stdin, None)

    def test_env(self):
        newenv = os.environ.copy()
        newenv['FRUIT'] = 'orange'
        with subprocess.Popen([sys.executable, '-c',
            'import sys,os;sys.stdout.write(os.getenv("FRUIT"))'], stdout=
            subprocess.PIPE, env=newenv) as p:
            stdout, stderr = p.communicate()
            self.assertEqual(stdout, b'orange')

    @unittest.skipIf(sys.platform == 'win32',
        'cannot test an empty env on Windows')
    @unittest.skipIf(sysconfig.get_config_var('Py_ENABLE_SHARED') is not
        None, 'the python library cannot be loaded with an empty environment')
    def test_empty_env(self):
        with subprocess.Popen([sys.executable, '-c',
            'import os; print(list(os.environ.keys()))'], stdout=subprocess
            .PIPE, env={}) as p:
            stdout, stderr = p.communicate()
            self.assertIn(stdout.strip(), (b'[]',
                b"['__CF_USER_TEXT_ENCODING']"))

    def test_invalid_cmd(self):
        cmd = sys.executable + '\x00'
        with self.assertRaises(ValueError):
            subprocess.Popen([cmd, '-c', 'pass'])
        with self.assertRaises(ValueError):
            subprocess.Popen([sys.executable, '-c', 'pass#\x00'])

    def test_invalid_env(self):
        newenv = os.environ.copy()
        newenv['FRUIT\x00VEGETABLE'] = 'cabbage'
        with self.assertRaises(ValueError):
            subprocess.Popen([sys.executable, '-c', 'pass'], env=newenv)
        newenv = os.environ.copy()
        newenv['FRUIT'] = 'orange\x00VEGETABLE=cabbage'
        with self.assertRaises(ValueError):
            subprocess.Popen([sys.executable, '-c', 'pass'], env=newenv)
        newenv = os.environ.copy()
        newenv['FRUIT=ORANGE'] = 'lemon'
        with self.assertRaises(ValueError):
            subprocess.Popen([sys.executable, '-c', 'pass'], env=newenv)
        newenv = os.environ.copy()
        newenv['FRUIT'] = 'orange=lemon'
        with subprocess.Popen([sys.executable, '-c',
            'import sys, os;sys.stdout.write(os.getenv("FRUIT"))'], stdout=
            subprocess.PIPE, env=newenv) as p:
            stdout, stderr = p.communicate()
            self.assertEqual(stdout, b'orange=lemon')

    def test_communicate_stdin(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys;sys.exit(sys.stdin.read() == "pear")'], stdin=
            subprocess.PIPE)
        p.communicate(b'pear')
        self.assertEqual(p.returncode, 1)

    def test_communicate_stdout(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.stdout.write("pineapple")'], stdout=subprocess
            .PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(stdout, b'pineapple')
        self.assertEqual(stderr, None)

    def test_communicate_stderr(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.stderr.write("pineapple")'], stderr=subprocess
            .PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(stdout, None)
        self.assertStderrEqual(stderr, b'pineapple')

    def test_communicate(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys,os;sys.stderr.write("pineapple");sys.stdout.write(sys.stdin.read())'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=
            subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        self.addCleanup(p.stdin.close)
        stdout, stderr = p.communicate(b'banana')
        self.assertEqual(stdout, b'banana')
        self.assertStderrEqual(stderr, b'pineapple')

    def test_communicate_timeout(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys,os,time;sys.stderr.write("pineapple\\n");time.sleep(1);sys.stderr.write("pear\\n");sys.stdout.write(sys.stdin.read())'
            ], universal_newlines=True, stdin=subprocess.PIPE, stdout=
            subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertRaises(subprocess.TimeoutExpired, p.communicate,
            'banana', timeout=0.3)
        stdout, stderr = p.communicate()
        self.assertEqual(stdout, 'banana')
        self.assertStderrEqual(stderr.encode(), b'pineapple\npear\n')

    def test_communicate_timeout_large_output(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys,os,time;sys.stdout.write("a" * (64 * 1024));time.sleep(0.2);sys.stdout.write("a" * (64 * 1024));time.sleep(0.2);sys.stdout.write("a" * (64 * 1024));time.sleep(0.2);sys.stdout.write("a" * (64 * 1024));'
            ], stdout=subprocess.PIPE)
        self.assertRaises(subprocess.TimeoutExpired, p.communicate, timeout=0.4
            )
        stdout, _ = p.communicate()
        self.assertEqual(len(stdout), 4 * 64 * 1024)

    def test_communicate_pipe_fd_leak(self):
        for stdin_pipe in (False, True):
            for stdout_pipe in (False, True):
                for stderr_pipe in (False, True):
                    options = {}
                    if stdin_pipe:
                        options['stdin'] = subprocess.PIPE
                    if stdout_pipe:
                        options['stdout'] = subprocess.PIPE
                    if stderr_pipe:
                        options['stderr'] = subprocess.PIPE
                    if not options:
                        continue
                    p = subprocess.Popen((sys.executable, '-c', 'pass'), **
                        options)
                    p.communicate()
                    if p.stdin is not None:
                        self.assertTrue(p.stdin.closed)
                    if p.stdout is not None:
                        self.assertTrue(p.stdout.closed)
                    if p.stderr is not None:
                        self.assertTrue(p.stderr.closed)

    def test_communicate_returns(self):
        p = subprocess.Popen([sys.executable, '-c', 'import sys; sys.exit(47)']
            )
        stdout, stderr = p.communicate()
        self.assertEqual(stdout, None)
        self.assertEqual(stderr, None)

    def test_communicate_pipe_buf(self):
        x, y = os.pipe()
        os.close(x)
        os.close(y)
        p = subprocess.Popen([sys.executable, '-c', 
            'import sys,os;sys.stdout.write(sys.stdin.read(47));sys.stderr.write("x" * %d);sys.stdout.write(sys.stdin.read())'
             % support.PIPE_MAX_SIZE], stdin=subprocess.PIPE, stdout=
            subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        self.addCleanup(p.stdin.close)
        string_to_write = b'a' * support.PIPE_MAX_SIZE
        stdout, stderr = p.communicate(string_to_write)
        self.assertEqual(stdout, string_to_write)

    def test_writes_before_communicate(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys,os;sys.stdout.write(sys.stdin.read())'], stdin=
            subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        self.addCleanup(p.stdin.close)
        p.stdin.write(b'banana')
        stdout, stderr = p.communicate(b'split')
        self.assertEqual(stdout, b'bananasplit')
        self.assertStderrEqual(stderr, b'')

    def test_universal_newlines(self):
        p = subprocess.Popen([sys.executable, '-c', 'import sys,os;' +
            SETBINARY +
            'buf = sys.stdout.buffer;buf.write(sys.stdin.readline().encode());buf.flush();buf.write(b"line2\\n");buf.flush();buf.write(sys.stdin.read().encode());buf.flush();buf.write(b"line4\\n");buf.flush();buf.write(b"line5\\r\\n");buf.flush();buf.write(b"line6\\r");buf.flush();buf.write(b"\\nline7");buf.flush();buf.write(b"\\nline8");'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            universal_newlines=1)
        with p:
            p.stdin.write('line1\n')
            p.stdin.flush()
            self.assertEqual(p.stdout.readline(), 'line1\n')
            p.stdin.write('line3\n')
            p.stdin.close()
            self.addCleanup(p.stdout.close)
            self.assertEqual(p.stdout.readline(), 'line2\n')
            self.assertEqual(p.stdout.read(6), 'line3\n')
            self.assertEqual(p.stdout.read(),
                'line4\nline5\nline6\nline7\nline8')

    def test_universal_newlines_communicate(self):
        p = subprocess.Popen([sys.executable, '-c', 'import sys,os;' +
            SETBINARY +
            'buf = sys.stdout.buffer;buf.write(b"line2\\n");buf.flush();buf.write(b"line4\\n");buf.flush();buf.write(b"line5\\r\\n");buf.flush();buf.write(b"line6\\r");buf.flush();buf.write(b"\\nline7");buf.flush();buf.write(b"\\nline8");'
            ], stderr=subprocess.PIPE, stdout=subprocess.PIPE,
            universal_newlines=1)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        stdout, stderr = p.communicate()
        self.assertEqual(stdout, 'line2\nline4\nline5\nline6\nline7\nline8')

    def test_universal_newlines_communicate_stdin(self):
        p = subprocess.Popen([sys.executable, '-c', 'import sys,os;' +
            SETBINARY + textwrap.dedent(
            """
                               s = sys.stdin.readline()
                               assert s == "line1\\n", repr(s)
                               s = sys.stdin.read()
                               assert s == "line3\\n", repr(s)
                              """
            )], stdin=subprocess.PIPE, universal_newlines=1)
        stdout, stderr = p.communicate('line1\nline3\n')
        self.assertEqual(p.returncode, 0)

    def test_universal_newlines_communicate_input_none(self):
        p = subprocess.Popen([sys.executable, '-c', 'pass'], stdin=
            subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        p.communicate()
        self.assertEqual(p.returncode, 0)

    def test_universal_newlines_communicate_stdin_stdout_stderr(self):
        p = subprocess.Popen([sys.executable, '-c', 'import sys,os;' +
            SETBINARY + textwrap.dedent(
            """
                               s = sys.stdin.buffer.readline()
                               sys.stdout.buffer.write(s)
                               sys.stdout.buffer.write(b"line2\\r")
                               sys.stderr.buffer.write(b"eline2\\n")
                               s = sys.stdin.buffer.read()
                               sys.stdout.buffer.write(s)
                               sys.stdout.buffer.write(b"line4\\n")
                               sys.stdout.buffer.write(b"line5\\r\\n")
                               sys.stderr.buffer.write(b"eline6\\r")
                               sys.stderr.buffer.write(b"eline7\\r\\nz")
                              """
            )], stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=
            subprocess.PIPE, universal_newlines=True)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        stdout, stderr = p.communicate('line1\nline3\n')
        self.assertEqual(p.returncode, 0)
        self.assertEqual('line1\nline2\nline3\nline4\nline5\n', stdout)
        self.assertTrue(stderr.startswith('eline2\neline6\neline7\n'))

    def test_universal_newlines_communicate_encodings(self):
        for encoding in ['utf-16', 'utf-32-be']:
            code = (
                "import sys; sys.stdout.buffer.write('1\\r\\n2\\r3\\n4'.encode('%s'))"
                 % encoding)
            args = [sys.executable, '-c', code]
            popen = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=
                subprocess.PIPE, encoding=encoding)
            stdout, stderr = popen.communicate(input='')
            self.assertEqual(stdout, '1\n2\n3\n4')

    def test_communicate_errors(self):
        for errors, expected in [('ignore', ''), ('replace', '��'), (
            'surrogateescape', '\udc80\udc80'), ('backslashreplace',
            '\\x80\\x80')]:
            code = "import sys; sys.stdout.buffer.write(b'[\\x80\\x80]')"
            args = [sys.executable, '-c', code]
            popen = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=
                subprocess.PIPE, encoding='utf-8', errors=errors)
            stdout, stderr = popen.communicate(input='')
            self.assertEqual(stdout, '[{}]'.format(expected))

    def test_no_leaking(self):
        if not mswindows:
            max_handles = 1026
        else:
            max_handles = 2050
        handles = []
        tmpdir = tempfile.mkdtemp()
        try:
            for i in range(max_handles):
                try:
                    tmpfile = os.path.join(tmpdir, support.TESTFN)
                    handles.append(os.open(tmpfile, os.O_WRONLY | os.O_CREAT))
                except OSError as e:
                    if e.errno != errno.EMFILE:
                        raise
                    break
            else:
                self.skipTest(
                    'failed to reach the file descriptor limit (tried %d)' %
                    max_handles)
            for i in range(10):
                os.close(handles.pop())
            for i in range(15):
                p = subprocess.Popen([sys.executable, '-c',
                    'import sys;sys.stdout.write(sys.stdin.read())'], stdin
                    =subprocess.PIPE, stdout=subprocess.PIPE, stderr=
                    subprocess.PIPE)
                data = p.communicate(b'lime')[0]
                self.assertEqual(data, b'lime')
        finally:
            for h in handles:
                os.close(h)
            shutil.rmtree(tmpdir)

    def test_list2cmdline(self):
        self.assertEqual(subprocess.list2cmdline(['a b c', 'd', 'e']),
            '"a b c" d e')
        self.assertEqual(subprocess.list2cmdline(['ab"c', '\\', 'd']),
            'ab\\"c \\ d')
        self.assertEqual(subprocess.list2cmdline(['ab"c', ' \\', 'd']),
            'ab\\"c " \\\\" d')
        self.assertEqual(subprocess.list2cmdline(['a\\\\\\b', 'de fg', 'h']
            ), 'a\\\\\\b "de fg" h')
        self.assertEqual(subprocess.list2cmdline(['a\\"b', 'c', 'd']),
            'a\\\\\\"b c d')
        self.assertEqual(subprocess.list2cmdline(['a\\\\b c', 'd', 'e']),
            '"a\\\\b c" d e')
        self.assertEqual(subprocess.list2cmdline(['a\\\\b\\ c', 'd', 'e']),
            '"a\\\\b\\ c" d e')
        self.assertEqual(subprocess.list2cmdline(['ab', '']), 'ab ""')

    def test_poll(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import os; os.read(0, 1)'], stdin=subprocess.PIPE)
        self.addCleanup(p.stdin.close)
        self.assertIsNone(p.poll())
        os.write(p.stdin.fileno(), b'A')
        p.wait()
        self.assertEqual(p.poll(), 0)

    def test_wait(self):
        p = subprocess.Popen([sys.executable, '-c', 'pass'])
        self.assertEqual(p.wait(), 0)
        self.assertEqual(p.wait(), 0)

    def test_wait_timeout(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import time; time.sleep(0.3)'])
        with self.assertRaises(subprocess.TimeoutExpired) as c:
            p.wait(timeout=0.0001)
        self.assertIn('0.0001', str(c.exception))
        self.assertEqual(p.wait(timeout=3), 0)

    def test_wait_endtime(self):
        """Confirm that the deprecated endtime parameter warns."""
        p = subprocess.Popen([sys.executable, '-c', 'pass'])
        try:
            with self.assertWarns(DeprecationWarning) as warn_cm:
                p.wait(endtime=time.time() + 0.01)
        except subprocess.TimeoutExpired:
            pass
        finally:
            p.kill()
        self.assertIn('test_subprocess.py', warn_cm.filename)
        self.assertIn('endtime', str(warn_cm.warning))

    def test_invalid_bufsize(self):
        with self.assertRaises(TypeError):
            subprocess.Popen([sys.executable, '-c', 'pass'], 'orange')

    def test_bufsize_is_none(self):
        p = subprocess.Popen([sys.executable, '-c', 'pass'], None)
        self.assertEqual(p.wait(), 0)
        p = subprocess.Popen([sys.executable, '-c', 'pass'], bufsize=None)
        self.assertEqual(p.wait(), 0)

    def _test_bufsize_equal_one(self, line, expected, universal_newlines):
        with subprocess.Popen([sys.executable, '-c',
            'import sys;sys.stdout.write(sys.stdin.readline());sys.stdout.flush()'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=
            subprocess.DEVNULL, bufsize=1, universal_newlines=
            universal_newlines) as p:
            p.stdin.write(line)
            os.close(p.stdin.fileno())
            read_line = p.stdout.readline()
            try:
                p.stdin.close()
            except OSError:
                pass
            p.stdin = None
        self.assertEqual(p.returncode, 0)
        self.assertEqual(read_line, expected)

    def test_bufsize_equal_one_text_mode(self):
        line = 'line\n'
        self._test_bufsize_equal_one(line, line, universal_newlines=True)

    def test_bufsize_equal_one_binary_mode(self):
        line = b'line' + os.linesep.encode()
        self._test_bufsize_equal_one(line, b'', universal_newlines=False)

    def test_leaking_fds_on_error(self):
        for i in range(1024):
            with self.assertRaises(OSError) as c:
                subprocess.Popen(['nonexisting_i_hope'], stdout=subprocess.
                    PIPE, stderr=subprocess.PIPE)
            if c.exception.errno not in (errno.ENOENT, errno.EACCES):
                raise c.exception

    @unittest.skipIf(threading is None, 'threading required')
    def test_double_close_on_error(self):
        fds = []

        def open_fds():
            for i in range(20):
                fds.extend(os.pipe())
                time.sleep(0.001)
        t = threading.Thread(target=open_fds)
        t.start()
        try:
            with self.assertRaises(EnvironmentError):
                subprocess.Popen(['nonexisting_i_hope'], stdin=subprocess.
                    PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        finally:
            t.join()
            exc = None
            for fd in fds:
                try:
                    os.close(fd)
                except OSError as e:
                    exc = e
            if exc is not None:
                raise exc

    @unittest.skipIf(threading is None, 'threading required')
    def test_threadsafe_wait(self):
        """Issue21291: Popen.wait() needs to be threadsafe for returncode."""
        proc = subprocess.Popen([sys.executable, '-c',
            'import time; time.sleep(12)'])
        self.assertEqual(proc.returncode, None)
        results = []

        def kill_proc_timer_thread():
            results.append(('thread-start-poll-result', proc.poll()))
            proc.kill()
            proc.wait()
            results.append(('thread-after-kill-and-wait', proc.returncode))
            proc.wait()
            results.append(('thread-after-second-wait', proc.returncode))
        t = threading.Timer(0.2, kill_proc_timer_thread)
        t.start()
        if mswindows:
            expected_errorcode = 1
        else:
            expected_errorcode = -9
        proc.wait(timeout=20)
        self.assertEqual(proc.returncode, expected_errorcode, msg=
            'unexpected result in wait from main thread')
        proc.wait()
        self.assertEqual(proc.returncode, expected_errorcode, msg=
            'unexpected result in second main wait.')
        t.join()
        self.assertEqual([('thread-start-poll-result', None), (
            'thread-after-kill-and-wait', expected_errorcode), (
            'thread-after-second-wait', expected_errorcode)], results)

    def test_issue8780(self):
        code = ';'.join(('import subprocess, sys',
            'retcode = subprocess.call([sys.executable, \'-c\', \'print("Hello World!")\'])'
            , 'assert retcode == 0'))
        output = subprocess.check_output([sys.executable, '-c', code])
        self.assertTrue(output.startswith(b'Hello World!'), ascii(output))

    def test_handles_closed_on_exception(self):
        ifhandle, ifname = tempfile.mkstemp()
        ofhandle, ofname = tempfile.mkstemp()
        efhandle, efname = tempfile.mkstemp()
        try:
            subprocess.Popen(['*'], stdin=ifhandle, stdout=ofhandle, stderr
                =efhandle)
        except OSError:
            os.close(ifhandle)
            os.remove(ifname)
            os.close(ofhandle)
            os.remove(ofname)
            os.close(efhandle)
            os.remove(efname)
        self.assertFalse(os.path.exists(ifname))
        self.assertFalse(os.path.exists(ofname))
        self.assertFalse(os.path.exists(efname))

    def test_communicate_epipe(self):
        p = subprocess.Popen([sys.executable, '-c', 'pass'], stdin=
            subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        self.addCleanup(p.stdin.close)
        p.communicate(b'x' * 2 ** 20)

    def test_communicate_epipe_only_stdin(self):
        p = subprocess.Popen([sys.executable, '-c', 'pass'], stdin=
            subprocess.PIPE)
        self.addCleanup(p.stdin.close)
        p.wait()
        p.communicate(b'x' * 2 ** 20)

    @unittest.skipUnless(hasattr(signal, 'SIGUSR1'), 'Requires signal.SIGUSR1')
    @unittest.skipUnless(hasattr(os, 'kill'), 'Requires os.kill')
    @unittest.skipUnless(hasattr(os, 'getppid'), 'Requires os.getppid')
    def test_communicate_eintr(self):

        def handler(signum, frame):
            pass
        old_handler = signal.signal(signal.SIGUSR1, handler)
        self.addCleanup(signal.signal, signal.SIGUSR1, old_handler)
        args = [sys.executable, '-c',
            'import os, signal;os.kill(os.getppid(), signal.SIGUSR1)']
        for stream in ('stdout', 'stderr'):
            kw = {stream: subprocess.PIPE}
            with subprocess.Popen(args, **kw) as process:
                process.communicate()

    @unittest.skipUnless(os.path.isdir('/proc/%d/fd' % os.getpid()),
        'Linux specific')
    def test_failed_child_execute_fd_leak(self):
        """Test for the fork() failure fd leak reported in issue16327."""
        fd_directory = '/proc/%d/fd' % os.getpid()
        fds_before_popen = os.listdir(fd_directory)
        with self.assertRaises(PopenTestException):
            PopenExecuteChildRaises([sys.executable, '-c', 'pass'], stdin=
                subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
        fds_after_exception = os.listdir(fd_directory)
        self.assertEqual(fds_before_popen, fds_after_exception)


class RunFuncTestCase(BaseTestCase):

    def run_python(self, code, **kwargs):
        """Run Python code in a subprocess using subprocess.run"""
        argv = [sys.executable, '-c', code]
        return subprocess.run(argv, **kwargs)

    def test_returncode(self):
        cp = self.run_python('import sys; sys.exit(47)')
        self.assertEqual(cp.returncode, 47)
        with self.assertRaises(subprocess.CalledProcessError):
            cp.check_returncode()

    def test_check(self):
        with self.assertRaises(subprocess.CalledProcessError) as c:
            self.run_python('import sys; sys.exit(47)', check=True)
        self.assertEqual(c.exception.returncode, 47)

    def test_check_zero(self):
        cp = self.run_python('import sys; sys.exit(0)', check=True)
        self.assertEqual(cp.returncode, 0)

    def test_timeout(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_python('while True: pass', timeout=0.0001)

    def test_capture_stdout(self):
        cp = self.run_python("print('BDFL')", stdout=subprocess.PIPE)
        self.assertIn(b'BDFL', cp.stdout)

    def test_capture_stderr(self):
        cp = self.run_python("import sys; sys.stderr.write('BDFL')", stderr
            =subprocess.PIPE)
        self.assertIn(b'BDFL', cp.stderr)

    def test_check_output_stdin_arg(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        tf.write(b'pear')
        tf.seek(0)
        cp = self.run_python(
            'import sys; sys.stdout.write(sys.stdin.read().upper())', stdin
            =tf, stdout=subprocess.PIPE)
        self.assertIn(b'PEAR', cp.stdout)

    def test_check_output_input_arg(self):
        cp = self.run_python(
            'import sys; sys.stdout.write(sys.stdin.read().upper())', input
            =b'pear', stdout=subprocess.PIPE)
        self.assertIn(b'PEAR', cp.stdout)

    def test_check_output_stdin_with_input_arg(self):
        tf = tempfile.TemporaryFile()
        self.addCleanup(tf.close)
        tf.write(b'pear')
        tf.seek(0)
        with self.assertRaises(ValueError, msg=
            'Expected ValueError when stdin and input args supplied.') as c:
            output = self.run_python("print('will not be run')", stdin=tf,
                input=b'hare')
        self.assertIn('stdin', c.exception.args[0])
        self.assertIn('input', c.exception.args[0])

    def test_check_output_timeout(self):
        with self.assertRaises(subprocess.TimeoutExpired) as c:
            cp = self.run_python(
                """import sys, time
sys.stdout.write('BDFL')
sys.stdout.flush()
time.sleep(3600)"""
                , timeout=3, stdout=subprocess.PIPE)
        self.assertEqual(c.exception.output, b'BDFL')
        self.assertEqual(c.exception.stdout, b'BDFL')

    def test_run_kwargs(self):
        newenv = os.environ.copy()
        newenv['FRUIT'] = 'banana'
        cp = self.run_python(
            'import sys, os;sys.exit(33 if os.getenv("FRUIT")=="banana" else 31)'
            , env=newenv)
        self.assertEqual(cp.returncode, 33)


@unittest.skipIf(mswindows, 'POSIX specific tests')
class POSIXProcessTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self._nonexistent_dir = '/_this/pa.th/does/not/exist'

    def _get_chdir_exception(self):
        try:
            os.chdir(self._nonexistent_dir)
        except OSError as e:
            desired_exception = e
            desired_exception.strerror += ': ' + repr(self._nonexistent_dir)
        else:
            self.fail('chdir to nonexistent directory %s succeeded.' % self
                ._nonexistent_dir)
        return desired_exception

    def test_exception_cwd(self):
        """Test error in the child raised in the parent for a bad cwd."""
        desired_exception = self._get_chdir_exception()
        try:
            p = subprocess.Popen([sys.executable, '-c', ''], cwd=self.
                _nonexistent_dir)
        except OSError as e:
            self.assertEqual(desired_exception.errno, e.errno)
            self.assertEqual(desired_exception.strerror, e.strerror)
        else:
            self.fail('Expected OSError: %s' % desired_exception)

    def test_exception_bad_executable(self):
        """Test error in the child raised in the parent for a bad executable."""
        desired_exception = self._get_chdir_exception()
        try:
            p = subprocess.Popen([sys.executable, '-c', ''], executable=
                self._nonexistent_dir)
        except OSError as e:
            self.assertEqual(desired_exception.errno, e.errno)
            self.assertEqual(desired_exception.strerror, e.strerror)
        else:
            self.fail('Expected OSError: %s' % desired_exception)

    def test_exception_bad_args_0(self):
        """Test error in the child raised in the parent for a bad args[0]."""
        desired_exception = self._get_chdir_exception()
        try:
            p = subprocess.Popen([self._nonexistent_dir, '-c', ''])
        except OSError as e:
            self.assertEqual(desired_exception.errno, e.errno)
            self.assertEqual(desired_exception.strerror, e.strerror)
        else:
            self.fail('Expected OSError: %s' % desired_exception)

    def test_restore_signals(self):
        subprocess.call([sys.executable, '-c', ''], restore_signals=True)
        subprocess.call([sys.executable, '-c', ''], restore_signals=False)

    def test_start_new_session(self):
        try:
            output = subprocess.check_output([sys.executable, '-c',
                'import os; print(os.getpgid(os.getpid()))'],
                start_new_session=True)
        except OSError as e:
            if e.errno != errno.EPERM:
                raise
        else:
            parent_pgid = os.getpgid(os.getpid())
            child_pgid = int(output)
            self.assertNotEqual(parent_pgid, child_pgid)

    def test_run_abort(self):
        with support.SuppressCrashReport():
            p = subprocess.Popen([sys.executable, '-c',
                'import os; os.abort()'])
            p.wait()
        self.assertEqual(-p.returncode, signal.SIGABRT)

    def test_CalledProcessError_str_signal(self):
        err = subprocess.CalledProcessError(-int(signal.SIGABRT), 'fake cmd')
        error_string = str(err)
        self.assertIn('signal', error_string.lower())
        self.assertIn('SIG', error_string)
        self.assertIn(str(signal.SIGABRT), error_string)

    def test_CalledProcessError_str_unknown_signal(self):
        err = subprocess.CalledProcessError(-9876543, 'fake cmd')
        error_string = str(err)
        self.assertIn('unknown signal 9876543.', error_string)

    def test_CalledProcessError_str_non_zero(self):
        err = subprocess.CalledProcessError(2, 'fake cmd')
        error_string = str(err)
        self.assertIn('non-zero exit status 2.', error_string)

    def test_preexec(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys,os;sys.stdout.write(os.getenv("FRUIT"))'], stdout=
            subprocess.PIPE, preexec_fn=lambda : os.putenv('FRUIT', 'apple'))
        with p:
            self.assertEqual(p.stdout.read(), b'apple')

    def test_preexec_exception(self):

        def raise_it():
            raise ValueError('What if two swallows carried a coconut?')
        try:
            p = subprocess.Popen([sys.executable, '-c', ''], preexec_fn=
                raise_it)
        except subprocess.SubprocessError as e:
            self.assertTrue(subprocess._posixsubprocess,
                'Expected a ValueError from the preexec_fn')
        except ValueError as e:
            self.assertIn('coconut', e.args[0])
        else:
            self.fail(
                'Exception raised by preexec_fn did not make it to the parent process.'
                )


    class _TestExecuteChildPopen(subprocess.Popen):
        """Used to test behavior at the end of _execute_child."""

        def __init__(self, testcase, *args, **kwargs):
            self._testcase = testcase
            subprocess.Popen.__init__(self, *args, **kwargs)

        def _execute_child(self, *args, **kwargs):
            try:
                subprocess.Popen._execute_child(self, *args, **kwargs)
            finally:
                devzero_fds = [os.open('/dev/zero', os.O_RDONLY) for _ in
                    range(8)]
                try:
                    for fd in devzero_fds:
                        self._testcase.assertNotIn(fd, (self.stdin.fileno(),
                            self.stdout.fileno(), self.stderr.fileno()),
                            msg='At least one fd was closed early.')
                finally:
                    for fd in devzero_fds:
                        os.close(fd)

    @unittest.skipIf(not os.path.exists('/dev/zero'), '/dev/zero required.')
    def test_preexec_errpipe_does_not_double_close_pipes(self):
        """Issue16140: Don't double close pipes on preexec error."""

        def raise_it():
            raise subprocess.SubprocessError(
                'force the _execute_child() errpipe_data path.')
        with self.assertRaises(subprocess.SubprocessError):
            self._TestExecuteChildPopen(self, [sys.executable, '-c', 'pass'
                ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=
                subprocess.PIPE, preexec_fn=raise_it)

    def test_preexec_gc_module_failure(self):

        def raise_runtime_error():
            raise RuntimeError("this shouldn't escape")
        enabled = gc.isenabled()
        orig_gc_disable = gc.disable
        orig_gc_isenabled = gc.isenabled
        try:
            gc.disable()
            self.assertFalse(gc.isenabled())
            subprocess.call([sys.executable, '-c', ''], preexec_fn=lambda :
                None)
            self.assertFalse(gc.isenabled(),
                "Popen enabled gc when it shouldn't.")
            gc.enable()
            self.assertTrue(gc.isenabled())
            subprocess.call([sys.executable, '-c', ''], preexec_fn=lambda :
                None)
            self.assertTrue(gc.isenabled(), 'Popen left gc disabled.')
            gc.disable = raise_runtime_error
            self.assertRaises(RuntimeError, subprocess.Popen, [sys.
                executable, '-c', ''], preexec_fn=lambda : None)
            del gc.isenabled
            self.assertRaises(AttributeError, subprocess.Popen, [sys.
                executable, '-c', ''], preexec_fn=lambda : None)
        finally:
            gc.disable = orig_gc_disable
            gc.isenabled = orig_gc_isenabled
            if not enabled:
                gc.disable()

    @unittest.skipIf(sys.platform == 'darwin',
        'setrlimit() seems to fail on OS X')
    def test_preexec_fork_failure(self):
        try:
            from resource import getrlimit, setrlimit, RLIMIT_NPROC
        except ImportError as err:
            self.skipTest(err)
        limits = getrlimit(RLIMIT_NPROC)
        [_, hard] = limits
        setrlimit(RLIMIT_NPROC, (0, hard))
        self.addCleanup(setrlimit, RLIMIT_NPROC, limits)
        try:
            subprocess.call([sys.executable, '-c', ''], preexec_fn=lambda :
                None)
        except BlockingIOError:
            pass
        else:
            self.skipTest('RLIMIT_NPROC had no effect; probably superuser')

    def test_args_string(self):
        fd, fname = tempfile.mkstemp()
        with open(fd, 'w', errors='surrogateescape') as fobj:
            fobj.write('#!%s\n' % support.unix_shell)
            fobj.write("exec '%s' -c 'import sys; sys.exit(47)'\n" % sys.
                executable)
        os.chmod(fname, 448)
        p = subprocess.Popen(fname)
        p.wait()
        os.remove(fname)
        self.assertEqual(p.returncode, 47)

    def test_invalid_args(self):
        self.assertRaises(ValueError, subprocess.call, [sys.executable,
            '-c', 'import sys; sys.exit(47)'], startupinfo=47)
        self.assertRaises(ValueError, subprocess.call, [sys.executable,
            '-c', 'import sys; sys.exit(47)'], creationflags=47)

    def test_shell_sequence(self):
        newenv = os.environ.copy()
        newenv['FRUIT'] = 'apple'
        p = subprocess.Popen(['echo $FRUIT'], shell=1, stdout=subprocess.
            PIPE, env=newenv)
        with p:
            self.assertEqual(p.stdout.read().strip(b' \t\r\n\x0c'), b'apple')

    def test_shell_string(self):
        newenv = os.environ.copy()
        newenv['FRUIT'] = 'apple'
        p = subprocess.Popen('echo $FRUIT', shell=1, stdout=subprocess.PIPE,
            env=newenv)
        with p:
            self.assertEqual(p.stdout.read().strip(b' \t\r\n\x0c'), b'apple')

    def test_call_string(self):
        fd, fname = tempfile.mkstemp()
        with open(fd, 'w', errors='surrogateescape') as fobj:
            fobj.write('#!%s\n' % support.unix_shell)
            fobj.write("exec '%s' -c 'import sys; sys.exit(47)'\n" % sys.
                executable)
        os.chmod(fname, 448)
        rc = subprocess.call(fname)
        os.remove(fname)
        self.assertEqual(rc, 47)

    def test_specific_shell(self):
        shells = []
        for prefix in ['/bin', '/usr/bin/', '/usr/local/bin']:
            for name in ['bash', 'ksh']:
                sh = os.path.join(prefix, name)
                if os.path.isfile(sh):
                    shells.append(sh)
        if not shells:
            self.skipTest('bash or ksh required for this test')
        sh = '/bin/sh'
        if os.path.isfile(sh) and not os.path.islink(sh):
            shells.append(sh)
        for sh in shells:
            p = subprocess.Popen('echo $0', executable=sh, shell=True,
                stdout=subprocess.PIPE)
            with p:
                self.assertEqual(p.stdout.read().strip(), bytes(sh, 'ascii'))

    def _kill_process(self, method, *args):
        old_handler = signal.signal(signal.SIGINT, signal.default_int_handler)
        try:
            p = subprocess.Popen([sys.executable, '-c',
                """if 1:
                                 import sys, time
                                 sys.stdout.write('x\\n')
                                 sys.stdout.flush()
                                 time.sleep(30)
                                 """
                ], close_fds=True, stdin=subprocess.PIPE, stdout=subprocess
                .PIPE, stderr=subprocess.PIPE)
        finally:
            signal.signal(signal.SIGINT, old_handler)
        p.stdout.read(1)
        getattr(p, method)(*args)
        return p

    @unittest.skipIf(sys.platform.startswith(('netbsd', 'openbsd')),
        'Due to known OS bug (issue #16762)')
    def _kill_dead_process(self, method, *args):
        p = subprocess.Popen([sys.executable, '-c',
            """if 1:
                             import sys, time
                             sys.stdout.write('x\\n')
                             sys.stdout.flush()
                             """
            ], close_fds=True, stdin=subprocess.PIPE, stdout=subprocess.
            PIPE, stderr=subprocess.PIPE)
        p.stdout.read(1)
        time.sleep(1)
        getattr(p, method)(*args)
        p.communicate()

    def test_send_signal(self):
        p = self._kill_process('send_signal', signal.SIGINT)
        _, stderr = p.communicate()
        self.assertIn(b'KeyboardInterrupt', stderr)
        self.assertNotEqual(p.wait(), 0)

    def test_kill(self):
        p = self._kill_process('kill')
        _, stderr = p.communicate()
        self.assertStderrEqual(stderr, b'')
        self.assertEqual(p.wait(), -signal.SIGKILL)

    def test_terminate(self):
        p = self._kill_process('terminate')
        _, stderr = p.communicate()
        self.assertStderrEqual(stderr, b'')
        self.assertEqual(p.wait(), -signal.SIGTERM)

    def test_send_signal_dead(self):
        self._kill_dead_process('send_signal', signal.SIGINT)

    def test_kill_dead(self):
        self._kill_dead_process('kill')

    def test_terminate_dead(self):
        self._kill_dead_process('terminate')

    def _save_fds(self, save_fds):
        fds = []
        for fd in save_fds:
            inheritable = os.get_inheritable(fd)
            saved = os.dup(fd)
            fds.append((fd, saved, inheritable))
        return fds

    def _restore_fds(self, fds):
        for fd, saved, inheritable in fds:
            os.dup2(saved, fd, inheritable=inheritable)
            os.close(saved)

    def check_close_std_fds(self, fds):
        stdin = 0
        saved_fds = self._save_fds(fds)
        for fd, saved, inheritable in saved_fds:
            if fd == 0:
                stdin = saved
                break
        try:
            for fd in fds:
                os.close(fd)
            out, err = subprocess.Popen([sys.executable, '-c',
                'import sys;sys.stdout.write("apple");sys.stdout.flush();sys.stderr.write("orange")'
                ], stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                ).communicate()
            err = support.strip_python_stderr(err)
            self.assertEqual((out, err), (b'apple', b'orange'))
        finally:
            self._restore_fds(saved_fds)

    def test_close_fd_0(self):
        self.check_close_std_fds([0])

    def test_close_fd_1(self):
        self.check_close_std_fds([1])

    def test_close_fd_2(self):
        self.check_close_std_fds([2])

    def test_close_fds_0_1(self):
        self.check_close_std_fds([0, 1])

    def test_close_fds_0_2(self):
        self.check_close_std_fds([0, 2])

    def test_close_fds_1_2(self):
        self.check_close_std_fds([1, 2])

    def test_close_fds_0_1_2(self):
        self.check_close_std_fds([0, 1, 2])

    def test_small_errpipe_write_fd(self):
        """Issue #15798: Popen should work when stdio fds are available."""
        new_stdin = os.dup(0)
        new_stdout = os.dup(1)
        try:
            os.close(0)
            os.close(1)
            subprocess.Popen([sys.executable, '-c',
                "print('AssertionError:0:CLOEXEC failure.')"]).wait()
        finally:
            os.dup2(new_stdin, 0)
            os.dup2(new_stdout, 1)
            os.close(new_stdin)
            os.close(new_stdout)

    def test_remapping_std_fds(self):
        temps = [tempfile.mkstemp() for i in range(3)]
        try:
            temp_fds = [fd for fd, fname in temps]
            for fd, fname in temps:
                os.unlink(fname)
            os.write(temp_fds[1], b'STDIN')
            os.lseek(temp_fds[1], 0, 0)
            saved_fds = self._save_fds(range(3))
            try:
                for fd, temp_fd in enumerate(temp_fds):
                    os.dup2(temp_fd, fd)
                p = subprocess.Popen([sys.executable, '-c',
                    'import sys; got = sys.stdin.read();sys.stdout.write("got %s"%got); sys.stderr.write("err")'
                    ], stdin=temp_fds[1], stdout=temp_fds[2], stderr=
                    temp_fds[0])
                p.wait()
            finally:
                self._restore_fds(saved_fds)
            for fd in temp_fds:
                os.lseek(fd, 0, 0)
            out = os.read(temp_fds[2], 1024)
            err = support.strip_python_stderr(os.read(temp_fds[0], 1024))
            self.assertEqual(out, b'got STDIN')
            self.assertEqual(err, b'err')
        finally:
            for fd in temp_fds:
                os.close(fd)

    def check_swap_fds(self, stdin_no, stdout_no, stderr_no):
        temps = [tempfile.mkstemp() for i in range(3)]
        temp_fds = [fd for fd, fname in temps]
        try:
            for fd, fname in temps:
                os.unlink(fname)
            saved_fds = self._save_fds(range(3))
            try:
                for fd, temp_fd in enumerate(temp_fds):
                    os.dup2(temp_fd, fd)
                os.write(stdin_no, b'STDIN')
                os.lseek(stdin_no, 0, 0)
                p = subprocess.Popen([sys.executable, '-c',
                    'import sys; got = sys.stdin.read();sys.stdout.write("got %s"%got); sys.stderr.write("err")'
                    ], stdin=stdin_no, stdout=stdout_no, stderr=stderr_no)
                p.wait()
                for fd in temp_fds:
                    os.lseek(fd, 0, 0)
                out = os.read(stdout_no, 1024)
                err = support.strip_python_stderr(os.read(stderr_no, 1024))
            finally:
                self._restore_fds(saved_fds)
            self.assertEqual(out, b'got STDIN')
            self.assertEqual(err, b'err')
        finally:
            for fd in temp_fds:
                os.close(fd)

    def test_swap_fds(self):
        self.check_swap_fds(0, 1, 2)
        self.check_swap_fds(0, 2, 1)
        self.check_swap_fds(1, 0, 2)
        self.check_swap_fds(1, 2, 0)
        self.check_swap_fds(2, 0, 1)
        self.check_swap_fds(2, 1, 0)

    def test_surrogates_error_message(self):

        def prepare():
            raise ValueError('surrogate:\udcff')
        try:
            subprocess.call([sys.executable, '-c', 'pass'], preexec_fn=prepare)
        except ValueError as err:
            self.assertIsNone(subprocess._posixsubprocess)
            self.assertEqual(str(err), 'surrogate:\udcff')
        except subprocess.SubprocessError as err:
            self.assertIsNotNone(subprocess._posixsubprocess)
            self.assertEqual(str(err), 'Exception occurred in preexec_fn.')
        else:
            self.fail('Expected ValueError or subprocess.SubprocessError')

    def test_undecodable_env(self):
        for key, value in (('test', 'abc\udcff'), ('test\udcff', '42')):
            encoded_value = value.encode('ascii', 'surrogateescape')
            script = 'import os; print(ascii(os.getenv(%s)))' % repr(key)
            env = os.environ.copy()
            env[key] = value
            env['LC_ALL'] = 'C'
            if sys.platform.startswith('aix'):
                decoded_value = encoded_value.decode('latin1',
                    'surrogateescape')
            else:
                decoded_value = value
            stdout = subprocess.check_output([sys.executable, '-c', script],
                env=env)
            stdout = stdout.rstrip(b'\n\r')
            self.assertEqual(stdout.decode('ascii'), ascii(decoded_value))
            key = key.encode('ascii', 'surrogateescape')
            script = 'import os; print(ascii(os.getenvb(%s)))' % repr(key)
            env = os.environ.copy()
            env[key] = encoded_value
            stdout = subprocess.check_output([sys.executable, '-c', script],
                env=env)
            stdout = stdout.rstrip(b'\n\r')
            self.assertEqual(stdout.decode('ascii'), ascii(encoded_value))

    def test_bytes_program(self):
        abs_program = os.fsencode(sys.executable)
        path, program = os.path.split(sys.executable)
        program = os.fsencode(program)
        exitcode = subprocess.call([abs_program, '-c', 'pass'])
        self.assertEqual(exitcode, 0)
        cmd = b"'" + abs_program + b"' -c pass"
        exitcode = subprocess.call(cmd, shell=True)
        self.assertEqual(exitcode, 0)
        env = os.environ.copy()
        env['PATH'] = path
        exitcode = subprocess.call([program, '-c', 'pass'], env=env)
        self.assertEqual(exitcode, 0)
        envb = os.environb.copy()
        envb[b'PATH'] = os.fsencode(path)
        exitcode = subprocess.call([program, '-c', 'pass'], env=envb)
        self.assertEqual(exitcode, 0)

    def test_pipe_cloexec(self):
        sleeper = support.findfile('input_reader.py', subdir='subprocessdata')
        fd_status = support.findfile('fd_status.py', subdir='subprocessdata')
        p1 = subprocess.Popen([sys.executable, sleeper], stdin=subprocess.
            PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds
            =False)
        self.addCleanup(p1.communicate, b'')
        p2 = subprocess.Popen([sys.executable, fd_status], stdout=
            subprocess.PIPE, close_fds=False)
        output, error = p2.communicate()
        result_fds = set(map(int, output.split(b',')))
        unwanted_fds = set([p1.stdin.fileno(), p1.stdout.fileno(), p1.
            stderr.fileno()])
        self.assertFalse(result_fds & unwanted_fds, 
            'Expected no fds from %r to be open in child, found %r' % (
            unwanted_fds, result_fds & unwanted_fds))

    def test_pipe_cloexec_real_tools(self):
        qcat = support.findfile('qcat.py', subdir='subprocessdata')
        qgrep = support.findfile('qgrep.py', subdir='subprocessdata')
        subdata = b'zxcvbn'
        data = subdata * 4 + b'\n'
        p1 = subprocess.Popen([sys.executable, qcat], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, close_fds=False)
        p2 = subprocess.Popen([sys.executable, qgrep, subdata], stdin=p1.
            stdout, stdout=subprocess.PIPE, close_fds=False)
        self.addCleanup(p1.wait)
        self.addCleanup(p2.wait)

        def kill_p1():
            try:
                p1.terminate()
            except ProcessLookupError:
                pass

        def kill_p2():
            try:
                p2.terminate()
            except ProcessLookupError:
                pass
        self.addCleanup(kill_p1)
        self.addCleanup(kill_p2)
        p1.stdin.write(data)
        p1.stdin.close()
        readfiles, ignored1, ignored2 = select.select([p2.stdout], [], [], 10)
        self.assertTrue(readfiles, 'The child hung')
        self.assertEqual(p2.stdout.read(), data)
        p1.stdout.close()
        p2.stdout.close()

    def test_close_fds(self):
        fd_status = support.findfile('fd_status.py', subdir='subprocessdata')
        fds = os.pipe()
        self.addCleanup(os.close, fds[0])
        self.addCleanup(os.close, fds[1])
        open_fds = set(fds)
        for _ in range(9):
            fd = os.open(os.devnull, os.O_RDONLY)
            self.addCleanup(os.close, fd)
            open_fds.add(fd)
        for fd in open_fds:
            os.set_inheritable(fd, True)
        p = subprocess.Popen([sys.executable, fd_status], stdout=subprocess
            .PIPE, close_fds=False)
        output, ignored = p.communicate()
        remaining_fds = set(map(int, output.split(b',')))
        self.assertEqual(remaining_fds & open_fds, open_fds,
            'Some fds were closed')
        p = subprocess.Popen([sys.executable, fd_status], stdout=subprocess
            .PIPE, close_fds=True)
        output, ignored = p.communicate()
        remaining_fds = set(map(int, output.split(b',')))
        self.assertFalse(remaining_fds & open_fds, 'Some fds were left open')
        self.assertIn(1, remaining_fds, 'Subprocess failed')
        fds_to_keep = set(open_fds.pop() for _ in range(8))
        p = subprocess.Popen([sys.executable, fd_status], stdout=subprocess
            .PIPE, close_fds=True, pass_fds=())
        output, ignored = p.communicate()
        remaining_fds = set(map(int, output.split(b',')))
        self.assertFalse(remaining_fds & fds_to_keep & open_fds,
            'Some fds not in pass_fds were left open')
        self.assertIn(1, remaining_fds, 'Subprocess failed')

    @unittest.skipIf(sys.platform.startswith('freebsd') and os.stat('/dev')
        .st_dev == os.stat('/dev/fd').st_dev,
        'Requires fdescfs mounted on /dev/fd on FreeBSD.')
    def test_close_fds_when_max_fd_is_lowered(self):
        """Confirm that issue21618 is fixed (may fail under valgrind)."""
        fd_status = support.findfile('fd_status.py', subdir='subprocessdata')
        p = subprocess.Popen([sys.executable, '-c', textwrap.dedent(
            """
        import os, resource, subprocess, sys, textwrap
        open_fds = set()
        # Add a bunch more fds to pass down.
        for _ in range(40):
            fd = os.open(os.devnull, os.O_RDONLY)
            open_fds.add(fd)

        # Leave a two pairs of low ones available for use by the
        # internal child error pipe and the stdout pipe.
        # We also leave 10 more open as some Python buildbots run into
        # "too many open files" errors during the test if we do not.
        for fd in sorted(open_fds)[:14]:
            os.close(fd)
            open_fds.remove(fd)

        for fd in open_fds:
            #self.addCleanup(os.close, fd)
            os.set_inheritable(fd, True)

        max_fd_open = max(open_fds)

        # Communicate the open_fds to the parent unittest.TestCase process.
        print(','.join(map(str, sorted(open_fds))))
        sys.stdout.flush()

        rlim_cur, rlim_max = resource.getrlimit(resource.RLIMIT_NOFILE)
        try:
            # 29 is lower than the highest fds we are leaving open.
            resource.setrlimit(resource.RLIMIT_NOFILE, (29, rlim_max))
            # Launch a new Python interpreter with our low fd rlim_cur that
            # inherits open fds above that limit.  It then uses subprocess
            # with close_fds=True to get a report of open fds in the child.
            # An explicit list of fds to check is passed to fd_status.py as
            # letting fd_status rely on its default logic would miss the
            # fds above rlim_cur as it normally only checks up to that limit.
            subprocess.Popen(
                [sys.executable, '-c',
                 textwrap.dedent(""\"
                     import subprocess, sys
                     subprocess.Popen([sys.executable, %r] +
                                      [str(x) for x in range({max_fd})],
                                      close_fds=True).wait()
                     ""\".format(max_fd=max_fd_open+1))],
                close_fds=False).wait()
        finally:
            resource.setrlimit(resource.RLIMIT_NOFILE, (rlim_cur, rlim_max))
        """
             % fd_status)], stdout=subprocess.PIPE)
        output, unused_stderr = p.communicate()
        output_lines = output.splitlines()
        self.assertEqual(len(output_lines), 2, msg=
            'expected exactly two lines of output:\n%r' % output)
        opened_fds = set(map(int, output_lines[0].strip().split(b',')))
        remaining_fds = set(map(int, output_lines[1].strip().split(b',')))
        self.assertFalse(remaining_fds & opened_fds, msg=
            'Some fds were left open.')

    @support.requires_mac_ver(10, 5)
    def test_pass_fds(self):
        fd_status = support.findfile('fd_status.py', subdir='subprocessdata')
        open_fds = set()
        for x in range(5):
            fds = os.pipe()
            self.addCleanup(os.close, fds[0])
            self.addCleanup(os.close, fds[1])
            os.set_inheritable(fds[0], True)
            os.set_inheritable(fds[1], True)
            open_fds.update(fds)
        for fd in open_fds:
            p = subprocess.Popen([sys.executable, fd_status], stdout=
                subprocess.PIPE, close_fds=True, pass_fds=(fd,))
            output, ignored = p.communicate()
            remaining_fds = set(map(int, output.split(b',')))
            to_be_closed = open_fds - {fd}
            self.assertIn(fd, remaining_fds, 'fd to be passed not passed')
            self.assertFalse(remaining_fds & to_be_closed,
                'fd to be closed passed')
            with self.assertWarns(RuntimeWarning) as context:
                self.assertFalse(subprocess.call([sys.executable, '-c',
                    'import sys; sys.exit(0)'], close_fds=False, pass_fds=(
                    fd,)))
            self.assertIn('overriding close_fds', str(context.warning))

    def test_pass_fds_inheritable(self):
        script = support.findfile('fd_status.py', subdir='subprocessdata')
        inheritable, non_inheritable = os.pipe()
        self.addCleanup(os.close, inheritable)
        self.addCleanup(os.close, non_inheritable)
        os.set_inheritable(inheritable, True)
        os.set_inheritable(non_inheritable, False)
        pass_fds = inheritable, non_inheritable
        args = [sys.executable, script]
        args += list(map(str, pass_fds))
        p = subprocess.Popen(args, stdout=subprocess.PIPE, close_fds=True,
            pass_fds=pass_fds)
        output, ignored = p.communicate()
        fds = set(map(int, output.split(b',')))
        self.assertEqual(fds, set(pass_fds), 'output=%a' % output)
        self.assertEqual(os.get_inheritable(inheritable), True)
        self.assertEqual(os.get_inheritable(non_inheritable), False)

    def test_stdout_stdin_are_single_inout_fd(self):
        with io.open(os.devnull, 'r+') as inout:
            p = subprocess.Popen([sys.executable, '-c',
                'import sys; sys.exit(0)'], stdout=inout, stdin=inout)
            p.wait()

    def test_stdout_stderr_are_single_inout_fd(self):
        with io.open(os.devnull, 'r+') as inout:
            p = subprocess.Popen([sys.executable, '-c',
                'import sys; sys.exit(0)'], stdout=inout, stderr=inout)
            p.wait()

    def test_stderr_stdin_are_single_inout_fd(self):
        with io.open(os.devnull, 'r+') as inout:
            p = subprocess.Popen([sys.executable, '-c',
                'import sys; sys.exit(0)'], stderr=inout, stdin=inout)
            p.wait()

    def test_wait_when_sigchild_ignored(self):
        sigchild_ignore = support.findfile('sigchild_ignore.py', subdir=
            'subprocessdata')
        p = subprocess.Popen([sys.executable, sigchild_ignore], stdout=
            subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode, 
            """sigchild_ignore.py exited non-zero with this error:
%s""" %
            stderr.decode('utf-8'))

    def test_select_unbuffered(self):
        select = support.import_module('select')
        p = subprocess.Popen([sys.executable, '-c',
            'import sys;sys.stdout.write("apple")'], stdout=subprocess.PIPE,
            bufsize=0)
        f = p.stdout
        self.addCleanup(f.close)
        try:
            self.assertEqual(f.read(4), b'appl')
            self.assertIn(f, select.select([f], [], [], 0.0)[0])
        finally:
            p.wait()

    def test_zombie_fast_process_del(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import sys, time;time.sleep(0.2)'], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        ident = id(p)
        pid = p.pid
        with support.check_warnings(('', ResourceWarning)):
            p = None
        self.assertIn(ident, [id(o) for o in subprocess._active])

    def test_leak_fast_process_del_killed(self):
        p = subprocess.Popen([sys.executable, '-c',
            'import time;time.sleep(3)'], stdout=subprocess.PIPE, stderr=
            subprocess.PIPE)
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        ident = id(p)
        pid = p.pid
        with support.check_warnings(('', ResourceWarning)):
            p = None
        os.kill(pid, signal.SIGKILL)
        self.assertIn(ident, [id(o) for o in subprocess._active])
        time.sleep(0.2)
        with self.assertRaises(OSError) as c:
            with subprocess.Popen(['nonexisting_i_hope'], stdout=subprocess
                .PIPE, stderr=subprocess.PIPE) as proc:
                pass
        self.assertRaises(OSError, os.waitpid, pid, 0)
        self.assertNotIn(ident, [id(o) for o in subprocess._active])

    def test_close_fds_after_preexec(self):
        fd_status = support.findfile('fd_status.py', subdir='subprocessdata')
        fd = os.dup(1)
        self.addCleanup(os.close, fd)
        p = subprocess.Popen([sys.executable, fd_status], stdout=subprocess
            .PIPE, close_fds=True, preexec_fn=lambda : os.dup2(1, fd))
        output, ignored = p.communicate()
        remaining_fds = set(map(int, output.split(b',')))
        self.assertNotIn(fd, remaining_fds)

    @support.cpython_only
    def test_fork_exec(self):
        import _posixsubprocess
        gc_enabled = gc.isenabled()
        try:
            func = lambda : None
            gc.enable()
            for args, exe_list, cwd, env_list in ((123, [b'exe'], None, [
                b'env']), ([b'arg'], 123, None, [b'env']), ([b'arg'], [
                b'exe'], 123, [b'env']), ([b'arg'], [b'exe'], None, 123)):
                with self.assertRaises(TypeError):
                    _posixsubprocess.fork_exec(args, exe_list, True, (),
                        cwd, env_list, -1, -1, -1, -1, 1, 2, 3, 4, True,
                        True, func)
        finally:
            if not gc_enabled:
                gc.disable()

    @support.cpython_only
    def test_fork_exec_sorted_fd_sanity_check(self):
        import _posixsubprocess


        class BadInt:
            first = True

            def __init__(self, value):
                self.value = value

            def __int__(self):
                if self.first:
                    self.first = False
                    return self.value
                raise ValueError
        gc_enabled = gc.isenabled()
        try:
            gc.enable()
            for fds_to_keep in ((-1, 2, 3, 4, 5), ('str', 4), (18, 23, 42, 
                2 ** 63), (5, 4), (6, 7, 7, 8), (BadInt(1), BadInt(2))):
                with self.assertRaises(ValueError, msg='fds_to_keep={}'.
                    format(fds_to_keep)) as c:
                    _posixsubprocess.fork_exec([b'false'], [b'false'], True,
                        fds_to_keep, None, [b'env'], -1, -1, -1, -1, 1, 2, 
                        3, 4, True, True, None)
                self.assertIn('fds_to_keep', str(c.exception))
        finally:
            if not gc_enabled:
                gc.disable()

    def test_communicate_BrokenPipeError_stdin_close(self):
        proc = subprocess.Popen([sys.executable, '-c', 'pass'])
        with proc, mock.patch.object(proc, 'stdin') as mock_proc_stdin:
            mock_proc_stdin.close.side_effect = BrokenPipeError
            proc.communicate()
            mock_proc_stdin.close.assert_called_with()

    def test_communicate_BrokenPipeError_stdin_write(self):
        proc = subprocess.Popen([sys.executable, '-c', 'pass'])
        with proc, mock.patch.object(proc, 'stdin') as mock_proc_stdin:
            mock_proc_stdin.write.side_effect = BrokenPipeError
            proc.communicate(b'stuff')
            mock_proc_stdin.write.assert_called_once_with(b'stuff')
            mock_proc_stdin.close.assert_called_once_with()

    def test_communicate_BrokenPipeError_stdin_flush(self):
        proc = subprocess.Popen([sys.executable, '-h'], stdin=subprocess.
            PIPE, stdout=subprocess.PIPE)
        with proc, mock.patch.object(proc, 'stdin') as mock_proc_stdin, open(os
            .devnull, 'wb') as dev_null:
            mock_proc_stdin.flush.side_effect = BrokenPipeError
            mock_proc_stdin.fileno.return_value = dev_null.fileno()
            proc.communicate(b'stuff')
            mock_proc_stdin.flush.assert_called_once_with()

    def test_communicate_BrokenPipeError_stdin_close_with_timeout(self):
        proc = subprocess.Popen([sys.executable, '-h'], stdin=subprocess.
            PIPE, stdout=subprocess.PIPE)
        with proc, mock.patch.object(proc, 'stdin') as mock_proc_stdin:
            mock_proc_stdin.close.side_effect = BrokenPipeError
            proc.communicate(timeout=999)
            mock_proc_stdin.close.assert_called_once_with()
    _libc_file_extensions = {'Linux': 'so.6', 'Darwin': 'dylib'}

    @unittest.skipIf(not ctypes, 'ctypes module required.')
    @unittest.skipIf(platform.uname()[0] not in _libc_file_extensions,
        'Test requires a libc this code can load with ctypes.')
    @unittest.skipIf(not sys.executable, 'Test requires sys.executable.')
    def test_child_terminated_in_stopped_state(self):
        """Test wait() behavior when waitpid returns WIFSTOPPED; issue29335."""
        PTRACE_TRACEME = 0
        libc_name = 'libc.' + self._libc_file_extensions[platform.uname()[0]]
        libc = ctypes.CDLL(libc_name)
        if not hasattr(libc, 'ptrace'):
            raise unittest.SkipTest('ptrace() required.')
        test_ptrace = subprocess.Popen([sys.executable, '-c',
            """if True:
             import ctypes
             libc = ctypes.CDLL({libc_name!r})
             libc.ptrace({PTRACE_TRACEME}, 0, 0)
             """
            .format(libc_name=libc_name, PTRACE_TRACEME=PTRACE_TRACEME)])
        if test_ptrace.wait() != 0:
            raise unittest.SkipTest('ptrace() failed - unable to test.')
        child = subprocess.Popen([sys.executable, '-c',
            """if True:
             import ctypes
             libc = ctypes.CDLL({libc_name!r})
             libc.ptrace({PTRACE_TRACEME}, 0, 0)
             libc.printf(ctypes.c_char_p(0xdeadbeef))  # Crash the process.
             """
            .format(libc_name=libc_name, PTRACE_TRACEME=PTRACE_TRACEME)])
        try:
            returncode = child.wait()
        except Exception as e:
            child.kill()
            raise e
        self.assertNotEqual(0, returncode)
        self.assertLess(returncode, 0)


@unittest.skipUnless(mswindows, 'Windows specific tests')
class Win32ProcessTestCase(BaseTestCase):

    def test_startupinfo(self):
        STARTF_USESHOWWINDOW = 1
        SW_MAXIMIZE = 3
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = SW_MAXIMIZE
        subprocess.call([sys.executable, '-c', 'import sys; sys.exit(0)'],
            startupinfo=startupinfo)

    def test_creationflags(self):
        CREATE_NEW_CONSOLE = 16
        sys.stderr.write('    a DOS box should flash briefly ...\n')
        subprocess.call(sys.executable +
            ' -c "import time; time.sleep(0.25)"', creationflags=
            CREATE_NEW_CONSOLE)

    def test_invalid_args(self):
        self.assertRaises(ValueError, subprocess.call, [sys.executable,
            '-c', 'import sys; sys.exit(47)'], preexec_fn=lambda : 1)
        self.assertRaises(ValueError, subprocess.call, [sys.executable,
            '-c', 'import sys; sys.exit(47)'], stdout=subprocess.PIPE,
            close_fds=True)

    def test_close_fds(self):
        rc = subprocess.call([sys.executable, '-c',
            'import sys; sys.exit(47)'], close_fds=True)
        self.assertEqual(rc, 47)

    def test_shell_sequence(self):
        newenv = os.environ.copy()
        newenv['FRUIT'] = 'physalis'
        p = subprocess.Popen(['set'], shell=1, stdout=subprocess.PIPE, env=
            newenv)
        with p:
            self.assertIn(b'physalis', p.stdout.read())

    def test_shell_string(self):
        newenv = os.environ.copy()
        newenv['FRUIT'] = 'physalis'
        p = subprocess.Popen('set', shell=1, stdout=subprocess.PIPE, env=newenv
            )
        with p:
            self.assertIn(b'physalis', p.stdout.read())

    def test_shell_encodings(self):
        for enc in ['ansi', 'oem']:
            newenv = os.environ.copy()
            newenv['FRUIT'] = 'physalis'
            p = subprocess.Popen('set', shell=1, stdout=subprocess.PIPE,
                env=newenv, encoding=enc)
            with p:
                self.assertIn('physalis', p.stdout.read(), enc)

    def test_call_string(self):
        rc = subprocess.call(sys.executable + ' -c "import sys; sys.exit(47)"')
        self.assertEqual(rc, 47)

    def _kill_process(self, method, *args):
        p = subprocess.Popen([sys.executable, '-c',
            """if 1:
                             import sys, time
                             sys.stdout.write('x\\n')
                             sys.stdout.flush()
                             time.sleep(30)
                             """
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=
            subprocess.PIPE)
        with p:
            p.stdout.read(1)
            getattr(p, method)(*args)
            _, stderr = p.communicate()
            self.assertStderrEqual(stderr, b'')
            returncode = p.wait()
        self.assertNotEqual(returncode, 0)

    def _kill_dead_process(self, method, *args):
        p = subprocess.Popen([sys.executable, '-c',
            """if 1:
                             import sys, time
                             sys.stdout.write('x\\n')
                             sys.stdout.flush()
                             sys.exit(42)
                             """
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=
            subprocess.PIPE)
        with p:
            p.stdout.read(1)
            time.sleep(1)
            getattr(p, method)(*args)
            _, stderr = p.communicate()
            self.assertStderrEqual(stderr, b'')
            rc = p.wait()
        self.assertEqual(rc, 42)

    def test_send_signal(self):
        self._kill_process('send_signal', signal.SIGTERM)

    def test_kill(self):
        self._kill_process('kill')

    def test_terminate(self):
        self._kill_process('terminate')

    def test_send_signal_dead(self):
        self._kill_dead_process('send_signal', signal.SIGTERM)

    def test_kill_dead(self):
        self._kill_dead_process('kill')

    def test_terminate_dead(self):
        self._kill_dead_process('terminate')


class MiscTests(unittest.TestCase):

    def test_getoutput(self):
        self.assertEqual(subprocess.getoutput('echo xyzzy'), 'xyzzy')
        self.assertEqual(subprocess.getstatusoutput('echo xyzzy'), (0, 'xyzzy')
            )
        dir = None
        try:
            dir = tempfile.mkdtemp()
            name = os.path.join(dir, 'foo')
            status, output = subprocess.getstatusoutput(('type ' if
                mswindows else 'cat ') + name)
            self.assertNotEqual(status, 0)
        finally:
            if dir is not None:
                os.rmdir(dir)

    def test__all__(self):
        """Ensure that __all__ is populated properly."""
        intentionally_excluded = {'list2cmdline', 'Handle'}
        exported = set(subprocess.__all__)
        possible_exports = set()
        import types
        for name, value in subprocess.__dict__.items():
            if name.startswith('_'):
                continue
            if isinstance(value, (types.ModuleType,)):
                continue
            possible_exports.add(name)
        self.assertEqual(exported, possible_exports - intentionally_excluded)


@unittest.skipUnless(hasattr(selectors, 'PollSelector'),
    'Test needs selectors.PollSelector')
class ProcessTestCaseNoPoll(ProcessTestCase):

    def setUp(self):
        self.orig_selector = subprocess._PopenSelector
        subprocess._PopenSelector = selectors.SelectSelector
        ProcessTestCase.setUp(self)

    def tearDown(self):
        subprocess._PopenSelector = self.orig_selector
        ProcessTestCase.tearDown(self)


@unittest.skipUnless(mswindows, 'Windows-specific tests')
class CommandsWithSpaces(BaseTestCase):

    def setUp(self):
        super().setUp()
        f, fname = tempfile.mkstemp('.py', 'te st')
        self.fname = fname.lower()
        os.write(f,
            b"import sys;sys.stdout.write('%d %s' % (len(sys.argv), [a.lower () for a in sys.argv]))"
            )
        os.close(f)

    def tearDown(self):
        os.remove(self.fname)
        super().tearDown()

    def with_spaces(self, *args, **kwargs):
        kwargs['stdout'] = subprocess.PIPE
        p = subprocess.Popen(*args, **kwargs)
        with p:
            self.assertEqual(p.stdout.read().decode('mbcs'), 
                "2 [%r, 'ab cd']" % self.fname)

    def test_shell_string_with_spaces(self):
        self.with_spaces('"%s" "%s" "%s"' % (sys.executable, self.fname,
            'ab cd'), shell=1)

    def test_shell_sequence_with_spaces(self):
        self.with_spaces([sys.executable, self.fname, 'ab cd'], shell=1)

    def test_noshell_string_with_spaces(self):
        self.with_spaces('"%s" "%s" "%s"' % (sys.executable, self.fname,
            'ab cd'))

    def test_noshell_sequence_with_spaces(self):
        self.with_spaces([sys.executable, self.fname, 'ab cd'])


class ContextManagerTests(BaseTestCase):

    def test_pipe(self):
        with subprocess.Popen([sys.executable, '-c',
            "import sys;sys.stdout.write('stdout');sys.stderr.write('stderr');"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            self.assertEqual(proc.stdout.read(), b'stdout')
            self.assertStderrEqual(proc.stderr.read(), b'stderr')
        self.assertTrue(proc.stdout.closed)
        self.assertTrue(proc.stderr.closed)

    def test_returncode(self):
        with subprocess.Popen([sys.executable, '-c',
            'import sys; sys.exit(100)']) as proc:
            pass
        self.assertEqual(proc.returncode, 100)

    def test_communicate_stdin(self):
        with subprocess.Popen([sys.executable, '-c',
            "import sys;sys.exit(sys.stdin.read() == 'context')"], stdin=
            subprocess.PIPE) as proc:
            proc.communicate(b'context')
            self.assertEqual(proc.returncode, 1)

    def test_invalid_args(self):
        with self.assertRaises((FileNotFoundError, PermissionError)) as c:
            with subprocess.Popen(['nonexisting_i_hope'], stdout=subprocess
                .PIPE, stderr=subprocess.PIPE) as proc:
                pass

    def test_broken_pipe_cleanup(self):
        """Broken pipe error should not prevent wait() (Issue 21619)"""
        proc = subprocess.Popen([sys.executable, '-c', 'pass'], stdin=
            subprocess.PIPE, bufsize=support.PIPE_MAX_SIZE * 2)
        proc = proc.__enter__()
        proc.stdin.write(b'x' * support.PIPE_MAX_SIZE)
        self.assertIsNone(proc.returncode)
        self.assertRaises(OSError, proc.__exit__, None, None, None)
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(proc.stdin.closed)


if __name__ == '__main__':
    unittest.main()
