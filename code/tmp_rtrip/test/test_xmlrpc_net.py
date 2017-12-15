import collections.abc
import unittest
from test import support
import xmlrpc.client as xmlrpclib


class PythonBuildersTest(unittest.TestCase):

    def test_python_builders(self):
        server = xmlrpclib.ServerProxy('http://buildbot.python.org/all/xmlrpc/'
            )
        try:
            builders = server.getAllBuilders()
        except OSError as e:
            self.skipTest('network error: %s' % e)
        self.addCleanup(lambda : server('close')())
        self.assertIsInstance(builders, collections.abc.Sequence)
        self.assertTrue([x for x in builders if '3.x' in x], builders)


def test_main():
    support.requires('network')
    support.run_unittest(PythonBuildersTest)


if __name__ == '__main__':
    test_main()
