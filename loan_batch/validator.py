"""Row-level validation for a loan payment file.

A row is a dict with these columns (CSV header):
    payment_id, account_number, amount, expected_amount, payment_date

Validation rules, in order:
  1. Missing field   - any of the five columns is blank.
  2. Duplicate       - the same payment_id appears twice in one file/batch.
                       The duplicate key is payment_id alone: a payment
                       must be processed exactly once per batch.
  3. Amount mismatch - amount != expected_amount (to the cent).
                       expected_amount is the amount the loan system
                       scheduled for that payment, so a mismatch means
                       the file and the schedule disagree and the payment
                       needs investigation, not silent acceptance.
  4. Bad amount      - amount / expected_amount is not a number.

A flagged row is stored with its flag reason and is NOT counted as a
successfully processed payment. A clean row is stored as processed.
"""

from dataclasses import dataclass, field

REQUIRED_FIELDS = (
    "payment_id",
    "account_number",
    "amount",
    "expected_amount",
    "payment_date",
)


@dataclass
class ValidatedRow:
    payment_id: str
    account_number: str
    amount: float | None
    expected_amount: float | None
    payment_date: str
    status: str  # "processed" or "flagged"
    flag_reason: str | None = None


def _parse_amount(value: str | None) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def validate_rows(rows: list[dict]) -> list[ValidatedRow]:
    """Validate rows in file order, tracking duplicates within the batch."""
    seen_payment_ids: set[str] = set()
    validated: list[ValidatedRow] = []

    for row in rows:
        payment_id = (row.get("payment_id") or "").strip()
        account_number = (row.get("account_number") or "").strip()
        payment_date = (row.get("payment_date") or "").strip()
        amount = _parse_amount(row.get("amount"))
        expected_amount = _parse_amount(row.get("expected_amount"))

        flag_reason: str | None = None
        if any(not (row.get(f) or "").strip() for f in REQUIRED_FIELDS):
            flag_reason = "missing_field"
        elif payment_id in seen_payment_ids:
            flag_reason = "duplicate_payment_id"
        elif amount is None or expected_amount is None:
            flag_reason = "invalid_amount"
        elif round(amount - expected_amount, 2) != 0:
            flag_reason = "amount_mismatch"

        if payment_id:
            seen_payment_ids.add(payment_id)

        validated.append(
            ValidatedRow(
                payment_id=payment_id,
                account_number=account_number,
                amount=amount,
                expected_amount=expected_amount,
                payment_date=payment_date,
                status="flagged" if flag_reason else "processed",
                flag_reason=flag_reason,
            )
        )
    return validated
