from datetime import datetime, date
from sqlalchemy import desc, func
import decimal

from sqlalchemy import Column, Integer, String, DateTime, Numeric
from project.db import Base, db_session
print(f"[models.py] Connecting Transaction model to {db_session.get_bind()}")

class Transaction(Base):

    __tablename__ = "transactions"
    id = Column(Integer, primary_key = True)
    description = Column(String(80), index = True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False, index = False, unique = False)
    saldo = Column(Numeric(precision=10, scale=2), nullable=True, index = False, unique = False)
    category = Column(String(20), nullable=False)
    date_booked = Column(DateTime, nullable=False)

    def __init__(self, description, amount, category, date_booked=None):
        if not isinstance(description, str) or len(description) > 80:
            raise ValueError("The 'description' variable must be a string with less than 80 characters.")
        else:
            self.description = description

        if not isinstance(amount, (int, float, decimal.Decimal)):
            raise ValueError("The 'amount' variable must be a decimal, integer or float.")
        else:
            self.amount = decimal.Decimal(amount)

        if category not in ["Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"]:
            raise ValueError("Invalid category value.")
        self.category = category

        if date_booked == None:
            self.date_booked = datetime.now()
        else:
            if not isinstance(date_booked, datetime):
                raise ValueError("date_booked is not of type datetime.")
            else:
                self.date_booked = date_booked
        self.saldo = None

    def __repr__(self):
        return "[{}] description: '{}', category: {}, amount: {:.2f}, saldo: {}".format(self.date_booked, self.description, self.category, self.amount, self.saldo)

    def calculate_saldo(self):
        # Calculate the saldo by summing up the "amount" of older transactions
        saldo_previous_transactions = db_session.query(func.sum(Transaction.amount)).filter(
            Transaction.date_booked < self.date_booked
        ).scalar()

        # If there are no older transactions, saldo is the same as the current transaction's amount
        if saldo_previous_transactions is None:
            self.saldo = self.amount
        else:
            self.saldo = saldo_previous_transactions + self.amount

        # Update the "saldo" column in the current transaction instance

        self.saldo = round(self.saldo, 2)

        db_session.add(self)
        db_session.commit()

    @classmethod
    def read_all(cls, start_date = None, end_date = None, category = None, search_type = None, transaction_description = None):

        # Check input parameters
        if start_date is not None and not isinstance(start_date, date):
            raise ValueError("start_date must be a date object.")
        if end_date is not None and not isinstance(end_date, date):
            raise ValueError("end_date must be a date object.")
        # Check search_type
        if search_type not in [None, "Includes", "Matches"]:
            raise ValueError("search_type must be either 'Includes' or 'Matches'.")

        # Check category
        if category not in [None, "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"]:
            raise ValueError("Invalid category value.")

        # print("Filtering start: {}, end: {}, search type: {}, description: {},".format(start_date, end_date, search_type, transaction_description))

        # Query database for description
        if transaction_description != None and transaction_description != "":
            if search_type == "Matches":
                transactions = Transaction.query.filter(Transaction.description == transaction_description).all()
            else:
                transactions = Transaction.query.filter(Transaction.description.like("%{}%".format(transaction_description))).all()
        else:
            transactions = Transaction.query.order_by(desc(Transaction.date_booked)).all()

        # Filter results for dates
        if start_date != None and end_date != None:
            start_date = start_date
            end_date = end_date
            filtered_transactions = [transaction for transaction in transactions if (transaction.date_booked.date() >= start_date and transaction.date_booked.date() <= end_date)]
        elif start_date != None:
            start_date = start_date
            filtered_transactions = [transaction for transaction in transactions if transaction.date_booked.date() >= start_date]
        elif end_date != None:
            end_date = end_date
            filtered_transactions = [transaction for transaction in transactions if transaction.date_booked.date() <= end_date]
        else:
            filtered_transactions = transactions

        # Filter results for category
        if category != None:
            temp = [transaction for transaction in filtered_transactions if transaction.category == category]
            filtered_transactions = temp

        sorted_filtered_transactions = sorted(filtered_transactions, key=lambda x: x.date_booked, reverse=True)

        return sorted_filtered_transactions

    @classmethod
    def group_by_month(cls, transactions):
        if not isinstance(transactions, list):
            raise TypeError("Input transactions must be a list.")

        for transaction in transactions:
            if not isinstance(transaction, cls):
                raise TypeError("Input transactions must be a list of Transaction objects.")

        data = {}
        for transaction in transactions:

            if transaction.date_booked.year not in data.keys():
                data[transaction.date_booked.year] = {}
            if transaction.date_booked.month not in data[transaction.date_booked.year].keys():
                data[transaction.date_booked.year][transaction.date_booked.month] = {"income": 0, "expenses": 0, "total": 0}
            if transaction.amount >= 0:
                data[transaction.date_booked.year][transaction.date_booked.month]["income"] += transaction.amount
            elif transaction.amount < 0:
                data[transaction.date_booked.year][transaction.date_booked.month]["expenses"] += transaction.amount
            data[transaction.date_booked.year][transaction.date_booked.month]["total"] += transaction.amount

        return data
