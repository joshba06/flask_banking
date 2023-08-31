from sqlalchemy.exc import OperationalError
from project.models import Transaction

from datetime import datetime, timedelta
import random

from faker import Faker
faker = Faker()


from pprint import pprint


def get_data_from_table(db_session):
    try:
        data = db_session.query(Transaction).all()
        db_session.close()
        return data
    except OperationalError:
        return []


def create_database(db_session):

    # db_session.create_all()

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
        db_session.add(new_transaction)

    db_session.commit()
    print("Created new database")

def update_database(db_session, existing_transactions):
    # db_session.drop_all()
    # db_session.create_all()
    for transaction in existing_transactions:
        db_session.merge(transaction)

    db_session.commit()
    print("Updated existing database")


def main(db_session):
    existing_transactions = get_data_from_table(db_session)

    if not existing_transactions:
        create_database(db_session)
    else:
        update_database(db_session, existing_transactions)
