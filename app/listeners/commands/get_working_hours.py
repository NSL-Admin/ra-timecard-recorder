import datetime

import sqlalchemy.sql.functions as sqlfuncs
from dateutil import relativedelta
from slack_bolt import Ack, BoltContext
from slack_sdk.web.client import WebClient
from sqlalchemy import select

from ...context import BotContext
from ...db.model import RA, TimeCard, User


def get_working_hours_wrapper(bot_context: BotContext):
    botctx = bot_context

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

        first_day_of_this_month = datetime.date(year=date.year, month=date.month, day=1)
        with botctx.db_sessmaker() as sess:
            # added type hint since SQLAlchemy can't infer it
            working_hours_of_all_RAs = sess.execute(
                select(RA.ra_name, sqlfuncs.sum(TimeCard.duration))
                .join(RA, RA.id == TimeCard.ra_id)
                .join(User, User.id == RA.user_id)
                .where(
                    User.slack_user_id == context.actor_user_id,
                    TimeCard.start_time >= first_day_of_this_month,
                    TimeCard.end_time
                    < first_day_of_this_month + relativedelta.relativedelta(months=1),
                )
                .group_by(RA.ra_name)
            ).all()

        if working_hours_of_all_RAs:
            message = f':pencil: {year_month if year_month else "今月"}の稼働時間は以下の通りです。'
            for working_hour in working_hours_of_all_RAs:
                ra_name, working_hours = working_hour._tuple()
                total_seconds = working_hours.total_seconds()
                # avoid problems related to float precision by only using floor division
                hours = total_seconds // 3600
                minutes = (total_seconds - hours * 3600) // 60
                message += f"\n{ra_name}:  {int(hours):02}:{int(minutes):02}"
            client.chat_postEphemeral(
                channel=context.channel_id, user=context.actor_user_id, text=message
            )
        else:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=f':beach_with_umbrella: {year_month if year_month else "今月"}の稼働時間はありません。',
            )

    return get_working_hours
