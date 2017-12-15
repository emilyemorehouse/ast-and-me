import io
import locale
import mimetypes
import sys
import unittest
from test import support
mimetypes.knownfiles = []
mimetypes.inited = False
mimetypes._default_mime_types()


class MimeTypesTestCase(unittest.TestCase):

    def setUp(self):
        self.db = mimetypes.MimeTypes()

    def test_default_data(self):
        eq = self.assertEqual
        eq(self.db.guess_type('foo.html'), ('text/html', None))
        eq(self.db.guess_type('foo.tgz'), ('application/x-tar', 'gzip'))
        eq(self.db.guess_type('foo.tar.gz'), ('application/x-tar', 'gzip'))
        eq(self.db.guess_type('foo.tar.Z'), ('application/x-tar', 'compress'))
        eq(self.db.guess_type('foo.tar.bz2'), ('application/x-tar', 'bzip2'))
        eq(self.db.guess_type('foo.tar.xz'), ('application/x-tar', 'xz'))

    def test_data_urls(self):
        eq = self.assertEqual
        guess_type = self.db.guess_type
        eq(guess_type('data:,thisIsTextPlain'), ('text/plain', None))
        eq(guess_type('data:;base64,thisIsTextPlain'), ('text/plain', None))
        eq(guess_type('data:text/x-foo,thisIsTextXFoo'), ('text/x-foo', None))

    def test_file_parsing(self):
        eq = self.assertEqual
        sio = io.StringIO('x-application/x-unittest pyunit\n')
        self.db.readfp(sio)
        eq(self.db.guess_type('foo.pyunit'), ('x-application/x-unittest', None)
            )
        eq(self.db.guess_extension('x-application/x-unittest'), '.pyunit')

    def test_non_standard_types(self):
        eq = self.assertEqual
        eq(self.db.guess_type('foo.xul', strict=True), (None, None))
        eq(self.db.guess_extension('image/jpg', strict=True), None)
        eq(self.db.guess_type('foo.xul', strict=False), ('text/xul', None))
        eq(self.db.guess_extension('image/jpg', strict=False), '.jpg')

    def test_guess_all_types(self):
        eq = self.assertEqual
        unless = self.assertTrue
        all = set(self.db.guess_all_extensions('text/plain', strict=True))
        unless(all >= set(['.bat', '.c', '.h', '.ksh', '.pl', '.txt']))
        all = self.db.guess_all_extensions('image/jpg', strict=False)
        all.sort()
        eq(all, ['.jpg'])
        all = self.db.guess_all_extensions('image/jpg', strict=True)
        eq(all, [])

    def test_encoding(self):
        getpreferredencoding = locale.getpreferredencoding
        self.addCleanup(setattr, locale, 'getpreferredencoding',
            getpreferredencoding)
        locale.getpreferredencoding = lambda : 'ascii'
        filename = support.findfile('mime.types')
        mimes = mimetypes.MimeTypes([filename])
        exts = mimes.guess_all_extensions('application/vnd.geocube+xml',
            strict=True)
        self.assertEqual(exts, ['.g3', '.g³'])


@unittest.skipUnless(sys.platform.startswith('win'), 'Windows only')
class Win32MimeTypesTestCase(unittest.TestCase):

    def setUp(self):
        self.original_types_map = mimetypes.types_map.copy()
        mimetypes.types_map.clear()
        mimetypes.init()
        self.db = mimetypes.MimeTypes()

    def tearDown(self):
        mimetypes.types_map.clear()
        mimetypes.types_map.update(self.original_types_map)

    def test_registry_parsing(self):
        eq = self.assertEqual
        eq(self.db.guess_type('foo.txt'), ('text/plain', None))
        eq(self.db.guess_type('image.jpg'), ('image/jpeg', None))
        eq(self.db.guess_type('image.png'), ('image/png', None))


class MiscTestCase(unittest.TestCase):

    def test__all__(self):
        support.check__all__(self, mimetypes)


if __name__ == '__main__':
    unittest.main()
