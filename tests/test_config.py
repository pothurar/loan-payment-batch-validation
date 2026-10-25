from loan_batch.config import database_url, s3_bucket


def test_defaults(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("S3_BUCKET", raising=False)
    assert database_url() == "sqlite:///./loan_batches.db"
    assert s3_bucket() == "loan-payment-batches"


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@localhost/db")
    monkeypatch.setenv("S3_BUCKET", "my-bucket")
    assert database_url() == "postgresql+psycopg2://u:p@localhost/db"
    assert s3_bucket() == "my-bucket"
