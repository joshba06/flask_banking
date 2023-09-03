import os
from flask import Flask

def create_app(test_setup=False):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from project.db import init_db
    if test_setup is False:
        print("Starting normal setup")
        init_db()
    else:
        print("Starting test setup")
        init_db(test_setup=True)


    # Register routes for model "transaction"
    from project.transactions import transactions
    from project.transactions.transactions import transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/')

    return app
