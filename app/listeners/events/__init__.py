from slack_bolt import App

from ...context import BotContext
from .on_mention import on_mention_wrapper
from .on_message_delete import on_message_delete_wrapper

# from .on_message_update import on_message_update_wrapper
# TODO: register on_message_update after implementation is completed.


def register(app: App, bot_context: BotContext):
    app.event("app_mention")(on_mention_wrapper(bot_context))
    # IMPORTANT: using `app.event("message")` multiple times will make the bot fail to register handlers but the first one.
    # DO NOT uncomment the below line if that activates more than one `app.event("message")`.
    # [^read the above message^] app.event("message")(on_message_update_wrapper(bot_context))
    app.event({"type": "message", "subtype": "message_deleted"})(
        on_message_delete_wrapper(bot_context)
    )
