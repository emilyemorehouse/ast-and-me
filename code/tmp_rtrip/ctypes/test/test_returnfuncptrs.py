import unittest
from ctypes import *
import _ctypes_test


class ReturnFuncPtrTestCase(unittest.TestCase):

    def test_with_prototype(self):
        dll = CDLL(_ctypes_test.__file__)
        get_strchr = dll.get_strchr
        get_strchr.restype = CFUNCTYPE(c_char_p, c_char_p, c_char)
        strchr = get_strchr()
        self.assertEqual(strchr(b'abcdef', b'b'), b'bcdef')
        self.assertEqual(strchr(b'abcdef', b'x'), None)
        self.assertEqual(strchr(b'abcdef', 98), b'bcdef')
        self.assertEqual(strchr(b'abcdef', 107), None)
        self.assertRaises(ArgumentError, strchr, b'abcdef', 3.0)
        self.assertRaises(TypeError, strchr, b'abcdef')

    def test_without_prototype(self):
        dll = CDLL(_ctypes_test.__file__)
        get_strchr = dll.get_strchr
        get_strchr.restype = c_void_p
        addr = get_strchr()
        strchr = CFUNCTYPE(c_char_p, c_char_p, c_char)(addr)
        self.assertTrue(strchr(b'abcdef', b'b'), 'bcdef')
        self.assertEqual(strchr(b'abcdef', b'x'), None)
        self.assertRaises(ArgumentError, strchr, b'abcdef', 3.0)
        self.assertRaises(TypeError, strchr, b'abcdef')

    def test_from_dll(self):
        dll = CDLL(_ctypes_test.__file__)
        strchr = CFUNCTYPE(c_char_p, c_char_p, c_char)(('my_strchr', dll))
        self.assertTrue(strchr(b'abcdef', b'b'), 'bcdef')
        self.assertEqual(strchr(b'abcdef', b'x'), None)
        self.assertRaises(ArgumentError, strchr, b'abcdef', 3.0)
        self.assertRaises(TypeError, strchr, b'abcdef')

    def test_from_dll_refcount(self):


        class BadSequence(tuple):

            def __getitem__(self, key):
                if key == 0:
                    return 'my_strchr'
                if key == 1:
                    return CDLL(_ctypes_test.__file__)
                raise IndexError
        strchr = CFUNCTYPE(c_char_p, c_char_p, c_char)(BadSequence((
            'my_strchr', CDLL(_ctypes_test.__file__))))
        self.assertTrue(strchr(b'abcdef', b'b'), 'bcdef')
        self.assertEqual(strchr(b'abcdef', b'x'), None)
        self.assertRaises(ArgumentError, strchr, b'abcdef', 3.0)
        self.assertRaises(TypeError, strchr, b'abcdef')


if __name__ == '__main__':
    unittest.main()
