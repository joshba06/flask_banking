# SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

# Import for seeding sessions
import random
from datetime import datetime, timezone, timedelta
import pytz
from pprint import pprint

from project import app



engine = create_engine(app.app.config["DATABASE_URL"])

db_session = scoped_session(sessionmaker(autocommit=False,
                                        autoflush=False,
                                        bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    from project.models import Account, Transaction
    Base.metadata.create_all(bind=engine)

    print(f"Continuing db setup with db session at: {db_session.get_bind()}")
    print(f"Table names: {Base.metadata.tables.keys()}")

    if app.app.config["TESTING"] is False:
        print("__________[DB] NORMAL SETUP__________")
        print(f"Existing accounts: {Account.query.count()}, existing transactions: {Transaction.query.count()}")

        if Account.query.count() < 3 or Transaction.query.count() == 0:
            Transaction.query.delete()
            Account.query.delete()
            print("Seeding database")
            create_database(Account, Transaction)
            print("Seeding complete")
    else:
        print("__________[DB] TEST SETUP__________")


def create_database(Account, Transaction):

    account1 = Account(title="Main account", iban="GB29000060161331920000")
    account2 = Account(title="Savings", iban="GB29000060161331920001")
    account3 = Account(title="Shared", iban="GB29000060161331920002")

    transactions = [
        # Year 2023 August
        Transaction(description="Paypal-Henry-Thanks!", amount=-95.00, category="Night out", utc_datetime_booked=random_utc_datetime(2023, 8, 15)),
        Transaction(description="Rent August", amount=-600.00, category="Rent", utc_datetime_booked=random_utc_datetime(2023, 8, 20)),
        Transaction(description="Apple salary", amount=1200.00, category="Salary", utc_datetime_booked=random_utc_datetime(2023, 8, 5)),
        Transaction(description="Grocery Store Purchase - Kroger", amount=-250.00, category="Groceries", utc_datetime_booked=random_utc_datetime(2023, 8, 10)),
        Transaction(description="Electric bill", amount=-80.00, category="Utilities", utc_datetime_booked=random_utc_datetime(2023, 8, 15)),

        # Year 2023 July
        Transaction(description="Wire Transfer - Invoice #12345", amount=-200.00, category="Groceries", utc_datetime_booked=random_utc_datetime(2023, 7, 2)),
        Transaction(description="Withdrawal - ATM Transaction", amount=-600.00, category="Rent", utc_datetime_booked=random_utc_datetime(2023, 7, 5)),
        Transaction(description="Apple salary", amount=1200.00, category="Salary", utc_datetime_booked=random_utc_datetime(2023, 7, 12)),
        Transaction(description="Grocery Store Purchase - Kroger", amount=-70.00, category="Groceries", utc_datetime_booked=random_utc_datetime(2023, 7, 18)),
        Transaction(description="Student Loan Payment - Sallie Mae", amount=150.00, category="Online services", utc_datetime_booked=random_utc_datetime(2023, 7, 25)),

        # Year 2023 June
        Transaction(description="Spotify lifetime membership", amount=-99.00, category="Online services", utc_datetime_booked=random_utc_datetime(2023, 6, 7)),
        Transaction(description="Rent June", amount=-600.00, category="Rent", utc_datetime_booked=random_utc_datetime(2023, 6, 11)),
        Transaction(description="Apple salary", amount=1200.00, category="Salary", utc_datetime_booked=random_utc_datetime(2023, 6, 15)),
        Transaction(description="Online Purchase - Amazon", amount=-55.00, category="Night out", utc_datetime_booked=random_utc_datetime(2023, 6, 20)),
        Transaction(description="Utility Bill Payment - Electric", amount=130.00, category="Utilities", utc_datetime_booked=random_utc_datetime(2023, 6, 30)),

        # Year 2023 April
        Transaction(description="Dividends", amount=70.00, category="Salary", utc_datetime_booked=random_utc_datetime(2023, 4, 4)),
        Transaction(description="Rent April", amount=-600.00, category="Rent", utc_datetime_booked=random_utc_datetime(2023, 4, 9)),
        Transaction(description="Apple salary", amount=1200.00, category="Salary", utc_datetime_booked=random_utc_datetime(2023, 4, 16)),
        Transaction(description="Utility Bill Payment - Electric", amount=-45.00, category="Utilities", utc_datetime_booked=random_utc_datetime(2023, 4, 22)),
        Transaction(description="EDEKA sagt danke", amount=-390.00, category="Groceries", utc_datetime_booked=random_utc_datetime(2023, 4, 28)),
    ]
    for transaction in transactions:
        account1.transactions.append(transaction)
    db_session.add_all([account1, account2, account3])
    db_session.commit()

    transactions = db_session.query(Transaction).all()
    for transaction in transactions:
        transaction.calculate_saldo()

    db_session.commit()

def random_utc_datetime(year, month, day):
    # Assign random time
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    # Create the datetime object
    dt = datetime(year, month, day, hour, minute, second)

    # Convert to UTC timezone-aware
    return dt.replace(tzinfo=pytz.UTC)
