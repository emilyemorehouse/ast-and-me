"""Fixer for intern().

intern(s) -> sys.intern(s)"""
from .. import fixer_base
from ..fixer_util import ImportAndCall, touch_import


class FixIntern(fixer_base.BaseFix):
    BM_compatible = True
    order = 'pre'
    PATTERN = """
    power< 'intern'
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
        names = 'sys', 'intern'
        new = ImportAndCall(node, results, names)
        touch_import(None, 'sys', node)
        return new
