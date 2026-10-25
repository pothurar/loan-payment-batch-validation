from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import database_url

Base = declarative_base()


def make_engine(url: str | None = None):
    """Create a SQLAlchemy engine.

    SQLite (the default for local runs) needs check_same_thread=False
    because the Flask test client / app may use the engine from more
    than one thread. PostgreSQL does not need that argument.
    """
    url = url or database_url()
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url)


def make_session_factory(url: str | None = None):
    engine = make_engine(url)
    return sessionmaker(bind=engine), engine
