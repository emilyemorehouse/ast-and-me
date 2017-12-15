""" Python Character Mapping Codec for ROT13.

This codec de/encodes from str to str.

Written by Marc-Andre Lemburg (mal@lemburg.com).
"""
import codecs


class Codec(codecs.Codec):

    def encode(self, input, errors='strict'):
        return input.translate(rot13_map), len(input)

    def decode(self, input, errors='strict'):
        return input.translate(rot13_map), len(input)


class IncrementalEncoder(codecs.IncrementalEncoder):

    def encode(self, input, final=False):
        return input.translate(rot13_map)


class IncrementalDecoder(codecs.IncrementalDecoder):

    def decode(self, input, final=False):
        return input.translate(rot13_map)


class StreamWriter(Codec, codecs.StreamWriter):
    pass


class StreamReader(Codec, codecs.StreamReader):
    pass


def getregentry():
    return codecs.CodecInfo(name='rot-13', encode=Codec().encode, decode=
        Codec().decode, incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder, streamwriter=StreamWriter,
        streamreader=StreamReader, _is_text_encoding=False)


rot13_map = codecs.make_identity_dict(range(256))
rot13_map.update({(65): 78, (66): 79, (67): 80, (68): 81, (69): 82, (70): 
    83, (71): 84, (72): 85, (73): 86, (74): 87, (75): 88, (76): 89, (77): 
    90, (78): 65, (79): 66, (80): 67, (81): 68, (82): 69, (83): 70, (84): 
    71, (85): 72, (86): 73, (87): 74, (88): 75, (89): 76, (90): 77, (97): 
    110, (98): 111, (99): 112, (100): 113, (101): 114, (102): 115, (103): 
    116, (104): 117, (105): 118, (106): 119, (107): 120, (108): 121, (109):
    122, (110): 97, (111): 98, (112): 99, (113): 100, (114): 101, (115): 
    102, (116): 103, (117): 104, (118): 105, (119): 106, (120): 107, (121):
    108, (122): 109})


def rot13(infile, outfile):
    outfile.write(codecs.encode(infile.read(), 'rot-13'))


if __name__ == '__main__':
    import sys
    rot13(sys.stdin, sys.stdout)
