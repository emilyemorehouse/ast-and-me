"""A collection of string constants.

Public module variables:

whitespace -- a string containing all ASCII whitespace
ascii_lowercase -- a string containing all ASCII lowercase letters
ascii_uppercase -- a string containing all ASCII uppercase letters
ascii_letters -- a string containing all ASCII letters
digits -- a string containing all ASCII decimal digits
hexdigits -- a string containing all ASCII hexadecimal digits
octdigits -- a string containing all ASCII octal digits
punctuation -- a string containing all ASCII punctuation characters
printable -- a string containing all ASCII characters considered printable

"""
__all__ = ['ascii_letters', 'ascii_lowercase', 'ascii_uppercase',
    'capwords', 'digits', 'hexdigits', 'octdigits', 'printable',
    'punctuation', 'whitespace', 'Formatter', 'Template']
import _string
whitespace = ' \t\n\r\x0b\x0c'
ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ascii_letters = ascii_lowercase + ascii_uppercase
digits = '0123456789'
hexdigits = digits + 'abcdef' + 'ABCDEF'
octdigits = '01234567'
punctuation = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
printable = digits + ascii_letters + punctuation + whitespace


def capwords(s, sep=None):
    """capwords(s [,sep]) -> string

    Split the argument into words using split, capitalize each
    word using capitalize, and join the capitalized words using
    join.  If the optional second argument sep is absent or None,
    runs of whitespace characters are replaced by a single space
    and leading and trailing whitespace are removed, otherwise
    sep is used to split and join the words.

    """
    return (sep or ' ').join(x.capitalize() for x in s.split(sep))


import re as _re
from collections import ChainMap as _ChainMap


class _TemplateMetaclass(type):
    pattern = """
    %(delim)s(?:
      (?P<escaped>%(delim)s) |   # Escape sequence of two delimiters
      (?P<named>%(id)s)      |   # delimiter and a Python identifier
      {(?P<braced>%(id)s)}   |   # delimiter and a braced identifier
      (?P<invalid>)              # Other ill-formed delimiter exprs
    )
    """

    def __init__(cls, name, bases, dct):
        super(_TemplateMetaclass, cls).__init__(name, bases, dct)
        if 'pattern' in dct:
            pattern = cls.pattern
        else:
            pattern = _TemplateMetaclass.pattern % {'delim': _re.escape(cls
                .delimiter), 'id': cls.idpattern}
        cls.pattern = _re.compile(pattern, cls.flags | _re.VERBOSE)


class Template(metaclass=_TemplateMetaclass):
    """A string class for supporting $-substitutions."""
    delimiter = '$'
    idpattern = '[_a-z][_a-z0-9]*'
    flags = _re.IGNORECASE

    def __init__(self, template):
        self.template = template

    def _invalid(self, mo):
        i = mo.start('invalid')
        lines = self.template[:i].splitlines(keepends=True)
        if not lines:
            colno = 1
            lineno = 1
        else:
            colno = i - len(''.join(lines[:-1]))
            lineno = len(lines)
        raise ValueError('Invalid placeholder in string: line %d, col %d' %
            (lineno, colno))

    def substitute(*args, **kws):
        if not args:
            raise TypeError(
                "descriptor 'substitute' of 'Template' object needs an argument"
                )
        self, *args = args
        if len(args) > 1:
            raise TypeError('Too many positional arguments')
        if not args:
            mapping = kws
        elif kws:
            mapping = _ChainMap(kws, args[0])
        else:
            mapping = args[0]

        def convert(mo):
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                return str(mapping[named])
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern', self.
                pattern)
        return self.pattern.sub(convert, self.template)

    def safe_substitute(*args, **kws):
        if not args:
            raise TypeError(
                "descriptor 'safe_substitute' of 'Template' object needs an argument"
                )
        self, *args = args
        if len(args) > 1:
            raise TypeError('Too many positional arguments')
        if not args:
            mapping = kws
        elif kws:
            mapping = _ChainMap(kws, args[0])
        else:
            mapping = args[0]

        def convert(mo):
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                try:
                    return str(mapping[named])
                except KeyError:
                    return mo.group()
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                return mo.group()
            raise ValueError('Unrecognized named group in pattern', self.
                pattern)
        return self.pattern.sub(convert, self.template)


class Formatter:

    def format(*args, **kwargs):
        if not args:
            raise TypeError(
                "descriptor 'format' of 'Formatter' object needs an argument")
        self, *args = args
        try:
            format_string, *args = args
        except ValueError:
            if 'format_string' in kwargs:
                format_string = kwargs.pop('format_string')
                import warnings
                warnings.warn(
                    "Passing 'format_string' as keyword argument is deprecated"
                    , DeprecationWarning, stacklevel=2)
            else:
                raise TypeError(
                    "format() missing 1 required positional argument: 'format_string'"
                    ) from None
        return self.vformat(format_string, args, kwargs)

    def vformat(self, format_string, args, kwargs):
        used_args = set()
        result, _ = self._vformat(format_string, args, kwargs, used_args, 2)
        self.check_unused_args(used_args, args, kwargs)
        return result

    def _vformat(self, format_string, args, kwargs, used_args,
        recursion_depth, auto_arg_index=0):
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')
        result = []
        for literal_text, field_name, format_spec, conversion in self.parse(
            format_string):
            if literal_text:
                result.append(literal_text)
            if field_name is not None:
                if field_name == '':
                    if auto_arg_index is False:
                        raise ValueError(
                            'cannot switch from manual field specification to automatic field numbering'
                            )
                    field_name = str(auto_arg_index)
                    auto_arg_index += 1
                elif field_name.isdigit():
                    if auto_arg_index:
                        raise ValueError(
                            'cannot switch from manual field specification to automatic field numbering'
                            )
                    auto_arg_index = False
                obj, arg_used = self.get_field(field_name, args, kwargs)
                used_args.add(arg_used)
                obj = self.convert_field(obj, conversion)
                format_spec, auto_arg_index = self._vformat(format_spec,
                    args, kwargs, used_args, recursion_depth - 1,
                    auto_arg_index=auto_arg_index)
                result.append(self.format_field(obj, format_spec))
        return ''.join(result), auto_arg_index

    def get_value(self, key, args, kwargs):
        if isinstance(key, int):
            return args[key]
        else:
            return kwargs[key]

    def check_unused_args(self, used_args, args, kwargs):
        pass

    def format_field(self, value, format_spec):
        return format(value, format_spec)

    def convert_field(self, value, conversion):
        if conversion is None:
            return value
        elif conversion == 's':
            return str(value)
        elif conversion == 'r':
            return repr(value)
        elif conversion == 'a':
            return ascii(value)
        raise ValueError('Unknown conversion specifier {0!s}'.format(
            conversion))

    def parse(self, format_string):
        return _string.formatter_parser(format_string)

    def get_field(self, field_name, args, kwargs):
        first, rest = _string.formatter_field_name_split(field_name)
        obj = self.get_value(first, args, kwargs)
        for is_attr, i in rest:
            if is_attr:
                obj = getattr(obj, i)
            else:
                obj = obj[i]
        return obj, first
