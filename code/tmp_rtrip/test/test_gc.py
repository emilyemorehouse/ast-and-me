import unittest
from test.support import verbose, refcount_test, run_unittest, strip_python_stderr, cpython_only, start_threads, temp_dir, requires_type_collecting
from test.support.script_helper import assert_python_ok, make_script
import sys
import time
import gc
import weakref
try:
    import threading
except ImportError:
    threading = None
try:
    from _testcapi import with_tp_del
except ImportError:

    def with_tp_del(cls):


        class C(object):

            def __new__(cls, *args, **kwargs):
                raise TypeError('requires _testcapi.with_tp_del')
        return C


class C1055820(object):

    def __init__(self, i):
        self.i = i
        self.loop = self


class GC_Detector(object):

    def __init__(self):
        self.gc_happened = False

        def it_happened(ignored):
            self.gc_happened = True
        self.wr = weakref.ref(C1055820(666), it_happened)


@with_tp_del
class Uncollectable(object):
    """Create a reference cycle with multiple __del__ methods.

    An object in a reference cycle will never have zero references,
    and so must be garbage collected.  If one or more objects in the
    cycle have __del__ methods, the gc refuses to guess an order,
    and leaves the cycle uncollected."""

    def __init__(self, partner=None):
        if partner is None:
            self.partner = Uncollectable(partner=self)
        else:
            self.partner = partner

    def __tp_del__(self):
        pass


class GCTests(unittest.TestCase):

    def test_list(self):
        l = []
        l.append(l)
        gc.collect()
        del l
        self.assertEqual(gc.collect(), 1)

    def test_dict(self):
        d = {}
        d[1] = d
        gc.collect()
        del d
        self.assertEqual(gc.collect(), 1)

    def test_tuple(self):
        l = []
        t = l,
        l.append(t)
        gc.collect()
        del t
        del l
        self.assertEqual(gc.collect(), 2)

    def test_class(self):


        class A:
            pass
        A.a = A
        gc.collect()
        del A
        self.assertNotEqual(gc.collect(), 0)

    def test_newstyleclass(self):


        class A(object):
            pass
        gc.collect()
        del A
        self.assertNotEqual(gc.collect(), 0)

    def test_instance(self):


        class A:
            pass
        a = A()
        a.a = a
        gc.collect()
        del a
        self.assertNotEqual(gc.collect(), 0)

    @requires_type_collecting
    def test_newinstance(self):


        class A(object):
            pass
        a = A()
        a.a = a
        gc.collect()
        del a
        self.assertNotEqual(gc.collect(), 0)


        class B(list):
            pass


        class C(B, A):
            pass
        a = C()
        a.a = a
        gc.collect()
        del a
        self.assertNotEqual(gc.collect(), 0)
        del B, C
        self.assertNotEqual(gc.collect(), 0)
        A.a = A()
        del A
        self.assertNotEqual(gc.collect(), 0)
        self.assertEqual(gc.collect(), 0)

    def test_method(self):


        class A:

            def __init__(self):
                self.init = self.__init__
        a = A()
        gc.collect()
        del a
        self.assertNotEqual(gc.collect(), 0)

    @cpython_only
    def test_legacy_finalizer(self):


        @with_tp_del
        class A:

            def __tp_del__(self):
                pass


        class B:
            pass
        a = A()
        a.a = a
        id_a = id(a)
        b = B()
        b.b = b
        gc.collect()
        del a
        del b
        self.assertNotEqual(gc.collect(), 0)
        for obj in gc.garbage:
            if id(obj) == id_a:
                del obj.a
                break
        else:
            self.fail("didn't find obj in garbage (finalizer)")
        gc.garbage.remove(obj)

    @cpython_only
    def test_legacy_finalizer_newclass(self):


        @with_tp_del
        class A(object):

            def __tp_del__(self):
                pass


        class B(object):
            pass
        a = A()
        a.a = a
        id_a = id(a)
        b = B()
        b.b = b
        gc.collect()
        del a
        del b
        self.assertNotEqual(gc.collect(), 0)
        for obj in gc.garbage:
            if id(obj) == id_a:
                del obj.a
                break
        else:
            self.fail("didn't find obj in garbage (finalizer)")
        gc.garbage.remove(obj)

    def test_function(self):
        d = {}
        exec('def f(): pass\n', d)
        gc.collect()
        del d
        self.assertEqual(gc.collect(), 2)

    @refcount_test
    def test_frame(self):

        def f():
            frame = sys._getframe()
        gc.collect()
        f()
        self.assertEqual(gc.collect(), 1)

    def test_saveall(self):
        gc.collect()
        self.assertEqual(gc.garbage, [])
        L = []
        L.append(L)
        id_L = id(L)
        debug = gc.get_debug()
        gc.set_debug(debug | gc.DEBUG_SAVEALL)
        del L
        gc.collect()
        gc.set_debug(debug)
        self.assertEqual(len(gc.garbage), 1)
        obj = gc.garbage.pop()
        self.assertEqual(id(obj), id_L)

    def test_del(self):
        thresholds = gc.get_threshold()
        gc.enable()
        gc.set_threshold(1)


        class A:

            def __del__(self):
                dir(self)
        a = A()
        del a
        gc.disable()
        gc.set_threshold(*thresholds)

    def test_del_newclass(self):
        thresholds = gc.get_threshold()
        gc.enable()
        gc.set_threshold(1)


        class A(object):

            def __del__(self):
                dir(self)
        a = A()
        del a
        gc.disable()
        gc.set_threshold(*thresholds)

    @refcount_test
    def test_get_count(self):
        gc.collect()
        a, b, c = gc.get_count()
        x = []
        d, e, f = gc.get_count()
        self.assertEqual((b, c), (0, 0))
        self.assertEqual((e, f), (0, 0))
        self.assertLess(a, 5)
        self.assertGreater(d, a)

    @refcount_test
    def test_collect_generations(self):
        gc.collect()
        x = []
        gc.collect(0)
        a, b, c = gc.get_count()
        gc.collect(1)
        d, e, f = gc.get_count()
        gc.collect(2)
        g, h, i = gc.get_count()
        self.assertEqual((b, c), (1, 0))
        self.assertEqual((e, f), (0, 1))
        self.assertEqual((h, i), (0, 0))

    def test_trashcan(self):


        class Ouch:
            n = 0

            def __del__(self):
                Ouch.n = Ouch.n + 1
                if Ouch.n % 17 == 0:
                    gc.collect()
        gc.enable()
        N = 150
        for count in range(2):
            t = []
            for i in range(N):
                t = [t, Ouch()]
            u = []
            for i in range(N):
                u = [u, Ouch()]
            v = {}
            for i in range(N):
                v = {(1): v, (2): Ouch()}
        gc.disable()

    @unittest.skipUnless(threading,
        'test meaningless on builds without threads')
    def test_trashcan_threads(self):
        NESTING = 60
        N_THREADS = 2

        def sleeper_gen():
            """A generator that releases the GIL when closed or dealloc'ed."""
            try:
                yield
            finally:
                time.sleep(1e-06)


        class C(list):
            inits = []
            dels = []

            def __init__(self, alist):
                self[:] = alist
                C.inits.append(None)

            def __del__(self):
                C.dels.append(None)
                g = sleeper_gen()
                next(g)

        def make_nested():
            """Create a sufficiently nested container object so that the
            trashcan mechanism is invoked when deallocating it."""
            x = C([])
            for i in range(NESTING):
                x = [C([x])]
            del x

        def run_thread():
            """Exercise make_nested() in a loop."""
            while not exit:
                make_nested()
        old_switchinterval = sys.getswitchinterval()
        sys.setswitchinterval(1e-05)
        try:
            exit = []
            threads = []
            for i in range(N_THREADS):
                t = threading.Thread(target=run_thread)
                threads.append(t)
            with start_threads(threads, lambda : exit.append(1)):
                time.sleep(1.0)
        finally:
            sys.setswitchinterval(old_switchinterval)
        gc.collect()
        self.assertEqual(len(C.inits), len(C.dels))

    def test_boom(self):


        class Boom:

            def __getattr__(self, someattribute):
                del self.attr
                raise AttributeError
        a = Boom()
        b = Boom()
        a.attr = b
        b.attr = a
        gc.collect()
        garbagelen = len(gc.garbage)
        del a, b
        self.assertEqual(gc.collect(), 4)
        self.assertEqual(len(gc.garbage), garbagelen)

    def test_boom2(self):


        class Boom2:

            def __init__(self):
                self.x = 0

            def __getattr__(self, someattribute):
                self.x += 1
                if self.x > 1:
                    del self.attr
                raise AttributeError
        a = Boom2()
        b = Boom2()
        a.attr = b
        b.attr = a
        gc.collect()
        garbagelen = len(gc.garbage)
        del a, b
        self.assertEqual(gc.collect(), 4)
        self.assertEqual(len(gc.garbage), garbagelen)

    def test_boom_new(self):


        class Boom_New(object):

            def __getattr__(self, someattribute):
                del self.attr
                raise AttributeError
        a = Boom_New()
        b = Boom_New()
        a.attr = b
        b.attr = a
        gc.collect()
        garbagelen = len(gc.garbage)
        del a, b
        self.assertEqual(gc.collect(), 4)
        self.assertEqual(len(gc.garbage), garbagelen)

    def test_boom2_new(self):


        class Boom2_New(object):

            def __init__(self):
                self.x = 0

            def __getattr__(self, someattribute):
                self.x += 1
                if self.x > 1:
                    del self.attr
                raise AttributeError
        a = Boom2_New()
        b = Boom2_New()
        a.attr = b
        b.attr = a
        gc.collect()
        garbagelen = len(gc.garbage)
        del a, b
        self.assertEqual(gc.collect(), 4)
        self.assertEqual(len(gc.garbage), garbagelen)

    def test_get_referents(self):
        alist = [1, 3, 5]
        got = gc.get_referents(alist)
        got.sort()
        self.assertEqual(got, alist)
        atuple = tuple(alist)
        got = gc.get_referents(atuple)
        got.sort()
        self.assertEqual(got, alist)
        adict = {(1): 3, (5): 7}
        expected = [1, 3, 5, 7]
        got = gc.get_referents(adict)
        got.sort()
        self.assertEqual(got, expected)
        got = gc.get_referents([1, 2], {(3): 4}, (0, 0, 0))
        got.sort()
        self.assertEqual(got, [0, 0] + list(range(5)))
        self.assertEqual(gc.get_referents(1, 'a', 4j), [])

    def test_is_tracked(self):
        self.assertFalse(gc.is_tracked(None))
        self.assertFalse(gc.is_tracked(1))
        self.assertFalse(gc.is_tracked(1.0))
        self.assertFalse(gc.is_tracked(1.0 + 5j))
        self.assertFalse(gc.is_tracked(True))
        self.assertFalse(gc.is_tracked(False))
        self.assertFalse(gc.is_tracked(b'a'))
        self.assertFalse(gc.is_tracked('a'))
        self.assertFalse(gc.is_tracked(bytearray(b'a')))
        self.assertFalse(gc.is_tracked(type))
        self.assertFalse(gc.is_tracked(int))
        self.assertFalse(gc.is_tracked(object))
        self.assertFalse(gc.is_tracked(object()))


        class UserClass:
            pass


        class UserInt(int):
            pass


        class UserClassSlots:
            __slots__ = ()


        class UserFloatSlots(float):
            __slots__ = ()


        class UserIntSlots(int):
            __slots__ = ()
        self.assertTrue(gc.is_tracked(gc))
        self.assertTrue(gc.is_tracked(UserClass))
        self.assertTrue(gc.is_tracked(UserClass()))
        self.assertTrue(gc.is_tracked(UserInt()))
        self.assertTrue(gc.is_tracked([]))
        self.assertTrue(gc.is_tracked(set()))
        self.assertFalse(gc.is_tracked(UserClassSlots()))
        self.assertFalse(gc.is_tracked(UserFloatSlots()))
        self.assertFalse(gc.is_tracked(UserIntSlots()))

    def test_bug1055820b(self):
        ouch = []

        def callback(ignored):
            ouch[:] = [wr() for wr in WRs]
        Cs = [C1055820(i) for i in range(2)]
        WRs = [weakref.ref(c, callback) for c in Cs]
        c = None
        gc.collect()
        self.assertEqual(len(ouch), 0)
        Cs = None
        gc.collect()
        self.assertEqual(len(ouch), 2)
        for x in ouch:
            self.assertEqual(x, None)

    def test_bug21435(self):
        gc.collect()


        class A:
            pass


        class B:

            def __init__(self, x):
                self.x = x

            def __del__(self):
                self.attr = None

        def do_work():
            a = A()
            b = B(A())
            a.attr = b
            b.attr = a
        do_work()
        gc.collect()

    @cpython_only
    def test_garbage_at_shutdown(self):
        import subprocess
        code = """if 1:
            import gc
            import _testcapi
            @_testcapi.with_tp_del
            class X:
                def __init__(self, name):
                    self.name = name
                def __repr__(self):
                    return "<X %%r>" %% self.name
                def __tp_del__(self):
                    pass

            x = X('first')
            x.x = x
            x.y = X('second')
            del x
            gc.set_debug(%s)
        """

        def run_command(code):
            p = subprocess.Popen([sys.executable, '-Wd', '-c', code],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            p.stdout.close()
            p.stderr.close()
            self.assertEqual(p.returncode, 0)
            self.assertEqual(stdout.strip(), b'')
            return strip_python_stderr(stderr)
        stderr = run_command(code % '0')
        self.assertIn(
            b'ResourceWarning: gc: 2 uncollectable objects at shutdown; use',
            stderr)
        self.assertNotIn(b"<X 'first'>", stderr)
        stderr = run_command(code % 'gc.DEBUG_UNCOLLECTABLE')
        self.assertIn(
            b'ResourceWarning: gc: 2 uncollectable objects at shutdown', stderr
            )
        self.assertTrue(b"[<X 'first'>, <X 'second'>]" in stderr or 
            b"[<X 'second'>, <X 'first'>]" in stderr, stderr)
        stderr = run_command(code % 'gc.DEBUG_SAVEALL')
        self.assertNotIn(b'uncollectable objects at shutdown', stderr)

    @requires_type_collecting
    def test_gc_main_module_at_shutdown(self):
        code = """if 1:
            class C:
                def __del__(self):
                    print('__del__ called')
            l = [C()]
            l.append(l)
            """
        rc, out, err = assert_python_ok('-c', code)
        self.assertEqual(out.strip(), b'__del__ called')

    @requires_type_collecting
    def test_gc_ordinary_module_at_shutdown(self):
        with temp_dir() as script_dir:
            module = """if 1:
                class C:
                    def __del__(self):
                        print('__del__ called')
                l = [C()]
                l.append(l)
                """
            code = (
                """if 1:
                import sys
                sys.path.insert(0, %r)
                import gctest
                """
                 % (script_dir,))
            make_script(script_dir, 'gctest', module)
            rc, out, err = assert_python_ok('-c', code)
            self.assertEqual(out.strip(), b'__del__ called')

    def test_get_stats(self):
        stats = gc.get_stats()
        self.assertEqual(len(stats), 3)
        for st in stats:
            self.assertIsInstance(st, dict)
            self.assertEqual(set(st), {'collected', 'collections',
                'uncollectable'})
            self.assertGreaterEqual(st['collected'], 0)
            self.assertGreaterEqual(st['collections'], 0)
            self.assertGreaterEqual(st['uncollectable'], 0)
        if gc.isenabled():
            self.addCleanup(gc.enable)
            gc.disable()
        old = gc.get_stats()
        gc.collect(0)
        new = gc.get_stats()
        self.assertEqual(new[0]['collections'], old[0]['collections'] + 1)
        self.assertEqual(new[1]['collections'], old[1]['collections'])
        self.assertEqual(new[2]['collections'], old[2]['collections'])
        gc.collect(2)
        new = gc.get_stats()
        self.assertEqual(new[0]['collections'], old[0]['collections'] + 1)
        self.assertEqual(new[1]['collections'], old[1]['collections'])
        self.assertEqual(new[2]['collections'], old[2]['collections'] + 1)


class GCCallbackTests(unittest.TestCase):

    def setUp(self):
        self.enabled = gc.isenabled()
        gc.disable()
        self.debug = gc.get_debug()
        gc.set_debug(0)
        gc.callbacks.append(self.cb1)
        gc.callbacks.append(self.cb2)
        self.othergarbage = []

    def tearDown(self):
        del self.visit
        gc.callbacks.remove(self.cb1)
        gc.callbacks.remove(self.cb2)
        gc.set_debug(self.debug)
        if self.enabled:
            gc.enable()
        gc.collect()
        for obj in gc.garbage:
            if isinstance(obj, Uncollectable):
                obj.partner = None
        del gc.garbage[:]
        del self.othergarbage
        gc.collect()

    def preclean(self):
        self.visit = []
        gc.collect()
        garbage, gc.garbage[:] = gc.garbage[:], []
        self.othergarbage.append(garbage)
        self.visit = []

    def cb1(self, phase, info):
        self.visit.append((1, phase, dict(info)))

    def cb2(self, phase, info):
        self.visit.append((2, phase, dict(info)))
        if phase == 'stop' and hasattr(self, 'cleanup'):
            uc = [e for e in gc.garbage if isinstance(e, Uncollectable)]
            gc.garbage[:] = [e for e in gc.garbage if not isinstance(e,
                Uncollectable)]
            for e in uc:
                e.partner = None

    def test_collect(self):
        self.preclean()
        gc.collect()
        n = [v[0] for v in self.visit]
        n1 = [i for i in n if i == 1]
        n2 = [i for i in n if i == 2]
        self.assertEqual(n1, [1] * 2)
        self.assertEqual(n2, [2] * 2)
        n = [v[1] for v in self.visit]
        n1 = [i for i in n if i == 'start']
        n2 = [i for i in n if i == 'stop']
        self.assertEqual(n1, ['start'] * 2)
        self.assertEqual(n2, ['stop'] * 2)
        for v in self.visit:
            info = v[2]
            self.assertTrue('generation' in info)
            self.assertTrue('collected' in info)
            self.assertTrue('uncollectable' in info)

    def test_collect_generation(self):
        self.preclean()
        gc.collect(2)
        for v in self.visit:
            info = v[2]
            self.assertEqual(info['generation'], 2)

    @cpython_only
    def test_collect_garbage(self):
        self.preclean()
        Uncollectable()
        Uncollectable()
        C1055820(666)
        gc.collect()
        for v in self.visit:
            if v[1] != 'stop':
                continue
            info = v[2]
            self.assertEqual(info['collected'], 2)
            self.assertEqual(info['uncollectable'], 8)
        self.assertEqual(len(gc.garbage), 4)
        for e in gc.garbage:
            self.assertIsInstance(e, Uncollectable)
        self.cleanup = True
        self.visit = []
        gc.garbage[:] = []
        gc.collect()
        for v in self.visit:
            if v[1] != 'stop':
                continue
            info = v[2]
            self.assertEqual(info['collected'], 0)
            self.assertEqual(info['uncollectable'], 4)
        self.assertEqual(len(gc.garbage), 0)


class GCTogglingTests(unittest.TestCase):

    def setUp(self):
        gc.enable()

    def tearDown(self):
        gc.disable()

    def test_bug1055820c(self):
        c0 = C1055820(0)
        gc.collect()
        c1 = C1055820(1)
        c1.keep_c0_alive = c0
        del c0.loop
        c2 = C1055820(2)
        c2wr = weakref.ref(c2)
        ouch = []

        def callback(ignored):
            ouch[:] = [c2wr()]
        c0wr = weakref.ref(c0, callback)
        c0 = c1 = c2 = None
        junk = []
        i = 0
        detector = GC_Detector()
        while not detector.gc_happened:
            i += 1
            if i > 10000:
                self.fail("gc didn't happen after 10000 iterations")
            self.assertEqual(len(ouch), 0)
            junk.append([])
        self.assertEqual(len(ouch), 1)
        for x in ouch:
            self.assertEqual(x, None)

    def test_bug1055820d(self):
        ouch = []


        class D(C1055820):

            def __del__(self):
                ouch[:] = [c2wr()]
        d0 = D(0)
        gc.collect()
        c1 = C1055820(1)
        c1.keep_d0_alive = d0
        del d0.loop
        c2 = C1055820(2)
        c2wr = weakref.ref(c2)
        d0 = c1 = c2 = None
        detector = GC_Detector()
        junk = []
        i = 0
        while not detector.gc_happened:
            i += 1
            if i > 10000:
                self.fail("gc didn't happen after 10000 iterations")
            self.assertEqual(len(ouch), 0)
            junk.append([])
        self.assertEqual(len(ouch), 1)
        for x in ouch:
            self.assertEqual(x, None)


def test_main():
    enabled = gc.isenabled()
    gc.disable()
    assert not gc.isenabled()
    debug = gc.get_debug()
    gc.set_debug(debug & ~gc.DEBUG_LEAK)
    try:
        gc.collect()
        run_unittest(GCTests, GCTogglingTests, GCCallbackTests)
    finally:
        gc.set_debug(debug)
        if verbose:
            print('restoring automatic collection')
        gc.enable()
        assert gc.isenabled()
        if not enabled:
            gc.disable()


if __name__ == '__main__':
    test_main()
