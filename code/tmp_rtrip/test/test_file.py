import sys
import os
import unittest
from array import array
from weakref import proxy
import io
import _pyio as pyio
from test.support import TESTFN
from collections import UserList


class AutoFileTests:

    def setUp(self):
        self.f = self.open(TESTFN, 'wb')

    def tearDown(self):
        if self.f:
            self.f.close()
        os.remove(TESTFN)

    def testWeakRefs(self):
        p = proxy(self.f)
        p.write(b'teststring')
        self.assertEqual(self.f.tell(), p.tell())
        self.f.close()
        self.f = None
        self.assertRaises(ReferenceError, getattr, p, 'tell')

    def testAttributes(self):
        f = self.f
        f.name
        f.mode
        f.closed

    def testReadinto(self):
        self.f.write(b'12')
        self.f.close()
        a = array('b', b'x' * 10)
        self.f = self.open(TESTFN, 'rb')
        n = self.f.readinto(a)
        self.assertEqual(b'12', a.tobytes()[:n])

    def testReadinto_text(self):
        a = array('b', b'x' * 10)
        self.f.close()
        self.f = self.open(TESTFN, 'r')
        if hasattr(self.f, 'readinto'):
            self.assertRaises(TypeError, self.f.readinto, a)

    def testWritelinesUserList(self):
        l = UserList([b'1', b'2'])
        self.f.writelines(l)
        self.f.close()
        self.f = self.open(TESTFN, 'rb')
        buf = self.f.read()
        self.assertEqual(buf, b'12')

    def testWritelinesIntegers(self):
        self.assertRaises(TypeError, self.f.writelines, [1, 2, 3])

    def testWritelinesIntegersUserList(self):
        l = UserList([1, 2, 3])
        self.assertRaises(TypeError, self.f.writelines, l)

    def testWritelinesNonString(self):


        class NonString:
            pass
        self.assertRaises(TypeError, self.f.writelines, [NonString(),
            NonString()])

    def testErrors(self):
        f = self.f
        self.assertEqual(f.name, TESTFN)
        self.assertFalse(f.isatty())
        self.assertFalse(f.closed)
        if hasattr(f, 'readinto'):
            self.assertRaises((OSError, TypeError), f.readinto, '')
        f.close()
        self.assertTrue(f.closed)

    def testMethods(self):
        methods = [('fileno', ()), ('flush', ()), ('isatty', ()), (
            '__next__', ()), ('read', ()), ('write', (b'',)), ('readline',
            ()), ('readlines', ()), ('seek', (0,)), ('tell', ()), ('write',
            (b'',)), ('writelines', ([],)), ('__iter__', ())]
        methods.append(('truncate', ()))
        self.f.__exit__(None, None, None)
        self.assertTrue(self.f.closed)
        for methodname, args in methods:
            method = getattr(self.f, methodname)
            self.assertRaises(ValueError, method, *args)
        self.assertEqual(self.f.__exit__(None, None, None), None)
        try:
            1 / 0
        except:
            self.assertEqual(self.f.__exit__(*sys.exc_info()), None)

    def testReadWhenWriting(self):
        self.assertRaises(OSError, self.f.read)


class CAutoFileTests(AutoFileTests, unittest.TestCase):
    open = io.open


class PyAutoFileTests(AutoFileTests, unittest.TestCase):
    open = staticmethod(pyio.open)


class OtherFileTests:

    def testModeStrings(self):
        for mode in ('', 'aU', 'wU+', 'U+', '+U', 'rU+'):
            try:
                f = self.open(TESTFN, mode)
            except ValueError:
                pass
            else:
                f.close()
                self.fail('%r is an invalid file mode' % mode)

    def testBadModeArgument(self):
        bad_mode = 'qwerty'
        try:
            f = self.open(TESTFN, bad_mode)
        except ValueError as msg:
            if msg.args[0] != 0:
                s = str(msg)
                if TESTFN in s or bad_mode not in s:
                    self.fail('bad error message for invalid mode: %s' % s)
        else:
            f.close()
            self.fail('no error for invalid mode: %s' % bad_mode)

    def testSetBufferSize(self):
        for s in (-1, 0, 1, 512):
            try:
                f = self.open(TESTFN, 'wb', s)
                f.write(str(s).encode('ascii'))
                f.close()
                f.close()
                f = self.open(TESTFN, 'rb', s)
                d = int(f.read().decode('ascii'))
                f.close()
                f.close()
            except OSError as msg:
                self.fail('error setting buffer size %d: %s' % (s, str(msg)))
            self.assertEqual(d, s)

    def testTruncateOnWindows(self):
        os.unlink(TESTFN)
        f = self.open(TESTFN, 'wb')
        try:
            f.write(b'12345678901')
            f.close()
            f = self.open(TESTFN, 'rb+')
            data = f.read(5)
            if data != b'12345':
                self.fail('Read on file opened for update failed %r' % data)
            if f.tell() != 5:
                self.fail('File pos after read wrong %d' % f.tell())
            f.truncate()
            if f.tell() != 5:
                self.fail('File pos after ftruncate wrong %d' % f.tell())
            f.close()
            size = os.path.getsize(TESTFN)
            if size != 5:
                self.fail('File size after ftruncate wrong %d' % size)
        finally:
            f.close()
            os.unlink(TESTFN)

    def testIteration(self):
        dataoffset = 16384
        filler = b'ham\n'
        assert not dataoffset % len(filler
            ), 'dataoffset must be multiple of len(filler)'
        nchunks = dataoffset // len(filler)
        testlines = [b'spam, spam and eggs\n',
            b'eggs, spam, ham and spam\n',
            b'saussages, spam, spam and eggs\n',
            b'spam, ham, spam and eggs\n',
            b'spam, spam, spam, spam, spam, ham, spam\n',
            b'wonderful spaaaaaam.\n']
        methods = [('readline', ()), ('read', ()), ('readlines', ()), (
            'readinto', (array('b', b' ' * 100),))]
        try:
            bag = self.open(TESTFN, 'wb')
            bag.write(filler * nchunks)
            bag.writelines(testlines)
            bag.close()
            for methodname, args in methods:
                f = self.open(TESTFN, 'rb')
                if next(f) != filler:
                    self.fail, 'Broken testfile'
                meth = getattr(f, methodname)
                meth(*args)
                f.close()
            f = self.open(TESTFN, 'rb')
            for i in range(nchunks):
                next(f)
            testline = testlines.pop(0)
            try:
                line = f.readline()
            except ValueError:
                self.fail(
                    'readline() after next() with supposedly empty iteration-buffer failed anyway'
                    )
            if line != testline:
                self.fail(
                    'readline() after next() with empty buffer failed. Got %r, expected %r'
                     % (line, testline))
            testline = testlines.pop(0)
            buf = array('b', b'\x00' * len(testline))
            try:
                f.readinto(buf)
            except ValueError:
                self.fail(
                    'readinto() after next() with supposedly empty iteration-buffer failed anyway'
                    )
            line = buf.tobytes()
            if line != testline:
                self.fail(
                    'readinto() after next() with empty buffer failed. Got %r, expected %r'
                     % (line, testline))
            testline = testlines.pop(0)
            try:
                line = f.read(len(testline))
            except ValueError:
                self.fail(
                    'read() after next() with supposedly empty iteration-buffer failed anyway'
                    )
            if line != testline:
                self.fail(
                    'read() after next() with empty buffer failed. Got %r, expected %r'
                     % (line, testline))
            try:
                lines = f.readlines()
            except ValueError:
                self.fail(
                    'readlines() after next() with supposedly empty iteration-buffer failed anyway'
                    )
            if lines != testlines:
                self.fail(
                    'readlines() after next() with empty buffer failed. Got %r, expected %r'
                     % (line, testline))
            f.close()
            f = self.open(TESTFN, 'rb')
            try:
                for line in f:
                    pass
                try:
                    f.readline()
                    f.readinto(buf)
                    f.read()
                    f.readlines()
                except ValueError:
                    self.fail('read* failed after next() consumed file')
            finally:
                f.close()
        finally:
            os.unlink(TESTFN)


class COtherFileTests(OtherFileTests, unittest.TestCase):
    open = io.open


class PyOtherFileTests(OtherFileTests, unittest.TestCase):
    open = staticmethod(pyio.open)


def tearDownModule():
    if os.path.exists(TESTFN):
        os.unlink(TESTFN)


if __name__ == '__main__':
    unittest.main()
