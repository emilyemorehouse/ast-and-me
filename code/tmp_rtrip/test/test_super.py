"""Unit tests for zero-argument super() & related machinery."""
import sys
import unittest
import warnings
from test.support import check_warnings


class A:

    def f(self):
        return 'A'

    @classmethod
    def cm(cls):
        return cls, 'A'


class B(A):

    def f(self):
        return super().f() + 'B'

    @classmethod
    def cm(cls):
        return cls, super().cm(), 'B'


class C(A):

    def f(self):
        return super().f() + 'C'

    @classmethod
    def cm(cls):
        return cls, super().cm(), 'C'


class D(C, B):

    def f(self):
        return super().f() + 'D'

    def cm(cls):
        return cls, super().cm(), 'D'


class E(D):
    pass


class F(E):
    f = E.f


class G(A):
    pass


class TestSuper(unittest.TestCase):

    def tearDown(self):
        nonlocal __class__
        __class__ = TestSuper

    def test_basics_working(self):
        self.assertEqual(D().f(), 'ABCD')

    def test_class_getattr_working(self):
        self.assertEqual(D.f(D()), 'ABCD')

    def test_subclass_no_override_working(self):
        self.assertEqual(E().f(), 'ABCD')
        self.assertEqual(E.f(E()), 'ABCD')

    def test_unbound_method_transfer_working(self):
        self.assertEqual(F().f(), 'ABCD')
        self.assertEqual(F.f(F()), 'ABCD')

    def test_class_methods_still_working(self):
        self.assertEqual(A.cm(), (A, 'A'))
        self.assertEqual(A().cm(), (A, 'A'))
        self.assertEqual(G.cm(), (G, 'A'))
        self.assertEqual(G().cm(), (G, 'A'))

    def test_super_in_class_methods_working(self):
        d = D()
        self.assertEqual(d.cm(), (d, (D, (D, (D, 'A'), 'B'), 'C'), 'D'))
        e = E()
        self.assertEqual(e.cm(), (e, (E, (E, (E, 'A'), 'B'), 'C'), 'D'))

    def test_super_with_closure(self):


        class E(A):

            def f(self):

                def nested():
                    self
                return super().f() + 'E'
        self.assertEqual(E().f(), 'AE')

    def test_various___class___pathologies(self):


        class X(A):

            def f(self):
                return super().f()
            __class__ = 413
        x = X()
        self.assertEqual(x.f(), 'A')
        self.assertEqual(x.__class__, 413)


        class X:
            x = __class__

            def f():
                __class__
        self.assertIs(X.x, type(self))
        with self.assertRaises(NameError) as e:
            exec(
                """class X:
                __class__
                def f():
                    __class__"""
                , globals(), {})
        self.assertIs(type(e.exception), NameError)


        class X:
            global __class__
            __class__ = 42

            def f():
                __class__
        self.assertEqual(globals()['__class__'], 42)
        del globals()['__class__']
        self.assertNotIn('__class__', X.__dict__)


        class X:
            nonlocal __class__
            __class__ = 42

            def f():
                __class__
        self.assertEqual(__class__, 42)

    def test___class___instancemethod(self):


        class X:

            def f(self):
                return __class__
        self.assertIs(X().f(), X)

    def test___class___classmethod(self):


        class X:

            @classmethod
            def f(cls):
                return __class__
        self.assertIs(X.f(), X)

    def test___class___staticmethod(self):


        class X:

            @staticmethod
            def f():
                return __class__
        self.assertIs(X.f(), X)

    def test___class___new(self):
        test_class = None


        class Meta(type):

            def __new__(cls, name, bases, namespace):
                nonlocal test_class
                self = super().__new__(cls, name, bases, namespace)
                test_class = self.f()
                return self


        class A(metaclass=Meta):

            @staticmethod
            def f():
                return __class__
        self.assertIs(test_class, A)

    def test___class___delayed(self):
        test_namespace = None


        class Meta(type):

            def __new__(cls, name, bases, namespace):
                nonlocal test_namespace
                test_namespace = namespace
                return None
        with check_warnings() as w:
            warnings.simplefilter('always', DeprecationWarning)


            class A(metaclass=Meta):

                @staticmethod
                def f():
                    return __class__
        self.assertEqual(w.warnings, [])
        self.assertIs(A, None)
        B = type('B', (), test_namespace)
        self.assertIs(B.f(), B)

    def test___class___mro(self):
        test_class = None


        class Meta(type):

            def mro(self):
                self.__dict__['f']()
                return super().mro()


        class A(metaclass=Meta):

            def f():
                nonlocal test_class
                test_class = __class__
        self.assertIs(test_class, A)

    def test___classcell___expected_behaviour(self):


        class Meta(type):

            def __new__(cls, name, bases, namespace):
                nonlocal namespace_snapshot
                namespace_snapshot = namespace.copy()
                return super().__new__(cls, name, bases, namespace)
        namespace_snapshot = None


        class WithoutClassRef(metaclass=Meta):
            pass
        self.assertNotIn('__classcell__', namespace_snapshot)
        namespace_snapshot = None


        class WithClassRef(metaclass=Meta):

            def f(self):
                return __class__
        class_cell = namespace_snapshot['__classcell__']
        method_closure = WithClassRef.f.__closure__
        self.assertEqual(len(method_closure), 1)
        self.assertIs(class_cell, method_closure[0])
        with self.assertRaises(AttributeError):
            WithClassRef.__classcell__

    def test___classcell___missing(self):


        class Meta(type):

            def __new__(cls, name, bases, namespace):
                namespace.pop('__classcell__', None)
                return super().__new__(cls, name, bases, namespace)
        with check_warnings() as w:
            warnings.simplefilter('always', DeprecationWarning)


            class WithoutClassRef(metaclass=Meta):
                pass
        self.assertEqual(w.warnings, [])
        expected_warning = ('__class__ not set.*__classcell__ propagated',
            DeprecationWarning)
        with check_warnings(expected_warning):
            warnings.simplefilter('always', DeprecationWarning)


            class WithClassRef(metaclass=Meta):

                def f(self):
                    return __class__
        self.assertIs(WithClassRef().f(), WithClassRef)
        with warnings.catch_warnings():
            warnings.simplefilter('error', DeprecationWarning)
            with self.assertRaises(DeprecationWarning):


                class WithClassRef(metaclass=Meta):

                    def f(self):
                        return __class__

    def test___classcell___overwrite(self):


        class Meta(type):

            def __new__(cls, name, bases, namespace, cell):
                namespace['__classcell__'] = cell
                return super().__new__(cls, name, bases, namespace)
        for bad_cell in (None, 0, '', object()):
            with self.subTest(bad_cell=bad_cell):
                with self.assertRaises(TypeError):


                    class A(metaclass=Meta, cell=bad_cell):
                        pass

    def test___classcell___wrong_cell(self):


        class Meta(type):

            def __new__(cls, name, bases, namespace):
                cls = super().__new__(cls, name, bases, namespace)
                B = type('B', (), namespace)
                return cls
        with self.assertRaises(TypeError):


            class A(metaclass=Meta):

                def f(self):
                    return __class__

    def test_obscure_super_errors(self):

        def f():
            super()
        self.assertRaises(RuntimeError, f)

        def f(x):
            del x
            super()
        self.assertRaises(RuntimeError, f, None)


        class X:

            def f(x):
                nonlocal __class__
                del __class__
                super()
        self.assertRaises(RuntimeError, X().f)

    def test_cell_as_self(self):


        class X:

            def meth(self):
                super()

        def f():
            k = X()

            def g():
                return k
            return g
        c = f().__closure__[0]
        self.assertRaises(TypeError, X.meth, c)

    def test_super_init_leaks(self):
        sp = super(float, 1.0)
        for i in range(1000):
            super.__init__(sp, int, i)


if __name__ == '__main__':
    unittest.main()
