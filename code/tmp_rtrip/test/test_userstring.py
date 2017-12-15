import unittest
from test import string_tests
from collections import UserString


class UserStringTest(string_tests.CommonTest, string_tests.
    MixinStrUnicodeUserStringTest, unittest.TestCase):
    type2test = UserString

    def checkequal(self, result, object, methodname, *args, **kwargs):
        result = self.fixtype(result)
        object = self.fixtype(object)
        realresult = getattr(object, methodname)(*args, **kwargs)
        self.assertEqual(result, realresult)

    def checkraises(self, exc, obj, methodname, *args):
        obj = self.fixtype(obj)
        with self.assertRaises(exc) as cm:
            getattr(obj, methodname)(*args)
        self.assertNotEqual(str(cm.exception), '')

    def checkcall(self, object, methodname, *args):
        object = self.fixtype(object)
        getattr(object, methodname)(*args)


if __name__ == '__main__':
    unittest.main()
