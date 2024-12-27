from slack_bolt import BoltContext


def on_message_events_to_ignore_handler(context: BoltContext):
    """This handler does nothing other than responding with Ack function

    Args:
        context (BoltContext): The context information provided by Bolt
    """

    context.ack()
