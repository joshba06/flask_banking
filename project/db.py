# SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

# Import for seeding sessions
from datetime import datetime, timedelta
import random
from faker import Faker
faker = Faker()

engine = create_engine('sqlite://')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db(test_setup=False):
    from project.models import Transaction


    if test_setup is False:

        Base.metadata.create_all(bind=engine)
        print("Initialising database for normal setup")
        # if len(Transaction.query.all()) == 0:
            # print("Seeding database")
            # create_database(db_session, Transaction)
    else:
        print("Hello")
        print(Transaction.query.count())
        Transaction.query.delete()
        print(Transaction.query.count())

        db_session.add(Transaction("New", 123))
        db_session.commit()
        print(Transaction.query.count())

        print("Skipping database initialisation.")



def create_database(db_session, Transaction):

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

        try:
            new_transaction = Transaction(name, amount, sorted_dates[i])
            # new_transaction.calculate_saldo(db_session)
            db_session.add(new_transaction)
            db_session.commit()
        except:
            pass

    print("Created new database")
