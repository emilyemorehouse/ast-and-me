import unittest
from doctest import DocTestSuite
from test import support
import weakref
import gc
_thread = support.import_module('_thread')
threading = support.import_module('threading')
import _threading_local


class Weak(object):
    pass


def target(local, weaklist):
    weak = Weak()
    local.weak = weak
    weaklist.append(weakref.ref(weak))


class BaseLocalTest:

    def test_local_refs(self):
        self._local_refs(20)
        self._local_refs(50)
        self._local_refs(100)

    def _local_refs(self, n):
        local = self._local()
        weaklist = []
        for i in range(n):
            t = threading.Thread(target=target, args=(local, weaklist))
            t.start()
            t.join()
        del t
        gc.collect()
        self.assertEqual(len(weaklist), n)
        deadlist = [weak for weak in weaklist if weak() is None]
        self.assertIn(len(deadlist), (n - 1, n))
        local.someothervar = None
        gc.collect()
        deadlist = [weak for weak in weaklist if weak() is None]
        self.assertIn(len(deadlist), (n - 1, n), (n, len(deadlist)))

    def test_derived(self):
        import time


        class Local(self._local):

            def __init__(self):
                time.sleep(0.01)
        local = Local()

        def f(i):
            local.x = i
            self.assertEqual(local.x, i)
        with support.start_threads(threading.Thread(target=f, args=(i,)) for
            i in range(10)):
            pass

    def test_derived_cycle_dealloc(self):


        class Local(self._local):
            pass
        locals = None
        passed = False
        e1 = threading.Event()
        e2 = threading.Event()

        def f():
            nonlocal passed
            cycle = [Local()]
            cycle.append(cycle)
            cycle[0].foo = 'bar'
            del cycle
            gc.collect()
            e1.set()
            e2.wait()
            passed = all(not hasattr(local, 'foo') for local in locals)
        t = threading.Thread(target=f)
        t.start()
        e1.wait()
        locals = [Local() for i in range(10)]
        e2.set()
        t.join()
        self.assertTrue(passed)

    def test_arguments(self):


        class MyLocal(self._local):

            def __init__(self, *args, **kwargs):
                pass
        MyLocal(a=1)
        MyLocal(1)
        self.assertRaises(TypeError, self._local, a=1)
        self.assertRaises(TypeError, self._local, 1)

    def _test_one_class(self, c):
        self._failed = 'No error message set or cleared.'
        obj = c()
        e1 = threading.Event()
        e2 = threading.Event()

        def f1():
            obj.x = 'foo'
            obj.y = 'bar'
            del obj.y
            e1.set()
            e2.wait()

        def f2():
            try:
                foo = obj.x
            except AttributeError:
                self._failed = ''
            else:
                self._failed = 'Incorrectly got value %r from class %r\n' % (
                    foo, c)
                sys.stderr.write(self._failed)
        t1 = threading.Thread(target=f1)
        t1.start()
        e1.wait()
        t2 = threading.Thread(target=f2)
        t2.start()
        t2.join()
        e2.set()
        t1.join()
        self.assertFalse(self._failed, self._failed)

    def test_threading_local(self):
        self._test_one_class(self._local)

    def test_threading_local_subclass(self):


        class LocalSubclass(self._local):
            """To test that subclasses behave properly."""
        self._test_one_class(LocalSubclass)

    def _test_dict_attribute(self, cls):
        obj = cls()
        obj.x = 5
        self.assertEqual(obj.__dict__, {'x': 5})
        with self.assertRaises(AttributeError):
            obj.__dict__ = {}
        with self.assertRaises(AttributeError):
            del obj.__dict__

    def test_dict_attribute(self):
        self._test_dict_attribute(self._local)

    def test_dict_attribute_subclass(self):


        class LocalSubclass(self._local):
            """To test that subclasses behave properly."""
        self._test_dict_attribute(LocalSubclass)

    def test_cycle_collection(self):


        class X:
            pass
        x = X()
        x.local = self._local()
        x.local.x = x
        wr = weakref.ref(x)
        del x
        gc.collect()
        self.assertIsNone(wr())


class ThreadLocalTest(unittest.TestCase, BaseLocalTest):
    _local = _thread._local


class PyThreadingLocalTest(unittest.TestCase, BaseLocalTest):
    _local = _threading_local.local


def test_main():
    suite = unittest.TestSuite()
    suite.addTest(DocTestSuite('_threading_local'))
    suite.addTest(unittest.makeSuite(ThreadLocalTest))
    suite.addTest(unittest.makeSuite(PyThreadingLocalTest))
    local_orig = _threading_local.local

    def setUp(test):
        _threading_local.local = _thread._local

    def tearDown(test):
        _threading_local.local = local_orig
    suite.addTest(DocTestSuite('_threading_local', setUp=setUp, tearDown=
        tearDown))
    support.run_unittest(suite)


if __name__ == '__main__':
    test_main()
