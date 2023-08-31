import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

#-> Make “app” available everywhere in the tests
@pytest.fixture()
def app():
        app = Flask(__name__)
        # Create in-memory database
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        app.config["SECRET_KEY"] = "my_secret"
        app.config['TESTING'] = True

        # db = SQLAlchemy(app)
        db = SQLAlchemy()
        db.init_app(app)

        with app.app_context():
                db.create_all()

        yield app

# Simulates requests to the app
@pytest.fixture()
def client(app):
        return app.test_client()
