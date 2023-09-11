# Flask
from flask import (
    Blueprint, redirect, url_for, jsonify, abort
)

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
    category = SelectField("Category", choices = ["Category", "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"])
    amount = DecimalField("Amount", places=2, validators=[DataRequired()], render_kw={"placeholder": "Amount"})
    submit = SubmitField("Add")

class SubaccountTransferForm(FlaskForm):
    description = StringField("Subaccount transfer description", validators=[DataRequired()], render_kw={"placeholder": "Reference"})
    choices = ["Recipient"]
    for account in Account.query.all():
        choices.append(f"{account.title} ({account.iban[:4]}...{account.iban[-2:]})")
    recipient = SelectField("Recipient", choices = choices, render_kw={"placeholder": "Recipient"})
    amount = DecimalField("Amount", places=2, validators=[DataRequired()], render_kw={"placeholder": "Amount"})
    submit = SubmitField("Add")



## App routes
# @transactions_bp.route("/", methods=["GET", "POST"])
# def index():

#     # Transactions filter
#     filter_form = FilterForm()
#     if request.method == 'POST' and filter_form.clear.data:
#         return redirect(url_for("transactions.index"))
#     elif request.method == 'POST' and filter_form.submit.data:
#         category = None if filter_form.category.data == "-Category-" else filter_form.category.data
#         transactions = Transaction.read_all(start_date = filter_form.start_date.data,
#                                              end_date=filter_form.end_date.data,
#                                              category=category,
#                                              search_type=filter_form.search_type.data,
#                                              transaction_description=filter_form.transaction_description.data)
#         grouped_transactions = Transaction.group_by_month(transactions)
#     else:
#         transactions = Transaction.read_all()
#         grouped_transactions = Transaction.group_by_month(transactions)

#     # New transaction
#     transaction_form = TransactionForm()
#     if transaction_form.validate_on_submit():
#         new_transaction = Transaction(transaction_form.description.data, transaction_form.amount.data, transaction_form.category.data)
#         try:
#             db_session.add(new_transaction)
#             db_session.commit()
#             new_transaction.calculate_saldo()
#             return redirect(url_for("transactions.index"))
#         except:
#             print("Something went wrong")


#     transactions_sum = 0
#     descriptions = []
#     for transaction in transactions:
#         descriptions.append(transaction.description)
#         transactions_sum += transaction.amount
#     unique_descriptions = list(set(descriptions))

#     ## Display graphs
#     # Prepare data for charts
#     data_y = []
#     data_pos = []
#     data_neg = []
#     data_sum = []
#     if len(transactions) > 0:
#         first_date = date(min(grouped_transactions.keys()), min(grouped_transactions[min(grouped_transactions.keys())].keys()), 1)
#         last_date = date(max(grouped_transactions.keys()), max(grouped_transactions[max(grouped_transactions.keys())].keys()), 1)
#         current_date = first_date

#         while current_date <= last_date:
#             if current_date.month < 10:
#                 data_y.append("0{}/{}".format(current_date.month, current_date.year))
#             else:
#                 data_y.append("{}/{}".format(current_date.month, current_date.year))

#             if current_date.year in grouped_transactions.keys():
#                 if current_date.month in grouped_transactions[current_date.year].keys():
#                     data_pos.append(grouped_transactions[current_date.year][current_date.month]['income'])
#                     data_neg.append(abs(grouped_transactions[current_date.year][current_date.month]['expenses']))
#                     data_sum.append(grouped_transactions[current_date.year][current_date.month]['total'])
#                 else:
#                     data_pos.append(0)
#                     data_neg.append(0)
#                     data_sum.append(0)
#             else:
#                 for i in range(12):
#                     data_pos.append(0)
#                     data_neg.append(0)
#                     data_sum.append(0)

#             if current_date.month == 12:
#                 current_date = date(current_date.year + 1, 1, 1)
#             else:
#                 current_date = date(current_date.year, current_date.month + 1, 1)
#     else:
#         data_y.append("None")
#         data_pos.append(0)
#         data_neg.append(0)
#         data_sum.append(0)

#     # Donut chart - only expenses
#     expenses_per_category = {
#         "Salary": 0,
#         "Rent": 0,
#         "Utilities": 0,
#         "Groceries": 0,
#         "Night out": 0,
#         "Online services": 0
#     }
#     for transaction in transactions:
#         if transaction.amount < 0:
#             expenses_per_category[transaction.category] += transaction.amount

#     colors = ["#321D70", "#25528F", "#5083C1", "#7CA6D7", "#A6C4E5", "#CCD9F5"]

#     if len(transactions) == 0:
#         values = [0, 0, 0, 0, 0, 0]
#         labels = list(expenses_per_category.keys())
#     else:
#         labels = []
#         values = []
#         for key, val in expenses_per_category.items():
#             labels.append(key)
#             values.append(float(-1*val))

#     fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.7)])
#     fig_donut.update_traces(hoverinfo='label+value',
#                             textinfo='none',
#                             marker=dict(colors=colors, line=dict(color='#000000', width=2))
#                             )
#     fig_donut.update_layout(
#             paper_bgcolor='rgba(0,0,0,0)',
#             plot_bgcolor='rgba(0,0,0,0)',
#             margin=dict(t=0, b=0, l=1, r=0),
#             legend=dict(
#                 y=0.5,
#             )
#         )
#     if len(transactions) == 0:
#         fig_donut.update_layout(annotations=[dict(text='No results', x=0.5, y=0.5, font_size=16, showarrow=False)])
#     else:
#         fig_donut.update_layout(annotations=[dict(text='Expenses', x=0.5, y=0.5, font_size=16, showarrow=False)])

#     graphJSON_donut = json.dumps(fig_donut, cls=plotly.utils.PlotlyJSONEncoder)

#     # Bar chart
#     fig_bar = go.Figure()
#     fig_bar.add_trace(go.Bar(x=data_y,
#                     y=data_pos,
#                     name='Income',
#                     marker_color='#38485E'
#                     ))
#     fig_bar.add_trace(go.Bar(x=data_y,
#                     y=data_neg,
#                     name='Expenses',
#                     marker_color='#E36E39'
#                     ))

#     fig_bar.update_layout(
#         xaxis_tickfont_size=14,
#         yaxis=dict(
#             title='Amount',
#             # titlefont_size=16,
#             # tickfont_size=14,
#         ),
#         margin=dict(r=0),
#         paper_bgcolor='rgba(0,0,0,0)',
#         plot_bgcolor='rgba(0,0,0,0)',
#         showlegend=False,
#         barmode='group',
#         bargap=0.15, # gap between bars of adjacent location coordinates.
#         bargroupgap=0.1 # gap between bars of the same location coordinate.
#     )

#     graphJSON_bar = json.dumps(fig_bar, cls=plotly.utils.PlotlyJSONEncoder)

#     return render_template('transactions/index.html',
#                             unique_descriptions=unique_descriptions,
#                             transactions=transactions,
#                             template_form=transaction_form,
#                             filter_form=filter_form,
#                             graphJSON_bar=graphJSON_bar,
#                             graphJSON_donut=graphJSON_donut,
#                             transactions_sum=transactions_sum)

@transactions_bp.route("/accounts/<int:account_id>/transactions/create", methods=["POST"])
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
            print(f"Added new transaction: {new_transaction}")
            return redirect(url_for("accounts.show", account_id=account_id))
        except:
            print("Something went wrong")

@transactions_bp.route("/accounts/<int:sender_account_id>/transactions/create_subaccount_transfer", methods=["POST"])
def create_subaccount_transfer(sender_account_id):

    subaccount_transfer_form = SubaccountTransferForm()

    sender_account = Account.query.get(sender_account_id)

    recipient_account_title = subaccount_transfer_form.recipient.data.split("(")[0].strip()
    recipient_account_fractional_iban = subaccount_transfer_form.recipient.data.split("(")[1].strip()
    recipient_account_fractional_iban = recipient_account_fractional_iban.split(")")[0].strip()

    recipient_account = Account.query.filter(Account.title==recipient_account_title, Account.iban.like(f"{recipient_account_fractional_iban[:4]}%"), Account.iban.like(f"%{recipient_account_fractional_iban[-2:]}")).one()

    if subaccount_transfer_form.validate_on_submit():
        sender_transaction = Transaction(subaccount_transfer_form.description.data, -subaccount_transfer_form.amount.data, "Transfer")
        sender_account.transactions.append(sender_transaction)

        recipient_transaction = Transaction(subaccount_transfer_form.description.data, subaccount_transfer_form.amount.data, "Transfer")
        recipient_account.transactions.append(recipient_transaction)

        try:
            db_session.add_all([sender_transaction, recipient_transaction])
            db_session.commit()
            sender_transaction.calculate_saldo()
            recipient_transaction.calculate_saldo()
            return redirect(url_for("accounts.show", account_id=sender_account_id))
        except:
            print("Something went wrong")







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
