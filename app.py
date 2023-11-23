import csv
import datetime
import io
import os
import re
import textwrap
from typing import Optional

import sqlalchemy.sql.functions as sqlfuncs
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
                text=":email: DMでこのBotからのメッセージを確認してください。",
            )
            dm_with_the_user = client.conversations_open(users=context.actor_user_id)
            client.chat_postMessage(
                channel=dm_with_the_user["channel"]["id"],
                text=f":white_check_mark: {username} さん、ようこそ！ユーザ登録が完了しました。\n:rocket: 上の「ホーム」タブを開いて使い方ガイドを読んでください！",
                mrkdwn=True,
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
                text=":x: `/init <氏名>` で先にユーザ登録を行ってください。",
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

    user_id, ra_id, ra_name = user_ra_data._tuple()
    expected_duration_format = r"(?P<date>.+) (?P<start_time>.{5})-(?P<end_time>.{5})( 休憩(?P<break_time>.{5}))?$"
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
    start_time_str = date_matched.group("start_time")
    end_time_str = date_matched.group("end_time")
    break_time_str_or_none = date_matched.group("break_time")
    # convert string to datetime type
    date_format = "%Y/%m/%d %H:%M"
    start_dt = datetime.datetime.strptime(f"{date_str} {start_time_str}", date_format)
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

    # add to the database
    with get_session() as sess:
        try:
            record = TimeCard(
                ra_id=ra_id,
                start_time=start_dt,
                end_time=end_dt,
                duration=duration_time,
                break_duration=break_time,
                description=description,
                slack_message_ts=slack_message_ts,
            )
            sess.add(record)
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


@app.event("message")
def delete_record(event: dict, context: BoltContext, client: WebClient):
    # check that `context` variable is available
    if not (context.channel_id and context.actor_user_id):
        raise ValueError("something is wrong with `context` variable")

    # check that the event is "message_delete" event
    if "deleted_ts" not in event:
        return

    deleted_slack_message_ts = event["deleted_ts"]
    with get_session() as sess:
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
            raise
        else:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=f":wastebasket: {record_to_delete.start_time}から{record_to_delete.end_time}の作業記録を削除しました。",
            )


@app.command("/get_working_hours")
def get_working_hours(
    ack: Ack, body: dict, client: WebClient, command: dict, context: BoltContext
):
    ack()

    # check that `context` variable is available
    if not (context.channel_id and context.actor_user_id):
        raise ValueError("something is wrong with `context` variable")

    year_month = command["text"].strip()
    if year_month:
        try:
            date = datetime.datetime.strptime(year_month, "%Y/%m")
        except ValueError:  # `year_month` was in invalid format
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=":x: `/get_working_hours 2023/11` のように実行してください。",
            )
            return
    else:
        date = datetime.date.today()

    with get_session() as sess:
        # added type hint since SQLAlchemy can't infer it
        working_hours: Optional[datetime.timedelta] = sess.execute(
            select(sqlfuncs.sum(TimeCard.duration))
            .join(RA, RA.id == TimeCard.ra_id)
            .join(User, User.id == RA.user_id)
            .where(
                User.slack_user_id == context.actor_user_id,
                TimeCard.end_time
                >= datetime.date(year=date.year, month=date.month, day=1),
                TimeCard.end_time
                < datetime.date(year=date.year, month=date.month + 1, day=1),
            )
        ).scalar()

    if working_hours:
        working_hours_datetime: datetime.time = (
            datetime.datetime.min + working_hours
        ).time()  # convert timedelta to time
        client.chat_postEphemeral(
            channel=context.channel_id,
            user=context.actor_user_id,
            text=f':pencil: {year_month if year_month else "今月"}の稼働時間は{working_hours_datetime.strftime("%H:%M")}です。',
        )
    else:
        client.chat_postEphemeral(
            channel=context.channel_id,
            user=context.actor_user_id,
            text=f':beach_with_umbrella: {year_month if year_month else "今月"}の稼働時間はありません。',
        )


@app.command("/download_csv")
def download_csv(
    ack: Ack, body: dict, client: WebClient, command: dict, context: BoltContext
):
    ack()

    # check that `context` variable is available
    if not (context.channel_id and context.actor_user_id):
        raise ValueError("something is wrong with `context` variable")

    year_month = command["text"].strip()
    if year_month:
        try:
            date = datetime.datetime.strptime(year_month, "%Y/%m")
        except ValueError:  # `year_month` was in invalid format
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=":x: `/download_csv 2023/11` のように実行してください。",
            )
            return
    else:
        date = datetime.date.today()

    # get all records within the specified month
    with get_session() as sess:
        records = sess.execute(
            select(User, RA, TimeCard)
            .join(RA, RA.id == TimeCard.ra_id)
            .join(User, User.id == RA.user_id)
            .where(
                User.slack_user_id == context.actor_user_id,
                TimeCard.end_time
                >= datetime.date(year=date.year, month=date.month, day=1),
                TimeCard.end_time
                < datetime.date(year=date.year, month=date.month + 1, day=1),
            )
            .order_by(TimeCard.start_time)
        ).all()
        if not records:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=f':beach_with_umbrella: {year_month if year_month else "今月"}の稼働時間はありません。',
            )
            return

    # make CSV file
    csv_text_as_file = io.StringIO()
    writer = csv.DictWriter(
        f=csv_text_as_file,
        fieldnames=[
            "ra_name",
            "date",
            "start_time",
            "end_time",
            "break_time",
            "description",
        ],
    )
    writer.writeheader()
    for record in records:
        _, ra, timecard = record._tuple()
        writer.writerow(
            {
                "ra_name": ra.ra_name,
                "date": timecard.start_time.strftime("%d"),
                "start_time": timecard.start_time.strftime("%H%M"),
                "end_time": timecard.end_time.strftime("%H%M"),
                "break_time": timecard.break_duration.strftime("%H%M"),
                "description": timecard.description,
            }
        )
    csv_text = csv_text_as_file.getvalue()
    csv_text_as_file.close()

    # upload the CSV and send user the URL to it
    new_csv_file = client.files_upload_v2(
        channel=context.channel_id,
        title=f"{date.year}/{date.month}の作業時間",
        filename=f"{date.year}_{date.month}_working_hours.csv",
        content=csv_text,
    )

    file_url = new_csv_file.get("file").get("permalink")  # type:ignore
    client.chat_postEphemeral(
        channel=context.channel_id,
        user=context.actor_user_id,
        text=f":page_facing_up: {file_url}",
    )


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
