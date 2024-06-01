import csv
import datetime
import io

from dateutil import relativedelta
from slack_bolt import Ack, BoltContext
from slack_sdk.web.client import WebClient
from sqlalchemy import select

from ...context import BotContext
from ...db.model import RA, TimeCard, User


def admin_download_all_records_wrapper(bot_context: BotContext):
    botctx = bot_context

    def admin_download_all_records(
        ack: Ack, body: dict, client: WebClient, command: dict, context: BoltContext
    ):
        ack()

        # check that `context` variable is available
        if not (context.channel_id and context.actor_user_id):
            raise ValueError("something is wrong with `context` variable")

        if context.actor_user_id not in botctx.botcfg.admin_ids:
            client.chat_postEphemeral(
                channel=context.channel_id,
                user=context.actor_user_id,
                text=":x: You are not allowed to use this command.",
            )
            botctx.logger.info(
                f"slack user {context.actor_user_id} tried to execute /admin_download_all_records, but is not allowed to"
            )
            return

        year_month = command["text"].strip()
        if year_month:
            try:
                date = datetime.datetime.strptime(year_month, "%Y/%m")
            except ValueError:  # `year_month` was in invalid format
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=":x: Use this command like `/download_all_working_records 2023/11`.",
                )
                botctx.logger.info(
                    f"slack user {context.actor_user_id} executed /admin_download_all_records with invalid argument: {year_month}"
                )
                return
        else:
            date = datetime.date.today()

        first_day_of_this_month = datetime.date(year=date.year, month=date.month, day=1)
        # get all records within the specified month
        with botctx.db_sessmaker() as sess:
            records = sess.execute(
                select(User, RA, TimeCard)
                .join(RA, RA.id == TimeCard.ra_id)
                .join(User, User.id == RA.user_id)
                .where(
                    TimeCard.start_time >= first_day_of_this_month,
                    TimeCard.end_time
                    < first_day_of_this_month + relativedelta.relativedelta(months=1),
                )
                .order_by(RA.ra_name, User.id, TimeCard.start_time)
            ).all()
            if not records:
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.actor_user_id,
                    text=f':beach_with_umbrella: No work records found in {year_month if year_month else "this month"}',
                )
                botctx.logger.info(
                    f"found no work record in {date.year}/{date.month} for any user"
                )
                return

        # make CSV file
        csv_text_as_file = io.StringIO()
        writer = csv.DictWriter(
            f=csv_text_as_file,
            fieldnames=[
                "name",
                "ra_name",
                "start_timestamp",
                "end_timestamp",
                "work_duration",
                "break_duration",
                "description",
            ],
        )
        writer.writeheader()
        for record in records:
            user, ra, timecard = record._tuple()
            duration_time = (
                datetime.datetime.min + (timecard.end_time - timecard.start_time)
            ).time()  # convert timedelta to Time
            writer.writerow(
                {
                    "name": user.name,
                    "ra_name": ra.ra_name,
                    "start_timestamp": timecard.start_time.strftime(
                        "%Y/%m/%d %H:%M:%S"
                    ),
                    "end_timestamp": timecard.end_time.strftime("%Y/%m/%d %H:%M:%S"),
                    "work_duration": duration_time.strftime("%H:%M"),
                    "break_duration": timecard.break_duration.strftime("%H:%M"),
                    "description": timecard.description,
                }
            )
        csv_text = csv_text_as_file.getvalue()
        csv_text_as_file.close()

        dm_with_the_user = client.conversations_open(users=context.actor_user_id)
        # upload the CSV and send user the URL to it
        client.files_upload_v2(
            channel=dm_with_the_user["channel"]["id"],
            title=f"Work records of all users in {date.year}/{date.month}",
            filename=f"{date.year}_{date.month}_all_working_records.csv",
            content=csv_text.encode(
                encoding="cp932"
            ),  # NOTE: this command exports CSV in Shift_JIS. "cp932" can handle platform-dependent characters like "髙".
        )

        client.chat_postEphemeral(
            channel=context.channel_id,
            user=context.actor_user_id,
            text=":page_facing_up: Sent you a CSV file in DM.",
        )

        botctx.logger.info(
            f"sent CSV file of all work records to slack user {context.actor_user_id}"
        )

    return admin_download_all_records
