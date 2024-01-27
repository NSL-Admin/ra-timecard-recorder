from slack_bolt import App

from ..context import BotContext
from . import commands, events


def register_listeners(app: App, bot_context: BotContext):
    """
    register listeners to the given app.
    """
    commands.register(app, bot_context)
    events.register(app, bot_context)
