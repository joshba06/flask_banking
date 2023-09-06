import os
from dotenv import load_dotenv

class Config:

    # Load secret vars from env file
    load_dotenv()

    IS_PROD = os.getenv('IS_HEROKU', None)

    ## PRODUCTION config
    if IS_PROD == "True" or IS_PROD is True:
        DATABASE_URL=os.getenv("DATABASE_URL_HEROKU")
        SECRET_KEY=os.getenv("SECRET_KEY_HEROKU"),

    ## DEVELOPMENT config
    else:
        DATABASE_URL="sqlite:///project.db"
        SECRET_KEY=os.getenv("SECRET_KEY_LOCAL")
        SQLALCHEMY_TRACK_MODIFICATIONS = False
