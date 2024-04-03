from slack_bolt import BoltContext
from slack_sdk.web.client import WebClient
from sqlalchemy import select

from ...context import BotContext
from ...db.model import TimeCard


def on_message_delete_wrapper(bot_context: BotContext):
    botctx = bot_context

    def on_message_delete(event: dict, context: BoltContext, client: WebClient):
        # check that `context` variable is available
        if not (context.channel_id and context.actor_user_id):
            raise ValueError("something is wrong with `context` variable")

        # check that the event is "message_delete" event
        if "deleted_ts" not in event:
            return

        deleted_slack_message_ts = event["deleted_ts"]
        with botctx.db_sessmaker() as sess:
            try:
                record_to_delete = sess.execute(
                    select(TimeCard).where(
                        TimeCard.slack_message_ts == deleted_slack_message_ts
                    )
                ).scalar_one_or_none()
                if not record_to_delete:
                    return  # the deleted message is not a report of work
                sess.delete(record_to_delete)
                sess.flush()
                sess.commit()
            except Exception:
                sess.rollback()
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=":x: 何らかのデータベースエラーにより削除できませんでした。",
                )
                botctx.logger.exception(
                    f"failed to delete work record whose ts is {deleted_slack_message_ts} by slack user {context.actor_user_id} due to a database error"
                )
                raise
            else:
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=f":wastebasket: {record_to_delete.start_time}から{record_to_delete.end_time}の作業記録を削除しました。",
                )
                botctx.logger.info(
                    f"deleted work record by slack user {context.actor_user_id} from {record_to_delete.start_time} to {record_to_delete.end_time}: {record_to_delete.description}"
                )

    return on_message_delete
