import sqlite3
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Boolean, Column, Integer, String, create_engine, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

db_url = Path("runtime/todo.db")
db_url.parent.mkdir(exist_ok=True)
sqlite3.connect(db_url)
engine = create_engine(f"sqlite:///{db_url}")
Base = declarative_base()

Session = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    """This function allows for a 'session' to be contained within a 'with' statement, to remove the need for repetition
    of code and ensure any sessions are commited/rolledback/closed appropriately.
    An example would be:
        with session_scope() as s:
            # do something here.

    Yields:
        session: Instance of Session() for performing database task within 'with' statements

    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class Task(Base):
    """Main table to store tasks."""

    __tablename__ = "task"

    # Columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    details = Column(String)
    category = Column(String)
    priority = Column(Integer)
    is_complete = Column(Boolean)
    archived = Column(Boolean)
    complete_by = Column(Date)
    effort = Column(Integer)




Base.metadata.create_all(engine)
