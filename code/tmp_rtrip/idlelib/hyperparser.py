"""Provide advanced parsing abilities for ParenMatch and other extensions.

HyperParser uses PyParser.  PyParser mostly gives information on the
proper indentation of code.  HyperParser gives additional information on
the structure of code.
"""
from keyword import iskeyword
import string
from idlelib import pyparse
_ASCII_ID_CHARS = frozenset(string.ascii_letters + string.digits + '_')
_ASCII_ID_FIRST_CHARS = frozenset(string.ascii_letters + '_')
_IS_ASCII_ID_CHAR = [(chr(x) in _ASCII_ID_CHARS) for x in range(128)]
_IS_ASCII_ID_FIRST_CHAR = [(chr(x) in _ASCII_ID_FIRST_CHARS) for x in range
    (128)]


class HyperParser:

    def __init__(self, editwin, index):
        """To initialize, analyze the surroundings of the given index."""
        self.editwin = editwin
        self.text = text = editwin.text
        parser = pyparse.Parser(editwin.indentwidth, editwin.tabwidth)

        def index2line(index):
            return int(float(index))
        lno = index2line(text.index(index))
        if not editwin.context_use_ps1:
            for context in editwin.num_context_lines:
                startat = max(lno - context, 1)
                startatindex = repr(startat) + '.0'
                stopatindex = '%d.end' % lno
                parser.set_str(text.get(startatindex, stopatindex) + ' \n')
                bod = parser.find_good_parse_start(editwin.
                    _build_char_in_string_func(startatindex))
                if bod is not None or startat == 1:
                    break
            parser.set_lo(bod or 0)
        else:
            r = text.tag_prevrange('console', index)
            if r:
                startatindex = r[1]
            else:
                startatindex = '1.0'
            stopatindex = '%d.end' % lno
            parser.set_str(text.get(startatindex, stopatindex) + ' \n')
            parser.set_lo(0)
        self.rawtext = parser.str[:-2]
        self.stopatindex = stopatindex
        self.bracketing = parser.get_last_stmt_bracketing()
        self.isopener = [(i > 0 and self.bracketing[i][1] > self.bracketing
            [i - 1][1]) for i in range(len(self.bracketing))]
        self.set_index(index)

    def set_index(self, index):
        """Set the index to which the functions relate.

        The index must be in the same statement.
        """
        indexinrawtext = len(self.rawtext) - len(self.text.get(index, self.
            stopatindex))
        if indexinrawtext < 0:
            raise ValueError('Index %s precedes the analyzed statement' % index
                )
        self.indexinrawtext = indexinrawtext
        self.indexbracket = 0
        while self.indexbracket < len(self.bracketing) - 1 and self.bracketing[
            self.indexbracket + 1][0] < self.indexinrawtext:
            self.indexbracket += 1
        if self.indexbracket < len(self.bracketing) - 1 and self.bracketing[
            self.indexbracket + 1][0
            ] == self.indexinrawtext and not self.isopener[self.
            indexbracket + 1]:
            self.indexbracket += 1

    def is_in_string(self):
        """Is the index given to the HyperParser in a string?"""
        return self.isopener[self.indexbracket] and self.rawtext[self.
            bracketing[self.indexbracket][0]] in ('"', "'")

    def is_in_code(self):
        """Is the index given to the HyperParser in normal code?"""
        return not self.isopener[self.indexbracket] or self.rawtext[self.
            bracketing[self.indexbracket][0]] not in ('#', '"', "'")

    def get_surrounding_brackets(self, openers='([{', mustclose=False):
        """Return bracket indexes or None.

        If the index given to the HyperParser is surrounded by a
        bracket defined in openers (or at least has one before it),
        return the indices of the opening bracket and the closing
        bracket (or the end of line, whichever comes first).

        If it is not surrounded by brackets, or the end of line comes
        before the closing bracket and mustclose is True, returns None.
        """
        bracketinglevel = self.bracketing[self.indexbracket][1]
        before = self.indexbracket
        while not self.isopener[before] or self.rawtext[self.bracketing[
            before][0]] not in openers or self.bracketing[before][1
            ] > bracketinglevel:
            before -= 1
            if before < 0:
                return None
            bracketinglevel = min(bracketinglevel, self.bracketing[before][1])
        after = self.indexbracket + 1
        while after < len(self.bracketing) and self.bracketing[after][1
            ] >= bracketinglevel:
            after += 1
        beforeindex = self.text.index('%s-%dc' % (self.stopatindex, len(
            self.rawtext) - self.bracketing[before][0]))
        if after >= len(self.bracketing) or self.bracketing[after][0] > len(
            self.rawtext):
            if mustclose:
                return None
            afterindex = self.stopatindex
        else:
            afterindex = self.text.index('%s-%dc' % (self.stopatindex, len(
                self.rawtext) - (self.bracketing[after][0] - 1)))
        return beforeindex, afterindex
    _ID_KEYWORDS = frozenset({'True', 'False', 'None'})

    @classmethod
    def _eat_identifier(cls, str, limit, pos):
        """Given a string and pos, return the number of chars in the
        identifier which ends at pos, or 0 if there is no such one.

        This ignores non-identifier eywords are not identifiers.
        """
        is_ascii_id_char = _IS_ASCII_ID_CHAR
        i = pos
        while i > limit and (ord(str[i - 1]) < 128 and is_ascii_id_char[ord
            (str[i - 1])]):
            i -= 1
        if i > limit and ord(str[i - 1]) >= 128:
            while i - 4 >= limit and ('a' + str[i - 4:pos]).isidentifier():
                i -= 4
            if i - 2 >= limit and ('a' + str[i - 2:pos]).isidentifier():
                i -= 2
            if i - 1 >= limit and ('a' + str[i - 1:pos]).isidentifier():
                i -= 1
            if not str[i:pos].isidentifier():
                return 0
        elif i < pos:
            if not _IS_ASCII_ID_FIRST_CHAR[ord(str[i])]:
                return 0
        if i < pos and (iskeyword(str[i:pos]) and str[i:pos] not in cls.
            _ID_KEYWORDS):
            return 0
        return pos - i
    _whitespace_chars = ' \t\n\\'

    def get_expression(self):
        """Return a string with the Python expression which ends at the
        given index, which is empty if there is no real one.
        """
        if not self.is_in_code():
            raise ValueError(
                'get_expression should only be calledif index is inside a code.'
                )
        rawtext = self.rawtext
        bracketing = self.bracketing
        brck_index = self.indexbracket
        brck_limit = bracketing[brck_index][0]
        pos = self.indexinrawtext
        last_identifier_pos = pos
        postdot_phase = True
        while 1:
            while 1:
                if pos > brck_limit and rawtext[pos - 1
                    ] in self._whitespace_chars:
                    pos -= 1
                elif not postdot_phase and pos > brck_limit and rawtext[pos - 1
                    ] == '.':
                    pos -= 1
                    postdot_phase = True
                elif pos == brck_limit and brck_index > 0 and rawtext[
                    bracketing[brck_index - 1][0]] == '#':
                    brck_index -= 2
                    brck_limit = bracketing[brck_index][0]
                    pos = bracketing[brck_index + 1][0]
                else:
                    break
            if not postdot_phase:
                break
            ret = self._eat_identifier(rawtext, brck_limit, pos)
            if ret:
                pos = pos - ret
                last_identifier_pos = pos
                postdot_phase = False
            elif pos == brck_limit:
                level = bracketing[brck_index][1]
                while brck_index > 0 and bracketing[brck_index - 1][1] > level:
                    brck_index -= 1
                if bracketing[brck_index][0] == brck_limit:
                    break
                pos = bracketing[brck_index][0]
                brck_index -= 1
                brck_limit = bracketing[brck_index][0]
                last_identifier_pos = pos
                if rawtext[pos] in '([':
                    pass
                else:
                    if rawtext[pos] in '\'"':
                        while pos > 0 and rawtext[pos - 1] in 'rRbBuU':
                            pos -= 1
                        last_identifier_pos = pos
                    break
            else:
                break
        return rawtext[last_identifier_pos:self.indexinrawtext]


if __name__ == '__main__':
    import unittest
    unittest.main('idlelib.idle_test.test_hyperparser', verbosity=2)
