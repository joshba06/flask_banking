from config import db

class Account(db.Model):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key = True)
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic')

    def __repr__(self):
        return f'<Account {self.id}>'

class Transaction(db.Model):
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key = True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    title = db.Column(db.String(80), index = True)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False, index = False, unique = False)
    saldo = db.Column(db.Numeric(precision=10, scale=2), nullable=False, index = False, unique = False)
    date_booked = db.Column(db.DateTime)

    def __repr__(self):
        return "[{}] {}, {}, saldo: {}".format(self.date_booked, self.title, self.amount, self.saldo)
