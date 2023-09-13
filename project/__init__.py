import connexion
from pprint import pprint
from flask import jsonify

app = None

def create_app(test_setup=False):
    # print("[__init__.py] Creating app")

    from swagger_ui_bundle import swagger_ui_3_path
    options = {'swagger_path': swagger_ui_3_path}

    global app
    app = connexion.App(__name__, specification_dir="./", options=options)
    app.app.config.from_object('config.Config')

    app.add_api("swagger.yml")
    app = app.app

    from project.db import init_db
    if test_setup is False:
        print("__________[APP] NORMAL SETUP__________")
    else:
        print("__________[APP] TEST SETUP__________")
        app.config.update({
            "TESTING": True,
            'WTF_CSRF_ENABLED': False
        })
    init_db()

    from project.accounts.accounts import accounts_bp
    app.register_blueprint(accounts_bp, url_prefix='/')

    from project.transactions.transactions import transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/')

    from project.main.main import main_bp
    app.register_blueprint(main_bp, url_prefix='/')

    return app
