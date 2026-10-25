def mask_account_number(account_number: str | None) -> str | None:
    """Mask an account number, keeping only the last 4 digits.

    This is a basic data-privacy practice for logs and reports: raw account
    numbers must never appear in CloudWatch logs or API error responses.

    Examples:
        "123456789012" -> "********9012"
        "1234"         -> "****"
        "" / None      -> same value back (the row is flagged as missing
                           by the validator, not silently invented)
    """
    if not account_number:
        return account_number
    digits = str(account_number)
    if len(digits) <= 4:
        return "*" * len(digits)
    return "*" * (len(digits) - 4) + digits[-4:]
