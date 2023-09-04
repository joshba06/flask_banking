## Controller with routes

# Flask
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, abort
)


# Forms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired

# Graphs
import plotly
import plotly.graph_objects as go
import json

# Basics
from datetime import datetime, date
from pprint import pprint
import functools

# Models
from project.models import Transaction
from project.db import db_session


# Define the name of this blueprint and which url its reached under. This has to be registered in create_app()
transactions_bp = Blueprint('transactions', __name__,
               template_folder='templates',
               static_folder='../static',
               static_url_path='assets')

# Define forms to be used in this controller
class TransactionForm(FlaskForm):
    description = StringField("Transaction description", validators=[DataRequired()], render_kw={"placeholder": "Description"})
    category = SelectField("Category", choices = ["Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"])
    amount = DecimalField("Amount", places=2, validators=[DataRequired()], render_kw={"placeholder": "Amount"})
    submit = SubmitField("Add")

class FilterForm(FlaskForm):
    search_type = SelectField('Search type', choices = ["Matches", "Includes"])
    transaction_description = StringField("Description", render_kw={"placeholder": "Filter description"})
    category = SelectField("Category", choices = ["-Category-", "Salary", "Rent", "Utilities", "Groceries", "Night out", "Online services"])
    start_date = DateField('Startdate', format='%Y-%m-%d')
    end_date = DateField('Enddate', format='%Y-%m-%d')
    submit = SubmitField("Filter")
    clear = SubmitField("Clear")



@transactions_bp.route("/", methods=["GET", "POST"])
def index():

    # Transactions filter
    filter_form = FilterForm()
    if request.method == 'POST' and filter_form.clear.data:
        return redirect(url_for("transactions.index"))
    elif request.method == 'POST' and filter_form.submit.data:
        category = None if filter_form.category.data == "-Category-" else filter_form.category.data
        transactions = Transaction.read_all(start_date = filter_form.start_date.data,
                                             end_date=filter_form.end_date.data,
                                             category=category,
                                             search_type=filter_form.search_type.data,
                                             transaction_description=filter_form.transaction_description.data)
        grouped_transactions = Transaction.group_by_month(transactions)
    else:
        transactions = Transaction.read_all()
        grouped_transactions = Transaction.group_by_month(transactions)

    # New transaction
    transaction_form = TransactionForm()
    if transaction_form.validate_on_submit():
        new_transaction = Transaction(transaction_form.description.data, transaction_form.amount.data, transaction_form.category.data)
        try:
            db_session.add(new_transaction)
            db_session.commit()
            new_transaction.calculate_saldo()
            return redirect(url_for("transactions.index"))
        except:
            print("Something went wrong")


    transactions_sum = 0
    descriptions = []
    for transaction in transactions:
        descriptions.append(transaction.description)
        transactions_sum += transaction.amount
    unique_descriptions = list(set(descriptions))

    ## Display graphs

    # Prepare data for charts
    data_y = []
    data_pos = []
    data_neg = []
    data_sum = []
    if len(transactions) > 0:
        first_date = date(min(grouped_transactions.keys()), min(grouped_transactions[min(grouped_transactions.keys())].keys()), 1)
        last_date = date(max(grouped_transactions.keys()), max(grouped_transactions[max(grouped_transactions.keys())].keys()), 1)
        current_date = first_date

        while current_date <= last_date:
            if current_date.month < 10:
                data_y.append("0{}/{}".format(current_date.month, current_date.year))
            else:
                data_y.append("{}/{}".format(current_date.month, current_date.year))

            if current_date.year in grouped_transactions.keys():
                if current_date.month in grouped_transactions[current_date.year].keys():
                    data_pos.append(grouped_transactions[current_date.year][current_date.month]['income'])
                    data_neg.append(abs(grouped_transactions[current_date.year][current_date.month]['expenses']))
                    data_sum.append(grouped_transactions[current_date.year][current_date.month]['total'])
                else:
                    data_pos.append(0)
                    data_neg.append(0)
                    data_sum.append(0)
            else:
                for i in range(12):
                    data_pos.append(0)
                    data_neg.append(0)
                    data_sum.append(0)

            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
    else:
        data_y.append("None")
        data_pos.append(0)
        data_neg.append(0)
        data_sum.append(0)

    # Donut chart - only expenses
    expenses_per_category = {
        "Salary": 0,
        "Rent": 0,
        "Utilities": 0,
        "Groceries": 0,
        "Night out": 0,
        "Online services": 0
    }
    for transaction in transactions:
        if transaction.amount < 0:
            expenses_per_category[transaction.category] += transaction.amount

    colors = ["#3F3B6C", "#624F82", "#9F73AB", "#A3C7D6", "#A3C7D6", "#A3C7D6"]

    if len(transactions) == 0:
        values = [0, 0, 0, 0, 0, 0]
        labels = list(expenses_per_category.keys())
    else:
        labels = []
        values = []
        for key, val in expenses_per_category.items():
            labels.append(key)
            values.append(float(-1*val))

    fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.7)])
    fig_donut.update_traces(hoverinfo='label+value',
                            textinfo='none',
                            marker=dict(colors=colors, line=dict(color='#000000', width=2))
                            )
    fig_donut.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=0, b=0, l=1, r=0),
            legend=dict(
                y=0.5,
            )
        )
    if len(transactions) == 0:
        fig_donut.update_layout(annotations=[dict(text='No results', x=0.5, y=0.5, font_size=20, showarrow=False)])
    else:
        fig_donut.update_layout(annotations=[dict(text='Expenses', x=0.5, y=0.5, font_size=20, showarrow=False)])

    graphJSON_donut = json.dumps(fig_donut, cls=plotly.utils.PlotlyJSONEncoder)

    # Bar chart
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=data_y,
                    y=data_pos,
                    name='Income',
                    marker_color='rgb(0,128,0)'
                    ))
    fig_bar.add_trace(go.Bar(x=data_y,
                    y=data_neg,
                    name='Expenses',
                    marker_color='rgb(255,160,122)'
                    ))

    fig_bar.update_layout(
        xaxis_tickfont_size=14,
        yaxis=dict(
            title='Amount',
            # titlefont_size=16,
            # tickfont_size=14,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        barmode='group',
        bargap=0.15, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1 # gap between bars of the same location coordinate.
    )

    graphJSON_bar = json.dumps(fig_bar, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('transactions/base.html',
                            unique_descriptions=unique_descriptions,
                            transactions=transactions,
                            template_form=transaction_form,
                            filter_form=filter_form,
                            graphJSON_bar=graphJSON_bar,
                            graphJSON_donut=graphJSON_donut,
                            transactions_sum=transactions_sum)



## API endpoints
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
