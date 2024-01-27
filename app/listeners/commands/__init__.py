from slack_bolt import App

from ...context import BotContext
from .admin_download_all_records import admin_download_all_records_wrapper
from .download_csv import download_csv_wrapper
from .get_working_hours import get_working_hours_wrapper
from .init import init_wrapper
from .register_RA import register_RA_wrapper


def register(app: App, bot_context: BotContext):
    app.command("/init")(init_wrapper(bot_context))
    app.command("/register_ra")(register_RA_wrapper(bot_context))
    app.command("/get_working_hours")(get_working_hours_wrapper(bot_context))
    app.command("/download_csv")(download_csv_wrapper(bot_context))
    app.command("/admin_download_all_records")(
        admin_download_all_records_wrapper(bot_context)
    )
