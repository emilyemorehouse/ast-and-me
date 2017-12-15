"""Tests for http/cookiejar.py."""
import os
import re
import test.support
import time
import unittest
import urllib.request
from http.cookiejar import time2isoz, http2time, iso2time, time2netscape, parse_ns_headers, join_header_words, split_header_words, Cookie, CookieJar, DefaultCookiePolicy, LWPCookieJar, MozillaCookieJar, LoadError, lwp_cookie_str, DEFAULT_HTTP_PORT, escape_path, reach, is_HDN, domain_match, user_domain_match, request_path, request_port, request_host


class DateTimeTests(unittest.TestCase):

    def test_time2isoz(self):
        base = 1019227000
        day = 24 * 3600
        self.assertEqual(time2isoz(base), '2002-04-19 14:36:40Z')
        self.assertEqual(time2isoz(base + day), '2002-04-20 14:36:40Z')
        self.assertEqual(time2isoz(base + 2 * day), '2002-04-21 14:36:40Z')
        self.assertEqual(time2isoz(base + 3 * day), '2002-04-22 14:36:40Z')
        az = time2isoz()
        bz = time2isoz(500000)
        for text in (az, bz):
            self.assertRegex(text,
                '^\\d{4}-\\d\\d-\\d\\d \\d\\d:\\d\\d:\\d\\dZ$', 
                'bad time2isoz format: %s %s' % (az, bz))

    def test_time2netscape(self):
        base = 1019227000
        day = 24 * 3600
        self.assertEqual(time2netscape(base), 'Fri, 19-Apr-2002 14:36:40 GMT')
        self.assertEqual(time2netscape(base + day),
            'Sat, 20-Apr-2002 14:36:40 GMT')
        self.assertEqual(time2netscape(base + 2 * day),
            'Sun, 21-Apr-2002 14:36:40 GMT')
        self.assertEqual(time2netscape(base + 3 * day),
            'Mon, 22-Apr-2002 14:36:40 GMT')
        az = time2netscape()
        bz = time2netscape(500000)
        for text in (az, bz):
            self.assertRegex(text,
                '[a-zA-Z]{3}, \\d{2}-[a-zA-Z]{3}-\\d{4} \\d{2}:\\d{2}:\\d{2} GMT$'
                , 'bad time2netscape format: %s %s' % (az, bz))

    def test_http2time(self):

        def parse_date(text):
            return time.gmtime(http2time(text))[:6]
        self.assertEqual(parse_date('01 Jan 2001'), (2001, 1, 1, 0, 0, 0.0))
        self.assertEqual(parse_date('03-Feb-20'), (2020, 2, 3, 0, 0, 0.0))
        self.assertEqual(parse_date('03-Feb-98'), (1998, 2, 3, 0, 0, 0.0))

    def test_http2time_formats(self):
        tests = ['Thu, 03 Feb 1994 00:00:00 GMT',
            'Thursday, 03-Feb-94 00:00:00 GMT',
            'Thursday, 03-Feb-1994 00:00:00 GMT',
            '03 Feb 1994 00:00:00 GMT', '03-Feb-94 00:00:00 GMT',
            '03-Feb-1994 00:00:00 GMT', '03-Feb-1994 00:00 GMT',
            '03-Feb-1994 00:00', '02-Feb-1994 24:00', '03-Feb-94',
            '03-Feb-1994', '03 Feb 1994', '  03   Feb   1994  0:00  ',
            '  03-Feb-1994  ']
        test_t = 760233600
        result = time2isoz(test_t)
        expected = '1994-02-03 00:00:00Z'
        self.assertEqual(result, expected, "%s  =>  '%s' (%s)" % (test_t,
            result, expected))
        for s in tests:
            self.assertEqual(http2time(s), test_t, s)
            self.assertEqual(http2time(s.lower()), test_t, s.lower())
            self.assertEqual(http2time(s.upper()), test_t, s.upper())

    def test_http2time_garbage(self):
        for test in ['', 'Garbage', 'Mandag 16. September 1996',
            '01-00-1980', '01-13-1980', '00-01-1980', '32-01-1980',
            '01-01-1980 25:00:00', '01-01-1980 00:61:00',
            '01-01-1980 00:00:62', '08-Oct-3697739', '08-01-3697739',
            '09 Feb 19942632 22:23:32 GMT', 'Wed, 09 Feb 1994834 22:23:32 GMT'
            ]:
            self.assertIsNone(http2time(test), 
                'http2time(%s) is not None\nhttp2time(test) %s' % (test,
                http2time(test)))

    def test_iso2time(self):

        def parse_date(text):
            return time.gmtime(iso2time(text))[:6]
        self.assertEqual(parse_date('19940203T141529Z'), (1994, 2, 3, 14, 
            15, 29))
        self.assertEqual(parse_date('1994-02-03 07:15:29 -0700'), (1994, 2,
            3, 14, 15, 29))
        self.assertEqual(parse_date('1994-02-03 19:45:29 +0530'), (1994, 2,
            3, 14, 15, 29))

    def test_iso2time_formats(self):
        tests = ['1994-02-03 00:00:00 -0000', '1994-02-03 00:00:00 +0000',
            '1994-02-03 00:00:00', '1994-02-03', '1994-02-03T00:00:00',
            '19940203', '1994-02-02 24:00:00', '19940203T000000Z',
            '  1994-02-03 ', '  1994-02-03T00:00:00  ']
        test_t = 760233600
        for s in tests:
            self.assertEqual(iso2time(s), test_t, s)
            self.assertEqual(iso2time(s.lower()), test_t, s.lower())
            self.assertEqual(iso2time(s.upper()), test_t, s.upper())

    def test_iso2time_garbage(self):
        for test in ['', 'Garbage', 'Thursday, 03-Feb-94 00:00:00 GMT',
            '1980-00-01', '1980-13-01', '1980-01-00', '1980-01-32',
            '1980-01-01 25:00:00', '1980-01-01 00:61:00',
            '01-01-1980 00:00:62', '01-01-1980T00:00:62',
            '19800101T250000Z1980-01-01 00:00:00 -2500']:
            self.assertIsNone(iso2time(test), 
                'iso2time(%s) is not None\niso2time(test) %s' % (test,
                iso2time(test)))


class HeaderTests(unittest.TestCase):

    def test_parse_ns_headers(self):
        expected = [[('foo', 'bar'), ('expires', 2209069412), ('version', '0')]
            ]
        for hdr in ['foo=bar; expires=01 Jan 2040 22:23:32 GMT',
            'foo=bar; expires="01 Jan 2040 22:23:32 GMT"']:
            self.assertEqual(parse_ns_headers([hdr]), expected)

    def test_parse_ns_headers_version(self):
        expected = [[('foo', 'bar'), ('version', '1')]]
        for hdr in ['foo=bar; version="1"', 'foo=bar; Version="1"']:
            self.assertEqual(parse_ns_headers([hdr]), expected)

    def test_parse_ns_headers_special_names(self):
        hdr = 'expires=01 Jan 2040 22:23:32 GMT'
        expected = [[('expires', '01 Jan 2040 22:23:32 GMT'), ('version', '0')]
            ]
        self.assertEqual(parse_ns_headers([hdr]), expected)

    def test_join_header_words(self):
        joined = join_header_words([[('foo', None), ('bar', 'baz')]])
        self.assertEqual(joined, 'foo; bar=baz')
        self.assertEqual(join_header_words([[]]), '')

    def test_split_header_words(self):
        tests = [('foo', [[('foo', None)]]), ('foo=bar', [[('foo', 'bar')]]
            ), ('   foo   ', [[('foo', None)]]), ('   foo=   ', [[('foo',
            '')]]), ('   foo=', [[('foo', '')]]), ('   foo=   ; ', [[('foo',
            '')]]), ('   foo=   ; bar= baz ', [[('foo', ''), ('bar', 'baz')
            ]]), ('foo=bar bar=baz', [[('foo', 'bar'), ('bar', 'baz')]]), (
            'foo= bar=baz', [[('foo', 'bar=baz')]]), ('foo=bar;bar=baz', [[
            ('foo', 'bar'), ('bar', 'baz')]]), ('foo bar baz', [[('foo',
            None), ('bar', None), ('baz', None)]]), ('a, b, c', [[('a',
            None)], [('b', None)], [('c', None)]]), (
            'foo; bar=baz, spam=, foo="\\,\\;\\"", bar= ', [[('foo', None),
            ('bar', 'baz')], [('spam', '')], [('foo', ',;"')], [('bar', '')]])]
        for arg, expect in tests:
            try:
                result = split_header_words([arg])
            except:
                import traceback, io
                f = io.StringIO()
                traceback.print_exc(None, f)
                result = '(error -- traceback follows)\n\n%s' % f.getvalue()
            self.assertEqual(result, expect, 
                """
When parsing: '%s'
Expected:     '%s'
Got:          '%s'
"""
                 % (arg, expect, result))

    def test_roundtrip(self):
        tests = [('foo', 'foo'), ('foo=bar', 'foo=bar'), ('   foo   ',
            'foo'), ('foo=', 'foo=""'), ('foo=bar bar=baz',
            'foo=bar; bar=baz'), ('foo=bar;bar=baz', 'foo=bar; bar=baz'), (
            'foo bar baz', 'foo; bar; baz'), ('foo="\\"" bar="\\\\"',
            'foo="\\""; bar="\\\\"'), ('foo,,,bar', 'foo, bar'), (
            'foo=bar,bar=baz', 'foo=bar, bar=baz'), (
            'text/html; charset=iso-8859-1',
            'text/html; charset="iso-8859-1"'), (
            'foo="bar"; port="80,81"; discard, bar=baz',
            'foo=bar; port="80,81"; discard, bar=baz'), (
            'Basic realm="\\"foo\\\\\\\\bar\\""',
            'Basic; realm="\\"foo\\\\\\\\bar\\""')]
        for arg, expect in tests:
            input = split_header_words([arg])
            res = join_header_words(input)
            self.assertEqual(res, expect, 
                """
When parsing: '%s'
Expected:     '%s'
Got:          '%s'
Input was:    '%s'
"""
                 % (arg, expect, res, input))


class FakeResponse:

    def __init__(self, headers=[], url=None):
        """
        headers: list of RFC822-style 'Key: value' strings
        """
        import email
        self._headers = email.message_from_string('\n'.join(headers))
        self._url = url

    def info(self):
        return self._headers


def interact_2965(cookiejar, url, *set_cookie_hdrs):
    return _interact(cookiejar, url, set_cookie_hdrs, 'Set-Cookie2')


def interact_netscape(cookiejar, url, *set_cookie_hdrs):
    return _interact(cookiejar, url, set_cookie_hdrs, 'Set-Cookie')


def _interact(cookiejar, url, set_cookie_hdrs, hdr_name):
    """Perform a single request / response cycle, returning Cookie: header."""
    req = urllib.request.Request(url)
    cookiejar.add_cookie_header(req)
    cookie_hdr = req.get_header('Cookie', '')
    headers = []
    for hdr in set_cookie_hdrs:
        headers.append('%s: %s' % (hdr_name, hdr))
    res = FakeResponse(headers, url)
    cookiejar.extract_cookies(res, req)
    return cookie_hdr


class FileCookieJarTests(unittest.TestCase):

    def test_lwp_valueless_cookie(self):
        filename = test.support.TESTFN
        c = LWPCookieJar()
        interact_netscape(c, 'http://www.acme.com/', 'boo')
        self.assertEqual(c._cookies['www.acme.com']['/']['boo'].value, None)
        try:
            c.save(filename, ignore_discard=True)
            c = LWPCookieJar()
            c.load(filename, ignore_discard=True)
        finally:
            try:
                os.unlink(filename)
            except OSError:
                pass
        self.assertEqual(c._cookies['www.acme.com']['/']['boo'].value, None)

    def test_bad_magic(self):
        filename = test.support.TESTFN
        for cookiejar_class in (LWPCookieJar, MozillaCookieJar):
            c = cookiejar_class()
            try:
                c.load(filename=
                    'for this test to work, a file with this filename should not exist'
                    )
            except OSError as exc:
                self.assertIsNot(exc.__class__, LoadError)
            else:
                self.fail('expected OSError for invalid filename')
        try:
            with open(filename, 'w') as f:
                f.write('oops\n')
                for cookiejar_class in (LWPCookieJar, MozillaCookieJar):
                    c = cookiejar_class()
                    self.assertRaises(LoadError, c.load, filename)
        finally:
            try:
                os.unlink(filename)
            except OSError:
                pass


class CookieTests(unittest.TestCase):

    def test_domain_return_ok(self):
        pol = DefaultCookiePolicy()
        for url, domain, ok in [('http://foo.bar.com/', 'blah.com', False),
            ('http://foo.bar.com/', 'rhubarb.blah.com', False), (
            'http://foo.bar.com/', 'rhubarb.foo.bar.com', False), (
            'http://foo.bar.com/', '.foo.bar.com', True), (
            'http://foo.bar.com/', 'foo.bar.com', True), (
            'http://foo.bar.com/', '.bar.com', True), (
            'http://foo.bar.com/', 'com', True), ('http://foo.com/',
            'rhubarb.foo.com', False), ('http://foo.com/', '.foo.com', True
            ), ('http://foo.com/', 'foo.com', True), ('http://foo.com/',
            'com', True), ('http://foo/', 'rhubarb.foo', False), (
            'http://foo/', '.foo', True), ('http://foo/', 'foo', True), (
            'http://foo/', 'foo.local', True), ('http://foo/', '.local', True)
            ]:
            request = urllib.request.Request(url)
            r = pol.domain_return_ok(domain, request)
            if ok:
                self.assertTrue(r)
            else:
                self.assertFalse(r)

    def test_missing_value(self):
        filename = test.support.TESTFN
        c = MozillaCookieJar(filename)
        interact_netscape(c, 'http://www.acme.com/', 'eggs')
        interact_netscape(c, 'http://www.acme.com/', '"spam"; path=/foo/')
        cookie = c._cookies['www.acme.com']['/']['eggs']
        self.assertIsNone(cookie.value)
        self.assertEqual(cookie.name, 'eggs')
        cookie = c._cookies['www.acme.com']['/foo/']['"spam"']
        self.assertIsNone(cookie.value)
        self.assertEqual(cookie.name, '"spam"')
        self.assertEqual(lwp_cookie_str(cookie),
            '"spam"; path="/foo/"; domain="www.acme.com"; path_spec; discard; version=0'
            )
        old_str = repr(c)
        c.save(ignore_expires=True, ignore_discard=True)
        try:
            c = MozillaCookieJar(filename)
            c.revert(ignore_expires=True, ignore_discard=True)
        finally:
            os.unlink(c.filename)
        self.assertEqual(repr(c), re.sub('path_specified=%s' % True, 
            'path_specified=%s' % False, old_str))
        self.assertEqual(interact_netscape(c, 'http://www.acme.com/foo/'),
            '"spam"; eggs')

    def test_rfc2109_handling(self):
        for rfc2109_as_netscape, rfc2965, version in [(None, False, 0), (
            None, True, 1), (False, False, None), (False, True, 1), (True,
            False, 0), (True, True, 0)]:
            policy = DefaultCookiePolicy(rfc2109_as_netscape=
                rfc2109_as_netscape, rfc2965=rfc2965)
            c = CookieJar(policy)
            interact_netscape(c, 'http://www.example.com/', 'ni=ni; Version=1')
            try:
                cookie = c._cookies['www.example.com']['/']['ni']
            except KeyError:
                self.assertIsNone(version)
            else:
                self.assertEqual(cookie.version, version)
                interact_2965(c, 'http://www.example.com/',
                    'foo=bar; Version=1')
                if rfc2965:
                    cookie2965 = c._cookies['www.example.com']['/']['foo']
                    self.assertEqual(cookie2965.version, 1)

    def test_ns_parser(self):
        c = CookieJar()
        interact_netscape(c, 'http://www.acme.com/',
            'spam=eggs; DoMain=.acme.com; port; blArgh="feep"')
        interact_netscape(c, 'http://www.acme.com/', 'ni=ni; port=80,8080')
        interact_netscape(c, 'http://www.acme.com:80/', 'nini=ni')
        interact_netscape(c, 'http://www.acme.com:80/', 'foo=bar; expires=')
        interact_netscape(c, 'http://www.acme.com:80/',
            'spam=eggs; expires="Foo Bar 25 33:22:11 3022"')
        interact_netscape(c, 'http://www.acme.com/', 'fortytwo=')
        interact_netscape(c, 'http://www.acme.com/', '=unladenswallow')
        interact_netscape(c, 'http://www.acme.com/', 'holyhandgrenade')
        cookie = c._cookies['.acme.com']['/']['spam']
        self.assertEqual(cookie.domain, '.acme.com')
        self.assertTrue(cookie.domain_specified)
        self.assertEqual(cookie.port, DEFAULT_HTTP_PORT)
        self.assertFalse(cookie.port_specified)
        self.assertTrue(cookie.has_nonstandard_attr('blArgh'))
        self.assertFalse(cookie.has_nonstandard_attr('blargh'))
        cookie = c._cookies['www.acme.com']['/']['ni']
        self.assertEqual(cookie.domain, 'www.acme.com')
        self.assertFalse(cookie.domain_specified)
        self.assertEqual(cookie.port, '80,8080')
        self.assertTrue(cookie.port_specified)
        cookie = c._cookies['www.acme.com']['/']['nini']
        self.assertIsNone(cookie.port)
        self.assertFalse(cookie.port_specified)
        foo = c._cookies['www.acme.com']['/']['foo']
        spam = c._cookies['www.acme.com']['/']['foo']
        self.assertIsNone(foo.expires)
        self.assertIsNone(spam.expires)
        cookie = c._cookies['www.acme.com']['/']['fortytwo']
        self.assertIsNotNone(cookie.value)
        self.assertEqual(cookie.value, '')
        cookie = c._cookies['www.acme.com']['/']['holyhandgrenade']
        self.assertIsNone(cookie.value)

    def test_ns_parser_special_names(self):
        c = CookieJar()
        interact_netscape(c, 'http://www.acme.com/', 'expires=eggs')
        interact_netscape(c, 'http://www.acme.com/', 'version=eggs; spam=eggs')
        cookies = c._cookies['www.acme.com']['/']
        self.assertIn('expires', cookies)
        self.assertIn('version', cookies)

    def test_expires(self):
        c = CookieJar()
        future = time2netscape(time.time() + 3600)
        interact_netscape(c, 'http://www.acme.com/', 
            'spam="bar"; expires=%s' % future)
        self.assertEqual(len(c), 1)
        now = time2netscape(time.time() - 1)
        interact_netscape(c, 'http://www.acme.com/', 
            'foo="eggs"; expires=%s' % now)
        h = interact_netscape(c, 'http://www.acme.com/')
        self.assertEqual(len(c), 1)
        self.assertIn('spam="bar"', h)
        self.assertNotIn('foo', h)
        interact_netscape(c, 'http://www.acme.com/', 
            'eggs="bar"; expires=%s' % future)
        interact_netscape(c, 'http://www.acme.com/', 
            'bar="bar"; expires=%s' % future)
        self.assertEqual(len(c), 3)
        interact_netscape(c, 'http://www.acme.com/', 
            'eggs="bar"; expires=%s; max-age=0' % future)
        interact_netscape(c, 'http://www.acme.com/', 
            'bar="bar"; max-age=0; expires=%s' % future)
        h = interact_netscape(c, 'http://www.acme.com/')
        self.assertEqual(len(c), 1)
        interact_netscape(c, 'http://www.rhubarb.net/', 'whum="fizz"')
        self.assertEqual(len(c), 2)
        c.clear_session_cookies()
        self.assertEqual(len(c), 1)
        self.assertIn('spam="bar"', h)
        cookie = Cookie(0, 'name', 'value', None, False, 'www.python.org',
            True, False, '/', False, False, '1444312383.018307', False,
            None, None, {})
        self.assertEqual(cookie.expires, 1444312383)

    def test_default_path(self):
        pol = DefaultCookiePolicy(rfc2965=True)
        c = CookieJar(pol)
        interact_2965(c, 'http://www.acme.com/', 'spam="bar"; Version="1"')
        self.assertIn('/', c._cookies['www.acme.com'])
        c = CookieJar(pol)
        interact_2965(c, 'http://www.acme.com/blah', 'eggs="bar"; Version="1"')
        self.assertIn('/', c._cookies['www.acme.com'])
        c = CookieJar(pol)
        interact_2965(c, 'http://www.acme.com/blah/rhubarb',
            'eggs="bar"; Version="1"')
        self.assertIn('/blah/', c._cookies['www.acme.com'])
        c = CookieJar(pol)
        interact_2965(c, 'http://www.acme.com/blah/rhubarb/',
            'eggs="bar"; Version="1"')
        self.assertIn('/blah/rhubarb/', c._cookies['www.acme.com'])
        c = CookieJar()
        interact_netscape(c, 'http://www.acme.com/', 'spam="bar"')
        self.assertIn('/', c._cookies['www.acme.com'])
        c = CookieJar()
        interact_netscape(c, 'http://www.acme.com/blah', 'eggs="bar"')
        self.assertIn('/', c._cookies['www.acme.com'])
        c = CookieJar()
        interact_netscape(c, 'http://www.acme.com/blah/rhubarb', 'eggs="bar"')
        self.assertIn('/blah', c._cookies['www.acme.com'])
        c = CookieJar()
        interact_netscape(c, 'http://www.acme.com/blah/rhubarb/', 'eggs="bar"')
        self.assertIn('/blah/rhubarb', c._cookies['www.acme.com'])

    def test_default_path_with_query(self):
        cj = CookieJar()
        uri = 'http://example.com/?spam/eggs'
        value = 'eggs="bar"'
        interact_netscape(cj, uri, value)
        self.assertIn('/', cj._cookies['example.com'])
        self.assertEqual(interact_netscape(cj, uri), value)

    def test_escape_path(self):
        cases = [('/foo%2f/bar', '/foo%2F/bar'), ('/foo%2F/bar',
            '/foo%2F/bar'), ('/foo%%/bar', '/foo%%/bar'), ('/fo%19o/bar',
            '/fo%19o/bar'), ('/fo%7do/bar', '/fo%7Do/bar'), ('/foo/bar&',
            '/foo/bar&'), ('/foo//bar', '/foo//bar'), ('~/foo/bar',
            '~/foo/bar'), ('/foo\x19/bar', '/foo%19/bar'), ('/}foo/bar',
            '/%7Dfoo/bar'), ('/foo/barü', '/foo/bar%C3%BC'), ('/foo/barꯍ',
            '/foo/bar%EA%AF%8D')]
        for arg, result in cases:
            self.assertEqual(escape_path(arg), result)

    def test_request_path(self):
        req = urllib.request.Request(
            'http://www.example.com/rheum/rhaponticum;foo=bar;sing=song?apples=pears&spam=eggs#ni'
            )
        self.assertEqual(request_path(req),
            '/rheum/rhaponticum;foo=bar;sing=song')
        req = urllib.request.Request(
            'http://www.example.com/rheum/rhaponticum?apples=pears&spam=eggs#ni'
            )
        self.assertEqual(request_path(req), '/rheum/rhaponticum')
        req = urllib.request.Request('http://www.example.com')
        self.assertEqual(request_path(req), '/')

    def test_request_port(self):
        req = urllib.request.Request('http://www.acme.com:1234/', headers={
            'Host': 'www.acme.com:4321'})
        self.assertEqual(request_port(req), '1234')
        req = urllib.request.Request('http://www.acme.com/', headers={
            'Host': 'www.acme.com:4321'})
        self.assertEqual(request_port(req), DEFAULT_HTTP_PORT)

    def test_request_host(self):
        req = urllib.request.Request('http://1.1.1.1/', headers={'Host':
            'www.acme.com:80'})
        self.assertEqual(request_host(req), '1.1.1.1')
        req = urllib.request.Request('http://www.acme.com/', headers={
            'Host': 'irrelevant.com'})
        self.assertEqual(request_host(req), 'www.acme.com')
        req = urllib.request.Request('http://www.acme.com:2345/resource.html',
            headers={'Host': 'www.acme.com:5432'})
        self.assertEqual(request_host(req), 'www.acme.com')

    def test_is_HDN(self):
        self.assertTrue(is_HDN('foo.bar.com'))
        self.assertTrue(is_HDN('1foo2.3bar4.5com'))
        self.assertFalse(is_HDN('192.168.1.1'))
        self.assertFalse(is_HDN(''))
        self.assertFalse(is_HDN('.'))
        self.assertFalse(is_HDN('.foo.bar.com'))
        self.assertFalse(is_HDN('..foo'))
        self.assertFalse(is_HDN('foo.'))

    def test_reach(self):
        self.assertEqual(reach('www.acme.com'), '.acme.com')
        self.assertEqual(reach('acme.com'), 'acme.com')
        self.assertEqual(reach('acme.local'), '.local')
        self.assertEqual(reach('.local'), '.local')
        self.assertEqual(reach('.com'), '.com')
        self.assertEqual(reach('.'), '.')
        self.assertEqual(reach(''), '')
        self.assertEqual(reach('192.168.0.1'), '192.168.0.1')

    def test_domain_match(self):
        self.assertTrue(domain_match('192.168.1.1', '192.168.1.1'))
        self.assertFalse(domain_match('192.168.1.1', '.168.1.1'))
        self.assertTrue(domain_match('x.y.com', 'x.Y.com'))
        self.assertTrue(domain_match('x.y.com', '.Y.com'))
        self.assertFalse(domain_match('x.y.com', 'Y.com'))
        self.assertTrue(domain_match('a.b.c.com', '.c.com'))
        self.assertFalse(domain_match('.c.com', 'a.b.c.com'))
        self.assertTrue(domain_match('example.local', '.local'))
        self.assertFalse(domain_match('blah.blah', ''))
        self.assertFalse(domain_match('', '.rhubarb.rhubarb'))
        self.assertTrue(domain_match('', ''))
        self.assertTrue(user_domain_match('acme.com', 'acme.com'))
        self.assertFalse(user_domain_match('acme.com', '.acme.com'))
        self.assertTrue(user_domain_match('rhubarb.acme.com', '.acme.com'))
        self.assertTrue(user_domain_match('www.rhubarb.acme.com', '.acme.com'))
        self.assertTrue(user_domain_match('x.y.com', 'x.Y.com'))
        self.assertTrue(user_domain_match('x.y.com', '.Y.com'))
        self.assertFalse(user_domain_match('x.y.com', 'Y.com'))
        self.assertTrue(user_domain_match('y.com', 'Y.com'))
        self.assertFalse(user_domain_match('.y.com', 'Y.com'))
        self.assertTrue(user_domain_match('.y.com', '.Y.com'))
        self.assertTrue(user_domain_match('x.y.com', '.com'))
        self.assertFalse(user_domain_match('x.y.com', 'com'))
        self.assertFalse(user_domain_match('x.y.com', 'm'))
        self.assertFalse(user_domain_match('x.y.com', '.m'))
        self.assertFalse(user_domain_match('x.y.com', ''))
        self.assertFalse(user_domain_match('x.y.com', '.'))
        self.assertTrue(user_domain_match('192.168.1.1', '192.168.1.1'))
        self.assertFalse(user_domain_match('192.168.1.1', '.168.1.1'))
        self.assertFalse(user_domain_match('192.168.1.1', '.'))
        self.assertFalse(user_domain_match('192.168.1.1', ''))

    def test_wrong_domain(self):
        c = CookieJar()
        interact_2965(c, 'http://www.nasty.com/',
            'foo=bar; domain=friendly.org; Version="1"')
        self.assertEqual(len(c), 0)

    def test_strict_domain(self):
        cp = DefaultCookiePolicy(strict_domain=True)
        cj = CookieJar(policy=cp)
        interact_netscape(cj, 'http://example.co.uk/', 'no=problemo')
        interact_netscape(cj, 'http://example.co.uk/',
            'okey=dokey; Domain=.example.co.uk')
        self.assertEqual(len(cj), 2)
        for pseudo_tld in ['.co.uk', '.org.za', '.tx.us', '.name.us']:
            interact_netscape(cj, 'http://example.%s/' % pseudo_tld,
                'spam=eggs; Domain=.co.uk')
            self.assertEqual(len(cj), 2)

    def test_two_component_domain_ns(self):
        c = CookieJar()
        interact_netscape(c, 'http://foo.net/', 'ns=bar')
        self.assertEqual(len(c), 1)
        self.assertEqual(c._cookies['foo.net']['/']['ns'].value, 'bar')
        self.assertEqual(interact_netscape(c, 'http://foo.net/'), 'ns=bar')
        self.assertEqual(interact_netscape(c, 'http://www.foo.net/'), 'ns=bar')
        pol = DefaultCookiePolicy(strict_ns_domain=DefaultCookiePolicy.
            DomainStrictNonDomain)
        c.set_policy(pol)
        self.assertEqual(interact_netscape(c, 'http://www.foo.net/'), '')
        interact_netscape(c, 'http://foo.net/foo/',
            'spam1=eggs; domain=foo.net')
        interact_netscape(c, 'http://foo.net/foo/bar/',
            'spam2=eggs; domain=.foo.net')
        self.assertEqual(len(c), 3)
        self.assertEqual(c._cookies['.foo.net']['/foo']['spam1'].value, 'eggs')
        self.assertEqual(c._cookies['.foo.net']['/foo/bar']['spam2'].value,
            'eggs')
        self.assertEqual(interact_netscape(c, 'http://foo.net/foo/bar/'),
            'spam2=eggs; spam1=eggs; ns=bar')
        interact_netscape(c, 'http://foo.net/', 'nini="ni"; domain=.net')
        self.assertEqual(len(c), 3)
        interact_netscape(c, 'http://foo.co.uk', 'nasty=trick; domain=.co.uk')
        self.assertEqual(len(c), 4)

    def test_two_component_domain_rfc2965(self):
        pol = DefaultCookiePolicy(rfc2965=True)
        c = CookieJar(pol)
        interact_2965(c, 'http://foo.net/', 'foo=bar; Version="1"')
        self.assertEqual(len(c), 1)
        self.assertEqual(c._cookies['foo.net']['/']['foo'].value, 'bar')
        self.assertEqual(interact_2965(c, 'http://foo.net/'),
            '$Version=1; foo=bar')
        self.assertEqual(interact_2965(c, 'http://www.foo.net/'), '')
        interact_2965(c, 'http://foo.net/foo',
            'spam=eggs; domain=foo.net; path=/foo; Version="1"')
        self.assertEqual(len(c), 1)
        self.assertEqual(interact_2965(c, 'http://foo.net/foo'),
            '$Version=1; foo=bar')
        interact_2965(c, 'http://www.foo.net/foo/',
            'spam=eggs; domain=foo.net; Version="1"')
        self.assertEqual(c._cookies['.foo.net']['/foo/']['spam'].value, 'eggs')
        self.assertEqual(len(c), 2)
        self.assertEqual(interact_2965(c, 'http://foo.net/foo/'),
            '$Version=1; foo=bar')
        self.assertEqual(interact_2965(c, 'http://www.foo.net/foo/'),
            '$Version=1; spam=eggs; $Domain="foo.net"')
        interact_2965(c, 'http://foo.net/',
            'ni="ni"; domain=".net"; Version="1"')
        self.assertEqual(len(c), 2)
        interact_2965(c, 'http://foo.co.uk/',
            'nasty=trick; domain=.co.uk; Version="1"')
        self.assertEqual(len(c), 3)

    def test_domain_allow(self):
        c = CookieJar(policy=DefaultCookiePolicy(blocked_domains=[
            'acme.com'], allowed_domains=['www.acme.com']))
        req = urllib.request.Request('http://acme.com/')
        headers = ['Set-Cookie: CUSTOMER=WILE_E_COYOTE; path=/']
        res = FakeResponse(headers, 'http://acme.com/')
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 0)
        req = urllib.request.Request('http://www.acme.com/')
        res = FakeResponse(headers, 'http://www.acme.com/')
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)
        req = urllib.request.Request('http://www.coyote.com/')
        res = FakeResponse(headers, 'http://www.coyote.com/')
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)
        req = urllib.request.Request('http://www.coyote.com/')
        res = FakeResponse(headers, 'http://www.coyote.com/')
        cookies = c.make_cookies(res, req)
        c.set_cookie(cookies[0])
        self.assertEqual(len(c), 2)
        c.add_cookie_header(req)
        self.assertFalse(req.has_header('Cookie'))

    def test_domain_block(self):
        pol = DefaultCookiePolicy(rfc2965=True, blocked_domains=['.acme.com'])
        c = CookieJar(policy=pol)
        headers = ['Set-Cookie: CUSTOMER=WILE_E_COYOTE; path=/']
        req = urllib.request.Request('http://www.acme.com/')
        res = FakeResponse(headers, 'http://www.acme.com/')
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 0)
        p = pol.set_blocked_domains(['acme.com'])
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)
        c.clear()
        req = urllib.request.Request('http://www.roadrunner.net/')
        res = FakeResponse(headers, 'http://www.roadrunner.net/')
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)
        req = urllib.request.Request('http://www.roadrunner.net/')
        c.add_cookie_header(req)
        self.assertTrue(req.has_header('Cookie'))
        self.assertTrue(req.has_header('Cookie2'))
        c.clear()
        pol.set_blocked_domains(['.acme.com'])
        c.extract_cookies(res, req)
        self.assertEqual(len(c), 1)
        req = urllib.request.Request('http://www.acme.com/')
        res = FakeResponse(headers, 'http://www.acme.com/')
        cookies = c.make_cookies(res, req)
        c.set_cookie(cookies[0])
        self.assertEqual(len(c), 2)
        c.add_cookie_header(req)
        self.assertFalse(req.has_header('Cookie'))

    def test_secure(self):
        for ns in (True, False):
            for whitespace in (' ', ''):
                c = CookieJar()
                if ns:
                    pol = DefaultCookiePolicy(rfc2965=False)
                    int = interact_netscape
                    vs = ''
                else:
                    pol = DefaultCookiePolicy(rfc2965=True)
                    int = interact_2965
                    vs = '; Version=1'
                c.set_policy(pol)
                url = 'http://www.acme.com/'
                int(c, url, 'foo1=bar%s%s' % (vs, whitespace))
                int(c, url, 'foo2=bar%s; secure%s' % (vs, whitespace))
                self.assertFalse(c._cookies['www.acme.com']['/']['foo1'].
                    secure, 'non-secure cookie registered secure')
                self.assertTrue(c._cookies['www.acme.com']['/']['foo2'].
                    secure, 'secure cookie registered non-secure')

    def test_quote_cookie_value(self):
        c = CookieJar(policy=DefaultCookiePolicy(rfc2965=True))
        interact_2965(c, 'http://www.acme.com/', 'foo=\\b"a"r; Version=1')
        h = interact_2965(c, 'http://www.acme.com/')
        self.assertEqual(h, '$Version=1; foo=\\\\b\\"a\\"r')

    def test_missing_final_slash(self):
        url = 'http://www.acme.com'
        c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        interact_2965(c, url, 'foo=bar; Version=1')
        req = urllib.request.Request(url)
        self.assertEqual(len(c), 1)
        c.add_cookie_header(req)
        self.assertTrue(req.has_header('Cookie'))

    def test_domain_mirror(self):
        pol = DefaultCookiePolicy(rfc2965=True)
        c = CookieJar(pol)
        url = 'http://foo.bar.com/'
        interact_2965(c, url, 'spam=eggs; Version=1')
        h = interact_2965(c, url)
        self.assertNotIn('Domain', h,
            'absent domain returned with domain present')
        c = CookieJar(pol)
        url = 'http://foo.bar.com/'
        interact_2965(c, url, 'spam=eggs; Version=1; Domain=.bar.com')
        h = interact_2965(c, url)
        self.assertIn('$Domain=".bar.com"', h, 'domain not returned')
        c = CookieJar(pol)
        url = 'http://foo.bar.com/'
        interact_2965(c, url, 'spam=eggs; Version=1; Domain=bar.com')
        h = interact_2965(c, url)
        self.assertIn('$Domain="bar.com"', h, 'domain not returned')

    def test_path_mirror(self):
        pol = DefaultCookiePolicy(rfc2965=True)
        c = CookieJar(pol)
        url = 'http://foo.bar.com/'
        interact_2965(c, url, 'spam=eggs; Version=1')
        h = interact_2965(c, url)
        self.assertNotIn('Path', h, 'absent path returned with path present')
        c = CookieJar(pol)
        url = 'http://foo.bar.com/'
        interact_2965(c, url, 'spam=eggs; Version=1; Path=/')
        h = interact_2965(c, url)
        self.assertIn('$Path="/"', h, 'path not returned')

    def test_port_mirror(self):
        pol = DefaultCookiePolicy(rfc2965=True)
        c = CookieJar(pol)
        url = 'http://foo.bar.com/'
        interact_2965(c, url, 'spam=eggs; Version=1')
        h = interact_2965(c, url)
        self.assertNotIn('Port', h, 'absent port returned with port present')
        c = CookieJar(pol)
        url = 'http://foo.bar.com/'
        interact_2965(c, url, 'spam=eggs; Version=1; Port')
        h = interact_2965(c, url)
        self.assertRegex(h, '\\$Port([^=]|$)',
            'port with no value not returned with no value')
        c = CookieJar(pol)
        url = 'http://foo.bar.com/'
        interact_2965(c, url, 'spam=eggs; Version=1; Port="80"')
        h = interact_2965(c, url)
        self.assertIn('$Port="80"', h,
            'port with single value not returned with single value')
        c = CookieJar(pol)
        url = 'http://foo.bar.com/'
        interact_2965(c, url, 'spam=eggs; Version=1; Port="80,8080"')
        h = interact_2965(c, url)
        self.assertIn('$Port="80,8080"', h,
            'port with multiple values not returned with multiple values')

    def test_no_return_comment(self):
        c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        url = 'http://foo.bar.com/'
        interact_2965(c, url,
            'spam=eggs; Version=1; Comment="does anybody read these?"; CommentURL="http://foo.bar.net/comment.html"'
            )
        h = interact_2965(c, url)
        self.assertNotIn('Comment', h,
            'Comment or CommentURL cookie-attributes returned to server')

    def test_Cookie_iterator(self):
        cs = CookieJar(DefaultCookiePolicy(rfc2965=True))
        interact_2965(cs, 'http://blah.spam.org/',
            'foo=eggs; Version=1; Comment="does anybody read these?"; CommentURL="http://foo.bar.net/comment.html"'
            )
        interact_netscape(cs, 'http://www.acme.com/blah/', 'spam=bar; secure')
        interact_2965(cs, 'http://www.acme.com/blah/',
            'foo=bar; secure; Version=1')
        interact_2965(cs, 'http://www.acme.com/blah/',
            'foo=bar; path=/; Version=1')
        interact_2965(cs, 'http://www.sol.no',
            'bang=wallop; version=1; domain=".sol.no"; port="90,100, 80,8080"; max-age=100; Comment = "Just kidding! (\\"|\\\\\\\\) "'
            )
        versions = [1, 1, 1, 0, 1]
        names = ['bang', 'foo', 'foo', 'spam', 'foo']
        domains = ['.sol.no', 'blah.spam.org', 'www.acme.com',
            'www.acme.com', 'www.acme.com']
        paths = ['/', '/', '/', '/blah', '/blah/']
        for i in range(4):
            i = 0
            for c in cs:
                self.assertIsInstance(c, Cookie)
                self.assertEqual(c.version, versions[i])
                self.assertEqual(c.name, names[i])
                self.assertEqual(c.domain, domains[i])
                self.assertEqual(c.path, paths[i])
                i = i + 1

    def test_parse_ns_headers(self):
        self.assertEqual(parse_ns_headers(['foo=bar; path=/; domain']), [[(
            'foo', 'bar'), ('path', '/'), ('domain', None), ('version', '0')]])
        self.assertEqual(parse_ns_headers([
            'foo=bar; expires=Foo Bar 12 33:22:11 2000']), [[('foo', 'bar'),
            ('expires', None), ('version', '0')]])
        self.assertEqual(parse_ns_headers(['foo']), [[('foo', None), (
            'version', '0')]])
        self.assertEqual(parse_ns_headers(['foo=bar; expires']), [[('foo',
            'bar'), ('expires', None), ('version', '0')]])
        self.assertEqual(parse_ns_headers(['foo=bar; version']), [[('foo',
            'bar'), ('version', None)]])
        self.assertEqual(parse_ns_headers(['']), [])

    def test_bad_cookie_header(self):

        def cookiejar_from_cookie_headers(headers):
            c = CookieJar()
            req = urllib.request.Request('http://www.example.com/')
            r = FakeResponse(headers, 'http://www.example.com/')
            c.extract_cookies(r, req)
            return c
        future = time2netscape(time.time() + 3600)
        for headers in [['Set-Cookie: '], ['Set-Cookie2: '], [
            'Set-Cookie2: a=foo; path=/; Version=1; domain'], [
            'Set-Cookie: b=foo; max-age=oops'], [
            'Set-Cookie: b=foo; version=spam'], ['Set-Cookie:; Expires=%s' %
            future]]:
            c = cookiejar_from_cookie_headers(headers)
            self.assertEqual(len(c), 0)
        headers = ['Set-Cookie: c=foo; expires=Foo Bar 12 33:22:11 2000']
        c = cookiejar_from_cookie_headers(headers)
        cookie = c._cookies['www.example.com']['/']['c']
        self.assertIsNone(cookie.expires)


class LWPCookieTests(unittest.TestCase):

    def test_netscape_example_1(self):
        year_plus_one = time.localtime()[0] + 1
        headers = []
        c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        req = urllib.request.Request('http://www.acme.com:80/', headers={
            'Host': 'www.acme.com:80'})
        headers.append(
            'Set-Cookie: CUSTOMER=WILE_E_COYOTE; path=/ ; expires=Wednesday, 09-Nov-%d 23:12:40 GMT'
             % year_plus_one)
        res = FakeResponse(headers, 'http://www.acme.com/')
        c.extract_cookies(res, req)
        req = urllib.request.Request('http://www.acme.com/')
        c.add_cookie_header(req)
        self.assertEqual(req.get_header('Cookie'), 'CUSTOMER=WILE_E_COYOTE')
        self.assertEqual(req.get_header('Cookie2'), '$Version="1"')
        headers.append('Set-Cookie: PART_NUMBER=ROCKET_LAUNCHER_0001; path=/')
        res = FakeResponse(headers, 'http://www.acme.com/')
        c.extract_cookies(res, req)
        req = urllib.request.Request('http://www.acme.com/foo/bar')
        c.add_cookie_header(req)
        h = req.get_header('Cookie')
        self.assertIn('PART_NUMBER=ROCKET_LAUNCHER_0001', h)
        self.assertIn('CUSTOMER=WILE_E_COYOTE', h)
        headers.append('Set-Cookie: SHIPPING=FEDEX; path=/foo')
        res = FakeResponse(headers, 'http://www.acme.com')
        c.extract_cookies(res, req)
        req = urllib.request.Request('http://www.acme.com/')
        c.add_cookie_header(req)
        h = req.get_header('Cookie')
        self.assertIn('PART_NUMBER=ROCKET_LAUNCHER_0001', h)
        self.assertIn('CUSTOMER=WILE_E_COYOTE', h)
        self.assertNotIn('SHIPPING=FEDEX', h)
        req = urllib.request.Request('http://www.acme.com/foo/')
        c.add_cookie_header(req)
        h = req.get_header('Cookie')
        self.assertIn('PART_NUMBER=ROCKET_LAUNCHER_0001', h)
        self.assertIn('CUSTOMER=WILE_E_COYOTE', h)
        self.assertTrue(h.startswith('SHIPPING=FEDEX;'))

    def test_netscape_example_2(self):
        c = CookieJar()
        headers = []
        req = urllib.request.Request('http://www.acme.com/')
        headers.append('Set-Cookie: PART_NUMBER=ROCKET_LAUNCHER_0001; path=/')
        res = FakeResponse(headers, 'http://www.acme.com/')
        c.extract_cookies(res, req)
        req = urllib.request.Request('http://www.acme.com/')
        c.add_cookie_header(req)
        self.assertEqual(req.get_header('Cookie'),
            'PART_NUMBER=ROCKET_LAUNCHER_0001')
        headers.append('Set-Cookie: PART_NUMBER=RIDING_ROCKET_0023; path=/ammo'
            )
        res = FakeResponse(headers, 'http://www.acme.com/')
        c.extract_cookies(res, req)
        req = urllib.request.Request('http://www.acme.com/ammo')
        c.add_cookie_header(req)
        self.assertRegex(req.get_header('Cookie'),
            'PART_NUMBER=RIDING_ROCKET_0023;\\s*PART_NUMBER=ROCKET_LAUNCHER_0001'
            )

    def test_ietf_example_1(self):
        c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        cookie = interact_2965(c, 'http://www.acme.com/acme/login',
            'Customer="WILE_E_COYOTE"; Version="1"; Path="/acme"')
        self.assertFalse(cookie)
        cookie = interact_2965(c, 'http://www.acme.com/acme/pickitem',
            'Part_Number="Rocket_Launcher_0001"; Version="1"; Path="/acme"')
        self.assertRegex(cookie,
            '^\\$Version="?1"?; Customer="?WILE_E_COYOTE"?; \\$Path="/acme"$')
        cookie = interact_2965(c, 'http://www.acme.com/acme/shipping',
            'Shipping="FedEx"; Version="1"; Path="/acme"')
        self.assertRegex(cookie, '^\\$Version="?1"?;')
        self.assertRegex(cookie,
            'Part_Number="?Rocket_Launcher_0001"?;\\s*\\$Path="\\/acme"')
        self.assertRegex(cookie,
            'Customer="?WILE_E_COYOTE"?;\\s*\\$Path="\\/acme"')
        cookie = interact_2965(c, 'http://www.acme.com/acme/process')
        self.assertRegex(cookie, 'Shipping="?FedEx"?;\\s*\\$Path="\\/acme"')
        self.assertIn('WILE_E_COYOTE', cookie)

    def test_ietf_example_2(self):
        c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        interact_2965(c, 'http://www.acme.com/acme/ammo/specific',
            'Part_Number="Rocket_Launcher_0001"; Version="1"; Path="/acme"',
            'Part_Number="Riding_Rocket_0023"; Version="1"; Path="/acme/ammo"')
        cookie = interact_2965(c, 'http://www.acme.com/acme/ammo/...')
        self.assertRegex(cookie, 'Riding_Rocket_0023.*Rocket_Launcher_0001')
        cookie = interact_2965(c, 'http://www.acme.com/acme/parts/')
        self.assertIn('Rocket_Launcher_0001', cookie)
        self.assertNotIn('Riding_Rocket_0023', cookie)

    def test_rejection(self):
        pol = DefaultCookiePolicy(rfc2965=True)
        c = LWPCookieJar(policy=pol)
        max_age = 'max-age=3600'
        cookie = interact_2965(c, 'http://www.acme.com',
            'foo=bar; domain=".com"; version=1')
        self.assertFalse(c)
        cookie = interact_2965(c, 'http://www.acme.com',
            'ping=pong; domain="acme.com"; version=1')
        self.assertEqual(len(c), 1)
        cookie = interact_2965(c, 'http://www.a.acme.com',
            'whiz=bang; domain="acme.com"; version=1')
        self.assertEqual(len(c), 1)
        cookie = interact_2965(c, 'http://www.a.acme.com',
            'wow=flutter; domain=".a.acme.com"; version=1')
        self.assertEqual(len(c), 2)
        cookie = interact_2965(c, 'http://125.125.125.125',
            'zzzz=ping; domain="125.125.125"; version=1')
        self.assertEqual(len(c), 2)
        cookie = interact_2965(c, 'http://www.sol.no',
            'blah=rhubarb; domain=".sol.no"; path="/foo"; version=1')
        self.assertEqual(len(c), 2)
        cookie = interact_2965(c, 'http://www.sol.no/foo/bar',
            'bing=bong; domain=".sol.no"; path="/foo"; version=1')
        self.assertEqual(len(c), 3)
        cookie = interact_2965(c, 'http://www.sol.no',
            'whiz=ffft; domain=".sol.no"; port="90,100"; version=1')
        self.assertEqual(len(c), 3)
        cookie = interact_2965(c, 'http://www.sol.no',
            'bang=wallop; version=1; domain=".sol.no"; port="90,100, 80,8080"; max-age=100; Comment = "Just kidding! (\\"|\\\\\\\\) "'
            )
        self.assertEqual(len(c), 4)
        cookie = interact_2965(c, 'http://www.sol.no',
            'foo9=bar; version=1; domain=".sol.no"; port; max-age=100;')
        self.assertEqual(len(c), 5)
        cookie = interact_2965(c, 'http://www.sol.no/<oo/',
            'foo8=bar; version=1; path="/%3coo"')
        self.assertEqual(len(c), 6)
        filename = test.support.TESTFN
        try:
            c.save(filename, ignore_discard=True)
            old = repr(c)
            c = LWPCookieJar(policy=pol)
            c.load(filename, ignore_discard=True)
        finally:
            try:
                os.unlink(filename)
            except OSError:
                pass
        self.assertEqual(old, repr(c))

    def test_url_encoding(self):
        c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        interact_2965(c,
            'http://www.acme.com/foo%2f%25/%3c%3c%0Anew%C3%A5/%C3%A5',
            'foo  =   bar; version    =   1')
        cookie = interact_2965(c,
            'http://www.acme.com/foo%2f%25/<<%0anewå/æøå',
            'bar=baz; path="/foo/"; version=1')
        version_re = re.compile('^\\$version=\\"?1\\"?', re.I)
        self.assertIn('foo=bar', cookie)
        self.assertRegex(cookie, version_re)
        cookie = interact_2965(c, 'http://www.acme.com/foo/%25/<<%0anewå/æøå')
        self.assertFalse(cookie)
        cookie = interact_2965(c, 'http://www.acme.com/ü')

    def test_mozilla(self):
        year_plus_one = time.localtime()[0] + 1
        filename = test.support.TESTFN
        c = MozillaCookieJar(filename, policy=DefaultCookiePolicy(rfc2965=True)
            )
        interact_2965(c, 'http://www.acme.com/',
            'foo1=bar; max-age=100; Version=1')
        interact_2965(c, 'http://www.acme.com/',
            'foo2=bar; port="80"; max-age=100; Discard; Version=1')
        interact_2965(c, 'http://www.acme.com/', 'foo3=bar; secure; Version=1')
        expires = 'expires=09-Nov-%d 23:12:40 GMT' % (year_plus_one,)
        interact_netscape(c, 'http://www.foo.com/', 'fooa=bar; %s' % expires)
        interact_netscape(c, 'http://www.foo.com/', 
            'foob=bar; Domain=.foo.com; %s' % expires)
        interact_netscape(c, 'http://www.foo.com/', 
            'fooc=bar; Domain=www.foo.com; %s' % expires)

        def save_and_restore(cj, ignore_discard):
            try:
                cj.save(ignore_discard=ignore_discard)
                new_c = MozillaCookieJar(filename, DefaultCookiePolicy(
                    rfc2965=True))
                new_c.load(ignore_discard=ignore_discard)
            finally:
                try:
                    os.unlink(filename)
                except OSError:
                    pass
            return new_c
        new_c = save_and_restore(c, True)
        self.assertEqual(len(new_c), 6)
        self.assertIn("name='foo1', value='bar'", repr(new_c))
        new_c = save_and_restore(c, False)
        self.assertEqual(len(new_c), 4)
        self.assertIn("name='foo1', value='bar'", repr(new_c))

    def test_netscape_misc(self):
        c = CookieJar()
        headers = []
        req = urllib.request.Request('http://foo.bar.acme.com/foo')
        headers.append('Set-Cookie: Customer=WILE_E_COYOTE; domain=.acme.com')
        res = FakeResponse(headers, 'http://www.acme.com/foo')
        c.extract_cookies(res, req)
        headers.append('Set-Cookie: PART_NUMBER=3,4; domain=foo.bar.acme.com')
        res = FakeResponse(headers, 'http://www.acme.com/foo')
        c.extract_cookies(res, req)
        req = urllib.request.Request('http://foo.bar.acme.com/foo')
        c.add_cookie_header(req)
        self.assertIn('PART_NUMBER=3,4', req.get_header('Cookie'))
        self.assertIn('Customer=WILE_E_COYOTE', req.get_header('Cookie'))

    def test_intranet_domains_2965(self):
        c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        interact_2965(c, 'http://example/',
            'foo1=bar; PORT; Discard; Version=1;')
        cookie = interact_2965(c, 'http://example/',
            'foo2=bar; domain=".local"; Version=1')
        self.assertIn('foo1=bar', cookie)
        interact_2965(c, 'http://example/', 'foo3=bar; Version=1')
        cookie = interact_2965(c, 'http://example/')
        self.assertIn('foo2=bar', cookie)
        self.assertEqual(len(c), 3)

    def test_intranet_domains_ns(self):
        c = CookieJar(DefaultCookiePolicy(rfc2965=False))
        interact_netscape(c, 'http://example/', 'foo1=bar')
        cookie = interact_netscape(c, 'http://example/',
            'foo2=bar; domain=.local')
        self.assertEqual(len(c), 2)
        self.assertIn('foo1=bar', cookie)
        cookie = interact_netscape(c, 'http://example/')
        self.assertIn('foo2=bar', cookie)
        self.assertEqual(len(c), 2)

    def test_empty_path(self):
        c = CookieJar(DefaultCookiePolicy(rfc2965=True))
        headers = []
        req = urllib.request.Request('http://www.ants.com/')
        headers.append('Set-Cookie: JSESSIONID=ABCDERANDOM123; Path=')
        res = FakeResponse(headers, 'http://www.ants.com/')
        c.extract_cookies(res, req)
        req = urllib.request.Request('http://www.ants.com/')
        c.add_cookie_header(req)
        self.assertEqual(req.get_header('Cookie'), 'JSESSIONID=ABCDERANDOM123')
        self.assertEqual(req.get_header('Cookie2'), '$Version="1"')
        req = urllib.request.Request('http://www.ants.com:8080')
        c.add_cookie_header(req)
        self.assertEqual(req.get_header('Cookie'), 'JSESSIONID=ABCDERANDOM123')
        self.assertEqual(req.get_header('Cookie2'), '$Version="1"')

    def test_session_cookies(self):
        year_plus_one = time.localtime()[0] + 1
        req = urllib.request.Request('http://www.perlmeister.com/scripts')
        headers = []
        headers.append('Set-Cookie: s1=session;Path=/scripts')
        headers.append(
            'Set-Cookie: p1=perm; Domain=.perlmeister.com;Path=/;expires=Fri, 02-Feb-%d 23:24:20 GMT'
             % year_plus_one)
        headers.append(
            'Set-Cookie: p2=perm;Path=/;expires=Fri, 02-Feb-%d 23:24:20 GMT' %
            year_plus_one)
        headers.append(
            'Set-Cookie: s2=session;Path=/scripts;Domain=.perlmeister.com')
        headers.append('Set-Cookie2: s3=session;Version=1;Discard;Path="/"')
        res = FakeResponse(headers, 'http://www.perlmeister.com/scripts')
        c = CookieJar()
        c.extract_cookies(res, req)
        counter = {'session_after': 0, 'perm_after': 0, 'session_before': 0,
            'perm_before': 0}
        for cookie in c:
            key = '%s_before' % cookie.value
            counter[key] = counter[key] + 1
        c.clear_session_cookies()
        for cookie in c:
            key = '%s_after' % cookie.value
            counter[key] = counter[key] + 1
        self.assertEqual(counter['perm_after'], counter['perm_before'])
        self.assertEqual(counter['session_after'], 0)
        self.assertNotEqual(counter['session_before'], 0)


def test_main(verbose=None):
    test.support.run_unittest(DateTimeTests, HeaderTests, CookieTests,
        FileCookieJarTests, LWPCookieTests)


if __name__ == '__main__':
    test_main(verbose=True)
