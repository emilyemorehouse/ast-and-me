"""Fixer for StandardError -> Exception."""
from .. import fixer_base
from ..fixer_util import Name


class FixStandarderror(fixer_base.BaseFix):
    BM_compatible = True
    PATTERN = """
              'StandardError'
              """

    def transform(self, node, results):
        return Name('Exception', prefix=node.prefix)
