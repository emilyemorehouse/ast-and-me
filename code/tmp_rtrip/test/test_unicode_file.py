import os, glob, time, shutil
import unicodedata
import unittest
from test.support import run_unittest, rmtree, change_cwd, TESTFN_ENCODING, TESTFN_UNICODE, TESTFN_UNENCODABLE, create_empty_file
if not os.path.supports_unicode_filenames:
    try:
        TESTFN_UNICODE.encode(TESTFN_ENCODING)
    except (UnicodeError, TypeError):
        raise unittest.SkipTest(
            'No Unicode filesystem semantics on this platform.')


def remove_if_exists(filename):
    if os.path.exists(filename):
        os.unlink(filename)


class TestUnicodeFiles(unittest.TestCase):

    def _do_single(self, filename):
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue(os.access(filename, os.R_OK))
        self.assertTrue(os.path.exists(os.path.abspath(filename)))
        self.assertTrue(os.path.isfile(os.path.abspath(filename)))
        self.assertTrue(os.access(os.path.abspath(filename), os.R_OK))
        os.chmod(filename, 511)
        os.utime(filename, None)
        os.utime(filename, (time.time(), time.time()))
        self._do_copyish(filename, filename)
        self.assertTrue(os.path.abspath(filename) == os.path.abspath(glob.
            glob(filename)[0]))
        path, base = os.path.split(os.path.abspath(filename))
        file_list = os.listdir(path)
        base = unicodedata.normalize('NFD', base)
        file_list = [unicodedata.normalize('NFD', f) for f in file_list]
        self.assertIn(base, file_list)

    def _do_copyish(self, filename1, filename2):
        self.assertTrue(os.path.isfile(filename1))
        os.rename(filename1, filename2 + '.new')
        self.assertFalse(os.path.isfile(filename2))
        self.assertTrue(os.path.isfile(filename1 + '.new'))
        os.rename(filename1 + '.new', filename2)
        self.assertFalse(os.path.isfile(filename1 + '.new'))
        self.assertTrue(os.path.isfile(filename2))
        shutil.copy(filename1, filename2 + '.new')
        os.unlink(filename1 + '.new')
        shutil.move(filename1, filename2 + '.new')
        self.assertFalse(os.path.exists(filename2))
        self.assertTrue(os.path.exists(filename1 + '.new'))
        shutil.move(filename1 + '.new', filename2)
        self.assertFalse(os.path.exists(filename2 + '.new'))
        self.assertTrue(os.path.exists(filename1))
        shutil.copy2(filename1, filename2 + '.new')
        self.assertTrue(os.path.isfile(filename1 + '.new'))
        os.unlink(filename1 + '.new')
        self.assertFalse(os.path.exists(filename2 + '.new'))

    def _do_directory(self, make_name, chdir_name):
        if os.path.isdir(make_name):
            rmtree(make_name)
        os.mkdir(make_name)
        try:
            with change_cwd(chdir_name):
                cwd_result = os.getcwd()
                name_result = make_name
                cwd_result = unicodedata.normalize('NFD', cwd_result)
                name_result = unicodedata.normalize('NFD', name_result)
                self.assertEqual(os.path.basename(cwd_result), name_result)
        finally:
            os.rmdir(make_name)

    def _test_single(self, filename):
        remove_if_exists(filename)
        create_empty_file(filename)
        try:
            self._do_single(filename)
        finally:
            os.unlink(filename)
        self.assertTrue(not os.path.exists(filename))
        f = os.open(filename, os.O_CREAT)
        os.close(f)
        try:
            self._do_single(filename)
        finally:
            os.unlink(filename)

    def test_single_files(self):
        self._test_single(TESTFN_UNICODE)
        if TESTFN_UNENCODABLE is not None:
            self._test_single(TESTFN_UNENCODABLE)

    def test_directories(self):
        ext = '.dir'
        self._do_directory(TESTFN_UNICODE + ext, TESTFN_UNICODE + ext)
        if TESTFN_UNENCODABLE is not None:
            self._do_directory(TESTFN_UNENCODABLE + ext, TESTFN_UNENCODABLE +
                ext)


def test_main():
    run_unittest(__name__)


if __name__ == '__main__':
    test_main()
