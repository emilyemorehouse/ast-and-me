"""Adjust some old Python 2 idioms to their modern counterparts.

* Change some type comparisons to isinstance() calls:
    type(x) == T -> isinstance(x, T)
    type(x) is T -> isinstance(x, T)
    type(x) != T -> not isinstance(x, T)
    type(x) is not T -> not isinstance(x, T)

* Change "while 1:" into "while True:".

* Change both

    v = list(EXPR)
    v.sort()
    foo(v)

and the more general

    v = EXPR
    v.sort()
    foo(v)

into

    v = sorted(EXPR)
    foo(v)
"""
from .. import fixer_base
from ..fixer_util import Call, Comma, Name, Node, BlankLine, syms
CMP = "(n='!=' | '==' | 'is' | n=comp_op< 'is' 'not' >)"
TYPE = "power< 'type' trailer< '(' x=any ')' > >"


class FixIdioms(fixer_base.BaseFix):
    explicit = True
    PATTERN = (
        """
        isinstance=comparison< %s %s T=any >
        |
        isinstance=comparison< T=any %s %s >
        |
        while_stmt< 'while' while='1' ':' any+ >
        |
        sorted=any<
            any*
            simple_stmt<
              expr_stmt< id1=any '='
                         power< list='list' trailer< '(' (not arglist<any+>) any ')' > >
              >
              '\\n'
            >
            sort=
            simple_stmt<
              power< id2=any
                     trailer< '.' 'sort' > trailer< '(' ')' >
              >
              '\\n'
            >
            next=any*
        >
        |
        sorted=any<
            any*
            simple_stmt< expr_stmt< id1=any '=' expr=any > '\\n' >
            sort=
            simple_stmt<
              power< id2=any
                     trailer< '.' 'sort' > trailer< '(' ')' >
              >
              '\\n'
            >
            next=any*
        >
    """
         % (TYPE, CMP, CMP, TYPE))

    def match(self, node):
        r = super(FixIdioms, self).match(node)
        if r and 'sorted' in r:
            if r['id1'] == r['id2']:
                return r
            return None
        return r

    def transform(self, node, results):
        if 'isinstance' in results:
            return self.transform_isinstance(node, results)
        elif 'while' in results:
            return self.transform_while(node, results)
        elif 'sorted' in results:
            return self.transform_sort(node, results)
        else:
            raise RuntimeError('Invalid match')

    def transform_isinstance(self, node, results):
        x = results['x'].clone()
        T = results['T'].clone()
        x.prefix = ''
        T.prefix = ' '
        test = Call(Name('isinstance'), [x, Comma(), T])
        if 'n' in results:
            test.prefix = ' '
            test = Node(syms.not_test, [Name('not'), test])
        test.prefix = node.prefix
        return test

    def transform_while(self, node, results):
        one = results['while']
        one.replace(Name('True', prefix=one.prefix))

    def transform_sort(self, node, results):
        sort_stmt = results['sort']
        next_stmt = results['next']
        list_call = results.get('list')
        simple_expr = results.get('expr')
        if list_call:
            list_call.replace(Name('sorted', prefix=list_call.prefix))
        elif simple_expr:
            new = simple_expr.clone()
            new.prefix = ''
            simple_expr.replace(Call(Name('sorted'), [new], prefix=
                simple_expr.prefix))
        else:
            raise RuntimeError('should not have reached here')
        sort_stmt.remove()
        btwn = sort_stmt.prefix
        if '\n' in btwn:
            if next_stmt:
                prefix_lines = btwn.rpartition('\n')[0], next_stmt[0].prefix
                next_stmt[0].prefix = '\n'.join(prefix_lines)
            else:
                assert list_call.parent
                assert list_call.next_sibling is None
                end_line = BlankLine()
                list_call.parent.append_child(end_line)
                assert list_call.next_sibling is end_line
                end_line.prefix = btwn.rpartition('\n')[0]
