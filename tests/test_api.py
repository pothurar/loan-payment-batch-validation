import pytest

from loan_batch.api import create_app
from loan_batch.db import Base, make_session_factory
from loan_batch.service import process_csv_text

CSV = """payment_id,account_number,amount,expected_amount,payment_date
P001,123456789012,250.00,250.00,2026-01-15
P002,234567890123,180.50,170.50,2026-01-15
"""


@pytest.fixture()
def client(session):
    # Seed the same in-memory database the app will use.
    process_csv_text(session, "batch-1", CSV, "sample.csv")

    def session_factory():
        return session

    app = create_app(session_factory=session_factory, engine=None)
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_list_and_get_batch(client):
    assert client.get("/batches").get_json()[0]["batch_id"] == "batch-1"
    assert client.get("/batches/batch-1").get_json()["flagged"] == 1
    assert client.get("/batches/nope").status_code == 404


def test_errors_endpoint_shows_only_flagged_and_masked(client):
    errors = client.get("/batches/batch-1/errors").get_json()
    assert len(errors) == 1
    assert errors[0]["payment_id"] == "P002"
    assert errors[0]["flag_reason"] == "amount_mismatch"
    assert errors[0]["account_number_masked"] == "********0123"
    assert client.get("/batches/nope/errors").status_code == 404


def test_daily_report_requires_date(client):
    assert client.get("/reports/daily").status_code == 400
    report = client.get("/reports/daily?date=2026-01-15").get_json()
    assert report[0]["processed"] == 1
