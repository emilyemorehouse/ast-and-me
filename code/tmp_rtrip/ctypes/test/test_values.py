"""
A testcase which accesses *values* in a dll.
"""
import unittest
import sys
from ctypes import *
import _ctypes_test


class ValuesTestCase(unittest.TestCase):

    def test_an_integer(self):
        ctdll = CDLL(_ctypes_test.__file__)
        an_integer = c_int.in_dll(ctdll, 'an_integer')
        x = an_integer.value
        self.assertEqual(x, ctdll.get_an_integer())
        an_integer.value *= 2
        self.assertEqual(x * 2, ctdll.get_an_integer())
        an_integer.value = x
        self.assertEqual(x, ctdll.get_an_integer())

    def test_undefined(self):
        ctdll = CDLL(_ctypes_test.__file__)
        self.assertRaises(ValueError, c_int.in_dll, ctdll, 'Undefined_Symbol')


class PythonValuesTestCase(unittest.TestCase):
    """This test only works when python itself is a dll/shared library"""

    def test_optimizeflag(self):
        opt = c_int.in_dll(pythonapi, 'Py_OptimizeFlag').value
        self.assertEqual(opt, sys.flags.optimize)

    def test_frozentable(self):


        class struct_frozen(Structure):
            _fields_ = [('name', c_char_p), ('code', POINTER(c_ubyte)), (
                'size', c_int)]
        FrozenTable = POINTER(struct_frozen)
        ft = FrozenTable.in_dll(pythonapi, 'PyImport_FrozenModules')
        items = []
        bootstrap_seen = []
        bootstrap_expected = [b'_frozen_importlib',
            b'_frozen_importlib_external']
        for entry in ft:
            if entry.name is None:
                break
            if entry.name in bootstrap_expected:
                bootstrap_seen.append(entry.name)
                self.assertTrue(entry.size,
                    '{!r} was reported as having no size'.format(entry.name))
                continue
            items.append((entry.name.decode('ascii'), entry.size))
        expected = [('__hello__', 139), ('__phello__', -139), (
            '__phello__.spam', 139)]
        self.assertEqual(items, expected,
            'PyImport_FrozenModules example in Doc/library/ctypes.rst may be out of date'
            )
        self.assertEqual(sorted(bootstrap_seen), bootstrap_expected,
            'frozen bootstrap modules did not match PyImport_FrozenModules')
        from ctypes import _pointer_type_cache
        del _pointer_type_cache[struct_frozen]

    def test_undefined(self):
        self.assertRaises(ValueError, c_int.in_dll, pythonapi,
            'Undefined_Symbol')


if __name__ == '__main__':
    unittest.main()
