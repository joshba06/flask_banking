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


def test_group_by_month_valid_input():
    # Test case: Valid input
    transactions = [
        Transaction(title="Income 1", amount=100.00, date_booked=datetime(2023, 1, 15)),
        Transaction(title="Expense 1", amount=-50.00, date_booked=datetime(2023, 1, 20)),
    ]
    result = Transaction.group_by_month(transactions)
    assert isinstance(result, dict)

def test_group_by_month_invalid_input_not_list():
    # Test case: Invalid input (not a list)
    with pytest.raises(TypeError, match="Input transactions must be a list."):
        Transaction.group_by_month("invalid_input")

def test_group_by_month_invalid_input_not_transaction_objects():
    # Test case: Invalid input (not a list of Transaction objects)
    with pytest.raises(TypeError, match="Input transactions must be a list of Transaction objects."):
        Transaction.group_by_month([1, 2, 3])

def test_group_by_month_data_calculation():
    transactions = [
        Transaction(title="Income 1", amount=100.00, date_booked=datetime(2023, 1, 15)),
        Transaction(title="Expense 1", amount=-50.00, date_booked=datetime(2023, 1, 20)),
        Transaction(title="Income 2", amount=75.00, date_booked=datetime(2023, 2, 5)),
    ]
    result = Transaction.group_by_month(transactions)

    # Check the calculated data for January 2023
    assert result[2023][1]["income"] == 100.00
    assert result[2023][1]["expenses"] == -50.00
    assert result[2023][1]["total"] == 50.00

    # Check the calculated data for February 2023
    assert result[2023][2]["income"] == 75.00
    assert result[2023][2]["expenses"] == 0  # No expenses in February
    assert result[2023][2]["total"] == 75.00


def test_group_by_month_empty_input():
    # Test case: Empty input list
    transactions = []
    result = Transaction.group_by_month(transactions)
    assert result == {}  # Expect an empty dictionary for an empty input list

def test_group_by_month_single_transaction():
    # Test case: Input with a single transaction
    transactions = [
        Transaction(title="Income 1", amount=100.00, date_booked=datetime(2023, 1, 15))
    ]
    result = Transaction.group_by_month(transactions)
    assert len(result) == 1  # Expect one year
    assert 2023 in result  # Year 2023 should be present
    assert len(result[2023]) == 1  # Expect one month
    assert 1 in result[2023]  # Month 1 should be present

def test_group_by_month_multiple_years():
    # Test case: Input with transactions spanning multiple years
    transactions = [
        Transaction(title="Income 1", amount=100.00, date_booked=datetime(2022, 12, 15)),
        Transaction(title="Income 2", amount=200.00, date_booked=datetime(2023, 1, 5)),
        Transaction(title="Expense 1", amount=-50.00, date_booked=datetime(2023, 2, 20)),
    ]
    result = Transaction.group_by_month(transactions)
    assert len(result) == 2  # Expect two years (2022 and 2023)
    assert 2022 in result and 2023 in result  # Years 2022 and 2023 should be present
    assert len(result[2022]) == 1  # Expect one month (December)
    assert 12 in result[2022]  # Month 12 (December) should be present
    assert len(result[2023]) == 2  # Expect two months (January and February)
    assert 1 in result[2023] and 2 in result[2023]  # Months 1 (January) and 2 (February) should be present

def test_group_by_month_mixed_income_expense():
    # Test case: Input with mixed income and expense transactions
    transactions = [
        Transaction(title="Income 1", amount=100.00, date_booked=datetime(2023, 1, 15)),
        Transaction(title="Expense 1", amount=-50.00, date_booked=datetime(2023, 1, 20)),
        Transaction(title="Income 2", amount=75.00, date_booked=datetime(2023, 2, 5)),
    ]
    result = Transaction.group_by_month(transactions)
    assert result[2023][1]["income"] == 100.00  # January income
    assert result[2023][1]["expenses"] == -50.00  # January expenses
    assert result[2023][1]["total"] == 50.00  # January total
    assert result[2023][2]["income"] == 75.00  # February income
    assert result[2023][2]["expenses"] == 0  # February expenses
    assert result[2023][2]["total"] == 75.00  # February total

def test_group_by_month_negative_amounts_only():
    # Test case: Input with transactions having only negative amounts
    transactions = [
        Transaction(title="Expense 1", amount=-50.00, date_booked=datetime(2023, 1, 15)),
        Transaction(title="Expense 2", amount=-75.00, date_booked=datetime(2023, 2, 5)),
    ]
    result = Transaction.group_by_month(transactions)
    assert result[2023][1]["income"] == 0  # January income
    assert result[2023][1]["expenses"] == -50.00  # January expenses
    assert result[2023][1]["total"] == -50.00  # January total
    assert result[2023][2]["income"] == 0  # February income
    assert result[2023][2]["expenses"] == -75.00  # February expenses
    assert result[2023][2]["total"] == -75.00  # February total

def test_group_by_month_positive_amounts_only():
    # Test case: Input with transactions having only positive amounts
    transactions = [
        Transaction(title="Income 1", amount=100.00, date_booked=datetime(2023, 1, 15)),
        Transaction(title="Income 2", amount=75.00, date_booked=datetime(2023, 2, 5)),
    ]
    result = Transaction.group_by_month(transactions)
    assert result[2023][1]["income"] == 100.00  # January income
    assert result[2023][1]["expenses"] == 0  # January expenses
    assert result[2023][1]["total"] == 100.00  # January total
    assert result[2023][2]["income"] == 75.00  # February


def test_group_by_month_multiple_years_months():
    # Test case: Input with transactions spanning 4 years (2022 to 2025) and 5 months per year
    transactions = [
        # Year 2022
        Transaction(title="Income 1", amount=100.00, date_booked=datetime(2022, 1, 15)),
        Transaction(title="Expense 1", amount=-50.00, date_booked=datetime(2022, 2, 20)),
        Transaction(title="Income 2", amount=75.00, date_booked=datetime(2022, 3, 5)),
        Transaction(title="Income 3", amount=120.00, date_booked=datetime(2022, 4, 10)),
        Transaction(title="Expense 2", amount=-80.00, date_booked=datetime(2022, 5, 15)),

        # Year 2023
        Transaction(title="Income 4", amount=200.00, date_booked=datetime(2023, 1, 2)),
        Transaction(title="Expense 3", amount=-60.00, date_booked=datetime(2023, 2, 5)),
        Transaction(title="Income 5", amount=90.00, date_booked=datetime(2023, 3, 12)),
        Transaction(title="Expense 4", amount=-70.00, date_booked=datetime(2023, 4, 18)),
        Transaction(title="Income 6", amount=150.00, date_booked=datetime(2023, 5, 25)),

        # Year 2024
        Transaction(title="Expense 5", amount=-40.00, date_booked=datetime(2024, 1, 7)),
        Transaction(title="Income 7", amount=80.00, date_booked=datetime(2024, 2, 11)),
        Transaction(title="Income 8", amount=110.00, date_booked=datetime(2024, 3, 15)),
        Transaction(title="Expense 6", amount=-55.00, date_booked=datetime(2024, 4, 20)),
        Transaction(title="Income 9", amount=130.00, date_booked=datetime(2024, 5, 30)),

        # Year 2025
        Transaction(title="Income 10", amount=70.00, date_booked=datetime(2025, 1, 4)),
        Transaction(title="Expense 7", amount=-30.00, date_booked=datetime(2025, 2, 9)),
        Transaction(title="Income 11", amount=140.00, date_booked=datetime(2025, 3, 16)),
        Transaction(title="Expense 8", amount=-45.00, date_booked=datetime(2025, 4, 22)),
        Transaction(title="Income 12", amount=95.00, date_booked=datetime(2025, 5, 28)),
    ]
    result = Transaction.group_by_month(transactions)

    # Check for all 4 years
    for year in range(2022, 2026):
        assert year in result
        assert len(result[year]) == 5  # Expect 5 months of data for each year

    # Check for specific months in each year (e.g., January, February, etc.)
    for year in range(2022, 2026):
        for month in range(1, 6):
            assert month in result[year]
            assert isinstance(result[year][month], dict)
            assert "income" in result[year][month]
            assert "expenses" in result[year][month]
            assert "total" in result[year][month]
