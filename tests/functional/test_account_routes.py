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


## API tests
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






# # def test_update_existing_account(client_initialiser, db_initialiser, first_account):
# #     client = client_initialiser
# #     Account, Transaction, db_session = db_initialiser

# #     # Get first_account id
# #     first_account = Account.query.filter(Account.title=="first_account").all()[0]

# #     response = client.post(f"/accounts/{first_account.id}/update", data={"title": "Updated Title"}, follow_redirects=True)

# #     assert 'Successfully updated account info.' in response.data.decode()
# #     assert Account.query.get(first_account.id).title == "Updated Title"
# #     assert response.request.path == f"/accounts/{first_account.id}"

# # def test_update_non_existent_account(client_initialiser):
# #     client = client_initialiser

# #     response = client.post("/accounts/999/update", data={"title": "New Title"}, follow_redirects=True)

# #     assert 'Account not found.' in response.data.decode()

# #     # Check that there were two redirect responses. 1-index, 2-showpage for first found account
# #     assert len(response.history) == 2

# #     # Check that the first request was to the index page.
# #     assert response.history[1].request.path == "/accounts"

# # def test_update_account_db_failure(client_initialiser, db_initialiser, first_account):
# #     client = client_initialiser
# #     Account, Transaction, db_session = db_initialiser

# #     # Get first_account id
# #     first_account = Account.query.filter(Account.title=="first_account").all()[0]

# #     response1 = client.post(f"/accounts/{first_account.id}/update", data={"title": "Another Title too long"}, follow_redirects=True)

# #     # assert 'Account title must be a string and max length of 15 characters.' in response1.data.decode()

# #     # Check that the first request was to the show page of current account.
# #     assert response1.request.path == f"/accounts/{first_account.id}"

# #     response2 = client.post(f"/accounts/{first_account.id}/update", data={"title": 12345}, follow_redirects=True)

# #     # assert 'Account title must be a string and max length of 15 characters.' in response2.data.decode()
# #     # Check that the first request was to the show page of current account.
# #     assert response2.request.path == f"/accounts/{first_account.id}"

# # def test_delete_existing_account(client_initialiser, db_initialiser, first_account):
# #     """Test deleting an existing account."""
# #     client = client_initialiser
# #     Account, Transaction, db_session = db_initialiser

# #     # Get first_account id
# #     first_account = Account.query.filter(Account.title=="first_account").first()

# #     # Create a new account
# #     num_accounts = Account.query.count()
# #     client.post(f"/accounts/create", data={"title": "Main account"}, follow_redirects=True)
# #     new_account = Account.query.filter(Account.title=="Main account").one()

# #     # Check it was added to db
# #     assert (num_accounts + 1) == Account.query.count()

# #     # Remove account that was last added
# #     response = client.post(f"/accounts/{new_account.id}/delete", follow_redirects=True)

# #     # Ensure success message is displayed to user
# #     assert 'Successfully deleted account.' in response.data.decode()

# #     # Ensure that user is forwarded to show page of first account
# #     assert response.request.path == f"/accounts/{first_account.id}"

# # def test_delete_non_existent_account(client_initialiser, db_initialiser, first_account):
# #     """Test trying to delete an account that doesn't exist."""
# #     client = client_initialiser
# #     Account, Transaction, db_session = db_initialiser

# #     non_existent_id = 99999
# #     response = client.post(f"/accounts/{non_existent_id}/delete", follow_redirects=True)

# #     assert 'Could not find account.' in response.data.decode()

# # def test_delete_last_account(client_initialiser, db_initialiser, first_account):
# #     """Test trying to delete when only one account exists."""
# #     client = client_initialiser
# #     Account, Transaction, db_session = db_initialiser

# #     # Get first_account id
# #     first_account = Account.query.filter(Account.title=="first_account").first()

# #     assert Account.query.count() == 1

# #     response = client.post(f"/accounts/{first_account.id}/delete", follow_redirects=True)
# #     assert 'Cannot delete the last account.' in response.data.decode()

# # def test_delete_account_with_transactions(client_initialiser, db_initialiser, first_account):
# #     client = client_initialiser
# #     Account, Transaction, db_session = db_initialiser

# #     new_account = Account(title="NewAccount", iban="DE123123")
# #     for i in range(4):
# #         new_account.transactions.append(Transaction(description=f"some{i}", category="Rent", amount=100))
# #     db_session.add(new_account)
# #     db_session.commit()

# #     # Ensure 2 accounts and 4 transactions were added to db
# #     assert Transaction.query.count() == 4
# #     assert Account.query.count() == 2

# #     # Delete new_account and ensure 1 account and 0 transactions are left
# #     client.post(f"/accounts/{new_account.id}/delete", follow_redirects=True)

# #     assert Account.query.count() == 1
# #     assert Transaction.query.count() == 0
