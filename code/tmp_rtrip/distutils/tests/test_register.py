"""Tests for distutils.command.register."""
import os
import unittest
import getpass
import urllib
import warnings
from test.support import check_warnings, run_unittest
from distutils.command import register as register_module
from distutils.command.register import register
from distutils.errors import DistutilsSetupError
from distutils.log import INFO
from distutils.tests.test_config import BasePyPIRCCommandTestCase
try:
    import docutils
except ImportError:
    docutils = None
PYPIRC_NOPASSWORD = """[distutils]

index-servers =
    server1

[server1]
username:me
"""
WANTED_PYPIRC = """[distutils]
index-servers =
    pypi

[pypi]
username:tarek
password:password
"""


class Inputs(object):
    """Fakes user inputs."""

    def __init__(self, *answers):
        self.answers = answers
        self.index = 0

    def __call__(self, prompt=''):
        try:
            return self.answers[self.index]
        finally:
            self.index += 1


class FakeOpener(object):
    """Fakes a PyPI server"""

    def __init__(self):
        self.reqs = []

    def __call__(self, *args):
        return self

    def open(self, req, data=None, timeout=None):
        self.reqs.append(req)
        return self

    def read(self):
        return b'xxx'

    def getheader(self, name, default=None):
        return {'content-type': 'text/plain; charset=utf-8'}.get(name.lower
            (), default)


class RegisterTestCase(BasePyPIRCCommandTestCase):

    def setUp(self):
        super(RegisterTestCase, self).setUp()
        self._old_getpass = getpass.getpass

        def _getpass(prompt):
            return 'password'
        getpass.getpass = _getpass
        urllib.request._opener = None
        self.old_opener = urllib.request.build_opener
        self.conn = urllib.request.build_opener = FakeOpener()

    def tearDown(self):
        getpass.getpass = self._old_getpass
        urllib.request._opener = None
        urllib.request.build_opener = self.old_opener
        super(RegisterTestCase, self).tearDown()

    def _get_cmd(self, metadata=None):
        if metadata is None:
            metadata = {'url': 'xxx', 'author': 'xxx', 'author_email':
                'xxx', 'name': 'xxx', 'version': 'xxx'}
        pkg_info, dist = self.create_dist(**metadata)
        return register(dist)

    def test_create_pypirc(self):
        cmd = self._get_cmd()
        self.assertFalse(os.path.exists(self.rc))
        inputs = Inputs('1', 'tarek', 'y')
        register_module.input = inputs.__call__
        try:
            cmd.run()
        finally:
            del register_module.input
        self.assertTrue(os.path.exists(self.rc))
        f = open(self.rc)
        try:
            content = f.read()
            self.assertEqual(content, WANTED_PYPIRC)
        finally:
            f.close()

        def _no_way(prompt=''):
            raise AssertionError(prompt)
        register_module.input = _no_way
        cmd.show_response = 1
        cmd.run()
        self.assertEqual(len(self.conn.reqs), 2)
        req1 = dict(self.conn.reqs[0].headers)
        req2 = dict(self.conn.reqs[1].headers)
        self.assertEqual(req1['Content-length'], '1374')
        self.assertEqual(req2['Content-length'], '1374')
        self.assertIn(b'xxx', self.conn.reqs[1].data)

    def test_password_not_in_file(self):
        self.write_file(self.rc, PYPIRC_NOPASSWORD)
        cmd = self._get_cmd()
        cmd._set_config()
        cmd.finalize_options()
        cmd.send_metadata()
        self.assertEqual(cmd.distribution.password, 'password')

    def test_registering(self):
        cmd = self._get_cmd()
        inputs = Inputs('2', 'tarek', 'tarek@ziade.org')
        register_module.input = inputs.__call__
        try:
            cmd.run()
        finally:
            del register_module.input
        self.assertEqual(len(self.conn.reqs), 1)
        req = self.conn.reqs[0]
        headers = dict(req.headers)
        self.assertEqual(headers['Content-length'], '608')
        self.assertIn(b'tarek', req.data)

    def test_password_reset(self):
        cmd = self._get_cmd()
        inputs = Inputs('3', 'tarek@ziade.org')
        register_module.input = inputs.__call__
        try:
            cmd.run()
        finally:
            del register_module.input
        self.assertEqual(len(self.conn.reqs), 1)
        req = self.conn.reqs[0]
        headers = dict(req.headers)
        self.assertEqual(headers['Content-length'], '290')
        self.assertIn(b'tarek', req.data)

    @unittest.skipUnless(docutils is not None, 'needs docutils')
    def test_strict(self):
        cmd = self._get_cmd({})
        cmd.ensure_finalized()
        cmd.strict = 1
        self.assertRaises(DistutilsSetupError, cmd.run)
        metadata = {'url': 'xxx', 'author': 'xxx', 'author_email': 'éxéxé',
            'name': 'xxx', 'version': 'xxx', 'long_description':
            'title\n==\n\ntext'}
        cmd = self._get_cmd(metadata)
        cmd.ensure_finalized()
        cmd.strict = 1
        self.assertRaises(DistutilsSetupError, cmd.run)
        metadata['long_description'] = 'title\n=====\n\ntext'
        cmd = self._get_cmd(metadata)
        cmd.ensure_finalized()
        cmd.strict = 1
        inputs = Inputs('1', 'tarek', 'y')
        register_module.input = inputs.__call__
        try:
            cmd.run()
        finally:
            del register_module.input
        cmd = self._get_cmd()
        cmd.ensure_finalized()
        inputs = Inputs('1', 'tarek', 'y')
        register_module.input = inputs.__call__
        try:
            cmd.run()
        finally:
            del register_module.input
        metadata = {'url': 'xxx', 'author': 'Éric', 'author_email': 'xxx',
            'name': 'xxx', 'version': 'xxx', 'description':
            'Something about esszet ß', 'long_description':
            'More things about esszet ß'}
        cmd = self._get_cmd(metadata)
        cmd.ensure_finalized()
        cmd.strict = 1
        inputs = Inputs('1', 'tarek', 'y')
        register_module.input = inputs.__call__
        try:
            cmd.run()
        finally:
            del register_module.input

    @unittest.skipUnless(docutils is not None, 'needs docutils')
    def test_register_invalid_long_description(self):
        description = ':funkie:`str`'
        metadata = {'url': 'xxx', 'author': 'xxx', 'author_email': 'xxx',
            'name': 'xxx', 'version': 'xxx', 'long_description': description}
        cmd = self._get_cmd(metadata)
        cmd.ensure_finalized()
        cmd.strict = True
        inputs = Inputs('2', 'tarek', 'tarek@ziade.org')
        register_module.input = inputs
        self.addCleanup(delattr, register_module, 'input')
        self.assertRaises(DistutilsSetupError, cmd.run)

    def test_check_metadata_deprecated(self):
        cmd = self._get_cmd()
        with check_warnings() as w:
            warnings.simplefilter('always')
            cmd.check_metadata()
            self.assertEqual(len(w.warnings), 1)

    def test_list_classifiers(self):
        cmd = self._get_cmd()
        cmd.list_classifiers = 1
        cmd.run()
        results = self.get_logs(INFO)
        self.assertEqual(results, ['running check', 'xxx'])

    def test_show_response(self):
        cmd = self._get_cmd()
        inputs = Inputs('1', 'tarek', 'y')
        register_module.input = inputs.__call__
        cmd.show_response = 1
        try:
            cmd.run()
        finally:
            del register_module.input
        results = self.get_logs(INFO)
        self.assertEqual(results[3], 75 * '-' + '\nxxx\n' + 75 * '-')


def test_suite():
    return unittest.makeSuite(RegisterTestCase)


if __name__ == '__main__':
    run_unittest(test_suite())
