from ...context import BotContext


def on_message_update_wrapper(bot_context: BotContext):
    def on_message_update():
        # TODO: extract update procedure from `on_mention`
        pass

    return on_message_update
