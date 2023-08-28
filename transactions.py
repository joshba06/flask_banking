from config import db
from models import Transaction

def read_all(start_date = None, end_date = None):
    if start_date != None:
        transactions = Transaction.query.filter(Transaction.created_at >= start_date).all()
    elif end_date != None:
        transactions = Transaction.query.filter(Transaction.created_at <= end_date).all()
    elif start_date != None and end_date != None:
        transactions = Transaction.query.filter(Transaction.created_at >= start_date, Transaction.created_at <= end_date).all()
    else:
        transactions = Transaction.query.all()
    return transactions

def create(title, amount):
    last_saldo = db.session.query(Transaction).order_by(Transaction.id.desc()).first().saldo
    saldo = last_saldo + amount
    new_transaction = Transaction(title=title, amount=amount, saldo=saldo)

    db.session.add(new_transaction)
    try:
        db.session.commit()
        print("Added new transaction. Title: {}, amount: {}".format(title, amount))
        return True
    except:
        db.session.rollback()
        print(f"Failed to create new transaction with title {new_transaction.title}")
        return False
