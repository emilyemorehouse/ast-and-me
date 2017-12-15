import copyreg
import unittest
from test.pickletester import ExtensionSaver


class C:
    pass


class WithoutSlots(object):
    pass


class WithWeakref(object):
    __slots__ = '__weakref__',


class WithPrivate(object):
    __slots__ = '__spam',


class WithSingleString(object):
    __slots__ = 'spam'


class WithInherited(WithSingleString):
    __slots__ = 'eggs',


class CopyRegTestCase(unittest.TestCase):

    def test_class(self):
        self.assertRaises(TypeError, copyreg.pickle, C, None, None)

    def test_noncallable_reduce(self):
        self.assertRaises(TypeError, copyreg.pickle, type(1), 'not a callable')

    def test_noncallable_constructor(self):
        self.assertRaises(TypeError, copyreg.pickle, type(1), int,
            'not a callable')

    def test_bool(self):
        import copy
        self.assertEqual(True, copy.copy(True))

    def test_extension_registry(self):
        mod, func, code = 'junk1 ', ' junk2', 43981
        e = ExtensionSaver(code)
        try:
            self.assertRaises(ValueError, copyreg.remove_extension, mod,
                func, code)
            copyreg.add_extension(mod, func, code)
            self.assertTrue(copyreg._extension_registry[mod, func] == code)
            self.assertTrue(copyreg._inverted_registry[code] == (mod, func))
            self.assertNotIn(code, copyreg._extension_cache)
            copyreg.add_extension(mod, func, code)
            self.assertRaises(ValueError, copyreg.add_extension, mod, func,
                code + 1)
            self.assertRaises(ValueError, copyreg.remove_extension, mod,
                func, code + 1)
            self.assertRaises(ValueError, copyreg.add_extension, mod[1:],
                func, code)
            self.assertRaises(ValueError, copyreg.remove_extension, mod[1:],
                func, code)
            self.assertRaises(ValueError, copyreg.add_extension, mod, func[
                1:], code)
            self.assertRaises(ValueError, copyreg.remove_extension, mod,
                func[1:], code)
            if code + 1 not in copyreg._inverted_registry:
                self.assertRaises(ValueError, copyreg.remove_extension, mod
                    [1:], func[1:], code + 1)
        finally:
            e.restore()
        self.assertNotIn((mod, func), copyreg._extension_registry)
        for code in (1, 2147483647):
            e = ExtensionSaver(code)
            try:
                copyreg.add_extension(mod, func, code)
                copyreg.remove_extension(mod, func, code)
            finally:
                e.restore()
        for code in (-1, 0, 2147483648):
            self.assertRaises(ValueError, copyreg.add_extension, mod, func,
                code)

    def test_slotnames(self):
        self.assertEqual(copyreg._slotnames(WithoutSlots), [])
        self.assertEqual(copyreg._slotnames(WithWeakref), [])
        expected = ['_WithPrivate__spam']
        self.assertEqual(copyreg._slotnames(WithPrivate), expected)
        self.assertEqual(copyreg._slotnames(WithSingleString), ['spam'])
        expected = ['eggs', 'spam']
        expected.sort()
        result = copyreg._slotnames(WithInherited)
        result.sort()
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
