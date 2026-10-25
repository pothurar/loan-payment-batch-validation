from loan_batch.models import Payment
from loan_batch.service import daily_reconciliation, process_csv_text

CSV = """payment_id,account_number,amount,expected_amount,payment_date
P001,123456789012,250.00,250.00,2026-01-15
P002,234567890123,180.50,180.50,2026-01-15
P003,345678901234,320.00,300.00,2026-01-15
P002,234567890123,180.50,180.50,2026-01-15
"""


def test_process_counts_processed_and_flagged(session):
    summary = process_csv_text(session, "batch-1", CSV, "sample.csv")
    assert summary == {
        "batch_id": "batch-1",
        "source_filename": "sample.csv",
        "payment_date": "2026-01-15",
        "total": 4,
        "processed": 2,
        "flagged": 2,
    }


def test_account_numbers_are_stored_masked(session):
    process_csv_text(session, "batch-1", CSV, "sample.csv")
    stored = session.query(Payment).filter_by(payment_id="P001").first()
    assert stored.account_number_masked == "********9012"
    assert "123456789012" not in stored.account_number_masked


def test_reprocessing_same_batch_is_idempotent(session):
    first = process_csv_text(session, "batch-1", CSV, "sample.csv")
    second = process_csv_text(session, "batch-1", CSV, "sample.csv")
    assert first == second
    assert session.query(Payment).count() == 4


def test_daily_reconciliation(session):
    process_csv_text(session, "batch-1", CSV, "sample.csv")
    report = daily_reconciliation(session, "2026-01-15")
    assert report[0]["processed"] == 2
    assert report[0]["flagged"] == 2
    assert daily_reconciliation(session, "2026-01-16") == []
