from flask import (
    Blueprint, redirect, url_for
)

main_bp = Blueprint('main', __name__,
               template_folder='templates',
               static_folder='../static',
               static_url_path='assets')

@main_bp.route("/", methods=['GET'])
def home():
    return redirect(url_for("accounts.index"))
