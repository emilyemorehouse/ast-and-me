from test.test_json import PyTest, CTest
JSON = """
{
    "JSON Test Pattern pass3": {
        "The outermost value": "must be an object or array.",
        "In this test": "It is an object."
    }
}
"""


class TestPass3:

    def test_parse(self):
        res = self.loads(JSON)
        out = self.dumps(res)
        self.assertEqual(res, self.loads(out))


class TestPyPass3(TestPass3, PyTest):
    pass


class TestCPass3(TestPass3, CTest):
    pass
