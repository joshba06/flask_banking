import pytest
from project import create_app
from project.models import Transaction

from project.db import db_session

# Define a fixture to clean up the transactions before every test
# @pytest.fixture(autouse=True)
# def clean_transactions():
#     Transaction.query.delete()
#     print("Deleted transcations")
#     print(Transaction.query.count())

#-> Make “app” available everywhere in the tests
@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    print(Transaction.query.all())
    u = Transaction('admin', 1234)
    db_session.add(u)
    db_session.commit()
    print(Transaction.query.all())

    yield app


# Simulates requests to the app
@pytest.fixture()
def client(app):
    return app.test_client()
