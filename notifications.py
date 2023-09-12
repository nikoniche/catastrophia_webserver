from notify_run import Notify
from secrets import secret

# endpoint  and channel for notify-run
NOTIFY_ENDPOINT = secret("NOTIFY_ENDPOINT")
channel = Notify(endpoint=NOTIFY_ENDPOINT)

def notify(message: str) -> None:
    """Sends a message to the current notify-run channel."""
    channel.send(message)
