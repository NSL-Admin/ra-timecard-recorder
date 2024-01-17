from slack_bolt import App

from listeners import commands, events

from ..context import BotContext


def register_listeners(app: App, bot_context: BotContext):
    """
    register listeners to the given app.
    """
    commands.register(app, bot_context)
    events.register(app, bot_context)
