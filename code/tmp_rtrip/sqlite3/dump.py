def _iterdump(connection):
    """
    Returns an iterator to the dump of the database in an SQL text format.

    Used to produce an SQL dump of the database.  Useful to save an in-memory
    database for later restoration.  This function should not be called
    directly but instead called from the Connection method, iterdump().
    """
    cu = connection.cursor()
    yield 'BEGIN TRANSACTION;'
    q = """
        SELECT "name", "type", "sql"
        FROM "sqlite_master"
            WHERE "sql" NOT NULL AND
            "type" == 'table'
            ORDER BY "name"
        """
    schema_res = cu.execute(q)
    for table_name, type, sql in schema_res.fetchall():
        if table_name == 'sqlite_sequence':
            yield 'DELETE FROM "sqlite_sequence";'
        elif table_name == 'sqlite_stat1':
            yield 'ANALYZE "sqlite_master";'
        elif table_name.startswith('sqlite_'):
            continue
        else:
            yield '{0};'.format(sql)
        table_name_ident = table_name.replace('"', '""')
        res = cu.execute('PRAGMA table_info("{0}")'.format(table_name_ident))
        column_names = [str(table_info[1]) for table_info in res.fetchall()]
        q = 'SELECT \'INSERT INTO "{0}" VALUES({1})\' FROM "{0}";'.format(
            table_name_ident, ','.join('\'||quote("{0}")||\''.format(col.
            replace('"', '""')) for col in column_names))
        query_res = cu.execute(q)
        for row in query_res:
            yield '{0};'.format(row[0])
    q = """
        SELECT "name", "type", "sql"
        FROM "sqlite_master"
            WHERE "sql" NOT NULL AND
            "type" IN ('index', 'trigger', 'view')
        """
    schema_res = cu.execute(q)
    for name, type, sql in schema_res.fetchall():
        yield '{0};'.format(sql)
    yield 'COMMIT;'
