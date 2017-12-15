import datetime
import unittest
import sqlite3 as sqlite


class RegressionTests(unittest.TestCase):

    def setUp(self):
        self.con = sqlite.connect(':memory:')

    def tearDown(self):
        self.con.close()

    def CheckPragmaUserVersion(self):
        cur = self.con.cursor()
        cur.execute('pragma user_version')

    def CheckPragmaSchemaVersion(self):
        con = sqlite.connect(':memory:', detect_types=sqlite.PARSE_COLNAMES)
        try:
            cur = self.con.cursor()
            cur.execute('pragma schema_version')
        finally:
            cur.close()
            con.close()

    def CheckStatementReset(self):
        con = sqlite.connect(':memory:', cached_statements=5)
        cursors = [con.cursor() for x in range(5)]
        cursors[0].execute('create table test(x)')
        for i in range(10):
            cursors[0].executemany('insert into test(x) values (?)', [(x,) for
                x in range(10)])
        for i in range(5):
            cursors[i].execute(' ' * i + 'select x from test')
        con.rollback()

    def CheckColumnNameWithSpaces(self):
        cur = self.con.cursor()
        cur.execute('select 1 as "foo bar [datetime]"')
        self.assertEqual(cur.description[0][0], 'foo bar')
        cur.execute('select 1 as "foo baz"')
        self.assertEqual(cur.description[0][0], 'foo baz')

    def CheckStatementFinalizationOnCloseDb(self):
        con = sqlite.connect(':memory:')
        cursors = []
        for i in range(105):
            cur = con.cursor()
            cursors.append(cur)
            cur.execute('select 1 x union select ' + str(i))
        con.close()

    @unittest.skipIf(sqlite.sqlite_version_info < (3, 2, 2),
        'needs sqlite 3.2.2 or newer')
    def CheckOnConflictRollback(self):
        con = sqlite.connect(':memory:')
        con.execute('create table foo(x, unique(x) on conflict rollback)')
        con.execute('insert into foo(x) values (1)')
        try:
            con.execute('insert into foo(x) values (1)')
        except sqlite.DatabaseError:
            pass
        con.execute('insert into foo(x) values (2)')
        try:
            con.commit()
        except sqlite.OperationalError:
            self.fail('pysqlite knew nothing about the implicit ROLLBACK')

    def CheckWorkaroundForBuggySqliteTransferBindings(self):
        """
        pysqlite would crash with older SQLite versions unless
        a workaround is implemented.
        """
        self.con.execute('create table foo(bar)')
        self.con.execute('drop table foo')
        self.con.execute('create table foo(bar)')

    def CheckEmptyStatement(self):
        """
        pysqlite used to segfault with SQLite versions 3.5.x. These return NULL
        for "no-operation" statements
        """
        self.con.execute('')

    def CheckTypeMapUsage(self):
        """
        pysqlite until 2.4.1 did not rebuild the row_cast_map when recompiling
        a statement. This test exhibits the problem.
        """
        SELECT = 'select * from foo'
        con = sqlite.connect(':memory:', detect_types=sqlite.PARSE_DECLTYPES)
        con.execute('create table foo(bar timestamp)')
        con.execute('insert into foo(bar) values (?)', (datetime.datetime.
            now(),))
        con.execute(SELECT)
        con.execute('drop table foo')
        con.execute('create table foo(bar integer)')
        con.execute('insert into foo(bar) values (5)')
        con.execute(SELECT)

    def CheckErrorMsgDecodeError(self):
        with self.assertRaises(sqlite.OperationalError) as cm:
            self.con.execute("select 'xxx' || ? || 'yyy' colname", (bytes(
                bytearray([250])),)).fetchone()
        msg = "Could not decode to UTF-8 column 'colname' with text 'xxx"
        self.assertIn(msg, str(cm.exception))

    def CheckRegisterAdapter(self):
        """
        See issue 3312.
        """
        self.assertRaises(TypeError, sqlite.register_adapter, {}, None)

    def CheckSetIsolationLevel(self):


        class CustomStr(str):

            def upper(self):
                return None

            def __del__(self):
                con.isolation_level = ''
        con = sqlite.connect(':memory:')
        con.isolation_level = None
        for level in ('', 'DEFERRED', 'IMMEDIATE', 'EXCLUSIVE'):
            with self.subTest(level=level):
                con.isolation_level = level
                con.isolation_level = level.lower()
                con.isolation_level = level.capitalize()
                con.isolation_level = CustomStr(level)
        con.isolation_level = None
        con.isolation_level = 'DEFERRED'
        pairs = [(1, TypeError), (b'', TypeError), ('abc', ValueError), (
            'IMMEDIATE\x00EXCLUSIVE', ValueError), ('é', ValueError)]
        for value, exc in pairs:
            with self.subTest(level=value):
                with self.assertRaises(exc):
                    con.isolation_level = value
                self.assertEqual(con.isolation_level, 'DEFERRED')

    def CheckCursorConstructorCallCheck(self):
        """
        Verifies that cursor methods check whether base class __init__ was
        called.
        """


        class Cursor(sqlite.Cursor):

            def __init__(self, con):
                pass
        con = sqlite.connect(':memory:')
        cur = Cursor(con)
        with self.assertRaises(sqlite.ProgrammingError):
            cur.execute('select 4+5').fetchall()

    def CheckStrSubclass(self):
        """
        The Python 3.0 port of the module didn't cope with values of subclasses of str.
        """


        class MyStr(str):
            pass
        self.con.execute('select ?', (MyStr('abc'),))

    def CheckConnectionConstructorCallCheck(self):
        """
        Verifies that connection methods check whether base class __init__ was
        called.
        """


        class Connection(sqlite.Connection):

            def __init__(self, name):
                pass
        con = Connection(':memory:')
        with self.assertRaises(sqlite.ProgrammingError):
            cur = con.cursor()

    def CheckCursorRegistration(self):
        """
        Verifies that subclassed cursor classes are correctly registered with
        the connection object, too.  (fetch-across-rollback problem)
        """


        class Connection(sqlite.Connection):

            def cursor(self):
                return Cursor(self)


        class Cursor(sqlite.Cursor):

            def __init__(self, con):
                sqlite.Cursor.__init__(self, con)
        con = Connection(':memory:')
        cur = con.cursor()
        cur.execute('create table foo(x)')
        cur.executemany('insert into foo(x) values (?)', [(3,), (4,), (5,)])
        cur.execute('select x from foo')
        con.rollback()
        with self.assertRaises(sqlite.InterfaceError):
            cur.fetchall()

    def CheckAutoCommit(self):
        """
        Verifies that creating a connection in autocommit mode works.
        2.5.3 introduced a regression so that these could no longer
        be created.
        """
        con = sqlite.connect(':memory:', isolation_level=None)

    def CheckPragmaAutocommit(self):
        """
        Verifies that running a PRAGMA statement that does an autocommit does
        work. This did not work in 2.5.3/2.5.4.
        """
        cur = self.con.cursor()
        cur.execute('create table foo(bar)')
        cur.execute('insert into foo(bar) values (5)')
        cur.execute('pragma page_size')
        row = cur.fetchone()

    def CheckSetDict(self):
        """
        See http://bugs.python.org/issue7478

        It was possible to successfully register callbacks that could not be
        hashed. Return codes of PyDict_SetItem were not checked properly.
        """


        class NotHashable:

            def __call__(self, *args, **kw):
                pass

            def __hash__(self):
                raise TypeError()
        var = NotHashable()
        self.assertRaises(TypeError, self.con.create_function, var)
        self.assertRaises(TypeError, self.con.create_aggregate, var)
        self.assertRaises(TypeError, self.con.set_authorizer, var)
        self.assertRaises(TypeError, self.con.set_progress_handler, var)

    def CheckConnectionCall(self):
        """
        Call a connection with a non-string SQL request: check error handling
        of the statement constructor.
        """
        self.assertRaises(sqlite.Warning, self.con, 1)

    def CheckCollation(self):

        def collation_cb(a, b):
            return 1
        self.assertRaises(sqlite.ProgrammingError, self.con.
            create_collation, '\udc80', collation_cb)

    def CheckRecursiveCursorUse(self):
        """
        http://bugs.python.org/issue10811

        Recursively using a cursor, such as when reusing it from a generator led to segfaults.
        Now we catch recursive cursor usage and raise a ProgrammingError.
        """
        con = sqlite.connect(':memory:')
        cur = con.cursor()
        cur.execute('create table a (bar)')
        cur.execute('create table b (baz)')

        def foo():
            cur.execute('insert into a (bar) values (?)', (1,))
            yield 1
        with self.assertRaises(sqlite.ProgrammingError):
            cur.executemany('insert into b (baz) values (?)', ((i,) for i in
                foo()))

    def CheckConvertTimestampMicrosecondPadding(self):
        """
        http://bugs.python.org/issue14720

        The microsecond parsing of convert_timestamp() should pad with zeros,
        since the microsecond string "456" actually represents "456000".
        """
        con = sqlite.connect(':memory:', detect_types=sqlite.PARSE_DECLTYPES)
        cur = con.cursor()
        cur.execute('CREATE TABLE t (x TIMESTAMP)')
        cur.execute("INSERT INTO t (x) VALUES ('2012-04-04 15:06:00.456')")
        cur.execute(
            "INSERT INTO t (x) VALUES ('2012-04-04 15:06:00.123456789')")
        cur.execute('SELECT * FROM t')
        values = [x[0] for x in cur.fetchall()]
        self.assertEqual(values, [datetime.datetime(2012, 4, 4, 15, 6, 0, 
            456000), datetime.datetime(2012, 4, 4, 15, 6, 0, 123456)])

    def CheckInvalidIsolationLevelType(self):
        self.assertRaises(TypeError, sqlite.connect, ':memory:',
            isolation_level=123)

    def CheckNullCharacter(self):
        con = sqlite.connect(':memory:')
        self.assertRaises(ValueError, con, '\x00select 1')
        self.assertRaises(ValueError, con, 'select 1\x00')
        cur = con.cursor()
        self.assertRaises(ValueError, cur.execute, ' \x00select 2')
        self.assertRaises(ValueError, cur.execute, 'select 2\x00')

    def CheckCommitCursorReset(self):
        """
        Connection.commit() did reset cursors, which made sqlite3
        to return rows multiple times when fetched from cursors
        after commit. See issues 10513 and 23129 for details.
        """
        con = sqlite.connect(':memory:')
        con.executescript(
            """
        create table t(c);
        create table t2(c);
        insert into t values(0);
        insert into t values(1);
        insert into t values(2);
        """
            )
        self.assertEqual(con.isolation_level, '')
        counter = 0
        for i, row in enumerate(con.execute('select c from t')):
            with self.subTest(i=i, row=row):
                con.execute('insert into t2(c) values (?)', (i,))
                con.commit()
                if counter == 0:
                    self.assertEqual(row[0], 0)
                elif counter == 1:
                    self.assertEqual(row[0], 1)
                elif counter == 2:
                    self.assertEqual(row[0], 2)
                counter += 1
        self.assertEqual(counter, 3, 'should have returned exactly three rows')


def suite():
    regression_suite = unittest.makeSuite(RegressionTests, 'Check')
    return unittest.TestSuite((regression_suite,))


def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())


if __name__ == '__main__':
    test()
