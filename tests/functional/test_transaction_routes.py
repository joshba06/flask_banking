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
            {'value': "A"*81, 'error_message': "is too long - 'description'"}, # swagger generated message
            {'value': "", 'error_message': "is too short - 'description'"}, # swagger generated message
            {'value': "   ", 'error_message': "The description variable must be a string with more than 0 and less than 80 characters."}, # model generated error message
            {'value': None, 'error_message': "is not of type 'string' - 'description'"} # swagger generated message
        ]
        },
    'amount': {
        'valid': [-50, 0.1, 123, 999],
        'invalid': [
            {'value': 0, 'error_message': "0 should not be valid under"}, #swagger generated message
            {'value': "", 'error_message': "'' is not of type 'number' - 'amount'"}, #swagger generated message
            {'value': None, 'error_message': "None is not of type 'number' - 'amount'"}, #swagger generated message
            {'value': "invalid", 'error_message': "'invalid' is not of type 'number' - 'amount'"} #swagger generated message
        ]
        },
    'category': {
        'valid': ["Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"],
        'invalid': [
            {'value': "Transfer", 'error_message': "'Transfer' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"}, # Transfer is only valid for subaccount_transfer! (swagger generated message)
            {'value': "", 'error_message': "'' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"}, #swagger generated message
            {'value': None, 'error_message': "None is not of type 'string' - 'category'"}, #swagger generated message
            {'value': "123", 'error_message': "'123' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"}, #swagger generated message
            {'value': "Books", 'error_message': "'Books' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"}, #swagger generated message
            {'value': "Category", 'error_message': "'Category' is not one of ['Salary', 'Rent', 'Utilities', 'Groceries', 'Night out', 'Online services'] - 'category'"} #swagger generated message
        ]
        },
    'utc_datetime_booked': {
        'valid': ["2023-09-04T12:00:00+00:00", "2021-06-01T12:00:00+00:00", "2027-09-04T12:14:11+00:00"], # None tested separatly as default date test
        'invalid': [
            {'value': "", 'error_message': "utc_datetime_booked was not provided in the correct format"}, # API endpoint error message
            {'value': "   ", 'error_message': "utc_datetime_booked was not provided in the correct format"}, # API endpoint error message
            {'value': "2023-09-04T12:00:00T", 'error_message': "utc_datetime_booked was not provided in the correct format"}, # API endpoint error message
            {'value': "2023-09-04T", 'error_message': "utc_datetime_booked was not provided in the correct format"}, # API endpoint error message
            {'value': "2023-09-04T12:00:00Z", 'error_message': "utc_datetime_booked was not provided in the correct format"}, # API endpoint error message
            {'value': "2023/09/04T12:00:00+02:00", 'error_message': "utc_datetime_booked was not provided in the correct format"}, # API endpoint error message
            {'value': "04/09/2023T12:00:00+02:00", 'error_message': "utc_datetime_booked was not provided in the correct format"}, # API endpoint error message
            {'value': "2023-02-31T12:00:00+00:00", 'error_message': "Could not convert utc_datetime_booked to datetime object"}, # date doesnt exist (API endpoint error message)
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
        print(response.data.decode())
        assert 'Successfully created the transaction.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

    for amount in valid_and_invalid_transaction_data["amount"]["valid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions", data={
            "description": "Somedesc",
            "amount": amount,
            "category": "Rent"
        }, follow_redirects=True)
        assert 'Successfully created the transaction.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

    for category in valid_and_invalid_transaction_data["category"]["valid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions", data={
            "description": "Somedesc",
            "amount": 123,
            "category": category
        }, follow_redirects=True)
        assert 'Successfully created the transaction.' in response.data.decode()
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
        assert 'Successfully created the transaction.' in response.data.decode()

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
        assert 'Successfully created the transaction.' in response.data.decode()
        assert response.request.path == f"/accounts/{second_account.id}"

    # Ensure second account has 4 transactions and their data matches and is correct
    assert second_account.transactions.count() == 4
    assert second_account.transactions.filter(Transaction.description == "Withdrawal - ATM Transaction").first().amount == -600
    assert second_account.transactions.filter(Transaction.description == "Withdrawal - ATM Transaction").first().saldo == -600
    assert second_account.transactions.filter(Transaction.description == "Student Loan Payment - Sallie Mae").first().saldo == 680

    # Ensure backref yields the same transactions
    assert Transaction.query.filter(Transaction.account_id == second_account.id).all() == second_account.transactions.all()

# create subaccount_transfer route
def test_create_subaccount_transfer_invalid_sender(client_initialiser, first_account):
    client = client_initialiser

    response = client.post(f"/accounts/99/transactions/create_subaccount_transfer", data={
        "description": "Transfer",
        "amount": 123,
        "recipient": "Transfer"
    }, follow_redirects=True)

    # If sender account isnt found, ensure redirect to index page occurs
    assert 'Account with ID 99 not found.' in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

def test_create_subaccount_transfer_invalid_form_data(client_initialiser, first_account, second_account, valid_and_invalid_transaction_data):
    client = client_initialiser

    recipient_valid_choice = f"{second_account.title} ({second_account.iban[:4]}...{second_account.iban[-2:]})"

    # Assuming first_account and second_account exist (for redirect)
    for description in valid_and_invalid_transaction_data["description"]["invalid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
            "description": description["value"],
            "amount": 123,
            "recipient": recipient_valid_choice
        }, follow_redirects=True)
        assert 'Form data is not valid.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

    for amount in valid_and_invalid_transaction_data["amount"]["invalid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
            "description": "Somedesc",
            "amount": amount,
            "recipient": recipient_valid_choice
        }, follow_redirects=True)
        assert 'Form data is not valid.' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

    # Ensure "Recipient" cannot be selected recipient
    response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
        "description": "Somedesc",
        "amount": 123,
        "recipient": "Recipient"
    }, follow_redirects=True)

    assert 'Form data is not valid.' in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

def test_create_subaccount_transfer_invalid_recipient(client_initialiser, first_account, second_account, valid_and_invalid_transaction_data):
    client = client_initialiser

    response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
        "description": "Valid description",
        "amount": 123,
        "recipient": "Invalid recipient"
    }, follow_redirects=True)

    assert 'Form data is not valid.' in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

def test_create_subaccount_transfer_valid_form_data(client_initialiser, first_account, second_account, valid_and_invalid_transaction_data):
    client = client_initialiser

    recipient_valid_choice = f"{second_account.title} ({second_account.iban[:4]}...{second_account.iban[-2:]})"

    for description in valid_and_invalid_transaction_data["description"]["valid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
            "description": description,
            "amount": 123,
            "recipient": recipient_valid_choice
        }, follow_redirects=True)
        assert 'Successfully created transfer' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

    for amount in valid_and_invalid_transaction_data["amount"]["valid"]:
        response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
            "description": "Somedesc",
            "amount": amount,
            "recipient": recipient_valid_choice
        }, follow_redirects=True)
        assert 'Successfully created transfer' in response.data.decode()
        assert response.request.path == f"/accounts/{first_account.id}"

def test_create_subaccount_transfer_valid_result_both_ends(client_initialiser, first_account, second_account, valid_and_invalid_transaction_data):
    client = client_initialiser

    # Ensure both accounts do not have any transactions
    assert first_account.transactions.count() == 0
    assert second_account.transactions.count() == 0

    response = client.post(f"/accounts/{first_account.id}/transactions/create_subaccount_transfer", data={
        "description": "Testing transfer",
        "amount": 150,
        "recipient": f"{second_account.title} ({second_account.iban[:4]}...{second_account.iban[-2:]})"
    }, follow_redirects=True)
    assert 'Successfully created transfer' in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

    outgoing_transaction = first_account.transactions.all()[-1]
    incoming_transaction = second_account.transactions.all()[-1]

    assert outgoing_transaction.description == incoming_transaction.description
    assert (outgoing_transaction.category == incoming_transaction.category) and (outgoing_transaction.category == "Transfer")
    assert outgoing_transaction.amount == -(incoming_transaction.amount) and (outgoing_transaction.amount == -150)
    assert outgoing_transaction.saldo == -(incoming_transaction.saldo) and (outgoing_transaction.saldo == -150)


## API tests
# create transaction
def test_api_create_transaction_non_existent_account(client_initialiser):
    client = client_initialiser

    response = client.post('/api/accounts/99/transactions', json={
        "description": "Test",
        "amount": 50.0,
        "category": "Groceries",
    })
    assert response.status_code == 400
    assert response.json["detail"] == "Account with ID 99 not found."

def test_api_create_transaction_invalid_request_body(first_account, client_initialiser, valid_and_invalid_transaction_data):
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

    for category in data["category"]["invalid"]: #tests "Transfer" as invalid category as well
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": "ValidDescription",
            "amount": 50,
            "category": category["value"]
        })

        assert response.status_code == 400
        assert category['error_message'] in response.json["detail"]

    for utc_datetime_booked in data["utc_datetime_booked"]["invalid"]:
        print(utc_datetime_booked["value"])
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
        assert first_account.id == response.json["account_id"]
        assert description == response.json["description"]

    for amount in data["amount"]["valid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": "ValidDescription",
            "amount": amount,
            "category": "Groceries"
        })
        assert response.status_code == 201
        assert "Successfully created new transaction" in response.json["detail"]
        assert first_account.id == response.json["account_id"]
        assert amount == response.json["amount"]

    for category in data["category"]["valid"]:
        response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
            "account_id": first_account.id,
            "description": "ValidDescription",
            "amount": 50,
            "category": category
        })

        assert response.status_code == 201
        assert "Successfully created new transaction" in response.json["detail"]
        assert first_account.id == response.json["account_id"]
        assert category == response.json["category"]

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
        assert response.json["transaction_id"] # ensure transaction_id exists in response

def test_api_create_transaction_valid_response_fields(first_account, client_initialiser):
    client = client_initialiser

    response = client.post(f'/api/accounts/{first_account.id}/transactions', json={
        "account_id": first_account.id,
        "description": "Valid description",
        "amount": 50.0,
        "category": "Groceries"
    })

    # Ensure all fields as documented in swagger exist
    assert response.status_code == 201
    assert "Successfully created new transaction" in response.json["detail"]
    assert response.json["account_id"] == first_account.id
    assert response.json["description"] == "Valid description"
    assert response.json["transaction_id"] # Only ensure that it exists
    assert response.json["category"] == "Groceries"
    assert response.json["amount"] == 50
    assert response.json["utc_datetime_booked"] # Only ensure that it exists
    assert response.json["saldo"] # Only ensure that it exists

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
    naive_datetime = datetime.fromisoformat(utc_datetime_booked_string)
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


# create subaccount_tranfer
def test_api_create_sub_transfer_non_existent_sender(client_initialiser):
    client = client_initialiser

    response = client.post('/api/accounts/99/subaccount_transfer', json={
        "description": "Test",
        "amount": 50.0,
        "category": "Groceries",
    })
    assert response.status_code == 400
    assert response.json["detail"] == "Account with ID 99 not found."

def test_api_create_sub_transfer_required_data_missing(client_initialiser, first_account, second_account):
    client = client_initialiser

    response = client.post(f"api/accounts/{first_account.id}/subaccount_transfer", json={
        "amount": 123,
        "recipient_account_id": second_account.id,
    })
    assert response.status_code == 400
    assert response.json["detail"] == "'description' is a required property"

    response = client.post(f"api/accounts/{first_account.id}/subaccount_transfer", json={
        "description": "Valid description",
        "recipient_account_id": second_account.id,
    })
    assert response.status_code == 400
    assert response.json["detail"] == "'amount' is a required property"

    response = client.post(f"api/accounts/{first_account.id}/subaccount_transfer", json={
        "description": "Valid description",
        "amount": 123,
    })
    assert response.status_code == 400
    assert response.json["detail"] == "'recipient_account_id' is a required property"

def test_api_create_sub_transfer_invalid_request_data(first_account, second_account, client_initialiser, valid_and_invalid_transaction_data):
    data = valid_and_invalid_transaction_data
    client = client_initialiser

    for description in data["description"]["invalid"]:
        response = client.post(f'/api/accounts/{first_account.id}/subaccount_transfer', json={
            "recipient_account_id": second_account.id,
            "description": description["value"],
            "amount": 50.0,
        })
        assert response.status_code == 400
        assert description["error_message"] in response.json["detail"]

    for amount in data["amount"]["invalid"]:
        response = client.post(f'/api/accounts/{first_account.id}/subaccount_transfer', json={
            "recipient_account_id": second_account.id,
            "description": "ValidDescription",
            "amount": amount["value"],
        })
        assert response.status_code == 400
        assert amount["error_message"] in response.json["detail"]

    for utc_datetime_booked in data["utc_datetime_booked"]["invalid"]:
        response = client.post(f'/api/accounts/{first_account.id}/subaccount_transfer', json={
            "recipient_account_id": second_account.id,
            "description": "ValidDescription",
            "amount": 50,
            "utc_datetime_booked": utc_datetime_booked["value"]
        })
        assert response.status_code == 400
        assert utc_datetime_booked["error_message"] in response.json["detail"]

def test_api_create_sub_transfer_invalid_recipient(first_account, client_initialiser):
    client = client_initialiser

    response = client.post(f'/api/accounts/{first_account.id}/subaccount_transfer', json={
        "recipient_account_id": 99,
        "description": "Valid",
        "amount": 50.0,
    })
    assert response.status_code == 400
    assert response.json["detail"] == "Account with ID 99 not found."

def test_api_create_sub_transfer_non_existent_sender(first_account, client_initialiser):
    client = client_initialiser

    response = client.post('/api/accounts/99/subaccount_transfer', json={
        "recipient_account_id": first_account.id,
        "description": "Valid",
        "amount": 50.0,
    })
    assert response.status_code == 400
    assert response.json["detail"] == "Account with ID 99 not found."

def test_api_create_sub_transfer_valid_data(first_account, second_account, client_initialiser, valid_and_invalid_transaction_data):
    data = valid_and_invalid_transaction_data
    client = client_initialiser

    for description in data["description"]["valid"]:
        response = client.post(f'/api/accounts/{first_account.id}/subaccount_transfer', json={
            "recipient_account_id": second_account.id,
            "description": description,
            "amount": 50.0,
        })
        assert response.status_code == 201
        assert response.json["detail"] == "Successfully created subaccount transfer."

    for amount in data["amount"]["valid"]:
        response = client.post(f'/api/accounts/{first_account.id}/subaccount_transfer', json={
            "recipient_account_id": second_account.id,
            "description": "ValidDescription",
            "amount": amount,
        })
        assert response.status_code == 201
        assert response.json["detail"] == "Successfully created subaccount transfer."

    for utc_datetime_booked in data["utc_datetime_booked"]["valid"]:
        response = client.post(f'/api/accounts/{first_account.id}/subaccount_transfer', json={
            "recipient_account_id": second_account.id,
            "description": "ValidDescription",
            "amount": 50,
            "utc_datetime_booked": utc_datetime_booked
        })
        assert response.status_code == 201
        assert response.json["detail"] == "Successfully created subaccount transfer."

def test_api_create_sub_transfer_valid_result_both_ends(first_account, second_account, client_initialiser, valid_and_invalid_transaction_data):
    data = valid_and_invalid_transaction_data
    client = client_initialiser

    # Ensure sender and recipient accounts have no transactions (saldo = 0)
    assert first_account.transactions.count() == 0
    assert second_account.transactions.count() == 0

    response = client.post(f'/api/accounts/{first_account.id}/subaccount_transfer', json={
        "recipient_account_id": second_account.id,
        "description": "First transaction 2309",
        "amount": 150.0,
    })
    assert response.status_code == 201
    assert response.json["detail"] == "Successfully created subaccount transfer."

    # Find transaction belonging to sender / recipient account in response
    dict_sender_transaction = next((t for t in response.json["transactions"] if t["account_id"] == first_account.id), None)
    assert dict_sender_transaction["account_id"] == first_account.id

    dict_recipient_transaction = next((t for t in response.json["transactions"] if t["account_id"] == second_account.id), None)
    assert dict_recipient_transaction["account_id"] == second_account.id

    # Ensure fields (description, category) match for both transactions
    assert ((dict_sender_transaction["description"] == dict_recipient_transaction["description"]) and (dict_sender_transaction["description"] == "First transaction 2309"))
    assert ((dict_sender_transaction["category"] == dict_recipient_transaction["category"]) and (dict_sender_transaction["category"] == "Transfer"))

    # Ensure fields (amount, saldo, transaction_id) do not match or are negative (where applicable) for both transactions
    assert ((dict_sender_transaction["amount"] == - dict_recipient_transaction["amount"]) and (dict_sender_transaction["amount"] == -150))
    assert ((dict_sender_transaction["saldo"] == - dict_recipient_transaction["saldo"]) and (dict_sender_transaction["saldo"] == -150))
    assert dict_sender_transaction["transaction_id"] != dict_recipient_transaction["transaction_id"]

def test_api_create_sub_transfer_valid_response_fields(client_initialiser, first_account, second_account):
    client = client_initialiser

    response = client.post(f"api/accounts/{first_account.id}/subaccount_transfer", json={
        "description": "Savings August",
        "amount": 123,
        "recipient_account_id": second_account.id,
    })
    assert response.status_code == 201
    assert response.json["detail"] == "Successfully created subaccount transfer."
    assert response.json["status"] == "success"
    assert type(response.json["transactions"]) == list
    assert len(response.json["transactions"]) == 2

    # Ensure each of the transactions is associated with first and second account without knowing the order
    assert (response.json["transactions"][0]["account_id"] == first_account.id) or (response.json["transactions"][1]["account_id"] == first_account.id)
    assert (response.json["transactions"][0]["account_id"] == second_account.id) or (response.json["transactions"][1]["account_id"] == second_account.id)

    assert response.json["transactions"][0]["transaction_id"] # only ensure that it exists
    assert response.json["transactions"][0]["utc_datetime_booked"] # only ensure that it exists
    assert response.json["transactions"][0]["saldo"] # only ensure that it exists
    assert response.json["transactions"][0]["description"] == "Savings August"
    assert (response.json["transactions"][0]["amount"] == 123) or (response.json["transactions"][1]["amount"] == 123)
