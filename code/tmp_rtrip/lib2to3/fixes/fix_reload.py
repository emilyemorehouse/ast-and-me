"""Fixer for reload().

reload(s) -> imp.reload(s)"""
from .. import fixer_base
from ..fixer_util import ImportAndCall, touch_import


class FixReload(fixer_base.BaseFix):
    BM_compatible = True
    order = 'pre'
    PATTERN = """
    power< 'reload'
           trailer< lpar='('
                    ( not(arglist | argument<any '=' any>) obj=any
                      | obj=arglist<(not argument<any '=' any>) any ','> )
                    rpar=')' >
           after=any*
    >
    """

    def transform(self, node, results):
        if results:
            obj = results['obj']
            if obj:
                if obj.type == self.syms.star_expr:
                    return
                if obj.type == self.syms.argument and obj.children[0
                    ].value == '**':
                    return
        names = 'imp', 'reload'
        new = ImportAndCall(node, results, names)
        touch_import(None, 'imp', node)
        return new
