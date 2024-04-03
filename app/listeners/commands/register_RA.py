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
                text=":x: `/register_ra <RA区分名>` のように実行してください。",
            )
            botctx.logger.info(
                f"slack user {context.actor_user_id} executed /register_RA command with no argument"
            )
            return

        # check that the user is already registered
        with botctx.db_sessmaker() as sess:
            user = sess.execute(
                select(User).where(User.slack_user_id == context.actor_user_id)
            ).scalar_one_or_none()
            if not user:
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=":x: `/init <氏名>` で先にユーザ登録を行ってください。",
                )
                botctx.logger.info(
                    f"slack user {context.actor_user_id} executed /register_RA, but is not registered as bot user yet"
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
                    text=":x: 何らかのデータベースエラーによりRAを登録できませんでした。",
                )
                botctx.logger.exception(
                    f"failed to register RA {ra_name} for slack user {context.actor_user_id} due to a database error"
                )
                raise
            else:
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=f':white_check_mark: RA "{ra_name}" を登録しました。',
                )
                botctx.logger.info(
                    f"registered RA {ra_name} for slack user {context.actor_user_id}"
                )

    return register_RA
