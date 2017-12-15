import unittest
import sys


class TestIsInstanceExceptions(unittest.TestCase):

    def test_class_has_no_bases(self):


        class I(object):

            def getclass(self):
                return None
            __class__ = property(getclass)


        class C(object):

            def getbases(self):
                return ()
            __bases__ = property(getbases)
        self.assertEqual(False, isinstance(I(), C()))

    def test_bases_raises_other_than_attribute_error(self):


        class E(object):

            def getbases(self):
                raise RuntimeError
            __bases__ = property(getbases)


        class I(object):

            def getclass(self):
                return E()
            __class__ = property(getclass)


        class C(object):

            def getbases(self):
                return ()
            __bases__ = property(getbases)
        self.assertRaises(RuntimeError, isinstance, I(), C())

    def test_dont_mask_non_attribute_error(self):


        class I:
            pass


        class C(object):

            def getbases(self):
                raise RuntimeError
            __bases__ = property(getbases)
        self.assertRaises(RuntimeError, isinstance, I(), C())

    def test_mask_attribute_error(self):


        class I:
            pass


        class C(object):

            def getbases(self):
                raise AttributeError
            __bases__ = property(getbases)
        self.assertRaises(TypeError, isinstance, I(), C())

    def test_isinstance_dont_mask_non_attribute_error(self):


        class C(object):

            def getclass(self):
                raise RuntimeError
            __class__ = property(getclass)
        c = C()
        self.assertRaises(RuntimeError, isinstance, c, bool)


        class D:
            pass
        self.assertRaises(RuntimeError, isinstance, c, D)


class TestIsSubclassExceptions(unittest.TestCase):

    def test_dont_mask_non_attribute_error(self):


        class C(object):

            def getbases(self):
                raise RuntimeError
            __bases__ = property(getbases)


        class S(C):
            pass
        self.assertRaises(RuntimeError, issubclass, C(), S())

    def test_mask_attribute_error(self):


        class C(object):

            def getbases(self):
                raise AttributeError
            __bases__ = property(getbases)


        class S(C):
            pass
        self.assertRaises(TypeError, issubclass, C(), S())

    def test_dont_mask_non_attribute_error_in_cls_arg(self):


        class B:
            pass


        class C(object):

            def getbases(self):
                raise RuntimeError
            __bases__ = property(getbases)
        self.assertRaises(RuntimeError, issubclass, B, C())

    def test_mask_attribute_error_in_cls_arg(self):


        class B:
            pass


        class C(object):

            def getbases(self):
                raise AttributeError
            __bases__ = property(getbases)
        self.assertRaises(TypeError, issubclass, B, C())


class AbstractClass(object):

    def __init__(self, bases):
        self.bases = bases

    def getbases(self):
        return self.bases
    __bases__ = property(getbases)

    def __call__(self):
        return AbstractInstance(self)


class AbstractInstance(object):

    def __init__(self, klass):
        self.klass = klass

    def getclass(self):
        return self.klass
    __class__ = property(getclass)


AbstractSuper = AbstractClass(bases=())
AbstractChild = AbstractClass(bases=(AbstractSuper,))


class Super:
    pass


class Child(Super):
    pass


class NewSuper(object):
    pass


class NewChild(NewSuper):
    pass


class TestIsInstanceIsSubclass(unittest.TestCase):

    def test_isinstance_normal(self):
        self.assertEqual(True, isinstance(Super(), Super))
        self.assertEqual(False, isinstance(Super(), Child))
        self.assertEqual(False, isinstance(Super(), AbstractSuper))
        self.assertEqual(False, isinstance(Super(), AbstractChild))
        self.assertEqual(True, isinstance(Child(), Super))
        self.assertEqual(False, isinstance(Child(), AbstractSuper))

    def test_isinstance_abstract(self):
        self.assertEqual(True, isinstance(AbstractSuper(), AbstractSuper))
        self.assertEqual(False, isinstance(AbstractSuper(), AbstractChild))
        self.assertEqual(False, isinstance(AbstractSuper(), Super))
        self.assertEqual(False, isinstance(AbstractSuper(), Child))
        self.assertEqual(True, isinstance(AbstractChild(), AbstractChild))
        self.assertEqual(True, isinstance(AbstractChild(), AbstractSuper))
        self.assertEqual(False, isinstance(AbstractChild(), Super))
        self.assertEqual(False, isinstance(AbstractChild(), Child))

    def test_subclass_normal(self):
        self.assertEqual(True, issubclass(Super, Super))
        self.assertEqual(False, issubclass(Super, AbstractSuper))
        self.assertEqual(False, issubclass(Super, Child))
        self.assertEqual(True, issubclass(Child, Child))
        self.assertEqual(True, issubclass(Child, Super))
        self.assertEqual(False, issubclass(Child, AbstractSuper))

    def test_subclass_abstract(self):
        self.assertEqual(True, issubclass(AbstractSuper, AbstractSuper))
        self.assertEqual(False, issubclass(AbstractSuper, AbstractChild))
        self.assertEqual(False, issubclass(AbstractSuper, Child))
        self.assertEqual(True, issubclass(AbstractChild, AbstractChild))
        self.assertEqual(True, issubclass(AbstractChild, AbstractSuper))
        self.assertEqual(False, issubclass(AbstractChild, Super))
        self.assertEqual(False, issubclass(AbstractChild, Child))

    def test_subclass_tuple(self):
        self.assertEqual(True, issubclass(Child, (Child,)))
        self.assertEqual(True, issubclass(Child, (Super,)))
        self.assertEqual(False, issubclass(Super, (Child,)))
        self.assertEqual(True, issubclass(Super, (Child, Super)))
        self.assertEqual(False, issubclass(Child, ()))
        self.assertEqual(True, issubclass(Super, (Child, (Super,))))
        self.assertEqual(True, issubclass(NewChild, (NewChild,)))
        self.assertEqual(True, issubclass(NewChild, (NewSuper,)))
        self.assertEqual(False, issubclass(NewSuper, (NewChild,)))
        self.assertEqual(True, issubclass(NewSuper, (NewChild, NewSuper)))
        self.assertEqual(False, issubclass(NewChild, ()))
        self.assertEqual(True, issubclass(NewSuper, (NewChild, (NewSuper,))))
        self.assertEqual(True, issubclass(int, (int, (float, int))))
        self.assertEqual(True, issubclass(str, (str, (Child, NewChild, str))))

    def test_subclass_recursion_limit(self):
        self.assertRaises(RecursionError, blowstack, issubclass, str, str)

    def test_isinstance_recursion_limit(self):
        self.assertRaises(RecursionError, blowstack, isinstance, '', str)


def blowstack(fxn, arg, compare_to):
    tuple_arg = compare_to,
    for cnt in range(sys.getrecursionlimit() + 5):
        tuple_arg = tuple_arg,
        fxn(arg, tuple_arg)


if __name__ == '__main__':
    unittest.main()
