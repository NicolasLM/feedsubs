import base64
import pickle
from typing import List
import zlib

from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend

from .tasks import tasks


class BackgroundEmailBackend(BaseEmailBackend):

    def send_messages(self, messages):
        msg_count = 0
        for message in messages:
            message.message()  # .message() triggers header validation
            msg_count += 1
        messages = serialize_email_messages(messages)
        tasks.schedule('spinachd:send_emails', messages)

        return msg_count


def serialize_email_messages(messages: List[EmailMessage]):
    """Serialize EmailMessages to be passed as task argument.

    Pickle is used because serializing an EmailMessage to json can be a bit
    tricky and would probably break if Django modifies the structure of the
    object in the future.
    """
    return [
        base64.b64encode(zlib.compress(pickle.dumps(m, protocol=4))).decode()
        for m in messages
    ]


def deserialize_email_messages(messages: List[str]):
    """Deserialize EmailMessages passed as task argument."""
    return [
        pickle.loads(zlib.decompress(base64.b64decode(m)))
        for m in messages
    ]
