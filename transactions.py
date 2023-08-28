from config import db
from models import Transaction
from sqlalchemy import desc
from pprint import pprint
from datetime import datetime

def read_all(start_date = None, end_date = None):
    if start_date != None:
        transactions = Transaction.query.filter(Transaction.date_booked >= start_date).order_by(desc(Transaction.date_booked)).all()
    elif end_date != None:
        transactions = Transaction.query.filter(Transaction.date_booked <= end_date).order_by(desc(Transaction.date_booked)).all()
    elif start_date != None and end_date != None:
        transactions = Transaction.query.filter(Transaction.date_booked >= start_date, Transaction.date_booked <= end_date).order_by(desc(Transaction.date_booked)).all()
    else:
        transactions = Transaction.query.order_by(desc(Transaction.date_booked)).all()
    return transactions

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
