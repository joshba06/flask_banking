from flask import render_template, request, url_for, redirect
import csv
from io import StringIO
from werkzeug.wrappers import Response
from datetime import datetime

from config import app
import transactions as Transactions

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired

from pprint import pprint

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


@app.route("/", methods=["GET", "POST"])
def index():

    # Transactions filter
    filter_form = FilterForm()
    if request.method == 'POST' and filter_form.clear.data:
        return redirect(url_for("index"))
    elif request.method == 'POST' and filter_form.submit.data:
        transactions = Transactions.read_all(start_date = filter_form.start_date.data,
                                             end_date=filter_form.end_date.data,
                                             search_type=filter_form.search_type.data,
                                             transaction_title=filter_form.transaction_title.data)
    else:
        transactions = Transactions.read_all()

    # New transaction
    transaction_form = TransactionForm()
    if transaction_form.validate_on_submit():
        response = Transactions.create(transaction_form.title.data, transaction_form.amount.data)
        if response:
            return redirect(url_for("index"))

    titles = []
    for transaction in transactions:
        titles.append(transaction.title)
    unique_titles = list(set(titles))

    return render_template('base.html',
                            unique_titles=unique_titles,
                            transactions=transactions,
                            template_form=transaction_form,
                            filter_form=filter_form)



@app.route("/download_csv", methods=["POST"])
def download_csv():
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') != "None" else None
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') != "None" else None
    transaction_title = request.form.get('transaction_title') if request.form.get('transaction_title') != "None" else None
    search_type = request.form.get('search_type') if request.form.get('search_type') != "None" else None

    # Query transactions, just like in index route
    transactions = Transactions.read_all(start_date = start_date,
                                             end_date=end_date,
                                             search_type=search_type,
                                             transaction_title=transaction_title)


    def generate():
        data = StringIO()
        writer = csv.writer(data)

        writer.writerow(("Date", "Title", "Amount", "Saldo"))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        for transaction in transactions:
            writer.writerow((
                transaction.date_booked.strftime("%Y / %m / %d"),
                transaction.title,
                transaction.amount,
                transaction.saldo,
            ))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="data.csv")
    return response




if __name__ == "__main__":
		#-> debug=False when in production!!
    app.run(host="0.0.0.0", port=8000, debug=True)
