import unittest


def funcattrs(**kwds):

    def decorate(func):
        func.__dict__.update(kwds)
        return func
    return decorate


class MiscDecorators(object):

    @staticmethod
    def author(name):

        def decorate(func):
            func.__dict__['author'] = name
            return func
        return decorate


class DbcheckError(Exception):

    def __init__(self, exprstr, func, args, kwds):
        Exception.__init__(self, 
            'dbcheck %r failed (func=%s args=%s kwds=%s)' % (exprstr, func,
            args, kwds))


def dbcheck(exprstr, globals=None, locals=None):
    """Decorator to implement debugging assertions"""

    def decorate(func):
        expr = compile(exprstr, 'dbcheck-%s' % func.__name__, 'eval')

        def check(*args, **kwds):
            if not eval(expr, globals, locals):
                raise DbcheckError(exprstr, func, args, kwds)
            return func(*args, **kwds)
        return check
    return decorate


def countcalls(counts):
    """Decorator to count calls to a function"""

    def decorate(func):
        func_name = func.__name__
        counts[func_name] = 0

        def call(*args, **kwds):
            counts[func_name] += 1
            return func(*args, **kwds)
        call.__name__ = func_name
        return call
    return decorate


def memoize(func):
    saved = {}

    def call(*args):
        try:
            return saved[args]
        except KeyError:
            res = func(*args)
            saved[args] = res
            return res
        except TypeError:
            return func(*args)
    call.__name__ = func.__name__
    return call


class TestDecorators(unittest.TestCase):

    def test_single(self):


        class C(object):

            @staticmethod
            def foo():
                return 42
        self.assertEqual(C.foo(), 42)
        self.assertEqual(C().foo(), 42)

    def test_staticmethod_function(self):

        @staticmethod
        def notamethod(x):
            return x
        self.assertRaises(TypeError, notamethod, 1)

    def test_dotted(self):
        decorators = MiscDecorators()

        @decorators.author('Cleese')
        def foo():
            return 42
        self.assertEqual(foo(), 42)
        self.assertEqual(foo.author, 'Cleese')

    def test_argforms(self):

        def noteargs(*args, **kwds):

            def decorate(func):
                setattr(func, 'dbval', (args, kwds))
                return func
            return decorate
        args = 'Now', 'is', 'the', 'time'
        kwds = dict(one=1, two=2)

        @noteargs(*args, **kwds)
        def f1():
            return 42
        self.assertEqual(f1(), 42)
        self.assertEqual(f1.dbval, (args, kwds))

        @noteargs('terry', 'gilliam', eric='idle', john='cleese')
        def f2():
            return 84
        self.assertEqual(f2(), 84)
        self.assertEqual(f2.dbval, (('terry', 'gilliam'), dict(eric='idle',
            john='cleese')))

        @noteargs(1, 2)
        def f3():
            pass
        self.assertEqual(f3.dbval, ((1, 2), {}))

    def test_dbcheck(self):

        @dbcheck('args[1] is not None')
        def f(a, b):
            return a + b
        self.assertEqual(f(1, 2), 3)
        self.assertRaises(DbcheckError, f, 1, None)

    def test_memoize(self):
        counts = {}

        @memoize
        @countcalls(counts)
        def double(x):
            return x * 2
        self.assertEqual(double.__name__, 'double')
        self.assertEqual(counts, dict(double=0))
        self.assertEqual(double(2), 4)
        self.assertEqual(counts['double'], 1)
        self.assertEqual(double(2), 4)
        self.assertEqual(counts['double'], 1)
        self.assertEqual(double(3), 6)
        self.assertEqual(counts['double'], 2)
        self.assertEqual(double([10]), [10, 10])
        self.assertEqual(counts['double'], 3)
        self.assertEqual(double([10]), [10, 10])
        self.assertEqual(counts['double'], 4)

    def test_errors(self):
        for expr in ['1+2', 'x[3]', '(1, 2)']:
            compile(expr, 'testexpr', 'exec')
            codestr = '@%s\ndef f(): pass' % expr
            self.assertRaises(SyntaxError, compile, codestr, 'test', 'exec')
        self.assertRaises(SyntaxError, compile, '@f1 @f2\ndef f(): pass',
            'test', 'exec')

        def unimp(func):
            raise NotImplementedError
        context = dict(nullval=None, unimp=unimp)
        for expr, exc in [('undef', NameError), ('nullval', TypeError), (
            'nullval.attr', AttributeError), ('unimp', NotImplementedError)]:
            codestr = '@%s\ndef f(): pass\nassert f() is None' % expr
            code = compile(codestr, 'test', 'exec')
            self.assertRaises(exc, eval, code, context)

    def test_double(self):


        class C(object):

            @funcattrs(abc=1, xyz='haha')
            @funcattrs(booh=42)
            def foo(self):
                return 42
        self.assertEqual(C().foo(), 42)
        self.assertEqual(C.foo.abc, 1)
        self.assertEqual(C.foo.xyz, 'haha')
        self.assertEqual(C.foo.booh, 42)

    def test_order(self):

        def callnum(num):
            """Decorator factory that returns a decorator that replaces the
            passed-in function with one that returns the value of 'num'"""

            def deco(func):
                return lambda : num
            return deco

        @callnum(2)
        @callnum(1)
        def foo():
            return 42
        self.assertEqual(foo(), 2,
            'Application order of decorators is incorrect')

    def test_eval_order(self):
        actions = []

        def make_decorator(tag):
            actions.append('makedec' + tag)

            def decorate(func):
                actions.append('calldec' + tag)
                return func
            return decorate


        class NameLookupTracer(object):

            def __init__(self, index):
                self.index = index

            def __getattr__(self, fname):
                if fname == 'make_decorator':
                    opname, res = 'evalname', make_decorator
                elif fname == 'arg':
                    opname, res = 'evalargs', str(self.index)
                else:
                    assert False, 'Unknown attrname %s' % fname
                actions.append('%s%d' % (opname, self.index))
                return res
        c1, c2, c3 = map(NameLookupTracer, [1, 2, 3])
        expected_actions = ['evalname1', 'evalargs1', 'makedec1',
            'evalname2', 'evalargs2', 'makedec2', 'evalname3', 'evalargs3',
            'makedec3', 'calldec3', 'calldec2', 'calldec1']
        actions = []

        @c1.make_decorator(c1.arg)
        @c2.make_decorator(c2.arg)
        @c3.make_decorator(c3.arg)
        def foo():
            return 42
        self.assertEqual(foo(), 42)
        self.assertEqual(actions, expected_actions)
        actions = []

        def bar():
            return 42
        bar = c1.make_decorator(c1.arg)(c2.make_decorator(c2.arg)(c3.
            make_decorator(c3.arg)(bar)))
        self.assertEqual(bar(), 42)
        self.assertEqual(actions, expected_actions)


class TestClassDecorators(unittest.TestCase):

    def test_simple(self):

        def plain(x):
            x.extra = 'Hello'
            return x


        @plain
        class C(object):
            pass
        self.assertEqual(C.extra, 'Hello')

    def test_double(self):

        def ten(x):
            x.extra = 10
            return x

        def add_five(x):
            x.extra += 5
            return x


        @add_five
        @ten
        class C(object):
            pass
        self.assertEqual(C.extra, 15)

    def test_order(self):

        def applied_first(x):
            x.extra = 'first'
            return x

        def applied_second(x):
            x.extra = 'second'
            return x


        @applied_second
        @applied_first
        class C(object):
            pass
        self.assertEqual(C.extra, 'second')


if __name__ == '__main__':
    unittest.main()
