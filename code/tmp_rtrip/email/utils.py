"""Miscellaneous utilities."""
__all__ = ['collapse_rfc2231_value', 'decode_params', 'decode_rfc2231',
    'encode_rfc2231', 'formataddr', 'formatdate', 'format_datetime',
    'getaddresses', 'make_msgid', 'mktime_tz', 'parseaddr', 'parsedate',
    'parsedate_tz', 'parsedate_to_datetime', 'unquote']
import os
import re
import time
import random
import socket
import datetime
import urllib.parse
from email._parseaddr import quote
from email._parseaddr import AddressList as _AddressList
from email._parseaddr import mktime_tz
from email._parseaddr import parsedate, parsedate_tz, _parsedate_tz
from email.charset import Charset
COMMASPACE = ', '
EMPTYSTRING = ''
UEMPTYSTRING = ''
CRLF = '\r\n'
TICK = "'"
specialsre = re.compile('[][\\\\()<>@,:;".]')
escapesre = re.compile('[\\\\"]')


def _has_surrogates(s):
    """Return True if s contains surrogate-escaped binary data."""
    try:
        s.encode()
        return False
    except UnicodeEncodeError:
        return True


def _sanitize(string):
    original_bytes = string.encode('utf-8', 'surrogateescape')
    return original_bytes.decode('utf-8', 'replace')


def formataddr(pair, charset='utf-8'):
    """The inverse of parseaddr(), this takes a 2-tuple of the form
    (realname, email_address) and returns the string value suitable
    for an RFC 2822 From, To or Cc header.

    If the first element of pair is false, then the second element is
    returned unmodified.

    Optional charset if given is the character set that is used to encode
    realname in case realname is not ASCII safe.  Can be an instance of str or
    a Charset-like object which has a header_encode method.  Default is
    'utf-8'.
    """
    name, address = pair
    address.encode('ascii')
    if name:
        try:
            name.encode('ascii')
        except UnicodeEncodeError:
            if isinstance(charset, str):
                charset = Charset(charset)
            encoded_name = charset.header_encode(name)
            return '%s <%s>' % (encoded_name, address)
        else:
            quotes = ''
            if specialsre.search(name):
                quotes = '"'
            name = escapesre.sub('\\\\\\g<0>', name)
            return '%s%s%s <%s>' % (quotes, name, quotes, address)
    return address


def getaddresses(fieldvalues):
    """Return a list of (REALNAME, EMAIL) for each fieldvalue."""
    all = COMMASPACE.join(fieldvalues)
    a = _AddressList(all)
    return a.addresslist


ecre = re.compile(
    """
  =\\?                   # literal =?
  (?P<charset>[^?]*?)   # non-greedy up to the next ? is the charset
  \\?                    # literal ?
  (?P<encoding>[qb])    # either a "q" or a "b", case insensitive
  \\?                    # literal ?
  (?P<atom>.*?)         # non-greedy up to the next ?= is the atom
  \\?=                   # literal ?=
  """
    , re.VERBOSE | re.IGNORECASE)


def _format_timetuple_and_zone(timetuple, zone):
    return '%s, %02d %s %04d %02d:%02d:%02d %s' % (['Mon', 'Tue', 'Wed',
        'Thu', 'Fri', 'Sat', 'Sun'][timetuple[6]], timetuple[2], ['Jan',
        'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
        'Nov', 'Dec'][timetuple[1] - 1], timetuple[0], timetuple[3],
        timetuple[4], timetuple[5], zone)


def formatdate(timeval=None, localtime=False, usegmt=False):
    """Returns a date string as specified by RFC 2822, e.g.:

    Fri, 09 Nov 2001 01:08:47 -0000

    Optional timeval if given is a floating point time value as accepted by
    gmtime() and localtime(), otherwise the current time is used.

    Optional localtime is a flag that when True, interprets timeval, and
    returns a date relative to the local timezone instead of UTC, properly
    taking daylight savings time into account.

    Optional argument usegmt means that the timezone is written out as
    an ascii string, not numeric one (so "GMT" instead of "+0000"). This
    is needed for HTTP, and is only used when localtime==False.
    """
    if timeval is None:
        timeval = time.time()
    if localtime or usegmt:
        dt = datetime.datetime.fromtimestamp(timeval, datetime.timezone.utc)
    else:
        dt = datetime.datetime.utcfromtimestamp(timeval)
    if localtime:
        dt = dt.astimezone()
        usegmt = False
    return format_datetime(dt, usegmt)


def format_datetime(dt, usegmt=False):
    """Turn a datetime into a date string as specified in RFC 2822.

    If usegmt is True, dt must be an aware datetime with an offset of zero.  In
    this case 'GMT' will be rendered instead of the normal +0000 required by
    RFC2822.  This is to support HTTP headers involving date stamps.
    """
    now = dt.timetuple()
    if usegmt:
        if dt.tzinfo is None or dt.tzinfo != datetime.timezone.utc:
            raise ValueError('usegmt option requires a UTC datetime')
        zone = 'GMT'
    elif dt.tzinfo is None:
        zone = '-0000'
    else:
        zone = dt.strftime('%z')
    return _format_timetuple_and_zone(now, zone)


def make_msgid(idstring=None, domain=None):
    """Returns a string suitable for RFC 2822 compliant Message-ID, e.g:

    <142480216486.20800.16526388040877946887@nightshade.la.mastaler.com>

    Optional idstring if given is a string used to strengthen the
    uniqueness of the message id.  Optional domain if given provides the
    portion of the message id after the '@'.  It defaults to the locally
    defined hostname.
    """
    timeval = int(time.time() * 100)
    pid = os.getpid()
    randint = random.getrandbits(64)
    if idstring is None:
        idstring = ''
    else:
        idstring = '.' + idstring
    if domain is None:
        domain = socket.getfqdn()
    msgid = '<%d.%d.%d%s@%s>' % (timeval, pid, randint, idstring, domain)
    return msgid


def parsedate_to_datetime(data):
    *dtuple, tz = _parsedate_tz(data)
    if tz is None:
        return datetime.datetime(*dtuple[:6])
    return datetime.datetime(*dtuple[:6], tzinfo=datetime.timezone(datetime
        .timedelta(seconds=tz)))


def parseaddr(addr):
    addrs = _AddressList(addr).addresslist
    if not addrs:
        return '', ''
    return addrs[0]


def unquote(str):
    """Remove quotes from a string."""
    if len(str) > 1:
        if str.startswith('"') and str.endswith('"'):
            return str[1:-1].replace('\\\\', '\\').replace('\\"', '"')
        if str.startswith('<') and str.endswith('>'):
            return str[1:-1]
    return str


def decode_rfc2231(s):
    """Decode string according to RFC 2231"""
    parts = s.split(TICK, 2)
    if len(parts) <= 2:
        return None, None, s
    return parts


def encode_rfc2231(s, charset=None, language=None):
    """Encode string according to RFC 2231.

    If neither charset nor language is given, then s is returned as-is.  If
    charset is given but not language, the string is encoded using the empty
    string for language.
    """
    s = urllib.parse.quote(s, safe='', encoding=charset or 'ascii')
    if charset is None and language is None:
        return s
    if language is None:
        language = ''
    return "%s'%s'%s" % (charset, language, s)


rfc2231_continuation = re.compile('^(?P<name>\\w+)\\*((?P<num>[0-9]+)\\*?)?$',
    re.ASCII)


def decode_params(params):
    """Decode parameters list according to RFC 2231.

    params is a sequence of 2-tuples containing (param name, string value).
    """
    params = params[:]
    new_params = []
    rfc2231_params = {}
    name, value = params.pop(0)
    new_params.append((name, value))
    while params:
        name, value = params.pop(0)
        if name.endswith('*'):
            encoded = True
        else:
            encoded = False
        value = unquote(value)
        mo = rfc2231_continuation.match(name)
        if mo:
            name, num = mo.group('name', 'num')
            if num is not None:
                num = int(num)
            rfc2231_params.setdefault(name, []).append((num, value, encoded))
        else:
            new_params.append((name, '"%s"' % quote(value)))
    if rfc2231_params:
        for name, continuations in rfc2231_params.items():
            value = []
            extended = False
            continuations.sort()
            for num, s, encoded in continuations:
                if encoded:
                    s = urllib.parse.unquote(s, encoding='latin-1')
                    extended = True
                value.append(s)
            value = quote(EMPTYSTRING.join(value))
            if extended:
                charset, language, value = decode_rfc2231(value)
                new_params.append((name, (charset, language, '"%s"' % value)))
            else:
                new_params.append((name, '"%s"' % value))
    return new_params


def collapse_rfc2231_value(value, errors='replace', fallback_charset='us-ascii'
    ):
    if not isinstance(value, tuple) or len(value) != 3:
        return unquote(value)
    charset, language, text = value
    if charset is None:
        charset = fallback_charset
    rawbytes = bytes(text, 'raw-unicode-escape')
    try:
        return str(rawbytes, charset, errors)
    except LookupError:
        return unquote(text)


def localtime(dt=None, isdst=-1):
    """Return local time as an aware datetime object.

    If called without arguments, return current time.  Otherwise *dt*
    argument should be a datetime instance, and it is converted to the
    local time zone according to the system time zone database.  If *dt* is
    naive (that is, dt.tzinfo is None), it is assumed to be in local time.
    In this case, a positive or zero value for *isdst* causes localtime to
    presume initially that summer time (for example, Daylight Saving Time)
    is or is not (respectively) in effect for the specified time.  A
    negative value for *isdst* causes the localtime() function to attempt
    to divine whether summer time is in effect for the specified time.

    """
    if dt is None:
        return datetime.datetime.now(datetime.timezone.utc).astimezone()
    if dt.tzinfo is not None:
        return dt.astimezone()
    tm = dt.timetuple()[:-1] + (isdst,)
    seconds = time.mktime(tm)
    localtm = time.localtime(seconds)
    try:
        delta = datetime.timedelta(seconds=localtm.tm_gmtoff)
        tz = datetime.timezone(delta, localtm.tm_zone)
    except AttributeError:
        delta = dt - datetime.datetime(*time.gmtime(seconds)[:6])
        dst = time.daylight and localtm.tm_isdst > 0
        gmtoff = -(time.altzone if dst else time.timezone)
        if delta == datetime.timedelta(seconds=gmtoff):
            tz = datetime.timezone(delta, time.tzname[dst])
        else:
            tz = datetime.timezone(delta)
    return dt.replace(tzinfo=tz)
