import codecs
import contextlib
import io
import locale
import sys
import unittest
import encodings
from test import support
try:
    import ctypes
except ImportError:
    ctypes = None
    SIZEOF_WCHAR_T = -1
else:
    SIZEOF_WCHAR_T = ctypes.sizeof(ctypes.c_wchar)


def coding_checker(self, coder):

    def check(input, expect):
        self.assertEqual(coder(input), (expect, len(input)))
    return check


class Queue(object):
    """
    queue: write bytes at one end, read bytes from the other end
    """

    def __init__(self, buffer):
        self._buffer = buffer

    def write(self, chars):
        self._buffer += chars

    def read(self, size=-1):
        if size < 0:
            s = self._buffer
            self._buffer = self._buffer[:0]
            return s
        else:
            s = self._buffer[:size]
            self._buffer = self._buffer[size:]
            return s


class MixInCheckStateHandling:

    def check_state_handling_decode(self, encoding, u, s):
        for i in range(len(s) + 1):
            d = codecs.getincrementaldecoder(encoding)()
            part1 = d.decode(s[:i])
            state = d.getstate()
            self.assertIsInstance(state[1], int)
            if not state[1]:
                d.setstate((state[0][:0], 0))
                self.assertTrue(not d.decode(state[0]))
                self.assertEqual(state, d.getstate())
            d = codecs.getincrementaldecoder(encoding)()
            d.setstate(state)
            part2 = d.decode(s[i:], True)
            self.assertEqual(u, part1 + part2)

    def check_state_handling_encode(self, encoding, u, s):
        for i in range(len(u) + 1):
            d = codecs.getincrementalencoder(encoding)()
            part1 = d.encode(u[:i])
            state = d.getstate()
            d = codecs.getincrementalencoder(encoding)()
            d.setstate(state)
            part2 = d.encode(u[i:], True)
            self.assertEqual(s, part1 + part2)


class ReadTest(MixInCheckStateHandling):

    def check_partial(self, input, partialresults):
        q = Queue(b'')
        r = codecs.getreader(self.encoding)(q)
        result = ''
        for c, partialresult in zip(input.encode(self.encoding), partialresults
            ):
            q.write(bytes([c]))
            result += r.read()
            self.assertEqual(result, partialresult)
        self.assertEqual(r.read(), '')
        self.assertEqual(r.bytebuffer, b'')
        d = codecs.getincrementaldecoder(self.encoding)()
        result = ''
        for c, partialresult in zip(input.encode(self.encoding), partialresults
            ):
            result += d.decode(bytes([c]))
            self.assertEqual(result, partialresult)
        self.assertEqual(d.decode(b'', True), '')
        self.assertEqual(d.buffer, b'')
        d.reset()
        result = ''
        for c, partialresult in zip(input.encode(self.encoding), partialresults
            ):
            result += d.decode(bytes([c]))
            self.assertEqual(result, partialresult)
        self.assertEqual(d.decode(b'', True), '')
        self.assertEqual(d.buffer, b'')
        encoded = input.encode(self.encoding)
        self.assertEqual(input, ''.join(codecs.iterdecode([bytes([c]) for c in
            encoded], self.encoding)))

    def test_readline(self):

        def getreader(input):
            stream = io.BytesIO(input.encode(self.encoding))
            return codecs.getreader(self.encoding)(stream)

        def readalllines(input, keepends=True, size=None):
            reader = getreader(input)
            lines = []
            while True:
                line = reader.readline(size=size, keepends=keepends)
                if not line:
                    break
                lines.append(line)
            return '|'.join(lines)
        s = 'foo\nbar\r\nbaz\rspam\u2028eggs'
        sexpected = 'foo\n|bar\r\n|baz\r|spam\u2028|eggs'
        sexpectednoends = 'foo|bar|baz|spam|eggs'
        self.assertEqual(readalllines(s, True), sexpected)
        self.assertEqual(readalllines(s, False), sexpectednoends)
        self.assertEqual(readalllines(s, True, 10), sexpected)
        self.assertEqual(readalllines(s, False, 10), sexpectednoends)
        lineends = '\n', '\r\n', '\r', '\u2028'
        vw = []
        vwo = []
        for i, lineend in enumerate(lineends):
            vw.append((i * 200 + 200) * 'あ' + lineend)
            vwo.append((i * 200 + 200) * 'あ')
        self.assertEqual(readalllines(''.join(vw), True), '|'.join(vw))
        self.assertEqual(readalllines(''.join(vw), False), '|'.join(vwo))
        for size in range(80):
            for lineend in lineends:
                s = 10 * (size * 'a' + lineend + 'xxx\n')
                reader = getreader(s)
                for i in range(10):
                    self.assertEqual(reader.readline(keepends=True), size *
                        'a' + lineend)
                    self.assertEqual(reader.readline(keepends=True), 'xxx\n')
                reader = getreader(s)
                for i in range(10):
                    self.assertEqual(reader.readline(keepends=False), size *
                        'a')
                    self.assertEqual(reader.readline(keepends=False), 'xxx')

    def test_mixed_readline_and_read(self):
        lines = ['Humpty Dumpty sat on a wall,\n',
            'Humpty Dumpty had a great fall.\r\n',
            "All the king's horses and all the king's men\r",
            "Couldn't put Humpty together again."]
        data = ''.join(lines)

        def getreader():
            stream = io.BytesIO(data.encode(self.encoding))
            return codecs.getreader(self.encoding)(stream)
        f = getreader()
        self.assertEqual(f.readline(), lines[0])
        self.assertEqual(f.read(), ''.join(lines[1:]))
        self.assertEqual(f.read(), '')
        f = getreader()
        self.assertEqual(f.readline(), lines[0])
        self.assertEqual(f.readlines(), lines[1:])
        self.assertEqual(f.read(), '')
        f = getreader()
        self.assertEqual(f.read(size=40, chars=5), data[:5])
        self.assertEqual(f.read(), data[5:])
        self.assertEqual(f.read(), '')
        f = getreader()
        self.assertEqual(f.read(size=40, chars=5), data[:5])
        self.assertEqual(f.readlines(), [lines[0][5:]] + lines[1:])
        self.assertEqual(f.read(), '')

    def test_bug1175396(self):
        s = ['<%!--===================================================\r\n',
            '    BLOG index page: show recent articles,\r\n',
            "    today's articles, or articles of a specific date.\r\n",
            '========================================================--%>\r\n',
            '<%@inputencoding="ISO-8859-1"%>\r\n',
            '<%@pagetemplate=TEMPLATE.y%>\r\n',
            '<%@import=import frog.util, frog%>\r\n',
            '<%@import=import frog.objects%>\r\n',
            '<%@import=from frog.storageerrors import StorageError%>\r\n',
            '<%\r\n', '\r\n', 'import logging\r\n',
            'log=logging.getLogger("Snakelets.logger")\r\n', '\r\n', '\r\n',
            'user=self.SessionCtx.user\r\n',
            'storageEngine=self.SessionCtx.storageEngine\r\n', '\r\n',
            '\r\n', 'def readArticlesFromDate(date, count=None):\r\n',
            '    entryids=storageEngine.listBlogEntries(date)\r\n',
            '    entryids.reverse() # descending\r\n', '    if count:\r\n',
            '        entryids=entryids[:count]\r\n', '    try:\r\n',
            '        return [ frog.objects.BlogEntry.load(storageEngine, date, Id) for Id in entryids ]\r\n'
            , '    except StorageError,x:\r\n',
            '        log.error("Error loading articles: "+str(x))\r\n',
            '        self.abort("cannot load articles")\r\n', '\r\n',
            'showdate=None\r\n', '\r\n', 'arg=self.Request.getArg()\r\n',
            'if arg=="today":\r\n',
            "    #-------------------- TODAY'S ARTICLES\r\n",
            '    self.write("<h2>Today\'s articles</h2>")\r\n',
            '    showdate = frog.util.isodatestr() \r\n',
            '    entries = readArticlesFromDate(showdate)\r\n',
            'elif arg=="active":\r\n',
            '    #-------------------- ACTIVE ARTICLES redirect\r\n',
            '    self.Yredirect("active.y")\r\n', 'elif arg=="login":\r\n',
            '    #-------------------- LOGIN PAGE redirect\r\n',
            '    self.Yredirect("login.y")\r\n', 'elif arg=="date":\r\n',
            '    #-------------------- ARTICLES OF A SPECIFIC DATE\r\n',
            '    showdate = self.Request.getParameter("date")\r\n',
            '    self.write("<h2>Articles written on %s</h2>"% frog.util.mediumdatestr(showdate))\r\n'
            , '    entries = readArticlesFromDate(showdate)\r\n',
            'else:\r\n', '    #-------------------- RECENT ARTICLES\r\n',
            '    self.write("<h2>Recent articles</h2>")\r\n',
            '    dates=storageEngine.listBlogEntryDates()\r\n',
            '    if dates:\r\n', '        entries=[]\r\n',
            '        SHOWAMOUNT=10\r\n',
            '        for showdate in dates:\r\n',
            '            entries.extend( readArticlesFromDate(showdate, SHOWAMOUNT-len(entries)) )\r\n'
            , '            if len(entries)>=SHOWAMOUNT:\r\n',
            '                break\r\n', '                \r\n']
        stream = io.BytesIO(''.join(s).encode(self.encoding))
        reader = codecs.getreader(self.encoding)(stream)
        for i, line in enumerate(reader):
            self.assertEqual(line, s[i])

    def test_readlinequeue(self):
        q = Queue(b'')
        writer = codecs.getwriter(self.encoding)(q)
        reader = codecs.getreader(self.encoding)(q)
        writer.write('foo\r')
        self.assertEqual(reader.readline(keepends=False), 'foo')
        writer.write('\nbar\r')
        self.assertEqual(reader.readline(keepends=False), '')
        self.assertEqual(reader.readline(keepends=False), 'bar')
        writer.write('baz')
        self.assertEqual(reader.readline(keepends=False), 'baz')
        self.assertEqual(reader.readline(keepends=False), '')
        writer.write('foo\r')
        self.assertEqual(reader.readline(keepends=True), 'foo\r')
        writer.write('\nbar\r')
        self.assertEqual(reader.readline(keepends=True), '\n')
        self.assertEqual(reader.readline(keepends=True), 'bar\r')
        writer.write('baz')
        self.assertEqual(reader.readline(keepends=True), 'baz')
        self.assertEqual(reader.readline(keepends=True), '')
        writer.write('foo\r\n')
        self.assertEqual(reader.readline(keepends=True), 'foo\r\n')

    def test_bug1098990_a(self):
        s1 = (
            'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy\r\n'
            )
        s2 = (
            'offending line: ladfj askldfj klasdj fskla dfzaskdj fasklfj laskd fjasklfzzzzaa%whereisthis!!!\r\n'
            )
        s3 = 'next line.\r\n'
        s = (s1 + s2 + s3).encode(self.encoding)
        stream = io.BytesIO(s)
        reader = codecs.getreader(self.encoding)(stream)
        self.assertEqual(reader.readline(), s1)
        self.assertEqual(reader.readline(), s2)
        self.assertEqual(reader.readline(), s3)
        self.assertEqual(reader.readline(), '')

    def test_bug1098990_b(self):
        s1 = 'aaaaaaaaaaaaaaaaaaaaaaaa\r\n'
        s2 = 'bbbbbbbbbbbbbbbbbbbbbbbb\r\n'
        s3 = 'stillokay:bbbbxx\r\n'
        s4 = 'broken!!!!badbad\r\n'
        s5 = 'againokay.\r\n'
        s = (s1 + s2 + s3 + s4 + s5).encode(self.encoding)
        stream = io.BytesIO(s)
        reader = codecs.getreader(self.encoding)(stream)
        self.assertEqual(reader.readline(), s1)
        self.assertEqual(reader.readline(), s2)
        self.assertEqual(reader.readline(), s3)
        self.assertEqual(reader.readline(), s4)
        self.assertEqual(reader.readline(), s5)
        self.assertEqual(reader.readline(), '')
    ill_formed_sequence_replace = '�'

    def test_lone_surrogates(self):
        self.assertRaises(UnicodeEncodeError, '\ud800'.encode, self.encoding)
        self.assertEqual('[\udc80]'.encode(self.encoding,
            'backslashreplace'), '[\\udc80]'.encode(self.encoding))
        self.assertEqual('[\udc80]'.encode(self.encoding, 'namereplace'),
            '[\\udc80]'.encode(self.encoding))
        self.assertEqual('[\udc80]'.encode(self.encoding,
            'xmlcharrefreplace'), '[&#56448;]'.encode(self.encoding))
        self.assertEqual('[\udc80]'.encode(self.encoding, 'ignore'), '[]'.
            encode(self.encoding))
        self.assertEqual('[\udc80]'.encode(self.encoding, 'replace'), '[?]'
            .encode(self.encoding))
        self.assertEqual('[\ud800\udc80]'.encode(self.encoding, 'ignore'),
            '[]'.encode(self.encoding))
        self.assertEqual('[\ud800\udc80]'.encode(self.encoding, 'replace'),
            '[??]'.encode(self.encoding))
        bom = ''.encode(self.encoding)
        for before, after in [('\U00010fff', 'A'), ('[', ']'), ('A',
            '\U00010fff')]:
            before_sequence = before.encode(self.encoding)[len(bom):]
            after_sequence = after.encode(self.encoding)[len(bom):]
            test_string = before + '\udc80' + after
            test_sequence = (bom + before_sequence + self.
                ill_formed_sequence + after_sequence)
            self.assertRaises(UnicodeDecodeError, test_sequence.decode,
                self.encoding)
            self.assertEqual(test_string.encode(self.encoding,
                'surrogatepass'), test_sequence)
            self.assertEqual(test_sequence.decode(self.encoding,
                'surrogatepass'), test_string)
            self.assertEqual(test_sequence.decode(self.encoding, 'ignore'),
                before + after)
            self.assertEqual(test_sequence.decode(self.encoding, 'replace'),
                before + self.ill_formed_sequence_replace + after)
            backslashreplace = ''.join('\\x%02x' % b for b in self.
                ill_formed_sequence)
            self.assertEqual(test_sequence.decode(self.encoding,
                'backslashreplace'), before + backslashreplace + after)


class UTF32Test(ReadTest, unittest.TestCase):
    encoding = 'utf-32'
    if sys.byteorder == 'little':
        ill_formed_sequence = b'\x80\xdc\x00\x00'
    else:
        ill_formed_sequence = b'\x00\x00\xdc\x80'
    spamle = (
        b'\xff\xfe\x00\x00s\x00\x00\x00p\x00\x00\x00a\x00\x00\x00m\x00\x00\x00s\x00\x00\x00p\x00\x00\x00a\x00\x00\x00m\x00\x00\x00'
        )
    spambe = (
        b'\x00\x00\xfe\xff\x00\x00\x00s\x00\x00\x00p\x00\x00\x00a\x00\x00\x00m\x00\x00\x00s\x00\x00\x00p\x00\x00\x00a\x00\x00\x00m'
        )

    def test_only_one_bom(self):
        _, _, reader, writer = codecs.lookup(self.encoding)
        s = io.BytesIO()
        f = writer(s)
        f.write('spam')
        f.write('spam')
        d = s.getvalue()
        self.assertTrue(d == self.spamle or d == self.spambe)
        s = io.BytesIO(d)
        f = reader(s)
        self.assertEqual(f.read(), 'spamspam')

    def test_badbom(self):
        s = io.BytesIO(4 * b'\xff')
        f = codecs.getreader(self.encoding)(s)
        self.assertRaises(UnicodeError, f.read)
        s = io.BytesIO(8 * b'\xff')
        f = codecs.getreader(self.encoding)(s)
        self.assertRaises(UnicodeError, f.read)

    def test_partial(self):
        self.check_partial('\x00ÿĀ\uffff𐀀', ['', '', '', '', '', '', '',
            '\x00', '\x00', '\x00', '\x00', '\x00ÿ', '\x00ÿ', '\x00ÿ',
            '\x00ÿ', '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ\uffff',
            '\x00ÿĀ\uffff', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff𐀀'])

    def test_handlers(self):
        self.assertEqual(('�', 1), codecs.utf_32_decode(b'\x01', 'replace',
            True))
        self.assertEqual(('', 1), codecs.utf_32_decode(b'\x01', 'ignore', True)
            )

    def test_errors(self):
        self.assertRaises(UnicodeDecodeError, codecs.utf_32_decode, b'\xff',
            'strict', True)

    def test_decoder_state(self):
        self.check_state_handling_decode(self.encoding, 'spamspam', self.spamle
            )
        self.check_state_handling_decode(self.encoding, 'spamspam', self.spambe
            )

    def test_issue8941(self):
        encoded_le = b'\xff\xfe\x00\x00' + b'\x00\x00\x01\x00' * 1024
        self.assertEqual('𐀀' * 1024, codecs.utf_32_decode(encoded_le)[0])
        encoded_be = b'\x00\x00\xfe\xff' + b'\x00\x01\x00\x00' * 1024
        self.assertEqual('𐀀' * 1024, codecs.utf_32_decode(encoded_be)[0])


class UTF32LETest(ReadTest, unittest.TestCase):
    encoding = 'utf-32-le'
    ill_formed_sequence = b'\x80\xdc\x00\x00'

    def test_partial(self):
        self.check_partial('\x00ÿĀ\uffff𐀀', ['', '', '', '\x00', '\x00',
            '\x00', '\x00', '\x00ÿ', '\x00ÿ', '\x00ÿ', '\x00ÿ', '\x00ÿĀ',
            '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff',
            '\x00ÿĀ\uffff', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff𐀀'])

    def test_simple(self):
        self.assertEqual('\U00010203'.encode(self.encoding),
            b'\x03\x02\x01\x00')

    def test_errors(self):
        self.assertRaises(UnicodeDecodeError, codecs.utf_32_le_decode,
            b'\xff', 'strict', True)

    def test_issue8941(self):
        encoded = b'\x00\x00\x01\x00' * 1024
        self.assertEqual('𐀀' * 1024, codecs.utf_32_le_decode(encoded)[0])


class UTF32BETest(ReadTest, unittest.TestCase):
    encoding = 'utf-32-be'
    ill_formed_sequence = b'\x00\x00\xdc\x80'

    def test_partial(self):
        self.check_partial('\x00ÿĀ\uffff𐀀', ['', '', '', '\x00', '\x00',
            '\x00', '\x00', '\x00ÿ', '\x00ÿ', '\x00ÿ', '\x00ÿ', '\x00ÿĀ',
            '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff',
            '\x00ÿĀ\uffff', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff𐀀'])

    def test_simple(self):
        self.assertEqual('\U00010203'.encode(self.encoding),
            b'\x00\x01\x02\x03')

    def test_errors(self):
        self.assertRaises(UnicodeDecodeError, codecs.utf_32_be_decode,
            b'\xff', 'strict', True)

    def test_issue8941(self):
        encoded = b'\x00\x01\x00\x00' * 1024
        self.assertEqual('𐀀' * 1024, codecs.utf_32_be_decode(encoded)[0])


class UTF16Test(ReadTest, unittest.TestCase):
    encoding = 'utf-16'
    if sys.byteorder == 'little':
        ill_formed_sequence = b'\x80\xdc'
    else:
        ill_formed_sequence = b'\xdc\x80'
    spamle = b'\xff\xfes\x00p\x00a\x00m\x00s\x00p\x00a\x00m\x00'
    spambe = b'\xfe\xff\x00s\x00p\x00a\x00m\x00s\x00p\x00a\x00m'

    def test_only_one_bom(self):
        _, _, reader, writer = codecs.lookup(self.encoding)
        s = io.BytesIO()
        f = writer(s)
        f.write('spam')
        f.write('spam')
        d = s.getvalue()
        self.assertTrue(d == self.spamle or d == self.spambe)
        s = io.BytesIO(d)
        f = reader(s)
        self.assertEqual(f.read(), 'spamspam')

    def test_badbom(self):
        s = io.BytesIO(b'\xff\xff')
        f = codecs.getreader(self.encoding)(s)
        self.assertRaises(UnicodeError, f.read)
        s = io.BytesIO(b'\xff\xff\xff\xff')
        f = codecs.getreader(self.encoding)(s)
        self.assertRaises(UnicodeError, f.read)

    def test_partial(self):
        self.check_partial('\x00ÿĀ\uffff𐀀', ['', '', '', '\x00', '\x00',
            '\x00ÿ', '\x00ÿ', '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ\uffff',
            '\x00ÿĀ\uffff', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff𐀀'])

    def test_handlers(self):
        self.assertEqual(('�', 1), codecs.utf_16_decode(b'\x01', 'replace',
            True))
        self.assertEqual(('', 1), codecs.utf_16_decode(b'\x01', 'ignore', True)
            )

    def test_errors(self):
        self.assertRaises(UnicodeDecodeError, codecs.utf_16_decode, b'\xff',
            'strict', True)

    def test_decoder_state(self):
        self.check_state_handling_decode(self.encoding, 'spamspam', self.spamle
            )
        self.check_state_handling_decode(self.encoding, 'spamspam', self.spambe
            )

    def test_bug691291(self):
        s1 = 'Hello\r\nworld\r\n'
        s = s1.encode(self.encoding)
        self.addCleanup(support.unlink, support.TESTFN)
        with open(support.TESTFN, 'wb') as fp:
            fp.write(s)
        with support.check_warnings(('', DeprecationWarning)):
            reader = codecs.open(support.TESTFN, 'U', encoding=self.encoding)
        with reader:
            self.assertEqual(reader.read(), s1)


class UTF16LETest(ReadTest, unittest.TestCase):
    encoding = 'utf-16-le'
    ill_formed_sequence = b'\x80\xdc'

    def test_partial(self):
        self.check_partial('\x00ÿĀ\uffff𐀀', ['', '\x00', '\x00', '\x00ÿ',
            '\x00ÿ', '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff',
            '\x00ÿĀ\uffff', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff𐀀'])

    def test_errors(self):
        tests = [(b'\xff', '�'), (b'A\x00Z', 'A�'), (
            b'A\x00B\x00C\x00D\x00Z', 'ABCD�'), (b'\x00\xd8', '�'), (
            b'\x00\xd8A', '�'), (b'\x00\xd8A\x00', '�A'), (b'\x00\xdcA\x00',
            '�A')]
        for raw, expected in tests:
            self.assertRaises(UnicodeDecodeError, codecs.utf_16_le_decode,
                raw, 'strict', True)
            self.assertEqual(raw.decode('utf-16le', 'replace'), expected)

    def test_nonbmp(self):
        self.assertEqual('\U00010203'.encode(self.encoding),
            b'\x00\xd8\x03\xde')
        self.assertEqual(b'\x00\xd8\x03\xde'.decode(self.encoding),
            '\U00010203')


class UTF16BETest(ReadTest, unittest.TestCase):
    encoding = 'utf-16-be'
    ill_formed_sequence = b'\xdc\x80'

    def test_partial(self):
        self.check_partial('\x00ÿĀ\uffff𐀀', ['', '\x00', '\x00', '\x00ÿ',
            '\x00ÿ', '\x00ÿĀ', '\x00ÿĀ', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff',
            '\x00ÿĀ\uffff', '\x00ÿĀ\uffff', '\x00ÿĀ\uffff𐀀'])

    def test_errors(self):
        tests = [(b'\xff', '�'), (b'\x00A\xff', 'A�'), (
            b'\x00A\x00B\x00C\x00DZ', 'ABCD�'), (b'\xd8\x00', '�'), (
            b'\xd8\x00\xdc', '�'), (b'\xd8\x00\x00A', '�A'), (
            b'\xdc\x00\x00A', '�A')]
        for raw, expected in tests:
            self.assertRaises(UnicodeDecodeError, codecs.utf_16_be_decode,
                raw, 'strict', True)
            self.assertEqual(raw.decode('utf-16be', 'replace'), expected)

    def test_nonbmp(self):
        self.assertEqual('\U00010203'.encode(self.encoding),
            b'\xd8\x00\xde\x03')
        self.assertEqual(b'\xd8\x00\xde\x03'.decode(self.encoding),
            '\U00010203')


class UTF8Test(ReadTest, unittest.TestCase):
    encoding = 'utf-8'
    ill_formed_sequence = b'\xed\xb2\x80'
    ill_formed_sequence_replace = '�' * 3
    BOM = b''

    def test_partial(self):
        self.check_partial('\x00ÿ\u07ffࠀ\uffff𐀀', ['\x00', '\x00', '\x00ÿ',
            '\x00ÿ', '\x00ÿ\u07ff', '\x00ÿ\u07ff', '\x00ÿ\u07ff',
            '\x00ÿ\u07ffࠀ', '\x00ÿ\u07ffࠀ', '\x00ÿ\u07ffࠀ',
            '\x00ÿ\u07ffࠀ\uffff', '\x00ÿ\u07ffࠀ\uffff',
            '\x00ÿ\u07ffࠀ\uffff', '\x00ÿ\u07ffࠀ\uffff', '\x00ÿ\u07ffࠀ\uffff𐀀'])

    def test_decoder_state(self):
        u = '\x00\x7f\x80ÿĀ\u07ffࠀ\uffff\U0010ffff'
        self.check_state_handling_decode(self.encoding, u, u.encode(self.
            encoding))

    def test_decode_error(self):
        for data, error_handler, expected in ((b'[\x80\xff]', 'ignore',
            '[]'), (b'[\x80\xff]', 'replace', '[��]'), (b'[\x80\xff]',
            'surrogateescape', '[\udc80\udcff]'), (b'[\x80\xff]',
            'backslashreplace', '[\\x80\\xff]')):
            with self.subTest(data=data, error_handler=error_handler,
                expected=expected):
                self.assertEqual(data.decode(self.encoding, error_handler),
                    expected)

    def test_lone_surrogates(self):
        super().test_lone_surrogates()
        self.assertEqual('[\udc80]'.encode(self.encoding, 'surrogateescape'
            ), self.BOM + b'[\x80]')
        with self.assertRaises(UnicodeEncodeError) as cm:
            '[\udc80\ud800\udfff]'.encode(self.encoding, 'surrogateescape')
        exc = cm.exception
        self.assertEqual(exc.object[exc.start:exc.end], '\ud800\udfff')

    def test_surrogatepass_handler(self):
        self.assertEqual('abc\ud800def'.encode(self.encoding,
            'surrogatepass'), self.BOM + b'abc\xed\xa0\x80def')
        self.assertEqual('\U00010fff\ud800'.encode(self.encoding,
            'surrogatepass'), self.BOM + b'\xf0\x90\xbf\xbf\xed\xa0\x80')
        self.assertEqual('[\ud800\udc80]'.encode(self.encoding,
            'surrogatepass'), self.BOM + b'[\xed\xa0\x80\xed\xb2\x80]')
        self.assertEqual(b'abc\xed\xa0\x80def'.decode(self.encoding,
            'surrogatepass'), 'abc\ud800def')
        self.assertEqual(b'\xf0\x90\xbf\xbf\xed\xa0\x80'.decode(self.
            encoding, 'surrogatepass'), '\U00010fff\ud800')
        self.assertTrue(codecs.lookup_error('surrogatepass'))
        with self.assertRaises(UnicodeDecodeError):
            b'abc\xed\xa0'.decode(self.encoding, 'surrogatepass')
        with self.assertRaises(UnicodeDecodeError):
            b'abc\xed\xa0z'.decode(self.encoding, 'surrogatepass')


@unittest.skipUnless(sys.platform == 'win32', 'cp65001 is a Windows-only codec'
    )
class CP65001Test(ReadTest, unittest.TestCase):
    encoding = 'cp65001'

    def test_encode(self):
        tests = [('abc', 'strict', b'abc'), ('é€', 'strict',
            b'\xc3\xa9\xe2\x82\xac'), ('\U0010ffff', 'strict',
            b'\xf4\x8f\xbf\xbf'), ('\udc80', 'strict', None), ('\udc80',
            'ignore', b''), ('\udc80', 'replace', b'?'), ('\udc80',
            'backslashreplace', b'\\udc80'), ('\udc80', 'namereplace',
            b'\\udc80'), ('\udc80', 'surrogatepass', b'\xed\xb2\x80')]
        for text, errors, expected in tests:
            if expected is not None:
                try:
                    encoded = text.encode('cp65001', errors)
                except UnicodeEncodeError as err:
                    self.fail(
                        'Unable to encode %a to cp65001 with errors=%r: %s' %
                        (text, errors, err))
                self.assertEqual(encoded, expected, 
                    '%a.encode("cp65001", %r)=%a != %a' % (text, errors,
                    encoded, expected))
            else:
                self.assertRaises(UnicodeEncodeError, text.encode,
                    'cp65001', errors)

    def test_decode(self):
        tests = [(b'abc', 'strict', 'abc'), (b'\xc3\xa9\xe2\x82\xac',
            'strict', 'é€'), (b'\xf4\x8f\xbf\xbf', 'strict', '\U0010ffff'),
            (b'\xef\xbf\xbd', 'strict', '�'), (b'[\xc3\xa9]', 'strict',
            '[é]'), (b'[\xff]', 'strict', None), (b'[\xff]', 'ignore', '[]'
            ), (b'[\xff]', 'replace', '[�]'), (b'[\xff]', 'surrogateescape',
            '[\udcff]'), (b'[\xed\xb2\x80]', 'strict', None), (
            b'[\xed\xb2\x80]', 'ignore', '[]'), (b'[\xed\xb2\x80]',
            'replace', '[���]')]
        for raw, errors, expected in tests:
            if expected is not None:
                try:
                    decoded = raw.decode('cp65001', errors)
                except UnicodeDecodeError as err:
                    self.fail(
                        'Unable to decode %a from cp65001 with errors=%r: %s' %
                        (raw, errors, err))
                self.assertEqual(decoded, expected, 
                    '%a.decode("cp65001", %r)=%a != %a' % (raw, errors,
                    decoded, expected))
            else:
                self.assertRaises(UnicodeDecodeError, raw.decode, 'cp65001',
                    errors)

    def test_lone_surrogates(self):
        self.assertRaises(UnicodeEncodeError, '\ud800'.encode, 'cp65001')
        self.assertRaises(UnicodeDecodeError, b'\xed\xa0\x80'.decode, 'cp65001'
            )
        self.assertEqual('[\udc80]'.encode('cp65001', 'backslashreplace'),
            b'[\\udc80]')
        self.assertEqual('[\udc80]'.encode('cp65001', 'namereplace'),
            b'[\\udc80]')
        self.assertEqual('[\udc80]'.encode('cp65001', 'xmlcharrefreplace'),
            b'[&#56448;]')
        self.assertEqual('[\udc80]'.encode('cp65001', 'surrogateescape'),
            b'[\x80]')
        self.assertEqual('[\udc80]'.encode('cp65001', 'ignore'), b'[]')
        self.assertEqual('[\udc80]'.encode('cp65001', 'replace'), b'[?]')

    def test_surrogatepass_handler(self):
        self.assertEqual('abc\ud800def'.encode('cp65001', 'surrogatepass'),
            b'abc\xed\xa0\x80def')
        self.assertEqual(b'abc\xed\xa0\x80def'.decode('cp65001',
            'surrogatepass'), 'abc\ud800def')
        self.assertEqual('\U00010fff\ud800'.encode('cp65001',
            'surrogatepass'), b'\xf0\x90\xbf\xbf\xed\xa0\x80')
        self.assertEqual(b'\xf0\x90\xbf\xbf\xed\xa0\x80'.decode('cp65001',
            'surrogatepass'), '\U00010fff\ud800')
        self.assertTrue(codecs.lookup_error('surrogatepass'))


class UTF7Test(ReadTest, unittest.TestCase):
    encoding = 'utf-7'

    def test_ascii(self):
        set_d = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'(),-./:?"
            )
        self.assertEqual(set_d.encode(self.encoding), set_d.encode('ascii'))
        self.assertEqual(set_d.encode('ascii').decode(self.encoding), set_d)
        set_o = ' !"#$%&*;<=>@[]^_`{|}'
        self.assertEqual(set_o.encode(self.encoding), set_o.encode('ascii'))
        self.assertEqual(set_o.encode('ascii').decode(self.encoding), set_o)
        self.assertEqual('a+b'.encode(self.encoding), b'a+-b')
        self.assertEqual(b'a+-b'.decode(self.encoding), 'a+b')
        ws = ' \t\n\r'
        self.assertEqual(ws.encode(self.encoding), ws.encode('ascii'))
        self.assertEqual(ws.encode('ascii').decode(self.encoding), ws)
        other_ascii = ''.join(sorted(set(bytes(range(128)).decode()) - set(
            set_d + set_o + '+' + ws)))
        self.assertEqual(other_ascii.encode(self.encoding),
            b'+AAAAAQACAAMABAAFAAYABwAIAAsADAAOAA8AEAARABIAEwAUABUAFgAXABgAGQAaABsAHAAdAB4AHwBcAH4Afw-'
            )

    def test_partial(self):
        self.check_partial('a+-b\x00c\x80dĀe𐀀f', ['a', 'a', 'a+', 'a+-',
            'a+-b', 'a+-b', 'a+-b', 'a+-b', 'a+-b', 'a+-b\x00', 'a+-b\x00c',
            'a+-b\x00c', 'a+-b\x00c', 'a+-b\x00c', 'a+-b\x00c',
            'a+-b\x00c\x80', 'a+-b\x00c\x80d', 'a+-b\x00c\x80d',
            'a+-b\x00c\x80d', 'a+-b\x00c\x80d', 'a+-b\x00c\x80d',
            'a+-b\x00c\x80dĀ', 'a+-b\x00c\x80dĀe', 'a+-b\x00c\x80dĀe',
            'a+-b\x00c\x80dĀe', 'a+-b\x00c\x80dĀe', 'a+-b\x00c\x80dĀe',
            'a+-b\x00c\x80dĀe', 'a+-b\x00c\x80dĀe', 'a+-b\x00c\x80dĀe',
            'a+-b\x00c\x80dĀe𐀀', 'a+-b\x00c\x80dĀe𐀀f'])

    def test_errors(self):
        tests = [(b'\xffb', '�b'), (b'a\xffb', 'a�b'), (b'a\xff\xffb',
            'a��b'), (b'a+IK', 'a�'), (b'a+IK-b', 'a�b'), (b'a+IK,b', 'a�b'
            ), (b'a+IKx', 'a€�'), (b'a+IKx-b', 'a€�b'), (b'a+IKwgr', 'a€�'),
            (b'a+IKwgr-b', 'a€�b'), (b'a+IKwgr,', 'a€�'), (b'a+IKwgr,-b',
            'a€�-b'), (b'a+IKwgrB', 'a€€�'), (b'a+IKwgrB-b', 'a€€�b'), (
            b'a+/,+IKw-b', 'a�€b'), (b'a+//,+IKw-b', 'a�€b'), (
            b'a+///,+IKw-b', 'a\uffff�€b'), (b'a+////,+IKw-b', 'a\uffff�€b'
            ), (b'a+IKw-b\xff', 'a€b�'), (b'a+IKw\xffb', 'a€�b')]
        for raw, expected in tests:
            with self.subTest(raw=raw):
                self.assertRaises(UnicodeDecodeError, codecs.utf_7_decode,
                    raw, 'strict', True)
                self.assertEqual(raw.decode('utf-7', 'replace'), expected)

    def test_nonbmp(self):
        self.assertEqual('𐒠'.encode(self.encoding), b'+2AHcoA-')
        self.assertEqual('\ud801\udca0'.encode(self.encoding), b'+2AHcoA-')
        self.assertEqual(b'+2AHcoA-'.decode(self.encoding), '𐒠')
        self.assertEqual(b'+2AHcoA'.decode(self.encoding), '𐒠')
        self.assertEqual('€𐒠'.encode(self.encoding), b'+IKzYAdyg-')
        self.assertEqual(b'+IKzYAdyg-'.decode(self.encoding), '€𐒠')
        self.assertEqual(b'+IKzYAdyg'.decode(self.encoding), '€𐒠')
        self.assertEqual('€€𐒠'.encode(self.encoding), b'+IKwgrNgB3KA-')
        self.assertEqual(b'+IKwgrNgB3KA-'.decode(self.encoding), '€€𐒠')
        self.assertEqual(b'+IKwgrNgB3KA'.decode(self.encoding), '€€𐒠')

    def test_lone_surrogates(self):
        tests = [(b'a+2AE-b', 'a\ud801b'), (b'a+2AE\xffb', 'a�b'), (
            b'a+2AE', 'a�'), (b'a+2AEA-b', 'a�b'), (b'a+2AH-b', 'a�b'), (
            b'a+IKzYAQ-b', 'a€\ud801b'), (b'a+IKzYAQ\xffb', 'a€�b'), (
            b'a+IKzYAQA-b', 'a€�b'), (b'a+IKzYAd-b', 'a€�b'), (
            b'a+IKwgrNgB-b', 'a€€\ud801b'), (b'a+IKwgrNgB\xffb', 'a€€�b'),
            (b'a+IKwgrNgB', 'a€€�'), (b'a+IKwgrNgBA-b', 'a€€�b')]
        for raw, expected in tests:
            with self.subTest(raw=raw):
                self.assertEqual(raw.decode('utf-7', 'replace'), expected)


class UTF16ExTest(unittest.TestCase):

    def test_errors(self):
        self.assertRaises(UnicodeDecodeError, codecs.utf_16_ex_decode,
            b'\xff', 'strict', 0, True)

    def test_bad_args(self):
        self.assertRaises(TypeError, codecs.utf_16_ex_decode)


class ReadBufferTest(unittest.TestCase):

    def test_array(self):
        import array
        self.assertEqual(codecs.readbuffer_encode(array.array('b', b'spam')
            ), (b'spam', 4))

    def test_empty(self):
        self.assertEqual(codecs.readbuffer_encode(''), (b'', 0))

    def test_bad_args(self):
        self.assertRaises(TypeError, codecs.readbuffer_encode)
        self.assertRaises(TypeError, codecs.readbuffer_encode, 42)


class UTF8SigTest(UTF8Test, unittest.TestCase):
    encoding = 'utf-8-sig'
    BOM = codecs.BOM_UTF8

    def test_partial(self):
        self.check_partial('\ufeff\x00ÿ\u07ffࠀ\uffff𐀀', ['', '', '', '', '',
            '\ufeff', '\ufeff\x00', '\ufeff\x00', '\ufeff\x00ÿ',
            '\ufeff\x00ÿ', '\ufeff\x00ÿ\u07ff', '\ufeff\x00ÿ\u07ff',
            '\ufeff\x00ÿ\u07ff', '\ufeff\x00ÿ\u07ffࠀ', '\ufeff\x00ÿ\u07ffࠀ',
            '\ufeff\x00ÿ\u07ffࠀ', '\ufeff\x00ÿ\u07ffࠀ\uffff',
            '\ufeff\x00ÿ\u07ffࠀ\uffff', '\ufeff\x00ÿ\u07ffࠀ\uffff',
            '\ufeff\x00ÿ\u07ffࠀ\uffff', '\ufeff\x00ÿ\u07ffࠀ\uffff𐀀'])

    def test_bug1601501(self):
        self.assertEqual(str(b'\xef\xbb\xbf', 'utf-8-sig'), '')

    def test_bom(self):
        d = codecs.getincrementaldecoder('utf-8-sig')()
        s = 'spam'
        self.assertEqual(d.decode(s.encode('utf-8-sig')), s)

    def test_stream_bom(self):
        unistring = 'ABC¡∀XYZ'
        bytestring = codecs.BOM_UTF8 + b'ABC\xc2\xa1\xe2\x88\x80XYZ'
        reader = codecs.getreader('utf-8-sig')
        for sizehint in ([None] + list(range(1, 11)) + [64, 128, 256, 512, 
            1024]):
            istream = reader(io.BytesIO(bytestring))
            ostream = io.StringIO()
            while 1:
                if sizehint is not None:
                    data = istream.read(sizehint)
                else:
                    data = istream.read()
                if not data:
                    break
                ostream.write(data)
            got = ostream.getvalue()
            self.assertEqual(got, unistring)

    def test_stream_bare(self):
        unistring = 'ABC¡∀XYZ'
        bytestring = b'ABC\xc2\xa1\xe2\x88\x80XYZ'
        reader = codecs.getreader('utf-8-sig')
        for sizehint in ([None] + list(range(1, 11)) + [64, 128, 256, 512, 
            1024]):
            istream = reader(io.BytesIO(bytestring))
            ostream = io.StringIO()
            while 1:
                if sizehint is not None:
                    data = istream.read(sizehint)
                else:
                    data = istream.read()
                if not data:
                    break
                ostream.write(data)
            got = ostream.getvalue()
            self.assertEqual(got, unistring)


class EscapeDecodeTest(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(codecs.escape_decode(b''), (b'', 0))
        self.assertEqual(codecs.escape_decode(bytearray()), (b'', 0))

    def test_raw(self):
        decode = codecs.escape_decode
        for b in range(256):
            b = bytes([b])
            if b != b'\\':
                self.assertEqual(decode(b + b'0'), (b + b'0', 2))

    def test_escape(self):
        decode = codecs.escape_decode
        check = coding_checker(self, decode)
        check(b'[\\\n]', b'[]')
        check(b'[\\"]', b'["]')
        check(b"[\\']", b"[']")
        check(b'[\\\\]', b'[\\]')
        check(b'[\\a]', b'[\x07]')
        check(b'[\\b]', b'[\x08]')
        check(b'[\\t]', b'[\t]')
        check(b'[\\n]', b'[\n]')
        check(b'[\\v]', b'[\x0b]')
        check(b'[\\f]', b'[\x0c]')
        check(b'[\\r]', b'[\r]')
        check(b'[\\7]', b'[\x07]')
        check(b'[\\78]', b'[\x078]')
        check(b'[\\41]', b'[!]')
        check(b'[\\418]', b'[!8]')
        check(b'[\\101]', b'[A]')
        check(b'[\\1010]', b'[A0]')
        check(b'[\\501]', b'[A]')
        check(b'[\\x41]', b'[A]')
        check(b'[\\x410]', b'[A0]')
        for i in range(97, 123):
            b = bytes([i])
            if b not in b'abfnrtvx':
                with self.assertWarns(DeprecationWarning):
                    check(b'\\' + b, b'\\' + b)
            with self.assertWarns(DeprecationWarning):
                check(b'\\' + b.upper(), b'\\' + b.upper())
        with self.assertWarns(DeprecationWarning):
            check(b'\\8', b'\\8')
        with self.assertWarns(DeprecationWarning):
            check(b'\\9', b'\\9')

    def test_errors(self):
        decode = codecs.escape_decode
        self.assertRaises(ValueError, decode, b'\\x')
        self.assertRaises(ValueError, decode, b'[\\x]')
        self.assertEqual(decode(b'[\\x]\\x', 'ignore'), (b'[]', 6))
        self.assertEqual(decode(b'[\\x]\\x', 'replace'), (b'[?]?', 6))
        self.assertRaises(ValueError, decode, b'\\x0')
        self.assertRaises(ValueError, decode, b'[\\x0]')
        self.assertEqual(decode(b'[\\x0]\\x0', 'ignore'), (b'[]', 8))
        self.assertEqual(decode(b'[\\x0]\\x0', 'replace'), (b'[?]?', 8))


class RecodingTest(unittest.TestCase):

    def test_recoding(self):
        f = io.BytesIO()
        f2 = codecs.EncodedFile(f, 'unicode_internal', 'utf-8')
        f2.write('a')
        f2.close()
        self.assertTrue(f.closed)


punycode_testcases = [('ليهمابتكلموشعربي؟', b'egbpdaj6bu4bxfgehfvwxn'), (
    '他们为什么不说中文', b'ihqwcrb4cv8a8dqg056pqjye'), ('他們爲什麽不說中文',
    b'ihqwctvzc91f659drss3x8bo0yb'), ('Pročprostěnemluvíčesky',
    b'Proprostnemluvesky-uyb24dma41a'), ('למההםפשוטלאמדבריםעברית',
    b'4dbcagdahymbxekheh6e0a7fei0b'), ('यहलोगहिन्दीक्योंनहींबोलसकतेहैं',
    b'i1baa7eci9glrd9b2ae1bj0hfcgg6iyaf8o0a1dig0cd'), ('なぜみんな日本語を話してくれないのか',
    b'n8jok5ay5dzabd5bym9f0cm5685rrjetr6pdxa'), ('세계의모든사람들이한국어를이해한다면얼마나좋을까',
    b'989aomsvi5e83db1d2a355cv1e0vak1dwrv93d5xbh15a0dt30a5jpsd879ccm6fea98c'
    ), ('почемужеонинеговорятпорусски', b'b1abfaaepdrnnbgefbaDotcwatmq2g4l'
    ), ('PorquénopuedensimplementehablarenEspañol',
    b'PorqunopuedensimplementehablarenEspaol-fmd56a'), (
    'TạisaohọkhôngthểchỉnóitiếngViệt',
    b'TisaohkhngthchnitingVit-kjcr8268qyxafd2f1b9g'), ('3年B組金八先生',
    b'3B-ww4c5e180e575a65lsy2b'), ('安室奈美恵-with-SUPER-MONKEYS',
    b'-with-SUPER-MONKEYS-pc58ag80a8qai00g7n9n'), (
    'Hello-Another-Way-それぞれの場所',
    b'Hello-Another-Way--fc4qua05auwb3674vfr0b'), ('ひとつ屋根の下2',
    b'2-u9tlzr9756bt3uc0v'), ('MajiでKoiする5秒前',
    b'MajiKoi5-783gue6qz075azm5e'), ('パフィーdeルンバ', b'de-jg4avhby1noc0d'), (
    'そのスピードで', b'd9juau41awczczp'), ('-> $1.00 <-', b'-> $1.00 <--')]
for i in punycode_testcases:
    if len(i) != 2:
        print(repr(i))


class PunycodeTest(unittest.TestCase):

    def test_encode(self):
        for uni, puny in punycode_testcases:
            self.assertEqual(str(uni.encode('punycode'), 'ascii').lower(),
                str(puny, 'ascii').lower())

    def test_decode(self):
        for uni, puny in punycode_testcases:
            self.assertEqual(uni, puny.decode('punycode'))
            puny = puny.decode('ascii').encode('ascii')
            self.assertEqual(uni, puny.decode('punycode'))


class UnicodeInternalTest(unittest.TestCase):

    @unittest.skipUnless(SIZEOF_WCHAR_T == 4, 'specific to 32-bit wchar_t')
    def test_bug1251300(self):
        ok = [(b'\x00\x10\xff\xff', '\U0010ffff'), (b'\x00\x00\x01\x01',
            'ā'), (b'', '')]
        not_ok = [b'\x7f\xff\xff\xff', b'\x80\x00\x00\x00',
            b'\x81\x00\x00\x00', b'\x00', b'\x00\x00\x00\x00\x00']
        for internal, uni in ok:
            if sys.byteorder == 'little':
                internal = bytes(reversed(internal))
            with support.check_warnings():
                self.assertEqual(uni, internal.decode('unicode_internal'))
        for internal in not_ok:
            if sys.byteorder == 'little':
                internal = bytes(reversed(internal))
            with support.check_warnings((
                'unicode_internal codec has been deprecated',
                DeprecationWarning)):
                self.assertRaises(UnicodeDecodeError, internal.decode,
                    'unicode_internal')
        if sys.byteorder == 'little':
            invalid = b'\x00\x00\x11\x00'
            invalid_backslashreplace = '\\x00\\x00\\x11\\x00'
        else:
            invalid = b'\x00\x11\x00\x00'
            invalid_backslashreplace = '\\x00\\x11\\x00\\x00'
        with support.check_warnings():
            self.assertRaises(UnicodeDecodeError, invalid.decode,
                'unicode_internal')
        with support.check_warnings():
            self.assertEqual(invalid.decode('unicode_internal', 'replace'), '�'
                )
        with support.check_warnings():
            self.assertEqual(invalid.decode('unicode_internal',
                'backslashreplace'), invalid_backslashreplace)

    @unittest.skipUnless(SIZEOF_WCHAR_T == 4, 'specific to 32-bit wchar_t')
    def test_decode_error_attributes(self):
        try:
            with support.check_warnings((
                'unicode_internal codec has been deprecated',
                DeprecationWarning)):
                b'\x00\x00\x00\x00\x00\x11\x11\x00'.decode('unicode_internal')
        except UnicodeDecodeError as ex:
            self.assertEqual('unicode_internal', ex.encoding)
            self.assertEqual(b'\x00\x00\x00\x00\x00\x11\x11\x00', ex.object)
            self.assertEqual(4, ex.start)
            self.assertEqual(8, ex.end)
        else:
            self.fail()

    @unittest.skipUnless(SIZEOF_WCHAR_T == 4, 'specific to 32-bit wchar_t')
    def test_decode_callback(self):
        codecs.register_error('UnicodeInternalTest', codecs.ignore_errors)
        decoder = codecs.getdecoder('unicode_internal')
        with support.check_warnings((
            'unicode_internal codec has been deprecated', DeprecationWarning)):
            ab = 'ab'.encode('unicode_internal').decode()
            ignored = decoder(bytes('%s""""%s' % (ab[:4], ab[4:]), 'ascii'),
                'UnicodeInternalTest')
        self.assertEqual(('ab', 12), ignored)

    def test_encode_length(self):
        with support.check_warnings((
            'unicode_internal codec has been deprecated', DeprecationWarning)):
            encoder = codecs.getencoder('unicode_internal')
            self.assertEqual(encoder('a')[1], 1)
            self.assertEqual(encoder('éł')[1], 2)
            self.assertEqual(codecs.escape_encode(b'\\x00')[1], 4)


nameprep_tests = [(
    b'foo\xc2\xad\xcd\x8f\xe1\xa0\x86\xe1\xa0\x8bbar\xe2\x80\x8b\xe2\x81\xa0baz\xef\xb8\x80\xef\xb8\x88\xef\xb8\x8f\xef\xbb\xbf'
    , b'foobarbaz'), (b'CAFE', b'cafe'), (b'\xc3\x9f', b'ss'), (b'\xc4\xb0',
    b'i\xcc\x87'), (b'\xc5\x83\xcd\xba', b'\xc5\x84 \xce\xb9'), (None, None
    ), (b'j\xcc\x8c\xc2\xa0\xc2\xaa', b'\xc7\xb0 a'), (b'\xe1\xbe\xb7',
    b'\xe1\xbe\xb6\xce\xb9'), (b'\xc7\xb0', b'\xc7\xb0'), (b'\xce\x90',
    b'\xce\x90'), (b'\xce\xb0', b'\xce\xb0'), (b'\xe1\xba\x96',
    b'\xe1\xba\x96'), (b'\xe1\xbd\x96', b'\xe1\xbd\x96'), (b' ', b' '), (
    b'\xc2\xa0', b' '), (b'\xe1\x9a\x80', None), (b'\xe2\x80\x80', b' '), (
    b'\xe2\x80\x8b', b''), (b'\xe3\x80\x80', b' '), (b'\x10\x7f',
    b'\x10\x7f'), (b'\xc2\x85', None), (b'\xe1\xa0\x8e', None), (
    b'\xef\xbb\xbf', b''), (b'\xf0\x9d\x85\xb5', None), (b'\xef\x84\xa3',
    None), (b'\xf3\xb1\x88\xb4', None), (b'\xf4\x8f\x88\xb4', None), (
    b'\xf2\x8f\xbf\xbe', None), (b'\xf4\x8f\xbf\xbf', None), (
    b'\xed\xbd\x82', None), (b'\xef\xbf\xbd', None), (b'\xe2\xbf\xb5', None
    ), (b'\xcd\x81', b'\xcc\x81'), (b'\xe2\x80\x8e', None), (
    b'\xe2\x80\xaa', None), (b'\xf3\xa0\x80\x81', None), (
    b'\xf3\xa0\x81\x82', None), (b'foo\xd6\xbebar', None), (
    b'foo\xef\xb5\x90bar', None), (b'foo\xef\xb9\xb6bar',
    b'foo \xd9\x8ebar'), (b'\xd8\xa71', None), (b'\xd8\xa71\xd8\xa8',
    b'\xd8\xa71\xd8\xa8'), (None, None), (
    b'X\xc2\xad\xc3\x9f\xc4\xb0\xe2\x84\xa1j\xcc\x8c\xc2\xa0\xc2\xaa\xce\xb0\xe2\x80\x80'
    , b'xssi\xcc\x87tel\xc7\xb0 a\xce\xb0 '), (
    b'X\xc3\x9f\xe3\x8c\x96\xc4\xb0\xe2\x84\xa1\xe2\x92\x9f\xe3\x8c\x80',
    b'xss\xe3\x82\xad\xe3\x83\xad\xe3\x83\xa1\xe3\x83\xbc\xe3\x83\x88\xe3\x83\xabi\xcc\x87tel(d)\xe3\x82\xa2\xe3\x83\x91\xe3\x83\xbc\xe3\x83\x88'
    )]


class NameprepTest(unittest.TestCase):

    def test_nameprep(self):
        from encodings.idna import nameprep
        for pos, (orig, prepped) in enumerate(nameprep_tests):
            if orig is None:
                continue
            orig = str(orig, 'utf-8', 'surrogatepass')
            if prepped is None:
                self.assertRaises(UnicodeError, nameprep, orig)
            else:
                prepped = str(prepped, 'utf-8', 'surrogatepass')
                try:
                    self.assertEqual(nameprep(orig), prepped)
                except Exception as e:
                    raise support.TestFailed('Test 3.%d: %s' % (pos + 1,
                        str(e)))


class IDNACodecTest(unittest.TestCase):

    def test_builtin_decode(self):
        self.assertEqual(str(b'python.org', 'idna'), 'python.org')
        self.assertEqual(str(b'python.org.', 'idna'), 'python.org.')
        self.assertEqual(str(b'xn--pythn-mua.org', 'idna'), 'pythön.org')
        self.assertEqual(str(b'xn--pythn-mua.org.', 'idna'), 'pythön.org.')

    def test_builtin_encode(self):
        self.assertEqual('python.org'.encode('idna'), b'python.org')
        self.assertEqual('python.org.'.encode('idna'), b'python.org.')
        self.assertEqual('pythön.org'.encode('idna'), b'xn--pythn-mua.org')
        self.assertEqual('pythön.org.'.encode('idna'), b'xn--pythn-mua.org.')

    def test_stream(self):
        r = codecs.getreader('idna')(io.BytesIO(b'abc'))
        r.read(3)
        self.assertEqual(r.read(), '')

    def test_incremental_decode(self):
        self.assertEqual(''.join(codecs.iterdecode((bytes([c]) for c in
            b'python.org'), 'idna')), 'python.org')
        self.assertEqual(''.join(codecs.iterdecode((bytes([c]) for c in
            b'python.org.'), 'idna')), 'python.org.')
        self.assertEqual(''.join(codecs.iterdecode((bytes([c]) for c in
            b'xn--pythn-mua.org.'), 'idna')), 'pythön.org.')
        self.assertEqual(''.join(codecs.iterdecode((bytes([c]) for c in
            b'xn--pythn-mua.org.'), 'idna')), 'pythön.org.')
        decoder = codecs.getincrementaldecoder('idna')()
        self.assertEqual(decoder.decode(b'xn--xam'), '')
        self.assertEqual(decoder.decode(b'ple-9ta.o'), 'äxample.')
        self.assertEqual(decoder.decode(b'rg'), '')
        self.assertEqual(decoder.decode(b'', True), 'org')
        decoder.reset()
        self.assertEqual(decoder.decode(b'xn--xam'), '')
        self.assertEqual(decoder.decode(b'ple-9ta.o'), 'äxample.')
        self.assertEqual(decoder.decode(b'rg.'), 'org.')
        self.assertEqual(decoder.decode(b'', True), '')

    def test_incremental_encode(self):
        self.assertEqual(b''.join(codecs.iterencode('python.org', 'idna')),
            b'python.org')
        self.assertEqual(b''.join(codecs.iterencode('python.org.', 'idna')),
            b'python.org.')
        self.assertEqual(b''.join(codecs.iterencode('pythön.org.', 'idna')),
            b'xn--pythn-mua.org.')
        self.assertEqual(b''.join(codecs.iterencode('pythön.org.', 'idna')),
            b'xn--pythn-mua.org.')
        encoder = codecs.getincrementalencoder('idna')()
        self.assertEqual(encoder.encode('äx'), b'')
        self.assertEqual(encoder.encode('ample.org'), b'xn--xample-9ta.')
        self.assertEqual(encoder.encode('', True), b'org')
        encoder.reset()
        self.assertEqual(encoder.encode('äx'), b'')
        self.assertEqual(encoder.encode('ample.org.'), b'xn--xample-9ta.org.')
        self.assertEqual(encoder.encode('', True), b'')

    def test_errors(self):
        """Only supports "strict" error handler"""
        """python.org""".encode('idna', 'strict')
        b'python.org'.decode('idna', 'strict')
        for errors in ('ignore', 'replace', 'backslashreplace',
            'surrogateescape'):
            self.assertRaises(Exception, 'python.org'.encode, 'idna', errors)
            self.assertRaises(Exception, b'python.org'.decode, 'idna', errors)


class CodecsModuleTest(unittest.TestCase):

    def test_decode(self):
        self.assertEqual(codecs.decode(b'\xe4\xf6\xfc', 'latin-1'), 'äöü')
        self.assertRaises(TypeError, codecs.decode)
        self.assertEqual(codecs.decode(b'abc'), 'abc')
        self.assertRaises(UnicodeDecodeError, codecs.decode, b'\xff', 'ascii')
        self.assertEqual(codecs.decode(obj=b'\xe4\xf6\xfc', encoding=
            'latin-1'), 'äöü')
        self.assertEqual(codecs.decode(b'[\xff]', 'ascii', errors='ignore'),
            '[]')

    def test_encode(self):
        self.assertEqual(codecs.encode('äöü', 'latin-1'), b'\xe4\xf6\xfc')
        self.assertRaises(TypeError, codecs.encode)
        self.assertRaises(LookupError, codecs.encode, 'foo', '__spam__')
        self.assertEqual(codecs.encode('abc'), b'abc')
        self.assertRaises(UnicodeEncodeError, codecs.encode, 'ÿff', 'ascii')
        self.assertEqual(codecs.encode(obj='äöü', encoding='latin-1'),
            b'\xe4\xf6\xfc')
        self.assertEqual(codecs.encode('[ÿ]', 'ascii', errors='ignore'), b'[]')

    def test_register(self):
        self.assertRaises(TypeError, codecs.register)
        self.assertRaises(TypeError, codecs.register, 42)

    def test_lookup(self):
        self.assertRaises(TypeError, codecs.lookup)
        self.assertRaises(LookupError, codecs.lookup, '__spam__')
        self.assertRaises(LookupError, codecs.lookup, ' ')

    def test_getencoder(self):
        self.assertRaises(TypeError, codecs.getencoder)
        self.assertRaises(LookupError, codecs.getencoder, '__spam__')

    def test_getdecoder(self):
        self.assertRaises(TypeError, codecs.getdecoder)
        self.assertRaises(LookupError, codecs.getdecoder, '__spam__')

    def test_getreader(self):
        self.assertRaises(TypeError, codecs.getreader)
        self.assertRaises(LookupError, codecs.getreader, '__spam__')

    def test_getwriter(self):
        self.assertRaises(TypeError, codecs.getwriter)
        self.assertRaises(LookupError, codecs.getwriter, '__spam__')

    def test_lookup_issue1813(self):
        oldlocale = locale.setlocale(locale.LC_CTYPE)
        self.addCleanup(locale.setlocale, locale.LC_CTYPE, oldlocale)
        try:
            locale.setlocale(locale.LC_CTYPE, 'tr_TR')
        except locale.Error:
            self.skipTest('test needs Turkish locale')
        c = codecs.lookup('ASCII')
        self.assertEqual(c.name, 'ascii')

    def test_all(self):
        api = ('encode', 'decode', 'register', 'CodecInfo', 'Codec',
            'IncrementalEncoder', 'IncrementalDecoder', 'StreamReader',
            'StreamWriter', 'lookup', 'getencoder', 'getdecoder',
            'getincrementalencoder', 'getincrementaldecoder', 'getreader',
            'getwriter', 'register_error', 'lookup_error', 'strict_errors',
            'replace_errors', 'ignore_errors', 'xmlcharrefreplace_errors',
            'backslashreplace_errors', 'namereplace_errors', 'open',
            'EncodedFile', 'iterencode', 'iterdecode', 'BOM', 'BOM_BE',
            'BOM_LE', 'BOM_UTF8', 'BOM_UTF16', 'BOM_UTF16_BE',
            'BOM_UTF16_LE', 'BOM_UTF32', 'BOM_UTF32_BE', 'BOM_UTF32_LE',
            'BOM32_BE', 'BOM32_LE', 'BOM64_BE', 'BOM64_LE',
            'StreamReaderWriter', 'StreamRecoder')
        self.assertCountEqual(api, codecs.__all__)
        for api in codecs.__all__:
            getattr(codecs, api)

    def test_open(self):
        self.addCleanup(support.unlink, support.TESTFN)
        for mode in ('w', 'r', 'r+', 'w+', 'a', 'a+'):
            with self.subTest(mode), codecs.open(support.TESTFN, mode, 'ascii'
                ) as file:
                self.assertIsInstance(file, codecs.StreamReaderWriter)

    def test_undefined(self):
        self.assertRaises(UnicodeError, codecs.encode, 'abc', 'undefined')
        self.assertRaises(UnicodeError, codecs.decode, b'abc', 'undefined')
        self.assertRaises(UnicodeError, codecs.encode, '', 'undefined')
        self.assertRaises(UnicodeError, codecs.decode, b'', 'undefined')
        for errors in ('strict', 'ignore', 'replace', 'backslashreplace'):
            self.assertRaises(UnicodeError, codecs.encode, 'abc',
                'undefined', errors)
            self.assertRaises(UnicodeError, codecs.decode, b'abc',
                'undefined', errors)


class StreamReaderTest(unittest.TestCase):

    def setUp(self):
        self.reader = codecs.getreader('utf-8')
        self.stream = io.BytesIO(b'\xed\x95\x9c\n\xea\xb8\x80')

    def test_readlines(self):
        f = self.reader(self.stream)
        self.assertEqual(f.readlines(), ['한\n', '글'])


class EncodedFileTest(unittest.TestCase):

    def test_basic(self):
        f = io.BytesIO(b'\xed\x95\x9c\n\xea\xb8\x80')
        ef = codecs.EncodedFile(f, 'utf-16-le', 'utf-8')
        self.assertEqual(ef.read(), b'\\\xd5\n\x00\x00\xae')
        f = io.BytesIO()
        ef = codecs.EncodedFile(f, 'utf-8', 'latin-1')
        ef.write(b'\xc3\xbc')
        self.assertEqual(f.getvalue(), b'\xfc')


all_unicode_encodings = ['ascii', 'big5', 'big5hkscs', 'charmap', 'cp037',
    'cp1006', 'cp1026', 'cp1125', 'cp1140', 'cp1250', 'cp1251', 'cp1252',
    'cp1253', 'cp1254', 'cp1255', 'cp1256', 'cp1257', 'cp1258', 'cp424',
    'cp437', 'cp500', 'cp720', 'cp737', 'cp775', 'cp850', 'cp852', 'cp855',
    'cp856', 'cp857', 'cp858', 'cp860', 'cp861', 'cp862', 'cp863', 'cp864',
    'cp865', 'cp866', 'cp869', 'cp874', 'cp875', 'cp932', 'cp949', 'cp950',
    'euc_jis_2004', 'euc_jisx0213', 'euc_jp', 'euc_kr', 'gb18030', 'gb2312',
    'gbk', 'hp_roman8', 'hz', 'idna', 'iso2022_jp', 'iso2022_jp_1',
    'iso2022_jp_2', 'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext',
    'iso2022_kr', 'iso8859_1', 'iso8859_10', 'iso8859_11', 'iso8859_13',
    'iso8859_14', 'iso8859_15', 'iso8859_16', 'iso8859_2', 'iso8859_3',
    'iso8859_4', 'iso8859_5', 'iso8859_6', 'iso8859_7', 'iso8859_8',
    'iso8859_9', 'johab', 'koi8_r', 'koi8_t', 'koi8_u', 'kz1048', 'latin_1',
    'mac_cyrillic', 'mac_greek', 'mac_iceland', 'mac_latin2', 'mac_roman',
    'mac_turkish', 'palmos', 'ptcp154', 'punycode', 'raw_unicode_escape',
    'shift_jis', 'shift_jis_2004', 'shift_jisx0213', 'tis_620',
    'unicode_escape', 'unicode_internal', 'utf_16', 'utf_16_be',
    'utf_16_le', 'utf_7', 'utf_8']
if hasattr(codecs, 'mbcs_encode'):
    all_unicode_encodings.append('mbcs')
if hasattr(codecs, 'oem_encode'):
    all_unicode_encodings.append('oem')
broken_unicode_with_stateful = ['punycode', 'unicode_internal']


class BasicUnicodeTest(unittest.TestCase, MixInCheckStateHandling):

    def test_basics(self):
        s = 'abc123'
        for encoding in all_unicode_encodings:
            name = codecs.lookup(encoding).name
            if encoding.endswith('_codec'):
                name += '_codec'
            elif encoding == 'latin_1':
                name = 'latin_1'
            self.assertEqual(encoding.replace('_', '-'), name.replace('_', '-')
                )
            with support.check_warnings():
                b, size = codecs.getencoder(encoding)(s)
                self.assertEqual(size, len(s), 'encoding=%r' % encoding)
                chars, size = codecs.getdecoder(encoding)(b)
                self.assertEqual(chars, s, 'encoding=%r' % encoding)
            if encoding not in broken_unicode_with_stateful:
                q = Queue(b'')
                writer = codecs.getwriter(encoding)(q)
                encodedresult = b''
                for c in s:
                    writer.write(c)
                    chunk = q.read()
                    self.assertTrue(type(chunk) is bytes, type(chunk))
                    encodedresult += chunk
                q = Queue(b'')
                reader = codecs.getreader(encoding)(q)
                decodedresult = ''
                for c in encodedresult:
                    q.write(bytes([c]))
                    decodedresult += reader.read()
                self.assertEqual(decodedresult, s, 'encoding=%r' % encoding)
            if encoding not in broken_unicode_with_stateful:
                try:
                    encoder = codecs.getincrementalencoder(encoding)()
                except LookupError:
                    pass
                else:
                    encodedresult = b''
                    for c in s:
                        encodedresult += encoder.encode(c)
                    encodedresult += encoder.encode('', True)
                    decoder = codecs.getincrementaldecoder(encoding)()
                    decodedresult = ''
                    for c in encodedresult:
                        decodedresult += decoder.decode(bytes([c]))
                    decodedresult += decoder.decode(b'', True)
                    self.assertEqual(decodedresult, s, 'encoding=%r' % encoding
                        )
                    result = ''.join(codecs.iterdecode(codecs.iterencode(s,
                        encoding), encoding))
                    self.assertEqual(result, s, 'encoding=%r' % encoding)
                    result = ''.join(codecs.iterdecode(codecs.iterencode('',
                        encoding), encoding))
                    self.assertEqual(result, '')
                if encoding not in ('idna', 'mbcs'):
                    try:
                        encoder = codecs.getincrementalencoder(encoding)(
                            'ignore')
                    except LookupError:
                        pass
                    else:
                        encodedresult = b''.join(encoder.encode(c) for c in s)
                        decoder = codecs.getincrementaldecoder(encoding)(
                            'ignore')
                        decodedresult = ''.join(decoder.decode(bytes([c])) for
                            c in encodedresult)
                        self.assertEqual(decodedresult, s, 'encoding=%r' %
                            encoding)

    @support.cpython_only
    def test_basics_capi(self):
        from _testcapi import codec_incrementalencoder, codec_incrementaldecoder
        s = 'abc123'
        for encoding in all_unicode_encodings:
            if encoding not in broken_unicode_with_stateful:
                try:
                    cencoder = codec_incrementalencoder(encoding)
                except LookupError:
                    pass
                else:
                    encodedresult = b''
                    for c in s:
                        encodedresult += cencoder.encode(c)
                    encodedresult += cencoder.encode('', True)
                    cdecoder = codec_incrementaldecoder(encoding)
                    decodedresult = ''
                    for c in encodedresult:
                        decodedresult += cdecoder.decode(bytes([c]))
                    decodedresult += cdecoder.decode(b'', True)
                    self.assertEqual(decodedresult, s, 'encoding=%r' % encoding
                        )
                if encoding not in ('idna', 'mbcs'):
                    try:
                        cencoder = codec_incrementalencoder(encoding, 'ignore')
                    except LookupError:
                        pass
                    else:
                        encodedresult = b''.join(cencoder.encode(c) for c in s)
                        cdecoder = codec_incrementaldecoder(encoding, 'ignore')
                        decodedresult = ''.join(cdecoder.decode(bytes([c])) for
                            c in encodedresult)
                        self.assertEqual(decodedresult, s, 'encoding=%r' %
                            encoding)

    def test_seek(self):
        s = '%s\n%s\n' % (100 * 'abc123', 100 * 'def456')
        for encoding in all_unicode_encodings:
            if encoding == 'idna':
                continue
            if encoding in broken_unicode_with_stateful:
                continue
            reader = codecs.getreader(encoding)(io.BytesIO(s.encode(encoding)))
            for t in range(5):
                reader.seek(0, 0)
                data = reader.read()
                self.assertEqual(s, data)

    def test_bad_decode_args(self):
        for encoding in all_unicode_encodings:
            decoder = codecs.getdecoder(encoding)
            self.assertRaises(TypeError, decoder)
            if encoding not in ('idna', 'punycode'):
                self.assertRaises(TypeError, decoder, 42)

    def test_bad_encode_args(self):
        for encoding in all_unicode_encodings:
            encoder = codecs.getencoder(encoding)
            with support.check_warnings():
                self.assertRaises(TypeError, encoder)

    def test_encoding_map_type_initialized(self):
        from encodings import cp1140
        table_type = type(cp1140.encoding_table)
        self.assertEqual(table_type, table_type)

    def test_decoder_state(self):
        u = 'abc123'
        for encoding in all_unicode_encodings:
            if encoding not in broken_unicode_with_stateful:
                self.check_state_handling_decode(encoding, u, u.encode(
                    encoding))
                self.check_state_handling_encode(encoding, u, u.encode(
                    encoding))


class CharmapTest(unittest.TestCase):

    def test_decode_with_string_map(self):
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'strict',
            'abc'), ('abc', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'strict',
            '\U0010ffffbc'), ('\U0010ffffbc', 3))
        self.assertRaises(UnicodeDecodeError, codecs.charmap_decode,
            b'\x00\x01\x02', 'strict', 'ab')
        self.assertRaises(UnicodeDecodeError, codecs.charmap_decode,
            b'\x00\x01\x02', 'strict', 'ab\ufffe')
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'replace',
            'ab'), ('ab�', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'replace',
            'ab\ufffe'), ('ab�', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02',
            'backslashreplace', 'ab'), ('ab\\x02', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02',
            'backslashreplace', 'ab\ufffe'), ('ab\\x02', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'ignore',
            'ab'), ('ab', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'ignore',
            'ab\ufffe'), ('ab', 3))
        allbytes = bytes(range(256))
        self.assertEqual(codecs.charmap_decode(allbytes, 'ignore', ''), ('',
            len(allbytes)))

    def test_decode_with_int2str_map(self):
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'strict', {
            (0): 'a', (1): 'b', (2): 'c'}), ('abc', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'strict', {
            (0): 'Aa', (1): 'Bb', (2): 'Cc'}), ('AaBbCc', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'strict', {
            (0): '\U0010ffff', (1): 'b', (2): 'c'}), ('\U0010ffffbc', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'strict', {
            (0): 'a', (1): 'b', (2): ''}), ('ab', 3))
        self.assertRaises(UnicodeDecodeError, codecs.charmap_decode,
            b'\x00\x01\x02', 'strict', {(0): 'a', (1): 'b'})
        self.assertRaises(UnicodeDecodeError, codecs.charmap_decode,
            b'\x00\x01\x02', 'strict', {(0): 'a', (1): 'b', (2): None})
        self.assertRaises(UnicodeDecodeError, codecs.charmap_decode,
            b'\x00\x01\x02', 'strict', {(0): 'a', (1): 'b', (2): '\ufffe'})
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'replace',
            {(0): 'a', (1): 'b'}), ('ab�', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'replace',
            {(0): 'a', (1): 'b', (2): None}), ('ab�', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'replace',
            {(0): 'a', (1): 'b', (2): '\ufffe'}), ('ab�', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02',
            'backslashreplace', {(0): 'a', (1): 'b'}), ('ab\\x02', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02',
            'backslashreplace', {(0): 'a', (1): 'b', (2): None}), (
            'ab\\x02', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02',
            'backslashreplace', {(0): 'a', (1): 'b', (2): '\ufffe'}), (
            'ab\\x02', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'ignore', {
            (0): 'a', (1): 'b'}), ('ab', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'ignore', {
            (0): 'a', (1): 'b', (2): None}), ('ab', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'ignore', {
            (0): 'a', (1): 'b', (2): '\ufffe'}), ('ab', 3))
        allbytes = bytes(range(256))
        self.assertEqual(codecs.charmap_decode(allbytes, 'ignore', {}), ('',
            len(allbytes)))

    def test_decode_with_int2int_map(self):
        a = ord('a')
        b = ord('b')
        c = ord('c')
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'strict', {
            (0): a, (1): b, (2): c}), ('abc', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'strict', {
            (0): 1114111, (1): b, (2): c}), ('\U0010ffffbc', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'strict', {
            (0): sys.maxunicode, (1): b, (2): c}), (chr(sys.maxunicode) +
            'bc', 3))
        self.assertRaises(TypeError, codecs.charmap_decode, b'\x00\x01\x02',
            'strict', {(0): sys.maxunicode + 1, (1): b, (2): c})
        self.assertRaises(UnicodeDecodeError, codecs.charmap_decode,
            b'\x00\x01\x02', 'strict', {(0): a, (1): b})
        self.assertRaises(UnicodeDecodeError, codecs.charmap_decode,
            b'\x00\x01\x02', 'strict', {(0): a, (1): b, (2): 65534})
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'replace',
            {(0): a, (1): b}), ('ab�', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'replace',
            {(0): a, (1): b, (2): 65534}), ('ab�', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02',
            'backslashreplace', {(0): a, (1): b}), ('ab\\x02', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02',
            'backslashreplace', {(0): a, (1): b, (2): 65534}), ('ab\\x02', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'ignore', {
            (0): a, (1): b}), ('ab', 3))
        self.assertEqual(codecs.charmap_decode(b'\x00\x01\x02', 'ignore', {
            (0): a, (1): b, (2): 65534}), ('ab', 3))


class WithStmtTest(unittest.TestCase):

    def test_encodedfile(self):
        f = io.BytesIO(b'\xc3\xbc')
        with codecs.EncodedFile(f, 'latin-1', 'utf-8') as ef:
            self.assertEqual(ef.read(), b'\xfc')
        self.assertTrue(f.closed)

    def test_streamreaderwriter(self):
        f = io.BytesIO(b'\xc3\xbc')
        info = codecs.lookup('utf-8')
        with codecs.StreamReaderWriter(f, info.streamreader, info.
            streamwriter, 'strict') as srw:
            self.assertEqual(srw.read(), 'ü')


class TypesTest(unittest.TestCase):

    def test_decode_unicode(self):
        decoders = [codecs.utf_7_decode, codecs.utf_8_decode, codecs.
            utf_16_le_decode, codecs.utf_16_be_decode, codecs.
            utf_16_ex_decode, codecs.utf_32_decode, codecs.utf_32_le_decode,
            codecs.utf_32_be_decode, codecs.utf_32_ex_decode, codecs.
            latin_1_decode, codecs.ascii_decode, codecs.charmap_decode]
        if hasattr(codecs, 'mbcs_decode'):
            decoders.append(codecs.mbcs_decode)
        for decoder in decoders:
            self.assertRaises(TypeError, decoder, 'xxx')

    def test_unicode_escape(self):
        self.assertEqual(codecs.unicode_escape_decode('\\u1234'), ('ሴ', 6))
        self.assertEqual(codecs.unicode_escape_decode(b'\\u1234'), ('ሴ', 6))
        self.assertEqual(codecs.raw_unicode_escape_decode('\\u1234'), ('ሴ', 6))
        self.assertEqual(codecs.raw_unicode_escape_decode(b'\\u1234'), ('ሴ', 6)
            )
        self.assertRaises(UnicodeDecodeError, codecs.unicode_escape_decode,
            b'\\U00110000')
        self.assertEqual(codecs.unicode_escape_decode('\\U00110000',
            'replace'), ('�', 10))
        self.assertEqual(codecs.unicode_escape_decode('\\U00110000',
            'backslashreplace'), (
            '\\x5c\\x55\\x30\\x30\\x31\\x31\\x30\\x30\\x30\\x30', 10))
        self.assertRaises(UnicodeDecodeError, codecs.
            raw_unicode_escape_decode, b'\\U00110000')
        self.assertEqual(codecs.raw_unicode_escape_decode('\\U00110000',
            'replace'), ('�', 10))
        self.assertEqual(codecs.raw_unicode_escape_decode('\\U00110000',
            'backslashreplace'), (
            '\\x5c\\x55\\x30\\x30\\x31\\x31\\x30\\x30\\x30\\x30', 10))


class UnicodeEscapeTest(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(codecs.unicode_escape_encode(''), (b'', 0))
        self.assertEqual(codecs.unicode_escape_decode(b''), ('', 0))

    def test_raw_encode(self):
        encode = codecs.unicode_escape_encode
        for b in range(32, 127):
            if b != b'\\'[0]:
                self.assertEqual(encode(chr(b)), (bytes([b]), 1))

    def test_raw_decode(self):
        decode = codecs.unicode_escape_decode
        for b in range(256):
            if b != b'\\'[0]:
                self.assertEqual(decode(bytes([b]) + b'0'), (chr(b) + '0', 2))

    def test_escape_encode(self):
        encode = codecs.unicode_escape_encode
        check = coding_checker(self, encode)
        check('\t', b'\\t')
        check('\n', b'\\n')
        check('\r', b'\\r')
        check('\\', b'\\\\')
        for b in range(32):
            if chr(b) not in '\t\n\r':
                check(chr(b), ('\\x%02x' % b).encode())
        for b in range(127, 256):
            check(chr(b), ('\\x%02x' % b).encode())
        check('€', b'\\u20ac')
        check('𝄠', b'\\U0001d120')

    def test_escape_decode(self):
        decode = codecs.unicode_escape_decode
        check = coding_checker(self, decode)
        check(b'[\\\n]', '[]')
        check(b'[\\"]', '["]')
        check(b"[\\']", "[']")
        check(b'[\\\\]', '[\\]')
        check(b'[\\a]', '[\x07]')
        check(b'[\\b]', '[\x08]')
        check(b'[\\t]', '[\t]')
        check(b'[\\n]', '[\n]')
        check(b'[\\v]', '[\x0b]')
        check(b'[\\f]', '[\x0c]')
        check(b'[\\r]', '[\r]')
        check(b'[\\7]', '[\x07]')
        check(b'[\\78]', '[\x078]')
        check(b'[\\41]', '[!]')
        check(b'[\\418]', '[!8]')
        check(b'[\\101]', '[A]')
        check(b'[\\1010]', '[A0]')
        check(b'[\\x41]', '[A]')
        check(b'[\\x410]', '[A0]')
        check(b'\\u20ac', '€')
        check(b'\\U0001d120', '𝄠')
        for i in range(97, 123):
            b = bytes([i])
            if b not in b'abfnrtuvx':
                with self.assertWarns(DeprecationWarning):
                    check(b'\\' + b, '\\' + chr(i))
            if b.upper() not in b'UN':
                with self.assertWarns(DeprecationWarning):
                    check(b'\\' + b.upper(), '\\' + chr(i - 32))
        with self.assertWarns(DeprecationWarning):
            check(b'\\8', '\\8')
        with self.assertWarns(DeprecationWarning):
            check(b'\\9', '\\9')

    def test_decode_errors(self):
        decode = codecs.unicode_escape_decode
        for c, d in ((b'x', 2), (b'u', 4), (b'U', 4)):
            for i in range(d):
                self.assertRaises(UnicodeDecodeError, decode, b'\\' + c + 
                    b'0' * i)
                self.assertRaises(UnicodeDecodeError, decode, b'[\\' + c + 
                    b'0' * i + b']')
                data = b'[\\' + c + b'0' * i + b']\\' + c + b'0' * i
                self.assertEqual(decode(data, 'ignore'), ('[]', len(data)))
                self.assertEqual(decode(data, 'replace'), ('[�]�', len(data)))
        self.assertRaises(UnicodeDecodeError, decode, b'\\U00110000')
        self.assertEqual(decode(b'\\U00110000', 'ignore'), ('', 10))
        self.assertEqual(decode(b'\\U00110000', 'replace'), ('�', 10))


class RawUnicodeEscapeTest(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(codecs.raw_unicode_escape_encode(''), (b'', 0))
        self.assertEqual(codecs.raw_unicode_escape_decode(b''), ('', 0))

    def test_raw_encode(self):
        encode = codecs.raw_unicode_escape_encode
        for b in range(256):
            self.assertEqual(encode(chr(b)), (bytes([b]), 1))

    def test_raw_decode(self):
        decode = codecs.raw_unicode_escape_decode
        for b in range(256):
            self.assertEqual(decode(bytes([b]) + b'0'), (chr(b) + '0', 2))

    def test_escape_encode(self):
        encode = codecs.raw_unicode_escape_encode
        check = coding_checker(self, encode)
        for b in range(256):
            if b not in b'uU':
                check('\\' + chr(b), b'\\' + bytes([b]))
        check('€', b'\\u20ac')
        check('𝄠', b'\\U0001d120')

    def test_escape_decode(self):
        decode = codecs.raw_unicode_escape_decode
        check = coding_checker(self, decode)
        for b in range(256):
            if b not in b'uU':
                check(b'\\' + bytes([b]), '\\' + chr(b))
        check(b'\\u20ac', '€')
        check(b'\\U0001d120', '𝄠')

    def test_decode_errors(self):
        decode = codecs.raw_unicode_escape_decode
        for c, d in ((b'u', 4), (b'U', 4)):
            for i in range(d):
                self.assertRaises(UnicodeDecodeError, decode, b'\\' + c + 
                    b'0' * i)
                self.assertRaises(UnicodeDecodeError, decode, b'[\\' + c + 
                    b'0' * i + b']')
                data = b'[\\' + c + b'0' * i + b']\\' + c + b'0' * i
                self.assertEqual(decode(data, 'ignore'), ('[]', len(data)))
                self.assertEqual(decode(data, 'replace'), ('[�]�', len(data)))
        self.assertRaises(UnicodeDecodeError, decode, b'\\U00110000')
        self.assertEqual(decode(b'\\U00110000', 'ignore'), ('', 10))
        self.assertEqual(decode(b'\\U00110000', 'replace'), ('�', 10))


class EscapeEncodeTest(unittest.TestCase):

    def test_escape_encode(self):
        tests = [(b'', (b'', 0)), (b'foobar', (b'foobar', 6)), (
            b'spam\x00eggs', (b'spam\\x00eggs', 9)), (b"a'b", (b"a\\'b", 3)
            ), (b'b\\c', (b'b\\\\c', 3)), (b'c\nd', (b'c\\nd', 3)), (
            b'd\re', (b'd\\re', 3)), (b'f\x7fg', (b'f\\x7fg', 3))]
        for data, output in tests:
            with self.subTest(data=data):
                self.assertEqual(codecs.escape_encode(data), output)
        self.assertRaises(TypeError, codecs.escape_encode, 'spam')
        self.assertRaises(TypeError, codecs.escape_encode, bytearray(b'spam'))


class SurrogateEscapeTest(unittest.TestCase):

    def test_utf8(self):
        self.assertEqual(b'foo\x80bar'.decode('utf-8', 'surrogateescape'),
            'foo\udc80bar')
        self.assertEqual('foo\udc80bar'.encode('utf-8', 'surrogateescape'),
            b'foo\x80bar')
        self.assertEqual(b'\xed\xb0\x80'.decode('utf-8', 'surrogateescape'),
            '\udced\udcb0\udc80')
        self.assertEqual('\udced\udcb0\udc80'.encode('utf-8',
            'surrogateescape'), b'\xed\xb0\x80')

    def test_ascii(self):
        self.assertEqual(b'foo\x80bar'.decode('ascii', 'surrogateescape'),
            'foo\udc80bar')
        self.assertEqual('foo\udc80bar'.encode('ascii', 'surrogateescape'),
            b'foo\x80bar')

    def test_charmap(self):
        self.assertEqual(b'foo\xa5bar'.decode('iso-8859-3',
            'surrogateescape'), 'foo\udca5bar')
        self.assertEqual('foo\udca5bar'.encode('iso-8859-3',
            'surrogateescape'), b'foo\xa5bar')

    def test_latin1(self):
        self.assertEqual('\udce4\udceb\udcef\udcf6\udcfc'.encode('latin-1',
            'surrogateescape'), b'\xe4\xeb\xef\xf6\xfc')


class BomTest(unittest.TestCase):

    def test_seek0(self):
        data = '1234567890'
        tests = ('utf-16', 'utf-16-le', 'utf-16-be', 'utf-32', 'utf-32-le',
            'utf-32-be')
        self.addCleanup(support.unlink, support.TESTFN)
        for encoding in tests:
            with codecs.open(support.TESTFN, 'w+', encoding=encoding) as f:
                f.write(data)
                f.write(data)
                f.seek(0)
                self.assertEqual(f.read(), data * 2)
                f.seek(0)
                self.assertEqual(f.read(), data * 2)
            with codecs.open(support.TESTFN, 'w+', encoding=encoding) as f:
                f.write(data[0])
                self.assertNotEqual(f.tell(), 0)
                f.seek(0)
                f.write(data)
                f.seek(0)
                self.assertEqual(f.read(), data)
            with codecs.open(support.TESTFN, 'w+', encoding=encoding) as f:
                f.writer.write(data[0])
                self.assertNotEqual(f.writer.tell(), 0)
                f.writer.seek(0)
                f.writer.write(data)
                f.seek(0)
                self.assertEqual(f.read(), data)
            with codecs.open(support.TESTFN, 'w+', encoding=encoding) as f:
                f.write(data)
                f.seek(f.tell())
                f.write(data)
                f.seek(0)
                self.assertEqual(f.read(), data * 2)
            with codecs.open(support.TESTFN, 'w+', encoding=encoding) as f:
                f.writer.write(data)
                f.writer.seek(f.writer.tell())
                f.writer.write(data)
                f.seek(0)
                self.assertEqual(f.read(), data * 2)


bytes_transform_encodings = ['base64_codec', 'uu_codec', 'quopri_codec',
    'hex_codec']
transform_aliases = {'base64_codec': ['base64', 'base_64'], 'uu_codec': [
    'uu'], 'quopri_codec': ['quopri', 'quoted_printable', 'quotedprintable'
    ], 'hex_codec': ['hex'], 'rot_13': ['rot13']}
try:
    import zlib
except ImportError:
    zlib = None
else:
    bytes_transform_encodings.append('zlib_codec')
    transform_aliases['zlib_codec'] = ['zip', 'zlib']
try:
    import bz2
except ImportError:
    pass
else:
    bytes_transform_encodings.append('bz2_codec')
    transform_aliases['bz2_codec'] = ['bz2']


class TransformCodecTest(unittest.TestCase):

    def test_basics(self):
        binput = bytes(range(256))
        for encoding in bytes_transform_encodings:
            with self.subTest(encoding=encoding):
                o, size = codecs.getencoder(encoding)(binput)
                self.assertEqual(size, len(binput))
                i, size = codecs.getdecoder(encoding)(o)
                self.assertEqual(size, len(o))
                self.assertEqual(i, binput)

    def test_read(self):
        for encoding in bytes_transform_encodings:
            with self.subTest(encoding=encoding):
                sin = codecs.encode(b'\x80', encoding)
                reader = codecs.getreader(encoding)(io.BytesIO(sin))
                sout = reader.read()
                self.assertEqual(sout, b'\x80')

    def test_readline(self):
        for encoding in bytes_transform_encodings:
            with self.subTest(encoding=encoding):
                sin = codecs.encode(b'\x80', encoding)
                reader = codecs.getreader(encoding)(io.BytesIO(sin))
                sout = reader.readline()
                self.assertEqual(sout, b'\x80')

    def test_buffer_api_usage(self):
        original = b'12345\x80'
        for encoding in bytes_transform_encodings:
            with self.subTest(encoding=encoding):
                data = original
                view = memoryview(data)
                data = codecs.encode(data, encoding)
                view_encoded = codecs.encode(view, encoding)
                self.assertEqual(view_encoded, data)
                view = memoryview(data)
                data = codecs.decode(data, encoding)
                self.assertEqual(data, original)
                view_decoded = codecs.decode(view, encoding)
                self.assertEqual(view_decoded, data)

    def test_text_to_binary_blacklists_binary_transforms(self):
        bad_input = 'bad input type'
        for encoding in bytes_transform_encodings:
            with self.subTest(encoding=encoding):
                fmt = (
                    '{!r} is not a text encoding; use codecs.encode\\(\\) to handle arbitrary codecs'
                    )
                msg = fmt.format(encoding)
                with self.assertRaisesRegex(LookupError, msg) as failure:
                    bad_input.encode(encoding)
                self.assertIsNone(failure.exception.__cause__)

    def test_text_to_binary_blacklists_text_transforms(self):
        msg = (
            "^'rot_13' is not a text encoding; use codecs.encode\\(\\) to handle arbitrary codecs"
            )
        with self.assertRaisesRegex(LookupError, msg):
            """just an example message""".encode('rot_13')

    def test_binary_to_text_blacklists_binary_transforms(self):
        data = b'encode first to ensure we meet any format restrictions'
        for encoding in bytes_transform_encodings:
            with self.subTest(encoding=encoding):
                encoded_data = codecs.encode(data, encoding)
                fmt = (
                    '{!r} is not a text encoding; use codecs.decode\\(\\) to handle arbitrary codecs'
                    )
                msg = fmt.format(encoding)
                with self.assertRaisesRegex(LookupError, msg):
                    encoded_data.decode(encoding)
                with self.assertRaisesRegex(LookupError, msg):
                    bytearray(encoded_data).decode(encoding)

    def test_binary_to_text_blacklists_text_transforms(self):
        for bad_input in (b'immutable', bytearray(b'mutable')):
            with self.subTest(bad_input=bad_input):
                msg = (
                    "^'rot_13' is not a text encoding; use codecs.decode\\(\\) to handle arbitrary codecs"
                    )
                with self.assertRaisesRegex(LookupError, msg) as failure:
                    bad_input.decode('rot_13')
                self.assertIsNone(failure.exception.__cause__)

    @unittest.skipUnless(zlib, 'Requires zlib support')
    def test_custom_zlib_error_is_wrapped(self):
        msg = "^decoding with 'zlib_codec' codec failed"
        with self.assertRaisesRegex(Exception, msg) as failure:
            codecs.decode(b'hello', 'zlib_codec')
        self.assertIsInstance(failure.exception.__cause__, type(failure.
            exception))

    def test_custom_hex_error_is_wrapped(self):
        msg = "^decoding with 'hex_codec' codec failed"
        with self.assertRaisesRegex(Exception, msg) as failure:
            codecs.decode(b'hello', 'hex_codec')
        self.assertIsInstance(failure.exception.__cause__, type(failure.
            exception))

    def test_aliases(self):
        for codec_name, aliases in transform_aliases.items():
            expected_name = codecs.lookup(codec_name).name
            for alias in aliases:
                with self.subTest(alias=alias):
                    info = codecs.lookup(alias)
                    self.assertEqual(info.name, expected_name)

    def test_quopri_stateless(self):
        encoded = codecs.encode(b'space tab\teol \n', 'quopri-codec')
        self.assertEqual(encoded, b'space=20tab=09eol=20\n')
        unescaped = b'space tab eol\n'
        self.assertEqual(codecs.decode(unescaped, 'quopri-codec'), unescaped)

    def test_uu_invalid(self):
        self.assertRaises(ValueError, codecs.decode, b'', 'uu-codec')


_TEST_CODECS = {}


def _get_test_codec(codec_name):
    return _TEST_CODECS.get(codec_name)


codecs.register(_get_test_codec)
try:
    from _codecs import _forget_codec
except ImportError:

    def _forget_codec(codec_name):
        pass


class ExceptionChainingTest(unittest.TestCase):

    def setUp(self):
        unique_id = repr(self) + str(id(self))
        self.codec_name = encodings.normalize_encoding(unique_id).lower()
        self.obj_to_raise = RuntimeError

    def tearDown(self):
        _TEST_CODECS.pop(self.codec_name, None)
        encodings._cache.pop(self.codec_name, None)
        try:
            _forget_codec(self.codec_name)
        except KeyError:
            pass

    def set_codec(self, encode, decode):
        codec_info = codecs.CodecInfo(encode, decode, name=self.codec_name)
        _TEST_CODECS[self.codec_name] = codec_info

    @contextlib.contextmanager
    def assertWrapped(self, operation, exc_type, msg):
        full_msg = '{} with {!r} codec failed \\({}: {}\\)'.format(operation,
            self.codec_name, exc_type.__name__, msg)
        with self.assertRaisesRegex(exc_type, full_msg) as caught:
            yield caught
        self.assertIsInstance(caught.exception.__cause__, exc_type)
        self.assertIsNotNone(caught.exception.__cause__.__traceback__)

    def raise_obj(self, *args, **kwds):
        raise self.obj_to_raise

    def check_wrapped(self, obj_to_raise, msg, exc_type=RuntimeError):
        self.obj_to_raise = obj_to_raise
        self.set_codec(self.raise_obj, self.raise_obj)
        with self.assertWrapped('encoding', exc_type, msg):
            """str_input""".encode(self.codec_name)
        with self.assertWrapped('encoding', exc_type, msg):
            codecs.encode('str_input', self.codec_name)
        with self.assertWrapped('decoding', exc_type, msg):
            b'bytes input'.decode(self.codec_name)
        with self.assertWrapped('decoding', exc_type, msg):
            codecs.decode(b'bytes input', self.codec_name)

    def test_raise_by_type(self):
        self.check_wrapped(RuntimeError, '')

    def test_raise_by_value(self):
        msg = 'This should be wrapped'
        self.check_wrapped(RuntimeError(msg), msg)

    def test_raise_grandchild_subclass_exact_size(self):
        msg = 'This should be wrapped'


        class MyRuntimeError(RuntimeError):
            __slots__ = ()
        self.check_wrapped(MyRuntimeError(msg), msg, MyRuntimeError)

    def test_raise_subclass_with_weakref_support(self):
        msg = 'This should be wrapped'


        class MyRuntimeError(RuntimeError):
            pass
        self.check_wrapped(MyRuntimeError(msg), msg, MyRuntimeError)

    def check_not_wrapped(self, obj_to_raise, msg):

        def raise_obj(*args, **kwds):
            raise obj_to_raise
        self.set_codec(raise_obj, raise_obj)
        with self.assertRaisesRegex(RuntimeError, msg):
            """str input""".encode(self.codec_name)
        with self.assertRaisesRegex(RuntimeError, msg):
            codecs.encode('str input', self.codec_name)
        with self.assertRaisesRegex(RuntimeError, msg):
            b'bytes input'.decode(self.codec_name)
        with self.assertRaisesRegex(RuntimeError, msg):
            codecs.decode(b'bytes input', self.codec_name)

    def test_init_override_is_not_wrapped(self):


        class CustomInit(RuntimeError):

            def __init__(self):
                pass
        self.check_not_wrapped(CustomInit, '')

    def test_new_override_is_not_wrapped(self):


        class CustomNew(RuntimeError):

            def __new__(cls):
                return super().__new__(cls)
        self.check_not_wrapped(CustomNew, '')

    def test_instance_attribute_is_not_wrapped(self):
        msg = 'This should NOT be wrapped'
        exc = RuntimeError(msg)
        exc.attr = 1
        self.check_not_wrapped(exc, '^{}$'.format(msg))

    def test_non_str_arg_is_not_wrapped(self):
        self.check_not_wrapped(RuntimeError(1), '1')

    def test_multiple_args_is_not_wrapped(self):
        msg_re = "^\\('a', 'b', 'c'\\)$"
        self.check_not_wrapped(RuntimeError('a', 'b', 'c'), msg_re)

    def test_codec_lookup_failure_not_wrapped(self):
        msg = '^unknown encoding: {}$'.format(self.codec_name)
        with self.assertRaisesRegex(LookupError, msg):
            """str input""".encode(self.codec_name)
        with self.assertRaisesRegex(LookupError, msg):
            codecs.encode('str input', self.codec_name)
        with self.assertRaisesRegex(LookupError, msg):
            b'bytes input'.decode(self.codec_name)
        with self.assertRaisesRegex(LookupError, msg):
            codecs.decode(b'bytes input', self.codec_name)

    def test_unflagged_non_text_codec_handling(self):

        def encode_to_str(*args, **kwds):
            return 'not bytes!', 0

        def decode_to_bytes(*args, **kwds):
            return b'not str!', 0
        self.set_codec(encode_to_str, decode_to_bytes)
        encoded = codecs.encode(None, self.codec_name)
        self.assertEqual(encoded, 'not bytes!')
        decoded = codecs.decode(None, self.codec_name)
        self.assertEqual(decoded, b'not str!')
        fmt = (
            "^{!r} encoder returned 'str' instead of 'bytes'; use codecs.encode\\(\\) to encode to arbitrary types$"
            )
        msg = fmt.format(self.codec_name)
        with self.assertRaisesRegex(TypeError, msg):
            """str_input""".encode(self.codec_name)
        fmt = (
            "^{!r} decoder returned 'bytes' instead of 'str'; use codecs.decode\\(\\) to decode to arbitrary types$"
            )
        msg = fmt.format(self.codec_name)
        with self.assertRaisesRegex(TypeError, msg):
            b'bytes input'.decode(self.codec_name)


@unittest.skipUnless(sys.platform == 'win32',
    'code pages are specific to Windows')
class CodePageTest(unittest.TestCase):
    CP_UTF8 = 65001

    def test_invalid_code_page(self):
        self.assertRaises(ValueError, codecs.code_page_encode, -1, 'a')
        self.assertRaises(ValueError, codecs.code_page_decode, -1, b'a')
        self.assertRaises(OSError, codecs.code_page_encode, 123, 'a')
        self.assertRaises(OSError, codecs.code_page_decode, 123, b'a')

    def test_code_page_name(self):
        self.assertRaisesRegex(UnicodeEncodeError, 'cp932', codecs.
            code_page_encode, 932, 'ÿ')
        self.assertRaisesRegex(UnicodeDecodeError, 'cp932', codecs.
            code_page_decode, 932, b'\x81\x00', 'strict', True)
        self.assertRaisesRegex(UnicodeDecodeError, 'CP_UTF8', codecs.
            code_page_decode, self.CP_UTF8, b'\xff', 'strict', True)

    def check_decode(self, cp, tests):
        for raw, errors, expected in tests:
            if expected is not None:
                try:
                    decoded = codecs.code_page_decode(cp, raw, errors, True)
                except UnicodeDecodeError as err:
                    self.fail(
                        'Unable to decode %a from "cp%s" with errors=%r: %s' %
                        (raw, cp, errors, err))
                self.assertEqual(decoded[0], expected, 
                    '%a.decode("cp%s", %r)=%a != %a' % (raw, cp, errors,
                    decoded[0], expected))
                self.assertGreaterEqual(decoded[1], 0)
                self.assertLessEqual(decoded[1], len(raw))
            else:
                self.assertRaises(UnicodeDecodeError, codecs.
                    code_page_decode, cp, raw, errors, True)

    def check_encode(self, cp, tests):
        for text, errors, expected in tests:
            if expected is not None:
                try:
                    encoded = codecs.code_page_encode(cp, text, errors)
                except UnicodeEncodeError as err:
                    self.fail(
                        'Unable to encode %a to "cp%s" with errors=%r: %s' %
                        (text, cp, errors, err))
                self.assertEqual(encoded[0], expected, 
                    '%a.encode("cp%s", %r)=%a != %a' % (text, cp, errors,
                    encoded[0], expected))
                self.assertEqual(encoded[1], len(text))
            else:
                self.assertRaises(UnicodeEncodeError, codecs.
                    code_page_encode, cp, text, errors)

    def test_cp932(self):
        self.check_encode(932, (('abc', 'strict', b'abc'), ('ｄ騾', 'strict',
            b'\x82\x84\xe9\x80'), ('ÿ', 'strict', None), ('[ÿ]', 'ignore',
            b'[]'), ('[ÿ]', 'replace', b'[y]'), ('[€]', 'replace', b'[?]'),
            ('[ÿ]', 'backslashreplace', b'[\\xff]'), ('[ÿ]', 'namereplace',
            b'[\\N{LATIN SMALL LETTER Y WITH DIAERESIS}]'), ('[ÿ]',
            'xmlcharrefreplace', b'[&#255;]'), ('\udcff', 'strict', None),
            ('[\udcff]', 'surrogateescape', b'[\xff]'), ('[\udcff]',
            'surrogatepass', None)))
        self.check_decode(932, ((b'abc', 'strict', 'abc'), (
            b'\x82\x84\xe9\x80', 'strict', 'ｄ騾'), (b'[\xff]', 'strict',
            None), (b'[\xff]', 'ignore', '[]'), (b'[\xff]', 'replace',
            '[�]'), (b'[\xff]', 'backslashreplace', '[\\xff]'), (b'[\xff]',
            'surrogateescape', '[\udcff]'), (b'[\xff]', 'surrogatepass',
            None), (b'\x81\x00abc', 'strict', None), (b'\x81\x00abc',
            'ignore', '\x00abc'), (b'\x81\x00abc', 'replace', '�\x00abc'),
            (b'\x81\x00abc', 'backslashreplace', '\\x81\x00abc')))

    def test_cp1252(self):
        self.check_encode(1252, (('abc', 'strict', b'abc'), ('é€', 'strict',
            b'\xe9\x80'), ('ÿ', 'strict', b'\xff'), ('Ł', 'strict', None),
            ('Ł', 'ignore', b''), ('Ł', 'replace', b'L'), ('\udc98',
            'surrogateescape', b'\x98'), ('\udc98', 'surrogatepass', None)))
        self.check_decode(1252, ((b'abc', 'strict', 'abc'), (b'\xe9\x80',
            'strict', 'é€'), (b'\xff', 'strict', 'ÿ')))

    def test_cp_utf7(self):
        cp = 65000
        self.check_encode(cp, (('abc', 'strict', b'abc'), ('é€', 'strict',
            b'+AOkgrA-'), ('\U0010ffff', 'strict', b'+2//f/w-'), ('\udc80',
            'strict', b'+3IA-'), ('�', 'strict', b'+//0-')))
        self.check_decode(cp, ((b'abc', 'strict', 'abc'), (b'+AOkgrA-',
            'strict', 'é€'), (b'+2//f/w-', 'strict', '\U0010ffff'), (
            b'+3IA-', 'strict', '\udc80'), (b'+//0-', 'strict', '�'), (
            b'[+/]', 'strict', '[]'), (b'[\xff]', 'strict', '[ÿ]')))

    def test_multibyte_encoding(self):
        self.check_decode(932, ((b'\x84\xe9\x80', 'ignore', '騾'), (
            b'\x84\xe9\x80', 'replace', '�騾')))
        self.check_decode(self.CP_UTF8, ((b'\xff\xf4\x8f\xbf\xbf', 'ignore',
            '\U0010ffff'), (b'\xff\xf4\x8f\xbf\xbf', 'replace', '�\U0010ffff'))
            )
        self.check_encode(self.CP_UTF8, (('[\U0010ffff\udc80]', 'ignore',
            b'[\xf4\x8f\xbf\xbf]'), ('[\U0010ffff\udc80]', 'replace',
            b'[\xf4\x8f\xbf\xbf?]')))

    def test_incremental(self):
        decoded = codecs.code_page_decode(932, b'\x82', 'strict', False)
        self.assertEqual(decoded, ('', 0))
        decoded = codecs.code_page_decode(932, b'\xe9\x80\xe9', 'strict', False
            )
        self.assertEqual(decoded, ('騾', 2))
        decoded = codecs.code_page_decode(932, b'\xe9\x80\xe9\x80',
            'strict', False)
        self.assertEqual(decoded, ('騾騾', 4))
        decoded = codecs.code_page_decode(932, b'abc', 'strict', False)
        self.assertEqual(decoded, ('abc', 3))

    def test_mbcs_alias(self):
        import _bootlocale

        def _get_fake_codepage(*a):
            return 'cp123'
        old_getpreferredencoding = _bootlocale.getpreferredencoding
        _bootlocale.getpreferredencoding = _get_fake_codepage
        try:
            codec = codecs.lookup('cp123')
            self.assertEqual(codec.name, 'mbcs')
        finally:
            _bootlocale.getpreferredencoding = old_getpreferredencoding


class ASCIITest(unittest.TestCase):

    def test_encode(self):
        self.assertEqual('abc123'.encode('ascii'), b'abc123')

    def test_encode_error(self):
        for data, error_handler, expected in (('[\x80ÿ€]', 'ignore', b'[]'),
            ('[\x80ÿ€]', 'replace', b'[???]'), ('[\x80ÿ€]',
            'xmlcharrefreplace', b'[&#128;&#255;&#8364;]'), (
            '[\x80ÿ€\U000abcde]', 'backslashreplace',
            b'[\\x80\\xff\\u20ac\\U000abcde]'), ('[\udc80\udcff]',
            'surrogateescape', b'[\x80\xff]')):
            with self.subTest(data=data, error_handler=error_handler,
                expected=expected):
                self.assertEqual(data.encode('ascii', error_handler), expected)

    def test_encode_surrogateescape_error(self):
        with self.assertRaises(UnicodeEncodeError):
            '\udc80ÿ'.encode('ascii', 'surrogateescape')

    def test_decode(self):
        self.assertEqual(b'abc'.decode('ascii'), 'abc')

    def test_decode_error(self):
        for data, error_handler, expected in ((b'[\x80\xff]', 'ignore',
            '[]'), (b'[\x80\xff]', 'replace', '[��]'), (b'[\x80\xff]',
            'surrogateescape', '[\udc80\udcff]'), (b'[\x80\xff]',
            'backslashreplace', '[\\x80\\xff]')):
            with self.subTest(data=data, error_handler=error_handler,
                expected=expected):
                self.assertEqual(data.decode('ascii', error_handler), expected)


class Latin1Test(unittest.TestCase):

    def test_encode(self):
        for data, expected in (('abc', b'abc'), ('\x80éÿ', b'\x80\xe9\xff')):
            with self.subTest(data=data, expected=expected):
                self.assertEqual(data.encode('latin1'), expected)

    def test_encode_errors(self):
        for data, error_handler, expected in (('[€\udc80]', 'ignore', b'[]'
            ), ('[€\udc80]', 'replace', b'[??]'), ('[€\U000abcde]',
            'backslashreplace', b'[\\u20ac\\U000abcde]'), ('[€\udc80]',
            'xmlcharrefreplace', b'[&#8364;&#56448;]'), ('[\udc80\udcff]',
            'surrogateescape', b'[\x80\xff]')):
            with self.subTest(data=data, error_handler=error_handler,
                expected=expected):
                self.assertEqual(data.encode('latin1', error_handler), expected
                    )

    def test_encode_surrogateescape_error(self):
        with self.assertRaises(UnicodeEncodeError):
            '\udc80€'.encode('latin1', 'surrogateescape')

    def test_decode(self):
        for data, expected in ((b'abc', 'abc'), (b'[\x80\xff]', '[\x80ÿ]')):
            with self.subTest(data=data, expected=expected):
                self.assertEqual(data.decode('latin1'), expected)


if __name__ == '__main__':
    unittest.main()
