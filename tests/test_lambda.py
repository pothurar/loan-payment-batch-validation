import io

import loan_batch.lambda_handler as lambda_module
from loan_batch.db import Base, make_session_factory

CSV = """payment_id,account_number,amount,expected_amount,payment_date
P001,123456789012,250.00,250.00,2026-01-15
P002,234567890123,180.50,170.50,2026-01-15
"""


class _FakeBody:
    def __init__(self, text):
        self._text = text

    def read(self):
        return self._text.encode("utf-8")


class _FakeS3:
    def get_object(self, Bucket, Key):
        assert Bucket == "loan-payment-batches"
        assert Key == "incoming/payments-2026-01-15.csv"
        return {"Body": _FakeBody(CSV)}


def test_lambda_processes_s3_event(session, monkeypatch):
    # session fixture already created the tables on its in-memory engine.
    # Point the handler at that same engine/session factory.
    engine = session.bind
    session_factory, _ = make_session_factory("sqlite:///:memory:")
    # Reuse the fixture session directly so the handler sees the same DB.
    monkeypatch.setattr(
        lambda_module, "make_session_factory", lambda: (lambda: session, engine)
    )
    monkeypatch.setattr(
        lambda_module.boto3, "client", lambda *args, **kwargs: _FakeS3()
    )

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "loan-payment-batches"},
                    "object": {"key": "incoming/payments-2026-01-15.csv"},
                }
            }
        ]
    }
    result = lambda_module.handler(event, None)
    assert result["processed"][0]["batch_id"] == "payments-2026-01-15"
    assert result["processed"][0]["processed"] == 1
    assert result["processed"][0]["flagged"] == 1
