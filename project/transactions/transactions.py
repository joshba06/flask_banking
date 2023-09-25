# Flask
from flask import (
    Blueprint, redirect, url_for, jsonify, abort, request, flash
)
from sqlalchemy.orm.exc import NoResultFound

# CSV download
import csv
from io import StringIO
from werkzeug.wrappers import Response

# Forms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, SelectField
from wtforms.validators import DataRequired, Length, AnyOf, ValidationError

# Basics
from datetime import datetime
from pprint import pprint

# Models
from project.models import Account, Transaction
from project.db import db_session

## Forms
def not_zero(form, field):
    if field.data == 0:
        raise ValidationError('Amount cannot be zero')

def not_empty_string(form, field):
    if len(field.data.strip()) < 3:
        raise ValidationError('Description too short (consider whitespaces)')

class TransactionForm(FlaskForm):
    description = StringField("Transaction description",
                              validators=[DataRequired(), Length(max=80), not_empty_string],
                              render_kw={"placeholder": "Reference"})
    choices = ["Category", "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"]
    category = SelectField("Category",
                           choices = choices,
                           validators=[
                                DataRequired(),
                                AnyOf(choices[1:])
                               ])
    amount = DecimalField("Amount",
                          places=2,
                          validators=[DataRequired(), not_zero],
                          render_kw={"placeholder": "Amount"}
                          )
    submit = SubmitField("Add")

class SubaccountTransferForm(TransactionForm):
    recipient = SelectField("Recipient", choices = ["Recipient"], validators=[DataRequired()], render_kw={"placeholder": "Recipient"})

    # Remove "category" from form
    def __init__(self, *args, **kwargs):
        super(SubaccountTransferForm, self).__init__(*args, **kwargs)
        del self.category

## Exceptions / errors
class AccountNotFoundError(Exception):
    pass
class TransactionError(Exception):
    pass

## Routes
transactions_bp = Blueprint('transactions', __name__,
               template_folder='templates',
               static_folder='../static',
               static_url_path='assets')

@transactions_bp.route("/accounts/<int:account_id>/transactions", methods=["POST"])
def create(account_id):

    transaction_form = TransactionForm()
    if not transaction_form.validate(): # Validates title max length, category(that it cannot be "Category" too), amount(can be string digits, cannot be <=0)
        message = 'Form data is not valid.'
        status = "error"
    else:
        try:
            account = validate_account(account_id)
        except AccountNotFoundError as e:
            message = 'Account not found.'
            status = "error"
        else:
            status, message, _ = create_transaction(account=account,
                                                 description=transaction_form.description.data,
                                                 amount=transaction_form.amount.data,
                                                 category=transaction_form.category.data)
    flash(message, status)

    if status == "success":
        return redirect(url_for("accounts.show", account_id=account_id))
    else:
        return redirect(url_for("accounts.index"))

@transactions_bp.route("/accounts/<int:sender_account_id>/transactions/create_subaccount_transfer", methods=["POST"])
def create_subaccount_transfer(sender_account_id):

    # Process form data
    transfer_form = SubaccountTransferForm()
    try:
        sender_account = validate_account(sender_account_id)


        message, status = update_transfer_form(transfer_form, sender_account.id)

        recipient_account_title, recipient_fractional_iban = validate_transfer_data(transfer_form)

        # Retrieve recipient account based on parsed data
        recipient_account = get_recipient_account(recipient_account_title, recipient_fractional_iban)

        # Create transactions
        process_sender_transaction(sender_account, transfer_form)
        process_recipient_transaction(recipient_account, transfer_form)

        message = f"Successfully created transfer from {sender_account.title} to {recipient_account.title}"
        status = "success"
        flash(message, status)
        return redirect(url_for("accounts.show", account_id=sender_account_id))

    except AccountNotFoundError as ae:
        flash(str(ae), "error")
        return redirect(url_for("accounts.index"))
    except (NoResultFound, TransactionError, ValueError) as e:
        flash(str(e), "error")
        return redirect(url_for("accounts.show", account_id=sender_account_id))

@transactions_bp.route('/download_csv', methods=['POST'])
def download_csv():
    try:
        account = Account.query.get(request.form.get('account_id'))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') != "None" else None
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') != "None" else None
        transaction_description = request.form.get('transaction_description') if request.form.get('transaction_description') != "None" else None
        search_type = request.form.get('search_type') if request.form.get('search_type') != "None" else None

        # Query transactions, just like in index route
        transactions = Transaction.read_all(account_id=account.id,
                                            start_date = start_date,
                                            end_date=end_date,
                                            search_type=search_type,
                                            transaction_description=transaction_description)

        def generate():
            data = StringIO()
            writer = csv.writer(data)

            writer.writerow(("Account_iban", "Date", "Description", "Category", "Amount", "Saldo"))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

            for transaction in transactions:
                writer.writerow((
                    transaction.account.iban,
                    transaction.utc_datetime_booked.strftime("%d/%m/%Y"),
                    transaction.description,
                    f"{transaction.amount}€",
                    f"{transaction.saldo}€"
                ))
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)

        response = Response(generate(), mimetype='text/csv')
        response.headers.set("Content-Disposition", "attachment", filename="data.csv")
        flash('Successfully downloaded csv.', "success")
        return response
    except:
        flash('Successfully went wrong while downloading csv.', "error")
        return redirect(url_for("accounts.show", account_id=1))



## Subfunctions
def create_transaction(account, description, amount, category, utc_datetime_booked=None):
    '''
    :param account: account instance
    :param description: Description of transaction
    :param amount: Transaction amount
    :param category: TO BE DISCUSSED
    :param utc_datetime_booked: datetime object in UTC timezone format
    '''

    try:
        # Create new transaction and link to account
        transaction = Transaction(description=description, amount=amount, category=category, utc_datetime_booked=utc_datetime_booked)
        account.transactions.append(transaction)
        db_session.add(account)
        db_session.commit()

        # Calculate saldo for transaction
        transaction.calculate_saldo()

        print(f"Successfully created new transaction: {transaction}")
        return "success", "Successfully created new transaction.", transaction.id

    except ValueError as ve: # This will capture all ValueErrors raised in __init__
        db_session.rollback()
        print(f"Error: {ve}") # Display the actual error message from __init__
        return "error", f"{ve}", None
    except Exception as e:
        db_session.rollback()
        print(f"Error occurred while creating new transaction: {e}")
        return "error", 'Error occurred while creating the transaction.', None

def validate_account(account_id):
    account = Account.query.get(account_id)
    if not account:
        raise AccountNotFoundError('Account not found.')
    else:
        return account

def update_transfer_form(form, sender_account_id):
    try:
        all_accounts = Account.query.all()
        if len(all_accounts) == 1:
            # If only one account exists, disable all fields (no transfer destination available)
            for field in form:
                field.render_kw = {**field.render_kw, 'disabled': True} if field.render_kw else {'disabled': True}

        else:
            for account in all_accounts:
                if account.id != sender_account_id:
                    form.recipient.choices.append(f"{account.title} ({account.iban[:4]}...{account.iban[-2:]})") # Do not add currently displayed account

            # Update the (AnyOf) validators for the recipient field
            form.recipient.validators = [DataRequired()]
            recipient_values = [choice for choice in form.recipient.choices if choice != "Recipient"] # make Recipient not a valid value
            form.recipient.validators.append(AnyOf(recipient_values))
    except Exception:
        return "Could not update transfer form.", "error"
    else:
        return "Updated transfer form", "success"

def validate_transfer_data(form):
    # Evaluate data received from form
    if not form.validate(): # Validates reference max length, recipient(that it cannot be "Recipient" too), amount(can be string digits, cannot be = 0)
        raise ValueError('Form data is not valid.')
    else:
        recipient_title = form.recipient.data.split("(")[0].strip()
        recipient_fractional_iban = form.recipient.data.split("(")[1].strip()
        recipient_fractional_iban = recipient_fractional_iban.split(")")[0].strip()
        return recipient_title, recipient_fractional_iban

def get_recipient_account(title, fractional_iban):
    """Retrieve recipient account based on title and fractional IBAN."""
    return Account.query.filter(
        Account.title == title,
        Account.iban.like(f"{fractional_iban[:4]}%"),
        Account.iban.like(f"%{fractional_iban[-2:]}")
    ).one()

def process_sender_transaction(account, form):
    """Process sender transaction and return its ID."""
    _, _, transaction_id = create_transaction(
        account=account,
        description=form.description.data,
        amount=-form.amount.data,
        category="Transfer"
    )
    if not transaction_id:
        raise TransactionError("Failed to process sender transaction.")

def process_recipient_transaction(account, form):
    """Process recipient transaction and return its ID."""
    _, _, transaction_id = create_transaction(
        account=account,
        description=form.description.data,
        amount=form.amount.data,
        category="Transfer"
    )
    if not transaction_id:
        raise TransactionError("Failed to process recipient transaction.")
