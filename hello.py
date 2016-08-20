import unittest
import sys
import sqlalchemy
import sqlalchemy.sql
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import tables


class TestAlchemyBase(unittest.TestCase):
    def setUp(self):
        # lazy connect, connecting doesn't occur until a task against database is necessary
        self.engine = sqlalchemy.create_engine('sqlite:///:memory:', echo = True)

    def tearDown(self):
        pass


class TestAlchemySession(TestAlchemyBase):
    def setUp(self):
        super(TestAlchemySession, self).setUp()
        self.Session = sessionmaker(bind = self.engine)

    def tearDown(self):
        if self.engine: self.engine.dispose()

    @contextmanager
    def getSession(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def test_version(self):
        self.assertEqual(sqlalchemy.__version__, "1.0.14", "SQLAlchemy version is different than 1.0.14")

    # by default, unittest runs the test cases order by alphabetical
    def test_vtables(self):
        tables.CreateAllTables(self.engine)
        self.assertEqual(self.engine.dialect.has_table(self.engine, tables.User.__tablename__), True, "Table User doesn't exist")
        # session doesn't implement __enter__ and __exit__
        with self.getSession() as session:
            session.add(tables.User(name = "foo", password = "bar"))
            self.assertEqual(session.query(tables.User).filter_by(name = 'foo').first().password, 'bar', "User info doesn't match with input")
            self.assertEqual(session.query(tables.User).filter_by(name = 'bar').first(), None, "User bar should not exist")

        with self.getSession() as session:
            session.add(tables.User(name = "bar", password = "bar"))
            session.add(tables.User(name = "foobar", password = "bar"))
            result = session.query(tables.User).filter_by(password = "bar").order_by(tables.User.name)
            self.assertEqual(result.count(), 3, "Not all 3 records returned")
            ulist = [u.name for u in result]
            self.assertEqual(ulist[0] == "bar" and ulist[2] == "foobar", True, "Return is not ordered")
            # Query object doesn't have function 'close'?
            # result.close()


class TestAlchemyConn(TestAlchemyBase):
    def setUp(self):
        super(TestAlchemyConn, self).setUp()
        self.metadata = sqlalchemy.MetaData()
        self.users = sqlalchemy.Table("users", self.metadata,
                                 sqlalchemy.Column('id', sqlalchemy.Integer, primary_key = True),
                                 sqlalchemy.Column('name', sqlalchemy.String),
                                 sqlalchemy.Column('password', sqlalchemy.String)
                                 )
        self.metadata.create_all(self.engine)

    def test_insert(self):
        ins = self.users.insert().values(name = "foo", password = "bar")
        with self.engine.connect() as conn:
            conn.execute(ins)

    def test_select(self):
        with self.engine.connect() as conn:
            sel = sqlalchemy.sql.select([tables.User])
            # Executes a SQL statement construct and returns a :class:`.ResultProxy`.
            # ResultProxy wraps a DB-API cursor object to provide easier access to row columns
            result = conn.execute(sel)
            try:
                # The 'rowcount' reports the number of rows *matched*, by the WHERE criterion of an UPDATE or DELETE statement.
                # https://github.com/zzzeek/sqlalchemy/blob/master/lib/sqlalchemy/engine/result.py#L695
                # rowcount is defined as function, but since util.memoized_property, it's a property now somehow
                self.assertEquals(result.rowcount, - 1, "Row count should be -1 since it's an select statement")
                for row in result:
                    self.assertTrue("foo" == row["name"] and "bar" == row["password"], "There should be only one row...")
            except Exception as e:
                # This is not necessary
                self.assertTrue(False, e.message)
            finally:
                result.close()

# unittest ignores __main__, therefore in order to retrieve the test result, manual override is necessary
#if __name__ == '__main__':
suite1 = unittest.TestLoader().loadTestsFromTestCase(TestAlchemySession)
# wasSuccessful returns 1 if success, otherwise 0
ret1 = unittest.TextTestRunner(verbosity = 2).run(suite1).wasSuccessful()

suite2 = unittest.TestLoader().loadTestsFromTestCase(TestAlchemyConn)
ret2 = unittest.TextTestRunner(verbosity = 2).run(suite2).wasSuccessful()

sys.exit(not(ret1 == 1 and ret2 == 1))
