# SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

# Import for seeding sessions
from datetime import datetime
from pprint import pprint

# Normal: sqlite:///project.db
engine = create_engine('sqlite:///project.db')

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
        if len(Transaction.query.all()) == 0:
            print("Seeding database")
            create_database(Transaction)
    else:
        print("Initialising database for test setup")



def create_database(Transaction):

    transactions = [

        # Year 2023 August
        Transaction(description="Paypal-Henry-Thanks!", amount=-95.00, category="Night out", date_booked=datetime(2023, 8, 15)),
        Transaction(description="Rent August", amount=-600.00, category="Rent", date_booked=datetime(2023, 8, 20)),
        Transaction(description="Apple salary", amount=1200.00, category="Salary", date_booked=datetime(2023, 8, 5)),
        Transaction(description="Grocery Store Purchase - Kroger", amount=-250.00, category="Groceries", date_booked=datetime(2023, 8, 10)),
        Transaction(description="Electric bill", amount=-80.00, category="Utilities", date_booked=datetime(2023, 8, 15)),

        # Year 2023 July
        Transaction(description="Wire Transfer - Invoice #12345", amount=-200.00, category="Groceries", date_booked=datetime(2023, 7, 2)),
        Transaction(description="Withdrawal - ATM Transaction", amount=-600.00, category="Rent", date_booked=datetime(2023, 7, 5)),
        Transaction(description="Apple salary", amount=1200.00, category="Salary", date_booked=datetime(2023, 7, 12)),
        Transaction(description="Grocery Store Purchase - Kroger", amount=-70.00, category="Groceries", date_booked=datetime(2023, 7, 18)),
        Transaction(description="Student Loan Payment - Sallie Mae", amount=150.00, category="Online services", date_booked=datetime(2023, 7, 25)),

        # Year 2023 June
        Transaction(description="Spotify lifetime membership", amount=-99.00, category="Online services", date_booked=datetime(2023, 6, 7)),
        Transaction(description="Rent June", amount=-600.00, category="Rent", date_booked=datetime(2023, 6, 11)),
        Transaction(description="Apple salary", amount=1200.00, category="Salary", date_booked=datetime(2023, 6, 15)),
        Transaction(description="Online Purchase - Amazon", amount=-55.00, category="Night out", date_booked=datetime(2023, 6, 20)),
        Transaction(description="Utility Bill Payment - Electric", amount=130.00, category="Utilities", date_booked=datetime(2023, 6, 30)),

        # Year 2023 April
        Transaction(description="Dividends", amount=70.00, category="Salary", date_booked=datetime(2023, 4, 4)),
        Transaction(description="Rent April", amount=-600.00, category="Rent", date_booked=datetime(2023, 4, 9)),
        Transaction(description="Apple salary", amount=1200.00, category="Salary", date_booked=datetime(2023, 4, 16)),
        Transaction(description="Utility Bill Payment - Electric", amount=-45.00, category="Utilities", date_booked=datetime(2023, 4, 22)),
        Transaction(description="EDEKA sagt danke", amount=-390.00, category="Groceries", date_booked=datetime(2023, 4, 28)),
    ]
    for transaction in transactions:
        db_session.add(transaction)
    db_session.commit()

    transactions = db_session.query(Transaction).all()
    for transaction in transactions:
        transaction.calculate_saldo()

    db_session.commit()
    print("Completed seeding database")
