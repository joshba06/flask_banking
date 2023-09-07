# Flask
from flask import (
    Blueprint, redirect, render_template, request, url_for, jsonify, abort
)

# Forms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired


# Models
from project.models import Account
from project.db import db_session


# Define the name of this blueprint and which url its reached under. This has to be registered in create_app()
accounts_bp = Blueprint('accounts', __name__,
               template_folder='templates',
               static_folder='../static',
               static_url_path='assets')

@accounts_bp.route("/accounts", methods=["GET"])
def index():
    return "Hello"

@accounts_bp.route("/accounts/<int:account_id>", methods=["GET"])
def show(account_id):
    return render_template('accounts/show.html', id=1)
