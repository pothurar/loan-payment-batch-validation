"""Batch processing: CSV -> validation -> database -> summary."""

import csv
import io
import logging

from .masking import mask_account_number
from .models import Payment, PaymentBatch
from .validator import validate_rows

logger = logging.getLogger(__name__)


def process_csv_text(session, batch_id: str, csv_text: str, source_filename: str | None = None) -> dict:
    """Process one CSV file for a batch_id and return its summary.

    Idempotent: if batch_id already exists, the existing summary is
    returned and nothing is inserted again.
    """
    existing = session.query(PaymentBatch).filter_by(batch_id=batch_id).first()
    if existing is not None:
        logger.info("batch %s already processed; returning existing summary", batch_id)
        return existing.summary

    rows = list(csv.DictReader(io.StringIO(csv_text)))
    validated = validate_rows(rows)

    payment_date = validated[0].payment_date if validated else None
    batch = PaymentBatch(
        batch_id=batch_id,
        source_filename=source_filename,
        payment_date=payment_date,
    )
    session.add(batch)

    for row in validated:
        session.add(
            Payment(
                batch_id=batch_id,
                payment_id=row.payment_id,
                account_number_masked=mask_account_number(row.account_number),
                amount=row.amount,
                expected_amount=row.expected_amount,
                payment_date=row.payment_date,
                status=row.status,
                flag_reason=row.flag_reason,
            )
        )
    session.commit()
    logger.info(
        "batch %s processed: %s", batch_id, batch.summary
    )  # CloudWatch picks up stdout/stderr logging in Lambda
    return batch.summary


def process_s3_object(session, s3_client, bucket: str, key: str) -> dict:
    """Download a CSV from S3 and process it. Used by the Lambda handler.

    batch_id is the S3 key without directories/extension, e.g.
    "incoming/payments-2026-01-15.csv" -> "payments-2026-01-15".
    """
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    csv_text = obj["Body"].read().decode("utf-8")
    batch_id = key.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return process_csv_text(session, batch_id, csv_text, source_filename=key)


def daily_reconciliation(session, payment_date: str) -> list[dict]:
    """Daily reconciliation report, by batch, for one payment_date.

    This is the SQL the report endpoint runs (see sql/reconciliation.sql
    for the raw PostgreSQL version): processed / failed(flagged) /
    flagged counts per batch.
    """
    batches = (
        session.query(PaymentBatch)
        .filter(PaymentBatch.payment_date == payment_date)
        .order_by(PaymentBatch.batch_id)
        .all()
    )
    return [b.summary for b in batches]
