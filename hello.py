import unittest
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import tables

class TestAlchemy(unittest.TestCase):
    def setUp(self):
        self.engine = sqlalchemy.create_engine('sqlite:///:memory:', echo = True)
	self.Session = sessionmaker(bind = self.engine)
    
    @contextmanager
    def getSession(self):
	try:
	    session = self.Session()
            yield session
	    session.commit()
	except:
	    session.rollback()
	    raise
        finally:
            session.close()
    
    def tearDown(self):
        if self.engine: self.engine.dispose()

    def test_version(self):
        self.assertEqual(sqlalchemy.__version__, "1.0.14", "SQLAlchemy version is different than 1.0.14")
    
    def test_tables(self):
	tables.CreateAllTables(self.engine)
        self.assertEqual(self.engine.dialect.has_table(self.engine, tables.User.__tablename__), True, "Table User doesn't exist")
	#session doesn't implement __enter__ and __exit__
	with self.getSession() as session:
	    session.add(tables.User(name = "foo", password = "bar"))
	    self.assertEqual(session.query(tables.User).filter_by(name = 'foo').first().password, 'bar', "User info doesn't match with input")

suite = unittest.TestLoader().loadTestsFromTestCase(TestAlchemy)
unittest.TextTestRunner(verbosity = 2).run(suite)
#if __name__ == '__main__':
#    unittest.main()
