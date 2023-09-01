import pytest
from project.models import Transaction
from datetime import datetime, timedelta
from decimal import Decimal
from project.db import db_session


# Database connection tests
def test_starts_with_empty_database(app):
    assert Transaction.query.count() == 0

## Model initialisation tests
def test_default_date_booked(app):
    # Test that if no date_booked is provided, it defaults to the current datetime
    transaction = Transaction("Test Transaction", 100.00)
    assert isinstance(transaction.date_booked, datetime)
    assert transaction.date_booked.date() == datetime.now().date()

def test_long_title(app):
    # Test that a ValueError is raised when the title is too long
    with pytest.raises(ValueError, match="The 'title' variable must be a string with less than 80 characters."):
        Transaction("A" * 81, 100.00)

def test_invalid_amount_type(app):
    # Test that a ValueError is raised when the amount is not a valid type
    with pytest.raises(ValueError, match="The 'amount' variable must be a decimal, integer or float."):
        Transaction("Test Transaction", "invalid")

def test_invalid_date_booked_type(app):
    # Test that a ValueError is raised when date_booked is not of type datetime
    with pytest.raises(ValueError, match="date_booked is not of type datetime"):
        Transaction("Test Transaction", 100.00, date_booked="invalid_date")

def test_valid_transaction(app):
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

    db_session.expire_all()
    num_rows = db_session.query(Transaction).count()
    assert num_rows == len(transactions_to_add)



def test_saldo_calculation_with_empty_database(app):
    # Test saldo calculation when the database is empty (should be the same as the transaction amount)
    transactions_to_add = [
        Transaction("Transaction 1", 100.00),
        Transaction("Transaction 2", 200.00),
        Transaction("Transaction 3", 300.00),
    ]
    for transaction in transactions_to_add:
        db_session.add(transaction)
        db_session.commit()

    db_session.expire_all()
    transactions = db_session.query(Transaction).all()
    for transaction in transactions:
        transaction.calculate_saldo()

    assert round(transactions[0].saldo, 2) == Decimal('100')
    assert round(transactions[1].saldo, 2) == Decimal('300')
    assert round(transactions[2].saldo, 2) == Decimal('600')


def test_saldo_calculation_with_empty_unordered_dates(app):
    # Test saldo calculation when the database is empty (should be the same as the transaction amount)
    transaction1 = Transaction("Transaction 1", 50.00, date_booked=datetime(2023,8,15,15,0,0)) # First added, last in time
    transaction2 = Transaction("Transaction 2", -100.00, date_booked=datetime(2023,8,15,12,0,0))
    transaction3 = Transaction("Transaction 3", 300.00, date_booked=datetime(2023,8,15,10,0,0)) # Last added, first in time
    db_session.add(transaction1)
    db_session.add(transaction2)
    db_session.add(transaction3)
    db_session.commit()

    db_session.expire_all()

    transactions = db_session.query(Transaction).all()

    for transaction in transactions:
        transaction.calculate_saldo()

    assert round(transaction1.saldo, 2) == Decimal('250')
    assert round(transaction2.saldo, 2) == Decimal('200')
    assert round(transaction3.saldo, 2) == Decimal('300')


transactions_to_add = [
    ["Apple purchase", 30.00, datetime(2023,7,15,15,0,0)],
    ["Groceries", -500.00, datetime(2023,8,30,15,0,0)],
    ["Tickets", 300.00, datetime(2023,7,15,15,0,0)],
    ["Golf", 100.00, datetime(2023,8,15,15,0,0)],
    ["Food", 75.00, datetime(2023,6,15,15,0,0)],
    ["Cinema", 7.00, datetime(2023,8,15,15,0,0)],
    ["Rent", 200.00, datetime(2023,5,15,15,0,0)],
    ["Salary", -400.00, datetime(2023,8,15,15,0,0)],
    ["Donuts", -60.00, datetime(2023,4,15,15,0,0)],
    ["Dining", 190.00, datetime(2023,3,15,15,0,0)]
]

def test_read_all_return_list(app):

    test_transactions = []
    for element in transactions_to_add:
        transaction = Transaction(element[0], element[1], element[2])
        test_transactions.append(transaction)
        db_session.add(transaction)
    db_session.commit()
    for transaction in test_transactions:
        transaction.calculate_saldo()
    db_session.expire_all()

    assert type(Transaction.read_all()) is list


def test_read_all_no_filters(app):

    test_transactions = []
    for element in transactions_to_add:
        transaction = Transaction(element[0], element[1], element[2])
        test_transactions.append(transaction)
        db_session.add(transaction)
    db_session.commit()
    for transaction in test_transactions:
        transaction.calculate_saldo()
    db_session.expire_all()

    assert len(test_transactions) == db_session.query(Transaction).count()

    transactions = Transaction.read_all()

    assert len(transactions) > 0  # Check that there are transactions
    assert transactions == sorted(test_transactions, key=lambda x: x.date_booked, reverse=True)  # Check sorting

    newest_transaction = transactions[0]
    oldest_transaction = transactions[-1]

    assert newest_transaction == db_session.query(Transaction).filter_by(title='Groceries').all()[0]
    assert oldest_transaction == db_session.query(Transaction).filter_by(title='Dining').all()[0]


def test_read_all_exact_title_match(app):
    # Create test transactions with specific titles
    t1 = Transaction(title="Test Transaction 1", amount=100.00, date_booked=datetime.now())
    t2 = Transaction(title="Test Transaction 2", amount=200.00, date_booked=datetime.now())
    t3 = Transaction(title="Another Transaction", amount=50.00, date_booked=datetime.now())
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    transactions = Transaction.read_all(transaction_title="Test Transaction 1", search_type="Matches")

    assert len(transactions) == 1
    assert transactions[0].title == "Test Transaction 1"


def test_read_all_partial_title_match(app):
    # Create test transactions with specific titles
    t1 = Transaction(title="Test Transaction 1", amount=100.00, date_booked=datetime.now())
    t2 = Transaction(title="Test Transaction 2", amount=200.00, date_booked=datetime.now())
    t3 = Transaction(title="Another Transaction", amount=50.00, date_booked=datetime.now())
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    transactions = Transaction.read_all(transaction_title="Transaction", search_type="Contains")

    assert len(transactions) == 3


def test_read_all_date_range(app):
    # Create test transactions with specific dates
    today = datetime.now()
    t1 = Transaction(title="Transaction 1", amount=100.00, date_booked=today)
    t2 = Transaction(title="Transaction 2", amount=200.00, date_booked=today - timedelta(days=5))
    t3 = Transaction(title="Transaction 3", amount=50.00, date_booked=today - timedelta(days=10))
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    start_date = today - timedelta(days=7)
    end_date = today - timedelta(days=3)

    transactions = Transaction.read_all(start_date=start_date, end_date=end_date)

    assert len(transactions) == 1
    assert transactions[0].title == "Transaction 2"


def test_read_all_invalid_start_date(app):
    # Test case: Invalid start_date (not a datetime object)
    with pytest.raises(ValueError, match="start_date must be a datetime object."):
        Transaction.read_all(start_date="2023-01-01")

def test_read_all_invalid_end_date(app):
    # Test case: Invalid end_date (not a datetime object)
    with pytest.raises(ValueError, match="end_date must be a datetime object."):
        Transaction.read_all(end_date="2023-12-31")

def test_read_all_invalid_search_type(app):
    # Test case: Invalid search_type (not "Contains" or "Matches")
    with pytest.raises(ValueError, match="search_type must be either 'Contains' or 'Matches'."):
        Transaction.read_all(search_type="InvalidSearch")


# Test the same for group_by



# Integration tests
# Check if sum of displayed transactions is correct by implementing certain class on document
# Check if number and value of transactions is displayed correctly
