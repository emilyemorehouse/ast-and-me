from collections.abc import Mapping
import re
import sys
(C_NONE, C_BACKSLASH, C_STRING_FIRST_LINE, C_STRING_NEXT_LINES, C_BRACKET
    ) = range(5)
if 0:

    def dump(*stuff):
        sys.__stdout__.write(' '.join(map(str, stuff)) + '\n')
_synchre = re.compile(
    """
    ^
    [ \\t]*
    (?: while
    |   else
    |   def
    |   return
    |   assert
    |   break
    |   class
    |   continue
    |   elif
    |   try
    |   except
    |   raise
    |   import
    |   yield
    )
    \\b
"""
    , re.VERBOSE | re.MULTILINE).search
_junkre = re.compile("""
    [ \\t]*
    (?: \\# \\S .* )?
    \\n
""", re.
    VERBOSE).match
_match_stringre = re.compile(
    """
    \\""\" [^"\\\\]* (?:
                     (?: \\\\. | "(?!"") )
                     [^"\\\\]*
                 )*
    (?: \\""\" )?

|   " [^"\\\\\\n]* (?: \\\\. [^"\\\\\\n]* )* "?

|   ''' [^'\\\\]* (?:
                   (?: \\\\. | '(?!'') )
                   [^'\\\\]*
                )*
    (?: ''' )?

|   ' [^'\\\\\\n]* (?: \\\\. [^'\\\\\\n]* )* '?
"""
    , re.VERBOSE | re.DOTALL).match
_itemre = re.compile(
    """
    [ \\t]*
    [^\\s#\\\\]    # if we match, m.end()-1 is the interesting char
"""
    , re.VERBOSE).match
_closere = re.compile(
    """
    \\s*
    (?: return
    |   break
    |   continue
    |   raise
    |   pass
    )
    \\b
"""
    , re.VERBOSE).match
_chew_ordinaryre = re.compile("""
    [^[\\](){}#'"\\\\]+
""", re.VERBOSE
    ).match


class StringTranslatePseudoMapping(Mapping):
    """Utility class to be used with str.translate()

    This Mapping class wraps a given dict. When a value for a key is
    requested via __getitem__() or get(), the key is looked up in the
    given dict. If found there, the value from the dict is returned.
    Otherwise, the default value given upon initialization is returned.

    This allows using str.translate() to make some replacements, and to
    replace all characters for which no replacement was specified with
    a given character instead of leaving them as-is.

    For example, to replace everything except whitespace with 'x':

    >>> whitespace_chars = ' \\t\\n\\r'
    >>> preserve_dict = {ord(c): ord(c) for c in whitespace_chars}
    >>> mapping = StringTranslatePseudoMapping(preserve_dict, ord('x'))
    >>> text = "a + b\\tc\\nd"
    >>> text.translate(mapping)
    'x x x\\tx\\nx'
    """

    def __init__(self, non_defaults, default_value):
        self._non_defaults = non_defaults
        self._default_value = default_value

        def _get(key, _get=non_defaults.get, _default=default_value):
            return _get(key, _default)
        self._get = _get

    def __getitem__(self, item):
        return self._get(item)

    def __len__(self):
        return len(self._non_defaults)

    def __iter__(self):
        return iter(self._non_defaults)

    def get(self, key, default=None):
        return self._get(key)


class Parser:

    def __init__(self, indentwidth, tabwidth):
        self.indentwidth = indentwidth
        self.tabwidth = tabwidth

    def set_str(self, s):
        assert len(s) == 0 or s[-1] == '\n'
        self.str = s
        self.study_level = 0

    def find_good_parse_start(self, is_char_in_string=None, _synchre=_synchre):
        str, pos = self.str, None
        if not is_char_in_string:
            return None
        limit = len(str)
        for tries in range(5):
            i = str.rfind(':\n', 0, limit)
            if i < 0:
                break
            i = str.rfind('\n', 0, i) + 1
            m = _synchre(str, i, limit)
            if m and not is_char_in_string(m.start()):
                pos = m.start()
                break
            limit = i
        if pos is None:
            m = _synchre(str)
            if m and not is_char_in_string(m.start()):
                pos = m.start()
            return pos
        i = pos + 1
        while 1:
            m = _synchre(str, i)
            if m:
                s, i = m.span()
                if not is_char_in_string(s):
                    pos = s
            else:
                break
        return pos

    def set_lo(self, lo):
        assert lo == 0 or self.str[lo - 1] == '\n'
        if lo > 0:
            self.str = self.str[lo:]
    _tran = {}
    _tran.update((ord(c), ord('(')) for c in '({[')
    _tran.update((ord(c), ord(')')) for c in ')}]')
    _tran.update((ord(c), ord(c)) for c in '"\'\\\n#')
    _tran = StringTranslatePseudoMapping(_tran, default_value=ord('x'))

    def _study1(self):
        if self.study_level >= 1:
            return
        self.study_level = 1
        str = self.str
        str = str.translate(self._tran)
        str = str.replace('xxxxxxxx', 'x')
        str = str.replace('xxxx', 'x')
        str = str.replace('xx', 'x')
        str = str.replace('xx', 'x')
        str = str.replace('\nx', '\n')
        continuation = C_NONE
        level = lno = 0
        self.goodlines = goodlines = [0]
        push_good = goodlines.append
        i, n = 0, len(str)
        while i < n:
            ch = str[i]
            i = i + 1
            if ch == 'x':
                continue
            if ch == '\n':
                lno = lno + 1
                if level == 0:
                    push_good(lno)
                continue
            if ch == '(':
                level = level + 1
                continue
            if ch == ')':
                if level:
                    level = level - 1
                continue
            if ch == '"' or ch == "'":
                quote = ch
                if str[i - 1:i + 2] == quote * 3:
                    quote = quote * 3
                firstlno = lno
                w = len(quote) - 1
                i = i + w
                while i < n:
                    ch = str[i]
                    i = i + 1
                    if ch == 'x':
                        continue
                    if str[i - 1:i + w] == quote:
                        i = i + w
                        break
                    if ch == '\n':
                        lno = lno + 1
                        if w == 0:
                            if level == 0:
                                push_good(lno)
                            break
                        continue
                    if ch == '\\':
                        assert i < n
                        if str[i] == '\n':
                            lno = lno + 1
                        i = i + 1
                        continue
                else:
                    if lno - 1 == firstlno:
                        continuation = C_STRING_FIRST_LINE
                    else:
                        continuation = C_STRING_NEXT_LINES
                continue
            if ch == '#':
                i = str.find('\n', i)
                assert i >= 0
                continue
            assert ch == '\\'
            assert i < n
            if str[i] == '\n':
                lno = lno + 1
                if i + 1 == n:
                    continuation = C_BACKSLASH
            i = i + 1
        if (continuation != C_STRING_FIRST_LINE and continuation !=
            C_STRING_NEXT_LINES and level > 0):
            continuation = C_BRACKET
        self.continuation = continuation
        assert (continuation == C_NONE) == (goodlines[-1] == lno)
        if goodlines[-1] != lno:
            push_good(lno)

    def get_continuation_type(self):
        self._study1()
        return self.continuation

    def _study2(self):
        if self.study_level >= 2:
            return
        self._study1()
        self.study_level = 2
        str, goodlines = self.str, self.goodlines
        i = len(goodlines) - 1
        p = len(str)
        while i:
            assert p
            q = p
            for nothing in range(goodlines[i - 1], goodlines[i]):
                p = str.rfind('\n', 0, p - 1) + 1
            if _junkre(str, p):
                i = i - 1
            else:
                break
        if i == 0:
            assert p == 0
            q = p
        self.stmt_start, self.stmt_end = p, q
        lastch = ''
        stack = []
        push_stack = stack.append
        bracketing = [(p, 0)]
        while p < q:
            m = _chew_ordinaryre(str, p, q)
            if m:
                newp = m.end()
                i = newp - 1
                while i >= p and str[i] in ' \t\n':
                    i = i - 1
                if i >= p:
                    lastch = str[i]
                p = newp
                if p >= q:
                    break
            ch = str[p]
            if ch in '([{':
                push_stack(p)
                bracketing.append((p, len(stack)))
                lastch = ch
                p = p + 1
                continue
            if ch in ')]}':
                if stack:
                    del stack[-1]
                lastch = ch
                p = p + 1
                bracketing.append((p, len(stack)))
                continue
            if ch == '"' or ch == "'":
                bracketing.append((p, len(stack) + 1))
                lastch = ch
                p = _match_stringre(str, p, q).end()
                bracketing.append((p, len(stack)))
                continue
            if ch == '#':
                bracketing.append((p, len(stack) + 1))
                p = str.find('\n', p, q) + 1
                assert p > 0
                bracketing.append((p, len(stack)))
                continue
            assert ch == '\\'
            p = p + 1
            assert p < q
            if str[p] != '\n':
                lastch = ch + str[p]
            p = p + 1
        self.lastch = lastch
        if stack:
            self.lastopenbracketpos = stack[-1]
        self.stmt_bracketing = tuple(bracketing)

    def compute_bracket_indent(self):
        self._study2()
        assert self.continuation == C_BRACKET
        j = self.lastopenbracketpos
        str = self.str
        n = len(str)
        origi = i = str.rfind('\n', 0, j) + 1
        j = j + 1
        while j < n:
            m = _itemre(str, j)
            if m:
                j = m.end() - 1
                extra = 0
                break
            else:
                i = j = str.find('\n', j) + 1
        else:
            j = i = origi
            while str[j] in ' \t':
                j = j + 1
            extra = self.indentwidth
        return len(str[i:j].expandtabs(self.tabwidth)) + extra

    def get_num_lines_in_stmt(self):
        self._study1()
        goodlines = self.goodlines
        return goodlines[-1] - goodlines[-2]

    def compute_backslash_indent(self):
        self._study2()
        assert self.continuation == C_BACKSLASH
        str = self.str
        i = self.stmt_start
        while str[i] in ' \t':
            i = i + 1
        startpos = i
        endpos = str.find('\n', startpos) + 1
        found = level = 0
        while i < endpos:
            ch = str[i]
            if ch in '([{':
                level = level + 1
                i = i + 1
            elif ch in ')]}':
                if level:
                    level = level - 1
                i = i + 1
            elif ch == '"' or ch == "'":
                i = _match_stringre(str, i, endpos).end()
            elif ch == '#':
                break
            elif level == 0 and ch == '=' and (i == 0 or str[i - 1] not in
                '=<>!') and str[i + 1] != '=':
                found = 1
                break
            else:
                i = i + 1
        if found:
            i = i + 1
            found = re.match('\\s*\\\\', str[i:endpos]) is None
        if not found:
            i = startpos
            while str[i] not in ' \t\n':
                i = i + 1
        return len(str[self.stmt_start:i].expandtabs(self.tabwidth)) + 1

    def get_base_indent_string(self):
        self._study2()
        i, n = self.stmt_start, self.stmt_end
        j = i
        str = self.str
        while j < n and str[j] in ' \t':
            j = j + 1
        return str[i:j]

    def is_block_opener(self):
        self._study2()
        return self.lastch == ':'

    def is_block_closer(self):
        self._study2()
        return _closere(self.str, self.stmt_start) is not None
    lastopenbracketpos = None

    def get_last_open_bracket_pos(self):
        self._study2()
        return self.lastopenbracketpos
    stmt_bracketing = None

    def get_last_stmt_bracketing(self):
        self._study2()
        return self.stmt_bracketing
