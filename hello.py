import unittest
import sys
import sqlalchemy
import sqlalchemy.sql
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import tables


class TestAlchemyBase(unittest.TestCase):
    def setUp(self):
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

    def test_select(self):
        with self.engine.connect() as conn:
            sel = sqlalchemy.sql.select([tables.User])
            result = conn.execute(sel)
            result.close()

if __name__ == '__main__':
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestAlchemySession)
    # wasSuccessful returns 1 if success, otherwise 0
    ret1 = unittest.TextTestRunner(verbosity = 2).run(suite1).wasSuccessful()

    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestAlchemyConn)
    ret2 = unittest.TextTestRunner(verbosity = 2).run(suite2).wasSuccessful()

    sys.exit(not(ret1 == 1 and ret2 == 1))
