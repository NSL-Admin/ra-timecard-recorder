import datetime
import re
import textwrap

from slack_bolt import BoltContext
from slack_sdk.models.blocks import (
    ContextBlock,
    DividerBlock,
    MarkdownTextObject,
    SectionBlock,
)
from slack_sdk.web.client import WebClient
from sqlalchemy import select

from ...context import BotContext
from ...db.model import RA, TimeCard, User


def on_mention_wrapper(bot_context: BotContext):
    botctx = bot_context

    # NOTE: **This event also occurs when a message is edited**
    # TODO: The implementation of `on_mention` is too complicated.
    #       It would be better to do only `add` in this event handler,
    #       and `update` should be handled by the handler attached @app.event("message"),
    #       because it is not obvious that "app_mention" event also occurs when the message is edited.

    def on_mention(event: dict, context: BoltContext, client: WebClient):
        # check that `context` variable is available
        if not (context.channel_id and context.actor_user_id):
            raise ValueError("something is wrong with `context` variable")

        slack_message_ts = event["ts"]
        text = event["text"]
        expected_message_format = (
            r"<@.+>.*\n"  # ignore the first mention line
            r"• (?P<name>.+)\n"
            r"• (?P<ra_name>.+)\n"
            r"• (?P<duration>.+)\n"
            r"• (?P<description>.+)$"
        )
        message_matched = re.match(pattern=expected_message_format, string=text)
        if not message_matched or (
            message_matched and len(message_matched.groups()) != 4
        ):
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=":x: 形式が不正です。以下の形式で入力してください",
                blocks=[
                    SectionBlock(
                        text=MarkdownTextObject(
                            text=textwrap.dedent(
                                """
                                    :x: 形式が不正です。以下の形式で入力してください

                                    ```
                                    @RA timecard recorder [任意のコメント(省略可)]
                                    • あなたの氏名 (例: RA太郎)
                                    • RA区分名 (例: NTTコム)
                                    • 実働期間 (例: 2023/11/18 10:00-17:00 休憩01:00)
                                    • 作業内容の説明 (例: データセットの確認)
                                    ```
                                    """
                            )
                        ),
                    ),
                    DividerBlock(),
                    ContextBlock(
                        elements=[
                            MarkdownTextObject(
                                text=":bulb: 送ったメッセージを消して再投稿する必要はありません。編集して修正してください。"
                            )
                        ]
                    ),
                ],
            )
            return

        # extract information from user's message
        ra_name = message_matched.group("ra_name").strip()
        duration_str = message_matched.group("duration").strip()
        description = message_matched.group("description").strip()

        # ensure that this user and RA is registered
        with botctx.db_sessmaker() as sess:
            user_ra_data = sess.execute(
                select(User.id.label("user_id"), RA.id.label("ra_id"), RA.ra_name)
                .join_from(User, RA, User.id == RA.user_id)
                .where(
                    User.slack_user_id == context.actor_user_id, RA.ra_name == ra_name
                )
            ).first()
            if not user_ra_data:
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=f':x: "{ra_name}" という名称のRAは登録されていません。',
                )
                return

        user_id, ra_id, ra_name = user_ra_data._tuple()
        expected_duration_format = r"(?P<date>.+) (?P<start_time>.{5})-(?P<end_time>.{5})( 休憩(?P<break_time>.{5}))?$"
        date_matched = re.match(pattern=expected_duration_format, string=duration_str)
        if not date_matched or (date_matched and len(date_matched.groups()) < 3):
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=textwrap.dedent(
                    """
                        :x: 実働期間の形式が不正です。次の形式で入力してください。"休憩" 以降は省略可能です。桁数や不要な空白等に注意してください。
                        `2023/11/18 10:00-18:00 休憩01:00`
                    """
                ),
            )
            return

        # extract string representations of datetime info
        date_str = date_matched.group("date")
        start_time_str = date_matched.group("start_time")
        end_time_str = date_matched.group("end_time")
        break_time_str_or_none = date_matched.group("break_time")
        # convert string to datetime type
        date_format = "%Y/%m/%d %H:%M"
        start_dt = datetime.datetime.strptime(
            f"{date_str} {start_time_str}", date_format
        )
        end_dt = datetime.datetime.strptime(f"{date_str} {end_time_str}", date_format)
        duration_time = (
            datetime.datetime.min + (end_dt - start_dt)
        ).time()  # convert timedelta to Time
        if break_time_str_or_none:
            # since `time` type has no equivalent to strptime, this dirty workaround is needed...
            break_time = datetime.datetime.strptime(break_time_str_or_none, "%H:%M")
            break_time = datetime.time(hour=break_time.hour, minute=break_time.minute)
        else:
            break_time = datetime.time(hour=0, minute=0)

        # add a new record or update existing one
        with botctx.db_sessmaker() as sess:
            record = sess.execute(
                select(TimeCard).where(TimeCard.slack_message_ts == slack_message_ts)
            ).scalar_one_or_none()
            if not record:  # existing record was not found, so try to add new one
                try:
                    new_record = TimeCard(
                        ra_id=ra_id,
                        start_time=start_dt,
                        end_time=end_dt,
                        duration=duration_time,
                        break_duration=break_time,
                        description=description,
                        slack_message_ts=slack_message_ts,
                    )
                    sess.add(new_record)
                    sess.flush()
                    sess.commit()
                except Exception:
                    sess.rollback()
                    client.chat_postEphemeral(
                        channel=context.channel_id,
                        user=context.actor_user_id,
                        text=":x: 何らかのデータベースエラーにより記録できませんでした。",
                    )
                    raise
                else:
                    client.chat_postEphemeral(
                        channel=context.channel_id,
                        user=context.actor_user_id,
                        text=(
                            f":white_check_mark: 作業を記録しました。\n"
                            f"RA区分: {ra_name}\n"
                            f"作業日時: {date_str} {start_time_str}-{end_time_str}\n"
                            f"作業時間: {duration_time.hour:02}:{duration_time.minute:02}\n"
                            f"休憩時間: {break_time.hour:02}:{break_time.minute:02}\n"
                            f"作業内容: {description}"
                        ),
                    )
            else:  # existing record was found, so update it
                try:
                    record.start_time = start_dt
                    record.end_time = end_dt
                    record.duration = duration_time
                    record.break_duration = break_time
                    record.description = description
                    sess.flush()
                    sess.commit()
                except Exception:
                    sess.rollback()
                    client.chat_postEphemeral(
                        channel=context.channel_id,
                        user=context.actor_user_id,
                        text=":x: 何らかのデータベースエラーにより更新できませんでした。",
                    )
                    raise
                else:
                    client.chat_postEphemeral(
                        channel=context.channel_id,
                        user=context.actor_user_id,
                        text=(
                            f":white_check_mark: 作業を更新しました。\n"
                            f"RA区分: {ra_name}\n"
                            f"作業日時: {date_str} {start_time_str}-{end_time_str}\n"
                            f"作業時間: {duration_time.hour:02}:{duration_time.minute:02}\n"
                            f"休憩時間: {break_time.hour:02}:{break_time.minute:02}\n"
                            f"作業内容: {description}"
                        ),
                    )

    return on_mention
