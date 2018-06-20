from logging import getLogger
from typing import List

from django.core.mail import get_connection
from spinach import Tasks

from .settings import SPINACH_ACTUAL_EMAIL_BACKEND

tasks = Tasks()
logger = getLogger(__name__)


@tasks.task(name='spinachd:send_emails')
def send_emails(messages: List[str]):
    from .mail import deserialize_email_messages
    messages = deserialize_email_messages(messages)
    connection = get_connection(SPINACH_ACTUAL_EMAIL_BACKEND)
    logger.info('Sending %d emails using %s', len(messages),
                SPINACH_ACTUAL_EMAIL_BACKEND)
    connection.send_messages(messages)
