"""A parser for HTML and XHTML."""
import re
import warnings
import _markupbase
from html import unescape
__all__ = ['HTMLParser']
interesting_normal = re.compile('[&<]')
incomplete = re.compile('&[a-zA-Z#]')
entityref = re.compile('&([a-zA-Z][-.a-zA-Z0-9]*)[^a-zA-Z0-9]')
charref = re.compile('&#(?:[0-9]+|[xX][0-9a-fA-F]+)[^0-9a-fA-F]')
starttagopen = re.compile('<[a-zA-Z]')
piclose = re.compile('>')
commentclose = re.compile('--\\s*>')
tagfind_tolerant = re.compile(
    '([a-zA-Z][^\\t\\n\\r\\f />\\x00]*)(?:\\s|/(?!>))*')
attrfind_tolerant = re.compile(
    '((?<=[\\\'"\\s/])[^\\s/>][^\\s/=>]*)(\\s*=+\\s*(\\\'[^\\\']*\\\'|"[^"]*"|(?![\\\'"])[^>\\s]*))?(?:\\s|/(?!>))*'
    )
locatestarttagend_tolerant = re.compile(
    """
  <[a-zA-Z][^\\t\\n\\r\\f />\\x00]*       # tag name
  (?:[\\s/]*                          # optional whitespace before attribute name
    (?:(?<=['"\\s/])[^\\s/>][^\\s/=>]*  # attribute name
      (?:\\s*=+\\s*                    # value indicator
        (?:'[^']*'                   # LITA-enclosed value
          |"[^"]*"                   # LIT-enclosed value
          |(?!['"])[^>\\s]*           # bare value
         )
         (?:\\s*,)*                   # possibly followed by a comma
       )?(?:\\s|/(?!>))*
     )*
   )?
  \\s*                                # trailing whitespace
"""
    , re.VERBOSE)
endendtag = re.compile('>')
endtagfind = re.compile('</\\s*([a-zA-Z][-.a-zA-Z0-9:_]*)\\s*>')


class HTMLParser(_markupbase.ParserBase):
    """Find tags and other markup and call handler functions.

    Usage:
        p = HTMLParser()
        p.feed(data)
        ...
        p.close()

    Start tags are handled by calling self.handle_starttag() or
    self.handle_startendtag(); end tags by self.handle_endtag().  The
    data between tags is passed from the parser to the derived class
    by calling self.handle_data() with the data as argument (the data
    may be split up in arbitrary chunks).  If convert_charrefs is
    True the character references are converted automatically to the
    corresponding Unicode character (and self.handle_data() is no
    longer split in chunks), otherwise they are passed by calling
    self.handle_entityref() or self.handle_charref() with the string
    containing respectively the named or numeric reference as the
    argument.
    """
    CDATA_CONTENT_ELEMENTS = 'script', 'style'

    def __init__(self, *, convert_charrefs=True):
        """Initialize and reset this instance.

        If convert_charrefs is True (the default), all character references
        are automatically converted to the corresponding Unicode characters.
        """
        self.convert_charrefs = convert_charrefs
        self.reset()

    def reset(self):
        """Reset this instance.  Loses all unprocessed data."""
        self.rawdata = ''
        self.lasttag = '???'
        self.interesting = interesting_normal
        self.cdata_elem = None
        _markupbase.ParserBase.reset(self)

    def feed(self, data):
        """Feed data to the parser.

        Call this as often as you want, with as little or as much text
        as you want (may include '\\n').
        """
        self.rawdata = self.rawdata + data
        self.goahead(0)

    def close(self):
        """Handle any buffered data."""
        self.goahead(1)
    __starttag_text = None

    def get_starttag_text(self):
        """Return full source of start tag: '<...>'."""
        return self.__starttag_text

    def set_cdata_mode(self, elem):
        self.cdata_elem = elem.lower()
        self.interesting = re.compile('</\\s*%s\\s*>' % self.cdata_elem, re.I)

    def clear_cdata_mode(self):
        self.interesting = interesting_normal
        self.cdata_elem = None

    def goahead(self, end):
        rawdata = self.rawdata
        i = 0
        n = len(rawdata)
        while i < n:
            if self.convert_charrefs and not self.cdata_elem:
                j = rawdata.find('<', i)
                if j < 0:
                    amppos = rawdata.rfind('&', max(i, n - 34))
                    if amppos >= 0 and not re.compile('[\\s;]').search(rawdata,
                        amppos):
                        break
                    j = n
            else:
                match = self.interesting.search(rawdata, i)
                if match:
                    j = match.start()
                else:
                    if self.cdata_elem:
                        break
                    j = n
            if i < j:
                if self.convert_charrefs and not self.cdata_elem:
                    self.handle_data(unescape(rawdata[i:j]))
                else:
                    self.handle_data(rawdata[i:j])
            i = self.updatepos(i, j)
            if i == n:
                break
            startswith = rawdata.startswith
            if startswith('<', i):
                if starttagopen.match(rawdata, i):
                    k = self.parse_starttag(i)
                elif startswith('</', i):
                    k = self.parse_endtag(i)
                elif startswith('<!--', i):
                    k = self.parse_comment(i)
                elif startswith('<?', i):
                    k = self.parse_pi(i)
                elif startswith('<!', i):
                    k = self.parse_html_declaration(i)
                elif i + 1 < n:
                    self.handle_data('<')
                    k = i + 1
                else:
                    break
                if k < 0:
                    if not end:
                        break
                    k = rawdata.find('>', i + 1)
                    if k < 0:
                        k = rawdata.find('<', i + 1)
                        if k < 0:
                            k = i + 1
                    else:
                        k += 1
                    if self.convert_charrefs and not self.cdata_elem:
                        self.handle_data(unescape(rawdata[i:k]))
                    else:
                        self.handle_data(rawdata[i:k])
                i = self.updatepos(i, k)
            elif startswith('&#', i):
                match = charref.match(rawdata, i)
                if match:
                    name = match.group()[2:-1]
                    self.handle_charref(name)
                    k = match.end()
                    if not startswith(';', k - 1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    continue
                else:
                    if ';' in rawdata[i:]:
                        self.handle_data(rawdata[i:i + 2])
                        i = self.updatepos(i, i + 2)
                    break
            elif startswith('&', i):
                match = entityref.match(rawdata, i)
                if match:
                    name = match.group(1)
                    self.handle_entityref(name)
                    k = match.end()
                    if not startswith(';', k - 1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    continue
                match = incomplete.match(rawdata, i)
                if match:
                    if end and match.group() == rawdata[i:]:
                        k = match.end()
                        if k <= i:
                            k = n
                        i = self.updatepos(i, i + 1)
                    break
                elif i + 1 < n:
                    self.handle_data('&')
                    i = self.updatepos(i, i + 1)
                else:
                    break
            else:
                assert 0, 'interesting.search() lied'
        if end and i < n and not self.cdata_elem:
            if self.convert_charrefs and not self.cdata_elem:
                self.handle_data(unescape(rawdata[i:n]))
            else:
                self.handle_data(rawdata[i:n])
            i = self.updatepos(i, n)
        self.rawdata = rawdata[i:]

    def parse_html_declaration(self, i):
        rawdata = self.rawdata
        assert rawdata[i:i + 2
            ] == '<!', 'unexpected call to parse_html_declaration()'
        if rawdata[i:i + 4] == '<!--':
            return self.parse_comment(i)
        elif rawdata[i:i + 3] == '<![':
            return self.parse_marked_section(i)
        elif rawdata[i:i + 9].lower() == '<!doctype':
            gtpos = rawdata.find('>', i + 9)
            if gtpos == -1:
                return -1
            self.handle_decl(rawdata[i + 2:gtpos])
            return gtpos + 1
        else:
            return self.parse_bogus_comment(i)

    def parse_bogus_comment(self, i, report=1):
        rawdata = self.rawdata
        assert rawdata[i:i + 2] in ('<!', '</'
            ), 'unexpected call to parse_comment()'
        pos = rawdata.find('>', i + 2)
        if pos == -1:
            return -1
        if report:
            self.handle_comment(rawdata[i + 2:pos])
        return pos + 1

    def parse_pi(self, i):
        rawdata = self.rawdata
        assert rawdata[i:i + 2] == '<?', 'unexpected call to parse_pi()'
        match = piclose.search(rawdata, i + 2)
        if not match:
            return -1
        j = match.start()
        self.handle_pi(rawdata[i + 2:j])
        j = match.end()
        return j

    def parse_starttag(self, i):
        self.__starttag_text = None
        endpos = self.check_for_whole_start_tag(i)
        if endpos < 0:
            return endpos
        rawdata = self.rawdata
        self.__starttag_text = rawdata[i:endpos]
        attrs = []
        match = tagfind_tolerant.match(rawdata, i + 1)
        assert match, 'unexpected call to parse_starttag()'
        k = match.end()
        self.lasttag = tag = match.group(1).lower()
        while k < endpos:
            m = attrfind_tolerant.match(rawdata, k)
            if not m:
                break
            attrname, rest, attrvalue = m.group(1, 2, 3)
            if not rest:
                attrvalue = None
            elif attrvalue[:1] == "'" == attrvalue[-1:] or attrvalue[:1
                ] == '"' == attrvalue[-1:]:
                attrvalue = attrvalue[1:-1]
            if attrvalue:
                attrvalue = unescape(attrvalue)
            attrs.append((attrname.lower(), attrvalue))
            k = m.end()
        end = rawdata[k:endpos].strip()
        if end not in ('>', '/>'):
            lineno, offset = self.getpos()
            if '\n' in self.__starttag_text:
                lineno = lineno + self.__starttag_text.count('\n')
                offset = len(self.__starttag_text
                    ) - self.__starttag_text.rfind('\n')
            else:
                offset = offset + len(self.__starttag_text)
            self.handle_data(rawdata[i:endpos])
            return endpos
        if end.endswith('/>'):
            self.handle_startendtag(tag, attrs)
        else:
            self.handle_starttag(tag, attrs)
            if tag in self.CDATA_CONTENT_ELEMENTS:
                self.set_cdata_mode(tag)
        return endpos

    def check_for_whole_start_tag(self, i):
        rawdata = self.rawdata
        m = locatestarttagend_tolerant.match(rawdata, i)
        if m:
            j = m.end()
            next = rawdata[j:j + 1]
            if next == '>':
                return j + 1
            if next == '/':
                if rawdata.startswith('/>', j):
                    return j + 2
                if rawdata.startswith('/', j):
                    return -1
                if j > i:
                    return j
                else:
                    return i + 1
            if next == '':
                return -1
            if (next in
                'abcdefghijklmnopqrstuvwxyz=/ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
                return -1
            if j > i:
                return j
            else:
                return i + 1
        raise AssertionError('we should not get here!')

    def parse_endtag(self, i):
        rawdata = self.rawdata
        assert rawdata[i:i + 2] == '</', 'unexpected call to parse_endtag'
        match = endendtag.search(rawdata, i + 1)
        if not match:
            return -1
        gtpos = match.end()
        match = endtagfind.match(rawdata, i)
        if not match:
            if self.cdata_elem is not None:
                self.handle_data(rawdata[i:gtpos])
                return gtpos
            namematch = tagfind_tolerant.match(rawdata, i + 2)
            if not namematch:
                if rawdata[i:i + 3] == '</>':
                    return i + 3
                else:
                    return self.parse_bogus_comment(i)
            tagname = namematch.group(1).lower()
            gtpos = rawdata.find('>', namematch.end())
            self.handle_endtag(tagname)
            return gtpos + 1
        elem = match.group(1).lower()
        if self.cdata_elem is not None:
            if elem != self.cdata_elem:
                self.handle_data(rawdata[i:gtpos])
                return gtpos
        self.handle_endtag(elem.lower())
        self.clear_cdata_mode()
        return gtpos

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        pass

    def handle_charref(self, name):
        pass

    def handle_entityref(self, name):
        pass

    def handle_data(self, data):
        pass

    def handle_comment(self, data):
        pass

    def handle_decl(self, decl):
        pass

    def handle_pi(self, data):
        pass

    def unknown_decl(self, data):
        pass

    def unescape(self, s):
        warnings.warn(
            'The unescape method is deprecated and will be removed in 3.5, use html.unescape() instead.'
            , DeprecationWarning, stacklevel=2)
        return unescape(s)
