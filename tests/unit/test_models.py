import pytest
from project.models import Transaction
from datetime import datetime
from decimal import Decimal
from project.db import db_session

# Database connection tests
def test_starts_with_empty_database(app):
    assert Transaction.query.count() == 0

## Model initialisation tests
# def test_default_date_booked(app):
#     print()
#     u = Transaction('admin2', 12345)
#     db_session.add(u)
#     db_session.commit()
#     print(Transaction.query.all())
#     assert u == Decimal('123.45')


def test_default_date_booked():
    # Test that if no date_booked is provided, it defaults to the current datetime
    transaction = Transaction("Test Transaction", 100.00)
    assert isinstance(transaction.date_booked, datetime)
    assert transaction.date_booked.date() == datetime.now().date()

def test_long_title():
    # Test that a ValueError is raised when the title is too long
    with pytest.raises(ValueError, match="The 'title' variable must be a string with less than 80 characters."):
        Transaction("A" * 81, 100.00)

def test_invalid_amount_type():
    # Test that a ValueError is raised when the amount is not a valid type
    with pytest.raises(ValueError, match="The 'amount' variable must be a decimal, integer or float."):
        Transaction("Test Transaction", "invalid")

def test_invalid_date_booked_type():
    # Test that a ValueError is raised when date_booked is not of type datetime
    with pytest.raises(ValueError, match="date_booked is not of type datetime"):
        Transaction("Test Transaction", 100.00, date_booked="invalid_date")

def test_valid_transaction():
    title = "Valid Transaction"
    amount = 100.50
    date_booked = datetime(2023, 9, 1, 12, 0, 0)
    transaction = Transaction(title, amount, date_booked)

    assert transaction.title == title
    assert transaction.amount == Decimal("100.50")
    assert transaction.date_booked == date_booked

## Database tests
def test_number_of_rows_added(app):
    # Create instances of the Transaction class and add them to the database
    transactions_to_add = [
        Transaction("Transaction 1", 100.00),
        Transaction("Transaction 2", 200.00),
        Transaction("Transaction 3", 300.00),
    ]
    for transaction in transactions_to_add:
        db_session.add(transaction)

    db_session.commit()
    num_rows = db_session.query(Transaction).count()

    assert num_rows == len(transactions_to_add)
    assert len(transactions_to_add) == Transaction.query.count()



# def test_saldo_calculation_with_empty_database(client):
#     # Test saldo calculation when the database is empty (should be the same as the transaction amount)
#     transaction = Transaction(title="Transaction 1", amount=123.45)
#     transaction.calculate_saldo
#     assert round(transaction.saldo, 2) == Decimal('123.45')

# def test_saldo_calculation_with_previous_transactions():
#     # Test saldo calculation when there are previous transactions in the database
#     t1 = Transaction(title="Transaction 1", amount=100.00)
#     t2 = Transaction(title="Transaction 2", amount=-50.00)
#     t3 = Transaction(title="Transaction 3", amount=75.00)

#     assert round(t1.saldo, 2) == Decimal('100.00')
#     assert round(t2.saldo, 2) == Decimal('50.00')
#     assert round(t3.saldo, 2) == Decimal('125.00')






## Model adding to database tests


# Test title too long
# Test no title or no amount

# Test adding multiple transactions (implement that dates must be provided too) and if get_all() with filter settings works
# Test the same for group_by
# Check that the saldo is correct



# Integration tests
# Check if sum of displayed transactions is correct by implementing certain class on document
# Check if number and value of transactions is displayed correctly
