from datetime import datetime
from sqlalchemy import desc, case

from sqlalchemy import Column, Integer, String, DateTime, Numeric
from project.db import Base, db_session


class Transaction(Base):

    __tablename__ = "transactions"
    id = Column(Integer, primary_key = True)
    title = Column(String(80), index = True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False, index = False, unique = False)
    saldo = Column(Numeric(precision=10, scale=2), nullable=False, index = False, unique = False)
    date_booked = Column(DateTime)

    def __repr__(self):
        return "[{}] {}, {}, saldo: {}".format(self.date_booked, self.title, self.amount, self.saldo)

    @classmethod
    def read_all(cls, start_date = None, end_date = None, search_type = None, transaction_title = None):
        # print("Filtering start: {}, end: {}, search type: {}, title: {},".format(start_date, end_date, search_type, transaction_title))

        # Query database for title
        if transaction_title != None and transaction_title != "":
            if search_type == "Matches":
                transactions = Transaction.query.filter(Transaction.title == transaction_title).all()
            else:
                transactions = Transaction.query.filter(Transaction.title.like("%{}%".format(transaction_title))).all()
        else:
            transactions = Transaction.query.order_by(desc(Transaction.date_booked)).all()

        # Filter results for dates
        if start_date != None and end_date != None:
            filtered_transactions = [transaction for transaction in transactions if (transaction.date_booked.date() >= start_date and transaction.date_booked.date() <= end_date)]
        elif start_date != None:
            filtered_transactions = [transaction for transaction in transactions if transaction.date_booked.date() >= start_date]
        elif end_date != None:
            filtered_transactions = [transaction for transaction in transactions if transaction.date_booked.date() <= end_date]
        else:
            filtered_transactions = transactions

        sorted_filtered_transactions = sorted(filtered_transactions, key=lambda x: x.date_booked, reverse=True)

        return sorted_filtered_transactions

    @classmethod
    def create(cls, title, amount):
        last_saldo = db_session.query(Transaction).order_by(Transaction.id.desc()).first().saldo
        saldo = last_saldo + amount
        new_transaction = Transaction(title=title, amount=amount, saldo=saldo, date_booked=datetime.now())

        db_session.add(new_transaction)
        try:
            db_session.commit()
            print("Added new transaction. Title: {}, amount: {}".format(title, amount))
            return True
        except:
            db_session.rollback()
            print(f"Failed to create new transaction with title {new_transaction.title}")
            return False

    @classmethod
    def group_by_month(cls, transactions):
        data = {}
        for transaction in transactions:
            # print("Date: {}, amount: {}".format(transaction.date_booked, transaction.amount))
            if transaction.date_booked.year not in data.keys():
                data[transaction.date_booked.year] = {}
            if transaction.date_booked.month not in data[transaction.date_booked.year].keys():
                data[transaction.date_booked.year][transaction.date_booked.month] = {"income": 0, "expenses": 0, "total": 0}
            if transaction.amount >= 0:
                data[transaction.date_booked.year][transaction.date_booked.month]["income"] += transaction.amount
            elif transaction.amount < 0:
                data[transaction.date_booked.year][transaction.date_booked.month]["expenses"] += transaction.amount
            data[transaction.date_booked.year][transaction.date_booked.month]["total"] += transaction.amount


        # result = session.query(
        #         func.extract('year', Transaction.date_booked).label('year'),
        #         func.extract('month', Transaction.date_booked).label('month'),
        #         func.sum(Transaction.amount).label('total_amount'),
        #         func.sum(case((Transaction.amount >= 0, Transaction.amount), else_=0)).label('positive_amount'),
        #         func.sum(case((Transaction.amount < 0, Transaction.amount), else_=0)).label('negative_amount')
        #     ).group_by('year', 'month').order_by('year', 'month').all()

        # summary_data = {}
        # for row in result:
        #     if row.year not in summary_data:
        #         summary_data[row.year] = {}
        #     summary_data[row.year][row.month] = {'total_amount': row.total_amount,
        #                                          'positive_amount': row.positive_amount,
        #                                          'negative_amount': row.negative_amount}

        return data
