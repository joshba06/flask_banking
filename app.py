from flask import render_template, request, url_for, redirect

from config import app
import transactions as transactions

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, RadioField
from wtforms.validators import DataRequired


class TransactionForm(FlaskForm):
    title = StringField("Transaction title", validators=[DataRequired()])
    amount = DecimalField("Amount", places=2, validators=[DataRequired()])
    submit = SubmitField("Add")

class FilterForm(FlaskForm):
    sorting_order = RadioField('Sorting Order', choices=[('asc', 'Ascending'), ('desc', 'Descending')])


@app.route("/", methods=["GET", "POST"])
def index():

    transaction_form = TransactionForm()
    filter_form = FilterForm()

    if transaction_form.validate_on_submit():
        response = transactions.create(transaction_form.title.data, transaction_form.amount.data)
        if response:
            return redirect(url_for("index"))


    return render_template('base.html',
                           transactions = transactions.read_all(),
                           template_form=transaction_form,
                           filter_form=filter_form)


if __name__ == "__main__":
		#-> debug=False when in production!!
    app.run(host="0.0.0.0", port=8000, debug=True)
