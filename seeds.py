from app import db, Account, Transaction
import random

from faker import Faker
fake = Faker()

class Seed:

    @classmethod
    def seed_transactions(self):
        for i in range(15):
            name = fake.name()
            amount = round(random.uniform(-1000, 1000), 2)
            transaction = Transaction(title=name, amount=amount)
            db.session.add(transaction)

        db.session.commit()
        print("Database seeded")
