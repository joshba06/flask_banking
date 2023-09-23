# Flask
from flask import (
    Blueprint, redirect, url_for, jsonify, abort, request, flash
)
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

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


# Define the name of this blueprint and which url its reached under. This has to be registered in create_app()
transactions_bp = Blueprint('transactions', __name__,
               template_folder='templates',
               static_folder='../static',
               static_url_path='assets')

# Define forms to be used in all controllers
def not_zero(form, field):
    if field.data == 0:
        raise ValidationError('Amount cannot be zero')

class TransactionForm(FlaskForm):
    description = StringField("Transaction description", validators=[DataRequired(), Length(max=80)], render_kw={"placeholder": "Reference"})
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

class SubaccountTransferForm(FlaskForm):
    description = StringField("Subaccount transfer description", validators=[DataRequired()], render_kw={"placeholder": "Reference"})
    choices = ["Recipient"]
    # for account in Account.query.all():
    #     choices.append(f"{account.title} ({account.iban[:4]}...{account.iban[-2:]})")
    recipient = SelectField("Recipient", choices = choices, validators=[DataRequired()], render_kw={"placeholder": "Recipient"})
    amount = DecimalField("Amount", places=2, validators=[DataRequired()], render_kw={"placeholder": "Amount"})
    submit = SubmitField("Add")


@transactions_bp.route("/accounts/<int:account_id>/transactions", methods=["POST"])
def create(account_id):

    transaction_form = TransactionForm()
    if not transaction_form.validate(): # Validates title max length, category(that it cannot be "Category" too), amount(can be string digits, cannot be <=0)
        message = 'Form data is not valid.'
        status = "error"
    else:
        account = Account.query.get(account_id)
        if not account: # Validates account exists
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
        print(f"Error occurred while creating new account: {e}")
        return "error", 'Error occurred while creating the account.', None

@transactions_bp.route("/accounts/<int:sender_account_id>/transactions/create_subaccount_transfer", methods=["POST"])
def create_subaccount_transfer(sender_account_id):

    sender_account = Account.query.get(sender_account_id)
    if not sender_account: # If sender account cannot be found, forward to index page
        flash("Could not find sender account.", "error")
        return redirect(url_for("accounts.index"))

    # Create subaccount transfer form and populate "choices" field. This is to
    subaccount_transfer_form = SubaccountTransferForm()



    recipient_account_title = subaccount_transfer_form.recipient.data.split("(")[0].strip()
    recipient_account_fractional_iban = subaccount_transfer_form.recipient.data.split("(")[1].strip()
    recipient_account_fractional_iban = recipient_account_fractional_iban.split(")")[0].strip()

    try:
        recipient_account = Account.query.filter(
            Account.title == recipient_account_title,
            Account.iban.like(f"{recipient_account_fractional_iban[:4]}%"),
            Account.iban.like(f"%{recipient_account_fractional_iban[-2:]}")
        ).one()
    except NoResultFound:
        print('Recipient account not found.')
        flash('Recipient account not found.', "error")
        return redirect(url_for("accounts.show", account_id=sender_account_id))

    print("Outside form")
    # POST request was made and form field have valid input
    if subaccount_transfer_form.validate_on_submit():
        print("I am inside the form")
        transfer_amount = subaccount_transfer_form.amount.data

        if transfer_amount <= 0:
            flash('Invalid transfer amount.', 'error')
            return redirect(url_for("accounts.show", account_id=sender_account_id))

        if sender_account.saldo < transfer_amount:
            flash('Insufficient funds.', 'error')
            return redirect(url_for("accounts.show", account_id=sender_account_id))


        sender_transaction = Transaction(subaccount_transfer_form.description.data, -subaccount_transfer_form.amount.data, "Transfer")
        sender_account.transactions.append(sender_transaction)

        recipient_transaction = Transaction(subaccount_transfer_form.description.data, subaccount_transfer_form.amount.data, "Transfer")
        recipient_account.transactions.append(recipient_transaction)

        try:
            db_session.add_all([sender_transaction, recipient_transaction])
            db_session.commit()
            sender_transaction.calculate_saldo()
            recipient_transaction.calculate_saldo()
            flash('Successfully created new transfer.', "success")
            return redirect(url_for("accounts.show", account_id=sender_account_id))
        except Exception as e:
            print(f"Something went wrong while creating new transfer: {e}")
            flash('Something went wrong while creating new transfer.', "error")
            db_session.rollback()

    else:
        flash('Invalid form submission.', "error")
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
