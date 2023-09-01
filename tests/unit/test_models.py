import pytest
from project.models import Transaction
from datetime import datetime
from decimal import Decimal
from project.db import db_session

def test_default_date_booked(app):
    print(Transaction.query.all())
    u = Transaction('admin2', 12345)
    db_session.add(u)
    db_session.commit()
    print(Transaction.query.all())
    assert u == Decimal('123.45')



























## Model initialisation tests
# def test_default_date_booked(session):


    # print("Session has: {} entries".format(session.query(Transaction).count()))
    # Transaction(title="Test Transaction", amount=100.00)

    # # Session = db_session()
    # new_transaction = Transaction("Hello", 123)
    # print("2 Session has: {} entries".format(session.query(Transaction).count()))
    # session.add(new_transaction)
    # session.commit()

    # print("3 Session has: {} entries".format(session.query(Transaction).count()))

    # trs = Transaction("Hello", 123)
    # db_session.add(trs)

    # Create new session and see if adding Transaction will add to db
    # print(db_session.query(Transaction).all())

    # Commit to db and see if now db has more entries


    # Test that if no date_booked is provided, it defaults to the current datetime
    # transaction = Transaction(title="Test Transaction", amount=100.00)
    # assert isinstance(transaction.amount, datetime)

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

# def test_long_title():
#     # Test that a ValueError is raised when the title is too long
#     with pytest.raises(ValueError, match="title must be a string with less than 80 characters"):
#         Transaction(title="A" * 81, amount=100.00)

# def test_invalid_amount_type():
#     # Test that a ValueError is raised when the amount is not a valid type
#     with pytest.raises(ValueError, match="amount must be a decimal, integer or float"):
#         Transaction(title="Test Transaction", amount="invalid")

# def test_invalid_date_booked_type():
#     # Test that a ValueError is raised when date_booked is not of type datetime
#     with pytest.raises(ValueError, match="date_booked is not of type datetime"):
#         Transaction(title="Test Transaction", amount=100.00, date_booked="invalid_date")

# def test_no_title_provided():
#     transaction = Transaction()
#     assert transaction.saldo == Decimal('123.45')


## Model adding to database tests


# Test title too long
# Test no title or no amount

# Test adding multiple transactions (implement that dates must be provided too) and if get_all() with filter settings works
# Test the same for group_by
# Check that the saldo is correct



# Integration tests
# Check if sum of displayed transactions is correct by implementing certain class on document
# Check if number and value of transactions is displayed correctly
