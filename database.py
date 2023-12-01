import os
import signal
import sys
import urllib.parse

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

from model import Base

# load secret tokens to environmental variables
# THIS MUST BE AT THE TOP OF SOURCE CODE
if os.path.exists(".db.env"):
    load_dotenv(dotenv_path=".db.env")
else:
    print("Skipped loading .db.env as it doesn't exist.")

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.environ["DB_USERNAME"],
    password=urllib.parse.quote_plus(os.environ["DB_PASSWORD"]),
    host=os.environ["DB_HOST"],
    database=os.environ["DB_NAME"],
    query={"sslmode": "disable"},
)

# define an engine that connects to the database
engine = create_engine(url=db_url, pool_pre_ping=True)
# define a sessionmaker that creates a "session", on which database operations are performed
get_session = sessionmaker(bind=engine, expire_on_commit=False)
# create tables related to Base, if they're not present
Base.metadata.create_all(bind=engine, checkfirst=True)


# define a signal handler to ensure the database connection is closed when the program is terminated
def signal_handler(signal_num, frame):
    engine.dispose()
    sys.exit()


# register signal_handler to be called when the program is TERMinated or INTerrupted
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
