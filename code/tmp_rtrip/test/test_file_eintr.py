import os
import select
import signal
import subprocess
import sys
import time
import unittest
import _io
import _pyio


@unittest.skipUnless(os.name == 'posix', 'tests requires a posix system.')
class TestFileIOSignalInterrupt:

    def setUp(self):
        self._process = None

    def tearDown(self):
        if self._process and self._process.poll() is None:
            try:
                self._process.kill()
            except OSError:
                pass

    def _generate_infile_setup_code(self):
        """Returns the infile = ... line of code for the reader process.

        subclasseses should override this to test different IO objects.
        """
        return (
            'import %s as io ;infile = io.FileIO(sys.stdin.fileno(), "rb")' %
            self.modname)

    def fail_with_process_info(self, why, stdout=b'', stderr=b'',
        communicate=True):
        """A common way to cleanup and fail with useful debug output.

        Kills the process if it is still running, collects remaining output
        and fails the test with an error message including the output.

        Args:
            why: Text to go after "Error from IO process" in the message.
            stdout, stderr: standard output and error from the process so
                far to include in the error message.
            communicate: bool, when True we call communicate() on the process
                after killing it to gather additional output.
        """
        if self._process.poll() is None:
            time.sleep(0.1)
            try:
                self._process.terminate()
            except OSError:
                pass
        if communicate:
            stdout_end, stderr_end = self._process.communicate()
            stdout += stdout_end
            stderr += stderr_end
        self.fail('Error from IO process %s:\nSTDOUT:\n%sSTDERR:\n%s\n' % (
            why, stdout.decode(), stderr.decode()))

    def _test_reading(self, data_to_write, read_and_verify_code):
        """Generic buffered read method test harness to validate EINTR behavior.

        Also validates that Python signal handlers are run during the read.

        Args:
            data_to_write: String to write to the child process for reading
                before sending it a signal, confirming the signal was handled,
                writing a final newline and closing the infile pipe.
            read_and_verify_code: Single "line" of code to read from a file
                object named 'infile' and validate the result.  This will be
                executed as part of a python subprocess fed data_to_write.
        """
        infile_setup_code = self._generate_infile_setup_code()
        assert len(data_to_write) < 512, 'data_to_write must fit in pipe buf.'
        self._process = subprocess.Popen([sys.executable, '-u', '-c', 
            'import signal, sys ;signal.signal(signal.SIGINT, lambda s, f: sys.stderr.write("$\\n")) ;'
             + infile_setup_code + ' ;' +
            'sys.stderr.write("Worm Sign!\\n") ;' + read_and_verify_code +
            ' ;' + 'infile.close()'], stdin=subprocess.PIPE, stdout=
            subprocess.PIPE, stderr=subprocess.PIPE)
        worm_sign = self._process.stderr.read(len(b'Worm Sign!\n'))
        if worm_sign != b'Worm Sign!\n':
            self.fail_with_process_info('while awaiting a sign', stderr=
                worm_sign)
        self._process.stdin.write(data_to_write)
        signals_sent = 0
        rlist = []
        while not rlist:
            rlist, _, _ = select.select([self._process.stderr], (), (), 0.05)
            self._process.send_signal(signal.SIGINT)
            signals_sent += 1
            if signals_sent > 200:
                self._process.kill()
                self.fail('reader process failed to handle our signals.')
        signal_line = self._process.stderr.readline()
        if signal_line != b'$\n':
            self.fail_with_process_info('while awaiting signal', stderr=
                signal_line)
        stdout, stderr = self._process.communicate(input=b'\n')
        if self._process.returncode:
            self.fail_with_process_info('exited rc=%d' % self._process.
                returncode, stdout, stderr, communicate=False)
    _READING_CODE_TEMPLATE = (
        'got = infile.{read_method_name}() ;expected = {expected!r} ;assert got == expected, ("{read_method_name} returned wrong data.\\n""got data %r\\nexpected %r" % (got, expected))'
        )

    def test_readline(self):
        """readline() must handle signals and not lose data."""
        self._test_reading(data_to_write=b'hello, world!',
            read_and_verify_code=self._READING_CODE_TEMPLATE.format(
            read_method_name='readline', expected=b'hello, world!\n'))

    def test_readlines(self):
        """readlines() must handle signals and not lose data."""
        self._test_reading(data_to_write=b'hello\nworld!',
            read_and_verify_code=self._READING_CODE_TEMPLATE.format(
            read_method_name='readlines', expected=[b'hello\n', b'world!\n']))

    def test_readall(self):
        """readall() must handle signals and not lose data."""
        self._test_reading(data_to_write=b'hello\nworld!',
            read_and_verify_code=self._READING_CODE_TEMPLATE.format(
            read_method_name='readall', expected=b'hello\nworld!\n'))
        self._test_reading(data_to_write=b'hello\nworld!',
            read_and_verify_code=self._READING_CODE_TEMPLATE.format(
            read_method_name='read', expected=b'hello\nworld!\n'))


class CTestFileIOSignalInterrupt(TestFileIOSignalInterrupt, unittest.TestCase):
    modname = '_io'


class PyTestFileIOSignalInterrupt(TestFileIOSignalInterrupt, unittest.TestCase
    ):
    modname = '_pyio'


class TestBufferedIOSignalInterrupt(TestFileIOSignalInterrupt):

    def _generate_infile_setup_code(self):
        """Returns the infile = ... line of code to make a BufferedReader."""
        return (
            'import %s as io ;infile = io.open(sys.stdin.fileno(), "rb") ;assert isinstance(infile, io.BufferedReader)'
             % self.modname)

    def test_readall(self):
        """BufferedReader.read() must handle signals and not lose data."""
        self._test_reading(data_to_write=b'hello\nworld!',
            read_and_verify_code=self._READING_CODE_TEMPLATE.format(
            read_method_name='read', expected=b'hello\nworld!\n'))


class CTestBufferedIOSignalInterrupt(TestBufferedIOSignalInterrupt,
    unittest.TestCase):
    modname = '_io'


class PyTestBufferedIOSignalInterrupt(TestBufferedIOSignalInterrupt,
    unittest.TestCase):
    modname = '_pyio'


class TestTextIOSignalInterrupt(TestFileIOSignalInterrupt):

    def _generate_infile_setup_code(self):
        """Returns the infile = ... line of code to make a TextIOWrapper."""
        return (
            'import %s as io ;infile = io.open(sys.stdin.fileno(), "rt", newline=None) ;assert isinstance(infile, io.TextIOWrapper)'
             % self.modname)

    def test_readline(self):
        """readline() must handle signals and not lose data."""
        self._test_reading(data_to_write=b'hello, world!',
            read_and_verify_code=self._READING_CODE_TEMPLATE.format(
            read_method_name='readline', expected='hello, world!\n'))

    def test_readlines(self):
        """readlines() must handle signals and not lose data."""
        self._test_reading(data_to_write=b'hello\r\nworld!',
            read_and_verify_code=self._READING_CODE_TEMPLATE.format(
            read_method_name='readlines', expected=['hello\n', 'world!\n']))

    def test_readall(self):
        """read() must handle signals and not lose data."""
        self._test_reading(data_to_write=b'hello\nworld!',
            read_and_verify_code=self._READING_CODE_TEMPLATE.format(
            read_method_name='read', expected='hello\nworld!\n'))


class CTestTextIOSignalInterrupt(TestTextIOSignalInterrupt, unittest.TestCase):
    modname = '_io'


class PyTestTextIOSignalInterrupt(TestTextIOSignalInterrupt, unittest.TestCase
    ):
    modname = '_pyio'


if __name__ == '__main__':
    unittest.main()
