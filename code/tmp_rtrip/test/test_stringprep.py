import unittest
from stringprep import *


class StringprepTests(unittest.TestCase):

    def test(self):
        self.assertTrue(in_table_a1('ȡ'))
        self.assertFalse(in_table_a1('Ȣ'))
        self.assertTrue(in_table_b1('\xad'))
        self.assertFalse(in_table_b1('®'))
        self.assertTrue(map_table_b2('A'), 'a')
        self.assertTrue(map_table_b2('a'), 'a')
        self.assertTrue(map_table_b3('A'), 'a')
        self.assertTrue(map_table_b3('a'), 'a')
        self.assertTrue(in_table_c11(' '))
        self.assertFalse(in_table_c11('!'))
        self.assertTrue(in_table_c12('\xa0'))
        self.assertFalse(in_table_c12('¡'))
        self.assertTrue(in_table_c12('\xa0'))
        self.assertFalse(in_table_c12('¡'))
        self.assertTrue(in_table_c11_c12('\xa0'))
        self.assertFalse(in_table_c11_c12('¡'))
        self.assertTrue(in_table_c21('\x1f'))
        self.assertFalse(in_table_c21(' '))
        self.assertTrue(in_table_c22('\x9f'))
        self.assertFalse(in_table_c22('\xa0'))
        self.assertTrue(in_table_c21_c22('\x9f'))
        self.assertFalse(in_table_c21_c22('\xa0'))
        self.assertTrue(in_table_c3('\ue000'))
        self.assertFalse(in_table_c3('豈'))
        self.assertTrue(in_table_c4('\uffff'))
        self.assertFalse(in_table_c4('\x00'))
        self.assertTrue(in_table_c5('\ud800'))
        self.assertFalse(in_table_c5('\ud7ff'))
        self.assertTrue(in_table_c6('\ufff9'))
        self.assertFalse(in_table_c6('\ufffe'))
        self.assertTrue(in_table_c7('⿰'))
        self.assertFalse(in_table_c7('\u2ffc'))
        self.assertTrue(in_table_c8('̀'))
        self.assertFalse(in_table_c8('͂'))
        self.assertTrue(in_table_d1('־'))
        self.assertFalse(in_table_d1('ֿ'))
        self.assertTrue(in_table_d2('A'))
        self.assertFalse(in_table_d2('@'))


if __name__ == '__main__':
    unittest.main()
