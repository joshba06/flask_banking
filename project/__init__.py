import os
import connexion
from dotenv import load_dotenv



def create_app(test_setup=False):
    # create and configure the app
    from swagger_ui_bundle import swagger_ui_3_path
    options = {'swagger_path': swagger_ui_3_path}
    app = connexion.App(__name__, specification_dir="./", options=options)
    app.add_api("swagger.yml")

    # Load secret vars from env file
    load_dotenv()

    app.app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        DATABASE=os.getenv("DATABASE_URL"),
    )

    from project.db import init_db
    if test_setup is False:
        print("Starting normal setup")
        init_db()
        print("Initialisation complete")
    else:
        print("Starting test setup")
        init_db(test_setup=True)

    from project.transactions.transactions import transactions_bp
    app.app.register_blueprint(transactions_bp, url_prefix='/banking')

    from project.main.main import main_bp
    app.app.register_blueprint(main_bp, url_prefix='/')

    return app.app
