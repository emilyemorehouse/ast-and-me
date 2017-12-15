import test.support
test.support.import_module('_sqlite3')
import unittest
import sqlite3
from sqlite3.test import dbapi, types, userfunctions, factory, transactions, hooks, regression, dump


def load_tests(*args):
    if test.support.verbose:
        print('test_sqlite: testing with version',
            '{!r}, sqlite_version {!r}'.format(sqlite3.version, sqlite3.
            sqlite_version))
    return unittest.TestSuite([dbapi.suite(), types.suite(), userfunctions.
        suite(), factory.suite(), transactions.suite(), hooks.suite(),
        regression.suite(), dump.suite()])


if __name__ == '__main__':
    unittest.main()
