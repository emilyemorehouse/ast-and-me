import codecs
import html.entities
import sys
import test.support
import unicodedata
import unittest


class PosReturn:

    def __init__(self):
        self.pos = 0

    def handle(self, exc):
        oldpos = self.pos
        realpos = oldpos
        if realpos < 0:
            realpos = len(exc.object) + realpos
        if realpos <= exc.start:
            self.pos = len(exc.object)
        return '<?>', oldpos


class BadStartUnicodeEncodeError(UnicodeEncodeError):

    def __init__(self):
        UnicodeEncodeError.__init__(self, 'ascii', '', 0, 1, 'bad')
        self.start = []


class BadObjectUnicodeEncodeError(UnicodeEncodeError):

    def __init__(self):
        UnicodeEncodeError.__init__(self, 'ascii', '', 0, 1, 'bad')
        self.object = []


class NoEndUnicodeDecodeError(UnicodeDecodeError):

    def __init__(self):
        UnicodeDecodeError.__init__(self, 'ascii', bytearray(b''), 0, 1, 'bad')
        del self.end


class BadObjectUnicodeDecodeError(UnicodeDecodeError):

    def __init__(self):
        UnicodeDecodeError.__init__(self, 'ascii', bytearray(b''), 0, 1, 'bad')
        self.object = []


class NoStartUnicodeTranslateError(UnicodeTranslateError):

    def __init__(self):
        UnicodeTranslateError.__init__(self, '', 0, 1, 'bad')
        del self.start


class NoEndUnicodeTranslateError(UnicodeTranslateError):

    def __init__(self):
        UnicodeTranslateError.__init__(self, '', 0, 1, 'bad')
        del self.end


class NoObjectUnicodeTranslateError(UnicodeTranslateError):

    def __init__(self):
        UnicodeTranslateError.__init__(self, '', 0, 1, 'bad')
        del self.object


class CodecCallbackTest(unittest.TestCase):

    def test_xmlcharrefreplace(self):
        s = 'スパモ änd eggs'
        self.assertEqual(s.encode('ascii', 'xmlcharrefreplace'),
            b'&#12473;&#12497;&#12514; &#228;nd eggs')
        self.assertEqual(s.encode('latin-1', 'xmlcharrefreplace'),
            b'&#12473;&#12497;&#12514; \xe4nd eggs')

    def test_xmlcharnamereplace(self):

        def xmlcharnamereplace(exc):
            if not isinstance(exc, UnicodeEncodeError):
                raise TypeError("don't know how to handle %r" % exc)
            l = []
            for c in exc.object[exc.start:exc.end]:
                try:
                    l.append('&%s;' % html.entities.codepoint2name[ord(c)])
                except KeyError:
                    l.append('&#%d;' % ord(c))
            return ''.join(l), exc.end
        codecs.register_error('test.xmlcharnamereplace', xmlcharnamereplace)
        sin = '«ℜ» = 〈ሴ€〉'
        sout = b'&laquo;&real;&raquo; = &lang;&#4660;&euro;&rang;'
        self.assertEqual(sin.encode('ascii', 'test.xmlcharnamereplace'), sout)
        sout = b'\xab&real;\xbb = &lang;&#4660;&euro;&rang;'
        self.assertEqual(sin.encode('latin-1', 'test.xmlcharnamereplace'), sout
            )
        sout = b'\xab&real;\xbb = &lang;&#4660;\xa4&rang;'
        self.assertEqual(sin.encode('iso-8859-15',
            'test.xmlcharnamereplace'), sout)

    def test_uninamereplace(self):

        def uninamereplace(exc):
            if not isinstance(exc, UnicodeEncodeError):
                raise TypeError("don't know how to handle %r" % exc)
            l = []
            for c in exc.object[exc.start:exc.end]:
                l.append(unicodedata.name(c, '0x%x' % ord(c)))
            return '\x1b[1m%s\x1b[0m' % ', '.join(l), exc.end
        codecs.register_error('test.uninamereplace', uninamereplace)
        sin = '¬ሴ€耀'
        sout = (
            b'\x1b[1mNOT SIGN, ETHIOPIC SYLLABLE SEE, EURO SIGN, CJK UNIFIED IDEOGRAPH-8000\x1b[0m'
            )
        self.assertEqual(sin.encode('ascii', 'test.uninamereplace'), sout)
        sout = (
            b'\xac\x1b[1mETHIOPIC SYLLABLE SEE, EURO SIGN, CJK UNIFIED IDEOGRAPH-8000\x1b[0m'
            )
        self.assertEqual(sin.encode('latin-1', 'test.uninamereplace'), sout)
        sout = (
            b'\xac\x1b[1mETHIOPIC SYLLABLE SEE\x1b[0m\xa4\x1b[1mCJK UNIFIED IDEOGRAPH-8000\x1b[0m'
            )
        self.assertEqual(sin.encode('iso-8859-15', 'test.uninamereplace'), sout
            )

    def test_backslashescape(self):
        sin = 'a¬ሴ€耀\U0010ffff'
        sout = b'a\\xac\\u1234\\u20ac\\u8000\\U0010ffff'
        self.assertEqual(sin.encode('ascii', 'backslashreplace'), sout)
        sout = b'a\xac\\u1234\\u20ac\\u8000\\U0010ffff'
        self.assertEqual(sin.encode('latin-1', 'backslashreplace'), sout)
        sout = b'a\xac\\u1234\xa4\\u8000\\U0010ffff'
        self.assertEqual(sin.encode('iso-8859-15', 'backslashreplace'), sout)

    def test_nameescape(self):
        sin = 'a¬ሴ€耀\U0010ffff'
        sout = (
            b'a\\N{NOT SIGN}\\N{ETHIOPIC SYLLABLE SEE}\\N{EURO SIGN}\\N{CJK UNIFIED IDEOGRAPH-8000}\\U0010ffff'
            )
        self.assertEqual(sin.encode('ascii', 'namereplace'), sout)
        sout = (
            b'a\xac\\N{ETHIOPIC SYLLABLE SEE}\\N{EURO SIGN}\\N{CJK UNIFIED IDEOGRAPH-8000}\\U0010ffff'
            )
        self.assertEqual(sin.encode('latin-1', 'namereplace'), sout)
        sout = (
            b'a\xac\\N{ETHIOPIC SYLLABLE SEE}\xa4\\N{CJK UNIFIED IDEOGRAPH-8000}\\U0010ffff'
            )
        self.assertEqual(sin.encode('iso-8859-15', 'namereplace'), sout)

    def test_decoding_callbacks(self):

        def relaxedutf8(exc):
            if not isinstance(exc, UnicodeDecodeError):
                raise TypeError("don't know how to handle %r" % exc)
            if exc.object[exc.start:exc.start + 2] == b'\xc0\x80':
                return '\x00', exc.start + 2
            else:
                raise exc
        codecs.register_error('test.relaxedutf8', relaxedutf8)
        sin = b'a\x00b\xc0\x80c\xc3\xbc\xc0\x80\xc0\x80'
        sout = 'a\x00b\x00cü\x00\x00'
        self.assertEqual(sin.decode('utf-8', 'test.relaxedutf8'), sout)
        sin = b'\xc0\x80\xc0\x81'
        self.assertRaises(UnicodeDecodeError, sin.decode, 'utf-8',
            'test.relaxedutf8')

    def test_charmapencode(self):
        charmap = dict((ord(c), bytes(2 * c.upper(), 'ascii')) for c in
            'abcdefgh')
        sin = 'abc'
        sout = b'AABBCC'
        self.assertEqual(codecs.charmap_encode(sin, 'strict', charmap)[0], sout
            )
        sin = 'abcA'
        self.assertRaises(UnicodeError, codecs.charmap_encode, sin,
            'strict', charmap)
        charmap[ord('?')] = b'XYZ'
        sin = 'abcDEF'
        sout = b'AABBCCXYZXYZXYZ'
        self.assertEqual(codecs.charmap_encode(sin, 'replace', charmap)[0],
            sout)
        charmap[ord('?')] = 'XYZ'
        self.assertRaises(TypeError, codecs.charmap_encode, sin, 'replace',
            charmap)

    def test_decodeunicodeinternal(self):
        with test.support.check_warnings((
            'unicode_internal codec has been deprecated', DeprecationWarning)):
            self.assertRaises(UnicodeDecodeError, b'\x00\x00\x00\x00\x00'.
                decode, 'unicode-internal')
            if len('\x00'.encode('unicode-internal')) == 4:

                def handler_unicodeinternal(exc):
                    if not isinstance(exc, UnicodeDecodeError):
                        raise TypeError("don't know how to handle %r" % exc)
                    return '\x01', 1
                self.assertEqual(b'\x00\x00\x00\x00\x00'.decode(
                    'unicode-internal', 'ignore'), '\x00')
                self.assertEqual(b'\x00\x00\x00\x00\x00'.decode(
                    'unicode-internal', 'replace'), '\x00�')
                self.assertEqual(b'\x00\x00\x00\x00\x00'.decode(
                    'unicode-internal', 'backslashreplace'), '\x00\\x00')
                codecs.register_error('test.hui', handler_unicodeinternal)
                self.assertEqual(b'\x00\x00\x00\x00\x00'.decode(
                    'unicode-internal', 'test.hui'), '\x00\x01\x00')

    def test_callbacks(self):

        def handler1(exc):
            r = range(exc.start, exc.end)
            if isinstance(exc, UnicodeEncodeError):
                l = [('<%d>' % ord(exc.object[pos])) for pos in r]
            elif isinstance(exc, UnicodeDecodeError):
                l = [('<%d>' % exc.object[pos]) for pos in r]
            else:
                raise TypeError("don't know how to handle %r" % exc)
            return '[%s]' % ''.join(l), exc.end
        codecs.register_error('test.handler1', handler1)

        def handler2(exc):
            if not isinstance(exc, UnicodeDecodeError):
                raise TypeError("don't know how to handle %r" % exc)
            l = [('<%d>' % exc.object[pos]) for pos in range(exc.start, exc
                .end)]
            return '[%s]' % ''.join(l), exc.end + 1
        codecs.register_error('test.handler2', handler2)
        s = b'\x00\x81\x7f\x80\xff'
        self.assertEqual(s.decode('ascii', 'test.handler1'),
            '\x00[<129>]\x7f[<128>][<255>]')
        self.assertEqual(s.decode('ascii', 'test.handler2'),
            '\x00[<129>][<128>]')
        self.assertEqual(b'\\u3042\\u3xxx'.decode('unicode-escape',
            'test.handler1'), 'あ[<92><117><51>]xxx')
        self.assertEqual(b'\\u3042\\u3xx'.decode('unicode-escape',
            'test.handler1'), 'あ[<92><117><51>]xx')
        self.assertEqual(codecs.charmap_decode(b'abc', 'test.handler1', {
            ord('a'): 'z'})[0], 'z[<98>][<99>]')
        self.assertEqual('güßrk'.encode('ascii', 'test.handler1'),
            b'g[<252><223>]rk')
        self.assertEqual('güß'.encode('ascii', 'test.handler1'),
            b'g[<252><223>]')

    def test_longstrings(self):
        errors = ['strict', 'ignore', 'replace', 'xmlcharrefreplace',
            'backslashreplace', 'namereplace']
        for err in errors:
            codecs.register_error('test.' + err, codecs.lookup_error(err))
        l = 1000
        errors += [('test.' + err) for err in errors]
        for uni in [(s * l) for s in ('x', 'あ', 'aä')]:
            for enc in ('ascii', 'latin-1', 'iso-8859-1', 'iso-8859-15',
                'utf-8', 'utf-7', 'utf-16', 'utf-32'):
                for err in errors:
                    try:
                        uni.encode(enc, err)
                    except UnicodeError:
                        pass

    def check_exceptionobjectargs(self, exctype, args, msg):
        self.assertRaises(TypeError, exctype, *args[:-1])
        self.assertRaises(TypeError, exctype, *(args + ['too much']))
        wrongargs = ['spam', b'eggs', b'spam', 42, 1.0, None]
        for i in range(len(args)):
            for wrongarg in wrongargs:
                if type(wrongarg) is type(args[i]):
                    continue
                callargs = []
                for j in range(len(args)):
                    if i == j:
                        callargs.append(wrongarg)
                    else:
                        callargs.append(args[i])
                self.assertRaises(TypeError, exctype, *callargs)
        exc = exctype(*args)
        self.assertEqual(str(exc), msg)

    def test_unicodeencodeerror(self):
        self.check_exceptionobjectargs(UnicodeEncodeError, ['ascii', 'gürk',
            1, 2, 'ouch'],
            "'ascii' codec can't encode character '\\xfc' in position 1: ouch")
        self.check_exceptionobjectargs(UnicodeEncodeError, ['ascii', 'gürk',
            1, 4, 'ouch'],
            "'ascii' codec can't encode characters in position 1-3: ouch")
        self.check_exceptionobjectargs(UnicodeEncodeError, ['ascii', 'üx', 
            0, 1, 'ouch'],
            "'ascii' codec can't encode character '\\xfc' in position 0: ouch")
        self.check_exceptionobjectargs(UnicodeEncodeError, ['ascii', 'Āx', 
            0, 1, 'ouch'],
            "'ascii' codec can't encode character '\\u0100' in position 0: ouch"
            )
        self.check_exceptionobjectargs(UnicodeEncodeError, ['ascii',
            '\uffffx', 0, 1, 'ouch'],
            "'ascii' codec can't encode character '\\uffff' in position 0: ouch"
            )
        self.check_exceptionobjectargs(UnicodeEncodeError, ['ascii', '𐀀x', 
            0, 1, 'ouch'],
            "'ascii' codec can't encode character '\\U00010000' in position 0: ouch"
            )

    def test_unicodedecodeerror(self):
        self.check_exceptionobjectargs(UnicodeDecodeError, ['ascii',
            bytearray(b'g\xfcrk'), 1, 2, 'ouch'],
            "'ascii' codec can't decode byte 0xfc in position 1: ouch")
        self.check_exceptionobjectargs(UnicodeDecodeError, ['ascii',
            bytearray(b'g\xfcrk'), 1, 3, 'ouch'],
            "'ascii' codec can't decode bytes in position 1-2: ouch")

    def test_unicodetranslateerror(self):
        self.check_exceptionobjectargs(UnicodeTranslateError, ['gürk', 1, 2,
            'ouch'], "can't translate character '\\xfc' in position 1: ouch")
        self.check_exceptionobjectargs(UnicodeTranslateError, ['gĀrk', 1, 2,
            'ouch'], "can't translate character '\\u0100' in position 1: ouch")
        self.check_exceptionobjectargs(UnicodeTranslateError, ['g\uffffrk',
            1, 2, 'ouch'],
            "can't translate character '\\uffff' in position 1: ouch")
        self.check_exceptionobjectargs(UnicodeTranslateError, ['g𐀀rk', 1, 2,
            'ouch'],
            "can't translate character '\\U00010000' in position 1: ouch")
        self.check_exceptionobjectargs(UnicodeTranslateError, ['gürk', 1, 3,
            'ouch'], "can't translate characters in position 1-2: ouch")

    def test_badandgoodstrictexceptions(self):
        self.assertRaises(TypeError, codecs.strict_errors, 42)
        self.assertRaises(Exception, codecs.strict_errors, Exception('ouch'))
        self.assertRaises(UnicodeEncodeError, codecs.strict_errors,
            UnicodeEncodeError('ascii', 'あ', 0, 1, 'ouch'))
        self.assertRaises(UnicodeDecodeError, codecs.strict_errors,
            UnicodeDecodeError('ascii', bytearray(b'\xff'), 0, 1, 'ouch'))
        self.assertRaises(UnicodeTranslateError, codecs.strict_errors,
            UnicodeTranslateError('あ', 0, 1, 'ouch'))

    def test_badandgoodignoreexceptions(self):
        self.assertRaises(TypeError, codecs.ignore_errors, 42)
        self.assertRaises(TypeError, codecs.ignore_errors, UnicodeError('ouch')
            )
        self.assertEqual(codecs.ignore_errors(UnicodeEncodeError('ascii',
            'aあb', 1, 2, 'ouch')), ('', 2))
        self.assertEqual(codecs.ignore_errors(UnicodeDecodeError('ascii',
            bytearray(b'a\xffb'), 1, 2, 'ouch')), ('', 2))
        self.assertEqual(codecs.ignore_errors(UnicodeTranslateError('aあb', 
            1, 2, 'ouch')), ('', 2))

    def test_badandgoodreplaceexceptions(self):
        self.assertRaises(TypeError, codecs.replace_errors, 42)
        self.assertRaises(TypeError, codecs.replace_errors, UnicodeError(
            'ouch'))
        self.assertRaises(TypeError, codecs.replace_errors,
            BadObjectUnicodeEncodeError())
        self.assertRaises(TypeError, codecs.replace_errors,
            BadObjectUnicodeDecodeError())
        self.assertEqual(codecs.replace_errors(UnicodeEncodeError('ascii',
            'aあb', 1, 2, 'ouch')), ('?', 2))
        self.assertEqual(codecs.replace_errors(UnicodeDecodeError('ascii',
            bytearray(b'a\xffb'), 1, 2, 'ouch')), ('�', 2))
        self.assertEqual(codecs.replace_errors(UnicodeTranslateError('aあb',
            1, 2, 'ouch')), ('�', 2))

    def test_badandgoodxmlcharrefreplaceexceptions(self):
        self.assertRaises(TypeError, codecs.xmlcharrefreplace_errors, 42)
        self.assertRaises(TypeError, codecs.xmlcharrefreplace_errors,
            UnicodeError('ouch'))
        self.assertRaises(TypeError, codecs.xmlcharrefreplace_errors,
            UnicodeDecodeError('ascii', bytearray(b'\xff'), 0, 1, 'ouch'))
        self.assertRaises(TypeError, codecs.xmlcharrefreplace_errors,
            UnicodeTranslateError('あ', 0, 1, 'ouch'))
        cs = (0, 1, 9, 10, 99, 100, 999, 1000, 9999, 10000, 99999, 100000, 
            999999, 1000000)
        cs += 55296, 57343
        s = ''.join(chr(c) for c in cs)
        self.assertEqual(codecs.xmlcharrefreplace_errors(UnicodeEncodeError
            ('ascii', 'a' + s + 'b', 1, 1 + len(s), 'ouch')), (''.join(
            '&#%d;' % c for c in cs), 1 + len(s)))

    def test_badandgoodbackslashreplaceexceptions(self):
        self.assertRaises(TypeError, codecs.backslashreplace_errors, 42)
        self.assertRaises(TypeError, codecs.backslashreplace_errors,
            UnicodeError('ouch'))
        tests = [('あ', '\\u3042'), ('\n', '\\x0a'), ('a', '\\x61'), ('\x00',
            '\\x00'), ('ÿ', '\\xff'), ('Ā', '\\u0100'), ('\uffff',
            '\\uffff'), ('𐀀', '\\U00010000'), ('\U0010ffff', '\\U0010ffff'),
            ('\ud800', '\\ud800'), ('\udfff', '\\udfff'), ('\ud800\udfff',
            '\\ud800\\udfff')]
        for s, r in tests:
            with self.subTest(str=s):
                self.assertEqual(codecs.backslashreplace_errors(
                    UnicodeEncodeError('ascii', 'a' + s + 'b', 1, 1 + len(s
                    ), 'ouch')), (r, 1 + len(s)))
                self.assertEqual(codecs.backslashreplace_errors(
                    UnicodeTranslateError('a' + s + 'b', 1, 1 + len(s),
                    'ouch')), (r, 1 + len(s)))
        tests = [(b'a', '\\x61'), (b'\n', '\\x0a'), (b'\x00', '\\x00'), (
            b'\xff', '\\xff')]
        for b, r in tests:
            with self.subTest(bytes=b):
                self.assertEqual(codecs.backslashreplace_errors(
                    UnicodeDecodeError('ascii', bytearray(b'a' + b + b'b'),
                    1, 2, 'ouch')), (r, 2))

    def test_badandgoodnamereplaceexceptions(self):
        self.assertRaises(TypeError, codecs.namereplace_errors, 42)
        self.assertRaises(TypeError, codecs.namereplace_errors,
            UnicodeError('ouch'))
        self.assertRaises(TypeError, codecs.namereplace_errors,
            UnicodeDecodeError('ascii', bytearray(b'\xff'), 0, 1, 'ouch'))
        self.assertRaises(TypeError, codecs.namereplace_errors,
            UnicodeTranslateError('あ', 0, 1, 'ouch'))
        tests = [('あ', '\\N{HIRAGANA LETTER A}'), ('\x00', '\\x00'), ('ﯹ',
            '\\N{ARABIC LIGATURE UIGHUR KIRGHIZ YEH WITH HAMZA ABOVE WITH ALEF MAKSURA ISOLATED FORM}'
            ), ('\U000e007f', '\\N{CANCEL TAG}'), ('\U0010ffff',
            '\\U0010ffff'), ('\ud800', '\\ud800'), ('\udfff', '\\udfff'), (
            '\ud800\udfff', '\\ud800\\udfff')]
        for s, r in tests:
            with self.subTest(str=s):
                self.assertEqual(codecs.namereplace_errors(
                    UnicodeEncodeError('ascii', 'a' + s + 'b', 1, 1 + len(s
                    ), 'ouch')), (r, 1 + len(s)))

    def test_badandgoodsurrogateescapeexceptions(self):
        surrogateescape_errors = codecs.lookup_error('surrogateescape')
        self.assertRaises(TypeError, surrogateescape_errors, 42)
        self.assertRaises(TypeError, surrogateescape_errors, UnicodeError(
            'ouch'))
        self.assertRaises(TypeError, surrogateescape_errors,
            UnicodeTranslateError('\udc80', 0, 1, 'ouch'))
        for s in ('a', '\udc7f', '\udd00'):
            with self.subTest(str=s):
                self.assertRaises(UnicodeEncodeError,
                    surrogateescape_errors, UnicodeEncodeError('ascii', s, 
                    0, 1, 'ouch'))
        self.assertEqual(surrogateescape_errors(UnicodeEncodeError('ascii',
            'a\udc80b', 1, 2, 'ouch')), (b'\x80', 2))
        self.assertRaises(UnicodeDecodeError, surrogateescape_errors,
            UnicodeDecodeError('ascii', bytearray(b'a'), 0, 1, 'ouch'))
        self.assertEqual(surrogateescape_errors(UnicodeDecodeError('ascii',
            bytearray(b'a\x80b'), 1, 2, 'ouch')), ('\udc80', 2))

    def test_badandgoodsurrogatepassexceptions(self):
        surrogatepass_errors = codecs.lookup_error('surrogatepass')
        self.assertRaises(TypeError, surrogatepass_errors, 42)
        self.assertRaises(TypeError, surrogatepass_errors, UnicodeError('ouch')
            )
        self.assertRaises(TypeError, surrogatepass_errors,
            UnicodeTranslateError('\ud800', 0, 1, 'ouch'))
        for enc in ('utf-8', 'utf-16le', 'utf-16be', 'utf-32le', 'utf-32be'):
            with self.subTest(encoding=enc):
                self.assertRaises(UnicodeEncodeError, surrogatepass_errors,
                    UnicodeEncodeError(enc, 'a', 0, 1, 'ouch'))
                self.assertRaises(UnicodeDecodeError, surrogatepass_errors,
                    UnicodeDecodeError(enc, 'a'.encode(enc), 0, 1, 'ouch'))
        for s in ('\ud800', '\udfff', '\ud800\udfff'):
            with self.subTest(str=s):
                self.assertRaises(UnicodeEncodeError, surrogatepass_errors,
                    UnicodeEncodeError('ascii', s, 0, len(s), 'ouch'))
        tests = [('utf-8', '\ud800', b'\xed\xa0\x80', 3), ('utf-16le',
            '\ud800', b'\x00\xd8', 2), ('utf-16be', '\ud800', b'\xd8\x00', 
            2), ('utf-32le', '\ud800', b'\x00\xd8\x00\x00', 4), ('utf-32be',
            '\ud800', b'\x00\x00\xd8\x00', 4), ('utf-8', '\udfff',
            b'\xed\xbf\xbf', 3), ('utf-16le', '\udfff', b'\xff\xdf', 2), (
            'utf-16be', '\udfff', b'\xdf\xff', 2), ('utf-32le', '\udfff',
            b'\xff\xdf\x00\x00', 4), ('utf-32be', '\udfff',
            b'\x00\x00\xdf\xff', 4), ('utf-8', '\ud800\udfff',
            b'\xed\xa0\x80\xed\xbf\xbf', 3), ('utf-16le', '\ud800\udfff',
            b'\x00\xd8\xff\xdf', 2), ('utf-16be', '\ud800\udfff',
            b'\xd8\x00\xdf\xff', 2), ('utf-32le', '\ud800\udfff',
            b'\x00\xd8\x00\x00\xff\xdf\x00\x00', 4), ('utf-32be',
            '\ud800\udfff', b'\x00\x00\xd8\x00\x00\x00\xdf\xff', 4)]
        for enc, s, b, n in tests:
            with self.subTest(encoding=enc, str=s, bytes=b):
                self.assertEqual(surrogatepass_errors(UnicodeEncodeError(
                    enc, 'a' + s + 'b', 1, 1 + len(s), 'ouch')), (b, 1 +
                    len(s)))
                self.assertEqual(surrogatepass_errors(UnicodeDecodeError(
                    enc, bytearray(b'a' + b[:n] + b'b'), 1, 1 + n, 'ouch')),
                    (s[:1], 1 + n))

    def test_badhandlerresults(self):
        results = 42, 'foo', (1, 2, 3), ('foo', 1, 3), ('foo', None), ('foo',
            ), ('foo', 1, 3), ('foo', None), ('foo',)
        encs = 'ascii', 'latin-1', 'iso-8859-1', 'iso-8859-15'
        for res in results:
            codecs.register_error('test.badhandler', lambda x: res)
            for enc in encs:
                self.assertRaises(TypeError, 'あ'.encode, enc, 'test.badhandler'
                    )
            for enc, bytes in (('ascii', b'\xff'), ('utf-8', b'\xff'), (
                'utf-7', b'+x-'), ('unicode-internal', b'\x00')):
                with test.support.check_warnings():
                    self.assertRaises(TypeError, bytes.decode, enc,
                        'test.badhandler')

    def test_lookup(self):
        self.assertEqual(codecs.strict_errors, codecs.lookup_error('strict'))
        self.assertEqual(codecs.ignore_errors, codecs.lookup_error('ignore'))
        self.assertEqual(codecs.strict_errors, codecs.lookup_error('strict'))
        self.assertEqual(codecs.xmlcharrefreplace_errors, codecs.
            lookup_error('xmlcharrefreplace'))
        self.assertEqual(codecs.backslashreplace_errors, codecs.
            lookup_error('backslashreplace'))
        self.assertEqual(codecs.namereplace_errors, codecs.lookup_error(
            'namereplace'))

    def test_unencodablereplacement(self):

        def unencrepl(exc):
            if isinstance(exc, UnicodeEncodeError):
                return '䉂', exc.end
            else:
                raise TypeError("don't know how to handle %r" % exc)
        codecs.register_error('test.unencreplhandler', unencrepl)
        for enc in ('ascii', 'iso-8859-1', 'iso-8859-15'):
            self.assertRaises(UnicodeEncodeError, '䉂'.encode, enc,
                'test.unencreplhandler')

    def test_badregistercall(self):
        self.assertRaises(TypeError, codecs.register_error, 42)
        self.assertRaises(TypeError, codecs.register_error, 'test.dummy', 42)

    def test_badlookupcall(self):
        self.assertRaises(TypeError, codecs.lookup_error)

    def test_unknownhandler(self):
        self.assertRaises(LookupError, codecs.lookup_error, 'test.unknown')

    def test_xmlcharrefvalues(self):
        v = (1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 
            500000, 1000000)
        s = ''.join([chr(x) for x in v])
        codecs.register_error('test.xmlcharrefreplace', codecs.
            xmlcharrefreplace_errors)
        for enc in ('ascii', 'iso-8859-15'):
            for err in ('xmlcharrefreplace', 'test.xmlcharrefreplace'):
                s.encode(enc, err)

    def test_decodehelper(self):
        self.assertRaises(LookupError, b'\xff'.decode, 'ascii', 'test.unknown')

        def baddecodereturn1(exc):
            return 42
        codecs.register_error('test.baddecodereturn1', baddecodereturn1)
        self.assertRaises(TypeError, b'\xff'.decode, 'ascii',
            'test.baddecodereturn1')
        self.assertRaises(TypeError, b'\\'.decode, 'unicode-escape',
            'test.baddecodereturn1')
        self.assertRaises(TypeError, b'\\x0'.decode, 'unicode-escape',
            'test.baddecodereturn1')
        self.assertRaises(TypeError, b'\\x0y'.decode, 'unicode-escape',
            'test.baddecodereturn1')
        self.assertRaises(TypeError, b'\\Uffffeeee'.decode,
            'unicode-escape', 'test.baddecodereturn1')
        self.assertRaises(TypeError, b'\\uyyyy'.decode,
            'raw-unicode-escape', 'test.baddecodereturn1')

        def baddecodereturn2(exc):
            return '?', None
        codecs.register_error('test.baddecodereturn2', baddecodereturn2)
        self.assertRaises(TypeError, b'\xff'.decode, 'ascii',
            'test.baddecodereturn2')
        handler = PosReturn()
        codecs.register_error('test.posreturn', handler.handle)
        handler.pos = -1
        self.assertEqual(b'\xff0'.decode('ascii', 'test.posreturn'), '<?>0')
        handler.pos = -2
        self.assertEqual(b'\xff0'.decode('ascii', 'test.posreturn'), '<?><?>')
        handler.pos = -3
        self.assertRaises(IndexError, b'\xff0'.decode, 'ascii',
            'test.posreturn')
        handler.pos = 1
        self.assertEqual(b'\xff0'.decode('ascii', 'test.posreturn'), '<?>0')
        handler.pos = 2
        self.assertEqual(b'\xff0'.decode('ascii', 'test.posreturn'), '<?>')
        handler.pos = 3
        self.assertRaises(IndexError, b'\xff0'.decode, 'ascii',
            'test.posreturn')
        handler.pos = 6
        self.assertEqual(b'\\uyyyy0'.decode('raw-unicode-escape',
            'test.posreturn'), '<?>0')


        class D(dict):

            def __getitem__(self, key):
                raise ValueError
        self.assertRaises(UnicodeError, codecs.charmap_decode, b'\xff',
            'strict', {(255): None})
        self.assertRaises(ValueError, codecs.charmap_decode, b'\xff',
            'strict', D())
        self.assertRaises(TypeError, codecs.charmap_decode, b'\xff',
            'strict', {(255): sys.maxunicode + 1})

    def test_encodehelper(self):
        self.assertRaises(LookupError, 'ÿ'.encode, 'ascii', 'test.unknown')

        def badencodereturn1(exc):
            return 42
        codecs.register_error('test.badencodereturn1', badencodereturn1)
        self.assertRaises(TypeError, 'ÿ'.encode, 'ascii',
            'test.badencodereturn1')

        def badencodereturn2(exc):
            return '?', None
        codecs.register_error('test.badencodereturn2', badencodereturn2)
        self.assertRaises(TypeError, 'ÿ'.encode, 'ascii',
            'test.badencodereturn2')
        handler = PosReturn()
        codecs.register_error('test.posreturn', handler.handle)
        handler.pos = -1
        self.assertEqual('ÿ0'.encode('ascii', 'test.posreturn'), b'<?>0')
        handler.pos = -2
        self.assertEqual('ÿ0'.encode('ascii', 'test.posreturn'), b'<?><?>')
        handler.pos = -3
        self.assertRaises(IndexError, 'ÿ0'.encode, 'ascii', 'test.posreturn')
        handler.pos = 1
        self.assertEqual('ÿ0'.encode('ascii', 'test.posreturn'), b'<?>0')
        handler.pos = 2
        self.assertEqual('ÿ0'.encode('ascii', 'test.posreturn'), b'<?>')
        handler.pos = 3
        self.assertRaises(IndexError, 'ÿ0'.encode, 'ascii', 'test.posreturn')
        handler.pos = 0


        class D(dict):

            def __getitem__(self, key):
                raise ValueError
        for err in ('strict', 'replace', 'xmlcharrefreplace',
            'backslashreplace', 'namereplace', 'test.posreturn'):
            self.assertRaises(UnicodeError, codecs.charmap_encode, 'ÿ', err,
                {(255): None})
            self.assertRaises(ValueError, codecs.charmap_encode, 'ÿ', err, D())
            self.assertRaises(TypeError, codecs.charmap_encode, 'ÿ', err, {
                (255): 300})

    def test_translatehelper(self):


        class D(dict):

            def __getitem__(self, key):
                raise ValueError
        self.assertRaises(ValueError, 'ÿ'.translate, {(255): sys.maxunicode +
            1})
        self.assertRaises(TypeError, 'ÿ'.translate, {(255): ()})

    def test_bug828737(self):
        charmap = {ord('&'): '&amp;', ord('<'): '&lt;', ord('>'): '&gt;',
            ord('"'): '&quot;'}
        for n in (1, 10, 100, 1000):
            text = 'abc<def>ghi' * n
            text.translate(charmap)

    def test_mutatingdecodehandler(self):
        baddata = [('ascii', b'\xff'), ('utf-7', b'++'), ('utf-8', b'\xff'),
            ('utf-16', b'\xff'), ('utf-32', b'\xff'), ('unicode-escape',
            b'\\u123g'), ('raw-unicode-escape', b'\\u123g'), (
            'unicode-internal', b'\xff')]

        def replacing(exc):
            if isinstance(exc, UnicodeDecodeError):
                exc.object = 42
                return '䉂', 0
            else:
                raise TypeError("don't know how to handle %r" % exc)
        codecs.register_error('test.replacing', replacing)
        with test.support.check_warnings():
            for encoding, data in baddata:
                with self.assertRaises(TypeError):
                    data.decode(encoding, 'test.replacing')

        def mutating(exc):
            if isinstance(exc, UnicodeDecodeError):
                exc.object[:] = b''
                return '䉂', 0
            else:
                raise TypeError("don't know how to handle %r" % exc)
        codecs.register_error('test.mutating', mutating)
        with test.support.check_warnings():
            for encoding, data in baddata:
                with self.assertRaises(TypeError):
                    data.decode(encoding, 'test.replacing')

    def test_fake_error_class(self):
        handlers = [codecs.strict_errors, codecs.ignore_errors, codecs.
            replace_errors, codecs.backslashreplace_errors, codecs.
            namereplace_errors, codecs.xmlcharrefreplace_errors, codecs.
            lookup_error('surrogateescape'), codecs.lookup_error(
            'surrogatepass')]
        for cls in (UnicodeEncodeError, UnicodeDecodeError,
            UnicodeTranslateError):


            class FakeUnicodeError(str):
                __class__ = cls
            for handler in handlers:
                with self.subTest(handler=handler, error_class=cls):
                    self.assertRaises(TypeError, handler, FakeUnicodeError())


            class FakeUnicodeError(Exception):
                __class__ = cls
            for handler in handlers:
                with self.subTest(handler=handler, error_class=cls):
                    with self.assertRaises((TypeError, FakeUnicodeError)):
                        handler(FakeUnicodeError())


if __name__ == '__main__':
    unittest.main()
