import datetime
import os
import re
import textwrap

from dotenv import load_dotenv
from psycopg2.errors import UniqueViolation
from slack_bolt import Ack, App, BoltContext
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.models.blocks import MarkdownTextObject, SectionBlock
from slack_sdk.web.client import WebClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database import get_session
from model import RA, TimeCard, User

# load secret tokens to environmental variables
# THIS MUST BE AT THE TOP OF SOURCE CODE
if os.path.exists(".slack.env"):
    load_dotenv(dotenv_path=".slack.env")
else:
    print("Skipped loading .slack.env as it doesn't exist.")

# Initialize app with BOT_TOKEN
app = App(token=os.environ["SLACK_BOT_TOKEN"])


@app.command("/init")
def register_user(
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
            text=":x: `/init <氏名>` のように実行してください。",
        )
        return

    with get_session() as sess:  # with `with` statement, sess.close() is not needed
        try:
            user = User(
                slack_user_id=context.actor_user_id,
                name=username,
            )
            sess.add(user)
            sess.flush()
            sess.commit()
        except IntegrityError as e:
            sess.rollback()
            if isinstance(e.orig, UniqueViolation):
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=f":thinking_face: {username} さん、既にユーザ登録が完了しているようです。",
                )
            else:
                # exceptions other than UniqueViolation
                raise e
        else:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=f":white_check_mark: {username} さん、ようこそ！ユーザ登録が完了しました。",
            )


@app.command("/register_ra")
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
        return

    # check that the user is already registered
    with get_session() as sess:
        user = sess.execute(
            select(User).where(User.slack_user_id == context.actor_user_id)
        ).scalar_one_or_none()
        if not user:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=":x: `/init [氏名]` で先にユーザ登録を行ってください。",
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
            raise
        else:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=f':white_check_mark: RA "{ra_name}" を登録しました。',
            )


@app.event("app_mention")
def add_record(event: dict, context: BoltContext, client: WebClient):
    # check that `context` variable is available
    if not (context.channel_id and context.actor_user_id):
        raise ValueError("something is wrong with `context` variable")

    text = event["text"]
    expected_message_format = (
        r"<@.+>.*\n"  # ignore the first mention line
        r"• (?P<name>.+)\n"
        r"• (?P<ra_name>.+)\n"
        r"• (?P<duration>.+)\n"
        r"• (?P<description>.+)$"
    )
    message_matched = re.match(pattern=expected_message_format, string=text)
    if not message_matched or (message_matched and len(message_matched.groups()) != 4):
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

                                @RA timecard recorder [任意のコメント(省略可)]
                                • あなたの氏名 (例: RA太郎)
                                • RA区分名 (例: NTTコム)
                                • 実働期間 (例: 2023/11/18 10:00-17:00 休憩01:00)
                                • 作業内容の説明 (例: データセットの確認)
                                """
                        )
                    ),
                ),
            ],
        )
        return

    # extract information from user's message
    ra_name = message_matched.group("ra_name")
    duration_str = message_matched.group("duration")
    description = message_matched.group("description")

    # ensure that this user and RA is registered
    with get_session() as sess:
        user_ra_data = sess.execute(
            select(User.id.label("user_id"), RA.id.label("ra_id"), RA.ra_name)
            .join_from(User, RA, User.id == RA.user_id)
            .where(User.slack_user_id == context.actor_user_id, RA.ra_name == ra_name)
        ).first()
        if not user_ra_data:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=f':x: "{ra_name}" という名称のRAは登録されていません。',
            )
            return

    user_id, ra_id, ra_name = user_ra_data
    expected_duration_format = r"(?P<date>.+) (?P<begin_time>.{5})-(?P<end_time>.{5})( 休憩(?P<break_time>.{5}))?$"
    date_matched = re.match(pattern=expected_duration_format, string=duration_str)
    if not date_matched or (date_matched and len(date_matched.groups()) < 3):
        client.chat_postEphemeral(
            channel=context.channel_id,
            user=context.actor_user_id,
            text=textwrap.dedent(
                """
                    :x: 形式が不正です。次の形式で入力してください。"休憩" 以降は省略可能です。桁数や不要な空白等に注意してください。
                    `2023/11/18 10:00-18:00 休憩01:00`
                """
            ),
        )
        return

    # extract string representations of datetime info
    date_str = date_matched.group("date")
    begin_time_str = date_matched.group("begin_time")
    end_time_str = date_matched.group("end_time")
    break_time_str_or_none = date_matched.group("break_time")
    # convert string to datetime type
    date_format = "%Y/%m/%d %H:%M"
    begin_dt = datetime.datetime.strptime(f"{date_str} {begin_time_str}", date_format)
    end_dt = datetime.datetime.strptime(f"{date_str} {end_time_str}", date_format)
    duration_time = (
        datetime.datetime.min + (end_dt - begin_dt)
    ).time()  # convert timedelta to Time
    if break_time_str_or_none:
        # since `time` type has no equivalent to strptime, this dirty workaround is needed...
        break_time = datetime.datetime.strptime(break_time_str_or_none, "%H:%M")
        break_time = datetime.time(hour=break_time.hour, minute=break_time.minute)
    else:
        break_time = datetime.time(hour=0, minute=0)

    # add to the database
    with get_session() as sess:
        try:
            record = TimeCard(
                ra_id=ra_id,
                start_time=begin_dt,
                end_time=end_dt,
                duration=duration_time,
                break_duration=break_time,
                description=description,
            )
            sess.add(record)
            sess.flush()
            sess.commit()
        except Exception:
            sess.rollback()
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text="何らかのデータベースエラーにより記録できませんでした。",
            )
            raise
        else:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=(
                    f":white_check_mark: 勤怠を記録しました。\n"
                    f"RA区分: {ra_name}\n"
                    f"作業日時: {date_str} {begin_time_str}-{end_time_str}\n"
                    f"作業時間: {duration_time.hour:02}:{duration_time.minute:02}\n"
                    f"休憩時間: {break_time.hour:02}:{break_time.minute:02}\n"
                    f"作業内容: {description}"
                ),
            )


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
