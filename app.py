import os
from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.sql import func

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Configure models
class Account(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic')

    def __repr__(self):
        return f'<Account {self.id}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    title = db.Column(db.String(80), index = True, unique = True)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False, index = False, unique = False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "[Transaction] {}, {}, {}".format(self.title, self.amount, self.created_at)

# Seed transactions
from seeds import Seed

with app.app_context():
    db.drop_all()
    db.create_all()

    Seed.seed_transactions()


@app.route('/')
def index():
    transactions = Transaction.query.all()
    return render_template('base.html', transactions = transactions)
