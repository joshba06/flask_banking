import pytest
from project import create_app
from project.db import db_session
from project.models import Transaction

# Define a fixture to clean up the transactions before every test
@pytest.fixture(autouse=True)
def clean_transactions():
    Transaction.query.delete()

#-> Make “app” available everywhere in the tests
@pytest.fixture()
def app(clean_transactions):
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    yield app



# Simulates requests to the app
@pytest.fixture()
def client(app):
    return app.test_client()
