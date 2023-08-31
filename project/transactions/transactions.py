## Controller with routes

# Flask
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
# Database connection
# from project.db import get_db

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


# Define the name of this blueprint and which url its reached under. This has to be registered in create_app()
transactions_bp = Blueprint('transactions', __name__,
               template_folder='templates',
               static_folder='../static',
               static_url_path='assets')

# Define forms to be used in this controller
class TransactionForm(FlaskForm):
    title = StringField("Transaction title", validators=[DataRequired()])
    amount = DecimalField("Amount", places=2, validators=[DataRequired()])
    submit = SubmitField("Add")

class FilterForm(FlaskForm):
    search_type = SelectField('Search type', choices = ["Matches", "Includes"])
    transaction_title = StringField("Title", render_kw={"placeholder": "Search term"})
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
        transactions = Transaction.read_all(start_date = filter_form.start_date.data,
                                             end_date=filter_form.end_date.data,
                                             search_type=filter_form.search_type.data,
                                             transaction_title=filter_form.transaction_title.data)
        grouped_transactions = Transaction.group_by_month(transactions)
    else:
        transactions = Transaction.read_all()
        grouped_transactions = Transaction.group_by_month(transactions)

    # New transaction
    transaction_form = TransactionForm()
    if transaction_form.validate_on_submit():
        response = Transaction.create(transaction_form.title.data, transaction_form.amount.data)
        if response:
            return redirect(url_for("transactions.index"))

    transactions_sum = 0
    titles = []
    for transaction in transactions:
        titles.append(transaction.title)
        transactions_sum += transaction.amount
    unique_titles = list(set(titles))

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

    # Donut chart
    labels = ['Income','Expenses']
    values = [sum(data_pos), sum(data_neg)]
    colors = ['green', 'red']
    fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig_donut.update_traces(hoverinfo='label+value', textinfo='value',
                  marker=dict(colors=colors, line=dict(color='#000000', width=2)))
    fig_donut.update_layout(
            # title='US Export of Plastic Scrap',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )
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
        # title='US Export of Plastic Scrap',
        xaxis_tickfont_size=14,
        yaxis=dict(
            title='Amount',
            # titlefont_size=16,
            # tickfont_size=14,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        # legend=dict(
        #     x=0,
        #     y=1.0,
        #     bgcolor='rgba(255, 255, 255, 0)',
        #     bordercolor='rgba(255, 255, 255, 0)'
        # ),
        barmode='group',
        bargap=0.15, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1 # gap between bars of the same location coordinate.
    )

    graphJSON_bar = json.dumps(fig_bar, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('transactions/base.html',
                            unique_titles=unique_titles,
                            transactions=transactions,
                            template_form=transaction_form,
                            filter_form=filter_form,
                            graphJSON_bar=graphJSON_bar,
                            graphJSON_donut=graphJSON_donut,
                            transactions_sum=transactions_sum)
