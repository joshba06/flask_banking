from config import db
from models import Transaction
from sqlalchemy import desc
from pprint import pprint
from datetime import datetime

def read_all(start_date = None, end_date = None, search_type = None, transaction_title = None):

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

def create(title, amount):
    last_saldo = db.session.query(Transaction).order_by(Transaction.id.desc()).first().saldo
    saldo = last_saldo + amount
    new_transaction = Transaction(title=title, amount=amount, saldo=saldo, date_booked=datetime.now())

    db.session.add(new_transaction)
    try:
        db.session.commit()
        print("Added new transaction. Title: {}, amount: {}".format(title, amount))
        return True
    except:
        db.session.rollback()
        print(f"Failed to create new transaction with title {new_transaction.title}")
        return False
