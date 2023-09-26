import pytest

@pytest.fixture()
def first_account(client_initialiser, account_initialiser):
    Account = account_initialiser
    assert Account.query.count() == 0

    # Create first account (database must have at least 1 account)
    client_initialiser.post("/accounts/create", data={"title": "first_account", "accept_terms": True}, follow_redirects=True)
    assert Account.query.count() == 1

    account = Account.query.filter(Account.title=="first_account").first()
    return account

## Route tests
# create route
def test_create_success_redirect(client_initialiser, account_initialiser, first_account):
    Account = account_initialiser
    client = client_initialiser

    response = client.post(f"accounts/create", data={'title': 'TestTitle', "accept_terms": True})

    # Check for successful redirection to "accounts.show"
    assert response.status_code == 302
    account = Account.query.filter(Account.title=="TestTitle").first()
    assert f"accounts/{account.id}" in response.location

def test_create_error_redirect(client_initialiser, account_initialiser, first_account):
    Account = account_initialiser
    client = client_initialiser

    response = client.post(f"accounts/create", data={'title': None, "accept_terms": True})

    # Ensure request is forwarded to index page, since error occurred
    assert response.status_code == 302
    assert response.location == "/accounts"

def test_create_account_error_flash(client_initialiser, account_initialiser, first_account):
    Account = account_initialiser
    client = client_initialiser

    # Invalid description tests (no iban as parameter tests, because those are generated internally)
    scenarios = [
        {
            "title": "Ab",  # too short
            "error_message": "Form data is not valid."
        },
        {
            "title": "Abcde"*5,  # too long
            "error_message": "Form data is not valid."
        },
        {
            "title": "123Hello",  # starts with digit
            "error_message": "title should be of type str and cannot start with digit"
        }
    ]

    for scenario in scenarios:
        response = client.post(f"accounts/create", data={'title':  scenario["title"], "accept_terms": True},  follow_redirects=True)

        assert scenario["error_message"] in response.data.decode() # Ensure correct flash message is displayed

def test_create_account_success_flash(client_initialiser, account_initialiser):
    client = client_initialiser
    Account = account_initialiser

    response = client.post(f"accounts/create", data={'title': "New", "accept_terms": True},  follow_redirects=True)
    assert "Successfully created new account" in response.data.decode()

    new_account = Account.query.filter(Account.title=="New").first()
    assert response.request.path == f"/accounts/{new_account.id}"

def test_create_duplicate_iban(client_initialiser, db_initialiser, first_account):
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    # Create the second account
    client.post("/accounts/create", data={"title": "Duplicate", "accept_terms": True}, follow_redirects=True)

    # Create a third account
    response = client.post("/accounts/create", data={"title": "Duplicate2", "accept_terms": True}, follow_redirects=True)

    # Verify that IBAN has been incremented
    third_account = Account.query.filter(Account.title=="Duplicate2").first()
    assert third_account.iban.endswith("002")

    # Verify 3 accounts exist in total
    assert Account.query.count() == 3

    # Verify redirect to show page of third account
    assert response.request.path == f"/accounts/{third_account.id}"

def test_get_not_allowed_for_create_route(client_initialiser):
    client = client_initialiser

    response = client.get("/accounts/create")

    # Check if the status code is 405 Method Not Allowed
    assert response.status_code == 405

def test_create_accounts_exceeds_limit(client_initialiser, db_initialiser, first_account):
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    # Create 4 accounts
    for i in range(4):
        client.post("/accounts/create", data={"title": "Duplicate", "accept_terms": True}, follow_redirects=True)
        assert Account.query.count() == (i+2)

    # Create 6th account
    response = client.post("/accounts/create", data={"title": "Duplicate", "accept_terms": True}, follow_redirects=True)
    assert "Cannot add more than 5 accounts." in response.data.decode()

    assert Account.query.count() == 5

    # Verify redirect to show page of first account

    assert response.request.path == f"/accounts/{Account.query.all()[0].id}"

def test_create_account_term_not_accepted_flash(client_initialiser, account_initialiser, first_account):
    Account = account_initialiser
    client = client_initialiser

    response = client.post(f"accounts/create", data={'title': "ValidTitle"},  follow_redirects=True)

    # Ensure request is forwarded to index ->showpage of first acount, since error occurred
    assert response.status_code == 200
    assert "Form data is not valid" in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

# update route
def test_update_invalid_title_length(client_initialiser, account_initialiser, first_account):
    client = client_initialiser

    response = client.post(f"/accounts/{first_account.id}/update", data={"title": "Sh"}, follow_redirects=True)
    assert "Form data is not valid" in response.data.decode()
    assert response.request.path == "/accounts/1"

    response = client.post(f"/accounts/{first_account.id}/update", data={"title": "Sh"*15}, follow_redirects=True)
    assert "Form data is not valid" in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

def test_update_invalid_title_type(client_initialiser, account_initialiser, first_account):
    client = client_initialiser

    response = client.post(f"/accounts/{first_account.id}/update", data={"title": 123}, follow_redirects=True)

    # 123 becomes a string so first char check should prove invalid input
    assert "Account title cannot start with a digit." in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

def test_update_nonexistent_account(client_initialiser, first_account):
    client = client_initialiser

    response = client.post("/accounts/999/update", data={"title": "ValidTitle"}, follow_redirects=True)
    assert "Account not found." in response.data.decode()
    assert response.request.path == f"/accounts/{first_account.id}"

def test_get_not_allowed_for_update_route(client_initialiser, first_account):
    client = client_initialiser

    response = client.get(f"/accounts/{first_account.id}/update")

    # Check if the status code is 405 Method Not Allowed
    assert response.status_code == 405

# delete route
@pytest.fixture
def two_accounts(client_initialiser, account_initialiser):
    Account = account_initialiser
    assert Account.query.count() == 0

    # Create 2 accounts
    client_initialiser.post("/accounts/create", data={"title": "first_account", "accept_terms": True})
    client_initialiser.post("/accounts/create", data={"title": "second_account", "accept_terms": True})
    assert Account.query.count() == 2

    account1 = Account.query.filter(Account.title=="first_account").first()
    account2 = Account.query.filter(Account.title=="second_account").first()
    return account1, account2

def test_delete_account_nonexistent_account(client_initialiser, two_accounts):
    response = client_initialiser.post("/accounts/999/delete", follow_redirects=True)
    assert "Could not find account." in response.data.decode()
    assert response.request.path == f"/accounts/{two_accounts[0].id}"

def test_delete_account_last_account(client_initialiser, two_accounts, account_initialiser):

    client_initialiser.post(f"/accounts/{two_accounts[0].id}/delete")
    assert account_initialiser.query.count() == 1

    response = client_initialiser.post(f"/accounts/{two_accounts[1].id}/delete", follow_redirects=True)

    assert "Cannot delete the last account." in response.data.decode()
    assert response.request.path == f"/accounts/{two_accounts[1].id}"

def test_successful_delete(client_initialiser, two_accounts, account_initialiser):

    response = client_initialiser.post(f"/accounts/{two_accounts[0].id}/delete", follow_redirects=True)
    assert account_initialiser.query.count() == 1

    assert "Successfully deleted account." in response.data.decode()
    assert response.request.path == f"/accounts/{two_accounts[1].id}"

def test_delete_account_associated_transactions(db_initialiser, client_initialiser, two_accounts):
    Account, Transaction, db_session = db_initialiser
    from project.transactions.transactions import create_transaction

    # Ensure account has no transactions before test and no transactions exist before test
    first_account = two_accounts[0]
    second_account = two_accounts[1]
    assert first_account.transactions.count() == 0
    assert Transaction.query.count() == 0

    # Add transactions to account and ensure transaction counts reflect the change
    status, message, transaction_1_id = create_transaction(first_account, "Description", 100, "Rent")
    status, message, transaction_2_id = create_transaction(first_account, "Description", 100, "Rent")
    assert Transaction.query.count() == 2 and first_account.transactions.count() == 2

    # Delete account and ensure transactions are deleted
    response = client_initialiser.post(f"/accounts/{first_account.id}/delete", follow_redirects=True)
    assert Account.query.count() == 1

    assert Transaction.query.count() == 0


## API tests

# create
def test_api_create_account_missing_title(client_initialiser):
    client = client_initialiser
    response = client.post("/api/accounts", json={})
    assert response.status_code == 400

    # Ensure error message is default swagger error message for missing property
    assert response.json["title"] == "Bad Request"
    assert response.json["detail"] == "'title' is a required property"

def test_api_create_account_invalid_title_type(client_initialiser):
    client = client_initialiser

    response = client.post("/api/accounts", json={"title": 12345})
    assert response.status_code == 400

    assert "is not of type 'string' - 'title" in response.json["detail"]

    response = client.post("/api/accounts", json={"title": "12345"})

    assert response.status_code == 400
    assert "title should be of type str and cannot start with digit" in response.json["detail"]

def test_api_create_account_short_title(client_initialiser):
    client = client_initialiser
    response = client.post("/api/accounts", json={"title": "ab"})

    assert response.status_code == 400
    assert "is too short - 'title'" in response.json["detail"]

def test_api_create_account_long_title(client_initialiser):
    client = client_initialiser
    response = client.post("/api/accounts", json={"title": "ab"*15})

    assert response.status_code == 400
    assert "is too long - 'title'" in response.json["detail"]

def test_api_create_account_invalid_property(client_initialiser):
    client = client_initialiser

    response = client.post("/api/accounts", json={"title": "Test", "iban": "12345678901234567890"})
    assert response.status_code == 400
    assert "Additional properties are not allowed ('iban' was unexpected)" in response.json["detail"]

    response = client.post("/api/accounts", json={"title": "Test", "something": 123})
    assert response.status_code == 400
    assert "Additional properties are not allowed ('something' was unexpected)" in response.json["detail"]

def test_api_create_accounts_success(client_initialiser, account_initialiser):
    client = client_initialiser
    Account = account_initialiser

    for i in range(5):
        response = client.post("/api/accounts", json={"title": f"Test_{i}"})

        # Ensure 5 accounts can be created successfully
        assert response.status_code == 201
        assert response.json['status'] == "success"
        assert response.json['detail'] == "Successfully created new account."
        assert response.json['title'] == f"Test_{i}"
        assert response.json['iban'] == f"GB2900006016133192000{i}"
        assert response.json['id'] == i+1

    assert Account.query.count() == 5

def test_api_create_accounts_exceed_limit(client_initialiser, account_initialiser):
    client = client_initialiser
    Account = account_initialiser

    for i in range(5):
        response = client.post("/api/accounts", json={"title": f"Test_{i}"})

        # Ensure 5 accounts can be created successfully
        assert response.status_code == 201
        assert response.json['status'] == "success"

    # Attempt creating 6th account
    response = client.post("/api/accounts", json={"title": f"Sixth acc"})
    assert response.status_code == 400

    # Ensure custom message, raised by Acount limit_accounts function, is returned
    assert response.json['status'] == "error"
    assert response.json['detail'] == "Cannot add more than 5 accounts."

# delete
def test_api_delete_account_success(client_initialiser, two_accounts):
    client = client_initialiser

    response = client.delete("/api/accounts/1")
    assert response.status_code == 200
    assert response.json['status'] == "success"
    assert response.json['detail'] == "Successfully deleted account."

    # Further test to ensure it's actually deleted
    response = client.delete("/api/accounts/1")
    assert response.status_code == 404

def test_api_delete_account_no_id(client_initialiser):
    client = client_initialiser

    response = client.delete("/api/accounts/")
    assert response.status_code == 404

def test_api_delete_account_invalid_id_type(client_initialiser):
    client = client_initialiser

    response = client.delete("/api/accounts/x")
    assert response.status_code == 404

def test_api_delete_nonexistent_account(client_initialiser):

    response = client_initialiser.delete("/api/accounts/999")

    assert response.status_code == 404
    assert response.json['status'] == "error"
    assert response.json['detail'] == "Account not found."

def test_api_delete_last_account(client_initialiser, two_accounts, account_initialiser):

    # Delete first account
    response = client_initialiser.delete(f"/api/accounts/{two_accounts[0].id}")
    assert response.status_code == 200

    assert account_initialiser.query.limit(2).count() == 1

    # Attempt deleting last account
    response = client_initialiser.delete(f"/api/accounts/{two_accounts[1].id}")
    assert response.status_code == 400
    assert response.json['status'] == "error"
    assert response.json['detail'] == "Cannot delete the last account."

    assert account_initialiser.query.limit(2).count() == 1

def test_api_delete_account_associated_transactions(db_initialiser, client_initialiser, two_accounts):
    Account, Transaction, db_session = db_initialiser
    from project.transactions.transactions import create_transaction

    # Ensure account has no transactions before test and no transactions exist before test
    first_account = two_accounts[0]
    second_account = two_accounts[1]
    assert first_account.transactions.count() == 0
    assert Transaction.query.count() == 0

    # Add transactions to account and ensure transaction counts reflect the change
    status, message, transaction_1_id = create_transaction(first_account, "Description", 100, "Rent")
    status, message, transaction_2_id = create_transaction(first_account, "Description", 100, "Rent")
    assert Transaction.query.count() == 2 and first_account.transactions.count() == 2

    # Delete account and ensure transactions are deleted
    response = client_initialiser.delete(f"/api/accounts/{first_account.id}")
    assert Account.query.count() == 1

    assert Transaction.query.count() == 0

# get
def test_api_get_account_invalid_id(client_initialiser):
    client = client_initialiser

    response = client.get("/api/accounts/x")
    assert response.status_code == 404

    response = client.get("/api/accounts/99")
    assert response.status_code == 404
    assert response.json['status'] == "error"
    assert response.json['detail'] == "Account not found."

def test_api_get_account_success(client_initialiser, two_accounts):
    client = client_initialiser

    response = client.get(f"/api/accounts/{two_accounts[0].id}")
    assert response.status_code == 200
    assert response.json[0]['title'] == two_accounts[0].title
    assert response.json[0]['id'] == str(two_accounts[0].id)
    assert response.json[0]['iban'] == two_accounts[0].iban

    response = client.get(f"/api/accounts/{two_accounts[1].id}")
    assert response.status_code == 200
    assert response.json[0]['title'] == two_accounts[1].title
    assert response.json[0]['id'] == str(two_accounts[1].id)
    assert response.json[0]['iban'] == two_accounts[1].iban

# get all
def test_api_get_all_accounts_success(client_initialiser, two_accounts, account_initialiser):
    client = client_initialiser
    Account = account_initialiser

    assert Account.query.count() == 2

    response = client.get("api/accounts")

    assert len(response.json) == 2
    assert response.json[0]["id"] == "1"
    assert response.json[1]["id"] == "2"

def test_api_get_all_accounts_no_accounts(client_initialiser, account_initialiser):
    client = client_initialiser
    Account = account_initialiser

    assert Account.query.count() == 0

    response = client.get("api/accounts")

    assert response.status_code == 404
    assert response.json['detail'] == "No accounts found."
    assert response.json['status'] == "error"
