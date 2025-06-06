from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

URL_DATABASE = 'mysql+pymysql://root:W0daiyar.19@localhost:3306/smart-classroom'

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit= False,autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  