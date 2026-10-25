import pytest

from loan_batch.db import Base, make_session_factory


@pytest.fixture()
def session():
    """Fresh in-memory SQLite database per test.

    Tests use SQLite so they run anywhere with no Postgres server.
    The app code is database-agnostic (SQLAlchemy); production runs
    use PostgreSQL via DATABASE_URL, and sql/schema.sql is the
    PostgreSQL DDL. That split is stated in the README, not hidden.
    """
    session_factory, engine = make_session_factory("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sess = session_factory()
    yield sess
    sess.close()
