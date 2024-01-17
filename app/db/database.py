import logging
import signal
import sys
import urllib.parse

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import DBConfig
from .model import Base


def setup_db_and_get_sessionmaker(
    db_config: DBConfig, sqlalchemy_loglevel: int = logging.WARNING
) -> sessionmaker[Session]:
    """
    return `sessionmaker` after following procedures:

    1. set SQLAlchemy logger to `sqlalchemy_loglevel`.
    2. connect to DB and create all tables defined in model.py.
    3. get `sessionmaker` that creates "session", on which DB operations will be performed.
    4. set up signal handler, so that connection to db will be properly closed on SIGINT or SIGTERM.
    """
    logging.getLogger("sqlalchemy.engine").setLevel(sqlalchemy_loglevel)

    ### DB setup ###
    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username=db_config.username,
        password=urllib.parse.quote_plus(db_config.password),
        host=db_config.host,
        database=db_config.db_name,
        query={"sslmode": "disable"},
    )

    # define an engine that connects to the database
    engine = create_engine(url=db_url, pool_pre_ping=True)
    # create tables related to Base, if they're not present
    Base.metadata.create_all(bind=engine, checkfirst=True)

    # define a sessionmaker that creates a "session", on which database operations are performed
    sessmaker = sessionmaker(bind=engine, expire_on_commit=False)

    ### signal handler setup ###
    # define a signal handler to ensure the database connection is closed when the program is terminated
    def signal_handler(signal_num, frame):
        engine.dispose()
        sys.exit()

    # register signal_handler to be called when the program is TERMinated or INTerrupted
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    return sessmaker
