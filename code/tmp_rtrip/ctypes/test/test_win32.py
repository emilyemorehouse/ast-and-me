from ctypes import *
import unittest, sys
from test import support
import _ctypes_test


@unittest.skipUnless(sys.platform == 'win32', 'Windows-specific test')
@unittest.skipUnless(sizeof(c_void_p) == sizeof(c_int),
    'sizeof c_void_p and c_int differ')
class WindowsTestCase(unittest.TestCase):

    def test_callconv_1(self):
        IsWindow = windll.user32.IsWindow
        self.assertRaises(ValueError, IsWindow)
        self.assertEqual(0, IsWindow(0))
        self.assertRaises(ValueError, IsWindow, 0, 0, 0)

    def test_callconv_2(self):
        IsWindow = cdll.user32.IsWindow
        self.assertRaises(ValueError, IsWindow, None)


@unittest.skipUnless(sys.platform == 'win32', 'Windows-specific test')
class FunctionCallTestCase(unittest.TestCase):

    @unittest.skipUnless('MSC' in sys.version, 'SEH only supported by MSC')
    @unittest.skipIf(sys.executable.lower().endswith('_d.exe'),
        'SEH not enabled in debug builds')
    def test_SEH(self):
        with support.disable_faulthandler():
            self.assertRaises(OSError, windll.kernel32.GetModuleHandleA, 32)

    def test_noargs(self):
        windll.user32.GetDesktopWindow()


@unittest.skipUnless(sys.platform == 'win32', 'Windows-specific test')
class TestWintypes(unittest.TestCase):

    def test_HWND(self):
        from ctypes import wintypes
        self.assertEqual(sizeof(wintypes.HWND), sizeof(c_void_p))

    def test_PARAM(self):
        from ctypes import wintypes
        self.assertEqual(sizeof(wintypes.WPARAM), sizeof(c_void_p))
        self.assertEqual(sizeof(wintypes.LPARAM), sizeof(c_void_p))

    def test_COMError(self):
        from _ctypes import COMError
        if support.HAVE_DOCSTRINGS:
            self.assertEqual(COMError.__doc__,
                'Raised when a COM method call failed.')
        ex = COMError(-1, 'text', ('details',))
        self.assertEqual(ex.hresult, -1)
        self.assertEqual(ex.text, 'text')
        self.assertEqual(ex.details, ('details',))


@unittest.skipUnless(sys.platform == 'win32', 'Windows-specific test')
class TestWinError(unittest.TestCase):

    def test_winerror(self):
        import errno
        ERROR_INVALID_PARAMETER = 87
        msg = FormatError(ERROR_INVALID_PARAMETER).strip()
        args = errno.EINVAL, msg, None, ERROR_INVALID_PARAMETER
        e = WinError(ERROR_INVALID_PARAMETER)
        self.assertEqual(e.args, args)
        self.assertEqual(e.errno, errno.EINVAL)
        self.assertEqual(e.winerror, ERROR_INVALID_PARAMETER)
        windll.kernel32.SetLastError(ERROR_INVALID_PARAMETER)
        try:
            raise WinError()
        except OSError as exc:
            e = exc
        self.assertEqual(e.args, args)
        self.assertEqual(e.errno, errno.EINVAL)
        self.assertEqual(e.winerror, ERROR_INVALID_PARAMETER)


class Structures(unittest.TestCase):

    def test_struct_by_value(self):


        class POINT(Structure):
            _fields_ = [('x', c_long), ('y', c_long)]


        class RECT(Structure):
            _fields_ = [('left', c_long), ('top', c_long), ('right', c_long
                ), ('bottom', c_long)]
        dll = CDLL(_ctypes_test.__file__)
        pt = POINT(15, 25)
        left = c_long.in_dll(dll, 'left')
        top = c_long.in_dll(dll, 'top')
        right = c_long.in_dll(dll, 'right')
        bottom = c_long.in_dll(dll, 'bottom')
        rect = RECT(left, top, right, bottom)
        PointInRect = dll.PointInRect
        PointInRect.argtypes = [POINTER(RECT), POINT]
        self.assertEqual(1, PointInRect(byref(rect), pt))
        ReturnRect = dll.ReturnRect
        ReturnRect.argtypes = [c_int, RECT, POINTER(RECT), POINT, RECT,
            POINTER(RECT), POINT, RECT]
        ReturnRect.restype = RECT
        for i in range(4):
            ret = ReturnRect(i, rect, pointer(rect), pt, rect, byref(rect),
                pt, rect)
            self.assertEqual(ret.left, left.value)
            self.assertEqual(ret.right, right.value)
            self.assertEqual(ret.top, top.value)
            self.assertEqual(ret.bottom, bottom.value)
        from ctypes import _pointer_type_cache
        del _pointer_type_cache[RECT]


if __name__ == '__main__':
    unittest.main()
