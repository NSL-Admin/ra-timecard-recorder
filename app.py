import os

from dotenv import load_dotenv
from psycopg2.errors import UniqueViolation
from slack_bolt import Ack, App, BoltContext
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.web.client import WebClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database import get_session
from model import RA, User

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
    print(type(client))
    print(event["text"])


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
