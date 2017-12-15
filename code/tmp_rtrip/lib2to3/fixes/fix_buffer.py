"""Fixer that changes buffer(...) into memoryview(...)."""
from .. import fixer_base
from ..fixer_util import Name


class FixBuffer(fixer_base.BaseFix):
    BM_compatible = True
    explicit = True
    PATTERN = """
              power< name='buffer' trailer< '(' [any] ')' > any* >
              """

    def transform(self, node, results):
        name = results['name']
        name.replace(Name('memoryview', prefix=name.prefix))
