import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pprint import pprint
import pytz
from sqlalchemy.orm.exc import NoResultFound

## Model tests (test the __init__ method)
def test_default_date_booked(model_initialiser):
    # Test that if no date_booked is provided, it defaults to the current datetime
    _, Transaction = model_initialiser

    transaction = Transaction("Test Transaction", 100.00, "Salary")
    assert isinstance(transaction.utc_datetime_booked, datetime)
    # Ensure dates match. Times do not necessarily match due to UTC time stored in db checking against local time
    assert transaction.utc_datetime_booked.date() == datetime.now().date()

def test_invalid_long_description(model_initialiser):
    # Test that a ValueError is raised when the description is too long
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="The description variable must be a string with more than 0 and less than 80 characters."):
        Transaction("A" * 81, 100.00, "Salary")

def test_invalid_whitespace_description(model_initialiser):
    # Test that a ValueError is raised when the description is too long
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="The description variable must be a string with more than 0 and less than 80 characters."):
        Transaction("    ", 100.00, "Salary")

def test_invalid_amount_type(model_initialiser):
    # Test that a ValueError is raised when the amount is not a valid type
    _, Transaction = model_initialiser

    invalid_amounts = ["abcd", [], {}, 0]
    for invalid_amount in invalid_amounts:
        with pytest.raises(ValueError, match="The amount variable must be non-zero decimal, integer or float."):
            Transaction("Description", invalid_amount, "Rent")

def test_invalid_date_booked_type(model_initialiser):
    # Test that a ValueError is raised when date_booked is not of type datetime
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="utc_datetime_booked is not of type datetime."):
        Transaction("Test Transaction", 100.00, "Salary", utc_datetime_booked="invalid_date")

    with pytest.raises(ValueError, match="utc_datetime_booked is not in UTC."):
        Transaction("Test Transaction", 100.00, "Salary", utc_datetime_booked=datetime(2023, 9, 1, 12, 0, 0))

def test_invalid_category(model_initialiser):
    _, Transaction = model_initialiser

    with pytest.raises(ValueError, match="Invalid category value."):
        Transaction("Test Transaction", 100.00, "Invalid category")

def test_valid_transaction(model_initialiser):
    _, Transaction = model_initialiser

    description = "Valid Transaction"
    amount = 100.50
    category = "Salary"
    date_booked = datetime(2023, 9, 1, 12, 0, 0)
    utc_date_booked = date_booked.replace(tzinfo=pytz.UTC)

    transaction = Transaction(description, amount, category, utc_date_booked)

    assert transaction.description == description
    assert transaction.amount == Decimal("100.50")
    assert transaction.utc_datetime_booked == utc_date_booked
    assert transaction.category == category


## Transaction sub-function tests (create_transaction, form validation etc.)
# Web route sub-function tests
@pytest.fixture
def valid_account(db_initialiser):
    Account, Transaction, db_session = db_initialiser
    account = Account("ValidAccount", "DE89370400440532013000")
    db_session.add(account)
    db_session.commit()
    assert Account.query.count() == 1

    return account

@pytest.fixture
def bulk_accounts(db_initialiser):
    Account, Transaction, db_session = db_initialiser
    account1 = Account("Main", "DE89370400440532013000")
    account2 = Account("Savings", "DE89370400440532013001")
    account3 = Account("Main", "DE89370400440532013002")
    account4 = Account("Shared", "DE89370400440532013003")
    accounts = [account1, account2, account3, account4]

    db_session.add_all(accounts)
    db_session.commit()
    assert Account.query.count() == 4

    return accounts

def test_create_transaction_valid_transaction(valid_account):
    from project.transactions.transactions import create_transaction

    status, message, _ = create_transaction(valid_account, "Description", 100, "Rent")
    assert status == "success"
    assert message == "Successfully created the transaction."

def test_create_transaction_invalid_description(valid_account):
    from project.transactions.transactions import create_transaction

    status, message, _ = create_transaction(valid_account, "A" * 81, 100, "Rent")
    assert status == "error"
    assert message == "The description variable must be a string with more than 0 and less than 80 characters."

    status, message, _ = create_transaction(valid_account, "     ", 100, "Rent")
    assert status == "error"
    assert message == "The description variable must be a string with more than 0 and less than 80 characters."

def test_create_transaction_invalid_amount(valid_account):
    from project.transactions.transactions import create_transaction

    status, message, _  = create_transaction(valid_account, "Description", "abcd", "Rent")
    assert status == "error"
    assert message == "The amount variable must be non-zero decimal, integer or float."

    status, message, _  = create_transaction(valid_account, "Description", 0, "Rent")
    assert status == "error"
    assert message == "The amount variable must be non-zero decimal, integer or float."

def test_create_transaction_invalid_category(valid_account):
    from project.transactions.transactions import create_transaction

    status, message, _ = create_transaction(valid_account, "Description", 100, "Holiday")
    assert status == "error"
    assert message == "Invalid category value."

def test_create_transaction_invalid_date_booked(valid_account):
    from project.transactions.transactions import create_transaction

    status, message, _ = create_transaction(valid_account, "Description", 100, "Rent", "2023-09-13T14:00:00Z")
    assert status == "error"
    assert message == "utc_datetime_booked is not of type datetime."

    status, message, _ = create_transaction(valid_account, "Description", 100, "Rent", datetime(2023, 9, 1, 12, 0, 0))
    assert status == "error"
    assert message == "utc_datetime_booked is not in UTC."

def test_create_transaction_valid_date_booked(valid_account):
    from project.transactions.transactions import create_transaction

    date_booked = datetime(2023, 9, 1, 12, 0, 0)
    utc_date_booked = date_booked.replace(tzinfo=pytz.UTC)

    status, message, _ = create_transaction(valid_account, "Description", 100, "Rent", utc_date_booked)
    assert status == "success"
    assert message == "Successfully created the transaction."

def test_create_transaction_database_error(account_initialiser):
    from project.transactions.transactions import create_transaction

    status, message, _ = create_transaction(None, "Description", 100, "Rent")
    assert status == "error"
    assert message == "Error occurred while creating the transaction."

def test_validate_account_nonexistent_id(valid_account):
    from project.accounts.accounts import validate_account, AccountNotFoundError

    result_account = validate_account(valid_account.id)
    assert result_account.id == valid_account.id
    assert result_account.iban == valid_account.iban

    with pytest.raises(AccountNotFoundError, match="Account with ID 99 not found."):
        validate_account(99)

def test_get_recipient_account_invalid(bulk_accounts):
    from project.transactions.transactions import get_recipient_account

    with pytest.raises(NoResultFound, match="No row was found when one was required"):
       get_recipient_account("Invalid", "123")

    with pytest.raises(NoResultFound, match="No row was found when one was required"):
       get_recipient_account("Main", "123")

    with pytest.raises(NoResultFound, match="No row was found when one was required"):
       get_recipient_account("Invalid", "DE89370400440532013002")

def test_get_recipient_account_valid(bulk_accounts):
    from project.transactions.transactions import get_recipient_account

    first = get_recipient_account("Main", "DE89...00")
    assert first.title == "Main"
    assert first.iban == "DE89370400440532013000"
    assert first.id == next((account for account in bulk_accounts if account.iban.endswith("00")), None).id

    second = get_recipient_account("Main", "DE89...02")
    assert second.title == "Main"
    assert second.iban == "DE89370400440532013002"
    assert second.id == next((account for account in bulk_accounts if account.iban.endswith("02")), None).id

    third = get_recipient_account("Shared", "DE89...03")
    assert third.title == "Shared"
    assert third.iban == "DE89370400440532013003"
    assert third.id == next((account for account in bulk_accounts if account.iban.endswith("03")), None).id

@pytest.fixture()
def configure_transfer_form(app_initialiser, bulk_accounts):
    app = app_initialiser[0]
    Account = app_initialiser[1]
    from project.transactions.transactions import update_transfer_form, SubaccountTransferForm

    assert Account.query.count() == len(bulk_accounts)

    # Assing account with iban ending "02" as current account
    sender_account =  next((account for account in bulk_accounts if account.iban.endswith("02")), None)
    assert sender_account.iban == "DE89370400440532013002"

    with app.app_context():
        form = SubaccountTransferForm()

        message, status = update_transfer_form(form, sender_account.id)
        assert status == "success"

        return form

def test_update_transfer_form_one_account_diabled(app_initialiser, valid_account):
    '''If only 1 account exists, tranfer form should be deactivated'''
    app = app_initialiser[0]
    Account = app_initialiser[1]
    from project.transactions.transactions import update_transfer_form, SubaccountTransferForm

    assert Account.query.count() == 1

    with app.app_context():
        form = SubaccountTransferForm()

        message, status = update_transfer_form(form, valid_account.id)

        assert status == "success"

        assert 'disabled' in form.description.render_kw and form.description.render_kw['disabled'] == True
        assert 'disabled' in form.amount.render_kw and form.amount.render_kw['disabled'] == True
        assert 'disabled' in form.recipient.render_kw and form.recipient.render_kw['disabled'] == True
        assert 'disabled' in form.submit.render_kw and form.submit.render_kw['disabled'] == True

def test_update_transfer_form_success(configure_transfer_form):
    form = configure_transfer_form
    # Ensure default value is "Recipient" and sender account is not in choices
    assert form.recipient.choices[0] == "Recipient"
    assert len(form.recipient.choices) == 4 # "Recipient" + 3 accounts (not sender account)

    assert form.recipient.choices == ["Recipient", "Main (DE89...00)", "Savings (DE89...01)", "Shared (DE89...03)" ]

def test_validate_transfer_data_valid_data(configure_transfer_form):
    from project.transactions.transactions import validate_transfer_data

    # Starts with form with choices and validation added. Sender account has iban DE89370400440532013002
    subaccount_transfer_form = configure_transfer_form

    # Fill form with valid data
    subaccount_transfer_form.description.data = "Valid"
    subaccount_transfer_form.amount.data = 100
    subaccount_transfer_form.recipient.data = "Main (DE89...00)"

    title, fractional_iban = validate_transfer_data(subaccount_transfer_form)

    # Ensure form accepts input as valid
    assert title == "Main"
    assert fractional_iban == "DE89...00"

def test_validate_transfer_data_invalid_recipient_format(configure_transfer_form):
    from project.transactions.transactions import validate_transfer_data

    invalid_formats = [" ", "Invalid Format", None, "Main (DE89...00", "Savings DE89...01)", "Shared(DE89...03)", "Main(DE89..00)"]

    # Starts form with choices and validation added. Sender account has iban DE89370400440532013002
    subaccount_transfer_form = configure_transfer_form

    # Fill form with valid data
    subaccount_transfer_form.description.data = "Valid"
    subaccount_transfer_form.amount.data = 100
    for invalid_recipient_format in invalid_formats:
        subaccount_transfer_form.recipient.data = invalid_recipient_format
        with pytest.raises(ValueError, match="Form data is not valid."):
            validate_transfer_data(subaccount_transfer_form)

def test_validate_transfer_data_invalid_recipient_account(configure_transfer_form):
    from project.transactions.transactions import validate_transfer_data

    recipient_sender_account = "Main (DE89...02)"

    # Starts with form with choices and validation added. Sender account has iban DE89370400440532013002
    subaccount_transfer_form = configure_transfer_form

    # Fill form with valid data
    subaccount_transfer_form.description.data = "Valid"
    subaccount_transfer_form.amount.data = 100

    subaccount_transfer_form.recipient.data = recipient_sender_account
    with pytest.raises(ValueError, match="Form data is not valid."):
        validate_transfer_data(subaccount_transfer_form)

def test_process_sender_transaction_invalid_data(configure_transfer_form, bulk_accounts):
    from project.transactions.transactions import process_sender_transaction, TransactionError
    subaccount_transfer_form = configure_transfer_form

    # Ensure transfer isnt processed with invalid form data
    subaccount_transfer_form.description.data = "A"*99
    subaccount_transfer_form.amount.data = 0
    account = bulk_accounts[0]

    with pytest.raises(TransactionError, match="The description variable must be a string with more than 0 and less than 80 characters."):
        process_sender_transaction(account, subaccount_transfer_form)

    # Ensure transfer isnt processed with invalid account
    subaccount_transfer_form.description.data = "Valid"
    subaccount_transfer_form.amount.data = 100
    account = 1

    with pytest.raises(TransactionError, match="Error occurred while creating the transaction."): #Generic error because account isnt validated in this function
        process_sender_transaction(account, subaccount_transfer_form)

def test_process_sender_transaction_valid_data(configure_transfer_form, bulk_accounts):
    from project.transactions.transactions import process_sender_transaction
    subaccount_transfer_form = configure_transfer_form

    subaccount_transfer_form.description.data = "Valid transaction 2023"
    subaccount_transfer_form.amount.data = 250
    account = bulk_accounts[0]

    process_sender_transaction(account, subaccount_transfer_form)

    transaction = next((transaction for transaction in account.transactions if transaction.description == "Valid transaction 2023"), None)
    assert transaction


# API subfunction tests
def test_validate_and_get_utc_datetime_valid_input(app_initialiser):
    from project.transactions.api import validate_and_get_utc_datetime

    valid_datetime_string = "2023-09-25T15:45:30+00:00"
    result = validate_and_get_utc_datetime(valid_datetime_string)

    expected = datetime(2023, 9, 25, 15, 45, 30, tzinfo=pytz.UTC)
    assert result == expected

def test_validate_and_get_utc_datetime_invalid_format(app_initialiser):
    from project.transactions.api import validate_and_get_utc_datetime, DateTimeFormatError

    invalid_datetime_string = "2023-09-25 15:45:30"

    with pytest.raises(DateTimeFormatError, match="utc_datetime_booked was not provided in the correct format."):
        validate_and_get_utc_datetime(invalid_datetime_string)

def test_validate_and_get_utc_datetime_unparseable_input(app_initialiser):
    from project.transactions.api import validate_and_get_utc_datetime, DateTimeConversionError

    invalid_datetime_string = "2023-13-45T99:99:99+00:00"  # Invalid month and time values

    with pytest.raises(DateTimeConversionError, match="Could not convert utc_datetime_booked to datetime object"):
        validate_and_get_utc_datetime(invalid_datetime_string)

def test_validate_and_get_utc_datetime_invalid_timezone(app_initialiser):
    from project.transactions.api import validate_and_get_utc_datetime, DateTimeFormatError

    invalid_datetime_string = "2023-09-25T15:45:30+05:00"  # +05:00 instead of +00:00

    with pytest.raises(DateTimeFormatError, match="utc_datetime_booked was not provided in the correct format."):
        validate_and_get_utc_datetime(invalid_datetime_string)







# ## Database tests (inkl. association of models Account and Transaction)
# def test_read_all_account_id_invalid_format(model_initialiser):
#     _, Transaction = model_initialiser
#     with pytest.raises(ValueError, match="account_id must be of type int."):
#         Transaction.read_all(account_id="31")

# def test_read_all_invalid_category(model_initialiser):
#     # Test invalid category
#     _, Transaction = model_initialiser

#     with pytest.raises(ValueError, match="Invalid category value."):
#         Transaction.read_all(account_id=1, category="InvalidCategory")


# @pytest.fixture()
# def generate_transactions():

#     transactions = [
#         # Year 2023 August
#         {"description": "Paypal-Henry-Thanks!", "amount": -95.00, "category": "Night out", "date_booked": datetime(2023, 8, 15, 12, 0, 0)},
#         {"description": "Rent August", "amount": -600.00, "category": "Rent", "date_booked": datetime(2023, 8, 20, 9, 0, 0)},
#         {"description": "Apple salary", "amount": 1200.00, "category": "Salary", "date_booked": datetime(2023, 8, 5, 7, 0, 0)},
#         {"description": "Grocery Store Purchase - Kroger", "amount": -250.00, "category": "Groceries", "date_booked": datetime(2023, 8, 10, 8, 0, 0)},
#         {"description": "Electric bill", "amount": -80.00, "category": "Utilities", "date_booked": datetime(2023, 8, 15, 4, 0, 0)},

#         # Year 2023 July
#         {"description": "Wire Transfer - Invoice #12345", "amount": -200.00, "category": "Groceries", "date_booked": datetime(2023, 7, 2, 12, 0, 0)},
#         {"description": "Withdrawal - ATM Transaction", "amount": -600.00, "category": "Rent", "date_booked": datetime(2023, 7, 5, 7, 0, 0)},
#         {"description": "Apple salary", "amount": 1200.00, "category": "Salary", "date_booked": datetime(2023, 7, 12, 3, 0, 0)},
#         {"description": "Grocery Store Purchase - Kroger", "amount": -70.00, "category": "Groceries", "date_booked": datetime(2023, 7, 18, 8, 0, 0)},
#         {"description": "Student Loan Payment - Sallie Mae", "amount": 150.00, "category": "Online services", "date_booked": datetime(2023, 7, 25, 15, 0, 0)},

#         # Year 2023 June
#         {"description": "Spotify lifetime membership", "amount": -99.00, "category": "Online services", "date_booked": datetime(2023, 6, 7, 16, 0, 0)},
#         {"description": "Rent June", "amount": -600.00, "category": "Rent", "date_booked": datetime(2023, 6, 11, 15, 0, 0)},
#         {"description": "Apple salary", "amount": 1200.00, "category": "Salary", "date_booked": datetime(2023, 6, 15, 12, 0, 0)},
#         {"description": "Online Purchase - Amazon", "amount": -55.00, "category": "Night out", "date_booked": datetime(2023, 6, 20, 11, 0, 0)},
#         {"description": "Utility Bill Payment - Electric", "amount": 130.00, "category": "Utilities", "date_booked": datetime(2023, 6, 30, 5, 0, 0)},

#         # Year 2023 April
#         {"description": "Dividends", "amount": 70.00, "category": "Salary", "date_booked": datetime(2023, 4, 4, 17, 0, 0)},
#         {"description": "Rent April", "amount": -600.00, "category": "Rent", "date_booked": datetime(2023, 4, 9, 15, 0, 0)},
#         {"description": "Apple salary", "amount": 1200.00, "category": "Salary", "date_booked": datetime(2023, 4, 16, 12, 0, 0)},
#         {"description": "Utility Bill Payment - Electric", "amount": -45.00, "category": "Utilities", "date_booked": datetime(2023, 4, 22, 11, 0, 0)},
#         {"description": "EDEKA sagt danke", "amount": -390.00, "category": "Groceries", "date_booked": datetime(2023, 4, 28, 8, 0, 0)},
#     ]

#     return transactions

# def test_read_all_return_list(generate_transactions, db_initialiser):
#     Account, Transaction, db_session = db_initialiser
#     account = Account(title="Jane's Savings", iban="DE6543210987654321")

#     transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
#     account.transactions = transactions_to_add
#     db_session.add(account)
#     db_session.commit()

#     for transaction in transactions_to_add:
#         transaction.calculate_saldo()
#     db_session.expire_all()

#     assert type(Transaction.read_all(account.id)) is list

# def test_read_all_no_filters(generate_transactions, db_initialiser):
#     Account, Transaction, db_session = db_initialiser
#     account1 = Account(title="Jane's Savings", iban="DE6543210987654321")
#     account2 = Account(title="Jane's Savings", iban="DE6543210987654329")

#     transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
#     for i in range(7):
#         account1.transactions.append(transactions_to_add.pop())
#     account2.transactions = transactions_to_add
#     db_session.add_all([account1, account2])
#     db_session.commit()

#     for transaction in transactions_to_add:
#         transaction.calculate_saldo()
#     db_session.expire_all()

#     assert 7 == db_session.query(Account).filter(Account.id == account1.id).first().transactions.count()
#     assert len(transactions_to_add) == db_session.query(Account).filter(Account.id == account2.id).first().transactions.count()

#     transactions_acc1 = Transaction.read_all(account1.id)
#     transactions_acc2 = Transaction.read_all(account2.id)

#     assert len(transactions_acc1) > 0 and len(transactions_acc2) > 0  # Check that there are transactions

#     assert transactions_acc2 == sorted(transactions_to_add, key=lambda x: x.date_booked, reverse=True) # Check order of transactions is desc

#     newest_transaction = transactions_acc2[0]
#     oldest_transaction = transactions_acc2[-1]

#     assert newest_transaction == db_session.query(Transaction).filter_by(account_id=account2.id, description='Rent August').all()[0]
#     assert oldest_transaction == db_session.query(Transaction).filter_by(account_id=account2.id, description='Spotify lifetime membership').all()[0]

# def test_read_all_exact_description_match(generate_transactions, db_initialiser):
#     # Create test transactions with specific descriptions
#     Account, Transaction, db_session = db_initialiser
#     account = Account(title="Jane's Savings", iban="DE6543210987654321")

#     transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
#     account.transactions = transactions_to_add
#     db_session.add(account)
#     db_session.commit()

#     transactions = Transaction.read_all(account_id=account.id, transaction_description="Spotify lifetime membership", search_type="Matches")

#     assert len(transactions) == 1
#     assert transactions[0].description == "Spotify lifetime membership"

# def test_read_all_partial_description_match(generate_transactions, db_initialiser):
#     # Create test transactions with specific descriptions
#     Account, Transaction, db_session = db_initialiser
#     account = Account(title="Jane's Savings", iban="DE6543210987654321")

#     transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
#     account.transactions = transactions_to_add
#     db_session.add(account)
#     db_session.commit()

#     # Case sensitive
#     transactions = Transaction.read_all(account_id=account.id, transaction_description="Apple", search_type="Includes")
#     assert len(transactions) == 4

#     # Case insensitive
#     transactions = Transaction.read_all(account_id=account.id, transaction_description="aPple", search_type="Includes")
#     assert len(transactions) == 4

# def test_read_all_date_range(db_initialiser):
#     # Create test transactions with specific dates
#     Account, Transaction, db_session = db_initialiser
#     account = Account(title="Jane's Savings", iban="DE6543210987654321")

#     today = datetime.now()
#     t1 = Transaction(description="Transaction 1", amount=100.00, category="Salary", date_booked=today)
#     t2 = Transaction(description="Transaction 2", amount=200.00, category="Salary", date_booked=today - timedelta(days=5))
#     t3 = Transaction(description="Transaction 3", amount=50.00, category="Salary", date_booked=today - timedelta(days=10))
#     account.transactions = [t1, t2, t3]
#     db_session.add(account)
#     db_session.commit()

#     start_date = today - timedelta(days=7)
#     end_date = today - timedelta(days=3)

#     transactions = Transaction.read_all(account_id=account.id, start_date=start_date.date(), end_date=end_date.date())

#     assert len(transactions) == 1
#     assert transactions[0].description == "Transaction 2"

# def test_read_all_category(generate_transactions, db_initialiser):
#     Account, Transaction, db_session = db_initialiser
#     account = Account(title="Jane's Savings", iban="DE6543210987654321")

#     transactions_to_add = [Transaction(**transaction) for transaction in generate_transactions]
#     account.transactions = transactions_to_add
#     db_session.add(account)
#     db_session.commit()

#     transactions = Transaction.read_all(account_id=account.id, category="Groceries")
#     assert len(transactions) == 4
#     assert transactions[0].category == "Groceries"

# def test_read_all_invalid_start_date(model_initialiser):
#     # Test case: Invalid start_date (not a datetime object)
#     _, Transaction = model_initialiser

#     with pytest.raises(ValueError, match="start_date must be a date object."):
#         Transaction.read_all(account_id=1, start_date="2023-01-01")

# def test_read_all_invalid_end_date(model_initialiser):
#     # Test case: Invalid end_date (not a datetime object)
#     _, Transaction = model_initialiser
#     with pytest.raises(ValueError, match="end_date must be a date object."):
#         Transaction.read_all(account_id=1, end_date="2023-12-31")

# def test_read_all_invalid_search_type(model_initialiser):
#     # Test case: Invalid search_type (not "Includes" or "Matches")
#     _, Transaction = model_initialiser

#     with pytest.raises(ValueError, match="search_type must be either 'Includes' or 'Matches'."):
#         Transaction.read_all(account_id=1, search_type="InvalidSearch")
