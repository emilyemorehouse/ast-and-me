from test.test_json import PyTest, CTest
JSONDOCS = ['"A JSON payload should be an object or array, not a string."',
    '["Unclosed array"', '{unquoted_key: "keys must be quoted"}',
    '["extra comma",]', '["double extra comma",,]',
    '[   , "<-- missing value"]', '["Comma after the close"],',
    '["Extra close"]]', '{"Extra comma": true,}',
    '{"Extra value after close": true} "misplaced quoted value"',
    '{"Illegal expression": 1 + 2}', '{"Illegal invocation": alert()}',
    '{"Numbers cannot have leading zeroes": 013}',
    '{"Numbers cannot be hex": 0x14}',
    '["Illegal backslash escape: \\x15"]', '[\\naked]',
    '["Illegal backslash escape: \\017"]',
    '[[[[[[[[[[[[[[[[[[[["Too deep"]]]]]]]]]]]]]]]]]]]]',
    '{"Missing colon" null}', '{"Double colon":: null}',
    '{"Comma instead of colon", null}', '["Colon instead of comma": false]',
    '["Bad value", truth]', "['single quote']",
    '["\ttab\tcharacter\tin\tstring\t"]',
    '["tab\\   character\\   in\\  string\\  "]', '["line\nbreak"]',
    '["line\\\nbreak"]', '[0e]', '[0e+]', '[0e+-1]',
    '{"Comma instead if closing brace": true,', '["mismatch"}',
    '["A\x1fZ control characters in string"]']
SKIPS = {(1): 'why not have a string payload?', (18):
    "spec doesn't specify any nesting limitations"}


class TestFail:

    def test_failures(self):
        for idx, doc in enumerate(JSONDOCS):
            idx = idx + 1
            if idx in SKIPS:
                self.loads(doc)
                continue
            try:
                self.loads(doc)
            except self.JSONDecodeError:
                pass
            else:
                self.fail('Expected failure for fail{0}.json: {1!r}'.format
                    (idx, doc))

    def test_non_string_keys_dict(self):
        data = {'a': 1, (1, 2): 2}
        self.assertRaises(TypeError, self.dumps, data)
        self.assertRaises(TypeError, self.dumps, data, indent=True)

    def test_truncated_input(self):
        test_cases = [('', 'Expecting value', 0), ('[', 'Expecting value', 
            1), ('[42', "Expecting ',' delimiter", 3), ('[42,',
            'Expecting value', 4), ('["', 'Unterminated string starting at',
            1), ('["spam', 'Unterminated string starting at', 1), (
            '["spam"', "Expecting ',' delimiter", 7), ('["spam",',
            'Expecting value', 8), ('{',
            'Expecting property name enclosed in double quotes', 1), ('{"',
            'Unterminated string starting at', 1), ('{"spam',
            'Unterminated string starting at', 1), ('{"spam"',
            "Expecting ':' delimiter", 7), ('{"spam":', 'Expecting value', 
            8), ('{"spam":42', "Expecting ',' delimiter", 10), (
            '{"spam":42,',
            'Expecting property name enclosed in double quotes', 11)]
        test_cases += [('"', 'Unterminated string starting at', 0), (
            '"spam', 'Unterminated string starting at', 0)]
        for data, msg, idx in test_cases:
            with self.assertRaises(self.JSONDecodeError) as cm:
                self.loads(data)
            err = cm.exception
            self.assertEqual(err.msg, msg)
            self.assertEqual(err.pos, idx)
            self.assertEqual(err.lineno, 1)
            self.assertEqual(err.colno, idx + 1)
            self.assertEqual(str(err), '%s: line 1 column %d (char %d)' % (
                msg, idx + 1, idx))

    def test_unexpected_data(self):
        test_cases = [('[,', 'Expecting value', 1), ('{"spam":[}',
            'Expecting value', 9), ('[42:', "Expecting ',' delimiter", 3),
            ('[42 "spam"', "Expecting ',' delimiter", 4), ('[42,]',
            'Expecting value', 4), ('{"spam":[42}',
            "Expecting ',' delimiter", 11), ('["]',
            'Unterminated string starting at', 1), ('["spam":',
            "Expecting ',' delimiter", 7), ('["spam",]', 'Expecting value',
            8), ('{:', 'Expecting property name enclosed in double quotes',
            1), ('{,', 'Expecting property name enclosed in double quotes',
            1), ('{42', 'Expecting property name enclosed in double quotes',
            1), ('[{]', 'Expecting property name enclosed in double quotes',
            2), ('{"spam",', "Expecting ':' delimiter", 7), ('{"spam"}',
            "Expecting ':' delimiter", 7), ('[{"spam"]',
            "Expecting ':' delimiter", 8), ('{"spam":}', 'Expecting value',
            8), ('[{"spam":]', 'Expecting value', 9), ('{"spam":42 "ham"',
            "Expecting ',' delimiter", 11), ('[{"spam":42]',
            "Expecting ',' delimiter", 11), ('{"spam":42,}',
            'Expecting property name enclosed in double quotes', 11)]
        for data, msg, idx in test_cases:
            with self.assertRaises(self.JSONDecodeError) as cm:
                self.loads(data)
            err = cm.exception
            self.assertEqual(err.msg, msg)
            self.assertEqual(err.pos, idx)
            self.assertEqual(err.lineno, 1)
            self.assertEqual(err.colno, idx + 1)
            self.assertEqual(str(err), '%s: line 1 column %d (char %d)' % (
                msg, idx + 1, idx))

    def test_extra_data(self):
        test_cases = [('[]]', 'Extra data', 2), ('{}}', 'Extra data', 2), (
            '[],[]', 'Extra data', 2), ('{},{}', 'Extra data', 2)]
        test_cases += [('42,"spam"', 'Extra data', 2), ('"spam",42',
            'Extra data', 6)]
        for data, msg, idx in test_cases:
            with self.assertRaises(self.JSONDecodeError) as cm:
                self.loads(data)
            err = cm.exception
            self.assertEqual(err.msg, msg)
            self.assertEqual(err.pos, idx)
            self.assertEqual(err.lineno, 1)
            self.assertEqual(err.colno, idx + 1)
            self.assertEqual(str(err), '%s: line 1 column %d (char %d)' % (
                msg, idx + 1, idx))

    def test_linecol(self):
        test_cases = [('!', 1, 1, 0), (' !', 1, 2, 1), ('\n!', 2, 1, 1), (
            '\n  \n\n     !', 4, 6, 10)]
        for data, line, col, idx in test_cases:
            with self.assertRaises(self.JSONDecodeError) as cm:
                self.loads(data)
            err = cm.exception
            self.assertEqual(err.msg, 'Expecting value')
            self.assertEqual(err.pos, idx)
            self.assertEqual(err.lineno, line)
            self.assertEqual(err.colno, col)
            self.assertEqual(str(err), 
                'Expecting value: line %s column %d (char %d)' % (line, col,
                idx))


class TestPyFail(TestFail, PyTest):
    pass


class TestCFail(TestFail, CTest):
    pass
