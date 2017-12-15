import io
import os
import unittest
import urllib.robotparser
from collections import namedtuple
from test import support
from http.server import BaseHTTPRequestHandler, HTTPServer
try:
    import threading
except ImportError:
    threading = None


class BaseRobotTest:
    robots_txt = ''
    agent = 'test_robotparser'
    good = []
    bad = []

    def setUp(self):
        lines = io.StringIO(self.robots_txt).readlines()
        self.parser = urllib.robotparser.RobotFileParser()
        self.parser.parse(lines)

    def get_agent_and_url(self, url):
        if isinstance(url, tuple):
            agent, url = url
            return agent, url
        return self.agent, url

    def test_good_urls(self):
        for url in self.good:
            agent, url = self.get_agent_and_url(url)
            with self.subTest(url=url, agent=agent):
                self.assertTrue(self.parser.can_fetch(agent, url))

    def test_bad_urls(self):
        for url in self.bad:
            agent, url = self.get_agent_and_url(url)
            with self.subTest(url=url, agent=agent):
                self.assertFalse(self.parser.can_fetch(agent, url))


class UserAgentWildcardTest(BaseRobotTest, unittest.TestCase):
    robots_txt = """User-agent: *
Disallow: /cyberworld/map/ # This is an infinite virtual URL space
Disallow: /tmp/ # these will soon disappear
Disallow: /foo.html
    """
    good = ['/', '/test.html']
    bad = ['/cyberworld/map/index.html', '/tmp/xxx', '/foo.html']


class CrawlDelayAndCustomAgentTest(BaseRobotTest, unittest.TestCase):
    robots_txt = """# robots.txt for http://www.example.com/

User-agent: *
Crawl-delay: 1
Request-rate: 3/15
Disallow: /cyberworld/map/ # This is an infinite virtual URL space

# Cybermapper knows where to go.
User-agent: cybermapper
Disallow:
    """
    good = ['/', '/test.html', ('cybermapper', '/cyberworld/map/index.html')]
    bad = ['/cyberworld/map/index.html']


class RejectAllRobotsTest(BaseRobotTest, unittest.TestCase):
    robots_txt = '# go away\nUser-agent: *\nDisallow: /\n    '
    good = []
    bad = ['/cyberworld/map/index.html', '/', '/tmp/']


class BaseRequestRateTest(BaseRobotTest):

    def test_request_rate(self):
        for url in (self.good + self.bad):
            agent, url = self.get_agent_and_url(url)
            with self.subTest(url=url, agent=agent):
                if self.crawl_delay:
                    self.assertEqual(self.parser.crawl_delay(agent), self.
                        crawl_delay)
                if self.request_rate:
                    self.assertEqual(self.parser.request_rate(agent).
                        requests, self.request_rate.requests)
                    self.assertEqual(self.parser.request_rate(agent).
                        seconds, self.request_rate.seconds)


class CrawlDelayAndRequestRateTest(BaseRequestRateTest, unittest.TestCase):
    robots_txt = """User-agent: figtree
Crawl-delay: 3
Request-rate: 9/30
Disallow: /tmp
Disallow: /a%3cd.html
Disallow: /a%2fb.html
Disallow: /%7ejoe/index.html
    """
    agent = 'figtree'
    request_rate = namedtuple('req_rate', 'requests seconds')(9, 30)
    crawl_delay = 3
    good = [('figtree', '/foo.html')]
    bad = ['/tmp', '/tmp.html', '/tmp/a.html', '/a%3cd.html', '/a%3Cd.html',
        '/a%2fb.html', '/~joe/index.html']


class DifferentAgentTest(CrawlDelayAndRequestRateTest):
    agent = 'FigTree Robot libwww-perl/5.04'
    request_rate = None
    crawl_delay = None


class InvalidRequestRateTest(BaseRobotTest, unittest.TestCase):
    robots_txt = """User-agent: *
Disallow: /tmp/
Disallow: /a%3Cd.html
Disallow: /a/b.html
Disallow: /%7ejoe/index.html
Crawl-delay: 3
Request-rate: 9/banana
    """
    good = ['/tmp']
    bad = ['/tmp/', '/tmp/a.html', '/a%3cd.html', '/a%3Cd.html',
        '/a/b.html', '/%7Ejoe/index.html']
    crawl_delay = 3


class InvalidCrawlDelayTest(BaseRobotTest, unittest.TestCase):
    robots_txt = 'User-Agent: *\nDisallow: /.\nCrawl-delay: pears\n    '
    good = ['/foo.html']
    bad = []


class AnotherInvalidRequestRateTest(BaseRobotTest, unittest.TestCase):
    robots_txt = """User-agent: Googlebot
Allow: /folder1/myfile.html
Disallow: /folder1/
Request-rate: whale/banana
    """
    agent = 'Googlebot'
    good = ['/folder1/myfile.html']
    bad = ['/folder1/anotherfile.html']


class UserAgentOrderingTest(BaseRobotTest, unittest.TestCase):
    robots_txt = """User-agent: Googlebot
Disallow: /

User-agent: Googlebot-Mobile
Allow: /
    """
    agent = 'Googlebot'
    bad = ['/something.jpg']


class UserAgentGoogleMobileTest(UserAgentOrderingTest):
    agent = 'Googlebot-Mobile'


class GoogleURLOrderingTest(BaseRobotTest, unittest.TestCase):
    robots_txt = (
        'User-agent: Googlebot\nAllow: /folder1/myfile.html\nDisallow: /folder1/\n    '
        )
    agent = 'googlebot'
    good = ['/folder1/myfile.html']
    bad = ['/folder1/anotherfile.html']


class DisallowQueryStringTest(BaseRobotTest, unittest.TestCase):
    robots_txt = 'User-agent: *\nDisallow: /some/path?name=value\n    '
    good = ['/some/path']
    bad = ['/some/path?name=value']


class UseFirstUserAgentWildcardTest(BaseRobotTest, unittest.TestCase):
    robots_txt = """User-agent: *
Disallow: /some/path

User-agent: *
Disallow: /another/path
    """
    good = ['/another/path']
    bad = ['/some/path']


class EmptyQueryStringTest(BaseRobotTest, unittest.TestCase):
    robots_txt = (
        'User-agent: *\nAllow: /some/path?\nDisallow: /another/path?\n    ')
    good = ['/some/path?']
    bad = ['/another/path?']


class DefaultEntryTest(BaseRequestRateTest, unittest.TestCase):
    robots_txt = """User-agent: *
Crawl-delay: 1
Request-rate: 3/15
Disallow: /cyberworld/map/
    """
    request_rate = namedtuple('req_rate', 'requests seconds')(3, 15)
    crawl_delay = 1
    good = ['/', '/test.html']
    bad = ['/cyberworld/map/index.html']


class RobotHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_error(403, 'Forbidden access')

    def log_message(self, format, *args):
        pass


@unittest.skipUnless(threading, 'threading required for this test')
class PasswordProtectedSiteTestCase(unittest.TestCase):

    def setUp(self):
        self.server = HTTPServer((support.HOST, 0), RobotHandler)
        self.t = threading.Thread(name='HTTPServer serving', target=self.
            server.serve_forever, kwargs={'poll_interval': 0.01})
        self.t.daemon = True
        self.t.start()

    def tearDown(self):
        self.server.shutdown()
        self.t.join()
        self.server.server_close()

    @support.reap_threads
    def testPasswordProtectedSite(self):
        addr = self.server.server_address
        url = 'http://' + support.HOST + ':' + str(addr[1])
        robots_url = url + '/robots.txt'
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(url)
        parser.read()
        self.assertFalse(parser.can_fetch('*', robots_url))


class NetworkTestCase(unittest.TestCase):
    base_url = 'http://www.pythontest.net/'
    robots_txt = '{}elsewhere/robots.txt'.format(base_url)

    @classmethod
    def setUpClass(cls):
        support.requires('network')
        with support.transient_internet(cls.base_url):
            cls.parser = urllib.robotparser.RobotFileParser(cls.robots_txt)
            cls.parser.read()

    def url(self, path):
        return '{}{}{}'.format(self.base_url, path, '/' if not os.path.
            splitext(path)[1] else '')

    def test_basic(self):
        self.assertFalse(self.parser.disallow_all)
        self.assertFalse(self.parser.allow_all)
        self.assertGreater(self.parser.mtime(), 0)
        self.assertFalse(self.parser.crawl_delay('*'))
        self.assertFalse(self.parser.request_rate('*'))

    def test_can_fetch(self):
        self.assertTrue(self.parser.can_fetch('*', self.url('elsewhere')))
        self.assertFalse(self.parser.can_fetch('Nutch', self.base_url))
        self.assertFalse(self.parser.can_fetch('Nutch', self.url('brian')))
        self.assertFalse(self.parser.can_fetch('Nutch', self.url('webstats')))
        self.assertFalse(self.parser.can_fetch('*', self.url('webstats')))
        self.assertTrue(self.parser.can_fetch('*', self.base_url))

    def test_read_404(self):
        parser = urllib.robotparser.RobotFileParser(self.url('i-robot.txt'))
        parser.read()
        self.assertTrue(parser.allow_all)
        self.assertFalse(parser.disallow_all)
        self.assertEqual(parser.mtime(), 0)
        self.assertIsNone(parser.crawl_delay('*'))
        self.assertIsNone(parser.request_rate('*'))


if __name__ == '__main__':
    unittest.main()
