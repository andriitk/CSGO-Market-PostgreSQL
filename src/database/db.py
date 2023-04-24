from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()

engine = create_engine(DATABASE_URL)
session_maker = sessionmaker(bind=engine, autoflush=True, autocommit=False)


@contextmanager
def get_session():
    session = session_maker()
    try:
        yield session
    except Exception as ex:
        print(ex)
        session.rollback()
    finally:
        session.commit()
        session.close()
