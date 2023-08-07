from notify_run import Notify
from secrets import secret
import os

# ENDPOINT = os.environ["NOTIFY_ENDPOINT"]
ENDPOINT = secret("NOTIFY_ENDPOINT")
channel = Notify(endpoint=ENDPOINT)


def notify(message):
    channel.send(message)
