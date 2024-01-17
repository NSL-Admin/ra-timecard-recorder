from slack_bolt import App

from ...context import BotContext
from .on_mention import on_mention_wrapper
from .on_message_delete import on_message_delete_wrapper
from .on_message_update import on_message_update_wrapper


def register(app: App, bot_context: BotContext):
    app.event("app_mention")(on_mention_wrapper(bot_context))
    app.event("message")(on_message_update_wrapper(bot_context))
    app.event("message")(on_message_delete_wrapper(bot_context))
