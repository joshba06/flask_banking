import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pprint import pprint


## Model initialisation tests (no db commit so account association isnt tested here)
def test_starts_with_empty_database(model_initialiser):
    _, Transaction = model_initialiser
    assert Transaction.query.count() == 0

def test_default_date_booked(model_initialiser):
    # Test that if no date_booked is provided, it defaults to the current datetime
    _, Transaction = model_initialiser

    transaction = Transaction("Test Transaction", 100.00, "Salary")
    assert isinstance(transaction.date_booked, datetime)
    assert transaction.date_booked.date() == datetime.now().date()

def test_long_description(model_initialiser):
    # Test that a ValueError is raised when the description is too long
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="The 'description' variable must be a string with less than 80 characters."):
        Transaction("A" * 81, 100.00, "Salary")

def test_invalid_amount_type(model_initialiser):
    # Test that a ValueError is raised when the amount is not a valid type
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="The 'amount' variable must be a decimal, integer or float."):
        Transaction("Test Transaction", "invalid", "Salary")

def test_invalid_date_booked_type(model_initialiser):
    # Test that a ValueError is raised when date_booked is not of type datetime
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="date_booked is not of type datetime"):
        Transaction("Test Transaction", 100.00, "Salary", date_booked="invalid_date")

def test_valid_transaction(model_initialiser):
    _, Transaction = model_initialiser

    description = "Valid Transaction"
    amount = 100.50
    category = "Salary"
    date_booked = datetime(2023, 9, 1, 12, 0, 0)
    transaction = Transaction(description, amount, category, date_booked)

    assert transaction.description == description
    assert transaction.amount == Decimal("100.50")
    assert transaction.date_booked == date_booked
    assert transaction.category == category

def test_read_all_invalid_category(model_initialiser):
    # Test invalid category
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="Invalid category value."):
        Transaction.read_all(category="InvalidCategory")



## Database tests (inkl. association of models Account and Transaction)
def test_transaction_association(db_initialiser):
    Account, Transaction, db_session = db_initialiser

    account = Account(title="John's Savings", iban="DE1234567890123456")
    db_session.add(account)
    db_session.commit()

    transaction = Transaction(description="Salary", amount=1000.0, category="Salary")
    transaction.account = account
    db_session.add(transaction)
    db_session.commit()

    retrieved_transaction = db_session.query(Transaction).first()
    assert retrieved_transaction.description == "Salary"
    assert retrieved_transaction.account == account

def test_backref_association(db_initialiser):
    Account, Transaction, db_session = db_initialiser

    account = Account(title="John's Savings", iban="DE1234567890123456")
    db_session.add(account)
    db_session.commit()

    transaction = Transaction(description="Rent", amount=-500.0, category="Rent")
    transaction.account = account
    db_session.add(transaction)
    db_session.commit()

    retrieved_account = db_session.query(Account).first()
    assert len(retrieved_account.transactions) == 1
    assert retrieved_account.transactions[0].description == "Rent"

def test_multiple_transactions(db_initialiser):
    Account, Transaction, db_session = db_initialiser

    account = Account(title="Jane's Savings", iban="DE6543210987654321")
    db_session.add(account)
    transaction1 = Transaction(description="Utilities", amount=-150.0, category="Utilities")
    transaction2 = Transaction(description="Groceries", amount=-80.0, category="Groceries")
    account.transactions = [transaction1, transaction2]
    db_session.add_all([transaction1, transaction2])
    db_session.commit()

    retrieved_account = db_session.query(Account).filter_by(title="Jane's Savings").first()
    assert len(retrieved_account.transactions) == 2

def test_number_of_rows_added(db_initialiser):
    # Create instances of the Transaction class and add them to the database
    Account, Transaction, db_session = db_initialiser
    account = Account(title="Jane's Savings", iban="DE6543210987654321")

    transactions = [
        Transaction("Transaction 1", 100.00, "Salary"),
        Transaction("Transaction 2", 200.00, "Salary"),
        Transaction("Transaction 3", 300.00, "Salary"),
    ]
    account.transactions = transactions
    db_session.add(account)
    db_session.commit()


    num_rows = len(db_session.query(Account).filter_by(iban="DE6543210987654321").first().transactions)
    assert num_rows == len(transactions)

def test_saldo_calculation_with_empty_database(db_initialiser):
    # Test saldo calculation when the database is empty (should be the same as the transaction amount)
    Account, Transaction, db_session = db_initialiser
    account = Account(title="Jane's Savings", iban="DE6543210987654321")

    transactions = [
        Transaction("Transaction 1", 100.00, "Salary"),
        Transaction("Transaction 2", 200.00, "Salary"),
        Transaction("Transaction 3", 300.00, "Salary"),
    ]
    account.transactions = transactions
    db_session.add(account)
    db_session.commit()

    db_session.expire_all()
    queried_transactions = db_session.query(Transaction).all()
    for transaction in queried_transactions:
        transaction.calculate_saldo()

    assert round(transactions[0].saldo, 2) == Decimal('100')
    assert round(transactions[1].saldo, 2) == Decimal('300')
    assert round(transactions[2].saldo, 2) == Decimal('600')

def test_saldo_calculation_with_empty_unordered_dates(db_initialiser):
    # Test saldo calculation when the database is empty (should be the same as the transaction amount)
    Account, Transaction, db_session = db_initialiser
    account = Account(title="Jane's Savings", iban="DE6543210987654321")

    transactions = [
        Transaction("Transaction 1", 50.00, "Salary", date_booked=datetime(2023,8,15,15,0,0)), # First added, last in time
        Transaction("Transaction 2", -100.00, "Rent", date_booked=datetime(2023,8,15,12,0,0)),
        Transaction("Transaction 3", 300.00, "Salary", date_booked=datetime(2023,8,15,10,0,0)) # Last added, first in time
    ]
    account.transactions = transactions
    db_session.add(account)
    db_session.commit()
    db_session.expire_all()

    queried_transactions = db_session.query(Transaction).all()

    for transaction in queried_transactions:
        transaction.calculate_saldo()

    assert round(transactions[0].saldo, 2) == Decimal('250')
    assert round(transactions[1].saldo, 2) == Decimal('200')
    assert round(transactions[2].saldo, 2) == Decimal('300')

@pytest.fixture()
def generate_transactions():

    transactions = [
        # Year 2023 August
        {"description": "Paypal-Henry-Thanks!", "amount": -95.00, "category": "Night out", "date_booked": datetime(2023, 8, 15, 12, 0, 0)},
        {"description": "Rent August", "amount": -600.00, "category": "Rent", "date_booked": datetime(2023, 8, 20, 9, 0, 0)},
        {"description": "Apple salary", "amount": 1200.00, "category": "Salary", "date_booked": datetime(2023, 8, 5, 7, 0, 0)},
        {"description": "Grocery Store Purchase - Kroger", "amount": -250.00, "category": "Groceries", "date_booked": datetime(2023, 8, 10, 8, 0, 0)},
        {"description": "Electric bill", "amount": -80.00, "category": "Utilities", "date_booked": datetime(2023, 8, 15, 4, 0, 0)},

        # Year 2023 July
        {"description": "Wire Transfer - Invoice #12345", "amount": -200.00, "category": "Groceries", "date_booked": datetime(2023, 7, 2, 12, 0, 0)},
        {"description": "Withdrawal - ATM Transaction", "amount": -600.00, "category": "Rent", "date_booked": datetime(2023, 7, 5, 7, 0, 0)},
        {"description": "Apple salary", "amount": 1200.00, "category": "Salary", "date_booked": datetime(2023, 7, 12, 3, 0, 0)},
        {"description": "Grocery Store Purchase - Kroger", "amount": -70.00, "category": "Groceries", "date_booked": datetime(2023, 7, 18, 8, 0, 0)},
        {"description": "Student Loan Payment - Sallie Mae", "amount": 150.00, "category": "Online services", "date_booked": datetime(2023, 7, 25, 15, 0, 0)},

        # Year 2023 June
        {"description": "Spotify lifetime membership", "amount": -99.00, "category": "Online services", "date_booked": datetime(2023, 6, 7, 16, 0, 0)},
        {"description": "Rent June", "amount": -600.00, "category": "Rent", "date_booked": datetime(2023, 6, 11, 15, 0, 0)},
        {"description": "Apple salary", "amount": 1200.00, "category": "Salary", "date_booked": datetime(2023, 6, 15, 12, 0, 0)},
        {"description": "Online Purchase - Amazon", "amount": -55.00, "category": "Night out", "date_booked": datetime(2023, 6, 20, 11, 0, 0)},
        {"description": "Utility Bill Payment - Electric", "amount": 130.00, "category": "Utilities", "date_booked": datetime(2023, 6, 30, 5, 0, 0)},

        # Year 2023 April
        {"description": "Dividends", "amount": 70.00, "category": "Salary", "date_booked": datetime(2023, 4, 4, 17, 0, 0)},
        {"description": "Rent April", "amount": -600.00, "category": "Rent", "date_booked": datetime(2023, 4, 9, 15, 0, 0)},
        {"description": "Apple salary", "amount": 1200.00, "category": "Salary", "date_booked": datetime(2023, 4, 16, 12, 0, 0)},
        {"description": "Utility Bill Payment - Electric", "amount": -45.00, "category": "Utilities", "date_booked": datetime(2023, 4, 22, 11, 0, 0)},
        {"description": "EDEKA sagt danke", "amount": -390.00, "category": "Groceries", "date_booked": datetime(2023, 4, 28, 8, 0, 0)},
    ]

    return transactions

def test_read_all_return_list(generate_transactions, db_initialiser):
    Account, Transaction, db_session = db_initialiser
    account = Account(title="Jane's Savings", iban="DE6543210987654321")

    transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
    account.transactions = transactions_to_add
    db_session.add(account)
    db_session.commit()

    for transaction in transactions_to_add:
        transaction.calculate_saldo()
    db_session.expire_all()

    assert type(Transaction.read_all()) is list

def test_read_all_no_filters(generate_transactions, db_initialiser):
    Account, Transaction, db_session = db_initialiser
    account = Account(title="Jane's Savings", iban="DE6543210987654321")

    transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
    account.transactions = transactions_to_add
    db_session.add(account)
    db_session.commit()

    for transaction in transactions_to_add:
        transaction.calculate_saldo()
    db_session.expire_all()

    assert len(transactions_to_add) == db_session.query(Transaction).count()

    transactions = Transaction.read_all()

    assert len(transactions) > 0  # Check that there are transactions
    assert transactions == sorted(transactions_to_add, key=lambda x: x.date_booked, reverse=True) # Check order of transactions is desc

    newest_transaction = transactions[0]
    oldest_transaction = transactions[-1]

    assert newest_transaction == db_session.query(Transaction).filter_by(description='Rent August').all()[0]
    assert oldest_transaction == db_session.query(Transaction).filter_by(description='Dividends').all()[0]

def test_read_all_exact_description_match(generate_transactions, db_initialiser):
    # Create test transactions with specific descriptions
    Account, Transaction, db_session = db_initialiser
    account = Account(title="Jane's Savings", iban="DE6543210987654321")

    transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
    account.transactions = transactions_to_add
    db_session.add(account)
    db_session.commit()

    transactions = Transaction.read_all(transaction_description="Spotify lifetime membership", search_type="Matches")

    assert len(transactions) == 1
    assert transactions[0].description == "Spotify lifetime membership"

def test_read_all_partial_description_match(generate_transactions, db_initialiser):
    # Create test transactions with specific descriptions
    Account, Transaction, db_session = db_initialiser
    account = Account(title="Jane's Savings", iban="DE6543210987654321")

    transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
    account.transactions = transactions_to_add
    db_session.add(account)
    db_session.commit()

    # Case sensitive
    transactions = Transaction.read_all(transaction_description="Apple", search_type="Includes")
    assert len(transactions) == 4

    # Case insensitive
    transactions = Transaction.read_all(transaction_description="aPple", search_type="Includes")
    assert len(transactions) == 4

def test_read_all_date_range(db_initialiser):
    # Create test transactions with specific dates
    Account, Transaction, db_session = db_initialiser
    account = Account(title="Jane's Savings", iban="DE6543210987654321")

    today = datetime.now()
    t1 = Transaction(description="Transaction 1", amount=100.00, category="Salary", date_booked=today)
    t2 = Transaction(description="Transaction 2", amount=200.00, category="Salary", date_booked=today - timedelta(days=5))
    t3 = Transaction(description="Transaction 3", amount=50.00, category="Salary", date_booked=today - timedelta(days=10))
    account.transactions = [t1, t2, t3]
    db_session.add(account)
    db_session.commit()

    start_date = today - timedelta(days=7)
    end_date = today - timedelta(days=3)

    transactions = Transaction.read_all(start_date=start_date.date(), end_date=end_date.date())

    assert len(transactions) == 1
    assert transactions[0].description == "Transaction 2"

def test_read_all_category(generate_transactions, db_initialiser):
    Account, Transaction, db_session = db_initialiser
    account = Account(title="Jane's Savings", iban="DE6543210987654321")

    transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
    account.transactions = transactions_to_add
    db_session.add(account)
    db_session.commit()

    transactions = Transaction.read_all(category="Groceries")
    assert len(transactions) == 4
    assert transactions[0].category == "Groceries"

def test_read_all_invalid_start_date(model_initialiser):
    # Test case: Invalid start_date (not a datetime object)
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="start_date must be a date object."):
        Transaction.read_all(start_date="2023-01-01")

def test_read_all_invalid_end_date(model_initialiser):
    # Test case: Invalid end_date (not a datetime object)
    _, Transaction = model_initialiser
    with pytest.raises(ValueError, match="end_date must be a date object."):
        Transaction.read_all(end_date="2023-12-31")

def test_read_all_invalid_search_type(model_initialiser):
    # Test case: Invalid search_type (not "Includes" or "Matches")
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="search_type must be either 'Includes' or 'Matches'."):
        Transaction.read_all(search_type="InvalidSearch")

def test_group_by_month_valid_input(model_initialiser):
    # Test case: Valid input
    _, Transaction = model_initialiser
    transactions = [
        Transaction(description="Income 1", amount=100.00, category="Salary", date_booked=datetime(2023, 1, 15)),
        Transaction(description="Expense 1", amount=-50.00, category="Rent", date_booked=datetime(2023, 1, 20)),
    ]
    result = Transaction.group_by_month(transactions)
    assert isinstance(result, dict)

def test_group_by_month_invalid_input_not_list(model_initialiser):
    # Test case: Invalid input (not a list)
    _, Transaction = model_initialiser

    with pytest.raises(TypeError, match="Input transactions must be a list."):
        Transaction.group_by_month("invalid_input")

def test_group_by_month_invalid_input_not_transaction_objects(model_initialiser):
    # Test case: Invalid input (not a list of Transaction objects)
    _, Transaction = model_initialiser

    with pytest.raises(TypeError, match="Input transactions must be a list of Transaction objects."):
        Transaction.group_by_month([1, 2, 3])

def test_group_by_month_data_calculation(model_initialiser):
    _, Transaction = model_initialiser

    transactions = [
        Transaction(description="Income 1", amount=100.00, category="Rent", date_booked=datetime(2023, 1, 15)),
        Transaction(description="Expense 1", amount=-50.00, category="Rent", date_booked=datetime(2023, 1, 20)),
        Transaction(description="Income 2", amount=75.00, category="Rent", date_booked=datetime(2023, 2, 5)),
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

def test_group_by_month_empty_input(model_initialiser):
    # Test case: Empty input list
    Transaction = model_initialiser

    transactions = []
    result = Transaction.group_by_month(transactions)
    assert result == {}  # Expect an empty dictionary for an empty input list

def test_group_by_month_single_transaction(model_initialiser):
    # Test case: Input with a single transaction
    Transaction = model_initialiser

    transactions = [
        Transaction(description="Income 1", amount=100.00, category="Rent", date_booked=datetime(2023, 1, 15))
    ]
    result = Transaction.group_by_month(transactions)
    assert len(result) == 1  # Expect one year
    assert 2023 in result  # Year 2023 should be present
    assert len(result[2023]) == 1  # Expect one month
    assert 1 in result[2023]  # Month 1 should be present

def test_group_by_month_multiple_years(model_initialiser):
    # Test case: Input with transactions spanning multiple years
    Transaction = model_initialiser

    transactions = [
        Transaction(description="Income 1", amount=100.00, category="Rent", date_booked=datetime(2022, 12, 15)),
        Transaction(description="Income 2", amount=200.00, category="Rent", date_booked=datetime(2023, 1, 5)),
        Transaction(description="Expense 1", amount=-50.00, category="Rent", date_booked=datetime(2023, 2, 20)),
    ]
    result = Transaction.group_by_month(transactions)
    assert len(result) == 2  # Expect two years (2022 and 2023)
    assert 2022 in result and 2023 in result  # Years 2022 and 2023 should be present
    assert len(result[2022]) == 1  # Expect one month (December)
    assert 12 in result[2022]  # Month 12 (December) should be present
    assert len(result[2023]) == 2  # Expect two months (January and February)
    assert 1 in result[2023] and 2 in result[2023]  # Months 1 (January) and 2 (February) should be present

def test_group_by_month_mixed_income_expense(model_initialiser):
    # Test case: Input with mixed income and expense transactions
    Transaction = model_initialiser

    transactions = [
        Transaction(description="Income 1", amount=100.00, category="Rent", date_booked=datetime(2023, 1, 15)),
        Transaction(description="Expense 1", amount=-50.00, category="Rent", date_booked=datetime(2023, 1, 20)),
        Transaction(description="Income 2", amount=75.00, category="Rent", date_booked=datetime(2023, 2, 5)),
    ]
    result = Transaction.group_by_month(transactions)
    assert result[2023][1]["income"] == 100.00  # January income
    assert result[2023][1]["expenses"] == -50.00  # January expenses
    assert result[2023][1]["total"] == 50.00  # January total
    assert result[2023][2]["income"] == 75.00  # February income
    assert result[2023][2]["expenses"] == 0  # February expenses
    assert result[2023][2]["total"] == 75.00  # February total

def test_group_by_month_negative_amounts_only(model_initialiser):
    # Test case: Input with transactions having only negative amounts
    Transaction = model_initialiser

    transactions = [
        Transaction(description="Expense 1", amount=-50.00, category="Rent", date_booked=datetime(2023, 1, 15)),
        Transaction(description="Expense 2", amount=-75.00, category="Rent", date_booked=datetime(2023, 2, 5)),
    ]
    result = Transaction.group_by_month(transactions)
    assert result[2023][1]["income"] == 0  # January income
    assert result[2023][1]["expenses"] == -50.00  # January expenses
    assert result[2023][1]["total"] == -50.00  # January total
    assert result[2023][2]["income"] == 0  # February income
    assert result[2023][2]["expenses"] == -75.00  # February expenses
    assert result[2023][2]["total"] == -75.00  # February total

def test_group_by_month_positive_amounts_only(model_initialiser):
    # Test case: Input with transactions having only positive amounts
    Transaction = model_initialiser

    transactions = [
        Transaction(description="Income 1", amount=100.00, category="Rent", date_booked=datetime(2023, 1, 15)),
        Transaction(description="Income 2", amount=75.00, category="Rent", date_booked=datetime(2023, 2, 5)),
    ]
    result = Transaction.group_by_month(transactions)
    assert result[2023][1]["income"] == 100.00  # January income
    assert result[2023][1]["expenses"] == 0  # January expenses
    assert result[2023][1]["total"] == 100.00  # January total
    assert result[2023][2]["income"] == 75.00  # February

def test_group_by_month_multiple_years_months(model_initialiser):
    # Test case: Input with transactions spanning 4 years (2022 to 2025) and 5 months per year
    Transaction = model_initialiser

    transactions = [
        # Year 2022
        Transaction(description="Income 1", amount=100.00, category="Rent", date_booked=datetime(2022, 1, 15)),
        Transaction(description="Expense 1", amount=-50.00, category="Rent", date_booked=datetime(2022, 2, 20)),
        Transaction(description="Income 2", amount=75.00, category="Rent", date_booked=datetime(2022, 3, 5)),
        Transaction(description="Income 3", amount=120.00, category="Rent", date_booked=datetime(2022, 4, 10)),
        Transaction(description="Expense 2", amount=-80.00, category="Rent", date_booked=datetime(2022, 5, 15)),

        # Year 2023
        Transaction(description="Income 4", amount=200.00, category="Rent", date_booked=datetime(2023, 1, 2)),
        Transaction(description="Expense 3", amount=-60.00, category="Rent", date_booked=datetime(2023, 2, 5)),
        Transaction(description="Income 5", amount=90.00, category="Rent", date_booked=datetime(2023, 3, 12)),
        Transaction(description="Expense 4", amount=-70.00, category="Rent", date_booked=datetime(2023, 4, 18)),
        Transaction(description="Income 6", amount=150.00, category="Rent", date_booked=datetime(2023, 5, 25)),

        # Year 2024
        Transaction(description="Expense 5", amount=-40.00, category="Rent", date_booked=datetime(2024, 1, 7)),
        Transaction(description="Income 7", amount=80.00, category="Rent", date_booked=datetime(2024, 2, 11)),
        Transaction(description="Income 8", amount=110.00, category="Rent", date_booked=datetime(2024, 3, 15)),
        Transaction(description="Expense 6", amount=-55.00, category="Rent", date_booked=datetime(2024, 4, 20)),
        Transaction(description="Income 9", amount=130.00, category="Rent", date_booked=datetime(2024, 5, 30)),

        # Year 2025
        Transaction(description="Income 10", amount=70.00, category="Rent", date_booked=datetime(2025, 1, 4)),
        Transaction(description="Expense 7", amount=-30.00,  category="Rent", date_booked=datetime(2025, 2, 9)),
        Transaction(description="Income 11", amount=140.00, category="Rent", date_booked=datetime(2025, 3, 16)),
        Transaction(description="Expense 8", amount=-45.00, category="Rent", date_booked=datetime(2025, 4, 22)),
        Transaction(description="Income 12", amount=95.00, category="Rent", date_booked=datetime(2025, 5, 28)),
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
