from loan_batch.masking import mask_account_number


def test_masks_all_but_last_four():
    assert mask_account_number("123456789012") == "********9012"


def test_short_number_is_fully_masked():
    assert mask_account_number("1234") == "****"


def test_empty_and_none_pass_through():
    assert mask_account_number("") == ""
    assert mask_account_number(None) is None
