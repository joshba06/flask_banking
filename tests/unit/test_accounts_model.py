import pytest
from pprint import pprint
from sqlalchemy.exc import IntegrityError

## Model / db tests
def test_create_account(db_initialiser):
    Account, _, db_session = db_initialiser

    account = Account(title="John's Savings", iban="DE1234567890123456")
    db_session.add(account)
    db_session.commit()

    retrieved_account = db_session.query(Account).first()
    assert retrieved_account.title == "John's Savings"
    assert retrieved_account.iban == "DE1234567890123456"

def test_invalid_title_type(db_initialiser):
    Account, _, db_session = db_initialiser

    with pytest.raises(ValueError, match="'title' should be of type 'str'."):
        Account(title=12345, iban="DE1234567890123456")

def test_invalid_iban_type(db_initialiser):
    Account, _, db_session = db_initialiser

    with pytest.raises(ValueError, match="'iban' should be of type 'str'."):
        Account(title="John's Savings", iban=1234567890123456)

def test_repr_method(db_initialiser):
    Account, _, db_session = db_initialiser

    account = Account(title="John's Savings", iban="DE1234567890123456")
    assert str(account) == "Account with iban: DE1234567890123456"

def test_duplicate_iban(db_initialiser):
    # Create the first account with a specific IBAN
    Account, _, db_session = db_initialiser

    account1 = Account(title="John's Savings", iban="DE1234567890123456")
    db_session.add(account1)
    db_session.commit()

    # Attempt to create a second account with the same IBAN
    account2 = Account(title="Jane's Savings", iban="DE1234567890123456")
    db_session.add(account2)
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()

def test_duplicate_title(db_initialiser):
    # Create the first account with a specific title
    Account, _, db_session = db_initialiser

    account1 = Account(title="John's Savings", iban="DE1234567890123456")
    db_session.add(account1)
    db_session.commit()

    # Create a second account with the same title but a different IBAN
    account2 = Account(title="John's Savings", iban="DE6543210987654321")
    db_session.add(account2)
    db_session.commit()

    # Query both accounts
    accounts = db_session.query(Account).filter_by(title="John's Savings").all()

    # Validate that two accounts exist with the same title
    assert len(accounts) == 2
    ibans = {account.iban for account in accounts}
    assert "DE1234567890123456" in ibans
    assert "DE6543210987654321" in ibans
