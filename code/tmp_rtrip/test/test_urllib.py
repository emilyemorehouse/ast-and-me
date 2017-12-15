"""Regression tests for what was in Python 2's "urllib" module"""
import urllib.parse
import urllib.request
import urllib.error
import http.client
import email.message
import io
import unittest
from unittest.mock import patch
from test import support
import os
try:
    import ssl
except ImportError:
    ssl = None
import sys
import tempfile
from nturl2path import url2pathname, pathname2url
from base64 import b64encode
import collections


def hexescape(char):
    """Escape char as RFC 2396 specifies"""
    hex_repr = hex(ord(char))[2:].upper()
    if len(hex_repr) == 1:
        hex_repr = '0%s' % hex_repr
    return '%' + hex_repr


_urlopener = None


def urlopen(url, data=None, proxies=None):
    """urlopen(url [, data]) -> open file-like object"""
    global _urlopener
    if proxies is not None:
        opener = urllib.request.FancyURLopener(proxies=proxies)
    elif not _urlopener:
        opener = FancyURLopener()
        _urlopener = opener
    else:
        opener = _urlopener
    if data is None:
        return opener.open(url)
    else:
        return opener.open(url, data)


def FancyURLopener():
    with support.check_warnings((
        'FancyURLopener style of invoking requests is deprecated.',
        DeprecationWarning)):
        return urllib.request.FancyURLopener()


def fakehttp(fakedata):


    class FakeSocket(io.BytesIO):
        io_refs = 1

        def sendall(self, data):
            FakeHTTPConnection.buf = data

        def makefile(self, *args, **kwds):
            self.io_refs += 1
            return self

        def read(self, amt=None):
            if self.closed:
                return b''
            return io.BytesIO.read(self, amt)

        def readline(self, length=None):
            if self.closed:
                return b''
            return io.BytesIO.readline(self, length)

        def close(self):
            self.io_refs -= 1
            if self.io_refs == 0:
                io.BytesIO.close(self)


    class FakeHTTPConnection(http.client.HTTPConnection):
        buf = None

        def connect(self):
            self.sock = FakeSocket(self.fakedata)
            type(self).fakesock = self.sock
    FakeHTTPConnection.fakedata = fakedata
    return FakeHTTPConnection


class FakeHTTPMixin(object):

    def fakehttp(self, fakedata):
        self._connection_class = http.client.HTTPConnection
        http.client.HTTPConnection = fakehttp(fakedata)

    def unfakehttp(self):
        http.client.HTTPConnection = self._connection_class


class FakeFTPMixin(object):

    def fakeftp(self):


        class FakeFtpWrapper(object):

            def __init__(self, user, passwd, host, port, dirs, timeout=None,
                persistent=True):
                pass

            def retrfile(self, file, type):
                return io.BytesIO(), 0

            def close(self):
                pass
        self._ftpwrapper_class = urllib.request.ftpwrapper
        urllib.request.ftpwrapper = FakeFtpWrapper

    def unfakeftp(self):
        urllib.request.ftpwrapper = self._ftpwrapper_class


class urlopen_FileTests(unittest.TestCase):
    """Test urlopen() opening a temporary file.

    Try to test as much functionality as possible so as to cut down on reliance
    on connecting to the Net for testing.

    """

    def setUp(self):
        self.text = bytes('test_urllib: %s\n' % self.__class__.__name__,
            'ascii')
        f = open(support.TESTFN, 'wb')
        try:
            f.write(self.text)
        finally:
            f.close()
        self.pathname = support.TESTFN
        self.returned_obj = urlopen('file:%s' % self.pathname)

    def tearDown(self):
        """Shut down the open object"""
        self.returned_obj.close()
        os.remove(support.TESTFN)

    def test_interface(self):
        for attr in ('read', 'readline', 'readlines', 'fileno', 'close',
            'info', 'geturl', 'getcode', '__iter__'):
            self.assertTrue(hasattr(self.returned_obj, attr), 
                'object returned by urlopen() lacks %s attribute' % attr)

    def test_read(self):
        self.assertEqual(self.text, self.returned_obj.read())

    def test_readline(self):
        self.assertEqual(self.text, self.returned_obj.readline())
        self.assertEqual(b'', self.returned_obj.readline(),
            'calling readline() after exhausting the file did not return an empty string'
            )

    def test_readlines(self):
        lines_list = self.returned_obj.readlines()
        self.assertEqual(len(lines_list), 1,
            'readlines() returned the wrong number of lines')
        self.assertEqual(lines_list[0], self.text,
            'readlines() returned improper text')

    def test_fileno(self):
        file_num = self.returned_obj.fileno()
        self.assertIsInstance(file_num, int, 'fileno() did not return an int')
        self.assertEqual(os.read(file_num, len(self.text)), self.text,
            'Reading on the file descriptor returned by fileno() did not return the expected text'
            )

    def test_close(self):
        self.returned_obj.close()

    def test_info(self):
        self.assertIsInstance(self.returned_obj.info(), email.message.Message)

    def test_geturl(self):
        self.assertEqual(self.returned_obj.geturl(), self.pathname)

    def test_getcode(self):
        self.assertIsNone(self.returned_obj.getcode())

    def test_iter(self):
        for line in self.returned_obj:
            self.assertEqual(line, self.text)

    def test_relativelocalfile(self):
        self.assertRaises(ValueError, urllib.request.urlopen, './' + self.
            pathname)


class ProxyTests(unittest.TestCase):

    def setUp(self):
        self.env = support.EnvironmentVarGuard()
        for k in list(os.environ):
            if 'proxy' in k.lower():
                self.env.unset(k)

    def tearDown(self):
        self.env.__exit__()
        del self.env

    def test_getproxies_environment_keep_no_proxies(self):
        self.env.set('NO_PROXY', 'localhost')
        proxies = urllib.request.getproxies_environment()
        self.assertEqual('localhost', proxies['no'])
        self.env.set('NO_PROXY',
            'localhost, anotherdomain.com, newdomain.com:1234')
        self.assertTrue(urllib.request.proxy_bypass_environment(
            'anotherdomain.com'))
        self.assertTrue(urllib.request.proxy_bypass_environment(
            'anotherdomain.com:8888'))
        self.assertTrue(urllib.request.proxy_bypass_environment(
            'newdomain.com:1234'))

    def test_proxy_cgi_ignore(self):
        try:
            self.env.set('HTTP_PROXY', 'http://somewhere:3128')
            proxies = urllib.request.getproxies_environment()
            self.assertEqual('http://somewhere:3128', proxies['http'])
            self.env.set('REQUEST_METHOD', 'GET')
            proxies = urllib.request.getproxies_environment()
            self.assertNotIn('http', proxies)
        finally:
            self.env.unset('REQUEST_METHOD')
            self.env.unset('HTTP_PROXY')

    def test_proxy_bypass_environment_host_match(self):
        bypass = urllib.request.proxy_bypass_environment
        self.env.set('NO_PROXY',
            'localhost, anotherdomain.com, newdomain.com:1234, .d.o.t')
        self.assertTrue(bypass('localhost'))
        self.assertTrue(bypass('LocalHost'))
        self.assertTrue(bypass('LOCALHOST'))
        self.assertTrue(bypass('newdomain.com:1234'))
        self.assertTrue(bypass('foo.d.o.t'))
        self.assertTrue(bypass('anotherdomain.com:8888'))
        self.assertTrue(bypass('www.newdomain.com:1234'))
        self.assertFalse(bypass('prelocalhost'))
        self.assertFalse(bypass('newdomain.com'))
        self.assertFalse(bypass('newdomain.com:1235'))


class ProxyTests_withOrderedEnv(unittest.TestCase):

    def setUp(self):
        self._saved_env = os.environ
        os.environ = collections.OrderedDict()

    def tearDown(self):
        os.environ = self._saved_env

    def test_getproxies_environment_prefer_lowercase(self):
        os.environ['no_proxy'] = ''
        os.environ['No_Proxy'] = 'localhost'
        self.assertFalse(urllib.request.proxy_bypass_environment('localhost'))
        self.assertFalse(urllib.request.proxy_bypass_environment('arbitrary'))
        os.environ['http_proxy'] = ''
        os.environ['HTTP_PROXY'] = 'http://somewhere:3128'
        proxies = urllib.request.getproxies_environment()
        self.assertEqual({}, proxies)
        os.environ['no_proxy'] = 'localhost, noproxy.com, my.proxy:1234'
        os.environ['No_Proxy'] = 'xyz.com'
        self.assertTrue(urllib.request.proxy_bypass_environment('localhost'))
        self.assertTrue(urllib.request.proxy_bypass_environment(
            'noproxy.com:5678'))
        self.assertTrue(urllib.request.proxy_bypass_environment(
            'my.proxy:1234'))
        self.assertFalse(urllib.request.proxy_bypass_environment('my.proxy'))
        self.assertFalse(urllib.request.proxy_bypass_environment('arbitrary'))
        os.environ['http_proxy'] = 'http://somewhere:3128'
        os.environ['Http_Proxy'] = 'http://somewhereelse:3128'
        proxies = urllib.request.getproxies_environment()
        self.assertEqual('http://somewhere:3128', proxies['http'])


class urlopen_HttpTests(unittest.TestCase, FakeHTTPMixin, FakeFTPMixin):
    """Test urlopen() opening a fake http connection."""

    def check_read(self, ver):
        self.fakehttp(b'HTTP/' + ver + b' 200 OK\r\n\r\nHello!')
        try:
            fp = urlopen('http://python.org/')
            self.assertEqual(fp.readline(), b'Hello!')
            self.assertEqual(fp.readline(), b'')
            self.assertEqual(fp.geturl(), 'http://python.org/')
            self.assertEqual(fp.getcode(), 200)
        finally:
            self.unfakehttp()

    def test_url_fragment(self):
        url = 'http://docs.python.org/library/urllib.html#OK'
        self.fakehttp(b'HTTP/1.1 200 OK\r\n\r\nHello!')
        try:
            fp = urllib.request.urlopen(url)
            self.assertEqual(fp.geturl(), url)
        finally:
            self.unfakehttp()

    def test_willclose(self):
        self.fakehttp(b'HTTP/1.1 200 OK\r\n\r\nHello!')
        try:
            resp = urlopen('http://www.python.org')
            self.assertTrue(resp.fp.will_close)
        finally:
            self.unfakehttp()

    def test_read_0_9(self):
        self.check_read(b'0.9')

    def test_read_1_0(self):
        self.check_read(b'1.0')

    def test_read_1_1(self):
        self.check_read(b'1.1')

    def test_read_bogus(self):
        self.fakehttp(
            b'HTTP/1.1 401 Authentication Required\nDate: Wed, 02 Jan 2008 03:03:54 GMT\nServer: Apache/1.3.33 (Debian GNU/Linux) mod_ssl/2.8.22 OpenSSL/0.9.7e\nConnection: close\nContent-Type: text/html; charset=iso-8859-1\n'
            )
        try:
            self.assertRaises(OSError, urlopen, 'http://python.org/')
        finally:
            self.unfakehttp()

    def test_invalid_redirect(self):
        self.fakehttp(
            b'HTTP/1.1 302 Found\nDate: Wed, 02 Jan 2008 03:03:54 GMT\nServer: Apache/1.3.33 (Debian GNU/Linux) mod_ssl/2.8.22 OpenSSL/0.9.7e\nLocation: file://guidocomputer.athome.com:/python/license\nConnection: close\nContent-Type: text/html; charset=iso-8859-1\n'
            )
        try:
            msg = "Redirection to url 'file:"
            with self.assertRaisesRegex(urllib.error.HTTPError, msg):
                urlopen('http://python.org/')
        finally:
            self.unfakehttp()

    def test_redirect_limit_independent(self):
        for i in range(FancyURLopener().maxtries):
            self.fakehttp(
                b'HTTP/1.1 302 Found\nLocation: file://guidocomputer.athome.com:/python/license\nConnection: close\n'
                )
            try:
                self.assertRaises(urllib.error.HTTPError, urlopen,
                    'http://something')
            finally:
                self.unfakehttp()

    def test_empty_socket(self):
        self.fakehttp(b'')
        try:
            self.assertRaises(OSError, urlopen, 'http://something')
        finally:
            self.unfakehttp()

    def test_missing_localfile(self):
        with self.assertRaises(urllib.error.URLError) as e:
            urlopen('file://localhost/a/file/which/doesnot/exists.py')
        self.assertTrue(e.exception.filename)
        self.assertTrue(e.exception.reason)

    def test_file_notexists(self):
        fd, tmp_file = tempfile.mkstemp()
        tmp_fileurl = 'file://localhost/' + tmp_file.replace(os.path.sep, '/')
        try:
            self.assertTrue(os.path.exists(tmp_file))
            with urlopen(tmp_fileurl) as fobj:
                self.assertTrue(fobj)
        finally:
            os.close(fd)
            os.unlink(tmp_file)
        self.assertFalse(os.path.exists(tmp_file))
        with self.assertRaises(urllib.error.URLError):
            urlopen(tmp_fileurl)

    def test_ftp_nohost(self):
        test_ftp_url = 'ftp:///path'
        with self.assertRaises(urllib.error.URLError) as e:
            urlopen(test_ftp_url)
        self.assertFalse(e.exception.filename)
        self.assertTrue(e.exception.reason)

    def test_ftp_nonexisting(self):
        with self.assertRaises(urllib.error.URLError) as e:
            urlopen('ftp://localhost/a/file/which/doesnot/exists.py')
        self.assertFalse(e.exception.filename)
        self.assertTrue(e.exception.reason)

    @patch.object(urllib.request, 'MAXFTPCACHE', 0)
    def test_ftp_cache_pruning(self):
        self.fakeftp()
        try:
            urllib.request.ftpcache['test'] = urllib.request.ftpwrapper('user',
                'pass', 'localhost', 21, [])
            urlopen('ftp://localhost')
        finally:
            self.unfakeftp()

    def test_userpass_inurl(self):
        self.fakehttp(b'HTTP/1.0 200 OK\r\n\r\nHello!')
        try:
            fp = urlopen('http://user:pass@python.org/')
            self.assertEqual(fp.readline(), b'Hello!')
            self.assertEqual(fp.readline(), b'')
            self.assertEqual(fp.geturl(), 'http://user:pass@python.org/')
            self.assertEqual(fp.getcode(), 200)
        finally:
            self.unfakehttp()

    def test_userpass_inurl_w_spaces(self):
        self.fakehttp(b'HTTP/1.0 200 OK\r\n\r\nHello!')
        try:
            userpass = 'a b:c d'
            url = 'http://{}@python.org/'.format(userpass)
            fakehttp_wrapper = http.client.HTTPConnection
            authorization = 'Authorization: Basic %s\r\n' % b64encode(userpass
                .encode('ASCII')).decode('ASCII')
            fp = urlopen(url)
            self.assertIn(authorization, fakehttp_wrapper.buf.decode('UTF-8'))
            self.assertEqual(fp.readline(), b'Hello!')
            self.assertEqual(fp.readline(), b'')
            self.assertNotEqual(fp.geturl(), url)
            self.assertEqual(fp.getcode(), 200)
        finally:
            self.unfakehttp()

    def test_URLopener_deprecation(self):
        with support.check_warnings(('', DeprecationWarning)):
            urllib.request.URLopener()

    @unittest.skipUnless(ssl, 'ssl module required')
    def test_cafile_and_context(self):
        context = ssl.create_default_context()
        with support.check_warnings(('', DeprecationWarning)):
            with self.assertRaises(ValueError):
                urllib.request.urlopen('https://localhost', cafile=
                    '/nonexistent/path', context=context)


class urlopen_DataTests(unittest.TestCase):
    """Test urlopen() opening a data URL."""

    def setUp(self):
        self.text = 'test data URLs :;,%=& ö Ä '
        self.image = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x01\x08\x02\x00\x00\x00{@\xe8\xdd\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x0fIDAT\x08\xd7c```\xf8\xff\xff?\x00\x06\x01\x02\xfe\no/\x1e\x00\x00\x00\x00IEND\xaeB`\x82'
            )
        self.text_url = (
            'data:text/plain;charset=UTF-8,test%20data%20URLs%20%3A%3B%2C%25%3D%26%20%C3%B6%20%C3%84%20'
            )
        self.text_url_base64 = (
            'data:text/plain;charset=ISO-8859-1;base64,dGVzdCBkYXRhIFVSTHMgOjssJT0mIPYgxCA%3D'
            )
        self.image_url = """data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAIAAAABCAIAAAB7
QOjdAAAAAXNSR0IArs4c6QAAAA9JREFUCNdj%0AYGBg%2BP//PwAGAQL%2BCm8 vHgAAAABJRU5ErkJggg%3D%3D%0A%20"""
        self.text_url_resp = urllib.request.urlopen(self.text_url)
        self.text_url_base64_resp = urllib.request.urlopen(self.text_url_base64
            )
        self.image_url_resp = urllib.request.urlopen(self.image_url)

    def test_interface(self):
        for attr in ('read', 'readline', 'readlines', 'close', 'info',
            'geturl', 'getcode', '__iter__'):
            self.assertTrue(hasattr(self.text_url_resp, attr), 
                'object returned by urlopen() lacks %s attribute' % attr)

    def test_info(self):
        self.assertIsInstance(self.text_url_resp.info(), email.message.Message)
        self.assertEqual(self.text_url_base64_resp.info().get_params(), [(
            'text/plain', ''), ('charset', 'ISO-8859-1')])
        self.assertEqual(self.image_url_resp.info()['content-length'], str(
            len(self.image)))
        self.assertEqual(urllib.request.urlopen('data:,').info().get_params
            (), [('text/plain', ''), ('charset', 'US-ASCII')])

    def test_geturl(self):
        self.assertEqual(self.text_url_resp.geturl(), self.text_url)
        self.assertEqual(self.text_url_base64_resp.geturl(), self.
            text_url_base64)
        self.assertEqual(self.image_url_resp.geturl(), self.image_url)

    def test_read_text(self):
        self.assertEqual(self.text_url_resp.read().decode(dict(self.
            text_url_resp.info().get_params())['charset']), self.text)

    def test_read_text_base64(self):
        self.assertEqual(self.text_url_base64_resp.read().decode(dict(self.
            text_url_base64_resp.info().get_params())['charset']), self.text)

    def test_read_image(self):
        self.assertEqual(self.image_url_resp.read(), self.image)

    def test_missing_comma(self):
        self.assertRaises(ValueError, urllib.request.urlopen, 'data:text/plain'
            )

    def test_invalid_base64_data(self):
        self.assertRaises(ValueError, urllib.request.urlopen,
            'data:;base64,Cg=')


class urlretrieve_FileTests(unittest.TestCase):
    """Test urllib.urlretrieve() on local files"""

    def setUp(self):
        self.tempFiles = []
        self.registerFileForCleanUp(support.TESTFN)
        self.text = b'testing urllib.urlretrieve'
        try:
            FILE = open(support.TESTFN, 'wb')
            FILE.write(self.text)
            FILE.close()
        finally:
            try:
                FILE.close()
            except:
                pass

    def tearDown(self):
        for each in self.tempFiles:
            try:
                os.remove(each)
            except:
                pass

    def constructLocalFileUrl(self, filePath):
        filePath = os.path.abspath(filePath)
        try:
            filePath.encode('utf-8')
        except UnicodeEncodeError:
            raise unittest.SkipTest('filePath is not encodable to utf8')
        return 'file://%s' % urllib.request.pathname2url(filePath)

    def createNewTempFile(self, data=b''):
        """Creates a new temporary file containing the specified data,
        registers the file for deletion during the test fixture tear down, and
        returns the absolute path of the file."""
        newFd, newFilePath = tempfile.mkstemp()
        try:
            self.registerFileForCleanUp(newFilePath)
            newFile = os.fdopen(newFd, 'wb')
            newFile.write(data)
            newFile.close()
        finally:
            try:
                newFile.close()
            except:
                pass
        return newFilePath

    def registerFileForCleanUp(self, fileName):
        self.tempFiles.append(fileName)

    def test_basic(self):
        result = urllib.request.urlretrieve('file:%s' % support.TESTFN)
        self.assertEqual(result[0], support.TESTFN)
        self.assertIsInstance(result[1], email.message.Message,
            'did not get an email.message.Message instance as second returned value'
            )

    def test_copy(self):
        second_temp = '%s.2' % support.TESTFN
        self.registerFileForCleanUp(second_temp)
        result = urllib.request.urlretrieve(self.constructLocalFileUrl(
            support.TESTFN), second_temp)
        self.assertEqual(second_temp, result[0])
        self.assertTrue(os.path.exists(second_temp),
            'copy of the file was not made')
        FILE = open(second_temp, 'rb')
        try:
            text = FILE.read()
            FILE.close()
        finally:
            try:
                FILE.close()
            except:
                pass
        self.assertEqual(self.text, text)

    def test_reporthook(self):

        def hooktester(block_count, block_read_size, file_size,
            count_holder=[0]):
            self.assertIsInstance(block_count, int)
            self.assertIsInstance(block_read_size, int)
            self.assertIsInstance(file_size, int)
            self.assertEqual(block_count, count_holder[0])
            count_holder[0] = count_holder[0] + 1
        second_temp = '%s.2' % support.TESTFN
        self.registerFileForCleanUp(second_temp)
        urllib.request.urlretrieve(self.constructLocalFileUrl(support.
            TESTFN), second_temp, hooktester)

    def test_reporthook_0_bytes(self):
        report = []

        def hooktester(block_count, block_read_size, file_size, _report=report
            ):
            _report.append((block_count, block_read_size, file_size))
        srcFileName = self.createNewTempFile()
        urllib.request.urlretrieve(self.constructLocalFileUrl(srcFileName),
            support.TESTFN, hooktester)
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0][2], 0)

    def test_reporthook_5_bytes(self):
        report = []

        def hooktester(block_count, block_read_size, file_size, _report=report
            ):
            _report.append((block_count, block_read_size, file_size))
        srcFileName = self.createNewTempFile(b'x' * 5)
        urllib.request.urlretrieve(self.constructLocalFileUrl(srcFileName),
            support.TESTFN, hooktester)
        self.assertEqual(len(report), 2)
        self.assertEqual(report[0][2], 5)
        self.assertEqual(report[1][2], 5)

    def test_reporthook_8193_bytes(self):
        report = []

        def hooktester(block_count, block_read_size, file_size, _report=report
            ):
            _report.append((block_count, block_read_size, file_size))
        srcFileName = self.createNewTempFile(b'x' * 8193)
        urllib.request.urlretrieve(self.constructLocalFileUrl(srcFileName),
            support.TESTFN, hooktester)
        self.assertEqual(len(report), 3)
        self.assertEqual(report[0][2], 8193)
        self.assertEqual(report[0][1], 8192)
        self.assertEqual(report[1][1], 8192)
        self.assertEqual(report[2][1], 8192)


class urlretrieve_HttpTests(unittest.TestCase, FakeHTTPMixin):
    """Test urllib.urlretrieve() using fake http connections"""

    def test_short_content_raises_ContentTooShortError(self):
        self.fakehttp(
            b'HTTP/1.1 200 OK\nDate: Wed, 02 Jan 2008 03:03:54 GMT\nServer: Apache/1.3.33 (Debian GNU/Linux) mod_ssl/2.8.22 OpenSSL/0.9.7e\nConnection: close\nContent-Length: 100\nContent-Type: text/html; charset=iso-8859-1\n\nFF\n'
            )

        def _reporthook(par1, par2, par3):
            pass
        with self.assertRaises(urllib.error.ContentTooShortError):
            try:
                urllib.request.urlretrieve('http://example.com/',
                    reporthook=_reporthook)
            finally:
                self.unfakehttp()

    def test_short_content_raises_ContentTooShortError_without_reporthook(self
        ):
        self.fakehttp(
            b'HTTP/1.1 200 OK\nDate: Wed, 02 Jan 2008 03:03:54 GMT\nServer: Apache/1.3.33 (Debian GNU/Linux) mod_ssl/2.8.22 OpenSSL/0.9.7e\nConnection: close\nContent-Length: 100\nContent-Type: text/html; charset=iso-8859-1\n\nFF\n'
            )
        with self.assertRaises(urllib.error.ContentTooShortError):
            try:
                urllib.request.urlretrieve('http://example.com/')
            finally:
                self.unfakehttp()


class QuotingTests(unittest.TestCase):
    """Tests for urllib.quote() and urllib.quote_plus()

    According to RFC 2396 (Uniform Resource Identifiers), to escape a
    character you write it as '%' + <2 character US-ASCII hex value>.
    The Python code of ``'%' + hex(ord(<character>))[2:]`` escapes a
    character properly. Case does not matter on the hex letters.

    The various character sets specified are:

    Reserved characters : ";/?:@&=+$,"
        Have special meaning in URIs and must be escaped if not being used for
        their special meaning
    Data characters : letters, digits, and "-_.!~*'()"
        Unreserved and do not need to be escaped; can be, though, if desired
    Control characters : 0x00 - 0x1F, 0x7F
        Have no use in URIs so must be escaped
    space : 0x20
        Must be escaped
    Delimiters : '<>#%"'
        Must be escaped
    Unwise : "{}|\\^[]`"
        Must be escaped

    """

    def test_never_quote(self):
        do_not_quote = ''.join(['ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'abcdefghijklmnopqrstuvwxyz', '0123456789', '_.-'])
        result = urllib.parse.quote(do_not_quote)
        self.assertEqual(do_not_quote, result, 'using quote(): %r != %r' %
            (do_not_quote, result))
        result = urllib.parse.quote_plus(do_not_quote)
        self.assertEqual(do_not_quote, result, 
            'using quote_plus(): %r != %r' % (do_not_quote, result))

    def test_default_safe(self):
        self.assertEqual(urllib.parse.quote.__defaults__[0], '/')

    def test_safe(self):
        quote_by_default = '<>'
        result = urllib.parse.quote(quote_by_default, safe=quote_by_default)
        self.assertEqual(quote_by_default, result, 
            'using quote(): %r != %r' % (quote_by_default, result))
        result = urllib.parse.quote_plus(quote_by_default, safe=
            quote_by_default)
        self.assertEqual(quote_by_default, result, 
            'using quote_plus(): %r != %r' % (quote_by_default, result))
        result = urllib.parse.quote(quote_by_default, safe=b'<>')
        self.assertEqual(quote_by_default, result, 
            'using quote(): %r != %r' % (quote_by_default, result))
        result = urllib.parse.quote('aüb', encoding='latin-1', safe='ü')
        expect = urllib.parse.quote('aüb', encoding='latin-1', safe='')
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))
        result = urllib.parse.quote('aüb', encoding='latin-1', safe=b'\xfc')
        expect = urllib.parse.quote('aüb', encoding='latin-1', safe='')
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))

    def test_default_quoting(self):
        should_quote = [chr(num) for num in range(32)]
        should_quote.append('<>#%"{}|\\^[]`')
        should_quote.append(chr(127))
        should_quote = ''.join(should_quote)
        for char in should_quote:
            result = urllib.parse.quote(char)
            self.assertEqual(hexescape(char), result, 
                'using quote(): %s should be escaped to %s, not %s' % (char,
                hexescape(char), result))
            result = urllib.parse.quote_plus(char)
            self.assertEqual(hexescape(char), result, 
                'using quote_plus(): %s should be escapes to %s, not %s' %
                (char, hexescape(char), result))
        del should_quote
        partial_quote = 'ab[]cd'
        expected = 'ab%5B%5Dcd'
        result = urllib.parse.quote(partial_quote)
        self.assertEqual(expected, result, 'using quote(): %r != %r' % (
            expected, result))
        result = urllib.parse.quote_plus(partial_quote)
        self.assertEqual(expected, result, 'using quote_plus(): %r != %r' %
            (expected, result))

    def test_quoting_space(self):
        result = urllib.parse.quote(' ')
        self.assertEqual(result, hexescape(' '), 'using quote(): %r != %r' %
            (result, hexescape(' ')))
        result = urllib.parse.quote_plus(' ')
        self.assertEqual(result, '+', 'using quote_plus(): %r != +' % result)
        given = 'a b cd e f'
        expect = given.replace(' ', hexescape(' '))
        result = urllib.parse.quote(given)
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))
        expect = given.replace(' ', '+')
        result = urllib.parse.quote_plus(given)
        self.assertEqual(expect, result, 'using quote_plus(): %r != %r' % (
            expect, result))

    def test_quoting_plus(self):
        self.assertEqual(urllib.parse.quote_plus('alpha+beta gamma'),
            'alpha%2Bbeta+gamma')
        self.assertEqual(urllib.parse.quote_plus('alpha+beta gamma', '+'),
            'alpha+beta+gamma')
        self.assertEqual(urllib.parse.quote_plus(b'alpha+beta gamma'),
            'alpha%2Bbeta+gamma')
        self.assertEqual(urllib.parse.quote_plus('alpha+beta gamma', b'+'),
            'alpha+beta+gamma')

    def test_quote_bytes(self):
        given = b'\xa2\xd8ab\xff'
        expect = '%A2%D8ab%FF'
        result = urllib.parse.quote(given)
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))
        self.assertRaises(TypeError, urllib.parse.quote, given, encoding=
            'latin-1')
        result = urllib.parse.quote_from_bytes(given)
        self.assertEqual(expect, result, 
            'using quote_from_bytes(): %r != %r' % (expect, result))

    def test_quote_with_unicode(self):
        given = '¢Øabÿ'
        expect = '%C2%A2%C3%98ab%C3%BF'
        result = urllib.parse.quote(given)
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))
        result = urllib.parse.quote(given, encoding=None, errors=None)
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))
        given = '¢Øabÿ'
        expect = '%A2%D8ab%FF'
        result = urllib.parse.quote(given, encoding='latin-1')
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))
        given = '漢字'
        expect = '%E6%BC%A2%E5%AD%97'
        result = urllib.parse.quote(given)
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))
        given = '漢字'
        self.assertRaises(UnicodeEncodeError, urllib.parse.quote, given,
            encoding='latin-1')
        given = '漢字'
        expect = '%3F%3F'
        result = urllib.parse.quote(given, encoding='latin-1', errors='replace'
            )
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))
        given = '漢字'
        expect = '%26%2328450%3B%26%2323383%3B'
        result = urllib.parse.quote(given, encoding='latin-1', errors=
            'xmlcharrefreplace')
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))

    def test_quote_plus_with_unicode(self):
        given = '¢Ø ÿ'
        expect = '%A2%D8+%FF'
        result = urllib.parse.quote_plus(given, encoding='latin-1')
        self.assertEqual(expect, result, 'using quote_plus(): %r != %r' % (
            expect, result))
        given = 'ab漢字 cd'
        expect = 'ab%3F%3F+cd'
        result = urllib.parse.quote_plus(given, encoding='latin-1', errors=
            'replace')
        self.assertEqual(expect, result, 'using quote_plus(): %r != %r' % (
            expect, result))


class UnquotingTests(unittest.TestCase):
    """Tests for unquote() and unquote_plus()

    See the doc string for quoting_Tests for details on quoting and such.

    """

    def test_unquoting(self):
        escape_list = []
        for num in range(128):
            given = hexescape(chr(num))
            expect = chr(num)
            result = urllib.parse.unquote(given)
            self.assertEqual(expect, result, 'using unquote(): %r != %r' %
                (expect, result))
            result = urllib.parse.unquote_plus(given)
            self.assertEqual(expect, result, 
                'using unquote_plus(): %r != %r' % (expect, result))
            escape_list.append(given)
        escape_string = ''.join(escape_list)
        del escape_list
        result = urllib.parse.unquote(escape_string)
        self.assertEqual(result.count('%'), 1, 
            'using unquote(): not all characters escaped: %s' % result)
        self.assertRaises((TypeError, AttributeError), urllib.parse.unquote,
            None)
        self.assertRaises((TypeError, AttributeError), urllib.parse.unquote, ()
            )
        with support.check_warnings(('', BytesWarning), quiet=True):
            self.assertRaises((TypeError, AttributeError), urllib.parse.
                unquote, b'')

    def test_unquoting_badpercent(self):
        given = '%xab'
        expect = given
        result = urllib.parse.unquote(given)
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        given = '%x'
        expect = given
        result = urllib.parse.unquote(given)
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        given = '%'
        expect = given
        result = urllib.parse.unquote(given)
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        given = '%xab'
        expect = bytes(given, 'ascii')
        result = urllib.parse.unquote_to_bytes(given)
        self.assertEqual(expect, result, 
            'using unquote_to_bytes(): %r != %r' % (expect, result))
        given = '%x'
        expect = bytes(given, 'ascii')
        result = urllib.parse.unquote_to_bytes(given)
        self.assertEqual(expect, result, 
            'using unquote_to_bytes(): %r != %r' % (expect, result))
        given = '%'
        expect = bytes(given, 'ascii')
        result = urllib.parse.unquote_to_bytes(given)
        self.assertEqual(expect, result, 
            'using unquote_to_bytes(): %r != %r' % (expect, result))
        self.assertRaises((TypeError, AttributeError), urllib.parse.
            unquote_to_bytes, None)
        self.assertRaises((TypeError, AttributeError), urllib.parse.
            unquote_to_bytes, ())

    def test_unquoting_mixed_case(self):
        given = '%Ab%eA'
        expect = b'\xab\xea'
        result = urllib.parse.unquote_to_bytes(given)
        self.assertEqual(expect, result, 
            'using unquote_to_bytes(): %r != %r' % (expect, result))

    def test_unquoting_parts(self):
        given = 'ab%sd' % hexescape('c')
        expect = 'abcd'
        result = urllib.parse.unquote(given)
        self.assertEqual(expect, result, 'using quote(): %r != %r' % (
            expect, result))
        result = urllib.parse.unquote_plus(given)
        self.assertEqual(expect, result, 'using unquote_plus(): %r != %r' %
            (expect, result))

    def test_unquoting_plus(self):
        given = 'are+there+spaces...'
        expect = given
        result = urllib.parse.unquote(given)
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        expect = given.replace('+', ' ')
        result = urllib.parse.unquote_plus(given)
        self.assertEqual(expect, result, 'using unquote_plus(): %r != %r' %
            (expect, result))

    def test_unquote_to_bytes(self):
        given = 'br%C3%BCckner_sapporo_20050930.doc'
        expect = b'br\xc3\xbcckner_sapporo_20050930.doc'
        result = urllib.parse.unquote_to_bytes(given)
        self.assertEqual(expect, result, 
            'using unquote_to_bytes(): %r != %r' % (expect, result))
        result = urllib.parse.unquote_to_bytes('漢%C3%BC')
        expect = b'\xe6\xbc\xa2\xc3\xbc'
        self.assertEqual(expect, result, 
            'using unquote_to_bytes(): %r != %r' % (expect, result))
        given = b'%A2%D8ab%FF'
        expect = b'\xa2\xd8ab\xff'
        result = urllib.parse.unquote_to_bytes(given)
        self.assertEqual(expect, result, 
            'using unquote_to_bytes(): %r != %r' % (expect, result))
        given = b'%A2\xd8ab%FF'
        expect = b'\xa2\xd8ab\xff'
        result = urllib.parse.unquote_to_bytes(given)
        self.assertEqual(expect, result, 
            'using unquote_to_bytes(): %r != %r' % (expect, result))

    def test_unquote_with_unicode(self):
        given = 'br%C3%BCckner_sapporo_20050930.doc'
        expect = 'brückner_sapporo_20050930.doc'
        result = urllib.parse.unquote(given)
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        result = urllib.parse.unquote(given, encoding=None, errors=None)
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        result = urllib.parse.unquote('br%FCckner_sapporo_20050930.doc',
            encoding='latin-1')
        expect = 'brückner_sapporo_20050930.doc'
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        given = '%E6%BC%A2%E5%AD%97'
        expect = '漢字'
        result = urllib.parse.unquote(given)
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        given = '%F3%B1'
        expect = '�'
        result = urllib.parse.unquote(given)
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        result = urllib.parse.unquote(given, errors='replace')
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        given = '%F3%B1'
        expect = ''
        result = urllib.parse.unquote(given, errors='ignore')
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        result = urllib.parse.unquote('漢%C3%BC')
        expect = '漢ü'
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))
        result = urllib.parse.unquote('漢%FC', encoding='latin-1')
        expect = '漢ü'
        self.assertEqual(expect, result, 'using unquote(): %r != %r' % (
            expect, result))


class urlencode_Tests(unittest.TestCase):
    """Tests for urlencode()"""

    def help_inputtype(self, given, test_type):
        """Helper method for testing different input types.

        'given' must lead to only the pairs:
            * 1st, 1
            * 2nd, 2
            * 3rd, 3

        Test cannot assume anything about order.  Docs make no guarantee and
        have possible dictionary input.

        """
        expect_somewhere = ['1st=1', '2nd=2', '3rd=3']
        result = urllib.parse.urlencode(given)
        for expected in expect_somewhere:
            self.assertIn(expected, result, 
                'testing %s: %s not found in %s' % (test_type, expected,
                result))
        self.assertEqual(result.count('&'), 2, 
            "testing %s: expected 2 '&'s; got %s" % (test_type, result.
            count('&')))
        amp_location = result.index('&')
        on_amp_left = result[amp_location - 1]
        on_amp_right = result[amp_location + 1]
        self.assertTrue(on_amp_left.isdigit() and on_amp_right.isdigit(), 
            "testing %s: '&' not located in proper place in %s" % (
            test_type, result))
        self.assertEqual(len(result), 5 * 3 + 2, 
            'testing %s: unexpected number of characters: %s != %s' % (
            test_type, len(result), 5 * 3 + 2))

    def test_using_mapping(self):
        self.help_inputtype({'1st': '1', '2nd': '2', '3rd': '3'},
            'using dict as input type')

    def test_using_sequence(self):
        self.help_inputtype([('1st', '1'), ('2nd', '2'), ('3rd', '3')],
            'using sequence of two-item tuples as input')

    def test_quoting(self):
        given = {'&': '='}
        expect = '%s=%s' % (hexescape('&'), hexescape('='))
        result = urllib.parse.urlencode(given)
        self.assertEqual(expect, result)
        given = {'key name': 'A bunch of pluses'}
        expect = 'key+name=A+bunch+of+pluses'
        result = urllib.parse.urlencode(given)
        self.assertEqual(expect, result)

    def test_doseq(self):
        given = {'sequence': ['1', '2', '3']}
        expect = 'sequence=%s' % urllib.parse.quote_plus(str(['1', '2', '3']))
        result = urllib.parse.urlencode(given)
        self.assertEqual(expect, result)
        result = urllib.parse.urlencode(given, True)
        for value in given['sequence']:
            expect = 'sequence=%s' % value
            self.assertIn(expect, result)
        self.assertEqual(result.count('&'), 2, "Expected 2 '&'s, got %s" %
            result.count('&'))

    def test_empty_sequence(self):
        self.assertEqual('', urllib.parse.urlencode({}))
        self.assertEqual('', urllib.parse.urlencode([]))

    def test_nonstring_values(self):
        self.assertEqual('a=1', urllib.parse.urlencode({'a': 1}))
        self.assertEqual('a=None', urllib.parse.urlencode({'a': None}))

    def test_nonstring_seq_values(self):
        self.assertEqual('a=1&a=2', urllib.parse.urlencode({'a': [1, 2]}, True)
            )
        self.assertEqual('a=None&a=a', urllib.parse.urlencode({'a': [None,
            'a']}, True))
        data = collections.OrderedDict([('a', 1), ('b', 1)])
        self.assertEqual('a=a&a=b', urllib.parse.urlencode({'a': data}, True))

    def test_urlencode_encoding(self):
        given = ('\xa0', 'Á'),
        expect = '%3F=%3F'
        result = urllib.parse.urlencode(given, encoding='ASCII', errors=
            'replace')
        self.assertEqual(expect, result)
        given = ('\xa0', 'Á'),
        expect = '%C2%A0=%C3%81'
        result = urllib.parse.urlencode(given)
        self.assertEqual(expect, result)
        given = ('\xa0', 'Á'),
        expect = '%A0=%C1'
        result = urllib.parse.urlencode(given, encoding='latin-1')
        self.assertEqual(expect, result)

    def test_urlencode_encoding_doseq(self):
        given = ('\xa0', 'Á'),
        expect = '%3F=%3F'
        result = urllib.parse.urlencode(given, doseq=True, encoding='ASCII',
            errors='replace')
        self.assertEqual(expect, result)
        given = ('\xa0', (1, 'Á')),
        expect = '%3F=1&%3F=%3F'
        result = urllib.parse.urlencode(given, True, encoding='ASCII',
            errors='replace')
        self.assertEqual(expect, result)
        given = ('\xa0', 'Á'),
        expect = '%C2%A0=%C3%81'
        result = urllib.parse.urlencode(given, True)
        self.assertEqual(expect, result)
        given = ('\xa0', (42, 'Á')),
        expect = '%C2%A0=42&%C2%A0=%C3%81'
        result = urllib.parse.urlencode(given, True)
        self.assertEqual(expect, result)
        given = ('\xa0', 'Á'),
        expect = '%A0=%C1'
        result = urllib.parse.urlencode(given, True, encoding='latin-1')
        self.assertEqual(expect, result)
        given = ('\xa0', (42, 'Á')),
        expect = '%A0=42&%A0=%C1'
        result = urllib.parse.urlencode(given, True, encoding='latin-1')
        self.assertEqual(expect, result)

    def test_urlencode_bytes(self):
        given = (b'\xa0$', b'\xc1$'),
        expect = '%A0%24=%C1%24'
        result = urllib.parse.urlencode(given)
        self.assertEqual(expect, result)
        result = urllib.parse.urlencode(given, True)
        self.assertEqual(expect, result)
        given = (b'\xa0$', (42, b'\xc1$')),
        expect = '%A0%24=42&%A0%24=%C1%24'
        result = urllib.parse.urlencode(given, True)
        self.assertEqual(expect, result)

    def test_urlencode_encoding_safe_parameter(self):
        given = (b'\xa0$', b'\xc1$'),
        result = urllib.parse.urlencode(given, safe=':$')
        expect = '%A0$=%C1$'
        self.assertEqual(expect, result)
        given = (b'\xa0$', b'\xc1$'),
        result = urllib.parse.urlencode(given, doseq=True, safe=':$')
        expect = '%A0$=%C1$'
        self.assertEqual(expect, result)
        given = (b'\xa0$', (b'\xc1$', 13, 42)),
        expect = '%A0$=%C1$&%A0$=13&%A0$=42'
        result = urllib.parse.urlencode(given, True, safe=':$')
        self.assertEqual(expect, result)
        given = (b'\xa0$', b'\xc1$'),
        result = urllib.parse.urlencode(given, safe=':$', encoding='latin-1')
        expect = '%A0$=%C1$'
        self.assertEqual(expect, result)
        given = (b'\xa0$', b'\xc1$'),
        expect = '%A0$=%C1$'
        result = urllib.parse.urlencode(given, doseq=True, safe=':$',
            encoding='latin-1')
        given = (b'\xa0$', (b'\xc1$', 13, 42)),
        expect = '%A0$=%C1$&%A0$=13&%A0$=42'
        result = urllib.parse.urlencode(given, True, safe=':$', encoding=
            'latin-1')
        self.assertEqual(expect, result)


class Pathname_Tests(unittest.TestCase):
    """Test pathname2url() and url2pathname()"""

    def test_basic(self):
        expected_path = os.path.join('parts', 'of', 'a', 'path')
        expected_url = 'parts/of/a/path'
        result = urllib.request.pathname2url(expected_path)
        self.assertEqual(expected_url, result, 
            'pathname2url() failed; %s != %s' % (result, expected_url))
        result = urllib.request.url2pathname(expected_url)
        self.assertEqual(expected_path, result, 
            'url2pathame() failed; %s != %s' % (result, expected_path))

    def test_quoting(self):
        given = os.path.join('needs', 'quot=ing', 'here')
        expect = 'needs/%s/here' % urllib.parse.quote('quot=ing')
        result = urllib.request.pathname2url(given)
        self.assertEqual(expect, result, 'pathname2url() failed; %s != %s' %
            (expect, result))
        expect = given
        result = urllib.request.url2pathname(result)
        self.assertEqual(expect, result, 'url2pathname() failed; %s != %s' %
            (expect, result))
        given = os.path.join('make sure', 'using_quote')
        expect = '%s/using_quote' % urllib.parse.quote('make sure')
        result = urllib.request.pathname2url(given)
        self.assertEqual(expect, result, 'pathname2url() failed; %s != %s' %
            (expect, result))
        given = 'make+sure/using_unquote'
        expect = os.path.join('make+sure', 'using_unquote')
        result = urllib.request.url2pathname(given)
        self.assertEqual(expect, result, 'url2pathname() failed; %s != %s' %
            (expect, result))

    @unittest.skipUnless(sys.platform == 'win32',
        'test specific to the urllib.url2path function.')
    def test_ntpath(self):
        given = '/C:/', '///C:/', '/C|//'
        expect = 'C:\\'
        for url in given:
            result = urllib.request.url2pathname(url)
            self.assertEqual(expect, result, 
                'urllib.request..url2pathname() failed; %s != %s' % (expect,
                result))
        given = '///C|/path'
        expect = 'C:\\path'
        result = urllib.request.url2pathname(given)
        self.assertEqual(expect, result, 
            'urllib.request.url2pathname() failed; %s != %s' % (expect, result)
            )


class Utility_Tests(unittest.TestCase):
    """Testcase to test the various utility functions in the urllib."""

    def test_thishost(self):
        """Test the urllib.request.thishost utility function returns a tuple"""
        self.assertIsInstance(urllib.request.thishost(), tuple)


class URLopener_Tests(unittest.TestCase):
    """Testcase to test the open method of URLopener class."""

    def test_quoted_open(self):


        class DummyURLopener(urllib.request.URLopener):

            def open_spam(self, url):
                return url
        with support.check_warnings((
            'DummyURLopener style of invoking requests is deprecated.',
            DeprecationWarning)):
            self.assertEqual(DummyURLopener().open('spam://example/ /'),
                '//example/%20/')
            self.assertEqual(DummyURLopener().open(
                "spam://c:|windows%/:=&?~#+!$,;'@()*[]|/path/"),
                "//c:|windows%/:=&?~#+!$,;'@()*[]|/path/")


class RequestTests(unittest.TestCase):
    """Unit tests for urllib.request.Request."""

    def test_default_values(self):
        Request = urllib.request.Request
        request = Request('http://www.python.org')
        self.assertEqual(request.get_method(), 'GET')
        request = Request('http://www.python.org', {})
        self.assertEqual(request.get_method(), 'POST')

    def test_with_method_arg(self):
        Request = urllib.request.Request
        request = Request('http://www.python.org', method='HEAD')
        self.assertEqual(request.method, 'HEAD')
        self.assertEqual(request.get_method(), 'HEAD')
        request = Request('http://www.python.org', {}, method='HEAD')
        self.assertEqual(request.method, 'HEAD')
        self.assertEqual(request.get_method(), 'HEAD')
        request = Request('http://www.python.org', method='GET')
        self.assertEqual(request.get_method(), 'GET')
        request.method = 'HEAD'
        self.assertEqual(request.get_method(), 'HEAD')


class URL2PathNameTests(unittest.TestCase):

    def test_converting_drive_letter(self):
        self.assertEqual(url2pathname('///C|'), 'C:')
        self.assertEqual(url2pathname('///C:'), 'C:')
        self.assertEqual(url2pathname('///C|/'), 'C:\\')

    def test_converting_when_no_drive_letter(self):
        self.assertEqual(url2pathname('///C/test/'), '\\\\\\C\\test\\')
        self.assertEqual(url2pathname('////C/test/'), '\\\\C\\test\\')

    def test_simple_compare(self):
        self.assertEqual(url2pathname('///C|/foo/bar/spam.foo'),
            'C:\\foo\\bar\\spam.foo')

    def test_non_ascii_drive_letter(self):
        self.assertRaises(IOError, url2pathname, '///è|/')

    def test_roundtrip_url2pathname(self):
        list_of_paths = ['C:', '\\\\\\C\\test\\\\', 'C:\\foo\\bar\\spam.foo']
        for path in list_of_paths:
            self.assertEqual(url2pathname(pathname2url(path)), path)


class PathName2URLTests(unittest.TestCase):

    def test_converting_drive_letter(self):
        self.assertEqual(pathname2url('C:'), '///C:')
        self.assertEqual(pathname2url('C:\\'), '///C:')

    def test_converting_when_no_drive_letter(self):
        self.assertEqual(pathname2url('\\\\\\folder\\test\\'),
            '/////folder/test/')
        self.assertEqual(pathname2url('\\\\folder\\test\\'), '////folder/test/'
            )
        self.assertEqual(pathname2url('\\folder\\test\\'), '/folder/test/')

    def test_simple_compare(self):
        self.assertEqual(pathname2url('C:\\foo\\bar\\spam.foo'),
            '///C:/foo/bar/spam.foo')

    def test_long_drive_letter(self):
        self.assertRaises(IOError, pathname2url, 'XX:\\')

    def test_roundtrip_pathname2url(self):
        list_of_paths = ['///C:', '/////folder/test/', '///C:/foo/bar/spam.foo'
            ]
        for path in list_of_paths:
            self.assertEqual(pathname2url(url2pathname(path)), path)


if __name__ == '__main__':
    unittest.main()
