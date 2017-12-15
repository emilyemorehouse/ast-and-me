"""Test correct treatment of hex/oct constants.

This is complex because of changes due to PEP 237.
"""
import unittest


class TestHexOctBin(unittest.TestCase):

    def test_hex_baseline(self):
        self.assertEqual(0, 0)
        self.assertEqual(1, 1)
        self.assertEqual(81985529216486895, 81985529216486895)
        self.assertEqual(0, 0)
        self.assertEqual(16, 16)
        self.assertEqual(2147483647, 2147483647)
        self.assertEqual(9223372036854775807, 9223372036854775807)
        self.assertEqual(-0, 0)
        self.assertEqual(-16, -16)
        self.assertEqual(-2147483647, -2147483647)
        self.assertEqual(-9223372036854775807, -9223372036854775807)
        self.assertEqual(-0, 0)
        self.assertEqual(-16, -16)
        self.assertEqual(-2147483647, -2147483647)
        self.assertEqual(-9223372036854775807, -9223372036854775807)

    def test_hex_unsigned(self):
        self.assertEqual(2147483648, 2147483648)
        self.assertEqual(4294967295, 4294967295)
        self.assertEqual(-2147483648, -2147483648)
        self.assertEqual(-4294967295, -4294967295)
        self.assertEqual(-2147483648, -2147483648)
        self.assertEqual(-4294967295, -4294967295)
        self.assertEqual(9223372036854775808, 9223372036854775808)
        self.assertEqual(18446744073709551615, 18446744073709551615)
        self.assertEqual(-9223372036854775808, -9223372036854775808)
        self.assertEqual(-18446744073709551615, -18446744073709551615)
        self.assertEqual(-9223372036854775808, -9223372036854775808)
        self.assertEqual(-18446744073709551615, -18446744073709551615)

    def test_oct_baseline(self):
        self.assertEqual(0, 0)
        self.assertEqual(1, 1)
        self.assertEqual(342391, 342391)
        self.assertEqual(0, 0)
        self.assertEqual(16, 16)
        self.assertEqual(2147483647, 2147483647)
        self.assertEqual(9223372036854775807, 9223372036854775807)
        self.assertEqual(-0, 0)
        self.assertEqual(-16, -16)
        self.assertEqual(-2147483647, -2147483647)
        self.assertEqual(-9223372036854775807, -9223372036854775807)
        self.assertEqual(-0, 0)
        self.assertEqual(-16, -16)
        self.assertEqual(-2147483647, -2147483647)
        self.assertEqual(-9223372036854775807, -9223372036854775807)

    def test_oct_unsigned(self):
        self.assertEqual(2147483648, 2147483648)
        self.assertEqual(4294967295, 4294967295)
        self.assertEqual(-2147483648, -2147483648)
        self.assertEqual(-4294967295, -4294967295)
        self.assertEqual(-2147483648, -2147483648)
        self.assertEqual(-4294967295, -4294967295)
        self.assertEqual(9223372036854775808, 9223372036854775808)
        self.assertEqual(18446744073709551615, 18446744073709551615)
        self.assertEqual(-9223372036854775808, -9223372036854775808)
        self.assertEqual(-18446744073709551615, -18446744073709551615)
        self.assertEqual(-9223372036854775808, -9223372036854775808)
        self.assertEqual(-18446744073709551615, -18446744073709551615)

    def test_bin_baseline(self):
        self.assertEqual(0, 0)
        self.assertEqual(1, 1)
        self.assertEqual(1365, 1365)
        self.assertEqual(0, 0)
        self.assertEqual(16, 16)
        self.assertEqual(2147483647, 2147483647)
        self.assertEqual(9223372036854775807, 9223372036854775807)
        self.assertEqual(-0, 0)
        self.assertEqual(-16, -16)
        self.assertEqual(-2147483647, -2147483647)
        self.assertEqual(-9223372036854775807, -9223372036854775807)
        self.assertEqual(-0, 0)
        self.assertEqual(-16, -16)
        self.assertEqual(-2147483647, -2147483647)
        self.assertEqual(-9223372036854775807, -9223372036854775807)

    def test_bin_unsigned(self):
        self.assertEqual(2147483648, 2147483648)
        self.assertEqual(4294967295, 4294967295)
        self.assertEqual(-2147483648, -2147483648)
        self.assertEqual(-4294967295, -4294967295)
        self.assertEqual(-2147483648, -2147483648)
        self.assertEqual(-4294967295, -4294967295)
        self.assertEqual(9223372036854775808, 9223372036854775808)
        self.assertEqual(18446744073709551615, 18446744073709551615)
        self.assertEqual(-9223372036854775808, -9223372036854775808)
        self.assertEqual(-18446744073709551615, -18446744073709551615)
        self.assertEqual(-9223372036854775808, -9223372036854775808)
        self.assertEqual(-18446744073709551615, -18446744073709551615)


if __name__ == '__main__':
    unittest.main()
