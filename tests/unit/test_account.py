import pytest
from pprint import pprint

## Model tests (test the __init__ method)
def test_valid_account_creation(account_initialiser):
    Account = account_initialiser

    account = Account("ValidTitle", "DE89370400440532013000")
    assert account.title == "ValidTitle"
    assert account.iban == "DE89370400440532013000"

def test_invalid_title_type(account_initialiser):
    Account = account_initialiser

    with pytest.raises(ValueError, match="title should be of type str."):
        Account(12345, "DE89370400440532013000")

def test_short_title_length(account_initialiser):
    Account = account_initialiser

    with pytest.raises(ValueError, match="title must be between 3 to 15 characters long."):
        Account("ab", "DE89370400440532013000")

def test_long_title_length(account_initialiser):
    Account = account_initialiser

    with pytest.raises(ValueError, match="title must be between 3 to 15 characters long."):
        Account("a"*16, "DE89370400440532013000")

def test_invalid_iban_type(account_initialiser):
    Account = account_initialiser

    with pytest.raises(ValueError, match="iban should be of type str."):
        Account("ValidTitle", 12345678901234567890)

def test_short_iban_length(account_initialiser):
    Account = account_initialiser

    with pytest.raises(ValueError, match="iban must be exactly 22 characters long."):
        Account("ValidTitle", "DE89370400440532")

def test_long_iban_length(account_initialiser):
    Account = account_initialiser

    with pytest.raises(ValueError, match="iban must be exactly 22 characters long."):
        Account("ValidTitle", "DE893704004405320130001234")

# -> No test for dupicate iban, because that requires db connection and thus no model test

def test_repr_method(account_initialiser):
    Account = account_initialiser

    account = Account(title="John's Savings", iban="GB29000060161331920000")
    assert str(account) == "[Account] iban: GB29000060161331920000, title: John's Savings"

## Account sub-function tests (create_account, generate_unique_iban ...)

def test_create_account_valid_account_creation(account_initialiser): # -> Sub function of create() route
    from project.accounts.accounts import create_account

    status, message = create_account("GB29000060161331920001", "TestTitle")
    assert status == "success"
    assert message == 'Successfully created new account.'

def test_create_account_invalid_iban_type(account_initialiser):
    from project.accounts.accounts import create_account

    status, message = create_account(1234567890123456789012, "TestTitle")
    assert status == "error"
    assert "iban should be of type str" in message

def test_create_account_invalid_title_type(account_initialiser):
    from project.accounts.accounts import create_account

    status, message = create_account("GB29000060161331920001", 123)
    assert status == "error"
    assert "title should be of type str" in message

def test_create_account_short_iban(account_initialiser):
    from project.accounts.accounts import create_account

    status, message = create_account("GB29000060161331", "TestTitle")
    assert status == "error"
    assert "iban must be exactly 22 characters long" in message

def test_create_account_long_iban(account_initialiser):
    from project.accounts.accounts import create_account

    status, message = create_account("GB290000601613319200012345", "TestTitle")
    assert status == "error"
    assert "iban must be exactly 22 characters long" in message

def test_create_account_short_title(account_initialiser):
    from project.accounts.accounts import create_account

    status, message = create_account("GB29000060161331920001", "TT")
    assert status == "error"
    assert "title must be between 3 to 15 characters long" in message

def test_create_account_long_title(account_initialiser):
    from project.accounts.accounts import create_account

    status, message = create_account("GB29000060161331920001", "ThisTitleIsTooLong")
    assert status == "error"
    assert "title must be between 3 to 15 characters long" in message

def test_create_account_iban_duplicate(account_initialiser):
    from project.accounts.accounts import create_account

    status1, message1 = create_account("GB29000060161331920001", "Title1")
    assert status1 != "error"

    status2, message2 = create_account("GB29000060161331920001", "Title2")
    assert status2 == "error"
    assert "The IBAN is already taken by another account." in message2

def test_create_account_iban_increases_and_duplicate_title(account_initialiser):
    from project.accounts.accounts import create_account, generate_unique_iban

    for i in range(5):
        new_iban = generate_unique_iban()
        assert new_iban.endswith(f"0{i}")
        status, message = create_account(new_iban, "Title")
        assert status == "success"

def test_create_account_accounts_within_limit(account_initialiser):
    from project.accounts.accounts import create_account, generate_unique_iban
    Account = account_initialiser

    for _ in range(4):
        iban = generate_unique_iban()
        status, message = create_account(iban, "Title")
        assert status == "success"

    assert Account.query.count() == 4

def test_create_account_accounts_at_limit(account_initialiser):
    from project.accounts.accounts import create_account, generate_unique_iban
    Account = account_initialiser

    for _ in range(5):
        iban = generate_unique_iban()
        status, message = create_account(iban, "Title")
        assert status == "success"

    assert Account.query.count() == 5

def test_create_account_accounts_exceed_limit(account_initialiser):
    from project.accounts.accounts import create_account, generate_unique_iban
    Account = account_initialiser

    for _ in range(5):
        iban = generate_unique_iban()
        status, message = create_account(iban, "Title")
        assert status == "success"

    iban = generate_unique_iban()
    status, message = create_account(iban, "Title")
    assert status == "error"
    assert message == "Cannot add more than 5 accounts."
