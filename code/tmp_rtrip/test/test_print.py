import unittest
from io import StringIO
from test import support
NotDefined = object()
dispatch = {(False, False, False): lambda args, sep, end, file: print(*args
    ), (False, False, True): lambda args, sep, end, file: print(*args, file
    =file), (False, True, False): lambda args, sep, end, file: print(*args,
    end=end), (False, True, True): lambda args, sep, end, file: print(*args,
    end=end, file=file), (True, False, False): lambda args, sep, end, file:
    print(*args, sep=sep), (True, False, True): lambda args, sep, end, file:
    print(*args, sep=sep, file=file), (True, True, False): lambda args, sep,
    end, file: print(*args, sep=sep, end=end), (True, True, True): lambda
    args, sep, end, file: print(*args, sep=sep, end=end, file=file)}


class ClassWith__str__:

    def __init__(self, x):
        self.x = x

    def __str__(self):
        return self.x


class TestPrint(unittest.TestCase):
    """Test correct operation of the print function."""

    def check(self, expected, args, sep=NotDefined, end=NotDefined, file=
        NotDefined):
        fn = dispatch[sep is not NotDefined, end is not NotDefined, file is not
            NotDefined]
        with support.captured_stdout() as t:
            fn(args, sep, end, file)
        self.assertEqual(t.getvalue(), expected)

    def test_print(self):

        def x(expected, args, sep=NotDefined, end=NotDefined):
            self.check(expected, args, sep=sep, end=end)
            o = StringIO()
            self.check('', args, sep=sep, end=end, file=o)
            self.assertEqual(o.getvalue(), expected)
        x('\n', ())
        x('a\n', ('a',))
        x('None\n', (None,))
        x('1 2\n', (1, 2))
        x('1   2\n', (1, ' ', 2))
        x('1*2\n', (1, 2), sep='*')
        x('1 s', (1, 's'), end='')
        x('a\nb\n', ('a', 'b'), sep='\n')
        x('1.01', (1.0, 1), sep='', end='')
        x('1*a*1.3+', (1, 'a', 1.3), sep='*', end='+')
        x('a\n\nb\n', ('a\n', 'b'), sep='\n')
        x('\x00+ +\x00\n', ('\x00', ' ', '\x00'), sep='+')
        x('a\n b\n', ('a\n', 'b'))
        x('a\n b\n', ('a\n', 'b'), sep=None)
        x('a\n b\n', ('a\n', 'b'), end=None)
        x('a\n b\n', ('a\n', 'b'), sep=None, end=None)
        x('*\n', (ClassWith__str__('*'),))
        x('abc 1\n', (ClassWith__str__('abc'), 1))
        self.assertRaises(TypeError, print, '', sep=3)
        self.assertRaises(TypeError, print, '', end=3)
        self.assertRaises(AttributeError, print, '', file='')

    def test_print_flush(self):


        class filelike:

            def __init__(self):
                self.written = ''
                self.flushed = 0

            def write(self, str):
                self.written += str

            def flush(self):
                self.flushed += 1
        f = filelike()
        print(1, file=f, end='', flush=True)
        print(2, file=f, end='', flush=True)
        print(3, file=f, flush=False)
        self.assertEqual(f.written, '123\n')
        self.assertEqual(f.flushed, 2)


        class noflush:

            def write(self, str):
                pass

            def flush(self):
                raise RuntimeError
        self.assertRaises(RuntimeError, print, 1, file=noflush(), flush=True)


if __name__ == '__main__':
    unittest.main()
