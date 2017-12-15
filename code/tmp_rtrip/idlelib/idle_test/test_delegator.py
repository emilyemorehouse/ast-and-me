import unittest
from idlelib.delegator import Delegator


class DelegatorTest(unittest.TestCase):

    def test_mydel(self):
        mydel = Delegator(int)
        self.assertIs(mydel.delegate, int)
        self.assertEqual(mydel._Delegator__cache, set())
        self.assertRaises(AttributeError, mydel.__getattr__, 'xyz')
        bl = mydel.bit_length
        self.assertIs(bl, int.bit_length)
        self.assertIs(mydel.__dict__['bit_length'], int.bit_length)
        self.assertEqual(mydel._Delegator__cache, {'bit_length'})
        mydel.numerator
        self.assertEqual(mydel._Delegator__cache, {'bit_length', 'numerator'})
        del mydel.numerator
        self.assertNotIn('numerator', mydel.__dict__)
        mydel.setdelegate(float)
        self.assertNotIn('bit_length', mydel.__dict__)
        self.assertEqual(mydel._Delegator__cache, set())
        self.assertIs(mydel.delegate, float)


if __name__ == '__main__':
    unittest.main(verbosity=2, exit=2)
