import pytest
from project import create_app

@pytest.fixture()
def app_initialiser():
    app = create_app(test_setup=True)

    from project.models import Account, Transaction
    from project.db import db_session
    num_before_setup = Transaction.query.count()
    Transaction.query.delete()
    db_session.commit()
    num_after_setup = Transaction.query.count()
    print(f"Transactions in db before setup: {num_before_setup}, after setup: {num_after_setup}")

    yield app, Account, Transaction, db_session


@pytest.fixture()
def client_initialiser(app_initialiser):
    print("Running client initialiser")
    app, _, _, _ = app_initialiser
    return app.test_client()

@pytest.fixture()
def model_initialiser(app_initialiser):
    print("Running model initialiser")
    _, Account, Transaction, _ = app_initialiser
    return Account, Transaction

@pytest.fixture()
def db_initialiser(app_initialiser):
    print("Running db initialiser")
    _, Account, Transaction, db_session = app_initialiser
    Account.query.delete()
    Transaction.query.delete()
    db_session.commit()
    return Account, Transaction, db_session
