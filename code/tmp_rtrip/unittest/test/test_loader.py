import sys
import types
import warnings
import unittest


def warningregistry(func):

    def wrapper(*args, **kws):
        missing = []
        saved = getattr(warnings, '__warningregistry__', missing).copy()
        try:
            return func(*args, **kws)
        finally:
            if saved is missing:
                try:
                    del warnings.__warningregistry__
                except AttributeError:
                    pass
            else:
                warnings.__warningregistry__ = saved
    return wrapper


class Test_TestLoader(unittest.TestCase):

    def test___init__(self):
        loader = unittest.TestLoader()
        self.assertEqual([], loader.errors)

    def test_loadTestsFromTestCase(self):


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foo_bar(self):
                pass
        tests = unittest.TestSuite([Foo('test_1'), Foo('test_2')])
        loader = unittest.TestLoader()
        self.assertEqual(loader.loadTestsFromTestCase(Foo), tests)

    def test_loadTestsFromTestCase__no_matches(self):


        class Foo(unittest.TestCase):

            def foo_bar(self):
                pass
        empty_suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        self.assertEqual(loader.loadTestsFromTestCase(Foo), empty_suite)

    def test_loadTestsFromTestCase__TestSuite_subclass(self):


        class NotATestCase(unittest.TestSuite):
            pass
        loader = unittest.TestLoader()
        try:
            loader.loadTestsFromTestCase(NotATestCase)
        except TypeError:
            pass
        else:
            self.fail('Should raise TypeError')

    def test_loadTestsFromTestCase__default_method_name(self):


        class Foo(unittest.TestCase):

            def runTest(self):
                pass
        loader = unittest.TestLoader()
        self.assertFalse('runTest'.startswith(loader.testMethodPrefix))
        suite = loader.loadTestsFromTestCase(Foo)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [Foo('runTest')])

    def test_loadTestsFromModule__TestCase_subclass(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(m)
        self.assertIsInstance(suite, loader.suiteClass)
        expected = [loader.suiteClass([MyTestCase('test')])]
        self.assertEqual(list(suite), expected)

    def test_loadTestsFromModule__no_TestCase_instances(self):
        m = types.ModuleType('m')
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [])

    def test_loadTestsFromModule__no_TestCase_tests(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):
            pass
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [loader.suiteClass()])

    def test_loadTestsFromModule__not_a_module(self):


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass


        class NotAModule(object):
            test_2 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(NotAModule)
        reference = [unittest.TestSuite([MyTestCase('test')])]
        self.assertEqual(list(suite), reference)

    @warningregistry
    def test_loadTestsFromModule__load_tests(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        load_tests_args = []

        def load_tests(loader, tests, pattern):
            self.assertIsInstance(tests, unittest.TestSuite)
            load_tests_args.extend((loader, tests, pattern))
            return tests
        m.load_tests = load_tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(m)
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertEqual(load_tests_args, [loader, suite, None])
        load_tests_args = []
        with warnings.catch_warnings(record=False):
            warnings.simplefilter('ignore')
            suite = loader.loadTestsFromModule(m, use_load_tests=False)
        self.assertEqual(load_tests_args, [loader, suite, None])

    @warningregistry
    def test_loadTestsFromModule__use_load_tests_deprecated_positional(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        load_tests_args = []

        def load_tests(loader, tests, pattern):
            self.assertIsInstance(tests, unittest.TestSuite)
            load_tests_args.extend((loader, tests, pattern))
            return tests
        m.load_tests = load_tests
        loader = unittest.TestLoader()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            suite = loader.loadTestsFromModule(m, False)
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertEqual(load_tests_args, [loader, suite, None])
        self.assertIs(w[-1].category, DeprecationWarning)
        self.assertEqual(str(w[-1].message),
            'use_load_tests is deprecated and ignored')

    @warningregistry
    def test_loadTestsFromModule__use_load_tests_deprecated_keyword(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        load_tests_args = []

        def load_tests(loader, tests, pattern):
            self.assertIsInstance(tests, unittest.TestSuite)
            load_tests_args.extend((loader, tests, pattern))
            return tests
        m.load_tests = load_tests
        loader = unittest.TestLoader()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            suite = loader.loadTestsFromModule(m, use_load_tests=False)
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertEqual(load_tests_args, [loader, suite, None])
        self.assertIs(w[-1].category, DeprecationWarning)
        self.assertEqual(str(w[-1].message),
            'use_load_tests is deprecated and ignored')

    @warningregistry
    def test_loadTestsFromModule__too_many_positional_args(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        load_tests_args = []

        def load_tests(loader, tests, pattern):
            self.assertIsInstance(tests, unittest.TestSuite)
            load_tests_args.extend((loader, tests, pattern))
            return tests
        m.load_tests = load_tests
        loader = unittest.TestLoader()
        with self.assertRaises(TypeError) as cm, warnings.catch_warnings(record
            =True) as w:
            warnings.simplefilter('always')
            loader.loadTestsFromModule(m, False, 'testme.*')
        self.assertIs(w[-1].category, DeprecationWarning)
        self.assertEqual(str(w[-1].message),
            'use_load_tests is deprecated and ignored')
        self.assertEqual(type(cm.exception), TypeError)
        self.assertEqual(str(cm.exception),
            'loadTestsFromModule() takes 1 positional argument but 3 were given'
            )

    @warningregistry
    def test_loadTestsFromModule__use_load_tests_other_bad_keyword(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        load_tests_args = []

        def load_tests(loader, tests, pattern):
            self.assertIsInstance(tests, unittest.TestSuite)
            load_tests_args.extend((loader, tests, pattern))
            return tests
        m.load_tests = load_tests
        loader = unittest.TestLoader()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with self.assertRaises(TypeError) as cm:
                loader.loadTestsFromModule(m, use_load_tests=False,
                    very_bad=True, worse=False)
        self.assertEqual(type(cm.exception), TypeError)
        self.assertEqual(str(cm.exception),
            "loadTestsFromModule() got an unexpected keyword argument 'very_bad'"
            )

    def test_loadTestsFromModule__pattern(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        load_tests_args = []

        def load_tests(loader, tests, pattern):
            self.assertIsInstance(tests, unittest.TestSuite)
            load_tests_args.extend((loader, tests, pattern))
            return tests
        m.load_tests = load_tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(m, pattern='testme.*')
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertEqual(load_tests_args, [loader, suite, 'testme.*'])

    def test_loadTestsFromModule__faulty_load_tests(self):
        m = types.ModuleType('m')

        def load_tests(loader, tests, pattern):
            raise TypeError('some failure')
        m.load_tests = load_tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(m)
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertEqual(suite.countTestCases(), 1)
        self.assertNotEqual([], loader.errors)
        self.assertEqual(1, len(loader.errors))
        error = loader.errors[0]
        self.assertTrue('Failed to call load_tests:' in error, 
            'missing error string in %r' % error)
        test = list(suite)[0]
        self.assertRaisesRegex(TypeError, 'some failure', test.m)

    def test_loadTestsFromName__empty_name(self):
        loader = unittest.TestLoader()
        try:
            loader.loadTestsFromName('')
        except ValueError as e:
            self.assertEqual(str(e), 'Empty module name')
        else:
            self.fail('TestLoader.loadTestsFromName failed to raise ValueError'
                )

    def test_loadTestsFromName__malformed_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('abc () //')
        error, test = self.check_deferred_error(loader, suite)
        expected = 'Failed to import test module: abc () //'
        expected_regex = 'Failed to import test module: abc \\(\\) //'
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(ImportError, expected_regex, getattr(test,
            'abc () //'))

    def test_loadTestsFromName__unknown_module_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('sdasfasfasdf')
        expected = "No module named 'sdasfasfasdf'"
        error, test = self.check_deferred_error(loader, suite)
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(ImportError, expected, test.sdasfasfasdf)

    def test_loadTestsFromName__unknown_attr_name_on_module(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('unittest.loader.sdasfasfasdf')
        expected = "module 'unittest.loader' has no attribute 'sdasfasfasdf'"
        error, test = self.check_deferred_error(loader, suite)
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected, test.sdasfasfasdf)

    def test_loadTestsFromName__unknown_attr_name_on_package(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('unittest.sdasfasfasdf')
        expected = "No module named 'unittest.sdasfasfasdf'"
        error, test = self.check_deferred_error(loader, suite)
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(ImportError, expected, test.sdasfasfasdf)

    def test_loadTestsFromName__relative_unknown_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('sdasfasfasdf', unittest)
        expected = "module 'unittest' has no attribute 'sdasfasfasdf'"
        error, test = self.check_deferred_error(loader, suite)
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected, test.sdasfasfasdf)

    def test_loadTestsFromName__relative_empty_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('', unittest)
        error, test = self.check_deferred_error(loader, suite)
        expected = "has no attribute ''"
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected, getattr(test, ''))

    def test_loadTestsFromName__relative_malformed_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('abc () //', unittest)
        error, test = self.check_deferred_error(loader, suite)
        expected = "module 'unittest' has no attribute 'abc () //'"
        expected_regex = "module 'unittest' has no attribute 'abc \\(\\) //'"
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected_regex, getattr(test,
            'abc () //'))

    def test_loadTestsFromName__relative_not_a_module(self):


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass


        class NotAModule(object):
            test_2 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('test_2', NotAModule)
        reference = [MyTestCase('test')]
        self.assertEqual(list(suite), reference)

    def test_loadTestsFromName__relative_bad_object(self):
        m = types.ModuleType('m')
        m.testcase_1 = object()
        loader = unittest.TestLoader()
        try:
            loader.loadTestsFromName('testcase_1', m)
        except TypeError:
            pass
        else:
            self.fail('Should have raised TypeError')

    def test_loadTestsFromName__relative_TestCase_subclass(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('testcase_1', m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [MyTestCase('test')])

    def test_loadTestsFromName__relative_TestSuite(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testsuite = unittest.TestSuite([MyTestCase('test')])
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('testsuite', m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [MyTestCase('test')])

    def test_loadTestsFromName__relative_testmethod(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('testcase_1.test', m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [MyTestCase('test')])

    def test_loadTestsFromName__relative_invalid_testmethod(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('testcase_1.testfoo', m)
        expected = "type object 'MyTestCase' has no attribute 'testfoo'"
        error, test = self.check_deferred_error(loader, suite)
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected, test.testfoo)

    def test_loadTestsFromName__callable__TestSuite(self):
        m = types.ModuleType('m')
        testcase_1 = unittest.FunctionTestCase(lambda : None)
        testcase_2 = unittest.FunctionTestCase(lambda : None)

        def return_TestSuite():
            return unittest.TestSuite([testcase_1, testcase_2])
        m.return_TestSuite = return_TestSuite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('return_TestSuite', m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [testcase_1, testcase_2])

    def test_loadTestsFromName__callable__TestCase_instance(self):
        m = types.ModuleType('m')
        testcase_1 = unittest.FunctionTestCase(lambda : None)

        def return_TestCase():
            return testcase_1
        m.return_TestCase = return_TestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('return_TestCase', m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [testcase_1])

    def test_loadTestsFromName__callable__TestCase_instance_ProperSuiteClass(
        self):


        class SubTestSuite(unittest.TestSuite):
            pass
        m = types.ModuleType('m')
        testcase_1 = unittest.FunctionTestCase(lambda : None)

        def return_TestCase():
            return testcase_1
        m.return_TestCase = return_TestCase
        loader = unittest.TestLoader()
        loader.suiteClass = SubTestSuite
        suite = loader.loadTestsFromName('return_TestCase', m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [testcase_1])

    def test_loadTestsFromName__relative_testmethod_ProperSuiteClass(self):


        class SubTestSuite(unittest.TestSuite):
            pass
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        loader.suiteClass = SubTestSuite
        suite = loader.loadTestsFromName('testcase_1.test', m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [MyTestCase('test')])

    def test_loadTestsFromName__callable__wrong_type(self):
        m = types.ModuleType('m')

        def return_wrong():
            return 6
        m.return_wrong = return_wrong
        loader = unittest.TestLoader()
        try:
            suite = loader.loadTestsFromName('return_wrong', m)
        except TypeError:
            pass
        else:
            self.fail('TestLoader.loadTestsFromName failed to raise TypeError')

    def test_loadTestsFromName__module_not_loaded(self):
        module_name = 'unittest.test.dummy'
        sys.modules.pop(module_name, None)
        loader = unittest.TestLoader()
        try:
            suite = loader.loadTestsFromName(module_name)
            self.assertIsInstance(suite, loader.suiteClass)
            self.assertEqual(list(suite), [])
            self.assertIn(module_name, sys.modules)
        finally:
            if module_name in sys.modules:
                del sys.modules[module_name]

    def check_deferred_error(self, loader, suite):
        """Helper function for checking that errors in loading are reported.

        :param loader: A loader with some errors.
        :param suite: A suite that should have a late bound error.
        :return: The first error message from the loader and the test object
            from the suite.
        """
        self.assertIsInstance(suite, unittest.TestSuite)
        self.assertEqual(suite.countTestCases(), 1)
        self.assertNotEqual([], loader.errors)
        self.assertEqual(1, len(loader.errors))
        error = loader.errors[0]
        test = list(suite)[0]
        return error, test

    def test_loadTestsFromNames__empty_name_list(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames([])
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [])

    def test_loadTestsFromNames__relative_empty_name_list(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames([], unittest)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [])

    def test_loadTestsFromNames__empty_name(self):
        loader = unittest.TestLoader()
        try:
            loader.loadTestsFromNames([''])
        except ValueError as e:
            self.assertEqual(str(e), 'Empty module name')
        else:
            self.fail(
                'TestLoader.loadTestsFromNames failed to raise ValueError')

    def test_loadTestsFromNames__malformed_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['abc () //'])
        error, test = self.check_deferred_error(loader, list(suite)[0])
        expected = 'Failed to import test module: abc () //'
        expected_regex = 'Failed to import test module: abc \\(\\) //'
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(ImportError, expected_regex, getattr(test,
            'abc () //'))

    def test_loadTestsFromNames__unknown_module_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['sdasfasfasdf'])
        error, test = self.check_deferred_error(loader, list(suite)[0])
        expected = 'Failed to import test module: sdasfasfasdf'
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(ImportError, expected, test.sdasfasfasdf)

    def test_loadTestsFromNames__unknown_attr_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['unittest.loader.sdasfasfasdf',
            'unittest.test.dummy'])
        error, test = self.check_deferred_error(loader, list(suite)[0])
        expected = "module 'unittest.loader' has no attribute 'sdasfasfasdf'"
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected, test.sdasfasfasdf)

    def test_loadTestsFromNames__unknown_name_relative_1(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['sdasfasfasdf'], unittest)
        error, test = self.check_deferred_error(loader, list(suite)[0])
        expected = "module 'unittest' has no attribute 'sdasfasfasdf'"
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected, test.sdasfasfasdf)

    def test_loadTestsFromNames__unknown_name_relative_2(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['TestCase', 'sdasfasfasdf'],
            unittest)
        error, test = self.check_deferred_error(loader, list(suite)[1])
        expected = "module 'unittest' has no attribute 'sdasfasfasdf'"
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected, test.sdasfasfasdf)

    def test_loadTestsFromNames__relative_empty_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames([''], unittest)
        error, test = self.check_deferred_error(loader, list(suite)[0])
        expected = "has no attribute ''"
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected, getattr(test, ''))

    def test_loadTestsFromNames__relative_malformed_name(self):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['abc () //'], unittest)
        error, test = self.check_deferred_error(loader, list(suite)[0])
        expected = "module 'unittest' has no attribute 'abc () //'"
        expected_regex = "module 'unittest' has no attribute 'abc \\(\\) //'"
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected_regex, getattr(test,
            'abc () //'))

    def test_loadTestsFromNames__relative_not_a_module(self):


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass


        class NotAModule(object):
            test_2 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['test_2'], NotAModule)
        reference = [unittest.TestSuite([MyTestCase('test')])]
        self.assertEqual(list(suite), reference)

    def test_loadTestsFromNames__relative_bad_object(self):
        m = types.ModuleType('m')
        m.testcase_1 = object()
        loader = unittest.TestLoader()
        try:
            loader.loadTestsFromNames(['testcase_1'], m)
        except TypeError:
            pass
        else:
            self.fail('Should have raised TypeError')

    def test_loadTestsFromNames__relative_TestCase_subclass(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['testcase_1'], m)
        self.assertIsInstance(suite, loader.suiteClass)
        expected = loader.suiteClass([MyTestCase('test')])
        self.assertEqual(list(suite), [expected])

    def test_loadTestsFromNames__relative_TestSuite(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testsuite = unittest.TestSuite([MyTestCase('test')])
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['testsuite'], m)
        self.assertIsInstance(suite, loader.suiteClass)
        self.assertEqual(list(suite), [m.testsuite])

    def test_loadTestsFromNames__relative_testmethod(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['testcase_1.test'], m)
        self.assertIsInstance(suite, loader.suiteClass)
        ref_suite = unittest.TestSuite([MyTestCase('test')])
        self.assertEqual(list(suite), [ref_suite])

    def test_loadTestsFromName__function_with_different_name_than_method(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):
            test = lambda : 1
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['testcase_1.test'], m)
        self.assertIsInstance(suite, loader.suiteClass)
        ref_suite = unittest.TestSuite([MyTestCase('test')])
        self.assertEqual(list(suite), [ref_suite])

    def test_loadTestsFromNames__relative_invalid_testmethod(self):
        m = types.ModuleType('m')


        class MyTestCase(unittest.TestCase):

            def test(self):
                pass
        m.testcase_1 = MyTestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['testcase_1.testfoo'], m)
        error, test = self.check_deferred_error(loader, list(suite)[0])
        expected = "type object 'MyTestCase' has no attribute 'testfoo'"
        self.assertIn(expected, error, 'missing error string in %r' % error)
        self.assertRaisesRegex(AttributeError, expected, test.testfoo)

    def test_loadTestsFromNames__callable__TestSuite(self):
        m = types.ModuleType('m')
        testcase_1 = unittest.FunctionTestCase(lambda : None)
        testcase_2 = unittest.FunctionTestCase(lambda : None)

        def return_TestSuite():
            return unittest.TestSuite([testcase_1, testcase_2])
        m.return_TestSuite = return_TestSuite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['return_TestSuite'], m)
        self.assertIsInstance(suite, loader.suiteClass)
        expected = unittest.TestSuite([testcase_1, testcase_2])
        self.assertEqual(list(suite), [expected])

    def test_loadTestsFromNames__callable__TestCase_instance(self):
        m = types.ModuleType('m')
        testcase_1 = unittest.FunctionTestCase(lambda : None)

        def return_TestCase():
            return testcase_1
        m.return_TestCase = return_TestCase
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['return_TestCase'], m)
        self.assertIsInstance(suite, loader.suiteClass)
        ref_suite = unittest.TestSuite([testcase_1])
        self.assertEqual(list(suite), [ref_suite])

    def test_loadTestsFromNames__callable__call_staticmethod(self):
        m = types.ModuleType('m')


        class Test1(unittest.TestCase):

            def test(self):
                pass
        testcase_1 = Test1('test')


        class Foo(unittest.TestCase):

            @staticmethod
            def foo():
                return testcase_1
        m.Foo = Foo
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromNames(['Foo.foo'], m)
        self.assertIsInstance(suite, loader.suiteClass)
        ref_suite = unittest.TestSuite([testcase_1])
        self.assertEqual(list(suite), [ref_suite])

    def test_loadTestsFromNames__callable__wrong_type(self):
        m = types.ModuleType('m')

        def return_wrong():
            return 6
        m.return_wrong = return_wrong
        loader = unittest.TestLoader()
        try:
            suite = loader.loadTestsFromNames(['return_wrong'], m)
        except TypeError:
            pass
        else:
            self.fail('TestLoader.loadTestsFromNames failed to raise TypeError'
                )

    def test_loadTestsFromNames__module_not_loaded(self):
        module_name = 'unittest.test.dummy'
        sys.modules.pop(module_name, None)
        loader = unittest.TestLoader()
        try:
            suite = loader.loadTestsFromNames([module_name])
            self.assertIsInstance(suite, loader.suiteClass)
            self.assertEqual(list(suite), [unittest.TestSuite()])
            self.assertIn(module_name, sys.modules)
        finally:
            if module_name in sys.modules:
                del sys.modules[module_name]

    def test_getTestCaseNames(self):


        class Test(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foobar(self):
                pass
        loader = unittest.TestLoader()
        self.assertEqual(loader.getTestCaseNames(Test), ['test_1', 'test_2'])

    def test_getTestCaseNames__no_tests(self):


        class Test(unittest.TestCase):

            def foobar(self):
                pass
        loader = unittest.TestLoader()
        self.assertEqual(loader.getTestCaseNames(Test), [])

    def test_getTestCaseNames__not_a_TestCase(self):


        class BadCase(int):

            def test_foo(self):
                pass
        loader = unittest.TestLoader()
        names = loader.getTestCaseNames(BadCase)
        self.assertEqual(names, ['test_foo'])

    def test_getTestCaseNames__inheritance(self):


        class TestP(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foobar(self):
                pass


        class TestC(TestP):

            def test_1(self):
                pass

            def test_3(self):
                pass
        loader = unittest.TestLoader()
        names = ['test_1', 'test_2', 'test_3']
        self.assertEqual(loader.getTestCaseNames(TestC), names)

    def test_testMethodPrefix__loadTestsFromTestCase(self):


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foo_bar(self):
                pass
        tests_1 = unittest.TestSuite([Foo('foo_bar')])
        tests_2 = unittest.TestSuite([Foo('test_1'), Foo('test_2')])
        loader = unittest.TestLoader()
        loader.testMethodPrefix = 'foo'
        self.assertEqual(loader.loadTestsFromTestCase(Foo), tests_1)
        loader.testMethodPrefix = 'test'
        self.assertEqual(loader.loadTestsFromTestCase(Foo), tests_2)

    def test_testMethodPrefix__loadTestsFromModule(self):
        m = types.ModuleType('m')


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foo_bar(self):
                pass
        m.Foo = Foo
        tests_1 = [unittest.TestSuite([Foo('foo_bar')])]
        tests_2 = [unittest.TestSuite([Foo('test_1'), Foo('test_2')])]
        loader = unittest.TestLoader()
        loader.testMethodPrefix = 'foo'
        self.assertEqual(list(loader.loadTestsFromModule(m)), tests_1)
        loader.testMethodPrefix = 'test'
        self.assertEqual(list(loader.loadTestsFromModule(m)), tests_2)

    def test_testMethodPrefix__loadTestsFromName(self):
        m = types.ModuleType('m')


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foo_bar(self):
                pass
        m.Foo = Foo
        tests_1 = unittest.TestSuite([Foo('foo_bar')])
        tests_2 = unittest.TestSuite([Foo('test_1'), Foo('test_2')])
        loader = unittest.TestLoader()
        loader.testMethodPrefix = 'foo'
        self.assertEqual(loader.loadTestsFromName('Foo', m), tests_1)
        loader.testMethodPrefix = 'test'
        self.assertEqual(loader.loadTestsFromName('Foo', m), tests_2)

    def test_testMethodPrefix__loadTestsFromNames(self):
        m = types.ModuleType('m')


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foo_bar(self):
                pass
        m.Foo = Foo
        tests_1 = unittest.TestSuite([unittest.TestSuite([Foo('foo_bar')])])
        tests_2 = unittest.TestSuite([Foo('test_1'), Foo('test_2')])
        tests_2 = unittest.TestSuite([tests_2])
        loader = unittest.TestLoader()
        loader.testMethodPrefix = 'foo'
        self.assertEqual(loader.loadTestsFromNames(['Foo'], m), tests_1)
        loader.testMethodPrefix = 'test'
        self.assertEqual(loader.loadTestsFromNames(['Foo'], m), tests_2)

    def test_testMethodPrefix__default_value(self):
        loader = unittest.TestLoader()
        self.assertEqual(loader.testMethodPrefix, 'test')

    def test_sortTestMethodsUsing__loadTestsFromTestCase(self):

        def reversed_cmp(x, y):
            return -((x > y) - (x < y))


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass
        loader = unittest.TestLoader()
        loader.sortTestMethodsUsing = reversed_cmp
        tests = loader.suiteClass([Foo('test_2'), Foo('test_1')])
        self.assertEqual(loader.loadTestsFromTestCase(Foo), tests)

    def test_sortTestMethodsUsing__loadTestsFromModule(self):

        def reversed_cmp(x, y):
            return -((x > y) - (x < y))
        m = types.ModuleType('m')


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass
        m.Foo = Foo
        loader = unittest.TestLoader()
        loader.sortTestMethodsUsing = reversed_cmp
        tests = [loader.suiteClass([Foo('test_2'), Foo('test_1')])]
        self.assertEqual(list(loader.loadTestsFromModule(m)), tests)

    def test_sortTestMethodsUsing__loadTestsFromName(self):

        def reversed_cmp(x, y):
            return -((x > y) - (x < y))
        m = types.ModuleType('m')


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass
        m.Foo = Foo
        loader = unittest.TestLoader()
        loader.sortTestMethodsUsing = reversed_cmp
        tests = loader.suiteClass([Foo('test_2'), Foo('test_1')])
        self.assertEqual(loader.loadTestsFromName('Foo', m), tests)

    def test_sortTestMethodsUsing__loadTestsFromNames(self):

        def reversed_cmp(x, y):
            return -((x > y) - (x < y))
        m = types.ModuleType('m')


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass
        m.Foo = Foo
        loader = unittest.TestLoader()
        loader.sortTestMethodsUsing = reversed_cmp
        tests = [loader.suiteClass([Foo('test_2'), Foo('test_1')])]
        self.assertEqual(list(loader.loadTestsFromNames(['Foo'], m)), tests)

    def test_sortTestMethodsUsing__getTestCaseNames(self):

        def reversed_cmp(x, y):
            return -((x > y) - (x < y))


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass
        loader = unittest.TestLoader()
        loader.sortTestMethodsUsing = reversed_cmp
        test_names = ['test_2', 'test_1']
        self.assertEqual(loader.getTestCaseNames(Foo), test_names)

    def test_sortTestMethodsUsing__default_value(self):
        loader = unittest.TestLoader()


        class Foo(unittest.TestCase):

            def test_2(self):
                pass

            def test_3(self):
                pass

            def test_1(self):
                pass
        test_names = ['test_2', 'test_3', 'test_1']
        self.assertEqual(loader.getTestCaseNames(Foo), sorted(test_names))

    def test_sortTestMethodsUsing__None(self):


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass
        loader = unittest.TestLoader()
        loader.sortTestMethodsUsing = None
        test_names = ['test_2', 'test_1']
        self.assertEqual(set(loader.getTestCaseNames(Foo)), set(test_names))

    def test_suiteClass__loadTestsFromTestCase(self):


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foo_bar(self):
                pass
        tests = [Foo('test_1'), Foo('test_2')]
        loader = unittest.TestLoader()
        loader.suiteClass = list
        self.assertEqual(loader.loadTestsFromTestCase(Foo), tests)

    def test_suiteClass__loadTestsFromModule(self):
        m = types.ModuleType('m')


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foo_bar(self):
                pass
        m.Foo = Foo
        tests = [[Foo('test_1'), Foo('test_2')]]
        loader = unittest.TestLoader()
        loader.suiteClass = list
        self.assertEqual(loader.loadTestsFromModule(m), tests)

    def test_suiteClass__loadTestsFromName(self):
        m = types.ModuleType('m')


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foo_bar(self):
                pass
        m.Foo = Foo
        tests = [Foo('test_1'), Foo('test_2')]
        loader = unittest.TestLoader()
        loader.suiteClass = list
        self.assertEqual(loader.loadTestsFromName('Foo', m), tests)

    def test_suiteClass__loadTestsFromNames(self):
        m = types.ModuleType('m')


        class Foo(unittest.TestCase):

            def test_1(self):
                pass

            def test_2(self):
                pass

            def foo_bar(self):
                pass
        m.Foo = Foo
        tests = [[Foo('test_1'), Foo('test_2')]]
        loader = unittest.TestLoader()
        loader.suiteClass = list
        self.assertEqual(loader.loadTestsFromNames(['Foo'], m), tests)

    def test_suiteClass__default_value(self):
        loader = unittest.TestLoader()
        self.assertIs(loader.suiteClass, unittest.TestSuite)


if __name__ == '__main__':
    unittest.main()
