from test.test_json import PyTest, CTest
JSON = """
[[[[[[[[[[[[[[[[[[["Not too deep"]]]]]]]]]]]]]]]]]]]
"""


class TestPass2:

    def test_parse(self):
        res = self.loads(JSON)
        out = self.dumps(res)
        self.assertEqual(res, self.loads(out))


class TestPyPass2(TestPass2, PyTest):
    pass


class TestCPass2(TestPass2, CTest):
    pass
