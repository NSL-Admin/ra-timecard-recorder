from slack_bolt import Ack, BoltContext
from slack_sdk.web.client import WebClient
from sqlalchemy import select

from ...context import BotContext
from ...db.model import RA, User


def register_RA_wrapper(bot_context: BotContext):
    botctx = bot_context

    def register_RA(
        ack: Ack, body: dict, client: WebClient, command: dict, context: BoltContext
    ):
        ack()

        # check that `context` variable is available
        if not (context.channel_id and context.actor_user_id):
            raise ValueError("something is wrong with `context` variable")

        ra_name = command["text"].strip()
        if not ra_name:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=":x: Use this command like `/register_ra <RA Job Name (e.g. CREST, NTT, ...)>`",
            )
            botctx.logger.info(
                f"slack user {context.actor_user_id} executed /register_ra command with no argument"
            )
            return

        # check that ra_name doesn't contain redundant prefix/suffix
        REDUNDANT_CHARS = ["<", ">", "*"]
        if ra_name[0] in REDUNDANT_CHARS or ra_name[-1] in REDUNDANT_CHARS:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=":x: Don't enclose RA name between symbols",
            )
            botctx.logger.info(
                f"slack user {context.actor_user_id} executed /register_ra command enclosing RA name in symbols: {ra_name}"
            )
            return

        with botctx.db_sessmaker() as sess:
            # check that the user is already registered
            user = sess.execute(
                select(User).where(User.slack_user_id == context.actor_user_id)
            ).scalar_one_or_none()
            if not user:
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=":x: You have to register first with `/init <Your Name>`.",
                )
                botctx.logger.info(
                    f"slack user {context.actor_user_id} executed /register_ra, but is not registered as bot user yet"
                )
                return

            # check that the RA job is not already registered for this user
            _should_be_none = sess.execute(
                select(RA)
                .join(User, User.id == RA.user_id)
                .where(
                    RA.ra_name == ra_name, User.slack_user_id == context.actor_user_id
                )
            ).scalar_one_or_none()
            if _should_be_none is not None:
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=f":x: RA {ra_name} is already registered for you",
                )
                botctx.logger.info(
                    f"slack user {context.actor_user_id} executed /register_ra, but RA job {ra_name} is already registered for the user."
                )
                return

            try:
                ra = RA(
                    user_id=user.id,
                    ra_name=ra_name,
                )
                sess.add(ra)
                sess.flush()
                sess.commit()
            except Exception:
                sess.rollback()
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=":x: Failed to register RA Job due to some database error.",
                )
                botctx.logger.exception(
                    f"failed to register RA Job {ra_name} for slack user {context.actor_user_id} due to a database error"
                )
                raise
            else:
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=f':white_check_mark: RA Job "{ra_name}" has been successfully registered.',
                )
                botctx.logger.info(
                    f"registered RA Job {ra_name} for slack user {context.actor_user_id}"
                )

    return register_RA
