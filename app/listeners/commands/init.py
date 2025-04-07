import json
import os

from psycopg2.errors import UniqueViolation
from slack_bolt import Ack, BoltContext
from slack_sdk.web.client import WebClient
from sqlalchemy.exc import IntegrityError

from ...context import BotContext
from ...db.model import User


def init_wrapper(bot_context: BotContext):
    botctx = bot_context

    def init(
        ack: Ack, body: dict, client: WebClient, command: dict, context: BoltContext
    ):
        ack()

        # check that `context` variable is available
        if not (context.channel_id and context.actor_user_id):
            raise ValueError("something is wrong with `context` variable")

        username = command["text"].strip()
        if not username:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=":x: Use this command like `/init <Your Name>`",
            )
            botctx.logger.info(
                f"slack user {context.actor_user_id} executed /init command with no argument"
            )
            return

        # check that username doesn't contain redundant prefix/suffix
        REDUNDANT_CHARS = ["<", ">", "*"]
        if username[0] in REDUNDANT_CHARS or username[-1] in REDUNDANT_CHARS:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=":x: Don't enclose your name between symbols",
            )
            botctx.logger.info(
                f"slack user {context.actor_user_id} executed /init command enclosing their name in symbols: {username}"
            )
            return

        with (
            botctx.db_sessmaker() as sess
        ):  # with `with` statement, sess.close() is not needed
            try:
                # add the user to the database
                user = User(
                    slack_user_id=context.actor_user_id,
                    name=username,
                )
                sess.add(user)
                sess.flush()
                sess.commit()
                # fetch App Home view to publish it to the user
                app_home_view_filepath = os.path.join(
                    os.path.dirname(__file__),
                    "../../assets/current_app_home_block.json",
                )
                if os.path.exists(app_home_view_filepath):
                    with open(app_home_view_filepath) as viewfile:
                        app_home_view = json.load(viewfile)
                else:
                    raise FileNotFoundError(
                        f"JSON file containing App Home view ({app_home_view_filepath}) was not found."
                    )
            except IntegrityError as e:
                sess.rollback()
                if isinstance(e.orig, UniqueViolation):
                    client.chat_postEphemeral(
                        channel=context.channel_id,
                        user=context.actor_user_id,
                        text=f":thinking_face: Hi {username}, it seems you've been registered already.",
                    )
                    botctx.logger.info(
                        f"slack user {context.actor_user_id} executed /init, but is already registered as bot user"
                    )
                else:
                    # exceptions other than UniqueViolation
                    client.chat_postEphemeral(
                        channel=context.channel_id,
                        user=context.actor_user_id,
                        text=":x: Failed to register due to some database error.",
                    )
                    botctx.logger.exception(
                        f"failed to register slack user {context.actor_user_id} as bot user due to a database error"
                    )
            else:
                # publish App Home view to the user
                client.views_publish(user_id=context.actor_user_id, view=app_home_view)
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=":email: Check DM from this bot.",
                )
                dm_with_the_user = client.conversations_open(
                    users=context.actor_user_id
                )
                client.chat_postMessage(
                    channel=dm_with_the_user["channel"]["id"],
                    text=f':white_check_mark: Hi {username}, you\'ve been successfully registered.\n:rocket: Open the "Home" tab above and read the usage guide!',
                    mrkdwn=True,
                )
                botctx.logger.info(
                    f"registered slack user {context.actor_user_id} as new bot user with the name {username}"
                )

    return init
