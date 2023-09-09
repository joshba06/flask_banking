# Flask
from flask import (
    Blueprint, redirect, render_template, request, url_for, jsonify, abort
)

# Basics
from pprint import pprint

# Forms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired


# Models
from project.models import Account, Transaction
from project.db import db_session


# Define the name of this blueprint and which url its reached under. This has to be registered in create_app()
accounts_bp = Blueprint('accounts', __name__,
               template_folder='templates',
               static_folder='../static',
               static_url_path='assets')


class TransactionForm(FlaskForm):
    description = StringField("Transaction description", validators=[DataRequired()], render_kw={"placeholder": "Reference"})
    category = SelectField("Category", choices = ["Category", "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"])
    amount = DecimalField("Amount", places=2, validators=[DataRequired()], render_kw={"placeholder": "Amount"})
    submit = SubmitField("Add")

class SubaccountTransferForm(FlaskForm):
    description = StringField("Subaccount transfer description", validators=[DataRequired()], render_kw={"placeholder": "Reference"})
    choices = ["Recipient"]
    for account in Account.query.all():
        choices.append(account.iban)
    recipient = SelectField("Recipient", choices = choices, render_kw={"placeholder": "Recipient"})
    amount = DecimalField("Amount", places=2, validators=[DataRequired()], render_kw={"placeholder": "Amount"})
    submit = SubmitField("Add")

class FilterForm(FlaskForm):
    search_type = SelectField('Search type', choices = ["Matches", "Includes"])
    transaction_description = StringField("Description", render_kw={"placeholder": "Search term"})
    category = SelectField("Category", choices = ["-Category-", "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"])
    start_date = DateField('Startdate', format='%Y-%m-%d')
    end_date = DateField('Enddate', format='%Y-%m-%d')
    submit = SubmitField("Filter")
    clear = SubmitField("Clear")


@accounts_bp.route("/accounts", methods=["GET"])
def index():
    accounts = Account.query.all()
    return render_template('accounts/show.html',
                           accounts=accounts)

@accounts_bp.route("/accounts/<int:account_id>", methods=["GET", "POST"])
def show(account_id):

    account = Account.query.get(account_id)
    all_accounts = Account.query.all()

    # Transactions filter. By default, show only transactions belonging to current account
    filter_form = FilterForm()
    if request.method == 'POST' and filter_form.clear.data:
        return redirect(url_for("accounts.show", account_id=account_id))
    elif request.method == 'POST' and filter_form.submit.data:
        category = None if filter_form.category.data == "-Category-" else filter_form.category.data
        transactions = Transaction.read_all(account_id=account_id,
                                            start_date = filter_form.start_date.data,
                                            end_date=filter_form.end_date.data,
                                            category=category,
                                            search_type=filter_form.search_type.data,
                                            transaction_description=filter_form.transaction_description.data)
    else:
        transactions = Transaction.read_all(account_id=account_id)

    # Extract unique transaction descriptions for display in autocomplete field
    autocomplete_descriptions = list(set([transaction.description for transaction in transactions]))

    # Extract saldos for accounts
    account_saldos = {}
    for account in all_accounts:
        account_saldos[account.id] = account.transactions.order_by(Transaction.date_booked.desc()).first().saldo if account.transactions.count() > 0 else 0

    # Calculate sum to be displayed in last table row
    transactions_table_sum = sum([transaction.amount for transaction in transactions])

    # New transaction frorm
    transaction_form = TransactionForm()
    subaccount_transfer_form = SubaccountTransferForm()


    return render_template('accounts/show.html',
                        active_account_id=account_id,
                        transactions=transactions,
                        accounts=all_accounts,
                        filter_form=filter_form,
                        autocomplete_descriptions=autocomplete_descriptions,
                        transactions_table_sum=transactions_table_sum,
                        account_saldos=account_saldos,
                        transaction_form=transaction_form,
                        subaccount_transfer_form=subaccount_transfer_form
                        )


@accounts_bp.route("/accounts/<int:account_id>/transactions", methods=["POST"])
def create(account_id):

    account = Account.query.get(account_id)

    transaction_form = TransactionForm()

    if transaction_form.validate_on_submit():
        new_transaction = Transaction(transaction_form.description.data, transaction_form.amount.data, transaction_form.category.data)
        try:
            account.transactions.append(new_transaction)
            db_session.add(account)
            db_session.commit()
            new_transaction.calculate_saldo()
            return redirect(url_for("accounts.show", account_id=account_id))
        except:
            print("Something went wrong")

# @accounts_bp.route("/accounts/<int:account_id>/subaccount_transfer", methods=["POST"])
# def subaccount_transfer(account_id)):
#     sender_account = Account.query.get(account_id)

#     subaccount_transfer_form = SubaccountTransferForm()

#     if subaccount_transfer_form.validate_on_submit():
#         recipient_account =
#         new_transaction = Transaction(subaccount_transfer_form.description.data, subaccount_transfer_form.amount.data, transaction_form.category.data)
#         try:
#             account.transactions.append(new_transaction)
#             db_session.add(account)
#             db_session.commit()
#             new_transaction.calculate_saldo()
#             return redirect(url_for("accounts.show", account_id=account_id))
#         except:
#             print("Something went wrong")
