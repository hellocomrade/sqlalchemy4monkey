import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    name = sqlalchemy.Column(sqlalchemy.String)
    password = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return "<User(name = {0}, password = {1}".format(self.name, self.password)

def CreateAllTables(engine):
    #create_all returns nothing
    Base.metadata.create_all(engine)
