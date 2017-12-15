import test.support, unittest
import os
import shutil
import sys
import subprocess
import tempfile
from test.support import script_helper, is_android
from test.support.script_helper import spawn_python, kill_python, assert_python_ok, assert_python_failure


def _kill_python_and_exit_code(p):
    data = kill_python(p)
    returncode = p.wait()
    return data, returncode


class CmdLineTest(unittest.TestCase):

    def test_directories(self):
        assert_python_failure('.')
        assert_python_failure('< .')

    def verify_valid_flag(self, cmd_line):
        rc, out, err = assert_python_ok(*cmd_line)
        self.assertTrue(out == b'' or out.endswith(b'\n'))
        self.assertNotIn(b'Traceback', out)
        self.assertNotIn(b'Traceback', err)

    def test_optimize(self):
        self.verify_valid_flag('-O')
        self.verify_valid_flag('-OO')

    def test_site_flag(self):
        self.verify_valid_flag('-S')

    def test_usage(self):
        rc, out, err = assert_python_ok('-h')
        self.assertIn(b'usage', out)

    def test_version(self):
        version = ('Python %d.%d' % sys.version_info[:2]).encode('ascii')
        for switch in ('-V', '--version', '-VV'):
            rc, out, err = assert_python_ok(switch)
            self.assertFalse(err.startswith(version))
            self.assertTrue(out.startswith(version))

    def test_verbose(self):
        rc, out, err = assert_python_ok('-v')
        self.assertNotIn(b'stack overflow', err)
        rc, out, err = assert_python_ok('-vv')
        self.assertNotIn(b'stack overflow', err)

    def test_xoptions(self):

        def get_xoptions(*args):
            args = (sys.executable, '-E') + args
            args += '-c', 'import sys; print(sys._xoptions)'
            out = subprocess.check_output(args)
            opts = eval(out.splitlines()[0])
            return opts
        opts = get_xoptions()
        self.assertEqual(opts, {})
        opts = get_xoptions('-Xa', '-Xb=c,d=e')
        self.assertEqual(opts, {'a': True, 'b': 'c,d=e'})

    def test_showrefcount(self):

        def run_python(*args):
            cmd = [sys.executable]
            cmd.extend(args)
            PIPE = subprocess.PIPE
            p = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            p.stdout.close()
            p.stderr.close()
            rc = p.returncode
            self.assertEqual(rc, 0)
            return rc, out, err
        code = 'import sys; print(sys._xoptions)'
        rc, out, err = run_python('-c', code)
        self.assertEqual(out.rstrip(), b'{}')
        self.assertEqual(err, b'')
        rc, out, err = run_python('-X', 'showrefcount', '-c', code)
        self.assertEqual(out.rstrip(), b"{'showrefcount': True}")
        if hasattr(sys, 'gettotalrefcount'):
            self.assertRegex(err, b'^\\[\\d+ refs, \\d+ blocks\\]')
        else:
            self.assertEqual(err, b'')

    def test_run_module(self):
        assert_python_failure('-m')
        assert_python_failure('-m', 'fnord43520xyz')
        assert_python_failure('-m', 'runpy', 'fnord43520xyz')
        assert_python_ok('-m', 'timeit', '-n', '1')

    def test_run_module_bug1764407(self):
        p = spawn_python('-i', '-m', 'timeit', '-n', '1')
        p.stdin.write(b'Timer\n')
        p.stdin.write(b'exit()\n')
        data = kill_python(p)
        self.assertTrue(data.find(b'1 loop') != -1)
        self.assertTrue(data.find(b'__main__.Timer') != -1)

    def test_run_code(self):
        assert_python_failure('-c')
        assert_python_failure('-c', 'raise Exception')
        assert_python_ok('-c', 'pass')

    @unittest.skipUnless(test.support.FS_NONASCII, 'need support.FS_NONASCII')
    def test_non_ascii(self):
        command = 'assert(ord(%r) == %s)' % (test.support.FS_NONASCII, ord(
            test.support.FS_NONASCII))
        assert_python_ok('-c', command)

    @unittest.skipIf(sys.platform == 'win32',
        'Windows has a native unicode API')
    def test_undecodable_code(self):
        undecodable = b'\xff'
        env = os.environ.copy()
        env['LC_ALL'] = 'C'
        code = (b'import locale; print(ascii("' + undecodable +
            b'"), locale.getpreferredencoding())')
        p = subprocess.Popen([sys.executable, '-c', code], stdout=
            subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        stdout, stderr = p.communicate()
        if p.returncode == 1:
            pattern = b'Unable to decode the command from the command line:'
        elif p.returncode == 0:
            pattern = b"'\\xff' "
        else:
            raise AssertionError('Unknown exit code: %s, output=%a' % (p.
                returncode, stdout))
        if not stdout.startswith(pattern):
            raise AssertionError("%a doesn't start with %a" % (stdout, pattern)
                )

    @unittest.skipUnless(sys.platform == 'darwin' or is_android,
        'test specific to Mac OS X and Android')
    def test_osx_android_utf8(self):

        def check_output(text):
            decoded = text.decode('utf-8', 'surrogateescape')
            expected = ascii(decoded).encode('ascii') + b'\n'
            env = os.environ.copy()
            env['LC_ALL'] = 'C'
            p = subprocess.Popen((sys.executable, '-c',
                'import sys; print(ascii(sys.argv[1]))', text), stdout=
                subprocess.PIPE, env=env)
            stdout, stderr = p.communicate()
            self.assertEqual(stdout, expected)
            self.assertEqual(p.returncode, 0)
        text = 'e:é, euro:€, non-bmp:\U0010ffff'.encode('utf-8')
        check_output(text)
        text = b'\xff\xc3\xa9\xc3\xff\xed\xa0\x80'
        check_output(text)

    def test_unbuffered_output(self):
        for stream in ('stdout', 'stderr'):
            code = (
                "import os, sys; sys.%s.buffer.write(b'x'); os._exit(0)" %
                stream)
            rc, out, err = assert_python_ok('-u', '-c', code)
            data = err if stream == 'stderr' else out
            self.assertEqual(data, b'x', 'binary %s not unbuffered' % stream)
            code = "import os, sys; sys.%s.write('x\\n'); os._exit(0)" % stream
            rc, out, err = assert_python_ok('-u', '-c', code)
            data = err if stream == 'stderr' else out
            self.assertEqual(data.strip(), b'x', 
                'text %s not line-buffered' % stream)

    def test_unbuffered_input(self):
        code = 'import sys; sys.stdout.write(sys.stdin.read(1))'
        p = spawn_python('-u', '-c', code)
        p.stdin.write(b'x')
        p.stdin.flush()
        data, rc = _kill_python_and_exit_code(p)
        self.assertEqual(rc, 0)
        self.assertTrue(data.startswith(b'x'), data)

    def test_large_PYTHONPATH(self):
        path1 = 'ABCDE' * 100
        path2 = 'FGHIJ' * 100
        path = path1 + os.pathsep + path2
        code = """if 1:
            import sys
            path = ":".join(sys.path)
            path = path.encode("ascii", "backslashreplace")
            sys.stdout.buffer.write(path)"""
        rc, out, err = assert_python_ok('-S', '-c', code, PYTHONPATH=path)
        self.assertIn(path1.encode('ascii'), out)
        self.assertIn(path2.encode('ascii'), out)

    def test_empty_PYTHONPATH_issue16309(self):
        code = """if 1:
            import sys
            path = ":".join(sys.path)
            path = path.encode("ascii", "backslashreplace")
            sys.stdout.buffer.write(path)"""
        rc1, out1, err1 = assert_python_ok('-c', code, PYTHONPATH='')
        rc2, out2, err2 = assert_python_ok('-c', code, __isolated=False)
        self.assertEqual(out1, out2)

    def test_displayhook_unencodable(self):
        for encoding in ('ascii', 'latin-1', 'utf-8'):
            env = {key: value for key, value in os.environ.copy().items() if
                not key.startswith('PYTHON')}
            env['PYTHONIOENCODING'] = encoding
            p = subprocess.Popen([sys.executable, '-i'], stdin=subprocess.
                PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
                )
            text = 'a=é b=\udc80 c=𐀀 d=\U0010ffff'
            p.stdin.write(ascii(text).encode('ascii') + b'\n')
            p.stdin.write(b'exit()\n')
            data = kill_python(p)
            escaped = repr(text).encode(encoding, 'backslashreplace')
            self.assertIn(escaped, data)

    def check_input(self, code, expected):
        with tempfile.NamedTemporaryFile('wb+') as stdin:
            sep = os.linesep.encode('ASCII')
            stdin.write(sep.join((b'abc', b'def')))
            stdin.flush()
            stdin.seek(0)
            with subprocess.Popen((sys.executable, '-c', code), stdin=stdin,
                stdout=subprocess.PIPE) as proc:
                stdout, stderr = proc.communicate()
        self.assertEqual(stdout.rstrip(), expected)

    def test_stdin_readline(self):
        self.check_input('import sys; print(repr(sys.stdin.readline()))',
            b"'abc\\n'")

    def test_builtin_input(self):
        self.check_input('print(repr(input()))', b"'abc'")

    def test_output_newline(self):
        code = """if 1:
            import sys
            print(1)
            print(2)
            print(3, file=sys.stderr)
            print(4, file=sys.stderr)"""
        rc, out, err = assert_python_ok('-c', code)
        if sys.platform == 'win32':
            self.assertEqual(b'1\r\n2\r\n', out)
            self.assertEqual(b'3\r\n4', err)
        else:
            self.assertEqual(b'1\n2\n', out)
            self.assertEqual(b'3\n4', err)

    def test_unmached_quote(self):
        rc, out, err = assert_python_failure('-c', "'")
        self.assertRegex(err.decode('ascii', 'ignore'), 'SyntaxError')
        self.assertEqual(b'', out)

    def test_stdout_flush_at_shutdown(self):
        code = """if 1:
            import os, sys, test.support
            test.support.SuppressCrashReport().__enter__()
            sys.stdout.write('x')
            os.close(sys.stdout.fileno())"""
        rc, out, err = assert_python_failure('-c', code)
        self.assertEqual(b'', out)
        self.assertEqual(120, rc)
        self.assertRegex(err.decode('ascii', 'ignore'),
            'Exception ignored in.*\nOSError: .*')

    def test_closed_stdout(self):
        code = 'import sys; sys.stdout.close()'
        rc, out, err = assert_python_ok('-c', code)
        self.assertEqual(b'', err)

    @unittest.skipIf(os.name != 'posix', 'test needs POSIX semantics')
    def _test_no_stdio(self, streams):
        code = (
            """if 1:
            import os, sys
            for i, s in enumerate({streams}):
                if getattr(sys, s) is not None:
                    os._exit(i + 1)
            os._exit(42)"""
            .format(streams=streams))

        def preexec():
            if 'stdin' in streams:
                os.close(0)
            if 'stdout' in streams:
                os.close(1)
            if 'stderr' in streams:
                os.close(2)
        p = subprocess.Popen([sys.executable, '-E', '-c', code], stdin=
            subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=preexec)
        out, err = p.communicate()
        self.assertEqual(test.support.strip_python_stderr(err), b'')
        self.assertEqual(p.returncode, 42)

    def test_no_stdin(self):
        self._test_no_stdio(['stdin'])

    def test_no_stdout(self):
        self._test_no_stdio(['stdout'])

    def test_no_stderr(self):
        self._test_no_stdio(['stderr'])

    def test_no_std_streams(self):
        self._test_no_stdio(['stdin', 'stdout', 'stderr'])

    def test_hash_randomization(self):
        self.verify_valid_flag('-R')
        hashes = []
        if os.environ.get('PYTHONHASHSEED', 'random') != 'random':
            env = dict(os.environ)
            del env['PYTHONHASHSEED']
            env['__cleanenv'] = '1'
        else:
            env = {}
        for i in range(3):
            code = 'print(hash("spam"))'
            rc, out, err = assert_python_ok('-c', code, **env)
            self.assertEqual(rc, 0)
            hashes.append(out)
        hashes = sorted(set(hashes))
        self.assertGreater(len(hashes), 1, msg=
            '3 runs produced an identical random hash  for "spam": {}'.
            format(hashes))
        code = 'import sys; print("random is", sys.flags.hash_randomization)'
        rc, out, err = assert_python_ok('-c', code)
        self.assertEqual(rc, 0)
        self.assertIn(b'random is 1', out)

    def test_del___main__(self):
        filename = test.support.TESTFN
        self.addCleanup(test.support.unlink, filename)
        with open(filename, 'w') as script:
            print('import sys', file=script)
            print("del sys.modules['__main__']", file=script)
        assert_python_ok(filename)

    def test_unknown_options(self):
        rc, out, err = assert_python_failure('-E', '-z')
        self.assertIn(b'Unknown option: -z', err)
        self.assertEqual(err.splitlines().count(b'Unknown option: -z'), 1)
        self.assertEqual(b'', out)
        rc, out, err = assert_python_failure('-z', without='-E')
        self.assertIn(b'Unknown option: -z', err)
        self.assertEqual(err.splitlines().count(b'Unknown option: -z'), 1)
        self.assertEqual(b'', out)
        rc, out, err = assert_python_failure('-a', '-z', without='-E')
        self.assertIn(b'Unknown option: -a', err)
        self.assertNotIn(b'Unknown option: -z', err)
        self.assertEqual(err.splitlines().count(b'Unknown option: -a'), 1)
        self.assertEqual(b'', out)

    @unittest.skipIf(script_helper.interpreter_requires_environment(),
        'Cannot run -I tests when PYTHON env vars are required.')
    def test_isolatedmode(self):
        self.verify_valid_flag('-I')
        self.verify_valid_flag('-IEs')
        rc, out, err = assert_python_ok('-I', '-c',
            'from sys import flags as f; print(f.no_user_site, f.ignore_environment, f.isolated)'
            , dummyvar='')
        self.assertEqual(out.strip(), b'1 1 1')
        with test.support.temp_cwd() as tmpdir:
            fake = os.path.join(tmpdir, 'uuid.py')
            main = os.path.join(tmpdir, 'main.py')
            with open(fake, 'w') as f:
                f.write("raise RuntimeError('isolated mode test')\n")
            with open(main, 'w') as f:
                f.write('import uuid\n')
                f.write("print('ok')\n")
            self.assertRaises(subprocess.CalledProcessError, subprocess.
                check_output, [sys.executable, main], cwd=tmpdir, stderr=
                subprocess.DEVNULL)
            out = subprocess.check_output([sys.executable, '-I', main], cwd
                =tmpdir)
            self.assertEqual(out.strip(), b'ok')


def test_main():
    test.support.run_unittest(CmdLineTest)
    test.support.reap_children()


if __name__ == '__main__':
    test_main()
