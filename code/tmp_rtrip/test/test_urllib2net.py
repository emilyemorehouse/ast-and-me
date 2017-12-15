import unittest
from test import support
from test.test_urllib2 import sanepathname2url
import os
import socket
import urllib.error
import urllib.request
import sys
support.requires('network')
TIMEOUT = 60


def _retry_thrice(func, exc, *args, **kwargs):
    for i in range(3):
        try:
            return func(*args, **kwargs)
        except exc as e:
            last_exc = e
            continue
    raise last_exc


def _wrap_with_retry_thrice(func, exc):

    def wrapped(*args, **kwargs):
        return _retry_thrice(func, exc, *args, **kwargs)
    return wrapped


_urlopen_with_retry = _wrap_with_retry_thrice(urllib.request.urlopen,
    urllib.error.URLError)


class AuthTests(unittest.TestCase):
    """Tests urllib2 authentication features."""


class CloseSocketTest(unittest.TestCase):

    def test_close(self):
        url = 'http://www.example.com/'
        with support.transient_internet(url):
            response = _urlopen_with_retry(url)
            sock = response.fp
            self.assertFalse(sock.closed)
            response.close()
            self.assertTrue(sock.closed)


class OtherNetworkTests(unittest.TestCase):

    def setUp(self):
        if 0:
            import logging
            logger = logging.getLogger('test_urllib2net')
            logger.addHandler(logging.StreamHandler())

    def test_ftp(self):
        urls = ['ftp://ftp.debian.org/debian/README', (
            'ftp://ftp.debian.org/debian/non-existent-file', None, urllib.
            error.URLError)]
        self._test_urls(urls, self._extra_handlers())

    def test_file(self):
        TESTFN = support.TESTFN
        f = open(TESTFN, 'w')
        try:
            f.write('hi there\n')
            f.close()
            urls = ['file:' + sanepathname2url(os.path.abspath(TESTFN)), (
                'file:///nonsensename/etc/passwd', None, urllib.error.URLError)
                ]
            self._test_urls(urls, self._extra_handlers(), retry=True)
        finally:
            os.remove(TESTFN)
        self.assertRaises(ValueError, urllib.request.urlopen,
            './relative_path/to/file')

    def test_urlwithfrag(self):
        urlwith_frag = 'http://www.pythontest.net/index.html#frag'
        with support.transient_internet(urlwith_frag):
            req = urllib.request.Request(urlwith_frag)
            res = urllib.request.urlopen(req)
            self.assertEqual(res.geturl(),
                'http://www.pythontest.net/index.html#frag')

    def test_redirect_url_withfrag(self):
        redirect_url_with_frag = 'http://www.pythontest.net/redir/with_frag/'
        with support.transient_internet(redirect_url_with_frag):
            req = urllib.request.Request(redirect_url_with_frag)
            res = urllib.request.urlopen(req)
            self.assertEqual(res.geturl(),
                'http://www.pythontest.net/elsewhere/#frag')

    def test_custom_headers(self):
        url = 'http://www.example.com'
        with support.transient_internet(url):
            opener = urllib.request.build_opener()
            request = urllib.request.Request(url)
            self.assertFalse(request.header_items())
            opener.open(request)
            self.assertTrue(request.header_items())
            self.assertTrue(request.has_header('User-agent'))
            request.add_header('User-Agent', 'Test-Agent')
            opener.open(request)
            self.assertEqual(request.get_header('User-agent'), 'Test-Agent')

    def test_sites_no_connection_close(self):
        URL = 'http://www.imdb.com'
        with support.transient_internet(URL):
            try:
                with urllib.request.urlopen(URL) as res:
                    pass
            except ValueError as e:
                self.fail(
                    'urlopen failed for site not sending                            Connection:close'
                    )
            else:
                self.assertTrue(res)
            req = urllib.request.urlopen(URL)
            res = req.read()
            self.assertTrue(res)

    def _test_urls(self, urls, handlers, retry=True):
        import time
        import logging
        debug = logging.getLogger('test_urllib2').debug
        urlopen = urllib.request.build_opener(*handlers).open
        if retry:
            urlopen = _wrap_with_retry_thrice(urlopen, urllib.error.URLError)
        for url in urls:
            with self.subTest(url=url):
                if isinstance(url, tuple):
                    url, req, expected_err = url
                else:
                    req = expected_err = None
                with support.transient_internet(url):
                    try:
                        f = urlopen(url, req, TIMEOUT)
                    except OSError as err:
                        if expected_err:
                            msg = (
                                "Didn't get expected error(s) %s for %s %s, got %s: %s"
                                 % (expected_err, url, req, type(err), err))
                            self.assertIsInstance(err, expected_err, msg)
                        else:
                            raise
                    else:
                        try:
                            with support.time_out, support.socket_peer_reset, support.ioerror_peer_reset:
                                buf = f.read()
                                debug('read %d bytes' % len(buf))
                        except socket.timeout:
                            print('<timeout: %s>' % url, file=sys.stderr)
                        f.close()
                time.sleep(0.1)

    def _extra_handlers(self):
        handlers = []
        cfh = urllib.request.CacheFTPHandler()
        self.addCleanup(cfh.clear_cache)
        cfh.setTimeout(1)
        handlers.append(cfh)
        return handlers


class TimeoutTest(unittest.TestCase):

    def test_http_basic(self):
        self.assertIsNone(socket.getdefaulttimeout())
        url = 'http://www.example.com'
        with support.transient_internet(url, timeout=None):
            u = _urlopen_with_retry(url)
            self.addCleanup(u.close)
            self.assertIsNone(u.fp.raw._sock.gettimeout())

    def test_http_default_timeout(self):
        self.assertIsNone(socket.getdefaulttimeout())
        url = 'http://www.example.com'
        with support.transient_internet(url):
            socket.setdefaulttimeout(60)
            try:
                u = _urlopen_with_retry(url)
                self.addCleanup(u.close)
            finally:
                socket.setdefaulttimeout(None)
            self.assertEqual(u.fp.raw._sock.gettimeout(), 60)

    def test_http_no_timeout(self):
        self.assertIsNone(socket.getdefaulttimeout())
        url = 'http://www.example.com'
        with support.transient_internet(url):
            socket.setdefaulttimeout(60)
            try:
                u = _urlopen_with_retry(url, timeout=None)
                self.addCleanup(u.close)
            finally:
                socket.setdefaulttimeout(None)
            self.assertIsNone(u.fp.raw._sock.gettimeout())

    def test_http_timeout(self):
        url = 'http://www.example.com'
        with support.transient_internet(url):
            u = _urlopen_with_retry(url, timeout=120)
            self.addCleanup(u.close)
            self.assertEqual(u.fp.raw._sock.gettimeout(), 120)
    FTP_HOST = 'ftp://ftp.debian.org/debian/'

    def test_ftp_basic(self):
        self.assertIsNone(socket.getdefaulttimeout())
        with support.transient_internet(self.FTP_HOST, timeout=None):
            u = _urlopen_with_retry(self.FTP_HOST)
            self.addCleanup(u.close)
            self.assertIsNone(u.fp.fp.raw._sock.gettimeout())

    def test_ftp_default_timeout(self):
        self.assertIsNone(socket.getdefaulttimeout())
        with support.transient_internet(self.FTP_HOST):
            socket.setdefaulttimeout(60)
            try:
                u = _urlopen_with_retry(self.FTP_HOST)
                self.addCleanup(u.close)
            finally:
                socket.setdefaulttimeout(None)
            self.assertEqual(u.fp.fp.raw._sock.gettimeout(), 60)

    def test_ftp_no_timeout(self):
        self.assertIsNone(socket.getdefaulttimeout())
        with support.transient_internet(self.FTP_HOST):
            socket.setdefaulttimeout(60)
            try:
                u = _urlopen_with_retry(self.FTP_HOST, timeout=None)
                self.addCleanup(u.close)
            finally:
                socket.setdefaulttimeout(None)
            self.assertIsNone(u.fp.fp.raw._sock.gettimeout())

    def test_ftp_timeout(self):
        with support.transient_internet(self.FTP_HOST):
            u = _urlopen_with_retry(self.FTP_HOST, timeout=60)
            self.addCleanup(u.close)
            self.assertEqual(u.fp.fp.raw._sock.gettimeout(), 60)


if __name__ == '__main__':
    unittest.main()
