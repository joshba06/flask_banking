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
from wtforms.validators import DataRequired

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
class TransactionForm(FlaskForm):
    description = StringField("Transaction description", validators=[DataRequired()], render_kw={"placeholder": "Reference"})
    category = SelectField("Category", choices = ["Category", "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"], validators=[DataRequired()])
    amount = DecimalField("Amount", places=2, validators=[DataRequired()], render_kw={"placeholder": "Amount"})
    submit = SubmitField("Add")

class SubaccountTransferForm(FlaskForm):
    description = StringField("Subaccount transfer description", validators=[DataRequired()], render_kw={"placeholder": "Reference"})
    choices = ["Recipient"]
    for account in Account.query.all():
        choices.append(f"{account.title} ({account.iban[:4]}...{account.iban[-2:]})")
    recipient = SelectField("Recipient", choices = choices, validators=[DataRequired()], render_kw={"placeholder": "Recipient"})
    amount = DecimalField("Amount", places=2, validators=[DataRequired()], render_kw={"placeholder": "Amount"})
    submit = SubmitField("Add")


@transactions_bp.route("/accounts/<int:account_id>/transactions/create", methods=["POST"])
def create(account_id):

    account = Account.query.get(account_id)
    if not account:
        print(f"Cannot find account with id {account_id}")
        flash('Account not found.', "error")
        return redirect(url_for("accounts.index"))

    transaction_form = TransactionForm()

    # POST request was made and all TransactionForm fields have valid input
    if transaction_form.validate_on_submit():
        print("I am inside the TRANSACTION form")
        new_transaction = Transaction(transaction_form.description.data, transaction_form.amount.data, transaction_form.category.data)
        try:
            account.transactions.append(new_transaction)
            db_session.add(account)
            db_session.commit()
            new_transaction.calculate_saldo()
            print(f"Added new transaction: {new_transaction}")
            flash('Successfully created new transaction.', "success")
            return redirect(url_for("accounts.show", account_id=account_id))
        except Exception as e:
            db_session.rollback()
            print(f"Something went wrong while creating new transaction: {e}")
            flash('Something went wrong while creating new transaction.', "error")

    # Request is not POST or form fields have invalid input
    else:
        flash('Invalid form submission.', "error")
        return redirect(url_for("accounts.show", account_id=account_id))

@transactions_bp.route("/accounts/<int:sender_account_id>/transactions/create_subaccount_transfer", methods=["POST"])
def create_subaccount_transfer(sender_account_id):

    sender_account = Account.query.get(sender_account_id)
    if not sender_account: # If sender account cannot be found, forward to index page
        flash("Could not find sender account.", "error")
        return redirect(url_for("accounts.index"))

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
                    transaction.date_booked.strftime("%d/%m/%Y"),
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





# ## API endpoints
def transactions_to_json(transaction_list):
    json_transactions = []
    for transaction in transaction_list:
        transaction_dict = {
            "id": str(transaction.id),
            "amount": str(transaction.amount),
            "saldo": str(transaction.saldo),
            "description": transaction.description,
            "category": transaction.category,
            "date_booked": transaction.date_booked.isoformat()
        }
        json_transactions.append(transaction_dict)
    return json_transactions

# Read all transactions
def read_all():
    return transactions_to_json(Transaction.query.all())

# Read single transaction
def read_one(id):
    data = Transaction.query.get(id)
    if data:
        return transactions_to_json([data])
    else:
        abort(
            404, f"Transaction with id {id} not found"
        )

# Create a transaction
def create(transaction):
    transaction = dict(description=transaction.get("description"),amount=transaction.get("amount"), category=transaction.get("category"), date_booked=transaction.get("date_booked"))

    # Validate request data
    if transaction["description"] == None or len(transaction["description"]) > 80:
        return jsonify({'error': 'Invalid or missing description'}), 400

    if not isinstance(transaction["amount"], (int, float)):
        return jsonify({'error': 'Invalid or missing amount'}), 400

    if transaction["category"] not in ["Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"]:
        return jsonify({'error': 'Invalid category value'}), 400

    if transaction["date_booked"] != None and transaction["date_booked"] != "None":
        try:
            transaction["date_booked"] = datetime.fromisoformat(transaction["date_booked"].replace('Z', '+00:00'))
        except:
            return jsonify({'error': 'Could not convert date_booked to datetime object,'}), 400

    # Create a new Transaction object
    new_transaction = Transaction(**transaction)
    db_session.add(new_transaction)
    db_session.commit()
    new_transaction.calculate_saldo()

    # Return a success response
    return jsonify({
        'id': new_transaction.id,
        'description': new_transaction.description,
        'amount': float(new_transaction.amount),
        'category': new_transaction.category,
        'date_booked': new_transaction.date_booked.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'saldo': float(new_transaction.saldo)
    }), 201
