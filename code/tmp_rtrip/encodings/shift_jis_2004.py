import _codecs_jp, codecs
import _multibytecodec as mbc
codec = _codecs_jp.getcodec('shift_jis_2004')


class Codec(codecs.Codec):
    encode = codec.encode
    decode = codec.decode


class IncrementalEncoder(mbc.MultibyteIncrementalEncoder, codecs.
    IncrementalEncoder):
    codec = codec


class IncrementalDecoder(mbc.MultibyteIncrementalDecoder, codecs.
    IncrementalDecoder):
    codec = codec


class StreamReader(Codec, mbc.MultibyteStreamReader, codecs.StreamReader):
    codec = codec


class StreamWriter(Codec, mbc.MultibyteStreamWriter, codecs.StreamWriter):
    codec = codec


def getregentry():
    return codecs.CodecInfo(name='shift_jis_2004', encode=Codec().encode,
        decode=Codec().decode, incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder, streamreader=StreamReader,
        streamwriter=StreamWriter)
