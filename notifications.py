from notify_run import Notify
from secrets import secret

NOTIFY_ENDPOINT = secret("NOTIFY_ENDPOINT")

channel = Notify(endpoint=NOTIFY_ENDPOINT)


def notify(message):
    channel.send(message)
