import os


def database_url() -> str:
    """Return the database URL.

    Defaults to a local SQLite file so the project runs with no setup.
    For PostgreSQL, set e.g.:
        DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/loan_batches
    """
    return os.environ.get("DATABASE_URL", "sqlite:///./loan_batches.db")


def s3_bucket() -> str:
    return os.environ.get("S3_BUCKET", "loan-payment-batches")
