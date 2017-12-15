import os, sys, errno
import unittest
from test import support
threading = support.import_module('threading')
from platform import machine
support.import_module('winreg', required_on=['win'])
from winreg import *
try:
    REMOTE_NAME = sys.argv[sys.argv.index('--remote') + 1]
except (IndexError, ValueError):
    REMOTE_NAME = None
WIN_VER = sys.getwindowsversion()[:2]
WIN64_MACHINE = True if machine() == 'AMD64' else False
HAS_REFLECTION = True if WIN_VER < (6, 1) else False
test_key_base = 'Python Test Key [%d] - Delete Me' % (os.getpid(),)
test_key_name = 'SOFTWARE\\' + test_key_base
test_reflect_key_name = 'SOFTWARE\\Classes\\' + test_key_base
test_data = [('Int Value', 45, REG_DWORD), ('Qword Value', 
    1234605616436508552, REG_QWORD), ('String Val', 'A string value',
    REG_SZ), ('StringExpand', 'The path is %path%', REG_EXPAND_SZ), (
    'Multi-string', ['Lots', 'of', 'string', 'values'], REG_MULTI_SZ), (
    'Raw Data', b'binary\x00data', REG_BINARY), ('Big String', 'x' * (2 ** 
    14 - 1), REG_SZ), ('Big Binary', b'x' * 2 ** 14, REG_BINARY), (
    'Japanese 日本', '日本語', REG_SZ)]


class BaseWinregTests(unittest.TestCase):

    def setUp(self):
        self.delete_tree(HKEY_CURRENT_USER, test_key_name)

    def delete_tree(self, root, subkey):
        try:
            hkey = OpenKey(root, subkey, 0, KEY_ALL_ACCESS)
        except OSError:
            return
        while True:
            try:
                subsubkey = EnumKey(hkey, 0)
            except OSError:
                break
            self.delete_tree(hkey, subsubkey)
        CloseKey(hkey)
        DeleteKey(root, subkey)

    def _write_test_data(self, root_key, subkeystr='sub_key', CreateKey=
        CreateKey):
        SetValue(root_key, test_key_name, REG_SZ, 'Default value')
        key = CreateKey(root_key, test_key_name)
        self.assertTrue(key.handle != 0)
        sub_key = CreateKey(key, subkeystr)
        for value_name, value_data, value_type in test_data:
            SetValueEx(sub_key, value_name, 0, value_type, value_data)
        nkeys, nvalues, since_mod = QueryInfoKey(key)
        self.assertEqual(nkeys, 1, 'Not the correct number of sub keys')
        self.assertEqual(nvalues, 1, 'Not the correct number of values')
        nkeys, nvalues, since_mod = QueryInfoKey(sub_key)
        self.assertEqual(nkeys, 0, 'Not the correct number of sub keys')
        self.assertEqual(nvalues, len(test_data),
            'Not the correct number of values')
        int_sub_key = int(sub_key)
        CloseKey(sub_key)
        try:
            QueryInfoKey(int_sub_key)
            self.fail(
                'It appears the CloseKey() function does not close the actual key!'
                )
        except OSError:
            pass
        int_key = int(key)
        key.Close()
        try:
            QueryInfoKey(int_key)
            self.fail(
                'It appears the key.Close() function does not close the actual key!'
                )
        except OSError:
            pass

    def _read_test_data(self, root_key, subkeystr='sub_key', OpenKey=OpenKey):
        val = QueryValue(root_key, test_key_name)
        self.assertEqual(val, 'Default value',
            "Registry didn't give back the correct value")
        key = OpenKey(root_key, test_key_name)
        with OpenKey(key, subkeystr) as sub_key:
            index = 0
            while 1:
                try:
                    data = EnumValue(sub_key, index)
                except OSError:
                    break
                self.assertEqual(data in test_data, True,
                    "Didn't read back the correct test data")
                index = index + 1
            self.assertEqual(index, len(test_data),
                "Didn't read the correct number of items")
            for value_name, value_data, value_type in test_data:
                read_val, read_typ = QueryValueEx(sub_key, value_name)
                self.assertEqual(read_val, value_data,
                    'Could not directly read the value')
                self.assertEqual(read_typ, value_type,
                    'Could not directly read the value')
        sub_key.Close()
        read_val = EnumKey(key, 0)
        self.assertEqual(read_val, subkeystr, 'Read subkey value wrong')
        try:
            EnumKey(key, 1)
            self.fail('Was able to get a second key when I only have one!')
        except OSError:
            pass
        key.Close()

    def _delete_test_data(self, root_key, subkeystr='sub_key'):
        key = OpenKey(root_key, test_key_name, 0, KEY_ALL_ACCESS)
        sub_key = OpenKey(key, subkeystr, 0, KEY_ALL_ACCESS)
        for value_name, value_data, value_type in test_data:
            DeleteValue(sub_key, value_name)
        nkeys, nvalues, since_mod = QueryInfoKey(sub_key)
        self.assertEqual(nkeys, 0, 'subkey not empty before delete')
        self.assertEqual(nvalues, 0, 'subkey not empty before delete')
        sub_key.Close()
        DeleteKey(key, subkeystr)
        try:
            DeleteKey(key, subkeystr)
            self.fail('Deleting the key twice succeeded')
        except OSError:
            pass
        key.Close()
        DeleteKey(root_key, test_key_name)
        try:
            key = OpenKey(root_key, test_key_name)
            self.fail('Could open the non-existent key')
        except OSError:
            pass

    def _test_all(self, root_key, subkeystr='sub_key'):
        self._write_test_data(root_key, subkeystr)
        self._read_test_data(root_key, subkeystr)
        self._delete_test_data(root_key, subkeystr)

    def _test_named_args(self, key, sub_key):
        with CreateKeyEx(key=key, sub_key=sub_key, reserved=0, access=
            KEY_ALL_ACCESS) as ckey:
            self.assertTrue(ckey.handle != 0)
        with OpenKeyEx(key=key, sub_key=sub_key, reserved=0, access=
            KEY_ALL_ACCESS) as okey:
            self.assertTrue(okey.handle != 0)


class LocalWinregTests(BaseWinregTests):

    def test_registry_works(self):
        self._test_all(HKEY_CURRENT_USER)
        self._test_all(HKEY_CURRENT_USER, '日本-subkey')

    def test_registry_works_extended_functions(self):
        cke = lambda key, sub_key: CreateKeyEx(key, sub_key, 0, KEY_ALL_ACCESS)
        self._write_test_data(HKEY_CURRENT_USER, CreateKey=cke)
        oke = lambda key, sub_key: OpenKeyEx(key, sub_key, 0, KEY_READ)
        self._read_test_data(HKEY_CURRENT_USER, OpenKey=oke)
        self._delete_test_data(HKEY_CURRENT_USER)

    def test_named_arguments(self):
        self._test_named_args(HKEY_CURRENT_USER, test_key_name)
        DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_connect_registry_to_local_machine_works(self):
        h = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        self.assertNotEqual(h.handle, 0)
        h.Close()
        self.assertEqual(h.handle, 0)

    def test_inexistant_remote_registry(self):
        connect = lambda : ConnectRegistry('abcdefghijkl', HKEY_CURRENT_USER)
        self.assertRaises(OSError, connect)

    def testExpandEnvironmentStrings(self):
        r = ExpandEnvironmentStrings('%windir%\\test')
        self.assertEqual(type(r), str)
        self.assertEqual(r, os.environ['windir'] + '\\test')

    def test_context_manager(self):
        try:
            with ConnectRegistry(None, HKEY_LOCAL_MACHINE) as h:
                self.assertNotEqual(h.handle, 0)
                raise OSError
        except OSError:
            self.assertEqual(h.handle, 0)

    def test_changing_value(self):
        done = False


        class VeryActiveThread(threading.Thread):

            def run(self):
                with CreateKey(HKEY_CURRENT_USER, test_key_name) as key:
                    use_short = True
                    long_string = 'x' * 2000
                    while not done:
                        s = 'x' if use_short else long_string
                        use_short = not use_short
                        SetValue(key, 'changing_value', REG_SZ, s)
        thread = VeryActiveThread()
        thread.start()
        try:
            with CreateKey(HKEY_CURRENT_USER, test_key_name +
                '\\changing_value') as key:
                for _ in range(1000):
                    num_subkeys, num_values, t = QueryInfoKey(key)
                    for i in range(num_values):
                        name = EnumValue(key, i)
                        QueryValue(key, name[0])
        finally:
            done = True
            thread.join()
            DeleteKey(HKEY_CURRENT_USER, test_key_name + '\\changing_value')
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_long_key(self):
        name = 'x' * 256
        try:
            with CreateKey(HKEY_CURRENT_USER, test_key_name) as key:
                SetValue(key, name, REG_SZ, 'x')
                num_subkeys, num_values, t = QueryInfoKey(key)
                EnumKey(key, 0)
        finally:
            DeleteKey(HKEY_CURRENT_USER, '\\'.join((test_key_name, name)))
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_dynamic_key(self):
        try:
            EnumValue(HKEY_PERFORMANCE_DATA, 0)
        except OSError as e:
            if e.errno in (errno.EPERM, errno.EACCES):
                self.skipTest(
                    'access denied to registry key (are you running in a non-interactive session?)'
                    )
            raise
        QueryValueEx(HKEY_PERFORMANCE_DATA, '')

    @unittest.skipUnless(WIN_VER < (5, 2), 'Requires Windows XP')
    def test_reflection_unsupported(self):
        try:
            with CreateKey(HKEY_CURRENT_USER, test_key_name) as ck:
                self.assertNotEqual(ck.handle, 0)
            key = OpenKey(HKEY_CURRENT_USER, test_key_name)
            self.assertNotEqual(key.handle, 0)
            with self.assertRaises(NotImplementedError):
                DisableReflectionKey(key)
            with self.assertRaises(NotImplementedError):
                EnableReflectionKey(key)
            with self.assertRaises(NotImplementedError):
                QueryReflectionKey(key)
            with self.assertRaises(NotImplementedError):
                DeleteKeyEx(HKEY_CURRENT_USER, test_key_name)
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_setvalueex_value_range(self):
        try:
            with CreateKey(HKEY_CURRENT_USER, test_key_name) as ck:
                self.assertNotEqual(ck.handle, 0)
                SetValueEx(ck, 'test_name', None, REG_DWORD, 2147483648)
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_queryvalueex_return_value(self):
        try:
            with CreateKey(HKEY_CURRENT_USER, test_key_name) as ck:
                self.assertNotEqual(ck.handle, 0)
                test_val = 2147483648
                SetValueEx(ck, 'test_name', None, REG_DWORD, test_val)
                ret_val, ret_type = QueryValueEx(ck, 'test_name')
                self.assertEqual(ret_type, REG_DWORD)
                self.assertEqual(ret_val, test_val)
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_setvalueex_crash_with_none_arg(self):
        try:
            with CreateKey(HKEY_CURRENT_USER, test_key_name) as ck:
                self.assertNotEqual(ck.handle, 0)
                test_val = None
                SetValueEx(ck, 'test_name', 0, REG_BINARY, test_val)
                ret_val, ret_type = QueryValueEx(ck, 'test_name')
                self.assertEqual(ret_type, REG_BINARY)
                self.assertEqual(ret_val, test_val)
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)

    def test_read_string_containing_null(self):
        try:
            with CreateKey(HKEY_CURRENT_USER, test_key_name) as ck:
                self.assertNotEqual(ck.handle, 0)
                test_val = 'A string\x00 with a null'
                SetValueEx(ck, 'test_name', 0, REG_SZ, test_val)
                ret_val, ret_type = QueryValueEx(ck, 'test_name')
                self.assertEqual(ret_type, REG_SZ)
                self.assertEqual(ret_val, 'A string')
        finally:
            DeleteKey(HKEY_CURRENT_USER, test_key_name)


@unittest.skipUnless(REMOTE_NAME, 'Skipping remote registry tests')
class RemoteWinregTests(BaseWinregTests):

    def test_remote_registry_works(self):
        remote_key = ConnectRegistry(REMOTE_NAME, HKEY_CURRENT_USER)
        self._test_all(remote_key)


@unittest.skipUnless(WIN64_MACHINE, 'x64 specific registry tests')
class Win64WinregTests(BaseWinregTests):

    def test_named_arguments(self):
        self._test_named_args(HKEY_CURRENT_USER, test_key_name)
        DeleteKeyEx(key=HKEY_CURRENT_USER, sub_key=test_key_name, access=
            KEY_ALL_ACCESS, reserved=0)

    def test_reflection_functions(self):
        with OpenKey(HKEY_LOCAL_MACHINE, 'Software') as key:
            self.assertTrue(QueryReflectionKey(key))
            self.assertIsNone(EnableReflectionKey(key))
            self.assertIsNone(DisableReflectionKey(key))
            self.assertTrue(QueryReflectionKey(key))

    @unittest.skipUnless(HAS_REFLECTION, "OS doesn't support reflection")
    def test_reflection(self):
        try:
            with CreateKeyEx(HKEY_CURRENT_USER, test_reflect_key_name, 0, 
                KEY_ALL_ACCESS | KEY_WOW64_32KEY) as created_key:
                self.assertNotEqual(created_key.handle, 0)
                with OpenKey(HKEY_CURRENT_USER, test_reflect_key_name, 0, 
                    KEY_ALL_ACCESS | KEY_WOW64_32KEY) as key:
                    self.assertNotEqual(key.handle, 0)
                SetValueEx(created_key, '', 0, REG_SZ, '32KEY')
                open_fail = lambda : OpenKey(HKEY_CURRENT_USER,
                    test_reflect_key_name, 0, KEY_READ | KEY_WOW64_64KEY)
                self.assertRaises(OSError, open_fail)
            with OpenKey(HKEY_CURRENT_USER, test_reflect_key_name, 0, 
                KEY_ALL_ACCESS | KEY_WOW64_64KEY) as key:
                self.assertNotEqual(key.handle, 0)
                self.assertEqual('32KEY', QueryValue(key, ''))
                SetValueEx(key, '', 0, REG_SZ, '64KEY')
            with OpenKey(HKEY_CURRENT_USER, test_reflect_key_name, 0, 
                KEY_READ | KEY_WOW64_32KEY) as key:
                self.assertEqual('64KEY', QueryValue(key, ''))
        finally:
            DeleteKeyEx(HKEY_CURRENT_USER, test_reflect_key_name,
                KEY_WOW64_32KEY, 0)

    @unittest.skipUnless(HAS_REFLECTION, "OS doesn't support reflection")
    def test_disable_reflection(self):
        try:
            with CreateKeyEx(HKEY_CURRENT_USER, test_reflect_key_name, 0, 
                KEY_ALL_ACCESS | KEY_WOW64_32KEY) as created_key:
                disabled = QueryReflectionKey(created_key)
                self.assertEqual(type(disabled), bool)
                self.assertFalse(disabled)
                DisableReflectionKey(created_key)
                self.assertTrue(QueryReflectionKey(created_key))
            open_fail = lambda : OpenKeyEx(HKEY_CURRENT_USER,
                test_reflect_key_name, 0, KEY_READ | KEY_WOW64_64KEY)
            self.assertRaises(OSError, open_fail)
            with OpenKeyEx(HKEY_CURRENT_USER, test_reflect_key_name, 0, 
                KEY_READ | KEY_WOW64_32KEY) as key:
                self.assertNotEqual(key.handle, 0)
        finally:
            DeleteKeyEx(HKEY_CURRENT_USER, test_reflect_key_name,
                KEY_WOW64_32KEY, 0)

    def test_exception_numbers(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            QueryValue(HKEY_CLASSES_ROOT, 'some_value_that_does_not_exist')


def test_main():
    support.run_unittest(LocalWinregTests, RemoteWinregTests, Win64WinregTests)


if __name__ == '__main__':
    if not REMOTE_NAME:
        print('Remote registry calls can be tested using',
            "'test_winreg.py --remote \\\\machine_name'")
    test_main()
