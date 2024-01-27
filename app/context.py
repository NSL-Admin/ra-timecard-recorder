from logging import Logger

from sqlalchemy.orm import Session, sessionmaker

from .config import BotConfig


class BotContext:
    def __init__(
        self, botcfg: BotConfig, logger: Logger, db_sessmaker: sessionmaker[Session]
    ) -> None:
        """
        container that stores various objects used in listeners
        """
        self.botcfg = botcfg
        self.logger = logger
        self.db_sessmaker = db_sessmaker
