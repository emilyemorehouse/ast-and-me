import sys
import unittest
from test import support
pwd = support.import_module('pwd')


def _getpwall():
    if hasattr(pwd, 'getpwall'):
        return pwd.getpwall()
    elif hasattr(pwd, 'getpwuid'):
        return [pwd.getpwuid(0)]
    else:
        return []


class PwdTest(unittest.TestCase):

    def test_values(self):
        entries = _getpwall()
        for e in entries:
            self.assertEqual(len(e), 7)
            self.assertEqual(e[0], e.pw_name)
            self.assertIsInstance(e.pw_name, str)
            self.assertEqual(e[1], e.pw_passwd)
            self.assertIsInstance(e.pw_passwd, str)
            self.assertEqual(e[2], e.pw_uid)
            self.assertIsInstance(e.pw_uid, int)
            self.assertEqual(e[3], e.pw_gid)
            self.assertIsInstance(e.pw_gid, int)
            self.assertEqual(e[4], e.pw_gecos)
            self.assertIsInstance(e.pw_gecos, str)
            self.assertEqual(e[5], e.pw_dir)
            self.assertIsInstance(e.pw_dir, str)
            self.assertEqual(e[6], e.pw_shell)
            self.assertIsInstance(e.pw_shell, str)

    def test_values_extended(self):
        entries = _getpwall()
        entriesbyname = {}
        entriesbyuid = {}
        if len(entries) > 1000:
            self.skipTest('passwd file is huge; extended test skipped')
        for e in entries:
            entriesbyname.setdefault(e.pw_name, []).append(e)
            entriesbyuid.setdefault(e.pw_uid, []).append(e)
        for e in entries:
            if not e[0] or e[0] == '+':
                continue
            self.assertIn(pwd.getpwnam(e.pw_name), entriesbyname[e.pw_name])
            self.assertIn(pwd.getpwuid(e.pw_uid), entriesbyuid[e.pw_uid])

    def test_errors(self):
        self.assertRaises(TypeError, pwd.getpwuid)
        self.assertRaises(TypeError, pwd.getpwuid, 3.14)
        self.assertRaises(TypeError, pwd.getpwnam)
        self.assertRaises(TypeError, pwd.getpwnam, 42)
        if hasattr(pwd, 'getpwall'):
            self.assertRaises(TypeError, pwd.getpwall, 42)
        bynames = {}
        byuids = {}
        for n, p, u, g, gecos, d, s in _getpwall():
            bynames[n] = u
            byuids[u] = n
        allnames = list(bynames.keys())
        namei = 0
        fakename = allnames[namei]
        while fakename in bynames:
            chars = list(fakename)
            for i in range(len(chars)):
                if chars[i] == 'z':
                    chars[i] = 'A'
                    break
                elif chars[i] == 'Z':
                    continue
                else:
                    chars[i] = chr(ord(chars[i]) + 1)
                    break
            else:
                namei = namei + 1
                try:
                    fakename = allnames[namei]
                except IndexError:
                    break
            fakename = ''.join(chars)
        self.assertRaises(KeyError, pwd.getpwnam, fakename)
        fakeuid = sys.maxsize
        self.assertNotIn(fakeuid, byuids)
        if not support.is_android:
            self.assertRaises(KeyError, pwd.getpwuid, fakeuid)
        if not support.is_android:
            self.assertRaises(KeyError, pwd.getpwuid, -1)
        self.assertRaises(KeyError, pwd.getpwuid, 2 ** 128)
        self.assertRaises(KeyError, pwd.getpwuid, -2 ** 128)


if __name__ == '__main__':
    unittest.main()
