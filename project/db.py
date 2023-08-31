SEED = False

# SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

engine = create_engine('sqlite:////tmp/test.db')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

from project.init_database import main

def init_db():
    import project.models
    Base.metadata.create_all(bind=engine)
    print("Initialised database")
    if SEED:
        main(db_session)
