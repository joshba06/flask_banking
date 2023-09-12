# Flask
from flask import (
    Blueprint, redirect, render_template, request, url_for, flash
)
from datetime import datetime, timedelta

# Basics
from pprint import pprint

# Forms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField, BooleanField
from wtforms.validators import DataRequired


# Models
from project.models import Account, Transaction, AccountLimitException
from project.db import db_session

# Forms
from project.transactions.transactions import TransactionForm, SubaccountTransferForm

# Define the name of this blueprint and which url its reached under. This has to be registered in create_app()
accounts_bp = Blueprint('accounts', __name__,
               template_folder='templates',
               static_folder='../static',
               static_url_path='assets')

class FilterForm(FlaskForm):
    search_type = SelectField('Search type', choices = ["Matches", "Includes"])
    transaction_description = StringField("Description", render_kw={"placeholder": "Search term"})
    category = SelectField("Category", choices = ["-Category-", "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"])
    start_date = DateField('Startdate', format='%Y-%m-%d')
    end_date = DateField('Enddate', format='%Y-%m-%d')
    submit = SubmitField("Filter")
    clear = SubmitField("Clear")

class AccountForm(FlaskForm):
    title = StringField("Title", render_kw={"placeholder": "e.g. 'Main' or 'Savings'"})
    iban = SelectField("Iban", choices = ["Coming soon..."], render_kw = {'disabled': 'disabled'})
    icon = SelectField("Icon", choices = ["Coming soon..."], render_kw = {'disabled': 'disabled'})
    accept_terms = BooleanField("Terms", validators=[DataRequired()])
    submit = SubmitField("Create")
    delete = SubmitField("Delete")

class DeleteAccountForm(FlaskForm):
    delete = SubmitField("Delete")


@accounts_bp.route("/accounts", methods=["GET"])
def index():
    print("I am here")
    # By default, forward to show page of any account
    return redirect(url_for("accounts.show", account_id=Account.query.all()[0].id))

@accounts_bp.route("/accounts/<int:account_id>", methods=["GET", "POST"])
def show(account_id, transactions_filter=None):
    account = Account.query.get(account_id)
    all_accounts = Account.query.all()
    transactions_filter = request.args.get('transactions_filter')

    # Transactions filter
    filter_form = FilterForm()
    if request.method == 'POST' and filter_form.clear.data:
        # print("Redirecting to accounts.show with default transactions filter cleared")
        return redirect(url_for("accounts.show", account_id=account_id, transactions_filter="cleared"))
    elif request.method == 'POST' and filter_form.submit.data:
        category = None if filter_form.category.data == "-Category-" else filter_form.category.data
        transactions = Transaction.read_all(account_id=account_id,
                                            start_date = filter_form.start_date.data,
                                            end_date=filter_form.end_date.data,
                                            category=category,
                                            search_type=filter_form.search_type.data,
                                            transaction_description=filter_form.transaction_description.data)
    else:
        if transactions_filter=="cleared":
            # print("Displaying ALL transactions")
            transactions = Transaction.read_all(account_id=account_id)
        else:
            transactions_filter="default_30_days"
            # print("Displaying default filter: Last 30 days")
            date_30_days_ago = (datetime.today() - timedelta(days=30)).date()
            filter_form.start_date.data = date_30_days_ago
            transactions = Transaction.read_all(start_date=date_30_days_ago, account_id=account_id)


    # Extract data for transaction statistics
    transaction_statistics = {}
    transaction_statistics['income'] = sum([transaction.amount for transaction in transactions if transaction.amount > 0])
    transaction_statistics['expenses'] = sum([transaction.amount for transaction in transactions if transaction.amount < 0])
    transaction_statistics['num_transactions'] = len(transactions)

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

    # Currency value formatting function to get format: 123.123,00
    def format_currency(value):
        # Determine if the value is negative
        is_negative = value < 0

        # Work with the absolute value to format the number
        abs_value = abs(value)

        # Convert the value to string and split at the decimal
        int_part, dec_part = "{:.2f}".format(abs_value).split('.')

        # Reverse the integer part to format in groups of 3
        reversed_int = int_part[::-1]

        # Group by threes and then join them with dots
        parts = [reversed_int[i:i+3] for i in range(0, len(reversed_int), 3)]
        formatted_int = '.'.join(parts)[::-1]  # Reverse again to get the original order

        # Build the final formatted string
        formatted_value = f"{formatted_int},{dec_part}"

        # If original value was negative, prepend the negative sign
        if is_negative:
            formatted_value = "-" + formatted_value

        return formatted_value


    # Create new account / edit account details form
    account_form = AccountForm()
    edit_account_form = AccountForm(obj=Account.query.get(account_id))
    delete_account_form = DeleteAccountForm()

    return render_template('accounts/show.html',
                        active_account_id=account_id,
                        transactions=transactions,
                        accounts=all_accounts,
                        filter_form=filter_form,
                        autocomplete_descriptions=autocomplete_descriptions,
                        transactions_table_sum=transactions_table_sum,
                        account_saldos=account_saldos,
                        transaction_form=transaction_form,
                        subaccount_transfer_form=subaccount_transfer_form,
                        format_currency=format_currency,
                        account_form=account_form,
                        edit_account_form=edit_account_form,
                        delete_account_form=delete_account_form,
                        transactions_filter=transactions_filter,
                        transaction_statistics=transaction_statistics
                        )

@accounts_bp.route("/accounts/create", methods=["POST"])
def create():

    account_form = AccountForm()

    # Create new iban
    iban = "GB29000060161331920000"
    all_ibans = [account.iban for account in Account.query.all()]
    iban_invalid = True
    increment = 1
    while iban_invalid:
        last_four = iban[-4:]
        incremented_value = int(last_four) + increment
        if incremented_value == 10000:
            incremented_value = 0
        new_last_four = "{:04}".format(incremented_value)
        new_iban = iban[:-4] + new_last_four
        if new_iban not in all_ibans:
            iban_invalid = False
        else:
            increment += 1

    try:
        new_account = Account(iban=new_iban, title=account_form.title.data)
        db_session.add(new_account)
        db_session.commit()
        print(f"Successfully created new account: {new_account}")
        flash('Successfully created new account.', "success")
        return redirect(url_for("accounts.show", account_id=new_account.id))
    except ValueError as ve:
        db_session.rollback()
        print(f"Error: {ve}")
        flash('Account title must be a string and max length of 15 characters.', "error")
        return redirect(url_for("accounts.index"))
    except Exception as e:
        db_session.rollback()
        print(f"Error occurred while creating new account: {e}")

        return redirect(url_for("accounts.index"))

@accounts_bp.route("/accounts/<int:account_id>/update", methods=["POST"])
def update(account_id):
    edit_account_form = AccountForm()

    account = Account.query.get(account_id)

    if not account:  # Edge case: Account does not exist.
        print(f"Could not find account with id {account_id}")
        flash('Account not found.', "error")
        return redirect(url_for("accounts.index"))

    account_title = edit_account_form.title.data
    if len(account_title) > 15:
        flash('Account title must be a string and max length of 15 characters.', "error")
    else:
        try:
            account.title = account_title
            db_session.add(account)
            db_session.commit()
            flash('Successfully updated account info.', "success")
        except Exception as e:
            db_session.rollback()
            print(f"Something went wrong while updating account info: {e}")
            flash('Something went wrong while updating account info.', "error")

    return redirect(url_for("accounts.show", account_id=account_id))

@accounts_bp.route("/accounts/<int:account_id>/delete", methods=["POST"])
def delete(account_id):

    try:
        account_to_delete = db_session.query(Account).filter(Account.id == account_id).first()
        if not account_to_delete:
            flash("Could not find account.", "error")
            return redirect(url_for("accounts.show", account_id=db_session.query(Account).first().id))

        account_count = db_session.query(Account).count()
        if account_count <= 1:
            flash("Cannot delete the last account.", "error")

        db_session.delete(account_to_delete)
        db_session.commit()
        flash('Successfully deleted account.', "success")
        return redirect(url_for("accounts.show", account_id=Account.query.all()[0].id))

    except Exception as e:
        db_session.rollback()
        print(f"Error occurred while deleting account: {e}")
        flash('Something went wrong while deleting account', "error")
        return redirect(url_for("accounts.show", account_id=account_id))
