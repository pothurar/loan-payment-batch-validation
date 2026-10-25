from loan_batch.validator import validate_rows


def _row(**overrides):
    row = {
        "payment_id": "P001",
        "account_number": "123456789012",
        "amount": "250.00",
        "expected_amount": "250.00",
        "payment_date": "2026-01-15",
    }
    row.update(overrides)
    return row


def test_clean_row_is_processed():
    result = validate_rows([_row()])
    assert result[0].status == "processed"
    assert result[0].flag_reason is None


def test_missing_field_is_flagged():
    result = validate_rows([_row(account_number="")])
    assert result[0].status == "flagged"
    assert result[0].flag_reason == "missing_field"


def test_duplicate_payment_id_is_flagged():
    result = validate_rows([_row(), _row()])
    assert result[0].status == "processed"
    assert result[1].status == "flagged"
    assert result[1].flag_reason == "duplicate_payment_id"


def test_amount_mismatch_is_flagged():
    result = validate_rows([_row(amount="250.00", expected_amount="240.00")])
    assert result[0].flag_reason == "amount_mismatch"


def test_invalid_amount_is_flagged():
    result = validate_rows([_row(amount="not-a-number")])
    assert result[0].flag_reason == "invalid_amount"


def test_one_cent_difference_is_a_mismatch():
    result = validate_rows([_row(amount="250.01", expected_amount="250.00")])
    assert result[0].flag_reason == "amount_mismatch"
