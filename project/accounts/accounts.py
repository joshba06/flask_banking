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
from wtforms.validators import DataRequired, Length


# Models
from project.models import Account, Transaction, AccountLimitException, IBANAlreadyExistsError
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
    title = StringField("Title",
                        render_kw={"placeholder": "e.g. 'Main' or 'Savings'"},
                        validators=[
                            DataRequired(),
                            Length(min=3, max=15)
                            # Further validation for string done in JS, because impossible if not using .is_validated()
                            ])
    accept_terms = BooleanField("Terms", validators=[DataRequired()])
    submit = SubmitField("Create")

class EditAccountForm(AccountForm):
    # Overriding the accept_terms field to make it not required
    accept_terms = BooleanField("Terms")

class DeleteAccountForm(FlaskForm):
    delete = SubmitField("Delete")


@accounts_bp.route("/accounts", methods=["GET"])
def index():
    return redirect(url_for("accounts.show", account_id=Account.query.all()[0].id))

@accounts_bp.route("/accounts/<int:account_id>", methods=["GET", "POST"])
def show(account_id, transactions_filter=None):

    # Importing form that relies on Account model to make sure import happens in correct order
    from project.transactions.transactions import SubaccountTransferForm

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
        account_saldos[account.id] = account.transactions.order_by(Transaction.utc_datetime_booked.desc()).first().saldo if account.transactions.count() > 0 else 0

    # Calculate sum to be displayed in last table row
    transactions_table_sum = sum([transaction.amount for transaction in transactions])

    # New transaction form
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
    edit_account_form = EditAccountForm(obj=Account.query.get(account_id))
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
    if not account_form.validate(): # Validates title length, checkbox (any form input is string by default)
        message = 'Form data is not valid.'
        status = "error"
    else:
        new_iban = generate_unique_iban()
        status, message = create_account(new_iban, account_form.title.data) # Validates title doesnt't start with digit

    flash(message, status)

    if status == "success":
        return redirect(url_for("accounts.show", account_id=Account.query.filter_by(iban=new_iban).first().id))
    else:
        return redirect(url_for("accounts.index"))

def generate_unique_iban():
    # Create new iban
    iban = "GB29000060161331920000"
    if Account.query.count() > 0:
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
    else:
        new_iban = iban
    return new_iban

def create_account(iban, title):
    try:
        new_account = Account(iban=iban, title=title)
        db_session.add(new_account)
        db_session.commit()
        print(f"Successfully created new account: {new_account}")
        return "success", 'Successfully created new account.'
    except ValueError as ve: # This will capture all ValueErrors raised in __init__
        db_session.rollback()
        print(f"Error: {ve}") # Display the actual error message from __init__
        return "error", f"{ve}"
    except IBANAlreadyExistsError as ib:
        db_session.rollback()
        print(f"Error: {ib}") # Display the actual error message from __init__
        return "error", f"{ib}"
    except AccountLimitException as ale:
        db_session.rollback()
        print(f"Error: {ale}") # Display the actual error message from __init__
        return "error", f"{ale}"
    except Exception as e:
        db_session.rollback()
        print(f"Error occurred while creating new account: {e}")
        return "error", 'Error occurred while creating the account.'

@accounts_bp.route("/accounts/<int:account_id>/update", methods=["POST"])
def update(account_id):

    edit_account_form = EditAccountForm()

    if not edit_account_form.validate(): # Validates title length (input is string by default)
        flash('Form data is not valid.', "error")
        return redirect(url_for("accounts.show", account_id=account_id))

    account = Account.query.get(account_id)
    if not account:  # Edge case: Account does not exist.
        flash('Account not found.', "error")
        return redirect(url_for("accounts.index"))

    account_title = edit_account_form.title.data

    # Validations (only title first char, because isnt part of form validation)
    try:
        if account_title[0] in "0123456789":
            flash('Account title cannot start with a digit.', "error")
            return redirect(url_for("accounts.show", account_id=account_id))

        # Update Account
        account.title = account_title
        db_session.add(account)
        db_session.commit()
        flash('Successfully updated account info.', "success")

    except Exception as e:
        db_session.rollback()
        print(f"Something went wrong while updating account info: {e}")
        flash('Something went wrong while updating account info. Please try again.', "error")

    return redirect(url_for("accounts.show", account_id=account_id))

@accounts_bp.route("/accounts/<int:account_id>/delete", methods=["POST"])
def delete(account_id):

    delete_account_form = DeleteAccountForm()
    if not delete_account_form.validate(): # Validates hidden_field (account is being deleted using form not url)
        flash("Form data is not valid.", "error")
        return redirect(url_for("accounts.index"))

    account_to_delete = Account.query.get(account_id)
    if not account_to_delete:
        flash("Could not find account.", "error")
        return redirect(url_for("accounts.index"))

    if Account.query.limit(2).count() <= 1:
        flash("Cannot delete the last account.", "error")
        return redirect(url_for("accounts.show", account_id=account_id))

    try:
        db_session.delete(account_to_delete)
        db_session.commit()

        next_account_id = Account.query.first().id
        flash('Successfully deleted account.', "success")
        return redirect(url_for("accounts.show", account_id=next_account_id))

    except Exception as e:
        db_session.rollback()
        print(f"Error occurred while deleting account: {e}")
        flash('Something went wrong while deleting account', "error")
        return redirect(url_for("accounts.show", account_id=account_id))
