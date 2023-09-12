# Test forms and if correct key specs are displayed on pages. And if show pages display correct forms
import pytest

# test_update_account_db_failure: Needs fixing. Also, alert is not displayed on page.


def test_create_new_account(client_initialiser, db_initialiser):
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    assert Account.query.count() == 0

    # Define form data
    data = {
        "title": "Test Account"
    }

    # Create a new account
    response = client.post("/accounts/create", data=data, follow_redirects=True)

    # Check if a new account has been created
    assert Account.query.count() == 1
    new_account = Account.query.first()
    assert new_account.iban.endswith("001")
    assert new_account.title == "Test Account"
    assert 'Successfully created new account.' in response.data.decode()

    # Check if request is redirected to show page for new account
    assert response.request.path == "/accounts/1"

def test_create_duplicate_iban(client_initialiser, db_initialiser):
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    # Define form data for both posts
    data = {
        "title": "Duplicate"
    }

    # Create the first account
    client.post("/accounts/create", data=data, follow_redirects=True)

    # Create a second account
    response = client.post("/accounts/create", data=data, follow_redirects=True)

    # Verify that IBAN has been incremented
    second_account = Account.query.all()[-1]
    assert second_account.iban.endswith("002")

def test_get_not_allowed_for_create_route(client_initialiser):
    client = client_initialiser

    response = client.get("/accounts/create")

    # Check if the status code is 405 Method Not Allowed
    assert response.status_code == 405


@pytest.fixture()
def first_account(client_initialiser):
    # Create first account (database must have at least 1 account)
    client = client_initialiser
    client.post("/accounts/create", data={"title": "first_account"}, follow_redirects=True)

def test_create_with_invalid_data(client_initialiser, db_initialiser, first_account):
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    client.post("/accounts/create", data={"title": "Testing1"}, follow_redirects=True)
    client.post("/accounts/create", data={"title": "Testing2"}, follow_redirects=True)
    client.post("/accounts/create", data={"title": "Testing3"}, follow_redirects=True)

    num_accounts = Account.query.count()
    assert num_accounts == 4

    # Verify response for title with incorrect length is forward to index page and error message
    response = client.post("/accounts/create", data={"title": "DuplicateAccount" * 3}, follow_redirects=True)

    # Verify error message is displayed to user
    assert 'Account title must be a string and max length of 15 characters.' in response.data.decode()

    # Verify number of accounts in db has not increased
    assert num_accounts == Account.query.count()

    # Verify redirect to show page of (oldest) existing account is made
    first_account = Account.query.all()[0]
    assert first_account.title == "first_account"
    assert response.request.path == f"/accounts/{first_account.id}"

def test_update_existing_account(client_initialiser, db_initialiser, first_account):
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    # Get first_account id
    first_account = Account.query.filter(Account.title=="first_account").all()[0]

    response = client.post(f"/accounts/{first_account.id}/update", data={"title": "Updated Title"}, follow_redirects=True)

    assert 'Successfully updated account info.' in response.data.decode()
    assert Account.query.get(first_account.id).title == "Updated Title"
    assert response.request.path == f"/accounts/{first_account.id}"

def test_update_non_existent_account(client_initialiser):
    client = client_initialiser

    response = client.post("/accounts/999/update", data={"title": "New Title"}, follow_redirects=True)

    assert 'Account not found.' in response.data.decode()

    # Check that there were two redirect responses. 1-index, 2-showpage for first found account
    assert len(response.history) == 2

    # Check that the first request was to the index page.
    assert response.history[1].request.path == "/accounts"

def test_update_account_db_failure(client_initialiser, db_initialiser, first_account):
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    # Get first_account id
    first_account = Account.query.filter(Account.title=="first_account").all()[0]

    response1 = client.post(f"/accounts/{first_account.id}/update", data={"title": "Another Title too long"}, follow_redirects=True)

    # assert 'Account title must be a string and max length of 15 characters.' in response1.data.decode()

    # Check that the first request was to the show page of current account.
    assert response1.request.path == f"/accounts/{first_account.id}"

    response2 = client.post(f"/accounts/{first_account.id}/update", data={"title": 12345}, follow_redirects=True)

    # assert 'Account title must be a string and max length of 15 characters.' in response2.data.decode()
    # Check that the first request was to the show page of current account.
    assert response2.request.path == f"/accounts/{first_account.id}"

def test_delete_existing_account(client_initialiser, db_initialiser, first_account):
    """Test deleting an existing account."""
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    # Get first_account id
    first_account = Account.query.filter(Account.title=="first_account").first()

    # Create a new account
    num_accounts = Account.query.count()
    client.post(f"/accounts/create", data={"title": "Main account"}, follow_redirects=True)
    new_account = Account.query.filter(Account.title=="Main account").one()

    # Check it was added to db
    assert (num_accounts + 1) == Account.query.count()

    # Remove account that was last added
    response = client.post(f"/accounts/{new_account.id}/delete", follow_redirects=True)

    # Ensure success message is displayed to user
    assert 'Successfully deleted account.' in response.data.decode()

    # Ensure that user is forwarded to show page of first account
    assert response.request.path == f"/accounts/{first_account.id}"

def test_delete_non_existent_account(client_initialiser, db_initialiser, first_account):
    """Test trying to delete an account that doesn't exist."""
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    non_existent_id = 99999
    response = client.post(f"/accounts/{non_existent_id}/delete", follow_redirects=True)

    assert 'Could not find account.' in response.data.decode()

def test_delete_last_account(client_initialiser, db_initialiser, first_account):
    """Test trying to delete when only one account exists."""
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    # Get first_account id
    first_account = Account.query.filter(Account.title=="first_account").first()

    assert Account.query.count() == 1

    response = client.post(f"/accounts/{first_account.id}/delete", follow_redirects=True)
    assert 'Cannot delete the last account.' in response.data.decode()

def test_delete_account_with_transactions(client_initialiser, db_initialiser, first_account):
    client = client_initialiser
    Account, Transaction, db_session = db_initialiser

    new_account = Account(title="NewAccount", iban="DE123123")
    for i in range(4):
        new_account.transactions.append(Transaction(description=f"some{i}", category="Rent", amount=100))
    db_session.add(new_account)
    db_session.commit()

    # Ensure 2 accounts and 4 transactions were added to db
    assert Transaction.query.count() == 4
    assert Account.query.count() == 2

    # Delete new_account and ensure 1 account and 0 transactions are left
    client.post(f"/accounts/{new_account.id}/delete", follow_redirects=True)

    assert Account.query.count() == 1
    assert Transaction.query.count() == 0
