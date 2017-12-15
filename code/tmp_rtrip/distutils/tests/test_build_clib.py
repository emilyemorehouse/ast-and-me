"""Tests for distutils.command.build_clib."""
import unittest
import os
import sys
from test.support import run_unittest, missing_compiler_executable
from distutils.command.build_clib import build_clib
from distutils.errors import DistutilsSetupError
from distutils.tests import support
from distutils.spawn import find_executable


class BuildCLibTestCase(support.TempdirManager, support.LoggingSilencer,
    unittest.TestCase):

    def test_check_library_dist(self):
        pkg_dir, dist = self.create_dist()
        cmd = build_clib(dist)
        self.assertRaises(DistutilsSetupError, cmd.check_library_list, 'foo')
        self.assertRaises(DistutilsSetupError, cmd.check_library_list, [
            'foo1', 'foo2'])
        self.assertRaises(DistutilsSetupError, cmd.check_library_list, [(1,
            'foo1'), ('name', 'foo2')])
        self.assertRaises(DistutilsSetupError, cmd.check_library_list, [(
            'name', 'foo1'), ('another/name', 'foo2')])
        self.assertRaises(DistutilsSetupError, cmd.check_library_list, [(
            'name', {}), ('another', 'foo2')])
        libs = [('name', {}), ('name', {'ok': 'good'})]
        cmd.check_library_list(libs)

    def test_get_source_files(self):
        pkg_dir, dist = self.create_dist()
        cmd = build_clib(dist)
        cmd.libraries = [('name', {})]
        self.assertRaises(DistutilsSetupError, cmd.get_source_files)
        cmd.libraries = [('name', {'sources': 1})]
        self.assertRaises(DistutilsSetupError, cmd.get_source_files)
        cmd.libraries = [('name', {'sources': ['a', 'b']})]
        self.assertEqual(cmd.get_source_files(), ['a', 'b'])
        cmd.libraries = [('name', {'sources': ('a', 'b')})]
        self.assertEqual(cmd.get_source_files(), ['a', 'b'])
        cmd.libraries = [('name', {'sources': ('a', 'b')}), ('name2', {
            'sources': ['c', 'd']})]
        self.assertEqual(cmd.get_source_files(), ['a', 'b', 'c', 'd'])

    def test_build_libraries(self):
        pkg_dir, dist = self.create_dist()
        cmd = build_clib(dist)


        class FakeCompiler:

            def compile(*args, **kw):
                pass
            create_static_lib = compile
        cmd.compiler = FakeCompiler()
        lib = [('name', {'sources': 'notvalid'})]
        self.assertRaises(DistutilsSetupError, cmd.build_libraries, lib)
        lib = [('name', {'sources': list()})]
        cmd.build_libraries(lib)
        lib = [('name', {'sources': tuple()})]
        cmd.build_libraries(lib)

    def test_finalize_options(self):
        pkg_dir, dist = self.create_dist()
        cmd = build_clib(dist)
        cmd.include_dirs = 'one-dir'
        cmd.finalize_options()
        self.assertEqual(cmd.include_dirs, ['one-dir'])
        cmd.include_dirs = None
        cmd.finalize_options()
        self.assertEqual(cmd.include_dirs, [])
        cmd.distribution.libraries = 'WONTWORK'
        self.assertRaises(DistutilsSetupError, cmd.finalize_options)

    @unittest.skipIf(sys.platform == 'win32', "can't test on Windows")
    def test_run(self):
        pkg_dir, dist = self.create_dist()
        cmd = build_clib(dist)
        foo_c = os.path.join(pkg_dir, 'foo.c')
        self.write_file(foo_c, 'int main(void) { return 1;}\n')
        cmd.libraries = [('foo', {'sources': [foo_c]})]
        build_temp = os.path.join(pkg_dir, 'build')
        os.mkdir(build_temp)
        cmd.build_temp = build_temp
        cmd.build_clib = build_temp
        ccmd = missing_compiler_executable()
        if ccmd is not None:
            self.skipTest('The %r command is not found' % ccmd)
        cmd.run()
        self.assertIn('libfoo.a', os.listdir(build_temp))


def test_suite():
    return unittest.makeSuite(BuildCLibTestCase)


if __name__ == '__main__':
    run_unittest(test_suite())
