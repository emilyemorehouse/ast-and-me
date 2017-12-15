import os
import sys
import unittest
import warnings
from unicodedata import normalize
from test import support
filenames = ['1_abc', '2_ascii', '3_Grüß-Gott', '4_Γειά-σας',
    '5_Здравствуйте', '6_にぽん', '7_השקצץס', '8_曨曩曫', '9_曨שんдΓß', '10_΅´']
if sys.platform != 'darwin':
    filenames.extend(['11_΅ϓϔ', '12_΅ϓϔ', '13_ ̈́ΎΫ', '14_ẛ῁῍῎῏῝῞῟῭',
        '15_΅´𣏕', '16_\u2000\u2000\u2000A', '17_\u2001\u2001\u2001A',
        '18_\u2003\u2003\u2003A', '19_   A'])
if not os.path.supports_unicode_filenames:
    fsencoding = sys.getfilesystemencoding()
    try:
        for name in filenames:
            name.encode(fsencoding)
    except UnicodeEncodeError:
        raise unittest.SkipTest(
            'only NT+ and systems with Unicode-friendly filesystem encoding')


class UnicodeFileTests(unittest.TestCase):
    files = set(filenames)
    normal_form = None

    def setUp(self):
        try:
            os.mkdir(support.TESTFN)
        except FileExistsError:
            pass
        self.addCleanup(support.rmtree, support.TESTFN)
        files = set()
        for name in self.files:
            name = os.path.join(support.TESTFN, self.norm(name))
            with open(name, 'wb') as f:
                f.write((name + '\n').encode('utf-8'))
            os.stat(name)
            files.add(name)
        self.files = files

    def norm(self, s):
        if self.normal_form:
            return normalize(self.normal_form, s)
        return s

    def _apply_failure(self, fn, filename, expected_exception=
        FileNotFoundError, check_filename=True):
        with self.assertRaises(expected_exception) as c:
            fn(filename)
        exc_filename = c.exception.filename
        if check_filename:
            self.assertEqual(exc_filename, filename, 
                "Function '%s(%a) failed with bad filename in the exception: %a"
                 % (fn.__name__, filename, exc_filename))

    def test_failures(self):
        for name in self.files:
            name = 'not_' + name
            self._apply_failure(open, name)
            self._apply_failure(os.stat, name)
            self._apply_failure(os.chdir, name)
            self._apply_failure(os.rmdir, name)
            self._apply_failure(os.remove, name)
            self._apply_failure(os.listdir, name)
    if sys.platform == 'win32':
        _listdir_failure = NotADirectoryError, FileNotFoundError
    else:
        _listdir_failure = NotADirectoryError

    def test_open(self):
        for name in self.files:
            f = open(name, 'wb')
            f.write((name + '\n').encode('utf-8'))
            f.close()
            os.stat(name)
            self._apply_failure(os.listdir, name, self._listdir_failure)

    @unittest.skipIf(sys.platform == 'darwin', 'irrelevant test on Mac OS X')
    def test_normalize(self):
        files = set(self.files)
        others = set()
        for nf in set(['NFC', 'NFD', 'NFKC', 'NFKD']):
            others |= set(normalize(nf, file) for file in files)
        others -= files
        for name in others:
            self._apply_failure(open, name)
            self._apply_failure(os.stat, name)
            self._apply_failure(os.chdir, name)
            self._apply_failure(os.rmdir, name)
            self._apply_failure(os.remove, name)
            self._apply_failure(os.listdir, name)

    @unittest.skipIf(sys.platform == 'darwin', 'irrelevant test on Mac OS X')
    def test_listdir(self):
        sf0 = set(self.files)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            f1 = os.listdir(support.TESTFN.encode(sys.getfilesystemencoding()))
        f2 = os.listdir(support.TESTFN)
        sf2 = set(os.path.join(support.TESTFN, f) for f in f2)
        self.assertEqual(sf0, sf2, '%a != %a' % (sf0, sf2))
        self.assertEqual(len(f1), len(f2))

    def test_rename(self):
        for name in self.files:
            os.rename(name, 'tmp')
            os.rename('tmp', name)

    def test_directory(self):
        dirname = os.path.join(support.TESTFN, 'Grüß-曨曩曫')
        filename = 'ß-曨曩曫'
        with support.temp_cwd(dirname):
            with open(filename, 'wb') as f:
                f.write((filename + '\n').encode('utf-8'))
            os.access(filename, os.R_OK)
            os.remove(filename)


class UnicodeNFCFileTests(UnicodeFileTests):
    normal_form = 'NFC'


class UnicodeNFDFileTests(UnicodeFileTests):
    normal_form = 'NFD'


class UnicodeNFKCFileTests(UnicodeFileTests):
    normal_form = 'NFKC'


class UnicodeNFKDFileTests(UnicodeFileTests):
    normal_form = 'NFKD'


def test_main():
    support.run_unittest(UnicodeFileTests, UnicodeNFCFileTests,
        UnicodeNFDFileTests, UnicodeNFKCFileTests, UnicodeNFKDFileTests)


if __name__ == '__main__':
    test_main()
