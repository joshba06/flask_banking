import pytest
from project import create_app
from project.models import Transaction

from project.db import db_session


#-> Make “app” available everywhere in the tests
@pytest.fixture()
def app():
    app = create_app(test_setup=True)

    print("Test environment before setup: {}".format(Transaction.query.all()))

    Transaction.query.delete()
    db_session.commit()
    print("Test environment after setup: {}".format(Transaction.query.all()))

    yield app


# Simulates requests to the app
@pytest.fixture()
def client(app):
    return app.test_client()
