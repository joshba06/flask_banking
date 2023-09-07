from flask import (
    Blueprint, render_template
)

main_bp = Blueprint('main', __name__,
               template_folder='templates',
               static_folder='../static',
               static_url_path='assets')

# @main_bp.route("/", methods=['GET'])
# def home():
#     return render_template('main/home.html')
