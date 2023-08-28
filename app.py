import os
from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, RadioField
from wtforms.validators import DataRequired


## Configure app and database
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## Configure forms
app.config["SECRET_KEY"] = "my_secret"

class TransactionForm(FlaskForm):
    title = StringField("Transaction title", validators=[DataRequired()])
    amount = DecimalField("Amount", places=2, validators=[DataRequired()])
    submit = SubmitField("Add")

class FilterForm(FlaskForm):
    sorting_order = RadioField('Sorting Order', choices=[('asc', 'Ascending'), ('desc', 'Descending')])


## Configure models
class Account(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic')

    def __repr__(self):
        return f'<Account {self.id}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    title = db.Column(db.String(80), index = True)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False, index = False, unique = False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "[Transaction] {}, {}, {}".format(self.title, self.amount, self.created_at)

## Seed or load existing transactions
with app.app_context():
    db.create_all()
    if len(Transaction.query.all()) == 0:
        from seeds import Seed
        Seed.seed_transactions()


@app.route("/", methods=["GET", "POST"])
def index():

    # Transaction form
    transaction_form = TransactionForm()
    filter_form = FilterForm()

    # Add newly submitted transaction to database
    if transaction_form.validate_on_submit():
        form_title = transaction_form.title.data
        form_amount = transaction_form.amount.data
        print("Adding new transaction. Title: {}, amount: {}".format(form_title, form_amount))

        new_transaction = Transaction(title=form_title, amount=form_amount)
        db.session.add(new_transaction)
        try:
            db.session.commit()
            return redirect(url_for('index'))
        except:
            db.session.rollback()
            print("[FAILURE] Could not add transaction '{}' - {} to db".format(form_title, form_amount))


    transactions = Transaction.query.all()
    return render_template('base.html',
                           transactions = transactions,
                           template_form=transaction_form,
                           filter_form=filter_form)
