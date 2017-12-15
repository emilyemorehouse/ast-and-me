import stringprep, re, codecs
from unicodedata import ucd_3_2_0 as unicodedata
dots = re.compile('[.。．｡]')
ace_prefix = b'xn--'
sace_prefix = 'xn--'


def nameprep(label):
    newlabel = []
    for c in label:
        if stringprep.in_table_b1(c):
            continue
        newlabel.append(stringprep.map_table_b2(c))
    label = ''.join(newlabel)
    label = unicodedata.normalize('NFKC', label)
    for c in label:
        if stringprep.in_table_c12(c) or stringprep.in_table_c22(c
            ) or stringprep.in_table_c3(c) or stringprep.in_table_c4(c
            ) or stringprep.in_table_c5(c) or stringprep.in_table_c6(c
            ) or stringprep.in_table_c7(c) or stringprep.in_table_c8(c
            ) or stringprep.in_table_c9(c):
            raise UnicodeError('Invalid character %r' % c)
    RandAL = [stringprep.in_table_d1(x) for x in label]
    for c in RandAL:
        if c:
            if any(stringprep.in_table_d2(x) for x in label):
                raise UnicodeError('Violation of BIDI requirement 2')
            if not RandAL[0] or not RandAL[-1]:
                raise UnicodeError('Violation of BIDI requirement 3')
    return label


def ToASCII(label):
    try:
        label = label.encode('ascii')
    except UnicodeError:
        pass
    else:
        if 0 < len(label) < 64:
            return label
        raise UnicodeError('label empty or too long')
    label = nameprep(label)
    try:
        label = label.encode('ascii')
    except UnicodeError:
        pass
    else:
        if 0 < len(label) < 64:
            return label
        raise UnicodeError('label empty or too long')
    if label.startswith(sace_prefix):
        raise UnicodeError('Label starts with ACE prefix')
    label = label.encode('punycode')
    label = ace_prefix + label
    if 0 < len(label) < 64:
        return label
    raise UnicodeError('label empty or too long')


def ToUnicode(label):
    if isinstance(label, bytes):
        pure_ascii = True
    else:
        try:
            label = label.encode('ascii')
            pure_ascii = True
        except UnicodeError:
            pure_ascii = False
    if not pure_ascii:
        label = nameprep(label)
        try:
            label = label.encode('ascii')
        except UnicodeError:
            raise UnicodeError('Invalid character in IDN label')
    if not label.startswith(ace_prefix):
        return str(label, 'ascii')
    label1 = label[len(ace_prefix):]
    result = label1.decode('punycode')
    label2 = ToASCII(result)
    if str(label, 'ascii').lower() != str(label2, 'ascii'):
        raise UnicodeError('IDNA does not round-trip', label, label2)
    return result


class Codec(codecs.Codec):

    def encode(self, input, errors='strict'):
        if errors != 'strict':
            raise UnicodeError('unsupported error handling ' + errors)
        if not input:
            return b'', 0
        try:
            result = input.encode('ascii')
        except UnicodeEncodeError:
            pass
        else:
            labels = result.split(b'.')
            for label in labels[:-1]:
                if not 0 < len(label) < 64:
                    raise UnicodeError('label empty or too long')
            if len(labels[-1]) >= 64:
                raise UnicodeError('label too long')
            return result, len(input)
        result = bytearray()
        labels = dots.split(input)
        if labels and not labels[-1]:
            trailing_dot = b'.'
            del labels[-1]
        else:
            trailing_dot = b''
        for label in labels:
            if result:
                result.extend(b'.')
            result.extend(ToASCII(label))
        return bytes(result + trailing_dot), len(input)

    def decode(self, input, errors='strict'):
        if errors != 'strict':
            raise UnicodeError('Unsupported error handling ' + errors)
        if not input:
            return '', 0
        if not isinstance(input, bytes):
            input = bytes(input)
        if ace_prefix not in input:
            try:
                return input.decode('ascii'), len(input)
            except UnicodeDecodeError:
                pass
        labels = input.split(b'.')
        if labels and len(labels[-1]) == 0:
            trailing_dot = '.'
            del labels[-1]
        else:
            trailing_dot = ''
        result = []
        for label in labels:
            result.append(ToUnicode(label))
        return '.'.join(result) + trailing_dot, len(input)


class IncrementalEncoder(codecs.BufferedIncrementalEncoder):

    def _buffer_encode(self, input, errors, final):
        if errors != 'strict':
            raise UnicodeError('unsupported error handling ' + errors)
        if not input:
            return b'', 0
        labels = dots.split(input)
        trailing_dot = b''
        if labels:
            if not labels[-1]:
                trailing_dot = b'.'
                del labels[-1]
            elif not final:
                del labels[-1]
                if labels:
                    trailing_dot = b'.'
        result = bytearray()
        size = 0
        for label in labels:
            if size:
                result.extend(b'.')
                size += 1
            result.extend(ToASCII(label))
            size += len(label)
        result += trailing_dot
        size += len(trailing_dot)
        return bytes(result), size


class IncrementalDecoder(codecs.BufferedIncrementalDecoder):

    def _buffer_decode(self, input, errors, final):
        if errors != 'strict':
            raise UnicodeError('Unsupported error handling ' + errors)
        if not input:
            return '', 0
        if isinstance(input, str):
            labels = dots.split(input)
        else:
            input = str(input, 'ascii')
            labels = input.split('.')
        trailing_dot = ''
        if labels:
            if not labels[-1]:
                trailing_dot = '.'
                del labels[-1]
            elif not final:
                del labels[-1]
                if labels:
                    trailing_dot = '.'
        result = []
        size = 0
        for label in labels:
            result.append(ToUnicode(label))
            if size:
                size += 1
            size += len(label)
        result = '.'.join(result) + trailing_dot
        size += len(trailing_dot)
        return result, size


class StreamWriter(Codec, codecs.StreamWriter):
    pass


class StreamReader(Codec, codecs.StreamReader):
    pass


def getregentry():
    return codecs.CodecInfo(name='idna', encode=Codec().encode, decode=
        Codec().decode, incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder, streamwriter=StreamWriter,
        streamreader=StreamReader)
