from flask import render_template, request, url_for, redirect

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


if __name__ == "__main__":
		#-> debug=False when in production!!
    app.run(host="0.0.0.0", port=8000, debug=True)
