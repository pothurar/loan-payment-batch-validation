import os

from loan_batch.cli import main
from loan_batch.db import Base, make_session_factory
from loan_batch.models import PaymentBatch

CSV = """payment_id,account_number,amount,expected_amount,payment_date
P001,123456789012,250.00,250.00,2026-01-15
P002,234567890123,180.50,170.50,2026-01-15
"""


def test_cli_processes_file(tmp_path, monkeypatch):
    csv_file = tmp_path / "payments.csv"
    csv_file.write_text(CSV, encoding="utf-8")
    db_file = tmp_path / "cli.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    assert main([str(csv_file), "--batch-id", "cli-batch"]) == 0

    session_factory, engine = make_session_factory(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)
    session = session_factory()
    try:
        batch = session.query(PaymentBatch).filter_by(batch_id="cli-batch").first()
        assert batch is not None
        assert batch.summary["processed"] == 1
        assert batch.summary["flagged"] == 1
    finally:
        session.close()


def test_cli_defaults_batch_id_from_filename(tmp_path, monkeypatch):
    csv_file = tmp_path / "mybatch.csv"
    csv_file.write_text(CSV, encoding="utf-8")
    db_file = tmp_path / "cli2.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    assert main([str(csv_file)]) == 0
    session_factory, _ = make_session_factory(f"sqlite:///{db_file}")
    session = session_factory()
    try:
        assert session.query(PaymentBatch).filter_by(batch_id="mybatch").first() is not None
    finally:
        session.close()
