import pytest
from datetime import datetime, timedelta
import pytz

## Test fixtures
@pytest.fixture()
def first_account(db_initialiser, client_initialiser):
    # Create first account (database must have at least 1 account)
    Account, Transaction, db_session = db_initialiser

    client = client_initialiser
    client.post("/accounts/create", data={"title": "John's Savings", "accept_terms": True}, follow_redirects=True)
    account = Account.query.filter(Account.title == "John's Savings").first()
    assert account.title == "John's Savings"
    return account

@pytest.fixture()
def second_account(db_initialiser, client_initialiser):
    Account, Transaction, db_session = db_initialiser

    client = client_initialiser
    client.post("/accounts/create", data={"title": "John's Savings2", "accept_terms": True}, follow_redirects=True)
    account = Account.query.filter(Account.title == "John's Savings2").first()
    assert account.title == "John's Savings2"
    return account

@pytest.fixture()
def valid_and_invalid_transaction_data():
    data = {
    'description': {
        'valid': ["Valid", "Test123", "123"],
        'invalid': [
            {'value': "A"*81, 'error_message': "is too long - 'description'"}, #swagger generated message
            {'value': "", 'error_message': "is too short - 'description'"}, #swagger generated message
            {'value': "   ", 'error_message': "The description variable must be a string with more than 0 and less than 80 characters."}, #model generated
            {'value': None, 'error_message': "is not of type 'string' - 'description'"} #swagger generated message
        ]
        },
    'amount': {
        'valid': [-50, 0.1, 123, 999],
        'invalid': [
            {'value': 0, 'error_message': "0 should not be valid under"},
            {'value': "", 'error_message': "'' is not of type 'number' - 'amount'"},
            {'value': None, 'error_message': "None is not of type 'number' - 'amount'"},
            {'value': "invalid", 'error_message': "'invalid' is not of type 'number' - 'amount'"}
        ]
        },
    'category': {
        'valid': ["Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"],
        'invalid': [
            {'value': "Transfer", 'error_message': "'Transfer' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"}, # Transfer is only valid for subaccount_transfer!
            {'value': "", 'error_message': "'' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"},
            {'value': None, 'error_message': "None is not of type 'string' - 'category'"},
            {'value': "123", 'error_message': "'123' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"},
            {'value': "Books", 'error_message': "'Books' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"},
            {'value': "Category", 'error_message': "'Category' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"}
        ]
        },
    'utc_datetime_booked': {
        'valid': ["2023-09-04T12:00:00Z", "2021-06-01T12:00:00Z", "2027-09-04T12:14:11Z"], # None tested separatly as default date test
        'invalid': [
            {'value': "", 'error_message': "utc_datetime_booked was not provided in the correct format"},
            {'value': "   ", 'error_message': "utc_datetime_booked was not provided in the correct format"},
            {'value': "2023-09-04T12:00:00T", 'error_message': "utc_datetime_booked was not provided in the correct format"},
            {'value': "2023-09-04T", 'error_message': "utc_datetime_booked was not provided in the correct format"},
            {'value': "2023-09-04T12:00:00+02:00", 'error_message': "utc_datetime_booked was not provided in the correct format"},
            {'value': "2023/09/04T12:00:00+02:00", 'error_message': "utc_datetime_booked was not provided in the correct format"},
            {'value': "04/09/2023T12:00:00+02:00", 'error_message': "utc_datetime_booked was not provided in the correct format"},
            {'value': "2023-02-31T12:00:00Z", 'error_message': "Could not convert utc_datetime_booked to datetime object"}, # date doesnt exist
        ]
        }
    }

    return data

@pytest.fixture()
def bulk_transactions():
    transactions = [
        # For first account
        {"description": "Paypal-Henry-Thanks!", "amount": -95.00, "category": "Night out"},
        {"description": "Rent August", "amount": -600.00, "category": "Rent"},
        {"description": "Apple salary", "amount": 1200.00, "category": "Salary"},
        {"description": "Grocery Store Purchase - Kroger", "amount": -250.00, "category": "Groceries"},
        {"description": "Electric bill", "amount": -80.00, "category": "Utilities"},
        {"description": "Wire Transfer - Invoice #12345", "amount": -200.00, "category": "Groceries"},
        # For second account
        {"description": "Withdrawal - ATM Transaction", "amount": -600.00, "category": "Rent"},
        {"description": "Apple salary", "amount": 1200.00, "category": "Salary"},
        {"description": "Grocery Store Purchase - Kroger", "amount": -70.00, "category": "Groceries"},
        {"description": "Student Loan Payment - Sallie Mae", "amount": 150.00, "category": "Online services"},
    ]
    return transactions

## Route tests
# create transaction route (simulating form submission)
def test_create_transaction_invalid_form_data(client_initialiser, first_account, valid_and_invalid_transaction_data):
    client = client_initialiser

    for description in valid_and_invalid_transaction_data["description"]["invalid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions", data={
            "description": description["value"],
            "amount": 123,
            "category": "Rent"
        }, follow_redirects=True)
        assert 'Form data is not valid.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

    for amount in valid_and_invalid_transaction_data["amount"]["invalid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions", data={
            "description": "Somedesc",
            "amount": amount,
            "category": "Rent"
        }, follow_redirects=True)
        assert 'Form data is not valid.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

    for category in valid_and_invalid_transaction_data["category"]["invalid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions", data={
            "description": "Somedesc",
            "amount": 123,
            "category": category["value"]
        }, follow_redirects=True)
        assert 'Form data is not valid.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

def test_create_transaction_non_existent_account(client_initialiser, first_account):
    #Test trying to create a transaction for a non-existent account
    client = client_initialiser

    response = client.post("/accounts/999/transactions", data={
        "description": "Somedesc",
        "amount": 123,
        "category": "Rent"
    }, follow_redirects=True)

    assert 'Account not found.' in response.data.decode()

def test_create_transaction_valid_data(client_initialiser, first_account, valid_and_invalid_transaction_data):
    client = client_initialiser

    for description in valid_and_invalid_transaction_data["description"]["valid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions", data={
            "description": description,
            "amount": 123,
            "category": "Rent"
        }, follow_redirects=True)
        assert 'Successfully created new transaction.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

    for amount in valid_and_invalid_transaction_data["amount"]["valid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions", data={
            "description": "Somedesc",
            "amount": amount,
            "category": "Rent"
        }, follow_redirects=True)
        assert 'Successfully created new transaction.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

    for category in valid_and_invalid_transaction_data["category"]["valid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions", data={
            "description": "Somedesc",
            "amount": 123,
            "category": category
        }, follow_redirects=True)
        assert 'Successfully created new transaction.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

def test_create_transaction_association_and_backgref(client_initialiser, first_account, second_account, bulk_transactions, db_initialiser):
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    # Ensure no transactions were added to db before
    assert Transaction.query.count() == 0

    # Add 6 transactions to first account
    for i in range(6):
        response = client.post(f"/accounts/{first_account.id}/transactions", data={
        "description": bulk_transactions[i]["description"],
        "amount": bulk_transactions[i]["amount"],
        "category": bulk_transactions[i]["category"],
        }, follow_redirects=True)

        # Ensure single transaction was successfully added
        assert 'Successfully created new transaction.' in response.data.decode()

    # Ensure first account has 6 transactions and their data matches and is correct
    assert first_account.transactions.count() == 6
    assert first_account.transactions.filter(Transaction.description == "Paypal-Henry-Thanks!").first().amount == -95
    assert first_account.transactions.filter(Transaction.description == "Grocery Store Purchase - Kroger").first().amount == -250
    assert first_account.transactions.filter(Transaction.description == "Grocery Store Purchase - Kroger").first().saldo == 255
    assert first_account.transactions.filter(Transaction.description == "Wire Transfer - Invoice #12345").first().saldo == -25

    # Ensure backref yields the same transactions
    assert Transaction.query.filter(Transaction.account_id == first_account.id).all() == first_account.transactions.all()


    # Add 4 transactions to second account
    for i in range(6,10):
        response = client.post(f"/accounts/{second_account.id}/transactions", data={
        "description": bulk_transactions[i]["description"],
        "amount": bulk_transactions[i]["amount"],
        "category": bulk_transactions[i]["category"],
        }, follow_redirects=True)

        # Ensure single transaction was successfully added
        assert 'Successfully created new transaction.' in response.data.decode()
        assert response.request.path == f"/accounts/{second_account.id}"

    # Ensure second account has 4 transactions and their data matches and is correct
    assert second_account.transactions.count() == 4
    assert second_account.transactions.filter(Transaction.description == "Withdrawal - ATM Transaction").first().amount == -600
    assert second_account.transactions.filter(Transaction.description == "Withdrawal - ATM Transaction").first().saldo == -600
    assert second_account.transactions.filter(Transaction.description == "Student Loan Payment - Sallie Mae").first().saldo == 680

    # Ensure backref yields the same transactions
    assert Transaction.query.filter(Transaction.account_id == second_account.id).all() == second_account.transactions.all()

# create subaccount_tranfer route
'''
- Sender account invalid
- Transfer form couldnt be updated (not enough accounts available?)
- Transfer data couldnt be validated
- Recipient account couldn'nt be found
- Sender / Recipient transaction couldnt be processed, correct errors raised
- Success, error redirects and flash messages

- Sender / Recipient transaction have same amount different sign
'''

def test_create_subaccount_transfer_invalid_sender(client_initialiser, first_account):
    client = client_initialiser

    response = client.post(f"/accounts/99/transactions/create_subaccount_transfer", data={
        "description": "Transfer",
        "amount": 123,
        "recipient": "Transfer"
    }, follow_redirects=True)

    # If sender account isnt found, ensure redirect to index page occurs
    assert 'Account not found.' in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

def test_create_subaccount_transfer_cannot_update_form():
    '''If there is only one account, the transfer form'''

## API tests
# create
def test_api_create_transaction_non_existent_account(client_initialiser):
    client = client_initialiser

    response = client.post('/api/accounts/99/transactions', json={
        "description": "Test",
        "amount": 50.0,
        "category": "Groceries",
    })
    assert response.status_code == 400
    assert response.json["detail"] == "Account not found"

def test_api_create_transaction_invalid(first_account, client_initialiser, valid_and_invalid_transaction_data):
    # Invalid body data should produce automatic swagger validation error + message (see swagger.yml for request requirements)

    data = valid_and_invalid_transaction_data
    client = client_initialiser

    for description in data["description"]["invalid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": description["value"],
            "amount": 50.0,
            "category": "Groceries"
        })
        assert response.status_code == 400
        assert description['error_message'] in response.json["detail"]

    for amount in data["amount"]["invalid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": "ValidDescription",
            "amount": amount["value"],
            "category": "Groceries"
        })

        assert response.status_code == 400
        assert amount['error_message'] in response.json["detail"]

    for category in data["category"]["invalid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": "ValidDescription",
            "amount": 50,
            "category": category["value"]
        })

        assert response.status_code == 400
        assert category['error_message'] in response.json["detail"]

    for utc_datetime_booked in data["utc_datetime_booked"]["invalid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": "ValidDescription",
            "amount": 50,
            "category": "Rent",
            "utc_datetime_booked": utc_datetime_booked["value"]
        })
        assert response.status_code == 400
        assert utc_datetime_booked['error_message'] in response.json["detail"]

def test_api_create_transaction_valid(first_account, client_initialiser, valid_and_invalid_transaction_data):
    data = valid_and_invalid_transaction_data
    client = client_initialiser

    for description in data["description"]["valid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": description,
            "amount": 50.0,
            "category": "Groceries"
        })
        assert response.status_code == 201
        assert "Successfully created new transaction" in response.json["detail"]

    for amount in data["amount"]["valid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": "ValidDescription",
            "amount": amount,
            "category": "Groceries"
        })
        assert response.status_code == 201
        assert "Successfully created new transaction" in response.json["detail"]

    for category in data["category"]["valid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": "ValidDescription",
            "amount": 50,
            "category": category
        })

        assert response.status_code == 201
        assert "Successfully created new transaction" in response.json["detail"]

    for utc_datetime_booked in data["utc_datetime_booked"]["valid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": "ValidDescription",
            "amount": 50,
            "category": "Rent",
            "utc_datetime_booked": utc_datetime_booked
        })
        assert response.json["utc_datetime_booked"] == utc_datetime_booked
        assert response.status_code == 201
        assert "Successfully created new transaction" in response.json["detail"]

def test_api_create_no_date_provided(first_account, client_initialiser):
    client = client_initialiser

    response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
        "account_id": first_account.id,
        "description": "ValidDescription",
        "amount": 50,
        "category": "Rent"
    })

    assert response.status_code == 201
    assert "Successfully created new transaction" in response.json["detail"]

    # Ensure date and time are within the last 60 seconds from current time UTC
    utc_datetime_booked_string = response.json["utc_datetime_booked"]
    naive_datetime = datetime.fromisoformat(utc_datetime_booked_string.replace("Z", "+00:00"))
    utc_datetime_booked = naive_datetime.astimezone(pytz.utc)

    utc_current_time = datetime.now(pytz.utc)
    delta_t = (utc_current_time - utc_datetime_booked).total_seconds()

    assert delta_t <= 60

def test_api_create_multiple_transactions_saldo(first_account, client_initialiser, valid_and_invalid_transaction_data):
    data = valid_and_invalid_transaction_data
    client = client_initialiser

    # Ensure no transactions were added to account
    assert first_account.transactions.count() == 0

    amounts = [50, 100, 25, 12, 99]
    for i in range(5):
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": f"Transaction {i}",
            "amount": amounts[i],
            "category": "Rent"
        })
        assert response.status_code == 201
        assert "Successfully created new transaction" in response.json["detail"]

        # Ensure each transaction has correct saldo
        assert response.json["saldo"] == sum(amounts[:i+1])

def test_api_create_negative_saldo_possible(first_account, client_initialiser, valid_and_invalid_transaction_data):
    data = valid_and_invalid_transaction_data
    client = client_initialiser

    # Ensure no transactions were added to account
    assert first_account.transactions.count() == 0

    amounts = [50, 100, -300, -100]
    for i in range(4):
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": f"Transaction {i}",
            "amount": amounts[i],
            "category": "Rent"
        })
        assert response.status_code == 201
        assert "Successfully created new transaction" in response.json["detail"]

        # Ensure each transaction has correct saldo
        assert response.json["saldo"] == sum(amounts[:i+1])
    assert first_account.transactions.all()[-1].saldo == -250



# create subaccount transfer

def test_api_create_transfer_invalid():
    pass






# def test_saldo_calculation_with_empty_unordered_dates(db_initialiser):
#     # Test saldo calculation when the database is empty (should be the same as the transaction amount)
#     Account, Transaction, db_session = db_initialiser
#     account = Account(title="Jane's Savings", iban="DE6543210987654321")

#     transactions = [
#         Transaction("Transaction 1", 50.00, "Salary", date_booked=datetime(2023,8,15,15,0,0)), # First added, last in time
#         Transaction("Transaction 2", -100.00, "Rent", date_booked=datetime(2023,8,15,12,0,0)),
#         Transaction("Transaction 3", 300.00, "Salary", date_booked=datetime(2023,8,15,10,0,0)) # Last added, first in time
#     ]
#     account.transactions = transactions
#     db_session.add(account)
#     db_session.commit()
#     db_session.expire_all()

#     queried_transactions = db_session.query(Transaction).all()

#     for transaction in queried_transactions:
#         transaction.calculate_saldo()

#     assert round(transactions[0].saldo, 2) == Decimal('250')
#     assert round(transactions[1].saldo, 2) == Decimal('200')
#     assert round(transactions[2].saldo, 2) == Decimal('300')


## API tests
# Add fixture for same invalid / valid data as in web routes

# Saldo is added correctly to response


# # Functional
# # Include transfer can only be made to other account, not same account
# # Subaccount transfer



# def test_create_invalid_transaction(client_initialiser, first_account):
#     client = client_initialiser

#     # Invalid description tests
#     scenarios = [
#         {
#             "description": 12345,  # not a string
#             "amount": 100,
#             "category": "Transfer",
#             "error_message": "Invalid form submission."
#         },
#         {
#             "description": "a" * 81,  # string too long
#             "amount": 100,
#             "category": "Transfer",
#             "error_message": "Invalid form submission."
#         },
#         {
#             "description": "Test",
#             "amount": "abc",  # not a valid number
#             "category": "Transfer",
#             "error_message": "Invalid form submission."
#         },
#         {
#             "description": "Test",
#             "amount": 100,
#             "category": "InvalidCategory",  # not a valid category
#             "error_message": "Invalid form submission."
#         },
#         {
#             "description": "Test",
#             "amount": 100,
#             "category": "Transfer",
#             "date_booked": "not a datetime",  # not a valid datetime
#             "error_message": "Invalid form submission."
#         }
#     ]

#     for scenario in scenarios:
#         form_data = {
#             "description": scenario["description"],
#             "amount": scenario["amount"],
#             "category": scenario["category"]
#         }
#         if "date_booked" in scenario:
#             form_data["date_booked"] = scenario["date_booked"]

#         response = client.post(f'/accounts/{first_account.id}/transactions/create', data=form_data, follow_redirects=True)

#         # Check for the specific error message that we expect for each scenario
#         assert scenario["error_message"] in response.data.decode()
#         assert response.request.path == f"/accounts/{first_account.id}"

# def test_invalid_sender_account(client_initialiser):
#     client = client_initialiser
#     response = client.post("/accounts/999/transactions/create_subaccount_transfer", follow_redirects=True)  # 999 is a non-existent ID

#     assert "Could not find sender account." in response.data.decode()

#     # Ensure first redirect is to accounts index page
#     assert response.history[1].request.path == f"/accounts"

# def test_no_recipient_account_found(client_initialiser, first_account):
#     client = client_initialiser

#     response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
#         'recipient': 'NonExistent Account (FRXX XX99)',
#         'amount': 50,
#         'description': 'Test transfer'
#     }, follow_redirects=True)

#     assert "Recipient account not found." in response.data.decode()
#     # Ensure redirect is made to first account show page
#     assert response.request.path == f"/accounts/{first_account.id}"

# def test_invalid_transfer_amount(client_initialiser, second_account):
#     response = client_initialiser.post("/accounts/1/transactions/create_subaccount_transfer", data={
#         'recipient': f"{second_account.title} ({second_account.iban[:4]}...{second_account.iban[-2:]})",
#         'amount': -10,
#         'description': 'Test transfer'
#     })
#     assert b'Invalid transfer amount.' in response.data


# # def test_valid_transfer(client_initialiser, first_account, second_account, db_initialiser):
# #     Account, Transaction, db_session = db_initialiser
# #     client = client_initialiser

# #     # Ensure balance of first account will cover subaccount transfer
# #     response = client.post(f'/accounts/{first_account.id}/transactions/create', data={
# #         'description': 'Sample transaction',
# #         'amount': 100.5,
# #         'category': 'Rent'
# #     }, follow_redirects=True)

# #     assert first_account.transactions.all()[-1].saldo > 50

# #     num_transactions_first_acc = first_account.transactions.count()
# #     num_transactions_second_acc = second_account.transactions.count()

# #     # Assuming you have created sender and recipient accounts and their IDs are 1 and 2
# #     response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
# #         'recipient': f"{second_account.title} ({second_account.iban[:4]}...{second_account.iban[-2:]})",
# #         'amount': 50,
# #         'description': 'Test transfer'
# #     })

# #     # Enure transfer was successfully created
# #     assert (num_transactions_first_acc + 1) == Account.query.get(first_account.id).transactions.count()
# #     assert (num_transactions_second_acc + 1) == Account.query.get(second_account.id).transactions.count()

# #     # Ensure first account was deducted the amount & second account was added the amount

# #     # Ensure transaction description is "Test transfer" and "Category" is transfer

# #     # Ensure redirect is to first account page
# #     assert b'Successfully created new transfer.' in response.data
