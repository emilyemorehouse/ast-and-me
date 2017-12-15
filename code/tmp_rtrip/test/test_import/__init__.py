import importlib
import importlib.util
from importlib._bootstrap_external import _get_sourcefile
import builtins
import marshal
import os
import platform
import py_compile
import random
import stat
import sys
import unittest
import unittest.mock as mock
import textwrap
import errno
import shutil
import contextlib
import test.support
from test.support import EnvironmentVarGuard, TESTFN, check_warnings, forget, is_jython, make_legacy_pyc, rmtree, run_unittest, swap_attr, swap_item, temp_umask, unlink, unload, create_empty_file, cpython_only, TESTFN_UNENCODABLE, temp_dir
from test.support import script_helper
skip_if_dont_write_bytecode = unittest.skipIf(sys.dont_write_bytecode,
    'test meaningful only when writing bytecode')


def remove_files(name):
    for f in (name + '.py', name + '.pyc', name + '.pyw', name + '$py.class'):
        unlink(f)
    rmtree('__pycache__')


@contextlib.contextmanager
def _ready_to_import(name=None, source=''):
    name = name or 'spam'
    with temp_dir() as tempdir:
        path = script_helper.make_script(tempdir, name, source)
        old_module = sys.modules.pop(name, None)
        try:
            sys.path.insert(0, tempdir)
            yield name, path
            sys.path.remove(tempdir)
        finally:
            if old_module is not None:
                sys.modules[name] = old_module
            elif name in sys.modules:
                del sys.modules[name]


class ImportTests(unittest.TestCase):

    def setUp(self):
        remove_files(TESTFN)
        importlib.invalidate_caches()

    def tearDown(self):
        unload(TESTFN)

    def test_import_raises_ModuleNotFoundError(self):
        with self.assertRaises(ModuleNotFoundError):
            import something_that_should_not_exist_anywhere

    def test_from_import_missing_module_raises_ModuleNotFoundError(self):
        with self.assertRaises(ModuleNotFoundError):
            from something_that_should_not_exist_anywhere import blah

    def test_from_import_missing_attr_raises_ImportError(self):
        with self.assertRaises(ImportError):
            from importlib import something_that_should_not_exist_anywhere

    def test_case_sensitivity(self):
        with self.assertRaises(ImportError):
            import RAnDoM

    def test_double_const(self):
        from test import double_const

    def test_import(self):

        def test_with_extension(ext):
            source = TESTFN + ext
            if is_jython:
                pyc = TESTFN + '$py.class'
            else:
                pyc = TESTFN + '.pyc'
            with open(source, 'w') as f:
                print("# This tests Python's ability to import a", ext,
                    'file.', file=f)
                a = random.randrange(1000)
                b = random.randrange(1000)
                print('a =', a, file=f)
                print('b =', b, file=f)
            if TESTFN in sys.modules:
                del sys.modules[TESTFN]
            importlib.invalidate_caches()
            try:
                try:
                    mod = __import__(TESTFN)
                except ImportError as err:
                    self.fail('import from %s failed: %s' % (ext, err))
                self.assertEqual(mod.a, a, 
                    'module loaded (%s) but contents invalid' % mod)
                self.assertEqual(mod.b, b, 
                    'module loaded (%s) but contents invalid' % mod)
            finally:
                forget(TESTFN)
                unlink(source)
                unlink(pyc)
        sys.path.insert(0, os.curdir)
        try:
            test_with_extension('.py')
            if sys.platform.startswith('win'):
                for ext in ['.PY', '.Py', '.pY', '.pyw', '.PYW', '.pYw']:
                    test_with_extension(ext)
        finally:
            del sys.path[0]

    def test_module_with_large_stack(self, module='longlist'):
        filename = module + '.py'
        with open(filename, 'w') as f:
            f.write('d = [\n')
            for i in range(65000):
                f.write('"",\n')
            f.write(']')
        try:
            py_compile.compile(filename)
        finally:
            unlink(filename)
        sys.path.append('')
        importlib.invalidate_caches()
        namespace = {}
        try:
            make_legacy_pyc(filename)
            exec('import ' + module, None, namespace)
        finally:
            del sys.path[-1]
            unlink(filename + 'c')
            unlink(filename + 'o')
            namespace.clear()
            try:
                del sys.modules[module]
            except KeyError:
                pass

    def test_failing_import_sticks(self):
        source = TESTFN + '.py'
        with open(source, 'w') as f:
            print('a = 1/0', file=f)
        sys.path.insert(0, os.curdir)
        importlib.invalidate_caches()
        if TESTFN in sys.modules:
            del sys.modules[TESTFN]
        try:
            for i in [1, 2, 3]:
                self.assertRaises(ZeroDivisionError, __import__, TESTFN)
                self.assertNotIn(TESTFN, sys.modules, 
                    'damaged module in sys.modules on %i try' % i)
        finally:
            del sys.path[0]
            remove_files(TESTFN)

    def test_import_name_binding(self):
        import test as x
        import test.support
        self.assertIs(x, test, x.__name__)
        self.assertTrue(hasattr(test.support, '__file__'))
        import test.support as y
        self.assertIs(y, test.support, y.__name__)

    def test_failing_reload(self):
        source = TESTFN + os.extsep + 'py'
        with open(source, 'w') as f:
            f.write('a = 1\nb=2\n')
        sys.path.insert(0, os.curdir)
        try:
            mod = __import__(TESTFN)
            self.assertIn(TESTFN, sys.modules)
            self.assertEqual(mod.a, 1, 'module has wrong attribute values')
            self.assertEqual(mod.b, 2, 'module has wrong attribute values')
            remove_files(TESTFN)
            with open(source, 'w') as f:
                f.write('a = 10\nb=20//0\n')
            self.assertRaises(ZeroDivisionError, importlib.reload, mod)
            mod = sys.modules.get(TESTFN)
            self.assertIsNotNone(mod, 'expected module to be in sys.modules')
            self.assertEqual(mod.a, 10, 'module has wrong attribute values')
            self.assertEqual(mod.b, 2, 'module has wrong attribute values')
        finally:
            del sys.path[0]
            remove_files(TESTFN)
            unload(TESTFN)

    @skip_if_dont_write_bytecode
    def test_file_to_source(self):
        source = TESTFN + '.py'
        with open(source, 'w') as f:
            f.write('test = None\n')
        sys.path.insert(0, os.curdir)
        try:
            mod = __import__(TESTFN)
            self.assertTrue(mod.__file__.endswith('.py'))
            os.remove(source)
            del sys.modules[TESTFN]
            make_legacy_pyc(source)
            importlib.invalidate_caches()
            mod = __import__(TESTFN)
            base, ext = os.path.splitext(mod.__file__)
            self.assertEqual(ext, '.pyc')
        finally:
            del sys.path[0]
            remove_files(TESTFN)
            if TESTFN in sys.modules:
                del sys.modules[TESTFN]

    def test_import_by_filename(self):
        path = os.path.abspath(TESTFN)
        encoding = sys.getfilesystemencoding()
        try:
            path.encode(encoding)
        except UnicodeEncodeError:
            self.skipTest('path is not encodable to {}'.format(encoding))
        with self.assertRaises(ImportError) as c:
            __import__(path)

    def test_import_in_del_does_not_crash(self):
        testfn = script_helper.make_script('', TESTFN, textwrap.dedent(
            """            import sys
            class C:
               def __del__(self):
                  import importlib
            sys.argv.insert(0, C())
            """
            ))
        script_helper.assert_python_ok(testfn)

    @skip_if_dont_write_bytecode
    def test_timestamp_overflow(self):
        sys.path.insert(0, os.curdir)
        try:
            source = TESTFN + '.py'
            compiled = importlib.util.cache_from_source(source)
            with open(source, 'w') as f:
                pass
            try:
                os.utime(source, (2 ** 33 - 5, 2 ** 33 - 5))
            except OverflowError:
                self.skipTest('cannot set modification time to large integer')
            except OSError as e:
                if e.errno not in (getattr(errno, 'EOVERFLOW', None),
                    getattr(errno, 'EINVAL', None)):
                    raise
                self.skipTest(
                    'cannot set modification time to large integer ({})'.
                    format(e))
            __import__(TESTFN)
            os.stat(compiled)
        finally:
            del sys.path[0]
            remove_files(TESTFN)

    def test_bogus_fromlist(self):
        try:
            __import__('http', fromlist=['blah'])
        except ImportError:
            self.fail('fromlist must allow bogus names')

    @cpython_only
    def test_delete_builtins_import(self):
        args = ['-c', 'del __builtins__.__import__; import os']
        popen = script_helper.spawn_python(*args)
        stdout, stderr = popen.communicate()
        self.assertIn(b'ImportError', stdout)

    def test_from_import_message_for_nonexistent_module(self):
        with self.assertRaisesRegex(ImportError, "^No module named 'bogus'"):
            from bogus import foo

    def test_from_import_message_for_existing_module(self):
        with self.assertRaisesRegex(ImportError, "^cannot import name 'bogus'"
            ):
            from re import bogus

    def test_from_import_AttributeError(self):


        class AlwaysAttributeError:

            def __getattr__(self, _):
                raise AttributeError
        module_name = 'test_from_import_AttributeError'
        self.addCleanup(unload, module_name)
        sys.modules[module_name] = AlwaysAttributeError()
        with self.assertRaises(ImportError):
            from test_from_import_AttributeError import does_not_exist


@skip_if_dont_write_bytecode
class FilePermissionTests(unittest.TestCase):

    @unittest.skipUnless(os.name == 'posix',
        'test meaningful only on posix systems')
    def test_creation_mode(self):
        mask = 18
        with temp_umask(mask), _ready_to_import() as (name, path):
            cached_path = importlib.util.cache_from_source(path)
            module = __import__(name)
            if not os.path.exists(cached_path):
                self.fail(
                    '__import__ did not result in creation of a .pyc file')
            stat_info = os.stat(cached_path)
        self.assertEqual(oct(stat.S_IMODE(stat_info.st_mode)), oct(438 & ~mask)
            )

    @unittest.skipUnless(os.name == 'posix',
        'test meaningful only on posix systems')
    def test_cached_mode_issue_2051(self):
        mode = 384
        with temp_umask(18), _ready_to_import() as (name, path):
            cached_path = importlib.util.cache_from_source(path)
            os.chmod(path, mode)
            __import__(name)
            if not os.path.exists(cached_path):
                self.fail(
                    '__import__ did not result in creation of a .pyc file')
            stat_info = os.stat(cached_path)
        self.assertEqual(oct(stat.S_IMODE(stat_info.st_mode)), oct(mode))

    @unittest.skipUnless(os.name == 'posix',
        'test meaningful only on posix systems')
    def test_cached_readonly(self):
        mode = 256
        with temp_umask(18), _ready_to_import() as (name, path):
            cached_path = importlib.util.cache_from_source(path)
            os.chmod(path, mode)
            __import__(name)
            if not os.path.exists(cached_path):
                self.fail(
                    '__import__ did not result in creation of a .pyc file')
            stat_info = os.stat(cached_path)
        expected = mode | 128
        self.assertEqual(oct(stat.S_IMODE(stat_info.st_mode)), oct(expected))

    def test_pyc_always_writable(self):
        with _ready_to_import() as (name, path):
            with open(path, 'w') as f:
                f.write("x = 'original'\n")
            s = os.stat(path)
            os.utime(path, (s.st_atime, s.st_mtime - 100000000))
            os.chmod(path, 256)
            m = __import__(name)
            self.assertEqual(m.x, 'original')
            os.chmod(path, 384)
            with open(path, 'w') as f:
                f.write("x = 'rewritten'\n")
            unload(name)
            importlib.invalidate_caches()
            m = __import__(name)
            self.assertEqual(m.x, 'rewritten')
            unlink(path)
            unload(name)
            importlib.invalidate_caches()
            bytecode_only = path + 'c'
            os.rename(importlib.util.cache_from_source(path), bytecode_only)
            m = __import__(name)
            self.assertEqual(m.x, 'rewritten')


class PycRewritingTests(unittest.TestCase):
    module_name = 'unlikely_module_name'
    module_source = """
import sys
code_filename = sys._getframe().f_code.co_filename
module_filename = __file__
constant = 1
def func():
    pass
func_filename = func.__code__.co_filename
"""
    dir_name = os.path.abspath(TESTFN)
    file_name = os.path.join(dir_name, module_name) + os.extsep + 'py'
    compiled_name = importlib.util.cache_from_source(file_name)

    def setUp(self):
        self.sys_path = sys.path[:]
        self.orig_module = sys.modules.pop(self.module_name, None)
        os.mkdir(self.dir_name)
        with open(self.file_name, 'w') as f:
            f.write(self.module_source)
        sys.path.insert(0, self.dir_name)
        importlib.invalidate_caches()

    def tearDown(self):
        sys.path[:] = self.sys_path
        if self.orig_module is not None:
            sys.modules[self.module_name] = self.orig_module
        else:
            unload(self.module_name)
        unlink(self.file_name)
        unlink(self.compiled_name)
        rmtree(self.dir_name)

    def import_module(self):
        ns = globals()
        __import__(self.module_name, ns, ns)
        return sys.modules[self.module_name]

    def test_basics(self):
        mod = self.import_module()
        self.assertEqual(mod.module_filename, self.file_name)
        self.assertEqual(mod.code_filename, self.file_name)
        self.assertEqual(mod.func_filename, self.file_name)
        del sys.modules[self.module_name]
        mod = self.import_module()
        self.assertEqual(mod.module_filename, self.file_name)
        self.assertEqual(mod.code_filename, self.file_name)
        self.assertEqual(mod.func_filename, self.file_name)

    def test_incorrect_code_name(self):
        py_compile.compile(self.file_name, dfile='another_module.py')
        mod = self.import_module()
        self.assertEqual(mod.module_filename, self.file_name)
        self.assertEqual(mod.code_filename, self.file_name)
        self.assertEqual(mod.func_filename, self.file_name)

    def test_module_without_source(self):
        target = 'another_module.py'
        py_compile.compile(self.file_name, dfile=target)
        os.remove(self.file_name)
        pyc_file = make_legacy_pyc(self.file_name)
        importlib.invalidate_caches()
        mod = self.import_module()
        self.assertEqual(mod.module_filename, pyc_file)
        self.assertEqual(mod.code_filename, target)
        self.assertEqual(mod.func_filename, target)

    def test_foreign_code(self):
        py_compile.compile(self.file_name)
        with open(self.compiled_name, 'rb') as f:
            header = f.read(12)
            code = marshal.load(f)
        constants = list(code.co_consts)
        foreign_code = importlib.import_module.__code__
        pos = constants.index(1)
        constants[pos] = foreign_code
        code = type(code)(code.co_argcount, code.co_kwonlyargcount, code.
            co_nlocals, code.co_stacksize, code.co_flags, code.co_code,
            tuple(constants), code.co_names, code.co_varnames, code.
            co_filename, code.co_name, code.co_firstlineno, code.co_lnotab,
            code.co_freevars, code.co_cellvars)
        with open(self.compiled_name, 'wb') as f:
            f.write(header)
            marshal.dump(code, f)
        mod = self.import_module()
        self.assertEqual(mod.constant.co_filename, foreign_code.co_filename)


class PathsTests(unittest.TestCase):
    SAMPLES = 'test', 'testäöüß', 'testéè', 'test°³²'
    path = TESTFN

    def setUp(self):
        os.mkdir(self.path)
        self.syspath = sys.path[:]

    def tearDown(self):
        rmtree(self.path)
        sys.path[:] = self.syspath

    def test_trailing_slash(self):
        with open(os.path.join(self.path, 'test_trailing_slash.py'), 'w') as f:
            f.write("testdata = 'test_trailing_slash'")
        sys.path.append(self.path + '/')
        mod = __import__('test_trailing_slash')
        self.assertEqual(mod.testdata, 'test_trailing_slash')
        unload('test_trailing_slash')

    @unittest.skipUnless(sys.platform == 'win32', 'Windows-specific')
    def test_UNC_path(self):
        with open(os.path.join(self.path, 'test_unc_path.py'), 'w') as f:
            f.write("testdata = 'test_unc_path'")
        importlib.invalidate_caches()
        path = os.path.abspath(self.path)
        import socket
        hn = socket.gethostname()
        drive = path[0]
        unc = '\\\\%s\\%s$' % (hn, drive)
        unc += path[2:]
        try:
            os.listdir(unc)
        except OSError as e:
            if e.errno in (errno.EPERM, errno.EACCES, errno.ENOENT):
                self.skipTest('cannot access administrative share %r' % (unc,))
            raise
        sys.path.insert(0, unc)
        try:
            mod = __import__('test_unc_path')
        except ImportError as e:
            self.fail("could not import 'test_unc_path' from %r: %r" % (unc, e)
                )
        self.assertEqual(mod.testdata, 'test_unc_path')
        self.assertTrue(mod.__file__.startswith(unc), mod.__file__)
        unload('test_unc_path')


class RelativeImportTests(unittest.TestCase):

    def tearDown(self):
        unload('test.relimport')
    setUp = tearDown

    def test_relimport_star(self):
        from .. import relimport
        self.assertTrue(hasattr(relimport, 'RelativeImportTests'))

    def test_issue3221(self):

        def check_relative():
            exec('from . import relimport', ns)
        ns = dict(__package__='test', __name__='test.notarealmodule')
        check_relative()
        ns = dict(__package__='test', __name__='notarealpkg.notarealmodule')
        check_relative()
        ns = dict(__package__='foo', __name__='test.notarealmodule')
        self.assertRaises(SystemError, check_relative)
        ns = dict(__package__='foo', __name__='notarealpkg.notarealmodule')
        self.assertRaises(SystemError, check_relative)
        ns = dict(__package__=object())
        self.assertRaises(TypeError, check_relative)

    def test_absolute_import_without_future(self):
        with self.assertRaises(ImportError):
            from .os import sep
            self.fail(
                'explicit relative import triggered an implicit absolute import'
                )


class OverridingImportBuiltinTests(unittest.TestCase):

    def test_override_builtin(self):
        import os

        def foo():
            import os
            return os
        self.assertEqual(foo(), os)
        with swap_attr(builtins, '__import__', lambda *x: 5):
            self.assertEqual(foo(), 5)
        with swap_item(globals(), '__import__', lambda *x: 5):
            self.assertEqual(foo(), os)


class PycacheTests(unittest.TestCase):

    def _clean(self):
        forget(TESTFN)
        rmtree('__pycache__')
        unlink(self.source)

    def setUp(self):
        self.source = TESTFN + '.py'
        self._clean()
        with open(self.source, 'w') as fp:
            print('# This is a test file written by test_import.py', file=fp)
        sys.path.insert(0, os.curdir)
        importlib.invalidate_caches()

    def tearDown(self):
        assert sys.path[0] == os.curdir, 'Unexpected sys.path[0]'
        del sys.path[0]
        self._clean()

    @skip_if_dont_write_bytecode
    def test_import_pyc_path(self):
        self.assertFalse(os.path.exists('__pycache__'))
        __import__(TESTFN)
        self.assertTrue(os.path.exists('__pycache__'))
        pyc_path = importlib.util.cache_from_source(self.source)
        self.assertTrue(os.path.exists(pyc_path),
            'bytecode file {!r} for {!r} does not exist'.format(pyc_path,
            TESTFN))

    @unittest.skipUnless(os.name == 'posix',
        'test meaningful only on posix systems')
    @unittest.skipIf(hasattr(os, 'geteuid') and os.geteuid() == 0,
        'due to varying filesystem permission semantics (issue #11956)')
    @skip_if_dont_write_bytecode
    def test_unwritable_directory(self):
        with temp_umask(146):
            __import__(TESTFN)
        self.assertTrue(os.path.exists('__pycache__'))
        pyc_path = importlib.util.cache_from_source(self.source)
        self.assertFalse(os.path.exists(pyc_path),
            'bytecode file {!r} for {!r} exists'.format(pyc_path, TESTFN))

    @skip_if_dont_write_bytecode
    def test_missing_source(self):
        __import__(TESTFN)
        pyc_file = importlib.util.cache_from_source(self.source)
        self.assertTrue(os.path.exists(pyc_file))
        os.remove(self.source)
        forget(TESTFN)
        importlib.invalidate_caches()
        self.assertRaises(ImportError, __import__, TESTFN)

    @skip_if_dont_write_bytecode
    def test_missing_source_legacy(self):
        __import__(TESTFN)
        pyc_file = make_legacy_pyc(self.source)
        os.remove(self.source)
        unload(TESTFN)
        importlib.invalidate_caches()
        m = __import__(TESTFN)
        self.assertEqual(m.__file__, os.path.join(os.curdir, os.path.
            relpath(pyc_file)))

    def test___cached__(self):
        m = __import__(TESTFN)
        pyc_file = importlib.util.cache_from_source(TESTFN + '.py')
        self.assertEqual(m.__cached__, os.path.join(os.curdir, pyc_file))

    @skip_if_dont_write_bytecode
    def test___cached___legacy_pyc(self):
        __import__(TESTFN)
        pyc_file = make_legacy_pyc(self.source)
        os.remove(self.source)
        unload(TESTFN)
        importlib.invalidate_caches()
        m = __import__(TESTFN)
        self.assertEqual(m.__cached__, os.path.join(os.curdir, os.path.
            relpath(pyc_file)))

    @skip_if_dont_write_bytecode
    def test_package___cached__(self):

        def cleanup():
            rmtree('pep3147')
            unload('pep3147.foo')
            unload('pep3147')
        os.mkdir('pep3147')
        self.addCleanup(cleanup)
        with open(os.path.join('pep3147', '__init__.py'), 'w'):
            pass
        with open(os.path.join('pep3147', 'foo.py'), 'w'):
            pass
        importlib.invalidate_caches()
        m = __import__('pep3147.foo')
        init_pyc = importlib.util.cache_from_source(os.path.join('pep3147',
            '__init__.py'))
        self.assertEqual(m.__cached__, os.path.join(os.curdir, init_pyc))
        foo_pyc = importlib.util.cache_from_source(os.path.join('pep3147',
            'foo.py'))
        self.assertEqual(sys.modules['pep3147.foo'].__cached__, os.path.
            join(os.curdir, foo_pyc))

    def test_package___cached___from_pyc(self):

        def cleanup():
            rmtree('pep3147')
            unload('pep3147.foo')
            unload('pep3147')
        os.mkdir('pep3147')
        self.addCleanup(cleanup)
        with open(os.path.join('pep3147', '__init__.py'), 'w'):
            pass
        with open(os.path.join('pep3147', 'foo.py'), 'w'):
            pass
        importlib.invalidate_caches()
        m = __import__('pep3147.foo')
        unload('pep3147.foo')
        unload('pep3147')
        importlib.invalidate_caches()
        m = __import__('pep3147.foo')
        init_pyc = importlib.util.cache_from_source(os.path.join('pep3147',
            '__init__.py'))
        self.assertEqual(m.__cached__, os.path.join(os.curdir, init_pyc))
        foo_pyc = importlib.util.cache_from_source(os.path.join('pep3147',
            'foo.py'))
        self.assertEqual(sys.modules['pep3147.foo'].__cached__, os.path.
            join(os.curdir, foo_pyc))

    def test_recompute_pyc_same_second(self):
        __import__(TESTFN)
        unload(TESTFN)
        with open(self.source, 'a') as fp:
            print('x = 5', file=fp)
        m = __import__(TESTFN)
        self.assertEqual(m.x, 5)


class TestSymbolicallyLinkedPackage(unittest.TestCase):
    package_name = 'sample'
    tagged = package_name + '-tagged'

    def setUp(self):
        test.support.rmtree(self.tagged)
        test.support.rmtree(self.package_name)
        self.orig_sys_path = sys.path[:]
        os.mkdir(self.tagged)
        self.addCleanup(test.support.rmtree, self.tagged)
        init_file = os.path.join(self.tagged, '__init__.py')
        test.support.create_empty_file(init_file)
        assert os.path.exists(init_file)
        os.symlink(self.tagged, self.package_name, target_is_directory=True)
        self.addCleanup(test.support.unlink, self.package_name)
        importlib.invalidate_caches()
        self.assertEqual(os.path.isdir(self.package_name), True)
        assert os.path.isfile(os.path.join(self.package_name, '__init__.py'))

    def tearDown(self):
        sys.path[:] = self.orig_sys_path

    @unittest.skipUnless(not hasattr(sys, 'getwindowsversion') or sys.
        getwindowsversion() >= (6, 0), 'Windows Vista or later required')
    @test.support.skip_unless_symlink
    def test_symlinked_dir_importable(self):
        sys.path[:] = ['.']
        assert os.path.exists(self.package_name)
        assert os.path.exists(os.path.join(self.package_name, '__init__.py'))
        importlib.import_module(self.package_name)


@cpython_only
class ImportlibBootstrapTests(unittest.TestCase):

    def test_frozen_importlib(self):
        mod = sys.modules['_frozen_importlib']
        self.assertTrue(mod)

    def test_frozen_importlib_is_bootstrap(self):
        from importlib import _bootstrap
        mod = sys.modules['_frozen_importlib']
        self.assertIs(mod, _bootstrap)
        self.assertEqual(mod.__name__, 'importlib._bootstrap')
        self.assertEqual(mod.__package__, 'importlib')
        self.assertTrue(mod.__file__.endswith('_bootstrap.py'), mod.__file__)

    def test_frozen_importlib_external_is_bootstrap_external(self):
        from importlib import _bootstrap_external
        mod = sys.modules['_frozen_importlib_external']
        self.assertIs(mod, _bootstrap_external)
        self.assertEqual(mod.__name__, 'importlib._bootstrap_external')
        self.assertEqual(mod.__package__, 'importlib')
        self.assertTrue(mod.__file__.endswith('_bootstrap_external.py'),
            mod.__file__)

    def test_there_can_be_only_one(self):
        from importlib import machinery
        mod = sys.modules['_frozen_importlib']
        self.assertIs(machinery.ModuleSpec, mod.ModuleSpec)


@cpython_only
class GetSourcefileTests(unittest.TestCase):
    """Test importlib._bootstrap_external._get_sourcefile() as used by the C API.

    Because of the peculiarities of the need of this function, the tests are
    knowingly whitebox tests.

    """

    def test_get_sourcefile(self):
        with mock.patch('importlib._bootstrap_external._path_isfile'
            ) as _path_isfile:
            _path_isfile.return_value = True
            path = TESTFN + '.pyc'
            expect = TESTFN + '.py'
            self.assertEqual(_get_sourcefile(path), expect)

    def test_get_sourcefile_no_source(self):
        with mock.patch('importlib._bootstrap_external._path_isfile'
            ) as _path_isfile:
            _path_isfile.return_value = False
            path = TESTFN + '.pyc'
            self.assertEqual(_get_sourcefile(path), path)

    def test_get_sourcefile_bad_ext(self):
        path = TESTFN + '.bad_ext'
        self.assertEqual(_get_sourcefile(path), path)


class ImportTracebackTests(unittest.TestCase):

    def setUp(self):
        os.mkdir(TESTFN)
        self.old_path = sys.path[:]
        sys.path.insert(0, TESTFN)

    def tearDown(self):
        sys.path[:] = self.old_path
        rmtree(TESTFN)

    def create_module(self, mod, contents, ext='.py'):
        fname = os.path.join(TESTFN, mod + ext)
        with open(fname, 'w') as f:
            f.write(contents)
        self.addCleanup(unload, mod)
        importlib.invalidate_caches()
        return fname

    def assert_traceback(self, tb, files):
        deduped_files = []
        while tb:
            code = tb.tb_frame.f_code
            fn = code.co_filename
            if not deduped_files or fn != deduped_files[-1]:
                deduped_files.append(fn)
            tb = tb.tb_next
        self.assertEqual(len(deduped_files), len(files), deduped_files)
        for fn, pat in zip(deduped_files, files):
            self.assertIn(pat, fn)

    def test_nonexistent_module(self):
        try:
            import nonexistent_xyzzy
        except ImportError as e:
            tb = e.__traceback__
        else:
            self.fail('ImportError should have been raised')
        self.assert_traceback(tb, [__file__])

    def test_nonexistent_module_nested(self):
        self.create_module('foo', 'import nonexistent_xyzzy')
        try:
            import foo
        except ImportError as e:
            tb = e.__traceback__
        else:
            self.fail('ImportError should have been raised')
        self.assert_traceback(tb, [__file__, 'foo.py'])

    def test_exec_failure(self):
        self.create_module('foo', '1/0')
        try:
            import foo
        except ZeroDivisionError as e:
            tb = e.__traceback__
        else:
            self.fail('ZeroDivisionError should have been raised')
        self.assert_traceback(tb, [__file__, 'foo.py'])

    def test_exec_failure_nested(self):
        self.create_module('foo', 'import bar')
        self.create_module('bar', '1/0')
        try:
            import foo
        except ZeroDivisionError as e:
            tb = e.__traceback__
        else:
            self.fail('ZeroDivisionError should have been raised')
        self.assert_traceback(tb, [__file__, 'foo.py', 'bar.py'])

    def test_syntax_error(self):
        self.create_module('foo', 'invalid syntax is invalid')
        try:
            import foo
        except SyntaxError as e:
            tb = e.__traceback__
        else:
            self.fail('SyntaxError should have been raised')
        self.assert_traceback(tb, [__file__])

    def _setup_broken_package(self, parent, child):
        pkg_name = '_parent_foo'
        self.addCleanup(unload, pkg_name)
        pkg_path = os.path.join(TESTFN, pkg_name)
        os.mkdir(pkg_path)
        init_path = os.path.join(pkg_path, '__init__.py')
        with open(init_path, 'w') as f:
            f.write(parent)
        bar_path = os.path.join(pkg_path, 'bar.py')
        with open(bar_path, 'w') as f:
            f.write(child)
        importlib.invalidate_caches()
        return init_path, bar_path

    def test_broken_submodule(self):
        init_path, bar_path = self._setup_broken_package('', '1/0')
        try:
            import _parent_foo.bar
        except ZeroDivisionError as e:
            tb = e.__traceback__
        else:
            self.fail('ZeroDivisionError should have been raised')
        self.assert_traceback(tb, [__file__, bar_path])

    def test_broken_from(self):
        init_path, bar_path = self._setup_broken_package('', '1/0')
        try:
            from _parent_foo import bar
        except ZeroDivisionError as e:
            tb = e.__traceback__
        else:
            self.fail('ImportError should have been raised')
        self.assert_traceback(tb, [__file__, bar_path])

    def test_broken_parent(self):
        init_path, bar_path = self._setup_broken_package('1/0', '')
        try:
            import _parent_foo.bar
        except ZeroDivisionError as e:
            tb = e.__traceback__
        else:
            self.fail('ZeroDivisionError should have been raised')
        self.assert_traceback(tb, [__file__, init_path])

    def test_broken_parent_from(self):
        init_path, bar_path = self._setup_broken_package('1/0', '')
        try:
            from _parent_foo import bar
        except ZeroDivisionError as e:
            tb = e.__traceback__
        else:
            self.fail('ZeroDivisionError should have been raised')
        self.assert_traceback(tb, [__file__, init_path])

    @cpython_only
    def test_import_bug(self):
        self.create_module('foo', '')
        importlib = sys.modules['_frozen_importlib_external']
        if 'load_module' in vars(importlib.SourceLoader):
            old_exec_module = importlib.SourceLoader.exec_module
        else:
            old_exec_module = None
        try:

            def exec_module(*args):
                1 / 0
            importlib.SourceLoader.exec_module = exec_module
            try:
                import foo
            except ZeroDivisionError as e:
                tb = e.__traceback__
            else:
                self.fail('ZeroDivisionError should have been raised')
            self.assert_traceback(tb, [__file__, '<frozen importlib', __file__]
                )
        finally:
            if old_exec_module is None:
                del importlib.SourceLoader.exec_module
            else:
                importlib.SourceLoader.exec_module = old_exec_module

    @unittest.skipUnless(TESTFN_UNENCODABLE, 'need TESTFN_UNENCODABLE')
    def test_unencodable_filename(self):
        pyname = script_helper.make_script('', TESTFN_UNENCODABLE, 'pass')
        self.addCleanup(unlink, pyname)
        name = pyname[:-3]
        script_helper.assert_python_ok('-c', 'mod = __import__(%a)' % name,
            __isolated=False)


class CircularImportTests(unittest.TestCase):
    """See the docstrings of the modules being imported for the purpose of the
    test."""

    def tearDown(self):
        """Make sure no modules pre-exist in sys.modules which are being used to
        test."""
        for key in list(sys.modules.keys()):
            if key.startswith('test.test_import.data.circular_imports'):
                del sys.modules[key]

    def test_direct(self):
        try:
            import test.test_import.data.circular_imports.basic
        except ImportError:
            self.fail('circular import through relative imports failed')

    def test_indirect(self):
        try:
            import test.test_import.data.circular_imports.indirect
        except ImportError:
            self.fail(
                'relative import in module contributing to circular import failed'
                )

    def test_subpackage(self):
        try:
            import test.test_import.data.circular_imports.subpackage
        except ImportError:
            self.fail('circular import involving a subpackage failed')

    def test_rebinding(self):
        try:
            import test.test_import.data.circular_imports.rebinding as rebinding
        except ImportError:
            self.fail(
                'circular import with rebinding of module attribute failed')
        from test.test_import.data.circular_imports.subpkg import util
        self.assertIs(util.util, rebinding.util)


if __name__ == '__main__':
    unittest.main()
