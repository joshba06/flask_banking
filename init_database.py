from sqlalchemy.exc import OperationalError

from config import app, db
from models import Transaction

from datetime import datetime, timedelta
import random

from faker import Faker
faker = Faker()

from pprint import pprint

def get_data_from_table(model):
    try:
        data = db.session.query(model).all()
        db.session.close()
        return data
    except OperationalError:
        return []


def create_database(db):

    db.create_all()

    # Generate array of random dates that will be later assigned to transactions date today-7days .. today+7days
    dates = []
    today = datetime.now()
    seven_days_ago = today - timedelta(days=65)

    for j in range(25):
        random_seconds = random.randint(0, (today - seven_days_ago).total_seconds())
        random_datetime = seven_days_ago + timedelta(seconds=random_seconds)
        dates.append(random_datetime)
    sorted_dates = sorted(dates)

    # Create transactions by ascending date
    saldo = 0
    for i in range(25):
        name = faker.name()
        amount = round(random.uniform(-1000, 1000), 2)
        saldo += amount
        saldo = round(saldo,2)
        # print("[{}] - amount: {}, saldo: {}".format(sorted_dates[i], amount, saldo))
        new_transaction = Transaction(title=name, amount=amount, saldo=saldo, date_booked=sorted_dates[i])
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
