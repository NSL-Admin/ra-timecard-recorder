import json
import os
from typing import Optional, Self, TypeGuard


def is_valid_dict(dict_to_check: dict[str, Optional[str]]) -> TypeGuard[dict[str, str]]:
    return all(dict_to_check.values())


class SlackConfig:
    def __init__(self, app_token: str, bot_token: str) -> None:
        self.app_token = app_token
        self.bot_token = bot_token

    @classmethod
    def from_file(cls, filepath: str) -> Self:
        """
        return `SlackConfig` instance by parsing JSON file at the given `filepath`.
        """
        with open(filepath) as f:
            _config_dict = json.load(f)
        return cls(**_config_dict)

    @classmethod
    def from_env(cls) -> Self:
        """
        return `SlackConfig` instance by reading environment variables.
        """
        _slack_config = {
            "app_token": os.environ.get("SLACK_APP_TOKEN"),
            "bot_token": os.environ.get("SLACK_BOT_TOKEN"),
        }
        if is_valid_dict(_slack_config):
            return cls(**_slack_config)
        raise ValueError(
            "some of the following environment variables was not found: SLACK_APP_TOKEN, SLACK_BOT_TOKEN"
        )


class DBConfig:
    def __init__(self, username: str, password: str, host: str, db_name: str) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.db_name = db_name

    @classmethod
    def from_file(cls, filepath: str) -> Self:
        """
        return `DBConfig` instance by parsing JSON file at the given `filepath`.
        """
        with open(filepath) as f:
            _config_dict = json.load(f)
        return cls(**_config_dict)

    @classmethod
    def from_env(cls) -> Self:
        """
        return `DBConfig` instance by reading environment variables.
        """
        _db_config = {
            "username": os.environ.get("DB_USERNAME"),
            "password": os.environ.get("DB_PASSWORD"),
            "host": os.environ.get("DB_HOST"),
            "db_name": os.environ.get("DB_NAME"),
        }
        if is_valid_dict(_db_config):
            return cls(**_db_config)
        raise ValueError(
            "some of the following environment variables was not found: DB_USENAME, DB_PASSWORD, DB_HOST, DB_NAME"
        )


class BotConfig:
    def __init__(self, admin_ids: list[str]) -> None:
        "[NOTE] This class should not be instantiated directly. Use `BotConfig.from_file`"
        self.admin_ids = admin_ids

    @classmethod
    def from_file(cls, filepath: str) -> Self:
        """
        return `BotConfig` instance by parsing JSON file at the given `filepath`.
        """
        with open(filepath) as f:
            _config_dict = json.load(f)
        return cls(**_config_dict)
