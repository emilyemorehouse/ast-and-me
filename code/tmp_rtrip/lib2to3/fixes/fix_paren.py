"""Fixer that addes parentheses where they are required

This converts ``[x for x in 1, 2]`` to ``[x for x in (1, 2)]``."""
from .. import fixer_base
from ..fixer_util import LParen, RParen


class FixParen(fixer_base.BaseFix):
    BM_compatible = True
    PATTERN = """
        atom< ('[' | '(')
            (listmaker< any
                comp_for<
                    'for' NAME 'in'
                    target=testlist_safe< any (',' any)+ [',']
                     >
                    [any]
                >
            >
            |
            testlist_gexp< any
                comp_for<
                    'for' NAME 'in'
                    target=testlist_safe< any (',' any)+ [',']
                     >
                    [any]
                >
            >)
        (']' | ')') >
    """

    def transform(self, node, results):
        target = results['target']
        lparen = LParen()
        lparen.prefix = target.prefix
        target.prefix = ''
        target.insert_child(0, lparen)
        target.append_child(RParen())
