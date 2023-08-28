from config import db
from sqlalchemy.sql import func

class Account(db.Model):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key = True)
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic')
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'<Account {self.id}>'

class Transaction(db.Model):
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key = True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    title = db.Column(db.String(80), index = True)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False, index = False, unique = False)
    saldo = db.Column(db.Numeric(precision=10, scale=2), nullable=False, index = False, unique = False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "[Transaction] {}, {}, saldo: {}".format(self.title, self.amount, self.saldo)
