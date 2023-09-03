# SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

# Import for seeding sessions
from datetime import datetime
from pprint import pprint

engine = create_engine('sqlite://')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db(test_setup=False):
    from project.models import Transaction
    Base.metadata.create_all(bind=engine)

    if test_setup is False:
        print("Initialising database for normal setup")
        # if len(Transaction.query.all()) == 0:
        print("Seeding database")
        create_database(Transaction)
    else:
        print("Initialising database for test setup")



def create_database(Transaction):

    transactions = [
        # Year 2022
        Transaction(title="Income 1", amount=100.00, date_booked=datetime(2022, 1, 15)),
        Transaction(title="Expense 1", amount=-50.00, date_booked=datetime(2022, 2, 20)),
        Transaction(title="Income 2", amount=75.00, date_booked=datetime(2022, 3, 5)),
        Transaction(title="Income 3", amount=120.00, date_booked=datetime(2022, 4, 10)),
        Transaction(title="Expense 2", amount=-80.00, date_booked=datetime(2022, 5, 15)),

        # Year 2023
        Transaction(title="Income 4", amount=200.00, date_booked=datetime(2023, 1, 2)),
        Transaction(title="Expense 3", amount=-60.00, date_booked=datetime(2023, 2, 5)),
        Transaction(title="Income 5", amount=90.00, date_booked=datetime(2023, 3, 12)),
        Transaction(title="Expense 4", amount=-70.00, date_booked=datetime(2023, 4, 18)),
        Transaction(title="Income 6", amount=150.00, date_booked=datetime(2023, 5, 25)),

        # Year 2024
        Transaction(title="Expense 5", amount=-40.00, date_booked=datetime(2024, 1, 7)),
        Transaction(title="Income 7", amount=80.00, date_booked=datetime(2024, 2, 11)),
        Transaction(title="Income 8", amount=110.00, date_booked=datetime(2024, 3, 15)),
        Transaction(title="Expense 6", amount=-55.00, date_booked=datetime(2024, 4, 20)),
        Transaction(title="Income 9", amount=130.00, date_booked=datetime(2024, 5, 30)),

        # Year 2025
        Transaction(title="Income 10", amount=70.00, date_booked=datetime(2025, 1, 4)),
        Transaction(title="Expense 7", amount=-30.00, date_booked=datetime(2025, 2, 9)),
        Transaction(title="Income 11", amount=140.00, date_booked=datetime(2025, 3, 16)),
        Transaction(title="Expense 8", amount=-45.00, date_booked=datetime(2025, 4, 22)),
        Transaction(title="Income 12", amount=95.00, date_booked=datetime(2025, 5, 28)),
    ]
    for transaction in transactions:
        db_session.add(transaction)
    db_session.commit()

    db_session.expire_all()

    transactions = db_session.query(Transaction).all()
    for transaction in transactions:
        transaction.calculate_saldo()

    pprint(Transaction.query.all())
    print("Completed seeding database")

