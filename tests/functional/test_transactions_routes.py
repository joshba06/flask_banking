import pytest
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

@pytest.fixture()
def first_account(db_initialiser, client_initialiser):
    # Create first account (database must have at least 1 account)
    Account, Transaction, db_session = db_initialiser

    client = client_initialiser
    client.post("/accounts/create", data={"title": "first_account"}, follow_redirects=True)
    account = Account.query.filter(Account.title == "first_account").first()
    return account

@pytest.fixture()
def second_account(db_initialiser, client_initialiser):
    # Create first account (database must have at least 1 account)
    Account, Transaction, db_session = db_initialiser

    client = client_initialiser
    client.post("/accounts/create", data={"title": "second_account"}, follow_redirects=True)
    account = Account.query.filter(Account.title == "second_account").first()
    return account


# Integration tests
# Check if sum of displayed transactions is correct by implementing certain class on document
# Check if number and value of transactions is displayed correctly


# Functional
# Include transfer can only be made to other account, not same account
# Subaccount transfer

def test_create_transaction_for_non_existent_account(client_initialiser):
    """Test trying to create a transaction for a non-existent account."""
    client = client_initialiser

    non_existent_id = 99999
    response = client.post(f'/accounts/{non_existent_id}/transactions/create', follow_redirects=True)
    assert 'Account not found.' in response.data.decode()

def test_create_valid_transaction(client_initialiser, first_account):
    """Test creating a transaction for an existing account."""
    client = client_initialiser

    # Ensure account has no transactions before POST request
    assert first_account.transactions.count() == 0

    response = client.post(f'/accounts/{first_account.id}/transactions/create', data={
        'description': 'Sample transaction',
        'amount': 100.5,
        'category': 'Rent'
    }, follow_redirects=True)

    # Ensure transaction is linked to account
    assert first_account.transactions.count() == 1
    assert first_account.transactions.first().description == 'Sample transaction'
    assert 'Successfully created new transaction.' in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

def test_create_invalid_transaction(client_initialiser, first_account):
    client = client_initialiser

    # Invalid description tests
    scenarios = [
        {
            "description": 12345,  # not a string
            "amount": 100,
            "category": "Transfer",
            "error_message": "Invalid form submission."
        },
        {
            "description": "a" * 81,  # string too long
            "amount": 100,
            "category": "Transfer",
            "error_message": "Invalid form submission."
        },
        {
            "description": "Test",
            "amount": "abc",  # not a valid number
            "category": "Transfer",
            "error_message": "Invalid form submission."
        },
        {
            "description": "Test",
            "amount": 100,
            "category": "InvalidCategory",  # not a valid category
            "error_message": "Invalid form submission."
        },
        {
            "description": "Test",
            "amount": 100,
            "category": "Transfer",
            "date_booked": "not a datetime",  # not a valid datetime
            "error_message": "Invalid form submission."
        }
    ]

    for scenario in scenarios:
        form_data = {
            "description": scenario["description"],
            "amount": scenario["amount"],
            "category": scenario["category"]
        }
        if "date_booked" in scenario:
            form_data["date_booked"] = scenario["date_booked"]

        response = client.post(f'/accounts/{first_account.id}/transactions/create', data=form_data, follow_redirects=True)

        # Check for the specific error message that we expect for each scenario
        assert scenario["error_message"] in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

def test_invalid_sender_account(client_initialiser):
    client = client_initialiser
    response = client.post("/accounts/999/transactions/create_subaccount_transfer", follow_redirects=True)  # 999 is a non-existent ID

    assert "Could not find sender account." in response.data.decode()

    # Ensure first redirect is to accounts index page
    assert response.history[1].request.path == f"/accounts"

def test_no_recipient_account_found(client_initialiser, first_account):
    client = client_initialiser

    response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
        'recipient': 'NonExistent Account (FRXX XX99)',
        'amount': 50,
        'description': 'Test transfer'
    }, follow_redirects=True)

    assert "Recipient account not found." in response.data.decode()
    # Ensure redirect is made to first account show page
    assert response.request.path == f"/accounts/{first_account.id}"

def test_invalid_transfer_amount(client_initialiser, second_account):
    response = client_initialiser.post("/accounts/1/transactions/create_subaccount_transfer", data={
        'recipient': f"{second_account.title} ({second_account.iban[:4]}...{second_account.iban[-2:]})",
        'amount': -10,
        'description': 'Test transfer'
    })
    assert b'Invalid transfer amount.' in response.data


# def test_valid_transfer(client_initialiser, first_account, second_account, db_initialiser):
#     Account, Transaction, db_session = db_initialiser
#     client = client_initialiser

#     # Ensure balance of first account will cover subaccount transfer
#     response = client.post(f'/accounts/{first_account.id}/transactions/create', data={
#         'description': 'Sample transaction',
#         'amount': 100.5,
#         'category': 'Rent'
#     }, follow_redirects=True)

#     assert first_account.transactions.all()[-1].saldo > 50

#     num_transactions_first_acc = first_account.transactions.count()
#     num_transactions_second_acc = second_account.transactions.count()

#     # Assuming you have created sender and recipient accounts and their IDs are 1 and 2
#     response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
#         'recipient': f"{second_account.title} ({second_account.iban[:4]}...{second_account.iban[-2:]})",
#         'amount': 50,
#         'description': 'Test transfer'
#     })

#     # Enure transfer was successfully created
#     assert (num_transactions_first_acc + 1) == Account.query.get(first_account.id).transactions.count()
#     assert (num_transactions_second_acc + 1) == Account.query.get(second_account.id).transactions.count()

#     # Ensure first account was deducted the amount & second account was added the amount

#     # Ensure transaction description is "Test transfer" and "Category" is transfer

#     # Ensure redirect is to first account page
#     assert b'Successfully created new transfer.' in response.data






# def test_insufficient_funds(client):
#     response = client.post("/accounts/1/transactions/create_subaccount_transfer", data={
#         'recipient': 'Recipient Account (FRXX XX99)',
#         'amount': 1000000,
#         'description': 'Test transfer'
#     })
#     assert b'Insufficient funds.' in response.data

# def test_invalid_form_submission(client):
#     response = client.post("/accounts/1/transactions/create_subaccount_transfer", data={})
#     assert b'Invalid form submission.' in response.data
