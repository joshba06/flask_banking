from flask import render_template, request, url_for, redirect

from config import app
import transactions as Transactions

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, DateField
from wtforms.validators import DataRequired

from pprint import pprint

class TransactionForm(FlaskForm):
    title = StringField("Transaction title", validators=[DataRequired()])
    amount = DecimalField("Amount", places=2, validators=[DataRequired()])
    submit = SubmitField("Add")

class FilterForm(FlaskForm):
    start_date = DateField('Startdate', format='%Y-%m-%d')
    end_date = DateField('Enddate', format='%Y-%m-%d')
    submit = SubmitField("Go")


@app.route("/", methods=["GET", "POST"])
def index():

    # Filter displayed results
    filter_form = FilterForm()
    if request.method == 'POST' and filter_form.submit:
        if filter_form.start_date.data != None and filter_form.end_date.data != None:
            transactions = Transactions.read_all(start_date = filter_form.start_date.data, end_date=filter_form.end_date.data)
        elif filter_form.start_date.data != None:
            filter_form.start_date.data = filter_form.start_date.data
            transactions = Transactions.read_all(start_date = filter_form.start_date.data)
        elif filter_form.end_date.data != None:
            transactions = Transactions.read_all(end_date=filter_form.end_date.data)
        else:
            transactions = Transactions.read_all()
    else:
        transactions = Transactions.read_all()

    # Provide form to add new transactions
    transaction_form = TransactionForm()
    if transaction_form.validate_on_submit():
        response = Transactions.create(transaction_form.title.data, transaction_form.amount.data)
        if response:
            return redirect(url_for("index"))


    return render_template('base.html',
                           transactions=transactions,
                           template_form=transaction_form,
                           filter_form=filter_form)


if __name__ == "__main__":
		#-> debug=False when in production!!
    app.run(host="0.0.0.0", port=8000, debug=True)
