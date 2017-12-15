import os, unittest
import sqlite3 as sqlite


def get_db_path():
    return 'sqlite_testdb'


class TransactionTests(unittest.TestCase):

    def setUp(self):
        try:
            os.remove(get_db_path())
        except OSError:
            pass
        self.con1 = sqlite.connect(get_db_path(), timeout=0.1)
        self.cur1 = self.con1.cursor()
        self.con2 = sqlite.connect(get_db_path(), timeout=0.1)
        self.cur2 = self.con2.cursor()

    def tearDown(self):
        self.cur1.close()
        self.con1.close()
        self.cur2.close()
        self.con2.close()
        try:
            os.unlink(get_db_path())
        except OSError:
            pass

    def CheckDMLDoesNotAutoCommitBefore(self):
        self.cur1.execute('create table test(i)')
        self.cur1.execute('insert into test(i) values (5)')
        self.cur1.execute('create table test2(j)')
        self.cur2.execute('select i from test')
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 0)

    def CheckInsertStartsTransaction(self):
        self.cur1.execute('create table test(i)')
        self.cur1.execute('insert into test(i) values (5)')
        self.cur2.execute('select i from test')
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 0)

    def CheckUpdateStartsTransaction(self):
        self.cur1.execute('create table test(i)')
        self.cur1.execute('insert into test(i) values (5)')
        self.con1.commit()
        self.cur1.execute('update test set i=6')
        self.cur2.execute('select i from test')
        res = self.cur2.fetchone()[0]
        self.assertEqual(res, 5)

    def CheckDeleteStartsTransaction(self):
        self.cur1.execute('create table test(i)')
        self.cur1.execute('insert into test(i) values (5)')
        self.con1.commit()
        self.cur1.execute('delete from test')
        self.cur2.execute('select i from test')
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 1)

    def CheckReplaceStartsTransaction(self):
        self.cur1.execute('create table test(i)')
        self.cur1.execute('insert into test(i) values (5)')
        self.con1.commit()
        self.cur1.execute('replace into test(i) values (6)')
        self.cur2.execute('select i from test')
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][0], 5)

    def CheckToggleAutoCommit(self):
        self.cur1.execute('create table test(i)')
        self.cur1.execute('insert into test(i) values (5)')
        self.con1.isolation_level = None
        self.assertEqual(self.con1.isolation_level, None)
        self.cur2.execute('select i from test')
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 1)
        self.con1.isolation_level = 'DEFERRED'
        self.assertEqual(self.con1.isolation_level, 'DEFERRED')
        self.cur1.execute('insert into test(i) values (5)')
        self.cur2.execute('select i from test')
        res = self.cur2.fetchall()
        self.assertEqual(len(res), 1)

    @unittest.skipIf(sqlite.sqlite_version_info < (3, 2, 2),
        'test hangs on sqlite versions older than 3.2.2')
    def CheckRaiseTimeout(self):
        self.cur1.execute('create table test(i)')
        self.cur1.execute('insert into test(i) values (5)')
        with self.assertRaises(sqlite.OperationalError):
            self.cur2.execute('insert into test(i) values (5)')

    @unittest.skipIf(sqlite.sqlite_version_info < (3, 2, 2),
        'test hangs on sqlite versions older than 3.2.2')
    def CheckLocking(self):
        """
        This tests the improved concurrency with pysqlite 2.3.4. You needed
        to roll back con2 before you could commit con1.
        """
        self.cur1.execute('create table test(i)')
        self.cur1.execute('insert into test(i) values (5)')
        with self.assertRaises(sqlite.OperationalError):
            self.cur2.execute('insert into test(i) values (5)')
        self.con1.commit()

    def CheckRollbackCursorConsistency(self):
        """
        Checks if cursors on the connection are set into a "reset" state
        when a rollback is done on the connection.
        """
        con = sqlite.connect(':memory:')
        cur = con.cursor()
        cur.execute('create table test(x)')
        cur.execute('insert into test(x) values (5)')
        cur.execute('select 1 union select 2 union select 3')
        con.rollback()
        with self.assertRaises(sqlite.InterfaceError):
            cur.fetchall()


class SpecialCommandTests(unittest.TestCase):

    def setUp(self):
        self.con = sqlite.connect(':memory:')
        self.cur = self.con.cursor()

    def CheckDropTable(self):
        self.cur.execute('create table test(i)')
        self.cur.execute('insert into test(i) values (5)')
        self.cur.execute('drop table test')

    def CheckPragma(self):
        self.cur.execute('create table test(i)')
        self.cur.execute('insert into test(i) values (5)')
        self.cur.execute('pragma count_changes=1')

    def tearDown(self):
        self.cur.close()
        self.con.close()


class TransactionalDDL(unittest.TestCase):

    def setUp(self):
        self.con = sqlite.connect(':memory:')

    def CheckDdlDoesNotAutostartTransaction(self):
        self.con.execute('create table test(i)')
        self.con.rollback()
        result = self.con.execute('select * from test').fetchall()
        self.assertEqual(result, [])

    def CheckImmediateTransactionalDDL(self):
        self.con.execute('begin immediate')
        self.con.execute('create table test(i)')
        self.con.rollback()
        with self.assertRaises(sqlite.OperationalError):
            self.con.execute('select * from test')

    def CheckTransactionalDDL(self):
        self.con.execute('begin')
        self.con.execute('create table test(i)')
        self.con.rollback()
        with self.assertRaises(sqlite.OperationalError):
            self.con.execute('select * from test')

    def tearDown(self):
        self.con.close()


def suite():
    default_suite = unittest.makeSuite(TransactionTests, 'Check')
    special_command_suite = unittest.makeSuite(SpecialCommandTests, 'Check')
    ddl_suite = unittest.makeSuite(TransactionalDDL, 'Check')
    return unittest.TestSuite((default_suite, special_command_suite, ddl_suite)
        )


def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())


if __name__ == '__main__':
    test()
