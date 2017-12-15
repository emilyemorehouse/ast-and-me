"""
General functions for HTML manipulation.
"""
import re as _re
from html.entities import html5 as _html5
__all__ = ['escape', 'unescape']


def escape(s, quote=True):
    """
    Replace special characters "&", "<" and ">" to HTML-safe sequences.
    If the optional flag quote is true (the default), the quotation mark
    characters, both double quote (") and single quote (') characters are also
    translated.
    """
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    if quote:
        s = s.replace('"', '&quot;')
        s = s.replace("'", '&#x27;')
    return s


_invalid_charrefs = {(0): '�', (13): '\r', (128): '€', (129): '\x81', (130):
    '‚', (131): 'ƒ', (132): '„', (133): '…', (134): '†', (135): '‡', (136):
    'ˆ', (137): '‰', (138): 'Š', (139): '‹', (140): 'Œ', (141): '\x8d', (
    142): 'Ž', (143): '\x8f', (144): '\x90', (145): '‘', (146): '’', (147):
    '“', (148): '”', (149): '•', (150): '–', (151): '—', (152): '˜', (153):
    '™', (154): 'š', (155): '›', (156): 'œ', (157): '\x9d', (158): 'ž', (
    159): 'Ÿ'}
_invalid_codepoints = {1, 2, 3, 4, 5, 6, 7, 8, 14, 15, 16, 17, 18, 19, 20, 
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 127, 128, 129, 130, 131, 
    132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 
    146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 
    64976, 64977, 64978, 64979, 64980, 64981, 64982, 64983, 64984, 64985, 
    64986, 64987, 64988, 64989, 64990, 64991, 64992, 64993, 64994, 64995, 
    64996, 64997, 64998, 64999, 65000, 65001, 65002, 65003, 65004, 65005, 
    65006, 65007, 11, 65534, 65535, 131070, 131071, 196606, 196607, 262142,
    262143, 327678, 327679, 393214, 393215, 458750, 458751, 524286, 524287,
    589822, 589823, 655358, 655359, 720894, 720895, 786430, 786431, 851966,
    851967, 917502, 917503, 983038, 983039, 1048574, 1048575, 1114110, 1114111}


def _replace_charref(s):
    s = s.group(1)
    if s[0] == '#':
        if s[1] in 'xX':
            num = int(s[2:].rstrip(';'), 16)
        else:
            num = int(s[1:].rstrip(';'))
        if num in _invalid_charrefs:
            return _invalid_charrefs[num]
        if 55296 <= num <= 57343 or num > 1114111:
            return '�'
        if num in _invalid_codepoints:
            return ''
        return chr(num)
    else:
        if s in _html5:
            return _html5[s]
        for x in range(len(s) - 1, 1, -1):
            if s[:x] in _html5:
                return _html5[s[:x]] + s[x:]
        else:
            return '&' + s


_charref = _re.compile(
    '&(#[0-9]+;?|#[xX][0-9a-fA-F]+;?|[^\\t\\n\\f <&#;]{1,32};?)')


def unescape(s):
    """
    Convert all named and numeric character references (e.g. &gt;, &#62;,
    &x3e;) in the string s to the corresponding unicode characters.
    This function uses the rules defined by the HTML 5 standard
    for both valid and invalid character references, and the list of
    HTML 5 named character references defined in html.entities.html5.
    """
    if '&' not in s:
        return s
    return _charref.sub(_replace_charref, s)
