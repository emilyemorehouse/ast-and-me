"""
csv.py - read/write/investigate CSV files
"""
import re
from _csv import Error, __version__, writer, reader, register_dialect, unregister_dialect, get_dialect, list_dialects, field_size_limit, QUOTE_MINIMAL, QUOTE_ALL, QUOTE_NONNUMERIC, QUOTE_NONE, __doc__
from _csv import Dialect as _Dialect
from collections import OrderedDict
from io import StringIO
__all__ = ['QUOTE_MINIMAL', 'QUOTE_ALL', 'QUOTE_NONNUMERIC', 'QUOTE_NONE',
    'Error', 'Dialect', '__doc__', 'excel', 'excel_tab', 'field_size_limit',
    'reader', 'writer', 'register_dialect', 'get_dialect', 'list_dialects',
    'Sniffer', 'unregister_dialect', '__version__', 'DictReader',
    'DictWriter', 'unix_dialect']


class Dialect:
    """Describe a CSV dialect.

    This must be subclassed (see csv.excel).  Valid attributes are:
    delimiter, quotechar, escapechar, doublequote, skipinitialspace,
    lineterminator, quoting.

    """
    _name = ''
    _valid = False
    delimiter = None
    quotechar = None
    escapechar = None
    doublequote = None
    skipinitialspace = None
    lineterminator = None
    quoting = None

    def __init__(self):
        if self.__class__ != Dialect:
            self._valid = True
        self._validate()

    def _validate(self):
        try:
            _Dialect(self)
        except TypeError as e:
            raise Error(str(e))


class excel(Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\r\n'
    quoting = QUOTE_MINIMAL


register_dialect('excel', excel)


class excel_tab(excel):
    """Describe the usual properties of Excel-generated TAB-delimited files."""
    delimiter = '\t'


register_dialect('excel-tab', excel_tab)


class unix_dialect(Dialect):
    """Describe the usual properties of Unix-generated CSV files."""
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = QUOTE_ALL


register_dialect('unix', unix_dialect)


class DictReader:

    def __init__(self, f, fieldnames=None, restkey=None, restval=None,
        dialect='excel', *args, **kwds):
        self._fieldnames = fieldnames
        self.restkey = restkey
        self.restval = restval
        self.reader = reader(f, dialect, *args, **kwds)
        self.dialect = dialect
        self.line_num = 0

    def __iter__(self):
        return self

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            try:
                self._fieldnames = next(self.reader)
            except StopIteration:
                pass
        self.line_num = self.reader.line_num
        return self._fieldnames

    @fieldnames.setter
    def fieldnames(self, value):
        self._fieldnames = value

    def __next__(self):
        if self.line_num == 0:
            self.fieldnames
        row = next(self.reader)
        self.line_num = self.reader.line_num
        while row == []:
            row = next(self.reader)
        d = OrderedDict(zip(self.fieldnames, row))
        lf = len(self.fieldnames)
        lr = len(row)
        if lf < lr:
            d[self.restkey] = row[lf:]
        elif lf > lr:
            for key in self.fieldnames[lr:]:
                d[key] = self.restval
        return d


class DictWriter:

    def __init__(self, f, fieldnames, restval='', extrasaction='raise',
        dialect='excel', *args, **kwds):
        self.fieldnames = fieldnames
        self.restval = restval
        if extrasaction.lower() not in ('raise', 'ignore'):
            raise ValueError(
                "extrasaction (%s) must be 'raise' or 'ignore'" % extrasaction)
        self.extrasaction = extrasaction
        self.writer = writer(f, dialect, *args, **kwds)

    def writeheader(self):
        header = dict(zip(self.fieldnames, self.fieldnames))
        self.writerow(header)

    def _dict_to_list(self, rowdict):
        if self.extrasaction == 'raise':
            wrong_fields = rowdict.keys() - self.fieldnames
            if wrong_fields:
                raise ValueError('dict contains fields not in fieldnames: ' +
                    ', '.join([repr(x) for x in wrong_fields]))
        return (rowdict.get(key, self.restval) for key in self.fieldnames)

    def writerow(self, rowdict):
        return self.writer.writerow(self._dict_to_list(rowdict))

    def writerows(self, rowdicts):
        return self.writer.writerows(map(self._dict_to_list, rowdicts))


try:
    complex
except NameError:
    complex = float


class Sniffer:
    """
    "Sniffs" the format of a CSV file (i.e. delimiter, quotechar)
    Returns a Dialect object.
    """

    def __init__(self):
        self.preferred = [',', '\t', ';', ' ', ':']

    def sniff(self, sample, delimiters=None):
        """
        Returns a dialect (or None) corresponding to the sample
        """
        quotechar, doublequote, delimiter, skipinitialspace = (self.
            _guess_quote_and_delimiter(sample, delimiters))
        if not delimiter:
            delimiter, skipinitialspace = self._guess_delimiter(sample,
                delimiters)
        if not delimiter:
            raise Error('Could not determine delimiter')


        class dialect(Dialect):
            _name = 'sniffed'
            lineterminator = '\r\n'
            quoting = QUOTE_MINIMAL
        dialect.doublequote = doublequote
        dialect.delimiter = delimiter
        dialect.quotechar = quotechar or '"'
        dialect.skipinitialspace = skipinitialspace
        return dialect

    def _guess_quote_and_delimiter(self, data, delimiters):
        """
        Looks for text enclosed between two identical quotes
        (the probable quotechar) which are preceded and followed
        by the same character (the probable delimiter).
        For example:
                         ,'some text',
        The quote with the most wins, same with the delimiter.
        If there is no quotechar the delimiter can't be determined
        this way.
        """
        matches = []
        for restr in (
            '(?P<delim>[^\\w\\n"\\\'])(?P<space> ?)(?P<quote>["\\\']).*?(?P=quote)(?P=delim)'
            ,
            '(?:^|\\n)(?P<quote>["\\\']).*?(?P=quote)(?P<delim>[^\\w\\n"\\\'])(?P<space> ?)'
            ,
            '(?P<delim>>[^\\w\\n"\\\'])(?P<space> ?)(?P<quote>["\\\']).*?(?P=quote)(?:$|\\n)'
            , '(?:^|\\n)(?P<quote>["\\\']).*?(?P=quote)(?:$|\\n)'):
            regexp = re.compile(restr, re.DOTALL | re.MULTILINE)
            matches = regexp.findall(data)
            if matches:
                break
        if not matches:
            return '', False, None, 0
        quotes = {}
        delims = {}
        spaces = 0
        groupindex = regexp.groupindex
        for m in matches:
            n = groupindex['quote'] - 1
            key = m[n]
            if key:
                quotes[key] = quotes.get(key, 0) + 1
            try:
                n = groupindex['delim'] - 1
                key = m[n]
            except KeyError:
                continue
            if key and (delimiters is None or key in delimiters):
                delims[key] = delims.get(key, 0) + 1
            try:
                n = groupindex['space'] - 1
            except KeyError:
                continue
            if m[n]:
                spaces += 1
        quotechar = max(quotes, key=quotes.get)
        if delims:
            delim = max(delims, key=delims.get)
            skipinitialspace = delims[delim] == spaces
            if delim == '\n':
                delim = ''
        else:
            delim = ''
            skipinitialspace = 0
        dq_regexp = re.compile(
            '((%(delim)s)|^)\\W*%(quote)s[^%(delim)s\\n]*%(quote)s[^%(delim)s\\n]*%(quote)s\\W*((%(delim)s)|$)'
             % {'delim': re.escape(delim), 'quote': quotechar}, re.MULTILINE)
        if dq_regexp.search(data):
            doublequote = True
        else:
            doublequote = False
        return quotechar, doublequote, delim, skipinitialspace

    def _guess_delimiter(self, data, delimiters):
        """
        The delimiter /should/ occur the same number of times on
        each row. However, due to malformed data, it may not. We don't want
        an all or nothing approach, so we allow for small variations in this
        number.
          1) build a table of the frequency of each character on every line.
          2) build a table of frequencies of this frequency (meta-frequency?),
             e.g.  'x occurred 5 times in 10 rows, 6 times in 1000 rows,
             7 times in 2 rows'
          3) use the mode of the meta-frequency to determine the /expected/
             frequency for that character
          4) find out how often the character actually meets that goal
          5) the character that best meets its goal is the delimiter
        For performance reasons, the data is evaluated in chunks, so it can
        try and evaluate the smallest portion of the data possible, evaluating
        additional chunks as necessary.
        """
        data = list(filter(None, data.split('\n')))
        ascii = [chr(c) for c in range(127)]
        chunkLength = min(10, len(data))
        iteration = 0
        charFrequency = {}
        modes = {}
        delims = {}
        start, end = 0, min(chunkLength, len(data))
        while start < len(data):
            iteration += 1
            for line in data[start:end]:
                for char in ascii:
                    metaFrequency = charFrequency.get(char, {})
                    freq = line.count(char)
                    metaFrequency[freq] = metaFrequency.get(freq, 0) + 1
                    charFrequency[char] = metaFrequency
            for char in charFrequency.keys():
                items = list(charFrequency[char].items())
                if len(items) == 1 and items[0][0] == 0:
                    continue
                if len(items) > 1:
                    modes[char] = max(items, key=lambda x: x[1])
                    items.remove(modes[char])
                    modes[char] = modes[char][0], modes[char][1] - sum(item
                        [1] for item in items)
                else:
                    modes[char] = items[0]
            modeList = modes.items()
            total = float(chunkLength * iteration)
            consistency = 1.0
            threshold = 0.9
            while len(delims) == 0 and consistency >= threshold:
                for k, v in modeList:
                    if v[0] > 0 and v[1] > 0:
                        if v[1] / total >= consistency and (delimiters is
                            None or k in delimiters):
                            delims[k] = v
                consistency -= 0.01
            if len(delims) == 1:
                delim = list(delims.keys())[0]
                skipinitialspace = data[0].count(delim) == data[0].count(
                    '%c ' % delim)
                return delim, skipinitialspace
            start = end
            end += chunkLength
        if not delims:
            return '', 0
        if len(delims) > 1:
            for d in self.preferred:
                if d in delims.keys():
                    skipinitialspace = data[0].count(d) == data[0].count(
                        '%c ' % d)
                    return d, skipinitialspace
        items = [(v, k) for k, v in delims.items()]
        items.sort()
        delim = items[-1][1]
        skipinitialspace = data[0].count(delim) == data[0].count('%c ' % delim)
        return delim, skipinitialspace

    def has_header(self, sample):
        rdr = reader(StringIO(sample), self.sniff(sample))
        header = next(rdr)
        columns = len(header)
        columnTypes = {}
        for i in range(columns):
            columnTypes[i] = None
        checked = 0
        for row in rdr:
            if checked > 20:
                break
            checked += 1
            if len(row) != columns:
                continue
            for col in list(columnTypes.keys()):
                for thisType in [int, float, complex]:
                    try:
                        thisType(row[col])
                        break
                    except (ValueError, OverflowError):
                        pass
                else:
                    thisType = len(row[col])
                if thisType != columnTypes[col]:
                    if columnTypes[col] is None:
                        columnTypes[col] = thisType
                    else:
                        del columnTypes[col]
        hasHeader = 0
        for col, colType in columnTypes.items():
            if type(colType) == type(0):
                if len(header[col]) != colType:
                    hasHeader += 1
                else:
                    hasHeader -= 1
            else:
                try:
                    colType(header[col])
                except (ValueError, TypeError):
                    hasHeader += 1
                else:
                    hasHeader -= 1
        return hasHeader > 0
