"""
Tests for the html module functions.
"""
import html
import unittest


class HtmlTests(unittest.TestCase):

    def test_escape(self):
        self.assertEqual(html.escape('\'<script>"&foo;"</script>\''),
            '&#x27;&lt;script&gt;&quot;&amp;foo;&quot;&lt;/script&gt;&#x27;')
        self.assertEqual(html.escape('\'<script>"&foo;"</script>\'', False),
            '\'&lt;script&gt;"&amp;foo;"&lt;/script&gt;\'')

    def test_unescape(self):
        numeric_formats = ['&#%d', '&#%d;', '&#x%x', '&#x%x;']
        errmsg = 'unescape(%r) should have returned %r'

        def check(text, expected):
            self.assertEqual(html.unescape(text), expected, msg=errmsg % (
                text, expected))

        def check_num(num, expected):
            for format in numeric_formats:
                text = format % num
                self.assertEqual(html.unescape(text), expected, msg=errmsg %
                    (text, expected))
        check('no character references', 'no character references')
        check('&\n&\t& &&', '&\n&\t& &&')
        check('&0 &9 &a &0; &9; &a;', '&0 &9 &a &0; &9; &a;')
        for x in ['&', '&#', '&#x', '&#X', '&#y', '&#xy', '&#Xy']:
            check(x, x)
            check(x + ';', x + ';')
        formats = ['&#%d', '&#%07d', '&#%d;', '&#%07d;', '&#x%x', '&#x%06x',
            '&#x%x;', '&#x%06x;', '&#x%X', '&#x%06X', '&#X%x;', '&#X%06x;']
        for num, char in zip([65, 97, 34, 38, 9731, 1053236], ['A', 'a',
            '"', '&', '☃', '\U00101234']):
            for s in formats:
                check(s % num, char)
                for end in [' ', 'X']:
                    check((s + end) % num, char + end)
        for cp in [55296, 56064, 56320, 57343, 1114112]:
            check_num(cp, '�')
        for cp in [1, 11, 14, 127, 65534, 65535, 1114110, 1114111]:
            check_num(cp, '')
        for num, ch in zip([13, 128, 149, 157], '\r€•\x9d'):
            check_num(num, ch)
        check_num(0, '�')
        check_num(9, '\t')
        check_num(1000000000000000000, '�')
        for e in ['&quot;;', '&#34;;', '&#x22;;', '&#X22;;']:
            check(e, '";')
        for e in ['&quot;quot;', '&#34;quot;', '&#x22;quot;', '&#X22;quot;']:
            check(e, '"quot;')
        for e in ['&quot', '&#34', '&#x22', '&#X22']:
            check(e * 3, '"""')
            check((e + ';') * 3, '"""')
        for e in ['&amp', '&amp;', '&AMP', '&AMP;']:
            check(e, '&')
        for e in ['&Amp', '&Amp;']:
            check(e, e)
        check('&svadilfari;', '&svadilfari;')
        check('&notit', '¬it')
        check('&notit;', '¬it;')
        check('&notin', '¬in')
        check('&notin;', '∉')
        check('&notReallyAnExistingNamedCharacterReference;',
            '¬ReallyAnExistingNamedCharacterReference;')
        check('&CounterClockwiseContourIntegral;', '∳')
        check('&acE;', '∾̳')
        check('&acE', '&acE')
        check('&#123; ' * 1050, '{ ' * 1050)
        check('&Eacuteric&Eacute;ric&alphacentauri&alpha;centauri',
            'ÉricÉric&alphacentauriαcentauri')
        check('&co;', '&co;')


if __name__ == '__main__':
    unittest.main()
