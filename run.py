import argparse
import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.config import BotConfig, DBConfig, SlackConfig
from app.context import BotContext
from app.db.setup import setup_db_and_get_sessionmaker
from app.listeners import register_listeners


class Args(argparse.Namespace):
    botconfig: str
    dbconfig: str
    slackconfig: str
    bot_verbose: bool
    db_verbose: bool


parser = argparse.ArgumentParser(description="Launch RA timecard recorder")
parser.add_argument(
    "--botconfig", help="JSON file containing bot configuration", required=True
)
parser.add_argument(
    "--dbconfig",
    help="JSON file containing database configuration (if not given, environment variables will be used)",
)
parser.add_argument(
    "--slackconfig",
    help="JSON file containing slack configuration (if not given, environment variables will be used)",
)
parser.add_argument(
    "--bot_verbose",
    help="Enable verbose logging from the bot application",
    action="store_true",
)
parser.add_argument(
    "--db_verbose", help="Enable verbose logging from SQLAlchemy", action="store_true"
)

if __name__ == "__main__":
    args = parser.parse_args(namespace=Args())

    ### globally enable logging (to stdout) ###
    logging.basicConfig()

    ### create logger for logs from this app ###
    logger = logging.getLogger("bot")
    if args.bot_verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    ### load config ###
    # load config file for bot
    bot_config = BotConfig.from_file(filepath=args.botconfig)

    # load config for db from either file or environment variables
    if args.dbconfig:
        db_config = DBConfig.from_file(filepath=args.dbconfig)
    else:
        logger.info(
            "database configuration file was not specified. loading from environment variables instead"
        )
        db_config = DBConfig.from_env()
    # load config for slack from either file or environment variables
    if args.slackconfig:
        slack_config = SlackConfig.from_file(filepath=args.slackconfig)
    else:
        logger.info(
            "slack configuration file was not specified. loading from environment variables instead"
        )
        slack_config = SlackConfig.from_env()

    ### setup db ###
    sqlalchemy_loglevel = logging.INFO if args.db_verbose else logging.WARNING
    db_sessmaker = setup_db_and_get_sessionmaker(
        db_config=db_config, sqlalchemy_loglevel=sqlalchemy_loglevel
    )

    # wrap objects in BotContext
    bot_context = BotContext(
        botcfg=bot_config, logger=logger, db_sessmaker=db_sessmaker
    )

    # create app and register listeners
    app = App(token=slack_config.bot_token)
    register_listeners(app=app, bot_context=bot_context)

    ### launch bot ###
    SocketModeHandler(app=app, app_token=slack_config.app_token).start()
