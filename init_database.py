from sqlalchemy.exc import OperationalError

from config import app, db
from models import Transaction

import random

from faker import Faker
faker = Faker()

def get_data_from_table(model):
    try:
        data = db.session.query(model).all()
        db.session.close()
        return data
    except OperationalError:
        return []

def create_database(db):
    db.create_all()
    saldo = 0
    for i in range(15):
        name = faker.name()
        amount = round(random.uniform(-1000, 1000), 2)
        saldo += amount
        saldo = round(saldo,2)
        new_transaction = Transaction(title=name, amount=amount, saldo=saldo)
        db.session.add(new_transaction)

    db.session.commit()
    print("Created new database")

def update_database(db, existing_transactions):
    db.drop_all()
    db.create_all()
    for transaction in existing_transactions:
        db.session.merge(transaction)

    db.session.commit()
    print("Updated existing database")


with app.app_context():
    existing_transactions = get_data_from_table(Transaction)

    if not existing_transactions:
        create_database(db)
    else:
        update_database(db, existing_transactions)
